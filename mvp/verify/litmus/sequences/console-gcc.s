# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# console (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 5 (outbound ring, LINE): post; fence w, w; the head
   10207032a:	c56080e7          	jalr	-938(ra) # 102070f7c <be_mvp_console_feed>
   10207033c:	984080e7          	jalr	-1660(ra) # 102008cbc <be_mvp_exec_fence_w_w>
   102070348:	6c8080e7          	jalr	1736(ra) # 102008a0c <be_mvp_ring_publish>
