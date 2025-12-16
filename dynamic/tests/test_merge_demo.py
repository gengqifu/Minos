from pathlib import Path
import json
import os
import subprocess


ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
MERGE_SCRIPT = SAMPLES / "merge_demo.py"


def run_script(env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        ["python3", str(MERGE_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=merged_env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_merge_success():
    code, out, err = run_script()
    assert code == 0, err
    data = json.loads(out)
    assert data["meta"]["mode"] == "both"
    assert len(data["findings"]) == 3
    assert data["stats"]["count_by_source"]["static"] == 1
    assert data["stats"]["count_by_source"]["frida"] == 1
    assert data["stats"]["count_by_source"]["mitmproxy"] == 1


def test_missing_file_errors():
    code, _, err = run_script()
    assert code == 0, err  # baseline works

    # point to a missing file via env
    env = {"STATIC_PATH": str(SAMPLES / "not_exist.json")}
    code, _, err = run_script(env=env)
    assert code != 0
    assert "文件不存在" in err


def test_invalid_json_errors(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{broken}")
    env = {"STATIC_PATH": str(bad)}
    code, _, err = run_script(env=env)
    assert code != 0
    assert "解析失败" in err
