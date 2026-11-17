# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# be_mvp_exec_fence_r_w (mvp-executor.c), gcc: the lines the litmus tests mirror, as
# objdump -d prints them (litmus.py --check-sequences). Specification SHA-256 ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
# the executor's tail call of be_mvp_arch_fence_r_w
   102008bce:	00000317          	auipc	t1,0x0
   102008bd2:	8fe30067          	jr	-1794(t1) # 1020084cc <be_mvp_arch_fence_r_w>
