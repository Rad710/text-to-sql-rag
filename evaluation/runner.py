"""Run the gold cases and report execution accuracy.

`python -m evaluation.runner` builds the store + schema, runs every case (mock LLM by default), and
prints a per-case table + the overall accuracy. Result-set comparison is order-insensitive over both
rows and columns (values compared as strings) — the standard "execution accuracy" idea.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.agent import ask
from app.config import Settings, get_settings
from app.engine import RagStore
from app.execution import run_sql
from app.llm import LlmProvider
from app.schema import SchemaInfo
from evaluation.cases import GOLD_CASES, EvalCase

RowMultiset = Counter[tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class CaseResult:
    case: EvalCase
    agent_sql: str | None
    passed: bool
    note: str = ""


@dataclass(frozen=True, slots=True)
class EvalReport:
    results: list[CaseResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def accuracy(self) -> float:
        return self.passed / self.total if self.total else 0.0


def _normalize(rows: list[tuple[Any, ...]]) -> RowMultiset:
    """Multiset of rows, each a sorted tuple of string values — order-insensitive rows + columns."""
    return Counter(tuple(sorted("NULL" if v is None else str(v) for v in row)) for row in rows)


def run_eval(
    cases: tuple[EvalCase, ...],
    *,
    store: RagStore,
    schema: SchemaInfo,
    settings: Settings | None = None,
    llm: LlmProvider | None = None,
) -> EvalReport:
    """Run each case through the agent and score its SQL by execution accuracy vs the gold SQL."""
    resolved = settings or get_settings()
    results: list[CaseResult] = []

    for case in cases:
        answer = ask(case.question, store=store, schema=schema, settings=resolved, llm=llm)
        agent_sql = answer.sql[-1] if answer.sql else None

        if agent_sql is None:
            results.append(CaseResult(case, None, False, "no SQL produced"))
            continue

        agent_run = run_sql(agent_sql, resolved)
        if agent_run.error:
            results.append(CaseResult(case, agent_sql, False, f"error: {agent_run.error}"))
            continue

        gold_run = run_sql(case.gold_sql, resolved)
        passed = _normalize(agent_run.rows) == _normalize(gold_run.rows)
        note = "" if passed else f"{agent_run.row_count} rows vs gold {gold_run.row_count}"
        results.append(CaseResult(case, agent_sql, passed, note))

    return EvalReport(results)


def format_report(report: EvalReport) -> str:
    lines = ["", "case                              result   note"]
    lines.append("-" * 64)
    for r in report.results:
        mark = "PASS " if r.passed else "FAIL "
        lines.append(f"{r.case.id:<33} {mark}   {r.note}")
    pct = report.accuracy * 100
    lines.append("-" * 64)
    lines.append(f"execution accuracy: {report.passed}/{report.total} = {pct:.0f}%")
    return "\n".join(lines)


def main() -> None:  # pragma: no cover - manual/CLI convenience
    from app.corpus import build_corpus
    from app.engine import RagStore
    from app.introspect import introspect_from_settings

    settings = get_settings()
    schema = introspect_from_settings()
    store = RagStore(path=settings.chroma_path)
    store.sync_corpus(build_corpus(schema))
    print(format_report(run_eval(GOLD_CASES, store=store, schema=schema, settings=settings)))


if __name__ == "__main__":
    main()
