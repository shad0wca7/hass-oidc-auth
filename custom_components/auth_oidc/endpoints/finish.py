"""Finish route to allow the user to view their code."""

from homeassistant.components.http import HomeAssistantView
from aiohttp import web
from ..helpers import get_view

PATH = "/auth/oidc/finish"


class OIDCFinishView(HomeAssistantView):
    """OIDC Plugin Finish View."""

    requires_auth = False
    url = PATH
    name = "auth:oidc:finish"

    async def get(self, request: web.Request) -> web.Response:
        """Show the finish screen to allow the user to view their code."""

        code = request.query.get("code")

        if not code:
            view_html = await get_view(
                "error",
                {"error": "Missing code to show the finish screen."},
            )
            return web.Response(text=view_html, content_type="text/html")

        view_html = await get_view("finish", {"code": code})
        return web.Response(
            text=view_html,
            content_type="text/html",
            headers={
                # Prevent one-time login codes from ending up in browser/proxy caches.
                "Cache-Control": "no-store, max-age=0",
                "Pragma": "no-cache",
            },
        )

    async def post(self, request: web.Request) -> web.Response:
        """Receive response."""

        # Get code from the message body
        data = await request.post()
        code = data.get("code")

        if not code:
            return web.Response(text="No code received", status=400)

        # Return redirect to the main page for sign in with a cookie.
        response = web.HTTPFound(location="/?storeToken=true")
        response.set_cookie(
            "auth_oidc_code",
            code,
            path="/auth/login_flow",
            max_age=5,
            httponly=True,
            samesite="Strict",
            secure=request.secure,
        )
        return response
