# Søppelkalender

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/github/license/frodeanonsen/soppel)](LICENSE)

A Home Assistant custom integration that scrapes waste collection dates from [hentavfall.no](https://www.hentavfall.no) and exposes them as a calendar entity.

## Data source

The integration fetches waste collection dates from [hentavfall.no](https://www.hentavfall.no) for your address. During setup, you select your municipality from a dropdown and then search for your address — no need to manually extract URL parameters.

### Supported municipalities

| ID   | Municipality |
| ---- | ------------ |
| 1103 | Stavanger    |
| 1108 | Sandnes      |
| 1120 | Klepp        |
| 1121 | Time         |
| 1122 | Gjesdal      |
| 1124 | Sola         |
| 1127 | Randaberg    |
| 5001 | Trondheim    |

## Waste types

The following waste types are tracked:

- **Restavfall** — residual waste
- **Matavfall** — food waste
- **Hageavfall** — garden waste
- **Papir** — paper
- **Plastemballasje** — plastic packaging

## Installation

### HACS (recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click the three-dot menu in the top right and select **Custom repositories**.
3. Add `https://github.com/frodeanonsen/soppel` and select **Integration** as the category.
4. Click **Download** on the Søppelkalender card.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration** and search for **Søppelkalender**.

### Manual

1. Copy `custom_components/soppel/` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**.
4. Search for **Søppelkalender** and follow the setup flow:
   1. **Municipality** — select your municipality from the dropdown list.
   2. **Address** — search for and select your address.

The calendar entity (`calendar.soppelkalender`) will appear under **My Calendars**. Data is refreshed once every 24 hours.

## Automation examples

### Notification the evening before pickup

```yaml
automation:
  - alias: "Søppelvarsel"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.soppelkalender
        offset: "-12:00:00"
    action:
      - service: notify.mobile_app
        data:
          message: "Husk å sette ut {{ trigger.calendar_event.summary }} i kveld!"
```

### Conditional check in a template

```yaml
template:
  - sensor:
      - name: "Neste søppeltømming"
        state: "{{ state_attr('calendar.soppelkalender', 'message') }}"
```

## Project structure

```
├── README.md
└── custom_components/soppel/
    ├── manifest.json
    ├── __init__.py
    ├── config_flow.py
    ├── calendar.py
    ├── strings.json
    └── translations/
        └── en.json
```
