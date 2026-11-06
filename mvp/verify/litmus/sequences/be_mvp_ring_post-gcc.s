# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_post (mvp-ring.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L3, L4, L5 P1: the reader's tail
   1020684ce:	6384                	ld	s1,0(a5)
# L4 P1: a misaligned tail: refused
   1020684d0:	0074fb13          	andi	s6,s1,7
   1020684d4:	fc0b1ae3          	bnez	s6,1020684a8 <be_mvp_ring_post+0x56>
# L4 P1: more than a capacity behind the published head: refused
   1020684de:	8f85                	sub	a5,a5,s1
   1020684e0:	fcfce4e3          	bltu	s9,a5,1020684a8 <be_mvp_ring_post+0x56>
# L4 P1: used = cursor - tail, more than a capacity: refused
   1020684e6:	409609b3          	sub	s3,a2,s1
   1020684ea:	fb3cefe3          	bltu	s9,s3,1020684a8 <be_mvp_ring_post+0x56>
# L3, L4, L5 P1: the room check, tail - cursor + capacity below the record's
#   size: refused
   1020684fe:	40c487b3          	sub	a5,s1,a2
   102068502:	97e6                	add	a5,a5,s9
   102068504:	faa7e2e3          	bltu	a5,a0,1020684a8 <be_mvp_ring_post+0x56>
# L2 P0, L3 P1, L4 P1: the record's type byte, by store_le
   102068516:	dc6080e7          	jalr	-570(ra) # 1020682d8 <store_le>
# L5 P1: the payload's bytes
   1020685a4:	00d78023          	sb	a3,0(a5)
