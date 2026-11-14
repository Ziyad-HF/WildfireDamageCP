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
- **T2 used one frozen prompt**, by design. Other prompts or models were not tried.
- **Possibly under-trained T3 runs.** T3 was capped at 3 epochs, and 2 of 12 runs scored best at the cap.
- **Amendment A1** was proposed after seeing test results. The original-rule results are kept in Table 5.
- **Fixed Mondrian α grid.** Mondrian curves are non-monotone at large α because sets become empty.
- **Hardware.** All runs were on H200; seed SD reflects training randomness only.
