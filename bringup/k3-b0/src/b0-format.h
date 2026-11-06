/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: bounded single-line text builder for B0 console markers.
 * Trust:   pure functions with explicit capacity checks; shared verbatim by
 *          the freestanding image and the host unit test.
 * Scope:   text, fixed-width hexadecimal, and 0/1 flags only.
 */

#ifndef BE_B0_FORMAT_H
#define BE_B0_FORMAT_H

#define BE_B0_LINE_CAPACITY 256UL

/**
 * struct be_b0_line - bounded, always NUL-terminated line buffer
 * @text: caller-owned storage of @capacity bytes
 * @capacity: storage size including the terminating NUL
 * @length: bytes appended, excluding the terminating NUL
 * @overflow: nonzero once any append was truncated
 */
struct be_b0_line {
	char *text;
	unsigned long capacity;
	unsigned long length;
	unsigned long overflow;
};

void be_b0_line_init(struct be_b0_line *line, char *storage,
		     unsigned long capacity);
void be_b0_line_text(struct be_b0_line *line, const char *text);
void be_b0_line_hex(struct be_b0_line *line, unsigned long value);
void be_b0_line_flag(struct be_b0_line *line, unsigned long value);

#endif
