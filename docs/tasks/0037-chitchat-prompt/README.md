---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-12     # YYYY-MM-DD, last touched
decision: null          # decisions/NNNN that governs this task, if any
depends_on: []          # task numbers that must finish first
---

# 0037 — Clean up the "non-database question" system-prompt rule

## Goal
In live mode (`llama3.1:8b`), greetings/small talk returned rambling nonsense that leaked the model's
internal reasoning ("No schema or SQL call necessary…", "No hay información relevante para la base de
datos…"). The system prompt's terse non-DB line was being parroted. Make the rule a clean, **general**
instruction (any non-data message → no tool, answer directly) rather than an enumerated list of greeting
phrases.

## Context
The `SYSTEM_PROMPT` (`backend/app/llm/prompts.py`) ended with a terse *"If the question is not about the
database, answer briefly without calling any tool."* No test asserts the prompt text (`test_llm.py` only
uses it as fixture content), so it's safe to reword.

## Plan
- Reword the last line to a general rule: *"Only use the tools when the user is asking for data from the
  database. Otherwise do NOT call any tool: reply directly and courteously in the user's language, in one
  short sentence. Output only that reply — no preamble, no explanation of your reasoning."* No hardcoded
  greeting examples.

## Done when
- [x] `ruff`/`format`/`pytest` (129) green; no test coupled to the prompt text.
- [x] Prompt is a single general rule (no enumerated greeting strings).
- [x] Behaviour spot-checked live (see the limitation below).

## Outcome / honest limitation
The general rule is the right spec. But on **`llama3.1:8b`** it does **not** reliably stop the model from
narrating its reasoning: across four phrasings tested live (strict+enumerated, terse-general, general,
general+courteous) the same greeting swung non-deterministically from clean ("Me alegra que te contactes.
¿Tienes alguna pregunta sobre los datos…?") to pure meta-babble ("No respondo con funciones porque no es
una pregunta sobre datos…"). A quick literature/search check confirms this is **model-dependent behaviour**,
not a wording problem. The reliable fixes are a **more capable model** for live mode, or the deterministic
**mock provider** (the demo default). Kept the clean general prompt and stopped tuning; recorded the
model limitation rather than chasing it. (Same class as the harder-question garble noted in the discussion.)

---
Log → [`discussion.md`](discussion.md)
