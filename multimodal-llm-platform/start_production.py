#!/usr/bin/env python3
"""
Production startup script for Autopicker API
Uses uvicorn with proper production settings
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    # Production configuration
    uvicorn.run(
        "simple_api:app",
        host="0.0.0.0",
        port=8001,
        workers=1,  # Single worker for monitoring consistency
        log_level="info",
        access_log=True,
        reload=False,  # Disable reload in production
        loop="asyncio"
    )