from fastapi import FastAPI

from timesheets import __version__


def create_app() -> FastAPI:
    app = FastAPI(title="timesheets", version=__version__)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
