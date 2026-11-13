# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# domain_failed (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 3 (inbound ring, ACK): post; fence w, w; the head
   102069b04:	c50080e7          	jalr	-944(ra) # 102008750 <be_mvp_ring_post>
   102069b0e:	162080e7          	jalr	354(ra) # 102008c6c <be_mvp_exec_fence_w_w>
   102069b18:	e50080e7          	jalr	-432(ra) # 102008964 <be_mvp_ring_publish>
