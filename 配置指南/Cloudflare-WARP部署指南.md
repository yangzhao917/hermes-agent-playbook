# Cloudflare WARP 方案

## 是什么

Cloudflare WARP 是一个基于 WireGuard 协议的 VPN 隧道服务，将服务器出口 IP 变成 Cloudflare 的 IP（AS13335），从而绕过对腾讯云上海节点（AS45090）的封锁。

典型场景：腾讯云上海服务器无法直接访问 x.com（被 AS45090 出口 IP 黑名单），但 Cloudflare 的 IP 不在黑名单中。

## 工作原理

```
服务器 (10.0.0.12) ──WARP 隧道──> Cloudflare 边缘节点 ──> 目标网站
         ↑                        ↑
   AS45090 封锁            AS13335 干净 IP
```

- WARP 在服务器创建一个虚拟网卡 `CloudflareWARP`（IP: 172.16.0.2）
- 所有流量通过 Cloudflare 节点路由，DNS 也走 Cloudflare 1.1.1.1
- 服务器实际出口 IP 变为 Cloudflare IP 段

## 安装步骤（Ubuntu 24.04）

### 1. 添加官方源并安装

```bash
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-warp.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-warp.list
sudo apt update
sudo apt install -y cloudflare-warp
```

### 2. 注册并连接

```bash
# 注册设备
warp-cli register

# 连接（官方推荐模式）
warp-cli connect

# 验证
warp-cli status  # 应显示 "Connected"
curl -s --noproxy '*' https://ipinfo.io | grep org
# 应输出 "AS13335 Cloudflare, Inc."
```

### 3. 开机自启（systemd）

```bash
sudo systemctl enable --now warp-svc
```

### 4. 断开连接

```bash
warp-cli disconnect
warp-cli status  # 应显示 "Disconnected"
```

## 关键坑点

### 1. DNS 劫持导致域名解析到腾讯云内网
**问题**：`curl --noproxy '*'` 才能直连，但 DNS 仍然被腾讯云劫持，导致 x.com 解析到被封 IP。

**现象**：x.com 直连报 403/307，但 `curl --noproxy '*'` 仍然失败。

**验证**：
```bash
curl -s --noproxy '*' https://x.com -o /dev/null -w "%{http_code}\n"
# 200 = 正常，000 = DNS 失败或超时
```

**解法**：WARP 接管 DNS 后问题消失。如果仍然失败，尝试：
```bash
# 检查 WARP DNS 是否生效
resolvectl status CloudflareWARP
# 确认 172.16.0.2 是 DNS 服务器
```

### 2. x.com / twitter.com 互相重定向导致 curl 取到 301
**现象**：`curl https://x.com` 返回 301 重定向到 `https://twitter.com`

**解法**：加了 `--noproxy '*'` 参数后直连，两边都返回 200：
```
curl -s --noproxy '*' https://x.com -o /dev/null -w "%{http_code}\n"    # 200
curl -s --noproxy '*' https://twitter.com -o /dev/null -w "%{http_code}\n"  # 200
```

### 3. WireGuard 隧道 DNS 可能被腾讯云拦截
**问题**：某些腾讯云节点会拦截 1.1.1.1 的 DNS 请求。

**解法**：WARP 使用 172.16.0.2 作为 DNS，Cloudflare WARP 服务端处理解析，不需要单独的 DNS 策略。

### 4. WARP 会改变默认路由
**问题**：连接 WARP 后，默认路由可能不变，但所有流量都经过 Cloudflare 隧道。

**验证出口 IP**：
```bash
curl -s --noproxy '*' https://ipinfo.io
# 应显示 "org": "AS13335 Cloudflare, Inc."
```

### 5. WARP 和 mihomo 端口冲突
**问题**：如果 mihomo 也监听 7890 端口，可能会冲突。

**解法**：确保 mihomo 已删除或端口不同：
```bash
ss -tlnp | grep 7890
```

## 提示词模板（解决网络问题）

### 判断是否需要 WARP
```
检查服务器当前出口 IP 和 AS 号：
curl -s --noproxy '*' https://ipinfo.io

如果 AS45090（腾讯云），且 x.com / github.com 连接失败，
则需要安装 WARP。

验证目标网站是否可达：
curl -s --noproxy '*' https://目标网站 -o /dev/null -w "%{http_code}\n"
```

### 安装 WARP 后验证
```
# 1. 确认 WARP 连接状态
warp-cli status

# 2. 确认出口 IP 变为 Cloudflare
curl -s --noproxy '*' https://ipinfo.io | grep org

# 3. 验证 x.com 可访问
curl -s --noproxy '*' https://x.com -o /dev/null -w "%{http_code}\n"

# 4. 验证 GitHub 可访问
curl -s --noproxy '*' https://github.com -o /dev/null -w "%{http_code}\n"
```

### 排查 WARP 不生效
```
# 检查 WARP 接口是否存在
ip addr show CloudflareWARP

# 检查 WARP 服务状态
systemctl status warp-svc

# 手动重连
warp-cli disconnect && warp-cli connect

# 查看 WARP 日志
journalctl -u warp-svc -n 50
```

## 已知限制

| 场景 | 是否可用 |
|------|----------|
| x.com / twitter.com | ✅ |
| github.com | ✅ |
| youtube.com | ✅ |
| 小红书（国内 CDN） | ⚠️ 可能被 Cloudflare IP 拦截 |
| 国内服务（百度等） | ⚠️ 可能有意外行为（走国际出口） |

**建议**：WARP 只用于访问海外被封服务，国内流量不要走 WARP。

## 相关文件

- WARP 配置目录：`/var/lib/cloudflare-warp/`
- warp-svc systemd 服务：`/lib/systemd/system/warp-svc.service`
- Notes: `/home/ubuntu/.hermes/notes/`
