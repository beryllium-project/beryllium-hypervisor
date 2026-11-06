# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# hart_fail (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 4 (outbound ring, FAIL): post; fence w, w; the head
   102066892:	f76080e7          	jalr	-138(ra) # 102067804 <be_mvp_post_fail>
   10206689c:	f4a080e7          	jalr	-182(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   1020668a6:	36a080e7          	jalr	874(ra) # 102068c0c <be_mvp_ring_publish>
# L2 reader (acknowledged, inbound ring): acquire; fence r, r; take; nothing
#   released
   1020668e6:	34c080e7          	jalr	844(ra) # 102068c2e <be_mvp_ring_acquire>
   1020668f0:	efe080e7          	jalr	-258(ra) # 10206a7ea <be_mvp_exec_fence_r_r>
   1020668fe:	378080e7          	jalr	888(ra) # 102068c72 <be_mvp_ring_take>
