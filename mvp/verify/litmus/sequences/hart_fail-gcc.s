# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# hart_fail (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 4 (outbound ring, FAIL): post; fence w, w; the head
   102066038:	2be080e7          	jalr	702(ra) # 1020672f2 <be_mvp_post_fail>
   102066042:	fdc080e7          	jalr	-36(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   10206604e:	63e080e7          	jalr	1598(ra) # 102068688 <be_mvp_ring_publish>
# L2 reader (acknowledged, inbound ring): acquire; fence r, r; take; nothing
#   released
   102066090:	620080e7          	jalr	1568(ra) # 1020686ac <be_mvp_ring_acquire>
   1020660e0:	f46080e7          	jalr	-186(ra) # 10206a022 <be_mvp_exec_fence_r_r>
   1020660fa:	602080e7          	jalr	1538(ra) # 1020686f8 <be_mvp_ring_take>
