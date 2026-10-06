"""
Goldman Alpha Framework Rules
Extracted from Yogesh Malhotra (2018) guidance for a $400-500B Goldman Sachs alumnus hedge fund.

This module provides the hard filters that sit between the fast Jev decision
and the final order execution.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class LiquidityRegime(Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    STRESSED = "stressed"


class VolatilityRegime(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class TradeCandidate:
    symbol: str
    direction: str          # "BUY" or "SELL"
    confidence: float       # 0.0 - 1.0 from decision engine
    size_lots: float
    entry_price: float
    stop_loss: float
    take_profit: float
    is_synthetic: bool      # True for Boom/Crash
    extra: Dict[str, Any] = None


@dataclass
class GoldmanDecision:
    approved: bool
    reason: str
    adjusted_size: float
    liquidity_regime: Optional[LiquidityRegime] = None
    volatility_regime: Optional[VolatilityRegime] = None


# ============================================================
# Core Goldman Filters
# ============================================================

def alpha_quality_gate(candidate: TradeCandidate) -> tuple[bool, str]:
    """
    Criterion: Alpha + Plausibility
    Reject low-quality or ad-hoc signals.
    """
    if candidate.confidence < 0.62:
        return False, f"Alpha quality failed: confidence {candidate.confidence:.2f} < 0.62"
    return True, "Alpha quality passed"


def liquidity_microstructure_gate(
    candidate: TradeCandidate,
    spread_pct: float,
    atr_pct: float,
    recent_volume_ratio: float = 1.0
) -> tuple[bool, str, LiquidityRegime]:
    """
    Criterion: Liquidity + Price Impact awareness
    Only fully applied to real instruments.
    """
    if candidate.is_synthetic:
        # Synthetic instruments have no real order book → skip deep liquidity analysis
        return True, "Synthetic – liquidity gate skipped", LiquidityRegime.NORMAL

    # Simple regime classification
    if spread_pct > 0.08 or recent_volume_ratio < 0.4:
        regime = LiquidityRegime.STRESSED
    elif spread_pct > 0.04 or recent_volume_ratio < 0.7:
        regime = LiquidityRegime.LOW
    elif spread_pct < 0.015 and recent_volume_ratio > 1.2:
        regime = LiquidityRegime.HIGH
    else:
        regime = LiquidityRegime.NORMAL

    if regime == LiquidityRegime.STRESSED:
        return False, "Liquidity stressed – price impact risk too high", regime

    if regime == LiquidityRegime.LOW and candidate.size_lots > 0.5:
        return False, "Low liquidity – size too large for current conditions", regime

    return True, f"Liquidity regime: {regime.value}", regime


def crowding_and_capacity_check(candidate: TradeCandidate, open_positions: list) -> tuple[bool, str]:
    """
    Criterion: Market Crowding + Sector Capacity
    """
    same_direction_count = sum(
        1 for p in open_positions
        if p.get("direction") == candidate.direction
    )

    if same_direction_count >= 4:
        return False, f"Crowding risk: already {same_direction_count} positions in same direction"

    # Simple capacity: limit concurrent exposure on highly correlated groups
    index_symbols = {"US30", "US100", "US500", "GER40", "UK100"}
    if candidate.symbol in index_symbols:
        index_count = sum(1 for p in open_positions if p.get("symbol") in index_symbols)
        if index_count >= 3:
            return False, "Index capacity limit reached (max 3 concurrent index positions)"

    return True, "Crowding/capacity check passed"


def volatility_regime_adjust(
    candidate: TradeCandidate,
    atr_pct: float
) -> tuple[float, VolatilityRegime]:
    """
    Adapt size based on volatility regime (Goldman emphasis on Volatility).
    Returns adjusted size and regime.
    """
    if atr_pct > 2.5:
        regime = VolatilityRegime.EXTREME
        size_mult = 0.4
    elif atr_pct > 1.4:
        regime = VolatilityRegime.HIGH
        size_mult = 0.65
    elif atr_pct < 0.45:
        regime = VolatilityRegime.LOW
        size_mult = 1.15
    else:
        regime = VolatilityRegime.NORMAL
        size_mult = 1.0

    adjusted = round(candidate.size_lots * size_mult, 2)
    return max(0.01, adjusted), regime


def portfolio_risk_overlay(
    candidate: TradeCandidate,
    open_positions: list,
    daily_pnl_pct: float,
    max_daily_loss_pct: float = -3.0
) -> tuple[bool, str]:
    """
    Criterion: Portfolio Risk + Operational Risk
    """
    if daily_pnl_pct <= max_daily_loss_pct:
        return False, f"Daily loss limit hit ({daily_pnl_pct:.2f}%)"

    if len(open_positions) >= 6:
        return False, "Max concurrent positions (6) reached"

    return True, "Portfolio risk overlay passed"


# ============================================================
# Main Entry Point
# ============================================================

def apply_goldman_filters(
    candidate: TradeCandidate,
    spread_pct: float = 0.02,
    atr_pct: float = 0.8,
    recent_volume_ratio: float = 1.0,
    open_positions: list = None,
    daily_pnl_pct: float = 0.0
) -> GoldmanDecision:
    """
    Full Goldman filter chain.
    Returns a final go/no-go decision with adjusted size.
    """
    open_positions = open_positions or []

    # 1. Alpha quality
    ok, reason = alpha_quality_gate(candidate)
    if not ok:
        return GoldmanDecision(False, reason, 0.0)

    # 2. Liquidity / Microstructure
    ok, reason, liq_regime = liquidity_microstructure_gate(
        candidate, spread_pct, atr_pct, recent_volume_ratio
    )
    if not ok:
        return GoldmanDecision(False, reason, 0.0, liquidity_regime=liq_regime)

    # 3. Crowding & Capacity
    ok, reason = crowding_and_capacity_check(candidate, open_positions)
    if not ok:
        return GoldmanDecision(False, reason, 0.0, liquidity_regime=liq_regime)

    # 4. Portfolio risk
    ok, reason = portfolio_risk_overlay(candidate, open_positions, daily_pnl_pct)
    if not ok:
        return GoldmanDecision(False, reason, 0.0, liquidity_regime=liq_regime)

    # 5. Volatility regime size adjustment
    adjusted_size, vol_regime = volatility_regime_adjust(candidate, atr_pct)

    return GoldmanDecision(
        approved=True,
        reason="All Goldman filters passed",
        adjusted_size=adjusted_size,
        liquidity_regime=liq_regime,
        volatility_regime=vol_regime
    )
