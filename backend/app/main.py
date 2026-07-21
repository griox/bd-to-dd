from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.persistence.postgres.database import Base, engine
from app.infrastructure.persistence.postgres import models as _models  # noqa: F401
from app.presentation.api.v1.router import router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="BD-to-DD Toolkit")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
