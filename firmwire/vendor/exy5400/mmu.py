## Copyright (c) 2022, Team FirmWire
## Copyright (c) 2024, Baseband Security Lab
## SPDX-License-Identifier: BSD-3-Clause
import struct
import intervaltree
import logging

AP_NAME = ["NA", "P_RW", "P_RW/U_RO", "RW", "RESV", "P_RO/U_NA", "RO", "RESV"]

log = logging.getLogger(__name__)


# T[APX][AP] encodes (priv r/w, unpriv r/w)
MMU_APX_AP_LOOKUP_TABLE = [
    # APX = 0
    [
        ((False, False), (False, False)),  # AP = 0
        ((True, True), (False, False)),  # AP = 1
        ((True, True), (True, False)),  # AP = 2
        ((True, True), (True, True)),  # AP = 3
    ],
    # APX = 1
    [
        # Reserved, user must check this is not being used.
        ((False, False), (False, False)),  # AP = 0
        # These are applicable
        ((True, False), (False, False)),  # AP = 1
        ((True, False), (True, False)),  # AP = 2
        ((True, False), (True, False)),  # AP = 3, same as AP = 2
    ],
]


# This is a "First Level Descriptor" in the table pointed to by TTBR0, that
# corresponds to a "Section" entry.
class MMUSectionEntry(object):
    def __init__(
        self, mapping_idx: int, virt_base: int, phys_base: int, phys_end: int, flags: int
    ):
        print(list(map(hex, (virt_base, phys_base, phys_end, flags))))
        
        # this is occupied by the Section indicator, 0b10.
        # this indicator gets or'd into the flags passed into this class
        # in the firmware. Nonetheless, the firmware has some entries with a
        # set LSB. This is why we also accept a 1.
        assert flags & 0b11 in (0, 1), flags

        # this is not a part of the MMU table spec for ARM but the "unpacker"
        # for the mmu table at 0x40a38524  can and does write over mappings
        # made by previous entries in the "compressed" table at 0x430178ac.
        # Therefore, we need to keep track of which entries come first.
        self.mapping_idx = mapping_idx

        self.virt_base = virt_base
        self.phys_base = phys_base
        self.phys_end = phys_end
        self.flags = flags

        # https://developer.arm.com/documentation/ddi0333/h/memory-management-unit/mmu-descriptors/first-level-descriptor
        NS = (flags >> 19) & 0b1
        assert ((flags >> 18) & 0b1) == 0
        nG = (flags >> 17) & 0b1
        S = (flags >> 16) & 0b1
        APX = (flags >> 15) & 0b1
        TEX = (flags >> 12) & 0b111
        AP = (flags >> 10) & 0b11
        XN = (flags >> 4) & 1
        C = (flags >> 3) & 1
        B = (flags >> 2) & 1

        self.executable = not bool(XN)

        # print(MMU_APX_AP_LOOKUP_TABLE[APX][AP])
        (self.priv_readable, self.priv_writable), (
            self.unpriv_readable,
            self.unpriv_writable,
        ) = MMU_APX_AP_LOOKUP_TABLE[APX][AP]

    def get_size(self):
        return self.phys_end - self.phys_base

    def get_virt_start(self):
        return self.virt_base

    def get_virt_end(self):
        return self.virt_base + self.get_size()-1

    def get_rwx_str(self, is_priv: bool):
        if is_priv:
            rb = self.priv_readable
            wb = self.priv_writable
        else:
            rb = self.unpriv_readable
            wb = self.unpriv_writable

        r = "r" if rb else "-"
        w = "w" if wb else "-"
        x = "x" if self.executable else "-"
        return "%c%c%c" % (r, w, x)

    def __repr__(self):

        return "<MMUEntry [%08x, %08x] phys_base=%08x priv_perm=%s>" % (
            self.get_virt_start(),
            self.get_virt_end(),
            self.phys_base,
            self.get_rwx_str(is_priv=True),
        )


class AddressItem(object):
    def __init__(self, addr, mpu, priority, end):
        self.addr = addr
        self.mpu = mpu
        self.priority = priority
        self.end = end

    def __repr__(self):
        return "<AddressItem [%08x] end=%s>" % (self.addr, self.end)


class AddressRange(object):
    def __init__(self, start: int, size: int , mpu: MMUSectionEntry):
        self.start = start
        self.size = size
        self.mmu = mpu

    def __repr__(self):
        return "<AddressRange [%08x, %08x] mpu=%s>" % (
            self.start,
            self.start + self.size,
            self.mmu,
        )


def parse_mmu_table(modem_main, address):
    entries = []

    data = modem_main.data
    address -= modem_main.load_address

    for mapping_idx in range(0x1B):
        # some of these mappings are coarse, some of them are sections. Figure
        # out what is what!
        # if mapping_idx == 0:
        #     coarse_page_table = True
        # else:
        #     coarse_page_table = False
        # print(hex(address+modem_main.load_address))

        virt_start, phys_start, size, flags = struct.unpack(
            "4I", data[address : address + 0x4 * 4]
        )
        # for a 0x100000 mapping:
        # *(base + (virt_start >> 20 << 2)) = phys_start | flags | 2
        address += 0x10

        # virt_start

        # in the binary these are effectively OR'd using ADD
        # access_control = sum(access_control)
        # size_select = (size >> 1) & 0b11111

        # size_bytes = 2 ** (8 + size_select - 7)

        # if size_select < 7:
        #     log.warning(
        #         "MPU table entry has an illegal size choice (%d). As per the Cortex-R reference manual, 7 should be the lowest. Rounding up...",
        #         size_bytes,
        #     )
        #     #  Even this size is a bit small for QEMU, which expects stricter alignment
        #     size_select = 7

        # if slot == 0xFF:
        #     break

        entry = MMUSectionEntry(mapping_idx, virt_start, phys_start, size, flags)
        entries.append(entry)

    print(entries)

    return entries


"""
Takes a list of MPU entries and converts them to a list of memory ranges with permissions
while taking into account how MPU entries are processed in the hardware. This handles
the case of MPU entry ranges overlapping with each other with different permissions.

For instance, one large range of read only memory with small spots of executable or
writable memory.
"""


def consolidate_mpu_table(entries: list[MMUSectionEntry]) -> list[AddressRange]:
    addr_entries = []
    final_entries = []
    for e in entries:
        addr_entries += [AddressItem(e.get_virt_start(), e, e.mapping_idx, False)]
        addr_entries += [AddressItem(e.get_virt_end(), e, e.mapping_idx, True)]

    addr_entries = sorted(addr_entries, key=lambda x: (x.addr, int(x.end)))
    # print(addr_entries)
    active = {}

    # https://softwareengineering.stackexchange.com/questions/363091/split-overlapping-ranges-into-all-unique-ranges
    for i, e in enumerate(addr_entries[:-1]):
        en = addr_entries[i + 1]
        if e.end:
            del active[e.priority]
        else:
            active[e.priority] = e.mpu

        start = e.addr if not e.end else e.addr + 1
        end = en.addr - 1 if not en.end else en.addr

        if start <= end and len(active):
            mpu = active[max(active)]
            final_entries += [AddressRange(start, end - start + 1, mpu)]

    return final_entries
