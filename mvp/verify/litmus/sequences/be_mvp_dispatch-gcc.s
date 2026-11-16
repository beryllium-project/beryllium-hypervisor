# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_dispatch (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 reader, L5 P0 (console_read, input ring): acquire; fence r, r; serve;
#   fence r, w; release
   10207046e:	5c6080e7          	jalr	1478(ra) # 102008a30 <be_mvp_ring_acquire>
   102070476:	852080e7          	jalr	-1966(ra) # 102008cc4 <be_mvp_exec_fence_r_r>
   10207048a:	0dc080e7          	jalr	220(ra) # 102071562 <be_mvp_input_serve>
   10207049e:	832080e7          	jalr	-1998(ra) # 102008ccc <be_mvp_exec_fence_r_w>
   1020704aa:	73c080e7          	jalr	1852(ra) # 102008be2 <be_mvp_ring_release>
# L2 reader, L4 P0 (tick, inbound ring): acquire; fence r, r; serve; fence r,
#   w; release; then L2 writer, call site 6 (outbound ring, PONG): fence w,
#   w; the head
   1020704d2:	562080e7          	jalr	1378(ra) # 102008a30 <be_mvp_ring_acquire>
   1020704da:	7ee080e7          	jalr	2030(ra) # 102008cc4 <be_mvp_exec_fence_r_r>
   1020704fa:	d6e080e7          	jalr	-658(ra) # 102071264 <be_mvp_ipi_serve>
   10207050a:	7c6080e7          	jalr	1990(ra) # 102008ccc <be_mvp_exec_fence_r_w>
   102070516:	6d0080e7          	jalr	1744(ra) # 102008be2 <be_mvp_ring_release>
   102070524:	79c080e7          	jalr	1948(ra) # 102008cbc <be_mvp_exec_fence_w_w>
   102070530:	4e0080e7          	jalr	1248(ra) # 102008a0c <be_mvp_ring_publish>
# L2 writer, call site 7 (outbound ring, stopped's SHUTDOWN): post; fence w,
#   w; the head
   10207056a:	e1a080e7          	jalr	-486(ra) # 102071380 <be_mvp_post_shutdown>
   102070574:	74c080e7          	jalr	1868(ra) # 102008cbc <be_mvp_exec_fence_w_w>
   102070580:	490080e7          	jalr	1168(ra) # 102008a0c <be_mvp_ring_publish>
