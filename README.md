# Neural Watt Energy Usage for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration that exposes
[Neural Watt](https://neuralwatt.com/) API usage and energy-consumption metrics as
sensors, with native support for the Home Assistant Energy Dashboard.

## Features

- Config-flow based setup (no YAML required)
- API key stored securely, with re-authentication support
- Polls the Neural Watt `/v1/usage/energy` and `/v1/usage/summary` endpoints
- Exposes energy (kWh), request counts, and cost (USD) sensors for multiple
  reporting periods
- Long-term history via Home Assistant statistics backfilled from the API's
  daily array
- Live "today" sensor that resets at midnight for immediate Energy Dashboard
  feedback

## Reporting periods

The integration exposes sensors for the following periods:

- Today
- This month (calendar)
- Last 30 days (rolling)

## Entities per period

- Energy consumed (kWh) — `device_class: energy`
- Requests count
- Requests with energy

In addition, the summary endpoint provides:

- Charged energy (kWh)
- Cost (USD) — `device_class: monetary`
- Accounting method (diagnostic)

## Energy Dashboard integration

The integration takes a two-pronged approach:

1. **Live daily-resetting sensor** — the "energy today" sensor is exposed as a
   `total` with `last_reset` set to local midnight, allowing it to feed the
   Energy Dashboard directly and provide immediate feedback on the current
   day's usage.
2. **Statistics backfill** — the API's `daily[]` array is used to backfill
   Home Assistant long-term statistics, one statistic per day, registered
   with the correct unit. This provides full historical context in the
   Energy Dashboard and statistics graphs beyond what live sensors alone
   can offer.

Cost is exposed as a current-value sensor only (the summary endpoint reports
a single as-of cost, not a daily-resolved series).

## Backfilling history beyond 30 days

The coordinator fetches roughly 30 days of `daily[]` data by default. To
backfill longer history into the long-term statistics, call the
`neuralwatt.backfill_statistics` service:

```yaml
service: neuralwatt.backfill_statistics
data:
  start_date: "2024-01-01"
  end_date: "2024-11-30"
```

The service fetches the requested range from the API, imports each day's
energy as a long-term statistic, and returns `{"ok": true, "imported_days": N}`.

## Configuration

1. Install via HACS (or copy `custom_components/neuralwatt/` into your
   `custom_components/` directory).
2. Restart Home Assistant.
3. Add the "Neural Watt" integration via **Settings → Devices & Services →
   Add Integration**.
4. Enter your Neural Watt API key (found in your Neural Watt account
   dashboard).

## API reference

- `GET https://api.neuralwatt.com/v1/usage/energy` — daily energy array and
  period totals.
- `GET https://api.neuralwatt.com/v1/usage/summary` — consumed vs. charged
  energy, cost, and accounting method.

See [Neural Watt API docs](https://docs.neuralwatt.com/) for full details.

## Polling

The integration polls the API every **1 hour** by default. Energy usage
figures are daily-granularity, so frequent polling is unnecessary; hourly is
a balance between freshness of the "today" sensor and API quota.

## License

MIT
