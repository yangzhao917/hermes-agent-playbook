# 网络与代理运维

## 定位

AgentOS 的部分能力依赖服务器稳定访问 GitHub、模型服务、搜索源和海外内容源。网络与代理方案的目标不是让所有流量都走代理，而是在必要时保证关键自动化链路可用。

当前保留的通用方案是 Cloudflare WARP。它适合处理云服务器出口访问受限、GitHub 或海外站点连接失败、搜索源访问不稳定等问题。

## 使用边界

WARP 属于运行保障能力，不属于 AgentOS 的产品核心能力。

适合使用 WARP 的场景：

- GitHub clone、pull、push 或 release 下载不稳定。
- 海外模型服务、搜索源、文档站点访问失败。
- 服务器出口 IP 被目标站点限制，导致请求失败。

不建议长期无差别依赖 WARP 的场景：

- 飞书、腾讯云、国内 API 等国内服务访问。
- 对源 IP 稳定性敏感的业务。
- 需要严格审计出站路径的生产任务。

## 安装与连接

Ubuntu 服务器可按 Cloudflare 官方源安装：

```bash
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-warp.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-warp.list
sudo apt update
sudo apt install -y cloudflare-warp
```

注册并连接：

```bash
warp-cli register
warp-cli connect
warp-cli status
sudo systemctl enable --now warp-svc
```

断开：

```bash
warp-cli disconnect
warp-cli status
```

## 验证

确认 WARP 状态：

```bash
warp-cli status
```

确认出口网络：

```bash
curl -s --noproxy '*' https://ipinfo.io
```

验证目标站点：

```bash
curl -s --noproxy '*' https://github.com -o /dev/null -w "%{http_code}\n"
curl -s --noproxy '*' https://x.com -o /dev/null -w "%{http_code}\n"
```

## 排障

检查服务状态：

```bash
systemctl status warp-svc
journalctl -u warp-svc -n 50
```

检查网络接口：

```bash
ip addr show CloudflareWARP
resolvectl status CloudflareWARP
```

重连：

```bash
warp-cli disconnect && warp-cli connect
```

检查端口冲突：

```bash
ss -tlnp | grep 7890
```

## 风险

- WARP 可能改变服务器出口 IP，导致部分国内服务风控或访问异常。
- DNS 行为可能变化，需要单独验证飞书、模型服务、GitHub 等关键链路。
- 不应把 WARP 当成长期产品依赖；如果某个能力必须依赖 WARP 才可用，应在复盘中记录为运行风险。

## 文档边界

本文件只记录通用网络运维方法。账号、服务器 IP、私有网络配置和真实故障记录不进入仓库，应放在私有运维记录中。
