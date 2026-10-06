# NILE-TRADES

**Fast self-contained trading agent** for Deriv MT5.

- **Goldman Alpha Framework** — institutional quality, liquidity, crowding, volatility, portfolio risk filters
- **Local fast signal** — pure Python, no external API (no Jev)
- **MetaTrader 5** connector (Deriv-ready)
- **Dashboard** for live monitoring
- Target cycle: **~150–250 ms** across 10 symbols

## Instruments

| Type | Symbols |
|------|---------|
| Metals | XAUUSD (Gold) |
| Crypto | BTCUSD |
| Indices | US30, US100, US500, GER40, UK100 |
| Synthetic 24/7 | Boom 500, Crash 500, Boom 1000 |

## Architecture

```
MT5 ticks
    ↓
Fast local signal   (momentum + RSI gate, <1 ms)
    ↓
Goldman Filters     (quality + liquidity + crowding + vol + portfolio)
    ↓
Order Intent        → MT5 execution (off by default)
    ↑
Trade Memory        (self-learning seed)
```

## Quick Start

```bash
git clone https://github.com/Leonorm56/NILE-TRADES.git
cd NILE-TRADES
pip install -r requirements.txt
cp .env.example .env
# Edit .env with Deriv MT5 login / password / server
python main.py
```

Open http://localhost:8000

## Speed

| Part | Typical |
|------|---------|
| Signal + Goldman (per symbol) | < 2 ms |
| Full cycle (10 symbols) | ~50–150 ms work |
| Loop interval | 200 ms (configurable in `main.py`) |

No external model or API call in the hot path.

## Project Structure

```
NILE-TRADES/
├── goldman/       # Institutional filters
├── mt5/           # Deriv MT5 connector
├── engine/        # Fast signal + decision
├── memory/        # Trade outcome memory
├── dashboard/     # FastAPI UI
├── config/
└── main.py
```

## License

MIT

## Disclaimer

Trading involves substantial risk of loss. Educational / research use. Use at your own risk.
