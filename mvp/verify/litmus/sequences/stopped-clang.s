# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# stopped (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 7 (outbound ring, SHUTDOWN): post; fence w, w; the
#   head
   102070358:	116080e7          	jalr	278(ra) # 10207146a <be_mvp_post_shutdown>
   102070362:	7de080e7          	jalr	2014(ra) # 102008b3c <be_mvp_exec_fence_w_w>
   10207036c:	4f0080e7          	jalr	1264(ra) # 102008858 <be_mvp_ring_publish>
