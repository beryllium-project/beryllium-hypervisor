# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_post (mvp-ring.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L3, L4, L5 P1: the reader's tail
   102008852:	6384                	ld	s1,0(a5)
# L4 P1: a misaligned tail: refused
   102008854:	0074fb13          	andi	s6,s1,7
   102008858:	fc0b1ae3          	bnez	s6,10200882c <be_mvp_ring_post+0x56>
# L4 P1: more than a capacity behind the published head: refused
   102008862:	8f85                	sub	a5,a5,s1
   102008864:	fcfce4e3          	bltu	s9,a5,10200882c <be_mvp_ring_post+0x56>
# L4 P1: used = cursor - tail, more than a capacity: refused
   10200886a:	409609b3          	sub	s3,a2,s1
   10200886e:	fb3cefe3          	bltu	s9,s3,10200882c <be_mvp_ring_post+0x56>
# L3, L4, L5 P1: the room check, tail - cursor + capacity below the record's
#   size: refused
   102008882:	40c487b3          	sub	a5,s1,a2
   102008886:	97e6                	add	a5,a5,s9
   102008888:	faa7e2e3          	bltu	a5,a0,10200882c <be_mvp_ring_post+0x56>
# L2 P0, L3 P1, L4 P1: the record's type byte, by store_le
   10200889a:	dc6080e7          	jalr	-570(ra) # 10200865c <store_le>
# L5 P1: the payload's bytes
   102008928:	00d78023          	sb	a3,0(a5)
