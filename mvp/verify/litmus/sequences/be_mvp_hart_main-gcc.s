# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_hart_main (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P1: the generation word; not 1, the hart parks; the fence r, r
   102070510:	60d8                	ld	a4,128(s1)
   102070512:	4785                	li	a5,1
   102070514:	fef71ae3          	bne	a4,a5,102070508 <be_mvp_hart_main+0x5e>
   10207051c:	6ae080e7          	jalr	1710(ra) # 102008bc6 <be_mvp_exec_fence_r_r>
# L1 P1: desc->hgatp, for the hart's one install
   1020705ae:	6888                	ld	a0,16(s1)
# L2 writer, call site 8 (outbound ring): READY, ENTERED; fence w, w; the
#   head
   102070690:	b1a080e7          	jalr	-1254(ra) # 1020711a6 <be_mvp_post_ready>
   1020706b0:	b64080e7          	jalr	-1180(ra) # 102071210 <be_mvp_post_entered>
   1020706ba:	508080e7          	jalr	1288(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   1020706c6:	24c080e7          	jalr	588(ra) # 10200890e <be_mvp_ring_publish>
