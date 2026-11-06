# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# poll_input (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 1 (input ring): the batch posted; fence w, w; the
#   head
   10206499a:	90e080e7          	jalr	-1778(ra) # 10206a2a4 <be_mvp_input_flush>
   1020649a8:	676080e7          	jalr	1654(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   1020649b2:	cda080e7          	jalr	-806(ra) # 102068688 <be_mvp_ring_publish>
