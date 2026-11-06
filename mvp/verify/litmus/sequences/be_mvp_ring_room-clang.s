# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_room (mvp-ring.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the reader's tail
   102068b50:	618c                	ld	a1,0(a1)
# L5 P1: used = cursor - tail, more than a capacity: refused
   102068b64:	40b685b3          	sub	a1,a3,a1
   102068b68:	00b67663          	bgeu	a2,a1,102068b74 <be_mvp_ring_room+0x34>
# L5 P1: free = capacity - used; 16 or fewer: no room
   102068b74:	40b60533          	sub	a0,a2,a1
   102068b78:	45c5                	li	a1,17
   102068b7a:	00b57563          	bgeu	a0,a1,102068b84 <be_mvp_ring_room+0x44>
   102068b7e:	4581                	li	a1,0
# L5 P1: the room, free - 16, at most 256, rounded down to 8
   102068b84:	1541                	addi	a0,a0,-16
   102068b8a:	00b56463          	bltu	a0,a1,102068b92 <be_mvp_ring_room+0x52>
   102068b92:	1f857593          	andi	a1,a0,504
