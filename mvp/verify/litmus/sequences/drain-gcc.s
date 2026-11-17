# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# drain (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0 (outbound ring): acquire; fence r, r; take; fence r, w;
#   release
   1020697c4:	172080e7          	jalr	370(ra) # 102008932 <be_mvp_ring_acquire>
   1020697e6:	3e4080e7          	jalr	996(ra) # 102008bc6 <be_mvp_exec_fence_r_r>
   1020697f8:	18a080e7          	jalr	394(ra) # 10200897e <be_mvp_ring_take>
   10206980a:	3c8080e7          	jalr	968(ra) # 102008bce <be_mvp_exec_fence_r_w>
   102069814:	2d4080e7          	jalr	724(ra) # 102008ae4 <be_mvp_ring_release>
# L2 writer, call site 2 (inbound ring, ping's PING): post; fence w, w; the
#   head
   10206990c:	f86080e7          	jalr	-122(ra) # 10200888e <be_mvp_ring_post_words>
   10206991a:	2a8080e7          	jalr	680(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   102069924:	fee080e7          	jalr	-18(ra) # 10200890e <be_mvp_ring_publish>
# L2 writer, call site 3 (inbound ring, domain_failed's ACK): post; fence w,
#   w; the head
   102069b64:	b78080e7          	jalr	-1160(ra) # 1020086d8 <be_mvp_ring_post>
   102069b6e:	054080e7          	jalr	84(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   102069b78:	d9a080e7          	jalr	-614(ra) # 10200890e <be_mvp_ring_publish>
