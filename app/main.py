import logging

import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI

from .routes import router
from .settings import settings
from .db import db

from prometheus_fastapi_instrumentator import Instrumentator

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()      # runs on startup
    yield                   # app runs here
    await db.disconnect()   # runs on shutdown

app = FastAPI(title=settings.APP_TITLE, lifespan=lifespan)

app.include_router(router, prefix="/api/v1")

Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    """
    Server configurations
    """
    uvicorn.run(
        app="app.main:app",
        host=settings.ALLOWED_HOST,
        debug=settings.DEBUG,
        port=settings.ALLOWED_PORT,
        reload=True,
        log_level=logging.INFO,
        use_colors=True,
    )
