"""
PharmaMind AI - Core Configuration
Pydantic Settings managing application, database, ML constraints, and security.
"""

from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    # Application Info
    PROJECT_NAME: str = "PharmaMind AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "pharmamind-super-secret-development-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/pharmamind"
    DATABASE_FALLBACK_SQLITE: bool = True
    SQLITE_URL: str = "sqlite+aiosqlite:///./pharmamind.db"
    
    # Hardware & ML Resource Management (CPU execution on 16GB RAM)
    ML_DEVICE: str = "cpu"
    TORCH_NUM_THREADS: int = 4
    ENABLE_LAZY_MODEL_LOADING: bool = True
    ENABLE_HF_TRANSFORMERS: bool = False
    MAX_BATCH_SIZE: int = 8
    MEMORY_SAFETY_THRESHOLD_MB: int = 1024  # Minimum free RAM required before loading large models
    
    # Knowledge Graph
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    USE_LOCAL_GRAPH_FALLBACK: bool = True
    
    # External APIs
    PUBMED_API_KEY: str = ""
    OPENFDA_API_KEY: str = ""
    DAILYMED_BASE_URL: str = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
    RXNORM_BASE_URL: str = "https://rxnav.nlm.nih.gov/REST"
    OPENFDA_BASE_URL: str = "https://api.fda.gov"
    PUBMED_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000"
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
