# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_dispatch (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 reader, L4 P0 (ipi, inbound ring): acquire; fence r, r; serve; served,
#   on to fence r, w; release; then L2 writer, call site 6 (outbound ring,
#   PONG): fence w, w; the head
   102070176:	814080e7          	jalr	-2028(ra) # 102008986 <be_mvp_ring_acquire>
   10207017e:	afa080e7          	jalr	-1286(ra) # 102008c74 <be_mvp_exec_fence_r_r>
   10207019c:	e18080e7          	jalr	-488(ra) # 102070fb0 <be_mvp_ipi_serve>
   1020701a0:	e95d                	bnez	a0,102070256 <be_mvp_dispatch+0x17c>
   10207025a:	a26080e7          	jalr	-1498(ra) # 102008c7c <be_mvp_exec_fence_r_w>
   102070264:	8f6080e7          	jalr	-1802(ra) # 102008b56 <be_mvp_ring_release>
   10207026e:	a02080e7          	jalr	-1534(ra) # 102008c6c <be_mvp_exec_fence_w_w>
   102070278:	6f0080e7          	jalr	1776(ra) # 102008964 <be_mvp_ring_publish>
# L2 reader, L5 P0 (console_read, input ring): acquire; fence r, r; serve;
#   fence r, w; release
   1020701ba:	7d0080e7          	jalr	2000(ra) # 102008986 <be_mvp_ring_acquire>
   1020701c2:	ab6080e7          	jalr	-1354(ra) # 102008c74 <be_mvp_exec_fence_r_r>
   1020701d4:	46e080e7          	jalr	1134(ra) # 10207163e <be_mvp_input_serve>
   1020701e4:	a9c080e7          	jalr	-1380(ra) # 102008c7c <be_mvp_exec_fence_r_w>
   1020701ee:	96c080e7          	jalr	-1684(ra) # 102008b56 <be_mvp_ring_release>
