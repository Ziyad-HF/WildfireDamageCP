# E2 checks: reproducibility and data quality

Supporting numbers for the added analysis E2 (see `e2_report_tables.md`).

## Reproduction of the published results
- The E2 code recomputes Phase 5 routing (LAC, APS and Mondrian under rule A1) for all 28 prediction files, on the
  test fire and Eaton: **168 of 168 rows match `p5_routing_amended.csv` to 4 decimals**
  (`scripts/checks/test_e2.py`).
- Prediction-file consistency check (`scripts/checks/verify_p34.py`): 28 prediction files, 12 T1 and 24 T3 training
  logs, no problems found.
- The paired-bootstrap point estimates (`e2_wp5_paired.csv`) equal the published values, e.g. T1 Santa Rosa
  macro-F1 0.6693 and missed-destroyed 0.0086 under APS.

## Vision-language model checks (WP8)
| Check | Qwen3-VL-8B (prompts v1–v4) | Gemma 4 12B (prompt v1) |
|---|---|---|
| Both images reach the model (image tokens per building) | 128 (64 per image) | 512 (256 per image) |
| Each answer letter is a single token | yes | yes |
| Probability mass on the answer letters, min / median over 83,079 buildings | 1.0000 / 1.0000 | 0.9997 / 1.0000 |
| Scoring time per building (batch 32 / 16) | about 0.02 s | about 0.05 s |

**Numerical reproducibility.** Re-scoring 64 Eaton buildings with the original prompt on a different GPU type and
batch layout gave the same predicted class for all 64, but logits differed by up to 1.05 (median 0.22) and class
probabilities by up to 0.125. Zero-shot VLM scores in bf16 are therefore not bit-identical across hardware; all
compared VLM runs were scored on the same GPU type.

**T3 with a 6-epoch cap.** 9 of 12 runs ended at the same checkpoint as the original 3-epoch runs (identical best
validation macro-F1); mean best validation macro-F1 0.6632 vs 0.6619 (`e2_wp8_t3e6_val.csv`).

## Image features for M5 (WP2)
T1 penultimate features were recomputed from the saved T1 models. The recomputed logits differed from the published
T1 logits by at most 0.019–0.076 per model, and 99.95–99.99% of predicted classes agreed.

## Palisades 2025 (WP7, not run)
CAL FIRE DINS 2025 Palisades: 12,081 records (Destroyed 6,845; No Damage 4,261; Affected 732; Minor 171;
Major 72), of which 1,793 are "Utility Misc Structure" and excluded, leaving 10,288 structures.

Maxar Open Data coverage of those 10,288 structures, by acquisition:

| Date | Satellite | Structures covered |
|---|---|---|
| 2024-12-21 (pre-fire) | WorldView-3 | 1,569 |
| 2025-01-09 (two days after ignition) | WorldView-3 | 917 |
| 2025-01-10 | GeoEye-1 | 8,326 |
| 2025-01-13 | WorldView-2 | 9,713 |
| 2025-01-14 | WorldView-2 | 9,713 |
| 2025-01-14 | WorldView-3 | 9,540 |
| 2025-01-15 | WorldView-3 | 9,552 |
| 2025-01-16 | GeoEye-1 | 10,198 |
| 2025-01-16 | WorldView-2 | 9,672 |
| 2025-01-19 | WorldView-2 | 7,383 |
| 2025-01-20 | WorldView-3 | 9,264 |

The only pre-fire acquisition limits any pre/post pair to at most 1,569 structures. The preset rule (WorldView-3,
most structures covered by both dates) selected 2024-12-21 / 2025-01-15 (1,546 structures; off-nadir 20.0° / 20.6°;
0% cloud). Alignment check on 30 buildings (10 per class): pre/post shift median 5.93 m, maximum 7.55 m, above the
preset 5 m threshold, so the test was not run (`outputs/gates/palisades/`). For comparison, Eaton: median 2.33 m.
