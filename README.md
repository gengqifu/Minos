# Minos

Android 隐私合规扫描工具：支持源码/APK 静态扫描，按法规规则输出 HTML/JSON 报告。规则与扫描均数据驱动，首版默认只接受 PRD 白名单法规链接在线同步。

## 目录
- 快速开始（5 分钟）
- 规则与适配器原理
- 运行扫描
- 规则同步（首版白名单约束）
- 法规文档转换（URL→YAML）
- 输出与报告
- 故障排查
- 相关文档

## 快速开始（5 分钟）
1) 安装依赖（Python 3.10+）：
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) 准备规则（单步 from-url，同步 PRD 白名单法规链接到本地缓存，参数可选且值不区分大小写）：
```bash
# 同步默认法规（gdpr/ccpa/lgpd/pipl/appi 等，使用 PRD 默认链接，version 可选）
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync --from-url --version v1 --cache-dir ~/.minos/rules
# 只同步指定法规（示例：GDPR，省略 URL 自动填充）
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync --from-url --regulation GDPR --version v1 --cache-dir ~/.minos/rules
# 需本地/自定义源时显式开启（仅受控环境）：--allow-local-sources / --allow-custom-sources
```
3) 扫描示例（完整参数，源码 + Manifest + APK，按需删减）：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli scan \
  --mode both \
  --input app/src \                                   # 源码目录，可多次传入
  --manifest app/src/main/AndroidManifest.xml \       # Manifest，可多次传入
  --apk-path app/build/outputs/apk/debug/app-debug.apk \  # 可选 APK
  --regions EU --regulations GDPR \                   # 地区/法规，大小写不敏感；不填法规默认 PRD 列表
  --rules-dir ~/.minos/rules \                        # 规则目录，默认 ~/.minos/rules 或内置兜底
  --rules-version v1 \                                # 规则版本，可选；不填用激活或最新
  --output-dir output/reports \                       # 报告目录
  --report-name full-scan \                           # 报告名前缀
  --format both \                                     # 报告格式：html/json/both
  --threads 4                                         # 并行度，可选
```
4) 查看报告：`output/reports/scan.html` 与 `output/reports/scan.json`。

## 规则与适配器原理
- 规则来源：PRD“法规参考链接”白名单站点（GDPR/CCPA-CPRA/LGPD/PIPL/APPI）；每条规则包含 rule_id、regulation、pattern、severity、recommendation 等。
- 规则驱动：Manifest/SDK 扫描器从 YAML 加载匹配逻辑，硬编码仅兜底且可被 YAML 禁用/覆盖。
- 站点适配器：通用框架 + 站点适配器将 HTML/PDF 正文条款拆分为规则 YAML；不使用 LLM。
- 语言策略：默认英文，不支持则使用页面默认语言；扫描基于模式匹配，不做语义理解。

## 运行扫描
- 全量示例（源码 + Manifest + APK）：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli scan \
  --mode both \
  --input app/src \
  --manifest app/src/main/AndroidManifest.xml \
  --apk-path app/build/outputs/apk/debug/app-debug.apk \
  --regions EU --regulations GDPR \
  --rules-dir ~/.minos/rules --rules-version v1 \
  --output-dir output/reports --report-name full-scan \
  --format both --threads 4
```
- 只扫源码：`--mode source --input <src>`；可去掉 `--manifest/--apk-path`。
- 只扫 APK：`--mode apk --apk-path <apk>`。
- 常用参数：`--format html|json|both`，`--output-dir` 报告目录，`--report-name` 前缀，`--log-file`/`--log-level` 日志。
- 规则加载：默认从缓存 `~/.minos/rules/<reg>/<version>/rules.yaml` 加载（参数值大小写不敏感，未指定法规默认使用 PRD 列表）；可用 `--rules-dir` 覆盖规则目录，`--rules-version` 选定版本；规则/缓存缺失会报错并返回非零。  

## 规则同步（首版白名单约束，参数值不区分大小写）
- 单步命令：`minos rulesync --from-url [--regulation <reg>] [--version <ver>] [--allow-local-sources] [--allow-custom-sources]`。URL 可省略，未指定 regulation 时默认同步 PRD 法规参考链接中的全部法规（gdpr/ccpa/cpra/lgpd/pipl/appi），reg/version 大小写不敏感。  
- 默认仅允许 PRD 白名单域名（eur-lex、leginfo、planalto、cac.gov.cn、ppc.go.jp 等）在线同步。  
- 本地文件/自定义源默认禁用：测试/开发可显式添加 `--allow-local-sources`（本地包/导入 YAML）或 `--allow-custom-sources`（非白名单在线源）。  
- 回滚/清理示例：
```bash
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync --from-url --version v1 --cache-dir ~/.minos/rules
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync <source> v1.1.0 --cache-dir ~/.minos/rules --rollback-to v1.0.0
PYTHONPATH=src .venv/bin/python -m minos.cli rulesync <source> v1.2.0 --cache-dir ~/.minos/rules --cleanup-keep 2
```

## 法规文档转换（URL/本地 HTML/PDF → YAML）
- 支持站点：GDPR（eur-lex）、CCPA/CPRA（leginfo）、LGPD（planalto）、PIPL（cac.gov.cn）、APPI（ppc.go.jp）；仅抽取正文条款，未支持站点直接失败。
- URL 转 YAML：
```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from minos import rulesync_convert
rulesync_convert.convert_url_to_yaml(
    url="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5",
    cache_dir=Path("~/.minos/cache").expanduser(),
    out_path=Path("output/ccpa_rules.yaml"),
    regulation="ccpa",
    version="1.0.0",
)
PY
```
- 本地 HTML/PDF 转 YAML（导入时需 `--allow-local-sources`）：
```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from minos import rulesync_convert
rulesync_convert.convert_files_to_yaml(
    inputs=[Path("docs/gdpr.html"), Path("docs/gdpr.pdf")],
    out_path=Path("output/gdpr_rules.yaml"),
    source_url="file://docs/gdpr.html",
    regulation="gdpr",
    version="1.0.0",
)
PY
```

## 输出与报告
- 默认输出目录：`output/reports`。
- 报告字段：findings（rule_id、regulation、source、severity、location、evidence、recommendation），stats（按法规/严重级别计数），meta（输入、时间、规则版本）。
- HTML/JSON 同步生成，stdout 输出扫描摘要（命中计数、报告路径）。

## 故障排查
- “本地源被禁用”：加 `--allow-local-sources`；在线非白名单源需 `--allow-custom-sources`。
- “未找到规则/版本”：检查 rulesync 缓存目录与版本号，或重新同步；可用 `--rollback-to` 回滚。
- “缺少依赖”：安装 `PyYAML`；使用 OCI 源需安装 `oras`，git 源需安装 `git`。
- “无网/受限”：先在有网环境准备缓存，离线模式使用 `--offline`（需已有缓存）。

## 相关文档
- CI 示例：`ci/README.md`
- 容器使用：`containers/README.md`
- 变更记录：`CHANGELOG.md`
- 测试清单：`tests/test-cases.md`
