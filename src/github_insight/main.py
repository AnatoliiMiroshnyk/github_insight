"""FastAPI application factory and web page routes."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from github_insight.api.routes import router as api_router
from github_insight.core.config import get_settings, package_dir
from github_insight.db.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create local development tables at startup.

    A larger production deployment should replace this with Alembic migrations.
    """

    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Analyze public GitHub profiles, repositories, languages and activity.",
        lifespan=lifespan,
    )
    static_dir = package_dir() / "static"
    templates = Jinja2Templates(directory=str(package_dir() / "templates"))
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(api_router)

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard(request: Request):
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"app_name": settings.app_name, "version": settings.app_version},
        )

    @app.get("/health", tags=["operations"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
