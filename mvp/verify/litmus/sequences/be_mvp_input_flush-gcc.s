# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_input_flush (mvp-input.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the room asked
   10206a314:	29a080e7          	jalr	666(ra) # 1020685aa <be_mvp_ring_room>
# L5 P1: the batch, the room or the pending bytes, the fewer; none: dropped
   10206a322:	00857363          	bgeu	a0,s0,10206a328 <be_mvp_input_flush+0x84>
   10206a326:	84aa                	mv	s1,a0
   10206a328:	c8b1                	beqz	s1,10206a37c <be_mvp_input_flush+0xd8>
# L5 P1: the post
   10206a342:	114080e7          	jalr	276(ra) # 102068452 <be_mvp_ring_post>
# L5 P1: the drop counted
   10206a388:	cea080e7          	jalr	-790(ra) # 10206a06e <drop.part.0>
