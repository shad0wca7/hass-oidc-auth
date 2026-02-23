"""Regression tests for OIDC flow state lifecycle handling."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from custom_components.auth_oidc.oidc_client import OIDCClient, OIDCTokenResponseInvalid


class _DummyHass:
    """Minimal Home Assistant stub used by the OIDC client tests."""

    def __init__(self) -> None:
        self.loop = asyncio.get_running_loop()


class TestOIDCClientFlowState(unittest.IsolatedAsyncioTestCase):
    """Tests for login state lifecycle reliability."""

    def _create_client(self) -> OIDCClient:
        return OIDCClient(
            hass=_DummyHass(),
            discovery_url="https://issuer/.well-known/openid-configuration",
            client_id="client-id",
            scope="openid profile",
            features={},
            claims={},
            roles={},
            network={},
        )

    async def test_complete_token_flow_consumes_state_once(self) -> None:
        """State must be consumed once to prevent replay and stale transitions."""
        client = self._create_client()
        client.discovery_document = {
            "token_endpoint": "https://issuer/token",
            "issuer": "https://issuer",
        }
        client.flows["state-1"] = {
            "code_verifier": "verifier",
            "nonce": "nonce-1",
            "created_at": 500.0,
        }

        async def _make_token_request(_endpoint: str, _query_params: dict) -> dict:
            return {"id_token": "token", "access_token": "access-token"}

        async def _parse_id_token(_id_token: str) -> dict:
            return {"nonce": "nonce-1", "sub": "abc"}

        async def _parse_user_details(_id_token: dict, _access_token: str) -> dict:
            return {
                "sub": "hash",
                "display_name": "User",
                "username": "user",
                "role": "system-users",
            }

        client._make_token_request = _make_token_request  # type: ignore[method-assign]
        client._parse_id_token = _parse_id_token  # type: ignore[method-assign]
        client.parse_user_details = _parse_user_details  # type: ignore[method-assign]

        with patch(
            "custom_components.auth_oidc.oidc_client.time.monotonic", return_value=500.0
        ):
            result = await client.async_complete_token_flow(
                "https://ha/auth/oidc/callback", "auth-code", "state-1"
            )
        self.assertIsNotNone(result)
        self.assertNotIn("state-1", client.flows)

        with patch(
            "custom_components.auth_oidc.oidc_client.time.monotonic", return_value=500.0
        ):
            replay_result = await client.async_complete_token_flow(
                "https://ha/auth/oidc/callback", "auth-code", "state-1"
            )
        self.assertIsNone(replay_result)

    async def test_generate_authorization_url_prunes_expired_flows(self) -> None:
        """Stale flow state should be removed before adding a new login flow."""
        client = self._create_client()
        client.discovery_document = {
            "authorization_endpoint": "https://issuer/authorize"
        }
        client.flows["expired-state"] = {
            "code_verifier": "old",
            "nonce": "old",
            "created_at": 0.0,
        }
        client.flows["fresh-state"] = {
            "code_verifier": "fresh",
            "nonce": "fresh",
            "created_at": 400.0,
        }

        values = iter(["new-nonce", "new-state", "new-code-verifier"])
        with patch.object(
            client,
            "_generate_random_url_string",
            side_effect=lambda _length=16: next(values),
        ):
            with patch(
                "custom_components.auth_oidc.oidc_client.time.monotonic",
                return_value=500.0,
            ):
                auth_url = await client.async_get_authorization_url(
                    "https://ha/auth/oidc/callback"
                )

        self.assertIsNotNone(auth_url)
        self.assertNotIn("expired-state", client.flows)
        self.assertIn("fresh-state", client.flows)
        self.assertIn("new-state", client.flows)

    async def test_complete_token_flow_removes_state_on_failure(self) -> None:
        """State should still be removed when token exchange fails."""
        client = self._create_client()
        client.discovery_document = {
            "token_endpoint": "https://issuer/token",
            "issuer": "https://issuer",
        }
        client.flows["state-2"] = {
            "code_verifier": "verifier",
            "nonce": "nonce-2",
            "created_at": 500.0,
        }

        async def _make_token_request(_endpoint: str, _query_params: dict) -> dict:
            raise OIDCTokenResponseInvalid

        client._make_token_request = _make_token_request  # type: ignore[method-assign]

        with patch(
            "custom_components.auth_oidc.oidc_client.time.monotonic", return_value=500.0
        ):
            result = await client.async_complete_token_flow(
                "https://ha/auth/oidc/callback", "auth-code", "state-2"
            )

        self.assertIsNone(result)
        self.assertNotIn("state-2", client.flows)
