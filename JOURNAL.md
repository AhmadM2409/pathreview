## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/13

**Issue title:** Add a content hash to detect unchanged documents and skip re-embedding

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**

The ingestion pipeline currently reprocesses and re-embeds a README even when the submitted content has not changed. This creates unnecessary embedding work and may result in avoidable API usage. The issue affects the ingestion pipeline and the `IngestedSource` model, which need a reliable way to store and compare a content hash. A successful fix will detect identical content and skip the embedding step while continuing normal processing when the document has changed.

**Selection notes — “Is this issue right for me?” checklist:**

The issue has a defined outcome, identifies the main files involved, and is estimated at 4–6 hours. It requires Python, database-model, ingestion-pipeline, and testing work, which are within my current experience. The scope appears limited to hashing submitted content, recording the hash, comparing it during later ingestion attempts, and verifying the behavior with tests. I understand that a database migration may be needed if the model does not already contain a suitable content-hash field.

**Branch name:** feat/13-content-hash-skip-reembedding

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
