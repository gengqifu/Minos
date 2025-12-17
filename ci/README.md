# CI 工作流示例说明

本文件面向“第一次接入 Minos CI”的用户，目标是：复制示例、改少量参数、跑通流水线并拿到报告。

## Minos 在 CI 中做什么

- 输入：源码目录和/或 APK。
- 输出：HTML/JSON 报告与日志文件。
- 失败策略：缺少输入/参数错误返回非零；发现风险不视为失败（不会阻断流水线）。

## Quick Start（最小可运行）

### GitHub Actions

1) 复制 `github-actions/minos-scan.yml` 到目标仓库 `.github/workflows/minos-scan.yml`。  
2) 修改环境变量（至少设置输入路径）：

```yaml
env:
  MINOS_INPUT_SRC: app/src
  MINOS_OUTPUT_DIR: output/reports
  MINOS_LOG_DIR: output/logs
```

3) 提交后触发 workflow，期望产出：`output/reports/*.json|*.html` 与 `output/logs/*.log`。

### GitLab CI

1) 复制 `gitlab-ci/minos-scan.yml` 到目标仓库，合并进 `.gitlab-ci.yml`。  
2) 修改变量（至少设置输入路径）：

```yaml
variables:
  MINOS_INPUT_SRC: app/src
  MINOS_OUTPUT_DIR: output/reports
  MINOS_LOG_DIR: output/logs
```

3) 触发流水线，期望产出与 GitHub 相同。

## CI 流程（推荐）

1) CI 外部准备规则缓存（定时/人工）。  
2) CI 中读取缓存并执行 `minos scan`。  
3) 产出报告与日志工件。

> 建议：CI 过程中不执行 `rulesync`，避免网络不稳定与延迟。

## 目录结构

- `github-actions/minos-scan.yml`：GitHub Actions 示例，包含本地 Python 与容器两种作业，上传 HTML/JSON 报告和日志工件。
- `gitlab-ci/minos-scan.yml`：GitLab CI 示例，包含 `scan_local`（python:3.10-slim）与 `scan_container`（docker dind）两个 job，上传 HTML/JSON 报告和日志工件。
- `tests/ci_workflow_smoke.sh`：本地/容器模拟 CI 的验收脚本，覆盖源码、源码+APK、缺少输入失败的场景。
- `fixtures/`：CI 示例用的输入样例（源码与占位 APK）。

## 配置参数

### 必填/常用

- `MINOS_INPUT_SRC`：源码路径（示例：`app/src`）。
- `MINOS_APK_PATH`：APK 路径（示例：`app-release.apk`）。
- `MINOS_OUTPUT_DIR`：报告输出目录（默认 `output/reports`）。
- `MINOS_LOG_DIR`：日志输出目录（默认 `output/logs`）。

### 可选

- `MINOS_REGIONS` / `MINOS_REGULATIONS`：地区/法规过滤。
- `MINOS_FORMAT_LOCAL` / `MINOS_FORMAT_CONTAINER`：报告格式（`json|html|both`）。
- `MINOS_LOG_LEVEL`：日志级别（`info|debug|warn|error`）。
- `MINOS_RULE_CACHE`：规则缓存目录（建议映射/缓存该目录）。

## 输出与验收

- 报告输出：`$MINOS_OUTPUT_DIR/*.json` 与 `*.html`。  
- 日志输出：`$MINOS_LOG_DIR/*.log`。  
- 成功判定：命令退出码为 0，日志中包含 `reports=[...]`。  
- 失败判定：缺少输入/参数错误返回非零。

## 缓存与更新策略（推荐）

- CI 中不运行 `rulesync`，避免网络不稳定与时延。  
- 规则缓存由 CI 外部更新（定时任务或人工执行 `minos rulesync`）。  
- CI 仅挂载/缓存 `MINOS_RULE_CACHE` 目录复用。

## 常见问题

- **缺少输入**：`--input`/`--apk-path` 未配置，命令直接失败。  
- **缓存不可写**：挂载目录权限不足，导致无法写入报告/日志。  
- **容器依赖缺失**：容器 job 需要 `containers/Dockerfile`；若不使用容器可删除相关 job。  
- **规则未更新**：CI 外部未更新缓存，导致规则版本滞后。

## 本地验证

- 运行：`./ci/tests/ci_workflow_smoke.sh` 先行验收，确保报告/日志与退出码符合预期。  
- 没有 `gitlab-runner` 时，可直接运行脚本中的命令模拟各 job。
