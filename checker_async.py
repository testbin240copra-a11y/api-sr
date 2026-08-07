# checker_async.py

import asyncio
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import auto_async
from auto import CheckStatus

# إخفاء الـ logs
sys.stderr = open(os.devnull, 'w')
logging.getLogger().setLevel(logging.CRITICAL)

# Per-site semaphore
_site_sems: dict[str, asyncio.Semaphore] = {}
_site_sems_lock = asyncio.Lock()

async def _get_site_sem(site: str) -> asyncio.Semaphore:
    async with _site_sems_lock:
        if site not in _site_sems:
            _site_sems[site] = asyncio.Semaphore(1)
        return _site_sems[site]

async def check_card_async(cc: str, site: str, proxy: str) -> dict:
    proxy_url = ""
    try:
        proxy_url = auto_async.normalize_proxy(proxy)
    except Exception:
        pass

    site_sem = await _get_site_sem(site)
    async with site_sem:
        try:
            res = await auto_async.run_checkout_for_card_async(site, cc, proxy_url)
        except Exception as e:
            err_msg = str(e).replace("\n", " ")[:150]
            return {
                "status": "error", "result": err_msg,
                "amount": "0", "site": site, "receipt_url": "", "card": cc,
            }

    status_map = {
        CheckStatus.CHARGED:  "charged",
        CheckStatus.APPROVED: "approved",
        CheckStatus.DECLINED: "declined",
        CheckStatus.ERROR:    "error",
    }
    status = status_map.get(res.status, "error")

    result_str = res.status_code or str(res.error) if res.error else "UNKNOWN"
    
    # تبسيط النتائج
    if status == "charged":
        result_str = "ORDER_PLACED"
    elif status == "approved":
        result_str = "3DS_AUTHENTICATION"
    elif status == "declined":
        result_str = "CARD_DECLINED"

    return {
        "status":      status,
        "result":      result_str,
        "amount":      res.amount or "0",
        "site":        site,
        "receipt_url": res.receipt_url or "",
        "card":        cc,
    }
