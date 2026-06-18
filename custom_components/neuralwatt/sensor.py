"""Neural Watt sensor entities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_USD, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACCOUNTING_METHOD,
    ATTR_ENERGY_KWH_CHARGED,
    ATTR_TOTAL_COST_USD,
    DOMAIN,
    PERIOD_LAST_30_DAYS,
    PERIOD_THIS_MONTH,
    PERIOD_TODAY,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_REQUESTS,
    SENSOR_TYPE_REQUESTS_WITH_ENERGY,
)
from .coordinator import NeuralWattDataUpdateCoordinator

_DEVICE_IDENT = "neuralwatt"
DEVICE_INFO = DeviceInfo(
    identifiers={(DOMAIN, _DEVICE_IDENT)},
    name="Neural Watt",
    manufacturer="Neural Watt",
    model="Energy & Usage API",
)


@dataclass(frozen=True, kw_only=True)
class NeuralWattPeriodSensorDescription(SensorEntityDescription):
    sensor_type: str
    period: str


@dataclass(frozen=True, kw_only=True)
class NeuralWattSummarySensorDescription(SensorEntityDescription):
    summary_field: str


def _last_reset_from_period(
    period_data: dict[str, Any] | None,
) -> datetime | None:
    if not period_data:
        return None
    last_reset_str = period_data.get("last_reset")
    if not last_reset_str:
        return None
    try:
        return datetime.fromisoformat(last_reset_str)
    except ValueError:
        return None


def _period_value(
    period_data: dict[str, Any] | None, sensor_type: str
) -> Any:
    if not period_data:
        return None
    if sensor_type == SENSOR_TYPE_ENERGY:
        return period_data.get("energy_kwh")
    if sensor_type == SENSOR_TYPE_REQUESTS:
        return period_data.get("requests")
    if sensor_type == SENSOR_TYPE_REQUESTS_WITH_ENERGY:
        return period_data.get("requests_with_energy")
    return None


PERIOD_SENSOR_DESCRIPTIONS: tuple[NeuralWattPeriodSensorDescription, ...] = (
    NeuralWattPeriodSensorDescription(
        key="energy_today",
        name="Energy today",
        sensor_type=SENSOR_TYPE_ENERGY,
        period=PERIOD_TODAY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    NeuralWattPeriodSensorDescription(
        key="energy_this_month",
        name="Energy this month",
        sensor_type=SENSOR_TYPE_ENERGY,
        period=PERIOD_THIS_MONTH,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    NeuralWattPeriodSensorDescription(
        key="energy_last_30_days",
        name="Energy last 30 days",
        sensor_type=SENSOR_TYPE_ENERGY,
        period=PERIOD_LAST_30_DAYS,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeuralWattPeriodSensorDescription(
        key="requests_today",
        name="Requests today",
        sensor_type=SENSOR_TYPE_REQUESTS,
        period=PERIOD_TODAY,
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.TOTAL,
    ),
    NeuralWattPeriodSensorDescription(
        key="requests_this_month",
        name="Requests this month",
        sensor_type=SENSOR_TYPE_REQUESTS,
        period=PERIOD_THIS_MONTH,
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.TOTAL,
    ),
    NeuralWattPeriodSensorDescription(
        key="requests_last_30_days",
        name="Requests last 30 days",
        sensor_type=SENSOR_TYPE_REQUESTS,
        period=PERIOD_LAST_30_DAYS,
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeuralWattPeriodSensorDescription(
        key="requests_with_energy_today",
        name="Requests with energy today",
        sensor_type=SENSOR_TYPE_REQUESTS_WITH_ENERGY,
        period=PERIOD_TODAY,
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.TOTAL,
    ),
    NeuralWattPeriodSensorDescription(
        key="requests_with_energy_this_month",
        name="Requests with energy this month",
        sensor_type=SENSOR_TYPE_REQUESTS_WITH_ENERGY,
        period=PERIOD_THIS_MONTH,
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.TOTAL,
    ),
    NeuralWattPeriodSensorDescription(
        key="requests_with_energy_last_30_days",
        name="Requests with energy last 30 days",
        sensor_type=SENSOR_TYPE_REQUESTS_WITH_ENERGY,
        period=PERIOD_LAST_30_DAYS,
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

SUMMARY_SENSOR_DESCRIPTIONS: tuple[NeuralWattSummarySensorDescription, ...] = (
    NeuralWattSummarySensorDescription(
        key="charged_kwh",
        name="Energy charged",
        summary_field=ATTR_ENERGY_KWH_CHARGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeuralWattSummarySensorDescription(
        key="total_cost",
        name="Cost",
        summary_field=ATTR_TOTAL_COST_USD,
        native_unit_of_measurement=CURRENCY_USD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeuralWattSummarySensorDescription(
        key="accounting_method",
        name="Accounting method",
        summary_field=ATTR_ACCOUNTING_METHOD,
        icon="mdi:calculator-variant",
    ),
)


class NeuralWattBaseSensor(
    CoordinatorEntity[NeuralWattDataUpdateCoordinator], SensorEntity
):
    _attr_has_entity_name = True

    def __init__(self, coordinator: NeuralWattDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DEVICE_INFO


class NeuralWattPeriodSensor(NeuralWattBaseSensor):
    entity_description: NeuralWattPeriodSensorDescription

    def __init__(
        self,
        coordinator: NeuralWattDataUpdateCoordinator,
        entry_id: str,
        description: NeuralWattPeriodSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data
        if not data:
            return None
        period_data = data.get(self.entity_description.period)
        value = _period_value(period_data, self.entity_description.sensor_type)
        if value is None:
            return None
        if self.entity_description.sensor_type == SENSOR_TYPE_ENERGY:
            return round(float(value), 6)
        return int(value)

    @property
    def last_reset(self) -> datetime | None:
        data = self.coordinator.data or {}
        period_data = data.get(self.entity_description.period)
        return _last_reset_from_period(period_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        if not data:
            return None
        period_data = data.get(self.entity_description.period)
        if not period_data:
            return None
        period = period_data.get("period") or {}
        return {
            "period_start": period.get("start"),
            "period_end": period.get("end"),
            "energy_joules": period_data.get("energy_joules"),
        }


class NeuralWattSummarySensor(NeuralWattBaseSensor):
    entity_description: NeuralWattSummarySensorDescription

    def __init__(
        self,
        coordinator: NeuralWattDataUpdateCoordinator,
        entry_id: str,
        description: NeuralWattSummarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data
        if not data:
            return None
        summary = data.get("summary") or {}
        value = summary.get(self.entity_description.summary_field)
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return round(float(value), 6)
        return str(value)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NeuralWattDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        NeuralWattPeriodSensor(coordinator, entry.entry_id, desc)
        for desc in PERIOD_SENSOR_DESCRIPTIONS
    ] + [
        NeuralWattSummarySensor(coordinator, entry.entry_id, desc)
        for desc in SUMMARY_SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)
