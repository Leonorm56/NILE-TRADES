"""
MetaTrader 5 connector for Deriv (and other standard MT5 brokers).
Requires Windows + running MT5 terminal with Algo Trading enabled.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None


@dataclass
class AccountSnapshot:
    login: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    profit: float
    currency: str


class MT5Connector:
    def __init__(
        self,
        login: int,
        password: str,
        server: str,
        path: Optional[str] = None,
        timeout: int = 60000,
    ):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.timeout = timeout
        self._connected = False

    def connect(self) -> bool:
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 package not installed or not on Windows")
            return False

        init_kwargs = {"login": self.login, "password": self.password, "server": self.server, "timeout": self.timeout}
        if self.path:
            init_kwargs["path"] = self.path

        if not mt5.initialize(**init_kwargs):
            err = mt5.last_error()
            logger.error(f"MT5 initialize failed: {err}")
            return False

        self._connected = True
        info = mt5.account_info()
        if info:
            logger.info(f"Connected to MT5 | login={info.login} balance={info.balance} {info.currency}")
        return True

    def disconnect(self):
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()
            self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def account(self) -> Optional[AccountSnapshot]:
        if not self._connected:
            return None
        info = mt5.account_info()
        if not info:
            return None
        return AccountSnapshot(
            login=info.login,
            balance=info.balance,
            equity=info.equity,
            margin=info.margin,
            free_margin=info.margin_free,
            profit=info.profit,
            currency=info.currency,
        )

    def positions(self) -> List[Dict[str, Any]]:
        if not self._connected:
            return []
        pos = mt5.positions_get()
        if pos is None:
            return []
        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "direction": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": p.volume,
                "price_open": p.price_open,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "magic": p.magic,
            }
            for p in pos
        ]

    def symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self._connected:
            return None
        info = mt5.symbol_info(symbol)
        if info is None:
            if not mt5.symbol_select(symbol, True):
                return None
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
        return {
            "symbol": info.name,
            "bid": info.bid,
            "ask": info.ask,
            "spread": info.spread,
            "digits": info.digits,
            "volume_min": info.volume_min,
            "volume_step": info.volume_step,
            "trade_mode": info.trade_mode,
        }

    def place_market_order(
        self,
        symbol: str,
        direction: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int = 20261006,
        comment: str = "NILE",
    ) -> Dict[str, Any]:
        if not self._connected:
            return {"ok": False, "error": "Not connected"}

        info = mt5.symbol_info(symbol)
        if info is None:
            return {"ok": False, "error": f"Symbol {symbol} not found"}

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"ok": False, "error": "No tick data"}

        order_type = mt5.ORDER_TYPE_BUY if direction.upper() == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if direction.upper() == "BUY" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None:
            return {"ok": False, "error": str(mt5.last_error())}

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {
                "ok": False,
                "error": f"retcode={result.retcode} comment={result.comment}",
                "retcode": result.retcode,
            }

        return {
            "ok": True,
            "ticket": result.order,
            "volume": result.volume,
            "price": result.price,
            "comment": result.comment,
        }

    def close_position(self, ticket: int) -> Dict[str, Any]:
        if not self._connected:
            return {"ok": False, "error": "Not connected"}
        pos_list = mt5.positions_get(ticket=ticket)
        if not pos_list:
            return {"ok": False, "error": "Position not found"}
        pos = pos_list[0]
        direction = "SELL" if pos.type == mt5.ORDER_TYPE_BUY else "BUY"
        return self.place_market_order(
            symbol=pos.symbol,
            direction=direction,
            volume=pos.volume,
            comment=f"close:{ticket}",
        )
