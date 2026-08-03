# Revision Report: decision_cascade
## Discovery Cycle 3 Phase 5

**Alpha ID**: IKROS-ALPHA-DC3-20260802-0009
**Family**: FAM-006
**Phase 4 Outcome**: RESEARCH
**ARB Decision**: RESEARCH
**ARB Rationale**: Decision cascade mechanism requires significant proxy redesign before revalidation is warranted. Core causal chain is plausible but current implementation is not ready for immediate revalidation. Further research (proxy construction, regime restriction) must precede a READY_FOR_REVALIDATION decision.

### Failed Assumptions
| Assumption | Revision Action | Priority |
| --- | --- | --- |
| Cascade initiator proxy reliably identifies HF-driven decision cascades in XAU/U | REPLACE_PROXY | HIGH |
| Decision cascade patterns are temporally stable across pre- and post-2019 market | RESTRICT_TO_VALIDATED_REGIME | HIGH |
| Cascade mechanism survives multiple-hypothesis benchmark correction. | REDESIGN_OR_RESEARCH | HIGH |
| Decision ecology model provides a reliable causal input to cascade initiator det | DECOUPLE_FROM_ECOLOGY_MODEL | HIGH |

### Supported Assumptions
- Fast-participant decision cascades are economically plausible during macro_transition and crisis regimes (DC2 B2 lineage).
- Walk-forward detects cascade patterns at moderate accuracy in macro_transition regime.
- Historical replay identifies 3/7 decision-cascade episodes — partial confirmation of existence.
