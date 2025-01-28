/*
 *  Samsung exynos5 SoC based boards emulation, inspired by exynos4_boards.c,
 *  which is (at the time of writing) authored by Samsung.
 *
 *  Copyright (c) 2024 Can Acar, Baseband Security Lab
 *
 *  This program is free software; you can redistribute it and/or modify it
 *  under the terms of the GNU General Public License as published by the
 *  Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful, but WITHOUT
 *  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 *  FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
 *  for more details.
 *
 *  You should have received a copy of the GNU General Public License along
 *  with this program; if not, see <http://www.gnu.org/licenses/>.
 *
 */

// TODO: qom'ify Exynos5BoardState.

#include "qemu/osdep.h"

// #include "arm-powerctl.h"
// #include "qemu/compiler.h"
#include "exec/address-spaces.h"
// #include "hw/arm/boot.h"
#include "hw/arm/arm.h"
#include "hw/arm/exynos5400.h"
#include "hw/boards.h"
// #include "hw/core/cpu.h"
// #include "hw/irq.h"
// #include "hw/loader.h"
// #include "hw/net/lan9118.h"
// #include "hw/qdev-properties.h"
#include "hw/sysbus.h"
// #include "net/net.h"
#include "qapi/error.h"
// #include "qemu/error-report.h"
// #include "qemu/units.h"
// #include "system/block-backend-global-state.h"
// #include "system/block-backend-io.h"
#include "sysemu/reset.h"
#include "target/arm/cpu-qom.h"
#include "target/arm/cpu.h"

#define EXYNOS5400_MAIN_BIN_BASE_ADDR (EXYNOS5400_DRAM0_BASE_ADDR + 0x00010000)
#define EXYNOS5400_BOOTBIN_MIRROR_SIZE (0x00010000)
// #define EXYNOS5400_BOOTLOADER_ADDR (EXYNOS5400_DRAM0_BASE_ADDR + 0x20000000)

typedef enum Exynos5BoardType {
  EXYNOS5400_BOARD_SMS24BB,
  EXYNOS5_NUM_OF_BOARDS
} Exynos5BoardType;

typedef struct Exynos5BoardState {
  Exynos5400State soc;
  MemoryRegion dram0_mem;
  MemoryRegion dram0_boot_bin_alias;
  // MemoryRegion dram1_mem;
} Exynos5BoardState;

static int exynos5_board_id[EXYNOS5_NUM_OF_BOARDS] = {
    [EXYNOS5400_BOARD_SMS24BB] = 0x6931,
};

static unsigned long exynos5_board_ram_size[EXYNOS5_NUM_OF_BOARDS] = {
    [EXYNOS5400_BOARD_SMS24BB] = 3 * 0x40000000ULL,
};

static struct arm_boot_info exynos5_board_binfo = {
    .loader_start = EXYNOS5400_MAIN_BIN_BASE_ADDR,
    // .entry = EXYNOS5400_BOOTLOADER_ADDR,
    .entry = EXYNOS5400_MAIN_BIN_BASE_ADDR,
    .is_linux = false,
};

static void exynos5_boards_init_ram(Exynos5BoardState *s,
                                    MemoryRegion *system_mem,
                                    unsigned long ram_size) {
  unsigned long mem_size = ram_size;

  if (mem_size > EXYNOS5400_DRAM_MAX_SIZE) {
    mem_size = EXYNOS5400_DRAM_MAX_SIZE;
  }

  /* Owners set to NULL because objects are not QOMified */
  memory_region_init_ram(&s->dram0_mem, /*OBJECT(s) segfault*/ NULL,
                         "exynos5400.dram0", mem_size, &error_fatal);
  memory_region_add_subregion(system_mem, EXYNOS5400_DRAM0_BASE_ADDR,
                              &s->dram0_mem);

  memory_region_init_alias(&s->dram0_boot_bin_alias, NULL,
                           "exynos5400.boot_bin_alias", &s->dram0_mem, 0,
                           EXYNOS5400_BOOTBIN_MIRROR_SIZE);
  memory_region_add_subregion(system_mem, 0,
                              &s->dram0_boot_bin_alias);
}

static Exynos5BoardState *
exynos5_boards_init_common(MachineState *machine, Exynos5BoardType board_type) {
  Exynos5BoardState *s = g_new(Exynos5BoardState, 1);

  // object_get_typename(OBJECT(machine));

  exynos5_board_binfo.ram_size = exynos5_board_ram_size[board_type];
  exynos5_board_binfo.board_id = exynos5_board_id[board_type];

  exynos5_boards_init_ram(s, get_system_memory(),
                          exynos5_board_ram_size[board_type]);


  object_initialize(&s->soc, sizeof(s->soc), TYPE_EXYNOS5400_SOC);
  object_property_add_child(OBJECT(machine), "soc", OBJECT(&s->soc),
                              &error_abort);
  object_property_set_bool(OBJECT(&s->soc), true, "realized", &error_fatal);
  // sysbus_realize(SYS_BUS_DEVICE(&s->soc), &error_fatal);

  return s;
}

// static const ARMInsnFixup stub_bootloader[] = {{0, FIXUP_TERMINATOR}};

static void sms24bb_init(MachineState *machine) {
  Exynos5BoardState *s =
      exynos5_boards_init_common(machine, EXYNOS5400_BOARD_SMS24BB);
  // static const uint32_t fixupcontext[FIXUP_MAX] = {0};
  // arm_load_kernel(s->soc.cpu[0], machine, &exynos5_board_binfo);
  // load_image_mr(const char *filename, MemoryRegion *mr)

  // load_image_size(blk_name(blk), EXYNOS5400_MAIN_BIN_BASE_ADDR, -
  // EXYNOS5400_DRAM0_BASE_ADDR + 0x00010000); cpu_set_pc(CPU(s->soc.cpu[0]),
  // 0x0);

  // arm_boot_address_space(s->soc.cpu[0], &exynos5_board_binfo);
  // arm_write_bootloader(
  //     "bootloader",
  //     arm_boot_address_space(s->soc.cpus[0], &exynos5_board_binfo),
  //     exynos5_board_binfo.entry, stub_bootloader, fixupcontext);
  // unset_feature(&s->soc.cpu[0]->env, ARM_FEATURE_AARCH64);

  // for (cs = first_cpu; cs; cs = CPU_NEXT(cs)) {
  //     ARM_CPU(cs)->env.boot_info = info;
  // }

  // arm_load_kernel(ARM_CPU(first_cpu), machine, &exynos5_board_binfo);
  // arm_set_cpu_on(0, loader_start.loader_start);
  // s->soc.cpus[0]->env.boot_info = &exynos5_board_binfo;

  // cpsr_write(env, mode_for_el[target_el], CPSR_M, CPSRWriteRaw);
  //   s->soc.cpu[0]->env.aarch64 = false;
}

static void exynos5_machine_reset(void) {
  ARMCPU *cpu;
  // Exynos5BoardState *soc = (Exynos5BoardState*)machine;

  qemu_devices_reset();

  // CPUs don't get reset on system reset (boot.c:arm_load_kernel). This is
  // good for us because now we get to mess with the whole CPU before main.bin
  // runs.

  cpu = ARM_CPU(first_cpu);
  cpu->env.aarch64 = false;
  // arm_emulate_firmware_reset(CPU(cpu), 1);
  cpu->env.pstate = PSTATE_MODE_EL1h;
  cpu_set_pc(CPU(cpu), exynos5_board_binfo.entry);
  // cpu->env.uncached_cpsr = ARM_CPU_MODE_SVC;

  // arm_rebuild_hflags(&cpu->env);

  // These are good to know for later if we want to mess even more, but we're
  // good for now. Also, we should probably call arm_rebuild_hflags after any
  // of these, as if we don't, TCG will be out of sync with our desired state.

  // aarch64_sync_64_to_32(&cpu->env);
  // helper_rebuild_hflags_a32(&cpu->env, new_el);
  // assert(cpu->env.aarch64 == false);
  // soc->cpu[0]->env.aarch64       = false;
}

// static const char *const valid_cpu_types[] = {ARM_CPU_TYPE_NAME("cortex-a55"),
//                                               NULL};

//   memory_region_init_rom(&s->mainbin, OBJECT(dev_soc), "EXY5400.MAIN",
//   EXY5400_MAIN_SIZE,
//                          &error_fatal);

// //   load_image_targphys(const char *filename, hwaddr, uint64_t max_sz)

//   memory_region_add_subregion(system_memory, EXY5400_MAIN_BASE, &s->mainbin);

static void sms24bb_class_init(ObjectClass *oc, void *data) {
  MachineClass *mc = MACHINE_CLASS(oc);

  mc->desc = "Samsung S24 baseband board (Exynos5540)";
  mc->init = sms24bb_init;
  // mc->valid_cpu_types = valid_cpu_types;
  mc->max_cpus = EXYNOS5400_NCPUS;
  // mc->min_cpus = EXYNOS5400_NCPUS;
  // mc->default_cpus = EXYNOS5400_NCPUS;
  mc->reset = exynos5_machine_reset;
  // mc->ignore_memory_transaction_failures = true;
}

static const TypeInfo sms24bb_type = {
    .name = MACHINE_TYPE_NAME("sms24bb"),
    .parent = TYPE_MACHINE,
    .class_init = sms24bb_class_init,
};

static void exynos5_machines_init(void) { type_register_static(&sms24bb_type); }

type_init(exynos5_machines_init)
