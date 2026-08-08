#!/usr/bin/env python3
"""verify_allow.py — repo-local な機械ゲート (.claude/verify.sh) の承認台帳と起動器。

hooks/verify-precommit.sh は commit のたびに repo の .claude/verify.sh を **実行**する。
hook は permission プロンプトを経ずに走るので、「ファイルが存在する」を「実行してよい」と
読み替えると、clone しただけの外部 repo でコードが自動実行される (2026-07-31 の
security-reviewer が CRITICAL として指摘)。既存 hook の方針
(bandit-precommit.sh:「repo 内 .venv バイナリは RCE 経路になるため意図的に探さない」)
とも矛盾する。

そこで direnv allow と同型の承認を挟む: **人間が内容を読んで承認した版のハッシュ**だけを
実行する。台帳は repo でなく ~/.claude 側 (= repo に書き込めるものから隔離) に置く。

**保護範囲 (明示的な前提)**: 守るのは *untrusted な repo の内容* であって、*侵害された
ローカルアカウント* ではない。台帳は署名のない平文 JSON なので、同一ユーザーで走る任意の
プロセスは偽の承認を書き込める — そのレベルの攻撃者は ~/.claude/hooks 自体も書き換えられる
ので、ここで防ぐ対象にしない (~/.zshrc と同じ信頼水準)。

  run <repo> [args...]  承認を照合し、**照合したバイト列そのもの**を実行する (推奨経路)
  check <repo>          照合のみ
  approve <repo>        現在の内容のハッシュを台帳に記録する (人間が読んだ後に実行する)
  revoke <repo>         承認を取り消す
  list                  台帳を表示

exit code (ゲート自身の 0/1/2 と衝突しないよう高位に置く):
  70 未承認 / 71 内容不一致 / 72 経路が不正 / 73 台帳が壊れている / 64 usage
  `run` はゲートの exit code をそのまま返す (0/1/2 は契約どおりの意味)。

台帳: ~/.claude/verify-allow.json  {"<repo realpath>": {"sha256": ..., "approved": "<UTC date>"}}
日付は承認操作時にのみ書き込むため、check 経路は時刻に依存しない。
VERIFY_ALLOW_LEDGER は **テスト用**の差し替え口 (攻撃者が到達する経路として想定しない)。

既知の false negative: macOS の case-insensitive FS では `Path.resolve()` が実際の大小文字に
正規化しないため、綴りの違う同一 repo は別キーになり「未承認」に落ちる。異なる綴りは常に
同一ディレクトリを指すので取り違えは起きず、安全側に倒れる。
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

LEDGER = Path(os.environ.get("VERIFY_ALLOW_LEDGER", Path.home() / ".claude" / "verify-allow.json"))
GATE_RELPATH = Path(".claude") / "verify.sh"

OK = 0
USAGE = 64
NOT_APPROVED = 70
MISMATCH = 71
UNSAFE_PATH = 72
LEDGER_CORRUPT = 73

Ledger = dict[str, dict[str, str]]


class LedgerCorrupt(Exception):
    """台帳が存在するのに読めない。空として扱うと承認が黙って消えるので区別する。"""


def resolve_checked(repo_arg: str) -> tuple[Path, Path] | None:
    """(repo realpath, gate realpath) を返す。gate が repo 外を指すなら None。

    symlink で repo 外の実行体に差し替える経路を塞ぐ (realpath 解決後に包含判定)。
    """
    try:
        repo = Path(repo_arg).expanduser().resolve()
        gate = repo / GATE_RELPATH
        if not gate.is_file():
            return None
        real = gate.resolve()
        real.relative_to(repo)
    except (OSError, RuntimeError, ValueError):
        # RuntimeError = symlink loop, ValueError = repo 外, OSError = 権限等
        return None
    return repo, real


def load() -> Ledger:
    if not LEDGER.exists():
        return {}
    try:
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise LedgerCorrupt(str(e)) from e
    if not isinstance(data, dict):
        raise LedgerCorrupt("台帳が JSON object でない")
    return data


def load_or_empty() -> Ledger:
    """check / run 用: 壊れていても空として扱う (エントリ無し = 未承認 = 安全側)。"""
    try:
        return load()
    except LedgerCorrupt:
        return {}


def save(data: Ledger) -> None:
    """原子的に書く。途中で落ちた半端な JSON が次回の承認消失を招くのを防ぐ。"""
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(LEDGER.parent), prefix=".verify-allow-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, LEDGER)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def verified_bytes(repo_arg: str) -> tuple[Path, bytes] | int:
    """承認と内容を照合し、**照合したバイト列**を返す。失敗なら exit code を返す。

    バイト列を呼び出し側に渡すのが要点 — 照合したものと実行するものを同一にして
    TOCTOU (照合後・実行前の差し替え) を閉じる。
    """
    resolved = resolve_checked(repo_arg)
    if resolved is None:
        print("gate が存在しないか、symlink で repo 外を指しています", file=sys.stderr)
        return UNSAFE_PATH
    repo, gate = resolved
    try:
        payload = gate.read_bytes()
    except OSError as e:
        print(f"gate を読めません: {e}", file=sys.stderr)
        return UNSAFE_PATH
    entry = load_or_empty().get(str(repo))
    if not entry:
        print(f"未承認: {gate}", file=sys.stderr)
        return NOT_APPROVED
    if entry.get("sha256") != hashlib.sha256(payload).hexdigest():
        print(f"承認時から内容が変わっています: {gate}", file=sys.stderr)
        return MISMATCH
    return repo, payload


def cmd_run(repo_arg: str, args: list[str]) -> int:
    result = verified_bytes(repo_arg)
    if isinstance(result, int):
        return result
    repo, payload = result

    # 照合済みバイト列を自分だけが読める一時ファイルに置いて実行する。
    # ゲートは BASH_SOURCE から repo root を決められないので VERIFY_REPO_ROOT で渡す (契約)。
    with tempfile.TemporaryDirectory(prefix="verify-gate-") as td:
        script = Path(td) / "verify.sh"
        script.write_bytes(payload)
        script.chmod(stat.S_IRWXU)
        env = {**os.environ, "VERIFY_REPO_ROOT": str(repo)}
        try:
            proc = subprocess.run([str(script), *args], cwd=str(repo), env=env, check=False)
        except OSError as e:
            print(f"gate を起動できません: {e}", file=sys.stderr)
            return UNSAFE_PATH
    return proc.returncode


def cmd_check(repo_arg: str) -> int:
    result = verified_bytes(repo_arg)
    return result if isinstance(result, int) else OK


def cmd_approve(repo_arg: str) -> int:
    resolved = resolve_checked(repo_arg)
    if resolved is None:
        print("gate が存在しないか、symlink で repo 外を指しています", file=sys.stderr)
        return UNSAFE_PATH
    repo, gate = resolved
    try:
        data = load()  # 壊れていたら黙って上書きしない (既存の承認が消える)
        digest = hashlib.sha256(gate.read_bytes()).hexdigest()
    except LedgerCorrupt as e:
        print(
            f"台帳が壊れています ({e})。中身を確認してから再実行: {LEDGER}",
            file=sys.stderr,
        )
        return LEDGER_CORRUPT
    except OSError as e:
        print(f"gate を読めません: {e}", file=sys.stderr)
        return UNSAFE_PATH
    data[str(repo)] = {
        "sha256": digest,
        "approved": datetime.now(UTC).date().isoformat(),
    }
    save(data)
    print(f"承認しました: {gate}")
    return OK


def cmd_revoke(repo_arg: str) -> int:
    repo = str(Path(repo_arg).expanduser().resolve())
    try:
        data = load()
    except LedgerCorrupt as e:
        print(f"台帳が壊れています ({e}): {LEDGER}", file=sys.stderr)
        return LEDGER_CORRUPT
    if data.pop(repo, None) is None:
        print(f"台帳にありません: {repo}", file=sys.stderr)
        return NOT_APPROVED
    save(data)
    print(f"承認を取り消しました: {repo}")
    return OK


def cmd_list() -> int:
    try:
        data = load()
    except LedgerCorrupt as e:
        print(f"台帳が壊れています ({e}): {LEDGER}", file=sys.stderr)
        return LEDGER_CORRUPT
    if not data:
        print("(承認済みのゲートはありません)")
        return OK
    for repo, entry in sorted(data.items()):
        print(f"{entry.get('approved', '?')}  {repo}")
    return OK


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return USAGE
    cmd, args = argv[0], argv[1:]
    if cmd == "list" and not args:
        return cmd_list()
    if cmd == "run" and args:
        return cmd_run(args[0], args[1:])
    if cmd in {"check", "approve", "revoke"} and len(args) == 1:
        return {"check": cmd_check, "approve": cmd_approve, "revoke": cmd_revoke}[cmd](args[0])
    print(__doc__, file=sys.stderr)
    return USAGE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
