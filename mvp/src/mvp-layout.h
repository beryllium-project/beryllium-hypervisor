/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the fixed MVP layout (planning/mvp-m0-plan.md, "Hart region",
 *          "Budgets", "Memory and load paths", "G-stage and VMIDs", and
 *          Plan revision M0-A.1): the monitor flat image, its core at its
 *          start (planning/mvp-m6-plan.md, D-4: code, data, and hart 0's
 *          stack), the two-root G-stage pool, the hart region
 *          and each domain hart's block and rings, the MVP region, the
 *          staged boot image, the two domain RAM windows and their VMIDs,
 *          the channel page and each root's level-0 page (M1 plan, "G-stage
 *          and VMIDs"), grown into the three shared pages and the secret's
 *          size (M2 plan, Q1 and "Memory and load paths"), the control hart
 *          and the domain harts, the guest kernel and DTB placement, the
 *          run limits and waits, and the SBI identity. The monitor, the
 *          boot-image link, the guest device-tree generator, and the
 *          checkers all read these values, so they cannot drift apart.
 * Trust:   constants only. Every value is a literal inside BE_MVP_C() so
 *          that scripts can parse it; C static assertions tie the derived
 *          values to their sources.
 * Scope:   the MVP line (M0 to M7). Usable from C, assembly, and
 *          preprocessed linker scripts (define __ASSEMBLER__ for the latter
 *          two).
 */

#ifndef BE_MVP_LAYOUT_H
#define BE_MVP_LAYOUT_H

#ifdef __ASSEMBLER__
#define BE_MVP_C(value)			value
#else
#define BE_MVP_C(value)			value##UL
#endif

/*
 * The monitor flat image (Plan revision M0-A.1): its first 0x34000 bytes,
 * the core, are the MVP's own layout since M6 (src/mvp-monitor.lds;
 * planning/mvp-m6-plan.md, D-4): the monitor code below the data, the
 * monitor data with the diagnostic page at its end, hart 0's stack, and
 * the rest unused and zero; then the NOLOAD pool and hart region, zeros in
 * the file; then the MVP region, which ends the image. The board tools'
 * layout rule (tools/platform-probe.py) checks the core, the pool, the
 * hart region, the MVP region, the staging reserve, the windows, and the
 * shared pages as the extents the preflight names.
 */
#define BE_MVP_MONITOR_HPA		BE_MVP_C(0x102000000)
#define BE_MVP_CORE_BYTES		BE_MVP_C(0x34000)
#define BE_MVP_IMAGE_BYTES		BE_MVP_C(0xa4000)
#define BE_MVP_DATA_HPA			BE_MVP_C(0x102008000)
#define BE_MVP_DATA_BYTES		BE_MVP_C(0x8000)
#define BE_MVP_CONTROL_STACK_HPA	BE_MVP_C(0x102010000)
#define BE_MVP_CONTROL_STACK_BYTES	BE_MVP_C(0x2000)

/*
 * The NOLOAD G-stage pool: two B6-shaped 32 KiB pools, one per domain,
 * each a 16 KiB root, then one level-1 page, then one level-0 page that
 * only a root with a channel uses (M1); the rest of each pool is spare.
 */
#define BE_MVP_DOMAINS			BE_MVP_C(2)
#define BE_MVP_POOL_HPA			BE_MVP_C(0x102034000)
#define BE_MVP_POOL_BYTES		BE_MVP_C(0x10000)
#define BE_MVP_GUEST_POOL_BYTES		BE_MVP_C(0x8000)
#define BE_MVP_ROOT_BYTES		BE_MVP_C(0x4000)
#define BE_MVP_G0_ROOT_HPA		BE_MVP_C(0x102034000)
#define BE_MVP_G0_LEVEL1_HPA		BE_MVP_C(0x102038000)
#define BE_MVP_G0_LEVEL0_HPA		BE_MVP_C(0x102039000)
#define BE_MVP_G1_ROOT_HPA		BE_MVP_C(0x10203c000)
#define BE_MVP_G1_LEVEL1_HPA		BE_MVP_C(0x102040000)
#define BE_MVP_G1_LEVEL0_HPA		BE_MVP_C(0x102041000)

/* Distinct VMIDs and each domain's hgatp: Sv39x4, VMID, root. */
#define BE_MVP_G0_VMID			BE_MVP_C(1)
#define BE_MVP_G1_VMID			BE_MVP_C(2)
#define BE_MVP_G0_HGATP			BE_MVP_C(0x8000100000102034)
#define BE_MVP_G1_HGATP			BE_MVP_C(0x800020000010203c)

/*
 * Hart identifiers ("Hart identifiers", Q12). The control hart is fixed by
 * the accepted R3 boot check; the domain harts are scenario data, hart 1
 * for G0 and hart 2 for G1 by default, validated at boot; the platform has
 * eight harts, and the rest are never started.
 */
#define BE_MVP_HARTS			BE_MVP_C(8)
#define BE_MVP_CONTROL_HART		BE_MVP_C(0)
#define BE_MVP_DOMAIN0_HART		BE_MVP_C(1)
#define BE_MVP_DOMAIN1_HART		BE_MVP_C(2)

/*
 * The NOLOAD hart region (Q1): one 64 KiB block per domain hart, G0's
 * first, written only at run time. Each block holds the hart's trusted
 * stack, its saved page at the stack top (the block's sscratch), its state
 * page (written by hart 0 before the barrier, by the hart after it), the
 * inbound ring (hart 0 writes, the hart reads), the outbound ring (the
 * hart writes, hart 0 reads), and, since M7, the input ring
 * (planning/mvp-m7-plan.md, D-1: hart 0 writes the console bytes routed to
 * the domain, the hart reads them at its DBCN-read exits), in the first
 * 4 KiB of what M0 left unused; the rest is unused.
 */
#define BE_MVP_HART_REGION_HPA		BE_MVP_C(0x102044000)
#define BE_MVP_HART_REGION_BYTES	BE_MVP_C(0x20000)
#define BE_MVP_BLOCK_BYTES		BE_MVP_C(0x10000)
#define BE_MVP_G0_BLOCK_HPA		BE_MVP_C(0x102044000)
#define BE_MVP_G1_BLOCK_HPA		BE_MVP_C(0x102054000)
#define BE_MVP_BLOCK_STACK_OFFSET	BE_MVP_C(0x0)
#define BE_MVP_BLOCK_STACK_BYTES	BE_MVP_C(0x2000)
#define BE_MVP_BLOCK_STACK_TOP_OFFSET	BE_MVP_C(0x2000)
#define BE_MVP_BLOCK_SAVED_OFFSET	BE_MVP_C(0x2000)
#define BE_MVP_BLOCK_SAVED_BYTES	BE_MVP_C(0x1000)
#define BE_MVP_BLOCK_STATE_OFFSET	BE_MVP_C(0x3000)
#define BE_MVP_BLOCK_STATE_BYTES	BE_MVP_C(0x1000)
#define BE_MVP_BLOCK_INBOUND_OFFSET	BE_MVP_C(0x4000)
#define BE_MVP_INBOUND_RING_BYTES	BE_MVP_C(0x1000)
#define BE_MVP_BLOCK_OUTBOUND_OFFSET	BE_MVP_C(0x5000)
#define BE_MVP_OUTBOUND_RING_BYTES	BE_MVP_C(0x8000)
#define BE_MVP_INPUT_RING_OFFSET	BE_MVP_C(0xd000)
#define BE_MVP_INPUT_RING_BYTES		BE_MVP_C(0x1000)
#define BE_MVP_BLOCK_UNUSED_OFFSET	BE_MVP_C(0xe000)
#define BE_MVP_BLOCK_UNUSED_BYTES	BE_MVP_C(0x2000)
/* The outbound high-water mark at or below which a run stays in budget. */
#define BE_MVP_RING_PEAK_BUDGET		BE_MVP_C(0x4000)
/* The generation word hart 0 publishes last, at the boot barrier. */
#define BE_MVP_GENERATION		BE_MVP_C(1)

/*
 * The MVP region (Plan revision M0-A.1): the MVP layer's C objects' code,
 * constants, data, and BSS, after the hart region, outside every accepted
 * extent, loaded with the flat image, which it ends. The accepted code
 * extent below 0x1_0200_8000 keeps the accepted code and the MVP's
 * assembly, the vector among it.
 */
#define BE_MVP_REGION_HPA		BE_MVP_C(0x102064000)
#define BE_MVP_REGION_BYTES		BE_MVP_C(0x40000)
/* Fedora's kernel on the COM260, the first byte above the free RAM the B7
 * preflight recorded after the monitor. */
#define BE_MVP_FEDORA_KERNEL_HPA	BE_MVP_C(0x102200000)

/* The boot image, staged by every loader at L; the staging reserve the
 * board tools check (M6, Q3): the image's maximum rounded up to 2 MiB plus
 * the 2 MiB slot the kexec era kept after it, so the checked extents are
 * the ones every retained preflight names. */
#define BE_MVP_STAGING_HPA		BE_MVP_C(0x108000000)
#define BE_MVP_STAGING_BYTES		BE_MVP_C(0x600000)
#define BE_MVP_BOOT_MONITOR_OFFSET	BE_MVP_C(0x1000)
#define BE_MVP_BOOT_KERNEL_OFFSET	BE_MVP_C(0xa5000)
#define BE_MVP_BOOT_IMAGE_MAX		BE_MVP_C(0x400000)
#define BE_MVP_KERNEL_FILE_MAX		BE_MVP_C(0x400000)
#define BE_MVP_KERNEL_IMAGE_SIZE_MAX	BE_MVP_C(0x800000)
#define BE_MVP_KERNEL_TEXT_OFFSET	BE_MVP_C(0x200000)
#define BE_MVP_DTB_BYTES		BE_MVP_C(0x1000)
#define BE_MVP_PAYLOAD_ALIGN		BE_MVP_C(0x1000)

/*
 * Loader placement: the booti RAM bases (B3's header stays in the image;
 * QEMU boots it at the same L), and the slot after the image where the
 * kexec loader once placed the FDT, which the board tools' staging region
 * keeps.
 */
#define BE_MVP_UBOOT_RAM_BASE		BE_MVP_C(0x102000000)
#define BE_MVP_UBOOT_TEXT_OFFSET	BE_MVP_C(0x6000000)
#define BE_MVP_QEMU_RAM_BASE		BE_MVP_C(0x80000000)
#define BE_MVP_QEMU_TEXT_OFFSET		BE_MVP_C(0x88000000)

/* The two domain RAM windows, each 64 MiB of 2 MiB leaves. */
#define BE_MVP_GUEST_GPA		BE_MVP_C(0x80000000)
#define BE_MVP_GUEST_BYTES		BE_MVP_C(0x4000000)
#define BE_MVP_GUEST_LEAF_BYTES		BE_MVP_C(0x200000)
#define BE_MVP_GUEST_LEAVES		BE_MVP_C(32)
#define BE_MVP_G0_HPA			BE_MVP_C(0x110000000)
#define BE_MVP_G1_HPA			BE_MVP_C(0x114000000)

/*
 * The shared pages (M2 plan, Q1, "Memory and load paths"): one MVP-owned
 * extent of three 4 KiB pages directly above G1's window, each at the same
 * GPA in every root that maps it, directly above the guest window, in the
 * windows' root entry and level-1 table (index 32, level-0 indices 0 to
 * 2). Each root maps its pages through its own level-0 page, with that
 * root's rights; a scenario maps only the pages it declares, a v3
 * scenario's pages (at most BE_MVP_PAGES_MAX), and the monitor writes the
 * secret, BE_MVP_SECRET_BYTES, into a secret page. M1's channel page (Q1
 * of the M1 plan) is the extent's first page: a v2 scenario's one channel,
 * which a scenario without a channel maps in neither root.
 */
#define BE_MVP_SHARED_PAGES_HPA		BE_MVP_C(0x118000000)
#define BE_MVP_SHARED_PAGES_BYTES	BE_MVP_C(0x3000)
#define BE_MVP_PAGES_MAX		BE_MVP_C(3)
#define BE_MVP_SECRET_BYTES		BE_MVP_C(0x20)
#define BE_MVP_CHANNELS_MAX		BE_MVP_C(1)
#define BE_MVP_CHANNEL_GPA		BE_MVP_C(0x84000000)
#define BE_MVP_CHANNEL_HPA		BE_MVP_C(0x118000000)
#define BE_MVP_CHANNEL_BYTES		BE_MVP_C(0x1000)

/* Guest placement and entry, the same in each window and on each hart. */
#define BE_MVP_KERNEL_GPA		BE_MVP_C(0x80200000)
#define BE_MVP_DTB_GPA			BE_MVP_C(0x83e00000)
#define BE_MVP_GUEST_HART		BE_MVP_C(0)
#define BE_MVP_TIMEBASE_HZ		BE_MVP_C(24000000)

/*
 * Run limits (Q11: exits per domain; one run budget on hart 0's timer),
 * the waits for a hart's start, its READY, and hart 0's acknowledgement of
 * a domain hart's failure (Q10), and the SBI identity (Q3). The
 * acknowledgement window keeps its length, but since Plan revision M1-B
 * it restarts each time hart 0 takes a record from the failed hart's
 * outbound ring, so it measures hart 0's progress, not its latency.
 */
#define BE_MVP_EXIT_CEILING		BE_MVP_C(0x100000)
#define BE_MVP_RUN_BUDGET		BE_MVP_C(0x100000000)
#define BE_MVP_HART_START_TICKS		BE_MVP_C(0x1000000)
#define BE_MVP_READY_TICKS		BE_MVP_C(0x4000000)
#define BE_MVP_FAIL_ACK_TICKS		BE_MVP_C(0x1000000)
/* The QEMU-only negative variants exit-budget, run-timeout, ring-full, and
 * hart-start; ring-full also delays hart 0's first LINE drain after both
 * domains' ENTERED (Plan revision M0-A.3). */
#define BE_MVP_VARIANT_EXIT_CEILING	BE_MVP_C(64)
#define BE_MVP_VARIANT_RUN_BUDGET	BE_MVP_C(0x100000)
#define BE_MVP_VARIANT_OUTBOUND_RING_BYTES	BE_MVP_C(0x400)
#define BE_MVP_VARIANT_DRAIN_DELAY_TICKS	BE_MVP_C(0x2000000)
#define BE_MVP_VARIANT_HART_START_HART	BE_MVP_C(9)
/*
 * Console input (planning/mvp-m7-plan.md, D-1 and Q2): in an image whose
 * sealed configuration grants console input to a domain, hart 0 polls the
 * firmware console at least every BE_MVP_INPUT_POLL_TICKS on its own
 * timer, which it re-arms at every wake, never past the run budget's end.
 */
#define BE_MVP_INPUT_POLL_TICKS		BE_MVP_C(0x40000)
/*
 * The SBI identity: version 5 since M7, which serves DBCN read
 * (planning/mvp-m7-plan.md, D-10 and Q11; 3 before), and 6 in an image
 * with the management extension (mvp.h).
 */
#define BE_MVP_SBI_IMPL_ID		BE_MVP_C(0x4245)
#define BE_MVP_SBI_IMPL_VERSION		BE_MVP_C(5)

#ifndef __ASSEMBLER__
_Static_assert(BE_MVP_POOL_HPA == BE_MVP_MONITOR_HPA + BE_MVP_CORE_BYTES,
	       "the pool follows the core, the board tools' extent");
_Static_assert(BE_MVP_DATA_HPA == BE_MVP_MONITOR_HPA + BE_MVP_C(0x8000) &&
	       BE_MVP_CONTROL_STACK_HPA == BE_MVP_DATA_HPA + BE_MVP_DATA_BYTES &&
	       BE_MVP_CONTROL_STACK_HPA + BE_MVP_CONTROL_STACK_BYTES <=
	       BE_MVP_MONITOR_HPA + BE_MVP_CORE_BYTES,
	       "the core: code below 0x1_0200_8000, data, then hart 0's stack");
_Static_assert(BE_MVP_POOL_BYTES == BE_MVP_DOMAINS * BE_MVP_GUEST_POOL_BYTES,
	       "the pool holds one B6-shaped pool per domain");
_Static_assert(BE_MVP_G0_ROOT_HPA == BE_MVP_POOL_HPA,
	       "G0's root starts the pool");
_Static_assert(BE_MVP_G1_ROOT_HPA ==
	       BE_MVP_G0_ROOT_HPA + BE_MVP_GUEST_POOL_BYTES,
	       "G1's root starts the second pool");
_Static_assert(BE_MVP_G0_LEVEL1_HPA == BE_MVP_G0_ROOT_HPA + BE_MVP_ROOT_BYTES,
	       "G0's level-1 page follows its root");
_Static_assert(BE_MVP_G1_LEVEL1_HPA == BE_MVP_G1_ROOT_HPA + BE_MVP_ROOT_BYTES,
	       "G1's level-1 page follows its root");
_Static_assert(BE_MVP_G0_LEVEL0_HPA ==
	       BE_MVP_G0_LEVEL1_HPA + BE_MVP_C(0x1000) &&
	       BE_MVP_G1_LEVEL0_HPA ==
	       BE_MVP_G1_LEVEL1_HPA + BE_MVP_C(0x1000),
	       "each level-0 page follows its level-1 page");
_Static_assert(BE_MVP_G0_LEVEL0_HPA + BE_MVP_C(0x1000) <= BE_MVP_G1_ROOT_HPA &&
	       BE_MVP_G1_LEVEL0_HPA + BE_MVP_C(0x1000) <=
	       BE_MVP_POOL_HPA + BE_MVP_POOL_BYTES,
	       "each level-0 page lies in its own pool");
_Static_assert((BE_MVP_G0_ROOT_HPA & (BE_MVP_ROOT_BYTES - 1)) == 0 &&
	       (BE_MVP_G1_ROOT_HPA & (BE_MVP_ROOT_BYTES - 1)) == 0,
	       "each Sv39x4 root is 16 KiB aligned");
_Static_assert(BE_MVP_G0_HGATP == ((BE_MVP_C(8) << 60) |
				   (BE_MVP_G0_VMID << 44) |
				   (BE_MVP_G0_ROOT_HPA >> 12)),
	       "G0's hgatp is Sv39x4, VMID 1, at its root");
_Static_assert(BE_MVP_G1_HGATP == ((BE_MVP_C(8) << 60) |
				   (BE_MVP_G1_VMID << 44) |
				   (BE_MVP_G1_ROOT_HPA >> 12)),
	       "G1's hgatp is Sv39x4, VMID 2, at its root");
_Static_assert(BE_MVP_G0_VMID != BE_MVP_G1_VMID && BE_MVP_G0_VMID != 0 &&
	       BE_MVP_G1_VMID != 0, "the domains have distinct nonzero VMIDs");
_Static_assert(BE_MVP_CONTROL_HART < BE_MVP_HARTS &&
	       BE_MVP_DOMAIN0_HART < BE_MVP_HARTS &&
	       BE_MVP_DOMAIN1_HART < BE_MVP_HARTS,
	       "the control and domain harts exist on the platform");
_Static_assert(BE_MVP_DOMAIN0_HART != BE_MVP_CONTROL_HART &&
	       BE_MVP_DOMAIN1_HART != BE_MVP_CONTROL_HART &&
	       BE_MVP_DOMAIN0_HART != BE_MVP_DOMAIN1_HART,
	       "each domain has its own hart, never the control hart");
_Static_assert(BE_MVP_VARIANT_HART_START_HART >= BE_MVP_HARTS,
	       "the hart-start variant names a hart the platform lacks");
_Static_assert(BE_MVP_HART_REGION_HPA == BE_MVP_POOL_HPA + BE_MVP_POOL_BYTES,
	       "the hart region follows the pool");
_Static_assert(BE_MVP_HART_REGION_BYTES == BE_MVP_DOMAINS * BE_MVP_BLOCK_BYTES,
	       "the hart region holds one block per domain hart");
_Static_assert(BE_MVP_G0_BLOCK_HPA == BE_MVP_HART_REGION_HPA &&
	       BE_MVP_G1_BLOCK_HPA == BE_MVP_G0_BLOCK_HPA + BE_MVP_BLOCK_BYTES,
	       "G0's block starts the region and G1's follows it");
_Static_assert((BE_MVP_HART_REGION_HPA & BE_MVP_C(0x3fff)) == 0 &&
	       (BE_MVP_G0_BLOCK_HPA & BE_MVP_C(0x3fff)) == 0 &&
	       (BE_MVP_G1_BLOCK_HPA & BE_MVP_C(0x3fff)) == 0,
	       "the hart region and each block are 16 KiB aligned");
_Static_assert(BE_MVP_BLOCK_STACK_OFFSET == 0 &&
	       BE_MVP_BLOCK_STACK_TOP_OFFSET ==
	       BE_MVP_BLOCK_STACK_OFFSET + BE_MVP_BLOCK_STACK_BYTES &&
	       BE_MVP_BLOCK_SAVED_OFFSET == BE_MVP_BLOCK_STACK_TOP_OFFSET,
	       "the saved page sits at the trusted-stack top");
_Static_assert(BE_MVP_BLOCK_STATE_OFFSET ==
	       BE_MVP_BLOCK_SAVED_OFFSET + BE_MVP_BLOCK_SAVED_BYTES &&
	       BE_MVP_BLOCK_INBOUND_OFFSET ==
	       BE_MVP_BLOCK_STATE_OFFSET + BE_MVP_BLOCK_STATE_BYTES &&
	       BE_MVP_BLOCK_OUTBOUND_OFFSET ==
	       BE_MVP_BLOCK_INBOUND_OFFSET + BE_MVP_INBOUND_RING_BYTES &&
	       BE_MVP_INPUT_RING_OFFSET ==
	       BE_MVP_BLOCK_OUTBOUND_OFFSET + BE_MVP_OUTBOUND_RING_BYTES &&
	       BE_MVP_BLOCK_UNUSED_OFFSET ==
	       BE_MVP_INPUT_RING_OFFSET + BE_MVP_INPUT_RING_BYTES &&
	       BE_MVP_BLOCK_UNUSED_OFFSET + BE_MVP_BLOCK_UNUSED_BYTES ==
	       BE_MVP_BLOCK_BYTES,
	       "a block is the stack, saved, state, inbound, outbound, input, "
	       "and unused pages in order, exactly");
_Static_assert((BE_MVP_INBOUND_RING_BYTES &
		(BE_MVP_INBOUND_RING_BYTES - 1)) == 0 &&
	       (BE_MVP_OUTBOUND_RING_BYTES &
		(BE_MVP_OUTBOUND_RING_BYTES - 1)) == 0 &&
	       (BE_MVP_INPUT_RING_BYTES & (BE_MVP_INPUT_RING_BYTES - 1)) == 0 &&
	       (BE_MVP_VARIANT_OUTBOUND_RING_BYTES &
		(BE_MVP_VARIANT_OUTBOUND_RING_BYTES - 1)) == 0,
	       "each ring's capacity is a power of two");
_Static_assert(BE_MVP_VARIANT_OUTBOUND_RING_BYTES < BE_MVP_OUTBOUND_RING_BYTES,
	       "the ring-full variant shrinks the outbound ring");
_Static_assert(BE_MVP_RING_PEAK_BUDGET * 2 == BE_MVP_OUTBOUND_RING_BYTES,
	       "the high-water budget is half the outbound ring");
_Static_assert(BE_MVP_POOL_HPA + BE_MVP_POOL_BYTES <= BE_MVP_STAGING_HPA,
	       "the pool ends below the staged image");
_Static_assert(BE_MVP_HART_REGION_HPA + BE_MVP_HART_REGION_BYTES <=
	       BE_MVP_STAGING_HPA,
	       "the hart region ends below the staged image");
_Static_assert(BE_MVP_HART_REGION_HPA + BE_MVP_HART_REGION_BYTES <=
	       BE_MVP_G0_HPA,
	       "the hart region ends below both windows");
_Static_assert(BE_MVP_REGION_HPA ==
	       BE_MVP_HART_REGION_HPA + BE_MVP_HART_REGION_BYTES,
	       "the MVP region follows the hart region");
_Static_assert(BE_MVP_REGION_HPA + BE_MVP_REGION_BYTES ==
	       BE_MVP_MONITOR_HPA + BE_MVP_IMAGE_BYTES &&
	       BE_MVP_REGION_HPA + BE_MVP_REGION_BYTES <=
	       BE_MVP_C(0x1020a4000),
	       "the MVP region ends the flat image, at 0x1_020a_4000");
_Static_assert((BE_MVP_REGION_HPA & BE_MVP_C(0x3fff)) == 0,
	       "the MVP region is 16 KiB aligned");
_Static_assert(BE_MVP_REGION_HPA + BE_MVP_REGION_BYTES <=
	       BE_MVP_FEDORA_KERNEL_HPA &&
	       BE_MVP_FEDORA_KERNEL_HPA <= BE_MVP_STAGING_HPA,
	       "the MVP region ends below Fedora's kernel and the staged "
	       "image");
_Static_assert(BE_MVP_IMAGE_BYTES > BE_MVP_CORE_BYTES +
	       BE_MVP_POOL_BYTES + BE_MVP_HART_REGION_BYTES,
	       "the flat image holds the core, the pool, the hart "
	       "region, and the MVP region");
_Static_assert(BE_MVP_BOOT_KERNEL_OFFSET ==
	       BE_MVP_BOOT_MONITOR_OFFSET + BE_MVP_IMAGE_BYTES,
	       "the kernel follows the monitor in the boot image");
_Static_assert(BE_MVP_UBOOT_RAM_BASE + BE_MVP_UBOOT_TEXT_OFFSET ==
	       BE_MVP_STAGING_HPA, "booti places the board image at L");
_Static_assert(BE_MVP_QEMU_RAM_BASE + BE_MVP_QEMU_TEXT_OFFSET ==
	       BE_MVP_STAGING_HPA, "booti places the QEMU image at L");
_Static_assert(BE_MVP_GUEST_LEAVES * BE_MVP_GUEST_LEAF_BYTES ==
	       BE_MVP_GUEST_BYTES, "the leaves cover each window");
_Static_assert(BE_MVP_G1_HPA == BE_MVP_G0_HPA + BE_MVP_GUEST_BYTES,
	       "the windows are adjacent and disjoint");
_Static_assert((BE_MVP_G0_HPA & (BE_MVP_GUEST_LEAF_BYTES - 1)) == 0 &&
	       (BE_MVP_G1_HPA & (BE_MVP_GUEST_LEAF_BYTES - 1)) == 0,
	       "each window is 2 MiB aligned");
_Static_assert(BE_MVP_CHANNELS_MAX == 1 &&
	       BE_MVP_CHANNEL_BYTES == BE_MVP_C(0x1000) &&
	       (BE_MVP_CHANNEL_GPA & BE_MVP_C(0xfff)) == 0 &&
	       (BE_MVP_CHANNEL_HPA & BE_MVP_C(0xfff)) == 0,
	       "one channel: one 4 KiB-aligned 4 KiB page");
_Static_assert(BE_MVP_PAGES_MAX == 3 &&
	       BE_MVP_SHARED_PAGES_BYTES ==
	       BE_MVP_PAGES_MAX * BE_MVP_C(0x1000) &&
	       (BE_MVP_SHARED_PAGES_HPA & BE_MVP_C(0xfff)) == 0 &&
	       BE_MVP_SECRET_BYTES <= BE_MVP_C(0x1000),
	       "the shared pages: three 4 KiB-aligned 4 KiB pages, and a "
	       "secret that fits one");
_Static_assert(BE_MVP_CHANNEL_HPA == BE_MVP_SHARED_PAGES_HPA &&
	       BE_MVP_CHANNEL_BYTES <= BE_MVP_SHARED_PAGES_BYTES,
	       "M1's channel page is the shared pages' first page");
_Static_assert(BE_MVP_SHARED_PAGES_HPA == BE_MVP_G1_HPA + BE_MVP_GUEST_BYTES,
	       "the shared pages lie directly above G1's window");
_Static_assert(BE_MVP_MONITOR_HPA + BE_MVP_IMAGE_BYTES <=
	       BE_MVP_SHARED_PAGES_HPA &&
	       BE_MVP_POOL_HPA + BE_MVP_POOL_BYTES <= BE_MVP_SHARED_PAGES_HPA &&
	       BE_MVP_HART_REGION_HPA + BE_MVP_HART_REGION_BYTES <=
	       BE_MVP_SHARED_PAGES_HPA &&
	       BE_MVP_REGION_HPA + BE_MVP_REGION_BYTES <=
	       BE_MVP_SHARED_PAGES_HPA &&
	       BE_MVP_STAGING_HPA + BE_MVP_STAGING_BYTES <=
	       BE_MVP_SHARED_PAGES_HPA &&
	       BE_MVP_G0_HPA + BE_MVP_GUEST_BYTES <= BE_MVP_SHARED_PAGES_HPA &&
	       BE_MVP_G1_HPA + BE_MVP_GUEST_BYTES <= BE_MVP_SHARED_PAGES_HPA,
	       "the shared pages lie above, so outside, the flat image, the "
	       "pool, the hart region, the MVP region, the staged image, the "
	       "kexec FDT, and both windows");
_Static_assert(BE_MVP_CHANNEL_GPA == BE_MVP_GUEST_GPA + BE_MVP_GUEST_BYTES,
	       "the shared pages' GPAs lie directly above each guest's window");
_Static_assert((BE_MVP_CHANNEL_GPA >> 30) == (BE_MVP_GUEST_GPA >> 30) &&
	       ((BE_MVP_CHANNEL_GPA >> 21) & BE_MVP_C(0x1ff)) ==
	       ((BE_MVP_GUEST_GPA >> 21) & BE_MVP_C(0x1ff)) +
	       BE_MVP_GUEST_LEAVES &&
	       ((BE_MVP_CHANNEL_GPA >> 21) & BE_MVP_C(0x1ff)) == BE_MVP_C(32) &&
	       ((BE_MVP_CHANNEL_GPA >> 12) & BE_MVP_C(0x1ff)) == 0 &&
	       ((BE_MVP_CHANNEL_GPA + BE_MVP_SHARED_PAGES_BYTES - 1) >> 21) ==
	       (BE_MVP_CHANNEL_GPA >> 21),
	       "the shared pages share the windows' root entry and level-1 "
	       "table, after the window's leaves at index 32, from level-0 "
	       "index 0, all behind that one level-1 entry");
_Static_assert(BE_MVP_KERNEL_GPA ==
	       BE_MVP_GUEST_GPA + BE_MVP_KERNEL_TEXT_OFFSET,
	       "the kernel sits at its text_offset");
_Static_assert(BE_MVP_DTB_GPA == BE_MVP_GUEST_GPA + BE_MVP_GUEST_BYTES -
	       BE_MVP_GUEST_LEAF_BYTES, "the DTB starts the last 2 MiB");
_Static_assert(BE_MVP_BOOT_IMAGE_MAX <= BE_MVP_STAGING_BYTES &&
	       BE_MVP_STAGING_HPA + BE_MVP_STAGING_BYTES <= BE_MVP_G0_HPA,
	       "the staging reserve holds the image and ends below the windows");
_Static_assert(BE_MVP_RUN_BUDGET / BE_MVP_TIMEBASE_HZ == 178,
	       "the run budget is about 179 s of the 24 MHz timebase");
_Static_assert(BE_MVP_READY_TICKS > BE_MVP_HART_START_TICKS,
	       "a hart has longer to reach READY than to start");
_Static_assert(BE_MVP_VARIANT_DRAIN_DELAY_TICKS > BE_MVP_FAIL_ACK_TICKS,
	       "in ring-full, hart 0 still waits when a domain hart's wait "
	       "for its acknowledgement ends");
_Static_assert(BE_MVP_INPUT_POLL_TICKS == BE_MVP_C(1) << 18 &&
	       BE_MVP_INPUT_POLL_TICKS < BE_MVP_VARIANT_RUN_BUDGET,
	       "hart 0 polls the console every 2^18 ticks (Q2), well inside "
	       "every run budget");
#endif

#endif /* BE_MVP_LAYOUT_H */
