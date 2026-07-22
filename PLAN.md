## Solution plan

**Issue:** [Add a content hash to detect unchanged documents and skip re-embedding](https://github.com/ascherj/pathreview/issues/13)

### Understand

The ingestion pipeline already computes a SHA-256-based content hash and includes a shortened version of that hash in each `source_id`. However, duplicate detection does not work because `_check_skip()` does not query the actual `IngestedSource` SQLAlchemy model, and `_record_ingested_source()` only logs the ingestion instead of saving a database record. As a result, when the same README is submitted again, the pipeline parses, chunks, and embeds it a second time rather than returning a skipped result. The expected behavior is for the first ingestion to store metadata about the source and for later ingestion attempts with the same profile, source type, repository, and content hash to skip embedding.

### Map

Expected files and code paths involved:

* `ingestion/pipeline.py`

  * `IngestionPipeline.ingest_readme()`
  * `IngestionPipeline._hash_content()`
  * `IngestionPipeline._check_skip()`
  * `IngestionPipeline._record_ingested_source()`
* `core/models/ingested_source.py`

  * Existing `IngestedSource` model
  * Existing `content_hash` field
* `tests/unit/test_ingestion_pipeline.py`

  * Reproduction test for submitting an identical README twice
  * Additional tests for changed content and database behavior
* Potentially an existing database-session or model-import module if required to avoid circular imports

A database migration is not currently expected because the `IngestedSource` model already contains a `content_hash` column.

### Plan

1. Import and use the actual `IngestedSource` SQLAlchemy model in the ingestion pipeline instead of querying the string `"IngestedSource"`.
2. Compute the full content hash once during ingestion and pass it separately to the duplicate-check and persistence methods.
3. Update `_check_skip()` so it queries for a matching ingested source using the relevant identity fields, including `profile_id`, `source_type`, and `content_hash`.
4. Update `_record_ingested_source()` so it creates an `IngestedSource` record, adds it to the database session, and commits or flushes it according to the project’s existing transaction conventions.
5. Expand `tests/unit/test_ingestion_pipeline.py` so it verifies:

   * the first README ingestion is processed;
   * the second identical README ingestion is skipped;
   * changed README content is processed;
   * the embedding processor is not called for skipped content;
   * ingestion metadata is persisted with the expected hash and chunk count.

### Inputs & outputs

**Inputs:**

* `profile_id`
* repository name
* README content as `str` or `bytes`
* database session
* embedding provider and vector database dependencies

**Outputs and changes:**

* First-time content should be parsed, chunked, embedded, and recorded in `ingested_sources`.
* Identical content submitted again should return an `IngestResult` with:

  * `skipped=True`
  * `chunk_count=0`
  * a clear skip reason
* Changed content should produce a different hash and proceed through embedding normally.
* The database should contain enough metadata to identify previously ingested content.

### Risks & unknowns

* The pipeline may currently rely on transaction ownership outside `_record_ingested_source()`, so calling `commit()` directly could conflict with existing session-management conventions. I need to inspect how other services add and persist SQLAlchemy models before choosing between `add()`, `flush()`, and `commit()`.
* Duplicate matching may need more than `profile_id`, `source_type`, and `content_hash`. README records may also need repository identity such as `source_url`, `filename`, or repository name to avoid incorrectly treating the same content in two different repositories as one source.
* The current `source_id` is not represented as a field on `IngestedSource`, so the skip implementation may need to rely entirely on model fields rather than the generated `source_id`.
* Resume and repository metadata ingestion use the same placeholder helper methods. Changing shared methods could affect those ingestion paths, so tests should verify that the implementation remains compatible with all source types.
* Importing `IngestedSource` directly into `ingestion/pipeline.py` could expose a circular import, which must be checked before implementation.

### Edge cases

* Empty README content
* README content provided as bytes instead of a string
* Same content submitted for two different profiles
* Same content submitted for two different repositories
* Changed content for the same profile and repository
* Database lookup failure
* Database persistence failure after embeddings have already been generated
* Existing legacy records with `content_hash=None`
* Duplicate submissions occurring close together before the first transaction is committed
