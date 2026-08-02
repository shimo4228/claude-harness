You are classifying tool calls from a coding agent session against expected behavioral steps.

For each tool call, determine which steps (if any) it belongs to. A tool call may be listed under EVERY step whose detector it genuinely satisfies on its own — a single Text message can, for example, both declare a task type and present a plan.

Steps:
{steps_description}

Tool calls (numbered):
{tool_calls}

Respond with ONLY a JSON object mapping step_id to a list of matching tool call numbers.
Include only steps that have at least one match. If no tool calls match a step, omit it.

Example response (note tool call 5 satisfies two detectors and appears under both steps):
{"write_test": [0, 1], "run_test_red": [2], "write_impl": [3, 4], "state_verdict": [5], "present_plan": [5]}

Rules:
- Match based on the MEANING of the tool call, not just keywords
- A Write to "test_calculator.py" is a test file write, even if the content is implementation-like
- A Write to "calculator.py" is an implementation write, even if it contains test helpers
- A Bash running "pytest" that outputs "FAILED" is a RED phase test run
- A Bash running "pytest" that outputs "passed" is a GREEN phase test run
- List a tool call under multiple steps ONLY when it genuinely satisfies each
  detector on its own; when detectors compete for the same aspect of a call
  (e.g. one pytest run vs. RED and GREEN detectors), pick the single best match
- If a tool call doesn't match any step, don't include it

Text pseudo-tool:
- A `Text` entry is NOT a real tool call — it's assistant natural-language
  output (reasoning, narration, conclusions). Its `output` field holds the text;
  `input` is empty.
- Match a Text entry to a step ONLY when the step's detector explicitly mentions
  "assistant text output" or describes a verdict / evaluation / plan statement.
- For verdict-style steps ("Adopt X", "Extend Y", "Compose A+B", "Build custom"),
  match a Text entry whose content contains one of these keywords followed by a
  library or approach name, OR a clear commitment like "I'll use X because...".
- For evaluation-style steps, match a Text entry that discusses trade-offs,
  compares candidates, or weighs pros and cons.
- A single Text entry that satisfies SEVERAL text-based detectors (e.g. it both
  states a classification and lays out a plan) must be listed under each of
  those steps, not just the best one.
- Do NOT match Text to tool-call steps like "Write a test file" or "run pytest"
  — those must match actual tool_use events.
- If no step mentions text output and no Text entry is a clear verdict, leave
  all Text entries unmatched.
