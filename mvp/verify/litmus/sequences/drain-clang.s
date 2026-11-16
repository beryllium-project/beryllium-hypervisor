# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# drain (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0 (outbound ring): acquire; fence r, r; take; fence r, w;
#   release
   1020696c0:	2de080e7          	jalr	734(ra) # 10200899a <be_mvp_ring_acquire>
   1020696cc:	59c080e7          	jalr	1436(ra) # 102008c64 <be_mvp_exec_fence_r_r>
   1020696d8:	30a080e7          	jalr	778(ra) # 1020089de <be_mvp_ring_take>
   1020696e8:	588080e7          	jalr	1416(ra) # 102008c6c <be_mvp_exec_fence_r_w>
   1020696f2:	47c080e7          	jalr	1148(ra) # 102008b6a <be_mvp_ring_release>
# L2 writer, call site 2 (inbound ring, ping's PING): post; fence w, w; the
#   head
   102069788:	180080e7          	jalr	384(ra) # 102008904 <be_mvp_ring_post_words>
   102069792:	4ce080e7          	jalr	1230(ra) # 102008c5c <be_mvp_exec_fence_w_w>
   10206979c:	1e0080e7          	jalr	480(ra) # 102008978 <be_mvp_ring_publish>
