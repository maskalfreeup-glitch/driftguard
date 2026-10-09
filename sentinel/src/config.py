import logging
import os
import re
from urllib.parse import urlsplit

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

logger = logging.getLogger("driftguard.config")

ANCHOR_ENV_OVERRIDES: dict[str | int, str] = {
    "arbitrum-one": "ANCHOR_ARB_ONE",
    42161: "ANCHOR_ARB_ONE",
    "be_arb": "ANCHOR_ARB_ONE",
    "arbitrum-nova": "ANCHOR_ARB_NOVA",
    42170: "ANCHOR_ARB_NOVA",
    "be_nova": "ANCHOR_ARB_NOVA",
    "arbitrum-sepolia": "ANCHOR_ARB_SEPOLIA",
    421614: "ANCHOR_ARB_SEPOLIA",
    "be_arb_sepolia": "ANCHOR_ARB_SEPOLIA",
}


def _resolve_anchor_override(chain_entry: dict) -> dict:
    data = dict(chain_entry)
    name = data.get("name")
    chain_id = data.get("chain_id")
    backend = data.get("backend")

    env_var = (
        ANCHOR_ENV_OVERRIDES.get(name)
        or ANCHOR_ENV_OVERRIDES.get(chain_id)
        or ANCHOR_ENV_OVERRIDES.get(backend)
    )
    if env_var:
        override_val = os.environ.get(env_var, "").strip()
        if override_val:
            data["reference_url"] = override_val
            logger.info("Overriding reference_url for chain '%s' from %s", name, env_var)

    return data


class ChainConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    chain_id: int
    backend: str
    primary_url: str
    fallback_url: str
    reference_url: str
    reference_fallback_urls: list[str] = Field(default_factory=list)
    drift_threshold: int = 2
    poll_interval: float = 0.2
    fail_open: bool = False

    @model_validator(mode="after")
    def validate_identity_and_urls(self):
        if self.chain_id <= 0 or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", self.backend):
            raise ValueError("chain_id must be positive and backend must be an HAProxy identifier")
        for field_name in ("primary_url", "fallback_url", "reference_url"):
            val = getattr(self, field_name)
            parsed_url = urlsplit(val or "")
            if parsed_url.scheme != "https" or not parsed_url.hostname or parsed_url.fragment:
                raise ValueError(f"{field_name} must use HTTPS")
        for fb_url in self.reference_fallback_urls:
            parsed_url = urlsplit(fb_url or "")
            if parsed_url.scheme != "https" or not parsed_url.hostname or parsed_url.fragment:
                raise ValueError("reference_fallback_urls must use HTTPS")
        if len({self.primary_url, self.fallback_url, self.reference_url}) != 3:
            raise ValueError("primary, fallback, and reference URLs must be independent endpoints")
        if self.poll_interval <= 0 or self.drift_threshold < 0:
            raise ValueError("poll_interval must be positive and drift_threshold non-negative")
        return self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    chains_config_path: str = Field(default="sentinel/config/chains.yaml", alias="CHAINS_CONFIG_PATH")
    haproxy_socket_path: str = Field(default="/run/haproxy/admin.sock", alias="HAPROXY_SOCKET_PATH")
    discord_webhook_url: str = Field(default="", alias="DISCORD_WEBHOOK_URL")
    rpc_timeout: float = Field(default=3.5, gt=0, alias="RPC_TIMEOUT")
    failure_threshold: int = Field(default=2, ge=1, alias="FAILURE_THRESHOLD")
    recovery_threshold: int = Field(default=2, ge=1, alias="RECOVERY_THRESHOLD")
    max_reference_age: float = Field(default=10.0, gt=0, alias="MAX_REFERENCE_AGE")
    admin_token: str = Field(default="", alias="DRIFTGUARD_ADMIN_TOKEN")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    redis_timeout: float = Field(default=2.0, alias="REDIS_TIMEOUT")
    history_limit: int = Field(default=100, alias="HISTORY_LIMIT")
    host: str = Field(default="0.0.0.0", alias="SENTINEL_HOST")
    port: int = Field(default=8000, alias="SENTINEL_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    anchor_arb_one: str = Field(default="", alias="ANCHOR_ARB_ONE")
    anchor_arb_nova: str = Field(default="", alias="ANCHOR_ARB_NOVA")
    anchor_arb_sepolia: str = Field(default="", alias="ANCHOR_ARB_SEPOLIA")


def load_chains_config(config_path: str | None = None) -> list[ChainConfig]:

    """
    Loads multi-tenant chain configurations from chains.yaml.
    Falls back to built-in EVM chain definitions if file is not found.
    """
    candidate_paths = []
    if config_path:
        candidate_paths.append(config_path)

    env_path = os.environ.get("CHAINS_CONFIG_PATH")
    configured_path = config_path or env_path
    if configured_path:
        candidate_paths = [configured_path]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate_paths.extend([
        os.path.join(base_dir, "config", "chains.yaml"),
        "/app/sentinel/config/chains.yaml",
        "sentinel/config/chains.yaml",
        "chains.yaml",
    ])

    for path in candidate_paths:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    parsed = yaml.safe_load(f)
                    has_chains = isinstance(parsed, dict) and isinstance(parsed.get("chains"), list)
                    if not has_chains or not parsed["chains"]:
                        raise ValueError("configuration must contain a non-empty chains list")

                    chains = [ChainConfig(**_resolve_anchor_override(c)) for c in parsed["chains"]]
                    names = {c.name for c in chains}
                    backends = {c.backend for c in chains}
                    if (len(names) != len(chains) or len(backends) != len(chains)
                            or names & backends):
                        raise ValueError("chain names and HAProxy backends must be unique")
                    logger.info("Loaded %s chain configurations from %s", len(chains), path)
                    return chains

            except Exception as e:
                raise ValueError(f"Invalid chains configuration at {path}: {e}") from e

    if configured_path:
        raise FileNotFoundError(f"Configured chains file not found: {configured_path}")
    logger.warning("No chains.yaml file found; using built-in multi-chain defaults.")
    fallback_defaults = [
        {
            "name": "base-mainnet",
            "chain_id": 8453,
            "backend": "be_base",
            "primary_url": "https://mainnet.base.org",
            "fallback_url": "https://base-rpc.publicnode.com",
            "reference_url": "https://base.gateway.tenderly.co",
            "drift_threshold": 2,
            "poll_interval": 0.2,
        },
        {
            "name": "arbitrum-one",
            "chain_id": 42161,
            "backend": "be_arb",
            "primary_url": "https://arb1.arbitrum.io/rpc",
            "fallback_url": "https://arbitrum-one-rpc.publicnode.com",
            "reference_url": "https://arbitrum.gateway.tenderly.co",
            "drift_threshold": 4,
            "poll_interval": 0.2,
        },
        {
            "name": "sepolia-testnet",
            "chain_id": 11155111,
            "backend": "be_sepolia",
            "primary_url": "https://ethereum-sepolia-rpc.publicnode.com",
            "fallback_url": "https://sepolia.gateway.tenderly.co",
            "reference_url": "https://rpc.sepolia.ethpandaops.io",
            "drift_threshold": 2,
            "poll_interval": 0.2,
        },
    ]
    return [ChainConfig(**_resolve_anchor_override(d)) for d in fallback_defaults]


settings = Settings()
