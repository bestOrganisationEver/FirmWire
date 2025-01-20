## Copyright (c) 2022, Team FirmWire
## SPDX-License-Identifier: BSD-3-Clause
from firmwire.hw import soc
import firmwire.loader
import logging
import tarfile
import zipfile
import filetype
import lz4.frame
import re
import os

from pathlib import PurePath

from firmwire.vendor.shannon.mpu import AddressRange

from .TOCFile import *
from avatar2 import *

import firmwire.vendor.exy5400 as exy5400
import firmwire.vendor.exy5400.mmu
import firmwire.vendor.exy5400.soc

from firmwire.hw.soc import get_soc
from .hw import *
from firmwire.hw.glink import GLinkPeripheral
from firmwire.emulator.patterndb import PatternDB, PatternDBEntry
from .machine import Exy5400Machine
from .pattern import PATTERNS

log = logging.getLogger(__name__)


# class ARM_CORTEX_R7(ARM):
#     cpu_model = "cortex-r7"
#     qemu_name = "arm"
#     gdb_name = "arm"
#     angr_name = "arm"

#     capstone_arch = CS_ARCH_ARM
#     capstone_mode = CS_MODE_LITTLE_ENDIAN | CS_MODE_THUMB
#     keystone_arch = KS_ARCH_ARM
#     keystone_mode = KS_MODE_LITTLE_ENDIAN | KS_MODE_THUMB
#     unicorn_arch = UC_ARCH_ARM
#     unicorn_mode = UC_MODE_LITTLE_ENDIAN | UC_MODE_THUMB

#     @staticmethod
#     def init(avatar):
#         pass


class ARM_CORTEX_A55(ARM):
    cpu_model = "cortex-a55"
    qemu_name = "aarch64"
    gdb_name = "arm"
    angr_name = "aarch64"
    capstone_arch = CS_ARCH_ARM64
    capstone_mode = CS_MODE_LITTLE_ENDIAN
    keystone_arch = KS_ARCH_ARM64
    keystone_mode = KS_MODE_LITTLE_ENDIAN | KS_MODE_ARM
    unicorn_arch = UC_ARCH_ARM64
    unicorn_mode = UC_MODE_LITTLE_ENDIAN | UC_MODE_ARM

    @staticmethod
    def init(avatar):
        pass

class Exy5400Loader(firmwire.loader.Loader):
    NAME = "exy5400"
    LOADER_ARGS = {
        "nv_data": {"type": PurePath, "help": "A path to a NV_DATA.bin file"},
        # TODO: find the revision, and find a way to findd it out during try_load and remove this.
        "is_s24": {
            "type": bool,
            "help": "If the SoC is the Exynos 5400 chip in the Samsung S24. (Unknown revision)",
        },
    }

    @property
    def ARCH(self):
        return ARM_CORTEX_A55

    @staticmethod
    def is_relevant(path):
        ft = filetype.guess(path)
        return (
            ft is not None and ft.mime in ["application/x-lz4", "application/x-tar"]
        ) or path.endswith(".bin")

    def try_load(self):
        # Make sure the path is a valid TOC file
        if not self.toc_load_modem_file(self.path):
            return False

        # We need the SoC version to handle quirks and memory layout changes
        if not self.guess_soc_version():
            return False

        # We now have an extracted TOC file and selected SoC definition

        # Resolve symbol patterns
        self.unsafe_regions = []

        # Set during patterndb finding
        self.task_layout = None

        try:
            db = PatternDB(self)

            for name, entry in PATTERNS.items():
                pat = PatternDBEntry(name)
                for k, v in entry.items():
                    setattr(pat, k, v)

                db.add_pattern(pat)

            main_toc = self.modem_file.get_section("MAIN")
            db.find_patterns(main_toc.data, main_toc.load_address)
        except ValueError as e:
            log.exception("Error resolving symbols")
            return False

        # assert self.task_layout is not None

        if not self.build_memory_map():
            return False

        self._machine_class = Exy5400Machine

        return True

    def build_memory_map(self):
        #######################
        # MPU Memory Map
        #######################

        modem_main = self.modem_file.get_section("MAIN")
        sym = self.symbol_table.lookup("boot_mmu_table")
        # XXX: poor man's hand-written mmu table. we now have the correct
        # table so let's switch to that, and remove this after.
        if self.loader_args.get("is_s24"):
            # some sp gets set to 0x471c4fd8 at some point. (holds at PC 
            # 0x42be9424) assuming the ram here is contiguous, it's reasonable
            # to assume it goes up to 0x08000000
            mpu_entries = [firmwire.vendor.exy5400.mmu.MMUSectionEntry(
                0, 0x40000000, 0x40000000, 0x08000000, (0 << 15) | (0b11 << 10)
            )]
        elif sym is None:
            log.error(
                "Unable to find MPU table in modem binary. Cannot create memory map"
            )
            return False
        else:
            mpu_entries = exy5400.mmu.parse_mmu_table(modem_main, sym.address)
        table = exy5400.mmu.consolidate_mpu_table(mpu_entries)
        self.mmu_table = table

        for entry in table:
            mmu = entry.mmu
            name = "MMU%d_%08x" % (mmu.mapping_idx, entry.start)
            print(name, hex(entry.size), mmu.get_rwx_str(is_priv=True))
            # XXX: how do permissions work here?
            self.add_memory_range(
                entry.start, entry.size, name=name, permissions=mmu.get_rwx_str(is_priv=True)
            )

        #######################
        # TOC File Memory Map
        #######################

        loader_workspace = self.workspace.path("/loader")
        loader_workspace.mkdir()

        # extract individual sections for the PANDA configurable machine to load
        for entry in self.modem_file.entries:
            if not entry.meta_section:
                size = entry.size
                section_path = loader_workspace.join(
                    "modem_%08x.bin" % entry.load_address
                )

                with section_path.open(mode="wb") as fp:
                    fp.write(entry.data)

                # TODO: add memory map merging to prevent this hardcode
                # if entry.name == "MAIN":
                #     size = 0x3000000

                # round up and page align
                if size % 0x1000 != 0:
                    size = (size + 0x1000) & ~0x1000

                name = "TOC_" + entry.name

                if not entry.name == "BOOT":

                    self.add_memory_range(
                        entry.load_address, size, file=section_path.to_path(), name=name
                    )

                # It is still unclear why we need boot in high AND low
                # (probably interrupts vectors need to be at 0x0)
                else:

                    self.add_memory_range(
                        0x00000000,
                        size,
                        file=section_path.to_path(),
                        name=name + "_LOW",
                    )

        ########################
        # Peripheral Memory Map
        ########################

        for peripheral in self.modem_soc.peripherals:
            self.create_soc_peripheral(peripheral)

        self.create_timer(self.modem_soc.TIMER_BASE + 0x000, 0x100, "tim0", 34, 100000)
        self.create_timer(self.modem_soc.TIMER_BASE + 0x100, 0x100, "tim1", 35, 6000000)
        self.create_timer(self.modem_soc.TIMER_BASE + 0x200, 0x100, "tim2", 36, 6000000)
        self.create_timer(self.modem_soc.TIMER_BASE + 0x300, 0x100, "tim3", 37, 6000000)
        self.create_timer(self.modem_soc.TIMER_BASE + 0x400, 0x100, "tim4", 38, 6000000)
        self.create_timer(self.modem_soc.TIMER_BASE + 0x500, 0x100, "tim5", 39, 6000000)

        self.create_peripheral(ShannonTCU, 0x8200F000, 0x100, name="TCU")

        self.create_peripheral(
            self.modem_soc.CLK_PERIPHERAL,
            self.modem_soc.SOC_CLK_BASE,
            0x200000,
            name="SOC_CLK",
        )

        # This has the CHIP_ID
        self.create_peripheral(
            ShannonSOCPeripheral, self.modem_soc.SOC_BASE, 0x2000, name="SOC"
        )

        self.create_peripheral(UARTPeripheral, 0x84000000, 0x1000, name="boot_uart")
        self.create_peripheral(Unknown2Peripheral, 0x81002000, 0x1000, name="unk_per8")

        # @ 40000958: 0x4b200c00
        # This contains CHIP MODE and communication FIFO
        # Matches with DTB from Kernel offset
        # modem-s5000ap-sipc-pdata.dtsi (shmem,ipc_offset = <0xB200000>)
        self.create_peripheral(
            SHMPeripheral, self.modem_soc.SHM_BASE, 0x500000, name="SHM"
        )

        # @ 40000834: 8f920008
        self.create_peripheral(
            SIPCPeripheral, self.modem_soc.SIPC_BASE, 0x1000, name="SIPC"
        )

        # 0x8f900080 @ 0x4103e6f6: ldr     r3, [r0]
        self.create_peripheral(LoggingPeripheral, 0x8F900000, 0x1000, name="unk_per10")

        self.create_peripheral(LoggingPeripheral, 0x8FC30000, 0x1000, name="usi1")
        self.create_peripheral(LoggingPeripheral, 0x8FC22000, 0x1000, name="usi2")
        self.create_peripheral(LoggingPeripheral, 0x8FC60000, 0x1000, name="usi3")
        self.create_peripheral(LoggingPeripheral, 0x8FD20000, 0x1000, name="usi4")
        self.create_peripheral(LoggingPeripheral, 0x40000000, 0x8000, name="boot")

        if self.modem_file.has_section("NV"):
            nv = self.modem_file.get_section("NV")
            nv_base_address = nv.load_address
            nv_data_size = nv.size
        # NOTE: this assumes that NV_PROT comes right after NV_NORM!
        elif self.modem_file.has_section("NV_NORM"):
            nv = self.modem_file.get_section("NV_NORM")
            nv_base_address = nv.load_address
            nv_data_size = nv.size * 2
        else:
            nv_base_address = 0x45600000
            nv_data_size = 0x100000
            log.warning(
                "Modem file does not have NV section information...defaulting to 0x%x",
                nv_base_address,
            )

        # size gathered from modem.bin TOC
        if self.loader_args["nv_data"]:
            nv_data_path = self.loader_args["nv_data"]

            if not os.access(nv_data_path, os.R_OK) or not os.path.isfile(nv_data_path):
                log.error("NV data file path is missing")
                return False

            nv_file_size = os.path.getsize(nv_data_path)

            if nv_file_size == 0:
                log.error("Blank NV data file provided")
                return False
            elif nv_file_size > nv_data_size:
                log.error(
                    "NV data file provided exceeds NV section size (0x%x > 0x%x)",
                    nv_file_size,
                    nv_data_size,
                )
                return False
            else:
                log.info(
                    "Loading NV data from file %s to %x (0x%x bytes)",
                    nv_data_path,
                    nv_base_address,
                    nv_data_size,
                )
                self.add_memory_range(
                    nv_base_address,
                    nv_data_size,
                    file=nv_data_path,
                    name="NV",
                    permissions="rw-",
                )
        else:
            log.info("Using blank NV data")
            self.add_memory_range(
                nv_base_address, nv_data_size, name="NV", permissions="rw-"
            )

        self.add_memory_range(
            0x80000000,
            0x2000,
            name="gic",
            qemu_name="a9mpcore_priv",  # hopefully close enough
            qemu_properties=[
                {"name": "num_cpu", "value": 1, "type": "int"},
                # max supported by shannon (0xLAB_42393f48)
                {"name": "num_irq", "value": 0x12A, "type": "int"},
            ],
        )

        self.add_memory_annotation(0x44200000, 0x1400000, "sysmem")
        self.add_memory_annotation(0x04000000, 0x1D000, "BIOS")
        self.add_memory_annotation(0x04100000, 0x06000000, "main.bin")
        self.add_memory_annotation(0xC1001000, 0x1000, "twog_something")
        # self.add_memory_annotation(0xc1800000, 0x5000, "marconi")
        # self.add_memory_annotation(0xc2000000, 0x1000, "marconi2")
        self.create_peripheral(CyclicBitPeripheral, 0xC1800000, 0x5000, name="marconi")
        self.create_peripheral(CyclicBitPeripheral, 0xC2000000, 0x1000, name="marconi2")

        # TODO: move GLINK peripheral creation to emulation time
        self.create_peripheral(GLinkPeripheral, 0xEC000000, 0x1000, name="glink")

        # self.add_memory_annotation(0x47f04000, 0x10000, "m_mem_unk_32_rxtx")
        self.create_peripheral(ShannonAbox, 0x47F00000, 0x14000, name="abox")
        self.add_memory_annotation(0xC1000000, 0x1000, "twog_something_2")

        # Referenced in the modem after powerup of domains
        # Faulting address: 0x80001108
        # Faulting PC: 0x4004546: str.w   r1, [r0, #0x104]
        self.add_memory_annotation(0x80000000, 0x2000, "unk_per7")

        return True

    def create_timer(self, start, size, name, irq_num, freq=1000000):
        self.add_memory_range
        props = [
            {"type": "uint32", "name": "irq_num", "value": irq_num},
            {"type": "uint32", "name": "freq", "value": freq},
        ]
        mr = self.add_memory_range(
            start,
            size,
            name=name,
            qemu_name="shannon_timer",
            qemu_properties=props,
            permissions="rw-",
        )
        return mr

    def toc_load_modem_file(self, path):
        modem_fp = self.open_modem_bin(path)

        if modem_fp is None:
            return False

        # load and parse the firmware image, recovering memory sections
        try:
            self.modem_file = TOCFile(modem_fp)
            modem_fp.close()
        except IOError as e:
            log.error("Failed to read the modem file: %s", e)
            return False
        except TOCFileException as e:
            log.error("Failed to parse the modem file: %s", e)
            return False

        main = self.modem_file.get_section("MAIN")

        # just keep an overlay copy of MAIN that isn't zeroed on boot
        self.trace_data_offset = main.load_address
        self.trace_data = main.data.tobytes()

        return True

    def open_modem_bin(self, path):
        if path.endswith(".bin"):
            return open(path, "rb")

        tfp = None

        # extract the firmware from a Samsung CP_* tar file LZ4 encoded or not
        try:
            if path.endswith("lz4"):
                lzfp = lz4.frame.open(open(path, "rb"))
                tfp = tarfile.open(fileobj=lzfp)
            else:
                tfp = tarfile.open(path, "r")
        except tarfile.ReadError as e:
            log.error("Not a valid tar file")
            return None

        files = tfp.getnames()

        if len(files) < 1:
            log.error("Modem CP tarfile needs at least modem.bin")
            return None

        if len(files) > 2:
            log.warning("Modem CP tarfile has unexpected number of files: %s", files)

        lz4_compressed = "lz4" in files[0]

        modem_name = "modem.bin"

        if lz4_compressed:
            modem_name += ".lz4"

        if modem_name not in files:
            log.error("Modem CP tarfile is missing required modem.bin")
            return None

        modem_fp = tfp.extractfile(modem_name)

        if lz4_compressed:
            modem_fp = lz4.frame.open(modem_fp)

        return modem_fp

    def guess_soc_version(self):
        main = self.modem_file.get_section("MAIN")
        if self.loader_args.get("is_s24", False):
            soc_guess = "S5123AP"
            soc_date = 20451201

        else:
            # from 0x40104d6c
            # Try to find the version with the date first
            found = re.search(
                rb"""
            (?P<SOC>[S][0-9]{3,}(AP)?) # SOC-ID
            _PROD_                    # Build type
            ([^_]+_[^\d_][^_]*)*      # Additional build data until we hit something
                                      # that starts with a digit. (which might be
                                      # the date?)

            (?P<date>[0-9]{8})        # Could be date as YYMMDD (for rough SoC revision)
            [^\x00]*                  # null terminator""",
                main.data,
                re.M | re.S | re.X,
            )

            # First pattern may fail for some OEM modified Shannon images
            if found is None:
                found = re.search(
                    rb"""
                (?P<SOC>[S][0-9]{3,}(AP)?) # SOC-ID
                .{,10}                    # garbage or unknown (usually underscores)
                [^\x00]*                  # null terminator""",
                    main.data,
                    re.M | re.S | re.X,
                )

                if found is None:
                    log.error(
                        "Unable to automatically determine the SoC type from the boot image"
                    )
                    return False

            soc_guess = found.group("SOC").decode()

            # SoC date is a best effort approach
            soc_date = (
                int(found.group("date").decode()) if "date" in found.groupdict() else 0
            )

            # Special handling for Moto One images; these don't use a classic date, but ID numbers
            if soc_guess == "S337AP":
                soc_date = int(found.group().split(b"SGCS_QB")[-1])

        self.modem_soc = get_soc(self.NAME, soc_guess)

        if self.modem_soc is None:
            print(soc.SOC_BY_NAME)
            log.error("Guessed SoC '%s' is not supported", soc_guess)
            return False

        # Initialize SoC object
        self.modem_soc = self.modem_soc(soc_date, main)

        log.info("SoC %s (automatic)", repr(self.modem_soc))

        return True


firmwire.loader.register_loader(Exy5400Loader)
