from pathlib import Path


_ROOT_DIR = Path(__file__).resolve().parents[1]
_BACKEND_APP_DIR = _ROOT_DIR / "backend" / "app"
__path__ = [str(_BACKEND_APP_DIR)]
