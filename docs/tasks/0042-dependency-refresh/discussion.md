# 0042 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-15: **Floors vs. exact pins.** CLAUDE.md says "pin dependency versions"; the repo has always
  read that as *a `>=major.minor` floor in the spec + an exact resolution in the lockfile*, which is what
  actually makes builds reproducible. Kept that style rather than converting to `==` — switching pin
  style is a change to how the project is maintained, not a version refresh, and `uv.lock` /
  `pnpm-lock.yaml` already give exact reproducibility.

- 2026-08-15: **The drift was in the specs, not the locks.** `uv.lock` was already carrying chromadb
  1.5.9, bcrypt 5.0.0, pytest 9.1.1, mypy 2.3.0 — all far above their declared floors (`>=0.5`, `>=4.2`,
  `>=8.3`, `>=1.11`). So the floors weren't holding anything back, they were just lying about what the
  project supports. Raising them is the substance of this task; `--upgrade` only moved five direct
  packages.

- 2026-08-15: **openai 2.53 → 3.1 (major).** Checked the blast radius before taking it: the only SDK
  surface used is `OpenAI(base_url=…, api_key=…)` and `chat.completions.create(model=…, messages=…)` plus
  `response.choices[0].message` / `response.usage` reads, all in `backend/app/llm/client.py`
  (`OpenAIProvider`). Everything else in the loop rides the markdown tool protocol, not JSON function
  calling, so there is no tools/`tool_calls` surface to break. `tests/test_llm.py` patches
  `openai.OpenAI` and still passes. Taken.

- 2026-08-15: **bcrypt 4.2 → 5.0, pytest 8 → 9, mypy 1 → 2 (majors).** All three are already the locked
  versions in use — this only makes the declared floor honest. Gates confirm: 136 backend tests pass and
  mypy is clean on 34 files under mypy 2.3 strict.

- 2026-08-15: **Frontend was essentially current.** Caret ranges meant `pnpm update --latest` moved only
  four packages. The bigger fix was cosmetic-but-real: `react`/`react-dom`/`@types/react*` still declared
  `^19.0.0` while resolving 19.2.x. Realigned so the manifest reads as the supported floor.

- 2026-08-15: **`release.yml` had rotted.** `ci.yml` is kept current (checkout v7, setup-uv v9,
  setup-node v7), but the GHCR release workflow from task 0032 was a major behind on all five actions.
  Bumped together. No behavioral change expected — none of the five renamed inputs across these majors,
  and the workflow only fires on a `v*` tag, so the first real proof comes at the next release.

- 2026-08-15: **Held back — base-image majors.** Deliberately *not* touched, because each is a runtime
  decision with its own blast radius rather than a dependency refresh, and each would need a coordinated
  change plus live verification:
  - `python:3.12-slim` → 3.13/3.14 — would also move `requires-python`, `.python-version`,
    ruff `target-version`, mypy `python_version`, and three CI jobs.
  - `node:22-alpine` → 24/26 — pairs with `node-version: "22"` in `ci.yml`.
  - `mysql:8.4` → 9.x — 8.4 is the LTS line; the demo DB and Flyway migrations are validated against it.
  - `postgres:17` → 18 — app datastore ([decision 0008](../../decisions/0008-app-datastore-postgres.md));
    needs a data-directory migration story for the deployed VM, not just a tag edit.
  - `flyway/flyway:11` → 13 ([decision 0011](../../decisions/0011-flyway-mock-db-migrations.md)).

  Flagged to the owner as a follow-up rather than decided here (CLAUDE.md: ask before picking).
