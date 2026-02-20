# main.py
# ─────────────────────────────────────────────
# Application entry point. Imports app from api.py and starts uvicorn.
# Reload enabled for development — restarts on any file change.
# Runs on 0.0.0.0:8000 so it's accessible from other machines.
# Logging configured at INFO level with timestamps and module names.
# ─────────────────────────────────────────────

import logging
from api import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)