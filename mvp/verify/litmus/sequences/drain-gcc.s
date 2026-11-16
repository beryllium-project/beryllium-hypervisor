# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# drain (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0 (outbound ring): acquire; fence r, r; take; fence r, w;
#   release
   102069766:	2ce080e7          	jalr	718(ra) # 102008a30 <be_mvp_ring_acquire>
   102069788:	540080e7          	jalr	1344(ra) # 102008cc4 <be_mvp_exec_fence_r_r>
   10206979a:	2e6080e7          	jalr	742(ra) # 102008a7c <be_mvp_ring_take>
   1020697ac:	524080e7          	jalr	1316(ra) # 102008ccc <be_mvp_exec_fence_r_w>
   1020697b6:	430080e7          	jalr	1072(ra) # 102008be2 <be_mvp_ring_release>
# L2 writer, call site 2 (inbound ring, ping's PING): post; fence w, w; the
#   head
   1020698ae:	0e2080e7          	jalr	226(ra) # 10200898c <be_mvp_ring_post_words>
   1020698bc:	404080e7          	jalr	1028(ra) # 102008cbc <be_mvp_exec_fence_w_w>
   1020698c6:	14a080e7          	jalr	330(ra) # 102008a0c <be_mvp_ring_publish>
# L2 writer, call site 3 (inbound ring, domain_failed's ACK): post; fence w,
#   w; the head
   102069b06:	cd4080e7          	jalr	-812(ra) # 1020087d6 <be_mvp_ring_post>
   102069b10:	1b0080e7          	jalr	432(ra) # 102008cbc <be_mvp_exec_fence_w_w>
   102069b1a:	ef6080e7          	jalr	-266(ra) # 102008a0c <be_mvp_ring_publish>
