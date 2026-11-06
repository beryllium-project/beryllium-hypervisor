// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: bounded single-line text builder for B0 console markers.
 * Trust:   pure functions; every append checks capacity, keeps the buffer
 *          NUL-terminated, and records truncation instead of overrunning.
 * Scope:   no allocation, varargs, or libc dependency.
 */
#include "b0-format.h"

static void line_put(struct be_b0_line *line, char character)
{
	if (line->text == (char *)0 || line->capacity == 0UL)
		return;
	if (line->length + 1UL >= line->capacity) {
		line->overflow = 1UL;
		return;
	}
	line->text[line->length] = character;
	line->length += 1UL;
	line->text[line->length] = '\0';
}

void be_b0_line_init(struct be_b0_line *line, char *storage,
		     unsigned long capacity)
{
	line->text = storage;
	line->capacity = capacity;
	line->length = 0UL;
	line->overflow = 0UL;
	if (storage != (char *)0 && capacity != 0UL)
		storage[0] = '\0';
	else
		line->overflow = 1UL;
}

void be_b0_line_text(struct be_b0_line *line, const char *text)
{
	unsigned long index;

	if (text == (const char *)0) {
		line->overflow = 1UL;
		return;
	}
	for (index = 0UL; text[index] != '\0'; ++index) {
		if (index >= line->capacity) {
			line->overflow = 1UL;
			return;
		}
		line_put(line, text[index]);
	}
}

void be_b0_line_hex(struct be_b0_line *line, unsigned long value)
{
	static const char digits[] = "0123456789abcdef";
	unsigned int shift;

	line_put(line, '0');
	line_put(line, 'x');
	for (shift = 64U; shift != 0U;) {
		shift -= 4U;
		line_put(line, digits[(value >> shift) & 0xfUL]);
	}
}

void be_b0_line_flag(struct be_b0_line *line, unsigned long value)
{
	line_put(line, value != 0UL ? '1' : '0');
}
