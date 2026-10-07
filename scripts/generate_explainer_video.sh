#!/usr/bin/env bash
# ==============================================================================
# DriftGuard - Deterministic Headless Explainer Video Generator Runner
# ==============================================================================
# Usage:
#   ./scripts/generate_explainer_video.sh                   # Full 1080p MP4
#   ./scripts/generate_explainer_video.sh --preview         # Fast 720p preview
#   ./scripts/generate_explainer_video.sh --scene 3         # Render Scene 3 only
#   ./scripts/generate_explainer_video.sh -o my_video.mp4   # Custom output path
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Resolve Python interpreter (.venv or system)
if [ -f "${PROJECT_ROOT}/.venv/bin/python" ]; then
    PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "Error: Python 3 not found. Please install Python 3 or create a virtualenv." >&2
    exit 1
fi

# Verify FFmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Error: ffmpeg is required but not installed." >&2
    echo "Install via: sudo apt-get install ffmpeg (Ubuntu/Debian) or brew install ffmpeg (macOS)" >&2
    exit 1
fi

# Run python video generator
exec "${PYTHON_BIN}" "${PROJECT_ROOT}/scripts/generate_explainer_video.py" "$@"
