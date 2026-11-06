/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the probe images' assembly: the VS probe stub's bytes, which
 *          hart 0 copies into both windows, and, in the two VMID probe
 *          images only, the raw hgatp write with no fence (planning/
 *          mvp-m0-plan.md, Platform record: probes).
 * Trust:   the raw write is the one exception to the rule that every hgatp
 *          write and hfence.gvma is the accepted install function's; the
 *          probe image checker profile admits exactly this function, in
 *          exactly the VMID images. The stub's bytes are data here, in the
 *          monitor's read-only segment, and never executed in place.
 * Scope:   probe images only. BE_MVP_PROBE_IMAGE names the probe image and
 *          BE_MVP_PROBE_STUB the stub's extracted binary.
 */

#if !defined(BE_MVP_PROBE_IMAGE)
#error "BE_MVP_PROBE_IMAGE must name the probe image"
#endif
#if !defined(BE_MVP_PROBE_STUB)
#error "BE_MVP_PROBE_STUB must name the probe stub's binary"
#endif

	.attribute arch, "rv64imach_zicsr_zifencei"
	.option norvc

	.section .rodata.mvp.probe.stub, "a", @progbits
	.balign 8
	.globl be_mvp_probe_stub
	.type be_mvp_probe_stub, @object
be_mvp_probe_stub:
	.incbin	BE_MVP_PROBE_STUB
	.globl be_mvp_probe_stub_end
be_mvp_probe_stub_end:
	.size be_mvp_probe_stub, . - be_mvp_probe_stub

#if BE_MVP_PROBE_IMAGE != 1
	/*
	 * The VMID probes' switch: hgatp for root B with no fence, read back.
	 * Any translation of root A that the hart cached under the same VMID
	 * survives; the stub's next read of X shows whether one did.
	 */
	.section .text.mvp.probe, "ax"
	.align 2
	.globl be_mvp_probe_arch_switch_hgatp
	.type be_mvp_probe_arch_switch_hgatp, @function
be_mvp_probe_arch_switch_hgatp:
	.option push
	.option arch, +h
	csrw	hgatp, a0
	csrr	a0, hgatp
	.option pop
	ret
	.size be_mvp_probe_arch_switch_hgatp, . - be_mvp_probe_arch_switch_hgatp
#endif
