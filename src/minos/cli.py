"""
Minos CLI 入口（rulesync 子命令）。
"""

import argparse
import json
import sys
from pathlib import Path

from minos import rulesync


def _add_rulesync_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("rulesync", help="同步规则包")
    parser.add_argument("source", help="规则包源（文件路径/git/oci/https），当前支持本地 tar.gz")
    parser.add_argument("version", help="规则版本/标签")
    parser.add_argument(
        "--sha256",
        dest="sha256",
        help="期望的 SHA256 校验值（可选）",
    )
    parser.add_argument(
        "--cache-dir",
        dest="cache_dir",
        default="~/.minos/rules",
        help="规则缓存目录（默认 ~/.minos/rules）",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="离线模式（仅使用已缓存的版本，不拉取）",
    )
    parser.add_argument(
        "--gpg-key",
        dest="gpg_key",
        help="GPG 公钥（预留，暂未启用）",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=0,
        help="失败重试次数（默认 0）",
    )
    parser.add_argument(
        "--rollback-to",
        dest="rollback_to",
        help="回滚到指定版本（可选）",
    )
    parser.add_argument(
        "--cleanup-keep",
        dest="cleanup_keep",
        type=int,
        help="同步后保留的版本数量（清理旧版本，默认不清理）",
    )
    parser.set_defaults(handler=_handle_rulesync)


def _add_scan_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("scan", help="执行扫描（占位实现）")
    parser.add_argument("--mode", choices=["source", "apk", "both"], default="both", help="扫描模式")
    parser.add_argument("--input", dest="inputs", action="append", help="源码目录（可多次传入）")
    parser.add_argument("--apk-path", dest="apks", action="append", help="APK 路径（可多次传入）")
    parser.add_argument("--manifest", dest="manifests", action="append", help="Manifest 路径（可多次传入）")
    parser.add_argument("--regions", dest="regions", action="append", help="地区代码（可多选）")
    parser.add_argument("--regulations", dest="regulations", action="append", help="法规标识（可多选）")
    parser.add_argument("--format", choices=["html", "json", "both"], default="both", help="报告格式")
    parser.add_argument("--output-dir", dest="output_dir", default="output/reports", help="报告输出目录")
    parser.add_argument("--report-name", dest="report_name", default="scan", help="报告文件前缀")
    parser.add_argument("--threads", type=int, default=4, help="并行度（默认4）")
    parser.add_argument("--timeout", type=int, help="全局超时（秒，可选）")
    parser.add_argument("--log-level", dest="log_level", default="info", choices=["debug", "info", "warn", "error"], help="日志级别")
    parser.add_argument("--config", dest="config", help="配置文件路径（可选）")
    parser.set_defaults(handler=_handle_scan)


def _write_report(output_dir: Path, report_name: str, data: dict, fmt: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if fmt in {"both", "json"}:
        (output_dir / f"{report_name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    if fmt in {"both", "html"}:
        meta = data.get("meta", {})
        stats = data.get("stats", {})
        rows = "\n".join(
            [
                "<tr>"
                f"<td>{f.get('rule_id','')}</td>"
                f"<td>{f.get('regulation','')}</td>"
                f"<td>{f.get('severity','')}</td>"
                f"<td>{f.get('location','')}</td>"
                f"<td>{f.get('evidence','')}</td>"
                "</tr>"
                for f in data.get("findings", [])
            ]
        )
        html = f"""<!DOCTYPE html>
<html><body>
<h3>Minos Scan Report</h3>
<p>Mode: {meta.get('mode','')}</p>
<p>Inputs: {', '.join(meta.get('inputs', []))}</p>
<p>Regions: {', '.join(meta.get('regions', []))}</p>
<p>Regulations: {', '.join(meta.get('regulations', []))}</p>
<p>Threads: {meta.get('threads','')}</p>
<p>Timeout: {meta.get('timeout','')}</p>
<p>Findings: {len(data.get('findings', []))}</p>
<p>Stats by regulation: {stats.get('count_by_regulation', {})}</p>
<p>Stats by severity: {stats.get('count_by_severity', {})}</p>
<table border="1" cellpadding="4" cellspacing="0">
<thead><tr><th>rule_id</th><th>regulation</th><th>severity</th><th>location</th><th>evidence</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body></html>
"""
        (output_dir / f"{report_name}.html").write_text(html)


def _handle_scan(args: argparse.Namespace) -> int:
    inputs = args.inputs or []
    apks = args.apks or []
    manifests = args.manifests or []
    needs_src = args.mode in {"source", "both"}
    needs_apk = args.mode in {"apk", "both"}

    if needs_src and not inputs and needs_apk and not apks:
        sys.stderr.write("[scan] 缺少输入：请指定 --input 或 --apk-path\n")
        return 2
    if needs_src and not inputs:
        sys.stderr.write("[scan] 缺少源码输入 (--input)\n")
        return 2
    if needs_apk and not apks:
        sys.stderr.write("[scan] 缺少 APK 输入 (--apk-path)\n")
        return 2

    meta_inputs = inputs + apks + manifests
    report = {
        "meta": {
            "inputs": meta_inputs,
            "mode": args.mode,
            "regions": args.regions or [],
            "regulations": args.regulations or [],
            "threads": args.threads,
            "timeout": args.timeout,
            "log_level": args.log_level,
            "config": args.config,
        },
        "findings": [],
        "stats": {"count_by_regulation": {}, "count_by_severity": {}},
    }
    _write_report(Path(args.output_dir), args.report_name, report, args.format)
    report_paths = []
    if args.format in {"both", "json"}:
        report_paths.append(str(Path(args.output_dir) / f"{args.report_name}.json"))
    if args.format in {"both", "html"}:
        report_paths.append(str(Path(args.output_dir) / f"{args.report_name}.html"))
    sys.stdout.write(
        f"[scan] mode={args.mode} inputs={len(meta_inputs)} findings=0 reports={report_paths}\n"
    )
    return 0


def _handle_rulesync(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).expanduser()
    retries = max(args.retries, 0)
    attempt = 0
    while True:
        try:
            # 回滚模式
            if args.rollback_to:
                path = rulesync.rollback(cache_dir, args.version, target_version=args.rollback_to)
                sys.stdout.write(f"[rulesync] 回滚成功: {path}\n")
                return 0
            # 同步模式
            path = rulesync.sync_rules(
                source=args.source,
                version=args.version,
                cache_dir=cache_dir,
                expected_sha256=args.sha256,
                gpg_key=args.gpg_key,
                offline=args.offline,
            )
            if args.cleanup_keep:
                rulesync.cleanup(cache_dir, keep=args.cleanup_keep)
            sys.stdout.write(f"[rulesync] 规则同步成功: {path}\n")
            active = rulesync.get_active_path(cache_dir)
            if active:
                sys.stdout.write(f"[rulesync] 当前激活规则路径: {active}\n")
            return 0
        except rulesync.RulesyncChecksumError as exc:
            attempt += 1
            if attempt > retries:
                sys.stderr.write(f"[rulesync] 规则校验失败: {exc}\n")
                return 2
            continue
        except rulesync.RulesyncError as exc:
            attempt += 1
            if attempt > retries:
                sys.stderr.write(f"[rulesync] 规则同步失败: {exc}\n")
                # 退出码约定：1 为其他失败（源缺失/离线无缓存/回滚失败等）
                return 1
            continue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="minos", description="Minos CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_rulesync_parser(subparsers)
    _add_scan_parser(subparsers)
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
