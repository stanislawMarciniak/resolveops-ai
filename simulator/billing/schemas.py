from pydantic import BaseModel, ConfigDict


class LegacyModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )


class GetInvoiceRequest(LegacyModel):
    CUST_NO: str
    INV_NO: str


class SearchPaymentsRequest(LegacyModel):
    CUST_NO: str


class MatchPaymentRequest(LegacyModel):
    PAY_ID: str
    INV_NO: str


class RemoveAccountHoldRequest(LegacyModel):
    CUST_NO: str


class LegacyInvoiceResponse(LegacyModel):
    CUST_NO: str
    INV_NO: str
    STAT_CD: str
    AMT: str
    CURR: str


class LegacyPaymentResponse(LegacyModel):
    PAY_ID: str
    CUST_NO: str

    AMT: str
    CURR: str

    STAT_CD: str

    INV_REF: str | None = None
    MATCHED_INV_NO: str | None = None

    RECEIVED_TS: str


class LegacyAccountHoldResponse(LegacyModel):
    CUST_NO: str
    HOLD_CD: str
    ACTIVE_FLG: str


class LegacyOperationResponse(LegacyModel):
    SUCCESS_FLG: str
    ERROR_CODE: str | None = None
    ERROR_MSG: str | None = None