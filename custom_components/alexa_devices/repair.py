from custom_components.alexa_devices.const import DOMAIN
from homeassistant.helpers import issue_registry as ir

def raise_revert_to_core_issue(hass) -> None:
    """Raise an issue indicating manual migration is required."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        "revert_to_core",
        is_fixable=False,
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="revert_to_core",
    )
