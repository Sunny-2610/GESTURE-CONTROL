"""FastAPI application assembly and entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import router as api_router
from app.api.runtime import Runtime, attach

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def _lifespan(runtime: Runtime):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if runtime.start_services:
            runtime.pipeline.start()
            if runtime.hotkey:
                runtime.hotkey.start()
                if runtime.hotkey.wait_registered(2.0):
                    runtime.machine.emit("HOTKEY REGISTERED", "ctrl+alt+shift+q")
                else:
                    runtime.machine.emit("HOTKEY UNAVAILABLE", "registration failed")
        runtime.machine.emit("BACKEND STARTED")
        yield
        if runtime.pipeline is not None:
            runtime.pipeline.stop()
        if runtime.hotkey is not None:
            runtime.hotkey.stop()

    return lifespan


def create_app(start_services: bool = True, settings_path=None) -> FastAPI:
    app = FastAPI(title="Gesture Control", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    runtime = Runtime(start_services=start_services, settings_path=settings_path)
    attach(app, runtime)
    app.include_router(api_router)
    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
    app.router.lifespan_context = _lifespan(runtime)
    return app


app = create_app(start_services=True)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":  # pragma: no cover
    run()
