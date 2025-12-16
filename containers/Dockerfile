# syntax=docker/dockerfile:1.5

FROM python:3.10-slim AS builder

ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL} \
    http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY}

RUN apt-get update && \
    apt-get install -y --no-install-recommends zip unzip ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml requirements.txt README.md /build/
COPY src /build/src
RUN pip install --upgrade pip && \
    pip wheel --no-deps --wheel-dir /wheels .

FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/work/src

RUN apt-get update && \
    apt-get install -y --no-install-recommends zip unzip ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY --from=builder /wheels /wheels
RUN pip install --no-deps /wheels/*.whl

COPY containers/entrypoint.sh /entrypoint.sh
# 预置规则缓存目录（空），便于挂载覆盖
RUN mkdir -p /root/.minos/rules && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
