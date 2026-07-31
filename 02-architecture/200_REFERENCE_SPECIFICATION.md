# DOCUMENT 200 — `200_REFERENCE_SPECIFICATION.md`

> **Authority Level:** Level 1 (Contractual) | **Specification ID:** `REF-001`
> 

## 1. Universal Transport Header (`CognitiveEnvelope`)

```protobuf
syntax = "proto3";

package afrp.v1;

import "afrp/v1/annotations.proto";

message CognitiveEnvelope {
    option (cio_id) = "ENVELOPE-v1";
    option (owner_subsystem) = "ALL";
    option (stability_level) = "L3";

    string message_id = 1 [(trace_sls) = "OBS-01"];
    string cognitive_cycle_id = 2 [(implements_req) = "UX-001", (trace_sls) = "ARB-03"];
    string producer_subsystem_id = 3 [(trace_sls) = "ARB-01"];
    uint32 schema_version = 4 [(trace_sls) = "ICC-02"];
    uint32 semantic_version = 5 [(trace_sls) = "ICC-02"];
    int64 generated_at_ns = 6 [(trace_sls) = "OBS-01"];
    string mission_profile_id = 7 [(trace_sls) = "SYS-05"];
    repeated string parent_cio_ids = 8 [(implements_req) = "UX-001", (trace_sls) = "ARB-03"];
    bytes payload_hash = 9 [(trace_sls) = "OBS-05"];
    string trace_id = 10 [(trace_sls) = "OBS-01"];
    string span_id = 11 [(trace_sls) = "OBS-01"];
}

```

## 2. Canonical Information Object (CIO) Taxonomy

* **`CIO-01` (Raw Observation):** Unprocessed trade, quote, or oracle event (`L1-ING`).


* **`CIO-02` (Standard Feature):** Normalized, immutable engineered value (`L1-FST`).


* **`CIO-03` (Domain Belief):** Basic belief assignment mass over $D^\Theta$ (`L2-AGENTS`).


* **`CIO-04` (WorldState Vector):** Fused global market state (`L3-WRM`).


* **`CIO-05A` (ScenarioSet):** Probability distribution over future trajectories (`L3-SIM`).


* **`CIO-05B` (DecisionContext):** Contextualized payload for optimization (`L4-FUS`).


* **`CIO-06` (Execution Candidate):** Unconstrained utility-maximized trade proposal (`L4-DEC`).


* **`CIO-07` (Authorized Action):** Policy-validated and signed trade authorization (`L4-VAL`).


* **`CIO-08` (Execution Intent):** Internal state machine order commitment (`L5-EXE`).


* **`CIO-09` (Execution Report):** Standardized venue event response (`L5-EXE`).


* **`CIO-10` (Portfolio State):** Reconciled snapshot of live exposure and cash (`L5-EXE`).


* **`CIO-11` (Calibration Weights):** Reliability modifiers for belief discounting (`L6-OPT`).


* **`CIO-12` (Episodic Embedding):** Latent vector representation of market regimes (`L6-OPT`).



## 3. Work Package Schema (`WPS-1.0`) & Evidence Schema (`ERS-1.0`)

Authoritative JSON Schema contracts stored at:

* `09-validation/schemas/wps-1.0.schema.json`

* `09-validation/schemas/ers-1.0.schema.json`


## 4. Execution Governance Protocol (`EGP-2.0`) & Diagnostic Payload

```yaml
repository_state:
  protocol_version: "EGP-2.0"
  lifecycle_state: "BASELINE_VERIFIED" # INITIAL | BASELINE_VERIFIED | WORK_PACKAGE_LOADED | PRECONDITIONS_VERIFIED | EXECUTION_AUTHORIZED | EXECUTING | VALIDATING | EVIDENCE_GENERATED | REVIEW_PENDING | COMPLETED | HALTED
  verification:
    baseline_verified: true
    governance_verified: true
    manifest_verified: true
  authorization:
    execution_authorized: false
    reason: "Work package contract not loaded. Write access locked."
  agent_identity:
    role: "AEF-02 (Software Engineer)"
    agent_vendor: "Vendor-Neutral"
    agent_name: "Claude Code / Gemini CLI / Codex / Cursor / Custom Engine"
  integrity:
    fingerprint_ledger: "00-governance/BASELINE_FINGERPRINT.yaml"
    status: "PASS"
  termination:
    state: "BASELINE_VERIFIED"
    reason: "Zero-write environment handshake complete. Awaiting WP assignment."
    next_action: "LOAD_WORK_PACKAGE"

```
