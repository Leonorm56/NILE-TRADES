"""
Jev speed layer – ultra-fast typed decisions (target 70–500 ms).

If JEV_API_KEY / JEV_ENDPOINT are set, calls the real service.
Otherwise uses a lightweight local mock that returns BUY / SELL / HOLD
based on simple momentum so the rest of the system can be developed.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class JevDecision:
    action: str          # BUY | SELL | HOLD
    confidence: float    # 0.0 – 1.0
    latency_ms: float
    raw: Optional[Dict[str, Any]] = None


class JevClient:
    def __init__(self, api_key: str = "", endpoint: str = ""):
        self.api_key = api_key or os.getenv("JEV_API_KEY", "")
        self.endpoint = endpoint or os.getenv("JEV_ENDPOINT", "")
        self.use_real = bool(self.api_key and self.endpoint)

    def decide(self, symbol: str, features: Dict[str, float]) -> JevDecision:
        """
        features expected keys (examples):
          bid, ask, spread_pct, atr_pct, mom_1m, mom_5m, rsi, volume_ratio
        """
        t0 = time.perf_counter()

        if self.use_real:
            decision = self._call_real(symbol, features)
        else:
            decision = self._mock(symbol, features)

        latency = (time.perf_counter() - t0) * 1000
        decision.latency_ms = latency
        return decision

    def _mock(self, symbol: str, features: Dict[str, float]) -> JevDecision:
        """
        Deterministic mock for development.
        Simple momentum + RSI style logic.
        """
        mom = features.get("mom_5m", 0.0)
        rsi = features.get("rsi", 50.0)
        spread = features.get("spread_pct", 0.02)

        if spread > 0.12:
            return JevDecision("HOLD", 0.3, 0.0)

        if mom > 0.15 and rsi < 70:
            conf = min(0.95, 0.55 + abs(mom) * 0.8)
            return JevDecision("BUY", conf, 0.0)
        if mom < -0.15 and rsi > 30:
            conf = min(0.95, 0.55 + abs(mom) * 0.8)
            return JevDecision("SELL", conf, 0.0)

        return JevDecision("HOLD", 0.4, 0.0)

    def _call_real(self, symbol: str, features: Dict[str, float]) -> JevDecision:
        """
        Placeholder for real Jev / System One HTTP call.
        Replace with the actual typed API once credentials are available.
        """
        try:
            import httpx
            payload = {"symbol": symbol, "features": features}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            with httpx.Client(timeout=0.8) as client:
                r = client.post(self.endpoint, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
            action = data.get("action", "HOLD").upper()
            conf = float(data.get("confidence", 0.5))
            return JevDecision(action, conf, 0.0, raw=data)
        except Exception as e:
            logger.warning(f"Jev real call failed, falling back to mock: {e}")
            return self._mock(symbol, features)
