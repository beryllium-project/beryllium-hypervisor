# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# hart_fail (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 4 (outbound ring, FAIL): post; fence w, w; the head
   1020700dc:	224080e7          	jalr	548(ra) # 1020712fc <be_mvp_post_fail>
   1020700e6:	adc080e7          	jalr	-1316(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   1020700f2:	820080e7          	jalr	-2016(ra) # 10200890e <be_mvp_ring_publish>
# L2 reader (acknowledged, inbound ring): acquire; fence r, r; take; nothing
#   released
   102070154:	7e2080e7          	jalr	2018(ra) # 102008932 <be_mvp_ring_acquire>
   102070198:	a32080e7          	jalr	-1486(ra) # 102008bc6 <be_mvp_exec_fence_r_r>
   1020701b0:	7d2080e7          	jalr	2002(ra) # 10200897e <be_mvp_ring_take>
