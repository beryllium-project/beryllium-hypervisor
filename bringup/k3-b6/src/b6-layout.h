/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the fixed K3 B6 layout (planning/k3-b6-plan.md, "Memory and
 *          load paths", "G-stage", and "Guest-physical layout"): the
 *          monitor image and G-stage pool, the staged boot image, the guest
 *          RAM window, the guest kernel and DTB placement, and the run
 *          limits. The monitor, the boot-image link, the guest device-tree
 *          generator, and the checkers all read these values, so they
 *          cannot drift apart.
 * Trust:   constants only. Every value is a literal inside BE_B6_C() so
 *          that scripts can parse it; C static assertions tie the derived
 *          values to their sources.
 * Scope:   B6 only. Usable from C, assembly, and preprocessed linker
 *          scripts (define __ASSEMBLER__ for the latter two).
 */

#ifndef BE_B6_LAYOUT_H
#define BE_B6_LAYOUT_H

#ifdef __ASSEMBLER__
#define BE_B6_C(value)			value
#else
#define BE_B6_C(value)			value##UL
#endif

/* The monitor flat image, as accepted and linked (B2's layout). */
#define BE_B6_MONITOR_HPA		BE_B6_C(0x102000000)
#define BE_B6_MONITOR_BYTES		BE_B6_C(0x34000)

/* The NOLOAD G-stage pool: a 16 KiB root, then one level-1 page. */
#define BE_B6_POOL_HPA			BE_B6_C(0x102034000)
#define BE_B6_POOL_BYTES		BE_B6_C(0x8000)
#define BE_B6_ROOT_HPA			BE_B6_C(0x102034000)
#define BE_B6_ROOT_BYTES		BE_B6_C(0x4000)
#define BE_B6_LEVEL1_HPA		BE_B6_C(0x102038000)
#define BE_B6_HGATP			BE_B6_C(0x8000000000102034)

/* The boot image, staged by every loader at L. */
#define BE_B6_STAGING_HPA		BE_B6_C(0x108000000)
#define BE_B6_BOOT_MONITOR_OFFSET	BE_B6_C(0x1000)
#define BE_B6_BOOT_KERNEL_OFFSET	BE_B6_C(0x35000)
#define BE_B6_BOOT_IMAGE_MAX		BE_B6_C(0x400000)
#define BE_B6_KERNEL_FILE_MAX		BE_B6_C(0x400000)
#define BE_B6_KERNEL_IMAGE_SIZE_MAX	BE_B6_C(0x800000)
#define BE_B6_KERNEL_TEXT_OFFSET	BE_B6_C(0x200000)
#define BE_B6_DTB_BYTES			BE_B6_C(0x1000)
#define BE_B6_PAYLOAD_ALIGN		BE_B6_C(0x1000)

/* Loader placement: booti RAM bases, and the kexec FDT after the image. */
#define BE_B6_UBOOT_RAM_BASE		BE_B6_C(0x102000000)
#define BE_B6_UBOOT_TEXT_OFFSET		BE_B6_C(0x6000000)
#define BE_B6_QEMU_RAM_BASE		BE_B6_C(0x80000000)
#define BE_B6_QEMU_TEXT_OFFSET		BE_B6_C(0x88000000)
#define BE_B6_KEXEC_FDT_ALIGN		BE_B6_C(0x200000)
#define BE_B6_KEXEC_FDT_MAX		BE_B6_C(0x200000)

/* The guest RAM window (Q1: 64 MiB), mapped by 2 MiB leaves. */
#define BE_B6_GUEST_GPA			BE_B6_C(0x80000000)
#define BE_B6_GUEST_HPA			BE_B6_C(0x110000000)
#define BE_B6_GUEST_BYTES		BE_B6_C(0x4000000)
#define BE_B6_GUEST_LEAF_BYTES		BE_B6_C(0x200000)
#define BE_B6_GUEST_LEAVES		BE_B6_C(32)

/* Guest placement and entry. */
#define BE_B6_KERNEL_GPA		BE_B6_C(0x80200000)
#define BE_B6_DTB_GPA			BE_B6_C(0x83e00000)
#define BE_B6_GUEST_HART		BE_B6_C(0)
#define BE_B6_TIMEBASE_HZ		BE_B6_C(24000000)

/* Run limits and the provisional SBI identity (Q6). */
#define BE_B6_EXIT_CEILING		BE_B6_C(0x100000)
#define BE_B6_GUEST_TIME_BUDGET		BE_B6_C(0x100000000)
/* The QEMU-only negative variants exit-budget and guest-timeout. */
#define BE_B6_VARIANT_EXIT_CEILING	BE_B6_C(64)
#define BE_B6_VARIANT_GUEST_TIME_BUDGET	BE_B6_C(0x100000)
#define BE_B6_SBI_IMPL_ID		BE_B6_C(0x4245)
#define BE_B6_SBI_IMPL_VERSION		BE_B6_C(2)

#ifndef __ASSEMBLER__
_Static_assert(BE_B6_POOL_HPA == BE_B6_MONITOR_HPA + BE_B6_MONITOR_BYTES,
	       "the pool follows the accepted flat image");
_Static_assert(BE_B6_LEVEL1_HPA == BE_B6_ROOT_HPA + BE_B6_ROOT_BYTES,
	       "the level-1 page follows the root");
_Static_assert(BE_B6_HGATP == ((BE_B6_C(8) << 60) | (BE_B6_ROOT_HPA >> 12)),
	       "hgatp is Sv39x4, VMID 0, at the root");
_Static_assert(BE_B6_BOOT_KERNEL_OFFSET ==
	       BE_B6_BOOT_MONITOR_OFFSET + BE_B6_MONITOR_BYTES,
	       "the kernel follows the monitor in the boot image");
_Static_assert(BE_B6_UBOOT_RAM_BASE + BE_B6_UBOOT_TEXT_OFFSET ==
	       BE_B6_STAGING_HPA, "booti places the board image at L");
_Static_assert(BE_B6_QEMU_RAM_BASE + BE_B6_QEMU_TEXT_OFFSET ==
	       BE_B6_STAGING_HPA, "booti places the QEMU image at L");
_Static_assert(BE_B6_GUEST_LEAVES * BE_B6_GUEST_LEAF_BYTES ==
	       BE_B6_GUEST_BYTES, "the leaves cover the window");
_Static_assert(BE_B6_KERNEL_GPA == BE_B6_GUEST_GPA + BE_B6_KERNEL_TEXT_OFFSET,
	       "the kernel sits at its text_offset");
_Static_assert(BE_B6_DTB_GPA == BE_B6_GUEST_GPA + BE_B6_GUEST_BYTES -
	       BE_B6_GUEST_LEAF_BYTES, "the DTB starts the last 2 MiB");
_Static_assert(BE_B6_STAGING_HPA + BE_B6_BOOT_IMAGE_MAX + BE_B6_KEXEC_FDT_ALIGN +
	       BE_B6_KEXEC_FDT_MAX <= BE_B6_GUEST_HPA,
	       "the staged image and the kexec FDT end below the window");
#endif

#endif /* BE_B6_LAYOUT_H */
