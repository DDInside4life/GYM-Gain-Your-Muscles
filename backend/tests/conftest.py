from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://gym:gym@localhost:5432/gym")
os.environ.setdefault("SECRET_KEY", "test-secret-please-change-32+chars")
