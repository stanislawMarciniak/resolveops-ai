from app.models import Account, Customer
from app.models.enums import AccountStatus
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from simulator.crm.data import ACCOUNTS, CUSTOMERS


class HealthResponse(BaseModel):
    status: str
    service: str


app = FastAPI(
    title="ResolveOps CRM Simulator",
    version="0.1.0",
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="crm-simulator",
    )


@app.get(
    "/customers/{customer_id}",
    response_model=Customer,
    tags=["customers"],
)
async def get_customer(
    customer_id: str,
) -> Customer:
    normalized_id = customer_id.upper()

    customer = CUSTOMERS.get(normalized_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return customer


@app.get(
    "/customers/{customer_id}/account",
    response_model=Account,
    tags=["customers"],
)
async def get_account(
    customer_id: str,
) -> Account:
    normalized_id = customer_id.upper()

    account = ACCOUNTS.get(normalized_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    return account

@app.post(
    "/customers/{customer_id}/account/restore",
    response_model=Account,
)
async def restore_account(
    customer_id: str,
) -> Account:
    key = customer_id.strip().upper()

    account = ACCOUNTS.get(key)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    restored_account = account.model_copy(
        update={
            "status": AccountStatus.ACTIVE,
        }
    )

    ACCOUNTS[key] = restored_account

    return restored_account