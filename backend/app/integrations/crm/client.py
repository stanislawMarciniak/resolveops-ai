import httpx
from app.integrations.errors import IntegrationError
from app.models import Account, Customer


class CRMClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_customer(
        self,
        customer_id: str,
    ) -> Customer:
        payload = await self._get(
            f"/customers/{customer_id}"
        )

        return Customer.model_validate(payload)

    async def get_account(
        self,
        customer_id: str,
    ) -> Account:
        payload = await self._get(
            f"/customers/{customer_id}/account"
        )

        return Account.model_validate(payload)

    async def _get(
        self,
        path: str,
    ) -> dict[str, object]:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            ) as client:
                response = await client.get(path)

                response.raise_for_status()

        except httpx.HTTPError as exc:
            raise IntegrationError(
                f"CRM request failed: {exc}"
            ) from exc

        payload = response.json()

        if not isinstance(payload, dict):
            raise IntegrationError(
                "CRM returned an invalid response."
            )

        return payload

    async def restore_account(
        self,
        customer_id: str,
    ) -> Account:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            ) as client:
                response = await client.post(
                    f"/customers/"
                    f"{customer_id}/account/restore"
                )

                response.raise_for_status()

        except httpx.HTTPError as exc:
            raise IntegrationError(
                "CRM account restoration "
                f"failed: {exc}"
            ) from exc

        return Account.model_validate(
            response.json()
        )