from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # RPC Endpoints
    primary_rpc_url: str = Field(default="https://ethereum-sepolia-rpc.publicnode.com", alias="PRIMARY_RPC_URL")
    fallback_rpc_url: str = Field(default="https://sepolia.gateway.tenderly.co", alias="FALLBACK_RPC_URL")
    backup_rpc_url: str = Field(default="https://sepolia.gateway.tenderly.co", alias="BACKUP_RPC_URL")
    canonical_rpc_url: str = Field(default="https://rpc.sepolia.ethpandaops.io", alias="CANONICAL_RPC_URL")

    # Drift & Polling Configuration
    block_drift_threshold: int = Field(default=2, alias="BLOCK_DRIFT_THRESHOLD")
    drift_threshold: int = Field(default=2, alias="DRIFT_THRESHOLD")

    poll_interval_ms: int = Field(default=3000, alias="POLL_INTERVAL_MS")
    poll_interval: float = Field(default=3.0, alias="POLL_INTERVAL")

    rpc_timeout: float = Field(default=3.5, alias="RPC_TIMEOUT")
    failure_threshold: int = Field(default=2, alias="FAILURE_THRESHOLD")
    recovery_threshold: int = Field(default=2, alias="RECOVERY_THRESHOLD")

    # Gateway Ports
    gateway_port: int = Field(default=8545, alias="GATEWAY_PORT")
    haproxy_stats_port: int = Field(default=8404, alias="HAPROXY_STATS_PORT")

    # Redis Persistence
    redis_password: str = Field(default="driftguard_redis_secure_pass", alias="REDIS_PASSWORD")
    redis_url: str = Field(default="redis://:driftguard_redis_secure_pass@redis:6379/0", alias="REDIS_URL")
    redis_timeout: float = Field(default=2.0, alias="REDIS_TIMEOUT")
    history_limit: int = Field(default=100, alias="HISTORY_LIMIT")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="SENTINEL_HOST")
    port: int = Field(default=8000, alias="SENTINEL_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @model_validator(mode="before")
    @classmethod
    def harmonize_env(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Harmonize fallback_rpc_url and backup_rpc_url
            if "FALLBACK_RPC_URL" in data and "BACKUP_RPC_URL" not in data:
                data["BACKUP_RPC_URL"] = data["FALLBACK_RPC_URL"]
            elif "BACKUP_RPC_URL" in data and "FALLBACK_RPC_URL" not in data:
                data["FALLBACK_RPC_URL"] = data["BACKUP_RPC_URL"]

            # Harmonize drift thresholds
            if "BLOCK_DRIFT_THRESHOLD" in data and "DRIFT_THRESHOLD" not in data:
                data["DRIFT_THRESHOLD"] = data["BLOCK_DRIFT_THRESHOLD"]
            elif "DRIFT_THRESHOLD" in data and "BLOCK_DRIFT_THRESHOLD" not in data:
                data["BLOCK_DRIFT_THRESHOLD"] = data["DRIFT_THRESHOLD"]

            # Harmonize polling intervals (ms vs seconds)
            if "POLL_INTERVAL_MS" in data and "POLL_INTERVAL" not in data:
                try:
                    data["POLL_INTERVAL"] = float(data["POLL_INTERVAL_MS"]) / 1000.0
                except (ValueError, TypeError):
                    pass
            elif "POLL_INTERVAL" in data and "POLL_INTERVAL_MS" not in data:
                try:
                    data["POLL_INTERVAL_MS"] = int(float(data["POLL_INTERVAL"]) * 1000)
                except (ValueError, TypeError):
                    pass

        return data


settings = Settings()
