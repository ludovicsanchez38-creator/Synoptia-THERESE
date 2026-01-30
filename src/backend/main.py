"""
THÉRÈSE v2 - Backend Entry Point

This module re-exports the FastAPI app from the app package.
Use 'uvicorn app.main:app' to run the server.
"""

from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
