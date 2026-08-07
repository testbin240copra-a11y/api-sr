# checker_aiohttp.py

import random
import time
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# استدعاء auto.py الأصلي (اللي شغال مع curl_cffi)
import auto
from auto import CheckStatus

from config import SITE_FILE, SITE_LOW_FILE, SITE_MID_FILE

_SITE_PATHS = {
    "random": SITE_FILE,
    "low": SITE_LOW_FILE,
    "mid": SITE_MID_FILE,
}

_dead_sites = {}
_dead_lock = asyncio.Lock()

_SITE_TTL = {
    "returned 429": 1800,
    "returned 403": 3600,
    "returned 402": 300,
    "returned 422": 300,
    "returned 404": 86400,
    "Step 0 failed": 90,
}

_alive_sites = {}
_alive_dirty = {t: True for t in _SITE_PATHS}

def _norm_range(site_range):
    return site_range if site_range in _SITE_PATHS else "random"

def _rebuild_alive(site_range="random"):
    global _alive_sites, _alive_dirty
    tier = _norm_range(site_range)
    now = time.time()
    expired = [u for u, exp in list(_dead_sites.items()) if exp <= now]
    for u in expired:
        _dead_sites.pop(u, None)
    pool = _base_pool(tier)
    _alive_sites[tier] = [s for s in pool if s not in _dead_sites]
    _alive_dirty[tier] = False

def _is_dead(site_url):
    exp = _dead_sites.get(site_url)
    if exp is None:
        return False
    if time.time() < exp:
        return True
    _dead_sites.pop(site_url, None)
    return False

def _mark_dead(site_url, error_str):
    global _alive_dirty
    if not error_str:
        return
    for pattern, ttl in _SITE_TTL.items():
        if pattern in error_str.lower():
            _dead_sites[site_url] = time.time() + ttl
            for t in _SITE_PATHS:
                _alive_dirty[t] = True
            return

def _load_sites(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        return []

_sites = {tier: _load_sites(path) for tier, path in _SITE_PATHS.items()}

def _base_pool(site_range="random"):
    tier = _norm_range(site_range)
    primary = _sites.get(tier) or []
    if primary:
        return primary
    if tier in ("low", "mid"):
        return _sites.get("random") or []
    return []

def get_random_site(site_range="random"):
    tier = _norm_range(site_range)
    pool = _base_pool(tier)
    if not pool:
        return None
    if _alive_dirty.get(tier, True):
        _rebuild_alive(tier)
    alive = _alive_sites.get(tier) or []
    pick = alive if alive else pool
    return random.choice(pick)

def normalize_proxy(proxy):
    return auto.normalize_proxy(proxy)

_APPROVED_KEYWORDS = (
    "3DS_AUTHENTICATION", "3DS_AUTH", "3DS",
    "AUTHENTICATION_REQUIRED", "ACTIONREQUIRED",
    "INSUFFICIENT_FUNDS",
)
_DECLINED_KEYWORDS = (
    "CARD_DECLINED", "DECLINED", "DO_NOT_HONOR", "GENERIC_ERROR",
    "EXPIRED_CARD", "PICKUP_CARD", "LOST_CARD", "STOLEN_CARD",
    "FRAUD", "CALL_ISSUER", "TRANSACTION_NOT_ALLOWED",
    "INVALID_NUMBER", "INCORRECT_NUMBER",
)
_INFRA_ERROR_KEYWORDS = (
    "STEP", "FAILED", "RETURNED 4", "RETURNED 5", "RETURNED 402",
    "RETURNED 422", "RETURNED 429", "PROXY", "TIMEOUT", "TIMED OUT",
    "COULD NOT", "POLL", "EXCEEDED", "INVENTORYRESERVATIONFAILURE",
)

def normalize_result(status, result_str):
    resp = (result_str or "").strip() or "UNKNOWN"
    up = resp.upper()

    if any(k in up for k in ("ORDER_PLACED", "SUCCESSFULRECEIPT", "PROCESSEDRECEIPT")):
        return "charged", resp
    if any(k in up for k in _APPROVED_KEYWORDS):
        return "approved", resp
    if status == "declined" or any(k in up for k in _DECLINED_KEYWORDS):
        return "declined", resp
    if any(k in up for k in _INFRA_ERROR_KEYWORDS):
        return "error", resp
    return "error", resp

def _exc_text(exc):
    if exc is None:
        return ""
    if exc.args and exc.args[0]:
        return str(exc.args[0])
    return str(exc) or ""

async def check_card(cc: str, site: str, proxy: str) -> dict:
    proxy_url = ""
    try:
        proxy_url = normalize_proxy(proxy)
    except Exception:
        pass

    try:
        # استدعاء auto.py الأصلي (غير متزامن)
        res = auto.run_checkout_for_card(site, cc, proxy_url)
    except Exception as e:
        err_msg = str(e).replace("\n", " ")[:150]
        _mark_dead(site, err_msg)
        return {
            "status": "error", "result": err_msg,
            "amount": "0", "site": site, "receipt_url": "", "card": cc,
        }

    status_map = {
        CheckStatus.CHARGED: "charged",
        CheckStatus.APPROVED: "approved",
        CheckStatus.DECLINED: "declined",
        CheckStatus.ERROR: "error",
    }
    status = status_map.get(res.status, "error")

    result_str = res.status_code or _exc_text(res.error) or "UNKNOWN"
    status, result_str = normalize_result(status, result_str)

    if status == "error":
        _mark_dead(site, result_str)

    return {
        "status": status,
        "result": result_str,
        "amount": res.amount or "0",
        "site": site,
        "receipt_url": res.receipt_url or "",
        "card": cc,
    }
