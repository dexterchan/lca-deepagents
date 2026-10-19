# python/tests/conftest.py
"""Shared pytest setup for the tests/ directory.

Pytest imports conftest.py before the test modules in this directory, so the
import-time setup here runs before `import m4_2_newsletter_agent`:

- The lab module raises RuntimeError without TAVILY_API_KEY, and models.py
  reads OPENROUTER_API_KEY. Dummy values satisfy both (no network happens at
  import time); your real .env keys win via load_dotenv(override=True).
- The lab modules live in python/m4/, which is not on sys.path when tests are
  collected from python/tests/, so it is added here (the labs are plain
  scripts with no package __init__.py).
"""

import os
import sys
from pathlib import Path

# python/ root (this file is python/tests/conftest.py)
ROOT = Path(__file__).resolve().parent.parent

os.environ.setdefault("TAVILY_API_KEY", "test-dummy")
os.environ.setdefault("OPENROUTER_API_KEY", "test-dummy")

sys.path.insert(0, str(ROOT / "m4"))
