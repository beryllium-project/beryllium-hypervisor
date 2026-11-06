# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# drain (mvp-runtime.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0 (outbound ring): acquire; fence r, r; take; fence r, w;
#   release
   102064ab2:	bfe080e7          	jalr	-1026(ra) # 1020686ac <be_mvp_ring_acquire>
   102064ad4:	552080e7          	jalr	1362(ra) # 10206a022 <be_mvp_exec_fence_r_r>
   102064ae6:	c16080e7          	jalr	-1002(ra) # 1020686f8 <be_mvp_ring_take>
   102064af8:	536080e7          	jalr	1334(ra) # 10206a02a <be_mvp_exec_fence_r_w>
   102064b02:	d60080e7          	jalr	-672(ra) # 10206885e <be_mvp_ring_release>
# L2 writer, call site 2 (inbound ring, ping's PING): post; fence w, w; the
#   head
   102064bfa:	a12080e7          	jalr	-1518(ra) # 102068608 <be_mvp_ring_post_words>
   102064c08:	416080e7          	jalr	1046(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   102064c12:	a7a080e7          	jalr	-1414(ra) # 102068688 <be_mvp_ring_publish>
# L2 writer, call site 3 (inbound ring, domain_failed's ACK): post; fence w,
#   w; the head
   102064e74:	5e2080e7          	jalr	1506(ra) # 102068452 <be_mvp_ring_post>
   102064e7e:	1a0080e7          	jalr	416(ra) # 10206a01a <be_mvp_exec_fence_w_w>
   102064e88:	804080e7          	jalr	-2044(ra) # 102068688 <be_mvp_ring_publish>
