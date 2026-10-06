"""
Canonical symbol list for NILE-TRADES on Deriv MT5.
Exact names can vary slightly by account type – adjust after checking Market Watch.
"""

REAL_INSTRUMENTS = {
    "XAUUSD": {"name": "Gold", "synthetic": False},
    "BTCUSD": {"name": "Bitcoin", "synthetic": False},
    "US30": {"name": "Wall Street 30", "synthetic": False},
    "US100": {"name": "US Tech 100", "synthetic": False},
    "US500": {"name": "US SP 500", "synthetic": False},
    "GER40": {"name": "Germany 40", "synthetic": False},
    "UK100": {"name": "UK 100", "synthetic": False},
}

SYNTHETIC_INSTRUMENTS = {
    "Boom 500": {"name": "Boom 500 Index", "synthetic": True},
    "Crash 500": {"name": "Crash 500 Index", "synthetic": True},
    "Boom 1000": {"name": "Boom 1000 Index", "synthetic": True},
}

ALL_SYMBOLS = {**REAL_INSTRUMENTS, **SYNTHETIC_INSTRUMENTS}

# Common Deriv MT5 aliases (update after login)
SYMBOL_ALIASES = {
    "US30": ["US30", "Wall Street 30", "US_30", ".US30Cash"],
    "US100": ["US100", "US Tech 100", "US_100", ".NAS100Cash"],
    "US500": ["US500", "US SP 500", "US_500", ".SPX500Cash"],
    "GER40": ["GER40", "Germany 40", "DE40", ".GER40Cash"],
    "UK100": ["UK100", "UK 100", ".UK100Cash"],
    "XAUUSD": ["XAUUSD", "GOLD"],
    "BTCUSD": ["BTCUSD", "BTCUSD.a"],
    "Boom 500": ["Boom 500 Index", "Boom500"],
    "Crash 500": ["Crash 500 Index", "Crash500"],
    "Boom 1000": ["Boom 1000 Index", "Boom1000"],
}


def is_synthetic(symbol: str) -> bool:
    return ALL_SYMBOLS.get(symbol, {}).get("synthetic", False) or any(
        s in symbol for s in ("Boom", "Crash")
    )
