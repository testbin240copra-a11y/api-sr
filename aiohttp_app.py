# aiohttp_app.py

import os
import sys
import time
import asyncio
import json
import datetime
from aiohttp import web
from aiohttp_cors import setup as setup_cors

sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

import logging
logging.basicConfig(level=logging.CRITICAL)

from status_page import get_status_page

_stats = {
    "active": 0,
    "total": 0,
    "charged": 0,
    "approved": 0,
    "declined": 0,
    "errors": 0,
    "by": "VeNoM",
    "started": time.strftime("%Y-%m-%d %H:%M:%S"),
}

_stats_lock = asyncio.Lock()

def _save_dump(card: str, site: str, status: str, result: str, amount: str):
    try:
        with open("dump.txt", "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"[{timestamp}] {status.upper()} | {card} | {site} | {result} | ${amount}\n"
            f.write(line)
            f.flush()
    except Exception:
        pass

class VeNoMHandler(web.View):
    async def get(self):
        return await self._handle()
    
    async def post(self):
        return await self._handle()
    
    async def _handle(self):
        cc = self.request.query.get("cc")
        site = self.request.query.get("site")
        proxy = self.request.query.get("proxy", "")
        
        if self.request.method == "POST":
            try:
                body = await self.request.json()
                cc = body.get("cc", cc)
                site = body.get("site", site)
                proxy = body.get("proxy", proxy)
            except:
                pass
        
        if not cc:
            return web.json_response({"error": "Missing cc"}, status=400)
        if not site:
            return web.json_response({"error": "Missing site"}, status=400)
        
        async with _stats_lock:
            _stats["active"] += 1
            _stats["total"] += 1
        
        t0 = time.time()
        
        try:
            from checker_aiohttp import check_card
            result = await check_card(cc, site, proxy or "")
        except Exception as e:
            async with _stats_lock:
                _stats["errors"] += 1
                _stats["active"] -= 1
            return web.json_response({
                "Status": "SiteError",
                "Response": str(e)[:150],
                "Price": "-",
                "Gateway": "VeNoM",
                "Card": cc,
                "site": site,
                "elapsed": round(time.time() - t0, 2),
            })
        
        elapsed = round(time.time() - t0, 2)
        status = result.get("status", "error")
        
        status_map = {"charged": "charged", "approved": "approved", "declined": "declined"}
        async with _stats_lock:
            _stats[status_map.get(status, "errors")] += 1
            _stats["active"] -= 1
        
        if status in ("charged", "approved", "declined"):
            _save_dump(cc, site, status, result.get("result", ""), result.get("amount", "0"))
        
        bot_status = {"charged": "Charged", "approved": "Approved", "declined": "Declined"}.get(status, "SiteError")
        
        return web.json_response({
            "Status": bot_status,
            "Response": result.get("result", ""),
            "Price": result.get("amount", "-"),
            "Gateway": "VeNoM",
            "Card": cc,
            "site": site,
            "elapsed": elapsed,
        })

class StatusHandler(web.View):
    async def get(self):
        async with _stats_lock:
            stats_copy = _stats.copy()
        return await get_status_page(stats_copy)

async def health_check(request):
    return web.json_response({"ok": True})

def create_app():
    app = web.Application()
    
    cors = setup_cors(app, defaults={
        "*": {
            "allow_credentials": True,
            "allow_methods": "*",
            "allow_headers": "*",
        }
    })
    
    app.router.add_view("/VeNoM-xK9qPm2r", VeNoMHandler)
    app.router.add_view("/VeNoM-status", StatusHandler)
    app.router.add_get("/health", health_check)
    app.router.add_get("/VeNoM-status", StatusHandler)
    
    for route in list(app.router.routes()):
        cors.add(route)
    
    return app
