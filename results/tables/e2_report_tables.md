# Added analysis E2: baselines, shift-robust routing and robustness checks

Defined after the main results had been computed and seen (see configs/preregistration.md, E2 and I1–I14). Test fires: mean over seeds (and 95% cluster-bootstrap CI where shown). Eaton: mean over the 4 fold models. "Safe" = missed-destroyed ≤ 5%; "useful" = auto-labelled ≥ 50%; "fixes transfer" = safe and useful on ≥ 4 of 5 targets.

## Methods compared — T3, destroyed vs not, limit 5%

Cells: auto-labelled share / missed-destroyed rate on the target. Main comparison (fixed in advance): M2 with 5% audits vs Conformal APS (Phase 5).

| family | method | Santa Rosa | Woolsey | Pinery | Portugal | Eaton | safe on | safe and useful on | fixes transfer |
|---|---|---|---|---|---|---|---|---|---|
| WP1 baseline | B1 top probability | 88% / 1.0% | 89% / 10.9% | 93% / 23.3% | 96% / 47.9% | 91% / 1.1% | 2 | 2 | no |
| WP1 baseline | B2 margin | 88% / 1.0% | 89% / 10.9% | 93% / 23.3% | 96% / 47.9% | 91% / 1.1% | 2 | 2 | no |
| WP1 baseline | B3 entropy | 88% / 1.0% | 89% / 10.9% | 93% / 23.3% | 96% / 47.9% | 91% / 1.1% | 2 | 2 | no |
| WP1 baseline | B4 seed agreement | 91% / 1.0% | 90% / 11.2% | 94% / 23.1% | 97% / 51.2% | 93% / 1.0% | 2 | 2 | no |
| WP1 baseline | B5 T1–T3 agreement | 90% / 0.7% | 93% / 12.4% | 97% / 33.2% | 98% / 59.5% | 93% / 1.2% | 2 | 2 | no |
| WP1 baseline | Conformal APS (Phase 5) | 86% / 0.8% | 85% / 8.4% | 92% / 20.2% | 96% / 46.0% | 89% / 1.0% | 2 | 2 | no |
| WP1 baseline | Conformal APS on seed average | 86% / 0.6% | 89% / 9.8% | 94% / 24.0% | 96% / 47.6% | 90% / 1.0% | 2 | 2 | no |
| WP1 baseline | Conformal LAC | 89% / 1.0% | 90% / 11.8% | 93% / 22.9% | 96% / 48.6% | 91% / 1.2% | 2 | 2 | no |
| WP1 baseline | Conformal Mondrian | 97% / 1.0% | 100% / 7.5% | 100% / 21.5% | 100% / 44.1% | 99% / 1.0% | 2 | 2 | no |
| WP1 baseline | Randomised APS (P1) | 79% / 0.9% | 79% / 8.0% | 86% / 17.2% | 88% / 33.6% | 82% / 1.0% | 2 | 2 | no |
| WP2 repair | M1 risk control (calib) | 88% / 0.9% | 89% / 10.9% | 93% / 23.3% | 96% / 47.9% | 91% / 1.1% | 2 | 2 | no |
| WP2 repair | M1 risk control (local sample, n = 100) | 43% / 1.7% | 32% / 2.5% | 0% / 0.0% | 2% / 0.1% | 73% / 1.9% | 5 | 1 | no |
| WP2 repair | M1 risk control (local sample, n = 300) | 85% / 3.2% | 72% / 4.9% | 24% / 3.0% | 20% / 2.4% | 95% / 2.2% | 5 | 3 | no |
| WP2 repair | M2 learn as you go (0% audits) | 95% / 2.7% | 96% / 21.2% | 96% / 30.4% | 99% / 62.3% | 92% / 1.3% | 2 | 2 | no |
| WP2 repair | M2 learn as you go (5% audits) | 94% / 2.3% | 71% / 6.1% | 56% / 14.1% | 24% / 6.5% | 92% / 1.3% | 2 | 2 | no |
| WP2 repair | M3 label-shift reweighting | 88% / 0.9% | 88% / 10.6% | 90% / 18.5% | 95% / 43.7% | 91% / 1.1% | 2 | 2 | no |
| WP2 repair | M5 look-alike weighting (image features) | 90% / 1.3% | 71% / 3.2% | 52% / 3.9% | 60% / 5.0% | 90% / 0.9% | 4 | 4 | yes |
| WP2 repair | M5 look-alike weighting (scores) | 98% / 3.8% | 78% / 4.2% | 28% / 3.9% | 55% / 9.1% | 96% / 1.9% | 4 | 3 | no |

## Methods compared — T3, 3 classes, limit 5%

Cells: auto-labelled share / missed-destroyed rate on the target. 

| family | method | Santa Rosa | Woolsey | Pinery | Portugal | Eaton | safe on | safe and useful on | fixes transfer |
|---|---|---|---|---|---|---|---|---|---|
| WP1 baseline | B1 top probability | 93% / 1.2% | 91% / 10.7% | 93% / 22.9% | 96% / 41.1% | 94% / 1.2% | 2 | 2 | no |
| WP1 baseline | B2 margin | 93% / 1.3% | 91% / 11.1% | 93% / 22.7% | 97% / 43.3% | 94% / 1.2% | 2 | 2 | no |
| WP1 baseline | B3 entropy | 93% / 1.3% | 91% / 10.7% | 94% / 20.8% | 95% / 39.4% | 95% / 1.5% | 2 | 2 | no |
| WP1 baseline | B4 seed agreement | 94% / 1.4% | 89% / 8.4% | 89% / 20.1% | 93% / 27.3% | 92% / 0.6% | 2 | 2 | no |
| WP1 baseline | B5 T1–T3 agreement | 94% / 0.8% | 92% / 8.4% | 93% / 25.3% | 96% / 39.9% | 95% / 0.7% | 2 | 2 | no |
| WP1 baseline | Conformal APS (Phase 5) | 92% / 1.1% | 90% / 9.4% | 92% / 20.4% | 95% / 38.3% | 93% / 1.0% | 2 | 2 | no |
| WP1 baseline | Conformal APS on seed average | 93% / 0.9% | 92% / 9.1% | 94% / 19.7% | 97% / 40.4% | 95% / 0.9% | 2 | 2 | no |
| WP1 baseline | Conformal LAC | 93% / 1.2% | 90% / 9.8% | 93% / 22.0% | 96% / 39.1% | 94% / 1.2% | 2 | 2 | no |
| WP1 baseline | Conformal Mondrian | 66% / 1.0% | 63% / 10.7% | 65% / 17.2% | 58% / 34.6% | 63% / 1.1% | 2 | 2 | no |
| WP1 baseline | Randomised APS (P1) | 83% / 0.9% | 72% / 3.7% | 74% / 9.2% | 79% / 15.1% | 80% / 0.6% | 3 | 3 | no |
| WP2 repair | M1 risk control (calib) | 93% / 1.2% | 91% / 10.4% | 93% / 22.9% | 96% / 41.1% | 94% / 1.2% | 2 | 2 | no |
| WP2 repair | M1 risk control (local sample, n = 100) | 43% / 1.5% | 33% / 2.7% | 0% / 0.0% | 2% / 0.1% | 74% / 1.7% | 5 | 1 | no |
| WP2 repair | M1 risk control (local sample, n = 300) | 86% / 2.8% | 74% / 4.9% | 23% / 3.3% | 20% / 2.1% | 96% / 2.1% | 5 | 3 | no |
| WP2 repair | M2 learn as you go (0% audits) | 96% / 2.4% | 97% / 18.2% | 98% / 32.4% | 99% / 55.4% | 95% / 1.4% | 2 | 2 | no |
| WP2 repair | M2 learn as you go (5% audits) | 96% / 2.9% | 85% / 6.8% | 54% / 13.5% | 29% / 7.2% | 96% / 1.7% | 2 | 2 | no |
| WP2 repair | M5 look-alike weighting (image features) | 93% / 1.4% | 83% / 4.9% | 76% / 7.9% | 86% / 17.5% | 94% / 1.0% | 3 | 3 | no |
| WP2 repair | M5 look-alike weighting (scores) | 99% / 3.9% | 84% / 5.2% | 82% / 10.9% | 84% / 16.5% | 97% / 1.6% | 2 | 2 | no |

## Methods compared — T1, destroyed vs not, limit 5%

Cells: auto-labelled share / missed-destroyed rate on the target. 

| family | method | Santa Rosa | Woolsey | Pinery | Portugal | Eaton | safe on | safe and useful on | fixes transfer |
|---|---|---|---|---|---|---|---|---|---|
| WP1 baseline | B1 top probability | 83% / 1.2% | 93% / 14.0% | 96% / 32.6% | 97% / 50.3% | 85% / 2.3% | 2 | 2 | no |
| WP1 baseline | B2 margin | 83% / 1.2% | 93% / 14.0% | 96% / 32.6% | 97% / 50.3% | 85% / 2.3% | 2 | 2 | no |
| WP1 baseline | B3 entropy | 83% / 1.2% | 93% / 14.0% | 96% / 32.6% | 97% / 50.3% | 85% / 2.3% | 2 | 2 | no |
| WP1 baseline | B4 seed agreement | 87% / 1.0% | 93% / 12.1% | 97% / 36.7% | 97% / 54.8% | 86% / 1.3% | 2 | 2 | no |
| WP1 baseline | B5 T1–T3 agreement | 90% / 0.7% | 93% / 12.4% | 97% / 33.2% | 98% / 59.5% | 93% / 1.2% | 2 | 2 | no |
| WP1 baseline | Conformal APS (Phase 5) | 75% / 0.6% | 91% / 11.7% | 95% / 30.6% | 96% / 47.2% | 81% / 1.7% | 2 | 2 | no |
| WP1 baseline | Conformal APS on seed average | 80% / 0.5% | 92% / 11.7% | 95% / 28.4% | 98% / 58.9% | 84% / 1.4% | 2 | 2 | no |
| WP1 baseline | Conformal LAC | 83% / 1.1% | 93% / 14.1% | 96% / 33.2% | 97% / 50.4% | 85% / 2.2% | 2 | 2 | no |
| WP1 baseline | Conformal Mondrian | 97% / 1.2% | 99% / 8.8% | 100% / 27.8% | 100% / 41.1% | 99% / 1.4% | 2 | 2 | no |
| WP1 baseline | Randomised APS (P1) | 75% / 1.1% | 80% / 8.5% | 88% / 24.2% | 88% / 34.6% | 75% / 1.9% | 2 | 2 | no |
| WP2 repair | M1 risk control (calib) | 83% / 1.2% | 93% / 14.0% | 96% / 32.6% | 97% / 50.3% | 85% / 2.3% | 2 | 2 | no |
| WP2 repair | M1 risk control (local sample, n = 100) | 41% / 1.8% | 26% / 2.3% | 0% / 0.0% | 2% / 0.1% | 70% / 2.7% | 5 | 1 | no |
| WP2 repair | M1 risk control (local sample, n = 300) | 81% / 3.1% | 63% / 3.8% | 22% / 2.0% | 19% / 1.9% | 91% / 3.5% | 5 | 3 | no |
| WP2 repair | M2 learn as you go (0% audits) | 92% / 2.5% | 98% / 20.9% | 98% / 41.5% | 99% / 65.3% | 88% / 2.6% | 2 | 2 | no |
| WP2 repair | M2 learn as you go (5% audits) | 90% / 2.1% | 63% / 5.9% | 39% / 12.1% | 23% / 6.1% | 86% / 2.2% | 2 | 2 | no |
| WP2 repair | M3 label-shift reweighting | 83% / 1.2% | 94% / 14.7% | 95% / 30.7% | 95% / 42.8% | 85% / 2.2% | 2 | 2 | no |
| WP2 repair | M5 look-alike weighting (image features) | 87% / 1.5% | 65% / 2.8% | 34% / 0.4% | 83% / 19.5% | 81% / 1.3% | 4 | 3 | no |
| WP2 repair | M5 look-alike weighting (scores) | 90% / 1.8% | 72% / 3.3% | 53% / 8.3% | 58% / 11.1% | 86% / 1.4% | 3 | 3 | no |

## Methods compared — T1, 3 classes, limit 5%

Cells: auto-labelled share / missed-destroyed rate on the target. 

| family | method | Santa Rosa | Woolsey | Pinery | Portugal | Eaton | safe on | safe and useful on | fixes transfer |
|---|---|---|---|---|---|---|---|---|---|
| WP1 baseline | B1 top probability | 86% / 1.0% | 95% / 14.6% | 94% / 33.0% | 96% / 45.5% | 92% / 3.2% | 2 | 2 | no |
| WP1 baseline | B2 margin | 85% / 1.0% | 94% / 14.7% | 94% / 33.6% | 97% / 48.3% | 91% / 3.0% | 2 | 2 | no |
| WP1 baseline | B3 entropy | 86% / 1.0% | 94% / 14.3% | 95% / 34.1% | 95% / 42.1% | 93% / 3.8% | 2 | 2 | no |
| WP1 baseline | B4 seed agreement | 88% / 0.8% | 88% / 7.5% | 89% / 24.0% | 94% / 34.8% | 89% / 1.0% | 2 | 2 | no |
| WP1 baseline | B5 T1–T3 agreement | 94% / 0.8% | 92% / 8.4% | 93% / 25.3% | 96% / 39.9% | 95% / 0.7% | 2 | 2 | no |
| WP1 baseline | Conformal APS (Phase 5) | 84% / 0.9% | 94% / 14.0% | 93% / 31.7% | 95% / 42.7% | 91% / 2.8% | 2 | 2 | no |
| WP1 baseline | Conformal APS on seed average | 87% / 0.5% | 95% / 12.2% | 95% / 31.9% | 97% / 44.7% | 94% / 2.1% | 2 | 2 | no |
| WP1 baseline | Conformal LAC | 85% / 0.9% | 94% / 13.8% | 94% / 33.3% | 96% / 46.3% | 91% / 2.9% | 2 | 2 | no |
| WP1 baseline | Conformal Mondrian | 42% / 1.5% | 34% / 14.7% | 58% / 29.0% | 60% / 39.9% | 36% / 3.4% | 2 | 0 | no |
| WP1 baseline | Randomised APS (P1) | 76% / 0.7% | 68% / 3.2% | 75% / 13.2% | 79% / 15.4% | 73% / 1.2% | 3 | 3 | no |
| WP2 repair | M1 risk control (calib) | 85% / 1.0% | 95% / 14.6% | 94% / 33.0% | 96% / 45.5% | 92% / 3.2% | 2 | 2 | no |
| WP2 repair | M1 risk control (local sample, n = 100) | 42% / 1.6% | 26% / 1.9% | 0% / 0.0% | 2% / 0.1% | 70% / 2.5% | 5 | 1 | no |
| WP2 repair | M1 risk control (local sample, n = 300) | 82% / 2.7% | 64% / 3.6% | 20% / 2.1% | 19% / 1.8% | 93% / 3.4% | 5 | 3 | no |
| WP2 repair | M2 learn as you go (0% audits) | 91% / 2.2% | 99% / 19.7% | 97% / 41.4% | 99% / 59.1% | 93% / 3.6% | 2 | 2 | no |
| WP2 repair | M2 learn as you go (5% audits) | 92% / 2.6% | 78% / 7.1% | 37% / 12.2% | 28% / 6.3% | 92% / 3.1% | 2 | 2 | no |
| WP2 repair | M5 look-alike weighting (image features) | 89% / 1.6% | 79% / 4.8% | 78% / 12.2% | 83% / 16.1% | 89% / 1.6% | 3 | 3 | no |
| WP2 repair | M5 look-alike weighting (scores) | 89% / 1.6% | 77% / 4.0% | 76% / 12.2% | 87% / 17.5% | 90% / 1.9% | 3 | 3 | no |

## Per-model robustness (T3, destroyed vs not, limit 5%)

Number of single models (fold × seed runs; Eaton: all 12 fold models) that are both safe (missed ≤ 5%) and useful (auto ≥ 50%). The summary tables above average over seeds, which can hide unsafe individual models.

| method | Santa Rosa | Woolsey | Pinery | Portugal | Eaton |
|---|---|---|---|---|---|
| Conformal APS (Phase 5) | 3/3 | 1/3 | 0/3 | 0/3 | 12/12 |
| M2 learn as you go (5% audits), mean over 20 orders | 3/3 | 1/3 | 0/3 | 0/3 | 12/12 |
| M1 local sample n = 300, mean over 20 samples | 3/3 | 2/3 | 0/3 | 0/3 | 12/12 |
| M5 look-alike weighting (scores) | 3/3 | 2/3 | 0/3 | 0/3 | 12/12 |
| M5 look-alike weighting (image features) | 3/3 | 3/3 | 1/3 | 0/3 | 12/12 |

## Sensitivity to the limit (T3, destroyed vs not)

Cells: auto-labelled / missed-destroyed.

| limit | method | Santa Rosa | Woolsey | Pinery | Portugal | Eaton |
|---|---|---|---|---|---|---|
| 2% | Conformal APS | 29% / 0.1% | 54% / 3.0% | 83% / 10.0% | 88% / 20.9% | 64% / 0.4% |
| 2% | M1 risk control (calib) | 77% / 0.4% | 78% / 4.3% | 84% / 11.1% | 90% / 25.0% | 82% / 0.5% |
| 2% | M2 (5% audits) | 85% / 1.8% | 54% / 2.6% | 56% / 8.7% | 15% / 3.8% | 86% / 0.6% |
| 5% | Conformal APS | 86% / 0.8% | 85% / 8.4% | 92% / 20.2% | 96% / 46.0% | 89% / 1.0% |
| 5% | M1 risk control (calib) | 88% / 0.9% | 89% / 10.9% | 93% / 23.3% | 96% / 47.9% | 91% / 1.1% |
| 5% | M2 (5% audits) | 94% / 2.3% | 71% / 6.1% | 56% / 14.1% | 24% / 6.5% | 92% / 1.3% |
| 10% | Conformal APS | 93% / 2.3% | 96% / 20.3% | 99% / 38.6% | 99% / 62.0% | 95% / 2.2% |
| 10% | M1 risk control (calib) | 94% / 2.4% | 97% / 22.5% | 99% / 38.1% | 99% / 63.1% | 96% / 2.3% |
| 10% | M2 (5% audits) | 97% / 3.9% | 82% / 10.4% | 57% / 19.3% | 38% / 9.5% | 97% / 2.5% |

## Destroyed vs not: ranking quality (WP4)

| model | target | destroyed share | AUROC | AUPRC | destroyed F1 |
|---|---|---|---|---|---|
| t1 | Eaton | 46.2% | 0.997 | 0.996 | 0.954 |
| t1 | Santa Rosa | 26.6% | 0.992 | 0.981 | 0.940 |
| t1 | Woolsey | 16.7% | 0.970 | 0.892 | 0.810 |
| t1 | Pinery | 4.2% | 0.947 | 0.605 | 0.551 |
| t1 | Portugal | 4.9% | 0.938 | 0.539 | 0.411 |
| t2 | Eaton | 46.2% | 0.979 | 0.976 | 0.910 |
| t2 | Santa Rosa | 26.6% | 0.960 | 0.923 | 0.760 |
| t2 | Woolsey | 16.7% | 0.887 | 0.690 | 0.435 |
| t2 | Pinery | 4.2% | 0.882 | 0.433 | 0.292 |
| t2 | Portugal | 4.9% | 0.796 | 0.277 | 0.029 |
| t3 | Eaton | 46.2% | 0.997 | 0.997 | 0.970 |
| t3 | Santa Rosa | 26.6% | 0.995 | 0.985 | 0.938 |
| t3 | Woolsey | 16.7% | 0.974 | 0.884 | 0.778 |
| t3 | Pinery | 4.2% | 0.950 | 0.597 | 0.586 |
| t3 | Portugal | 4.9% | 0.931 | 0.469 | 0.413 |

## T1 vs T3, paired cluster bootstrap (WP5)

Same resample of grid cells for both models. Equivalence on macro-F1: CI inside ±0.02. Routing = APS under A1.

| metric | Santa Rosa | Woolsey | Pinery | Portugal | Eaton |
|---|---|---|---|---|---|
| auto_share | +0.076 [+0.065, +0.088] | -0.037 [-0.044, -0.031] | -0.011 [-0.020, -0.004] | +0.001 [-0.002, +0.003] | +0.024 [+0.019, +0.028] |
| ece | -0.020 [-0.022, -0.017] | +0.003 [-0.002, +0.008] | +0.014 [+0.006, +0.016] | +0.005 [+0.003, +0.007] | -0.004 [-0.009, -0.000] |
| f1_des | +0.000 [-0.006, +0.008] | -0.026 [-0.034, -0.017] | +0.000 [-0.052, +0.049] | -0.007 [-0.028, +0.015] | +0.012 [+0.009, +0.014] |
| macro_f1 | -0.003 [-0.013, +0.008] | -0.001 [-0.010, +0.009] | -0.007 [-0.030, +0.015] | -0.016 [-0.028, -0.002] | +0.010 [+0.005, +0.014] |
| missed_destroyed_rate | +0.002 [-0.001, +0.005] | -0.045 [-0.057, -0.034] | -0.114 [-0.168, -0.062] | -0.044 [-0.068, -0.024] | -0.018 [-0.021, -0.014] |

## How different is each target? (WP3)

Energy distance and MMD between calib and target probability vectors; transfer gap of Phase 5 APS (A1) in percentage points.

| model | tgt | energy | mmd | transfer_gap_pp | destroyed_share |
|---|---|---|---|---|---|
| t1 | Eaton | 0.205 | 0.15 | -1.672 | 0.462 |
| t1 | Pinery | 0.044 | 0.027 | 27.16 | 0.042 |
| t1 | Portugal | 0.085 | 0.044 | 38.341 | 0.049 |
| t1 | Santa Rosa | 0.114 | 0.095 | -3.505 | 0.266 |
| t1 | Woolsey | 0.025 | 0.046 | 9.352 | 0.167 |
| t2 | Eaton | 0.184 | 0.249 | -3.294 | 0.462 |
| t2 | Pinery | 0.023 | 0.034 | 23.913 | 0.042 |
| t2 | Portugal | 0.06 | 0.128 | 17.945 | 0.049 |
| t2 | Santa Rosa | 0.081 | 0.106 | -3.809 | 0.266 |
| t2 | Woolsey | 0.01 | 0.021 | 2.084 | 0.167 |
| t3 | Eaton | 0.228 | 0.162 | -3.163 | 0.462 |
| t3 | Pinery | 0.037 | 0.022 | 16.156 | 0.042 |
| t3 | Portugal | 0.077 | 0.043 | 34.563 | 0.049 |
| t3 | Santa Rosa | 0.075 | 0.045 | -3.54 | 0.266 |
| t3 | Woolsey | 0.01 | 0.015 | 5.248 | 0.167 |

Within-target check (4 × 4-cell blocks with ≥ 10 destroyed): Spearman correlation between a block's distance to calib and its missed-destroyed rate.

| model | target | n_blocks | spearman_rho | p_value |
|---|---|---|---|---|
| t1 | Eaton | 9 | -0.817 | 0.007 |
| t1 | Pinery | 5 | -0.051 | 0.935 |
| t1 | Portugal | 30 | 0.114 | 0.549 |
| t1 | Santa Rosa | 24 | -0.01 | 0.965 |
| t1 | Woolsey | 45 | 0.215 | 0.156 |
| t2 | Eaton | 9 | -0.517 | 0.154 |
| t2 | Pinery | 5 | 0.2 | 0.747 |
| t2 | Portugal | 30 | 0.121 | 0.523 |
| t2 | Santa Rosa | 24 | -0.375 | 0.071 |
| t2 | Woolsey | 45 | -0.336 | 0.024 |
| t3 | Eaton | 9 | -0.733 | 0.025 |
| t3 | Pinery | 5 | -0.3 | 0.624 |
| t3 | Portugal | 30 | 0.15 | 0.429 |
| t3 | Santa Rosa | 24 | -0.05 | 0.818 |
| t3 | Woolsey | 45 | -0.232 | 0.125 |

## Inspection workload (WP6), T3, destroyed vs not, limit 5%

Houses to visit include M2 audits and the M1 local sample. One team checks 100 houses per day (50 and 150 in the CSV).

| target | method | houses_to_visit | team-days (100/day) | days, 25 teams | missed destroyed |
|---|---|---|---|---|---|
| Eaton | B1 top probability | 767 | 8 | 0.3 | 44.0 |
| Pinery | B1 top probability | 371 | 4 | 0.1 | 53.0 |
| Portugal | B1 top probability | 835 | 8 | 0.3 | 522.0 |
| Santa Rosa | B1 top probability | 2531 | 25 | 1.0 | 56.0 |
| Woolsey | B1 top probability | 2840 | 28 | 1.1 | 456.0 |
| Eaton | Conformal APS (Phase 5, A1) | 904 | 9 | 0.4 | 39.0 |
| Pinery | Conformal APS (Phase 5, A1) | 429 | 4 | 0.2 | 46.0 |
| Portugal | Conformal APS (Phase 5, A1) | 927 | 9 | 0.4 | 502.0 |
| Santa Rosa | Conformal APS (Phase 5, A1) | 3039 | 30 | 1.2 | 44.0 |
| Woolsey | Conformal APS (Phase 5, A1) | 3653 | 37 | 1.5 | 351.0 |
| Eaton | Randomised APS (P1) | 1500 | 15 | 0.6 | 40.0 |
| Pinery | Randomised APS (P1) | 775 | 8 | 0.3 | 39.0 |
| Portugal | Randomised APS (P1) | 2760 | 28 | 1.1 | 366.0 |
| Santa Rosa | Randomised APS (P1) | 4641 | 46 | 1.9 | 51.0 |
| Woolsey | Randomised APS (P1) | 5151 | 52 | 2.1 | 336.0 |
| Eaton | M1 risk control (calib) | 773 | 8 | 0.3 | 44.0 |
| Pinery | M1 risk control (calib) | 371 | 4 | 0.1 | 53.0 |
| Portugal | M1 risk control (calib) | 835 | 8 | 0.3 | 522.0 |
| Santa Rosa | M1 risk control (calib) | 2561 | 26 | 1.0 | 55.0 |
| Woolsey | M1 risk control (calib) | 2840 | 28 | 1.1 | 456.0 |
| Eaton | M1 risk control (local sample, n = 300) | 777 | 8 | 0.3 | 88.0 |
| Pinery | M1 risk control (local sample, n = 300) | 4217 | 42 | 1.7 | 7.0 |
| Portugal | M1 risk control (local sample, n = 300) | 17850 | 179 | 7.1 | 26.0 |
| Santa Rosa | M1 risk control (local sample, n = 300) | 3681 | 37 | 1.5 | 186.0 |
| Woolsey | M1 risk control (local sample, n = 300) | 7325 | 73 | 2.9 | 206.0 |
| Eaton | M2 learn as you go (5% audits) | 1057 | 11 | 0.4 | 49.0 |
| Pinery | M2 learn as you go (5% audits) | 2551 | 26 | 1.0 | 32.0 |
| Portugal | M2 learn as you go (5% audits) | 17180 | 172 | 6.9 | 71.0 |
| Santa Rosa | M2 learn as you go (5% audits) | 2432 | 24 | 1.0 | 131.0 |
| Woolsey | M2 learn as you go (5% audits) | 8099 | 81 | 3.2 | 255.0 |
| Eaton | M5 look-alike weighting (scores) | 358 | 4 | 0.1 | 74.0 |
| Pinery | M5 look-alike weighting (scores) | 3893 | 39 | 1.6 | 9.0 |
| Portugal | M5 look-alike weighting (scores) | 9992 | 100 | 4.0 | 99.0 |
| Santa Rosa | M5 look-alike weighting (scores) | 510 | 5 | 0.2 | 222.0 |
| Woolsey | M5 look-alike weighting (scores) | 5552 | 56 | 2.2 | 175.0 |
| Eaton | M5 look-alike weighting (image features) | 843 | 8 | 0.3 | 34.0 |
| Pinery | M5 look-alike weighting (image features) | 2625 | 26 | 1.0 | 9.0 |
| Portugal | M5 look-alike weighting (image features) | 8982 | 90 | 3.6 | 55.0 |
| Santa Rosa | M5 look-alike weighting (image features) | 2266 | 23 | 0.9 | 73.0 |
| Woolsey | M5 look-alike weighting (image features) | 7160 | 72 | 2.9 | 134.0 |
| Santa Rosa | Inspect everything | 21869 | 219 | 8.7 | 0.0 |
| Eaton | Inspect everything | 8457 | 85 | 3.4 | 0.0 |
| Woolsey | Inspect everything | 24976 | 250 | 10.0 | 0.0 |
| Pinery | Inspect everything | 5428 | 54 | 2.2 | 0.0 |
| Portugal | Inspect everything | 22349 | 223 | 8.9 | 0.0 |

## Fairer test of the vision-language models (WP8)

T2 prompts v2–v4, a second VLM (Gemma 4 12B, zero-shot) and T3 with a 6-epoch cap. Routing = APS under A1 on destroyed vs not.

| label | target | macro-F1 | ECE after | AUROC destroyed | binary auto / missed |
|---|---|---|---|---|---|
| T2 prompt v1 (original) | Eaton | 0.426 | 0.233 | 0.979 | 27% / 0.2% |
| T2 prompt v1 (original) | Santa Rosa | 0.399 | 0.229 | 0.960 | 16% / 0.3% |
| T2 prompt v1 (original) | Woolsey | 0.375 | 0.157 | 0.887 | 32% / 2.8% |
| T2 prompt v1 (original) | Pinery | 0.373 | 0.074 | 0.882 | 59% / 9.2% |
| T2 prompt v1 (original) | Portugal | 0.311 | 0.152 | 0.796 | 82% / 41.0% |
| Gemma 4 12B zero-shot (prompt v1) | Eaton | 0.641 | 0.033 | 0.996 | 95% / 0.4% |
| Gemma 4 12B zero-shot (prompt v1) | Santa Rosa | 0.560 | 0.051 | 0.987 | 76% / 0.4% |
| Gemma 4 12B zero-shot (prompt v1) | Woolsey | 0.542 | 0.044 | 0.955 | 98% / 7.9% |
| Gemma 4 12B zero-shot (prompt v1) | Pinery | 0.461 | 0.054 | 0.934 | 94% / 17.5% |
| Gemma 4 12B zero-shot (prompt v1) | Portugal | 0.505 | 0.105 | 0.923 | 100% / 36.9% |
| T2 prompt v2 (CAL FIRE terms) | Eaton | 0.403 | 0.251 | 0.977 | 19% / 0.2% |
| T2 prompt v2 (CAL FIRE terms) | Santa Rosa | 0.380 | 0.271 | 0.954 | 16% / 0.7% |
| T2 prompt v2 (CAL FIRE terms) | Woolsey | 0.368 | 0.206 | 0.876 | 33% / 3.7% |
| T2 prompt v2 (CAL FIRE terms) | Pinery | 0.370 | 0.164 | 0.883 | 56% / 8.7% |
| T2 prompt v2 (CAL FIRE terms) | Portugal | 0.326 | 0.126 | 0.785 | 79% / 39.3% |
| T2 prompt v3 (reversed options) | Eaton | 0.396 | 0.217 | 0.979 | 17% / 0.2% |
| T2 prompt v3 (reversed options) | Santa Rosa | 0.308 | 0.283 | 0.961 | 19% / 0.4% |
| T2 prompt v3 (reversed options) | Woolsey | 0.270 | 0.231 | 0.891 | 36% / 3.7% |
| T2 prompt v3 (reversed options) | Pinery | 0.279 | 0.119 | 0.882 | 61% / 8.7% |
| T2 prompt v3 (reversed options) | Portugal | 0.251 | 0.050 | 0.791 | 79% / 37.9% |
| T2 prompt v4 (destroyed yes/no) | Eaton | – | – | 0.970 | 60% / 0.3% |
| T2 prompt v4 (destroyed yes/no) | Santa Rosa | – | – | 0.952 | 20% / 0.5% |
| T2 prompt v4 (destroyed yes/no) | Woolsey | – | – | 0.872 | 46% / 6.6% |
| T2 prompt v4 (destroyed yes/no) | Pinery | – | – | 0.874 | 65% / 12.2% |
| T2 prompt v4 (destroyed yes/no) | Portugal | – | – | 0.768 | 76% / 39.0% |
| T3 LoRA, 3-epoch cap (original) | Eaton | 0.693 | 0.031 | 0.997 | 89% / 1.0% |
| T3 LoRA, 3-epoch cap (original) | Santa Rosa | 0.667 | 0.012 | 0.995 | 86% / 0.8% |
| T3 LoRA, 3-epoch cap (original) | Woolsey | 0.637 | 0.019 | 0.974 | 85% / 8.4% |
| T3 LoRA, 3-epoch cap (original) | Pinery | 0.571 | 0.025 | 0.950 | 92% / 20.2% |
| T3 LoRA, 3-epoch cap (original) | Portugal | 0.519 | 0.015 | 0.931 | 96% / 46.0% |

## Palisades (WP7)

Not run. The only WorldView-3 pre-fire image in the Maxar Open Data collection covers 1,546 of 10,288 Palisades structures, and the pre/post alignment check failed its preset gate (median shift 5.93 m > 5 m).
