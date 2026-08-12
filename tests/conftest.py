"""Test-suite hermeticity.

The unit/integration tests assume the deterministic **mock** LLM provider and must not depend on a
developer's local ``.env`` (which may be flipped to ``LLM_MODE=openai`` for a live Ollama run).
Set the env here — pytest imports conftest before the test modules import ``app.config``, and
``config.py`` calls ``load_dotenv(override=False)``, so this preset value wins over any ``.env``.
"""

import os

# Force the deterministic mock provider for every test, regardless of a local .env.
os.environ["LLM_MODE"] = "mock"
