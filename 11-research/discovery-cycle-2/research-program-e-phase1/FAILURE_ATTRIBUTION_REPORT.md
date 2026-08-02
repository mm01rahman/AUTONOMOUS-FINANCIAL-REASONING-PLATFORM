# Failure Attribution Report
## Discovery Cycle 2 Program E Phase 1

| Failure ID | Primary Layer | Baseline Metric | Ablated Metric | Attribution | Priority |
| --- | --- | --- | --- | --- | --- |
| F-001 | macro_layer | 0.7182 | 0.7371 | LAYER_MASKING_FAILURE | MEDIUM |
| F-002 | participant_ecology_layer | 0.4862 | 0.4150 | LAYER_CAUSING_FAILURE | HIGH |
| F-003 | interaction_layer | 0.6393 | 0.5457 | LAYER_CAUSING_FAILURE | HIGH |
| F-004 | liquidity_layer | 0.6051 | 0.6051 | NEUTRAL | LOW |
| F-005 | regime_layer | 0.6051 | 0.6941 | LAYER_CAUSING_FAILURE | HIGH |

### Failures from Program D
Each row attributes one of the five Program D documented failures to the responsible engine component.
Attribution direction: LAYER_CAUSING_FAILURE = removal of that layer improved the failure metric.
