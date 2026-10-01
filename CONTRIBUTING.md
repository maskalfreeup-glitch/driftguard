# Contributing to DriftGuard

Thank you for your interest in contributing to DriftGuard! DriftGuard is an open-source, resilient EVM JSON-RPC failover gateway designed to guarantee sub-4s failover, consensus drift mitigation, and an ultra-lean (<100MB RAM) runtime footprint.

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
- **Memory Footprint**: Sentinel must run stably within a strict `48MB` RAM budget (`mem_limit: 48m`). Avoid unbounded in-memory caches; all ring buffers must specify `maxlen`.

### HAProxy Gateway
- **Configuration Integrity**: HAProxy syntax must be validated before submitting:
  ```bash
  docker run --rm -v $(pwd)/haproxy:/usr/local/etc/haproxy:ro haproxy:2.8-alpine haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg
  ```
- **Performance & Timeouts**: Maintain aggressive keep-alive and health check timers (`inter 1s fastinter 500ms fall 2 rise 2`) to ensure sub-4.0s failover SLA.

### Shell Scripts
- **Portability & Safety**: All shell scripts in `scripts/` must begin with `set -euo pipefail`.
- **Status Reporting**: Standardize on clean terminal output using `[PASS]`, `[FAIL]`, `[INFO]`, and `[WARN]` indicators.

---

## 3. Testnet RPC Testing Requirements

Before proposing changes to routing, circuit breakers, or upstream providers:

1. **EVM JSON-RPC Compliance**:
   - Upstream endpoints must properly handle standard JSON-RPC 2.0 payloads (`eth_blockNumber`, `eth_chainId`, `eth_syncing`).
   - Responses must parse hexadecimal block heights (`0x...`) into valid canonical chain heads.
2. **Consensus Drift Verification**:
   - Test against a live EVM testnet (default: Ethereum Sepolia `11155111`).
   - Run the automated failover suite to verify active-passive failover within 4.0s:
     ```bash
     make test
     ```
3. **Zero 5xx Guarantee**:
   - The gateway must never return HTTP 500, 502, 503, or 504 errors during upstream failover transitions.
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
