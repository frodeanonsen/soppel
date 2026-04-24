"""Calendar platform for Søppelkalender."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from bs4 import BeautifulSoup
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

BASE_URL = (
    "https://www.hentavfall.no/rogaland/sandnes/tommekalender/show"
    "?id={calendar_id}&municipality={municipality}"
    "&gnumber={gnumber}&bnumber={bnumber}&snumber={snumber}"
)

SCAN_INTERVAL = timedelta(hours=24)


def parse_waste_calendar(html: str) -> list[tuple[date, list[str]]]:
    """Parse the waste calendar HTML and return a list of (date, types) tuples."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="waste-calendar")
    if not table:
        return []
    results: list[tuple[date, list[str]]] = []
    for tbody in table.find_all("tbody", attrs={"data-month": True}):
        month_str, year_str = tbody["data-month"].split("-")
        year = int(year_str)
        month = int(month_str)
        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            date_text = cells[0].get_text(strip=True)
            day = int(date_text.split(".")[0])
            types = [img["alt"] for img in cells[1].find_all("img", alt=True)]
            if types:
                results.append((date(year, month, day), types))
    return results


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Søppelkalender calendar from a config entry."""
    session = async_get_clientsession(hass)

    url = BASE_URL.format(
        calendar_id=entry.data["calendar_id"],
        municipality=entry.data["municipality"],
        gnumber=entry.data["gnumber"],
        bnumber=entry.data["bnumber"],
        snumber=entry.data["snumber"],
    )

    async def _async_update_data() -> list[tuple[date, list[str]]]:
        """Fetch and parse the waste calendar."""
        resp = await session.get(url)
        resp.raise_for_status()
        html = await resp.text()
        return parse_waste_calendar(html)

    coordinator: DataUpdateCoordinator[list[tuple[date, list[str]]]] = (
        DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="soppel",
            update_method=_async_update_data,
            update_interval=SCAN_INTERVAL,
        )
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([SoppelCalendar(coordinator, entry)])


class SoppelCalendar(
    CoordinatorEntity[DataUpdateCoordinator[list[tuple[date, list[str]]]]],
    CalendarEntity,
):
    """A calendar entity for waste collection dates."""

    _attr_name = "Søppelkalender"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[list[tuple[date, list[str]]]],
        entry: ConfigEntry,
    ) -> None:
        """Initialize the calendar entity."""
        super().__init__(coordinator)
        self._attr_unique_id = entry.data["calendar_id"]
        self._entry = entry

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        if not self.coordinator.data:
            return None

        today = date.today()
        for pickup_date, waste_types in sorted(
            self.coordinator.data, key=lambda x: x[0]
        ):
            if pickup_date >= today:
                return CalendarEvent(
                    summary=", ".join(waste_types),
                    start=pickup_date,
                    end=pickup_date + timedelta(days=1),
                )
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a date range."""
        if not self.coordinator.data:
            return []

        start = start_date.date() if isinstance(start_date, datetime) else start_date
        end = end_date.date() if isinstance(end_date, datetime) else end_date

        events: list[CalendarEvent] = []
        for pickup_date, waste_types in sorted(
            self.coordinator.data, key=lambda x: x[0]
        ):
            if pickup_date >= start and pickup_date < end:
                events.append(
                    CalendarEvent(
                        summary=", ".join(waste_types),
                        start=pickup_date,
                        end=pickup_date + timedelta(days=1),
                    )
                )
        return events
