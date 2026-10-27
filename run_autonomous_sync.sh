#!/usr/bin/env bash
set -e

PROJECT_DIR="/home/uxd/autonomous-engine"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"

cd "$PROJECT_DIR"

echo "=== [Fable Autonomous Sync: $(date)] ===" >> /tmp/fable-sync.log

# 1. Harvest historic git fixes & external dataset updates
$VENV_PYTHON harvester.py >> /tmp/fable-sync.log 2>&1

# 2. Update architectural & semantic memory
$VENV_PYTHON semantic_watcher.py >> /tmp/fable-sync.log 2>&1

echo "=== [Sync Complete] ===" >> /tmp/fable-sync.log
