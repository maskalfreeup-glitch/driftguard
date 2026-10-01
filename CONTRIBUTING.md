# Contributing to DriftGuard

Thank you for your interest in contributing to DriftGuard, an experimental EVM JSON-RPC health and failover gateway. Performance and memory use depend on configuration and deployment; the project does not claim a general failover SLA.

---

## 1. Branch Workflow & Pull Requests

We follow a structured Git branching model to ensure production stability:

- **Target Branch**: All pull requests must target the `main` branch.
- **Branch Naming**:
  - `feature/<short-description>`: New features or architecture enhancements.
  - `fix/<issue-description>`: Bug fixes, circuit breaker corrections, or timeout adjustments.
  - `chore/<task>`: Dependency updates, CI workflows, or maintenance.
  - `docs/<subject>`: Documentation, runbooks, or architecture guides.
- **Commit Messages**: Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
  - `feat: add Base testnet configuration profile`
  - `fix: prevent race condition in sentinel redis reconnect`
  - `docs: update benchmark table for latency overhead`
- **Pull Request Checklist**:
  1. Fork the repository and clone your fork locally.
  2. Create a feature branch off `main`.
  3. Ensure code passes all linters (`flake8`, `ruff`, HAProxy syntax validation).
  4. Ensure `make test` (automated failover verification) and `make test-unit` pass cleanly.
  5. Open a Pull Request with a clear description of changes and test output.

---

## 2. Code Style & Standards

### Python (Sentinel Daemon)
- **Formatting & Style**: Follow PEP 8 guidelines. Code is verified via `ruff` and `flake8` (`--max-line-length=120`).
- **Typing**: Use strict Python type annotations (`typing.Optional`, `typing.Dict`, `typing.Any`).
- **Async Best Practices**: Sentinel is an asynchronous asyncio daemon. Avoid blocking synchronous I/O; use `asyncio.sleep()`, `httpx.AsyncClient`, and asynchronous Redis clients.
- **Memory Footprint**: Sentinel has a `96MiB` container limit. Avoid unbounded in-memory caches; all ring buffers must specify `maxlen`.

### HAProxy Gateway
- **Configuration Integrity**: HAProxy syntax must be validated before submitting:
  ```bash
  docker run --rm -v $(pwd)/haproxy:/usr/local/etc/haproxy:ro haproxy:2.8-alpine haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
  ```
- **Performance & Timeouts**: Health check timing is configurable and environment-dependent. Do not describe a fixed failover SLA without repeatable measurements that include the full request window.

### Shell Scripts
- **Portability & Safety**: All shell scripts in `scripts/` must begin with `set -euo pipefail`.
- **Status Reporting**: Standardize on clean terminal output using `[PASS]`, `[FAIL]`, `[INFO]`, and `[WARN]` indicators.

---

## 3. Testnet RPC Testing Requirements

Before proposing changes to routing, circuit breakers, or upstream providers:

1. **EVM JSON-RPC Compliance**:
   - Upstream endpoints must properly handle standard JSON-RPC 2.0 payloads (`eth_blockNumber`, `eth_chainId`, `eth_syncing`).
   - Responses must parse hexadecimal block heights (`0x...`) into valid canonical chain heads.
2. **Health and failover verification**:
   - Test against a live EVM testnet (default: Ethereum Sepolia `11155111`).
   - The automated drill measures a synthetic health transition and checks a successful fallback response. It is not a universal SLA test:
     ```bash
     make test
     ```
3. **Failure semantics**:
   - Preserve clear errors when no healthy upstream is available. Do not claim uninterrupted service unless a test measures all requests across the transition.
4. **Security & Secrets**:
   - **NEVER** commit `.env` files, private RPC API keys, Alchemy/Infura tokens, or server credentials.
   - Decouple all runtime configurations via `.env.example`.

---

## 4. Running Verification Locally

```bash
# 1. Start the stack
make up

# 2. Run unit tests
make test-unit

# 3. Run automated failover verification
make test

# 4. View container metrics & resource usage
docker stats --no-stream
```

Thank you for helping keep decentralized infrastructure resilient!
