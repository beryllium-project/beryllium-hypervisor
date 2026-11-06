#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Generate the MVP port from the accepted B2 port.

  port.py ROOT B2_PORT OUT           derive the MVP port into OUT
  port.py --check ROOT B2_PORT OUT   re-derive and require OUT to match exactly
  port.py --inputs                   print the ported paths (B2's)

The MVP line (planning/mvp-m0-plan.md, "Port and copies") reuses B2's K3
port of accepted R5 (B2 accepted at 898af4e0) unchanged except for B7's five
counted rules and seven substitutions (bringup/k3-b7/scripts/port.py), with
MVP names, and seven more rules: the hart region, and the six of the MVP
region (Plan revision M0-A.1). This script first runs B2's unchanged
bringup/k3-b2/scripts/port.py --check on B2_PORT, so B2_PORT must be B2's
byte-identical re-derivation from the pinned accepted inputs, and requires
B2's PORT-MANIFEST.txt to match its pinned SHA-256. It then copies every
file B2's manifest lists from B2_PORT to OUT and applies only these rules,
each with an exact count:

- r5-entry.S: `call be_r5_runtime_main` becomes `call be_mvp_runtime_main`
  (1) and `tail be_r5_arch_halt` becomes `tail be_r3_arch_halt` (1);
- r5-beryllium.lds: `be_r5_trap_vector` becomes `be_mvp_trap_vector` (3);
  PHDRS gains an `mvp_pool` PT_LOAD entry after `guest_protected` (1 block);
  a NOLOAD `.gstage.root.mvp` section at 0x1_0203_4000 (64 KiB, 16 KiB
  aligned: domain 0's 32 KiB pool, then domain 1's) follows the protected
  guest page, with its ASSERTs, before the accepted ASSERTs (1 block);
- the hart region (Q1): a NOLOAD `.hart.mvp` section at 0x1_0204_4000
  (128 KiB, 16 KiB aligned: one 64 KiB block per domain hart) follows the
  pool in the pool's read-write segment, with its ASSERTs, before the
  accepted ASSERTs (1 block);
- and the MVP region (M0-A.1): PHDRS gains `mvp_text` (R-X), `mvp_ro` (R),
  and `mvp_data` (RW) PT_LOAD entries after `mvp_pool` (1 block); the
  accepted `.monitor.text` input pattern `*(.text .text.*)` (1), the
  `.monitor.rodata` pattern `*(.rodata .rodata.*)` (1), the `.monitor.data`
  pattern `*(.data .data.*)` (1), and its `*(.bss .bss.*)` and `*(COMMON)`
  patterns (1 block) exclude the MVP layer's C objects (MVP_C_OBJECTS);
  and `.mvp.text`, `.mvp.rodata`, and `.mvp.data` (data, then BSS) at
  0x1_0206_4000, at most 256 KiB, 16 KiB aligned, holding exactly those
  objects' sections by explicit input patterns, follow the hart region
  with their ASSERTs, before the accepted ASSERTs (1 block). The assembly
  objects, mvp-trap.o (the vector the accepted R3 validation requires
  inside the accepted code extent) and mvp-hartentry.o, stay in
  `.monitor.text`. Each exclusion puts one EXCLUDE_FILE before each section
  pattern, the one form GNU ld and lld read alike: GNU ld applies an
  EXCLUDE_FILE inside the parentheses to the next pattern only, lld to
  every pattern up to the next EXCLUDE_FILE, and lld ignores the form
  before the file pattern.

M6 (planning/mvp-m6-plan.md, D-1 to D-4) adds the MVP core profile's
rules: manifest.h's limits (24 resources, 12 authorities, 8 mappings, 3
channels), the named harts and the VMID bound, the MVP core profile, the
inventory's and the canonical state's platform hart count, and each
domain's hart in its request, its binding, and its derived root;
manifest.c's validation of that profile (any number of monitor code and
data extents, guest-code windows with write, channels in either direction,
private pages read or read and write, VMIDs and harts distinct per
domain, guest-physical ranges disjoint per domain, counts bounded rather
than fixed); r3.c's boot check without the fixture extents the MVP's
linker script (src/mvp-monitor.lds, which the MVP links in place of the
port's r5-beryllium.lds) no longer places; and r5-entry.S's stack, hart
0's, by name. A Span rule replaces the text from its first line through
its last, pinned by that text's SHA-256.

M7 (planning/mvp-m7-plan.md, D-5) adds one configuration fact the same
way: each domain's console input grant, `console_input`, 0 or 1, in its
request, its binding, and its derived root; manifest.c refuses a request
or a canonical binding whose grant is neither, carries the grant into
the binding and the root, includes it in the canonical identity, and
requires each derived root's to be its binding's.

Every other byte, including every other accepted ASSERT and the management
fixture in its page, is B2's. --check re-derives the tree and requires OUT
to hold exactly those bytes, the same manifest, and no other file.
"""

import hashlib
import pathlib
import subprocess
import sys

ACCEPTED_B2 = "898af4e02fd36744a93b0eef99bc159955409d25"
B2_PORT_SCRIPT = "bringup/k3-b2/scripts/port.py"
# SHA-256 of B2's PORT-MANIFEST.txt, derived by B2's accepted port.py from
# the pinned accepted R5 inputs (bringup/k3-b2/README.md).
B2_MANIFEST_SHA256 = \
    "7c43e75b2066c86e01813143d2200be98a81f7dbd8773fad6c7785029b467878"
B2_PORTED_FILES = 32
ENTRY = "arch/riscv/be/r5-entry.S"
LDS = "arch/riscv/be/r5-beryllium.lds"

PHDR_ANCHOR = "\tguest_protected PT_LOAD FLAGS(5);\n"
POOL_PHDR = PHDR_ANCHOR + "\tmvp_pool PT_LOAD FLAGS(6);\n"
ASSERT_ANCHOR = "\tASSERT(be_reset == 0x102000000, \"R5 entry moved\")\n"
POOL_SECTION = (
    "\t/* MVP: the MVP-owned G-stage pool, domain 0's 32 KiB pool then\n"
    "\t * domain 1's, each a 16 KiB root and one level-1 page, the rest\n"
    "\t * zero; outside every accepted extent. */\n"
    "\t. = 0x102034000;\n"
    "\t.gstage.root.mvp (NOLOAD) : ALIGN(0x4000)\n"
    "\t{\n"
    "\t\t__be_mvp_pool_start = .; . += 0x10000;\n"
    "\t\t__be_mvp_pool_end = .;\n"
    "\t} :mvp_pool\n"
    "\n"
    "\tASSERT(__be_mvp_pool_start == 0x102034000 &&\n"
    "\t       __be_mvp_pool_end == 0x102044000, \"MVP G-stage pool moved\")\n"
    "\tASSERT((__be_mvp_pool_start & 0x3fff) == 0,\n"
    "\t       \"MVP G-stage pool alignment\")\n"
    "\tASSERT(__be_guest_protected_end <= __be_mvp_pool_start,\n"
    "\t       \"MVP G-stage pool overlaps the protected guest page\")\n"
    "\n")
HART_SECTION = (
    "\t/* MVP: the hart region, one 64 KiB block per domain hart (its\n"
    "\t * trusted stack, saved page, state page, and rings), written only\n"
    "\t * at run time; after the pool, in its read-write segment. */\n"
    "\t. = 0x102044000;\n"
    "\t.hart.mvp (NOLOAD) : ALIGN(0x4000)\n"
    "\t{\n"
    "\t\t__be_mvp_hart_region_start = .; . += 0x20000;\n"
    "\t\t__be_mvp_hart_region_end = .;\n"
    "\t} :mvp_pool\n"
    "\n"
    "\tASSERT(__be_mvp_hart_region_start == 0x102044000 &&\n"
    "\t       __be_mvp_hart_region_end == 0x102064000,\n"
    "\t       \"MVP hart region moved\")\n"
    "\tASSERT((__be_mvp_hart_region_start & 0x3fff) == 0,\n"
    "\t       \"MVP hart region alignment\")\n"
    "\tASSERT(__be_mvp_pool_end <= __be_mvp_hart_region_start,\n"
    "\t       \"MVP hart region overlaps the G-stage pool\")\n"
    "\n")

# The MVP region (Plan revision M0-A.1): the MVP layer's C objects. The
# assembly objects (mvp-trap.o, mvp-hartentry.o) stay in .monitor.text.
MVP_C_OBJECTS = ("mvp-runtime.o", "mvp-hartmain.o", "mvp-sbi.o",
                 "mvp-hart.o", "mvp-ring.o", "mvp-gstage.o", "mvp-payload.o",
                 "mvp-probe.o", "mvp-sha256.o")
REGION_PHDR_ANCHOR = "\tmvp_pool PT_LOAD FLAGS(6);\n"
REGION_PHDRS = (REGION_PHDR_ANCHOR + "\tmvp_text PT_LOAD FLAGS(5);\n"
                "\tmvp_ro PT_LOAD FLAGS(4);\n"
                "\tmvp_data PT_LOAD FLAGS(6);\n")
EXCLUDED = ("EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o\n"
            "\t\t\t       *mvp-hart.o *mvp-ring.o *mvp-gstage.o\n"
            "\t\t\t       *mvp-payload.o *mvp-probe.o *mvp-sha256.o)")
EXCLUDE_NOTE = (
    "\t\t/* MVP: not the MVP layer's C objects, which the MVP region\n"
    "\t\t * holds; one EXCLUDE_FILE before each section pattern, the\n"
    "\t\t * form GNU ld and lld read alike. */\n")


def excluding(patterns):
    """One input description: each pattern with the MVP C objects
    excluded."""
    return ("\t\t*(" + "\n\t\t  ".join(f"{EXCLUDED} {pattern}"
                                       for pattern in patterns) + ")\n")


TEXT_ANCHOR = "\t\t*(.text .text.*)\n"
TEXT_EXCLUDED = EXCLUDE_NOTE + excluding((".text", ".text.*"))
RODATA_ANCHOR = ("\t.monitor.rodata : ALIGN(16) { *(.rodata .rodata.*) } "
                 ":monitor_ro\n")
RODATA_EXCLUDED = ("\t.monitor.rodata : ALIGN(16)\n\t{\n" + EXCLUDE_NOTE +
                   excluding((".rodata", ".rodata.*")) +
                   "\t} :monitor_ro\n")
DATA_ANCHOR = "\t\t*(.data .data.*)\n"
DATA_EXCLUDED = EXCLUDE_NOTE + excluding((".data", ".data.*"))
BSS_ANCHOR = "\t\t*(.bss .bss.*)\n\t\t*(COMMON)\n"
BSS_EXCLUDED = excluding((".bss", ".bss.*")) + excluding(("COMMON",))


def objects(patterns):
    """Each MVP C object's sections of these patterns, one line each."""
    return "".join(f"\t\t*{name}({patterns})\n" for name in MVP_C_OBJECTS)


REGION_SECTION = (
    "\t/* MVP: the MVP region, after the hart region and outside every\n"
    "\t * accepted extent: the MVP layer's C objects' code, constants,\n"
    "\t * data, and BSS, named object by object. The flat image loads it;\n"
    "\t * hart 0 clears its BSS before it uses any of it. */\n"
    "\t. = 0x102064000;\n"
    "\t.mvp.text : ALIGN(0x4000)\n"
    "\t{\n"
    "\t\t__be_mvp_region_start = .;\n"
    "\t\t__be_mvp_text_start = .;\n" +
    objects(".text .text.*") +
    "\t\t. = ALIGN(16);\n"
    "\t\t__be_mvp_text_end = .;\n"
    "\t} :mvp_text\n"
    "\t.mvp.rodata : ALIGN(16)\n"
    "\t{\n" +
    objects(".rodata .rodata.*") +
    "\t} :mvp_ro\n"
    "\t.mvp.data : ALIGN(16)\n"
    "\t{\n" +
    objects(".data .data.*") +
    "\t\t. = ALIGN(8);\n"
    "\t\t__be_mvp_bss_start = .;\n" +
    objects(".bss .bss.* COMMON") +
    "\t\t. = ALIGN(8);\n"
    "\t\t__be_mvp_bss_end = .;\n"
    "\t\t__be_mvp_region_end = .;\n"
    "\t} :mvp_data\n"
    "\n"
    "\tASSERT(__be_mvp_region_start == 0x102064000 &&\n"
    "\t       __be_mvp_region_end <= 0x1020a4000,\n"
    "\t       \"MVP region moved or overflowed\")\n"
    "\tASSERT((__be_mvp_region_start & 0x3fff) == 0,\n"
    "\t       \"MVP region alignment\")\n"
    "\tASSERT(__be_mvp_hart_region_end <= __be_mvp_region_start,\n"
    "\t       \"MVP region overlaps the hart region\")\n"
    "\n")


class Span(tuple):
    """(first, last, sha256): the text from FIRST through the first LAST
    after it, which must have that SHA-256."""


# The MVP core profile (planning/mvp-m6-plan.md, D-1 and Q1).
MANIFEST_H = "include/be/manifest.h"
MANIFEST_C = "virt/be/manifest.c"
R3_C = "virt/be/r3.c"
NOTE = (" *          MVP port: the MVP core profile, by mvp/tools/port.py's\n"
        " *          counted rules (planning/mvp-m6-plan.md, D-1).\n")
LIMITS = ("#define BE_MAX_RESOURCES\t\t{}U\n#define BE_MAX_AUTHORITIES\t\t{}U\n"
          "#define BE_MAX_ROOTS\t\t\t2U\n#define BE_MAX_MAPPINGS\t\t\t{}U\n"
          "#define BE_MAX_SAVED_STATES\t\t2U\n#define BE_MAX_CHANNELS\t\t\t{}U\n")
HARTS = ("/* MVP: the control hart and each domain's, and each VMID's bound. */\n"
         "#define BE_MAX_HARTS\t\t\t3U\n#define BE_VMID_LIMIT\t\t\t16384U\n")


def field(rule, name, at, doc_at, doc):
    """Two rules: the struct field `be_u32 NAME;` and its kernel-doc line
    DOC, each inserted where AT and DOC_AT hold "|"."""
    return [(f"{rule}-doc", doc_at.replace("|", ""), doc_at.replace("|", doc),
             1),
            (rule, at.replace("|", ""), at.replace("|", f"\tbe_u32 {name};\n"),
             1)]


CHANNELS = """\
/* MVP: one channel: a nonzero identity and a frame no earlier channel
 * has, two distinct domains, its source's read and write and its
 * target's read, on a shared frame without an owner. */
static enum be_check_result
channel_result(const struct be_canonical_state *canonical, be_size index)
{
	const struct be_channel_desc *channel = &canonical->channels[index];
	const struct be_frame_desc *frame =
		find_frame(canonical, channel->frame_id);
	be_size other;

	if (channel->id == 0U || !domain_is_valid(channel->source) ||
	    !domain_is_valid(channel->target) ||
	    channel->source == channel->target ||
	    channel->source_rights != (BE_RIGHT_READ | BE_RIGHT_WRITE) ||
	    channel->target_rights != BE_RIGHT_READ)
		return BE_CHECK_CHANNEL_RIGHTS;
	if (frame == (const struct be_frame_desc *)0 ||
	    frame->class != BE_FRAME_SHARED || frame->owner_mask != 0U)
		return BE_CHECK_UNDECLARED_SHARED;
	for (other = 0U; other < index; ++other) {
		if (canonical->channels[other].id == channel->id ||
		    canonical->channels[other].frame_id == channel->frame_id)
			return BE_CHECK_UNDECLARED_SHARED;
	}
	return BE_CHECK_OK;
}

static enum be_check_result
canonicalize_channel(const struct be_proposal *proposal,
		     struct be_canonical_state *canonical)
{
	enum be_check_result result;
	be_size index;

	for (index = 0U; index < proposal->channel_count; ++index) {
		const struct be_channel_request *request =
			&proposal->channels[index];
		struct be_channel_desc *channel = &canonical->channels[index];

		channel->id = request->id;
		channel->source = request->source;
		channel->target = request->target;
		channel->frame_id = request->resource_id;
		channel->source_rights = request->source_rights;
		channel->target_rights = request->target_rights;
		result = channel_result(canonical, index);
		if (result != BE_CHECK_OK)
			return result;
	}
	canonical->channel_count = proposal->channel_count;
	return BE_CHECK_OK;
}
"""
AUTHORITIES = """\
/*
 * MVP: one authority's domain, page-aligned GPA range that does not wrap,
 * rights, and frame: its own private page, read or read and write; its
 * own guest-code frame, read and execute, with write for its RAM window;
 * or a declared channel's shared frame, with its end's rights.
 */
static enum be_check_result
authority_result(const struct be_canonical_state *canonical,
		 const struct be_authority_desc *authority,
		 const struct be_frame_desc *frame)
{
	const struct be_channel_desc *channel =
		find_channel(canonical, authority->frame_id);
	be_u32 rights = authority->rights;

	if (!domain_is_valid(authority->domain) ||
	    (authority->gpa & (BE_PAGE_SIZE - BE_U64_C(1))) != 0U ||
	    authority->gpa + frame->size < authority->gpa ||
	    !rights_are_valid(rights))
		return BE_CHECK_UNSUPPORTED;
	if (frame->class == BE_FRAME_PRIVATE ||
	    frame->class == BE_FRAME_GUEST_CODE) {
		if (frame->owner_mask != owner_mask_for(authority->domain))
			return BE_CHECK_PRIVATE_OWNER;
		if (frame->class == BE_FRAME_PRIVATE ?
		    (rights & BE_RIGHT_EXECUTE) != 0U :
		    (rights & (BE_RIGHT_READ | BE_RIGHT_EXECUTE)) !=
			    (BE_RIGHT_READ | BE_RIGHT_EXECUTE))
			return BE_CHECK_EXCESS_RIGHTS;
		return BE_CHECK_OK;
	}
	if (frame->class != BE_FRAME_SHARED)
		return BE_CHECK_EXCLUDED_MAPPING;
	if (channel == (const struct be_channel_desc *)0 ||
	    (authority->domain != channel->source &&
	     authority->domain != channel->target))
		return BE_CHECK_UNDECLARED_SHARED;
	if (rights != (authority->domain == channel->source ?
		       channel->source_rights : channel->target_rights))
		return BE_CHECK_CHANNEL_RIGHTS;
	return BE_CHECK_OK;
}

/* MVP: two authorities of one domain on one frame, or at overlapping
 * guest-physical ranges. */
static int authorities_collide(const struct be_canonical_state *canonical,
			       const struct be_authority_desc *left,
			       const struct be_authority_desc *right)
{
	const struct be_frame_desc *left_frame =
		find_frame(canonical, left->frame_id);
	const struct be_frame_desc *right_frame =
		find_frame(canonical, right->frame_id);

	if (left_frame == (const struct be_frame_desc *)0 ||
	    right_frame == (const struct be_frame_desc *)0)
		return 1;
	return left->domain == right->domain &&
	       (left->frame_id == right->frame_id ||
		(left->gpa < right->gpa + right_frame->size &&
		 right->gpa < left->gpa + left_frame->size));
}

static enum be_check_result
canonicalize_authorities(const struct be_proposal *proposal,
			 struct be_canonical_state *canonical)
{
	enum be_check_result result;
	be_size index;
	be_size other;

	for (index = 0U; index < proposal->authority_count; ++index) {
		const struct be_authority_request *request =
			&proposal->authorities[index];
		const struct be_frame_desc *frame =
			find_frame(canonical, request->resource_id);
		struct be_authority_desc *authority =
			&canonical->authorities[index];

		if (frame == (const struct be_frame_desc *)0)
			return BE_CHECK_INVENTORY_CLOSURE;
		authority->domain = request->domain;
		authority->gpa = request->gpa;
		authority->frame_id = request->resource_id;
		authority->rights = request->rights;
		result = authority_result(canonical, authority, frame);
		if (result != BE_CHECK_OK)
			return result;
		for (other = 0U; other < index; ++other) {
			if (authorities_collide(canonical,
						&canonical->authorities[other],
						authority))
				return BE_CHECK_UNDECLARED_MAPPING;
		}
	}
	canonical->authority_count = proposal->authority_count;
	sort_authorities(canonical);
	return BE_CHECK_OK;
}
"""
CHECK_CHANNELS = """\
static enum be_check_result
check_canonical_channel(const struct be_canonical_state *canonical)
{
	enum be_check_result result;
	be_size index;

	for (index = 0U; index < canonical->channel_count; ++index) {
		result = channel_result(canonical, index);
		if (result != BE_CHECK_OK)
			return result;
	}
	return BE_CHECK_OK;
}
"""
CHECK_AUTHORITIES = """\
static enum be_check_result
check_canonical_authorities(const struct be_canonical_state *canonical)
{
	be_size guest_code[BE_MAX_DOMAINS] = { 0U, 0U };
	be_size ends = 0U;
	be_size index;
	be_size other;

	/* MVP: each domain's one guest-code window, each channel's two ends,
	 * and any private pages, sorted and without collisions. */
	for (index = 0U; index < canonical->authority_count; ++index) {
		const struct be_authority_desc *authority =
			&canonical->authorities[index];
		const struct be_frame_desc *frame =
			find_frame(canonical, authority->frame_id);
		enum be_check_result result;

		if (frame == (const struct be_frame_desc *)0 ||
		    (index > 0U &&
		     !authority_before(&canonical->authorities[index - 1U],
				       authority)))
			return BE_CHECK_UNDECLARED_MAPPING;
		result = authority_result(canonical, authority, frame);
		if (result != BE_CHECK_OK)
			return result;
		for (other = 0U; other < index; ++other) {
			if (authorities_collide(canonical,
						&canonical->authorities[other],
						authority))
				return BE_CHECK_UNDECLARED_MAPPING;
		}
		if (frame->class == BE_FRAME_GUEST_CODE)
			++guest_code[authority->domain - BE_DOMAIN_MANAGEMENT];
		if (frame->class == BE_FRAME_SHARED)
			++ends;
	}
	if (guest_code[0] != 1U || guest_code[1] != 1U ||
	    ends != 2U * canonical->channel_count)
		return BE_CHECK_INCOMPLETE;
	return BE_CHECK_OK;
}
"""
FIND_CHANNEL = """\
/* MVP: the channel a shared frame backs, if any. */
static const struct be_channel_desc *
find_channel(const struct be_canonical_state *canonical, be_u32 frame_id)
{
	be_size index;

	for (index = 0U; index < canonical->channel_count; ++index) {
		if (canonical->channels[index].frame_id == frame_id)
			return &canonical->channels[index];
	}
	return (const struct be_channel_desc *)0;
}

"""
CORE_RULES = {
    MANIFEST_H: [
        ("note", " *          profile including guest-code resources.\n */\n",
         " *          profile including guest-code resources.\n" + NOTE +
         " */\n", 1),
        ("limits", LIMITS.format(13, 6, 6, 1),
         LIMITS.format(24, 12, 8, 3) + HARTS, 1),
        ("profile-doc", " * @BE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN: "
         "accepted fixed R1 profile\n", " * @BE_PROFILE_FIXED_SINGLE_HART_"
         "TWO_DOMAIN: accepted fixed R1 profile\n * @BE_PROFILE_MVP_CORE: "
         "the MVP core profile (MVP port)\n", 1),
        ("profile", "\tBE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN,\n",
         "\tBE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN,\n"
         "\tBE_PROFILE_MVP_CORE,\n", 1)] +
    field("inventory-harts", "hart_count", "\tbe_u32 hart_id;\n|\tbe_size "
          "resource_count;\n", " * @hart_id: sole active hart identifier\n|"
          " * @resource_count:", " * @hart_count: the platform's harts (MVP "
          "core profile)\n") +
    field("request-hart", "hart_id", "\tbe_u32 saved_state_resource_id;\n|};",
          " * @saved_state_resource_id: requested saved-state storage "
          "resource\n|", " * @hart_id: requested domain hart (MVP core "
          "profile)\n") +
    field("binding-hart", "hart_id", "\tbe_u32 saved_state_frame;\n|};",
          " * @saved_state_frame: monitor-owned saved-state frame identity\n|",
          " * @hart_id: domain hart (MVP core profile)\n") +
    field("canonical-harts", "hart_count", "\tbe_u32 hart_id;\n|\tbe_u64 "
          "configuration_id;\n", " * @hart_id: sole active hart identifier\n|"
          " * @configuration_id:", " * @hart_count: the platform's harts (MVP "
          "core profile)\n") +
    field("root-hart", "hart_id", "\tbe_u32 saved_state_frame;\n|\tbe_size "
          "mapping_count;\n", " * @saved_state_frame: bound saved-state frame "
          "identity\n|", " * @hart_id: bound domain hart (MVP core "
          "profile)\n") +
    # M7 (planning/mvp-m7-plan.md, D-5): the console input grant.
    field("request-console", "console_input", "\tbe_u32 saved_state_"
          "resource_id;\n\tbe_u32 hart_id;\n|};", " * @hart_id: requested "
          "domain hart (MVP core profile)\n|", " * @console_input: requested "
          "console input grant, 0 or 1 (MVP, M7)\n") +
    field("binding-console", "console_input", "\tbe_u32 saved_state_frame;\n"
          "\tbe_u32 hart_id;\n|};", " * @hart_id: domain hart (MVP core "
          "profile)\n|", " * @console_input: console input grant, 0 or 1 "
          "(MVP, M7)\n") +
    field("root-console", "console_input", "\tbe_u32 hart_id;\n|\tbe_size "
          "mapping_count;\n", " * @hart_id: bound domain hart (MVP core "
          "profile)\n|", " * @console_input: bound console input grant (MVP, "
          "M7)\n"),
    MANIFEST_C: [
        ("note", " *          abstract roots and mappings, not Sv39x4 tables or "
         "privileged state.\n */\n", " *          abstract roots and mappings, "
         "not Sv39x4 tables or privileged state.\n" + NOTE + " */\n", 1),
        ("rights", "\tif ((rights & BE_RIGHT_WRITE) != 0U &&\n\t    (rights & "
         "BE_RIGHT_EXECUTE) != 0U)\n\t\treturn 0;\n", "\t/* MVP: write with "
         "execute on a guest-code frame alone (authority_result()). */\n", 1),
        ("find-channel", "static const struct be_root_image *\nfind_root(",
         FIND_CHANNEL + "static const struct be_root_image *\nfind_root(", 1),
        ("profile", "profile != BE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN ||",
         "profile != BE_PROFILE_MVP_CORE ||", 2),
        ("inventory-harts", "\t    inventory->hart_id != BE_CONFIGURATION_HART_"
         "ID)\n\t\treturn BE_CHECK_UNSUPPORTED;\n\tif (inventory->resource_"
         "count != BE_MAX_RESOURCES)\n", "\t    inventory->hart_id != BE_"
         "CONFIGURATION_HART_ID ||\n\t    inventory->hart_count < BE_MAX_HARTS)"
         "\n\t\treturn BE_CHECK_UNSUPPORTED;\n\tif (inventory->resource_count "
         "== 0U ||\n\t    inventory->resource_count > BE_MAX_RESOURCES)\n", 1),
        ("monitor-extents", "\tif (monitor_code != 1U || monitor_data != 1U "
         "||\n", "\tif (monitor_code == 0U || monitor_data == 0U ||\n", 2),
        ("assignable", " || assignable != 3U ||\n", " ||\n\t    assignable > "
         "BE_MAX_CHANNELS + BE_MAX_DOMAINS ||\n", 1),
        ("domain-binding", "\t\t    request->root_resource_id == 0U || "
         "request->vmid != 0U ||\n", "\t\t    request->root_resource_id == 0U "
         "|| request->vmid == 0U ||\n\t\t    request->vmid >= BE_VMID_LIMIT ||"
         "\n\t\t    request->hart_id == inventory->hart_id ||\n", 1),
        ("domain-hart", "\t\t\trequest->saved_state_resource_id;\n\t\tsaved->",
         "\t\t\trequest->saved_state_resource_id;\n\t\tdomain->hart_id = "
         "request->hart_id;\n\t\tsaved->", 1),
        ("domains-distinct", "\t\t\tif (left->vcpu_id == right->vcpu_id ||\n",
         "\t\t\tif (left->vcpu_id == right->vcpu_id ||\n\t\t\t    left->vmid "
         "== right->vmid ||\n\t\t\t    left->hart_id == right->hart_id ||\n",
         1),
        ("channels", Span(("static enum be_check_result\ncanonicalize_channel(",
                           "\tcanonical->channel_count = BE_MAX_CHANNELS;\n\t"
                           "return BE_CHECK_OK;\n}\n", "4cb501dfe0adf8a74f54754f"
                           "c1b073753f09a1247bc09736814f26d74b3741ea")),
         CHANNELS, 1),
        ("authorities", Span(("static enum be_check_result\ncanonicalize_"
                              "authorities(", "\tsort_authorities(canonical);"
                              "\n\treturn BE_CHECK_OK;\n}\n", "10a4be1eab37419ef"
                              "6395bbf5591597b091874590007147484ed60bb204962b4"
                              )), AUTHORITIES, 1),
        ("counts", "\t    proposal->authority_count != BE_MAX_AUTHORITIES ||\n"
         "\t    proposal->channel_count != BE_MAX_CHANNELS)\n", "\t    proposal"
         "->authority_count == 0U ||\n\t    proposal->authority_count > BE_MAX_"
         "AUTHORITIES ||\n\t    proposal->channel_count > BE_MAX_CHANNELS)\n",
         1),
        ("canonical-harts", "\tcandidate.hart_id = inventory->hart_id;\n",
         "\tcandidate.hart_id = inventory->hart_id;\n\tcandidate.hart_count = "
         "inventory->hart_count;\n", 1),
        ("assignable-frames", "\t    private_frame != BE_MAX_DOMAINS || "
         "shared != BE_MAX_CHANNELS ||\n", "\t    private_frame > BE_MAX_DOMAINS"
         " ||\n\t    shared != canonical->channel_count ||\n", 1),
        ("canonical-binding", "\t\t    domain->vmid != 0U)\n", "\t\t    domain->"
         "vmid == 0U || domain->vmid >= BE_VMID_LIMIT ||\n\t\t    domain->"
         "hart_id == canonical->hart_id)\n", 1),
        ("canonical-distinct", "\t\t\tif (domain->vcpu_id == candidate->vcpu_id "
         "||\n", "\t\t\tif (domain->vcpu_id == candidate->vcpu_id ||\n\t\t\t    "
         "domain->vmid == candidate->vmid ||\n\t\t\t    domain->hart_id == "
         "candidate->hart_id ||\n", 1),
        ("check-channels", Span(("static enum be_check_result\ncheck_canonical_"
                                 "channel(", "\t    backing->owner_mask != 0U)\n"
                                 "\t\treturn BE_CHECK_UNDECLARED_SHARED;\n\t"
                                 "return BE_CHECK_OK;\n}\n", "e0052e9905638334df"
                                 "103533331193e6bd80dede59271c75cb68413b54464f64"
                                 )), CHECK_CHANNELS, 1),
        ("check-authorities", Span(("static enum be_check_result\ncheck_"
                                    "canonical_authorities(", "\t    protected_"
                                    "shared != 1U || protected_guest_code != 1U)"
                                    "\n\t\treturn BE_CHECK_INCOMPLETE;\n\treturn "
                                    "BE_CHECK_OK;\n}\n", "504f015bf4d89b052404f4"
                                    "b4e758ab63f3b9ba3f8f6ca9a1995a0c198470ad05"
                                    )), CHECK_AUTHORITIES, 1),
        ("canonical-counts", "\t    canonical->hart_id != BE_CONFIGURATION_HART_"
         "ID)\n\t\treturn BE_CHECK_UNSUPPORTED;\n\tif (canonical->domain_count "
         "!= BE_MAX_DOMAINS ||\n\t    canonical->frame_count != BE_MAX_RESOURCES"
         " ||\n\t    canonical->authority_count != BE_MAX_AUTHORITIES ||\n", "\t "
         "   canonical->hart_id != BE_CONFIGURATION_HART_ID ||\n\t    canonical->"
         "hart_count < BE_MAX_HARTS)\n\t\treturn BE_CHECK_UNSUPPORTED;\n\tif ("
         "canonical->domain_count != BE_MAX_DOMAINS ||\n\t    canonical->frame_"
         "count == 0U ||\n\t    canonical->frame_count > BE_MAX_RESOURCES ||\n\t"
         "    canonical->authority_count == 0U ||\n\t    canonical->authority_"
         "count > BE_MAX_AUTHORITIES ||\n", 1),
        ("canonical-channels", "\t    canonical->channel_count != BE_MAX_"
         "CHANNELS)\n\t\treturn BE_CHECK_INCOMPLETE;\n\n", "\t    canonical->"
         "channel_count > BE_MAX_CHANNELS)\n\t\treturn BE_CHECK_INCOMPLETE;\n\n",
         1),
        ("identity-harts", "\tidentity = identity_u64(identity, canonical->"
         "hart_id);\n", "\tidentity = identity_u64(identity, canonical->"
         "hart_id);\n\tidentity = identity_u64(identity, canonical->"
         "hart_count);\n", 1),
        ("identity-hart", "\t\t\t\t\t domain->saved_state_frame);\n\t}\n",
         "\t\t\t\t\t domain->saved_state_frame);\n\t\tidentity = identity_u64("
         "identity, domain->hart_id);\n\t}\n", 1),
        ("derive-hart", "\t\troot->vmid = domain->vmid;\n", "\t\troot->vmid = "
         "domain->vmid;\n\t\troot->hart_id = domain->hart_id;\n", 1),
        ("root-hart", "\t\t    root->vmid != domain->vmid ||\n", "\t\t    root->"
         "vmid != domain->vmid ||\n\t\t    root->hart_id != domain->hart_id ||"
         "\n", 1),
        ("mappings", "\t\tif (root->mapping_count != 3U ||\n", "\t\tif (root->"
         "mapping_count == 0U ||\n", 1),
        ("profile-name", "\treturn profile == BE_PROFILE_FIXED_SINGLE_HART_TWO_"
         "DOMAIN ?\n", "\tif (profile == BE_PROFILE_MVP_CORE)\n\t\treturn "
         "\"mvp-core\";\n\treturn profile == BE_PROFILE_FIXED_SINGLE_HART_TWO_"
         "DOMAIN ?\n", 1),
        # M7 (planning/mvp-m7-plan.md, D-5): the console input grant.
        ("request-console", "\t\t    request->hart_id == inventory->hart_id "
         "||\n", "\t\t    request->hart_id == inventory->hart_id ||\n\t\t"
         "    request->console_input > 1U ||\n", 1),
        ("domain-console", "\t\tdomain->hart_id = request->hart_id;\n",
         "\t\tdomain->hart_id = request->hart_id;\n\t\tdomain->console_input "
         "= request->console_input;\n", 1),
        ("canonical-console", "\t\t    domain->hart_id == canonical->hart_id)"
         "\n", "\t\t    domain->hart_id == canonical->hart_id ||\n\t\t    "
         "domain->console_input > 1U)\n", 1),
        ("identity-console", "\t\tidentity = identity_u64(identity, domain->"
         "hart_id);\n", "\t\tidentity = identity_u64(identity, domain->"
         "hart_id);\n\t\tidentity = identity_u64(identity, domain->"
         "console_input);\n", 1),
        ("derive-console", "\t\troot->hart_id = domain->hart_id;\n", "\t\t"
         "root->hart_id = domain->hart_id;\n\t\troot->console_input = "
         "domain->console_input;\n", 1),
        ("root-console", "\t\t    root->hart_id != domain->hart_id ||\n",
         "\t\t    root->hart_id != domain->hart_id ||\n\t\t    root->"
         "console_input != domain->console_input ||\n", 1),
    ],
    R3_C: [
        ("fixture-extents", Span(("\t    layout->diagnostic_end != BE_R3_"
                                  "DIAGNOSTIC_END ||\n", "\t     (BE_R0_SV39X4_"
                                  "ROOT_ALIGN - 1U)) != 0U)\n\t\treturn 0;\n",
                                  "7e6c3b4ccc78656aaad11859bbb83af03d728c317427"
                                  "d2a59beb81726040dff6")),
         "\t    layout->diagnostic_end != BE_R3_DIAGNOSTIC_END)\n\t\treturn 0;\n"
         "\t/* MVP: no fixture root, stack, saved, private, shared, or guest\n"
         "\t * page (planning/mvp-m6-plan.md, D-3 and D-4). */\n", 1),
    ],
}

# path -> [(rule, old, new, count)], applied in order to B2's ported text.
RULES = {
    ENTRY: [
        ("runtime", "\tcall\tbe_r5_runtime_main\n",
         "\tcall\tbe_mvp_runtime_main\n", 1),
        ("halt", "\ttail\tbe_r5_arch_halt\n", "\ttail\tbe_r3_arch_halt\n", 1),
        ("control-stack", "\tla\tsp, __be_stack_management_end\n",
         "\tla\tsp, __be_control_stack_end\n", 1),
    ],
    LDS: [
        ("trap-vector", "be_r5_trap_vector", "be_mvp_trap_vector", 3),
        ("pool-phdr", PHDR_ANCHOR, POOL_PHDR, 1),
        ("pool-section", ASSERT_ANCHOR, POOL_SECTION + ASSERT_ANCHOR, 1),
        ("hart-region", ASSERT_ANCHOR, HART_SECTION + ASSERT_ANCHOR, 1),
        ("region-phdrs", REGION_PHDR_ANCHOR, REGION_PHDRS, 1),
        ("region-text-exclude", TEXT_ANCHOR, TEXT_EXCLUDED, 1),
        ("region-rodata-exclude", RODATA_ANCHOR, RODATA_EXCLUDED, 1),
        ("region-data-exclude", DATA_ANCHOR, DATA_EXCLUDED, 1),
        ("region-bss-exclude", BSS_ANCHOR, BSS_EXCLUDED, 1),
        ("mvp-region", ASSERT_ANCHOR, REGION_SECTION + ASSERT_ANCHOR, 1),
    ],
    **CORE_RULES,
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def b2_listing(root, b2_port):
    """Check B2's port with B2's own script; return its manifest entries."""
    check = subprocess.run(
        [sys.executable, "-B", str(root / B2_PORT_SCRIPT), "--check",
         str(root), str(b2_port)],
        capture_output=True, text=True, check=False)
    if check.returncode != 0 or not check.stdout.startswith(
            "BE_B2_PORT: CHECK PASS "):
        raise ValueError("B2 port.py --check failed: "
                         f"{(check.stdout + check.stderr).strip()}")
    manifest = (b2_port / "PORT-MANIFEST.txt").read_bytes()
    if sha256(manifest) != B2_MANIFEST_SHA256:
        raise ValueError("B2 PORT-MANIFEST.txt differs from the pinned "
                         f"SHA-256 (sha256 {sha256(manifest)})")
    entries = []
    for line in manifest.decode("utf-8").splitlines():
        if line.startswith("#"):
            continue
        _, output_sha256, path = line.split(" ")
        entries.append((path, output_sha256))
    if len(entries) != B2_PORTED_FILES:
        raise ValueError(f"B2 manifest lists {len(entries)} files, "
                         f"expected {B2_PORTED_FILES}")
    return entries


def derive(root, b2_port):
    """Return [(path, B2 sha256, MVP text, report lines)] or raise."""
    entries = b2_listing(root, b2_port)
    paths = [path for path, _ in entries]
    unknown = sorted(set(RULES) - set(paths))
    if unknown:
        raise ValueError(f"rules for paths outside B2's port: {unknown}")
    ported = []
    for path, b2_sha256 in entries:
        data = (b2_port / path).read_bytes()
        if sha256(data) != b2_sha256:
            raise ValueError(f"{path}: B2 port file differs from its manifest")
        text = data.decode("utf-8")
        report = []
        for rule, old, new, count in RULES.get(path, []):
            if isinstance(old, Span):
                first, last, digest = old
                start = text.find(first)
                end = text.find(last, start) + len(last)
                old = text[start:end] if start >= 0 and end >= len(last) \
                    else first
                if sha256(old.encode("utf-8")) != digest:
                    raise ValueError(f"{path}: rule {rule}: the span from "
                                     f"{first!r} is not the pinned text")
            found = text.count(old)
            if found != count:
                raise ValueError(f"{path}: rule {rule}: {old!r} found "
                                 f"{found} times, expected {count}")
            text = text.replace(old, new)
            report.append(f"rule {rule} x{count}")
        ported.append((path, b2_sha256, text, report))
    return ported


def main(argv):
    if len(argv) == 2 and argv[1] == "--inputs":
        # The MVP ports exactly the files B2 ports, so B2's list is its.
        root = pathlib.Path(__file__).resolve().parents[2]
        return subprocess.run([sys.executable, "-B",
                               str(root / B2_PORT_SCRIPT), "--inputs"],
                              check=False).returncode
    check = len(argv) == 5 and argv[1] == "--check"
    if not check and len(argv) != 4:
        print(__doc__)
        return 2
    root, b2_port, out = (pathlib.Path(argument) for argument in argv[-3:])
    try:
        ported = derive(root.resolve(), b2_port.resolve())
    except (OSError, ValueError, UnicodeDecodeError) as error:
        print(f"BE_MVP_PORT: FAIL {error}")
        return 1
    manifest = [f"# MVP port of accepted B2 {ACCEPTED_B2} "
                f"(B2 manifest sha256 {B2_MANIFEST_SHA256})",
                "# b2-port-sha256 mvp-port-sha256 path"]
    for path, b2_sha256, text, report in ported:
        target = out / path
        data = text.encode("utf-8")
        if check:
            if not target.is_file() or target.read_bytes() != data:
                print(f"BE_MVP_PORT: FAIL {path} differs from a fresh "
                      "derivation")
                return 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest.append(f"{b2_sha256} {sha256(data)} {path}")
        for line in report:
            manifest.append(f"#   {path}: {line}")
    manifest_text = "\n".join(manifest) + "\n"
    manifest_path = out / "PORT-MANIFEST.txt"
    if check:
        expected = {out / path for path, _, _, _ in ported} | {manifest_path}
        present = {path for path in out.rglob("*") if path.is_file()}
        if present != expected:
            extra = sorted(str(path.relative_to(out))
                           for path in present ^ expected)
            print(f"BE_MVP_PORT: FAIL unexpected or missing files: {extra}")
            return 1
        if manifest_path.read_text() != manifest_text:
            print("BE_MVP_PORT: FAIL manifest differs")
            return 1
    else:
        manifest_path.write_text(manifest_text)
    rules = sum(len(RULES[path]) for path in RULES)
    applied = sum(count for path in RULES for _, _, _, count in RULES[path])
    changed = sum(1 for _, _, _, report in ported if report)
    print(f"BE_MVP_PORT: {'CHECK ' if check else ''}PASS files={len(ported)} "
          f"changed={changed} rules={rules} substitutions={applied} "
          f"b2_manifest={B2_MANIFEST_SHA256[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
