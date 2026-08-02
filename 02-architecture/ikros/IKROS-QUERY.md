# IKROS Query Architecture

**Document ID:** AFRP-IKROS-QUERY-1.0.0
**Specification Authority:** SPEC-060 §11 — Query System
**Work Package:** WP-IMP-0041
**Version:** 1.0.0
**Status:** Draft — Awaiting ARB Approval

---

## 1. Overview

The IKROS Query Architecture supports **institutional intelligence queries** — high-level questions about the accumulated research corpus. Queries span the Knowledge Graph, all 13 Registries, and the Memory tiers.

---

## 2. Query Taxonomy

### 2.1 Hypothesis Queries
```
"What hypotheses explain gold during inflation?"
→ MATCH (h:Hypothesis)-[:MOTIVATED_BY_HYP]->(t:EconomicThesis)
  WHERE t.title CONTAINS 'inflation' AND h.status = 'SUPPORTED'
  RETURN h ORDER BY h.posterior_confidence DESC
```

### 2.2 Failure Queries
```
"What experiments rejected mean reversion for XAU/USD?"
→ MATCH (f:Failure)-[:RECORDS_FAILURE_OF]->(cand:AlphaCandidate)
  WHERE cand.strategy_type = 'MEAN_REVERSION'
  RETURN f, cand
```

### 2.3 Feature Queries
```
"What features have been validated for regime detection?"
→ MATCH (feat:Feature)-[:MEMBER_OF]->(ff:FeatureFamily)
  WHERE ff.name = 'REGIME' AND feat.status = 'ACTIVE'
  RETURN feat ORDER BY feat.information_content DESC
```

### 2.4 Evidence Queries
```
"What evidence supports the inflation hedge hypothesis?"
→ MATCH (h:Hypothesis {statement: $stmt})-[:SUPPORTED_BY_HYP]->(v:Validation)
  RETURN h, collect(v) as evidence
```

### 2.5 Contradiction Queries
```
"What contradictory evidence exists for this alpha?"
→ MATCH (a:AlphaCandidate)<-[:CONTRADICTS_OBJ]-(c:ContradictoryEvidence)
  WHERE a.ikros_id = $alpha_id
  RETURN c ORDER BY c.severity DESC
```

### 2.6 Lineage Queries
```
"What data validated this model?"
→ MATCH (m:Model)-[:TRAINED_ON]->(dsv:DatasetVersion)-[:VERSION_OF]->(ds:Dataset)
  WHERE m.ikros_id = $model_id
  RETURN ds, dsv
```

### 2.7 Institutional Knowledge Queries
```
"What constraints must any new gold strategy respect?"
→ MATCH (ko:KnowledgeObject)
  WHERE ko.category = 'CONSTRAINT' AND ko.status = 'INSTITUTIONALISED'
  RETURN ko ORDER BY ko.confidence DESC
```

### 2.8 Research Gap Queries
```
"What research questions remain unanswered?"
→ MATCH (rq:ResearchQuestion)
  WHERE rq.status IN ['OPEN', 'ACTIVE']
  AND NOT (rq)-[:ANSWERED_BY]->()
  RETURN rq ORDER BY rq.created_at
```

---

## 3. Natural Language Query Interface (Future)

Future IKROS versions will support natural language queries translated to graph traversals via an LLM with the IKROS ontology as schema context.

---

## 4. Traceability

| Specification Section | Implemented By |
|----------------------|----------------|
| SPEC-060 §11 Query System | This document |
