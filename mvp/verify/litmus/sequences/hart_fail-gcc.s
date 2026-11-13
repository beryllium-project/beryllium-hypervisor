# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# hart_fail (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 4 (outbound ring, FAIL): post; fence w, w; the head
   102070134:	1dc080e7          	jalr	476(ra) # 10207130c <be_mvp_post_fail>
   10207013e:	ba6080e7          	jalr	-1114(ra) # 102008ce0 <be_mvp_exec_fence_w_w>
   10207014a:	8c6080e7          	jalr	-1850(ra) # 102008a0c <be_mvp_ring_publish>
# L2 reader (acknowledged, inbound ring): acquire; fence r, r; take; nothing
#   released
   10207018c:	8a8080e7          	jalr	-1880(ra) # 102008a30 <be_mvp_ring_acquire>
   1020701dc:	b10080e7          	jalr	-1264(ra) # 102008ce8 <be_mvp_exec_fence_r_r>
   1020701f6:	88a080e7          	jalr	-1910(ra) # 102008a7c <be_mvp_ring_take>
