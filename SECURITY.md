# Security policy

## Reporting a vulnerability

Please do not report security vulnerabilities in public issues. Email **hello@maskal.space** with a description, impact, and steps to reproduce. The maintainers will acknowledge reports within seven days and coordinate a fix and disclosure timeline with the reporter.

## Deployment notes

- Keep the Sentinel diagnostic port and HAProxy stats port private or behind authenticated access.
- Set a unique `DRIFTGUARD_ADMIN_TOKEN` only when chaos drill endpoints are needed. Those endpoints are disabled when the value is empty.
- Do not use example credentials in a public deployment. Protect RPC provider URLs as secrets when they contain credentials.
- DriftGuard is experimental and should not be the sole protection for safety-critical transaction flows.
