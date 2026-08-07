# app.py

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
import time
import asyncio
import threading
import json

app = Flask(__name__)

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

_stats_lock = threading.Lock()

def _save_dump(card, site, status, result, amount):
    try:
        with open("dump.txt", "a", encoding="utf-8") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            line = f"[{timestamp}] {status.upper()} | {card} | {site} | {result} | ${amount}\n"
            f.write(line)
            f.flush()
    except Exception:
        pass

@app.route('/VeNoM-status', methods=['GET'])
def status():
    with _stats_lock:
        stats_copy = _stats.copy()
    return jsonify({"ok": True, "api": "VeNoM", **stats_copy})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"ok": True, "status": "healthy"})

@app.route('/VeNoM-xK9qPm2r', methods=['GET', 'POST'])
def check():
    cc = request.args.get('cc')
    site = request.args.get('site')
    proxy = request.args.get('proxy', '')
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            if data:
                cc = data.get('cc', cc)
                site = data.get('site', site)
                proxy = data.get('proxy', proxy)
        except:
            pass
    
    if not cc:
        return jsonify({"error": "Missing cc"}), 400
    if not site:
        return jsonify({"error": "Missing site"}), 400
    
    with _stats_lock:
        _stats["active"] += 1
        _stats["total"] += 1
    
    t0 = time.time()
    
    try:
        import auto_async
        
        proxy_url = ""
        try:
            proxy_url = auto_async.normalize_proxy(proxy)
        except:
            pass
        
        # تشغيل async function باستخدام asyncio.run()
        res = asyncio.run(auto_async.run_checkout_for_card_async(site, cc, proxy_url))
        
        status_map = {
            auto_async.CheckStatus.CHARGED: "charged",
            auto_async.CheckStatus.APPROVED: "approved",
            auto_async.CheckStatus.DECLINED: "declined",
            auto_async.CheckStatus.ERROR: "error",
        }
        
        status = status_map.get(res.status, "error")
        result_str = res.status_code or str(res.error) if res.error else "UNKNOWN"
        
        if status == "charged":
            result_str = "ORDER_PLACED"
        elif status == "approved":
            result_str = "3DS_AUTHENTICATION"
        elif status == "declined":
            result_str = "CARD_DECLINED"
        
        with _stats_lock:
            _stats["active"] -= 1
            if status == "charged":
                _stats["charged"] += 1
            elif status == "approved":
                _stats["approved"] += 1
            elif status == "declined":
                _stats["declined"] += 1
            else:
                _stats["errors"] += 1
        
        if status in ("charged", "approved", "declined"):
            _save_dump(cc, site, status, result_str, res.amount or "0")
        
        bot_status = {"charged": "Charged", "approved": "Approved", "declined": "Declined"}.get(status, "SiteError")
        
        return jsonify({
            "Status": bot_status,
            "Response": result_str,
            "Price": res.amount or "-",
            "Gateway": "VeNoM",
            "Card": cc,
            "site": site,
            "elapsed": round(time.time() - t0, 2),
        })
        
    except Exception as e:
        with _stats_lock:
            _stats["errors"] += 1
            _stats["active"] -= 1
        return jsonify({
            "Status": "SiteError",
            "Response": str(e)[:150],
            "Price": "-",
            "Gateway": "VeNoM",
            "Card": cc,
            "site": site,
            "elapsed": round(time.time() - t0, 2),
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6767))
    print(f"Starting VeNoM Checker API on port {port}...")
    print(f"Endpoint: /VeNoM-xK9qPm2r")
    print(f"Status  : /VeNoM-status")
    print(f"Health  : /health")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
