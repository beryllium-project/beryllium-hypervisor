# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_hart_main (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P1: the generation word; not 1, the hart parks; the fence r, r
   10207040c:	08093503          	ld	a0,128(s2) # 20405080 <BE_R3_HSTATUS_CONTROL_MASK+0x1fcc5d00>
   102070410:	4585                	li	a1,1
   102070412:	0cb51963          	bne	a0,a1,1020704e4 <be_mvp_hart_main+0x13a>
   10207041a:	85e080e7          	jalr	-1954(ra) # 102008c74 <be_mvp_exec_fence_r_r>
# L1 P1: desc->hgatp, for the hart's one install
   102070496:	01093503          	ld	a0,16(s2)
# L2 writer, call site 8 (outbound ring): READY, ENTERED; fence w, w; the
#   head
   10207054c:	ec6080e7          	jalr	-314(ra) # 10207140e <be_mvp_post_ready>
   102070560:	f04080e7          	jalr	-252(ra) # 102071460 <be_mvp_post_entered>
   10207056a:	706080e7          	jalr	1798(ra) # 102008c6c <be_mvp_exec_fence_w_w>
   102070574:	3f4080e7          	jalr	1012(ra) # 102008964 <be_mvp_ring_publish>
