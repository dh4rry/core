"""Platform for sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from intellifire4py import IntellifirePollData

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import utcnow

from . import IntellifireDataUpdateCoordinator
from .const import DOMAIN
from .entity import IntellifireEntity


@dataclass
class IntellifireSensorRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[IntellifirePollData], int | str | datetime | None]


@dataclass
class IntellifireSensorEntityDescription(
    SensorEntityDescription,
    IntellifireSensorRequiredKeysMixin,
):
    """Describes a sensor entity."""


def _time_remaining_to_timestamp(data: IntellifirePollData) -> datetime | None:
    """Define a sensor that takes into account timezone."""
    if not (seconds_offset := data.timeremaining_s):
        return None
    return utcnow() + timedelta(seconds=seconds_offset)


INTELLIFIRE_SENSORS: tuple[IntellifireSensorEntityDescription, ...] = (
    IntellifireSensorEntityDescription(
        key="flame_height",
        icon="mdi:fire-circle",
        name="Flame Height",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.flameheight,
    ),
    IntellifireSensorEntityDescription(
        key="temperature",
        name="Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        value_fn=lambda data: data.temperature_c,
    ),
    IntellifireSensorEntityDescription(
        key="target_temp",
        name="Target Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        value_fn=lambda data: data.thermostat_setpoint_c,
    ),
    IntellifireSensorEntityDescription(
        key="fan_speed",
        icon="mdi:fan",
        name="Fan Speed",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.fanspeed,
    ),
    IntellifireSensorEntityDescription(
        key="timer_end_timestamp",
        icon="mdi:timer-sand",
        name="Timer End",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_time_remaining_to_timestamp,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Define setup entry call."""

    coordinator: IntellifireDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        IntellifireSensor(coordinator=coordinator, description=description)
        for description in INTELLIFIRE_SENSORS
    )


class IntellifireSensor(IntellifireEntity, SensorEntity):
    """Extends IntellifireEntity with Sensor specific logic."""

    entity_description: IntellifireSensorEntityDescription

    @property
    def native_value(self) -> int | str | datetime | None:
        """Return the state."""
        return self.entity_description.value_fn(self.coordinator.api.data)
