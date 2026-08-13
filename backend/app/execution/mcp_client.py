from collections.abc import (
    AsyncIterator,
)
from contextlib import (
    asynccontextmanager,
)
from time import perf_counter
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import (
    streamable_http_client,
)
from mcp.types import TextContent
from opentelemetry import trace

from app.observability.instruments import (
    record_tool_call,
)

tracer = trace.get_tracer(
    __name__
)


class MCPToolExecutionError(
    RuntimeError
):
    """Raised when deterministic MCP execution fails."""


@asynccontextmanager
async def open_mcp_session(
    server_url: str,
) -> AsyncIterator[ClientSession]:
    async with streamable_http_client(
        server_url
    ) as (
        read_stream,
        write_stream,
        _,
    ), ClientSession(
        read_stream,
        write_stream,
    ) as session:
        await session.initialize()

        yield session


async def call_tool_json(
    session: ClientSession,
    *,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    started_at = perf_counter()

    with tracer.start_as_current_span(
        f"resolveops.tool.{tool_name}"
    ) as span:
        span.set_attribute(
            "resolveops.tool.name",
            tool_name,
        )

        try:
            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            success = not result.isError

        except Exception:
            latency_ms = (
                perf_counter()
                - started_at
            ) * 1000.0

            record_tool_call(
                tool_name=tool_name,
                latency_ms=latency_ms,
                success=False,
            )

            span.set_attribute(
                "resolveops.tool.success",
                False,
            )

            raise

        latency_ms = (
            perf_counter()
            - started_at
        ) * 1000.0

        record_tool_call(
            tool_name=tool_name,
            latency_ms=latency_ms,
            success=success,
        )

        span.set_attribute(
            "resolveops.tool.success",
            success,
        )

        if result.isError:
            messages = [
                content.text
                for content in result.content
                if isinstance(
                    content,
                    TextContent,
                )
            ]

            message = (
                " ".join(messages)
                or "Unknown MCP tool error."
            )

            raise MCPToolExecutionError(
                f"{tool_name} failed: "
                f"{message}"
            )

        structured = (
            result.structuredContent
        )

        if structured is None:
            raise MCPToolExecutionError(
                f"{tool_name} did not return "
                "structured content."
            )

        return dict(
            structured
        )