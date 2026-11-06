/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the separately built K3 B5 test guest's code and read-only data,
 *          embedded as the management guest-code page (GPA 0x4001_0000,
 *          PA 0x1_0203_2000), which the accepted management root maps R-X.
 * Trust:   untrusted VS bytes. The build pins their SHA-256 per toolchain,
 *          and tests/check-b5-image.py compares the page with that binary.
 * Scope:   B5 only. BE_B5_GUEST_BIN names the extracted guest binary.
 */

#ifndef BE_B5_GUEST_BIN
#error "BE_B5_GUEST_BIN must name the extracted guest binary"
#endif

	.section .guest.b5.payload, "ax", @progbits
	.globl be_b5_payload
	.type be_b5_payload, @object
be_b5_payload:
	.incbin	BE_B5_GUEST_BIN
	.globl be_b5_payload_end
be_b5_payload_end:
	.size be_b5_payload, . - be_b5_payload
