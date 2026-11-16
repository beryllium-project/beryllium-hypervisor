# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_room (mvp-ring.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the reader's tail
   1020088bc:	618c                	ld	a1,0(a1)
# L5 P1: used = cursor - tail, more than a capacity: refused
   1020088d0:	40b685b3          	sub	a1,a3,a1
   1020088d4:	00b67663          	bgeu	a2,a1,1020088e0 <be_mvp_ring_room+0x34>
# L5 P1: free = capacity - used; 16 or fewer: no room
   1020088e0:	40b60533          	sub	a0,a2,a1
   1020088e4:	45c5                	li	a1,17
   1020088e6:	00b57563          	bgeu	a0,a1,1020088f0 <be_mvp_ring_room+0x44>
   1020088ea:	4581                	li	a1,0
# L5 P1: the room, free - 16, at most 256, rounded down to 8
   1020088f0:	1541                	addi	a0,a0,-16
   1020088f6:	00b56463          	bltu	a0,a1,1020088fe <be_mvp_ring_room+0x52>
   1020088fe:	1f857593          	andi	a1,a0,504
