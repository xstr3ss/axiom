#!/bin/bash
echo "🚀 Starting Fable with High-Speed Uvicorn Workers..."
# Kill any stuck ports cleanly
fuser -k 8000/tcp 2>/dev/null || pkill -f "uvicorn server:app"; sleep 1
# Run with uvicorn directly for async speed
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
