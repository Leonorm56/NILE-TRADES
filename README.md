# NILE-TRADES

**Self-learning trading agent** built with:

- **Goldman Alpha Framework** (institutional quality + liquidity + crowding + volatility + portfolio risk filters)
- **MetaTrader 5** connection (Deriv-ready)
- **Jev speed layer** (fast BUY / SELL / HOLD decisions)
- **Dashboard** for live monitoring
- Designed for continuous 24/7 operation

## Instruments

| Type | Symbols |
|------|---------|
| Metals | XAUUSD (Gold) |
| Crypto | BTCUSD |
| Indices | US30, US100, US500, GER40, UK100 |
| Synthetic 24/7 | Boom 500, Crash 500, Boom 1000 |

## Architecture

```
Jev (speed) → Goldman Filters → Risk Overlay → MT5 Execution
                     ↑
              Trade Memory (self-learning seed)
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Leonorm56/NILE-TRADES.git
cd NILE-TRADES

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your Deriv MT5 login, password, server

# 4. Run dashboard + engine
python main.py
```

Open http://localhost:8000 for the dashboard.

## Project Structure

```
NILE-TRADES/
├── goldman/          # Institutional alpha filters
├── mt5/              # MetaTrader 5 connector (Deriv)
├── jev/              # Fast decision speed layer
├── engine/           # Decision + risk orchestration
├── memory/           # Trade outcome memory (self-learning seed)
├── dashboard/        # FastAPI web UI
├── config/           # Settings
└── main.py           # Entry point
```

## Goldman Layer

Based on Yogesh Malhotra (2018) guidance for a Goldman Sachs alumnus hedge fund ($400–500B AUM):

1. Alpha Quality Gate
2. Liquidity & Microstructure Gate
3. Crowding & Capacity Check
4. Volatility Regime size adjustment
5. Portfolio Risk Overlay

Full details in `goldman/framework.md`.

## License

MIT

## Disclaimer

Trading involves substantial risk of loss. This software is for educational and research purposes. Past performance is not indicative of future results. Use at your own risk.
