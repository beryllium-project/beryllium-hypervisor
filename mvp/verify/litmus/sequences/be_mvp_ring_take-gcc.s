# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_take (mvp-ring.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0, L4 P0: the record's type byte, by load_le
   102068782:	b7e080e7          	jalr	-1154(ra) # 1020682fc <load_le>
# L5 P0: the payload's bytes
   102068836:	00074703          	lbu	a4,0(a4)
