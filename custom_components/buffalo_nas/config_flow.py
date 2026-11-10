"""Set up, reconfigure and reauthenticate a Buffalo TeraStation."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .client import BuffaloAuthError, BuffaloError, base_url
from .const import (
    CONF_DEVICE_IDENTIFIER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import make_client
from .models import read_snapshot

PASSWORD = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


class BuffaloNASConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Validate NAS access before saving a connection."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        return await self._connection_form("user", user_input)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        return await self._connection_form(
            "reconfigure", user_input, self._get_reconfigure_entry()
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        return await self._connection_form(
            "reauth_confirm", user_input, self._get_reauth_entry()
        )

    async def _connection_form(self, step_id, user_input, entry=None):
        previous = entry.data if entry else {}
        errors = {}
        if user_input is not None:
            data = {**previous, **user_input}
            try:
                data[CONF_HOST] = str(base_url(data[CONF_HOST]))
            except ValueError:
                errors[CONF_HOST] = "invalid_host"
            else:
                client = make_client(self.hass, data)
                try:
                    await read_snapshot(client)
                    try:
                        identity = await client.portal_info()
                    except BuffaloAuthError:
                        raise
                    except BuffaloError:
                        identity = {}
                except BuffaloAuthError:
                    errors["base"] = "invalid_auth"
                except BuffaloError:
                    errors["base"] = "cannot_connect"
                finally:
                    await client.logout()

            if not errors:
                serial = identity.get("serial_number")
                serial = serial.strip() if isinstance(serial, str) else None
                if entry and entry.unique_id is not None and serial != entry.unique_id:
                    return self.async_abort(reason="unique_id_mismatch")
                for existing in self._async_current_entries():
                    if entry and existing.entry_id == entry.entry_id:
                        continue
                    if serial and existing.unique_id == serial:
                        return self.async_abort(reason="already_configured")
                    try:
                        same_origin = base_url(existing.data[CONF_HOST]) == client.url
                    except (KeyError, ValueError):
                        same_origin = False
                    if same_origin:
                        return self.async_abort(reason="already_configured")
                if entry:
                    if CONF_VERIFY_SSL not in previous:
                        # Keep the old device registry key after moving to a URL.
                        data[CONF_DEVICE_IDENTIFIER] = previous[CONF_HOST]
                    return self.async_update_reload_and_abort(
                        entry, data_updates=data, unique_id=serial or entry.unique_id
                    )

                if serial:
                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_configured()
                name = identity.get("hostname")
                return self.async_create_entry(
                    title=name.strip()
                    if isinstance(name, str) and name.strip()
                    else f"Buffalo NAS ({client.url.host})",
                    data=data,
                )

        fields = {
            vol.Required(
                CONF_USERNAME, default=previous.get(CONF_USERNAME, "admin")
            ): str,
            vol.Required(CONF_PASSWORD): PASSWORD,
        }
        if step_id != "reauth_confirm":
            fields = {
                vol.Required(CONF_HOST): str,
                **fields,
                vol.Required(
                    CONF_VERIFY_SSL,
                    default=previous.get(CONF_VERIFY_SSL, not previous),
                ): bool,
            }
        suggestions = {
            **{key: previous[key] for key in (CONF_HOST,) if key in previous},
            **{
                key: value
                for key, value in (user_input or {}).items()
                if key != CONF_PASSWORD
            },
        }
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(fields), suggestions
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return BuffaloNASOptionsFlow()


class BuffaloNASOptionsFlow(config_entries.OptionsFlow):
    """Adjust how often Home Assistant polls the NAS."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
        )
