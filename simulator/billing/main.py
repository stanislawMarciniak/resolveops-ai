from fastapi import FastAPI
from pydantic import BaseModel

from simulator.billing.data import (
    ACCOUNT_HOLDS,
    INVOICES,
    PAYMENTS,
)
from simulator.billing.schemas import (
    GetInvoiceRequest,
    LegacyAccountHoldResponse,
    LegacyInvoiceResponse,
    LegacyOperationResponse,
    LegacyPaymentResponse,
    MatchPaymentRequest,
    RemoveAccountHoldRequest,
    SearchPaymentsRequest,
)


class HealthResponse(BaseModel):
    status: str
    service: str


app = FastAPI(
    title="ResolveOps Legacy Billing Simulator",
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
        service="legacy-billing-simulator",
    )


@app.post(
    "/GetInvoice",
    response_model=(
        LegacyInvoiceResponse
        | LegacyOperationResponse
    ),
    tags=["billing"],
)
async def get_invoice(
    request: GetInvoiceRequest,
) -> (
    LegacyInvoiceResponse
    | LegacyOperationResponse
):
    invoice = INVOICES.get(
        request.INV_NO,
    )

    if invoice is None:
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="INV_404",
            ERROR_MSG="Invoice does not exist.",
        )

    if invoice["CUST_NO"] != request.CUST_NO:
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="CUST_MISMATCH",
            ERROR_MSG=(
                "Invoice belongs to another customer."
            ),
        )

    return LegacyInvoiceResponse(
        **invoice,
    )


@app.post(
    "/SearchPayments",
    response_model=list[LegacyPaymentResponse],
    tags=["billing"],
)
async def search_payments(
    request: SearchPaymentsRequest,
) -> list[LegacyPaymentResponse]:
    matching_payments = [
        LegacyPaymentResponse(**payment)
        for payment in PAYMENTS.values()
        if payment["CUST_NO"] == request.CUST_NO
    ]

    return matching_payments


@app.post(
    "/GetAccountHold",
    response_model=(
        LegacyAccountHoldResponse
        | LegacyOperationResponse
    ),
    tags=["billing"],
)
async def get_account_hold(
    request: SearchPaymentsRequest,
) -> (
    LegacyAccountHoldResponse
    | LegacyOperationResponse
):
    hold = ACCOUNT_HOLDS.get(
        request.CUST_NO,
    )

    if hold is None:
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="HOLD_404",
            ERROR_MSG="No active hold.",
        )

    return LegacyAccountHoldResponse(
        **hold,
    )


@app.post(
    "/MatchPayment",
    response_model=LegacyOperationResponse,
    tags=["billing"],
)
async def match_payment(
    request: MatchPaymentRequest,
) -> LegacyOperationResponse:
    payment = PAYMENTS.get(
        request.PAY_ID,
    )

    if payment is None:
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="PAY_404",
            ERROR_MSG="Payment does not exist.",
        )

    invoice = INVOICES.get(
        request.INV_NO,
    )

    if invoice is None:
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="INV_404",
            ERROR_MSG="Invoice does not exist.",
        )

    if payment["CUST_NO"] != invoice["CUST_NO"]:
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="CUST_MISMATCH",
            ERROR_MSG=(
                "Payment and invoice belong "
                "to different customers."
            ),
        )

    if payment["AMT"] != invoice["AMT"]:
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="AMOUNT_MISMATCH",
            ERROR_MSG=(
                "Payment amount does not match invoice."
            ),
        )

    payment["MATCHED_INV_NO"] = request.INV_NO
    payment["STAT_CD"] = "MATCH"

    invoice["STAT_CD"] = "PAID"

    return LegacyOperationResponse(
        SUCCESS_FLG="Y",
    )


@app.post(
    "/RemoveAccountHold",
    response_model=LegacyOperationResponse,
    tags=["billing"],
)
async def remove_account_hold(
    request: RemoveAccountHoldRequest,
) -> LegacyOperationResponse:
    hold = ACCOUNT_HOLDS.get(
        request.CUST_NO,
    )

    if hold is None:
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="HOLD_404",
            ERROR_MSG="No active hold.",
        )

    if hold["ACTIVE_FLG"] != "Y":
        return LegacyOperationResponse(
            SUCCESS_FLG="N",
            ERROR_CODE="HOLD_ALREADY_REMOVED",
            ERROR_MSG="Hold is already inactive.",
        )

    hold["ACTIVE_FLG"] = "N"

    return LegacyOperationResponse(
        SUCCESS_FLG="Y",
    )