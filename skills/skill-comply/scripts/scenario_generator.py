"""Generate pressure scenarios from skill + spec using LLM."""

from __future__ import annotations

import secrets
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from scripts.parser import extract_yaml_payload
from scripts.spec_generator import GENERATION_TIMEOUT_SECONDS, UTILITY_SETTINGS

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@dataclass(frozen=True)
class Scenario:
    id: str
    level: int
    level_name: str
    description: str
    prompt: str
    setup_commands: tuple[str, ...]
    #: Fixture files as (relative path, content) pairs — data, not commands.
    #: The generator kept reaching for `cat > f << EOF` because the two-verb
    #: setup vocabulary cannot express content, and every such entry was refused
    #: (6 refusals in one real run), leaving sandboxes empty and one agent
    #: writing its own 15KB fixture. The invariant that matters is "no shell, no
    #: process, paths confined and inert" — not "no content" — so content gets a
    #: route that starts no process instead of pressure to smuggle one.
    files: tuple[tuple[str, str], ...] = ()


def generate_scenarios(
    skill_path: Path,
    spec_yaml: str,
    model: str = "haiku",
) -> list[Scenario]:
    """Generate 3 scenarios with decreasing prompt strictness.

    Calls claude -p with the scenario_generator prompt, parses YAML output.
    """
    skill_content = skill_path.read_text()
    prompt_template = (PROMPTS_DIR / "scenario_generator.md").read_text()
    # The audited file is untrusted input, so it is fenced with a nonce the
    # document cannot predict and therefore cannot close to escape its block.
    # A fixed delimiter (the old `---`) is reproduced by ordinary markdown
    # frontmatter, which is how an imported skill could address the generator
    # directly and dictate the setup_commands it emits (security scan F2, F3).
    nonce = f"<<<AUDITED-DOCUMENT-{secrets.token_hex(8)}>>>"
    prompt = (
        prompt_template.replace("{nonce}", nonce)
        .replace("{skill_content}", skill_content)
        .replace("{spec_yaml}", spec_yaml)
    )

    result = subprocess.run(
        [
            "claude",
            "-p",
            prompt,
            "--model",
            model,
            "--output-format",
            "text",
            "--settings",
            UTILITY_SETTINGS,
        ],
        capture_output=True,
        text=True,
        timeout=GENERATION_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr}")

    raw_yaml = extract_yaml_payload(result.stdout)
    parsed = yaml.safe_load(raw_yaml)

    scenarios: list[Scenario] = []
    for s in parsed["scenarios"]:
        scenarios.append(
            Scenario(
                id=s["id"],
                level=s["level"],
                level_name=s["level_name"],
                description=s["description"],
                prompt=s["prompt"].strip(),
                setup_commands=tuple(s.get("setup_commands", [])),
                files=tuple((str(k), str(v)) for k, v in (s.get("files") or {}).items()),
            )
        )

    return sorted(scenarios, key=lambda s: s.level)
