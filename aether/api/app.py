from __future__ import annotations

from fastapi import FastAPI

from aether.api.routers import task


def create_app() -> FastAPI:
    app = FastAPI(title="Aether-Native", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(task.router)
    return app
