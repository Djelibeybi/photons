"""Data models for LIFX light data."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Union, TYPE_CHECKING

from photons_messages import Services

if TYPE_CHECKING:
    from .light import (
        Light,
        ColorLight,
        WhiteWarmLight,
        IrLight,
        HevLight,
        MultiZoneLight,
        MatrixLight,
    )


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
