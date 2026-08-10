"""Pure schema model + DDL/annotation rendering for the RAG layer.

No I/O. Given a :class:`SchemaInfo` (built by :mod:`app.introspect` from the live DB), render the
annotated ``CREATE TABLE`` DDL and compact one-line summaries that the retriever indexes and the
``search_schema`` tool serves. Kept pure so it unit-tests without a database.

The `-- joins:` annotation on each table lists its join neighbours in **both** directions — the
tables it references via foreign keys, and the tables that reference it — so retrieval can follow
a dimension→fact edge as readily as fact→dimension (the "relationship-following" RAG signal).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Column:
    name: str
    data_type: str
    nullable: bool
    is_primary_key: bool = False


@dataclass(frozen=True, slots=True)
class ForeignKey:
    column: str
    ref_table: str
    ref_column: str


@dataclass(frozen=True, slots=True)
class Table:
    name: str
    columns: tuple[Column, ...]
    foreign_keys: tuple[ForeignKey, ...] = ()

    @property
    def primary_key(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns if c.is_primary_key)

    def foreign_key_for(self, column: str) -> ForeignKey | None:
        return next((fk for fk in self.foreign_keys if fk.column == column), None)


@dataclass(frozen=True, slots=True)
class SchemaInfo:
    tables: tuple[Table, ...]

    def table(self, name: str) -> Table | None:
        return next((t for t in self.tables if t.name == name), None)

    def referencing_tables(self, name: str) -> tuple[str, ...]:
        """Tables that hold a foreign key pointing at ``name``."""
        return tuple(
            t.name for t in self.tables if any(fk.ref_table == name for fk in t.foreign_keys)
        )

    def join_partners(self, name: str) -> tuple[str, ...]:
        """All join neighbours of ``name`` — tables it references and tables referencing it."""
        table = self.table(name)
        outgoing = {fk.ref_table for fk in table.foreign_keys} if table else set()
        incoming = set(self.referencing_tables(name))
        return tuple(sorted(outgoing | incoming))


def render_table_ddl(schema: SchemaInfo, table: Table) -> str:
    """Render one table's annotated ``CREATE TABLE`` (`-- joins:` comment + columns + keys)."""
    lines: list[str] = []
    partners = schema.join_partners(table.name)
    if partners:
        lines.append(f"-- joins: {', '.join(partners)}")
    lines.append(f"CREATE TABLE {table.name} (")

    body: list[str] = []
    for col in table.columns:
        nn = " NOT NULL" if not col.nullable else ""
        body.append(f"    {col.name} {col.data_type}{nn}")
    if table.primary_key:
        body.append(f"    PRIMARY KEY ({', '.join(table.primary_key)})")
    for fk in table.foreign_keys:
        body.append(f"    FOREIGN KEY ({fk.column}) REFERENCES {fk.ref_table}({fk.ref_column})")

    lines.append(",\n".join(body))
    lines.append(");")
    return "\n".join(lines)


def render_table_summary(table: Table, max_cols: int = 16) -> str:
    """Compact one-liner ``name(col type PK, col type ->ref, …)``, capped at ``max_cols`` cols."""
    parts: list[str] = []
    for col in table.columns[:max_cols]:
        annot = ""
        if col.is_primary_key:
            annot = " PK"
        else:
            fk = table.foreign_key_for(col.name)
            if fk:
                annot = f" ->{fk.ref_table}"
        parts.append(f"{col.name} {col.data_type}{annot}")
    hidden = len(table.columns) - max_cols
    if hidden > 0:
        parts.append(f"(+{hidden} more)")
    return f"{table.name}({', '.join(parts)})"


def render_schema_ddl(schema: SchemaInfo) -> str:
    """Full annotated DDL for every table, blank-line separated."""
    return "\n\n".join(render_table_ddl(schema, t) for t in schema.tables)


def render_schema_summaries(schema: SchemaInfo) -> str:
    """One compact summary line per table."""
    return "\n".join(render_table_summary(t) for t in schema.tables)
