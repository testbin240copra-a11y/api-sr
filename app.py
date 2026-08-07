# app.py

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 6767))
    print(f"Starting VeNoM Checker API on port {port}...")
    print(f"Endpoint: /VeNoM-xK9qPm2r")
    print(f"Status  : /VeNoM-status")
    
    uvicorn.run(
        "checker_api2:app",
        host="0.0.0.0",
        port=port,
        access_log=False,
        log_level="critical",
    )
