import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db
from app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize SQLite tables and ensure directories exist
    init_db()
    yield
    # Shutdown logic if any

app = FastAPI(
    title="ProofMind AI Backend API",
    description="Evidence-Aware AI Decision Engine API with Page-level Citations, Contradiction Detection, and Verification Engine.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
allow_all = "*" in origins or not origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(api_router)

# Serve built React frontend if available (enables unified single-URL deployment)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

dist_dirs = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend_dist"),
    os.path.abspath("frontend_dist"),
    os.path.abspath("frontend/dist")
]
frontend_dist_dir = next((d for d in dist_dirs if os.path.exists(d) and os.path.exists(os.path.join(d, "index.html"))), None)

if frontend_dist_dir:
    assets_dir = os.path.join(frontend_dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist_dir, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "app": "ProofMind AI",
            "tagline": "Every decision needs evidence.",
            "docs": "/docs",
            "health": "/health"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
