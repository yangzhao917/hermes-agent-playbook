#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Just One API 小红书备用数据源客户端

用途：当 Rnote 不可用时，使用 Just One API 获取小红书公开信息。

环境变量：
  JUSTONE_API_TOKEN  必填，Just One API token
  JUSTONE_BASE_URL   可选，默认 https://api.justoneapi.com

示例：
  python scripts/justone_client.py search_notes --keyword "AI Agent 求职" --page 1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests


DEFAULT_BASE_URL = "https://api.justoneapi.com"
TIMEOUT = 65
MAX_RETRIES = 2
RETRY_CODES = {301, 302, 500}


class JustOneError(Exception):
    pass


def get_token() -> str:
    token = os.getenv("JUSTONE_API_TOKEN")
    if not token:
        raise JustOneError("缺少环境变量 JUSTONE_API_TOKEN")
    return token


def get_base_url() -> str:
    base_url = os.getenv("JUSTONE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise JustOneError("JUSTONE_BASE_URL 格式不正确")
    return base_url


def clean_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not params:
        return {}
    return {k: v for k, v in params.items() if v is not None and v != ""}


def redact_token(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("***" if k.lower() == "token" else redact_token(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_token(x) for x in value]
    return value


def normalize_success(status_code: int, body: Dict[str, Any], path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    data = body.get("data")
    return {
        "success": True,
        "provider": "justoneapi",
        "status_code": status_code,
        "code": body.get("code"),
        "message": body.get("message", ""),
        "path": path,
        "params": redact_token(params),
        "data": data,
        "data_is_empty": data in (None, [], {}),
        "anti_hallucination_notice": "Only use fields present in data. Missing fields must be reported as 接口未返回.",
    }


def normalize_error(
    *,
    status_code: Optional[int],
    code: Optional[int],
    message: str,
    path: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "success": False,
        "provider": "justoneapi",
        "status_code": status_code,
        "code": code,
        "message": message,
        "path": path,
        "params": redact_token(params or {}),
        "data": None,
        "anti_hallucination_notice": "Request failed. Do not generate analysis or conclusions from this result.",
    }


def request_justone(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    retry: int = MAX_RETRIES,
) -> Dict[str, Any]:
    token = get_token()
    base_url = get_base_url()
    url = f"{base_url}{path}"
    final_params = clean_params(params)
    final_params["token"] = token

    last_error: Optional[Dict[str, Any]] = None

    for attempt in range(retry + 1):
        try:
            response = requests.get(url, params=final_params, timeout=TIMEOUT)
            try:
                body = response.json()
            except Exception:
                return normalize_error(
                    status_code=response.status_code,
                    code=None,
                    message=f"响应不是 JSON，HTTP {response.status_code}",
                    path=path,
                    params=final_params,
                )

            code = body.get("code")
            message = body.get("message") or body.get("msg") or ""

            if response.status_code < 400 and code == 0:
                return normalize_success(response.status_code, body, path, final_params)

            last_error = normalize_error(
                status_code=response.status_code,
                code=code,
                message=message or f"HTTP {response.status_code}",
                path=path,
                params=final_params,
            )

            should_retry = code in RETRY_CODES or response.status_code in {429, 500, 502, 503, 504}
            if not should_retry or attempt >= retry:
                return last_error

            time.sleep(2 * (attempt + 1))

        except requests.Timeout:
            last_error = normalize_error(
                status_code=None,
                code=None,
                message="请求超时",
                path=path,
                params=final_params,
            )
            if attempt >= retry:
                return last_error
            time.sleep(2 * (attempt + 1))

        except requests.RequestException as exc:
            last_error = normalize_error(
                status_code=None,
                code=None,
                message=f"网络请求失败：{exc}",
                path=path,
                params=final_params,
            )
            if attempt >= retry:
                return last_error
            time.sleep(2 * (attempt + 1))

    return last_error or normalize_error(
        status_code=None,
        code=None,
        message="未知错误",
        path=path,
        params=final_params,
    )


def print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


# Actions

def action_search_notes(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/search-note/v2",
        {
            "keyword": args.keyword,
            "page": args.page,
            "sort": args.sort,
            "noteType": args.note_type,
            "noteTime": args.note_time,
        },
    )


def action_search_notes_v3(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/search-note/v3",
        {
            "keyword": args.keyword,
            "page": args.page,
            "sort": args.sort,
            "noteType": args.note_type,
        },
    )


def action_search_users(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/search-user/v2",
        {"keyword": args.keyword, "page": args.page},
    )


def action_note_detail(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/get-note-detail/v1",
        {"noteId": args.note_id, "format": args.format},
    )


def action_note_detail_v5(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/get-note-detail/v5",
        {"noteId": args.note_id},
    )


def action_note_comments(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/get-note-comment/v2",
        {"noteId": args.note_id, "lastCursor": args.last_cursor, "sort": args.sort},
    )


def action_note_comments_v4(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/get-note-comment/v4",
        {"noteId": args.note_id},
    )


def action_comment_replies(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/get-note-sub-comment/v2",
        {"noteId": args.note_id, "commentId": args.comment_id, "lastCursor": args.last_cursor},
    )


def action_user_profile(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/get-user/v3",
        {"userId": args.user_id},
    )


def action_user_notes(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/get-user-note-list/v4",
        {"userId": args.user_id, "lastCursor": args.last_cursor},
    )


def action_resolve_share(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/share-url-transfer/v1",
        {"shareUrl": args.share_url},
    )


def action_keyword_suggestions(args: argparse.Namespace) -> Dict[str, Any]:
    return request_justone(
        "/api/xiaohongshu/search-recommend/v1",
        {"keyword": args.keyword},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Just One API 小红书备用数据源客户端")
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("search_notes", help="搜索笔记 V2")
    p.add_argument("--keyword", required=True)
    p.add_argument("--page", type=int, default=1)
    p.add_argument(
        "--sort",
        default="general",
        choices=["general", "popularity_descending", "time_descending", "comment_descending", "collect_descending"],
    )
    p.add_argument("--note-type", default="_0", choices=["_0", "_1", "_2"])
    p.add_argument("--note-time", default=None, choices=[None, "一天内", "一周内", "半年内"])
    p.set_defaults(func=action_search_notes)

    p = sub.add_parser("search_notes_v3", help="搜索笔记 V3")
    p.add_argument("--keyword", required=True)
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--sort", default="general", choices=["general", "popularity_descending", "time_descending"])
    p.add_argument("--note-type", default="_0", choices=["_0", "_1", "_2"])
    p.set_defaults(func=action_search_notes_v3)

    p = sub.add_parser("search_users", help="搜索用户")
    p.add_argument("--keyword", required=True)
    p.add_argument("--page", type=int, default=1)
    p.set_defaults(func=action_search_users)

    p = sub.add_parser("note_detail", help="获取笔记详情 V1")
    p.add_argument("--note-id", required=True)
    p.add_argument("--format", default=None, choices=[None, "true", "false"])
    p.set_defaults(func=action_note_detail)

    p = sub.add_parser("note_detail_v5", help="获取笔记详情 V5，适合媒体/视频，可能不含互动指标")
    p.add_argument("--note-id", required=True)
    p.set_defaults(func=action_note_detail_v5)

    p = sub.add_parser("note_comments", help="获取笔记评论 V2")
    p.add_argument("--note-id", required=True)
    p.add_argument("--last-cursor", default=None)
    p.add_argument("--sort", default="latest", choices=["normal", "latest"])
    p.set_defaults(func=action_note_comments)

    p = sub.add_parser("note_comments_v4", help="获取笔记评论 V4")
    p.add_argument("--note-id", required=True)
    p.set_defaults(func=action_note_comments_v4)

    p = sub.add_parser("comment_replies", help="获取评论回复 V2")
    p.add_argument("--note-id", required=True)
    p.add_argument("--comment-id", required=True)
    p.add_argument("--last-cursor", default=None)
    p.set_defaults(func=action_comment_replies)

    p = sub.add_parser("user_profile", help="获取用户资料 V3")
    p.add_argument("--user-id", required=True)
    p.set_defaults(func=action_user_profile)

    p = sub.add_parser("user_notes", help="获取用户发布笔记 V4")
    p.add_argument("--user-id", required=True)
    p.add_argument("--last-cursor", default=None)
    p.set_defaults(func=action_user_notes)

    p = sub.add_parser("resolve_share", help="解析分享链接")
    p.add_argument("--share-url", required=True)
    p.set_defaults(func=action_resolve_share)

    p = sub.add_parser("keyword_suggestions", help="关键词建议")
    p.add_argument("--keyword", required=True)
    p.set_defaults(func=action_keyword_suggestions)

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
        print_json(normalize_error(status_code=None, code=None, message=str(exc)))
        sys.exit(1)


if __name__ == "__main__":
    main()
