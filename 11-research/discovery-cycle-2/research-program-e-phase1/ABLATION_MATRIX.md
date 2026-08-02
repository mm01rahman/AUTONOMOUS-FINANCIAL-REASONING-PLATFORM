# Ablation Matrix
## Discovery Cycle 2 Program E Phase 1

Total ablation runs: 64 (baseline + 7 single + 21 pair + 35 triple)

### Single-Component Ablations
| Combination | Detection Acc | False Rate | Missed Rate | Brier |
| --- | --- | --- | --- | --- |
| BASELINE | 0.6051 | 0.7182 | 0.4862 | 0.6393 |
| cross_asset_network_layer | 0.6720 | 0.7092 | 0.6584 | 0.6412 |
| decision_ecology_layer | 0.6049 | 0.7088 | 0.4448 | 0.6010 |
| interaction_layer | 0.6036 | 0.7396 | 0.5640 | 0.5457 |
| liquidity_layer | 0.6051 | 0.7182 | 0.4862 | 0.6393 |
| macro_layer | 0.6118 | 0.7371 | 0.5756 | 0.6134 |
| participant_ecology_layer | 0.6351 | 0.6802 | 0.4150 | 0.5991 |
| regime_layer | 0.6941 | 0.6573 | 0.5741 | 0.6704 |

Full ablation matrix persisted in: `dc2_program_e_ablation_analysis.json`
