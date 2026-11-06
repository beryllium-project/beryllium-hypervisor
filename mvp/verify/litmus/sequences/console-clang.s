# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# console (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 5 (outbound ring, LINE): post; fence w, w; the head
   102066514:	08a080e7          	jalr	138(ra) # 10206759a <be_mvp_console_feed>
   102066524:	2c2080e7          	jalr	706(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   10206652e:	6e2080e7          	jalr	1762(ra) # 102068c0c <be_mvp_ring_publish>
