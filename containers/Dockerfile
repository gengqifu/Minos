# syntax=docker/dockerfile:1.5

FROM python:3.10-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends zip unzip ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY src src
COPY README.md pyproject.toml* requirements.txt* /work/
COPY containers/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 安装依赖（如果有 requirements.txt 则优先）
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi && \
    pip install -e .

ENTRYPOINT ["/entrypoint.sh"]
