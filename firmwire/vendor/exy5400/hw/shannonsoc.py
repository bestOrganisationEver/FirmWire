## Copyright (c) 2022, Team FirmWire
## SPDX-License-Identifier: BSD-3-Clause
import sys
import struct
from avatar2 import *

from . import LoggingPeripheral


class ShannonSOCPeripheral(LoggingPeripheral):
    def hw_read(self, offset, size, *args, **kwargs):
        if offset == 0x00:
            value = self.warm_boot[0]
            offset_name = "WARM_BOOT_0"
        elif offset == 0x04:
            value = self.warm_boot[1]
            offset_name = "WARM_BOOT_1"
        # 0x40a4cddc
        elif offset in (
            0x0a04, 0x0a24, 0x0a3c, 0x0a50, 0x0b04, 0x0b18, 0x0b2c, 0x0b40, # arg1 = 0
            0x0b7c, 0x0b68, # arg1 = 1
                        ):
            # Something non-zero
            value = 1
            offset_name = f"CHIP_WAKEUP? {offset}"
        # 0x40a3b046
        elif offset == 0x0bb0:
            # Something non-zero
            # value = 1
            value = self.chip_wakeup2
            offset_name = f"CHIP_WAKEUP?2 {offset}"
        else:
            value = 0
            offset_name = ""
            value = super().hw_read(offset, size)

        if offset_name != "":
            self.log_read(value, size, offset_name)

        return value

    def hw_write(self, offset, size, value, *args, **kwargs):
        # TODO: add write of warm_boot.

        # 0x416015aa called thru 0x415e3f2e and the other branches in that func
        if offset == 0x168:
            # 4 | 3 |   2  |   1   | 0
            #   |   | MPLL |       | 
            self.mpll = value
            self.reconfigure_mpll()
        # from 0x40a3b078
        elif offset == 0xb94:
            self.chip_wakeup2 = value

        return super().hw_write(offset, size, value)

    def reconfigure_mpll(self):
        # TODO!
        ...

    def __init__(self, name, address, size, **kwargs):
        super().__init__(name, address, size, **kwargs)

        # self.chip_id = 0x50000000
        self.warm_boot = [1, 1]

        self.read_handler[0:size] = self.hw_read
        self.write_handler[0:size] = self.hw_write

        self.cycle_idx = 0

        self.chip_wakeup2 = 0
