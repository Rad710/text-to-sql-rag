"""Evaluation harness: measure the assistant's SQL by EXECUTION ACCURACY.

For each gold case we run the agent, execute its generated SQL and an independent gold SQL against
the synthetic DB, and compare the *result sets* (order-insensitive over rows and columns) — not the
SQL strings, which penalize correct-but-differently-written queries. In mock mode this is a pipeline
+ example-corpus regression guard (should be 100%); against a real LLM it reports true accuracy.
"""
