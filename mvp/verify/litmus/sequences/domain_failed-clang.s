# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# domain_failed (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 3 (inbound ring, ACK): post; fence w, w; the head
   1020660d6:	926080e7          	jalr	-1754(ra) # 1020689f8 <be_mvp_ring_post>
   1020660e0:	706080e7          	jalr	1798(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   1020660ea:	b26080e7          	jalr	-1242(ra) # 102068c0c <be_mvp_ring_publish>
