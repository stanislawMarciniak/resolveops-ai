from typing import Protocol

from google import genai
from google.genai import types


class EmbeddingProvider(Protocol):
    @property
    def model(self) -> str:
        ...

    @property
    def dimensions(self) -> int:
        ...

    async def embed_document(
        self,
        title: str,
        text: str,
    ) -> list[float]:
        ...

    async def embed_query(
        self,
        query: str,
    ) -> list[float]:
        ...


class GeminiEmbeddingProvider:
    def __init__(
      self,
      model: str,
      dimensions: int,
      api_key: str,
    ) -> None:
      self._model = model
      self._dimensions = dimensions

      self._client = genai.Client(
          api_key=api_key,
      )

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_document(
        self,
        title: str,
        text: str,
    ) -> list[float]:
        content = (
            f"title: {title} | "
            f"text: {text}"
        )

        return await self._embed(
            content
        )

    async def embed_query(
        self,
        query: str,
    ) -> list[float]:
        content = (
            "task: question answering | "
            f"query: {query}"
        )

        return await self._embed(
            content
        )

    async def _embed(
        self,
        content: str,
    ) -> list[float]:
        response = (
            await self._client.aio.models.embed_content(
                model=self._model,
                contents=content,
                config=types.EmbedContentConfig(
                    output_dimensionality=(
                        self._dimensions
                    )
                ),
            )
        )

        if not response.embeddings:
            raise RuntimeError(
                "Embedding model returned "
                "no embeddings."
            )

        values = response.embeddings[
            0
        ].values

        if values is None:
            raise RuntimeError(
                "Embedding model returned "
                "an empty embedding."
            )

        return [
            float(value)
            for value in values
        ]