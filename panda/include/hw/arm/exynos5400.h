/*
 * Exynos5400 SoC emulation
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

#ifndef ARM_EXYNOS5400_H
#define ARM_EXYNOS5400_H

// #include "hw/arm/boot.h"
#include "qemu/osdep.h"
#include "hw/sysbus.h"
#include "qom/object.h"
#include "target/arm/cpu-qom.h"


#define TYPE_EXYNOS5400_SOC     "exynos5400-soc"

#define EXYNOS5400_SOC(obj) \
    OBJECT_CHECK(Exynos5400State, (obj), TYPE_EXYNOS5400_SOC)
// OBJECT_DECLARE_SIMPLE_TYPE(Exynos5400State, EXYNOS5400_SOC)

// lie, probably
#define EXYNOS5400_NCPUS                    1

#define EXYNOS5400_DRAM0_BASE_ADDR          ((uint64_t)0x40000000)

// no idea if this is right.
#define EXYNOS5400_DRAM_MAX_SIZE            ((uint64_t)0x60000000)  /* 1.5 GB */

typedef struct Exynos5400State {
    /*< private >*/
    SysBusDevice parent_obj;

    /*< public >*/
    ARMCPU *cpus[EXYNOS5400_NCPUS];
} Exynos5400State;

#endif /* ARM_EXYNOS5400_H */
