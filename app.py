# app.py

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import asyncio
    import uvloop
    from aiohttp import web
    
    import aiohttp_app
    
    port = int(os.environ.get("PORT", 6667))
    
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    app = aiohttp_app.create_app()
    web.run_app(app, host="0.0.0.0", port=port, access_log=None)
