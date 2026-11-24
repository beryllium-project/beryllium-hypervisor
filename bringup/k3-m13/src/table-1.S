/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: image 1's table (planning/mvp-m13-3-review-point.md, sections 2
 *          and 3): P1, then P7. tests/expect-1.txt is its expected list,
 *          written apart; the image check compares the two.
 */
#include "m13.h"

	be_m13_begin 1

	/*
	 * P1: hgeie (CSR 0x607) on each of harts 0, 1, and 2: as booted; all
	 * ones written, then read back; 0 written, then read back.
	 */
	.irp cpu, 0, 1, 2
	be_m13_csrr 1, \cpu, hart\cpu\().hgeie
	be_m13_csrw 1, \cpu, 0xffffffffffffffff, hart\cpu\().hgeie
	be_m13_csrr 1, \cpu, hart\cpu\().hgeie
	be_m13_csrw 1, \cpu, 0, hart\cpu\().hgeie
	be_m13_csrr 1, \cpu, hart\cpu\().hgeie
	.endr

	/*
	 * P7: the S-level APLIC at 0xE080_4000, source 200. Its writes are
	 * made only if domaincfg reads 0x8000_0004 and sourcecfg[200] reads
	 * 0; if sourcecfg[200] does not read back 0x1, it is written 0 and
	 * nothing more is made.
	 */
	be_m13_read 7, 0xe0804000, 4, domaincfg
	.set	read_domaincfg, be_m13_index - 1
	be_m13_read 7, 0xe0804320, 4, sourcecfg[200]
	.set	read_sourcecfg, be_m13_index - 1
	be_m13_guard_end 7, read_domaincfg, 0x80000004, domaincfg
	be_m13_guard_end 7, read_sourcecfg, 0, sourcecfg[200]
	be_m13_write 7, 0xe0804320, 4, 0x1, sourcecfg[200]
	be_m13_read 7, 0xe0804320, 4, sourcecfg[200]
	.set	read_detached, be_m13_index - 1
	be_m13_guard_else 7, read_detached, 0x1, sourcecfg[200]
	be_m13_write 7, 0xe0804320, 4, 0, sourcecfg[200]
	be_m13_write 7, 0xe0807320, 4, 0x1000, target[200]
	be_m13_read 7, 0xe0807320, 4, target[200]
	be_m13_write 7, 0xe0807320, 4, 0, target[200]
	be_m13_read 7, 0xe0807320, 4, target[200]
	be_m13_write 7, 0xe0804320, 4, 0, sourcecfg[200]
	be_m13_read 7, 0xe0804320, 4, sourcecfg[200]

	be_m13_end
