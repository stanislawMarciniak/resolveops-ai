from app.models.base import DomainModel
from pydantic import Field


class PolicyManifestEntry(DomainModel):
    document_id: str = Field(
        min_length=1,
        max_length=100,
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    file_name: str = Field(
        min_length=1,
        max_length=200,
    )

    customer_id: str | None = Field(
        default=None,
        max_length=64,
    )


class PolicyChunk(DomainModel):
    chunk_id: str = Field(
        min_length=1,
        max_length=150,
    )

    document_id: str = Field(
        min_length=1,
        max_length=100,
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    section: str = Field(
        min_length=1,
        max_length=200,
    )

    content: str = Field(
        min_length=1,
    )

    customer_id: str | None = Field(
        default=None,
        max_length=64,
    )


class IndexedPolicyChunk(PolicyChunk):
    embedding: list[float] = Field(
        min_length=1,
    )


class PolicyIndex(DomainModel):
    embedding_model: str

    dimensions: int = Field(
        gt=0,
    )

    chunks: list[IndexedPolicyChunk]


class PolicySearchResult(DomainModel):
    document_id: str
    title: str
    section: str
    content: str

    score: float = Field(
        ge=-1.0,
        le=1.0,
    )