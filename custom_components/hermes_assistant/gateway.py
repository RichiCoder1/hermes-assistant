"""HTTP client for the public Hermes Agent Gateway API."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import aiohttp


class HermesGatewayError(Exception):
    """Base gateway error."""


class HermesAuthenticationError(HermesGatewayError):
    """The gateway rejected the API key."""


class HermesConnectionError(HermesGatewayError):
    """The gateway could not be reached."""


class HermesProtocolError(HermesGatewayError):
    """The gateway response did not match its public API contract."""


@dataclass(frozen=True, slots=True)
class GatewayCapabilities:
    """Validated subset of Hermes gateway capabilities."""

    model: str
    session_id_header: str | None
    session_key_header: str | None


def normalize_base_url(value: str) -> str:
    """Return a validated gateway base URL without a trailing slash."""
    candidate = value.strip().rstrip("/")
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("A complete http:// or https:// URL is required")
    if parsed.username or parsed.password:
        raise ValueError("Credentials must not be embedded in the base URL")
    if parsed.query or parsed.fragment:
        raise ValueError("The base URL cannot contain a query or fragment")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


class HermesGatewayClient:
    """Small asynchronous client for Hermes's stable API surface."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        api_key: str,
        *,
        timeout: int,
    ) -> None:
        if not api_key.strip():
            raise ValueError("An API key is required")
        self._session = session
        self.base_url = normalize_base_url(base_url)
        self._api_key = api_key.strip()
        self.timeout = timeout
        self.capabilities: GatewayCapabilities | None = None

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }

    async def async_validate(self) -> GatewayCapabilities:
        """Authenticate and verify that the endpoint is Hermes Agent."""
        payload = await self._request_json("GET", "/v1/capabilities")
        if (
            payload.get("object") != "hermes.api_server.capabilities"
            or payload.get("platform") != "hermes-agent"
            or not isinstance(payload.get("model"), str)
            or not payload["model"].strip()
        ):
            raise HermesProtocolError("Endpoint is not a Hermes Agent gateway")

        features = payload.get("features")
        auth = payload.get("auth")
        if (
            not isinstance(auth, dict)
            or auth.get("type") != "bearer"
            or auth.get("required") is not True
        ):
            raise HermesProtocolError(
                "Hermes gateway must require bearer authentication"
            )
        if (
            not isinstance(features, dict)
            or features.get("chat_completions") is not True
        ):
            raise HermesProtocolError(
                "Hermes gateway does not advertise chat completions"
            )

        capabilities = GatewayCapabilities(
            model=payload["model"].strip(),
            session_id_header=_optional_header(
                features.get("session_continuity_header")
            ),
            session_key_header=_optional_header(features.get("session_key_header")),
        )
        self.capabilities = capabilities
        return capabilities

    async def async_complete(
        self,
        messages: list[dict[str, str]],
        *,
        session_id: str,
        session_key: str,
    ) -> str:
        """Send a complete stateless transcript and return spoken text."""
        capabilities = self.capabilities or await self.async_validate()
        headers: dict[str, str] = {}
        if capabilities.session_id_header:
            headers[capabilities.session_id_header] = session_id
        if capabilities.session_key_header:
            headers[capabilities.session_key_header] = session_key

        payload = await self._request_json(
            "POST",
            "/v1/chat/completions",
            headers=headers,
            json={"model": capabilities.model, "messages": messages, "stream": False},
        )
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as err:
            raise HermesProtocolError(
                "Hermes returned an invalid chat completion"
            ) from err
        if not isinstance(content, str) or not content.strip():
            raise HermesProtocolError("Hermes returned an empty response")
        return content.strip()

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_headers = {**self._headers, **(headers or {})}
        try:
            async with asyncio.timeout(self.timeout):
                async with self._session.request(
                    method,
                    self._url(path),
                    headers=request_headers,
                    json=json,
                ) as response:
                    if response.status in {401, 403}:
                        raise HermesAuthenticationError("Hermes rejected the API key")
                    if response.status >= 400:
                        raise HermesConnectionError(
                            f"Hermes returned HTTP {response.status}"
                        )
                    try:
                        payload = await response.json(content_type=None)
                    except (ValueError, aiohttp.ContentTypeError) as err:
                        raise HermesProtocolError(
                            "Hermes returned invalid JSON"
                        ) from err
        except HermesGatewayError:
            raise
        except (TimeoutError, aiohttp.ClientError) as err:
            raise HermesConnectionError("Unable to reach Hermes") from err

        if not isinstance(payload, dict):
            raise HermesProtocolError("Hermes returned a non-object JSON response")
        return payload


def _optional_header(value: object) -> str | None:
    """Accept only a simple advertised HTTP header name."""
    if not isinstance(value, str) or not value:
        return None
    if not all(character.isalnum() or character == "-" for character in value):
        return None
    return value
