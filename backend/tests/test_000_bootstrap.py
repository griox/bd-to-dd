import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
TEST_STUBS_DIR = BACKEND_DIR / "tests" / "_stubs"

if str(TEST_STUBS_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_STUBS_DIR))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
