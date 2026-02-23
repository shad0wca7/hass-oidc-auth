import asyncio
import unittest
from unittest.mock import AsyncMock

from custom_components.auth_oidc.oidc_client import OIDCClient


class _FakeHass:
    def __init__(self) -> None:
        self.loop = asyncio.get_running_loop()


class OIDCClientGuardrailsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        OIDCClient.flows = {}
        self.client = OIDCClient(
            hass=_FakeHass(),
            discovery_url="https://issuer/.well-known/openid-configuration",
            client_id="client-id",
            scope="openid profile",
            features={},
            claims={},
            roles={},
            network={},
        )
        self.client.discovery_document = {
            "issuer": "https://issuer",
            "token_endpoint": "https://issuer/token",
        }

    async def asyncTearDown(self) -> None:
        OIDCClient.flows = {}

    async def test_state_is_consumed_on_failed_token_response(self) -> None:
        state = "state-1"
        self.client.flows[state] = {"code_verifier": "verifier", "nonce": "nonce-1"}

        self.client._make_token_request = AsyncMock(return_value={})  # type: ignore[attr-defined]

        result = await self.client.async_complete_token_flow(
            "https://ha/redirect", "code", state
        )

        self.assertIsNone(result)
        self.assertNotIn(state, self.client.flows)

    async def test_missing_id_token_returns_none_without_crash(self) -> None:
        state = "state-2"
        self.client.flows[state] = {"code_verifier": "verifier", "nonce": "nonce-2"}

        self.client._make_token_request = AsyncMock(return_value={"access_token": "at"})  # type: ignore[attr-defined]
        self.client._parse_id_token = AsyncMock(
            return_value={"nonce": "nonce-2", "sub": "sub"}
        )  # type: ignore[attr-defined]

        result = await self.client.async_complete_token_flow(
            "https://ha/redirect", "code", state
        )

        self.assertIsNone(result)
        self.client._parse_id_token.assert_not_called()  # type: ignore[attr-defined]

    async def test_missing_access_token_with_userinfo_endpoint_returns_none(
        self,
    ) -> None:
        state = "state-3"
        self.client.flows[state] = {"code_verifier": "verifier", "nonce": "nonce-3"}
        self.client.discovery_document["userinfo_endpoint"] = "https://issuer/userinfo"

        self.client._make_token_request = AsyncMock(
            return_value={"id_token": "id-token"}
        )  # type: ignore[attr-defined]
        self.client._parse_id_token = AsyncMock(
            return_value={"nonce": "nonce-3", "sub": "sub"}
        )  # type: ignore[attr-defined]
        self.client.parse_user_details = AsyncMock(return_value={})  # type: ignore[assignment]

        result = await self.client.async_complete_token_flow(
            "https://ha/redirect", "code", state
        )

        self.assertIsNone(result)
        self.client.parse_user_details.assert_not_called()  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
