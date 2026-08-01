# SPEC-021 — Implementation Guide

> **Specification ID:** `SPEC-021`
> **Version:** `1.0.0`
> **Level:** L3 (Engineering Specification)
> **Status:** Approved
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** Lead Engineer
> **Work Package:** WP-IMP-0040
> **Canonical Source:** `03-engineering/300_IMPLEMENTATION_GUIDE.md`
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Guides AI coding agents through the EGP-2.0 execution cycle for implementing
AFRP Work Packages.

## 2. Canonical Content Reference

**`03-engineering/300_IMPLEMENTATION_GUIDE.md`** (IMP-001)

## 3. EGP-2.0 Execution Cycle

1. Load Work Package → verify baseline SHA256
2. Verify preconditions from `depends_on` capabilities
3. Receive write lock to `bounded_files` only
4. Execute quality gates: ruff, mypy --strict, pytest, coverage ≥ 80%
5. Run: `afrp validate`, `afrp plan`, `afrp health`, `afrp evidence`
6. Emit ERS-1.0 evidence record
7. Transition to REVIEW_PENDING

## 4. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-02 | Initial import into canonical specification library |
