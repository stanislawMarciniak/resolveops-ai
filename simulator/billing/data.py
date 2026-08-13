from copy import deepcopy
from typing import Any

INITIAL_INVOICES: dict[str, dict[str, Any]] = {
    "INV8231": {
        "CUST_NO": "000018392",
        "INV_NO": "INV8231",
        "STAT_CD": "OVD",
        "AMT": "4999.00",
        "CURR": "PLN",
    },
    "INV9001": {
        "CUST_NO": "000018401",
        "INV_NO": "INV9001",
        "STAT_CD": "PAID",
        "AMT": "1200.00",
        "CURR": "PLN",
    },
    "INV9002": {
        "CUST_NO": "000018402",
        "INV_NO": "INV9002",
        "STAT_CD": "OPEN",
        "AMT": "850.00",
        "CURR": "EUR",
    },
    "INV9003": {
        "CUST_NO": "000018403",
        "INV_NO": "INV9003",
        "STAT_CD": "OVD",
        "AMT": "2500.00",
        "CURR": "PLN",
    },
}


INITIAL_PAYMENTS: dict[str, dict[str, Any]] = {
    "TX-9912": {
        "PAY_ID": "TX-9912",
        "CUST_NO": "000018392",
        "AMT": "4999.00",
        "CURR": "PLN",
        "STAT_CD": "RCVD",
        "INV_REF": "INV-8231",
        "MATCHED_INV_NO": None,
        "RECEIVED_TS": "2026/08/08 14:31:22",
    },
    "TX-9913": {
        "PAY_ID": "TX-9913",
        "CUST_NO": "000018401",
        "AMT": "1200.00",
        "CURR": "PLN",
        "STAT_CD": "MATCH",
        "INV_REF": "INV-9001",
        "MATCHED_INV_NO": "INV9001",
        "RECEIVED_TS": "2026/08/07 11:10:05",
    },
    "TX-9914": {
        "PAY_ID": "TX-9914",
        "CUST_NO": "000018403",
        "AMT": "2500.00",
        "CURR": "PLN",
        "STAT_CD": "RCVD",
        "INV_REF": "INV-9003",
        "MATCHED_INV_NO": None,
        "RECEIVED_TS": "2026/08/08 09:42:10",
    },
}


INITIAL_ACCOUNT_HOLDS: dict[str, dict[str, Any]] = {
    "000018392": {
        "CUST_NO": "000018392",
        "HOLD_CD": "PAYMENT_OVERDUE",
        "ACTIVE_FLG": "Y",
    },
    "000018403": {
        "CUST_NO": "000018403",
        "HOLD_CD": "PAYMENT_OVERDUE",
        "ACTIVE_FLG": "Y",
    },
}


INVOICES = deepcopy(INITIAL_INVOICES)
PAYMENTS = deepcopy(INITIAL_PAYMENTS)
ACCOUNT_HOLDS = deepcopy(INITIAL_ACCOUNT_HOLDS)


def reset_billing_data() -> None:
    INVOICES.clear()
    INVOICES.update(
        deepcopy(INITIAL_INVOICES)
    )

    PAYMENTS.clear()
    PAYMENTS.update(
        deepcopy(INITIAL_PAYMENTS)
    )

    ACCOUNT_HOLDS.clear()
    ACCOUNT_HOLDS.update(
        deepcopy(INITIAL_ACCOUNT_HOLDS)
    )