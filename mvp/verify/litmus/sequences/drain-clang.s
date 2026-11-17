# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# drain (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0 (outbound ring): acquire; fence r, r; take; fence r, w;
#   release
   10206955c:	322080e7          	jalr	802(ra) # 10200887a <be_mvp_ring_acquire>
   102069568:	5e0080e7          	jalr	1504(ra) # 102008b44 <be_mvp_exec_fence_r_r>
   102069574:	34e080e7          	jalr	846(ra) # 1020088be <be_mvp_ring_take>
   102069584:	5cc080e7          	jalr	1484(ra) # 102008b4c <be_mvp_exec_fence_r_w>
   10206958e:	4c0080e7          	jalr	1216(ra) # 102008a4a <be_mvp_ring_release>
# L2 writer, call site 2 (inbound ring, ping's PING): post; fence w, w; the
#   head
   102069624:	1c4080e7          	jalr	452(ra) # 1020087e4 <be_mvp_ring_post_words>
   10206962e:	512080e7          	jalr	1298(ra) # 102008b3c <be_mvp_exec_fence_w_w>
   102069638:	224080e7          	jalr	548(ra) # 102008858 <be_mvp_ring_publish>
