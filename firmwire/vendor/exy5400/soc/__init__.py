## Copyright (c) 2022, Team FirmWire
## SPDX-License-Identifier: BSD-3-Clause
from ..hw import *
from firmwire.hw.soc import FirmWireSOC, SOCPeripheral, register_soc
from firmwire.util.BinaryPattern import BinaryPattern


class ShannonSOC(FirmWireSOC):
    # Start in BOOT (can be overwritten)
    ENTRY_ADDRESS = 0x0

    # Whether the OSI for the TaskStruct should use the Moto or Samsung version

    name = "Unknown"

    def __init__(self, date, main_section=None):
        self.date = date

    def __repr__(self):
        return "<ShannonSOC %s - %d>" % (self.name, self.date)


def dsp_base_search(main_section):
    # SoC init is before symbol resolving, so we do it here on our own
    # We abuse that the data pointer is right before the DSP_SUBSYS_CRTLDSP string
    bp = BinaryPattern("CRTLDSP_LOC", -4)
    bp.from_str(b"DSP_SUBSYS_CRTLDSP")

    str_loc = bp.find(main_section.data)
    if str_loc is None:
        print("Failed retrieving DSP base, defaulting to 0x47382000")
        return 0x47382000
    else:
        off = str_loc[0]
        return struct.unpack("<I", main_section.data[off : off + 4])[0]


# Modem AP in the Samsung S24
class S5123AP(ShannonSOC):
    peripherals = [
        # SOCPeripheral(S3xxAPBoot, 0x90540000, 0x100, name="S3xxboot"),
    ]

    CHIP_ID = 0x03350000
    SIPC_BASE = 0x8F170000
    SHM_BASE = 0x48000000
    SOC_BASE = 0x82020000
    SOC_CLK_BASE = 0x88500000
    CLK_PERIPHERAL = S5123APClkPeripheral
    TIMER_BASE = SOC_BASE + 0xC000
    ENTRY_ADDRESS = 0x40010000
    name = "S5123AP"

    def __init__(self, date, main_section):
        super().__init__(date)

        # dsp_load_addr = dsp_base_search(main_section)
        # self.peripherals += [
        #     SOCPeripheral(
        #         DSPPeripheral,
        #         dsp_load_addr,
        #         0x100,
        #         name="DSPPeripheral",
        #         sync=[125, 255],
        #     )
        # ]

register_soc("exy5400", S5123AP)
