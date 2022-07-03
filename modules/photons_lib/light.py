"""Representation of LIFX Light powered by Photons."""
from __future__ import annotations

import asyncio
from typing import Any, cast, Optional, Union
import logging



from photons_app.helpers import Firmware, create_future
from photons_control.attributes import find_packet
from photons_control.transform import PowerToggle, Transformer
from photons_messages import protocol_register
from photons_messages.enums import Services
from photons_messages.messages import DeviceMessages
from photons_products import Products
from photons_products.lifx import Capability, Family, Product
from photons_transport.session.network import NetworkSession
from photons_transport.targets import LanTarget

from .models import Endpoint, Hsbk
from .utils import serial_to_mac_address, stringify

DEFAULT_REQUEST_REFRESH_DELAY = 0.2
_LOGGER = logging.getLogger(__name__)


class Light:
    """Represents the base functionality of all LIFX bulbs."""

    def __init__(self, serial: str, host: str, port: int = 56700) -> None:
        """Initialize an instance of a light device controlled by Photons."""

        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        self._endpoint = Endpoint(serial=serial, host=host, port=port)
        self._label: Optional[str] = None
        self._power: Optional[int] = None
        self._mac_address: Optional[str] = None
        self._hsbk: Optional[Hsbk] = None
        self._product: Optional[Product] = None
        self._cap: Optional[Capability] = None
        self._firmware: Optional[Firmware] = None
        self._group: Optional[str] = None
        self._location: Optional[str] = None

        self._future: asyncio.Future = create_future(loop=self._loop)
        self._lan_target: LanTarget = LanTarget.create(
            {"protocol_register": protocol_register, "final_future": self._future}
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Light):
            return self.serial == cast(Light, other).serial
        if isinstance(other, str):
            return other == self.label
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._endpoint.serial)

    def __repr__(self):
        return f"<Light: {self.label} ({self.serial})>"

    def __str__(self):
        return f"{self.model:24s}: {self.label:32s} [IP: {self.ip_address:15s}] [Serial: {self.serial:12s}]"

    def as_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the device."""

        a_dict = {
            "serial": self.endpoint.serial,
            "ip_address": self.endpoint.host,
            "mac_address": self.mac_address,
            "label": self.label,
            "power": self.power,
            "group": self.group,
            "location": self.location,
            "hsbk": stringify(self._hsbk.as_dict()),
            "product": stringify(self.product.as_dict(), ["cap"]),
            "firmware": stringify(self.firmware.as_dict()),
            "capabilities": [
                str(key).removeprefix("has_")
                for key, val in self.cap.as_dict().items()
                if val is True
            ],
        }
        return a_dict

    @property
    def serial(self) -> str:
        return self.endpoint.serial

    @property
    def label(self) -> str:
        return self._label

    @property
    def ip_address(self) -> str:
        return self.endpoint.host

    @property
    def port(self) -> int:
        return self.endpoint.port

    @property
    def endpoint(self) -> Endpoint:
        return self._endpoint

    @property
    def product(self) -> Product:
        return self._product

    @property
    def vendor(self) -> str:
        return self.product.vendor

    @property
    def product_id(self) -> int:
        return self.product.pid

    @property
    def model(self) -> str:
        return self.product.friendly

    @property
    def cap(self) -> Capability:
        return Products[self.vendor, self.product_id].cap

    @property
    def power(self) -> str:
        return "off" if self._power == 0 else "on"

    @property
    def is_on(self) -> bool:
        return False if self._power == 0 else True

    @property
    def group(self) -> str:
        return self._group

    @property
    def location(self) -> str:
        return self._location

    @property
    def firmware(self) -> Firmware:
        return self._firmware

    @property
    def firmware_version(self) -> str:
        return f"{self.firmware.major}.{self.firmware.minor}"

    @property
    def hsbk(self) -> Hsbk:
        return self._hsbk

    @property
    def hue(self) -> float:
        return self.hsbk.hue

    @property
    def saturation(self) -> float:
        return self.hsbk.saturation

    @property
    def brightness(self) -> float:
        return self.hsbk.brightness

    @property
    def kelvin(self) -> int:
        return self.hsbk.kelvin

    @property
    def mac_address(self) -> str:
        return self._mac_address

    @property
    def hw_version(self) -> str:
        family = Family(self.product.family)
        if family == "lcm1":
            return f"Gen 1 ({family.value})"
        elif family == "lcm2":
            return f"Gen 2 ({family.value})"
        elif family == "lcm3":
            return f"Gen 3 ({family.value})"

    #
    # Convenience methods (simplified actions)
    #
    async def transform(self, transform: dict[str, Any], **kwargs) -> None:
        """Transform a bulb from its current state to a new state."""
        msg = Transformer.using(transform, **kwargs, ack_required=True, res_required=False)
        if msg is not None:
            await self.__send_msg(msg)

    async def power_toggle(self, **kwargs) -> None:
        """Generate a power toggle packet."""
        msg = PowerToggle(ack_required=True, res_required=False, **kwargs)
        await self.__send_msg(msg)

    async def power_on(self, **kwargs) -> None:
        """Turn the light on."""
        duration = kwargs.pop("duration", 0)
        await self.__set_attr("light_power", level=65535, duration=duration)

    async def power_off(self, **kwargs) -> None:
        """Turn the light off."""
        duration = kwargs.pop("duration", 0)
        await self.__set_attr("light_power", level=0, duration=duration)

    async def reboot(self) -> None:
        """Send a magic reboot packet."""
        msg = DeviceMessages.SetReboot(target=self.serial, ack_required=False, res_required=False)
        await self.__send_msg(msg)

    #
    # Methods to retrieve device data/state
    #

    async def connect(self) -> Light:

        tasks = set()
        for func in [
            self.get_state,
            self.get_firmware,
            self.get_product,
            self.get_cap,
            self.get_mac_address,
            self.get_group,
            self.get_location,
        ]:
            task = asyncio.create_task(func())
            tasks.add(task)
            task.add_done_callback(tasks.discard)
            await task

        return self

    async def get_state(self) -> Hsbk:
        """Send a GetColor packet and return the LightState response."""
        light_state: dict[str, Any] = await self.__get_attr("color")
        self._label = light_state.pop("label")
        self._power = light_state.pop("power")
        self._hsbk = Hsbk(**light_state)
        return self.hsbk

    async def get_firmware(self) -> Firmware:
        state_firmware = await self.__get_attr("host_firmware")
        self._firmware = Firmware(
            major=state_firmware["version_major"],
            minor=state_firmware["version_minor"],
            build=state_firmware["build"],
        )
        return self.firmware

    async def get_product(self) -> Product:
        state_version = await self.__get_attr("version")
        self._product: Product = Products[state_version["vendor"], state_version["product"]]
        return self.product

    async def get_cap(self) -> Capability:
        if self._product is None:
            await self.get_product()

        return self.cap

    async def get_group(self) -> str:
        state_group = await self.__get_attr("group")
        self._group = state_group["label"]
        return self.group

    async def get_location(self) -> str:
        state_location = await self.__get_attr("location")
        self._location = state_location["label"]
        return self.location

    async def get_mac_address(self) -> str:
        if self._firmware is None:
            await self.get_firmware()

        return serial_to_mac_address(self.serial, self.firmware)

    async def __get_attr(self, attr, **kwargs) -> None:
        """Send a Get message to the device and return the State response."""

        def log_errors(e):
            """Log any errors that occur when sending messages."""
            _LOGGER.debug("__get_attr error: %s", e)

        sender: NetworkSession
        async with self._lan_target.session() as sender:
            await sender.add_service(service=Services.UDP, **self._endpoint.as_dict())

            kls = find_packet(protocol_register=protocol_register, value=attr, prefix="Get")
            msg = kls.create(ack_required=False, res_required=True)

            async for pkt in sender(msg, self.serial, error_catcher=log_errors):
                return {
                    key: value
                    for key, value in pkt.payload.items()
                    if str(key).startswith("reserved") is False
                }

    async def set_color(self, color: Hsbk, duration: int = 0) -> Hsbk:
        """Send new HSBK values to device with duration of transition."""
        return await self.__set_attr("color", duration=duration, **color)

    async def __set_attr(self, attr, **kwargs) -> Any:
        """Send a Set message to the device, return the current State."""

        def log_errors(e):
            """Log any errors that occur when sending messages."""
            _LOGGER.debug("__set_attr error: %s", e)

        sender: NetworkSession
        async with self._lan_target.session() as sender:
            await sender.add_service(service=Services.UDP, **self._endpoint.as_dict())

            set_kls = find_packet(protocol_register=protocol_register, value=attr, prefix="Set")
            set_msg = set_kls.create(ack_required=True, res_required=False, **kwargs)

            await sender(set_msg, self.serial, error_catcher=log_errors)
            await asyncio.sleep(DEFAULT_REQUEST_REFRESH_DELAY)

            return await self.__get_attr(attr, **kwargs)


class WhiteWarmLight(Light):
    """LIFX White to Warm light."""

    def __repr__(self):
        return f"<WhiteWarmLight: {self.label} ({self.serial})>"


class ColorLight(WhiteWarmLight):
    """LIFX Color light."""

    def __repr__(self):
        return f"<ColorLight: {self.label} ({self.serial})>"


class HevLight(ColorLight):
    """LIFX Clean light."""

    def __repr__(self):
        return f"<HevLight: {self.label} ({self.serial})>"

    def as_dict(self) -> dict[str, Any]:
        a_dict = super().as_dict()
        a_dict["hev"] = {"config": {"to": "do"}, "status": {"to": "do"}}
        return a_dict


class IrLight(ColorLight):
    """LIFX Nightvision lights."""

    def __repr__(self):
        return f"<IrLight: {self.label} ({self.serial})>"

    def as_dict(self) -> dict[str, Any]:
        a_dict = super().as_dict()
        a_dict["infrared"] = {"brightness": 0}
        return a_dict


class MultiZoneLight(ColorLight):
    """LIFX Lightstrip and Beam lights."""

    def __repr__(self):
        return f"<MultiZoneLight: {self.label} ({self.serial})>"

    def as_dict(self) -> dict[str, Any]:
        a_dict = super().as_dict()
        a_dict["zones"] = str(self.cap.zones.name).capitalize()
        return a_dict


class MatrixLight(ColorLight):
    """LIFX Tile and Candle lights."""

    def __repr__(self):
        return f"<MatrixLight: {self.label} ({self.serial})>"

    def as_dict(self) -> dict[str, Any]:
        a_dict = super().as_dict()
        a_dict["zones"] = str(self.cap.zones.name).capitalize()
        return a_dict


async def create_light(
    endpoint: Endpoint,
) -> Light | HevLight | IrLight | MultiZoneLight | MatrixLight | None:
    """Return a PhotonsDevice object after gathering enough data from the device."""

    cap = await Light(**endpoint.as_dict()).get_cap()

    if cap.is_light is False:
        return None

    if cap.has_matrix:
        return await MatrixLight(**endpoint.as_dict()).connect()
    elif cap.has_multizone:
        return await MultiZoneLight(**endpoint.as_dict()).connect()
    elif cap.has_ir:
        return await IrLight(**endpoint.as_dict()).connect()
    elif cap.has_hev:
        return await HevLight(**endpoint.as_dict()).connect()
    elif cap.has_color:
        return await ColorLight(**endpoint.as_dict()).connect()
    elif cap.has_variable_color_temp:
        return await WhiteWarmLight(**endpoint.as_dict()).connect()
    elif cap.is_light:
        return await Light(**endpoint.as_dict()).connect()
