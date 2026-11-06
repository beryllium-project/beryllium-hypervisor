# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# stopped (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 7 (outbound ring, SHUTDOWN): post; fence w, w; the
#   head
   1020665b8:	1c4080e7          	jalr	452(ra) # 102067778 <be_mvp_post_shutdown>
   1020665c2:	224080e7          	jalr	548(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   1020665cc:	644080e7          	jalr	1604(ra) # 102068c0c <be_mvp_ring_publish>
