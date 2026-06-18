"""Constants for the Neural Watt integration."""

DOMAIN = "neuralwatt"

API_BASE_URL = "https://api.neuralwatt.com/v1"
API_ENERGY_ENDPOINT = "/usage/energy"
API_SUMMARY_ENDPOINT = "/usage/summary"

CONF_API_KEY = "api_key"

DEFAULT_POLL_INTERVAL_SECONDS = 3600

PERIOD_TODAY = "today"
PERIOD_THIS_MONTH = "this_month"
PERIOD_LAST_30_DAYS = "last_30_days"

ATTR_PERIOD_START = "period_start"
ATTR_PERIOD_END = "period_end"
ATTR_REQUESTS = "requests"
ATTR_REQUESTS_WITH_ENERGY = "requests_with_energy"
ATTR_ENERGY_KWH = "energy_kwh"
ATTR_ENERGY_JOULES = "energy_joules"
ATTR_ENERGY_KWH_CONSUMED = "energy_kwh_consumed"
ATTR_ENERGY_KWH_CHARGED = "energy_kwh_charged"
ATTR_TOTAL_COST_USD = "total_cost_usd"
ATTR_ACCOUNTING_METHOD = "accounting_method"
ATTR_DAILY = "daily"
ATTR_DATE = "date"

ACCOUNTING_METHOD_TOKEN = "token"
ACCOUNTING_METHOD_ENERGY = "energy"

SENSOR_TYPE_ENERGY = "energy"
SENSOR_TYPE_REQUESTS = "requests"
SENSOR_TYPE_REQUESTS_WITH_ENERGY = "requests_with_energy"
SENSOR_TYPE_CHARGED_KWH = "charged_kwh"
SENSOR_TYPE_COST = "cost"
SENSOR_TYPE_ACCOUNTING_METHOD = "accounting_method"
