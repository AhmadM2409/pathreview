"""Reproduction tests for ingestion pipeline deduplication."""

from unittest.mock import MagicMock

import pytest

from ingestion.pipeline import IngestionPipeline


@pytest.mark.unit
def test_identical_readme_is_not_embedded_twice(sample_readme_text: str) -> None:
    """
    Reproduce issue #13.

    Submitting the same README twice should skip the second embedding,
    but the current pipeline processes it twice because ingestion
    metadata is not actually persisted.
    """
    vector_db = MagicMock()
    db_session = MagicMock()
    db_session.query.return_value.filter_by.return_value.first.return_value = None
    embedding_provider = MagicMock()

    pipeline = IngestionPipeline(
        vector_db=vector_db,
        db_session=db_session,
        embedding_provider=embedding_provider,
    )

    # Isolate the test from parsing and chunking details.
    parse_result = MagicMock()
    parse_result.text = sample_readme_text
    parse_result.metadata = {
        "heading_count": 2,
        "word_count": 20,
    }

    pipeline.readme_parser.parse = MagicMock(return_value=parse_result)  # type: ignore[method-assign]
    pipeline.strategy_selector.chunk = MagicMock(return_value=[MagicMock()])  # type: ignore[method-assign]
    pipeline.batch_processor.process = MagicMock()  # type: ignore[method-assign]

    first_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )

    second_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )

    assert first_result.skipped is False
    assert second_result.skipped is True
    assert pipeline.batch_processor.process.call_count == 1
