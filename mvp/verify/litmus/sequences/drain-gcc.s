# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# drain (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0 (outbound ring): acquire; fence r, r; take; fence r, w;
#   release
   102069696:	39e080e7          	jalr	926(ra) # 102008a30 <be_mvp_ring_acquire>
   1020696b8:	634080e7          	jalr	1588(ra) # 102008ce8 <be_mvp_exec_fence_r_r>
   1020696ca:	3b6080e7          	jalr	950(ra) # 102008a7c <be_mvp_ring_take>
   1020696dc:	618080e7          	jalr	1560(ra) # 102008cf0 <be_mvp_exec_fence_r_w>
   1020696e6:	500080e7          	jalr	1280(ra) # 102008be2 <be_mvp_ring_release>
# L2 writer, call site 2 (inbound ring, ping's PING): post; fence w, w; the
#   head
   1020697de:	1b2080e7          	jalr	434(ra) # 10200898c <be_mvp_ring_post_words>
   1020697ec:	4f8080e7          	jalr	1272(ra) # 102008ce0 <be_mvp_exec_fence_w_w>
   1020697f6:	21a080e7          	jalr	538(ra) # 102008a0c <be_mvp_ring_publish>
# L2 writer, call site 3 (inbound ring, domain_failed's ACK): post; fence w,
#   w; the head
   102069a58:	d82080e7          	jalr	-638(ra) # 1020087d6 <be_mvp_ring_post>
   102069a62:	282080e7          	jalr	642(ra) # 102008ce0 <be_mvp_exec_fence_w_w>
   102069a6c:	fa4080e7          	jalr	-92(ra) # 102008a0c <be_mvp_ring_publish>
