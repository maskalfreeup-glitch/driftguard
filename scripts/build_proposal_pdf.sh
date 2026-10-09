#!/usr/bin/env bash
# ==============================================================================
# DriftGuard - Deterministic Executive PDF Grant Proposal Compiler
# ==============================================================================
# Compiles the executive grant proposal dossier deterministically using Typst.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SOURCE_TYP="${PROJECT_ROOT}/docs/DriftGuard_Executive_Grant_Proposal.typ"
OUTPUT_PDF="${PROJECT_ROOT}/docs/DriftGuard_Executive_Grant_Proposal.pdf"
ROOT_PDF="${PROJECT_ROOT}/DriftGuard_Executive_Grant_Proposal.pdf"

echo "======================================================================"
echo " DriftGuard Executive Grant Proposal: Deterministic PDF Build"
echo "======================================================================"

if ! command -v typst &> /dev/null; then
    echo "[-] Error: 'typst' compiler not found in PATH."
    exit 1
fi

TYPST_VERSION=$(typst --version)
echo "[+] Using compiler: ${TYPST_VERSION}"
echo "[+] Source file:    ${SOURCE_TYP}"

# Compile deterministically using root anchor
typst compile --root "${PROJECT_ROOT}" "${SOURCE_TYP}" "${OUTPUT_PDF}"

# Create root convenience copy
cp -f "${OUTPUT_PDF}" "${ROOT_PDF}"

# Compute deterministic SHA-256 checksum
CHECKSUM=$(sha256sum "${OUTPUT_PDF}" | awk '{print $1}')
FILESIZE=$(stat -c%s "${OUTPUT_PDF}")

echo "[+] Compilation successful!"
echo "[+] PDF Artifact:   ${OUTPUT_PDF} (${FILESIZE} bytes)"
echo "[+] Root Artifact:  ${ROOT_PDF}"
echo "[+] SHA-256 Digest: ${CHECKSUM}"
echo "======================================================================"
