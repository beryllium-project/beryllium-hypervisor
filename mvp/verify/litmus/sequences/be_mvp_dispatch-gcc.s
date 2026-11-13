# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_dispatch (mvp-hartmain.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 reader, L5 P0 (console_read, input ring): acquire; fence r, r; serve;
#   fence r, w; release
   10207046e:	5c6080e7          	jalr	1478(ra) # 102008a30 <be_mvp_ring_acquire>
   102070476:	876080e7          	jalr	-1930(ra) # 102008ce8 <be_mvp_exec_fence_r_r>
   10207048a:	fa6080e7          	jalr	-90(ra) # 10207142c <be_mvp_input_serve>
   10207049e:	856080e7          	jalr	-1962(ra) # 102008cf0 <be_mvp_exec_fence_r_w>
   1020704aa:	73c080e7          	jalr	1852(ra) # 102008be2 <be_mvp_ring_release>
# L2 reader, L4 P0 (ipi, inbound ring): acquire; fence r, r; serve; fence r,
#   w; release; then L2 writer, call site 6 (outbound ring, PONG): fence w,
#   w; the head
   1020704d0:	564080e7          	jalr	1380(ra) # 102008a30 <be_mvp_ring_acquire>
   1020704d8:	814080e7          	jalr	-2028(ra) # 102008ce8 <be_mvp_exec_fence_r_r>
   1020704f6:	cb2080e7          	jalr	-846(ra) # 1020711a4 <be_mvp_ipi_serve>
   102070502:	7f2080e7          	jalr	2034(ra) # 102008cf0 <be_mvp_exec_fence_r_w>
   10207050e:	6d8080e7          	jalr	1752(ra) # 102008be2 <be_mvp_ring_release>
   102070518:	7cc080e7          	jalr	1996(ra) # 102008ce0 <be_mvp_exec_fence_w_w>
   102070524:	4ec080e7          	jalr	1260(ra) # 102008a0c <be_mvp_ring_publish>
# L2 writer, call site 7 (outbound ring, stopped's SHUTDOWN): post; fence w,
#   w; the head
   102070566:	d28080e7          	jalr	-728(ra) # 10207128a <be_mvp_post_shutdown>
   102070570:	774080e7          	jalr	1908(ra) # 102008ce0 <be_mvp_exec_fence_w_w>
   10207057c:	494080e7          	jalr	1172(ra) # 102008a0c <be_mvp_ring_publish>
