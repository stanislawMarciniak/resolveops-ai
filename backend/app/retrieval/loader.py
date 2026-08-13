import json
from pathlib import Path

from app.retrieval.models import (
    PolicyChunk,
    PolicyManifestEntry,
)
from pydantic import TypeAdapter

_manifest_adapter = TypeAdapter(
    list[PolicyManifestEntry]
)


def load_manifest(
    documents_dir: Path,
) -> list[PolicyManifestEntry]:
    manifest_path = (
        documents_dir / "manifest.json"
    )

    raw = manifest_path.read_text(
        encoding="utf-8"
    )

    return _manifest_adapter.validate_python(
        json.loads(raw)
    )


def load_policy_chunks(
    documents_dir: Path,
) -> list[PolicyChunk]:
    entries = load_manifest(
        documents_dir
    )

    chunks: list[PolicyChunk] = []

    for entry in entries:
        path = (
            documents_dir
            / entry.file_name
        )

        text = path.read_text(
            encoding="utf-8"
        )

        sections = split_markdown_sections(
            text
        )

        for index, (
            section,
            content,
        ) in enumerate(sections):
            chunks.append(
                PolicyChunk(
                    chunk_id=(
                        f"{entry.document_id}:"
                        f"{index}"
                    ),
                    document_id=(
                        entry.document_id
                    ),
                    title=entry.title,
                    section=section,
                    content=content,
                    customer_id=(
                        entry.customer_id
                    ),
                )
            )

    return chunks


def split_markdown_sections(
    text: str,
) -> list[tuple[str, str]]:
    sections: list[
        tuple[str, str]
    ] = []

    current_section = "Overview"
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if line.startswith("# "):
            # The H1 is the document title and is
            # already stored in manifest metadata.
            continue

        if line.startswith("## "):
            _append_section(
                sections,
                current_section,
                current_lines,
            )

            current_section = line[3:].strip()
            current_lines = []

            continue

        if line:
            current_lines.append(line)

    _append_section(
        sections,
        current_section,
        current_lines,
    )

    return sections


def _append_section(
    sections: list[tuple[str, str]],
    title: str,
    lines: list[str],
) -> None:
    content = "\n".join(lines).strip()

    if not content:
        return

    sections.append(
        (
            title,
            content,
        )
    )