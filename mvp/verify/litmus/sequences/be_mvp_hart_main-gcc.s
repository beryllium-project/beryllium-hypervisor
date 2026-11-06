# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_hart_main (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P1: the generation word; not 1, the hart parks; the fence r, r
   1020664c8:	16853983          	ld	s3,360(a0)
   1020664cc:	4785                	li	a5,1
   1020664d0:	fef998e3          	bne	s3,a5,1020664c0 <be_mvp_hart_main+0x2c>
   1020664d8:	b4e080e7          	jalr	-1202(ra) # 10206a022 <be_mvp_exec_fence_r_r>
# L1 P1: desc->hgatp, for the hart's one install
   102066554:	11043503          	ld	a0,272(s0)
# L2 writer, call site 8 (outbound ring): READY, ENTERED; fence w, w; the
#   head
   102066648:	bb8080e7          	jalr	-1096(ra) # 1020671fc <be_mvp_post_ready>
   102066664:	be4080e7          	jalr	-1052(ra) # 102067244 <be_mvp_post_entered>
   10206666e:	9b0080e7          	jalr	-1616(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   10206667a:	012080e7          	jalr	18(ra) # 102068688 <be_mvp_ring_publish>
