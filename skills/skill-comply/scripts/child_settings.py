"""The permission envelope every `claude -p` child this tool starts runs inside.

One module because there are three kinds of child — the scenario agent under
test, the spec/scenario generators, and the trace classifier — and all three
receive text derived from an audited .md file that the user did not necessarily
write. They need the same floor.
"""

from __future__ import annotations

import json

#: Tools removed from every child.
#:
#: **`--allowedTools` does not restrict the tool set.** `claude --help` calls it
#: "tool names to allow" — it is an auto-approval list, not a whitelist. A tool
#: left off it is still present and still runs. Measured 2026-08-02 on Claude
#: Code 2.1.220: with `--allowedTools "Read,Glob,Grep"` and no config anywhere in
#: the sandbox, the child called Bash and `uname -sr` executed on the host,
#: reproducibly. Unchanged by `--permission-mode` (manual / dontAsk /
#: acceptEdits) and unchanged by `--setting-sources project`, which rules out
#: the user's own allowlist as the cause. `permissions.deny` is the only
#: mechanism found that actually removes a tool, and it also beats a skill's
#: frontmatter `allowed-tools`.
#:
#: This invalidated the mitigation recorded for security scan F3/F4 (2026-07-25):
#: `DEFAULT_ALLOWED_TOOLS` narrowed nothing, and `--allow-bash` was not an opt-in
#: because Bash was never off.
#:
#: Why each entry, given the child's default set is Agent / Bash / Edit / Glob /
#: Grep / Read / ReportFindings / ScheduleWakeup / Skill / ToolSearch / Workflow
#: / Write:
#:
#: - `Bash` — a shell reaches the whole filesystem and the network. This is the
#:   one the trust boundary always claimed was off.
#: - `Agent`, `Workflow` — they start subagents whose tool set this code does not
#:   control, so denying Bash on the parent alone is not containment.
#: - `ToolSearch` — it loads deferred tools on demand, and the child inherits the
#:   user's MCP servers. Left in, an audited document could reach mail, drive,
#:   calendar or browser tools through it.
#: - `ScheduleWakeup` — it schedules execution that outlives the measurement.
#:
#: Deliberately kept: `Read` / `Write` / `Edit` / `Glob` / `Grep` (the work a
#: scenario is supposed to do) and `Skill` (invoking a skill is the behaviour
#: being measured — removing it would measure nothing).
#:
#: A denylist is the weaker shape and this one is known to rot: it enumerates a
#: tool set owned by an external product. When Claude Code ships a new default
#: tool, this list does not know. Re-check it on CLI upgrades — a child that
#: reached for a denied tool and then went looking for another surface is the
#: behaviour to expect (measured: with `Agent` denied, the child fell back to
#: `Skill`).
DENIED_TOOLS: tuple[str, ...] = (
    "Bash",
    "Agent",
    "Workflow",
    "ToolSearch",
    "ScheduleWakeup",
)


def child_settings(*, allow_bash: bool = False, pin_output_style: bool = False) -> str:
    """Build the `--settings` JSON for a child process.

    `allow_bash` removes Bash from the denial rather than adding it to an allow
    list — denial is what has effect, so the opt-in has to work by subtraction.

    `pin_output_style` is for the generator and classifier children only. They
    are measurement utilities, and a user-level output style would wrap their
    machine-readable answer in prose. The scenario child must NOT pin it: what
    that child inherits from the user's own configuration is precisely what is
    under measurement.
    """
    denied = [tool for tool in DENIED_TOOLS if not (allow_bash and tool == "Bash")]
    settings: dict[str, object] = {"permissions": {"deny": denied}}
    if pin_output_style:
        settings["outputStyle"] = "default"
    return json.dumps(settings)
