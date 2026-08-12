# 0037 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-12: **Repro (live Playwright).** "hola, ¿cómo estás?" → the model gave meta-reasoning nonsense
  ("No hay información relevante para la base de datos… La respuesta a la pregunta original: …", even a
  stray Dutch word "iets"). "how are you doing today?" → "No schema or SQL call necessary; just a brief
  response in the same language as the question. I'm functioning properly…". Both: 1 step, no tool call —
  so not a tool-misfire, but the model echoing the guardrail instruction as its answer.

- 2026-08-12: **Cause + fix.** The prompt's last line ("If the question is not about the database, answer
  briefly without calling any tool.") reads like reasoning the small model then narrates. Reworded to
  explicitly cover greetings/small talk and to forbid narrating reasoning or mentioning
  SQL/schema/tools/"the database" — "write ONLY that reply". Chose a prompt fix (reviewable, versioned)
  over code; the mock provider is unaffected (it ignores prompt content).

- 2026-08-12: **Verified (live).** After restart: "hola, ¿cómo estás?" → "Me alegra que te contactes.
  ¿Tienes alguna pregunta sobre los datos de DYR Transportes?"; English greeting → "Hola, estoy aquí para
  ayudarte. ¿Tienes alguna pregunta sobre los datos de DYR Transportes?" — clean one-liners, no tool call,
  no reasoning leak. (Minor: the English greeting was answered in Spanish — an 8B language-match slip, not
  nonsense.) A data question ("how many drivers…") still enters the tool loop, so the guidance didn't
  suppress tools.

- 2026-08-12: **Known limitation (not fixed).** That same data question, in English, garbled: 3 tool
  calls, the schema dumped as the "answer", a hallucinated `Conductor` table, and a `run_sql` tool call
  printed as literal JSON text instead of being invoked. This is `llama3.1:8b` emitting tool calls as prose
  — a weak-8B capability limit, non-deterministic (the Spanish phrasing returns a clean `4`). Not
  prompt-fixable; the honest fix is a stronger model for live mode, with mock as the deterministic demo
  default. Recorded so it isn't mistaken for an app bug.

- 2026-08-12: **Owner feedback → general rule; and the leak is model-bound.** Owner: the enumerated version
  ("hola"/"gracias"/…) was too specific — the rule should just be "if unrelated to SQL/DB, don't call the
  tools." Reworded to a single general rule (no example strings). Re-tested live and the meta-narration
  leak persisted, sometimes worse (a greeting answered with only "No respondo con funciones porque no es
  una pregunta sobre datos…" and no actual reply). Tried four phrasings total (strict+enumerated,
  terse-general, general, general+courteous); results swung non-deterministically from clean to pure
  reasoning-dump. A quick search (OpenAI community, aihero.dev) confirms suppressing pre-answer reasoning is
  model-dependent, not a wording fix. Conclusion: keep the clean general prompt, stop tuning, and treat the
  residual leak as the same `llama3.1:8b` capability limit — a stronger model (or the mock default) is the
  real fix. Not going to keep micro-editing the prompt for a weak model.
