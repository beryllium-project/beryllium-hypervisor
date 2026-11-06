# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_dispatch (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 reader, L5 P0 (console_read, input ring): acquire; fence r, r; serve;
#   fence r, w; release
   102066370:	340080e7          	jalr	832(ra) # 1020686ac <be_mvp_ring_acquire>
   102066378:	cae080e7          	jalr	-850(ra) # 10206a022 <be_mvp_exec_fence_r_r>
   10206638c:	09c080e7          	jalr	156(ra) # 10206a424 <be_mvp_input_serve>
   1020663a0:	c8e080e7          	jalr	-882(ra) # 10206a02a <be_mvp_exec_fence_r_w>
   1020663ac:	4b6080e7          	jalr	1206(ra) # 10206885e <be_mvp_ring_release>
# L2 reader, L4 P0 (ipi, inbound ring): acquire; fence r, r; serve; fence r,
#   w; release; then L2 writer, call site 6 (outbound ring, PONG): fence w,
#   w; the head
   1020663d2:	2de080e7          	jalr	734(ra) # 1020686ac <be_mvp_ring_acquire>
   1020663da:	c4c080e7          	jalr	-948(ra) # 10206a022 <be_mvp_exec_fence_r_r>
   1020663f8:	d96080e7          	jalr	-618(ra) # 10206718a <be_mvp_ipi_serve>
   102066404:	c2a080e7          	jalr	-982(ra) # 10206a02a <be_mvp_exec_fence_r_w>
   102066410:	452080e7          	jalr	1106(ra) # 10206885e <be_mvp_ring_release>
   10206641a:	c04080e7          	jalr	-1020(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   102066426:	266080e7          	jalr	614(ra) # 102068688 <be_mvp_ring_publish>
# L2 writer, call site 7 (outbound ring, stopped's SHUTDOWN): post; fence w,
#   w; the head
   102066468:	e0c080e7          	jalr	-500(ra) # 102067270 <be_mvp_post_shutdown>
   102066472:	bac080e7          	jalr	-1108(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   10206647e:	20e080e7          	jalr	526(ra) # 102068688 <be_mvp_ring_publish>
