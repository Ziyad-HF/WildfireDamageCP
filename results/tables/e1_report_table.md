# E1 few-shot recalibration (added analysis, not preregistered)

Grid-cell sampling (B), 20 repeats; mean over repeats (T seed-averaged; Eaton also averaged over 4 fold models). Evaluated on the target buildings not in the sample. Full table: e1_summary.csv (incl. scheme A, LAC, APS_rand, T2, p10/p90).


## T3

| Target | Setting | Sample size (destroyed) | Mondrian coverage | Mondrian destroyed cov. | APS A1 auto share | APS A1 missed destroyed | Repeats with missed ≤5% |
|---|---|---|---|---|---|---|---|
| Santa Rosa | other fires | calib of other fires | 0.933 | 0.975 | 0.920 | 0.011 | 1.00 |
| Santa Rosa | local ~100 | 185 (40) | 0.907 | 0.934 | 0.830 | 0.032 | 0.60 |
| Santa Rosa | local ~200 | 237 (55) | 0.903 | 0.932 | 0.922 | 0.032 | 0.75 |
| Santa Rosa | local ~300 | 362 (106) | 0.890 | 0.898 | 0.964 | 0.035 | 0.75 |
| Woolsey | other fires | calib of other fires | 0.831 | 0.748 | 0.902 | 0.094 | 0.00 |
| Woolsey | local ~100 | 170 (29) | 0.880 | 0.909 | 0.740 | 0.079 | 0.40 |
| Woolsey | local ~200 | 244 (46) | 0.880 | 0.922 | 0.812 | 0.068 | 0.45 |
| Woolsey | local ~300 | 339 (66) | 0.880 | 0.904 | 0.844 | 0.070 | 0.40 |
| Pinery | other fires | calib of other fires | 0.833 | 0.598 | 0.920 | 0.202 | 0.00 |
| Pinery | local ~100 | 133 (6) | 0.915 | 0.971 | 0.648 | 0.119 | 0.35 |
| Pinery | local ~200 | 246 (12) | 0.846 | 0.949 | 0.614 | 0.080 | 0.50 |
| Pinery | local ~300 | 312 (13) | 0.866 | 0.892 | 0.726 | 0.123 | 0.30 |
| Portugal | other fires | calib of other fires | 0.851 | 0.297 | 0.953 | 0.383 | 0.00 |
| Portugal | local ~100 | 128 (7) | 0.889 | 0.984 | 0.690 | 0.138 | 0.35 |
| Portugal | local ~200 | 235 (12) | 0.886 | 0.940 | 0.669 | 0.129 | 0.35 |
| Portugal | local ~300 | 317 (16) | 0.897 | 0.912 | 0.678 | 0.121 | 0.40 |
| Eaton | other fires | calib of other fires | 0.917 | 0.974 | 0.933 | 0.010 | 1.00 |
| Eaton | local ~100 | 166 (76) | 0.913 | 0.923 | 0.946 | 0.025 | 1.00 |
| Eaton | local ~200 | 252 (103) | 0.908 | 0.918 | 0.955 | 0.021 | 1.00 |
| Eaton | local ~300 | 348 (151) | 0.902 | 0.911 | 0.982 | 0.023 | 1.00 |

## T1

| Target | Setting | Sample size (destroyed) | Mondrian coverage | Mondrian destroyed cov. | APS A1 auto share | APS A1 missed destroyed | Repeats with missed ≤5% |
|---|---|---|---|---|---|---|---|
| Santa Rosa | other fires | calib of other fires | 0.834 | 0.973 | 0.845 | 0.009 | 1.00 |
| Santa Rosa | local ~100 | 185 (40) | 0.894 | 0.932 | 0.814 | 0.034 | 0.55 |
| Santa Rosa | local ~200 | 237 (55) | 0.903 | 0.927 | 0.911 | 0.036 | 0.65 |
| Santa Rosa | local ~300 | 362 (106) | 0.888 | 0.908 | 0.931 | 0.034 | 0.75 |
| Woolsey | other fires | calib of other fires | 0.720 | 0.689 | 0.939 | 0.140 | 0.00 |
| Woolsey | local ~100 | 170 (29) | 0.903 | 0.909 | 0.672 | 0.071 | 0.50 |
| Woolsey | local ~200 | 244 (46) | 0.892 | 0.922 | 0.772 | 0.063 | 0.55 |
| Woolsey | local ~300 | 339 (66) | 0.892 | 0.917 | 0.791 | 0.065 | 0.45 |
| Pinery | other fires | calib of other fires | 0.824 | 0.454 | 0.931 | 0.319 | 0.00 |
| Pinery | local ~100 | 133 (6) | 0.908 | 0.982 | 0.604 | 0.130 | 0.35 |
| Pinery | local ~200 | 246 (12) | 0.850 | 0.937 | 0.642 | 0.079 | 0.35 |
| Pinery | local ~300 | 312 (13) | 0.877 | 0.892 | 0.694 | 0.146 | 0.35 |
| Portugal | other fires | calib of other fires | 0.861 | 0.235 | 0.952 | 0.427 | 0.00 |
| Portugal | local ~100 | 128 (7) | 0.885 | 0.980 | 0.626 | 0.116 | 0.40 |
| Portugal | local ~200 | 235 (12) | 0.892 | 0.934 | 0.712 | 0.128 | 0.15 |
| Portugal | local ~300 | 317 (16) | 0.893 | 0.931 | 0.648 | 0.106 | 0.30 |
| Eaton | other fires | calib of other fires | 0.878 | 0.927 | 0.910 | 0.028 | 1.00 |
| Eaton | local ~100 | 166 (76) | 0.912 | 0.919 | 0.930 | 0.035 | 0.90 |
| Eaton | local ~200 | 252 (103) | 0.912 | 0.928 | 0.927 | 0.033 | 0.90 |
| Eaton | local ~300 | 348 (151) | 0.898 | 0.906 | 0.951 | 0.037 | 0.95 |
