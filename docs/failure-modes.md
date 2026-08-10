# Failure modes

Where the assistant is known to break, and how we measure it. A system with documented failure modes is
more trustworthy than one with only clean demos.

## How accuracy is measured

**Execution accuracy** (see [`evaluation/`](../evaluation/)): run the agent's generated SQL and an
independent *gold* SQL, then compare the **result sets** (order-insensitive over rows and columns) — not
the SQL strings, which would penalize correct-but-differently-written queries ("it executed without error"
is a vanity metric; the same result is what matters).

- **Mock mode** (default, CI): a pipeline + example-corpus regression guard — the gold set scores **100%**,
  wired into the integration CI job. It catches a broken example, a mis-execution, a bad seed, or a
  regression in the safety/execution path.
- **Real LLM** (`LLM_MODE=openai`): reports the model's true accuracy. Run `python -m evaluation.runner`.

## Known failure modes

- **Ambiguity** — "revenue" (`price` vs `payroll_price`?), "last month" boundaries, which date column. The
  model guesses; a semantic layer or a clarifying-question step would help.
- **Wrong or missing joins** — multi-hop paths (driver → driver_payroll → shipment) can duplicate or drop
  rows. The FK `-- joins:` hints mitigate but don't eliminate this.
- **Silently-wrong filters** — a missing `deleted = 0` or a wrong `WHERE` returns a plausible but wrong
  number that still executes. This is the dangerous class — it *runs*, so only execution+result checks
  (not syntax) catch it.
- **Aggregation / grouping errors** — grouping by the wrong key, or `SUM` vs `AVG`.
- **Mock limitations** — the mock matches questions to canned examples by token overlap; a novel question
  far from the examples gets a wrong or generic answer. Mock mode is a stand-in for the pipeline, not a
  measure of an LLM.
- **Dialect** — SQL is MySQL-only today; the validator is dialect-parameterized but untested on others.
- **Large schemas** — the demo is 7 tables. Retrieval is *designed* to scale (selective DDL + one-line
  summaries for the rest), but schema-linking accuracy on hundreds of tables is unverified here.

## Guarded against (not failure modes)

- **Destructive SQL / writes** — impossible: a read-only DB user + `sqlglot` AST validation + enforced
  `LIMIT` ([decision 0003](decisions/0003-sql-safety-defense-in-depth.md)).
- **Runaway / unbounded queries** — enforced `LIMIT` + statement timeout + row cap + fresh connection.
