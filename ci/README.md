# CI 工作流示例说明

本文件面向“第一次接入 Minos CI”的用户，目标：复制示例、改少量参数、跑通流水线并拿到报告。

## 前置条件与约束
- Python 3.10+（示例使用 python:3.10-slim 基础镜像）。  
- 规则缓存：首版仅支持 PRD 法规参考链接白名单源（eur-lex/leginfo/planalto/cac.gov.cn/ppc.go.jp）。默认禁用本地/自定义源，若需测试/开发，请在生成缓存时显式加 `--allow-local-sources` 或 `--allow-custom-sources`。  
- CI 推荐不执行 `rulesync`（避免网络抖动）；请在 CI 外部预先准备好规则缓存并挂载至 CI。  
- 示例输入：仓库内 `fixtures/` 提供占位源码/APK，可用于本地或 CI smoke 验证。

## Quick Start（最小可运行）

### GitHub Actions
1) 复制 `github-actions/minos-scan.yml` 到 `.github/workflows/minos-scan.yml`。  
2) 配置最小变量（如使用仓库自带样例）：
```yaml
env:
  MINOS_INPUT_SRC: fixtures/src
  MINOS_OUTPUT_DIR: output/reports
  MINOS_LOG_DIR: output/logs
  MINOS_RULE_CACHE: ~/.minos/rules   # 挂载到缓存目录
```
3) 在触发前，先在有网环境准备好规则缓存并放入 `~/.minos/rules`（CI 任务挂载同路径）。  
4) 提交后触发 workflow，期望产出：`output/reports/*.json|*.html` 与 `output/logs/*.log`。

### GitLab CI
1) 复制 `gitlab-ci/minos-scan.yml`，合并进项目 `.gitlab-ci.yml`。  
2) 配置最小变量：
```yaml
variables:
  MINOS_INPUT_SRC: fixtures/src
  MINOS_OUTPUT_DIR: output/reports
  MINOS_LOG_DIR: output/logs
  MINOS_RULE_CACHE: ~/.minos/rules
```
3) 预先准备规则缓存并挂载/缓存 `MINOS_RULE_CACHE` 目录。  
4) 触发流水线，期望产出同上。

## 推荐 CI 流程
1) CI 外部：从白名单法规链接生成/同步规则包，写入共享缓存目录。  
2) CI 任务：挂载缓存目录，执行 `minos scan`。  
3) 产出报告与日志工件，失败仅因缺参/输入缺失/执行错误；命中风险不阻断流水线。

## 目录结构
- `github-actions/minos-scan.yml`：GitHub Actions 示例，包含本地 Python 与容器两种作业，上传 HTML/JSON 报告和日志工件。  
- `gitlab-ci/minos-scan.yml`：GitLab CI 示例，包含 `scan_local`（python:3.10-slim）与 `scan_container`（docker dind）两个 job。  
- `tests/ci_workflow_smoke.sh`：本地/容器模拟 CI 的验收脚本，覆盖源码、源码+APK、缺少输入失败场景。  
- `fixtures/`：CI 示例用的输入样例（源码与占位 APK）。

## 配置参数速览
必填/常用：
- `MINOS_INPUT_SRC`：源码路径（如 `app/src` 或 `fixtures/src`）。  
- `MINOS_APK_PATH`：APK 路径（如 `app-release.apk` 或 `fixtures/app.apk`）。  
- `MINOS_OUTPUT_DIR`：报告输出目录（默认 `output/reports`）。  
- `MINOS_LOG_DIR`：日志输出目录（默认 `output/logs`）。  
- `MINOS_RULE_CACHE`：规则缓存目录（需预置/挂载）。  

可选：
- `MINOS_REGIONS` / `MINOS_REGULATIONS`：地区/法规过滤。  
- `MINOS_FORMAT_LOCAL` / `MINOS_FORMAT_CONTAINER`：报告格式（`json|html|both`）。  
- `MINOS_LOG_LEVEL`：日志级别（`info|debug|warn|error`）。  

## 输出与验收
- 报告：`$MINOS_OUTPUT_DIR/*.json` 与 `*.html`。  
- 日志：`$MINOS_LOG_DIR/*.log`。  
- 成功判定：`minos scan` 退出码 0，日志含 `reports=[...]`。  
- 失败判定：缺少输入/参数错误/缓存缺失等返回非零。

## 缓存与更新策略
- CI 中不运行 `rulesync`；由外部定时或人工执行 `minos rulesync` 准备缓存。  
- 挂载/缓存 `MINOS_RULE_CACHE`，确保版本一致；需要更新时在外部刷新缓存后再跑 CI。  
- 首版规则源限制：仅 PRD 白名单域名，非白名单或本地源需显式 `--allow-*`，并建议仅在受控环境使用。

## 常见问题与解决
- **缺少输入**：确认 `MINOS_INPUT_SRC`/`MINOS_APK_PATH` 指向存在路径。  
- **规则未加载/版本为空**：检查 `MINOS_RULE_CACHE` 是否挂载、版本目录是否存在。  
- **源被拒绝（白名单/本地禁用）**：生成缓存时显式传 `--allow-local-sources` 或 `--allow-custom-sources`，并仅在受控环境使用。  
- **缓存/输出不可写**：检查挂载目录权限，确保 runner 用户可写。  
- **容器依赖缺失**：使用容器 job 需 `containers/Dockerfile` 与 `docker:dind`，如不需要可删除相关 job。

## 本地与 CI 前置验收
- 运行：`./ci/tests/ci_workflow_smoke.sh`（包含源码、源码+APK、缺少输入失败场景），确认报告/日志/退出码符合预期。  
- 无 gitlab-runner 时，可直接执行脚本中的命令模拟各 job。  
