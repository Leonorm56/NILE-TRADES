"""
Core decision loop: Jev (speed) → Goldman filters → final order intent.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from jev import JevClient, JevDecision
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
    jev_latency_ms: float
    approved: bool


class DecisionEngine:
    def __init__(self, jev: JevClient, default_lot: float = 0.01):
        self.jev = jev
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
        # 1. Fast decision
        jev_out: JevDecision = self.jev.decide(symbol, features)

        if jev_out.action == "HOLD":
            return OrderIntent(
                symbol=symbol,
                direction="HOLD",
                volume=0.0,
                sl=0.0,
                tp=0.0,
                confidence=jev_out.confidence,
                goldman_reason="Jev HOLD",
                jev_latency_ms=jev_out.latency_ms,
                approved=False,
            )

        # 2. Build candidate for Goldman
        candidate = TradeCandidate(
            symbol=symbol,
            direction=jev_out.action,
            confidence=jev_out.confidence,
            size_lots=self.default_lot,
            entry_price=entry_price,
            stop_loss=proposed_sl,
            take_profit=proposed_tp,
            is_synthetic=is_synthetic(symbol),
        )

        # 3. Goldman institutional filters
        goldman: GoldmanDecision = apply_goldman_filters(
            candidate=candidate,
            spread_pct=features.get("spread_pct", 0.02),
            atr_pct=features.get("atr_pct", 0.8),
            recent_volume_ratio=features.get("volume_ratio", 1.0),
            open_positions=open_positions,
            daily_pnl_pct=daily_pnl_pct,
        )

        if not goldman.approved:
            logger.info(f"Goldman rejected {symbol} {jev_out.action}: {goldman.reason}")
            return OrderIntent(
                symbol=symbol,
                direction=jev_out.action,
                volume=0.0,
                sl=proposed_sl,
                tp=proposed_tp,
                confidence=jev_out.confidence,
                goldman_reason=goldman.reason,
                jev_latency_ms=jev_out.latency_ms,
                approved=False,
            )

        return OrderIntent(
            symbol=symbol,
            direction=jev_out.action,
            volume=goldman.adjusted_size,
            sl=proposed_sl,
            tp=proposed_tp,
            confidence=jev_out.confidence,
            goldman_reason=goldman.reason,
            jev_latency_ms=jev_out.latency_ms,
            approved=True,
        )
