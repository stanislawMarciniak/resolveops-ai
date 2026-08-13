from typing import Any

import httpx

from app.integrations.billing.adapter import (
    parse_legacy_account_hold,
    parse_legacy_invoice_lookup,
    parse_legacy_payment_lookup,
    to_legacy_invoice_id,
)
from app.integrations.billing.results import (
    InvoiceLookupResult,
    PaymentLookupResult,
)
from app.integrations.billing.schemas import (
    LegacyAccountHold,
    LegacyInvoice,
    LegacyOperationResponse,
    LegacyPayment,
)
from app.integrations.errors import IntegrationError
from app.models import (
    AccountHold,
    Invoice,
    Payment,
)


class BillingClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_invoice(
        self,
        billing_customer_id: str,
        invoice_id: str,
    ) -> Invoice:
        result = (
            await self
            .get_invoice_with_provenance(
                billing_customer_id,
                invoice_id,
            )
        )

        return result.invoice

    async def get_invoice_with_provenance(
        self,
        billing_customer_id: str,
        invoice_id: str,
    ) -> InvoiceLookupResult:
        payload = await self._post(
            "/GetInvoice",
            {
                "CUST_NO": billing_customer_id,
                "INV_NO": to_legacy_invoice_id(
                    invoice_id
                ),
            },
        )

        self._raise_for_business_error(
            payload
        )

        raw = LegacyInvoice.model_validate(
            payload
        )

        return parse_legacy_invoice_lookup(
            raw
        )

    async def search_payments(
        self,
        billing_customer_id: str,
    ) -> list[Payment]:
        results = (
            await self
            .search_payments_with_provenance(
                billing_customer_id
            )
        )

        return [
            result.payment
            for result in results
        ]

    async def search_payments_with_provenance(
        self,
        billing_customer_id: str,
    ) -> list[PaymentLookupResult]:
        payload = await self._post(
            "/SearchPayments",
            {
                "CUST_NO": billing_customer_id,
            },
        )

        if not isinstance(payload, list):
            raise IntegrationError(
                "Billing SearchPayments returned "
                "an invalid response."
            )

        results: list[
            PaymentLookupResult
        ] = []

        for item in payload:
            raw = LegacyPayment.model_validate(
                item
            )

            results.append(
                parse_legacy_payment_lookup(
                    raw
                )
            )

        return results

    async def get_account_hold(
        self,
        billing_customer_id: str,
    ) -> AccountHold:
        hold = (
            await self
            .get_account_hold_optional(
                billing_customer_id
            )
        )

        if hold is None:
            raise IntegrationError(
                "Customer does not have an "
                "active billing hold.",
                code="HOLD_404",
            )

        return hold

    async def get_account_hold_optional(
        self,
        billing_customer_id: str,
    ) -> AccountHold | None:
        payload = await self._post(
            "/GetAccountHold",
            {
                "CUST_NO": billing_customer_id,
            },
        )

        if (
            isinstance(payload, dict)
            and payload.get(
                "SUCCESS_FLG"
            )
            == "N"
        ):
            result = (
                LegacyOperationResponse
                .model_validate(payload)
            )

            if (
                result.ERROR_CODE
                == "HOLD_404"
            ):
                return None

            raise IntegrationError(
                "Legacy billing error "
                f"{result.ERROR_CODE}: "
                f"{result.ERROR_MSG}",
                code=result.ERROR_CODE,
            )

        raw = (
            LegacyAccountHold
            .model_validate(payload)
        )

        return parse_legacy_account_hold(
            raw
        )

    async def match_payment(
        self,
        payment_id: str,
        invoice_id: str,
    ) -> None:
        payload = await self._post(
            "/MatchPayment",
            {
                "PAY_ID": payment_id,
                "INV_NO": (
                    to_legacy_invoice_id(
                        invoice_id
                    )
                ),
            },
        )

        self._require_success(
            payload
        )

    async def remove_account_hold(
        self,
        billing_customer_id: str,
    ) -> None:
        payload = await self._post(
            "/RemoveAccountHold",
            {
                "CUST_NO": (
                    billing_customer_id
                ),
            },
        )

        self._require_success(
            payload
        )

    async def _post(
        self,
        path: str,
        payload: dict[str, str],
    ) -> Any:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            ) as client:
                response = await client.post(
                    path,
                    json=payload,
                )

                response.raise_for_status()

        except httpx.HTTPError as exc:
            raise IntegrationError(
                "Billing request failed: "
                f"{exc}"
            ) from exc

        return response.json()

    @staticmethod
    def _raise_for_business_error(
        payload: Any,
    ) -> None:
        if not isinstance(payload, dict):
            return

        if "SUCCESS_FLG" not in payload:
            return

        result = (
            LegacyOperationResponse
            .model_validate(payload)
        )

        if result.SUCCESS_FLG != "Y":
            raise IntegrationError(
                "Legacy billing error "
                f"{result.ERROR_CODE}: "
                f"{result.ERROR_MSG}",
                code=result.ERROR_CODE,
            )

    @staticmethod
    def _require_success(
        payload: Any,
    ) -> None:
        if not isinstance(payload, dict):
            raise IntegrationError(
                "Legacy billing returned "
                "an invalid operation response."
            )

        result = (
            LegacyOperationResponse
            .model_validate(payload)
        )

        if result.SUCCESS_FLG != "Y":
            raise IntegrationError(
                "Legacy billing error "
                f"{result.ERROR_CODE}: "
                f"{result.ERROR_MSG}",
                code=result.ERROR_CODE,
            )