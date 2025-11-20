#!/usr/bin/env bash
# Automated helper: build backend, restart, apply normalization, collect report
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DC=""

echo "Detecting docker compose command..."
if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  DC="docker compose"
else
  echo "docker-compose or docker compose not found in PATH" >&2
  exit 1
fi

# Check if docker command needs sudo
SUDO=""
if ! ${DC} ps >/dev/null 2>&1; then
  echo "docker compose requires sudo; using sudo for subsequent commands"
  SUDO="sudo"
fi

echo "Using: ${SUDO} ${DC}"

REPORT_DIR="${REPO_ROOT}/.normalize_report"
mkdir -p "${REPORT_DIR}"

echo "Building backend image..."
${SUDO} ${DC} build --no-cache backend

echo "Starting backend (no deps)..."
${SUDO} ${DC} up -d --no-deps backend

echo "Waiting 5s for container to initialize..."
sleep 5

echo "Applying normalization script inside backend container..."
# Run apply
${SUDO} ${DC} exec backend python /app/scripts/normalize_alerts.py --apply | tee "${REPORT_DIR}/apply_output.txt"

echo "Collecting DB report via container script..."
${SUDO} ${DC} exec backend python /app/scripts/collect_alerts_report.py > "${REPORT_DIR}/alerts_report.json"

echo "Saving backend logs (tail 200)..."
${SUDO} ${DC} logs --tail 200 backend > "${REPORT_DIR}/backend_logs.txt" || true

echo "Done. Report directory: ${REPORT_DIR}"
echo "Files generated:"
ls -la "${REPORT_DIR}"

echo "To view the JSON report, run: jq . ${REPORT_DIR}/alerts_report.json"
