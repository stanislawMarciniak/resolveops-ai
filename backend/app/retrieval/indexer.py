from pathlib import Path

from app.retrieval.embeddings import (
    EmbeddingProvider,
)
from app.retrieval.loader import (
    load_policy_chunks,
)
from app.retrieval.models import (
    IndexedPolicyChunk,
    PolicyIndex,
)


async def build_policy_index(
    documents_dir: Path,
    index_path: Path,
    embeddings: EmbeddingProvider,
) -> PolicyIndex:
    chunks = load_policy_chunks(
        documents_dir
    )

    indexed_chunks: list[
        IndexedPolicyChunk
    ] = []

    for chunk in chunks:
        embedding = (
            await embeddings.embed_document(
                title=(
                    f"{chunk.title} — "
                    f"{chunk.section}"
                ),
                text=chunk.content,
            )
        )

        indexed_chunks.append(
            IndexedPolicyChunk(
                **chunk.model_dump(),
                embedding=embedding,
            )
        )

    index = PolicyIndex(
        embedding_model=embeddings.model,
        dimensions=embeddings.dimensions,
        chunks=indexed_chunks,
    )

    index_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    index_path.write_text(
        index.model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )

    return index