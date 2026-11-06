# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# poll_input (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 writer, call site 1 (input ring): the batch posted; fence w, w; the
#   head
   10206576e:	392080e7          	jalr	914(ra) # 10206aafc <be_mvp_input_flush>
   10206577c:	06a080e7          	jalr	106(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   102065786:	48a080e7          	jalr	1162(ra) # 102068c0c <be_mvp_ring_publish>
