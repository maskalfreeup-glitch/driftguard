#!/usr/bin/env bash
# ==============================================================================
# DriftGuard - Maintainer Business Dossier Desktop Exporter
# ==============================================================================
# Compiles all business documents deterministically via Typst and exports
# the complete dossier package to /home/masky/Desktop.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DESKTOP_DIR="/home/masky/Desktop"
DOSSIER_DIR="${DESKTOP_DIR}/DriftGuard_Business_Dossier"

echo "======================================================================"
echo " DriftGuard Maintainer Business Dossier: Exporting to Desktop"
echo "======================================================================"

mkdir -p "${DOSSIER_DIR}"

# 1. Compile all documents deterministically
echo "[+] Compiling Executive Tooling Grant Proposal..."
typst compile --root "${PROJECT_ROOT}" \
    "${PROJECT_ROOT}/docs/DriftGuard_Executive_Grant_Proposal.typ" \
    "${PROJECT_ROOT}/docs/DriftGuard_Executive_Grant_Proposal.pdf"

echo "[+] Compiling B2B Retainer Service SOP..."
typst compile --root "${PROJECT_ROOT}" \
    "${PROJECT_ROOT}/docs/DriftGuard_B2B_Retainer_SOP.typ" \
    "${PROJECT_ROOT}/docs/DriftGuard_B2B_Retainer_SOP.pdf"

echo "[+] Compiling Maintainer Grant Application Playbook..."
typst compile --root "${PROJECT_ROOT}" \
    "${PROJECT_ROOT}/docs/DriftGuard_Grant_Application_Playbook.typ" \
    "${PROJECT_ROOT}/docs/DriftGuard_Grant_Application_Playbook.pdf"

echo "[+] Compiling YouTube Client Acquisition Series Blueprint..."
typst compile --root "${PROJECT_ROOT}" \
    "${PROJECT_ROOT}/docs/DriftGuard_YouTube_Client_Acquisition_Series.typ" \
    "${PROJECT_ROOT}/docs/DriftGuard_YouTube_Client_Acquisition_Series.pdf"

# 2. Sync to Desktop Dossier Folder
echo "[+] Populating ${DOSSIER_DIR}..."

cp -f "${PROJECT_ROOT}/docs/DriftGuard_Executive_Grant_Proposal.pdf" \
      "${DOSSIER_DIR}/01_DriftGuard_Tooling_Grant_Proposal.pdf"
cp -f "${PROJECT_ROOT}/GRANT_PROPOSAL_MULTI_ECOSYSTEM.md" \
      "${DOSSIER_DIR}/01_DriftGuard_Tooling_Grant_Proposal.md"

cp -f "${PROJECT_ROOT}/docs/DriftGuard_B2B_Retainer_SOP.pdf" \
      "${DOSSIER_DIR}/02_DriftGuard_B2B_Retainer_SOP.pdf"
cp -f "${PROJECT_ROOT}/docs/B2B_RETAINER_SERVICE_SOP.md" \
      "${DOSSIER_DIR}/02_DriftGuard_B2B_Retainer_SOP.md"

cp -f "${PROJECT_ROOT}/docs/DriftGuard_Grant_Application_Playbook.pdf" \
      "${DOSSIER_DIR}/03_DriftGuard_Maintainer_Grant_Playbook.pdf"
cp -f "${PROJECT_ROOT}/docs/GRANT_APPLICATION_PLAYBOOK.md" \
      "${DOSSIER_DIR}/03_DriftGuard_Maintainer_Grant_Playbook.md"

cp -f "${PROJECT_ROOT}/docs/DriftGuard_YouTube_Client_Acquisition_Series.pdf" \
      "${DOSSIER_DIR}/04_DriftGuard_YouTube_Client_Acquisition_Series.pdf"
cp -f "${PROJECT_ROOT}/docs/YOUTUBE_CLIENT_ACQUISITION_BLUEPRINT.md" \
      "${DOSSIER_DIR}/04_DriftGuard_YouTube_Client_Acquisition_Series.md"

# 3. Direct access convenience copies on Desktop root
cp -f "${PROJECT_ROOT}/docs/DriftGuard_Executive_Grant_Proposal.pdf" \
      "${DESKTOP_DIR}/DriftGuard_Tooling_Grant_Proposal.pdf"
cp -f "${PROJECT_ROOT}/docs/DriftGuard_B2B_Retainer_SOP.pdf" \
      "${DESKTOP_DIR}/DriftGuard_B2B_Retainer_SOP.pdf"
cp -f "${PROJECT_ROOT}/docs/DriftGuard_Grant_Application_Playbook.pdf" \
      "${DESKTOP_DIR}/DriftGuard_Maintainer_Grant_Playbook.pdf"
cp -f "${PROJECT_ROOT}/docs/DriftGuard_YouTube_Client_Acquisition_Series.pdf" \
      "${DESKTOP_DIR}/DriftGuard_YouTube_Client_Acquisition_Series.pdf"

# Clean up older unnumbered root file if present
rm -f "${DESKTOP_DIR}/DriftGuard_Executive_Grant_Proposal.pdf"

# 4. Generate Master Index README in Dossier
cat << 'INDEX_EOF' > "${DOSSIER_DIR}/README_MAINTAINER_INDEX.md"
# DriftGuard Systems: Maintainer Business & Operations Dossier

**Confidential Document Package for DriftGuard Maintainers & Lead Systems Engineers**  
**Effective Date:** October 2026 | Version 2.0  
**License:** Open Source Core (MIT) + Enterprise B2B Retainers

---

## 📁 Package Contents

### 1. Developer Tooling Grant Proposal
- **PDF Dossier (8 Pages):** `01_DriftGuard_Tooling_Grant_Proposal.pdf`
- **Markdown Source:** `01_DriftGuard_Tooling_Grant_Proposal.md`
- **Core Value:** 100% open-source software engineering grant proposal ($35,000 USD request across 4 milestones) for Arbitrum Foundation/Questbook, Base, Optimism, and Gitcoin. **$0 requested for hosting.** Live cluster at `rpc.driftguard.live` is framed as a self-funded empirical proof harness.

### 2. Commercial B2B Client Retainer SOP
- **PDF Dossier (5 Pages):** `02_DriftGuard_B2B_Retainer_SOP.pdf`
- **Markdown Source:** `02_DriftGuard_B2B_Retainer_SOP.md`
- **Core Value:** Complete commercial operations runbook for institutional clients (Orbit L3 rollups, Web3 game studios, ERC-4337 paymaster bundlers).
- **Service Tiers:**
  - *Tier 1: Sentinel Standard* — $2,500 / month
  - *Tier 2: Orbit Rollup Mission-Critical* — $5,000 / month (<15 min Sev-1 SLA)
  - *Tier 3: Institutional Sovereign / Paymaster* — $8,500 / month (99.99% SLA)
- **SOP Runbooks:** Onboarding pre-flight audit, sidecar injection patterns, drift threshold tuning, 24/7 incident escalation workflow, bi-weekly chaos drills, and monthly vendor scorecards.

### 3. Maintainer Grant Application Playbook
- **PDF Dossier (3 Pages):** `03_DriftGuard_Maintainer_Grant_Playbook.pdf`
- **Markdown Source:** `03_DriftGuard_Maintainer_Grant_Playbook.md`
- **Core Value:** Tactical application guide with direct submission portal URLs, copy-paste form fields, week-by-week sprint calendar, reviewer 60-second terminal verification commands, and interview defense cheat-sheet.

### 4. YouTube Client Acquisition Series Blueprint & Script Pack
- **PDF Dossier (6 Pages):** `04_DriftGuard_YouTube_Client_Acquisition_Series.pdf`
- **Markdown Source:** `04_DriftGuard_YouTube_Client_Acquisition_Series.md`
- **Core Value:** The "Educational Trojan Horse" positioning strategy. Complete word-for-word spoken scripts for 4 episodes teaching deep systems engineering (The Silent 200 OK trap, ERC-4337 nonce desyncs, sub-130ms UNIX socket draining, active-active Orbit L3 clusters).
- **Lead Magnet & Inbound CTA:** Drives viewers to book a *Free 48-Hour RPC Resilience & Staleness Audit*, bridging directly into $2,500 – $8,500/mo retainer closes. Includes discovery call closing scripts and YouTube SEO metadata.

---

## 🔒 Confidentiality & Integrity Notice
All documents in this folder are local internal maintainer assets. None of these documents have been published or committed to external repositories.
INDEX_EOF

echo "[+] Computing SHA-256 Checksums..."
sha256sum "${DOSSIER_DIR}"/*.pdf > "${DOSSIER_DIR}/checksums.sha256"

echo "======================================================================"
echo "[+] Export complete! All business documents ready in:"
echo "    -> ${DOSSIER_DIR}"
echo "    -> Direct desktop PDFs at ${DESKTOP_DIR}"
echo "======================================================================"
