"""Representation of a group of LIFX Lights."""
from __future__ import annotations

import asyncio
from typing import Any, cast, Optional, Union
import logging
import rich

from photons_app.helpers import Firmware, create_future, AsyncCMMixin

from photons_control.attributes import find_packet
# from photons_control.transform import PowerToggle, Transformer
from photons_messages import protocol_register, Services
# from photons_messages.enums import Services
# from photons_messages.messages import DeviceMessages
# from photons_products import Products
# from photons_products.lifx import Capability, Family, Product
from photons_transport.session.network import NetworkSession
from photons_transport.targets import LanTarget

from .light import Light, WhiteWarmLight, ColorLight, IrLight, HevLight, MultiZoneLight, MatrixLight
from .models import Endpoint, Hsbk
from .utils import serial_to_mac_address, stringify

DEFAULT_REQUEST_REFRESH_DELAY = 0.2
_LOGGER = logging.getLogger(__name__)


class LightGroup(AsyncCMMixin):

    def __init__(self, loop: asyncio.AbstractEventLoop = None):

        self._loop = loop if loop else asyncio.get_event_loop_policy().get_event_loop()
        self._future: asyncio.Future = create_future(loop=self._loop)
        self._lan_target: LanTarget = LanTarget.create(
            {"protocol_register": protocol_register, "final_future": self._future}
        )
        self._sender: Optional[NetworkSession] = None
        self._members: list[Union[Light, WhiteWarmLight, ColorLight, IrLight, HevLight, MultiZoneLight, MatrixLight]] = []
        self._reference: list[str] = []

    @property
    def reference(self) -> list[str]:
        """Return the current list of member serials as reference."""
        return [light.serial for light in self._members]

    @property
    def endpoints(self) -> list[Endpoint]:
        """Return all member endpoints."""
        return [light.endpoint for light in self._members]

    async def start(self, **kwargs) -> LightGroup:
        rich.print("LightGroup: start()", kwargs)
        if self._sender is None:
            self._sender = await self._lan_target.make_sender()

        await asyncio.gather(*[self._sender.add_service(service=Services.UDP, **endpoint.as_dict()) for endpoint in self.endpoints])
        return self

    async def finish(self, exc_typ=None, exc=None, tb=None):
        print("LightGroup: finish()")
        if self._sender is not None:
            await self._lan_target.close_sender(self._sender)

    async def add(self, light: Union[Light, WhiteWarmLight, ColorLight, IrLight, HevLight, MultiZoneLight, MatrixLight]) -> bool:
        """Add a light to the group."""
        if light not in self._members:
            self._members.append(light)

        return True


    async def remove(self, light: Union[Light, WhiteWarmLight, ColorLight, IrLight, HevLight, MultiZoneLight, MatrixLight]) -> bool:
        """Remove a light from the group."""
        if light in self._members:
            self._members.pop(light)
        return True

    async def __get_group_attr(self, attr, **kwargs) -> Any:
        """Get the same packet from all members of the group."""
        def log_errors(e):
            _LOGGER.debug("__group_attr error: %s", e)

        async with self as group:
            kls = find_packet(protocol_register=protocol_register, value=attr, prefix="Get")
            msg = kls.create(ack_required=False, res_required=True)
            response: dict[str, Any] = {}

            async for pkt in group._sender(msg, self._reference, error_catcher=log_errors):
                response[pkt.serial] = {
                    key: value
                    for key, value in pkt.payload.items()
                    if str(key).startswith("reserved") is False
                }

            return response

    async def power_on(self, duration: int = 0) -> Any:
        """Turn all group members on."""
        return await self.__set_group_attr("light_power", level=65535, duration=duration)

    async def power_off(self, duration: int = 0) -> Any:
        """Turn all group members on."""
        return await self.__set_group_attr("light_power", level=0, duration=duration)

    async def __set_group_attr(self, attr, **kwargs) -> Any:
        """Send the same message to the all members of the group."""
        def log_errors(e):
            _LOGGER.debug("__group_attr error: %s", e)

        async with self as group:
            set_kls = find_packet(protocol_register=protocol_register, value=attr, prefix="Set")
            set_msg = set_kls.create(ack_required=True, res_required=False, **kwargs)

            await group._sender(set_msg, self._reference, error_catcher=log_errors)
            await asyncio.sleep(DEFAULT_REQUEST_REFRESH_DELAY)

            return await self.__get_group_attr(attr, **kwargs)
