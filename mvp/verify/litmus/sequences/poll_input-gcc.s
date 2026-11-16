# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# poll_input (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 1 (input ring): the batch posted; fence w, w; the
#   head
   10206957e:	eba080e7          	jalr	-326(ra) # 10206b434 <be_mvp_input_flush>
   10206958c:	734080e7          	jalr	1844(ra) # 102008cbc <be_mvp_exec_fence_w_w>
   102069596:	47a080e7          	jalr	1146(ra) # 102008a0c <be_mvp_ring_publish>
