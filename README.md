# Minos
一个扫描Android APP是否违反特定隐私合规规范的程序

## 使用示例

### rulesync 同步/回滚/清理

- 本地同步规则包（校验 SHA256，并设置激活版本）：
  ```bash
  PYTHONPATH=src .venv/bin/python -m minos.cli rulesync ./rules-v1.0.0.tar.gz v1.0.0 --sha256 <digest> --cache-dir ~/.minos/rules
  ```
- 离线使用缓存：
  ```bash
  PYTHONPATH=src .venv/bin/python -m minos.cli rulesync ./rules-v1.0.0.tar.gz v1.0.0 --sha256 <digest> --cache-dir ~/.minos/rules --offline
  ```
- 回滚到指定版本：
  ```bash
  PYTHONPATH=src .venv/bin/python -m minos.cli rulesync ./rules-v1.1.0.tar.gz v1.1.0 --cache-dir ~/.minos/rules --rollback-to v1.0.0
  ```
- 同步后清理旧版本（仅保留最新 2 个）：
  ```bash
  PYTHONPATH=src .venv/bin/python -m minos.cli rulesync ./rules-v1.2.0.tar.gz v1.2.0 --sha256 <digest> --cache-dir ~/.minos/rules --cleanup-keep 2
  ```

说明：
- 成功退出码=0，校验失败=2，其他失败=1。
- 输出包含同步/回滚结果与当前激活规则路径。

### 地区→法规选择（映射/手动）

- CLI/配置示例：
  ```json
  {
    "regions": ["EU", "US-CA"],
    "manual_add": ["LGPD"],
    "manual_remove": []
  }
  ```
- 产出供扫描/报告使用的字段（示意）：
  ```json
  {
    "regions": ["EU", "US-CA"],
    "regulations": ["CCPA/CPRA", "LGPD"],
    "source_flags": {
      "CCPA/CPRA": "region",
      "LGPD": "manual"
    },
    "summary": {
      "regions": ["EU", "US-CA"],
      "regulations": ["CCPA/CPRA", "LGPD"]
    }
  }
  ```

### 验收用例（rulesync）

- 拉取成功：校验通过，metadata 写入版本/来源/sha256/gpg/时间戳，active=true，退出码=0。  
- 校验失败：故意传错 sha256，退出码=2，不写入 active 版本。  
- 离线使用缓存：offline 模式且缓存存在，退出码=0；若缓存不存在则失败。  
- 回滚：存在多个版本时回滚到上一或指定版本，active 指向目标版本。  
- 清理缓存：`--cleanup-keep N` 后仅保留最新 N 个版本。  
- 切换版本：同步新版本激活，旧版本仍在缓存列表。  
- 缺少输入/源不存在：退出码=1，提示错误。  
- CLI 摘要输出：包含同步/回滚结果与当前激活路径，便于 CI 收集。

### 验收用例（地区→法规映射）

- 单地区：EU -> 输出 {GDPR}，source_flags=region。  
- 多地区并集：[EU, US-CA] -> 输出 {GDPR, CCPA/CPRA}，source_flags 对应地区。  
- 手动添加/移除：在映射结果上 add/remove，最终集合与 source_flags=manual 准确。  
- 配置读取：JSON config 读写一致（regions/manual_add/manual_remove），非法配置报错。  
- 无效输入：非法地区抛出明确错误；缺省输入需提示。  
- 输出字段：包含 regions/regulations/source_flags/summary，供扫描器/报告使用。

### 验收用例（Manifest 扫描）

- 敏感权限命中：包含 ACCESS_FINE_LOCATION 命中对应规则，source 透传。  
- 导出组件命中：exported=true 的 activity/service/provider 未保护时命中，source 透传。  
- 未命中：合规配置下 findings 为空，stats 为零。  
- 规则缺失/非法规则：给出清晰错误或空结果，退出码/日志符合预期。  
- 非法 manifest：解析失败抛出 ManifestScanError，退出码非零。  
- stats：按 regulation/severity 汇总计数，与 findings 对应。

### 例行命令（Manifest 扫描示例）

- 直接扫描 manifest 文件：
  ```bash
  PYTHONPATH=src .venv/bin/python -c "from minos import manifest_scanner; from pathlib import Path; import json; rules=[{'rule_id':'PERM_SENSITIVE_LOCATION','type':'permission','pattern':'android.permission.ACCESS_FINE_LOCATION','regulation':'PIPL','severity':'high'}]; print(manifest_scanner.scan_manifest(Path('AndroidManifest.xml'), rules, {'PERM_SENSITIVE_LOCATION':'region'}))"
  ```
- 扫描目录（自动查找 AndroidManifest.xml，含 src/main）：
  ```bash
  PYTHONPATH=src .venv/bin/python -c "from minos import manifest_scanner; from pathlib import Path; import json; rules=[{'rule_id':'EXPORTED_ACTIVITY','type':'component','component':'activity','regulation':'GDPR','severity':'high'}]; print(manifest_scanner.scan_manifest(Path('app'), rules, {'EXPORTED_ACTIVITY':'region'}))"
  ```
- 扫描 APK（读取包内 manifest，假设可解析 XML）：
  ```bash
  PYTHONPATH=src .venv/bin/python -c "from minos import manifest_scanner; from pathlib import Path; import json; rules=[{'rule_id':'EXPORTED_ACTIVITY','type':'component','component':'activity','regulation':'GDPR','severity':'high'}]; print(manifest_scanner.scan_manifest(Path('app-release.apk'), rules, {'EXPORTED_ACTIVITY':'region'}))"
  ```

### 容器运行（占位示例）

- 入口脚本：`containers/entrypoint.sh`（默认调用 `python -m minos.cli`）。  
- 运行示例：
  ```bash
  docker run --rm \
    -v "$PWD":/work -w /work \
    -v "$HOME/.minos/rules":/root/.minos/rules \
    minos:latest \
    minos scan --mode apk --apk-path app-release.apk --output-dir output/reports
  ```
- 受限/无网：提前在宿主机执行 rulesync 缓存规则，再挂载 `~/.minos/rules` 供容器使用。  

### 本地运行 CLI 扫描（示例）

- 安装依赖后（如使用 `.venv`）：  
  ```bash
  PYTHONPATH=src .venv/bin/python -m minos.cli scan \
    --mode source \
    --input app/src \
    --output-dir output/reports \
    --format both \
    --regions EU --regulations GDPR
  ```
- APK 模式：  
  ```bash
  PYTHONPATH=src .venv/bin/python -m minos.cli scan \
    --mode apk \
    --apk-path app-release.apk \
    --output-dir output/reports \
    --format json
  ```
- 行为与容器运行一致：报告路径/格式、stdout 摘要字段相同；缺少输入时返回非零并提示。
- 输出路径：默认写入 `output/reports/{scan.json,scan.html}`（可通过 `--output-dir`/`--report-name` 覆盖）；日志可选 `--log-file`（支持轮转）。
- 受限网络提示：提前执行 `minos rulesync ... --cache-dir ~/.minos/rules --offline` 缓存规则，再在离线环境使用。
