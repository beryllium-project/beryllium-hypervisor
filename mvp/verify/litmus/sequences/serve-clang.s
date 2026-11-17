# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# serve (mvp-sbi.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L4 P0: the take
   102070f76:	94c080e7          	jalr	-1716(ra) # 1020088be <be_mvp_ring_take>
