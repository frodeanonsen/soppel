"""Config flow for Søppelkalender integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "soppel"

MUNICIPALITIES: dict[str, str] = {
    "1103": "Stavanger",
    "1108": "Sandnes",
    "1120": "Klepp",
    "1121": "Time",
    "1122": "Gjesdal",
    "1124": "Sola",
    "1127": "Randaberg",
    "5001": "Trondheim",
}

ADDRESS_SEARCH_URL = (
    "https://www.hentavfall.no/api/renovasjonservice/AddressSearch"
    "?address={address}&municipalityId={municipality_id}"
)


class SoppelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Søppelkalender."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._addresses: list[dict[str, str]] = []
        self._address_map: dict[str, dict[str, str]] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Search for an address."""
        errors: dict[str, str] = {}

        municipality_options = {
            mid: f"{name} ({mid})" for mid, name in MUNICIPALITIES.items()
        }

        if user_input is not None:
            municipality_id = user_input["municipality_id"]
            address = user_input["address"].strip()

            if not address:
                errors["address"] = "no_address"
            else:
                try:
                    session = async_get_clientsession(self.hass)
                    url = ADDRESS_SEARCH_URL.format(
                        address=address, municipality_id=municipality_id
                    )
                    resp = await session.get(url)
                    resp.raise_for_status()
                    data = await resp.json()
                except (aiohttp.ClientError, TimeoutError):
                    errors["base"] = "cannot_connect"
                else:
                    results = data.get("Result", [])
                    if not results:
                        errors["address"] = "no_results"
                    else:
                        self._addresses = results
                        self._address_map = {entry["id"]: entry for entry in results}
                        return await self.async_step_select_address()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("municipality_id", default="1108"): vol.In(
                        municipality_options
                    ),
                    vol.Required("address"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Pick an address from the search results."""
        if user_input is not None:
            selected_id = user_input["address_id"]
            entry = self._address_map[selected_id]

            await self.async_set_unique_id(selected_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{entry['adresse']}, {entry['kommune']}",
                data={
                    "calendar_id": entry["id"],
                    "municipality": entry["kommune"],
                    "gnumber": entry["gNr"],
                    "bnumber": entry["bNr"],
                    "snumber": entry["sNr"],
                    "address": entry["adresse"],
                },
            )

        address_options = {
            entry[
                "id"
            ]: f"{entry['adresse']} (gnr {entry['gNr']}, bnr {entry['bNr']}, snr {entry['sNr']})"
            for entry in self._addresses
        }

        return self.async_show_form(
            step_id="select_address",
            data_schema=vol.Schema(
                {
                    vol.Required("address_id"): vol.In(address_options),
                }
            ),
        )
