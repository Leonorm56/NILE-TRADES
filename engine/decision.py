"""
Core decision loop: Local fast signal → Goldman filters → final order intent.
No external Jev dependency. Designed for sub-second cycles.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from goldman import TradeCandidate, apply_goldman_filters, GoldmanDecision
from mt5.symbols import is_synthetic

logger = logging.getLogger(__name__)


@dataclass
class OrderIntent:
    symbol: str
    direction: str
    volume: float
    sl: float
    tp: float
    confidence: float
    goldman_reason: str
    latency_ms: float
    approved: bool


def fast_signal(features: Dict[str, float]) -> tuple[str, float]:
    """
    Ultra-light local signal. Pure Python, no network, no model call.
    Returns (action, confidence).

    Expand later with real indicators; keep this path under ~1 ms.
    """
    spread = features.get("spread_pct", 0.05)
    mom = features.get("mom_5m", 0.0)
    rsi = features.get("rsi", 50.0)

    # Wide spread → no trade
    if spread > 0.12:
        return "HOLD", 0.25

    # Simple momentum + RSI gate
    if mom > 0.12 and rsi < 68:
        conf = min(0.92, 0.58 + abs(mom) * 0.9)
        return "BUY", conf
    if mom < -0.12 and rsi > 32:
        conf = min(0.92, 0.58 + abs(mom) * 0.9)
        return "SELL", conf

    return "HOLD", 0.35


class DecisionEngine:
    def __init__(self, default_lot: float = 0.01):
        self.default_lot = default_lot

    def evaluate(
        self,
        symbol: str,
        features: Dict[str, float],
        entry_price: float,
        open_positions: List[Dict[str, Any]],
        daily_pnl_pct: float = 0.0,
        proposed_sl: float = 0.0,
        proposed_tp: float = 0.0,
    ) -> OrderIntent:
        t0 = time.perf_counter()

        action, confidence = fast_signal(features)

        if action == "HOLD":
            return OrderIntent(
                symbol=symbol,
                direction="HOLD",
                volume=0.0,
                sl=0.0,
                tp=0.0,
                confidence=confidence,
                goldman_reason="Signal HOLD",
                latency_ms=(time.perf_counter() - t0) * 1000,
                approved=False,
            )

        candidate = TradeCandidate(
            symbol=symbol,
            direction=action,
            confidence=confidence,
            size_lots=self.default_lot,
            entry_price=entry_price,
            stop_loss=proposed_sl,
            take_profit=proposed_tp,
            is_synthetic=is_synthetic(symbol),
        )

        goldman: GoldmanDecision = apply_goldman_filters(
            candidate=candidate,
            spread_pct=features.get("spread_pct", 0.02),
            atr_pct=features.get("atr_pct", 0.8),
            recent_volume_ratio=features.get("volume_ratio", 1.0),
            open_positions=open_positions,
            daily_pnl_pct=daily_pnl_pct,
        )

        latency = (time.perf_counter() - t0) * 1000

        if not goldman.approved:
            return OrderIntent(
                symbol=symbol,
                direction=action,
                volume=0.0,
                sl=proposed_sl,
                tp=proposed_tp,
                confidence=confidence,
                goldman_reason=goldman.reason,
                latency_ms=latency,
                approved=False,
            )

        return OrderIntent(
            symbol=symbol,
            direction=action,
            volume=goldman.adjusted_size,
            sl=proposed_sl,
            tp=proposed_tp,
            confidence=confidence,
            goldman_reason=goldman.reason,
            latency_ms=latency,
            approved=True,
        )
