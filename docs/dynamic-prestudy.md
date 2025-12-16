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

## PII/域名标签设计（5.2）

- PII 标签：`pii_tags` 取值示例 `["email", "phone", "idfa", "imei", "android_id"]`，匹配证据写入 `evidence`，location 为 URL/接口。  
- 域名标签：`domains` 字段列出命中的主机（如 `api.example.com`），可供后续域名清单汇总。  
- 规则映射：每个标签对应规则 ID，如 `TRAFFIC_PII_EMAIL`、`TRAFFIC_IDFA_LEAK`，`regulation` 与静态规则保持一致，`severity` 按隐私敏感度设置。  
- 输出示例：见 `dynamic/samples/dynamic_findings.json` 中 mitmproxy 条目，包含 `pii_tags` 与 `domains`，detection_type=dynamic。  
- 错误处理：若无 PII/域名命中，仍可输出空 findings 或 status=error=“no traffic captured”；不得输出空字段导致 schema 破坏。

## 合并与报告策略（6.1）

- 去重键：`rule_id + location + source`，动态/静态并集后去重；动态条目标记 `detection_type=dynamic`，静态为 `static`。  
- 统计：stats 扩展 `count_by_source`（static/frida/mitmproxy…），保持 meta/findings/stats 三段结构与现有报告兼容。  
- 优先级：同一 rule/location 下动态优先于静态展示（保留动态），但不影响总体计数；可在报告中标记 “dynamic_override=true”。  
- 失败策略：合并失败或动态数据缺失时仍输出静态结果，返回码=0；但若输入/解析错误则返回非零并记录 `status=error` 与错误原因。  
- 摘要输出：stdout 摘要应包含 `findings_dynamic`、`findings_static` 计数与报告路径，便于 CI 观察。

## 报告字段扩展（6.2）

- detection_type：`static|dynamic`，标注来源类型，默认静态。  
- timestamp：动态条目需要时间戳，静态可选。  
- session：动态条目需会话 ID；静态可省略。  
- request_id（可选）：流量场景用于定位请求。  
- dynamic_override（可选）：当动态覆盖同一 rule/location 静态条目时标记为 true。  
- 兼容性：保持 meta/findings/stats 三段结构，HTML/JSON 报告共用同一字段集；未使用的扩展字段可为空或缺省，不影响解析。

## TODO/风险

- TLS Pinning 绕过、证书注入方案待与 mitmproxy 预研（见任务 5.x）。  
- 设备兼容性：需测试不同 Android 版本/ABI、root/非 root 场景下 frida-server 可用性。  
- 自动化成本：App 进入目标页面、触发隐私相关操作需脚本或 UI 驱动工具配合。
