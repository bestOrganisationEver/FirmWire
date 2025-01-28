import importlib.resources as importlib_res
import importlib_resources
setattr(importlib_res, "files", importlib_resources.files)
setattr(importlib_res, "as_file", importlib_resources.as_file)

from pandare import Panda
def fake_sig_hdlr(*args, **kwargs):
	pass
Panda.setup_internal_signal_handler = fake_sig_hdlr
Panda._setup_internal_signal_handler = fake_sig_hdlr

import os
import subprocess
from avatar2 import *

A64_CODE = (b'\x81\x00\x80\xd2' # mov x1, 4
						b'\xa2\x01\x80\xd2')# mov x2, 13

def register_dump(qemu):
        print("dumping")
        R = qemu.regs
        dump = """\npc:  %016x      lr:  %016x      sp:  %016x
r0:  %016x      r1:  %016x      r2:  %016x
r3:  %016x      r4:  %016x      r5:  %016x
r6:  %016x      r7:  %016x      r8:  %016x
r9:  %016x      r10: %016x      r11: %016x
r12: %016x     cpsr: %016x""" % (
            R.pc,
            R.lr,
            R.sp,
            R.r0,
            R.r1,
            R.r2,
            R.r3,
            R.r4,
            R.r5,
            R.r6,
            R.r7,
            R.r8,
            R.r9,
            R.r10,
            R.r11,
            R.r12,
            R.cpsr,
        )
        print(dump)

class ARM_CORTEX_A55(ARM):
    cpu_model = "cortex-a55"
    qemu_name = "aarch64"
    gdb_name = "aarch64"
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

avatar = Avatar(arch=ARM_CORTEX_A55)
avatar.load_plugin("disassembler")
avatar.load_plugin("assembler")

target = avatar.add_target(PyPandaTarget,name="test",entry_address=0)

avatar.add_memory_range(0,size=0x10000, name="testmem", permissions='rwx')
avatar.init_targets()
print("writing mem")
target.write_memory(0, len(A64_CODE), A64_CODE, raw=True)
print("stepping")
target.step()
register_dump(target)
print("another step")
target.step()
register_dump(target)
avatar.shutdown()

