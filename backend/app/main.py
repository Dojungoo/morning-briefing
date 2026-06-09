from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

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
    return JSONResponse(content={"status": "ok"})
