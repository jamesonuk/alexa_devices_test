"""Text."""

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import AmazonConfigEntry, AmazonDevicesCoordinator

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AmazonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Setup."""
    coordinator: AmazonDevicesCoordinator = entry.runtime_data
    async_add_entities([AmazonLastUsedDevice(coordinator)])


class AmazonLastUsedDevice(TextEntity):
    """Store last used device."""

    _attr_has_entity_name = True
    _attr_native_value = ""
    _attr_mode = "text"

    def __init__(self, coordinator: AmazonDevicesCoordinator) -> None:
        """Create entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_last_used_device"
        coordinator.last_used_entity = self

    def update_last_used(self, serial_num: str) -> None:
        """Update serial."""
        self._attr_native_value = self._coordinator.data[serial_num].account_name
        self.async_write_ha_state()
