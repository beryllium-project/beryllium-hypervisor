# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# console (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 5 (outbound ring, LINE): post; fence w, w; the head
   102070248:	c14080e7          	jalr	-1004(ra) # 102070e58 <be_mvp_console_feed>
   10207025a:	968080e7          	jalr	-1688(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   102070266:	6ac080e7          	jalr	1708(ra) # 10200890e <be_mvp_ring_publish>
