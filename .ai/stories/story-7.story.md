# Epic-N - Story-1
# 动态流量与运行时检测预研（Frida/mitmproxy 接口预留）

**As a** 合规/安全研究员  
**I want** 预研动态检测方案（Frida Hook 与 mitmproxy 流量抓取）的接口与集成路径  
**so that** 为后续版本提供可插拔的运行时与流量检测能力

## Status

Approved

## Context

- Epic-N 为后续迭代，当前仅做预研与接口定义，不在首版发布范围。  
- 目标：界定可插拔的运行时（Frida/Xposed）与流量检测（mitmproxy/pcap）接口，定义输出格式与与静态结果的合并策略。  
- 需与 PRD 的规则数据驱动、报告字段、日志要求保持一致；不破坏现有 CI 流程（可放 nightly 或独立任务）。

## Estimation

Story Points: 1

## Tasks

1. - [ ] 设计预研用例（TDD 先行，偏设计验收）  
   1. - [ ] 覆盖：Frida Hook 输出格式、mitmproxy 流量标签、与静态 findings 合并、错误与超时处理  
   2. - [ ] 断言：接口返回 schema、合并后报告字段一致性、退出码与日志规范  
2. - [ ] 实现测试用例/样例（自动化或可运行样例）  
   1. - [ ] 提供 schema 校验、合并逻辑的自动化测试或可运行样例（含动态/静态合并）  
   2. - [ ] 覆盖错误/超时/无输出等场景的断言  
3. - [ ] 定义动态检测插件接口  
   1. - [ ] 插件元数据（名称、版本、支持的 hook/流量类型）  
   2. - [ ] 输入/输出 schema（与静态 findings 兼容：rule_id/位置/证据/严重级别/来源标记）  
   3. - [ ] 生命周期与运行模式（nightly/独立 CI job），超时与失败策略  
4. - [ ] 预研 Frida 集成路径  
   1. - [ ] 如何注入/启动 Frida server、脚本示例、常见反调试绕过思路（记录，不实现）  
   2. - [ ] Hook 重点：敏感 API 调用、标识收集、出网目标；输出映射到 findings 格式  
5. - [ ] 预研 mitmproxy/流量捕获路径  
   1. - [ ] 代理/证书注入、受 TLS Pinning 影响的绕过思路（记录，不实现）  
   2. - [ ] PII/ID/域名识别规则与标签；输出映射到 findings 格式  
6. - [ ] 合并与报告策略  
   1. - [ ] 动态 findings 与静态 findings 的合并规则（去重、优先级、来源标记=dynamic）  
   2. - [ ] 报告新增字段：检测类型（static/dynamic）、时间戳、会话 ID（可选）  
7. - [ ] 文档与验收  
   1. - [ ] 预研结论文档：接口定义、样例输出、限制与风险（反调试、证书校验、自动化成本）  
   2. - [ ] 验收：接口 schema 评审通过，样例输出与合并策略明确

## Constraints

- 不在首版交付范围，不破坏现有 CI 路径；可作为 nightly/独立任务。  
- 不上传业务数据；预研输出仅为接口定义与样例。  
- 与现有报告/日志/规则格式兼容（字段一致）。

## Data Models / Schema

- 动态检测输出示例：

```json
{
  "type": "dynamic",
  "source": "frida",
  "rule_id": "RUNTIME_ID_ACCESS",
  "regulation": "GDPR",
  "severity": "medium",
  "location": "com.example.MainActivity#getDeviceId()",
  "evidence": "IMEI accessed at runtime",
  "timestamp": "2024-01-01T00:00:00Z",
  "session": "run-001"
}
```

## Structure

- `dynamic/interfaces/`：插件接口与 schema 定义  
- `dynamic/samples/`：示例 Frida/mitmproxy 输出  
- `docs/dynamic-prestudy.md`：预研结论与限制

## Diagrams

```mermaid
flowchart TD
    HOOK["Frida/Hook 脚本"] --> DYN["动态 findings (runtime)"]
    PROXY["mitmproxy/pcap"] --> DYN
    DYN --> MERGE["合并器 (静态+动态)"]
    MERGE --> REPORT["报告生成 (标注检测类型)"]
```

## Dev Notes

- 聚焦接口与格式，不落实现码；记录绕过与限制，作为后续开发参考。  
- TDD：以 schema/合并逻辑的测试与样例输出作为验收基线。

## Chat Command Log

- User: 生成下一个 story  
- Assistant: 起草 Epic-N Story-1（动态流量与运行时检测预研）草稿
