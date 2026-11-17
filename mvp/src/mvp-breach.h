/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the hostile-monitor test hook of the breach images (M11-7;
 *          planning/mvp-m11-plan.md, D-10's VS-domain column; M11-8, its
 *          control-hart column): the attempt table's row, the translation
 *          modes, the record the hook keeps (a VS-domain hart's in its own
 *          hart mailbox, the control hart's in its control tail), and the
 *          words hart 0 fills before the barrier, which tools/gen-breach.py
 *          writes and reads.
 * Trust:   test code. Only the breach images (BE_MVP_BREACH, with
 *          BE_MVP_BREACH_DOMAIN or BE_MVP_BREACH_CONTROL) link the hook
 *          (mvp-breach.c, mvp-breach-arch.S); a scenario image includes no
 *          part of it. The table is generated before the link from
 *          scenarios/anchor/breach.json or breach-control.json
 *          (mvp-breach-table.h) and decoded again after it by
 *          tests/check-image.py.
 * Scope:   anchor's breach-g0, breach-g1, and breach-c and their -off
 *          copies (BE_MVP_BREACH_DISCRIMINATE, which run every attempt
 *          that has a witness, with no boundary).
 */

#ifndef BE_MVP_BREACH_H
#define BE_MVP_BREACH_H

#include "mvp-layout.h"

/* An attempt's operation (the row's kind, bits 16 to 23). */
#define BE_MVP_BREACH_OP_LOAD		BE_MVP_C(1)
#define BE_MVP_BREACH_OP_STORE		BE_MVP_C(2)
#define BE_MVP_BREACH_OP_JUMP		BE_MVP_C(3)
#define BE_MVP_BREACH_OP_AMOADD		BE_MVP_C(4)
#define BE_MVP_BREACH_OP_LRSC		BE_MVP_C(5)
#define BE_MVP_BREACH_OP_CBO_ZERO	BE_MVP_C(6)
#define BE_MVP_BREACH_OP_CBO_INVAL	BE_MVP_C(7)
#define BE_MVP_BREACH_OP_HLV		BE_MVP_C(8)
#define BE_MVP_BREACH_OP_HSV		BE_MVP_C(9)
#define BE_MVP_BREACH_OP_ECALL		BE_MVP_C(10)

/*
 * The translation an attempt runs under (the row's kind, bits 8 to 15),
 * an index into be_mvp_breach_modes: satp, hgatp, and vsatp, each
 * BE_MVP_BREACH_KEEP for the value the hook saved at its entry.
 */
#define BE_MVP_BREACH_MODE_BARE		BE_MVP_C(0)
#define BE_MVP_BREACH_MODE_SATP		BE_MVP_C(1)
#define BE_MVP_BREACH_MODE_GSTAGE_OWN	BE_MVP_C(2)
#define BE_MVP_BREACH_MODE_GSTAGE_OTHER	BE_MVP_C(3)
#define BE_MVP_BREACH_MODE_VS_FORGED	BE_MVP_C(4)
#define BE_MVP_BREACH_MODES		BE_MVP_C(5)
#define BE_MVP_BREACH_KEEP		BE_MVP_C(0xffffffffffffffff)

/* A row: kind, then the address (an ecall's a0), the value (a store's,
 * an AMO's addend, or an ecall's a1), extra (an ecall's a2), and call (an
 * ecall's EID << 32 | FID). kind is row << 32 | op << 16 | mode << 8 |
 * width. */
#define BE_MVP_BREACH_ROW_KIND		BE_MVP_C(0)
#define BE_MVP_BREACH_ROW_ADDRESS	BE_MVP_C(8)
#define BE_MVP_BREACH_ROW_VALUE		BE_MVP_C(16)
#define BE_MVP_BREACH_ROW_EXTRA		BE_MVP_C(24)
#define BE_MVP_BREACH_ROW_CALL		BE_MVP_C(32)
#define BE_MVP_BREACH_ROW_BYTES		BE_MVP_C(40)

/*
 * The record, in the hooked hart's own mailbox past the bytes its rings
 * use: a 128-byte header, whose words 4 to 8 are the frame the hook's
 * vector reads through sscratch, then one 32-byte slot per row. Then the
 * control rows' block and words, the hook's own Sv39 root, and its forged
 * Sv39x4 root.
 */
#define BE_MVP_BREACH_RECORD_OFFSET	BE_MVP_C(0x8100)
#define BE_MVP_BREACH_HEADER_BYTES	BE_MVP_C(0x80)
#define BE_MVP_BREACH_SLOT_BYTES	BE_MVP_C(32)
#define BE_MVP_BREACH_SLOTS		BE_MVP_C(112)
#define BE_MVP_BREACH_CONTROL_OFFSET	BE_MVP_C(0x8f80)
#define BE_MVP_BREACH_SV39_OFFSET	BE_MVP_C(0x9000)
#define BE_MVP_BREACH_SV39X4_OFFSET	BE_MVP_C(0xc000)
#define BE_MVP_BREACH_MAGIC		BE_MVP_C(0x4843414552424542)
#define BE_MVP_BREACH_STATE_CLEAR	BE_MVP_C(0)
#define BE_MVP_BREACH_STATE_RUNNING	BE_MVP_C(1)
#define BE_MVP_BREACH_STATE_DONE	BE_MVP_C(2)
#define BE_MVP_BREACH_STATE_AGAIN	BE_MVP_C(3)
/* The frame, from the record's start, and its words from the frame. */
#define BE_MVP_BREACH_FRAME_OFFSET	BE_MVP_C(32)
#define BE_MVP_BREACH_FRAME_SLOT	BE_MVP_C(0)
#define BE_MVP_BREACH_FRAME_CONTINUE	BE_MVP_C(8)
#define BE_MVP_BREACH_FRAME_CAUSE	BE_MVP_C(16)
#define BE_MVP_BREACH_FRAME_SEPC	BE_MVP_C(24)
#define BE_MVP_BREACH_FRAME_STVAL	BE_MVP_C(32)
/* A slot's words: what the hook's vector saw, and what the attempt kept. */
#define BE_MVP_BREACH_SLOT_CAUSE	BE_MVP_C(0)
#define BE_MVP_BREACH_SLOT_STVAL	BE_MVP_C(8)
#define BE_MVP_BREACH_SLOT_VALUE	BE_MVP_C(16)
#define BE_MVP_BREACH_SLOT_ERROR	BE_MVP_C(24)
#define BE_MVP_BREACH_NO_TRAP		BE_MVP_C(0xffffffffffffffff)
#define BE_MVP_BREACH_SENTINEL		BE_MVP_C(0x5eb55eb55eb55eb5)
/* The saved registers, in their order. */
#define BE_MVP_BREACH_SAVED_STVEC	BE_MVP_C(0)
#define BE_MVP_BREACH_SAVED_SSCRATCH	BE_MVP_C(8)
#define BE_MVP_BREACH_SAVED_SEPC	BE_MVP_C(16)
#define BE_MVP_BREACH_SAVED_SSTATUS	BE_MVP_C(24)
#define BE_MVP_BREACH_SAVED_HSTATUS	BE_MVP_C(32)
#define BE_MVP_BREACH_SAVED_SATP	BE_MVP_C(40)
#define BE_MVP_BREACH_SAVED_HGATP	BE_MVP_C(48)
#define BE_MVP_BREACH_SAVED_VSATP	BE_MVP_C(56)

/*
 * The fill: a known word for each place the attempts change, hart 0's
 * (the hooked VS domain's control mailbox, before the barrier) and the
 * hook's own (its control rows'), BE_MVP_BREACH_FILL with the word's
 * offset in its mailbox in the low bits. Hart 0 also writes a forged Sv39
 * VS-stage root, one gigapage at VA 0 to GPA 0xc000_0000, into the
 * control tail page (the VS-stage rows).
 */
#define BE_MVP_BREACH_FILL		BE_MVP_C(0xb5eaf11100000000)
#define BE_MVP_BREACH_FILL_BLOCK	BE_MVP_C(0x3f80)
#define BE_MVP_BREACH_FILL_WORDS	BE_MVP_C(0x3fc0)
#define BE_MVP_BREACH_FILL_COUNT	BE_MVP_C(3)
#define BE_MVP_BREACH_BLOCK_BYTES	BE_MVP_C(64)
#define BE_MVP_BREACH_FORGED_VS_ROOT	BE_MVP_C(0x102016000)

/* The gigapage the hook's roots map: the MVP region, the windows, and the
 * pages; its alias VA under its Sv39 root; its forged GPA under its
 * Sv39x4 root; and the forged roots' VMID, which no scenario uses. */
#define BE_MVP_BREACH_GIGAPAGE		BE_MVP_C(0x100000000)
#define BE_MVP_BREACH_ALIAS_VA		BE_MVP_C(0x40000000)
#define BE_MVP_BREACH_FORGED_GPA	BE_MVP_C(0xc0000000)
#define BE_MVP_BREACH_VMID		BE_MVP_C(0x3fff)

/*
 * The control role (M11-8, breach-c; D-10's control-hart column). Its
 * record, header and slots, at the start of the control tail, which hart
 * 0's profile holds and nothing else uses; then its control rows' block
 * and words at the tail's end, each its fill. Its own Sv39 root in the
 * control padding page, which it writes itself. Its forged Sv39x4 root in
 * VS domain 0's hart mailbox, which it may read, and the forged VS-stage
 * root in VS domain 0's G-stage pool's spare page, which it may not: hart
 * 0's boot code writes both before the barrier, as it fills the words of
 * each VS-domain hart's mailbox that the hart-mailbox rows change
 * (BE_MVP_BREACH_FILL with the word's offset in its mailbox). The record's
 * domain word holds BE_MVP_BREACH_CONTROL_ROLE.
 */
#define BE_MVP_BREACH_CONTROL_RECORD_HPA	BE_MVP_C(0x102016000)
#define BE_MVP_BREACH_CONTROL_SLOTS	BE_MVP_C(144)
#define BE_MVP_BREACH_CONTROL_BLOCK_HPA	BE_MVP_C(0x102017f00)
#define BE_MVP_BREACH_CONTROL_FILL_BYTES BE_MVP_C(0x80)
#define BE_MVP_BREACH_CONTROL_SV39_HPA	BE_MVP_C(0x102013000)
#define BE_MVP_BREACH_CONTROL_SV39X4_HPA BE_MVP_C(0x10204c000)
#define BE_MVP_BREACH_CONTROL_VS_ROOT_HPA BE_MVP_C(0x102026000)
#define BE_MVP_BREACH_MAILBOX_FILL	BE_MVP_C(0xbf40)
#define BE_MVP_BREACH_MAILBOX_FILL_BYTES BE_MVP_C(0xc0)
#define BE_MVP_BREACH_CONTROL_ROLE	BE_MVP_C(0xc0)
/* The control role's modes: bare, satp, its forged hgatp, each VS
 * domain's own G-stage root, and its forged hgatp with the VS-stage root
 * in forbidden memory. */
#define BE_MVP_BREACH_CONTROL_MODES	BE_MVP_C(6)

#ifndef __ASSEMBLER__
#include <be/types.h>

#if defined(BE_MVP_BREACH) && \
	(defined(BE_MVP_BREACH_CONTROL) ? defined(BE_MVP_BREACH_DOMAIN) : \
	 (!defined(BE_MVP_BREACH_DOMAIN) || \
	  (BE_MVP_BREACH_DOMAIN != 0 && BE_MVP_BREACH_DOMAIN != 1)))
#error "a breach image hooks one VS domain, 0 or 1, or the control hart"
#endif

/*
 * The hook's sections: in the control role, every function and constant
 * of the hook, of its executor functions, and of its table goes into
 * sections of its own, which mvp-monitor.lds places in the MVP control
 * text and constants, ahead of the VS role's patterns.
 */
#if defined(BE_MVP_BREACH_CONTROL)
#define BE_MVP_BREACH_TEXT \
	__attribute__((section(".text.mvp.breach.control")))
#define BE_MVP_BREACH_RODATA \
	__attribute__((section(".rodata.mvp.breach.control")))
#define BE_MVP_BREACH_ROLE_SLOTS	BE_MVP_BREACH_CONTROL_SLOTS
#define BE_MVP_BREACH_ROLE_MODES	BE_MVP_BREACH_CONTROL_MODES
#else
#define BE_MVP_BREACH_TEXT
#define BE_MVP_BREACH_RODATA
#define BE_MVP_BREACH_ROLE_SLOTS	BE_MVP_BREACH_SLOTS
#define BE_MVP_BREACH_ROLE_MODES	BE_MVP_BREACH_MODES
#endif

struct be_mvp_breach_attempt {
	be_u64 kind;
	be_u64 address;
	be_u64 value;
	be_u64 extra;
	be_u64 call;
};

struct be_mvp_breach_slot {
	be_u64 cause;
	be_u64 stval;
	be_u64 value;
	be_u64 error;
};

struct be_mvp_breach_record {
	be_u64 magic;
	be_u64 state;
	be_u64 rows;
	be_u64 domain;
	be_u64 slot;
	be_u64 resume;
	be_u64 abort_cause;
	be_u64 abort_sepc;
	be_u64 abort_stval;
	be_u64 reserved[7];
	struct be_mvp_breach_slot slots[BE_MVP_BREACH_ROLE_SLOTS];
};

struct be_mvp_breach_saved {
	be_u64 stvec;
	be_u64 sscratch;
	be_u64 sepc;
	be_u64 sstatus;
	be_u64 hstatus;
	be_u64 satp;
	be_u64 hgatp;
	be_u64 vsatp;
};

_Static_assert(sizeof(struct be_mvp_breach_attempt) ==
	       BE_MVP_BREACH_ROW_BYTES &&
	       __builtin_offsetof(struct be_mvp_breach_attempt, call) ==
	       BE_MVP_BREACH_ROW_CALL, "the row's layout");
_Static_assert(sizeof(struct be_mvp_breach_slot) ==
	       BE_MVP_BREACH_SLOT_BYTES &&
	       __builtin_offsetof(struct be_mvp_breach_slot, error) ==
	       BE_MVP_BREACH_SLOT_ERROR, "the slot's layout");
_Static_assert(__builtin_offsetof(struct be_mvp_breach_record, slot) ==
	       BE_MVP_BREACH_FRAME_OFFSET &&
	       __builtin_offsetof(struct be_mvp_breach_record, abort_stval) ==
	       BE_MVP_BREACH_FRAME_OFFSET + BE_MVP_BREACH_FRAME_STVAL &&
	       __builtin_offsetof(struct be_mvp_breach_record, slots) ==
	       BE_MVP_BREACH_HEADER_BYTES, "the record's header");
#if defined(BE_MVP_BREACH_CONTROL)
_Static_assert(BE_MVP_BREACH_CONTROL_RECORD_HPA ==
	       BE_MVP_CONTROL_STACK_HPA + BE_MVP_CONTROL_STACK_BYTES &&
	       BE_MVP_BREACH_CONTROL_RECORD_HPA +
	       sizeof(struct be_mvp_breach_record) <=
	       BE_MVP_BREACH_CONTROL_BLOCK_HPA &&
	       BE_MVP_BREACH_CONTROL_BLOCK_HPA +
	       BE_MVP_BREACH_CONTROL_FILL_BYTES <=
	       BE_MVP_CONTROL_PROFILE_HPA + BE_MVP_CONTROL_PROFILE_BYTES &&
	       BE_MVP_BREACH_CONTROL_SV39_HPA ==
	       BE_MVP_DIAGNOSTIC_HPA + BE_MVP_DIAGNOSTIC_BYTES &&
	       BE_MVP_BREACH_CONTROL_SV39_HPA + 0x1000 <=
	       BE_MVP_CONTROL_STACK_HPA &&
	       BE_MVP_BREACH_CONTROL_SV39X4_HPA + 0x4000 ==
	       BE_MVP_G0_HART_MAILBOX_HPA + BE_MVP_HART_MAILBOX_BYTES &&
	       BE_MVP_HART_OUTBOUND_HEAD_OFFSET + 0xc0 <=
	       BE_MVP_BREACH_MAILBOX_FILL &&
	       BE_MVP_G0_HART_MAILBOX_HPA + BE_MVP_BREACH_MAILBOX_FILL +
	       BE_MVP_BREACH_MAILBOX_FILL_BYTES ==
	       BE_MVP_BREACH_CONTROL_SV39X4_HPA &&
	       BE_MVP_BREACH_CONTROL_VS_ROOT_HPA ==
	       BE_MVP_G0_LEVEL0_HPA + 0x1000 &&
	       BE_MVP_BREACH_CONTROL_VS_ROOT_HPA + 0x1000 <=
	       BE_MVP_G0_ROOT_HPA + BE_MVP_GUEST_POOL_BYTES,
	       "the control role's record, roots, and fill");
#else
_Static_assert(BE_MVP_BREACH_RECORD_OFFSET +
	       sizeof(struct be_mvp_breach_record) <=
	       BE_MVP_BREACH_CONTROL_OFFSET &&
	       BE_MVP_BREACH_CONTROL_OFFSET + BE_MVP_BREACH_BLOCK_BYTES +
	       2 * 8 <= BE_MVP_BREACH_SV39_OFFSET &&
	       BE_MVP_HART_OUTBOUND_HEAD_OFFSET + 0xc0 <=
	       BE_MVP_BREACH_RECORD_OFFSET &&
	       BE_MVP_BREACH_SV39X4_OFFSET + 0x4000 <=
	       BE_MVP_HART_MAILBOX_BYTES, "the record's place in the mailbox");
#endif
_Static_assert(__builtin_offsetof(struct be_mvp_breach_saved, vsatp) ==
	       BE_MVP_BREACH_SAVED_VSATP, "the saved registers' layout");

#if defined(BE_MVP_BREACH_CONTROL)
/**
 * be_mvp_breach_hook_control - the control hart's hostile-monitor
 * attempts, once (M11-8)
 *
 * Called once by hart 0 after its activation, before it reads any ring:
 * from its confined entry, after the BE_MVP:08 lines, in a boundary-on
 * image; after the starts in an -off copy. Runs every row of
 * be_mvp_breach_attempts from HS mode and records each one's trap in the
 * record in the control tail. A record already begun is marked
 * BE_MVP_BREACH_STATE_AGAIN, and nothing runs again.
 */
void be_mvp_breach_hook_control(void);
#else
/**
 * be_mvp_breach_hook - the hostile-monitor attempts, once, from a dispatch
 * @block: the dispatching hart's block
 * @exits: its exit count before this exit
 *
 * At the hooked VS domain's first exit, after its activation, runs every
 * row of be_mvp_breach_attempts from HS mode and records each one's trap
 * in the record; at any other exit, returns at once. The dispatch does not
 * call it for a tick, which is never an exit. A record already begun is
 * marked BE_MVP_BREACH_STATE_AGAIN, and nothing runs again.
 */
void be_mvp_breach_hook(be_u64 block, be_u64 exits);
#endif

/* The secret's source (mvp-runtime.c), with external linkage in a breach
 * image alone, for the row that names it (finding F-4). */
extern const be_u8 be_mvp_secret[BE_MVP_SECRET_BYTES];
#endif

#endif
