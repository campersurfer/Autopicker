#!/usr/bin/env python3
"""
Simple startup script for Autopicker Platform
Runs the FastAPI application with uvicorn
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    # Ensure we're in the backend directory
    backend_dir = Path(__file__).parent / "multimodal-llm-platform" / "backend"
    if not backend_dir.exists():
        backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        sys.exit(1)
    
    os.chdir(backend_dir)
    
    # Activate virtual environment and run uvicorn
    venv_python = backend_dir / "venv" / "bin" / "python"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        sys.exit(1)
    
    print("🚀 Starting Autopicker Platform...")
    print(f"📁 Working directory: {backend_dir.absolute()}")
    
    # Run with uvicorn
    cmd = [
        str(venv_python), 
        "-m", "uvicorn", 
        "simple_api:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--workers", "1"
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Autopicker Platform...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()