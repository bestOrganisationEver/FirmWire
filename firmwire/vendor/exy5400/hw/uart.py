## Copyright (c) 2022, Team FirmWire
## SPDX-License-Identifier: BSD-3-Clause
import sys
from avatar2 import *

from . import FirmWirePeripheral, LoggingPeripheral

# from firmwire.hw.peripheral import *


class UARTPeripheral(FirmWirePeripheral):
    def hw_read(self, offset, size, *args, **kwargs):
        self.log_read(offset, size, "UART")
        if offset == 0x18:
            return self.status
        if offset == 0x30:
            return self.status2

        return 0

    def hw_write(self, offset, size, value, *args, **kwargs):
        if offset == 0:
            sys.stderr.write("[BOOTUART] " + chr(value & 0xFF) + "\n")
            sys.stderr.flush()
        else:
            self.log_write(value, size, "UART")

        return True

    def __init__(self, name, address, size, **kwargs):
        super().__init__(name, address, size, **kwargs)

        self.status = 0
        self.status2 = 1 << 8 # bit 8 enables uart, see 0x40a3cea2

        self.write_handler[0:size] = self.hw_write
        self.read_handler[0:size] = self.hw_read

        # init of this peripheral bypasses shannon peripheral, hence we set pc
        # dummy value manually
        self.pc = 0
