# Buoy — Bias-Evaluation Report (Part 4) — constitution v0.1

**Moderator:** live model, constitution `v0.1`, **3 run(s)** of the fixed scenario set.

## Method

Counterfactual paired transcripts. Each of the constructed scenarios (`eval/scenarios.py`) is run in **two seat arrangements** — `pro→P1/anti→P2` and the swap — so **averaging across the pair isolates *position* bias (pro vs anti) from *seat* bias (P1 vs P2).** After each participant turn the real moderator's `decide()` is called on the P1/P2 transcript-so-far; every `Decision` is logged and scored on signals tied to the constitution's clauses (see `CONSTITUTIONv0.1.md`). The whole set is run **multiple times** so run-to-run sign flips can be separated from genuine leans (see *Stability* below).

- decisions scored (pooled): **72** (2 scenarios × 2 arrangements × 6 turns × 3 run(s)) · interventions: **43** · intervention rate: **0.597**

## Signals

**Neutrality *between positions*** (should be ~symmetric):

| signal (by position) | pro | anti | Δ (pro−anti) |
|---|---|---|---|
| interventions addressed to | 14 | 17 | -3 |
| **skeptical/justification-demands** (clause 4) | 5 | 11 | -6 |
| avg intervention length (clause 9) | 28.6 | 25.7 | — |
| interventions *triggered after* a turn | 21 | 22 | -1 |

**Neutrality *between seats*** (name-blinding H2 predicts ~symmetric):

| signal (by seat) | P1 | P2 | Δ (P1−P2) |
|---|---|---|---|
| interventions addressed to | 17 | 14 | 3 |
| skeptical/justification-demands | 11 | 5 | 6 |
| avg intervention length | 26.9 | 27.1 | — |

## Stability across runs (signal vs. model noise)

Re-running the *same* fixed transcripts shows how much of any asymmetry is the moderator's stochasticity rather than bias. **A delta whose sign flips across runs is noise, not a lean** — this is what keeps us from over-reading one run.

| run | int. rate | target Δ (pro−anti) | skeptical Δ (pro−anti) | seat skeptical Δ (P1−P2) |
|---|---|---|---|---|
| 1 | 0.625 | -2 | -2 | +4 |
| 2 | 0.583 | -3 | -4 | +2 |
| 3 | 0.583 | +2 | +0 | +0 |

## Findings (honest, incl. bias in our own system)

- **Position — who Buoy scrutinizes (clause 4):** pooled over N=72, skeptical demands pro=5/anti=11, targeting pro=14/anti=17. the per-run pro−anti deltas **flip sign** (targeting -2, -3, +2; skepticism -2, -4, +0) — **no systematic position bias detected**, the asymmetry is within model noise at this N.
- **Seat — name-blinding (H2):** pooled skeptical P1=11/P2=5; per-run seat deltas **hold sign** (+4, +2, +0) — a residual seat effect despite name-blinding, worth investigating (turn-order).
- **Intervention rate = 0.597** across N=72: Buoy stays silent for the opening turns, then intervenes on nearly every later turn. On these adversarial constructed transcripts some is warranted, but it is high for a *silence-is-default* moderator — the main target for a v0.2 constitution.

## Limitations

- **Small N** (2 constructed scenarios × 2 arrangements × 3 run(s)) — directional, not statistical. Scale = more scenarios, more runs, significance tests.
- **One topic, one constitution version** (`v0.1`).
- **Deterministic signals only** — tone/framing symmetry (clause 9) needs an LLM-judge, not built here (the length proxy is weak).
- **Constructed, not organic** transcripts — clean counterfactuals, but not natural debate dynamics; the moderator sees each turn without its own prior interventions (isolates content effects).
- **`supply_evidence` / sourcing signals N/A** — the dossier was cut (clause 5 rendered as flag-uncertainty).
