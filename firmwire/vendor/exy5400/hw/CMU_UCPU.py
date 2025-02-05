from firmwire.hw.peripheral import LoggingPeripheral
from firmwire.vendor.exy5400.hw.PLLs import S5123ApPllPeripheral


# not sure what CMU_UCPU stands for, but it seems to have something to do with
# non-power delivery PLLs
class S5123ApCmuUcpuPeripheral(LoggingPeripheral):
    def hw_read(self, offset, size, *args, **kwargs):
        # inline PLLs
        if 0x100 <= offset < 0x140:
            return self.cpll.hw_read(offset - 0x100, size, *args, **kwargs)
        elif 0x140 <= offset < 0x180:
            return self.dpll.hw_read(offset - 0x140, size, *args, **kwargs)

        elif offset == 0x4100:
            val = self.cpll_d1
            self.log_read(val, size, "CPLL_D1")
            return val

        elif offset == 0x4140:
            val = self.dpll_d1
            self.log_read(val, size, "DPLL_D1")
            return val

        return super().hw_read(offset, size, *args, **kwargs)

    def hw_write(self, offset, size, value, *args, **kwargs):
        # inline PLLs
        if 0x100 <= offset < 0x140:
            return self.cpll.hw_write(offset - 0x100, size, value, *args, **kwargs)
        elif 0x140 <= offset < 0x180:
            return self.dpll.hw_write(offset - 0x140, size, value, *args, **kwargs)

        return super().hw_write(offset, size, value, *args, **kwargs)

    def set_machine(self, machine):
        super().set_machine(machine)
        self.cpll.set_machine(machine)
        self.dpll.set_machine(machine)

    def __init__(self, name, address, size, **kwargs):
        super().__init__(name, address, size, **kwargs)
        self.cpll = S5123ApPllPeripheral("CPLL", address + 0x100, 0x40, **kwargs)
        self.dpll = S5123ApPllPeripheral("DPLL", address + 0x100 + 0x40, 0x40, **kwargs)

        # power delivery?
        # & 0x3f0000 != 0 and != 0x3f0000 indicates stability.
        # so make em stable by default, even though
        # this process probably happens after the respective PLL is set to on.
        self.cpll_d1 = 0x180000  # == self.cpll_d2? (0x42cd5888)
        self.dpll_d1 = 0x180000  # found thru running emul, idk how it gets to a read of this. but it does.

        self.read_handler[0:size] = self.hw_read
        self.write_handler[0:size] = self.hw_write
