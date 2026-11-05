import hmac
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

TOKEN_COOKIE = "paper_clip_token"
TOKEN_QUERY = "token"
CallNext = Callable[[Request], Awaitable[Response]]
Middleware = Callable[[Request, CallNext], Awaitable[Response]]


def token_guard(token: str) -> Middleware:
    """Require the server token on API calls and trade a one-time token link for a session cookie."""
    async def check(request: Request, call_next: CallNext) -> Response:
        if request.query_params.get(TOKEN_QUERY) is not None and not request.url.path.startswith("/api"):
            return _sign_in(request, token)
        if request.url.path.startswith("/api") and not _carries(request, token):
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)
    return check


def token_url(base: str, token: str) -> str:
    """Return the link that signs a browser in to a token-protected server."""
    return f"{base}?{TOKEN_QUERY}={token}"


def _carries(request: Request, token: str) -> bool:
    bearer = request.headers.get("authorization", "").removeprefix("Bearer ")
    return _same(bearer, token) or _same(request.cookies.get(TOKEN_COOKIE, ""), token)


def _sign_in(request: Request, token: str) -> Response:
    if not _same(request.query_params.get(TOKEN_QUERY, ""), token):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)
    response = RedirectResponse(request.url.path, status_code=303)
    response.set_cookie(TOKEN_COOKIE, token, httponly=True, samesite="strict")
    return response


def _same(given: str, token: str) -> bool:
    return bool(given) and hmac.compare_digest(given.encode(), token.encode())
