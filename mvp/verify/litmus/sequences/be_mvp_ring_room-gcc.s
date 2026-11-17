# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_ring_room (mvp-ring.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the reader's tail; its low bits, 0 when aligned, the answer when
#   there is no room
   102008846:	639c                	ld	a5,0(a5)
   102008848:	0077f513          	andi	a0,a5,7
# L5 P1: used = cursor - tail, more than a capacity: refused
   10200885a:	40f68633          	sub	a2,a3,a5
   10200885e:	00c77963          	bgeu	a4,a2,102008870 <be_mvp_ring_room+0x40>
# L5 P1: free = tail - cursor + capacity; 16 or fewer: no room
   102008870:	8f95                	sub	a5,a5,a3
   102008872:	97ba                	add	a5,a5,a4
   102008876:	fef779e3          	bgeu	a4,a5,102008868 <be_mvp_ring_room+0x38>
# L5 P1: the room, free - 16, at most 256, rounded down to 8
   10200887a:	17c1                	addi	a5,a5,-16
   102008884:	fef762e3          	bltu	a4,a5,102008868 <be_mvp_ring_room+0x38>
   102008888:	ff87f513          	andi	a0,a5,-8
