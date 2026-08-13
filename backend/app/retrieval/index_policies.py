import asyncio

from app.config import get_settings
from app.retrieval.embeddings import (
    GeminiEmbeddingProvider,
)
from app.retrieval.indexer import (
    build_policy_index,
)


async def main() -> None:
    settings = get_settings()

    embeddings = GeminiEmbeddingProvider(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        api_key=settings.google_api_key,
    )

    index = await build_policy_index(
        documents_dir=(
            settings.policy_documents_dir
        ),
        index_path=(
            settings.policy_index_path
        ),
        embeddings=embeddings,
    )

    print(
        "Policy index created:"
        f" {len(index.chunks)} chunks"
    )


if __name__ == "__main__":
    asyncio.run(main())