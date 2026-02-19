#!/usr/bin/env bash
# install_session_templates.sh — Symlink session template scripts into REAPER Scripts path
#
# Usage: ./scripts/install_session_templates.sh
#
# Creates a symlink from the repo's lua/session_template/ directory
# to REAPER's Scripts/SessionTemplate/ so REAPER can load the scripts directly.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="${REPO_DIR}/lua/session_template"
REAPER_SCRIPTS="${HOME}/Library/Application Support/REAPER/Scripts"
TARGET_DIR="${REAPER_SCRIPTS}/SessionTemplate"

echo "Session Template Installer"
echo "=========================="
echo ""
echo "Source: ${SOURCE_DIR}"
echo "Target: ${TARGET_DIR}"
echo ""

# Check source exists
if [ ! -d "${SOURCE_DIR}" ]; then
    echo "ERROR: Source directory not found: ${SOURCE_DIR}"
    exit 1
fi

# Check REAPER Scripts directory exists
if [ ! -d "${REAPER_SCRIPTS}" ]; then
    echo "WARNING: REAPER Scripts directory not found: ${REAPER_SCRIPTS}"
    echo "Is REAPER installed? Creating directory..."
    mkdir -p "${REAPER_SCRIPTS}"
fi

# Handle existing target
if [ -L "${TARGET_DIR}" ]; then
    existing=$(readlink "${TARGET_DIR}")
    if [ "${existing}" = "${SOURCE_DIR}" ]; then
        echo "Already installed (symlink exists and is correct)."
        exit 0
    fi
    echo "Existing symlink points to: ${existing}"
    echo "Updating to point to: ${SOURCE_DIR}"
    rm "${TARGET_DIR}"
elif [ -d "${TARGET_DIR}" ]; then
    echo "ERROR: ${TARGET_DIR} exists as a real directory."
    echo "Please remove or rename it first, then re-run this script."
    exit 1
fi

# Create symlink
ln -s "${SOURCE_DIR}" "${TARGET_DIR}"
echo "Symlink created: ${TARGET_DIR} → ${SOURCE_DIR}"
echo ""
echo "Next steps:"
echo "  1. Open REAPER"
echo "  2. Actions → Show action list"
echo "  3. Load: Scripts/SessionTemplate/session_template.lua"
echo "  4. Bind to a key (e.g., Ctrl+Shift+N)"
echo ""
echo "Done."
