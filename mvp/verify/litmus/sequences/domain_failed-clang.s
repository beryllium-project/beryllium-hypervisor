# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# domain_failed (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 3 (inbound ring, ACK): post; fence w, w; the head
   102069a38:	c10080e7          	jalr	-1008(ra) # 102008644 <be_mvp_ring_post>
   102069a42:	0fe080e7          	jalr	254(ra) # 102008b3c <be_mvp_exec_fence_w_w>
   102069a4c:	e10080e7          	jalr	-496(ra) # 102008858 <be_mvp_ring_publish>
