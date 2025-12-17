# CI 工作流示例说明

## 目录结构

- `github-actions/minos-scan.yml`：GitHub Actions 示例，包含本地 Python 与容器两种作业，上传 HTML/JSON 报告和日志工件。
- `gitlab-ci/minos-scan.yml`：GitLab CI 示例，包含 `scan_local`（python:3.10-slim）与 `scan_container`（docker dind）两个 job，上传 HTML/JSON 报告和日志工件。
- `tests/ci_workflow_smoke.sh`：本地/容器模拟 CI 的验收脚本，覆盖源码、源码+APK、缺少输入失败的场景。
- `fixtures/`：CI 示例用的输入样例（源码与占位 APK）。

## 使用指南

- **复制/包含**：将对应 YAML 复制到目标仓库（GitHub: `.github/workflows/`；GitLab: `.gitlab-ci.yml` 或 include），按项目路径调整输入/输出参数。
- **可调参数（env）**：`MINOS_INPUT_SRC`、`MINOS_APK_PATH`、`MINOS_REGIONS`、`MINOS_REGULATIONS`、`MINOS_OUTPUT_DIR`、`MINOS_LOG_DIR`、`MINOS_FORMAT_LOCAL`/`MINOS_FORMAT_CONTAINER`、`MINOS_LOG_LEVEL`、`MINOS_RULE_CACHE`。
- **缓存与工件**：两套示例均支持规则缓存目录（GitHub 用 actions/cache，GitLab 用 cache），默认上传 `${MINOS_OUTPUT_DIR}/*.json|*.html` 与 `${MINOS_LOG_DIR}/*.log`。
- **依赖与镜像**：需要 `requirements.txt` 与 `containers/Dockerfile`（若启用容器 job）；若不需要容器 job 可删除相关步骤。
- **受限/离线**：提前在宿主机执行 `minos rulesync ... --cache-dir ~/.minos/rules --offline` 准备规则缓存（可放置在制品库或预置在 Runner），CI 中通过挂载/缓存 `MINOS_RULE_CACHE` 目录复用，避免在线下载。
- **规则同步策略（推荐）**：CI 过程中不执行 `rulesync`，而是在 CI 外部（定时/人工）更新缓存；CI 只使用缓存运行扫描，降低不稳定与延迟风险。
- **日志与摘要**：CLI 默认 stdout 输出风险计数和报告路径（形如 `findings=0 ... reports=[...]`），适合作为流水线日志观测；同时通过 `--log-file "${MINOS_LOG_DIR}/..."` 生成可上传的文件日志以便调试。
- **退出码约定**：成功扫描返回 0；缺少输入、参数错误等配置/运行错误返回非零（示例脚本会在缺少 APK 时断言失败并不产出报告）；存在风险不视为错误，不会导致退出非零（无阻断策略）。

## 本地验证

- GitHub/GitLab 脚本均可用 `./ci/tests/ci_workflow_smoke.sh` 先行验收，确保报告/日志与退出码符合预期。
- 没有 gitlab-runner 时，可直接运行脚本中的命令（或 README 的说明）模拟各 job。 
