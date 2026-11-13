# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# hart_fail (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 4 (outbound ring, FAIL): post; fence w, w; the head
   102070686:	e96080e7          	jalr	-362(ra) # 102071518 <be_mvp_post_fail>
   102070690:	5e0080e7          	jalr	1504(ra) # 102008c6c <be_mvp_exec_fence_w_w>
   10207069a:	2ce080e7          	jalr	718(ra) # 102008964 <be_mvp_ring_publish>
# L2 reader (acknowledged, inbound ring): acquire; fence r, r; take; nothing
#   released
   1020706da:	2b0080e7          	jalr	688(ra) # 102008986 <be_mvp_ring_acquire>
   1020706e4:	594080e7          	jalr	1428(ra) # 102008c74 <be_mvp_exec_fence_r_r>
   1020706f2:	2dc080e7          	jalr	732(ra) # 1020089ca <be_mvp_ring_take>
