"""Constants for LIFX Photons."""
from typing import Final

# Device Attributes
ATTR_BRIGHTNESS: Final = "brightness"
ATTR_COLOR: Final = "color"
ATTR_DIRECTION: Final = "direction"
ATTR_DURATION: Final = "duration"
ATTR_GROUP: Final = "group"
ATTR_HUE: Final = "hue"
ATTR_INFRARED: Final = "infrared"
ATTR_KELVIN: Final = "kelvin"
ATTR_LABEL: Final = "label"
ATTR_LOCATION: Final = "location"
ATTR_PARAMETERS: Final = "parameters"
ATTR_POWER: Final = "power"
ATTR_POWER_ON: Final = "power_on"
ATTR_POWER_ON_DURATION: Final = "power_on_duration"
ATTR_RSSI: Final = "rssi"
ATTR_SATURATION = "saturation"
ATTR_SPEED: Final = "speed"
ATTR_SPEED_DIRECTION: Final = "speed_direction"
ATTR_TYPE: Final = "type"
ATTR_ZONE_TYPE: Final = "zone_type"
ATTR_ZONE_COUNT: Final = "zone_count"
ATTR_ZONES: Final = "zones"

# Configuration options
CONF_ENABLE_RESTART_BUTTON: Final = "enable_restart_button"
CONF_ENABLE_RSSI_SENSOR: Final = "enable_rssi_sensor"
CONF_ENABLE_LIFX_GROUP_SENSOR: Final = "enable_lifx_group_sensor"
CONF_ENABLE_LIFX_GROUP_TO_AREA: Final = "enable_lifx_group_to_area"
CONF_ENABLE_LIFX_LOCATION_SENSOR: Final = "enable_lifx_location_sensor"
CONF_ENABLE_LIFX_FIRMWARE_EFFECTS: Final = "enable_lifx_firmware_effects"
CONF_ENABLE_PHOTONS_ANIMATIONS: Final = "enable_photons_animations"

# HEV attributes
HEV_CONFIG_DURATION_S: Final = "hev_config_duration_s"
HEV_CONFIG_INDICATION: Final = "hev_config_indication"
HEV_STATUS_DURATION_S: Final = "hevcurrent_duration_s"
HEV_STATUS_LAST_POWER: Final = "hev_status_last_power"
HEV_STATUS_REMAINING: Final = "hev_status_remaining"
HEV_STATUS_ACTIVE: Final = "hev_status_active"
HEV_LAST_RESULT: Final = "hev_last_result"

# Infrared Attributes
INFRARED_BRIGHTNESS: Final = "infrared_brightness"

# Defaults
DEFAULT_ENABLE_RESTART_BUTTON: Final = False
DEFAULT_ENABLE_RSSI_SENSOR: Final = False
DEFAULT_ENABLE_LIFX_GROUP_SENSOR: Final = True
DEFAULT_ENABLE_LIFX_GROUP_TO_AREA: Final = True
DEFAULT_ENABLE_LIFX_LOCATION_SENSOR: Final = True
DEFAULT_ENABLE_LIFX_FIRMWARE_EFFECTS: Final = True
DEFAULT_ENABLE_PHOTONS_ANIMATIONS: Final = False
DEFAULT_TIMEOUT: Final = 10
DEFAULT_TRANSITION_DURATION: Final = 0

# Immutable device attributes
DEVICE_FIRMWARE: Final = "firmware"
DEVICE_MAC_ADDRESS: Final = "mac_address"
DEVICE_PRODUCT: Final = "product"
DEVICE_SERIAL: Final = "serial"
DEVICE_RESTART: Final = "restart"

# Firmware effects
FIRMWARE_EFFECT_MOVE: Final = "MOVE"
FIRMWARE_EFFECT_MORPH: Final = "MORPH"
FIRMWARE_EFFECT_FLAME: Final = "FLAME"
FIRMWARE_EFFECT_OFF: Final = "OFF"

# Services and effects
SERVICE_PHOTONS_TRANSFORM: Final = "transform"
SERVICE_EFFECT_MOVE: Final = "effect_move"
SERVICE_EFFECT_FLAME: Final = "effect_flame"
SERVICE_EFFECT_MORPH: Final = "effect_morph"
SERVICE_EFFECT_OFF: Final = "effect_off"

# Discovery States
DISCOVERY_PENDING: Final = "pending"

# Internal components
PHOTONS_DATA: Final = "photons_data"
PHOTONS_DISPATCHER: Final = "photons_dispatcher"

# Update keys
UPDATE_FIRMWARE_EFFECT: Final = "update_firmware_effect"
UPDATE_INFRARED: Final = "update_infrared"
UPDATE_HEV_STATUS: Final = "update_hev_status"
UPDATE_HEV_CONFIG: Final = "update_hev_config"
UPDATE_RSSI: Final = "update_rssi"
UPDATE_STATE: Final = "update_state"
UPDATE_ZONES: Final = "update_zones"
