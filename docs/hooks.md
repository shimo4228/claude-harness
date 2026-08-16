# Commit-surface hooks

Five PreToolUse hooks that run at the `git commit` boundary, plus the two parts
they need to work. Several ADRs in [docs/adr/](adr/README.md) argue about the
internals of these scripts — ADR-0027, 0028, 0034, 0035 — so the code is
published here rather than leaving those decisions pointing at nothing.

These are not a framework. They are the hooks one person actually runs, warts
included: the inline comments are in Japanese, so are the stderr messages you
will see when a gate goes quiet, and they date their own bug fixes.

## What each one does

| Script | Fires on | Blocks when | Bypass |
|---|---|---|---|
| [`secret-scan-precommit.sh`](../hooks/secret-scan-precommit.sh) | Bash command containing `git … commit` | A line the command **will commit** looks like a credential. Prefers `detect-secrets`, falls back to regex | `SECRET_SCAN_BYPASS=1` |
| [`verify-precommit.sh`](../hooks/verify-precommit.sh) | same | The repo's own `.claude/verify.sh --staged` exits non-zero (other than the codes below) | `VERIFY_BYPASS=1` |
| [`bandit-precommit.sh`](../hooks/bandit-precommit.sh) | same | Staged `.py` trips bandit at `-ll -ii` (MEDIUM severity + MEDIUM confidence) | `BANDIT_SCAN_BYPASS=1` |
| [`ruff-format-precommit.sh`](../hooks/ruff-format-precommit.sh) | same | Staged `.py` fails `ruff format --check`. Checks only, never rewrites | `RUFF_FORMAT_BYPASS=1` |
| [`review-chain-notice.sh`](../hooks/review-chain-notice.sh) | `git … commit`/`revert`/`merge` | Never — injects an advisory asking whether review and verify ran | — |

Bypasses must sit at the **head** of the command string, in env-prefix position
(`SECRET_SCAN_BYPASS=1 git commit -m …`). A substring match anywhere would let a
mention inside a commit message disable the gate.

The scan target is the interesting part of the secret hook. Because PreToolUse
fires *before* the command runs, reading the staged diff would see nothing at all
for `git commit -am` or `git add -A && git commit` — which is exactly how it sat
silent until a 2026-07-25 scan caught it. The target is now derived from what the
command is about to commit: staged content, plus tracked modifications when `-a`
is present, plus untracked files when `add -A` / `add .` / `add <path>` is.

Three shared parts ship alongside:

- [`hooks/_git-target-common.sh`](../hooks/_git-target-common.sh) — works out
  which repos a command will commit to. Drops backslash escapes and quoted spans
  before splitting on segment boundaries, because bash does not interpret quotes
  and a crafted commit message could otherwise redirect the scan at a repo of the
  attacker's choosing. It returns **every** matching repo, not one: with a single
  answer, `git -C a commit … && git -C b commit …` leaves one side unexamined,
  and picking the left or the right just decides which side an attacker puts the
  secret on. The three read-only hooks scan all of them.
- [`hooks/_advisory-common.sh`](../hooks/_advisory-common.sh) — the single
  implementation of the envelope a hook uses to pass a string to the model:
  `{"hookSpecificOutput": {"hookEventName": …, "additionalContext": …}}`. Plain
  stdout stops at the transcript and a top-level `additionalContext` is not read
  either — **both fail silently** (the hook exits 0, the tests pass, and only the
  string disappears), which is why the envelope is a function rather than prose
  telling you to copy a precedent. `review-chain-notice.sh` and
  `verify-precommit.sh` source it; `systemMessage` and `decision`/`reason` are
  separate channels and stay top-level.
- [`scripts/hooks/verify_allow.py`](../scripts/hooks/verify_allow.py) — the
  approval ledger described below.

`bandit-precommit.sh` and `ruff-format-precommit.sh` **stand down entirely** in a
repo with an executable `.claude/verify.sh`, on the theory that a repo which owns
its gate should not have tool choices imposed from outside. Note what that means
together with the approval model below: in a repo whose gate you have **not**
approved, all three Python-side gates are off at once — verify because it will
not run an unapproved gate, bandit and ruff because they defer on the mere
presence of one. Each says so on stderr; none of them blocks.

## Requirements

- `git` and `jq` — every hook parses its stdin with `jq`.
- `python3` — required unconditionally only by `verify-precommit.sh`, which runs
  the ledger through it. The other scanners reach for it only when assembling a
  block message, and each degrades to a plain-text reason if that fails, so a
  finding is never dropped because JSON assembly broke.
- `timeout` or `gtimeout` — optional, and worth knowing about: the verify gate is
  capped at 120 s only when one of them exists. macOS ships neither by default
  (both come from Homebrew coreutils), in which case the gate runs uncapped.
- `detect-secrets` — optional. `secret-scan-precommit.sh` uses it when it is on
  `PATH`, and otherwise falls back to a built-in regex pass, so the gate always
  runs in some form.
- `bandit`, `ruff` — optional. Those two hooks resolve their tool via `PATH`,
  then `uvx` (found on `PATH` or at `~/.local/bin/uvx`, since a hook subprocess
  need not inherit an interactive shell's `PATH`), pinning a version to keep the
  supply chain fixed. If neither resolves they **fail soft**: the commit is
  allowed and a line goes to stderr. Binaries inside the repo's own `.venv` are
  deliberately never searched — that is an arbitrary-code-execution path from a
  cloned repo, the same reasoning as the approval ledger below.
- `bats` — only to run the tests.

## Install

The hooks resolve their shared parts relative to their own location, and
`verify-precommit.sh` hardcodes `$HOME/.claude/scripts/hooks/verify_allow.py`.
**Install under `~/.claude` or the verify gate silently stops running** — it
cannot find its ledger, so it warns on stderr and allows every commit.

```bash
git clone https://github.com/shimo4228/claude-harness.git ~/.claude-harness
mkdir -p ~/.claude/hooks ~/.claude/scripts/hooks ~/.claude/tests
cp ~/.claude-harness/hooks/*.sh          ~/.claude/hooks/
cp ~/.claude-harness/scripts/hooks/*.py  ~/.claude/scripts/hooks/
cp ~/.claude-harness/tests/*.bats        ~/.claude/tests/   # optional
```

Then merge this into the `hooks` key of `~/.claude/settings.json`. Nothing in it
is machine-specific — the paths are `~`-relative and work as written. If a
`PreToolUse` entry with matcher `Bash` already exists, append these to its
`hooks` array rather than adding a second entry.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash ~/.claude/hooks/secret-scan-precommit.sh" },
          { "type": "command", "command": "bash ~/.claude/hooks/verify-precommit.sh" },
          { "type": "command", "command": "bash ~/.claude/hooks/bandit-precommit.sh" },
          { "type": "command", "command": "bash ~/.claude/hooks/ruff-format-precommit.sh" },
          { "type": "command", "command": "bash ~/.claude/hooks/review-chain-notice.sh" }
        ]
      }
    ]
  }
}
```

Adopt them one at a time if you prefer — they share no state, and each is quiet
in a repo that gives it nothing to check. The one exception is
`verify-precommit.sh` in a repo with an unapproved gate: it prints a reminder on
every commit until you approve or remove the gate.

## The verify gate needs your approval first

`verify-precommit.sh` knows no languages and no tools. If the repo has
`.claude/verify.sh`, it runs `.claude/verify.sh --staged` and reads only the
exit code: `0` pass, `2` unable to check (allowed through, but noisy on stderr),
**any other non-zero** blocks the commit. Keeping tool names out of the harness
keeps the harness from going stale as tooling turns over. Exit codes 70–73 are
reserved for the ledger's own refusals and never mean "your code is bad"; a
timeout (124/137) allows the commit and reports that the gate broke its
contract of returning in seconds.

That means a hook executes a script that lives inside the repo — and hooks run
without a permission prompt, so merely cloning a repo would otherwise be enough
to get its code executed. `verify_allow.py` closes that with a
`direnv allow`-style content hash: only a version whose SHA-256 a human has
recorded gets run, and the bytes that were checked are the bytes that execute
(no re-read between check and run).

Until you approve it, the gate does not run and the commit is not blocked:

```bash
# read the gate first, then:
python3 ~/.claude/scripts/hooks/verify_allow.py approve /path/to/repo
python3 ~/.claude/scripts/hooks/verify_allow.py list
python3 ~/.claude/scripts/hooks/verify_allow.py revoke /path/to/repo
```

Editing `verify.sh` invalidates the approval, so you re-read and re-approve.
The ledger lives at `~/.claude/verify-allow.json`, outside every repo it governs.

**What this does not protect against.** The ledger is unsigned plaintext, so any
process running as you can forge an approval. An attacker at that level can
rewrite `~/.claude/hooks` too. The threat model is untrusted *repository
content*, not a compromised local account — the same trust level as `~/.zshrc`.

## Tests

```bash
bats ~/.claude/tests/
```

All five hooks are covered, plus the shared extractor. The tests hardcode
`$HOME/.claude/hooks/…`, so they only pass after the install above, and they
invoke each hook as `bash <path>` — the way `settings.json` does — rather than
depending on a mode bit that production never consults.

| Test | Pins |
|---|---|
| `git-target-extraction.bats` | Repo extraction: the quoted-span and escaped-quote hijacks, the `git -C … add && git -C … commit` spelling, and that a compound commit yields *both* targets in either order |
| `secret-scan-precommit.bats` | That the scan target comes from what the command will commit rather than from what is staged when the hook fires; that a hostile `diff.external` or `diff.textconv` neither runs nor blinds the scan; that a secret in either half of a compound commit is caught |
| `verify-precommit.bats` | That an unapproved gate is **never executed** and never blocks; that editing a gate revokes its approval; that a gate symlinked outside the repo is refused; that any unexpected non-zero exit blocks rather than waving the commit through; and that the gate is handed `--staged`, the repo root as cwd, and `VERIFY_REPO_ROOT` |
| `bandit-precommit.bats` | That the **index** is scanned rather than the working tree; that MEDIUM+ blocks while LOW does not; that an executable `.claude/verify.sh` triggers the stand-down and a non-executable one does not; fail-soft when no scanner resolves |
| `ruff-format-precommit.bats` | That a blocked commit leaves the working tree and index byte-identical (check only, never rewrite); that the repo's own `ruff.toml` / `pyproject.toml` is honoured; that each repo of a compound commit is judged by its own config |
| `review-chain-notice.bats` | Which command shapes trigger the advisory |

Every claim above was checked with a negative control — the hook was mutated to
remove the property, and the test confirmed to fail against the mutant. A test
that also passes against the broken version is pinning nothing, which is easy to
ship by accident and impossible to notice later.

One honest exception, found that way: `bandit-precommit.sh` and
`ruff-format-precommit.sh` ask git only for `diff --name-only` and
`git show :<path>`, and **neither converts content**, so their `--no-textconv`
tests pass with the flag removed. The flag and its test are kept there as
defence in depth for the day either grows a content diff. In
`secret-scan-precommit.sh`, which does diff content, the vector was live and the
test does pin the fix.

## Not published here

The live harness runs other hooks that are omitted on purpose, because they only
fire inside `~/.claude` itself or encode this setup's private wiring: a harness
config linter, episode-log read guards, a terminal-multiplexer state hook, and a
naming reminder. The non-commit surface (bash-command validation, docs
pre-write checks, test auto-run, usage logging) is a separate judgement and is
not published yet. The reasoning is [ADR-0038](adr/0038-publish-curated-commit-hooks.md).

Some published comments still point at files that stay private: a security rule
under `rules/common/` that carries no reusable content, working notes under
`.notes/`, ticket IDs from a private ledger (`T-…`), and two retired or
unpublished sibling hooks (`ruff-autofix.sh`, `bats-autorun.sh`). The comments
are left as written rather than sanitised, since editing code on the way out
would make the published copy diverge from the one that actually runs.
