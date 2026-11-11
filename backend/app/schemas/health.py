"""
PharmaMind AI - Health Check Schemas
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class MemoryStatus(BaseModel):
    total_gb: float
    available_gb: float
    used_gb: float
    memory_load_pct: float
    is_safe_for_ml: bool
    safety_threshold_mb: int


class DatabaseStatus(BaseModel):
    connected: bool
    dialect: str
    is_fallback: bool
    url_target: str
    latency_ms: Optional[float] = None


class MLDeviceStatus(BaseModel):
    device: str
    torch_version: str
    num_threads: int
    lazy_loading_enabled: bool
    max_batch_size: int


class HealthResponse(BaseModel):
    status: str = Field(..., description="'healthy', 'degraded', or 'unhealthy'")
    application: str
    version: str
    environment: str
    timestamp: str
    database: DatabaseStatus
    memory: MemoryStatus
    machine_learning: MLDeviceStatus
    provenance_integrity: bool = True

