"""
Simple trade outcome memory – seed for self-learning.
Stores closed trades and basic statistics that can later feed prompt evolution or fine-tuning.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TradeRecord:
    ticket: int
    symbol: str
    direction: str
    volume: float
    entry_price: float
    exit_price: float
    profit: float
    open_time: float
    close_time: float
    goldman_reason: str
    jev_confidence: float
    notes: str = ""


class TradeMemory:
    def __init__(self, path: str = "data/trade_memory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: List[TradeRecord] = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.records = [TradeRecord(**r) for r in data]
            except Exception:
                self.records = []

    def _save(self):
        self.path.write_text(json.dumps([asdict(r) for r in self.records], indent=2))

    def add(self, record: TradeRecord):
        self.records.append(record)
        self._save()

    def stats(self) -> Dict[str, Any]:
        if not self.records:
            return {"trades": 0, "win_rate": 0.0, "avg_profit": 0.0, "total_profit": 0.0}
        wins = sum(1 for r in self.records if r.profit > 0)
        total = sum(r.profit for r in self.records)
        return {
            "trades": len(self.records),
            "win_rate": wins / len(self.records),
            "avg_profit": total / len(self.records),
            "total_profit": total,
        }

    def recent(self, n: int = 20) -> List[TradeRecord]:
        return self.records[-n:]
