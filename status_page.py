# status_page.py

import time
import os
from datetime import datetime
from aiohttp import web

async def get_status_page(stats: dict) -> web.Response:
    """توليد صفحة HTML لحالة VeNoM"""
    
    total_checks = 0
    charged = 0
    approved = 0
    declined = 0
    errors = 0
    
    try:
        if os.path.exists("dump.txt"):
            with open("dump.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                total_checks = len(lines)
                for line in lines:
                    upper = line.upper()
                    if "CHARGED" in upper:
                        charged += 1
                    elif "APPROVED" in upper:
                        approved += 1
                    elif "DECLINED" in upper:
                        declined += 1
                    elif "ERROR" in upper or "SITEERROR" in upper:
                        errors += 1
    except Exception:
        pass
    
    active = stats.get("active", 0)
    total = stats.get("total", total_checks)
    charged = stats.get("charged", charged)
    approved = stats.get("approved", approved)
    declined = stats.get("declined", declined)
    errors = stats.get("errors", errors)
    started = stats.get("started", time.strftime("%Y-%m-%d %H:%M:%S"))
    by = stats.get("by", "VeNoM")
    
    total_real = charged + approved + declined + errors
    if total_real > 0:
        charged_pct = round((charged / total_real) * 100, 1)
        approved_pct = round((approved / total_real) * 100, 1)
        declined_pct = round((declined / total_real) * 100, 1)
        errors_pct = round((errors / total_real) * 100, 1)
    else:
        charged_pct = approved_pct = declined_pct = errors_pct = 0
    
    try:
        start_time = datetime.strptime(started, "%Y-%m-%d %H:%M:%S")
        uptime = datetime.now() - start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    except Exception:
        uptime_str = "N/A"
    
    html = f"""<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VeNoM - Status Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #0a0e17 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .dashboard {{
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 32px;
            padding: 48px 56px;
            max-width: 820px;
            width: 100%;
            box-shadow: 0 40px 80px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 32px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .logo {{
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #f7971e, #ffd200);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 900;
            color: #0a0e17;
            box-shadow: 0 8px 24px rgba(255, 210, 0, 0.25);
        }}
        .title {{
            color: #ffffff;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .title span {{
            background: linear-gradient(135deg, #f7971e, #ffd200);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .status-badge {{
            background: rgba(0, 255, 150, 0.12);
            border: 1px solid rgba(0, 255, 150, 0.2);
            border-radius: 100px;
            padding: 6px 16px;
            color: #00ff96;
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .status-badge .dot {{
            width: 8px;
            height: 8px;
            background: #00ff96;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.8); }}
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 28px;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 18px 16px;
            text-align: center;
            transition: all 0.3s ease;
        }}
        .stat-card:hover {{
            background: rgba(255, 255, 255, 0.07);
            transform: translateY(-2px);
        }}
        .stat-card .number {{
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 4px;
        }}
        .stat-card .label {{
            font-size: 13px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.5);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-card.charged .number {{ color: #00ff96; }}
        .stat-card.approved .number {{ color: #ffd700; }}
        .stat-card.declined .number {{ color: #ff6b6b; }}
        .stat-card.errors .number {{ color: #ff9f43; }}
        .progress-section {{
            margin-bottom: 28px;
        }}
        .progress-label {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: rgba(255, 255, 255, 0.5);
            margin-bottom: 10px;
        }}
        .progress-track {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 100px;
            overflow: hidden;
            display: flex;
        }}
        .progress-segment {{
            height: 100%;
            transition: width 0.6s ease;
        }}
        .progress-segment.charged {{ background: #00ff96; }}
        .progress-segment.approved {{ background: #ffd700; }}
        .progress-segment.declined {{ background: #ff6b6b; }}
        .progress-segment.errors {{ background: #ff9f43; }}
        .info-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 24px;
        }}
        .info-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 16px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }}
        .info-item .key {{
            color: rgba(255, 255, 255, 0.4);
            font-size: 13px;
            font-weight: 500;
        }}
        .info-item .value {{
            color: rgba(255, 255, 255, 0.85);
            font-size: 14px;
            font-weight: 600;
        }}
        .footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            font-size: 13px;
            color: rgba(255, 255, 255, 0.25);
        }}
        .footer .by {{
            color: rgba(255, 255, 255, 0.5);
        }}
        .footer .by strong {{
            background: linear-gradient(135deg, #f7971e, #ffd200);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .telegram-link {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            color: rgba(255, 255, 255, 0.5);
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            padding: 6px 14px 6px 10px;
            border-radius: 100px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            transition: all 0.3s ease;
        }}
        .telegram-link:hover {{
            background: rgba(0, 136, 204, 0.15);
            border-color: rgba(0, 136, 204, 0.3);
            color: #ffffff;
            transform: translateY(-1px);
            box-shadow: 0 8px 24px rgba(0, 136, 204, 0.15);
        }}
        .telegram-link svg {{
            width: 20px;
            height: 20px;
            flex-shrink: 0;
        }}
        @media (max-width: 640px) {{
            .dashboard {{
                padding: 28px 20px;
                border-radius: 24px;
            }}
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }}
            .stat-card .number {{
                font-size: 26px;
            }}
            .header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }}
            .info-row {{
                grid-template-columns: 1fr;
            }}
            .footer {{
                flex-direction: column;
                gap: 12px;
                text-align: center;
            }}
            .title {{
                font-size: 20px;
            }}
            .telegram-link {{
                padding: 4px 12px 4px 8px;
                font-size: 12px;
            }}
            .telegram-link svg {{
                width: 17px;
                height: 17px;
            }}
        }}
        @media (max-width: 400px) {{
            .stats-grid {{
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }}
            .stat-card {{
                padding: 12px 10px;
            }}
            .stat-card .number {{
                font-size: 22px;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <div class="brand">
                <div class="logo">V</div>
                <div class="title">VeNoM <span>Checker</span></div>
            </div>
            <div class="status-badge">
                <span class="dot"></span>
                Online
            </div>
        </div>
        <div class="stats-grid">
            <div class="stat-card charged">
                <div class="number">{charged}</div>
                <div class="label">✅ Charged</div>
            </div>
            <div class="stat-card approved">
                <div class="number">{approved}</div>
                <div class="label">🟡 Approved</div>
            </div>
            <div class="stat-card declined">
                <div class="number">{declined}</div>
                <div class="label">❌ Declined</div>
            </div>
            <div class="stat-card errors">
                <div class="number">{errors}</div>
                <div class="label">⚠️ Errors</div>
            </div>
        </div>
        <div class="progress-section">
            <div class="progress-label">
                <span>Distribution</span>
                <span>{charged_pct}% · {approved_pct}% · {declined_pct}% · {errors_pct}%</span>
            </div>
            <div class="progress-track">
                <div class="progress-segment charged" style="width: {charged_pct}%;"></div>
                <div class="progress-segment approved" style="width: {approved_pct}%;"></div>
                <div class="progress-segment declined" style="width: {declined_pct}%;"></div>
                <div class="progress-segment errors" style="width: {errors_pct}%;"></div>
            </div>
        </div>
        <div class="info-row">
            <div class="info-item">
                <span class="key">Total Checks</span>
                <span class="value">{total}</span>
            </div>
            <div class="info-item">
                <span class="key">Active Now</span>
                <span class="value">{active}</span>
            </div>
            <div class="info-item">
                <span class="key">Uptime</span>
                <span class="value">{uptime_str}</span>
            </div>
            <div class="info-item">
                <span class="key">Started</span>
                <span class="value">{started}</span>
            </div>
        </div>
        <div class="footer">
            <span>VeNoM API — Shopify Checker</span>
            <div style="display: flex; align-items: center; gap: 12px;">
                <a href="https://t.me/im_porto" target="_blank" class="telegram-link">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 24C18.6274 24 24 18.6274 24 12C24 5.37258 18.6274 0 12 0C5.37258 0 0 5.37258 0 12C0 18.6274 5.37258 24 12 24Z" fill="#0088CC"/>
                        <path d="M17.5914 6.63726L15.2426 17.2867C15.2426 17.2867 14.879 17.7631 14.109 17.4528L10.6271 14.6241L9.14023 16.0836C9.14023 16.0836 9.01792 16.2858 8.77534 16.2625L9.04975 12.7474L14.0995 8.36067C14.4551 8.05513 14.018 7.89103 13.5534 8.17934L7.17358 12.1265L3.74832 11.0399C3.74832 11.0399 3.11939 10.7895 3.15883 10.2918C3.19826 9.79398 3.97781 9.49679 3.97781 9.49679L16.8353 5.24028C16.8353 5.24028 17.5914 4.83494 17.5914 6.63726Z" fill="white"/>
                    </svg>
                    @im_porto
                </a>
                <span class="by">Powered by <strong>{by}</strong></span>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    return web.Response(text=html, content_type="text/html", status=200)