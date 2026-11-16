# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_input_flush (mvp-input.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the room asked
   10206b5c8:	2e8080e7          	jalr	744(ra) # 1020088ac <be_mvp_ring_room>
# L5 P1: the batch, the room or the pending bytes, the fewer; no room:
#   dropped
   10206b5d2:	8b2a                	mv	s6,a0
   10206b5d4:	89aa                	mv	s3,a0
   10206b5d6:	01956363          	bltu	a0,s9,10206b5dc <be_mvp_input_flush+0x7c>
   10206b5da:	89e6                	mv	s3,s9
   10206b5dc:	040b0963          	beqz	s6,10206b62e <be_mvp_input_flush+0xce>
# L5 P1: the post
   10206b5f8:	170080e7          	jalr	368(ra) # 102008764 <be_mvp_ring_post>
# L5 P1: the drop count, hart 0's own word
   10206b64e:	04b93423          	sd	a1,72(s2)
