# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_dispatch (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 reader, L4 P0 (tick, inbound ring): acquire; fence r, r; serve; served,
#   on to fence r, w; release; then L2 writer, call site 6 (outbound ring,
#   PONG): fence w, w; the head
   1020701d6:	6a8080e7          	jalr	1704(ra) # 10200887a <be_mvp_ring_acquire>
   1020701de:	96a080e7          	jalr	-1686(ra) # 102008b44 <be_mvp_exec_fence_r_r>
   1020701fe:	cde080e7          	jalr	-802(ra) # 102070ed8 <be_mvp_ipi_serve>
   102070202:	ed29                	bnez	a0,10207025c <be_mvp_dispatch+0x182>
   102070260:	8f0080e7          	jalr	-1808(ra) # 102008b4c <be_mvp_exec_fence_r_w>
   10207026a:	7e4080e7          	jalr	2020(ra) # 102008a4a <be_mvp_ring_release>
   102070286:	8ba080e7          	jalr	-1862(ra) # 102008b3c <be_mvp_exec_fence_w_w>
   102070290:	5cc080e7          	jalr	1484(ra) # 102008858 <be_mvp_ring_publish>
# L2 reader, L5 P0 (console_read, input ring): acquire; fence r, r; serve;
#   fence r, w; release
   102070184:	6fa080e7          	jalr	1786(ra) # 10200887a <be_mvp_ring_acquire>
   10207018c:	9bc080e7          	jalr	-1604(ra) # 102008b44 <be_mvp_exec_fence_r_r>
   10207019e:	45e080e7          	jalr	1118(ra) # 1020715f8 <be_mvp_input_serve>
   1020701ae:	9a2080e7          	jalr	-1630(ra) # 102008b4c <be_mvp_exec_fence_r_w>
   1020701b8:	896080e7          	jalr	-1898(ra) # 102008a4a <be_mvp_ring_release>
