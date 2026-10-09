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
