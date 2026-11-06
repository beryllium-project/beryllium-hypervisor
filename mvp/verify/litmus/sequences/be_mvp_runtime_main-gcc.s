# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_runtime_main (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P0: publish_blocks, inlined here: each block filled (be_mvp_block_fill)
   102065afc:	b82080e7          	jalr	-1150(ra) # 10206767a <be_mvp_block_fill>
# L1 P0: the fence w, w, then the generation words, domain 0's and domain
#   1's (s0 = 1)
   102065bfa:	424080e7          	jalr	1060(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   102065c0a:	16853423          	sd	s0,360(a0)
   102065c1c:	16853423          	sd	s0,360(a0)
