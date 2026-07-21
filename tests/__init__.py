from pathlib import Path


_ROOT_DIR = Path(__file__).resolve().parents[1]
_BACKEND_TESTS_DIR = _ROOT_DIR / "backend" / "tests"
__path__ = [str(_BACKEND_TESTS_DIR)]
