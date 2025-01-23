from firmwire.hw.peripheral import LoggingPeripheral
from firmwire.util.misc import extract_bits


class S5123ApPllPeripheral(LoggingPeripheral):
    def hw_read(self, offset, size, *args, **kwargs):
        assert size == 4
        val = None
        offset_name = None
        # PLL_CON0_x_CP
        if offset == 0:
            offset_name = "PLL_CON0_%s_CP" % self.name
            val = self.con[0]
        # PLL_CON1_x_CP
        elif offset == 4:
            offset_name = "PLL_CON1_%s_CP" % self.name
            val = self.con[1]
        # PLL_CON2_x_CP
        elif offset == 8:
            offset_name = "PLL_CON2_%s_CP" % self.name
            val = self.con[2]
        # PLL_CON3_x_CP
        elif offset == 0xC:
            # TODO: I messed up the offsets and MSB/LSB-side'ness with this
            # explanation. Take it as a rough sketch.
            
            # CPLL (and less checked, DPLL) boot:
            # CON6:
            # disabled if 0x20 is not set or 0x1e is not set
            # 0x20 -> write -> start enable
            # 0x1e -> read 1 > enabled

            # CON7:
            # or by 0xc000

            # CON3:
            # disabled if 0x20 is not set or 0x1e is not set
            # 0x20 -> write -> start enable
            # 0x1e -> read 1 > enabled

            # CON0:
            # 0x4 -> write -> start enable
            # 0xf -> read 0 -> enable

            # MPLL boot:
            # call en_some_stuff for power delivery (?)
            # check PowerDomainStatus for PD_MDM_MCW

            # 415e47ea                    MCW_MR_REGISTER_A04 |= &data_10000
            # 415e47f6                    MCW_MR_REGISTER_A04 &= 0xffefffff

            # loop until (MCW_MR_REGISTER_A04 & 0x220000) == 0


            # CON0:
            # 0x4 -> _CLEAR_ -> start enable
            # 0xf -> read 0 -> enable

            # Set CON{3,4,5,6,7,8}

            # CON6:
            # disabled if 0x20 is not set or 0x1e is not set
            # 0x20 -> write -> start enable
            # 0x1e -> read 1 > enabled

            # -- DOES NOT HAPPEN -- CON7:
            # or by 0xc000
    
            # CON3:
            # disabled if 0x20 is not set or 0x1e is not set <- initial check for `already enabled`
            # 0x20 -> write -> start enable
            # 0x1e -> read 1 > enabled
            # also wait for PLL_CONx_MPLL_CP_D before enable
            # Think it's got to do with MPLL stability.
            # TODO: Read up on PLL stability



            # CON0:
            # 0x4 -> write -> start enable
            # 0xf -> read 0 -> enable
            offset_name = "PLL_CON3_%s_CP" % self.name
            val = self.con[3]
        # PLL_CON4_x_CP
        elif offset == 0x10:
            offset_name = "PLL_CON4_%s_CP" % self.name
            val = self.con[4]
        # PLL_CON5_x_CP
        elif offset == 0x14:
            offset_name = "PLL_CON5_%s_CP" % self.name
            val = self.con[5]
        # PLL_CON6_x_CP
        elif offset == 0x18:
            offset_name = "PLL_CON6_%s_CP" % self.name
            val = self.con[6]
        # PLL_CON7_x_CP
        elif offset == 0x1C:
            offset_name = "PLL_CON7_%s_CP" % self.name
            val = self.con[7]
        # PLL_CON8_x_CP
        # not sure if this is a part of the con structure, it might be from
        # something else. Seems to hold a boolean factor of 150 or 500 for
        # clkpllup.
        elif offset == 0x20:
            offset_name = "PLL_CON8_%s_CP" % self.name
            val = self.con[8]

        if val is not None:
            self.log_read(val, size, offset_name)
            return val
        
        return super().hw_read(offset, size, offset_name, *args, **kwargs)

    def hw_write(self, offset, size, value, *args, **kwargs):
        offset_name = None
        assert size == 4
        if offset == 0:
            offset_name = "PLL_CON0_%s_CP" % self.name
            self.con[0] = value
        elif offset == 4:
            offset_name = "PLL_CON1_%s_CP" % self.name
            self.con[1] = value
        elif offset == 8:
            offset_name = "PLL_CON2_%s_CP" % self.name
            self.con[2] = value
        elif offset == 0xC:
            offset_name = "PLL_CON3_%s_CP" % self.name
            if extract_bits(value, 0x1f, 1):
                self.con[3] |= 1 << 0x1f
                # this bit is set when the PLL says it's ready to work.
                # we make it work immediately.
                self.con[3] |= 1 << 0x1d
            else:
                self.con[3] &= ~(1 << 0x1f)
                self.con[3] &= ~(1 << 0x1d)

        elif offset == 0x10:
            offset_name = "PLL_CON4_%s_CP" % self.name
            self.con[4] = value
        elif offset == 0x14:
            offset_name = "PLL_CON5_%s_CP" % self.name
            self.con[5] = value
        elif offset == 0x18:
            offset_name = "PLL_CON6_%s_CP" % self.name
            if extract_bits(value, 0x1f, 1):
                self.con[6] |= 1 << 0x1f
                # this bit is set when the PLL says it's ready to work.
                # we make it work immediately.
                self.con[6] |= 1 << 0x1d
            else:
                self.con[6] &= ~(1 << 0x1f)
                self.con[6] &= ~(1 << 0x1d)

        elif offset == 0x1C:
            offset_name = "PLL_CON7_%s_CP" % self.name
            self.con[7] = value
        elif offset == 0x20:
            offset_name = "PLL_CON8_%s_CP" % self.name
            self.con[8] = value
        else:
            return super().hw_write(offset, size, value, offset_name, *args, **kwargs)
        self.log_write(value, size, offset_name)
        
        return True
    def __init__(self, name, address, size, **kwargs):
        super().__init__(name, address, size, **kwargs)

        self.enabled = False
        self.con = [0] * 9
        
        self.read_handler[0:size] = self.hw_read
        self.write_handler[0:size] = self.hw_write
