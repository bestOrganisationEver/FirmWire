from firmwire.hw.peripheral import LoggingPeripheral
from firmwire.vendor.exy5400.hw.PLLs import S5123ApPllPeripheral


# not sure what CMU_MCW stands for, but it seems to have something to do with
# PLLs and power delivery
class S5123ApCmuMcwPeripheral(LoggingPeripheral):
    def hw_read(self, offset, size, *args, **kwargs):
        # inline PLLs
        if 0x100 <= offset < 0x140:
            return self.ipll0.hw_read(offset - 0x100, size, *args, **kwargs)
        elif 0x140 <= offset < 0x180:
            return self.ipll1.hw_read(offset - 0x140, size, *args, **kwargs)
        elif 0x180 <= offset < 0x1C0:
            return self.mpll.hw_read(offset - 0x180, size, *args, **kwargs)
        elif 0x1C0 <= offset < 0x200:
            return self.mpll_nrt.hw_read(offset - 0x1C0, size, *args, **kwargs)

        elif offset == 0xA00:
            return super().hw_read(offset, size, "MCW_MR_REGISTER_A00")
        elif offset == 0xA04:
            return super().hw_read(offset, size, "MCW_MR_REGISTER_A04")
        elif offset == 0xA08:
            return super().hw_read(offset, size, "MCW_MR_REGISTER_A08")
        elif offset == 0xA0C:
            return super().hw_read(offset, size, "MCW_MR_REGISTER_A0C")
        elif offset == 0xB18:
            # LSB reads 0b0 when the sync request is complete.
            # I don't know what we're syncing, but since the code here is
            # syncronous, assume that we don't need to deal with this.
            val = 0
            super().log_read(val, size, "TSM_MCW_SYNC_REQ")
            return val
        elif offset == 0xC00:
            return super().hw_read(offset, size, "MCW_MR_REGISTER_C00")
        elif offset == 0xC04:
            return super().hw_read(offset, size, "MCW_MR_REGISTER_C04")

        elif offset == 0x4100:
            val = self.ipll0_d
            self.log_read(val, size, "IPLL0_D")
            return val

        elif offset == 0x4140:
            val = self.ipll1_d
            self.log_read(val, size, "IPLL1_D")
            return val

        elif offset == 0x4180:
            val = self.mpll_d
            self.log_read(val, size, "MPLL_D")
            return val

        elif offset == 0x41C0:
            val = self.mpll_nrt_d
            self.log_read(val, size, "MPLL_NRT_D")
            return val

        return super().hw_read(offset, size, *args, **kwargs)

    def hw_write(self, offset, size, value, *args, **kwargs):
        # inline PLLs
        if 0x100 <= offset < 0x140:
            return self.ipll0.hw_write(offset - 0x100, size, value, *args, **kwargs)
        elif 0x140 <= offset < 0x180:
            return self.ipll1.hw_write(offset - 0x140, size, value, *args, **kwargs)
        elif 0x180 <= offset < 0x1C0:
            return self.mpll.hw_write(offset - 0x180, size, value, *args, **kwargs)
        elif 0x1C0 <= offset < 0x200:
            return self.mpll_nrt.hw_write(offset - 0x1C0, size, value, *args, **kwargs)

        elif offset == 0xA00:
            return super().hw_write(
                offset, size, value, "MCW_MR_REGISTER_A00", *args, **kwargs
            )
        elif offset == 0xA04:
            return super().hw_write(
                offset, size, value, "MCW_MR_REGISTER_A04", *args, **kwargs
            )
        elif offset == 0xA08:
            return super().hw_write(
                offset, size, value, "MCW_MR_REGISTER_A08", *args, **kwargs
            )
        elif offset == 0xA0C:
            return super().hw_write(
                offset, size, value, "MCW_MR_REGISTER_A0C", *args, **kwargs
            )
        elif offset == 0xB18:
            # This will be a write of 1, for a "sync request". Don't know what
            # sync does, but we assume we handle this well. Read the note
            # in hw_read for more details.
            assert value == 1
            super().log_write(value, size, "TSM_MCW_SYNC_REQ")
            return True
        elif offset == 0xC00:
            return super().hw_write(
                offset, size, value, "MCW_MR_REGISTER_C00", *args, **kwargs
            )
        elif offset == 0xC04:
            return super().hw_write(
                offset, size, value, "MCW_MR_REGISTER_C04", *args, **kwargs
            )

        return super().hw_write(offset, size, value, *args, **kwargs)

    def __init__(self, name, address, size, **kwargs):
        super().__init__(name, address, size, **kwargs)
        self.ipll0 = S5123ApPllPeripheral("IPLL0", address + 0x100, 0x40, **kwargs)
        self.ipll1 = S5123ApPllPeripheral(
            "IPLL1", address + 0x100 + 0x40, 0x40, **kwargs
        )
        self.mpll = S5123ApPllPeripheral("MPLL", address + 0x100 + 0x80, 0x40, **kwargs)
        self.mpll_nrt = S5123ApPllPeripheral(
            "MPLL_NRT", address + 0x100 + 0xC0, 0x40, **kwargs
        )

        # power delivery?
        # & 0x3f0000 != 0 and != 0x3f0000 indicates stability.
        # so make em stable by default, even though
        # this process probably happens after the respective PLL is set to on.
        self.ipll0_d = 0x180000
        self.ipll1_d = 0x180000
        self.mpll_d = 0x180000
        self.mpll_nrt_d = 0x180000

        self.read_handler[0:size] = self.hw_read
        self.write_handler[0:size] = self.hw_write
