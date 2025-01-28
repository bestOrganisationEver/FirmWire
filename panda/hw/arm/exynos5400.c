/*
 * Exynos5400 impl, inspired by the SmartFusion2 SoC impl.
 *
 * Copyright (c) 2024 Can Acar, Baseband Security Lab
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

// TODO: switch to the normal qemu qom stuff. NOT EASY.

#include "qemu/osdep.h"

#include "cpu-qom.h"
// #include "exec/address-spaces.h"
// #include "hw/arm/boot.h"
#include "hw/arm/exynos5400.h"
// #include "target/arm/cpu-qom.h"
// #include "hw/loader.h"
// #include "hw/qdev-clock.h"
// #include "hw/qdev-properties.h"
#include "qapi/error.h"
// #include "qemu/units.h"

#define EXY5400_MAIN_BASE 0x40010000
#define EXY5400_MAIN_SIZE 128 * 1024 * 1024

static void exynos5400_soc_initfn(Object *obj) {
  // Exynos5400State *s = EXYNOS5400_SOC(obj);
  // int i;

  //   object_initialize_child(obj, "cpu", &s->cpu, TYPE_ARM_CPU);
}

static void exynos5400_soc_realize(DeviceState *dev_soc, Error **errp) {
  Exynos5400State *s = EXYNOS5400_SOC(dev_soc);
  ObjectClass *cpu_oc;

  cpu_oc = cpu_class_by_name(TYPE_ARM_CPU, "cortex-a55");
  assert(cpu_oc);

  for (int n = 0; n < EXYNOS5400_NCPUS; n++) {
    Object *cpuobj = object_new(object_class_get_name(cpu_oc));

    // object_property_add_child(OBJECT(s), "cpu[*]", cpuobj);

    if (object_property_find(cpuobj, "has_el3", NULL)) {
      object_property_set_bool(cpuobj, true, "has_el3", &error_fatal);
    }

    // boot.bin is tasked with setting this, just stub boot.bin out for now.
    // object_property_set_bool(cpuobj, "aarch64", false, &error_fatal);

    s->cpus[n] = ARM_CPU(cpuobj);
    object_property_set_bool(cpuobj, true, "realized", &error_fatal);

    // qdev_realize(DEVICE(cpuobj), NULL, &error_fatal);
  }
}

static void exynos5400_soc_class_init(ObjectClass *klass, void *data) {
  DeviceClass *dc = DEVICE_CLASS(klass);

  dc->realize = exynos5400_soc_realize;
}

static const TypeInfo exynos5400_soc_info = {
    .name = TYPE_EXYNOS5400_SOC,
    .parent = TYPE_SYS_BUS_DEVICE,
    .instance_size = sizeof(Exynos5400State),
    .instance_init = exynos5400_soc_initfn,
    .class_init = exynos5400_soc_class_init,
};

static void exynos5540_register_types(void) {
  type_register_static(&exynos5400_soc_info);
}

type_init(exynos5540_register_types)
