# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_hart_main (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P1: the generation word; not 1, the hart parks; the fence r, r
   102066626:	16893503          	ld	a0,360(s2) # 3168 <MVP_HVIP_VS_BITS+0x2d24>
   10206662a:	4585                	li	a1,1
   10206662c:	0ab51d63          	bne	a0,a1,1020666e6 <be_mvp_hart_main+0xf6>
   102066638:	1b6080e7          	jalr	438(ra) # 10206a7ea <be_mvp_exec_fence_r_r>
# L1 P1: desc->hgatp, for the hart's one install
   102066694:	11093503          	ld	a0,272(s2)
# L2 writer, call site 8 (outbound ring): READY, ENTERED; fence w, w; the
#   head
   102066750:	fae080e7          	jalr	-82(ra) # 1020676fa <be_mvp_post_ready>
   102066764:	fec080e7          	jalr	-20(ra) # 10206774c <be_mvp_post_entered>
   10206676e:	078080e7          	jalr	120(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   102066778:	498080e7          	jalr	1176(ra) # 102068c0c <be_mvp_ring_publish>
