"""Data models for LIFX light data."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

from photons_messages import Services


@dataclass(frozen=True)
class Endpoint:
    serial: str
    host: str
    port: int = field(default=56700)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Hsbk:
    hue: float
    saturation: float
    brightness: float
    kelvin: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# @dataclass(frozen=True)
# class Light:
#     serial: str
#     label: str
#     power: int
#     hue: float
#     saturation: float
#     brightness: float
#     kelvin: float
#     product_id: int
#     group_id: str
#     group_name: str
#     location_id: str
#     location_name: str
#     firmware_version: str
#     product_name: str
#     product_type: str
#     cap: list[str]
