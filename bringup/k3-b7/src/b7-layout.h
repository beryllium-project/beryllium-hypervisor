/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the fixed K3 B7 layout (planning/k3-b7-plan.md, "Budgets",
 *          "Memory and load paths", and "G-stage and VMIDs"): the monitor
 *          image and the two-root G-stage pool, the staged boot image, the
 *          two guest RAM windows and their VMIDs, the guest kernel and DTB
 *          placement, the HS slice, and the run limits. The monitor, the
 *          boot-image link, the guest device-tree generator, and the
 *          checkers all read these values, so they cannot drift apart.
 * Trust:   constants only. Every value is a literal inside BE_B7_C() so
 *          that scripts can parse it; C static assertions tie the derived
 *          values to their sources.
 * Scope:   B7 only. Usable from C, assembly, and preprocessed linker
 *          scripts (define __ASSEMBLER__ for the latter two).
 */

#ifndef BE_B7_LAYOUT_H
#define BE_B7_LAYOUT_H

#ifdef __ASSEMBLER__
#define BE_B7_C(value)			value
#else
#define BE_B7_C(value)			value##UL
#endif

/* The monitor flat image, as accepted and linked (B2's layout). */
#define BE_B7_MONITOR_HPA		BE_B7_C(0x102000000)
#define BE_B7_MONITOR_BYTES		BE_B7_C(0x34000)

/*
 * The NOLOAD G-stage pool: two B6-shaped 32 KiB pools, one per guest,
 * each a 16 KiB root and then one level-1 page.
 */
#define BE_B7_GUESTS			BE_B7_C(2)
#define BE_B7_POOL_HPA			BE_B7_C(0x102034000)
#define BE_B7_POOL_BYTES		BE_B7_C(0x10000)
#define BE_B7_GUEST_POOL_BYTES		BE_B7_C(0x8000)
#define BE_B7_ROOT_BYTES		BE_B7_C(0x4000)
#define BE_B7_G0_ROOT_HPA		BE_B7_C(0x102034000)
#define BE_B7_G0_LEVEL1_HPA		BE_B7_C(0x102038000)
#define BE_B7_G1_ROOT_HPA		BE_B7_C(0x10203c000)
#define BE_B7_G1_LEVEL1_HPA		BE_B7_C(0x102040000)

/* Distinct VMIDs (Q2) and each guest's hgatp: Sv39x4, VMID, root. */
#define BE_B7_G0_VMID			BE_B7_C(1)
#define BE_B7_G1_VMID			BE_B7_C(2)
#define BE_B7_G0_HGATP			BE_B7_C(0x8000100000102034)
#define BE_B7_G1_HGATP			BE_B7_C(0x800020000010203c)

/* The boot image, staged by every loader at L. */
#define BE_B7_STAGING_HPA		BE_B7_C(0x108000000)
#define BE_B7_BOOT_MONITOR_OFFSET	BE_B7_C(0x1000)
#define BE_B7_BOOT_KERNEL_OFFSET	BE_B7_C(0x35000)
#define BE_B7_BOOT_IMAGE_MAX		BE_B7_C(0x400000)
#define BE_B7_KERNEL_FILE_MAX		BE_B7_C(0x400000)
#define BE_B7_KERNEL_IMAGE_SIZE_MAX	BE_B7_C(0x800000)
#define BE_B7_KERNEL_TEXT_OFFSET	BE_B7_C(0x200000)
#define BE_B7_DTB_BYTES			BE_B7_C(0x1000)
#define BE_B7_PAYLOAD_ALIGN		BE_B7_C(0x1000)

/*
 * Loader placement: the booti RAM bases (B3's header stays in the image;
 * QEMU boots it at the same L), and the kexec FDT after the image.
 */
#define BE_B7_UBOOT_RAM_BASE		BE_B7_C(0x102000000)
#define BE_B7_UBOOT_TEXT_OFFSET		BE_B7_C(0x6000000)
#define BE_B7_QEMU_RAM_BASE		BE_B7_C(0x80000000)
#define BE_B7_QEMU_TEXT_OFFSET		BE_B7_C(0x88000000)
#define BE_B7_KEXEC_FDT_ALIGN		BE_B7_C(0x200000)
#define BE_B7_KEXEC_FDT_MAX		BE_B7_C(0x200000)

/* The two guest RAM windows (Q3), each 64 MiB of 2 MiB leaves. */
#define BE_B7_GUEST_GPA			BE_B7_C(0x80000000)
#define BE_B7_GUEST_BYTES		BE_B7_C(0x4000000)
#define BE_B7_GUEST_LEAF_BYTES		BE_B7_C(0x200000)
#define BE_B7_GUEST_LEAVES		BE_B7_C(32)
#define BE_B7_G0_HPA			BE_B7_C(0x110000000)
#define BE_B7_G1_HPA			BE_B7_C(0x114000000)

/* Guest placement and entry, the same in each window. */
#define BE_B7_KERNEL_GPA		BE_B7_C(0x80200000)
#define BE_B7_DTB_GPA			BE_B7_C(0x83e00000)
#define BE_B7_GUEST_HART		BE_B7_C(0)
#define BE_B7_TIMEBASE_HZ		BE_B7_C(24000000)

/* The HS slice (Q1): 10 ms at 24 MHz. */
#define BE_B7_SLICE_TICKS		BE_B7_C(240000)

/* Run limits (per guest exits; one run budget) and the SBI identity (Q7). */
#define BE_B7_EXIT_CEILING		BE_B7_C(0x100000)
#define BE_B7_GUEST_TIME_BUDGET		BE_B7_C(0x100000000)
/* The QEMU-only negative variants exit-budget and guest-timeout. */
#define BE_B7_VARIANT_EXIT_CEILING	BE_B7_C(64)
#define BE_B7_VARIANT_GUEST_TIME_BUDGET	BE_B7_C(0x100000)
#define BE_B7_SBI_IMPL_ID		BE_B7_C(0x4245)
#define BE_B7_SBI_IMPL_VERSION		BE_B7_C(3)

#ifndef __ASSEMBLER__
_Static_assert(BE_B7_POOL_HPA == BE_B7_MONITOR_HPA + BE_B7_MONITOR_BYTES,
	       "the pool follows the accepted flat image");
_Static_assert(BE_B7_POOL_BYTES == BE_B7_GUESTS * BE_B7_GUEST_POOL_BYTES,
	       "the pool holds one B6-shaped pool per guest");
_Static_assert(BE_B7_G0_ROOT_HPA == BE_B7_POOL_HPA,
	       "G0's root starts the pool");
_Static_assert(BE_B7_G1_ROOT_HPA == BE_B7_G0_ROOT_HPA + BE_B7_GUEST_POOL_BYTES,
	       "G1's root starts the second pool");
_Static_assert(BE_B7_G0_LEVEL1_HPA == BE_B7_G0_ROOT_HPA + BE_B7_ROOT_BYTES,
	       "G0's level-1 page follows its root");
_Static_assert(BE_B7_G1_LEVEL1_HPA == BE_B7_G1_ROOT_HPA + BE_B7_ROOT_BYTES,
	       "G1's level-1 page follows its root");
_Static_assert((BE_B7_G0_ROOT_HPA & (BE_B7_ROOT_BYTES - 1)) == 0 &&
	       (BE_B7_G1_ROOT_HPA & (BE_B7_ROOT_BYTES - 1)) == 0,
	       "each Sv39x4 root is 16 KiB aligned");
_Static_assert(BE_B7_G0_HGATP == ((BE_B7_C(8) << 60) | (BE_B7_G0_VMID << 44) |
				  (BE_B7_G0_ROOT_HPA >> 12)),
	       "G0's hgatp is Sv39x4, VMID 1, at its root");
_Static_assert(BE_B7_G1_HGATP == ((BE_B7_C(8) << 60) | (BE_B7_G1_VMID << 44) |
				  (BE_B7_G1_ROOT_HPA >> 12)),
	       "G1's hgatp is Sv39x4, VMID 2, at its root");
_Static_assert(BE_B7_G0_VMID != BE_B7_G1_VMID && BE_B7_G0_VMID != 0 &&
	       BE_B7_G1_VMID != 0, "the guests have distinct nonzero VMIDs");
_Static_assert(BE_B7_POOL_HPA + BE_B7_POOL_BYTES <= BE_B7_STAGING_HPA,
	       "the pool ends below the staged image");
_Static_assert(BE_B7_BOOT_KERNEL_OFFSET ==
	       BE_B7_BOOT_MONITOR_OFFSET + BE_B7_MONITOR_BYTES,
	       "the kernel follows the monitor in the boot image");
_Static_assert(BE_B7_UBOOT_RAM_BASE + BE_B7_UBOOT_TEXT_OFFSET ==
	       BE_B7_STAGING_HPA, "booti places the board image at L");
_Static_assert(BE_B7_QEMU_RAM_BASE + BE_B7_QEMU_TEXT_OFFSET ==
	       BE_B7_STAGING_HPA, "booti places the QEMU image at L");
_Static_assert(BE_B7_GUEST_LEAVES * BE_B7_GUEST_LEAF_BYTES ==
	       BE_B7_GUEST_BYTES, "the leaves cover each window");
_Static_assert(BE_B7_G1_HPA == BE_B7_G0_HPA + BE_B7_GUEST_BYTES,
	       "the windows are adjacent and disjoint");
_Static_assert((BE_B7_G0_HPA & (BE_B7_GUEST_LEAF_BYTES - 1)) == 0 &&
	       (BE_B7_G1_HPA & (BE_B7_GUEST_LEAF_BYTES - 1)) == 0,
	       "each window is 2 MiB aligned");
_Static_assert(BE_B7_KERNEL_GPA == BE_B7_GUEST_GPA + BE_B7_KERNEL_TEXT_OFFSET,
	       "the kernel sits at its text_offset");
_Static_assert(BE_B7_DTB_GPA == BE_B7_GUEST_GPA + BE_B7_GUEST_BYTES -
	       BE_B7_GUEST_LEAF_BYTES, "the DTB starts the last 2 MiB");
_Static_assert(BE_B7_STAGING_HPA + BE_B7_BOOT_IMAGE_MAX + BE_B7_KEXEC_FDT_ALIGN +
	       BE_B7_KEXEC_FDT_MAX <= BE_B7_G0_HPA,
	       "the staged image and the kexec FDT end below the windows");
_Static_assert(BE_B7_SLICE_TICKS * 100 == BE_B7_TIMEBASE_HZ,
	       "the slice is 10 ms of the 24 MHz timebase");
#endif

#endif /* BE_B7_LAYOUT_H */
