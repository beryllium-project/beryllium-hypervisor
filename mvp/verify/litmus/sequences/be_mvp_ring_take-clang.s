# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_take (mvp-ring.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0, L4 P0: the record's type byte
   102068cf8:	0005c883          	lbu	a7,0(a1)
# L5 P0: the payload's bytes
   102068d96:	00054503          	lbu	a0,0(a0)
