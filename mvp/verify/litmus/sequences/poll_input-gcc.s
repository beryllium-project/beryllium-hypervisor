# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# poll_input (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 1 (input ring): the batch posted; fence w, w; the
#   head
   1020696ac:	2a2080e7          	jalr	674(ra) # 10206a94a <be_mvp_input_flush>
   1020696ba:	508080e7          	jalr	1288(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   1020696c4:	24e080e7          	jalr	590(ra) # 10200890e <be_mvp_ring_publish>
