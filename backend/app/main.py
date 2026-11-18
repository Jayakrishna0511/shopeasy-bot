from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import approve, auth, chat, health
from app.rag.embedder import get_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm local embedding model during startup so requests are instant
    try:
        get_embedding_model()
    except Exception as e:
        print(f"Warning: could not pre-warm embedding model at startup: {e}")
    try:
        from app.rag.rerank import get_reranker
        get_reranker()
    except Exception as e:
        print(f"Warning: could not pre-warm reranker at startup: {e}")
    yield


app = FastAPI(title="ShopEasy Support Bot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(approve.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
