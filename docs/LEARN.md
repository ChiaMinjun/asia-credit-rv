# Study guide: own this project before the interview

Goal: in 2–3 weeks of evenings you can explain every number on the screen, defend a trade from
it, and say what's wrong with it. Interviewers care more about the last part than the code.

## Week 1 — the concepts

**OAS (option-adjusted spread).** Extra yield a bond pays over Treasuries, after stripping out the
value of embedded options (calls). The index OAS is the market-cap-weighted average across all
bonds in the index. Wider = cheaper credit / more risk priced in. You quote it in bp.

**Why compare regions (pairs).** Outright spreads move with global risk sentiment. Asia minus EM
removes much of that common move, leaving the Asia-specific story: China property, Fed
sensitivity of Asian IG, technicals (supply, Asian real-money demand). That's a *relative-value*
trade rather than a macro bet.

**z-score.** (today − 1y mean) / 1y standard deviation. z = +2 means unusually wide vs the past
year. It says *stretched*, not *wrong*. Something can stay at +2 for months.

**Percentile.** Where today sits in the full ~3-year history. Useful cross-check: z = +2 but 60th
percentile means the last year was unusually calm, not that today is extreme.

**Half-life.** Fit `daily change = a + b × yesterday's level`. If b is negative, the series pulls
back to its mean; half-life = −ln2 / ln(1+b) days. Short half-life = fast snap-back. Infinite =
no evidence it mean-reverts, so the z-score signal is weak.

**Curve trades.** 2s10s = 10y yield − 2y yield. **Steepener** profits if it rises (long 2y, short
10y, duration-weighted). **Flattener** the opposite. **Butterfly** 2×5y − 2y − 10y: positive
means the 5y belly yields more than the wings, i.e. the belly is cheap.

**Target and stop.** Target = back to the 1y mean. Stop = half the distance to target on the
other side (2:1 reward/risk), but never closer than 1.5× daily vol, or noise stops you out.

## Week 2 — the code (read in this order)

1. `acrv/universe.py` — what's screened, and the sign convention for pairs.
2. `acrv/data.py` — downloads FRED CSVs, converts percent → bp, builds pairs and curves.
3. `acrv/signals.py` — z, percentile, half-life, vol. ~50 lines. Know each formula.
4. `acrv/screen.py` — turns stats into flags and trade levels.
5. `acrv/journal.py` — P&L in bp, best/worst point, stop/target detection.
6. `tests/` — run `pytest -q`, then break a formula on purpose and watch a test fail.

Exercise: run `python -m acrv screen`, pick the most stretched line, and write three sentences
on *why* it might be stretched using news from that week. That's your first journal entry.

## Week 3 — trade it and prepare to defend it

Log 1–2 ideas a week with `python -m acrv open ...`. Write the thesis as you'd say it to a
trader: what, why now, what would make you wrong. Close trades honestly. A journal with some
losers and clear post-mortems reads better than a perfect one.

## Questions you will get (and how to answer)

**"Walk me through your project in 60 seconds."**
I screen Asia USD credit and the Treasury curve daily against their own history, flag anything
beyond 2σ, and check how fast it has historically mean-reverted. Ideas go into a public journal
marked to market, so my hit rate and mistakes are visible.

**"Your screen says Asia is cheap vs EM. Would you put it on?"**
Not on the number alone. First: why is it wide — fundamentals (a China property headline),
technicals (heavy supply), or composition change in the index? Then half-life and carry: am I
paid to wait? Then size off daily vol with a stop where I'm clearly wrong.

**"What's wrong with z-scores?"**
They assume the past year is the right reference and that spreads are stationary. After a
regime change (Fed pivot, default wave) the mean itself moves, and "cheap" keeps getting cheaper.
That's why I show half-life and percentile beside z.

**"How would you actually trade Asia vs EM?"**
On a desk: long a basket of Asia IG bonds vs short EM bonds or CDX EM, duration- and
DV01-matched. Index-level data is a proxy; I'd want bond-level spreads to pick names.

**"What would you add next?"**
Carry and roll-down (the P&L you earn if nothing moves), so a signal is judged net of what it
costs to hold. Then a backtest of the 2σ rule with transaction costs.

**"Why credit / why this desk?"**
Tie it to your seat at TP ICAP: you set up the bonds and CDS these desks trade, see the flow
daily, and built this to understand the pricing side of what you support.

## Things to be honest about

- The data is index-level and limited to ~3 years on FRED.
- No transaction costs or carry in P&L yet.
- The journal is paper trading.

Saying these before they're asked shows you understand the tool's limits.
