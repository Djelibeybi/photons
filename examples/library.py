"""Simple CLI example of photons_lib usage."""
import asyncio
from ipaddress import IPv4Address
from typing import Union

import rich
from time import perf_counter


from photons_lib.discover import Discover
from photons_lib.light import (
    ColorLight,
    MultiZoneLight,
    create_light,
    Endpoint,
    WhiteWarmLight,
)
from photons_lib.group import LightGroup


async def main(loop: asyncio.AbstractEventLoop) -> None:
    """Discover LIFX devices and print basic info for each."""

    lights = await asyncio.gather(
        *[
            create_light(Endpoint(serial="d073d553d316", host="192.168.254.44")),
            create_light(Endpoint(serial="d073d554498e", host="192.168.254.45")),
            create_light(Endpoint(serial="d073d5543a9c", host="192.168.254.46")),
            create_light(Endpoint(serial="d073d5408740", host="192.168.254.47")),
            create_light(Endpoint(serial="d073d5320ac8", host="192.168.254.48")),
            create_light(Endpoint(serial="d073d52a135f", host="192.168.254.49")),
            create_light(Endpoint(serial="d073d55627ff", host="192.168.254.50")),
        ]
    )

    print(f"Found lights in: {perf_counter() - start:.4f} seconds")

    light_group = LightGroup()
    result = await asyncio.gather(*[light_group.add(light) for light in lights])
    rich.print(result)

    async with LightGroup() as lg:

        result = await lg.power_off(duration=1)
        rich.print(result)

        await asyncio.sleep(2)
        result = await lg.power_on(duration=2)
        rich.print(result)

    # firmware = await light.get_firmware()
    # product = await light.get_product()
    # cap = await light.get_cap()
    # mac_address = light.mac_address
    # rich.print(light.serial, light.mac_address, light.state.as_dict(), light.product.friendly, light.cap.as_dict())


if __name__ == "__main__":
    """Run a asynchronous discovery and print the results."""
    start = perf_counter()
    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(main(loop=loop))
    print(f"Time: {perf_counter() - start:.3f} seconds")
