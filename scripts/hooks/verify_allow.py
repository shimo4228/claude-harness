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
  known <repo>          台帳に repo の記録があるか (gate の有無・内容は見ない。読み取り専用)
                        0 = ある (一致した key を stdout に出す) / 70 = 無い / 73 = 台帳が壊れている。
                        hook が gate 不在時に「未導入の repo」と「承認済み repo の gate 消失」を
                        区別するために引く
  approve <repo>        現在の内容のハッシュを台帳に記録する (人間が読んだ後に実行する)
  revoke <repo>         承認を取り消す
  list                  台帳を表示

exit code (ゲート自身の 0/1/2 と衝突しないよう高位に置く):
  70 未承認 / 71 内容不一致 / 72 経路が不正 / 73 台帳が壊れている / 64 usage
  `run` はゲートの exit code をそのまま返す (0/1/2 は契約どおりの意味)。

台帳: ~/.claude/verify-allow.json  {"<repo realpath>": {"sha256": ..., "approved": "<UTC date>"}}
日付は承認操作時にのみ書き込むため、check 経路は時刻に依存しない。

linked worktree (`git worktree add`) の toplevel は台帳に無い別 path なので、run / check / known は
repo 自身が台帳に無いとき、それが**登録されている** main worktree の key で引く (ledger_key)。
照合・実行するのは worktree 自身の gate のバイト列で、承認済みの hash と一致したときだけ走る。
approve / revoke と台帳の形式は変えない (worktree の path で approve すれば、その key が優先)。
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


# repo 探索を差し替える env。hook の環境に残っていると `-C <repo>` より優先され、別の repo の
# worktree 一覧を読んでしまう
_GIT_DISCOVERY_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")


def _git_out(repo: Path, *args: str) -> str | None:
    """repo で git を読み取り専用に呼び、stdout を返す。失敗なら None。

    repo 内 config による実行 (core.fsmonitor / core.hooksPath) は hook と同じく封じ、
    repo 探索を差し替える env は外す。
    """
    env = {k: v for k, v in os.environ.items() if k not in _GIT_DISCOVERY_ENV}
    cmd = ["git", "-c", "core.fsmonitor=", "-c", "core.hooksPath=", "-C", str(repo), *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, env=env, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "surrogateescape")


def _owns_registration(repo: Path, main: Path) -> bool:
    """repo の git dir が、main の git dir の管理領域にある自分の登録 (<common>/worktrees/<id>) か。

    3 つの偽装を閉じる (いずれも 2026-09-26 の security review が再現):

    - `git worktree list` の登録は path だけで照合される。git が登録を prunable と報告するのは
      `<path>/.git` が無いときだけで、lock された登録は prune されない。消えた worktree の path に
      後から置いたディレクトリが `.git` ファイルで main の git dir を名乗ると、path の一致だけでは
      登録済みに見える → repo の git dir が `<common>/worktrees/` 直下にあり、その管理
      ディレクトリの `gitdir` ファイルが repo の `.git` を指し返すことを要件にする
    - git は main worktree を「common dir の realpath から末尾の /.git を除いたもの」として求める。
      承認済み repo の **work tree** に偽の管理領域 (objects/・refs/・worktrees/<id>/ で commondir
      が `../..`) を置くと、common dir が work tree そのものになり main = 承認済み repo に見える →
      main 自身の git dir (main で `rev-parse --absolute-git-dir`) が common dir と一致することを
      要件にする
    - git は登録時の realpath を記録する。消えた登録の path の祖先に後から symlink を置くと
      (repo の tree は symlink を運べる)、記録した path が外のディレクトリへ解決される → 記録した
      path が今 symlink を通らないことを要件にする

    `gitdir` ファイルは相対 path のことがある (`worktree add --relative-paths` /
    worktree.useRelativePaths)。git と同じく管理ディレクトリ起点で解決する。本物の管理ディレクトリを
    指す `.git` ファイルを持つディレクトリを、消えた登録の path そのものに置く形は区別できない
    (`.git` ファイルは repo の tree では運べず、その path へのローカル書き込みが要る — 保護範囲の外)。
    """
    out = _git_out(
        repo, "rev-parse", "--path-format=absolute", "--absolute-git-dir", "--git-common-dir"
    )
    main_out = _git_out(main, "rev-parse", "--absolute-git-dir")
    if out is None or main_out is None:
        return False
    lines = out.splitlines()
    main_lines = main_out.splitlines()
    if len(lines) != 2 or len(main_lines) != 1:
        return False
    try:
        git_dir = Path(lines[0]).resolve()
        common = Path(lines[1]).resolve()
        if Path(main_lines[0]).resolve() != common:
            return False
        if git_dir.parent != common / "worktrees":
            return False
        back = (git_dir / "gitdir").read_text(encoding="utf-8").strip()
        # git は登録時の realpath を記録する。記録した path が今 symlink を通るなら、登録後に祖先へ
        # symlink が置かれた (追跡された `.claude/worktrees` の symlink 等で、消えた登録の path を外の
        # ディレクトリへ向けられる — 2026-09-26 security review、再現済み)。字面のまま一致を求める
        recorded = Path(os.path.normpath(git_dir / back))
        if recorded != recorded.resolve():
            return False
        return recorded == (repo / ".git").resolve()
    except (OSError, RuntimeError, UnicodeDecodeError, ValueError):
        return False


def main_checkout_of(repo: Path) -> Path | None:
    """repo が linked worktree なら、それが**登録されている** main worktree の realpath を返す。

    linked worktree でない (main worktree 自身・通常 repo・bare・git 外)、または判定できない
    ときは None。main は `git worktree list` の先頭 (git が common dir から求める main worktree)。

    worktree 側の `.git` ファイルは repo が制御するデータで、任意の承認済み repo の git dir を
    名乗れる (common dir の一致だけで信じると、同じバイト列の verify.sh を置いた任意の
    ディレクトリで承認済みゲートが走る)。そこで「main の管理領域 (<common>/worktrees/*) に
    この path が登録されていること」と「repo の git dir がその登録の管理ディレクトリで、common dir
    が main 自身の git dir であること」(_owns_registration) の両方を要件にする — 一覧は common dir
    側から作られ、偽の `.git` ファイルは自分をそこに載せられない。git が prunable と報告した登録は
    数えない。
    """
    out = _git_out(repo, "worktree", "list", "--porcelain", "-z")
    if out is None:
        return None
    # -z: 各属性が NUL 終端、レコード間は空属性。先頭レコードが main worktree
    records: list[list[str]] = [[]]
    for field in out.split("\0"):
        if field:
            records[-1].append(field)
        elif records[-1]:
            records.append([])
    records = [r for r in records if r and r[0].startswith("worktree ")]
    if len(records) < 2 or "bare" in records[0]:
        return None
    try:
        main = Path(records[0][0].removeprefix("worktree ")).resolve()
        if main == repo:
            return None
        for rec in records[1:]:
            if any(f == "prunable" or f.startswith("prunable ") for f in rec):
                continue
            if Path(rec[0].removeprefix("worktree ")).resolve() == repo:
                return main if _owns_registration(repo, main) else None
    except (OSError, RuntimeError):
        return None
    return None


def ledger_key(repo: Path, data: Ledger) -> tuple[str, bool]:
    """(台帳の key, linked worktree として main の key を引いたか) を返す。

    repo 自身が台帳にあればそれ (通常 repo と、path で直接承認された worktree の挙動は不変)。
    無ければ、repo が登録済みの linked worktree のときだけ main worktree の key を引く。
    """
    if str(repo) in data:
        return str(repo), False
    main = main_checkout_of(repo)
    if main is not None:
        return str(main), True
    return str(repo), False


def verified_bytes(repo_arg: str) -> tuple[Path, bytes] | int:
    """承認と内容を照合し、**照合したバイト列**を返す。失敗なら exit code を返す。

    バイト列を呼び出し側に渡すのが要点 — 照合したものと実行するものを同一にして
    TOCTOU (照合後・実行前の差し替え) を閉じる。

    linked worktree は main worktree の key で引き、照合するのは **worktree 自身の**
    gate のバイト列 (経路の包含判定も worktree の root に対して行う)。hash が違えば 71 でなく
    70 (未承認) — 71 は「承認した repo のゲートが眠った」の意味で、branch 上の編集は
    merge 後に main で承認する (ADR-0059 の 70/71 の意味を変えない)。
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
    data = load_or_empty()
    key, via_main = ledger_key(repo, data)
    entry = data.get(key)
    if not entry:
        print(f"未承認: {gate}", file=sys.stderr)
        return NOT_APPROVED
    if entry.get("sha256") != hashlib.sha256(payload).hexdigest():
        if via_main:
            print(
                f"未承認: {gate} (linked worktree。main worktree {key} の承認済みの版と"
                "内容が違います — merge 後に main で承認してください)",
                file=sys.stderr,
            )
            return NOT_APPROVED
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


def cmd_known(repo_arg: str) -> int:
    """台帳の key 判定だけ。key の引き方は run / check と同じ (ledger_key)。

    ある場合は一致した key を stdout に 1 行出す — linked worktree では repo と key (main
    worktree) が違い、revoke の対象は key の方なので、hook の案内文がこれを使う。
    """
    repo = Path(repo_arg).expanduser().resolve()
    try:
        data = load()
    except LedgerCorrupt as e:
        print(f"台帳が壊れています ({e}): {LEDGER}", file=sys.stderr)
        return LEDGER_CORRUPT
    key, _ = ledger_key(repo, data)
    if key not in data:
        return NOT_APPROVED
    print(key)
    return OK


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
    if cmd in {"check", "known", "approve", "revoke"} and len(args) == 1:
        handlers = {
            "check": cmd_check,
            "known": cmd_known,
            "approve": cmd_approve,
            "revoke": cmd_revoke,
        }
        return handlers[cmd](args[0])
    print(__doc__, file=sys.stderr)
    return USAGE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
