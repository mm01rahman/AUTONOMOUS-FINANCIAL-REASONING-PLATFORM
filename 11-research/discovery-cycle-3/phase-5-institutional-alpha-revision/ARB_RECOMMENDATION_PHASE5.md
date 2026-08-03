# ARB Recommendation — Phase 5
## Discovery Cycle 3 Revision Program

### Mechanism Decisions
- REJECT: []
- RESEARCH: ['IKROS-ALPHA-DC3-20260802-0009']
- READY FOR REVALIDATION: ['IKROS-ALPHA-DC3-20260802-0006']

### Confidence Updates
| Mechanism | Phase4 Posterior | Phase5 Posterior | Delta | Direction |
| --- | --- | --- | --- | --- |
| safe_haven_migration | 0.5760 | 0.5900 | 0.0140 | MARGINAL_INCREASE |
| decision_cascade | 0.5280 | 0.5100 | -0.0180 | DECREASE |

### Experiment Backlog
8 experiments across 2 mechanisms.

### Dataset Gaps
7 gaps identified; HIGH priority: 4.

### Institutional Learning
- Ecology-model dependency is a systemic weakness across FAM-006 mechanisms; decouple before any revalidation.
- Concept drift must be treated as a first-class gate; mechanisms with confirmed drift require regime-restricted revalidation.
- Static trigger thresholds are non-stationary; all future mechanism designs must use regime-conditional trigger logic.
- VIX and TED spread are critical missing datasets; acquisition is a prerequisite for multiple planned experiments.

### Recommendation
safe_haven_migration is READY_FOR_REVALIDATION pending composite trigger implementation and VIX/TED dataset acquisition. decision_cascade requires further RESEARCH: proxy replacement must precede revalidation. Await ARB approval before revalidation.
