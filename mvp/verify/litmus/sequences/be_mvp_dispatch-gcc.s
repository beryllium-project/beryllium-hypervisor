# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_dispatch (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 reader, L5 P0 (console_read, input ring): acquire; fence r, r; serve;
#   fence r, w; release
   10207038c:	5aa080e7          	jalr	1450(ra) # 102008932 <be_mvp_ring_acquire>
   102070394:	836080e7          	jalr	-1994(ra) # 102008bc6 <be_mvp_exec_fence_r_r>
   1020703a8:	042080e7          	jalr	66(ra) # 1020713e6 <be_mvp_input_serve>
   1020703bc:	816080e7          	jalr	-2026(ra) # 102008bce <be_mvp_exec_fence_r_w>
   1020703c8:	720080e7          	jalr	1824(ra) # 102008ae4 <be_mvp_ring_release>
# L2 reader, L4 P0 (tick, inbound ring): acquire; fence r, r; serve; fence r,
#   w; release; then L2 writer, call site 6 (outbound ring, PONG): fence w,
#   w; the head
   1020703f0:	546080e7          	jalr	1350(ra) # 102008932 <be_mvp_ring_acquire>
   1020703f8:	7d2080e7          	jalr	2002(ra) # 102008bc6 <be_mvp_exec_fence_r_r>
   102070418:	d2c080e7          	jalr	-724(ra) # 102071140 <be_mvp_ipi_serve>
   102070428:	7aa080e7          	jalr	1962(ra) # 102008bce <be_mvp_exec_fence_r_w>
   102070434:	6b4080e7          	jalr	1716(ra) # 102008ae4 <be_mvp_ring_release>
   102070442:	780080e7          	jalr	1920(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   10207044e:	4c4080e7          	jalr	1220(ra) # 10200890e <be_mvp_ring_publish>
# L2 writer, call site 7 (outbound ring, stopped's SHUTDOWN): post; fence w,
#   w; the head
   102070488:	dd8080e7          	jalr	-552(ra) # 10207125c <be_mvp_post_shutdown>
   102070492:	730080e7          	jalr	1840(ra) # 102008bbe <be_mvp_exec_fence_w_w>
   10207049e:	474080e7          	jalr	1140(ra) # 10200890e <be_mvp_ring_publish>
