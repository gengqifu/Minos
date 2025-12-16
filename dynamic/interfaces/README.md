# 动态检测插件接口（元数据）

## 插件元数据字段

- `name`：插件名称，例如 `frida-runtime-hooks` / `mitmproxy-traffic-tags`。  
- `version`：插件版本号。  
- `type`：`frida` | `mitmproxy` | `pcap` | `xposed` 等。  
- `supports`：支持的检测范围，示例 `["id_access", "network_targets", "pii_tags"]`。  
- `entrypoint`：执行入口或脚本路径（预研阶段仅记录）。  
- `timeout_sec`：建议超时时间。  
- `dependencies`：依赖列表（如 `frida-server>=16`、`mitmproxy>=10`）。  
- `input_schema`：引用的输入 schema（如 `dynamic/interfaces/input_schema.json`），包含目标列表/超时/插件配置。  
- `output_schema`：引用的输出 schema 文件（如 `dynamic/interfaces/output_schema.json`），需与静态 findings 兼容（rule_id/region/severity/location/evidence/detection_type 等）。

## 示例

```json
{
  "name": "frida-runtime-hooks",
  "version": "0.1.0",
  "type": "frida",
  "supports": ["id_access", "network_targets"],
  "entrypoint": "scripts/frida_hooks.js",
  "timeout_sec": 300,
  "dependencies": ["frida-server>=16"],
  "output_schema": "dynamic/interfaces/output_schema.json"
}
```
