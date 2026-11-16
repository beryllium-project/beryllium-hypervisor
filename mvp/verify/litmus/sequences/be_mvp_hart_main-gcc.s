# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_hart_main (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P1: the generation word; not 1, the hart parks; the fence r, r
   1020705f2:	60d8                	ld	a4,128(s1)
   1020705f4:	4785                	li	a5,1
   1020705f6:	fef71ae3          	bne	a4,a5,1020705ea <be_mvp_hart_main+0x5e>
   1020705fe:	6ca080e7          	jalr	1738(ra) # 102008cc4 <be_mvp_exec_fence_r_r>
# L1 P1: desc->hgatp, for the hart's one install
   102070690:	6888                	ld	a0,16(s1)
# L2 writer, call site 8 (outbound ring): READY, ENTERED; fence w, w; the
#   head
   102070772:	b5c080e7          	jalr	-1188(ra) # 1020712ca <be_mvp_post_ready>
   102070792:	ba6080e7          	jalr	-1114(ra) # 102071334 <be_mvp_post_entered>
   10207079c:	524080e7          	jalr	1316(ra) # 102008cbc <be_mvp_exec_fence_w_w>
   1020707a8:	268080e7          	jalr	616(ra) # 102008a0c <be_mvp_ring_publish>
