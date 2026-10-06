"""
NILE-TRADES entry point.
Starts the decision loop + FastAPI dashboard.
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
from mt5 import MT5Connector, ALL_SYMBOLS, is_synthetic
from jev import JevClient
from engine import DecisionEngine
from memory.trade_memory import TradeMemory
from dashboard.app import app, STATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nile")


def build_features(symbol: str, connector: MT5Connector) -> Dict[str, float]:
    """Minimal feature set for Jev + Goldman. Expand later."""
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
    logger.info(f"Trading loop started | symbols={symbols}")

    while True:
        try:
            if STATE.get("paused"):
                await asyncio.sleep(1)
                continue

            if not connector.connected:
                ok = connector.connect()
                STATE["connected"] = ok
                if not ok:
                    await asyncio.sleep(5)
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
            STATE["updated_at"] = time.time()

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
                    "jev_latency_ms": intent.jev_latency_ms,
                    "ts": time.time(),
                })
                STATE["last_decisions"] = STATE["last_decisions"][-50:]

                if intent.approved and intent.direction in ("BUY", "SELL"):
                    logger.info(
                        f"ORDER {intent.direction} {intent.symbol} vol={intent.volume} "
                        f"conf={intent.confidence:.2f} goldman={intent.goldman_reason}"
                    )
                    # Uncomment to enable live orders:
                    # result = connector.place_market_order(
                    #     symbol=intent.symbol,
                    #     direction=intent.direction,
                    #     volume=intent.volume,
                    #     sl=intent.sl,
                    #     tp=intent.tp,
                    # )
                    # logger.info(f"Order result: {result}")

            await asyncio.sleep(3)

        except Exception as e:
            logger.exception(f"Loop error: {e}")
            await asyncio.sleep(5)


def main():
    connector = MT5Connector(
        login=settings.mt5_login,
        password=settings.mt5_password,
        server=settings.mt5_server,
        path=settings.mt5_path,
    )
    jev = JevClient(api_key=settings.jev_api_key, endpoint=settings.jev_endpoint)
    engine = DecisionEngine(jev=jev, default_lot=settings.default_lot_size)
    memory = TradeMemory()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(trading_loop(connector, engine, memory))

    logger.info(f"Dashboard \u2192 http://{settings.dashboard_host}:{settings.dashboard_port}")
    uvicorn.run(app, host=settings.dashboard_host, port=settings.dashboard_port, log_level="info")


if __name__ == "__main__":
    main()
