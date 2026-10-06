"""
NILE-TRADES Dashboard – FastAPI + simple HTML.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="NILE-TRADES", version="0.1.0")

STATE: Dict[str, Any] = {
    "connected": False,
    "account": {},
    "positions": [],
    "last_decisions": [],
    "memory_stats": {},
    "paused": False,
    "updated_at": 0,
}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NILE-TRADES</title>
  <style>
    :root { --bg:#0f1115; --card:#1a1d24; --text:#e6e8ec; --accent:#3b82f6; --green:#22c55e; --red:#ef4444; --muted:#9ca3af; }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family: system-ui, sans-serif; background:var(--bg); color:var(--text); padding:1.5rem; }
    h1 { font-size:1.5rem; margin-bottom:1rem; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1rem; }
    .card { background:var(--card); border-radius:12px; padding:1.25rem; }
    .card h2 { font-size:0.9rem; color:var(--muted); margin-bottom:0.75rem; text-transform:uppercase; letter-spacing:0.05em; }
    .big { font-size:1.75rem; font-weight:600; }
    .green { color:var(--green); } .red { color:var(--red); }
    table { width:100%; border-collapse:collapse; font-size:0.85rem; }
    th, td { text-align:left; padding:0.4rem 0.2rem; border-bottom:1px solid #2a2e38; }
    .status { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }
    .status.on { background:var(--green); } .status.off { background:var(--red); }
    button { background:var(--accent); color:white; border:none; padding:0.5rem 1rem; border-radius:8px; cursor:pointer; margin-top:0.5rem; }
  </style>
</head>
<body>
  <h1>NILE-TRADES</h1>
  <div class="grid">
    <div class="card"><h2>Account</h2><div id="account">Loading…</div></div>
    <div class="card"><h2>Status</h2><div id="status">Loading…</div><button onclick="togglePause()">Pause / Resume</button></div>
    <div class="card"><h2>Memory</h2><div id="memory">Loading…</div></div>
  </div>
  <div class="card" style="margin-top:1rem;"><h2>Open Positions</h2><div id="positions">Loading…</div></div>
  <div class="card" style="margin-top:1rem;"><h2>Recent Decisions</h2><div id="decisions">Loading…</div></div>
  <script>
    async function refresh() {
      const r = await fetch('/api/state');
      const d = await r.json();
      document.getElementById('account').innerHTML = d.connected
        ? `<div class="big">${d.account.equity?.toFixed(2) ?? '—'} ${d.account.currency || ''}</div>
           <div>Balance: ${d.account.balance?.toFixed(2) ?? '—'} | Profit: <span class="${(d.account.profit||0)>=0?'green':'red'}">${d.account.profit?.toFixed(2) ?? '—'}</span></div>`
        : '<span class="red">Disconnected</span>';
      document.getElementById('status').innerHTML = `
        <div><span class="status ${d.connected?'on':'off'}"></span>${d.connected?'Connected':'Disconnected'}</div>
        <div>${d.paused ? '⏸ PAUSED' : '▶ Running'}</div>
        <div style="color:var(--muted);font-size:0.8rem;margin-top:0.3rem;">Updated ${new Date(d.updated_at*1000).toLocaleTimeString()}</div>`;
      document.getElementById('memory').innerHTML = `
        Trades: ${d.memory_stats.trades||0}<br>
        Win rate: ${((d.memory_stats.win_rate||0)*100).toFixed(1)}%<br>
        Total P/L: <span class="${(d.memory_stats.total_profit||0)>=0?'green':'red'}">${(d.memory_stats.total_profit||0).toFixed(2)}</span>`;
      const pos = d.positions || [];
      document.getElementById('positions').innerHTML = pos.length
        ? `<table><tr><th>Symbol</th><th>Dir</th><th>Vol</th><th>Profit</th></tr>
           ${pos.map(p=>`<tr><td>${p.symbol}</td><td>${p.direction}</td><td>${p.volume}</td>
           <td class="${p.profit>=0?'green':'red'}">${p.profit.toFixed(2)}</td></tr>`).join('')}</table>`
        : 'No open positions';
      const dec = d.last_decisions || [];
      document.getElementById('decisions').innerHTML = dec.length
        ? `<table><tr><th>Symbol</th><th>Action</th><th>Conf</th><th>Goldman</th><th>ms</th></tr>
           ${dec.slice(-15).reverse().map(x=>`<tr>
             <td>${x.symbol}</td><td>${x.direction}</td><td>${(x.confidence*100).toFixed(0)}%</td>
             <td>${x.approved?'✓':'✗'} ${x.goldman_reason.slice(0,40)}</td>
             <td>${x.jev_latency_ms.toFixed(0)}</td></tr>`).join('')}</table>`
        : 'No decisions yet';
    }
    async function togglePause() { await fetch('/api/pause', {method:'POST'}); refresh(); }
    refresh();
    setInterval(refresh, 2000);
  </script>
</body>
</html>
"""
    return HTMLResponse(html)


@app.get("/api/state")
async def api_state():
    return JSONResponse(STATE)


@app.post("/api/pause")
async def api_pause():
    STATE["paused"] = not STATE.get("paused", False)
    return {"paused": STATE["paused"]}
