"""Message plans to optimize the packet delivery."""
from __future__ import annotations

import math

from photons_control.planner import Plan, Skip, a_plan
from photons_control.planner.plans import CapabilityPlan
from photons_messages.messages import DeviceMessages, LightMessages


@a_plan("infrared")
class InfraredPlan(Plan):
    @property
    def dependant_info(kls):
        return {"c": CapabilityPlan()}

    class Instance(Plan.Instance):
        @property
        def has_ir(self):
            return self.deps["c"]["cap"].has_ir is True

        @property
        def messages(self):
            if self.has_ir:
                return [LightMessages.GetInfrared()]

        def process(self, pkt):
            if pkt | LightMessages.StateInfrared:
                self.brightness = pkt.brightness
                return True

        async def info(self):
            return self.brightness


@a_plan("group")
class GroupPlan(Plan):
    @property
    def dependant_info(kls):
        return {}

    messages = [DeviceMessages.GetGroup()]

    class Instance(Plan.Instance):
        group: str = ""

        def process(self, pkt):
            if pkt | DeviceMessages.StateGroup:
                self.group = pkt.payload["label"]
                return True

        async def info(self):
            return self.group


@a_plan("location")
class LocationPlan(Plan):
    @property
    def dependant_info(kls):
        return {}

    messages = [DeviceMessages.GetLocation()]

    class Instance(Plan.Instance):
        location: str = ""

        def process(self, pkt):
            if pkt | DeviceMessages.StateLocation:
                self.location = pkt.payload["label"]
                return True

        async def info(self):
            return self.location


@a_plan("rssi")
class RssiPlan(Plan):

    messages = [DeviceMessages.GetWifiInfo()]

    class Instance(Plan.Instance):

        rssi = 0

        @staticmethod
        def _rssi(signal: float) -> int:
            return int(math.floor(10 * math.log10(signal) + 0.5))

        @staticmethod
        def _strength(rssi: int) -> str:
            if rssi == 200:
                return "No signal"
            if rssi < 0:
                if rssi <= -80:
                    return "Weak signal"
                elif rssi <= -70:
                    return "Poor signal"
                elif rssi <= -60:
                    return "Good signal"
                else:
                    return "Strong signal"
            if rssi > 0:
                if rssi == 4 or rssi == 5 or rssi == 6:
                    status = "Weak signal"
                elif rssi >= 7 and rssi <= 11:
                    status = "Poor signal"
                elif rssi >= 12 and rssi <= 16:
                    status = "Good signal"
                elif rssi > 16:
                    status = "Strong signal"

        def process(self, pkt):
            if pkt | DeviceMessages.StateWifiInfo:
                self.rssi = self._rssi(pkt.signal)
                return True

        async def info(self):
            return self.rssi
