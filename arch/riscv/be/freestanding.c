// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: minimal freestanding byte primitives required by compiler-lowered
 *          fixed-size R1/R2/R3 structure operations.
 * Trust:   restricted support code with explicit bounded loops.
 * Scope:   no allocator, strings, formatting, overlap semantics, or libc ABI
 *          beyond the two compiler-required byte operations.
 */
#include "r3-platform.h"

void *memcpy(void *destination, const void *source, be_size count)
{
	be_u8 *to = (be_u8 *)destination;
	const be_u8 *from = (const be_u8 *)source;
	be_size index;

	for (index = 0U; index < count; ++index)
		to[index] = from[index];
	return destination;
}

void *memset(void *destination, int value, be_size count)
{
	be_u8 *bytes = (be_u8 *)destination;
	be_u8 byte = (be_u8)value;
	be_size index;

	for (index = 0U; index < count; ++index)
		bytes[index] = byte;
	return destination;
}
