# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_input_flush (mvp-input.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L5 P1: the room asked
   10206ac2c:	b64080e7          	jalr	-1180(ra) # 10200878c <be_mvp_ring_room>
# L5 P1: the batch, the room or the pending bytes, the fewer; no room:
#   dropped
   10206ac36:	8b2a                	mv	s6,a0
   10206ac38:	89aa                	mv	s3,a0
   10206ac3a:	01956363          	bltu	a0,s9,10206ac40 <be_mvp_input_flush+0x7c>
   10206ac3e:	89e6                	mv	s3,s9
   10206ac40:	040b0963          	beqz	s6,10206ac92 <be_mvp_input_flush+0xce>
# L5 P1: the post
   10206ac5c:	9ec080e7          	jalr	-1556(ra) # 102008644 <be_mvp_ring_post>
# L5 P1: the drop count, hart 0's own word
   10206acb2:	04b93423          	sd	a1,72(s2)
