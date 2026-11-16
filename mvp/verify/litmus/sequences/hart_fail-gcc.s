# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# hart_fail (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 4 (outbound ring, FAIL): post; fence w, w; the head
   102070132:	2f2080e7          	jalr	754(ra) # 102071420 <be_mvp_post_fail>
   10207013c:	b84080e7          	jalr	-1148(ra) # 102008cbc <be_mvp_exec_fence_w_w>
   102070148:	8c8080e7          	jalr	-1848(ra) # 102008a0c <be_mvp_ring_publish>
# L2 reader (acknowledged, inbound ring): acquire; fence r, r; take; nothing
#   released
   1020701aa:	88a080e7          	jalr	-1910(ra) # 102008a30 <be_mvp_ring_acquire>
   1020701f2:	ad6080e7          	jalr	-1322(ra) # 102008cc4 <be_mvp_exec_fence_r_r>
   10207020a:	876080e7          	jalr	-1930(ra) # 102008a7c <be_mvp_ring_take>
