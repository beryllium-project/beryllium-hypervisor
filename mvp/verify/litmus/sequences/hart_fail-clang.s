# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# hart_fail (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 4 (outbound ring, FAIL): post; fence w, w; the head
   102070666:	fd4080e7          	jalr	-44(ra) # 102071636 <be_mvp_post_fail>
   102070670:	5f0080e7          	jalr	1520(ra) # 102008c5c <be_mvp_exec_fence_w_w>
   10207067a:	302080e7          	jalr	770(ra) # 102008978 <be_mvp_ring_publish>
# L2 reader (acknowledged, inbound ring): acquire; fence r, r; take; nothing
#   released
   1020706da:	2c4080e7          	jalr	708(ra) # 10200899a <be_mvp_ring_acquire>
   1020706e4:	584080e7          	jalr	1412(ra) # 102008c64 <be_mvp_exec_fence_r_r>
   1020706f2:	2f0080e7          	jalr	752(ra) # 1020089de <be_mvp_ring_take>
