#!/usr/bin/env python3
"""claims.py — セッション横断のタスク claim / 系譜ジャーナル。

`.notes/TASKS.md`（rule: common/task-tracking.md が規定する repo ごとの単一台帳）は
共有可変ファイルで、gitignored のため git の履歴も conflict 検出も無い。並行セッションが
read-modify-write すると後から書いた方が黙って前の編集を消し、しかも「誰が着手中か」を
書く列が無いので同じタスクを 2 セッションが始める。

本ツールは台帳を**置き換えず**、追記専用のジャーナル `.notes/claims.jsonl` を足す。
追記しかしないので、既存バイトに誰も触らず、上書きによる消失が原理的に起きない
（同じ形を contemplative-agent の audit.jsonl が採っている）。

状態の正本は台帳のまま。ジャーナルの正本は「誰が握っているか」と「何から生まれたか」。

台帳の形は 2 つある。単一表 `.notes/TASKS.md`（小さい repo）と、1 タスク 1 ファイルの
store（frontmatter に `state:`、本文は自由。並行編集で他タスクが消えない置き方 —
2026-08-16 に contemplative-agent の 3 層機構を退役してこの形だけを残した）。
store の家は公開 `rfcs/NNNN-slug.md`（ID は stem 先頭 4 桁から `RFC-NNNN`。本文の推奨
様式は Rust RFC テンプレ準拠 — 正本は skill: task-stocktake、判断は ADR-0049/0050）。
旧 `.notes/tasks/` の dual-read は 2026-08-25 に畳んだ（RFC-0001 完了）。`ready` は
store を読んで着手可能なものだけを列挙する。台帳を読む機能はこれで全部で、描画も読み戻しも
状態機械も持たない（それらを持った版が 2 日で 5,000 行になり、そのバグを
直し続ける形になった）。

    claims.py claim   T-FOO [--label ...] [--note ...] [--force]
    claims.py release T-FOO --outcome done|abandoned|handoff [--commit SHA]
    claims.py spawn   T-FOO --origin review|gate|instrument|idea|incident
                            [--producer PATH:LINE]...   # review 由来では必須
                            [--parent T-BAR] [--commit SHA]
    claims.py open [--oneline]
    claims.py ready [--state STATE]     # store 形式の repo で、着手可能なタスク

exit code: 0 成功 / 1 入力が契約を満たさない（不正な task id・--producer 欠落や形式違反）/
          2 argparse が弾いた使い方の誤り / 3 他セッションが握っている（--force で上書き可）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

EVENTS = ("claim", "release", "spawn")
OUTCOMES = ("done", "abandoned", "handoff")
ORIGINS = ("review", "gate", "instrument", "idea", "incident")

# review 由来の起票だけ、指摘が名指す値を**書いているコード**の引用を要求する。
# 真偽は検査しない — それは起票する側の仕事で、ここが検査できるのは形だけ。
# 形だけでも効くのは、消えるのが「見に行くより起票する方が安い」経路だから
# (2026-08-16: T-PACKET-FLOOR-BYPASS は誰も読んでいない producer と共に起票され、
# weekly-pipeline.sh:850 を 1 回 grep すれば消えていた)。
# 行番号を必須にするのは「このファイルのどこか」を弾くため — それはファイルを
# 開いていない者が書く形。範囲 (`:340-352`) は許す: 引用は 1 行で足りないことがある。
PRODUCER_REQUIRED_ORIGINS = ("review",)
# `\Z` でなく `$` にすると末尾改行 1 個の手前でも一致する (f0f8c53 が _TASK_ID_RE で
# 同じ穴を閉じた)。今日は表示 sink が無いので実害は無いが、同じ誤りを 2 度書かない。
_PRODUCER_RE = re.compile(r"^[^\s:]+:\d+(?:-\d+)?\Z")

# lease: claim 時に期限を**宣言する**。期限切れは「引き継いでよい」の機械判定で、
# 相手の生存確認を要さないので check-then-act にならない。ここが下の STALE_HOURS と
# 決定的に違う点で、だから lease だけが引き継ぎの根拠になれる。
# それでも自動 release はしない — 期限切れは印であって、奪うのは次の claim の意思表示。
LEASE_HOURS = 24

# lease を持たない旧 record 向けの後方互換。期限が宣言されていない以上「切れた」とは
# 言えないので、印を付けるだけで引き継ぎの根拠にはしない。解除を「生存確認 → 解除」で
# 判断すると check-then-act になり、それ自体が本ツールの直したい race と同じ形になる。
STALE_HOURS = 24

# T- は自由命名のタスク、RFC- は rfcs/ store のエントリ（ADR-0049）。どちらも同じ
# claim / spawn / ready の機構に乗る — 語彙も店舗も 1 つのままにするための同型扱い。
_TASK_RE = re.compile(r"^(?:T|RFC)-[A-Z0-9][A-Z0-9-]*$")

# `open --oneline` の上限。この 1 行は hook 経由でエージェントの文脈に入るので、
# 攻撃者が長さを選べる面をひとつも残さない（security review HIGH の詳細は cmd_open）。
_ONELINE_MAX_ID = 32
_ONELINE_MAX_ITEMS = 10
_ONELINE_MAX_CHARS = 2048

# 表示前に潰す文字。C0 全域 + DEL + C1 + 行区切り + ZWSP/bidi。
_UNSAFE_RE = re.compile(r"[\x00-\x1f\x7f-\x9f  ​-‏‪-‮⁦-⁩]")


def safe(text: object) -> str:
    """自由記述を 1 行の表示可能テキストへ潰してから print する。

    `label` / `note` は設計上の自由文字列で、外部由来の引用（上流 PR のタイトル、
    エラー出力、貼り付けたログ）を持つ。この出力は hook 経由でエージェントの
    文脈に入るので、行を跨げれば偽の `[claims]` 行や偽の `[system]` 行を作れる。
    自由記述である以上、検証でなく脱字化で閉じる（2026-08-15 security review HIGH）。
    """
    return " ".join(_UNSAFE_RE.sub(" ", str(text)).split())


def repo_root() -> Path:
    """台帳のある repo root。CLAUDE_PROJECT_DIR → git → cwd の順で解決する。"""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and Path(env).is_dir():
        return Path(env)
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd()


def journal_path(root: Path) -> Path:
    return root / ".notes" / "claims.jsonl"


def ledger_path(root: Path) -> Path:
    return root / ".notes" / "TASKS.md"


UNKNOWN_SESSION = "unknown"


def session_id() -> str:
    """環境が与えるセッション UUID。名乗らせると嘘も表記揺れも起きる。

    Claude Code は必ず与えるが、ADR-0015 の cross-agent 構成（Codex / agy /
    素のシェル）は与えない。その場合は全員が同じ `unknown` になるので、
    `held.get("session") != me` が偽になり相互排他が黙って無効化される
    （2026-08-15 code review MEDIUM、実証済み）。呼び出し側は
    `is_unknown()` で「自分自身とも一致しない」扱いにする。
    """
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or UNKNOWN_SESSION


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _needs_leading_newline(path: Path) -> bool:
    """前の追記が途中で落ちて改行を欠いたか。"""
    try:
        with path.open("rb") as handle:
            if handle.seek(0, 2) == 0:
                return False
            handle.seek(-1, 2)
            return handle.read(1) != b"\n"
    except OSError:
        return False


def append(root: Path, record: dict) -> None:
    """1 イベント = 1 回の追記 = 1 行。

    追記専用の並行安全性は「誰も既存バイトに触らない」ことだけに依存している。
    書き換え・圧縮・重複排除を一切しないのはそのため。

    `ensure_ascii=True` は可読性のためでなく**正しさのため**: False だと
    U+0085 / U+2028 / U+2029 が生バイトで出て、`read_events` 側の行分割が
    そこをレコード境界と誤読する。書き手と読み手の行の文法が食い違うと、
    `--note` に貼り付けられた 1 文字（web からのコピー、Windows 系ツール出力）が
    claim を丸ごと消し、2 セッションが同じタスクを握る（2026-08-15 security
    review HIGH、実証済み）。

    末尾に改行が無ければ先に 1 つ足す。落ちた書き込みの断片へ次の行を連結すると、
    壊れるのは 1 行でなく 2 行になる。追記しかしない性質は保たれる。
    """
    path = journal_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=True) + "\n"
    # O_NOFOLLOW: `open("a")` は symlink を辿るので、`.notes/claims.jsonl` を
    # 任意のファイルへ向けた repo が claim 1 回でそこへ追記させられた
    # （2026-08-15 security review MEDIUM、実証済み）。tasks.py の `_atomic_write`
    # は同じ理由で `os.replace` を使っているのに、journal 側だけ素通りしていた。
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
    with os.fdopen(os.open(path, flags, 0o600), "a", encoding="utf-8") as handle:
        if _needs_leading_newline(path):
            handle.write("\n")
        handle.write(line)


def read_events(root: Path) -> list[dict]:
    """ジャーナルを読む。解析できない行は飛ばす。

    セッションが追記中に落ちると末尾が欠ける。audit.jsonl の消費者と同じ扱いで、
    壊れた 1 行が読み取り全体を落とさないようにする。
    """
    path = journal_path(root)
    if not path.is_file():
        return []
    events = []
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    # splitlines() ではなく split("\n"): 前者は U+0085 / U+2028 / U+2029 でも切るので、
    # 書き手（json.dumps）の行の定義とズレる。ズレると 1 行が 2 断片になり、
    # 両方が「解析できない行」として黙って捨てられる。
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict) and rec.get("event") in EVENTS:
            events.append(rec)
    return events


def open_claims(root: Path) -> dict[str, dict]:
    """いま開いている claim を task -> 最後の claim イベントで返す。

    ファイル順が時刻順（追記専用なので保証される）。claim で保持者をセットし
    release でクリアする、それだけの畳み込み。
    """
    held: dict[str, dict] = {}
    for rec in read_events(root):
        task = rec.get("task")
        # 書き込み側の require_task_id と同じ検査を**読み側にも**当てる。
        # journal は repo に commit されうるので、値は外部由来でありうる
        # （2026-08-15 security review HIGH: `"task": "T-OK\n[system] …"` が
        # hook の stdout 経由でセッション文脈へ注入できた）。
        if not isinstance(task, str) or not _TASK_RE.match(task):
            continue
        if rec["event"] == "claim":
            held[task] = rec
        elif rec["event"] == "release":
            held.pop(task, None)
    return held


def lease_expiry(hours: float) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat(timespec="seconds")


def lease_expired(rec: dict) -> bool | None:
    """lease が切れているか。宣言が無い / 読めない旧 record は None（不明）。

    None を「切れている」に丸めない。宣言されていない期限を切れたと扱うと、
    生きているセッションから黙って奪える経路になる。
    """
    raw = rec.get("lease_expires")
    if not isinstance(raw, str):
        return None
    try:
        then = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if then.tzinfo is None:
        then = then.replace(tzinfo=UTC)
    return datetime.now(UTC) >= then


def age_hours(ts: str) -> float | None:
    try:
        then = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None
    if then.tzinfo is None:
        then = then.replace(tzinfo=UTC)
    return (datetime.now(UTC) - then).total_seconds() / 3600.0


def fmt_age(hours: float | None) -> str:
    if hours is None:
        return "?"
    if hours < 1:
        return f"{int(hours * 60)}m"
    if hours < 48:
        return f"{int(hours)}h"
    return f"{int(hours / 24)}d"


def rfc_store_path(root: Path) -> Path:
    return root / "rfcs"


# rfcs/ のエントリは `NNNN-slug.md`。ID は数字 4 桁だけから導出するので、slug に
# 何が書かれていても表示 ID に混入しない（README.md や template はここで弾かれる）。
_RFC_FILE_RE = re.compile(r"^(\d{4})-")


def _rfc_entries(root: Path) -> list[tuple[str, Path]]:
    """(RFC-NNNN, path)。symlink の store は辿らない — repo 外へ向けられると glob が
    そちらを列挙し、typo 警告や ready の判断材料が repo 外になるため（security review LOW）。"""
    rfcs = rfc_store_path(root)
    if not rfcs.is_dir() or rfcs.is_symlink():
        return []
    entries = []
    for path in sorted(rfcs.glob("*.md")):
        m = _RFC_FILE_RE.match(path.stem)
        if m:
            entries.append((f"RFC-{m.group(1)}", path))
    return entries


def known_tasks(root: Path) -> set[str]:
    """起票済みの ID。claim 時の typo を捕まえるためだけに使う。

    store（rfcs/）を先に見て単一表（TASKS.md）との**和**を取る: store を持たない
    repo（単一表のまま）では表だけが答え、どちらか一方にしかない ID も既知として通る。
    旧 store `.notes/tasks/` の dual-read は 2026-08-25 に畳んだ（全 repo で移送完了 +
    CA weekly-pipeline の書き先を rfcs/ へ変更 — RFC-0001）。
    """
    known: set[str] = set()
    known |= {task for task, _path in _rfc_entries(root)}
    path = ledger_path(root)
    if not path.is_file():
        return known
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return known
    return known | set(re.findall(r"^\|\s*((?:T|RFC)-[A-Z0-9-]+)\s*\|", raw, re.MULTILINE))


def require_task_id(task: str) -> str:
    if not _TASK_RE.match(task):
        sys.exit(f"Error: task id の形式が不正です: {task!r} (例: T-ADOPT-HOLD / RFC-0001)")
    return task


def cmd_claim(args: argparse.Namespace, root: Path) -> int:
    task = require_task_id(args.task)
    me = session_id()
    if not 0 <= args.lease_hours <= 720:
        sys.exit("Error: --lease-hours は 0〜720（30 日）の範囲で指定する")
    held = open_claims(root).get(task)
    # `unknown` は自分自身とも一致しない扱いにする（session_id の docstring）。
    # 引き継ぎの痕跡。claim record は畳み込みで前の保持者を**消す**ので、記録しないと
    # 「引き継がれた」と「最初からこのセッションが握っていた」がジャーナルから
    # 区別できない。追記専用なので前の claim 行自体は残るが、それを読むには全件を
    # 畳み直す必要がある。
    #
    # 読み手は **生ジャーナルを後から読む人間 / セッション**。`open` にも hook にも
    # 出さないのは意図で、あの 1 行は攻撃者が長さを選べる面をひとつも持てない
    # （下の上限群の理由）。表示側の consumer を足すなら `open` の非 oneline 側へ。
    takeover: dict[str, str] | None = None
    if held is not None and (held.get("session") != me or me == UNKNOWN_SESSION):
        age = fmt_age(age_hours(held.get("ts", "")))
        label = held.get("label") or "(label なし)"
        if lease_expired(held) is True:
            # 期限切れ = 宣言された期限を過ぎたということ。生存確認は要らない。
            print(
                f"Note: {task} の lease は期限切れ（前保持者 {safe(held.get('session'))} / {age} 前）。"
                "引き継ぎます。",
                file=sys.stderr,
            )
            takeover = {"from": safe(held.get("session"))[:64], "reason": "lease-expired"}
        elif args.force:
            takeover = {"from": safe(held.get("session"))[:64], "reason": "force"}
        else:
            print(
                f"Error: {task} は別セッションが {age} 前から握っています "
                f"— session={safe(held.get('session'))} {safe(label)}",
                file=sys.stderr,
            )
            print(
                "  引き継ぐなら --force。相手が生きているかは ListAgents / SendMessage で確認できます"
                "（offline の Remote Control セッションは返事ができないので、生存確認は補助です）。",
                file=sys.stderr,
            )
            return 3
    known = known_tasks(root)
    if known and task not in known:
        print(
            f"Warning: {task} は台帳に見当たりません（typo か、まだ起票していない）",
            file=sys.stderr,
        )
    rec = {
        "ts": now_iso(),
        "event": "claim",
        "task": task,
        "session": me,
        "lease_expires": lease_expiry(args.lease_hours),
    }
    if takeover is not None:
        rec["stolen_from"] = takeover["from"]
        rec["takeover"] = takeover["reason"]
    if args.label:
        rec["label"] = args.label
    if args.note:
        rec["note"] = args.note
    append(root, rec)
    print(f"claimed {task}")
    return 0


def cmd_release(args: argparse.Namespace, root: Path) -> int:
    task = require_task_id(args.task)
    me = session_id()
    held = open_claims(root).get(task)
    if held is None:
        print(
            f"Warning: {task} に開いている claim がありません（二重 release か、claim 忘れ）",
            file=sys.stderr,
        )
    elif held.get("session") != me and not args.force:
        # claim は exit 3 で拒むのに release が通ると、gate は迂回できる:
        # 他セッションの claim を release すれば open_claims から消え、次の claim が
        # 素通りする。保持者には何の合図も出ない（2026-08-15 security review HIGH、実証済み）。
        print(
            f"Error: {task} を握っているのは別セッション ({safe(held.get('session'))}) です。"
            "他セッションの claim を手放すなら --force。",
            file=sys.stderr,
        )
        return 3
    rec = {
        "ts": now_iso(),
        "event": "release",
        "task": task,
        "session": me,
        "outcome": args.outcome,
    }
    if args.commit:
        rec["commit"] = args.commit
    if args.note:
        rec["note"] = args.note
    append(root, rec)
    print(f"released {task} ({args.outcome})")
    return 0


def require_producers(origin: str, producers: list[str]) -> list[str]:
    """review 由来の起票に、値を書いているコードの `path:line` 引用を要求する。"""
    for p in producers:
        if not _PRODUCER_RE.match(p):
            sys.exit(
                f"Error: --producer は path:line の形で書きます: {p!r} "
                "(例: scripts/weekly-pipeline.sh:850、範囲なら :340-352)"
            )
    if origin in PRODUCER_REQUIRED_ORIGINS and not producers:
        sys.exit(
            f"Error: --origin {origin} の起票には --producer path:line が要ります。\n"
            "  指摘が名指す値を**書いているコード**を 1 回読んで、その行を引用してください。\n"
            "  読んだ結果その値が固定されていたなら、それは起票でなく破棄の材料です\n"
            "  (commit message に 1 行残す)。"
        )
    return producers


def cmd_spawn(args: argparse.Namespace, root: Path) -> int:
    task = require_task_id(args.task)
    producers = require_producers(args.origin, args.producer)
    rec = {
        "ts": now_iso(),
        "event": "spawn",
        "task": task,
        "session": session_id(),
        "parent": require_task_id(args.parent) if args.parent else None,
        "origin": args.origin,
    }
    if producers:
        rec["producers"] = producers
    if args.commit:
        rec["commit"] = args.commit
    if args.note:
        rec["note"] = args.note
    append(root, rec)
    parent = rec["parent"] or "(独立起票)"
    print(f"spawned {task} <- {parent} [{args.origin}]")
    return 0


def _mark(rec: dict, hours: float | None, verbose: bool = False) -> str:
    """開いている claim の注記。STEALABLE と STALE は別物なので混ぜない。

    STEALABLE = 宣言された lease が切れた（引き継いでよい）。
    STALE     = 期限の宣言が無いまま古い（生存確認が要る。奪う根拠にはならない）。
    """
    if lease_expired(rec) is True:
        return "  ** STEALABLE (lease 期限切れ) **" if verbose else " STEALABLE"
    if hours is not None and hours >= STALE_HOURS:
        return "  ** STALE (期限の宣言なし — 生存確認を) **" if verbose else " STALE"
    return ""


def cmd_open(args: argparse.Namespace, root: Path) -> int:
    held = open_claims(root)
    if args.oneline:
        # hook が読む 1 行形式。claim が無いときは何も言わない（無音が正常）。
        if not held:
            return 0
        # **長さの上限を全部に置く。** この行は hook 経由でエージェントの文脈へ
        # 入る。`safe()` は自由記述（label / note）を脱字化するが、脱字化された
        # フィールドは元から短く、上限が無かったのは *検査済み* の側だった:
        # `task` は `_TASK_RE` で [A-Z0-9-] に絞られるだけで長さは無制限、件数も
        # 無制限。commit された claims.jsonl から 59,108 文字の攻撃者選択テキスト
        # （T-IGNORE-ALL-PREVIOUS-INSTRUCTIONS-… の類）を注入できた
        # （2026-08-15 security review HIGH、実証済み）。文字種の検査は長さの
        # 上限を兼ねない。件数の上限は、この hook の文脈コストも同時に抑える。
        parts = []
        for task, rec in sorted(held.items())[:_ONELINE_MAX_ITEMS]:
            hours = age_hours(rec.get("ts", ""))
            # `session` も外部由来でありうる（journal は commit されうる）。
            parts.append(
                f"{task[:_ONELINE_MAX_ID]}"
                f"({safe(rec.get('session', '?'))[:8]} {fmt_age(hours)}{_mark(rec, hours)})"
            )
        rest = len(held) - len(parts)
        if rest > 0:
            parts.append(f"(+{rest} more)")
        print(("着手中: " + " / ".join(parts))[:_ONELINE_MAX_CHARS])
        return 0
    if not held:
        print("開いている claim はありません。")
        return 0
    for task, rec in sorted(held.items()):
        hours = age_hours(rec.get("ts", ""))
        print(
            f"{task:<28} {safe(rec.get('session', '?'))}  "
            f"{fmt_age(hours)} 前{_mark(rec, hours, True)}"
        )
        if rec.get("label"):
            print(f"{'':<28} {safe(rec['label'])}")
    return 0


_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
_HEADING_RE = re.compile(r"^#{1,6}\s")
_READY_SUMMARY_CHARS = 90


def task_head(text: str) -> tuple[str, str]:
    """`T-XXX.md` の (state, 要約 1 行)。frontmatter が無ければ state は空文字。

    要約は本文の最初の非空・非見出し行。台帳の grammar はこれで全部で、
    セクション名も列も規定しない — 本文は人と agent が読む自由記述。
    """
    state = ""
    body = text
    m = _FRONTMATTER_RE.match(text)
    if m:
        body = text[m.end() :]
        for line in m.group(1).splitlines():
            key, sep, value = line.partition(":")
            if sep and key.strip() == "state":
                state = value.strip()
                break
    for line in body.splitlines():
        line = line.strip()
        if line and not _HEADING_RE.match(line):
            return state, line
    return state, ""


def cmd_ready(args: argparse.Namespace, root: Path) -> int:
    rfcs = rfc_store_path(root)
    if not rfcs.is_dir() or rfcs.is_symlink():
        print("rfcs/ が無い。この repo は単一表（.notes/TASKS.md）— 直接読む。")
        return 0
    entries: list[tuple[str, Path]] = _rfc_entries(root)
    held = open_claims(root)
    wanted = args.state
    rows: list[tuple[str, str, str]] = []
    for task, path in entries:
        try:
            state, summary = task_head(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        # `done 2026-08-15` のように日付を伴う書き方を許す（先頭語で照合）
        if (state.split() or [""])[0] != wanted:
            continue
        rows.append((task, state, summary))
    if not rows:
        print(f"state: {wanted} のタスクはありません。")
    for task, _state, summary in rows:
        rec = held.get(task)
        mark = ""
        if rec:
            hours = age_hours(rec.get("ts", ""))
            mark = f"  [claimed {safe(rec.get('session', '?'))[:8]} {fmt_age(hours)}]"
        print(f"{task:<34} {safe(summary)[:_READY_SUMMARY_CHARS]}{mark}")
    # 単一表と store が併存する移行期の repo で、store 経路に入った途端に単一表への
    # 誘導が消えると、表の ready 行が黙って隠れる (2026-08-25 実測: harness の T-002)。
    ledger = ledger_path(root)
    if ledger.is_file():
        try:
            raw = ledger.read_text(encoding="utf-8", errors="replace")
        except OSError:
            raw = ""
        if re.search(r"^\|\s*(?:T|RFC)-[A-Z0-9-]+\s*\|", raw, re.MULTILINE):
            print("単一表 .notes/TASKS.md にも行がある — そちらは直接読む。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claims.py", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("claim", help="タスクを握る（着手 / 着手予定を宣言する）")
    p.add_argument("task")
    p.add_argument("--label", help="人間が見分けるための自由記述")
    p.add_argument("--note")
    p.add_argument("--force", action="store_true", help="他セッションの claim を引き継ぐ")
    p.add_argument(
        "--lease-hours",
        type=float,
        default=LEASE_HOURS,
        help=f"占有を宣言する時間（既定 {LEASE_HOURS}）。期限切れは --force なしで引き継げる",
    )
    p.set_defaults(func=cmd_claim)

    p = sub.add_parser("release", help="手放す")
    p.add_argument("task")
    p.add_argument("--outcome", required=True, choices=OUTCOMES)
    p.add_argument("--commit")
    p.add_argument("--note")
    p.add_argument("--force", action="store_true", help="他セッションが握っている claim を手放す")
    p.set_defaults(func=cmd_release)

    p = sub.add_parser("spawn", help="このタスクが生まれたことを記録する")
    p.add_argument("task")
    p.add_argument("--origin", required=True, choices=ORIGINS)
    p.add_argument(
        "--producer",
        action="append",
        default=[],
        metavar="PATH:LINE",
        help=f"指摘が名指す値を書いているコード。{'/'.join(PRODUCER_REQUIRED_ORIGINS)} 由来では必須、複数可",
    )
    p.add_argument("--parent", help="親タスク ID。独立起票なら省略")
    p.add_argument("--commit")
    p.add_argument("--note")
    p.set_defaults(func=cmd_spawn)

    p = sub.add_parser("open", help="いま開いている claim を表示")
    p.add_argument("--oneline", action="store_true", help="hook 用の 1 行形式")
    p.set_defaults(func=cmd_open)

    p = sub.add_parser(
        "ready", help="着手可能なタスクを列挙（rfcs/ / .notes/tasks/ store 形式の repo）"
    )
    # 語彙は 2026-08-25 に標準語へ移行（ADR-0050: ready→accepted 等）。subcommand 名の
    # `ready` は「着手可能なものを問う」動詞句として維持 — hook 文言・docs が広く参照する。
    p.add_argument("--state", default="accepted", help="列挙する state（既定 accepted）")
    p.set_defaults(func=cmd_ready)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args, repo_root())


if __name__ == "__main__":
    sys.exit(main())
