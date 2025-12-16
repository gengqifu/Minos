#!/usr/bin/env bash
# 本地/容器模拟的 CI 工作流验收脚本，验证工件产出与摘要。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${SRC:-${ROOT_DIR}/fixtures/source}"
APK="${APK:-${ROOT_DIR}/fixtures/dummy.apk}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-${ROOT_DIR}/../output}"
REPORT_DIR="${REPORT_DIR:-${ARTIFACT_ROOT}/reports}"
LOG_DIR="${LOG_DIR:-${ARTIFACT_ROOT}/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/scan.log}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTHONPATH="${ROOT_DIR}/../src:${PYTHONPATH:-}"
export PYTHONPATH

mkdir -p "${REPORT_DIR}" "${LOG_DIR}"

assert_file() {
  local file="$1"
  if [ ! -s "${file}" ]; then
    echo "[ci-test] 缺少文件: ${file}"
    exit 1
  fi
}

assert_not_exists() {
  local file="$1"
  if [ -e "${file}" ]; then
    echo "[ci-test] 不期望存在: ${file}"
    exit 1
  fi
}

assert_contains() {
  local needle="$1"
  local file="$2"
  if ! grep -q "${needle}" "${file}"; then
    echo "[ci-test] 未匹配到内容: ${needle} in ${file}"
    exit 1
  fi
}

assert_json_schema() {
  local file="$1"
  local expect_mode="$2"
  local expect_inputs="$3"
  "${PYTHON_BIN}" - <<PY
import json, sys
path = "${file}"
data = json.load(open(path, "r"))
required_keys = {"meta", "findings", "stats"}
assert set(data.keys()) == required_keys, f"keys mismatch: {set(data.keys())}"
meta = data["meta"]
assert meta.get("mode") == "${expect_mode}", meta
assert len(meta.get("inputs", [])) == ${expect_inputs}, meta.get("inputs")
stats = data["stats"]
assert "count_by_regulation" in stats and "count_by_severity" in stats, stats
print("[ci-test] json schema ok", path)
PY
}

assert_html_basic() {
  local file="$1"
  assert_contains "Minos Scan Report" "${file}"
  assert_contains "Stats by regulation" "${file}"
}

run_github_like() {
  local stdout_file="${ARTIFACT_ROOT}/github_stdout.log"
  rm -rf "${ARTIFACT_ROOT}"
  mkdir -p "${REPORT_DIR}" "${LOG_DIR}"

  echo "[ci-test] GitHub Actions 模拟：源码模式，生成 HTML+JSON+日志"
  "${PYTHON_BIN}" -m minos.cli scan \
    --mode source \
    --input "${SRC}" \
    --output-dir "${REPORT_DIR}" \
    --format both \
    --log-file "${LOG_FILE}" \
    --report-name gha-report \
    --log-level info | tee "${stdout_file}"

  assert_file "${REPORT_DIR}/gha-report.json"
  assert_file "${REPORT_DIR}/gha-report.html"
  assert_file "${LOG_FILE}"
  assert_contains "findings=0" "${stdout_file}"
  assert_contains "reports=" "${stdout_file}"
  assert_json_schema "${REPORT_DIR}/gha-report.json" "source" 1
  assert_html_basic "${REPORT_DIR}/gha-report.html"
}

run_gitlab_like() {
  local stdout_file="${ARTIFACT_ROOT}/gitlab_stdout.log"
  rm -rf "${ARTIFACT_ROOT}"
  mkdir -p "${REPORT_DIR}" "${LOG_DIR}"

  echo "[ci-test] GitLab CI 模拟：源码+APK，JSON 报告、日志工件"
  "${PYTHON_BIN}" -m minos.cli scan \
    --mode both \
    --input "${SRC}" \
    --apk-path "${APK}" \
    --output-dir "${REPORT_DIR}" \
    --format json \
    --log-file "${LOG_FILE}" \
    --report-name gitlab-report \
    --log-level info | tee "${stdout_file}"

  assert_file "${REPORT_DIR}/gitlab-report.json"
  assert_not_exists "${REPORT_DIR}/gitlab-report.html"
  assert_file "${LOG_FILE}"
  assert_contains "findings=0" "${stdout_file}"
  assert_contains "reports=" "${stdout_file}"
  assert_json_schema "${REPORT_DIR}/gitlab-report.json" "both" 2
}

run_missing_input_case() {
  local stdout_file="${ARTIFACT_ROOT}/missing_stdout.log"
  local stderr_file="${ARTIFACT_ROOT}/missing_stderr.log"
  rm -rf "${ARTIFACT_ROOT}"
  mkdir -p "${REPORT_DIR}" "${LOG_DIR}"

  echo "[ci-test] 缺少输入路径应失败"
  set +e
  "${PYTHON_BIN}" -m minos.cli scan \
    --mode apk \
    --format json \
    --output-dir "${REPORT_DIR}" >"${stdout_file}" 2>"${stderr_file}"
  exit_code=$?
  set -e

  if [ "${exit_code}" -eq 0 ]; then
    echo "[ci-test] 预期失败但实际成功"
    exit 1
  fi
  assert_contains "缺少 APK 输入" "${stderr_file}"
  if ls "${REPORT_DIR}"/* >/dev/null 2>&1; then
    echo "[ci-test] 不应生成报告文件"
    exit 1
  fi
}

run_github_like
run_gitlab_like
run_missing_input_case

echo "[ci-test] CI 工作流验收脚本完成"
