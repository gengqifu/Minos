# 容器运行说明（占位）

示例命令（请使用仓库内的 Dockerfile）：

```bash
# 构建镜像（仓库路径下执行）
docker build -f containers/Dockerfile -t minos:latest .

# 运行：本地代码/产物挂载到 /work，规则缓存挂载到 /root/.minos/rules，输出到 /work/output
docker run --rm \
  -v "$PWD":/work -w /work \
  -v "$HOME/.minos/rules":/root/.minos/rules \
  minos:latest \
  minos scan --mode apk --apk-path app-release.apk --output-dir output/reports
```

- 入口脚本：`containers/entrypoint.sh`，默认调用 `python -m minos.cli ...`。  
- 构建镜像（示例）：`docker build -t minos:latest .`（可通过 ARG 覆盖 `PIP_INDEX_URL`/代理）。  
- 运行示例（apk 模式）：  
  ```bash
  docker run --rm \
    -v "$PWD":/work -w /work \
    -v "$HOME/.minos/rules":/root/.minos/rules \
    minos:latest \
    minos scan --mode apk --apk-path app-release.apk --output-dir output/reports
  ```
- 输出：报告默认写入 `output/reports`（可通过 `--output-dir` 指定）。  

规则缓存挂载约定：
- 默认容器内缓存目录：`/root/.minos/rules`，建议宿主机挂载 `~/.minos/rules:/root/.minos/rules`。  
- 无网/受限网络：先在宿主机执行 `minos rulesync ... --cache-dir ~/.minos/rules --offline`，再运行容器复用缓存。  
- 挂载时请确保宿主目录存在且可写，否则容器可能无法写入缓存。  
- 在线同步（容器内）：  
  ```bash
  docker run --rm \
    -v "$PWD":/work -w /work \
    -v "$HOME/.minos/rules":/root/.minos/rules \
    minos:latest \
    minos rulesync <source> <version> --sha256 <digest> \
      --cache-dir /root/.minos/rules \
      --regulations gdpr --regulations ccpa
  ```
  说明：默认无 `--regulations` 同步 PRD 法规参考链接中的全部法规；缓存按 `/root/.minos/rules/<regulation>` 隔离，仅保留最新版本。  

远端 source 示例与注意事项：
- HTTP 规则包（容器内可直接下载）：  
  ```bash
  docker run --rm \
    -v "$PWD":/work -w /work \
    -v "$HOME/.minos/rules":/root/.minos/rules \
    minos:latest \
    minos rulesync https://example.com/rules.tar.gz v1.0.0 \
      --sha256 <digest> --cache-dir /root/.minos/rules
  ```
- git/OCI 规则包：镜像内需安装 `git` 或 `oras`。默认镜像未包含这两个工具，建议自定义镜像扩展：  
  ```dockerfile
  FROM minos:latest
  RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && \
      rm -rf /var/lib/apt/lists/*
  # 若需 OCI：安装 oras（根据环境下载对应版本）
  ```
  使用示例：  
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
  说明：`#path=` 用于指定制品内的 tar.gz 路径；未指定时要求制品中只有一个 tar.gz。  

网络/证书建议：
- 受限网络请配置代理（可通过 Dockerfile 的 `HTTP_PROXY/HTTPS_PROXY/NO_PROXY` build args 或运行时环境变量）。  
- HTTPS 依赖系统 CA 证书，若访问自签证书需在镜像中注入 CA。  

输出目录挂载与权限：
- 推荐挂载宿主目录到容器 `/work/output`（或自定义）以便保存报告/日志：`-v "$PWD/output":/work/output`。  
- CLI `--output-dir` 默认为 `output/reports`（相对工作目录），保持与本地一致；确保宿主挂载目录可写。  

镜像标签与推送（占位约定）：
- 标签建议与仓库版本或 git tag 对齐，例如 `minos:<git-tag>`；开发测试可用 `minos:ci`/`minos:test`。  
- 推送示例：`docker push <registry>/minos:<tag>`（或 OCI registry）；需要在 CI 中配置登录/凭据。  
- 构建代理/源：通过 `--build-arg PIP_INDEX_URL=...` 等参数在受限网络构建。  
