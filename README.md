# Minos

一个扫描 Android APP 是否违反特定隐私合规规范的程序，支持源码/APK 静态扫描并输出 HTML/JSON 报告。

## 快速开始

1) 安装依赖（Python 3.10+）：
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) 同步规则（当前实现使用本地规则包；在线同步能力在开发中）：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync ./rules-v1.0.0.tar.gz v1.0.0 --sha256 <digest> --cache-dir ~/.minos/rules
```

3) 扫描（源码示例）：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli scan \
  --mode source \
  --input app/src \
  --output-dir output/reports \
  --format both \
  --regions EU --regulations GDPR
```

4) 查看报告：`output/reports/scan.html` 与 `output/reports/scan.json`。

## 基本原理

- 规则数据驱动：规则以 YAML/JSON 管理，可同步/缓存并在扫描时加载。
- 扫描管线：解析输入（源码/Manifest/APK）→ 匹配规则 → 汇总 findings/stats。
- 报告输出：生成 HTML+JSON，stdout 输出摘要（风险计数与报告路径）。

## 常见使用场景

### 本地运行（源码/APK）
- 源码扫描：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli scan \
  --mode source --input app/src --output-dir output/reports --format both
```
- APK 扫描：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli scan \
  --mode apk --apk-path app-release.apk --output-dir output/reports --format json
```

### 容器运行
- 参考 `containers/README.md`。

### CI 集成
- 参考 `ci/README.md`（GitHub Actions/GitLab CI 示例）。

## 规则同步（rulesync）

- **离线缓存**：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync ./rules-v1.0.0.tar.gz v1.0.0 \
  --sha256 <digest> --cache-dir ~/.minos/rules --offline
```
- **回滚/清理**：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync ./rules-v1.1.0.tar.gz v1.1.0 \
  --cache-dir ~/.minos/rules --rollback-to v1.0.0

PYTHONPATH=src .venv/bin/python -m minos.cli rulesync ./rules-v1.2.0.tar.gz v1.2.0 \
  --sha256 <digest> --cache-dir ~/.minos/rules --cleanup-keep 2
```
- **在线同步（规划中）**：PRD 要求支持按法规子集同步与法规隔离缓存；当前实现仍使用本地规则包路径。

## 报告与输出

- 输出目录默认：`output/reports`（可用 `--output-dir` 覆盖）。
- 输出格式：`--format html|json|both`。
- 日志：`--log-file output/logs/scan.log` 可输出文件日志。

## 相关文档

- CI 示例与推荐流程：`ci/README.md`
- 容器使用说明：`containers/README.md`
- 动态检测预研（接口/样例）：`docs/dynamic-prestudy.md`
- 变更记录：`CHANGELOG.md`
- 验收用例与详细测试清单：`docs/acceptance.md`
