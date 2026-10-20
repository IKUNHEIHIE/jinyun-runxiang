"""Test environment defaults, applied before any app module is imported.

Without this, running a single test file (instead of the whole directory) fails during
collection because Settings requires JWT_SECRET_KEY.
"""
import os
import secrets
import sys
from pathlib import Path

os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(48))
os.environ.setdefault("DATABASE_URL", "sqlite://")

TESTS_DIR = str(Path(__file__).resolve().parent)
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)
