# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# publish_blocks (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L1 P0: each block filled (be_mvp_block_fill)
   102064fa6:	b9a080e7          	jalr	-1126(ra) # 102067b3c <be_mvp_block_fill>
# L1 P0: the fence w, w, then the generation words, domain 0's and domain
#   1's (s1 = 1)
   1020650a6:	740080e7          	jalr	1856(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   1020650b8:	4485                	li	s1,1
   1020650ba:	16953423          	sd	s1,360(a0)
   1020650ca:	16953423          	sd	s1,360(a0)
