from pydantic import BaseModel, ConfigDict


class LegacyBillingModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )


class LegacyInvoice(LegacyBillingModel):
    CUST_NO: str
    INV_NO: str
    STAT_CD: str
    AMT: str
    CURR: str


class LegacyPayment(LegacyBillingModel):
    PAY_ID: str
    CUST_NO: str

    AMT: str
    CURR: str

    STAT_CD: str

    INV_REF: str | None = None
    MATCHED_INV_NO: str | None = None

    RECEIVED_TS: str


class LegacyAccountHold(LegacyBillingModel):
    CUST_NO: str
    HOLD_CD: str
    ACTIVE_FLG: str


class LegacyOperationResponse(LegacyBillingModel):
    SUCCESS_FLG: str

    ERROR_CODE: str | None = None
    ERROR_MSG: str | None = None