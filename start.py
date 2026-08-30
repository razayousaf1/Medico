#!/usr/bin/env python3
"""Root-level entry point for Railway — delegates to backend/start.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))

import subprocess
port = os.environ.get("PORT", "8000")
sys.exit(subprocess.call(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port]))
