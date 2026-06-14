import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from timesheets import __version__, db
from timesheets.config import get_settings
from timesheets.errors import install_error_handlers
from timesheets.routers import (
    auth,
    clients,
    dashboard,
    entries,
    invoices,
    projects,
    reports,
    settings,
    timer,
    timesheet,
)

logger = logging.getLogger("timesheets")


def create_app() -> FastAPI:
    config = get_settings()
    logging.basicConfig(
        level=config.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    app = FastAPI(title="timesheets", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s %s %.1fms", request.method, request.url.path, response.status_code, elapsed
        )
        return response

    @app.get("/api/health", tags=["meta"])
    def health() -> JSONResponse:
        """Liveness and database connectivity, for container healthchecks."""
        try:
            with db.get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.exception("health check: database unavailable")
            return JSONResponse(
                {"status": "error", "database": "unavailable", "version": __version__},
                status_code=503,
            )
        return JSONResponse({"status": "ok", "database": "ok", "version": __version__})

    install_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(clients.router)
    app.include_router(projects.router)
    app.include_router(entries.router)
    app.include_router(timer.router)
    app.include_router(timesheet.router)
    app.include_router(invoices.router)
    app.include_router(reports.router)
    app.include_router(dashboard.router)
    app.include_router(settings.router)
    return app


app = create_app()
