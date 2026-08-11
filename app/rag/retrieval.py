"""The 4-tier retrieval merge (pure) + the assembled context object.

Given the raw hits from the vector store plus the live schema, decide which tables are relevant and
in what order, then package the context the agent consumes. Four tiers, highest priority first:

* **P1 semantic** — tables whose DDL is nearest the question (passed in nearest-first).
* **P2 example** — tables parsed out of the retrieved few-shot SQL.
* **P3 relationship** — join neighbours of the already-chosen tables (from the FK join graph).
* **P4 keyword** — stopword-filtered token match against table/column names.

The merge is a priority append: iterate the tiers in order and take each table the first time it
appears, so "highest-priority source wins ties" falls out naturally. Pure — unit-tests in isolation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from app.schema import SchemaInfo

_TOKEN_RE = re.compile(r"[a-z0-9_]+")

# Small bilingual (EN/ES) stopword set — enough to keep the keyword tier from matching on filler.
_STOPWORD_TEXT = (
    "the a an of for to in on by and or per how many much what which is are do did show list "
    "total each all with from de la el los las por para en y o cuanto cuantos cuantas que cual "
    "cuales son muestra lista cada todos todas con del"
)
_STOPWORDS = frozenset(_STOPWORD_TEXT.split())


@dataclass(frozen=True, slots=True)
class Candidate:
    table: str
    source: str  # semantic | example | relationship | keyword


@dataclass(frozen=True)
class RetrievedContext:
    tables: list[str]  # the top tables, full DDL provided, ordered
    ddl: list[str]  # full annotated DDL for `tables`
    summaries: list[str]  # compact one-liners for the remaining tables
    docs: list[str]  # business-rule notes
    examples: list[tuple[str, str]]  # (question, sql) few-shot pairs

    def as_prompt(self) -> str:
        """Render the retrieved context as a single block for the SQL-generation prompt."""
        parts: list[str] = []
        if self.ddl:
            parts.append("-- Relevant tables (full schema)\n" + "\n\n".join(self.ddl))
        if self.summaries:
            parts.append("-- Other tables (summary)\n" + "\n".join(self.summaries))
        if self.docs:
            parts.append("-- Business rules\n" + "\n".join(f"- {d}" for d in self.docs))
        if self.examples:
            rendered = "\n".join(f"Q: {q}\nSQL: {s}" for q, s in self.examples)
            parts.append("-- Example queries\n" + rendered)
        return "\n\n".join(parts)


def extract_tables_from_sql(sql: str, known_tables: set[str]) -> list[str]:
    """Return the known tables referenced in ``sql`` (FROM/JOIN), in order, deduped."""
    try:
        expression = sqlglot.parse_one(sql, read="mysql")
    except SqlglotError:
        return []
    out: list[str] = []
    for table in expression.find_all(exp.Table):
        name = table.name
        if name in known_tables and name not in out:
            out.append(name)
    return out


def keyword_tables(question: str, schema: SchemaInfo) -> list[str]:
    """P4 fallback: tables whose name or a column name matches a (non-stopword) question token."""
    tokens = {t for t in _TOKEN_RE.findall(question.lower()) if len(t) >= 3 and t not in _STOPWORDS}
    if not tokens:
        return []
    result: list[str] = []
    for table in schema.tables:
        name = table.name.lower()
        columns = {c.name.lower() for c in table.columns}
        name_hit = any(tok in name or name in tok for tok in tokens)
        column_hit = any(tok == col or tok in col for tok in tokens for col in columns)
        if name_hit or column_hit:
            result.append(table.name)
    return result


def follow_relationships(chosen: list[str], schema: SchemaInfo) -> list[str]:
    """P3: join neighbours of the chosen tables that aren't already chosen."""
    chosen_set = set(chosen)
    result: list[str] = []
    for table_name in chosen:
        for partner in schema.join_partners(table_name):
            if partner not in chosen_set and partner not in result:
                result.append(partner)
    return result


def merge_candidates(
    semantic: list[str],
    example: list[str],
    relationship: list[str],
    keyword: list[str],
) -> list[Candidate]:
    """Priority-append the four tiers, keeping each table under the first tier that yields it."""
    seen: set[str] = set()
    out: list[Candidate] = []
    for source, names in (
        ("semantic", semantic),
        ("example", example),
        ("relationship", relationship),
        ("keyword", keyword),
    ):
        for name in names:
            if name not in seen:
                seen.add(name)
                out.append(Candidate(table=name, source=source))
    return out
