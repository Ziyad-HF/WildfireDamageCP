# Preregistration: WildfireDamageCP (CIV E 779)

Frozen before any model training or evaluation. Changes need Ziyad's approval and must be logged
(date, old text, new text, reason) in the "Amendments" section below and in the runbook Results log.
Source: project analysis plan, Section 5, copied verbatim on 2026-11-09.

## Rules (verbatim from runbook Section 5)

1. **Classes:** 0 no damage, 1 damaged, 2 destroyed (mapping in the project page, Section 6.3).
2. **Exclusions:** the 138 xBD buildings with bx or by outside 0–223.
3. **Folds:** fold k tests on one fire: 1 Santa Rosa, 2 Woolsey (socal-fire + woolsey-fire), 3 Pinery, 4 Portugal. The other three fires are split into train 70% / val 10% / calib 20% by **spatial grid cell** (0.005° × 0.005°, about 500 m, from lon/lat), seed 0, so neighbouring houses and the two Woolsey image sets never fall in different roles. Every fold also scores all Eaton buildings (role eaton).
4. **Data use:** model selection and early stopping on val only; temperature and conformal thresholds on calib only; test fire and Eaton are evaluated once per final model.
5. **Marker:** draw the same red circle (radius 9 px, width 2 px) at (bx, by) on both crops for T1, T2 and T3.
6. **Metrics:** macro-F1 (primary accuracy), per-class F1; ECE with 15 equal-width bins on the top-class probability; multi-class Brier score; conformal coverage (overall and per class) and mean set size.
7. **Conformal:** α = 0.10; scores LAC and APS; ordinal-contiguous sets; class-conditional (Mondrian) variant; split conformal on the calib role.
8. **Routing rule:** auto-label a building only if its set has one class. Missed-destroyed rate = truly destroyed buildings auto-labelled as non-destroyed ÷ all truly destroyed buildings. Choose α on calib as the largest value whose missed-destroyed rate ≤ 5%; apply unchanged to test and Eaton; report the auto-labelled share.
9. **Uncertainty:** 95% CIs by cluster bootstrap over grid cells within each test fire (1,000 resamples); Eaton: mean ± SD across the 4 fold models.
10. **Seeds and hardware:** T1 and T3 with seeds 0, 1, 2; T2 deterministic. All runs of one model level on the same GPU type (H200 first).
11. **Honesty:** report every fold and every model, including failures; no result is dropped after seeing test numbers.

## Implementation details (not rule changes; fixed before training; flagged to Ziyad for review)

These specify points the rules leave open. Code: `src/make_splits.py`, checks: `src/check_splits.py`.

- **D1 Grid cell:** cell = (floor(lon / 0.005), floor(lat / 0.005)) on WGS84 lon/lat from `data/metadata/buildings_xbd.csv`. Checked: no cell contains buildings of two fire groups. socal-fire and woolsey-fire buildings share cells, as intended.
- **D2 Role assignment:** done **once per fire group** with seed 0 and reused in every fold where that fire is a training fire (a building's train/val/calib role is the same in all folds). Within a fire: cells shuffled with `numpy.random.default_rng(0).permutation`; cells assigned in that order to train while the share of the fire's buildings already assigned is < 70%, then val while < 80%, else calib. The 70/10/20 targets are therefore building shares, met up to whole-cell granularity (realised: train 70.1–71.0%, val 9.2–11.7%, calib 18.2–19.9% per fire). Not stratified by class.
- **D3 Exclusions:** the 138 buildings (Woolsey 129, Pinery 9) are removed from every role, including test.
- **D4 Grid cells for the bootstrap (rule 9):** the same D1 cells, stored in `data/processed/splits/cells_xbd.csv`.
- **D5 T2/T3 model:** Qwen/Qwen3-VL-8B-Instruct (Ziyad's choice, 2026-11-09).
- **D6 Software:** Python virtual environment `venv_wdcp` (versions in `configs/env_versions.txt`); every job sources `slurm/env.sh`.

Timing note (for transparency): the split files were generated in the same session, immediately before this
file was committed, with the D1–D3 procedure written beforehand and run once. No model had been trained or
evaluated, and no test-fire or Eaton predictions existed.

### Phase 5 implementation details (added 2026-11-10, before any Phase 5 computation; flagged to Ziyad for review)

- **D7 Temperature scaling:** one temperature T per model × fold × seed, minimising mean NLL on the calib role over log T in [-3, 3] (bounded scalar search). Applied to every role.
- **D8 Conformal input:** conformal sets use the temperature-scaled probabilities. T and the conformal thresholds are both fitted on the same calib role (rule 4); T is a single parameter, so this dependence is small but is noted as a limitation.
- **D9 Scores and sets (K = 3 classes):** LAC s = 1 − p_y. APS (non-randomised, U = 0): s = total probability of the classes ranked strictly above y (Σ_{j: p_j > p_y} p_j, ties counted as above except y itself). Ordinal-contiguous: nested intervals grown from the argmax class by adding the neighbouring class with the higher probability (ties → lower class); s = probability mass of the intervals before the first one that contains y. Class-conditional (Mondrian) uses the LAC score with one threshold per true class. Threshold q̂ = the ⌈(n+1)(1−α)⌉-th smallest calib score (q̂ = ∞ if that index exceeds n). Set C(x) = {y : s(x, y) ≤ q̂}, the same score for thresholds and sets. APS and Ordinal sets always contain the top class (score 0); LAC and Mondrian sets can be empty (reported; count as "not auto-labelled"). *Revision note (2026-11-10, before any test/Eaton computation):* the first draft used the inclusive APS score (mass up to and including y), which gave ~4% empty sets in a calib-only half-split test; a second draft mixed inclusive thresholds with exclusive sets, giving near-full sets (mean size 2.8). Both were replaced by this consistent exclusive score.
- **D10 Routing (rule 8):** α grid 0.005 to 0.500, step 0.005. The calib missed-destroyed rate at each α uses thresholds fitted on all of calib (in-sample). α* = largest grid value with calib rate ≤ 0.05; if none qualifies, every building is routed. Done separately for each of the 4 conformal methods. All 4 are reported; none is chosen using test or Eaton results. If one headline method is needed, it is the method with the largest calib auto-labelled share at its α*.
- **D11 Metric details:** ECE: 15 equal-width bins on [0, 1] over the top-class probability, |accuracy − mean confidence| weighted by bin share. Brier: mean over buildings of Σ_c (p_c − 1[y = c])² (range 0–2). Coverage: share of buildings with y ∈ C(x), overall and per true class. Set size: mean |C(x)|, empty sets included as 0.
- **D12 Bootstrap (rule 9):** resample the test fire's grid cells (cells_xbd.csv) with replacement, 1,000 resamples, numpy seed 0, percentile 2.5–97.5%. Model, T and thresholds are held fixed. For T1 the metric is averaged over the 3 seeds within each resample (seed SD reported separately). Eaton: mean ± SD across the 4 fold models (T1 seed-averaged first); no bootstrap.
- **D13 Secondary destroyed-vs-not:** binary probabilities from the temperature-scaled 3-class output (p_des vs 1 − p_des); LAC and Mondrian-LAC sets; same routing rule (missed-destroyed ≤ 5% on calib).
- **D14 Reliability diagrams:** 15 bins, T1 seeds pooled, before and after temperature scaling, per test fire and Eaton.

## Amendments

### A1 (2026-11-10): rule 8 α selection. Approved by Ziyad on 2026-11-10.
- **Old text (rule 8):** "Choose α on calib as the largest value whose missed-destroyed rate ≤ 5%; apply unchanged to test and Eaton; report the auto-labelled share."
- **New text:** "Choose α on calib as the grid value (D10 grid) that maximises the calib auto-labelled share subject to calib missed-destroyed rate ≤ 5% (ties → larger α); if none qualifies, route every building. Apply unchanged to test and Eaton; report the auto-labelled share."
- **Reason:** with LAC (and the binary destroyed-vs-not analysis), larger α gives more empty sets and fewer auto-labels, so the missed-destroyed rate keeps falling and "largest α" always hit the grid edge (0.500, calib auto share ≈ 0.50), contrary to the rule's intent (RQ3: the largest auto-labelled share at ≤ 5% missed destroyed).
- **Disclosure:** this amendment was proposed **after** the test-fire and Eaton results under the original rule had been computed and seen (commit b31eafa). The selection still uses calib only. Results under the original rule are kept and reported alongside (results/tables/p5_routing.csv, p5_routing_binary.csv); amended results are in p5_routing_amended.csv, p5_routing_binary_amended.csv.

### P1 (2026-11-10): post-hoc analysis, randomised APS and Ordinal. Approved by Ziyad on 2026-11-10. **Not preregistered.**
- **Why:** with the preregistered D9 scores, T1 APS/Ordinal sets at α = 0.10 are degenerate (q̂ = 0 in all 12 T1 runs because calib top-1 accuracy 0.937–0.963 > 0.90, so every set = the top-1 class). Found after the test results were computed.
- **Method:** score s(x, y) = (mass ranked strictly above y, as in D9) + U · p_y, with U ~ Uniform(0, 1) drawn once per building (numpy default_rng(0), file row order, per run) and shared by all labels of that building; threshold and sets as in D9 (C = {y : s ≤ q̂}; sets can be empty when U · p_top > q̂). Named "APS_rand" and "Ordinal_rand". Routing under both the original rule 8 and A1. Always labelled post-hoc in tables and the report; the preregistered D9 results are reported too.

## Added analyses (after the main results)

### E1 (2026-11-11): few-shot recalibration on the target fire. Approved by Ziyad on 2026-11-11. **Added after all Phase 5–7 test-fire and Eaton results had been computed and seen; not preregistered.**
- **Question:** if inspectors label a small first batch of houses on the new fire, does fitting T and the conformal thresholds on that batch (instead of on other fires' calib) restore coverage and the ≤ 5% missed-destroyed target on the rest of that fire?
- **Targets:** each fold's test fire (role test) and Eaton (role eaton, scored by each fold model). Models T1 and T3 (all folds × seeds) are the main result; T2 is computed and reported as secondary.
- **Sample sizes:** n ∈ {100, 200, 300} buildings; 20 repeats r = 0..19.
- **Sampling B (main, spatial):** the target's D1 grid cells (xBD: cells_xbd.csv; Eaton: floor(lon/0.005), floor(lat/0.005) from buildings_eaton.csv) shuffled with numpy default_rng(seed), whole cells added in that order until the sample has ≥ n buildings (realised size reported). **Sampling A (check):** n buildings drawn uniformly without replacement with default_rng(seed). seed = 100000·scheme(A=1, B=2) + 1000·n + r, independent of model/fold/seed, so all models see the same samples of a given target (paired comparison; Eaton samples identical across the 4 fold models).
- **Recalibration:** T fitted on the sample (D7 procedure); conformal thresholds at α = 0.10 fitted on the sample (D9); routing α chosen on the sample by rule 8 (original) and by A1 (both reported). Methods: LAC, APS, Mondrian (D9) and APS_rand (P1, post-hoc, same U as Phase 5). If a Mondrian class is absent or too rare in the sample, its threshold is ∞ (class always included), per D9.
- **Evaluation:** on the remaining buildings of the same target (target minus sample). **Baseline:** the existing Phase 5 T, thresholds and α* (fitted on other fires' calib) evaluated on the same remaining buildings.
- **Metrics:** coverage overall and per class, mean set size, empty share, ECE after scaling, routing auto share and missed-destroyed rate, number of destroyed houses in the sample.
- **Summary:** per tier × target × method × n × scheme: T1/T3 seed-averaged within each repeat, then mean and 10th–90th percentile over the 20 repeats; plus the share of repeats with remaining-set missed-destroyed ≤ 5%. Eaton additionally averaged over the 4 fold models within each repeat.
- **Limits stated in advance:** labels in the sample are the dataset labels (assumes inspector labels equal ground truth); no new model training; nothing is tuned on the evaluation buildings.
- **Code / outputs:** src/e1_recalibration.py; results/tables/e1_raw/*.csv (per file), results/tables/e1_summary.csv; outputs/figures/fig6_recalibration.
