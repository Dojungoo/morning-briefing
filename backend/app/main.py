from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.routes.briefing import router as briefing_router
from app.routes.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="AI 보험·대체투자 모닝 브리핑 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(users_router)
app.include_router(briefing_router)


@app.get("/api/health")
async def health() -> JSONResponse:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503, content={"status": "error", "detail": "database"}
        )
    # Non-secret LLM config snapshot: tells us at a glance whether the
    # managed-LLM env (ANTHROPIC_BASE_URL / _API_KEY) was injected by the
    # platform. Never expose the key itself — only whether it's present and
    # the proxy host. This is how we diagnose "why is model=fallback".
    base = settings.anthropic_base_url or ""
    llm = {
        "enabled": settings.llm_enabled,
        "model": settings.llm_model,
        "base_url_set": bool(base),
        "base_url_host": urlparse(base).hostname if base else None,
        "api_key_set": bool(settings.anthropic_api_key),
    }
    return JSONResponse(content={"status": "ok", "llm": llm})
