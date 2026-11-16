# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_post (mvp-ring.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L3, L4, L5 P1: the reader's tail
   1020087a6:	0007b803          	ld	a6,0(a5) # 40803000 <BE_R3_HSTATUS_CONTROL_MASK+0x400c3c80>
# L4 P1: a misaligned tail: refused
   1020087aa:	00787793          	andi	a5,a6,7
   1020087ae:	f7f1                	bnez	a5,10200877a <be_mvp_ring_post+0x16>
# L4 P1: more than a capacity behind the published head: refused
   1020087b6:	410787b3          	sub	a5,a5,a6
   1020087ba:	fcf360e3          	bltu	t1,a5,10200877a <be_mvp_ring_post+0x16>
# L4 P1: used = cursor - tail, more than a capacity: refused
   1020087c2:	410388b3          	sub	a7,t2,a6
   1020087c6:	fb136ae3          	bltu	t1,a7,10200877a <be_mvp_ring_post+0x16>
# L3, L4, L5 P1: the room check, capacity - used below the record's size:
#   refused
   1020087d6:	411307b3          	sub	a5,t1,a7
   1020087da:	fb07e0e3          	bltu	a5,a6,10200877a <be_mvp_ring_post+0x16>
# L2 P0, L3 P1, L4 P1: the record's type byte
   1020087ea:	00b78023          	sb	a1,0(a5)
# L5 P1: the payload's bytes
   10200888e:	00760023          	sb	t2,0(a2)
