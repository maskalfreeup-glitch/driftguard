# Funding plan

DriftGuard is an experimental open source EVM RPC health and failover gateway. Funding would support engineering, independent review, and reproducible evaluation. No grant is assumed or awarded by this plan.

## Proposed 12-week milestones

1. **Trustworthy health decisions (weeks 1–4):** fail closed on missing or stale canonical data; validate chain IDs and RPC responses; publish unit and integration coverage for failure cases.
2. **Reproducible evaluation (weeks 5–8):** provide scripted fault injection for latency, stale heads, wrong chain IDs, reference outages, and provider errors; publish methodology and results across repeated runs.
3. **Rollup support and adoption (weeks 9–12):** document deployment profiles for Ethereum L1 and selected EVM rollups, gather operator feedback, and publish a compatibility matrix. L2-specific finality and sequencer health are separate signals and will not be inferred from block height alone.

## Deliverables and reporting

Each milestone should produce merged code, public documentation, and a tagged release or reproducible report. Progress reports should include completed work, test evidence, spend by category, and remaining risks. Funding requests should specify their amount and adapt the milestone scope to the relevant ecosystem program.

## Cost categories

- Maintainer engineering and security review
- CI and controlled test infrastructure
- RPC access for repeatable multi-provider evaluation
- Documentation and operator onboarding

Specific amounts should be set in an ecosystem application based on its term, rates, and infrastructure requirements; this repository does not yet have independently validated cost estimates.
