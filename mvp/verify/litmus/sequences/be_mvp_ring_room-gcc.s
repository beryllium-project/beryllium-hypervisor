# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_room (mvp-ring.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the reader's tail; its low bits, 0 when aligned, the answer when
#   there is no room
   1020685c0:	639c                	ld	a5,0(a5)
   1020685c2:	0077f513          	andi	a0,a5,7
# L5 P1: used = cursor - tail, more than a capacity: refused
   1020685d4:	40f68633          	sub	a2,a3,a5
   1020685d8:	00c77963          	bgeu	a4,a2,1020685ea <be_mvp_ring_room+0x40>
# L5 P1: free = tail - cursor + capacity; 16 or fewer: no room
   1020685ea:	8f95                	sub	a5,a5,a3
   1020685ec:	97ba                	add	a5,a5,a4
   1020685f0:	fef779e3          	bgeu	a4,a5,1020685e2 <be_mvp_ring_room+0x38>
# L5 P1: the room, free - 16, at most 256, rounded down to 8
   1020685f4:	17c1                	addi	a5,a5,-16
   1020685fe:	fef762e3          	bltu	a4,a5,1020685e2 <be_mvp_ring_room+0x38>
   102068602:	ff87f513          	andi	a0,a5,-8
