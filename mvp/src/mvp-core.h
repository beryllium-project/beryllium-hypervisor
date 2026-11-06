/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP core profile (planning/mvp-m6-plan.md, D-1 to D-3): the
 *          generated inventory and proposal each image links (the
 *          scenario's mvp-config.c, the R1 input section), which hart 0
 *          copies, validates, seals, and derives through the ported R1
 *          mechanism at boot; their identity, the SHA-256 of their
 *          canonical bytes (Q6); the G-stage builder's inputs, each
 *          domain's window and the declared pages, from the derived roots
 *          alone (D-2); and, since M7, the domains the derived roots grant
 *          console input (planning/mvp-m7-plan.md, D-5).
 * Trust:   restricted C over the sealed state. No CSR, fence, or I/O.
 * Scope:   the MVP line from M6: two domains, one window each, and at most
 *          BE_MVP_PAGES_MAX pages of 4 KiB.
 */

#ifndef BE_MVP_CORE_H
#define BE_MVP_CORE_H

#include <be/manifest.h>

#include "mvp-gstage.h"
#include "mvp-sha256.h"

extern const struct be_platform_inventory be_mvp_inventory;
extern const struct be_proposal be_mvp_proposal;

/**
 * be_mvp_core_identity - the configuration's identity (Q6)
 * @inventory: a validated inventory
 * @proposal: a validated proposal
 * @identity: the SHA-256 of their canonical bytes
 *
 * The canonical bytes are each field below, in order, as eight
 * little-endian bytes, each array to its count only: the inventory's
 * version, architecture, profile, control hart, hart count, and resource
 * count, then each resource's identity, base, size, and kind; the
 * proposal's identity, vocabulary, and domain count, then each domain's
 * identity, vCPU, root, root resource, VMID, stack, saved-state identity,
 * saved-state resource, and hart; its resource count and each request's
 * resource, base, size, class, and owner; its authority count and each
 * authority's domain, GPA, resource, and rights; its channel count and
 * each channel's identity, source, target, resource, and both rights; and
 * the three published fields. tools/policy-check.py computes the same.
 */
void be_mvp_core_identity(const struct be_platform_inventory *inventory,
			  const struct be_proposal *proposal,
			  be_u8 identity[BE_MVP_SHA256_BYTES]);

/**
 * be_mvp_core_gstage - the G-stage builder's inputs from the derived roots
 * @canonical: the sealed canonical state
 * @enforcement: the roots derived from it, in domain order
 * @descs: each domain's window, root pool, VMID, and hart
 * @pages: the declared pages in GPA order
 * @count: how many
 *
 * Each root's one guest-code mapping gives its domain's window (the
 * mapping's GPA, its frame's base and size), its root-table frame the
 * pool, and the root its VMID and hart. Every other mapping is a page: a
 * channel's shared frame (kind channel, writer the channel's source,
 * reader its target) or a private frame (kind secret, read by its owner);
 * each domain's rights on a page are its mapping's, 0 without one.
 *
 * Return: 1, or 0 for roots that are not one window each and at most
 *         BE_MVP_PAGES_MAX 4 KiB pages, each at one GPA in every root.
 */
int be_mvp_core_gstage(const struct be_canonical_state *canonical,
		       const struct be_enforcement_state *enforcement,
		       struct be_mvp_gstage_desc *descs,
		       struct be_mvp_gstage_page *pages, be_u64 *count);

/**
 * be_mvp_core_console - the domains the derived roots grant console input
 * @enforcement: the roots derived from the sealed state, in domain order
 * @grants: bit d set when domain d's root grants it console input
 *
 * The grant is a configuration fact (planning/mvp-m7-plan.md, D-5), not
 * policy: the scenario's "console_input", carried by the generated
 * proposal through validation, the seal, and the derivation. The identity
 * above does not cover it (the configuration section of the authority
 * report is M7-4's).
 *
 * Return: 1, or 0 for roots that are not one per domain, each with a grant
 *         of 0 or 1, @grants then 0.
 */
int be_mvp_core_console(const struct be_enforcement_state *enforcement,
			be_u64 *grants);

/**
 * be_mvp_core_same - whether two objects hold the same bytes
 * @left: one object
 * @right: the other
 * @bytes: their size
 *
 * Hart 0 compares the builder's inputs from the derived roots with what
 * the image links, which the image checker matches to the scenario's
 * authority report; out of line, so that every linked object stays in
 * the image to be checked.
 *
 * Return: 1 if they do, else 0.
 */
int be_mvp_core_same(const void *left, const void *right, be_u64 bytes);

#endif
