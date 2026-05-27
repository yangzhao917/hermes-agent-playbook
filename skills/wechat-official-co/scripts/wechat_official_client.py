#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Just One API 微信公众号公开内容获取工具

环境变量：
  JUSTONE_API_TOKEN      推荐配置，Just One API token
  JUSTONE_API_BASE_URL   可选，默认 https://api.justoneapi.com

示例：
  python scripts/wechat_official_client.py search --keyword "黑客松" --search-type _2 --sort-type _2
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import requests

# 非敏感运行参数默认值：未配置环境变量时自动使用这些值
DEFAULT_BASE_URL = "https://api.justoneapi.com"
DEFAULT_TIMEOUT = "75"
DEFAULT_MAX_RETRIES = "1"
DEFAULT_DETAIL_MIN_INTERVAL_SECONDS = "8"
DEFAULT_DETAIL_CACHE_TTL_SECONDS = str(7 * 24 * 3600)
DEFAULT_SEARCH_CACHE_TTL_SECONDS = str(6 * 3600)
DEFAULT_CACHE_DIR = ".cache/justone_wechat"

TIMEOUT = int(os.getenv("JUSTONE_TIMEOUT", DEFAULT_TIMEOUT))
MAX_RETRIES = int(os.getenv("JUSTONE_MAX_RETRIES", DEFAULT_MAX_RETRIES))
# article_detail 的 301/COLLECT FAILED 通常是采集失败或限流，不做连续强重试，避免越重试越失败。
RETRYABLE_CODES = {302, 500}
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}
CACHE_DIR = Path(os.getenv("JUSTONE_CACHE_DIR", DEFAULT_CACHE_DIR))
DETAIL_CACHE_TTL_SECONDS = int(os.getenv("JUSTONE_DETAIL_CACHE_TTL_SECONDS", DEFAULT_DETAIL_CACHE_TTL_SECONDS))
SEARCH_CACHE_TTL_SECONDS = int(os.getenv("JUSTONE_SEARCH_CACHE_TTL_SECONDS", DEFAULT_SEARCH_CACHE_TTL_SECONDS))
DETAIL_MIN_INTERVAL_SECONDS = float(os.getenv("JUSTONE_DETAIL_MIN_INTERVAL_SECONDS", DEFAULT_DETAIL_MIN_INTERVAL_SECONDS))
DETAIL_LAST_CALL_FILE = CACHE_DIR / "article_detail.last_call"


class JustOneError(Exception):
    pass


def get_token() -> str:
    # Token 只允许从 JUSTONE_API_TOKEN 读取。
    # 不提供默认 token，避免泄露、误提交或误用。
    token = os.getenv("JUSTONE_API_TOKEN")
    if not token or token.strip() in {"", "your_token_here", "请替换为你的token", "你的 token"}:
        raise JustOneError("缺少环境变量 JUSTONE_API_TOKEN。请配置真实 token；为避免泄露和误用，脚本不提供默认 token。")
    return token.strip()


def get_base_url() -> str:
    return os.getenv("JUSTONE_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def normalize_article_url(url: str) -> str:
    """规范化微信文章 URL，减少同一文章因追踪参数不同导致重复采集。"""
    parsed = urlparse(url.strip())
    keep_keys = {"__biz", "mid", "idx", "sn", "chksm", "scene"}
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k in keep_keys]
    normalized_query = urlencode(query)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", normalized_query, ""))


def cache_key(action: str, path: str, params: Optional[Dict[str, Any]]) -> str:
    safe_params = clean_params(params)
    if "articleUrl" in safe_params:
        safe_params["articleUrl"] = normalize_article_url(str(safe_params["articleUrl"]))
    raw = json.dumps({"action": action, "path": path, "params": safe_params}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cache_ttl(action: str) -> int:
    if action == "article_detail":
        return DETAIL_CACHE_TTL_SECONDS
    if action == "search":
        return SEARCH_CACHE_TTL_SECONDS
    return 0


def read_cache(action: str, path: str, params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    ttl = get_cache_ttl(action)
    if ttl <= 0:
        return None
    file_path = CACHE_DIR / f"{cache_key(action, path, params)}.json"
    if not file_path.exists():
        return None
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if time.time() - float(payload.get("cached_at", 0)) > ttl:
            return None
        result = payload.get("result")
        if isinstance(result, dict):
            result["from_cache"] = True
            return result
    except Exception:
        return None
    return None


def write_cache(action: str, path: str, params: Optional[Dict[str, Any]], result: Dict[str, Any]) -> None:
    ttl = get_cache_ttl(action)
    if ttl <= 0:
        return
    # 只缓存成功结果，避免把临时限流/失败状态长期固化。
    if result.get("success") is not True:
        return
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        file_path = CACHE_DIR / f"{cache_key(action, path, params)}.json"
        file_path.write_text(json.dumps({"cached_at": time.time(), "result": result}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def throttle_article_detail(action: str) -> None:
    if action != "article_detail" or DETAIL_MIN_INTERVAL_SECONDS <= 0:
        return
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        last = 0.0
        if DETAIL_LAST_CALL_FILE.exists():
            last = float(DETAIL_LAST_CALL_FILE.read_text(encoding="utf-8") or "0")
        wait = DETAIL_MIN_INTERVAL_SECONDS - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        DETAIL_LAST_CALL_FILE.write_text(str(time.time()), encoding="utf-8")
    except Exception:
        # 限速文件失败不影响主流程。
        pass


def build_anti_hallucination(can_use_data: bool = False, can_full_article: bool = False) -> Dict[str, Any]:
    return {
        "can_use_data_for_facts": can_use_data,
        "can_summarize_full_article": can_full_article,
        "must_not_infer_missing_fields": True,
        "missing_field_text": "未获取到",
        "failed_detail_rule": "article_detail 失败、限流、COLLECT FAILED 或正文缺失时，只能整理搜索结果线索，不能生成完整文章摘要、报名链接、赛程、地点、奖项、主办方等正文级事实。",
    }


def clean_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not params:
        return {}
    return {k: v for k, v in params.items() if v is not None}


def extract_message(body: Dict[str, Any]) -> str:
    for key in ("message", "msg", "error", "errmsg"):
        value = body.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def contains_collect_failed(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return "COLLECT FAILED" in value.upper()
    if isinstance(value, dict):
        return any(contains_collect_failed(v) for v in value.values())
    if isinstance(value, list):
        return any(contains_collect_failed(v) for v in value)
    return False


def has_article_body(data: Any) -> bool:
    """尽量保守地判断 article_detail 是否返回正文内容。"""
    if not isinstance(data, dict):
        return False

    body_keys = (
        "content",
        "html",
        "markdown",
        "text",
        "articleContent",
        "article_content",
        "rich_media_content",
    )
    for key in body_keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return True

    # 某些接口可能把正文放在嵌套对象中；仅做保守识别，不在此处生成内容。
    for value in data.values():
        if isinstance(value, dict) and has_article_body(value):
            return True
    return False


def normalize_response(
    *,
    action: str,
    path: str,
    status_code: Optional[int],
    body: Dict[str, Any],
) -> Dict[str, Any]:
    code = body.get("code")
    message = extract_message(body)
    data = body.get("data")

    is_success = status_code is not None and status_code < 400 and code == 0
    is_collect_failed = contains_collect_failed(body)
    failure_type = None

    if is_collect_failed:
        failure_type = "collect_failed"
    elif not is_success:
        failure_type = "api_failed"
    elif action == "article_detail" and not has_article_body(data):
        # 正文详情接口成功但无正文，仍然不能当完整正文使用。
        failure_type = "article_body_missing"

    return {
        "success": is_success and failure_type is None,
        "status_code": status_code,
        "code": code,
        "message": message or None,
        "data": data if is_success else None,
        "raw": body,
        "action": action,
        "path": path,
        "is_collect_failed": is_collect_failed,
        "failure_type": failure_type,
        "degrade_mode": "candidate_leads" if action == "article_detail" and failure_type is not None else None,
        "from_cache": False,
        "anti_hallucination": build_anti_hallucination(
            can_use_data=bool(is_success and data is not None),
            can_full_article=bool(action == "article_detail" and is_success and failure_type is None),
        ),
    }


def request_justone(
    *,
    action: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    retry: int = MAX_RETRIES,
) -> Dict[str, Any]:
    token = get_token()
    base_url = get_base_url()
    url = f"{base_url}{path}"
    query = {"token": token}
    clean = clean_params(params)
    if "articleUrl" in clean:
        clean["articleUrl"] = normalize_article_url(str(clean["articleUrl"]))
    query.update(clean)

    cached = read_cache(action, path, clean)
    if cached is not None:
        return cached

    last_result: Optional[Dict[str, Any]] = None

    for attempt in range(retry + 1):
        try:
            throttle_article_detail(action)
            response = requests.get(url, params=query, timeout=TIMEOUT)
            try:
                body = response.json()
            except Exception:
                body = {
                    "code": None,
                    "message": f"响应不是 JSON，HTTP {response.status_code}",
                    "data": None,
                }

            result = normalize_response(
                action=action,
                path=path,
                status_code=response.status_code,
                body=body,
            )
            last_result = result

            if result.get("success") is True:
                write_cache(action, path, clean, result)
                return result

            code = result.get("code")
            # 301/COLLECT FAILED 多数不是瞬时网络错误，立即重试通常会加剧限流；直接降级。
            if result.get("is_collect_failed") or result.get("failure_type") == "collect_failed" or code == 301:
                return result

            should_retry = (
                response.status_code in RETRYABLE_HTTP_STATUS
                or code in RETRYABLE_CODES
            )

            # 正文采集失败可以有限重试；重试后仍失败则交给上层按防幻读规则处理。
            if not should_retry or attempt >= retry:
                return result

            wait_seconds = 2 + attempt
            time.sleep(wait_seconds)

        except requests.Timeout:
            last_result = {
                "success": False,
                "status_code": None,
                "code": None,
                "message": "请求超时",
                "data": None,
                "raw": None,
                "action": action,
                "path": path,
                "is_collect_failed": False,
                "failure_type": "timeout",
                "anti_hallucination": build_anti_hallucination(False, False),
            }
            if attempt >= retry:
                return last_result
            time.sleep(2 + attempt)

        except requests.RequestException as exc:
            last_result = {
                "success": False,
                "status_code": None,
                "code": None,
                "message": f"网络请求失败：{exc}",
                "data": None,
                "raw": None,
                "action": action,
                "path": path,
                "is_collect_failed": False,
                "failure_type": "network_error",
                "anti_hallucination": build_anti_hallucination(False, False),
            }
            if attempt >= retry:
                return last_result
            time.sleep(2 + attempt)

    return last_result or {
        "success": False,
        "status_code": None,
        "code": None,
        "message": "未知错误",
        "data": None,
        "raw": None,
        "action": action,
        "path": path,
        "is_collect_failed": False,
        "failure_type": "unknown_error",
        "anti_hallucination": {
            "can_use_data_for_facts": False,
            "can_summarize_full_article": False,
            "must_not_infer_missing_fields": True,
            "missing_field_text": "未获取到",
        },
    }


def print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def action_search(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        action="search",
        path="/api/weixin/search/v1",
        params={
            "keyword": args.keyword,
            "offset": args.offset,
            "searchType": args.search_type,
            "sortType": args.sort_type,
        },
    )


def action_user_posts(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        action="user_posts",
        path="/api/weixin/get-user-post/v1",
        params={"wxid": args.wxid},
    )


def action_article_detail(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        action="article_detail",
        path="/api/weixin/get-article-detail/v1",
        params={"articleUrl": args.article_url},
    )


def action_article_feedback(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        action="article_feedback",
        path="/api/weixin/get-article-feedback/v1",
        params={"articleUrl": args.article_url},
    )


def action_article_comments(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        action="article_comments",
        path="/api/weixin/get-article-comment/v1",
        params={"articleUrl": args.article_url},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Just One API 微信公众号公开内容获取工具")
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("search", help="关键词搜索微信公众号内容")
    p.add_argument("--keyword", required=True, help="搜索关键词")
    p.add_argument("--offset", type=int, default=0, help="分页偏移量，从 0 开始，每次增加 20")
    p.add_argument(
        "--search-type",
        default="_0",
        choices=["_0", "_1", "_2", "_7", "_262208", "_384", "_16777728", "_9", "_1024", "_512", "_16384", "_8192", "_8"],
        help="搜索结果类型：_0全部，_1公众号，_2文章等",
    )
    p.add_argument(
        "--sort-type",
        default="_0",
        choices=["_0", "_2", "_4"],
        help="排序：_0默认，_2最新，_4热门",
    )
    p.set_defaults(func=action_search)

    p = sub.add_parser("user_posts", help="获取微信公众号用户发布帖子")
    p.add_argument("--wxid", required=True, help="微信公众号 ID，例如 rmrbwx")
    p.set_defaults(func=action_user_posts)

    p = sub.add_parser("article_detail", help="获取微信公众号文章详情")
    p.add_argument("--article-url", required=True, help="微信文章 URL")
    p.set_defaults(func=action_article_detail)

    p = sub.add_parser("article_feedback", help="获取微信公众号文章互动指标")
    p.add_argument("--article-url", required=True, help="微信文章 URL")
    p.set_defaults(func=action_article_feedback)

    p = sub.add_parser("article_comments", help="获取微信公众号文章评论")
    p.add_argument("--article-url", required=True, help="微信文章 URL")
    p.set_defaults(func=action_article_comments)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = args.func(args)
        print_json(result)
        if not result.get("success"):
            sys.exit(1)
    except JustOneError as exc:
        print_json({
            "success": False,
            "status_code": None,
            "code": None,
            "message": str(exc),
            "data": None,
            "raw": None,
            "action": args.action if hasattr(args, "action") else None,
            "path": None,
            "is_collect_failed": False,
            "failure_type": "config_error",
            "anti_hallucination": {
                "can_use_data_for_facts": False,
                "can_summarize_full_article": False,
                "must_not_infer_missing_fields": True,
                "missing_field_text": "未获取到",
            },
        })
        sys.exit(1)


if __name__ == "__main__":
    main()
