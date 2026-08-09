"""Config flow for Hermes Assistant."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, override
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_MAX_RESPONSE_CHARS,
    CONF_MEMORY_SCOPE,
    CONF_PROMPT,
    CONF_TIMEOUT,
    DEFAULT_MAX_RESPONSE_CHARS,
    DEFAULT_MEMORY_SCOPE,
    DEFAULT_PROMPT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MEMORY_SCOPES,
)
from .gateway import (
    HermesAuthenticationError,
    HermesGatewayClient,
    HermesGatewayError,
    normalize_base_url,
)


def _connection_schema(suggested: Mapping[str, Any] | None = None) -> vol.Schema:
    suggested = suggested or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_BASE_URL,
                default=suggested.get(CONF_BASE_URL, "http://hermes:8642"),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
            vol.Required(CONF_API_KEY): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
        }
    )


def _reconfigure_schema(suggested: Mapping[str, Any]) -> vol.Schema:
    """Return a connection schema that can retain the stored API key."""
    return vol.Schema(
        {
            vol.Required(
                CONF_BASE_URL,
                description={"suggested_value": suggested[CONF_BASE_URL]},
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
            vol.Optional(CONF_API_KEY): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
        }
    )


class HermesAssistantConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a Hermes Agent gateway."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                base_url = normalize_base_url(user_input[CONF_BASE_URL])
                await self._async_validate(base_url, user_input[CONF_API_KEY])
            except ValueError:
                errors["base"] = "invalid_url"
            except HermesAuthenticationError:
                errors["base"] = "invalid_auth"
            except HermesGatewayError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(base_url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=urlsplit(base_url).hostname or base_url,
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_API_KEY: user_input[CONF_API_KEY],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._async_validate(
                    entry.data[CONF_BASE_URL], user_input[CONF_API_KEY]
                )
            except HermesAuthenticationError:
                errors["base"] = "invalid_auth"
            except HermesGatewayError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the gateway address or credentials."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY) or entry.data[CONF_API_KEY]
            try:
                base_url = normalize_base_url(user_input[CONF_BASE_URL])
                await self._async_validate(base_url, api_key)
            except ValueError:
                errors["base"] = "invalid_url"
            except HermesAuthenticationError:
                errors["base"] = "invalid_auth"
            except HermesGatewayError:
                errors["base"] = "cannot_connect"
            else:
                if any(
                    configured_entry.entry_id != entry.entry_id
                    and configured_entry.unique_id == base_url
                    for configured_entry in self.hass.config_entries.async_entries(
                        DOMAIN
                    )
                ):
                    return self.async_abort(reason="already_configured")
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=base_url,
                    title=urlsplit(base_url).hostname or base_url,
                    data_updates={
                        CONF_BASE_URL: base_url,
                        CONF_API_KEY: api_key,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_reconfigure_schema(entry.data),
            errors=errors,
        )

    async def _async_validate(self, base_url: str, api_key: str) -> None:
        client = HermesGatewayClient(
            async_get_clientsession(self.hass),
            base_url,
            api_key,
            timeout=DEFAULT_TIMEOUT,
        )
        await client.async_validate()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> OptionsFlow:
        return HermesAssistantOptionsFlow()


class HermesAssistantOptionsFlow(OptionsFlow):
    """Configure voice behavior and memory isolation."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PROMPT, default=current.get(CONF_PROMPT, DEFAULT_PROMPT)
                    ): TextSelector(TextSelectorConfig(multiline=True)),
                    vol.Required(
                        CONF_TIMEOUT, default=current.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=10, max=600, step=5, mode=NumberSelectorMode.BOX
                        )
                    ),
                    vol.Required(
                        CONF_MAX_RESPONSE_CHARS,
                        default=current.get(
                            CONF_MAX_RESPONSE_CHARS, DEFAULT_MAX_RESPONSE_CHARS
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=100, max=5000, step=100, mode=NumberSelectorMode.BOX
                        )
                    ),
                    vol.Required(
                        CONF_MEMORY_SCOPE,
                        default=current.get(CONF_MEMORY_SCOPE, DEFAULT_MEMORY_SCOPE),
                    ): SelectSelector(SelectSelectorConfig(options=MEMORY_SCOPES)),
                }
            ),
        )
