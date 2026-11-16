# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# publish_blocks (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P0: each block filled (be_mvp_block_fill)
   10207b376:	c8e080e7          	jalr	-882(ra) # 102079000 <be_mvp_block_fill>
# L1 P0: the fence w, w, then the generation words, domain 0's and domain
#   1's (a1 = 1)
   10207b534:	72c080e7          	jalr	1836(ra) # 102008c5c <be_mvp_exec_fence_w_w>
   10207b53c:	4585                	li	a1,1
   10207b540:	e14c                	sd	a1,128(a0)
   10207b548:	e14c                	sd	a1,128(a0)
