# Goldman Sachs Alumnus Hedge Fund Alpha Framework
**Source:** Yogesh Malhotra (2018)  
**Title:** Guidance to a Goldman Sachs alumnus Hedge Fund with $400 Billion–$500 Billion AUM:  
Alpha Trading Strategies Analysis, Maximizing Alpha for Hedge Funds, and High Frequency Econometrics for Analyzing Price Impact of Trades, Liquidity, and Market Microstructure  

**DOI:** 10.2139/ssrn.3306817  
**Length:** 8 pages  

---

## 1. Origin of the Framework

This report came from a real engagement with a Goldman Sachs alumnus hedge fund that managed approximately **$400–500 billion AUM** at the time.

The core problem identified:
> Liquidity and Volatility became the overriding structural drivers of alpha in the post-Financial Crisis period. Traditional alpha research was no longer sufficient.

The study combined three workstreams:
1. Analysis of ~400 trading strategies (primarily from State Street Associates *SSA Quarterly*)
2. Post-crisis strategies for maximizing hedge fund alpha
3. High-frequency econometrics focused on price impact, liquidity, and market microstructure

---

## 2. Strategy Selection Criteria (from the 400-strategy scan)

| Criterion              | Description |
|------------------------|-------------|
| **Alpha**              | Expected excess return after realistic costs |
| **Plausibility**       | Economic and statistical credibility of the edge |
| **Technical Profile**  | How the strategy is constructed and executed |
| **Operational Risk**   | Implementation difficulty and operational fragility |
| **Portfolio Risk**     | Contribution to overall portfolio risk |
| **Market Crowding**    | How many other managers are already in the same trade |
| **Sector Capacity**    | How much capital the opportunity can absorb |
| **Alternative Investments** | Fit within broader alt portfolio construction |

---

## 3. Post-Crisis Alpha Maximization Principles

After the 2008 crisis, the dominant structural factors became:

- **Liquidity** (availability and cost of liquidity)
- **Volatility** (regime changes and volatility of volatility)
- **Market Microstructure** (how prices are actually formed)

---

## 4. Practical Rules Encoded in NILE-TRADES

1. **Alpha Quality Gate** – reject low-confidence signals
2. **Liquidity & Microstructure Gate** – full on real instruments, relaxed on Boom/Crash
3. **Crowding & Capacity Check**
4. **Volatility Regime size adjustment**
5. **Portfolio Risk Overlay** (daily loss + max positions)

See `goldman/rules.py` for the implementation.
