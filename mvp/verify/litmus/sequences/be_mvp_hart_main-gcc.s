# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_hart_main (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P1: the generation word; not 1, the hart parks; the fence r, r
   1020705f4:	60d8                	ld	a4,128(s1)
   1020705f6:	4785                	li	a5,1
   1020705f8:	fef71ae3          	bne	a4,a5,1020705ec <be_mvp_hart_main+0x5a>
   102070600:	6ec080e7          	jalr	1772(ra) # 102008ce8 <be_mvp_exec_fence_r_r>
# L1 P1: desc->hgatp, for the hart's one install
   102070692:	6888                	ld	a0,16(s1)
# L2 writer, call site 8 (outbound ring): READY, ENTERED; fence w, w; the
#   head
   102070770:	aaa080e7          	jalr	-1366(ra) # 102071216 <be_mvp_post_ready>
   10207078c:	ad6080e7          	jalr	-1322(ra) # 10207125e <be_mvp_post_entered>
   102070796:	54e080e7          	jalr	1358(ra) # 102008ce0 <be_mvp_exec_fence_w_w>
   1020707a2:	26e080e7          	jalr	622(ra) # 102008a0c <be_mvp_ring_publish>
