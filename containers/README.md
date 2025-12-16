# 容器运行说明（占位）

示例命令：

```bash
# 本地代码/产物挂载到 /work，规则缓存挂载到 /root/.minos/rules，输出到 /work/output
docker run --rm \
  -v "$PWD":/work -w /work \
  -v "$HOME/.minos/rules":/root/.minos/rules \
  minos:latest \
  minos scan --mode apk --apk-path app-release.apk --output-dir output/reports
```

- 入口脚本：`containers/entrypoint.sh`，默认调用 `python -m minos.cli ...`。  
- 无网/受限网络：可提前在宿主机执行 `minos rulesync ...` 将规则缓存到 `~/.minos/rules`，容器挂载后可离线使用。  
- 输出：报告默认写入 `output/reports`（可通过 `--output-dir` 指定）。  

规则缓存挂载约定：
- 默认容器内缓存目录：`/root/.minos/rules`，建议宿主机挂载 `~/.minos/rules:/root/.minos/rules`。  
- 无网/受限网络：先在宿主机执行 `minos rulesync ... --cache-dir ~/.minos/rules --offline`，再运行容器复用缓存。  
- 挂载时请确保宿主目录存在且可写，否则容器可能无法写入缓存。  
