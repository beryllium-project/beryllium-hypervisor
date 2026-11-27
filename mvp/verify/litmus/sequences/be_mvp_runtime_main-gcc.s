# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_runtime_main (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P0: publish_blocks, inlined here: each block filled (be_mvp_block_fill)
   10207c3e4:	db0080e7          	jalr	-592(ra) # 102079190 <be_mvp_block_fill>
# L1 P0: the fence w, w, then the generation words, domain 0's and domain
#   1's (s3 = 1)
   10207c4f8:	6ca080e7          	jalr	1738(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   10207c502:	0937b023          	sd	s3,128(a5) # 20405080 <BE_R3_HSTATUS_CONTROL_MASK+0x1fcc5d00>
   10207c50c:	0937b023          	sd	s3,128(a5) # 20407080 <BE_R3_HSTATUS_CONTROL_MASK+0x1fcc7d00>
