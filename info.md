# Neural Watt

A Home Assistant integration for [Neural Watt](https://neuralwatt.com/), exposing
API energy-usage and cost metrics as sensors with full Energy Dashboard support.

## What it gives you

- **Live "today" energy sensor** that resets at local midnight — feeds the
  Energy Dashboard directly for same-day feedback.
- **Long-term statistics** backfilled from Neural Watt's daily array, so the
  Energy Dashboard and statistics graphs have full history beyond what live
  sensors alone can show.
- **Period sensors** for *today*, *this month*, and *last 30 days* covering
  energy consumed (kWh), request count, and requests with energy.
- **Summary sensors** for charged energy (kWh), total cost (USD), and accounting
  method (token vs. energy) from the `/v1/usage/summary` endpoint.

## Install

1. Install via HACS as a custom repository, or copy
   `custom_components/neuralwatt/` into your HA `custom_components/` directory.
2. Restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → Neural Watt**.
4. Enter your Neural Watt API key (found in your Neural Watt account dashboard).

## Energy Dashboard setup

To use the integration with the Energy Dashboard, configure the Energy Dashboard
and add the **Energy today** sensor as an electricity-consuming device. Long-term
history comes from the backfilled `neuralwatt:energy_consumed_daily` statistic.

## Polling

The integration polls the API every hour by default. Usage data is
daily-granularity, so frequent polling is unnecessary.
