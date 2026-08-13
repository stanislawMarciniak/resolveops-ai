import math
from pathlib import Path

from app.retrieval.embeddings import (
    EmbeddingProvider,
)
from app.retrieval.models import (
    IndexedPolicyChunk,
    PolicyIndex,
    PolicySearchResult,
)


class PolicyRetriever:
    def __init__(
        self,
        index_path: Path,
        embeddings: EmbeddingProvider,
        top_k: int = 3,
    ) -> None:
        self._index_path = index_path
        self._embeddings = embeddings
        self._top_k = top_k

        self._index: PolicyIndex | None = None

    async def search(
        self,
        query: str,
        customer_id: str | None = None,
    ) -> list[PolicySearchResult]:
        index = self._load_index()

        query_embedding = (
            await self._embeddings.embed_query(
                query
            )
        )

        scored: list[
            tuple[
                float,
                IndexedPolicyChunk,
            ]
        ] = []

        for chunk in index.chunks:
            if not _is_visible_to_customer(
                chunk,
                customer_id,
            ):
                continue

            score = cosine_similarity(
                query_embedding,
                chunk.embedding,
            )

            scored.append(
                (
                    score,
                    chunk,
                )
            )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            PolicySearchResult(
                document_id=chunk.document_id,
                title=chunk.title,
                section=chunk.section,
                content=chunk.content,
                score=score,
            )
            for score, chunk
            in scored[: self._top_k]
        ]

    def _load_index(
        self,
    ) -> PolicyIndex:
        if self._index is not None:
            return self._index

        if not self._index_path.exists():
            raise RuntimeError(
                "Policy index does not exist. "
                "Run the policy indexing command."
            )

        self._index = (
            PolicyIndex.model_validate_json(
                self._index_path.read_text(
                    encoding="utf-8"
                )
            )
        )

        if (
            self._index.embedding_model
            != self._embeddings.model
        ):
            raise RuntimeError(
                "Policy index was created "
                "with a different embedding model."
            )

        if (
            self._index.dimensions
            != self._embeddings.dimensions
        ):
            raise RuntimeError(
                "Policy index uses different "
                "embedding dimensions."
            )

        return self._index


def _is_visible_to_customer(
    chunk: IndexedPolicyChunk,
    customer_id: str | None,
) -> bool:
    if chunk.customer_id is None:
        return True

    if customer_id is None:
        return False

    return (
        chunk.customer_id.upper()
        == customer_id.upper()
    )


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    if len(left) != len(right):
        raise ValueError(
            "Embedding dimensions do not match."
        )

    dot_product = sum(
        a * b
        for a, b in zip(
            left,
            right,
            strict=True,
        )
    )

    left_norm = math.sqrt(
        sum(
            value * value
            for value in left
        )
    )

    right_norm = math.sqrt(
        sum(
            value * value
            for value in right
        )
    )

    if (
        left_norm == 0.0
        or right_norm == 0.0
    ):
        return 0.0

    return (
        dot_product
        / (left_norm * right_norm)
    )