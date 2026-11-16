# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_dispatch (mvp-hartmain.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 reader, L4 P0 (tick, inbound ring): acquire; fence r, r; serve; served,
#   on to fence r, w; release; then L2 writer, call site 6 (outbound ring,
#   PONG): fence w, w; the head
   1020701d6:	7c8080e7          	jalr	1992(ra) # 10200899a <be_mvp_ring_acquire>
   1020701de:	a8a080e7          	jalr	-1398(ra) # 102008c64 <be_mvp_exec_fence_r_r>
   1020701fe:	dc0080e7          	jalr	-576(ra) # 102070fba <be_mvp_ipi_serve>
   102070202:	ed29                	bnez	a0,10207025c <be_mvp_dispatch+0x182>
   102070260:	a10080e7          	jalr	-1520(ra) # 102008c6c <be_mvp_exec_fence_r_w>
   10207026a:	904080e7          	jalr	-1788(ra) # 102008b6a <be_mvp_ring_release>
   102070286:	9da080e7          	jalr	-1574(ra) # 102008c5c <be_mvp_exec_fence_w_w>
   102070290:	6ec080e7          	jalr	1772(ra) # 102008978 <be_mvp_ring_publish>
# L2 reader, L5 P0 (console_read, input ring): acquire; fence r, r; serve;
#   fence r, w; release
   102070184:	81a080e7          	jalr	-2022(ra) # 10200899a <be_mvp_ring_acquire>
   10207018c:	adc080e7          	jalr	-1316(ra) # 102008c64 <be_mvp_exec_fence_r_r>
   10207019e:	5e4080e7          	jalr	1508(ra) # 10207177e <be_mvp_input_serve>
   1020701ae:	ac2080e7          	jalr	-1342(ra) # 102008c6c <be_mvp_exec_fence_r_w>
   1020701b8:	9b6080e7          	jalr	-1610(ra) # 102008b6a <be_mvp_ring_release>
