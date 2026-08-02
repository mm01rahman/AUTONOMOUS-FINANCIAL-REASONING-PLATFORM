# SPEC-031 — Memory & Knowledge Architecture

> **Specification ID:** `SPEC-031`
> **Version:** `0.5.0`
> **Level:** L4 (Implementation Specification)
> **Status:** Draft
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0040 (stub) / WP-IMP-0041 (implementation)
> **Canonical Source:** Derived from L1-MEM + L6-OPT + SPEC-060
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Defines the complete memory and knowledge architecture for AFRP, encompassing both
operational runtime memory and institutional research knowledge accumulation.

## 2. Memory Taxonomy

### 2.1 Operational Memory (Runtime — IMPLEMENTED)

| Component | Purpose | CIO | Location | Status |
|-----------|---------|-----|----------|--------|
| L1-MEM Vector Store | Episodic embeddings retrieval | CIO-12 | `layer1/memory.py` | COMPLETE |
| L1-RDB Relational DB | Trade history, portfolio state | CIO-10 | `layer1/storage.py` | COMPLETE |
| L6-OPT Calibration | Agent reliability weights | CIO-11 | `layer6/learning.py` | COMPLETE |

### 2.2 Research Memory (IKROS — NOT IMPLEMENTED)

Per SPEC-060 (IKROS Architecture), the full memory architecture requires:

| Memory Type | Purpose | Status |
|-------------|---------|--------|
| Short-term Research Memory | Active experiment context | **MISSING** |
| Working Memory | Current hypothesis under test | **MISSING** |
| Semantic Memory | Consolidated research knowledge | **MISSING** |
| Episodic Memory | Experiment history and outcomes | **MISSING** |
| Procedural Memory | Research methodology procedures | **MISSING** |
| Long-term Research Memory | Validated institutional knowledge | **MISSING** |

## 3. Gap Analysis

**Critical gap:** Phase E research failures (all 6 hypotheses) are not captured
in any persistent memory. When the session ends, this knowledge is lost.

**Constitutional violation:** Article IX states "every failure, benchmark, and
lesson must become institutional memory." Current state violates this article.

## 4. Implementation Path

Full memory architecture requires IKROS (SPEC-060 → WP-IMP-0041).
Runtime memory (L1-MEM, L1-RDB, L6-OPT) is COMPLETE.

## 5. Traceability

FR-009, FR-014 in TVM-001.

## 6. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.5.0 | 2026-08-02 | Draft derived from runtime implementation; IKROS gap documented |
