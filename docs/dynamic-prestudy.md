# 动态检测预研笔记（Frida/mitmproxy）

## Frida 集成要点（4.1）

- 注入/启动：在设备/模拟器启动 `frida-server`（root 或对应 ABI 版本），通过 USB/TCP 连接；脚本示例入口 `scripts/frida_hooks.js`（占位），使用 `Java.perform`/`Interceptor` Hook 目标方法。  
- 反调试绕过：常见检测点= `Debug.isDebuggerConnected`、`ptrace`、`TracerPid`、签名校验/校验证书；可在脚本中重写返回值、NOP 检测函数或劫持 `SSLContext`。  
- Hook 重点：敏感标识读取（IMEI/Android ID/广告 ID）、网络目标（OkHttp/HttpUrlConnection DNS/请求 URL）、位置/传感器调用；输出映射为 `source=frida` 的 dynamic finding（含 timestamp/session）。  
- 超时建议：单次会话设置 `timeout_sec`（如 300s），超时记录 `status=error` 并停止脚本。  
- 运行模式：推荐放 nightly/独立 CI job，不阻塞主流水线；日志写入 stdout+文件，摘要记录 dynamic/static 计数。

## mitmproxy/流量预研（4.2）

- 代理/证书：通过 mitmproxy 生成并注入 CA 证书；对 TLS Pinning 的 App 需配合 Frida 动态绕过（替换 TrustManager/SSLSocketFactory）。  
- 捕获与标签：在 mitmproxy addon 中对请求/响应域名、路径、PII（email/phone/idfa/imei 等）打标签，输出 `source=mitmproxy` 的 dynamic finding（含 `pii_tags`、`domains`、`session`/`request_id`）。  
- TLS Pinning 风险：对强 Pinning 的 SDK/自研客户端，需要 Frida 脚本绕过或使用受信任的证书注入；失败时应记录 status=error 与域名。  
- 运行模式：同样建议独立 job，启动 mitmproxy + App 自动化流转（待后续实现）；超时无流量时返回非零或 status=error，日志记录“无流量”。  
- 输出映射：将域名、PII 标签映射到 findings 字段，location=URL，evidence=匹配片段，detection_type=dynamic，保持与输出 schema 兼容。

## TODO/风险

- TLS Pinning 绕过、证书注入方案待与 mitmproxy 预研（见任务 5.x）。  
- 设备兼容性：需测试不同 Android 版本/ABI、root/非 root 场景下 frida-server 可用性。  
- 自动化成本：App 进入目标页面、触发隐私相关操作需脚本或 UI 驱动工具配合。
