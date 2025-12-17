# Minos 黑盒测试用例

说明：用例以 CLI 行为为准，关注输入/输出/退出码。若未安装命令行入口，请用 `PYTHONPATH=src .venv/bin/python -m minos.cli` 替代文中的 `minos`。用例内路径与版本可按实际环境调整。

## A. rulesync 规则同步

**RS-01 本地规则包同步成功（P0）**
- 前置：准备本地规则包 `rules-v1.0.0.tar.gz` 与正确 sha256
- 步骤：`minos rulesync ./rules-v1.0.0.tar.gz v1.0.0 --sha256 <digest> --cache-dir ~/.minos/rules`
- 预期：退出码 0；缓存目录有版本目录与 metadata；stdout 含成功信息

**RS-02 校验失败（P0）**
- 步骤：使用错误 sha256
- 预期：退出码非零；不写入缓存

**RS-03 离线使用已有缓存（P0）**
- 前置：已成功同步 v1.0.0
- 步骤：`minos rulesync ./rules-v1.0.0.tar.gz v1.0.0 --offline --cache-dir ~/.minos/rules`
- 预期：退出码 0；提示使用缓存

**RS-04 离线无缓存（P0）**
- 步骤：`minos rulesync ./rules-v1.0.0.tar.gz v1.0.0 --offline --cache-dir ~/.minos/rules`
- 预期：退出码非零；提示缺少缓存

**RS-05 回滚到上一版本（P1）**
- 前置：已同步 v1.0.0 与 v1.1.0
- 步骤：`minos rulesync ./rules-v1.1.0.tar.gz v1.1.0 --rollback-to v1.0.0 --cache-dir ~/.minos/rules`
- 预期：退出码 0；激活版本切换为 v1.0.0

**RS-06 清理旧版本（P1）**
- 前置：已有多个版本
- 步骤：`minos rulesync ./rules-v1.2.0.tar.gz v1.2.0 --cleanup-keep 1 --cache-dir ~/.minos/rules`
- 预期：只保留 1 个最新版本

**RS-07 远端 HTTP 同步成功（P1）**
- 前置：可访问 HTTP 规则包
- 步骤：`minos rulesync https://example.com/rules.tar.gz v1.0.0 --sha256 <digest> --cache-dir ~/.minos/rules`
- 预期：退出码 0；缓存更新

**RS-08 远端 HTTP 超时（P1）**
- 前置：模拟超时或不可达地址
- 步骤：`minos rulesync https://example.com/slow.tar.gz v1.0.0 --timeout 1 --cache-dir ~/.minos/rules`
- 预期：退出码非零；错误提示包含超时

**RS-09 远端 git 同步成功（P1）**
- 前置：容器或本机安装 git，仓库包含规则包
- 步骤：`minos rulesync git+https://example.com/rules.git#path=dist/rules.tar.gz v1.0.0 --cache-dir ~/.minos/rules`
- 预期：退出码 0；缓存更新

**RS-10 远端 OCI 同步成功（P1）**
- 前置：安装 oras，OCI 制品包含规则包
- 步骤：`minos rulesync oci://example.com/minos/rules:1.0.0#path=rules.tar.gz v1.0.0 --cache-dir ~/.minos/rules`
- 预期：退出码 0；缓存更新

**RS-11 远端路径不存在（P1）**
- 步骤：git/oci 传入错误 `#path`
- 预期：退出码非零；错误提示明确路径不存在

**RS-12 多法规参数（P2）**
- 步骤：`minos rulesync <source> <version> --regulations gdpr --regulations ccpa`
- 预期：若支持法规子集，缓存按法规隔离；否则记录为已知限制

## B. scan 扫描

**SC-01 源码扫描（P0）**
- 步骤：`minos scan --mode source --input ci/fixtures/source --output-dir output/reports --format both`
- 预期：生成 JSON/HTML 报告；退出码 0

**SC-02 APK 扫描（P0）**
- 步骤：`minos scan --mode apk --apk-path ci/fixtures/dummy.apk --output-dir output/reports --format json`
- 预期：生成 JSON 报告；退出码 0

**SC-03 源码+APK（P0）**
- 步骤：`minos scan --mode both --input ci/fixtures/source --apk-path ci/fixtures/dummy.apk --format both`
- 预期：报告生成；退出码 0

**SC-04 缺少输入（P0）**
- 步骤：`minos scan --mode source --output-dir output/reports`
- 预期：退出码非零；提示缺少输入

**SC-05 输出格式 JSON/HTML（P1）**
- 步骤：分别设置 `--format json` 与 `--format html`
- 预期：仅生成指定格式

**SC-06 自定义报告名（P1）**
- 步骤：`--report-name smoke`
- 预期：生成 `smoke.json/html`

**SC-07 输出目录不可写（P1）**
- 前置：输出目录无写权限
- 预期：退出码非零；日志提示无法写入

**SC-08 日志输出（P1）**
- 步骤：`--log-file output/logs/scan.log --log-level debug`
- 预期：日志文件生成，包含摘要

## C. 报告与日志

**RP-01 JSON 字段检查（P0）**
- 预期：JSON 包含 `meta/findings/stats` 字段

**RP-02 HTML 可打开（P1）**
- 预期：HTML 能用浏览器打开且包含摘要信息

## D. CI 集成

**CI-01 CI smoke 脚本（P1）**
- 步骤：`./ci/tests/ci_workflow_smoke.sh`
- 预期：源码/源码+APK 产出报告；缺少输入场景失败

## E. 容器运行

**CT-01 构建镜像（P1）**
- 步骤：`docker build -f containers/Dockerfile -t minos:latest .`
- 预期：镜像构建成功

**CT-02 容器内扫描（P1）**
- 步骤：参考 `containers/README.md` Quick Start
- 预期：宿主机输出目录生成报告

**CT-03 容器内 rulesync（P2）**
- 步骤：容器内执行 rulesync（HTTP 或 git/OCI）
- 预期：缓存写入并可复用
