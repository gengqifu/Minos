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

### 验收用例（rulesync）

- 拉取成功：校验通过，metadata 写入版本/来源/sha256/gpg/时间戳，active=true，退出码=0。  
- 校验失败：故意传错 sha256，退出码=2，不写入 active 版本。  
- 离线使用缓存：offline 模式且缓存存在，退出码=0；若缓存不存在则失败。  
- 回滚：存在多个版本时回滚到上一或指定版本，active 指向目标版本。  
- 清理缓存：`--cleanup-keep N` 后仅保留最新 N 个版本。  
- 切换版本：同步新版本激活，旧版本仍在缓存列表。  
- 缺少输入/源不存在：退出码=1，提示错误。  
- CLI 摘要输出：包含同步/回滚结果与当前激活路径，便于 CI 收集。
