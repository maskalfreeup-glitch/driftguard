import logging
import secrets
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from sentinel import __version__

from .config import settings
from .monitor import DriftMonitor
from .storage import StorageEngine

# Configure Structured Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("driftguard.sentinel")

storage = StorageEngine(
    redis_url=settings.redis_url, timeout=settings.redis_timeout, history_limit=settings.history_limit
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
    version=__version__,
    description="High-availability EVM RPC drift detection, circuit breaker, and health probe daemon",
    lifespan=lifespan,
)


@app.get("/healthz", summary="Stack Liveness Probe")
async def healthz(response: Response):
    """
    General health probe for container orchestration.
    Returns 200 if the monitor is active.
    """
    uptime = round(time.time() - start_time, 1)
    if not monitor.is_running:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "STARTING",
            "uptime_seconds": uptime,
        }

    return {
        "status": "OK",
        "monitor_running": monitor.is_running,
        "uptime_seconds": uptime,
    }


@app.get("/readyz", summary="Aggregate Chain Readiness Probe")
async def readyz(response: Response):
    ready = monitor.is_healthy
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "READY" if ready else "DEGRADED",
        "chains": {
            chain.chain.name: {
                "reference": chain.reference.status,
                "primary": chain.primary.status,
                "fallback": chain.fallback.status,
            }
            for chain in monitor.unique_monitors().values()
        },
    }


@app.get("/healthz/primary", summary="HAProxy Primary Pool Probe")
async def healthz_primary(response: Response):
    """
    Dedicated endpoint consumed by HAProxy to route to the primary pool.
    Returns HTTP 200 OK only when primary is healthy and within drift threshold.
    Returns HTTP 503 to trigger seamless failover.
    """
    data = await storage.get_health(f"{monitor._default_chain.chain.backend}:primary")
    if not data or monitor.primary.status != "HEALTHY":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "DOWN",
            "reason": monitor.primary.reason,
            "drift": monitor.primary.last_drift,
            "consecutive_failures": monitor.primary.consecutive_failures,
        }

    return {
        "status": "UP",
        "node": "primary",
        "block": monitor.primary.last_sample.block_number if monitor.primary.last_sample else None,
        "drift": monitor.primary.last_drift,
        "latency_ms": monitor.primary.last_sample.latency_ms if monitor.primary.last_sample else 0.0,
    }


@app.get("/healthz/backup", summary="HAProxy Backup Pool Probe")
async def healthz_backup(response: Response):
    """
    Dedicated endpoint consumed by HAProxy to route to the backup pool.
    """
    data = await storage.get_health(f"{monitor._default_chain.chain.backend}:fallback")
    if not data or monitor.backup.status != "HEALTHY":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "DOWN",
            "reason": monitor.backup.reason,
            "drift": monitor.backup.last_drift,
            "consecutive_failures": monitor.backup.consecutive_failures,
        }

    return {
        "status": "UP",
        "node": "backup",
        "block": monitor.backup.last_sample.block_number if monitor.backup.last_sample else None,
        "drift": monitor.backup.last_drift,
        "latency_ms": monitor.backup.last_sample.latency_ms if monitor.backup.last_sample else 0.0,
    }


@app.get("/status", summary="Diagnostic Status Dashboard")
async def get_status():
    """Return sanitized chain-specific health without provider URL paths or credentials."""
    chain_status = []
    for chain_monitor in monitor.unique_monitors().values():
        chain_status.append({
            "name": chain_monitor.chain.name,
            "chain_id": chain_monitor.chain.chain_id,
            "backend": chain_monitor.chain.backend,
            "reference": _node_status(chain_monitor.reference),
            "primary": _node_status(chain_monitor.primary),
            "fallback": _node_status(chain_monitor.fallback),
        })
    return {
        "driftguard_version": __version__,
        "uptime_seconds": round(time.time() - start_time, 1),
        "configuration": {
            "max_reference_age_seconds": settings.max_reference_age,
            "failure_threshold": settings.failure_threshold,
            "recovery_threshold": settings.recovery_threshold,
        },
        "chains": chain_status,
    }


@app.get("/history", summary="Telemetry History")
async def get_history(limit: int = Query(default=20, ge=1, le=100)):
    """
    Returns historical telemetry samples for trend analysis.
    """
    histories = {}
    for chain_monitor in monitor.unique_monitors().values():
        backend = chain_monitor.chain.backend
        histories[chain_monitor.chain.name] = {
            "primary": await storage.get_history(f"{backend}:primary", limit=limit),
            "fallback": await storage.get_history(f"{backend}:fallback", limit=limit),
        }
    return {"limit": limit, "chains": histories}


@app.get("/metrics", response_class=PlainTextResponse, summary="Prometheus Exporter")
def metrics():
    """
    Prometheus metrics endpoint for scraping by Prometheus/Grafana.
    """
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/admin/simulate", summary="Chaos Drill - Simulate Fault")
async def simulate_fault(
    node: str = Query(..., pattern="^(primary|backup)$"),
    drift: int | None = Query(default=None),
    fault: str | None = Query(default=None),
    chain: str | None = Query(default=None),
    backend: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
):
    """
    Injects a synthetic drift or fault on a node for automated failover testing.
    """
    _require_admin(authorization)
    if drift is None and fault is None:
        raise HTTPException(status_code=422, detail="Specify drift or fault")
    try:
        await monitor.simulate_fault(node=node, drift=drift, fault=fault, chain=chain, backend=backend)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Unknown chain or backend") from exc
    logger.warning("Injected simulated fault on %s: drift=%s, fault=%s", node, drift, fault)
    return {"status": "FAULT_INJECTED", "node": node, "chain": chain, "backend": backend,
            "drift": drift, "fault": fault}


@app.post("/admin/reset", summary="Chaos Drill - Reset Faults")
async def reset_faults(chain: str | None = None, backend: str | None = None,
                       authorization: str | None = Header(default=None)):
    """
    Clears all simulated faults and restores genuine live probing.
    """
    _require_admin(authorization)
    try:
        await monitor.reset_faults(chain=chain, backend=backend)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Unknown chain or backend") from exc
    logger.info("Cleared all simulated faults. Live probing restored.")
    return {"status": "FAULTS_RESET"}


@app.post("/admin/test-alert", summary="Test Discord Alert Webhook")
async def test_alert(chain: str | None = None, authorization: str | None = Header(default=None)):
    """
    Emits a test Discord alert to verify webhook integration.
    """
    _require_admin(authorization)
    target = monitor._resolve_chain(chain)
    sent = await monitor.alerter.send_drift_tripped(
        chain_name=target.chain.name,
        chain_id=target.chain.chain_id,
        backend=target.chain.backend,
        canonical_head=1000,
        primary_head=950,
        delta_blocks=50,
        failover_action="[TEST DRILL] Drained primary -> Fallback active",
        force=True,
    )
    return {
        "status": "ALERT_SENT" if sent else "ALERT_NOOP",
        "webhook_configured": bool(monitor.alerter.webhook_url),
    }


def _require_admin(authorization: str | None):

    token = settings.admin_token
    if not token or not authorization or not secrets.compare_digest(authorization, f"Bearer {token}"):
        raise HTTPException(status_code=404, detail="Not found")


def _endpoint_host(url: str) -> str:
    """Expose the host for diagnostics without leaking path/query API credentials."""
    return urlsplit(url).hostname or "configured"


def _node_status(node):
    return {
        "endpoint_host": _endpoint_host(node.url),
        "status": node.status,
        "reason": node.reason,
        "block": node.last_sample.block_number if node.last_sample else None,
        "chain_id": node.last_sample.chain_id if node.last_sample else None,
        "syncing_checked": node.last_sample.syncing_checked if node.last_sample else None,
        "drift": node.last_drift,
    }


if __name__ == "__main__":
    uvicorn.run("sentinel.src.main:app", host=settings.host, port=settings.port, log_level="warning")
