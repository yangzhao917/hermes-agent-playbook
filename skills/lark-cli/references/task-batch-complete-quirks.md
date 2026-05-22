# 批量完成任务踩坑实录 (2026-05-20)

## 事件

清理 47 个 2025年10月-2026年4月过期任务，以为已全部标记完成。5月20日复盘时发现这批任务仍然出现在 `+get-my-tasks` 结果中。

## 根因

之前使用的批量完成命令格式为：
```bash
lark-cli task +complete guid1 guid2 guid3 ...
```
输出显示 `✅ Task completed successfully!`（单个 success），但实际只有**第一个** guid 被处理，后续全部因「positional arguments not supported」被静默跳过。

## 复现

```bash
# 创建测试任务后尝试批量完成
$ lark-cli task +complete \
    799ca352-d277-44d6-9b08-fb79e61bcd73 \
    f2d3acdd-340f-4d38-a25a-92ab80cc7eff \
    1fed1b0e-6ed9-42fa-ba28-dd7ee3c71e33

✅ Task completed successfully!
Task ID: 799ca352-d277-44d6-9b08-fb79e61bcd73
# ← 只处理了第一个，后面全部跳过后才报 success

# 验证：第二个任务并没有被完成
$ lark-cli task +get-my-tasks --query '协商龙祥公寓桶装饮用水押金问题'
# → 仍然出现在未完成列表中
```

## 正确做法

```bash
# ✅ 串行循环，每次单独 --task-id
for guid in $GUids; do
  result=$(lark-cli task +complete --task-id "$guid" 2>&1)
  if echo "$result" | grep -q '"ok": true'; then
    echo "OK: $guid"
  else
    echo "FAIL: $guid — $result"
  fi
done

# ✅ 或者更简洁的版本（适用于少量任务）
lark-cli task +complete --task-id guid1
lark-cli task +complete --task-id guid2
lark-cli task +complete --task-id guid3
```

## 教训

1. **`+complete` 不接受位置参数**，必须用 `--task-id` flag
2. 批量时不要用 `printf | xargs` 管道传给位置参数（会变成位置参数而非 flag）
3. 成功标志是 **`"ok": true`**，不是 `"code": 0`
4. 每次批量操作后**必须用 `tasks list --params '{"completed": true}'` 验证已完成任务**，确认目标 guid 确实消失
