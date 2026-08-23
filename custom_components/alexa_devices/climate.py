"""Climate platform for Alexa Devices."""

from typing import TYPE_CHECKING, Any, Final, override

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AmazonConfigEntry
from .entity import AmazonEntity

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0

HVAC_MODE_MAP: Final[dict[str, HVACMode]] = {
    "OFF": HVACMode.OFF,
    "HEAT": HVACMode.HEAT,
    "COOL": HVACMode.COOL,
    "AUTO": HVACMode.HEAT_COOL,
}

TEMPERATURE_SCALE_MAP: Final[dict[str, str]] = {
    "CELSIUS": UnitOfTemperature.CELSIUS,
    "FAHRENHEIT": UnitOfTemperature.FAHRENHEIT,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AmazonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Alexa Devices climate entities based on a config entry."""
    coordinator = entry.runtime_data

    known_devices: set[str] = set()

    def _check_device() -> None:
        current_devices = set(coordinator.data)
        new_devices = current_devices - known_devices
        if new_devices:
            known_devices.update(new_devices)
            async_add_entities(
                AmazonClimateEntity(
                    coordinator, serial_num, ClimateEntityDescription(key="thermostat")
                )
                for serial_num in new_devices
                if coordinator.data[serial_num].sensors.get("thermostat") is not None
            )

    _check_device()
    entry.async_on_unload(coordinator.async_add_listener(_check_device))


class AmazonClimateEntity(AmazonEntity, ClimateEntity):
    """Representation of an Alexa Devices thermostat."""

    _attr_name = None  # Uses the device name
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    )

    @property
    def _thermostat_data(self) -> dict[str, Any]:
        """Return the raw thermostat data."""
        value = self.device.sensors["thermostat"].value
        if TYPE_CHECKING:
            assert isinstance(value, dict)
        return value

    @property
    @override
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return TEMPERATURE_SCALE_MAP.get(
            self._thermostat_data.get("temperatureScale", ""),
            UnitOfTemperature.FAHRENHEIT,
        )

    @property
    @override
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._thermostat_data.get("temperature")

    @property
    @override
    def hvac_mode(self) -> HVACMode | None:
        """Return current HVAC mode."""
        return HVAC_MODE_MAP.get(self._thermostat_data.get("thermostatMode", ""))

    @property
    @override
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of supported HVAC modes."""
        return [
            HVAC_MODE_MAP[mode]
            for mode in self._thermostat_data.get("supportedModes", [])
            if mode in HVAC_MODE_MAP
        ]

    @property
    @override
    def target_temperature(self) -> float | None:
        """Return the temperature currently set to be reached."""
        return self._thermostat_data.get("targetSetpoint")

    @property
    @override
    def target_temperature_high(self) -> float | None:
        """Return the upper bound target temperature."""
        return self._thermostat_data.get("upperSetpoint")

    @property
    @override
    def target_temperature_low(self) -> float | None:
        """Return the lower bound target temperature."""
        return self._thermostat_data.get("lowerSetpoint")

    @property
    def _temperature_bounds(self) -> tuple[float | None, float | None]:
        """Return the (min, max) temperature bounds for the current HVAC mode."""
        if self.hvac_mode == HVACMode.HEAT:
            return (
                self._thermostat_data.get("heatingMinimumTemperature"),
                self._thermostat_data.get("heatingMaximumTemperature"),
            )
        if self.hvac_mode == HVACMode.COOL:
            return (
                self._thermostat_data.get("coolingMinimumTemperature"),
                self._thermostat_data.get("coolingMaximumTemperature"),
            )
        # HEAT_COOL uses the heating setpoint as the lower handle and the
        # cooling setpoint as the upper handle, so the range must cover both.
        return (
            self._thermostat_data.get("heatingMinimumTemperature"),
            self._thermostat_data.get("coolingMaximumTemperature"),
        )

    @property
    @override
    def min_temp(self) -> float:
        """Return the minimum supported temperature."""
        min_temp = self._temperature_bounds[0]
        return min_temp if min_temp is not None else super().min_temp

    @property
    @override
    def max_temp(self) -> float:
        """Return the maximum supported temperature."""
        max_temp = self._temperature_bounds[1]
        return max_temp if max_temp is not None else super().max_temp

    @property
    @override
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and (sensor := self.device.sensors.get("thermostat")) is not None
            and sensor.error is False
        )
