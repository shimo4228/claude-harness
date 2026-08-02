"""Generate compliance specs from skill files using LLM."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import yaml

from scripts.child_settings import child_settings
from scripts.parser import ComplianceSpec, extract_yaml_payload, parse_spec

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Generator/classifier children are measurement utilities, not the agent under
# test — pin them to the default output style so a user-level style (e.g.
# Explanatory) cannot wrap the machine-readable answer in narrative prose.
#
# They also carry the permission denial. These children matter most for it: the
# generator receives the audited document's RAW BODY, and until 2026-08-02 it ran
# with no `--allowedTools` at all and therefore with a shell available. The nonce
# fence is a prompt-level mitigation; it was standing in front of an agent that
# could reach the network.
UTILITY_SETTINGS = child_settings(pin_output_style=True)

# Generation children get the whole audited document embedded in the prompt;
# a large table-heavy SKILL.md pushed haiku past 120s twice on 2026-07-28.
# The ceiling only bounds hangs — a generous value costs nothing on success.
GENERATION_TIMEOUT_SECONDS = 600


def generate_spec(
    skill_path: Path,
    model: str = "haiku",
    max_retries: int = 2,
    save_to: Path | None = None,
) -> ComplianceSpec:
    """Generate a compliance spec from a skill/rule file.

    Calls claude -p with the spec_generator prompt, parses YAML output.
    Retries on YAML parse errors with error feedback.

    When save_to is given, the raw generated YAML is written there and kept
    (successful spec persists for --spec reuse; a failed final attempt leaves
    its YAML behind for debugging). Otherwise a tempfile is used and removed.
    """
    skill_content = skill_path.read_text()
    prompt_template = (PROMPTS_DIR / "spec_generator.md").read_text()
    base_prompt = prompt_template.replace("{skill_content}", skill_content)

    last_error: Exception | None = None

    if save_to is not None:
        save_to.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries + 1):
        prompt = base_prompt
        if attempt > 0 and last_error is not None:
            prompt += (
                f"\n\nPREVIOUS ATTEMPT FAILED with YAML parse error:\n"
                f"{last_error}\n\n"
                f"Please fix the YAML. Remember to quote all string values "
                f'that contain colons, e.g.: description: "Use type: description format"'
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

        if save_to is not None:
            save_to.write_text(raw_yaml)
            spec_path = save_to
        else:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".yaml",
                delete=False,
            ) as f:
                f.write(raw_yaml)
                spec_path = Path(f.name)

        try:
            return parse_spec(spec_path)
        except (yaml.YAMLError, KeyError, TypeError, ValueError) as e:
            last_error = e
            if attempt == max_retries:
                raise
        finally:
            if save_to is None:
                spec_path.unlink(missing_ok=True)

    raise RuntimeError("unreachable")
