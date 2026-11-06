# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# console (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 5 (outbound ring, LINE): post; fence w, w; the head
   10206621c:	ca0080e7          	jalr	-864(ra) # 102066eb8 <be_mvp_console_feed>
   10206622e:	df0080e7          	jalr	-528(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   10206623a:	452080e7          	jalr	1106(ra) # 102068688 <be_mvp_ring_publish>
