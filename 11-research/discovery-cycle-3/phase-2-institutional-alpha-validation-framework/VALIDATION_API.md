# Validation API
## Discovery Cycle 3 Phase 2

API version: **1.0.0**

| Endpoint | Input | Output |
| --- | --- | --- |
| register_alpha_for_validation | alpha_id, mechanism_spec, evidence_refs | validation_id, status |
| execute_validation_protocol | validation_id, methods | method_reports, dimension_scores, promotion_level |
| record_failure_analysis | validation_id, failure_packet | failure_id, continuation_task_id |
| record_success_analysis | validation_id, success_packet | support_packet_id, promotion_level |
| update_validation_confidence | validation_id, confidence_components | confidence_post |
