"""
PharmaMind AI - Main FastAPI Application
"""

from contextlib import asynccontextmanager
import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.database.session import initialize_database_engine, init_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    setup_logging()
    logger.info(f"Initializing {settings.PROJECT_NAME} (v{settings.VERSION})...")
    
    # Configure CPU execution limits to respect 16GB RAM constraint
    torch.set_num_threads(settings.TORCH_NUM_THREADS)
    logger.info(f"PyTorch configured: Device={settings.ML_DEVICE}, Threads={torch.get_num_threads()}")
    
    # Initialize database engine (PostgreSQL 18 with SQLite resilient fallback)
    await initialize_database_engine()
    await init_db()
    
    logger.info("Application startup sequence completed successfully.")
    yield
    # Shutdown sequence
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "PharmaMind AI is a biomedical drug-information assistant platform combining "
        "Biomedical NLP, Knowledge Graphs, Semantic Retrieval, and Evidence-Grounded AI."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "api_docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

