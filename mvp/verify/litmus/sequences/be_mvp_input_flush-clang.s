# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_input_flush (mvp-input.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the room asked
   10206ab64:	fe0080e7          	jalr	-32(ra) # 102068b40 <be_mvp_ring_room>
# L5 P1: the batch, the room or the pending bytes, the fewer; no room:
#   dropped
   10206ab6e:	8b2a                	mv	s6,a0
   10206ab70:	89aa                	mv	s3,a0
   10206ab72:	01956363          	bltu	a0,s9,10206ab78 <be_mvp_input_flush+0x7c>
   10206ab76:	89e6                	mv	s3,s9
   10206ab78:	040b0963          	beqz	s6,10206abca <be_mvp_input_flush+0xce>
# L5 P1: the post
   10206ab94:	e68080e7          	jalr	-408(ra) # 1020689f8 <be_mvp_ring_post>
# L5 P1: the drop count, hart 0's own word
   10206abea:	04b93423          	sd	a1,72(s2)
