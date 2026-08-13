from pydantic import Field

from .base import DomainModel
from .enums import AccountStatus


class Customer(DomainModel):
    customer_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)

    billing_customer_id: str | None = Field(
        default=None,
        max_length=64,
    )


class Account(DomainModel):
    account_id: str = Field(min_length=1, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)

    status: AccountStatus
    plan: str = Field(min_length=1, max_length=100)