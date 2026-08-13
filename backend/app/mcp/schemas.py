from app.models.base import DomainModel


class OperationResult(DomainModel):
    success: bool
    operation: str
    message: str