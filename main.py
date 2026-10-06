"""
NILE-TRADES entry point.
Fast local signal → Goldman filters → MT5. No Jev.
Target cycle: ~150–250 ms across 10 symbols.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Any

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from config.settings import settings
from mt5 import MT5Connector, ALL_SYMBOLS
from engine import DecisionEngine
from memory.trade_memory import TradeMemory
from dashboard.app import app, STATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nile")

# Loop timing (seconds). 0.15–0.25 is aggressive but stable on retail MT5.
LOOP_INTERVAL = 0.20


def build_features(symbol: str, connector: MT5Connector) -> Dict[str, float]:
    """Minimal features — keep under 1–2 ms."""
    info = connector.symbol_info(symbol)
    if not info:
        return {"spread_pct": 0.05, "atr_pct": 0.8, "mom_5m": 0.0, "rsi": 50.0, "volume_ratio": 1.0}

    mid = (info["bid"] + info["ask"]) / 2 or 1.0
    spread_pct = (info["ask"] - info["bid"]) / mid * 100 if mid else 0.05

    return {
        "spread_pct": spread_pct,
        "atr_pct": 0.8,
        "mom_5m": 0.0,
        "rsi": 50.0,
        "volume_ratio": 1.0,
        "bid": info["bid"],
        "ask": info["ask"],
    }


async def trading_loop(connector: MT5Connector, engine: DecisionEngine, memory: TradeMemory):
    symbols = list(ALL_SYMBOLS.keys())
    logger.info(f"Fast loop started | symbols={len(symbols)} | interval={LOOP_INTERVAL*1000:.0f}ms")

    while True:
        cycle_t0 = time.perf_counter()
        try:
            if STATE.get("paused"):
                await asyncio.sleep(0.5)
                continue

            if not connector.connected:
                ok = connector.connect()
                STATE["connected"] = ok
                if not ok:
                    await asyncio.sleep(2)
                    continue

            acct = connector.account()
            if acct:
                STATE["account"] = {
                    "login": acct.login,
                    "balance": acct.balance,
                    "equity": acct.equity,
                    "profit": acct.profit,
                    "currency": acct.currency,
                }

            positions = connector.positions()
            STATE["positions"] = positions
            STATE["memory_stats"] = memory.stats()

            daily_pnl_pct = 0.0
            if acct and acct.balance:
                daily_pnl_pct = (acct.profit / acct.balance) * 100

            for symbol in symbols:
                features = build_features(symbol, connector)
                info = connector.symbol_info(symbol)
                entry = (info["bid"] + info["ask"]) / 2 if info else 0.0

                intent = engine.evaluate(
                    symbol=symbol,
                    features=features,
                    entry_price=entry,
                    open_positions=positions,
                    daily_pnl_pct=daily_pnl_pct,
                )

                STATE.setdefault("last_decisions", []).append({
                    "symbol": intent.symbol,
                    "direction": intent.direction,
                    "confidence": intent.confidence,
                    "approved": intent.approved,
                    "goldman_reason": intent.goldman_reason,
                    "latency_ms": intent.latency_ms,
                    "ts": time.time(),
                })
                STATE["last_decisions"] = STATE["last_decisions"][-40:]

                if intent.approved and intent.direction in ("BUY", "SELL"):
                    logger.info(
                        f"ORDER {intent.direction} {intent.symbol} vol={intent.volume} "
                        f"conf={intent.confidence:.2f} [{intent.latency_ms:.1f}ms] {intent.goldman_reason}"
                    )
                    # Live orders OFF by default — uncomment when ready:
                    # result = connector.place_market_order(
                    #     symbol=intent.symbol,
                    #     direction=intent.direction,
                    #     volume=intent.volume,
                    #     sl=intent.sl,
                    #     tp=intent.tp,
                    # )

            STATE["updated_at"] = time.time()
            cycle_ms = (time.perf_counter() - cycle_t0) * 1000
            STATE["last_cycle_ms"] = cycle_ms

            # Sleep only the remaining time to hit LOOP_INTERVAL
            remaining = LOOP_INTERVAL - (cycle_ms / 1000)
            if remaining > 0.01:
                await asyncio.sleep(remaining)
            else:
                await asyncio.sleep(0.01)  # yield

        except Exception as e:
            logger.exception(f"Loop error: {e}")
            await asyncio.sleep(1)


def main():
    connector = MT5Connector(
        login=settings.mt5_login,
        password=settings.mt5_password,
        server=settings.mt5_server,
        path=settings.mt5_path,
    )
    engine = DecisionEngine(default_lot=settings.default_lot_size)
    memory = TradeMemory()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(trading_loop(connector, engine, memory))

    logger.info(f"Dashboard → http://{settings.dashboard_host}:{settings.dashboard_port}")
    uvicorn.run(app, host=settings.dashboard_host, port=settings.dashboard_port, log_level="warning")


if __name__ == "__main__":
    main()
