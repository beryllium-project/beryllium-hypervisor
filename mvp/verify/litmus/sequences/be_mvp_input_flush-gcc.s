# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_input_flush (mvp-input.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the room asked
   10206b4a4:	48e080e7          	jalr	1166(ra) # 10200892e <be_mvp_ring_room>
# L5 P1: the batch, the room or the pending bytes, the fewer; none: dropped
   10206b4b2:	00857363          	bgeu	a0,s0,10206b4b8 <be_mvp_input_flush+0x84>
   10206b4b6:	84aa                	mv	s1,a0
   10206b4b8:	c8b1                	beqz	s1,10206b50c <be_mvp_input_flush+0xd8>
# L5 P1: the post
   10206b4d2:	308080e7          	jalr	776(ra) # 1020087d6 <be_mvp_ring_post>
# L5 P1: the drop counted
   10206b518:	d48080e7          	jalr	-696(ra) # 10206b25c <drop.part.0>
