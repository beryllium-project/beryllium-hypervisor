# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# poll_input (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 1 (input ring): the batch posted; fence w, w; the
#   head
   102069388:	1dc080e7          	jalr	476(ra) # 10206b560 <be_mvp_input_flush>
   102069396:	8ca080e7          	jalr	-1846(ra) # 102008c5c <be_mvp_exec_fence_w_w>
   1020693a0:	5dc080e7          	jalr	1500(ra) # 102008978 <be_mvp_ring_publish>
