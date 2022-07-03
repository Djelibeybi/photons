"""Discovery of LIFX lights."""
from __future__ import annotations
from typing import Union, AsyncGenerator
import rich

import asyncio
from ipaddress import IPv4Address
import logging


from photons_app import helpers as hp
from photons_control.device_finder import DeviceFinder, Filter
from photons_messages import protocol_register, Services
from photons_messages.messages import DiscoveryMessages, LightMessages, CoreMessages
from photons_transport.session.network import NetworkSession
from photons_transport.targets import LanTarget

from .models import Endpoint
from .light import Light, HevLight, IrLight, MatrixLight, MultiZoneLight, create_light

_LOGGER = logging.getLogger(__name__)


class Discover:
    """Discover LIFX devices on the local network."""

    def __init__(self) -> None:
        """Instantiate the Discover class."""
        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        self._final_future = hp.create_future(name="discover", loop=self._loop)
        self._target: LanTarget = LanTarget.create(
            {"protocol_register": protocol_register, "final_future": self._final_future}
        )

    async def endpoints(self, broadcast: IPv4Address) -> AsyncGenerator[Endpoint]:
        """Find LIFX endpoints using the broadcast address provided."""
        async with self._target.session() as sender:
            async for pkt in sender(DiscoveryMessages.GetService(), broadcast=str(broadcast)):
                if pkt | DiscoveryMessages.StateService and pkt.payload.service == Services.UDP:
                    yield Endpoint(pkt.serial, *(pkt.Information.remote_addr))

    async def lights(
        self, broadcast: IPv4Address
    ) -> AsyncGenerator[Union[Light, HevLight, IrLight, MatrixLight, MultiZoneLight]]:
        """Yield Light objects for each endpoint discovered."""
        async for endpoint in self.endpoints(broadcast=broadcast):
            light = await create_light(endpoint=endpoint)
            if light is not None:
                yield light

    async def find_lights(
        self, broadcast: IPv4Address
    ) -> set[Union[Light, HevLight, IrLight, MatrixLight, MultiZoneLight]]:
        """Return a list of Light objects."""
        endpoints: set[Endpoint] = set()
        async with self._target.session() as sender:
            async for pkt in sender(DiscoveryMessages.GetService(), broadcast=str(broadcast)):
                if pkt | DiscoveryMessages.StateService and pkt.payload.service == Services.UDP:
                    endpoints.add(Endpoint(pkt.serial, *(pkt.Information.remote_addr)))

        lights = await asyncio.gather(*[create_light(endpoint) for endpoint in endpoints])
        return {light for light in lights if light is not None}
