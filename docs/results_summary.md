# Results summary (Phase 7, 2026-11-10)

Generated from results/tables/report_tables.md (src/phase7_tables.py) and outputs/figures/ (src/phase7_figs.py).
Leave-one-fire-out on 4 xBD wildfires, plus the 2025 Eaton Fire (CAL FIRE DINS labels) scored by every fold model.
Test values: mean ± SD over seeds with 95% cluster-bootstrap CIs. Eaton values: mean ± SD across the 4 fold models.

## Main findings
1. **Accuracy (Table 2).** The fine-tuned VLM (T3) is about as accurate as the CNN (T1). Both are far better than the VLM used as-is (T2).
   - Test macro-F1, T1 / T3: Santa Rosa 0.669 / 0.667, Woolsey 0.638 / 0.637, Pinery 0.578 / 0.571, Portugal 0.534 / 0.519.
   - T2: 0.31–0.40 on test.
   - Eaton macro-F1: T1 0.683 ± 0.026, T3 0.693 ± 0.026, T2 0.426.
   - The "damaged" class is barely learned: F1 ≤ 0.22 for every model and fire.
   - Accuracy falls on the fires least like the training fires (Pinery, Portugal), mainly through destroyed F1 of about 0.46–0.56.
2. **Calibration (Table 3, Fig 1).**
   - T1 and T3 are close to calibrated already. After temperature scaling (fitted on calib), test ECE is 0.010–0.032.
   - T2 is strongly overconfident (T = 6.8–11.9). Its ECE stays at 0.07–0.23 after scaling, because one temperature cannot fix its miscalibration.
3. **Conformal sets at α = 0.10 (Table 4, Fig 2).** The 90% coverage guarantee assumes calib and test are exchangeable. It does not hold when the test fire is a new fire.
   - Mondrian coverage of destroyed homes is 0.97 on Santa Rosa for all models. On Portugal it falls to 0.24 (T1), 0.30 (T3) and 0.40 (T2).
   - On Eaton, coverage is close to nominal: T3 0.917 overall and 0.974 for destroyed; T1 0.878 overall and 0.926 for destroyed.
   - Non-randomised APS/Ordinal give one class per building for T1 and T3: q̂ = 0, because calib accuracy is above 0.90.
4. **Routing (Table 5, Figs 3 and 5).** The rule-8 α keeps calib missed-destroyed at or below 5%, but this does not carry over to new xBD fires.
   - APS test missed-destroyed, T1: 0.9% Santa Rosa, 14.0% Woolsey, 31.7% Pinery, 42.7% Portugal, with 84–95% auto-labelled.
   - APS test missed-destroyed, T3: 1.1%, 9.4%, 20.4%, 38.3%, with 90–95% auto-labelled.
   - Eaton meets the target: T3 APS auto-labels 93% and misses 1.0% ± 0.6% of destroyed homes; T1 91% and 2.8% ± 2.7%.
   - Recorded failure: T3 fold 4 seed 1 chose α = 0.5, auto-labelled 100% of Portugal and missed 54% of its destroyed homes.
   - T1 vs T3 differences are descriptive. The CIs are per model, not a paired test.
5. **Amendment and post-hoc results (Tables 5b, 5c; disclosed as added after seeing test results).**
   - A1 changes only the LAC rows.
   - Randomised APS (P1) lowers T3 missed-destroyed to 0.9%, 3.7%, 9.2%, 15.1% on the 4 fires, but auto-labels fewer buildings (72–83%).
   - P1 is post-hoc, not a headline result.

## Tables and figures
- Tables: results/tables/report_tables.md (all tables), and table1_data.csv, table2_accuracy.csv, table3_calibration.csv, table4_conformal.csv, table4b_conformal_posthoc.csv, table5_routing.csv, table5b_routing_A1.csv, table5c_routing_posthoc.csv.
- Figures (PNG + PDF, outputs/figures/):
  - fig1_reliability: reliability diagrams.
  - fig2_coverage_alpha: coverage vs nominal for Mondrian sets.
  - fig3_workload: auto-labelled share vs missed-destroyed rate over α.
  - fig4_examples: 8 Eaton houses with their sets.
  - fig5_eaton_map: Eaton map of auto-labelled vs routed houses.
- Figs 4 and 5 use one model fixed in advance (T3 fold 1 seed 0, rule-8 α). The examples were drawn with rng(0), not hand-picked.
- Curve data: results/tables/fig_curves_alpha.csv.

## Limitations
- **Fire shift.** It is the main driver of the results. Four training fires are too few to separate fire-level effects (region, imagery, building type) from model effects.
- **Small "damaged" class** (about 2% of xBD buildings). Per-class results for "damaged" are noisy.
- **Eaton labels and imagery differ from xBD.** Eaton labels are CAL FIRE field inspections, mapped to 3 classes (Affected/Minor/Major → damaged). The imagery is Maxar, not xBD. Eaton agreement may partly reflect its large destroyed share (46%).
- **T2 used one frozen prompt**, by design. Checked later in E2: three other prompts did not help, but a second zero-shot VLM (Gemma 4 12B) was much stronger (see below).
- **Possibly under-trained T3 runs.** T3 was capped at 3 epochs, and 2 of 12 runs scored best at the cap. Checked later in E2: a 6-epoch cap changes test macro-F1 by at most 0.003.
- **Amendment A1** was proposed after seeing test results. The original-rule results are kept in Table 5.
- **Fixed Mondrian α grid.** Mondrian curves are non-monotone at large α because sets become empty.
- **Hardware.** All runs were on H200; seed SD reflects training randomness only.

## Added analysis E2: can the routing be made to transfer? (2026-11-20)
Defined after the results above had been seen (configs/preregistration.md, E2 and I1–I14). Full tables:
results/tables/e2_report_tables.md; figures: outputs/figures/e2/. T3, destroyed vs not, 5% limit unless stated.

1. **Simple rules are as good as conformal routing at saving work.** Accepting the model's answer when its top
   probability passes a cut-off is within about 3 points of conformal APS on every fire; both keep the 5% limit only
   on Santa Rosa and Eaton.
2. **The ranking is fine; the cut-off is not.** Destroyed-vs-not AUROC is 0.93–0.997 on every target, so the
   failures on Woolsey, Pinery and Portugal come from where the calibration-fire threshold lands on a new fire.
3. **Repair methods trade safety for work.**
   - Risk control on 300 locally inspected houses keeps ≤ 5% on all five targets but auto-labels only 20–24% on
     Pinery and Portugal.
   - An adaptive threshold with 5% random audits (the main comparison fixed in advance) cuts missed destroyed homes
     on Portugal from 46% to 6.5% while auto-labelling 24%; it is safe on 2 of 5 targets, like conformal APS.
     Without audits it is worse than APS.
   - Covariate-shift weighting on T1 image features is the best label-free method: safe and useful on 4 of 5 targets
     on average, but single models fail on Pinery (2 of 3) and Portugal (3 of 3).
   - Label-shift reweighting and a shift alarm do not help (the alarm fires on every target).
4. **Shift measured from predictions does not predict failure.** Eaton looks most different from the calibration
   fires yet works; Woolsey looks least different yet fails.
5. **Model comparisons.** T1 and T3 have equivalent macro-F1 (±0.02) on Santa Rosa, Woolsey and Eaton (paired
   bootstrap); T3 misses fewer destroyed homes under routing on four targets. Gemma 4 12B zero-shot reaches
   macro-F1 0.46–0.64, far above Qwen zero-shot (0.31–0.43) and close to fine-tuned T3 (0.52–0.69).
6. **Palisades 2025 could not be used** as a second external test: one pre-fire WorldView-3 image covers 15% of its
   buildings and the pre/post alignment check failed its preset threshold (median shift 5.93 m > 5 m).

Additional limitations: only five targets; many methods compared (one main comparison fixed in advance); VLM scores
are not bit-identical across GPU types.
