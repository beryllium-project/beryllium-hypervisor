# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_block_fill (mvp-hart.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P0: desc->hart, then desc->hgatp
   102067c1c:	e018                	sd	a4,0(s0)
   102067c22:	e80c                	sd	a1,16(s0)
