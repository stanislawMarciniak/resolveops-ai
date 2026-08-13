from fastapi.testclient import TestClient

from simulator.crm.main import app

client = TestClient(app)


def test_get_acme_customer() -> None:
    response = client.get(
        "/customers/ACME"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["customer_id"] == "ACME"

    assert (
        body["billing_customer_id"]
        == "000018392"
    )


def test_customer_id_is_case_insensitive() -> None:
    response = client.get(
        "/customers/acme"
    )

    assert response.status_code == 200
    assert response.json()["customer_id"] == "ACME"


def test_get_acme_account() -> None:
    response = client.get(
        "/customers/ACME/account"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["customer_id"] == "ACME"
    assert body["status"] == "SUSPENDED"
    assert body["plan"] == "ENTERPRISE"


def test_unknown_customer_returns_404() -> None:
    response = client.get(
        "/customers/DOES-NOT-EXIST"
    )

    assert response.status_code == 404


def test_customer_without_billing_id() -> None:
    response = client.get(
        "/customers/NOBILL"
    )

    assert response.status_code == 200

    assert (
        response.json()["billing_customer_id"]
        is None
    )