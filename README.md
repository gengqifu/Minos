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
- **远端同步（HTTP）**：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync https://example.com/rules.tar.gz v1.0.0 \
  --sha256 <digest> --cache-dir ~/.minos/rules
```
- **远端同步（git/OCI）**：需要本地安装 `git` 或 `oras`，支持 `#path=` 指定制品路径。
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync \
  git+https://example.com/rules.git#path=dist/rules.tar.gz v1.0.0 --cache-dir ~/.minos/rules

PYTHONPATH=src .venv/bin/python -m minos.cli rulesync \
  oci://example.com/minos/rules:1.0.0#path=rules.tar.gz v1.0.0 --cache-dir ~/.minos/rules
```

## 法规文档转换（URL/本地 HTML/PDF → YAML）

- 支持站点：GDPR（eur-lex）、CCPA/CPRA（leginfo）、LGPD（planalto）、PIPL（cac.gov.cn）、APPI（ppc.go.jp）。原文语言保持不变。
- 适配范围：支持 HTML/PDF；仅抽取正文条款，遇目录/附录/付则时停止或跳过；未支持的法规/站点直接失败。
- 将法规页面转换为 YAML：
```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from minos import rulesync_convert

out = rulesync_convert.convert_url_to_yaml(
    url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",   # 或 file://local.html / 本地 PDF 路径
    cache_dir=Path("~/.minos/cache").expanduser(),
    out_path=Path("output/gdpr_rules.yaml"),
    regulation="gdpr",
    version="1.0.0",
)
print("YAML written to", out)
PY
```
- 导入生成的 YAML 到缓存（跳过远程拉取）：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync dummy-source 1.0.0 \
  --import-yaml output/gdpr_rules.yaml \
  --regulation gdpr --version 1.0.0 --cache-dir ~/.minos/rules
```
- 本地 HTML/PDF 也可直接传入 `convert_files_to_yaml`：
```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from minos import rulesync_convert
out = rulesync_convert.convert_files_to_yaml(
    inputs=[Path("docs/gdpr.html"), Path("docs/gdpr.pdf")],
    out_path=Path("output/gdpr_rules.yaml"),
    source_url="file://docs/gdpr.html",
    regulation="gdpr",
    version="1.0.0",
)
print(out)
PY
```

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
