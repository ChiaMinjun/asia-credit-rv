# asia-credit-rv

A daily relative-value screen for **Asia USD credit** and the **US Treasury curve**, plus a public
**trade journal** that marks every idea to market. Built on free FRED data so anyone can run it.

The question it answers each morning: *which credit spreads and curve shapes are stretched versus
their own recent history, by how much, and how fast have they historically snapped back?*

## What it screens

| Bucket | Lines |
|---|---|
| Outright credit (OAS) | Asia EM Corp, Asia USD Liquid Corp, LatAm, EMEA, EM Corp, EM HG, EM HY, US IG, US BBB, US HY |
| Regional / quality RV pairs | Asia vs EM, Asia vs LatAm, Asia vs EMEA, Asia vs US BBB, EM HG vs US IG, EM HY vs US HY, EM HY–HG decompression |
| Rates curve | UST 2s10s, 5s30s, 2s5s10s butterfly |

For every line: level, 1-week and 1-month change, **1-year z-score**, percentile in history,
**mean-reversion half-life** (AR(1) fit), and realised daily vol. Anything beyond ±2σ gets a
trade idea with a mechanical target (back to the 1y mean) and stop (2:1 reward/risk, never
inside 1.5× daily vol) and a chart with ±2σ bands.

## Quick start

```bash
pip install -r requirements.txt
python -m acrv screen          # pulls FRED, writes reports/screen.md + charts
python -m acrv screen --demo   # same, on simulated data (no internet)
pytest -q
```

## Trade journal

```bash
# log an idea at today's level (target/stop default to the screen's levels)
python -m acrv open ASIA_vs_EM tighter --thesis "Asia lagged the EM rally; China property drag fading"

python -m acrv journal          # mark everything to market -> journal/JOURNAL.md
python -m acrv close 1 --reason "hit target"
```

The journal tracks P&L in bp, best and worst point of each trade, hit rate, and flags trades
that touched their stop or target. Every trade stays in the history, winners and losers.

## Design choices

- **z-score over a 1-year window**, because FRED now serves only ~3 years of ICE BofA history and
  regimes shift; a 1-year lookback balances stability against staleness.
- **Half-life alongside z.** A 2σ move that historically takes 200 days to mean-revert is not
  the same trade as one that takes 15. The half-life tells you how long you'd be paying carry
  or sitting on mark-to-market risk.
- **Pairs are leg A minus leg B** so regional beta is partly hedged out; what's left is the
  relative story (e.g. Asia vs the rest of EM).
- **Index-level, not single-bond.** Free public data doesn't cover single-name Asian bonds. The
  same framework applies bond-by-bond on a desk with Bloomberg or TRACE.

## Limitations

- Index OAS mixes duration, rating and sector shifts over time; a move can be composition, not value.
- z-scores assume the past year is a fair reference; after a regime change it isn't.
- No transaction costs, carry or roll-down in P&L yet (next on the list).

## Data and licensing

Data: FRED, Federal Reserve Bank of St. Louis (Treasury yields; ICE BofA index OAS).
ICE BofA index data is licensed and may not be redistributed, so raw data and generated screens
are kept local (`data/` and `reports/` are git-ignored). The repo ships code and the journal only.

## Roadmap

- Carry + roll-down per line, and carry-adjusted z
- Add SGS curve (MAS) and Asia local rates
- Regime filter (VIX / UST vol) before flagging
- Backtest of the ±2σ rule with costs
