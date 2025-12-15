# Architecture for Minos 隐私合规扫描程序

Status: Draft

## Technical Summary

Minos 由数据驱动的规则引擎、静态扫描器（源码/APK）、报告生成器和规则同步器组成，通过 CLI/容器在 CI 中运行，输出 HTML/JSON 报告，并记录日志摘要。规则以 YAML/JSON 管理，可从受控仓库拉取更新，支持地区→法规映射与手动增删。

## Technology Table

| Technology | Description |
| ---------- | ----------- |
| Python 3.10+ | 主要编排语言，CLI、规则加载、扫描管线调度、报告生成 |
| Androguard/jadx | APK/DEX/Manifest 静态解析（权限、导出组件、字符串、常量池） |
| Frida/mitmproxy（预留） | 动态检测接口预留，后续迭代启用 |
| Jinja2/模板引擎 | HTML 报告渲染 |
| YAML/JSON | 规则定义、配置与输出格式 |
| Docker/OCI 镜像 | CI/CD 交付形态，便于隔离依赖 |

## Architectural Diagrams

```mermaid
flowchart TD
    CI["CI Job / CLI"] --> CFG["配置参数 (地区/法规/模式)"]
    CI --> RSYNC["规则同步器 (rulesync)"]
    RSYNC --> RULES["本地规则集 (YAML/JSON)"]

    CFG --> PIPE["扫描管线调度"]
    RULES --> PIPE
    SRC["源码输入"] --> PIPE
    APK["APK 输入"] --> PIPE

    PIPE --> MANI["Manifest/权限扫描"]
    PIPE --> SDK["SDK/敏感API/字符串扫描"]
    PIPE --> NET["域名/资源/so 名称扫描"]

    MANI --> AGG["结果汇总"]
    SDK  --> AGG
    NET  --> AGG

    AGG --> REPORT["报告生成器 (HTML/JSON)"]
    AGG --> LOGS["日志输出 stdout+file"]
    REPORT --> OUT1["HTML 报告"]
    REPORT --> OUT2["JSON 报告"]
```

## Data Models, API Specs, Schemas, etc...

### 扫描结果数据模型（简要）

```json
{
  "meta": {
    "target": "app-release.apk",
    "mode": "apk",
    "regions": ["EU", "US-CA"],
    "regulations": ["GDPR", "CCPA/CPRA"],
    "ruleset_version": "v1.0.0",
    "tool_version": "v1.0.0",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "findings": [
    {
      "rule_id": "MANIFEST_EXPORT_001",
      "regulation": "GDPR",
      "region_source": "EU",
      "severity": "high",
      "location": "AndroidManifest.xml:45",
      "evidence": "exported=true component: com.example.ExposedActivity",
      "recommendation": "将组件设为非导出或增加权限保护"
    }
  ],
  "stats": {
    "count_by_severity": {"high": 1, "medium": 0, "low": 0},
    "count_by_regulation": {"GDPR": 1}
  }
}
```

### 核心组件

- 规则同步器（rulesync）：从受控仓库拉取/校验规则包，支持离线缓存与回滚。
- 规则引擎：解析 YAML/JSON 规则，编译匹配器（正则/AST/清单节点等）。
- 静态扫描器：
  - Manifest/权限与导出组件检查
  - SDK/敏感 API/字符串扫描
  - 域名/资源/so 名称轻量分析
- 报告生成器：合成 HTML+JSON 报告，附统计摘要与条款链接；stdout 输出摘要。
- 日志与监控：info/debug/error，文件与 stdout，支持轮转配置。

### 部署/交付

- 本地可直接运行（Python 环境安装依赖后使用 CLI），也可在 CI 通过 Docker/OCI 镜像运行；支持无网模式使用本地规则缓存。
- 预留动态检测插件接口（Frida/mitmproxy），后续迭代可接入。
