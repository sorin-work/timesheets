from fastapi import FastAPI

from timesheets import __version__
from timesheets.routers import auth


def create_app() -> FastAPI:
    app = FastAPI(title="timesheets", version=__version__)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(auth.router)
    return app


app = create_app()
