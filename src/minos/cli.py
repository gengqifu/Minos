"""
Minos CLI 入口（rulesync 子命令）。
"""

import argparse
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


def _handle_rulesync(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).expanduser()
    retries = max(args.retries, 0)
    attempt = 0
    while True:
        try:
            # 回滚模式
            if args.rollback_to:
                path = rulesync.rollback(cache_dir, args.version, target_version=args.rollback_to)
                sys.stdout.write(f"回滚成功: {path}\n")
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
            sys.stdout.write(f"规则同步成功: {path}\n")
            return 0
        except rulesync.RulesyncChecksumError as exc:
            attempt += 1
            if attempt > retries:
                sys.stderr.write(f"规则校验失败: {exc}\n")
                return 2
            continue
        except rulesync.RulesyncError as exc:
            attempt += 1
            if attempt > retries:
                sys.stderr.write(f"规则同步失败: {exc}\n")
                return 1
            continue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="minos", description="Minos CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_rulesync_parser(subparsers)
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
