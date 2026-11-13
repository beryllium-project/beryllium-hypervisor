# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# stopped (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 7 (outbound ring, SHUTDOWN): post; fence w, w; the
#   head
   102070372:	11e080e7          	jalr	286(ra) # 10207148c <be_mvp_post_shutdown>
   10207037c:	8f4080e7          	jalr	-1804(ra) # 102008c6c <be_mvp_exec_fence_w_w>
   102070386:	5e2080e7          	jalr	1506(ra) # 102008964 <be_mvp_ring_publish>
