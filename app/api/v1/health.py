"""Health check endpoint."""

from litestar import Controller, get


class HealthController(Controller):
    """Health check controller."""

    path = "/health"

    @get("/")
    async def health_check(self) -> dict[str, str]:
        """Return health status."""
        return {"status": "ok"}
