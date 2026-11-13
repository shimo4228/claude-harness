# Provisional decisions

Everything in this file is provisional and is expected to be replaced. This file is the index: each
section names the one place where its decision is stated and the places to change when it is
replaced.

## 1. Where the holistic stage sits, and what it is shown

- **Current decision**: the four stages of skill `llm-as-judge`.
- **Where the decision is written**: skill `llm-as-judge`, the four-stage section.
- **What would replace it**: learning about the conditions under which intuition can be trusted;
  about LLM evaluators' biases toward position and length, and their self-preference.
- **Where to change it**: that section only.

## 2. The form of the scale

- **Current decision**: the form skill `llm-as-judge` states (its three principles). One addition
  stated here: comparing two is used only where the task is choosing among candidates.
- **Where the decision is written**: skill `llm-as-judge`, the three principles; the addition, here.
- **What would replace it**: learning about comparative judgment (comparing two rather than
  scoring); about LLM evaluators' biases toward position and length.
- **Where to change it**: here, and in skill `llm-as-judge` the table of the three principles and
  the output schema.

## 3. How the standard reaches the judge

- **Current decision**: the way skill `llm-as-judge` hands them over (its binary checks, its named
  verdict, its judge prompt template). One addition stated here: no anchor examples are passed.
- **Where the decision is written**: skill `llm-as-judge`; the addition, here.
- **What would replace it**: learning about sharing a standard through examples.
- **Where to change it**: here, and the judge prompt template in skill `llm-as-judge`.

## 4. The judge's confidence

- **Current decision**: the verdict judge outputs no confidence. The two places that do output
  confidence (agent `security-reviewer`, skill `generation-audit`) stay as they are.
- **Where the decision is written**: here.
- **What would replace it**: learning about calibration and confidence.
- **Where to change it**: here.
