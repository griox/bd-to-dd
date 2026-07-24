import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for minimal test envs
    def load_dotenv() -> None:
        return None


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
TMP_DIR = Path(os.getenv("TMP_DIR", str(BASE_DIR / "tmp")))
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", str(BASE_DIR / "artifacts")))
SEED_SAMPLES_PATH = BASE_DIR / "app" / "sample_data" / "reviewed_detail_design_samples.json"
INPUT_ROOT_PATH = Path(os.getenv("INPUT_ROOT_PATH", str(BASE_DIR.parent / "INPUT")))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

TMP_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_llm_model(model_name: str) -> str:
    legacy_aliases = {
        "gemini-pro": "gemini-2.5-flash",
    }
    return legacy_aliases.get(model_name, model_name)


GEMINI_LLM_API_KEY = (
    os.getenv("GEMINI_LLM_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or "dummy"
)
GEMINI_LLM_MODEL = normalize_llm_model(
    os.getenv("GEMINI_LLM_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
)
LLM_API_KEY = GEMINI_LLM_API_KEY
LLM_MODEL = GEMINI_LLM_MODEL
MAX_REVIEW_ITERATIONS = int(os.getenv("MAX_REVIEW_ITERATIONS", "2"))

# ---------------------------------------------------------------------------
# Gemini Embedding (Phase 3+)
# ---------------------------------------------------------------------------
GEMINI_EMBEDDING_API_KEY: str = (
    os.getenv("GEMINI_EMBEDDING_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or ""
)
GEMINI_EMBEDDING_MODEL: str = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-001",
)
GEMINI_EMBEDDING_DIMENSIONS: int = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "1536"))
GEMINI_EMBEDDING_BATCH_SIZE: int = int(
    os.getenv("GEMINI_EMBEDDING_BATCH_SIZE", "100")
)

# ---------------------------------------------------------------------------
# Qdrant (Phase 4+)
# ---------------------------------------------------------------------------
VECTOR_DB_PROVIDER: str = os.getenv("VECTOR_DB_PROVIDER", "qdrant")
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "bd_to_dd_chunks")

# ---------------------------------------------------------------------------
# BM25 (Phase 5+)
# ---------------------------------------------------------------------------
BM25_INDEX_PATH: str = os.getenv("BM25_INDEX_PATH", str(TMP_DIR / "bm25_index.json"))
BM25_TOP_K: int = int(os.getenv("BM25_TOP_K", "20"))

# ---------------------------------------------------------------------------
# Retrieval (Phase 9+)
# ---------------------------------------------------------------------------
RETRIEVAL_MIN_TOP_K: int = int(os.getenv("RETRIEVAL_MIN_TOP_K", "3"))
RETRIEVAL_MAX_TOP_K: int = int(os.getenv("RETRIEVAL_MAX_TOP_K", "3"))
RETRIEVAL_SCORE_GAP: float = float(os.getenv("RETRIEVAL_SCORE_GAP", "0.10"))
