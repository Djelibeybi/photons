"""Utility functions for photons_lib."""
import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar
import math

from photons_app.helpers import Firmware, create_future
from photons_messages import protocol_register
from photons_transport.session.network import NetworkSession
from photons_transport.targets import LanTarget

_R = TypeVar("_R")


def serial_to_mac_address(serial: str, firmware: Firmware) -> str:
    """Generate the MAC address."""
    octets = [int(serial[i : i + 2], 16) for i in range(0, 12, 2)]
    if firmware >= Firmware(3, 70):
        octets[5] = (octets[5] + 1) % 256
    return ":".join(f"{octet:02x}" for octet in octets)


def calculate_rssi_from_signal(signal: float) -> int:
    """Convert the device signal value to RSSI."""
    return int(math.floor(10 * math.log10(signal) + 0.5))


def stringify(a_dict: dict[str, Any], without: list[str] = []) -> dict[str, str]:
    return {
        key: str(value.name) if hasattr(value, "name") else str(value)
        for key, value in a_dict.items()
        if key not in without
    }
