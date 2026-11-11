"""
PharmaMind AI - Database Engine and Session Management
Configures primary PostgreSQL 18 with resilient local SQLite fallback.
"""

import asyncio
import socket
from typing import AsyncGenerator, Dict, Any
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.database.base import Base

# Import all models to ensure metadata registration
import app.models  # noqa: F401

logger = logging.getLogger("pharmamind.database")

# Runtime state tracker
_active_engine = None
_active_sessionmaker = None
_is_using_fallback = False
_db_status_cache: Dict[str, Any] = {}


def _is_pg_port_reachable(url: str) -> bool:
    """Non-blocking TCP socket check to verify PostgreSQL is listening before pooling."""
    try:
        host = "127.0.0.1"
        port = 5432
        if "@" in url:
            host_port = url.split("@")[-1].split("/")[0]
            if ":" in host_port:
                h, p = host_port.split(":")
                host = h
                port = int(p)
            else:
                host = host_port
        if host.lower() == "localhost":
            host = "127.0.0.1"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        err = s.connect_ex((host, port))
        s.close()
        return err == 0
    except Exception:
        return False


async def initialize_database_engine():
    """
    Initializes primary PostgreSQL or falls back to SQLite if unreachable.
    Guarantees seamless offline development, automated testing, and CI.
    """
    global _active_engine, _active_sessionmaker, _is_using_fallback, _db_status_cache
    
    primary_url = settings.DATABASE_URL
    target_display = primary_url.split("@")[-1] if "@" in primary_url else primary_url
    
    # 1. Fast socket check before initializing heavy asyncpg connection pool
    if _is_pg_port_reachable(primary_url):
        logger.info(f"PostgreSQL port is reachable at {target_display}. Attempting connection...")
        try:
            pg_engine = create_async_engine(
                primary_url,
                echo=False,
                pool_pre_ping=True
            )
            async with pg_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                
            _active_engine = pg_engine
            _active_sessionmaker = async_sessionmaker(
                bind=_active_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )
            _is_using_fallback = False
            _db_status_cache = {
                "dialect": "postgresql",
                "is_fallback": False,
                "connected": True,
                "url_target": target_display
            }
            logger.info("Successfully connected to primary PostgreSQL database.")
            return _active_engine
        except Exception as e:
            logger.warning(f"PostgreSQL connection handshake failed: {e}")
    else:
        logger.info(f"PostgreSQL service not currently listening at {target_display}.")

    # Fallback to SQLite if configured
    if settings.DATABASE_FALLBACK_SQLITE:
        logger.info(f"Engaging resilient local fallback SQLite database: {settings.SQLITE_URL}")
        sqlite_engine = create_async_engine(
            settings.SQLITE_URL,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in settings.SQLITE_URL else {}
        )
        _active_engine = sqlite_engine
        _active_sessionmaker = async_sessionmaker(
            bind=_active_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        _is_using_fallback = True
        _db_status_cache = {
            "dialect": "sqlite",
            "is_fallback": True,
            "connected": True,
            "url_target": settings.SQLITE_URL
        }
        logger.info("Resilient SQLite fallback database active.")
        return _active_engine
    else:
        raise RuntimeError("Primary database unreachable and DATABASE_FALLBACK_SQLITE is disabled.")


def get_engine():
    """Return active async engine."""
    global _active_engine
    if _active_engine is None:
        # Synchronous fallback creation for initial loader
        _active_engine = create_async_engine(
            settings.SQLITE_URL if settings.DATABASE_FALLBACK_SQLITE else settings.DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in settings.SQLITE_URL else {}
        )
    return _active_engine


def get_sessionmaker():
    """Return active sessionmaker."""
    global _active_sessionmaker
    if _active_sessionmaker is None:
        engine = get_engine()
        _active_sessionmaker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
    return _active_sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for yielding async database sessions."""
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all schema tables in active database."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully.")


def get_active_db_info() -> Dict[str, Any]:
    """Return runtime database status for health checks."""
    return _db_status_cache or {
        "dialect": "sqlite" if settings.DATABASE_FALLBACK_SQLITE else "postgresql",
        "is_fallback": _is_using_fallback,
        "connected": _active_engine is not None,
        "url_target": settings.SQLITE_URL if _is_using_fallback else settings.DATABASE_URL
    }
