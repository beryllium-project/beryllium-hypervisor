# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# drain (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0 (outbound ring): acquire; fence r, r; take; fence r, w;
#   release
   10206968e:	2fc080e7          	jalr	764(ra) # 102008986 <be_mvp_ring_acquire>
   10206969a:	5de080e7          	jalr	1502(ra) # 102008c74 <be_mvp_exec_fence_r_r>
   1020696a6:	328080e7          	jalr	808(ra) # 1020089ca <be_mvp_ring_take>
   1020696b6:	5ca080e7          	jalr	1482(ra) # 102008c7c <be_mvp_exec_fence_r_w>
   1020696c0:	49a080e7          	jalr	1178(ra) # 102008b56 <be_mvp_ring_release>
# L2 writer, call site 2 (inbound ring, ping's PING): post; fence w, w; the
#   head
   10206975a:	19a080e7          	jalr	410(ra) # 1020088f0 <be_mvp_ring_post_words>
   102069764:	50c080e7          	jalr	1292(ra) # 102008c6c <be_mvp_exec_fence_w_w>
   10206976e:	1fa080e7          	jalr	506(ra) # 102008964 <be_mvp_ring_publish>
