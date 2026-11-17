# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# hart_fail (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 4 (outbound ring, FAIL): post; fence w, w; the head
   10207065e:	eb6080e7          	jalr	-330(ra) # 102071510 <be_mvp_post_fail>
   102070668:	4d8080e7          	jalr	1240(ra) # 102008b3c <be_mvp_exec_fence_w_w>
   102070672:	1ea080e7          	jalr	490(ra) # 102008858 <be_mvp_ring_publish>
# L2 reader (acknowledged, inbound ring): acquire; fence r, r; take; nothing
#   released
   1020706d2:	1ac080e7          	jalr	428(ra) # 10200887a <be_mvp_ring_acquire>
   1020706dc:	46c080e7          	jalr	1132(ra) # 102008b44 <be_mvp_exec_fence_r_r>
   1020706ea:	1d8080e7          	jalr	472(ra) # 1020088be <be_mvp_ring_take>
