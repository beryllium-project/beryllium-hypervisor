# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# poll_input (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 1 (input ring): the batch posted; fence w, w; the
#   head
   102069d16:	eb2080e7          	jalr	-334(ra) # 10206abc4 <be_mvp_input_flush>
   102069d24:	e1c080e7          	jalr	-484(ra) # 102008b3c <be_mvp_exec_fence_w_w>
   102069d2e:	b2e080e7          	jalr	-1234(ra) # 102008858 <be_mvp_ring_publish>
