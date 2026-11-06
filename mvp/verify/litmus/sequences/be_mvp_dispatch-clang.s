# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_dispatch (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 reader, L4 P0 (ipi, inbound ring): acquire; fence r, r; serve; served,
#   on to fence r, w; release; then L2 writer, call site 6 (outbound ring,
#   PONG): fence w, w; the head
   1020663bc:	876080e7          	jalr	-1930(ra) # 102068c2e <be_mvp_ring_acquire>
   1020663c4:	42a080e7          	jalr	1066(ra) # 10206a7ea <be_mvp_exec_fence_r_r>
   1020663e2:	dfe080e7          	jalr	-514(ra) # 1020671dc <be_mvp_ipi_serve>
   1020663e6:	e95d                	bnez	a0,10206649c <be_mvp_dispatch+0x178>
   1020664a0:	356080e7          	jalr	854(ra) # 10206a7f2 <be_mvp_exec_fence_r_w>
   1020664aa:	958080e7          	jalr	-1704(ra) # 102068dfe <be_mvp_ring_release>
   1020664b4:	332080e7          	jalr	818(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   1020664be:	752080e7          	jalr	1874(ra) # 102068c0c <be_mvp_ring_publish>
# L2 reader, L5 P0 (console_read, input ring): acquire; fence r, r; serve;
#   fence r, w; release
   102066400:	832080e7          	jalr	-1998(ra) # 102068c2e <be_mvp_ring_acquire>
   102066408:	3e6080e7          	jalr	998(ra) # 10206a7ea <be_mvp_exec_fence_r_r>
   10206641a:	8a4080e7          	jalr	-1884(ra) # 10206acba <be_mvp_input_serve>
   10206642a:	3cc080e7          	jalr	972(ra) # 10206a7f2 <be_mvp_exec_fence_r_w>
   102066434:	9ce080e7          	jalr	-1586(ra) # 102068dfe <be_mvp_ring_release>
