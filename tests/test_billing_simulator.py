import pytest
from fastapi.testclient import TestClient

from simulator.billing.data import (
    reset_billing_data,
)
from simulator.billing.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_data() -> None:
    reset_billing_data()


def test_get_acme_invoice() -> None:
    response = client.post(
        "/GetInvoice",
        json={
            "CUST_NO": "000018392",
            "INV_NO": "INV8231",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "CUST_NO": "000018392",
        "INV_NO": "INV8231",
        "STAT_CD": "OVD",
        "AMT": "4999.00",
        "CURR": "PLN",
    }


def test_invoice_business_error_uses_http_200() -> None:
    response = client.post(
        "/GetInvoice",
        json={
            "CUST_NO": "000018392",
            "INV_NO": "UNKNOWN",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["SUCCESS_FLG"] == "N"
    assert body["ERROR_CODE"] == "INV_404"


def test_search_acme_payments() -> None:
    response = client.post(
        "/SearchPayments",
        json={
            "CUST_NO": "000018392",
        },
    )

    assert response.status_code == 200

    payments = response.json()

    assert len(payments) == 1

    assert (
        payments[0]["PAY_ID"]
        == "TX-9912"
    )

    assert (
        payments[0]["INV_REF"]
        == "INV-8231"
    )


def test_match_payment_changes_invoice_status() -> None:
    match_response = client.post(
        "/MatchPayment",
        json={
            "PAY_ID": "TX-9912",
            "INV_NO": "INV8231",
        },
    )

    assert match_response.json()[
        "SUCCESS_FLG"
    ] == "Y"

    invoice_response = client.post(
        "/GetInvoice",
        json={
            "CUST_NO": "000018392",
            "INV_NO": "INV8231",
        },
    )

    assert (
        invoice_response.json()["STAT_CD"]
        == "PAID"
    )


def test_remove_account_hold() -> None:
    response = client.post(
        "/RemoveAccountHold",
        json={
            "CUST_NO": "000018392",
        },
    )

    assert response.status_code == 200

    assert response.json()[
        "SUCCESS_FLG"
    ] == "Y"


def test_payment_cannot_match_other_customer_invoice() -> None:
    response = client.post(
        "/MatchPayment",
        json={
            "PAY_ID": "TX-9912",
            "INV_NO": "INV9003",
        },
    )

    assert response.json()[
        "ERROR_CODE"
    ] == "CUST_MISMATCH"