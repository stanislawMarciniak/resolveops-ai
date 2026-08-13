import json
from pathlib import Path

from app.retrieval.loader import (
    load_policy_chunks,
)


def test_load_policy_chunks(
    tmp_path: Path,
) -> None:
    manifest = [
        {
            "document_id": "test-policy",
            "title": "Test Policy",
            "file_name": "test.md",
            "customer_id": "ACME",
        }
    ]

    (
        tmp_path / "manifest.json"
    ).write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    (
        tmp_path / "test.md"
    ).write_text(
        """
# Test Policy

## First Rule

First content.

## Second Rule

Second content.
""",
        encoding="utf-8",
    )

    chunks = load_policy_chunks(
        tmp_path
    )

    assert len(chunks) == 2

    assert chunks[0].section == "First Rule"
    assert chunks[0].content == "First content."

    assert chunks[1].section == "Second Rule"

    assert (
        chunks[0].customer_id
        == "ACME"
    )