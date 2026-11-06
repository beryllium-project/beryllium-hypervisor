# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# drain (mvp-runtime.c), clang: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# L2 P1, L3 P0 (outbound ring): acquire; fence r, r; take; fence r, w;
#   release
   102065c56:	fdc080e7          	jalr	-36(ra) # 102068c2e <be_mvp_ring_acquire>
   102065c62:	b8c080e7          	jalr	-1140(ra) # 10206a7ea <be_mvp_exec_fence_r_r>
   102065c6e:	008080e7          	jalr	8(ra) # 102068c72 <be_mvp_ring_take>
   102065c7e:	b78080e7          	jalr	-1160(ra) # 10206a7f2 <be_mvp_exec_fence_r_w>
   102065c88:	17a080e7          	jalr	378(ra) # 102068dfe <be_mvp_ring_release>
# L2 writer, call site 2 (inbound ring, ping's PING): post; fence w, w; the
#   head
   102065d22:	e7a080e7          	jalr	-390(ra) # 102068b98 <be_mvp_ring_post_words>
   102065d2c:	aba080e7          	jalr	-1350(ra) # 10206a7e2 <be_mvp_exec_fence_w_w>
   102065d36:	eda080e7          	jalr	-294(ra) # 102068c0c <be_mvp_ring_publish>
