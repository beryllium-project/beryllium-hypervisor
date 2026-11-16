# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_hart_main (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P1: the generation word; not 1, the hart parks; the fence r, r
   1020703ec:	08093503          	ld	a0,128(s2) # 20405080 <BE_R3_HSTATUS_CONTROL_MASK+0x1fcc5d00>
   1020703f0:	4585                	li	a1,1
   1020703f2:	0cb51963          	bne	a0,a1,1020704c4 <be_mvp_hart_main+0x13c>
   1020703fa:	86e080e7          	jalr	-1938(ra) # 102008c64 <be_mvp_exec_fence_r_r>
# L1 P1: desc->hgatp, for the hart's one install
   102070476:	01093503          	ld	a0,16(s2)
# L2 writer, call site 8 (outbound ring): READY, ENTERED; fence w, w; the
#   head
   102070532:	f14080e7          	jalr	-236(ra) # 102071442 <be_mvp_post_ready>
   102070548:	ffe080e7          	jalr	-2(ra) # 102071542 <be_mvp_post_entered>
   102070552:	70e080e7          	jalr	1806(ra) # 102008c5c <be_mvp_exec_fence_w_w>
   10207055c:	420080e7          	jalr	1056(ra) # 102008978 <be_mvp_ring_publish>
