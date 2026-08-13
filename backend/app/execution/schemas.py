from pydantic import Field

from app.models.base import DomainModel


class MatchPaymentArguments(DomainModel):
    customer_id: str = Field(
        min_length=1,
        max_length=64,
    )

    payment_id: str = Field(
        min_length=1,
        max_length=64,
    )

    invoice_id: str = Field(
        min_length=1,
        max_length=64,
    )


class RemoveAccountHoldArguments(
    DomainModel
):
    customer_id: str = Field(
        min_length=1,
        max_length=64,
    )