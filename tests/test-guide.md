# Minos 黑盒测试指南

本指南面向功能测试工程师，目标是帮助你从 0 开始验证 Minos 的核心能力与边界行为。

## 1. 测试目标与范围

覆盖以下能力：
- rulesync：本地/远端同步、from-url 默认映射/全量同步、白名单拒绝与开关放开、校验、离线、回滚、清理、超时与错误提示。
- scan：源码/APK/both 扫描、报告输出、日志输出、退出码；从规则缓存/自定义 `--rules-dir` 加载规则，未指定法规默认 PRD 全量，参数值不区分大小写，缺规则/缓存报错。
- 报告：JSON/HTML 产出与基础字段可读性。
- CI 集成：GitHub/GitLab 示例与 smoke 验收脚本。
- 容器：构建镜像、容器内扫描与 rulesync。

不在范围（如需可扩展）：
- 规则质量与实际风险准确性（规则内容验证）。
- 性能压测与超大规模项目压力测试。

## 2. 环境准备

- 本地 Python 环境（建议使用项目 README 的 venv 方式）。
- 可执行命令：若未安装 `minos` 命令，可用 `PYTHONPATH=src .venv/bin.python -m minos.cli ...`。
- Docker（用于容器测试）。
- 可选依赖（远端拉取时）：`git` / `oras`。
- CLI 参数值大小写不敏感（reg/regulation/regions/version 等统一按小写解析）。

## 3. 测试数据准备

- 源码样例目录：可使用本仓库 `ci/fixtures/source`。
- APK 样例：可使用 `ci/fixtures/dummy.apk`（占位）。
- 规则包：
  - from-url：使用 PRD 白名单默认链接（gdpr/ccpa/lgpd/pipl/appi），可选指定 regulation/version；本地/自定义源需显式开关。
  - 本地 tar.gz（需 `--allow-local-sources`）。
  - 远端 HTTP/git/OCI（需 `--allow-custom-sources`，可用内网或测试仓库）。
- 规则目录：默认 `~/.minos/rules/<reg>/<ver>/rules.yaml`，可用 `--rules-dir` 指定自定义目录（容器内默认 `/root/.minos/rules`）；参数值大小写不敏感。

## 4. 测试方法与策略

- 以黑盒方式执行 CLI 命令，观察退出码、输出报告、日志内容。
- 先跑 P0 核心路径（scan、rulesync 基本成功/失败），再覆盖边界场景。
- 远端场景优先在可控测试仓库验证，避免公网不稳定因素。

## 5. 执行流程建议

1) rulesync：优先验证 from-url 默认映射/全量同步（白名单），再覆盖非白名单拒绝与开关放开、本地包/导入 YAML（需开关）、回滚/清理/离线。  
2) scan：验证源码/APK/both 的扫描与报告产出；覆盖默认缓存加载、自定义 `--rules-dir`、缺规则/缓存报错、大小写不敏感、禁用/覆盖规则生效。  
3) 报告/日志：检查 JSON/HTML 与日志输出。  
4) CI：运行 `ci/tests/ci_workflow_smoke.sh`。  
5) 容器：构建镜像并在容器内执行 scan/rulesync。

## 6. 通过标准

- CLI 退出码符合约定：成功=0；输入缺失/参数错误/白名单拒绝/未开关本地源=非零。  
- 报告文件实际生成且内容可打开/可解析。  
- 日志包含摘要与失败原因。  
- 缓存隔离与覆盖策略符合预期（同法规不混淆、旧版可清理）。

## 7. 风险与注意事项

- 远端拉取依赖网络，需控制超时与重试次数；默认仅接受 PRD 白名单域名。
- CI 中不建议运行 rulesync，建议外部使用 from-url 单步准备缓存。
- 容器内远端拉取需安装 git/oras，并注意证书与代理；默认拒绝非白名单/本地源，需开关显式放开。  
