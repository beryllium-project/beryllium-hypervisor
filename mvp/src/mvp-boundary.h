/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the physical boundary's monitor side in step 1
 *          (planning/mvp-m11-plan.md, D-3 "Pairing", D-6, D-8, D-12): the
 *          firmware's domain commit extension (EID 0x08004246; function 0
 *          confine, function 1 one word of the configuration identity),
 *          hart 0's verdict on the extension's probe and on the identity
 *          it reads against the image's own, the two-hart census of a
 *          boundary-on image, and the offset of a VS domain's state word,
 *          which the harness reads at the end of a run.
 * Trust:   restricted C with no CSR, fence, SBI call, or I/O; every input
 *          is checked, and a null pointer, a zero probe, a read error, or a
 *          word that differs is the boundary class.
 * Scope:   built into every monitor (mvp-hart.c), used by a boundary-on
 *          image alone (BE_MVP_BOUNDARY, mvp/Makefile's MVP_BOUNDARY); no
 *          proved leaf includes it.
 */

#ifndef BE_MVP_BOUNDARY_H
#define BE_MVP_BOUNDARY_H

#include <be/types.h>

#include "mvp.h"
#include "mvp-sbi.h"

/* The firmware's domain commit extension (mvp/firmware/patches/0007). */
#define BE_MVP_BOUNDARY_EID		BE_MVP_C(0x08004246)
#define BE_MVP_BOUNDARY_FID_CONFINE	BE_MVP_C(0)
#define BE_MVP_BOUNDARY_FID_IDENTITY	BE_MVP_C(1)
/* The configuration identity: four 64-bit words, most significant first,
 * the descriptor's 32 bytes in order. */
#define BE_MVP_BOUNDARY_IDENTITY_WORDS	BE_MVP_C(4)
#define BE_MVP_BOUNDARY_IDENTITY_BYTES	BE_MVP_C(32)

/*
 * A VS domain's state word (planning/mvp-m11-plan.md, D-10): the 64-bit
 * word at this offset in its block's state page holds the hart's phase
 * and, above it, its failure class; tests/check-boundary.py reads these
 * three values from here, and mvp-hart.c ties them to the C structure.
 */
#define BE_MVP_BOUNDARY_PHASE_OFFSET	BE_MVP_C(0xa0)
#define BE_MVP_BOUNDARY_PHASE_FAILED	BE_MVP_C(2)
#define BE_MVP_BOUNDARY_CLASS_RING	BE_MVP_C(22)

/**
 * be_mvp_boundary_word - one word of an identity, as the firmware gives it
 * @identity: the identity, %BE_MVP_BOUNDARY_IDENTITY_BYTES bytes
 * @index: the word, 0 to 3
 *
 * Return: bytes 8 * @index to 8 * @index + 7 of @identity, the first the
 * most significant; 0 for a null @identity or an @index beyond the last.
 */
be_u64 be_mvp_boundary_word(const be_u8 *identity, be_u64 index);

/**
 * be_mvp_boundary_bytes - an identity's bytes from its four words
 * @words: the words, %BE_MVP_BOUNDARY_IDENTITY_WORDS of them
 * @bytes: the bytes, %BE_MVP_BOUNDARY_IDENTITY_BYTES of them
 *
 * The inverse of be_mvp_boundary_word(). A null pointer writes nothing.
 */
void be_mvp_boundary_bytes(const be_u64 *words, be_u8 *bytes);

/**
 * be_mvp_boundary_check - hart 0's verdict on the extension and identity
 * @probe: the extension's probe value: 0 when the firmware lacks it
 * @errors: each identity read's SBI error, %BE_MVP_BOUNDARY_IDENTITY_WORDS
 * @words: each identity read's value, %BE_MVP_BOUNDARY_IDENTITY_WORDS
 * @identity: the image's own identity, %BE_MVP_BOUNDARY_IDENTITY_BYTES
 * @failed: the word that failed: the first read error, or else the first
 *          word that differs; 0 for a zero @probe;
 *          %BE_MVP_BOUNDARY_IDENTITY_WORDS when every word equals
 *
 * Every read's error is judged before any word is compared, so a word
 * that differs is reported only when the whole identity was read.
 *
 * Return: %BE_MVP_CLASS_NONE when @probe is nonzero and every word read
 * without an error and equals the image's identity, else
 * %BE_MVP_CLASS_BOUNDARY, as for any null pointer.
 */
enum be_mvp_class be_mvp_boundary_check(be_u64 probe, const long *errors,
					const be_u64 *words,
					const be_u8 *identity, be_u64 *failed);

/**
 * be_mvp_boundary_census - the census rule of a boundary-on image
 * @census: hart 0's census over the layout's VS-domain harts, 1 and 2
 *
 * A boundary-on image has no start rule (the tree restricts the cold boot
 * to hart 0), so no hart may be STARTED.
 *
 * Return: 1 when the census holds and found no STARTED hart, else 0.
 */
int be_mvp_boundary_census(const struct be_mvp_hsm_census *census);

/* The confining stub (mvp-hartentry.S), in a boundary-on image alone. */
extern be_u8 be_mvp_confine_entry[];

#endif
