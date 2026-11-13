# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# console (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 5 (outbound ring, LINE): post; fence w, w; the head
   1020702ce:	fe4080e7          	jalr	-28(ra) # 1020712ae <be_mvp_console_feed>
   1020702de:	992080e7          	jalr	-1646(ra) # 102008c6c <be_mvp_exec_fence_w_w>
   1020702e8:	680080e7          	jalr	1664(ra) # 102008964 <be_mvp_ring_publish>
