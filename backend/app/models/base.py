from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Base class for ResolveOps domain models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )