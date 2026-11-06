# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_post (mvp-ring.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L3, L4, L5 P1: the reader's tail
   102068a3a:	0007b803          	ld	a6,0(a5)
# L4 P1: a misaligned tail: refused
   102068a3e:	00787793          	andi	a5,a6,7
   102068a42:	f7f1                	bnez	a5,102068a0e <be_mvp_ring_post+0x16>
# L4 P1: more than a capacity behind the published head: refused
   102068a4a:	410787b3          	sub	a5,a5,a6
   102068a4e:	fcf360e3          	bltu	t1,a5,102068a0e <be_mvp_ring_post+0x16>
# L4 P1: used = cursor - tail, more than a capacity: refused
   102068a56:	410388b3          	sub	a7,t2,a6
   102068a5a:	fb136ae3          	bltu	t1,a7,102068a0e <be_mvp_ring_post+0x16>
# L3, L4, L5 P1: the room check, capacity - used below the record's size:
#   refused
   102068a6a:	411307b3          	sub	a5,t1,a7
   102068a6e:	fb07e0e3          	bltu	a5,a6,102068a0e <be_mvp_ring_post+0x16>
# L2 P0, L3 P1, L4 P1: the record's type byte
   102068a7e:	00b78023          	sb	a1,0(a5)
# L5 P1: the payload's bytes
   102068b22:	00760023          	sb	t2,0(a2)
