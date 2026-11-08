// SPDX-License-Identifier: GPL-2.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: beryllium-cheri: a guest kernel's tagged capability store into
 *          a declared page (planning/cheri-enforcement-plan.md, CE-4; section
 *          6, B3 and B4), which /init-cap-store loads with finit_module and
 *          the te-poc channel page's GPA in its parameter gpa
 *          (guest/cheri/cheri-tests.c). At load it stores a tagged
 *          capability into its own data, maps the page with memremap(),
 *          stores an integer at offset 64, then stores the mapping's own
 *          tagged capability at offset 128, reading each back, the integer
 *          first, as the plan's scratch experiment E3 did:
 *            be_cheri_store: own tag=<t>
 *            be_cheri_store: channel gpa=<g> offset=0x40 value=<v>
 *            be_cheri_store: channel offset=0x80 tag=<t>
 *          the last printed only if the capability store returns. With the
 *          CHERI emulator's Zcheripte, the page's G-stage leaf, without the
 *          capability-write bit, faults that store as cause 23 and the run
 *          ends there; without it, the control, the store lands, tag 1.
 * Trust:   untrusted guest kernel code; the monitor's G-stage decides.
 * Scope:   the CHERI platform branch's CHERI Linux guest only: built out of
 *          tree by tools/build-guest-cheri.sh and held by its initramfs
 *          alone. GPL-2.0-only, as guest/mgmt/be-mgmt.c (Q11): it is linked
 *          into the GPL-2.0-only guest kernel.
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/io.h>
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/printk.h>

#define INTEGER_OFFSET		0x40
#define INTEGER_VALUE		0x5678UL
#define CAPABILITY_OFFSET	0x80

static unsigned long gpa;
module_param(gpa, ulong, 0);
MODULE_PARM_DESC(gpa, "the declared page's guest-physical address");

/* The module's own capability slot, in its data. */
static void *own;

static int __init be_cheri_store_init(void)
{
	void *volatile *slot = (void *volatile *)&own;
	char *page;
	void *loaded;

	*slot = &own;
	loaded = *slot;
	pr_info("own tag=%d\n", (int)__builtin_cheri_tag_get(loaded));
	page = memremap(gpa, PAGE_SIZE, MEMREMAP_WB);
	if (!page) {
		pr_info("channel gpa=%#lx error=memremap\n", gpa);
		return -ENOMEM;
	}
	*(volatile unsigned long *)(page + INTEGER_OFFSET) = INTEGER_VALUE;
	pr_info("channel gpa=%#lx offset=%#x value=%#lx\n", gpa, INTEGER_OFFSET,
		*(volatile unsigned long *)(page + INTEGER_OFFSET));
	slot = (void *volatile *)(page + CAPABILITY_OFFSET);
	*slot = page;
	loaded = *slot;
	pr_info("channel offset=%#x tag=%d\n", CAPABILITY_OFFSET,
		(int)__builtin_cheri_tag_get(loaded));
	memunmap(page);
	return 0;
}

module_init(be_cheri_store_init);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Beryllium CHERI guest's tagged store into a declared page");
MODULE_AUTHOR("James Morris <jamorris@linux.microsoft.com>");
