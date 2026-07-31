# DOCUMENT 050 — `050_FORMAL_SYSTEM_GLOSSARY.md`

> **Authority Level:** Level 1 (Semi-Immutable) | **Specification ID:** `GLOSS-001`
> 

1. **World Model Kernel (`L3-WRM`):** The authoritative real-time state engine that synthesizes constituent domain belief vectors into a unified Cognitive State Vector ($S_t$).


2. **Cognitive State Vector ($S_t$):** The continuous 6-tuple state object $\langle \mathbf{B}_t, \mathbf{U}_t, \mathbf{C}_t, \mathbf{M}_t, \mathbf{H}_t, \mathbf{R}_t \rangle$ representing the global market manifold at time $t$.


3. **DSmT PCR5:** Proportional Conflict Redistribution Rule #5 under Dezert-Smarandache Theory, allocating conflicting evidence mass proportionally to non-empty focal elements without distortion.


4. **Equilibrium World Model ($\Sigma_{EWM}$):** A probability measure over trajectory space constrained strictly to valid market physics on the Equilibrium Manifold $\mathcal{E}$.


5. **Epistemic Uncertainty:** Mass assigned to total ignorance $m(\Theta)$, reflecting missing, noisy, or incomplete telemetry.


6. **Aleatory Uncertainty:** Statistical randomness inherent in the physical market trajectory space, measured via Differential Shannon Entropy $H(\Sigma_{EWM})$.


7. **Work Package (`WPS-1.0`):** An immutable, machine-executable task contract (`WP-IMP-XXXX.yaml`) defining exact requirements, resources, and explicit file boundaries (`bounded_files`).


8. **Execution Evidence (`ERS-1.0`):** Machine-verifiable audit telemetry record (`EXEC-XXX.yaml`) detailing agent identity, boundary compliance, quality gate results, and unlocked capabilities.


9. **Execution Governance Protocol (`EGP-2.0`):** Vendor-neutral, zero-write environment handshake protocol driving the Repository State Model (`RSM-1.0`).


10. **Cognitive Envelope:** Universal Protobuf metadata header wrapping every message in AFRP to provide OpenTelemetry tracing, schema versioning, and complete provenance lineage.


11. **Mission Profile:** Operational configuration profile (`MP-01` through `MP-05`) establishing active risk tolerances, spread limits, and agent quorum requirements.


12. **Capability Registry:** Authoritative dependency graph ledger (`CAPABILITY_REGISTRY.yaml`) maintaining capability completion states and execution DAG relationships.
