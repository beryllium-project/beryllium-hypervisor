/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: image 2's table (planning/mvp-m13-3-review-point.md, sections 2
 *          and 3): P3, then P4, then P2, which comes last since its block's
 *          clock rests on the weakest inference. tests/expect-2.txt is its
 *          expected list, written apart; the image check compares the two.
 */
#include "m13.h"

	be_m13_begin 2

	/* P3: PCIE_SUBSYS_MGMT, offset 0x1D8 of the AP PMU at 0xD428_2800. */
	be_m13_read 3, 0xd42829d8, 4, PCIE_SUBSYS_MGMT

	/*
	 * P4: port A's inbound address-translation regions 0 to 30, region i
	 * at 0x8030_0000 + 0x200 * i + 0x100: CTRL2 at +0x04, LOWER_TARGET at
	 * +0x14. Then the root port's BAR0 and BAR1 (DBI 0x8000_0000 + 0x10,
	 * + 0x14).
	 */
	.irp region, 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30
	be_m13_read 4, 0x80300104+0x200*\region, 4, CTRL2[\region]
	be_m13_read 4, 0x80300114+0x200*\region, 4, LOWER_TARGET[\region]
	.endr
	be_m13_read 4, 0x80000010, 4, BAR0
	be_m13_read 4, 0x80000014, 4, BAR1

	/* P2: the IOMMU at 0xC0F0_0000: capabilities, fctl, ddtp. */
	be_m13_read 2, 0xc0f00000, 8, capabilities
	be_m13_read 2, 0xc0f00008, 4, fctl
	be_m13_read 2, 0xc0f00010, 8, ddtp

	be_m13_end
