import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # RPC Endpoints
    primary_rpc_url: str = Field(
        default="https://ethereum-sepolia-rpc.publicnode.com",
        alias="PRIMARY_RPC_URL"
    )
    backup_rpc_url: str = Field(
        default="https://sepolia.drpc.org",
        alias="BACKUP_RPC_URL"
    )
    canonical_rpc_url: str = Field(
        default="https://rpc.sepolia.ethpandaops.io",
        alias="CANONICAL_RPC_URL"
    )

    # Drift & Polling Configuration
    drift_threshold: int = Field(default=2, alias="DRIFT_THRESHOLD")
    poll_interval: float = Field(default=4.0, alias="POLL_INTERVAL")
    rpc_timeout: float = Field(default=3.5, alias="RPC_TIMEOUT")
    failure_threshold: int = Field(default=2, alias="FAILURE_THRESHOLD")
    recovery_threshold: int = Field(default=2, alias="RECOVERY_THRESHOLD")

    # Redis Persistence
    redis_url: str = Field(
        default="redis://:driftguard_secure_pass@redis:6379/0",
        alias="REDIS_URL"
    )
    redis_timeout: float = Field(default=2.0, alias="REDIS_TIMEOUT")
    history_limit: int = Field(default=100, alias="HISTORY_LIMIT")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="SENTINEL_HOST")
    port: int = Field(default=8000, alias="SENTINEL_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

settings = Settings()
