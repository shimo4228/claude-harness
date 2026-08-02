"""Classify what is being measured, and make it visible to the child.

The child's project is the sandbox, so a skill living in some other repo's
`.claude/skills/` does not exist for it. A real run against
`…/contemplative-agent/.claude/skills/apple-silicon-local-llm-serving/SKILL.md`
opened with `Skill(apple-silicon-local-llm-serving)` → `Unknown skill`, and the
report printed 75% / 50% / 25% for an agent that never loaded the thing under
test. Measuring the wrong subject and saying nothing about it is the worst
failure mode this tool has.

What that trace actually shows is a **discovery** failure, not a procedure
failure. Discovery and invocation run off the frontmatter `name` and
`description`; the body is what the agent reads *after* it decides to reach for
the skill. Those separate cleanly, so the fix does too:

- **stub** (default) — real `name` and `description`, inert body. Measures
  whether the agent reached for the skill. The audited body never reaches the
  child.
- **full** (`--load-target-skill`) — the real body. Measures whether the agent
  follows the procedure inside. The document now instructs an unattended agent,
  which is a genuine escalation, so it is opt-in and recorded in the report.

The stub is not a zero-exposure option, and the gap is wider than "one or two
lines". `description` is attacker-controlled text that must reach the child —
that is how discovery works — and a real target measured on 2026-08-02 had a
~500-character description that reads as a summary of its own body (runtime
names, constraints, tradeoffs). The cap below is doing real work, but the honest
claim is "narrower than the whole document", not "safe".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

TargetKind = Literal["global-skill", "project-skill", "document"]

#: The `description` is copied into the sandbox verbatim, so it is the one piece
#: of the audited document that reaches the child even in stub mode. Cap it.
MAX_DESCRIPTION_CHARS = 500

#: A skill is only worth placing if the file is small enough to be one. This also
#: bounds what full mode copies.
MAX_SKILL_BYTES = 512 * 1024

STUB_BODY = """
You have been loaded. State that you loaded the `{name}` skill, then carry on
with the user's task using your own judgement.
""".strip()


@dataclass(frozen=True)
class Target:
    path: Path
    kind: TargetKind
    #: The path exactly as given, before `resolve()`. Kept because resolving
    #: discards the fact that the input WAS a link: `resolve()` follows it, so a
    #: later `path.is_symlink()` always inspects the destination and answers
    #: False. The refusal below has to `lstat` what the user actually pointed at.
    source_path: Path | None = None
    #: The name the child would invoke. None when the target is not a skill.
    skill_name: str | None = None
    description: str = ""

    @property
    def needs_placement(self) -> bool:
        """Is the child unable to find this on its own?

        Global skills live in `~/.claude/skills/`, which every child sees
        regardless of cwd. Project skills belong to a repo the child is not in.
        Rules, agent definitions and loose .md files are not invocable at all —
        nothing to place, and no `Skill` call should be expected of the agent.
        """
        return self.kind == "project-skill"


def _frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---")
    block, sep, _ = rest.partition("\n---")
    if not sep:
        return {}
    try:
        parsed = yaml.safe_load(block)
    except yaml.YAMLError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def classify_target(path: Path, *, global_root: Path | None = None) -> Target:
    """Decide what `path` is and whether the child can reach it unaided.

    Classification is structural — where the file sits and what its frontmatter
    says — because that is what actually governs discovery. It deliberately does
    not try to judge whether the user wrote the file: nothing on disk
    distinguishes "my skill" from "a skill I am auditing", which is why full mode
    is a flag and not an inference.
    """
    resolved = path.resolve()
    home_skills = (global_root or Path.home() / ".claude") / "skills"

    is_skill_file = resolved.name == "SKILL.md" and resolved.parent.name != "skills"
    if not is_skill_file:
        return Target(path=resolved, kind="document", source_path=path)

    front = _frontmatter(resolved)
    name = str(front.get("name") or resolved.parent.name)
    description = str(front.get("description") or "")[:MAX_DESCRIPTION_CHARS]

    try:
        resolved.relative_to(home_skills.resolve())
    except (ValueError, OSError):
        return Target(
            path=resolved,
            kind="project-skill",
            source_path=path,
            skill_name=name,
            description=description,
        )
    return Target(
        path=resolved,
        kind="global-skill",
        source_path=path,
        skill_name=name,
        description=description,
    )


def skill_payload(target: Target, *, full_body: bool) -> tuple[str, str] | None:
    """The `(name, SKILL.md text)` to place in the sandbox, or None if nothing is.

    Full mode copies the SKILL.md file **only**, never the surrounding directory.
    Most skills are a single file, and refusing the rest defers a whole tree of
    validation questions — symlinks, nested `.claude/`, hardlinks, device nodes,
    executable bits — until a real target needs them. A skill that depends on its
    `references/` will measure short in full mode; that is a visible, reportable
    limitation rather than a silent hole.
    """
    if not target.needs_placement or target.skill_name is None:
        return None

    header = yaml.safe_dump(
        {"name": target.skill_name, "description": target.description},
        allow_unicode=True,
        sort_keys=False,
    ).strip()

    if not full_body:
        return (
            target.skill_name,
            f"---\n{header}\n---\n\n{STUB_BODY.format(name=target.skill_name)}\n",
        )

    if target.path.stat().st_size > MAX_SKILL_BYTES:
        raise ValueError(
            f"{target.path} is {target.path.stat().st_size} bytes, over the "
            f"{MAX_SKILL_BYTES} byte cap for --load-target-skill"
        )
    # `target.path` is resolved, so asking IT is always False — check what was
    # actually pointed at, and every directory on the way to it, because a link
    # anywhere in the chain redirects what gets copied.
    original = target.source_path or target.path
    for candidate in (original, *original.parents):
        if candidate.is_symlink():
            raise ValueError(
                f"{candidate} is a symlink; refusing to copy through it into the sandbox"
            )
        if candidate == candidate.parent:
            break
    return target.skill_name, target.path.read_text()
