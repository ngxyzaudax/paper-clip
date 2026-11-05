import logging
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import Scope

from common.spoken_error import plain_device_message
from web.auth import token_guard
from web.routes.calibrate_routes import router as calibrate_router
from web.routes.care_routes import router as care_router
from web.routes.decode_routes import router as decode_router
from web.routes.encode_routes import router as encode_router
from web.routes.media_routes import router as media_router
from web.routes.meta_routes import router as meta_router
from web.routes.print_routes import router as print_router

logger = logging.getLogger(__name__)
_MISSING = "<p>The interface has not been built. From the web directory, run npm install and npm run build.</p>"
_DEV_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173"]
_ROUTERS = (meta_router, encode_router, print_router, decode_router, care_router, calibrate_router, media_router)


def create_app(token: str | None = None) -> FastAPI:
    """Build the FastAPI application that serves the API and the built interface."""
    app = FastAPI(title="paper-clip")
    app.add_middleware(CORSMiddleware, allow_origins=_DEV_ORIGINS, allow_methods=["*"], allow_headers=["*"])
    if token:
        app.middleware("http")(token_guard(token))
    app.include_router(_api(), prefix="/api")
    app.exception_handler(FileNotFoundError)(_missing)
    app.exception_handler(ValueError)(_invalid)
    _mount_ui(app)
    return app


def _api() -> APIRouter:
    router = APIRouter()
    for item in _ROUTERS:
        router.include_router(item)
    return router


def _mount_ui(app: FastAPI) -> None:
    dist = Path(__file__).resolve().parents[2] / "web" / "dist"
    if not dist.is_dir():
        app.get("/", response_class=HTMLResponse)(_missing_ui)
        return
    app.mount("/", _Spa(directory=dist), name="ui")


def _missing_ui() -> str:
    return _MISSING


class _Spa(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            return await super().get_response("index.html", scope)


async def _missing(request: Request, exc: FileNotFoundError) -> JSONResponse:
    logger.info("Not found for %s: %s", request.url.path, exc)
    return JSONResponse({"detail": "Not found"}, status_code=404)


async def _invalid(_request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse({"detail": plain_device_message(str(exc))}, status_code=400)
