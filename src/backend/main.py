"""
THÉRÈSE v2 - Backend FastAPI

L'assistante souveraine des entrepreneurs français.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="THÉRÈSE v2 API",
    description="Backend de l'assistante souveraine des entrepreneurs français",
    version="0.1.0",
)

# CORS pour le frontend Tauri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "THÉRÈSE v2",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health check pour monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
