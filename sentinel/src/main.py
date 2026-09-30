import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, Response, status, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import uvicorn

from .config import settings
from .storage import StorageEngine
from .monitor import DriftMonitor

# Configure Structured Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("driftguard.sentinel")

storage = StorageEngine(
    redis_url=settings.redis_url,
    timeout=settings.redis_timeout,
    history_limit=settings.history_limit
)
monitor = DriftMonitor(config=settings, storage=storage)
start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing DriftGuard Sentinel...")
    await storage.connect()
    await monitor.start()
    yield
    logger.info("Shutting down DriftGuard Sentinel...")
    await monitor.stop()
    await storage.close()

app = FastAPI(
    title="DriftGuard Sentinel",
    version="1.0.0",
    description="High-availability EVM RPC drift detection, circuit breaker, and health probe daemon",
    lifespan=lifespan
)

@app.get("/healthz", summary="Stack Liveness Probe")
async def healthz(response: Response):
    """
    General health probe for container orchestration.
    Returns 200 if the monitor is active.
    """
    uptime = round(time.time() - start_time, 1)
    p_healthy = monitor.primary.status == "HEALTHY"
    b_healthy = monitor.backup.status == "HEALTHY"

    if not p_healthy and not b_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "CRITICAL",
            "message": "Both primary and backup nodes are unavailable or drifting",
            "uptime_seconds": uptime
        }

    return {
        "status": "OK",
        "primary": monitor.primary.status,
        "backup": monitor.backup.status,
        "uptime_seconds": uptime
    }

@app.get("/healthz/primary", summary="HAProxy Primary Pool Probe")
async def healthz_primary(response: Response):
    """
    Dedicated endpoint consumed by HAProxy to route to the primary pool.
    Returns HTTP 200 OK only when primary is healthy and within drift threshold.
    Returns HTTP 503 to trigger seamless failover.
    """
    data = await storage.get_health("primary")
    if not data or monitor.primary.status != "HEALTHY":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "DOWN",
            "reason": monitor.primary.reason,
            "drift": monitor.primary.last_drift,
            "consecutive_failures": monitor.primary.consecutive_failures
        }

    return {
        "status": "UP",
        "node": "primary",
        "block": monitor.primary.last_sample.block_number if monitor.primary.last_sample else None,
        "drift": monitor.primary.last_drift,
        "latency_ms": monitor.primary.last_sample.latency_ms if monitor.primary.last_sample else 0.0
    }

@app.get("/healthz/backup", summary="HAProxy Backup Pool Probe")
async def healthz_backup(response: Response):
    """
    Dedicated endpoint consumed by HAProxy to route to the backup pool.
    """
    data = await storage.get_health("backup")
    if not data or monitor.backup.status != "HEALTHY":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "DOWN",
            "reason": monitor.backup.reason,
            "drift": monitor.backup.last_drift,
            "consecutive_failures": monitor.backup.consecutive_failures
        }

    return {
        "status": "UP",
        "node": "backup",
        "block": monitor.backup.last_sample.block_number if monitor.backup.last_sample else None,
        "drift": monitor.backup.last_drift,
        "latency_ms": monitor.backup.last_sample.latency_ms if monitor.backup.last_sample else 0.0
    }

@app.get("/status", summary="Diagnostic Status Dashboard")
async def get_status():
    """
    Returns full diagnostic telemetry for all nodes, reference status, and settings.
    """
    p_health = await storage.get_health("primary")
    b_health = await storage.get_health("backup")

    return {
        "driftguard_version": "1.0.0",
        "uptime_seconds": round(time.time() - start_time, 1),
        "configuration": {
            "drift_threshold_blocks": settings.drift_threshold,
            "poll_interval_seconds": settings.poll_interval,
            "failure_threshold": settings.failure_threshold,
            "recovery_threshold": settings.recovery_threshold
        },
        "nodes": {
            "primary": {
                "url": settings.primary_rpc_url,
                "status": monitor.primary.status,
                "reason": monitor.primary.reason,
                "latest": p_health
            },
            "backup": {
                "url": settings.backup_rpc_url,
                "status": monitor.backup.status,
                "reason": monitor.backup.reason,
                "latest": b_health
            },
            "canonical_reference": {
                "url": settings.canonical_rpc_url,
                "status": monitor.canonical.status,
                "block": monitor.canonical.last_sample.block_number if monitor.canonical.last_sample else None,
                "latency_ms": monitor.canonical.last_sample.latency_ms if monitor.canonical.last_sample else None
            }
        }
    }

@app.get("/history", summary="Telemetry History")
async def get_history(limit: int = Query(default=20, ge=1, le=100)):
    """
    Returns historical telemetry samples for trend analysis.
    """
    p_hist = await storage.get_history("primary", limit=limit)
    b_hist = await storage.get_history("backup", limit=limit)
    return {
        "limit": limit,
        "primary_history": p_hist,
        "backup_history": b_hist
    }

@app.get("/metrics", response_class=PlainTextResponse, summary="Prometheus Exporter")
def metrics():
    """
    Prometheus metrics endpoint for scraping by Prometheus/Grafana.
    """
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    uvicorn.run("sentinel.src.main:app", host=settings.host, port=settings.port, log_level="warning")
