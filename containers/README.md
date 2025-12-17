# 容器运行说明

本文件面向“第一次使用容器运行 Minos”的用户，目标是：构建镜像、跑通一次扫描并拿到报告。

## Minos 在容器中做什么

- 输入：源码目录和/或 APK（通过挂载到容器内）。
- 输出：HTML/JSON 报告与日志文件（写入挂载目录）。
- 失败策略：缺少输入/参数错误返回非零；发现风险不视为失败（不阻断）。

## Quick Start（最小可运行）

### 1) 构建镜像

```bash
# 仓库根目录执行
docker build -f containers/Dockerfile -t minos:latest .
```

### 2) 运行扫描（源码示例）

```bash
docker run --rm \
  -v "$PWD":/work -w /work \
  -v "$HOME/.minos/rules":/root/.minos/rules \
  minos:latest \
  minos scan --mode source --input app/src --output-dir output/reports
```

期望输出：`output/reports/*.json|*.html`。

## 运行流程（建议）

1) 挂载源码/输出目录/规则缓存目录。  
2) 在容器内执行 `minos scan`。  
3) 读取宿主机上的报告与日志。

## 规则缓存与同步

规则缓存挂载约定：
- 容器内缓存目录：`/root/.minos/rules`。  
- 建议宿主机挂载：`~/.minos/rules:/root/.minos/rules`。  
- 挂载时请确保宿主目录存在且可写。

离线复用缓存：
- 无网/受限网络时，先在宿主机执行 `minos rulesync ... --offline` 准备缓存，再在容器内复用。

远端 rulesync（容器内）：
```bash
docker run --rm \
  -v "$PWD":/work -w /work \
  -v "$HOME/.minos/rules":/root/.minos/rules \
  minos:latest \
  minos rulesync https://example.com/rules.tar.gz v1.0.0 \
    --sha256 <digest> --cache-dir /root/.minos/rules
```

git/OCI 规则包：镜像内需安装 `git` 或 `oras`。
```bash
# 自定义镜像示例
FROM minos:latest
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && \
    rm -rf /var/lib/apt/lists/*
# 若需 OCI：安装 oras（根据环境下载对应版本）
```

```bash
docker run --rm \
  -v "$PWD":/work -w /work \
  -v "$HOME/.minos/rules":/root/.minos/rules \
  minos:latest \
  minos rulesync git+https://example.com/rules.git#path=dist/rules.tar.gz v1.0.0 \
    --cache-dir /root/.minos/rules

docker run --rm \
  -v "$PWD":/work -w /work \
  -v "$HOME/.minos/rules":/root/.minos/rules \
  minos:latest \
  minos rulesync oci://example.com/minos/rules:1.0.0#path=rules.tar.gz v1.0.0 \
    --cache-dir /root/.minos/rules
```

说明：`#path=` 用于指定制品内 tar.gz 路径；未指定时要求制品中只有一个 tar.gz。

## 输出目录与权限

- 推荐挂载宿主目录到容器 `/work/output`（或自定义）以保存报告/日志：`-v "$PWD/output":/work/output`。  
- CLI `--output-dir` 默认为 `output/reports`（相对工作目录），确保宿主挂载目录可写。

## 网络与证书

- 受限网络可配置代理（构建时 `HTTP_PROXY/HTTPS_PROXY/NO_PROXY` build args，或运行时环境变量）。  
- HTTPS 依赖系统 CA 证书；自签证书需在镜像内注入 CA。

## 常见问题

- **权限不足**：挂载目录不可写导致报告/日志无法生成。  
- **缺少规则缓存**：离线环境未准备缓存，rulesync 会失败。  
- **远端拉取失败**：git/oras 未安装或网络受限。  
- **路径错误**：`--input`/`--apk-path` 与容器内挂载路径不一致。

## 附：镜像构建说明

- 入口脚本：`containers/entrypoint.sh`，默认调用 `python -m minos.cli ...`。  
- 构建镜像（示例）：`docker build -t minos:latest .`（可通过 ARG 覆盖 `PIP_INDEX_URL/HTTP_PROXY` 等）。
