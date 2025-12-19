# 容器运行说明

本文件面向“第一次用容器跑 Minos”的用户，目标：构建镜像、挂载缓存和输入、跑通一次扫描并拿到报告。

## 前置条件与约束
- 需要 Docker 环境（支持 build/run）。  
- 规则缓存：首版仅支持 PRD 法规参考链接白名单源（eur-lex/leginfo/planalto/cac.gov.cn/ppc.go.jp），参数值不区分大小写。默认禁用本地/自定义源；如需测试/开发，请在生成缓存时显式加 `--allow-local-sources` 或 `--allow-custom-sources`。scan 默认从缓存 `~/.minos/rules/<reg>/<version>/rules.yaml` 加载规则，可用 `--rules-dir` 覆盖（容器内默认 `/root/.minos/rules`）。  
- 镜像内规则缓存路径约定：`/root/.minos/rules`（运行时请挂载）。  
- 建议先在宿主机准备好规则缓存，再在容器内复用（避免容器内上网与下载）。

## Quick Start（最小可运行）

### 1) 构建镜像
```bash
# 仓库根目录
docker build -f containers/Dockerfile -t minos:latest .
```

### 2) 运行扫描（源码示例）
```bash
docker run --rm \
  -v "$PWD":/work -w /work \
  -v "$HOME/.minos/rules":/root/.minos/rules \  # 规则缓存（预先准备好）
  minos:latest \
  minos scan --mode source --input app/src --output-dir output/reports
```
期望输出：`output/reports/*.json|*.html`。

## 推荐运行流程
1) 在宿主机生成/同步规则并放入 `~/.minos/rules`。示例命令：`minos rulesync --from-url [--regulation <reg>] [--version <ver>] --cache-dir ~/.minos/rules`（URL 可省略，未给 regulation 默认同步全部 PRD 法规）。容器内扫描默认读取 `/root/.minos/rules/<reg>/<version>/rules.yaml`，可通过 `--rules-dir` 指向挂载目录。  
2) 运行容器时挂载源码/输出/规则缓存目录。  
3) 容器内执行 `minos scan`，报告与日志写回宿主挂载目录。

## 规则缓存与同步
- 挂载约定：`~/.minos/rules:/root/.minos/rules`，确保宿主目录存在且可写。  
- 离线/受限网络：宿主机先 `minos rulesync --from-url ... --offline`（需已有缓存）或在有网环境准备缓存，再在容器内复用。  
- 容器内规则同步（不推荐，需网络且受白名单限制）：同样使用 `minos rulesync --from-url [--regulation <reg>] [--version <ver>] --cache-dir /root/.minos/rules`，必要时开启 `--allow-local-sources`/`--allow-custom-sources`（仅受控环境）。  
- git/OCI 规则包：镜像内需有 `git` 或 `oras`。可基于 `minos:latest` 追加安装。
```Dockerfile
FROM minos:latest
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && \
    rm -rf /var/lib/apt/lists/*
# 若需 OCI：安装 oras（根据环境下载对应版本）
```

## 输出目录与权限
- 推荐挂载宿主输出目录：`-v "$PWD/output":/work/output`，并使用 `--output-dir /work/output/reports`。  
- 默认输出目录为工作目录下的 `output/reports`，确保挂载路径可写；日志可通过 `--log-file` 指定到挂载目录。

## 网络与证书
- 受限网络可通过 build args/环境变量设置 `HTTP_PROXY/HTTPS_PROXY/NO_PROXY`。  
- 自签证书需在镜像内注入 CA；HTTPS 依赖系统 CA 证书。

## 常见问题与解决
- **规则缓存缺失/版本为空**：确认宿主缓存已准备且挂载到 `/root/.minos/rules`。  
- **源被拒（白名单/本地禁用）**：生成缓存时显式 `--allow-local-sources` 或 `--allow-custom-sources`（仅受控环境）。  
- **权限不足**：宿主挂载目录不可写，导致报告/日志无法生成；调整目录权限或以合适用户运行。  
- **路径错误**：容器内 `--input`/`--apk-path` 应使用容器路径，与挂载保持一致。  
- **远端拉取失败**：容器内缺少 `git`/`oras` 或网络受限，优先在宿主准备缓存。

## 附：镜像构建说明
- 入口脚本：`containers/entrypoint.sh`（默认执行 `python -m minos.cli ...`）。  
- 构建示例：`docker build -t minos:latest .`，可通过 ARG 覆盖 `PIP_INDEX_URL/HTTP_PROXY` 等。  
