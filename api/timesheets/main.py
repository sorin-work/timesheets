from fastapi import FastAPI

from timesheets import __version__
from timesheets.errors import install_error_handlers
from timesheets.routers import auth, clients, projects


def create_app() -> FastAPI:
    app = FastAPI(title="timesheets", version=__version__)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    install_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(clients.router)
    app.include_router(projects.router)
    return app


app = create_app()
