import json
from pathlib import Path

import pytest
from app.retrieval.indexer import (
    build_policy_index,
)
from app.retrieval.retriever import (
    PolicyRetriever,
)


class FakeEmbeddingProvider:
    @property
    def model(self) -> str:
        return "fake-embedding-model"

    @property
    def dimensions(self) -> int:
        return 3

    async def embed_document(
        self,
        title: str,
        text: str,
    ) -> list[float]:
        return _vector_for(
            f"{title} {text}"
        )

    async def embed_query(
        self,
        query: str,
    ) -> list[float]:
        return _vector_for(query)


def _vector_for(
    text: str,
) -> list[float]:
    lowered = text.lower()

    if "refund" in lowered:
        return [0.0, 1.0, 0.0]

    if (
        "payment" in lowered
        or "invoice" in lowered
    ):
        return [1.0, 0.0, 0.0]

    return [0.0, 0.0, 1.0]


@pytest.mark.asyncio
async def test_policy_retrieval(
    tmp_path: Path,
) -> None:
    documents_dir = (
        tmp_path / "policies"
    )

    documents_dir.mkdir()

    manifest = [
        {
            "document_id": "billing",
            "title": "Billing Policy",
            "file_name": "billing.md",
            "customer_id": None,
        },
        {
            "document_id": "refund",
            "title": "Refund Policy",
            "file_name": "refund.md",
            "customer_id": None,
        },
    ]

    (
        documents_dir
        / "manifest.json"
    ).write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    (
        documents_dir
        / "billing.md"
    ).write_text(
        """
# Billing

## Matching

A payment can be matched to an invoice.
""",
        encoding="utf-8",
    )

    (
        documents_dir
        / "refund.md"
    ).write_text(
        """
# Refund

## Refunds

A refund reverses a payment.
""",
        encoding="utf-8",
    )

    index_path = (
        tmp_path / "index.json"
    )

    embeddings = (
        FakeEmbeddingProvider()
    )

    await build_policy_index(
        documents_dir=documents_dir,
        index_path=index_path,
        embeddings=embeddings,
    )

    retriever = PolicyRetriever(
        index_path=index_path,
        embeddings=embeddings,
        top_k=1,
    )

    results = await retriever.search(
        "How do I match an invoice payment?"
    )

    assert len(results) == 1

    assert (
        results[0].document_id
        == "billing"
    )


@pytest.mark.asyncio
async def test_customer_contract_is_filtered(
    tmp_path: Path,
) -> None:
    documents_dir = (
        tmp_path / "policies"
    )

    documents_dir.mkdir()

    manifest = [
        {
            "document_id": "acme-contract",
            "title": "ACME Contract",
            "file_name": "acme.md",
            "customer_id": "ACME",
        }
    ]

    (
        documents_dir
        / "manifest.json"
    ).write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    (
        documents_dir
        / "acme.md"
    ).write_text(
        """
# ACME Contract

## Payment

ACME payment restoration rule.
""",
        encoding="utf-8",
    )

    index_path = (
        tmp_path / "index.json"
    )

    embeddings = (
        FakeEmbeddingProvider()
    )

    await build_policy_index(
        documents_dir=documents_dir,
        index_path=index_path,
        embeddings=embeddings,
    )

    retriever = PolicyRetriever(
        index_path=index_path,
        embeddings=embeddings,
    )

    results = await retriever.search(
        query="payment",
        customer_id="GLOBEX",
    )

    assert results == []