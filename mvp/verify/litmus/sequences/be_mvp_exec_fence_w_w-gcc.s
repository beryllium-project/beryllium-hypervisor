# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_exec_fence_w_w (mvp-executor.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# the executor's tail call of be_mvp_arch_fence_w_w
   102008ce0:	fffff317          	auipc	t1,0xfffff
   102008ce4:	7dc30067          	jr	2012(t1) # 1020084bc <be_mvp_arch_fence_w_w>
