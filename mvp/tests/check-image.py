#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
# A copy of B7's tests/check-b7-image.py (accepted at 7b6b846b) with the
# counted changes listed in mvp/README.md.
"""Check the MVP images (planning/mvp-m0-plan.md, "Tests and evidence").

  check-image.py --pins PINS --kernel IMAGE --dtb0 DTB --dtb1 DTB
                 [--base B] [--lds MONITOR_LDS] [--expect JSON]
                 [--report AUTHORITY_REPORT]
                 --image TOOLCHAIN:ELF:BIN:BOOT_ELF:BOOT_IMG [--image ...]
                 [--probe PROBE:TOOLCHAIN:ELF:BIN:BOOT_ELF:BOOT_IMG ...]
  check-image.py --pins PINS --kernel IMAGE --dtb0 DTB --dtb1 DTB
                 --reference TOOLCHAIN:ELF:BIN:BOOT_ELF:BOOT_IMG
                 [--variant-dtbs NAME:DTB0:DTB1 ...]
                 [--variant NAME:BOOT_ELF:BOOT_IMG ...]
                 [--variant NAME:ELF:BIN:BOOT_ELF:BOOT_IMG ...]
  check-image.py --pins PINS --kernel IMAGE --dtb0 DTB --dtb1 DTB
                 --mutation-test TOOLCHAIN:ELF:BIN:BOOT_ELF:BOOT_IMG
                 [--mutation-probe PROBE:TOOLCHAIN:ELF:BIN:BOOT_ELF:BOOT_IMG]
  check-image.py --pins PINS --kernel IMAGE --dtb0 DTB --dtb1 DTB
                 --qemu-image QEMU_IMG --board-image BOOT_IMG [...]

beryllium-cheri: each form also takes --monitor riscv|cheri and
--guest-flavour linux|cheri-linux (planning/cheri-platform.md; the
defaults are riscv and linux, the development line's): the CHERI-aware
monitor's rules (its vector, resume tail, helpers, and mutations, marked
beryllium-cheri below) and the CHERI Linux guest's DT extensions.

The MVP links none of the R5 switch, so this is an MVP-specific checker,
as B1's to B7's are. Every address and budget comes from src/mvp-layout.h.
B7's rules hold, adapted for two domain harts under static ownership; the
plan's image checker (planning/mvp-m0-plan.md, "Tests and evidence") adds
or changes these, the MVP profile:

Monitor (ELF and its flat image):

- the M11-3 core, laid out by src/mvp-monitor.lds, whose eight PT_LOAD
  segments and every ASSERT conjunct hold: the flat image's first 0x20000
  bytes hold boot, control, shared, and VS-domain-hart executable groups,
  read-only data, generated input, control-writable data, the diagnostic
  page, and hart 0's stack, with all padding inside output sections;
- the fourth and fifth PT_LOAD segments are the two 64 KiB read clusters
  and the writer-split hart region: NOLOAD and RW;
- the MVP region (Plan revision M0-A.1): the sixth to eighth PT_LOAD
  segments, R-X, R, and RW, hold .mvp.text at 0x1_0206_8000, .mvp.rodata,
  and .mvp.data, in order, inside the region's 0x3c000 bytes (at most
  0x40000) and never inside the core, with the script's two region
  conjuncts; the flat image is exactly 0xa4000 bytes, the region ending
  it;
- the configuration (planning/mvp-m6-plan.md, D-1): the inventory and
  proposal (be_mvp_inventory, be_mvp_proposal) in the input section,
  which by the link map holds mvp-config.o's constants alone;
- by the link map (GNU ld's or lld's), every input section of the MVP
  layer's C objects (MVP_C_OBJECTS; mvp-core.o and mvp-sha256.o, the
  configuration's G-stage inputs and identity, and mvp-executor.o, the
  executor, and mvp-input.o, M7's console input, in every image) lies in
  the MVP region, never in the core's code
  extent or data, and no other object's lies there; by symbol, the MVP's
  assembly (the vector the accepted R3 validation requires inside the code
  extent among it, the resume tail, the hart entry, and the helpers) lies in
  the core's code extent and the MVP C entry points in the region's text;
- be_reset calls or tails nothing but be_b1_quiesce, be_mvp_runtime_main,
  and be_r3_arch_halt;
- be_r3_arch_install_management has exactly one call site, the
  executor's be_mvp_exec_install_hgatp (planning/mvp-m6-plan.md, D-5),
  and that has exactly one, the domain hart's, in be_mvp_hart_main: hart
  0 installs no root (M6, D-3);
- the seam (D-5): no function in the MVP region's text but the
  executor's (be_mvp_exec_*, and be_mvp_fw_call) calls, tails, or forms
  the address of an assembly helper (be_mvp_arch_*, be_mvp_probe_arch_*)
  or an accepted privileged helper (be_r3_arch_*, be_r3_platform_*);
- from the instruction words of the core's code extent and the MVP region's
  text together: exactly three sret (the dead R3 entry, the MVP resume tail,
  B1's skip); exactly one ecall, the accepted be_r3_arch_sbi_call, reached
  only from the accepted platform helpers and the executor's be_mvp_fw_call;
  exactly one fence.i, in be_mvp_arch_fence_i; exactly six wfi (the
  accepted halts' three, the wait, be_mvp_arch_wait, the domain park,
  be_mvp_arch_park, and the park page's entry, be_mvp_park_entry); hgatp
  writes and hfence.gvma only in the accepted R3 functions; no hfence.vvma,
  H load or store (hlv, hlvx, hsv), mret, ebreak, or F, D, or V
  instruction; no access at all to hstateen0, hvictl, hvien, hviprio1, or
  hviprio2;
- the CSR writer table: vsstatus, vsie, vstvec, vsscratch, vsepc,
  vscause, vstval, vsatp, scounteren, and senvcfg written after the R3
  reset only by the arm helper, be_mvp_arch_arm_controls; vstimecmp also
  by the TIME helper; vscause, vstval, vsepc, and vsstatus also by the
  injection helper, be_mvp_arch_inject (planning/mvp-m1-plan.md, "Tests
  and evidence"); stimecmp only by hart 0's budget helper, the scenario
  tick and park helpers, and B1's quiesce; sie by the arm and budget
  helpers; sip cleared only by the SSIP helper,
  be_mvp_arch_clear_ssip; hstatus only cleared, so VTW is never set;
- the values the helpers write, by constant tracking: the Sstc helper's
  henvcfg STCE; the arm helper's vstimecmp ~0, then hip read, then hedeleg
  0xb15d, hideleg 0x40, hcounteren 0x2, hstatus VTVM, VTW, and VTSR
  cleared (0x700000), scenario sie SSIE and STIE set (0x22), probe sie
  SSIE set (0x2), sscratch the trusted top, and
  the eleven per-domain CSRs from its third argument's words 0-10, in
  order, with every control read back into its first argument and the set
  into its fourth; the budget helper's stimecmp from its argument, sie
  SSIE and STIE set (0x22), and sscratch; the TIME helper's vstimecmp from
  its argument; the injection helper's vscause, vstval, vsepc, and
  vsstatus from its first four arguments, in that order, each then read
  back, in that order, into its fifth argument's four words, and no other
  CSR; the tick and scenario park write time plus the fixed period to
  stimecmp; the SSIP helper's clear of sip.SSIP, one csrrc that reads sip
  as it was and nothing else; the wait helper writes no CSR and reads only
  sip and time; the probe park writes and reads none;
- the injection helper's call sites: exactly one, the executor's
  be_mvp_exec_inject, itself called once, by the denial action
  (be_mvp_dispatch, or its deny), in an image whose scenario's
  accepted-exit set names denial and that is not the no-inject variant
  (te-poc and reader-write), and none in every other (two-guests and its
  variants, no-inject, the probe images);
- the vector stores the exit record's words, vsstatus at 352 among them,
  which it reads once;
- the vector and the resume tail derive the record from sscratch and
  require it to be a block's 0x2000 offset in the hart region; the hart
  entry sets sp to its block's stack top, after the same arithmetic on a1
  and before any memory access, calls be_mvp_hart_main, and otherwise
  parks;
- the resume tail: exactly the plan's checks (sscratch is the record,
  satp, stvec, scenario sie SSIE and STIE (probe sie SSIE only), sstatus
  under its mask against the saved
  SPVP, hstatus under the R3 mask without SPVP against SPV alone,
  hedeleg against the armed readback, hideleg, hie at most VSTIE, hvip's
  VS bits, hcounteren, htimedelta, henvcfg, hgeie, and the hgatp
  argument); SPP cleared, then set from the saved SPVP; sepc and every GPR
  from the frame; one SRET;
- the domains the monitor links (be_mvp_descs, be_mvp_hgatps, and
  be_mvp_bindings): two windows of 64 MiB at GPA 0x8000_0000 that do not
  overlap, two disjoint 32 KiB roots in the MVP pool, distinct nonzero
  VMIDs, each hgatp Sv39x4 with its domain's VMID and root, two distinct
  domain harts other than hart 0, and all equal to src/mvp-layout.h and,
  with --expect, the scenario's binding;
- the hart region (src/mvp-layout.h): two blocks of 64 KiB at their
  offsets, each a stack, saved page, state page, inbound and outbound ring,
  since M7 an input ring (planning/mvp-m7-plan.md, D-1), and unused tail
  in order, the rings powers of two;
- in an image of a scenario without pages, the linked channel record
  (be_mvp_channel) and configuration identity (be_mvp_config_identity):
  with --report, the scenario's authority report's channel (the page's
  GPA, HPA, and size, the writer's and the reader's domains and rights)
  and configuration identity; without, an all-zero record and no
  identity;
- in an image of a scenario with pages (planning/mvp-m2-plan.md; its
  expectation's schema be-mvp-expect-v3), the linked pages (be_mvp_pages):
  one to three 4 KiB pages inside the shared pages, each a channel
  between the two domains (the writer read and write, the reader read) or
  a secret page (one reader, read; the other domain no rights), at the
  GPA directly above the windows that matches its HPA, and equal to the
  pages the scenario's authority report gives; no channel record, since
  each domain hart's denial path takes its root's walked leaves of every
  page (M2-3); the configuration identity the report's; and the secret
  (be_mvp_secret, 32 bytes) in .mvp.rodata. An image of any other
  scenario links none of these;
- the measurement log (M9; mvp/docs/log-profile.md, planning/
  mvp-m9-plan.md, D-1 to D-4), in every image: hart 0's page (be_mvp_log,
  4 KiB, 4 KiB aligned) and its registers (be_mvp_log_registers, 128
  bytes), each wholly inside the MVP region's BSS; the image's pre-link
  constants (be_mvp_log_constants, 172 bytes, src/mvp-log.h) in
  .mvp.rodata: its sequence the image's (v1, v2, v3, or the probes'), its
  expected count that sequence's, with R2's five records when it logs
  them, its scenario digest the expectation's, its configuration and
  policy identities the report's, or zero without one, and each domain's
  expected launch register the recurrence over the SHA-256 of the
  domain's kernel and device tree as the boot image stages them and, for
  the secret page's reader, of the secret page (the linked secret,
  zero-padded), wrong-measurement's with bit 0 of that domain's first
  byte flipped (Q16), and a probe's zero; the inert canary
  (be_mvp_log_canary, 16 bytes) in .mvp.rodata, strictly inside the
  mvp-rodata range, whose address no instruction forms and no aligned
  word of the flat image holds; and each R2 range's start and end
  symbols, exactly its section's extent: .monitor.text, .monitor.rodata,
  .monitor.input, .mvp.text, and .mvp.rodata;
- in an image of a scenario whose accepted-exit set names the management
  extension (mgmt; planning/mvp-m2-plan.md, "The management extension"):
  the sealed grants (be_mvp_grants), one to four in the MVP control
  constants, each from one domain to the other with pause (1), terminate
  (2), or both, no pair twice, and equal to the domain grants of the
  scenario's authority report and its expectation's; hart 0's management
  state (be_mvp_mgmt_state) in the control writable-data extent; and the
  domain hart's request and wait (be_mvp_post_mgmt_request,
  be_mvp_wait_serve) and hart 0's setup (be_mvp_control_mgmt) linked. An
  image of any other scenario links none of these;
- the code a domain hart runs ("The measurement"): every function the
  hart entry and the vector reach through the calls and addresses their
  instruction words form, transitively, names no byte of hart 0's
  log page or registers (be_mvp_log, be_mvp_log_registers; M9, I19),
  management state, or grants (be_mvp_mgmt_state, be_mvp_grants), or,
  since M7, hart 0's console
  input (be_mvp_console_in, its read buffer be_mvp_console_in_buffer, and
  its views of the input rings, be_mvp_input_rings;
  planning/mvp-m7-plan.md, D-1 and D-3), and neither hart 0's entry
  (be_mvp_runtime_main), the management decision (be_mvp_mgmt_decide),
  hart 0's management setup, the firmware console read
  (be_mvp_exec_console_read), nor hart 0's routing of console input
  (be_mvp_input_byte, be_mvp_input_flush) is among them; the request and
  the wait, where linked, are, and, in every image but the probes, the
  service of a granted console read (be_mvp_input_serve);
- the firmware console read (M7, D-1): the executor's
  be_mvp_exec_console_read calls be_mvp_fw_call alone and is called from
  hart 0's code alone, never from the domain harts' (above).

Boot image (the board file and the ELF QEMU boots):

- B3's header with text_offset 0x0600_0000 and image_size equal to the
  file, B3's descriptor and report templates, and the start rule's;
- the shim: B3's instructions plus the start rule's ecall, so SBI DBCN
  write, SRST, and HSM hart_start, and HSM hart_stop only in the QEMU-only
  shim-rule variant, whose start rule's wait for hart 0 (mvp/README.md,
  item 137) adds HSM hart_get_status, a second SRST, two reads of time,
  and its FAIL line's template, which no other image holds;
- the eight ranges pairwise disjoint and in S-mode RAM: the core, the
  pool, the hart region, the MVP region, the staged image at L, the two
  domain windows, and the shared pages
  (planning/mvp-m2-plan.md, Q1), above G1's window, whose first page is
  M1's channel page (planning/mvp-m1-plan.md, Q1); when the image links a
  channel, the linked record's page is that page, and when it links
  pages, each lies inside the shared pages;
- B3's descriptor with the MVP flat image's length, 0xa4000;
- the monitor flat image at 0x1000, the kernel at 0xa5000, zeros, then
  G0's 4 KiB DTB at the next 4 KiB boundary and G1's right after it,
  which ends the file (at most BE_MVP_BOOT_IMAGE_MAX);
- each DTB through an FDT reader for its domain's DT contract (B7's, with
  the MVP model and compatible; in a te-poc or anchor image, the
  scenario's bootargs with each init's role, from --expect), the two
  equal but for /chosen/bootargs, and each against its pin;
- with the monitor ELF, the payload constants (be_mvp_payload_layout)
  equal to these offsets and sizes; with the boot ELF, its entry at L,
  four PT_LOAD segments (R-X, RW, R, R) whose bytes are the file, and its
  kernel and DTB labels.

The probe profile (--probe): probe-platform's monitor adds the probe
module's call of the executor's install, in be_mvp_probe_hgatp; the two
VMID images add the raw hgatp write, be_mvp_probe_arch_switch_hgatp, their
only hgatp write outside the accepted R3 functions, and no fence; no other
image holds either. probe-console-input (planning/mvp-m7-plan.md, D-12)
adds neither; its hart 0 alone reaches the firmware console read. The MVP
image links no probe symbol.

--variant checks a QEMU-only negative variant against the reference
images of its toolchain: payload, the kernel's magic2 byte; init-exit, G1's
DTB; rdcycle,
G0's DTB; sbi-time, both DTBs (since M9 each DTB variant's monitor its
own, which must pass the MVP profile itself and differ from the
reference's only in its expected launch registers); shim-rule, the shim;
exit-budget,
run-timeout, ring-full, and hart-start, the monitor, which must pass the
MVP profile itself (hart-start's domain 1 binding names hart 9); and,
against a te-poc reference with --expect and --report, te-poc's
reader-write and no-inject, each the monitor, which must pass the MVP
profile itself, no-inject with no injection call site; and, against an
anchor reference, anchor's secret-shared, response-writable,
wrong-measurement, and no-grant-check (planning/mvp-m2-plan.md, Q10),
each the monitor, and M9's self-report-flip (D-4), the monitor's
be_mvp_log_canary, exactly bit 0 of its first byte and no other bit of
the monitor or the boot image, with the variant's metadata
(self-report-flip.json beside it) naming the reference's and its own
SHA-256. M7-4's (planning/mvp-m7-plan.md, D-4 and Q4): hostile,
G0's DTB with rdinit=/init-hostile; and, against each scenario's
reference, its console variant SCENARIO-shell, whose monitor must pass the MVP
profile itself and differ from the reference's only in be_mvp_proposal,
one grant word from 0 to 1 for each domain a shell runs in, and its
expected launch registers, and whose
DTBs differ only for those domains, each the scenario's with
rdinit=/init-shell and pinned (the protected domain's is its own, Q27).
beryllium-cheri: with --monitor cheri, te-poc's channel-cw too
(planning/cheri-enforcement-plan.md, section 6, B2), the monitor, which
must pass the MVP profile itself, and its mutation, the reference's own
monitor and boot image under its name, refused as the reference; and with
the CHERI Linux guest (--guest-flavour cheri-linux), cheri-fault-hs (C3),
whose monitor must pass it with its arm helper's hedeleg 0xb15d, without
cause 28, and its mutation, the reference's under its name, refused for
its hedeleg.
M11-7 (planning/mvp-m11-plan.md, D-12, step 1): --boundary-image names
each image whose monitor is built with the boundary (a run image named in
--pairing's file runs its paired image's monitor), and the expectation
must agree. A boundary-on monitor links the confine stub
(be_mvp_confine_entry, in MVP boot text past the park page, which checks
its block and sets sp as the hart entry does, then calls the executor's
confine), named once by hart 0's start; since M11-8 start_harts calls
confine too, for hart 0 itself, and no other code does (C6); the two
executor functions, which call be_mvp_fw_call alone; the identity read
from hart 0's firmware probe alone; no formed hart-entry address; no
firmware call reachable from the domain harts' entry or the trap vector;
and be_mvp_partition_identity, 32 bytes of the MVP boot read-only extent,
its descriptor's identity (--partition-report). Its shim makes no HSM
call and holds the refused line. An off image links none of these. Each
scenario's off copy (SCENARIO-off, the same monitor built without the
boundary) passes the MVP profile itself; a variant whose boundary differs
from its reference's is checked against the scenario's off copy
(shim-rule's always). A breach image (--breach NAME:DECLARATION:DOMAIN,
DOMAIN 0, 1, or since M11-8 control) is checked under rules of its own:
its hook's instruction sites and CSR writers (BREACH_SITES,
BREACH_WRITERS) join the profile's, the hook's own instructions
(BREACH_KINDS) lie in its attempt helper alone, its functions lie in MVP
VS text, or the control hart's hook's in MVP control text, and the hook
is called once: by the dispatch, or the control hart's by hart 0's
confined C (in its -off copy by start_run() or the main that a compiler
folds it into). Every other image links none of the hook.
M11-8 (planning/mvp-m11-plan.md, D-4 rule 1; I22): in a boundary-on
image, each constant that the control role's code names in the MVP
control constants or the monitor's shared constants, and each constant
that its words name in turn, holds no image address outside the control
profile but be_mvp_bindings' two G-stage roots (C8); each object that
boot code hands to hart 0's state (the management grants and state, the
sealed maps and pages or channel, the ring views, console input and its
buffer) lies in the control profile with the rights hart 0 uses, and
each one that the scenario's kind has is linked (C9); and no function in
a role's text extents and no constant in a role's constant range is
reached from be_reset without being reached from that role, or for the
shared extents from either role (C10). What no root reaches is not
refused, and a constant without a symbol of its own (a merged string)
runs on to the next symbol: one that only boot code names, after one
that the role names, is not refused. Step 2's own rules (D-6 step 6), in
a boundary-on image: the control hart's confined entry alone in its slot,
at the MVP region's first byte (C1); its seven words, sp formed as hart
0's stack top, the call of its C side, the exception class, and the tail
of the terminal, with no other instruction (C2, C14); its address formed
by no code but hart 0's region check, at most once, as the MVP region's
start, and never as a call or a jump (C3); the control roots' reach, from
the confined entry as from the control loop, inside the control role's
extents and holding the shared trap vector (C4); boot code reaching none
of the confined entry, its C side, the READY wait, and the control loop
(C5); the executor's confine called by the stub and by start_harts
alone (C6); on every path from a start to hart 0's confine, no call but
a start again, a helper that reaches no firmware call and no ring, or a
function that does not return (C7); and the control roots reaching the
firmware through the console write, the reset, and the console read
alone, and none of boot code's firmware helpers (C13).
--mutation-test applies known defects in memory, to the images, their
ELF headers and symbols, the link map, or the layout they are built from,
and requires each to be rejected for its own reason.
--qemu-image checks each QEMU-only image of the U-Boot rehearsal against
the board image it was made from (--board-image, in the same order;
planning/mvp-m5-plan.md, "Tool changes (M5-2)", QEMU-only images): the
same size and bytes but header bytes 8 to 15, text_offset, which hold
BE_MVP_QEMU_TEXT_OFFSET where the board image holds
BE_MVP_UBOOT_TEXT_OFFSET, so that booti on QEMU's virt (RAM base
0x8000_0000) moves it to L, as the board's U-Boot moves the board image
(RAM base 0x1_0200_0000); then the rule's own mutations, each rejected
for its own reason: a byte changed before the header's text_offset,
after it, or last, the board's text_offset left in place, a byte
appended, and a board image carrying QEMU's text_offset.
"""

import argparse
import bisect
import hashlib
import importlib.util
import json
import pathlib
import re
import struct
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve()
MVP_DIR = HERE.parents[1]
REPO_ROOT = HERE.parents[2]
MONITOR_LDS = MVP_DIR / "src" / "mvp-monitor.lds"
B3_CHECKER = REPO_ROOT / "bringup" / "k3-b3" / "tests" / "check-b3-image.py"
LAYOUT_H = MVP_DIR / "src" / "mvp-layout.h"


def layout_constants(path=LAYOUT_H):
    """Every BE_MVP_* literal in mvp-layout.h, as integers."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    return {name[len("BE_MVP_"):]: int(value, 0) for name, value in
            re.findall(r"^#define\s+(BE_MVP_\w+)\s+BE_MVP_C\("
                       r"(0x[0-9a-fA-F]+|\d+)\)", text, re.M)}


LAYOUT = layout_constants()
BASE = LAYOUT["MONITOR_HPA"]
MVP_H = MVP_DIR / "src" / "mvp.h"


def class_number(name, path=MVP_H):
    """An enum be_mvp_class member's value, from mvp.h: its place in the
    enumeration, which begins at BE_MVP_CLASS_NONE = 0 and sets no other
    value."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    body = re.search(r"enum be_mvp_class \{(.*?)\};", text, re.S)
    members = re.findall(r"^\s*(BE_MVP_CLASS_\w+)(?:\s*=\s*(\d+))?,",
                         body.group(1) if body else "", re.M)
    require(members and members[0] == ("BE_MVP_CLASS_NONE", "0") and
            all(not value for _, value in members[1:]),
            f"{path}'s enum be_mvp_class is not a plain enumeration from 0")
    names = [member for member, _ in members]
    require(name in names, f"{path} has no class {name}")
    return names.index(name)
# The flat image (M11-3): the core's 0x20000 bytes
# (planning/mvp-m6-plan.md, D-4), the NOLOAD pool and hart region as
# zeros, and the MVP region, which ends it.
SPAN = LAYOUT["IMAGE_BYTES"]
CORE_SPAN = LAYOUT["CORE_BYTES"]
REGION = LAYOUT["REGION_HPA"]
REGION_BYTES = LAYOUT["REGION_BYTES"]
POOL = LAYOUT["POOL_HPA"]
POOL_BYTES = LAYOUT["POOL_BYTES"]
STAGING = LAYOUT["STAGING_HPA"]
WINDOW_BYTES = LAYOUT["GUEST_BYTES"]
WINDOWS = (LAYOUT["G0_HPA"], LAYOUT["G1_HPA"])
GUEST_POOL_BYTES = LAYOUT["GUEST_POOL_BYTES"]
ROOTS = (LAYOUT["G0_ROOT_HPA"], LAYOUT["G1_ROOT_HPA"])
VMIDS = (LAYOUT["G0_VMID"], LAYOUT["G1_VMID"])
HGATPS = (LAYOUT["G0_HGATP"], LAYOUT["G1_HGATP"])
KERNEL_OFFSET = LAYOUT["BOOT_KERNEL_OFFSET"]
MONITOR_OFFSET = LAYOUT["BOOT_MONITOR_OFFSET"]
DTB_BYTES = LAYOUT["DTB_BYTES"]
PAGE = LAYOUT["PAYLOAD_ALIGN"]
MONITOR_TEXT_LIMIT = LAYOUT["MONITOR_RODATA_HPA"]
MONITOR_DATA_LIMIT = LAYOUT["DIAGNOSTIC_HPA"]
CONTROL_STACK = LAYOUT["CONTROL_STACK_HPA"]
CONTROL_STACK_END = CONTROL_STACK + LAYOUT["CONTROL_STACK_BYTES"]
# The core's extents (planning/mvp-m6-plan.md, D-4), and the extent each of
# its sections lies in; the rest of the core, from hart 0's stack's end,
# holds no section and is zero.
CORE_EXTENTS = {
    "code": (BASE, LAYOUT["MONITOR_RODATA_HPA"]),
    "data": (LAYOUT["DATA_HPA"], LAYOUT["CONTROL_DATA_HPA"]),
    "control": (LAYOUT["CONTROL_PROFILE_HPA"],
                LAYOUT["CONTROL_PROFILE_HPA"] +
                LAYOUT["CONTROL_PROFILE_BYTES"]),
    "padding": (BASE + 0x18000, BASE + CORE_SPAN),
}
CORE_SECTIONS = {".monitor.text": "code", ".monitor.input": "data",
                 ".monitor.rodata": "data", ".monitor.data": "control",
                 ".diagnostic": "control", ".control.pad": "control",
                 ".stack.control": "control", ".control.tail": "control",
                 ".core.padding": "padding"}
CONFIG_SYMBOLS = ("be_mvp_inventory", "be_mvp_proposal")
# S-mode RAM on the COM260: above OpenSBI, to the end of its 8 GiB.
SMODE_RAM = (0x102000000, 0x300000000)
PF_X, PF_W = 1, 2
RISCV_MV_S0_A0 = 0x00050413
MASK64 = (1 << 64) - 1

# The hart region (src/mvp-layout.h): one block per domain hart, each its
# trusted stack, saved page, state page, two rings, since M7 the input ring
# (planning/mvp-m7-plan.md, D-1), and an unused tail.
HART_REGION = LAYOUT["HART_REGION_HPA"]
HART_REGION_BYTES = LAYOUT["HART_REGION_BYTES"]
BLOCK_BYTES = LAYOUT["BLOCK_BYTES"]
BLOCKS = (LAYOUT["G0_BLOCK_HPA"], LAYOUT["G1_BLOCK_HPA"])
BLOCK_AREAS = (("stack", "BLOCK_STACK_OFFSET", "BLOCK_STACK_BYTES"),
               ("saved page", "BLOCK_SAVED_OFFSET", "BLOCK_SAVED_BYTES"),
               ("state page", "BLOCK_STATE_OFFSET", "BLOCK_STATE_BYTES"))
RINGS = ("INBOUND_RING_BYTES", "OUTBOUND_RING_BYTES",
         "VARIANT_OUTBOUND_RING_BYTES", "INPUT_RING_BYTES")
HARTS = (LAYOUT["DOMAIN0_HART"], LAYOUT["DOMAIN1_HART"])

# The MVP-owned linker script (src/mvp-monitor.lds): its segments, and the
# conjuncts the checker requires among its ASSERTs, every one of which it
# evaluates: the core's code, data, and hart 0's stack, the trap vector in
# the code, the MVP pool block, the hart region after it, in the pool's
# segment, and the MVP region after that (Plan revision M0-A.1), in its
# own three segments.
PHDRS = [("monitor_text", 5), ("monitor_ro", 4), ("monitor_data", 6),
         ("mvp_pool", 6), ("mvp_hart", 6), ("mvp_text", 5),
         ("mvp_ro", 4), ("mvp_data", 6)]
MVP_CONJUNCTS = (
    f"be_reset == 0x{BASE:x}",
    f"__be_monitor_code_end == 0x{MONITOR_TEXT_LIMIT:x}",
    f"__be_monitor_data_start == 0x{MONITOR_TEXT_LIMIT:x}",
    f"__be_input_start == 0x{LAYOUT['MONITOR_INPUT_HPA']:x}",
    f"__be_input_end == 0x{LAYOUT['CONTROL_DATA_HPA']:x}",
    f"__be_diagnostic_start == 0x{LAYOUT['DIAGNOSTIC_HPA']:x}",
    f"__be_diagnostic_end == 0x{LAYOUT['DIAGNOSTIC_HPA'] + LAYOUT['DIAGNOSTIC_BYTES']:x}",
    f"__be_control_stack_start == 0x{CONTROL_STACK:x}",
    f"__be_control_stack_end == 0x{CONTROL_STACK_END:x}",
    f"__be_mvp_pool_start == 0x{POOL:x}",
    f"__be_mvp_pool_end == 0x{POOL + POOL_BYTES:x}",
    f"__be_mvp_hart_region_start == 0x{HART_REGION:x}",
    f"__be_mvp_hart_region_end == 0x{HART_REGION + HART_REGION_BYTES:x}",
    f"__be_mvp_region_start == 0x{REGION:x}",
    f"__be_mvp_region_end == 0x{REGION + REGION_BYTES:x}",
    f"be_mvp_park_entry == 0x{LAYOUT['PARK_ENTRY_HPA']:x}",
    f"be_mvp_hart_entry == 0x{LAYOUT['G0_CONFINED_ENTRY_HPA']:x}",
    # M11-8: the control hart's confined entry, in a boundary-on image.
    f"DEFINED(be_mvp_control_entry) ? be_mvp_control_entry == "
    f"0x{LAYOUT['CONTROL_CONFINED_ENTRY_HPA']:x} : 1",
)
POOL_PHDR = ("mvp_pool", 6)
HART_PHDR = ("mvp_hart", 6)
# The MVP layer's C objects, which only the MVP region holds; the MVP's
# assembly (mvp-trap.o, mvp-hartentry.o, and the probe images'
# mvp-probe-arch.o) stays with the core's code.
MVP_C_OBJECTS = ("mvp-runtime.o", "mvp-hartmain.o", "mvp-sbi.o",
                 "mvp-hart.o", "mvp-ring.o", "mvp-gstage.o", "mvp-payload.o",
                 "mvp-probe.o", "mvp-sha256.o", "mvp-core.o",
                 "mvp-executor.o", "mvp-input.o", "mvp-log.o")
ROLE_EXTENTS = (
    ("monitor boot", LAYOUT["MONITOR_BOOT_TEXT_HPA"],
     LAYOUT["MONITOR_BOOT_TEXT_HPA"] + LAYOUT["MONITOR_BOOT_TEXT_BYTES"],
     {"manifest.o", "state.o", "r3.o", "platform.o", "r5-entry.o",
      "b1-handoff.o", "privileged.o"}),
    ("monitor control", LAYOUT["MONITOR_CONTROL_TEXT_HPA"],
     LAYOUT["MONITOR_CONTROL_TEXT_HPA"] +
     LAYOUT["MONITOR_CONTROL_TEXT_BYTES"],
     {"r3.o", "platform.o", "privileged.o", "mvp-trap.o"}),
    ("monitor shared", LAYOUT["MONITOR_SHARED_TEXT_HPA"],
     LAYOUT["MONITOR_SHARED_TEXT_HPA"] + LAYOUT["MONITOR_SHARED_TEXT_BYTES"],
     {"freestanding.o", "r3.o", "platform.o", "privileged.o",
      "mvp-trap.o", "mvp-ring.o",
      "mvp-executor.o", "mvp-runtime.o", "mvp-sbi.o", "mvp-hart.o",
      "mvp-probe-arch.o"}),
    ("monitor VS-domain-hart", LAYOUT["MONITOR_DOMAIN_TEXT_HPA"],
     LAYOUT["MONITOR_DOMAIN_TEXT_HPA"] + LAYOUT["MONITOR_DOMAIN_TEXT_BYTES"],
     {"privileged.o", "mvp-trap.o", "mvp-probe-arch.o"}),
    ("monitor read-only", LAYOUT["MONITOR_RODATA_HPA"],
     LAYOUT["MONITOR_RODATA_HPA"] + LAYOUT["MONITOR_RODATA_BYTES"],
     {"manifest.o", "state.o", "r3.o", "platform.o", "freestanding.o",
      "privileged.o", "r5-entry.o", "b1-handoff.o",
      "mvp-probe-arch.o"}),
    ("monitor input", LAYOUT["MONITOR_INPUT_HPA"],
     LAYOUT["MONITOR_INPUT_HPA"] + LAYOUT["MONITOR_INPUT_BYTES"],
     {"mvp-config.o"}),
    ("control data", LAYOUT["CONTROL_DATA_HPA"],
     LAYOUT["CONTROL_DATA_HPA"] + LAYOUT["CONTROL_DATA_BYTES"],
     {"mvp-runtime.o"}),
    # M11-8: the control breach image's hook (breach-c), whose rule set
    # (check_breach_code()) places each role's hook in its role's text.
    ("MVP control", LAYOUT["MVP_CONTROL_TEXT_HPA"],
     LAYOUT["MVP_CONTROL_TEXT_HPA"] + LAYOUT["MVP_CONTROL_TEXT_BYTES"],
     {"mvp-hartentry.o", "mvp-trap.o", "mvp-runtime.o", "mvp-hart.o",
      "mvp-input.o", "mvp-executor.o", "mvp-sha256.o", "mvp-sbi.o",
      "mvp-probe.o", "mvp-breach.o", "mvp-breach-arch.o"}),
    ("MVP VS-domain-hart", LAYOUT["MVP_DOMAIN_TEXT_HPA"],
     LAYOUT["MVP_DOMAIN_TEXT_HPA"] + LAYOUT["MVP_DOMAIN_TEXT_BYTES"],
     {"mvp-hartentry.o", "mvp-trap.o", "mvp-hartmain.o", "mvp-sbi.o",
      "mvp-gstage.o", "mvp-input.o", "mvp-hart.o", "mvp-executor.o",
      "mvp-probe.o", "mvp-probe-arch.o", "mvp-breach.o",
      "mvp-breach-arch.o"}),
    ("MVP boot", LAYOUT["MVP_BOOT_TEXT_HPA"],
     LAYOUT["MVP_BOOT_TEXT_HPA"] + LAYOUT["MVP_BOOT_TEXT_BYTES"],
     set(MVP_C_OBJECTS) | {"mvp-trap.o", "mvp-hartentry.o",
                           "mvp-probe-arch.o"}),
    ("MVP boot read-only", LAYOUT["MVP_BOOT_RODATA_HPA"],
     LAYOUT["MVP_BOOT_RODATA_HPA"] + LAYOUT["MVP_BOOT_RODATA_BYTES"],
     set(MVP_C_OBJECTS)),
    ("MVP writable", LAYOUT["MVP_BOOT_DATA_HPA"],
     LAYOUT["REGION_HPA"] + LAYOUT["REGION_BYTES"],
     set(MVP_C_OBJECTS)),
)
DOMAIN_CODE_EXTENTS = (
    (LAYOUT["MONITOR_SHARED_TEXT_HPA"],
     LAYOUT["MONITOR_SHARED_TEXT_HPA"] + LAYOUT["MONITOR_SHARED_TEXT_BYTES"]),
    (LAYOUT["MONITOR_DOMAIN_TEXT_HPA"],
     LAYOUT["MONITOR_DOMAIN_TEXT_HPA"] + LAYOUT["MONITOR_DOMAIN_TEXT_BYTES"]),
    (LAYOUT["MVP_DOMAIN_TEXT_HPA"],
     LAYOUT["MVP_DOMAIN_TEXT_HPA"] + LAYOUT["MVP_DOMAIN_TEXT_BYTES"]),
)
CONTROL_CODE_EXTENTS = (
    (LAYOUT["MONITOR_CONTROL_TEXT_HPA"],
     LAYOUT["MONITOR_CONTROL_TEXT_HPA"] +
     LAYOUT["MONITOR_CONTROL_TEXT_BYTES"]),
    (LAYOUT["MONITOR_SHARED_TEXT_HPA"],
     LAYOUT["MONITOR_SHARED_TEXT_HPA"] + LAYOUT["MONITOR_SHARED_TEXT_BYTES"]),
    (LAYOUT["MVP_CONTROL_TEXT_HPA"],
     LAYOUT["MVP_CONTROL_TEXT_HPA"] + LAYOUT["MVP_CONTROL_TEXT_BYTES"]),
)
CONTROL_REFERENCE_EXTENTS = (
    ("monitor control", LAYOUT["MONITOR_CONTROL_TEXT_HPA"],
     LAYOUT["MONITOR_CONTROL_TEXT_HPA"] +
     LAYOUT["MONITOR_CONTROL_TEXT_BYTES"], "r"),
    ("monitor shared", LAYOUT["MONITOR_SHARED_TEXT_HPA"],
     LAYOUT["MONITOR_SHARED_TEXT_HPA"] +
     LAYOUT["MONITOR_SHARED_TEXT_BYTES"], "r"),
    ("MVP control", LAYOUT["MVP_CONTROL_TEXT_HPA"],
     LAYOUT["MVP_CONTROL_TEXT_HPA"] + LAYOUT["MVP_CONTROL_TEXT_BYTES"], "r"),
    ("control data", LAYOUT["CONTROL_PROFILE_HPA"],
     LAYOUT["CONTROL_PROFILE_HPA"] + LAYOUT["CONTROL_PROFILE_BYTES"], "rw"),
    ("sealed data", LAYOUT["MVP_SEALED_HPA"],
     LAYOUT["MVP_SEALED_HPA"] + LAYOUT["MVP_SEALED_BYTES"], "r"),
    ("measurement log", LAYOUT["MVP_LOG_HPA"],
     LAYOUT["MVP_LOG_HPA"] + LAYOUT["MVP_LOG_BYTES"], "r"),
    ("G0 control mailbox", LAYOUT["G0_CONTROL_MAILBOX_HPA"],
     LAYOUT["G0_CONTROL_MAILBOX_HPA"] + LAYOUT["CONTROL_MAILBOX_BYTES"],
     "rw"),
    ("G1 control mailbox", LAYOUT["G1_CONTROL_MAILBOX_HPA"],
     LAYOUT["G1_CONTROL_MAILBOX_HPA"] + LAYOUT["CONTROL_MAILBOX_BYTES"],
     "rw"),
    ("hart mailboxes", LAYOUT["G0_HART_MAILBOX_HPA"],
     LAYOUT["G1_HART_MAILBOX_HPA"] + LAYOUT["HART_MAILBOX_BYTES"], "r"),
)
DOMAIN_REFERENCE_EXTENTS = (
    ("monitor shared", LAYOUT["MONITOR_SHARED_TEXT_HPA"],
     LAYOUT["MONITOR_SHARED_TEXT_HPA"] +
     LAYOUT["MONITOR_SHARED_TEXT_BYTES"], "r"),
    ("monitor VS-domain-hart", LAYOUT["MONITOR_DOMAIN_TEXT_HPA"],
     LAYOUT["MONITOR_DOMAIN_TEXT_HPA"] +
     LAYOUT["MONITOR_DOMAIN_TEXT_BYTES"], "r"),
    ("MVP VS-domain-hart", LAYOUT["MVP_DOMAIN_TEXT_HPA"],
     LAYOUT["MVP_DOMAIN_TEXT_HPA"] + LAYOUT["MVP_DOMAIN_TEXT_BYTES"], "r"),
)
# The probe images run with the boundary off (the M11 plan's Q16): their
# post-barrier code keeps the boot OpenSBI domain's wide access.
PROBE_REFERENCE_EXTENTS = (
    ("boundary-off image", BASE, BASE + SPAN, "rw"),
)
# The region's sections, and its linked symbols beyond the ASSERTs'.
REGION_SECTIONS = (".mvp.text", ".mvp.rodata", ".mvp.data")
REGION_SYMBOLS = ("__be_mvp_region_start", "__be_mvp_region_end",
                  "__be_mvp_text_start", "__be_mvp_text_end",
                  "__be_mvp_bss_start", "__be_mvp_bss_end",
                  "__be_mvp_control_text_start",
                  "__be_mvp_control_text_end",
                  "__be_control_confined_entry_slot_start",
                  "__be_control_confined_entry_slot_end")

# From the accepted B2 images (bringup/k3-b2/README.md: GCC 9c145f00...,
# Clang 47be17e3...): the R3 functions the MVP reuses.
B2_R3_FUNCTIONS = {
    "gcc": {
        "be_r3_arch_reset_state": (
            0x1aa,
            "0e32a04aab3cd1b900639e53495ef8879909b712436fa369c6d4c6f906ad840a"),
        "be_r3_arch_install_management": (
            0xe,
            "d928179d49757046c40c5ed17e8fda517ec041707cdee758c33182942f2d2f52"),
        "be_r3_arch_enter_management": (
            0x56,
            "d406f12926032eacda7c8e2d80d5d1609ea9251c6dabd95d38bbd7b12cd5c610"),
    },
    "clang": {
        "be_r3_arch_reset_state": (
            0x1aa,
            "aba92183d42684c487d1e14e054e366c707b308c224d8f9b6086d3ab1cf88427"),
        "be_r3_arch_install_management": (
            0xe,
            "d928179d49757046c40c5ed17e8fda517ec041707cdee758c33182942f2d2f52"),
        "be_r3_arch_enter_management": (
            0x56,
            "d406f12926032eacda7c8e2d80d5d1609ea9251c6dabd95d38bbd7b12cd5c610"),
    },
}

R3_RESET = "be_r3_arch_reset_state"
R3_INSTALL = "be_r3_arch_install_management"
R3_ENTER = "be_r3_arch_enter_management"
R3_ARM = "be_r3_arm_management_entry"
R3_SBI = "be_r3_arch_sbi_call"
R3_UNEXPECTED = "be_r3_unexpected_trap"
R3_HALT = "be_r3_arch_halt"
B1_QUIESCE = "be_b1_quiesce"
B1_SKIP = "be_b1_skip"
B1_HALT = "be_b1_halt"
MVP_STCE = "be_mvp_arch_arm_stce"
MVP_ARM = "be_mvp_arch_arm_controls"
MVP_TIMER = "be_mvp_arch_set_timer"
MVP_TICK = "be_mvp_arch_rearm_tick"
MVP_BUDGET = "be_mvp_arch_arm_budget"
MVP_WAIT = "be_mvp_arch_wait"
MVP_SSIP = "be_mvp_arch_clear_ssip"
MVP_TIME = "be_mvp_arch_read_time"
MVP_PARK = "be_mvp_arch_park"
MVP_PARK_ENTRY = "be_mvp_park_entry"
MVP_FENCE_I = "be_mvp_arch_fence_i"
MVP_VECTOR = "be_mvp_trap_vector"
MVP_RESUME = "be_mvp_arch_resume"
MVP_ENTRY = "be_mvp_hart_entry"
MVP_MAIN = "be_mvp_runtime_main"
MVP_HART_MAIN = "be_mvp_hart_main"
MVP_DISPATCH = "be_mvp_dispatch"
MVP_TERMINAL = "be_mvp_runtime_terminal"
MVP_HART_TERMINAL = "be_mvp_hart_terminal"
CONTROL_LOOP = "control_loop"
MVP_FW_CALL = "be_mvp_fw_call"
MVP_INJECT = "be_mvp_arch_inject"
# The executor's install and injection (planning/mvp-m6-plan.md, D-5).
EXEC_INSTALL = "be_mvp_exec_install_hgatp"
EXEC_INJECT = "be_mvp_exec_inject"
# The executor's henvcfg arm, which boot code and each VS-domain hart call.
EXEC_STCE = "be_mvp_exec_arm_stce"
# M11-7 (planning/mvp-m11-plan.md, D-3 "Pairing", D-6, D-8, D-12): a
# boundary-on image's confining stub, the domain commit extension's two
# executor functions, and the image's configuration identity, the
# partition descriptor's; a boundary-off image holds none of them.
MVP_CONFINE_ENTRY = "be_mvp_confine_entry"
EXEC_CONFINE = "be_mvp_exec_confine"
EXEC_IDENTITY = "be_mvp_exec_boundary_identity"
MVP_PARTITION_IDENTITY = "be_mvp_partition_identity"
# M11-8 (planning/mvp-m11-plan.md, D-6 step 6; step 2): the control hart's
# confined entry, alone in its slot at the device tree's next-addr, and the
# C it calls, which runs the READY wait and the control loop; the boot code
# that starts both VS-domain harts and then confines hart 0.
CONTROL_ENTRY = "be_mvp_control_entry"
CONTROL_CONFINED = "be_mvp_control_confined"
START_HARTS = "start_harts"
START_FAILED = "start_failed"
WAIT_READY = "wait_ready"
EXEC_HART_START = "be_mvp_exec_hart_start"
BOUNDARY_SYMBOLS = (MVP_CONFINE_ENTRY, EXEC_CONFINE, EXEC_IDENTITY,
                    MVP_PARTITION_IDENTITY, CONTROL_ENTRY, CONTROL_CONFINED)
# What the code a confined VS-domain hart runs never reaches (D-8): any
# firmware call, and the boundary's own boot-time calls.
VS_UNREACHABLE = ("be_mvp_fw_call", "be_r3_arch_sbi_call",
                  "be_mvp_exec_dbcn_write", "be_mvp_exec_system_reset",
                  MVP_CONFINE_ENTRY, EXEC_CONFINE, EXEC_IDENTITY)
VS_UNREACHABLE_PREFIX = "be_r3_platform_"
# Hart 0's boot code that probes the firmware and starts the harts (each
# inlined into be_mvp_runtime_main, or its own function).
BOUNDARY_PROBE_OWNERS = ("be_mvp_runtime_main", "probe_firmware")
BOUNDARY_START_OWNERS = ("be_mvp_runtime_main", "start_harts")
# The images built with the boundary (--boundary-images, mvp/Makefile's
# MVP_BOUNDARY_IMAGES), the run images paired with another's monitor
# (--pairing, scenarios/pairing.txt), and each descriptor's identity
# (--partition-report, tools/gen-partition.py's authority report), which
# select_boundary() sets before any check.
BOUNDARY_IMAGES = frozenset()
PAIRING = {}
PARTITION_IDENTITIES = {}
# M11-7 (planning/mvp-m11-plan.md, D-10): anchor's hostile-monitor images
# (--breach NAME:DECLARATION:DOMAIN; mvp/Makefile's MVP_BREACH_VARIANTS and
# their -off copies), {name: (declaration, VS domain or BREACH_CONTROL)},
# and their hook: the hook, its executor functions, and its privileged
# helpers, which hold the instruction sites and CSR writes BREACH_SITES and
# BREACH_WRITERS add and every instruction of BREACH_KINDS; every other
# image links none. M11-8: the control hart's hook (BREACH_CONTROL, its
# entry BREACH_CONTROL_HOOK), called once by hart 0's confined entry, or in
# its -off copy after the starts, by start_run() or the runtime's main into
# which a compiler folds it (BREACH_OFF_CALLERS).
BREACH = {}
BREACH_HOOK = "be_mvp_breach_hook"
BREACH_CONTROL = "control"
BREACH_CONTROL_HOOK = "be_mvp_breach_hook_control"
BREACH_OFF_CALLERS = ("start_run", "be_mvp_runtime_main")
BREACH_ENTER = "be_mvp_breach_arch_enter"
BREACH_TRANSLATE = "be_mvp_breach_arch_translate"
BREACH_ATTEMPT = "be_mvp_breach_arch_attempt"
BREACH_LEAVE = "be_mvp_breach_arch_leave"
BREACH_VECTOR = "be_mvp_breach_arch_vector"
BREACH_ARCH = (BREACH_ENTER, BREACH_TRANSLATE, BREACH_ATTEMPT, BREACH_LEAVE)
BREACH_EXEC_PREFIX = "be_mvp_exec_breach_"
BREACH_TABLE = "be_mvp_breach_attempts"
BREACH_MODES_TABLE = "be_mvp_breach_modes"
BREACH_PREFIXES = ("be_mvp_breach_", BREACH_EXEC_PREFIX)
BREACH_OBJECTS = ("mvp-breach.o", "mvp-breach-arch.o")
BREACH_SITES = {"ecall": {BREACH_ATTEMPT: 1}, "sret": {BREACH_VECTOR: 1},
                "sfence.vma": {BREACH_TRANSLATE: 1},
                "hfence.gvma": {BREACH_TRANSLATE: 1},
                "hfence.vvma": {BREACH_TRANSLATE: 1},
                "hlsv": {BREACH_ATTEMPT: 2}, "wfi": {BREACH_VECTOR: 1}}
BREACH_WRITERS = {"stvec": {BREACH_ENTER, BREACH_LEAVE},
                  "sscratch": {BREACH_ENTER, BREACH_LEAVE},
                  "sepc": {BREACH_LEAVE, BREACH_VECTOR},
                  "sstatus": {BREACH_LEAVE},
                  "hstatus": {BREACH_ENTER, BREACH_LEAVE},
                  "satp": {BREACH_TRANSLATE}, "hgatp": {BREACH_TRANSLATE},
                  "vsatp": {BREACH_TRANSLATE}}
BREACH_KINDS = {"amo": 1, "lr": 1, "sc": 1, "cbo.zero": 1, "cbo.inval": 1,
                "jalr-link": 1}
BREACH_TOOL = MVP_DIR / "tools" / "gen-breach.py"
BREACH_HEADER = MVP_DIR / "src" / "mvp-breach.h"
# The log page's bytes in use (src/mvp-log.h): its header and capacity.
LOG_USED_BYTES = 128 + 41 * 96
MVP_LAYOUT_SYMBOL = "be_mvp_payload_layout"
MVP_CHANNEL_SYMBOL = "be_mvp_channel"
MVP_IDENTITY_SYMBOL = "be_mvp_config_identity"
MVP_BINDINGS_SYMBOL = "be_mvp_bindings"
MVP_DESCS_SYMBOL = "be_mvp_descs"
MVP_HGATPS_SYMBOL = "be_mvp_hgatps"
# A scenario with pages (planning/mvp-m2-plan.md, Q1 and Q5): the linked
# pages and the secret.
MVP_PAGES_SYMBOL = "be_mvp_pages"
MVP_SECRET_SYMBOL = "be_mvp_secret"
# The measurement log (mvp/docs/log-profile.md; planning/mvp-m9-plan.md,
# D-1 to D-4): hart 0's page and registers, the image's pre-link constants
# (src/mvp-log.h, struct be_mvp_log_constants: scenario, configuration,
# policy, two launch registers, then count, sequence, and r2 as 32-bit
# words), the inert canary, and the R2 ranges, each its section's extent.
MVP_LOG_SYMBOL = "be_mvp_log"
MVP_LOG_REGISTERS_SYMBOL = "be_mvp_log_registers"
MVP_LOG_CONSTANTS_SYMBOL = "be_mvp_log_constants"
MVP_LOG_CANARY_SYMBOL = "be_mvp_log_canary"
LOG_PAGE_BYTES = 0x1000
LOG_REGISTERS_BYTES = 128
LOG_CONSTANTS_BYTES = 172
LOG_LAUNCH_AT = 96
LOG_CANARY_BYTES = 16
LOG_R2_RANGES = (
    ("monitor-text", ".monitor.text", "__be_monitor_code_start",
     "__be_monitor_code_end"),
    ("monitor-rodata", ".monitor.rodata", "__be_monitor_rodata_start",
     "__be_monitor_rodata_end"),
    ("monitor-input", ".monitor.input", "__be_input_start",
     "__be_input_end"),
    ("mvp-text", ".mvp.text", "__be_mvp_text_start", "__be_mvp_text_end"),
    ("mvp-rodata", ".mvp.rodata", "__be_mvp_rodata_start",
     "__be_mvp_rodata_end"))
# Each sequence's count, the close included, without R2's five records
# (the profile's 3.1): v1 to v3, then the probes'.
LOG_COUNTS = {1: 8, 2: 9, 3: 10, 4: 4}
LOG_R2_RECORDS = 5
MVP_GRANTS_SYMBOL = "be_mvp_grants"
MVP_MGMT_STATE_SYMBOL = "be_mvp_mgmt_state"
MVP_DECIDE = "be_mvp_mgmt_decide"
MVP_REQUEST = "be_mvp_post_mgmt_request"
MVP_WAIT_SERVE = "be_mvp_wait_serve"
MVP_CONTROL_MGMT = "be_mvp_control_mgmt"
# The management extension's linked objects and functions
# (planning/mvp-m2-plan.md, "The management extension"): exactly in an
# image whose scenario accepts it.
MGMT_SYMBOLS = (MVP_GRANTS_SYMBOL, MVP_MGMT_STATE_SYMBOL, MVP_REQUEST,
                MVP_WAIT_SERVE, MVP_CONTROL_MGMT)
# Hart 0's own objects, which no code a domain hart runs names ("The
# measurement"; since M9 the log's page and registers, I19), the domain
# harts' entries into the monitor, and hart 0's
# code they never reach; and the domain hart's management code, which they
# do.
# Console input (planning/mvp-m7-plan.md, D-1 and D-3): hart 0's routing
# and accounting, its firmware read buffer, and its views of the input
# rings; the executor's firmware console read and hart 0's routing; and
# the domain hart's service of a granted read.
MVP_CONSOLE_IN_SYMBOL = "be_mvp_console_in"
MVP_CONSOLE_BUFFER_SYMBOL = "be_mvp_console_in_buffer"
MVP_INPUT_RINGS_SYMBOL = "be_mvp_input_rings"
EXEC_CONSOLE_READ = "be_mvp_exec_console_read"
INPUT_ROUTING = ("be_mvp_input_byte", "be_mvp_input_flush")
INPUT_SERVE = "be_mvp_input_serve"
HART0_ONLY = (MVP_LOG_SYMBOL, MVP_LOG_REGISTERS_SYMBOL, MVP_MGMT_STATE_SYMBOL,
              MVP_GRANTS_SYMBOL, MVP_CONSOLE_IN_SYMBOL,
              MVP_CONSOLE_BUFFER_SYMBOL, MVP_INPUT_RINGS_SYMBOL)
DOMAIN_ROOTS = (MVP_ENTRY, MVP_VECTOR)
HART0_CODE = (MVP_MAIN, MVP_DECIDE, MVP_CONTROL_MGMT, EXEC_CONSOLE_READ) + \
    INPUT_ROUTING
# M11-8, step 2 (planning/mvp-m11-plan.md, D-6 step 6 and D-8): what boot
# code never reaches (C5); what start_harts may call between its last
# start and hart 0's confine (C7); and the firmware calls the control roots
# make, through the console write, the reset, and the console read alone
# (C13), reaching none of the boot code's firmware helpers.
CONTROL_ONLY = (CONTROL_ENTRY, CONTROL_CONFINED, WAIT_READY, CONTROL_LOOP)
# C3: the entry's address is the MVP region's start, which hart 0's region
# check (clear_mvp_bss(), inlined into be_mvp_runtime_main or not) forms.
REGION_CHECK_OWNERS = (MVP_MAIN, "clear_mvp_bss")
# C7: what start_harts may call on a path from a start to hart 0's
# confine: hart_start again, these helpers, which return, and these
# functions, which do not; each helper reaches no firmware call and no
# ring (R2-2).
START_TAIL_HELPERS = ("be_mvp_exec_read_time", "be_mvp_block_hpa",
                      "be_mvp_control_started")
START_TAIL_ENDS = (START_FAILED, MVP_TERMINAL)
RING_PREFIX = "be_mvp_ring_"
CONTROL_FIRMWARE = ("be_mvp_fw_call", "be_r3_arch_sbi_call")
CONTROL_FIRMWARE_CALLERS = ("be_r3_platform_write", "be_r3_platform_reset",
                            EXEC_CONSOLE_READ)
CONTROL_UNREACHABLE = (EXEC_HART_START, "be_mvp_exec_hart_status",
                       "be_mvp_exec_sbi_probe", "be_mvp_exec_sbi_version",
                       EXEC_CONFINE, EXEC_IDENTITY, "be_mvp_exec_send_ipi",
                       "be_mvp_exec_dbcn_write")
DOMAIN_MGMT_CODE = (MVP_REQUEST, MVP_WAIT_SERVE)
PAGE_SYMBOLS = (MVP_PAGES_SYMBOL, MVP_SECRET_SYMBOL)
PROBE_HGATP = "be_mvp_probe_hgatp"
PROBE_SWITCH = "be_mvp_probe_arch_switch_hgatp"
PROBE_STUB = "be_mvp_probe_stub"
# Where the MVP's code lies (Plan revision M0-A.1): its assembly with the
# accepted code, below 0x1_0200_8000, the vector the accepted R3 validation
# requires there among it; its C, these entry points among it, in the MVP
# region's text.
MVP_ASSEMBLY = (MVP_VECTOR, MVP_RESUME, MVP_ENTRY, MVP_STCE, MVP_ARM,
                MVP_TIMER, MVP_INJECT, MVP_BUDGET, MVP_WAIT, MVP_SSIP,
                MVP_TIME, MVP_PARK, MVP_FENCE_I, "be_mvp_arch_fence_w_w",
                "be_mvp_arch_fence_r_r", "be_mvp_arch_fence_r_w",
                "be_mvp_arch_fence_rw_rw")
MVP_C_ENTRIES = (MVP_MAIN, MVP_HART_MAIN, MVP_DISPATCH, MVP_TERMINAL,
                 MVP_HART_TERMINAL, MVP_FW_CALL)
# The HS-to-M calls: the accepted platform helpers, and the MVP's HSM, IPI,
# and domain-hart DBCN calls, all through the accepted ecall site.
PLATFORM_HELPERS = {"sbi_value_call", "be_r3_platform_get_spec_version",
                    "be_r3_platform_probe_extension", "be_r3_platform_write",
                    "be_r3_platform_reset", MVP_FW_CALL}
REQUIRED_SYMBOLS = (
    "be_reset", B1_QUIESCE, MVP_MAIN, CONTROL_LOOP, MVP_HART_MAIN,
    MVP_DISPATCH,
    MVP_VECTOR, MVP_RESUME, MVP_ENTRY, MVP_STCE, MVP_ARM, MVP_TIMER,
    MVP_BUDGET, MVP_WAIT, MVP_SSIP, MVP_TIME, MVP_PARK, MVP_PARK_ENTRY,
    MVP_FENCE_I,
    MVP_TERMINAL, MVP_HART_TERMINAL, MVP_FW_CALL, MVP_INJECT, EXEC_INSTALL,
    MVP_LAYOUT_SYMBOL, MVP_BINDINGS_SYMBOL, MVP_DESCS_SYMBOL,
    MVP_HGATPS_SYMBOL,
    "__be_mvp_pool_start", "__be_mvp_pool_end", "__be_mvp_hart_region_start",
    "__be_mvp_hart_region_end", R3_RESET, R3_INSTALL, R3_ENTER, R3_SBI,
    R3_HALT,
)

# beryllium-cheri: the monitor variant and the guest flavour this checker
# judges (--monitor and --guest-flavour; planning/cheri-platform.md), which
# select_variant() sets before any check. The defaults are the RISC-V
# monitor and the Linux guest, whose rules are the development line's; the
# CHERI-aware monitor adds CHERI_CSR_NAMES and CHERI_CSR_WRITERS, takes
# CHERI_HELPER_WRITES and its ARMED_HENVCFG, and has its own trap entry,
# resume tail, helper, and mutation rules, each marked beryllium-cheri; the
# CHERI Linux guest's DTBs name FLAVOUR_EXTENSIONS too.
MONITOR, GUEST_FLAVOUR = "riscv", "linux"
CSR_NAMES = {
    0x100: "sstatus", 0x104: "sie", 0x105: "stvec", 0x106: "scounteren",
    0x10A: "senvcfg", 0x140: "sscratch", 0x141: "sepc", 0x142: "scause",
    0x143: "stval", 0x144: "sip", 0x14D: "stimecmp", 0x150: "siselect",
    0x151: "sireg", 0x180: "satp",
    0x200: "vsstatus", 0x204: "vsie", 0x205: "vstvec", 0x240: "vsscratch",
    0x241: "vsepc", 0x242: "vscause", 0x243: "vstval", 0x244: "vsip",
    0x24D: "vstimecmp", 0x280: "vsatp",
    0x600: "hstatus", 0x602: "hedeleg", 0x603: "hideleg", 0x604: "hie",
    0x605: "htimedelta", 0x606: "hcounteren", 0x607: "hgeie",
    0x608: "hvien", 0x609: "hvictl", 0x60A: "henvcfg", 0x60C: "hstateen0",
    0x643: "htval", 0x644: "hip", 0x645: "hvip", 0x646: "hviprio1",
    0x647: "hviprio2", 0x64A: "htinst", 0x680: "hgatp", 0xC01: "time",
}
# Never accessed, read or written: the DT contract avoids what they gate.
FORBIDDEN_CSRS = {"hstateen0", "hvictl", "hvien", "hviprio1", "hviprio2"}
# The per-domain CSR set, in the arm helper's word order (mvp.h).
VCSRS = ("vsstatus", "vsie", "vstvec", "vsscratch", "vsepc", "vscause",
         "vstval", "vsatp", "vstimecmp", "scounteren", "senvcfg")
VS_LOADED = ("vsstatus", "vsie", "vstvec", "vsscratch", "vsepc", "vscause",
             "vstval", "vsatp")
# The injection helper's CSRs, in its argument and readback order (mvp.h,
# BE_MVP_INJECT_*): written once per accepted denial (planning/mvp-m1-plan.md,
# "The denial path").
INJECTED = ("vscause", "vstval", "vsepc", "vsstatus")
# Every CSR the monitor writes, and exactly the functions that write it.
CSR_WRITERS = {
    "satp": {R3_RESET},
    "sstatus": {R3_RESET, R3_ENTER, B1_QUIESCE, B1_HALT, MVP_RESUME},
    "stvec": {R3_RESET, B1_QUIESCE},
    "sscratch": {R3_RESET, R3_ENTER, MVP_ARM, MVP_BUDGET, MVP_VECTOR},
    "sepc": {R3_RESET, R3_ENTER, B1_SKIP, MVP_RESUME},
    "scause": {R3_RESET},
    "stval": {R3_RESET},
    "sie": {R3_RESET, R3_UNEXPECTED, R3_HALT, B1_QUIESCE, B1_HALT, MVP_ARM,
            MVP_BUDGET},
    "sip": {B1_QUIESCE, MVP_SSIP},
    "senvcfg": {R3_RESET, MVP_ARM},
    "scounteren": {R3_RESET, MVP_ARM},
    "stimecmp": {B1_QUIESCE, MVP_BUDGET},
    "siselect": {B1_QUIESCE},
    "sireg": {B1_QUIESCE},
    "hstatus": {R3_RESET, MVP_ARM},
    "hedeleg": {R3_RESET, MVP_ARM},
    "hideleg": {R3_RESET, MVP_ARM},
    "hie": {R3_RESET, R3_UNEXPECTED, R3_HALT},
    "hvip": {R3_RESET, R3_UNEXPECTED, R3_HALT},
    "hcounteren": {R3_RESET, MVP_ARM},
    "htimedelta": {R3_RESET},
    "henvcfg": {R3_RESET, MVP_STCE},
    "hgeie": {R3_RESET},
    "htval": {R3_RESET},
    "hgatp": {R3_RESET, R3_INSTALL},
    "vstimecmp": {MVP_ARM, MVP_TIMER},
    "vsip": {R3_RESET},
    **{name: {R3_RESET, MVP_ARM} for name in VS_LOADED},
    **{name: {R3_RESET, MVP_ARM, MVP_INJECT} for name in INJECTED},
}
INSTRUCTION_SITES = {
    "ecall": {R3_SBI: 1},
    "sret": {R3_ENTER: 1, MVP_RESUME: 1, B1_SKIP: 1},
    "hfence.gvma": {R3_RESET: 1, R3_INSTALL: 1},
    "sfence.vma": {R3_RESET: 1},
    "wfi": {R3_UNEXPECTED: 1, R3_HALT: 1, B1_HALT: 1, MVP_WAIT: 1,
            MVP_PARK: 1, MVP_PARK_ENTRY: 1},
    "fence.i": {MVP_FENCE_I: 1},
    "hfence.vvma": {},
    "hlsv": {},
    "mret": {},
    "ebreak": {},
}
NOP = 0x00000013
C_NOP = 0x0001
FENCE_I = 0x0000100F
CSRRW_SP_SSCRATCH_SP = 0x14011173
# beryllium-cheri: CHERI v0.9.3's encodings in src/mvp-trap.S
# (MVP_INSN_MODESW_CAP and _INT; SC and LC by opcode and funct3), and
# the capability frame's offsets in the saved page (CF, CF_MON_DDC).
MODESW_CAP = 0x12001033
MODESW_INT = 0x14001033
CAP_FRAME = 368
CAP_MON_DDC = 880
DDC_CSR = 0x416
CSRRS_CT6_SSCRATCH = 0x14002FF3  # csrrs t6, sscratch, zero
# beryllium-cheri: the vector's restore of sscratchc, csrrw zero, sscratch,
# sp, in Capability Pointer Mode; its bad-stack path's step back below the
# top, addi sp, sp, -16; and the CSRs the CHERI rules name.
CSRW_SSCRATCH_SP = 0x14011073
ADDI_SP_SP_M16 = 0xFF010113
SSCRATCH, SEPC, VSTVEC, VSEPC, VSSTATUS, VSCAUSE, VSTVAL = \
    0x140, 0x141, 0x205, 0x241, 0x200, 0x242, 0x243
# beryllium-cheri: SCADDR and SCBNDSR (.insn r 0x33, 1, 0x06 and 0x07),
# under the mask of an R-type word's funct7, funct3, and opcode.
R_TYPE_MASK, SCADDR_WORD, SCBNDSR_WORD = 0xFE00707F, 0x0C001033, 0x0E001033
SHF_WRITE, SHF_ALLOC, SHF_EXECINSTR = 1, 2, 4
# The accepted R5 checker's section table, without the fixture sections
# (planning/mvp-m6-plan.md, D-4), at the K3 addresses: (address or None,
# size or None, required flags, forbidden flags).
EXPECTED_SECTIONS = {
    ".monitor.text": (BASE, 0xC000, "AX", "W"),
    ".monitor.rodata": (LAYOUT["MONITOR_RODATA_HPA"],
                        LAYOUT["MONITOR_RODATA_BYTES"], "A", "WX"),
    ".monitor.input": (LAYOUT["MONITOR_INPUT_HPA"],
                       LAYOUT["MONITOR_INPUT_BYTES"], "A", "WX"),
    ".monitor.data": (LAYOUT["CONTROL_DATA_HPA"],
                      LAYOUT["CONTROL_DATA_BYTES"], "WA", "X"),
    ".diagnostic": (LAYOUT["DIAGNOSTIC_HPA"], 0x1000, "WA", "X"),
    ".stack.control": (CONTROL_STACK, LAYOUT["CONTROL_STACK_BYTES"], "WA",
                       "X"),
    ".gstage.g0": (LAYOUT["G0_ROOT_HPA"], LAYOUT["GUEST_POOL_BYTES"], "A",
                   "X"),
    ".gstage.g1": (LAYOUT["G1_ROOT_HPA"], LAYOUT["GUEST_POOL_BYTES"], "A",
                   "X"),
    ".published.g0": (LAYOUT["G0_PUBLISHED_HPA"],
                      LAYOUT["PUBLISHED_BYTES"], "A", "X"),
    ".published.g1": (LAYOUT["G1_PUBLISHED_HPA"],
                      LAYOUT["PUBLISHED_BYTES"], "A", "X"),
    ".mailbox.control.g0": (LAYOUT["G0_CONTROL_MAILBOX_HPA"],
                            LAYOUT["CONTROL_MAILBOX_BYTES"], "A", "X"),
    ".mailbox.control.g1": (LAYOUT["G1_CONTROL_MAILBOX_HPA"],
                            LAYOUT["CONTROL_MAILBOX_BYTES"], "A", "X"),
    ".mailbox.hart.g0": (LAYOUT["G0_HART_MAILBOX_HPA"],
                         LAYOUT["HART_MAILBOX_BYTES"], "A", "X"),
    ".mailbox.hart.g1": (LAYOUT["G1_HART_MAILBOX_HPA"],
                         LAYOUT["HART_MAILBOX_BYTES"], "A", "X"),
    ".private.g0": (LAYOUT["G0_BLOCK_HPA"], LAYOUT["BLOCK_BYTES"], "A", "X"),
    ".private.g1": (LAYOUT["G1_BLOCK_HPA"], LAYOUT["BLOCK_BYTES"], "A", "X"),
    ".mvp.text": (REGION, 0x18000, "AX", "W"),
    ".mvp.rodata": (LAYOUT["MVP_BOOT_RODATA_HPA"],
                    LAYOUT["MVP_BOOT_RODATA_BYTES"], "A", "WX"),
    ".mvp.data": (LAYOUT["MVP_BOOT_DATA_HPA"],
                  LAYOUT["REGION_HPA"] + LAYOUT["REGION_BYTES"] -
                  LAYOUT["MVP_BOOT_DATA_HPA"], "WA", "X"),
}
PADDING_SECTIONS = {
    ".control.pad", ".control.tail", ".core.padding",
    ".readpad.g0.1", ".readpad.g0.2", ".readpad.g1.1", ".readpad.g1.2",
}
ALLOCATED_SECTIONS = set(EXPECTED_SECTIONS) | PADDING_SECTIONS
MAP_SECTIONS = tuple(EXPECTED_SECTIONS)
# The frame offsets of the eight trap CSRs (struct be_r4_frame), then the
# four words struct be_mvp_exit adds after the 320-byte frame.
TRAP_CSRS = ("vstvec", "vsepc", "vscause", "vstval", "scause", "sepc",
             "stval", "htval")
FRAME_TRAP_CSRS = 248
FRAME_RESERVED = 312
FRAME_SEPC = 288
EXIT_WORDS = (("hstatus", 320), ("htinst", 328), ("vsatp", 336),
              ("time", 344), ("vsstatus", 352))
HSTATUS_SPV = 0x80
HSTATUS_SPVP = 0x100
# Only boot code may name the G-stage pool, the MVP's.
MVP_POOL_USERS = {MVP_MAIN, "build_gstage"}
# The executor (planning/mvp-m6-plan.md, D-5): the install function's and
# the injection helper's one call site each lie in its functions; in the
# MVP region's text, no other function names a privileged helper.
EXECUTOR_PREFIX = "be_mvp_exec_"
PRIVILEGED_PREFIXES = ("be_mvp_arch_", "be_mvp_probe_arch_", "be_r3_arch_",
                       "be_r3_platform_")
# The executor's install's call sites: each domain hart's (the MVP profile;
# hart 0 installs none since M6, D-3); probe-platform adds the probe
# module's.
INSTALL_CALLERS = [MVP_HART_MAIN]
INSTALL_CALL_SITES = 1
# The executor's injection's one call site, in an image that accepts
# denials: the denial action, deny, or the dispatch it is inlined into.
INJECT_CALLERS = {"deny", MVP_DISPATCH}

# The image profiles (planning/mvp-m0-plan.md, Image checker): the extra
# install callers, the extra hgatp writers, and whether the probe module
# is linked.
PROFILES = {
    "mvp": ((), (), False),
    "probe-platform": ((PROBE_HGATP,), (), True),
    "probe-vmid-distinct": ((), (PROBE_SWITCH,), True),
    "probe-vmid-shared": ((), (PROBE_SWITCH,), True),
    "probe-console-input": ((), (), True),
}
PROBES = tuple(name for name in PROFILES if name != "mvp")
# The VMID images' raw switch: csrw hgatp, a0; csrr a0, hgatp; ret.
PROBE_SWITCH_WORDS = (0x68051073, 0x68002573, 0x00008067)

# What the MVP's helpers write, in order: (CSR, operation, value). A value
# read from memory is ("mem", argument, offset, mask).
ARG_A0, ARG_A1, ARG_A2 = ("arg", "a0"), ("arg", "a1"), ("arg", "a2")
ARG_A3, ARG_A4 = ("arg", "a3"), ("arg", "a4")
HSTATUS_VTW = 0x200000
HSTATUS_CLEARED = 0x700000
SIE_SSIE = 0x2
SIE_STIE = 0x20
HELPER_WRITES = {
    MVP_STCE: [("henvcfg", "w", ("const", 1 << 63))],
    MVP_ARM: [("vstimecmp", "w", ("const", MASK64)),
              ("hedeleg", "w", ("const", 0xB15D)),
              ("hideleg", "w", ("const", 0x40)),
              ("hcounteren", "w", ("const", 0x2)),
              ("hstatus", "c", ("const", HSTATUS_CLEARED)),
              ("sie", "s", ("const", SIE_SSIE)),
              ("sscratch", "w", ARG_A1)] +
             [(name, "w", ("mem", "a2", index * 8, MASK64))
              for index, name in enumerate(VCSRS)],
    MVP_TIMER: [("vstimecmp", "w", ARG_A0)],
    MVP_INJECT: [(name, "w", argument) for name, argument in
                 zip(INJECTED, (ARG_A0, ARG_A1, ARG_A2, ARG_A3))],
    MVP_BUDGET: [("stimecmp", "w", ARG_A0),
                 ("sie", "s", ("const", SIE_SSIE | SIE_STIE)),
                 ("sscratch", "w", ARG_A1)],
    MVP_SSIP: [("sip", "c", ("const", SIE_SSIE))],
    MVP_WAIT: [],
    MVP_PARK: [],
    MVP_TIME: [],
}
# beryllium-cheri: the CHERI-aware monitor's tables (--monitor cheri): ddc,
# CHERI v0.9.3's default data capability, which the vector switches to the
# monitor's and the resume tail back to the guest's; sepc, which the
# injection helper writes too, moving vstvecc into sepcc whole before the
# resume tail sets its address; its armed henvcfg, STCE and CRE; and its
# helpers' writes.
CHERI_CSR_NAMES = {0x416: "ddc"}
CHERI_CSR_WRITERS = {"sepc": CSR_WRITERS["sepc"] | {MVP_INJECT},
                     "ddc": {MVP_VECTOR, MVP_RESUME}}
ARMED_HENVCFG = {"riscv": 1 << 63, "cheri": 1 << 63 | 1 << 28}
CHERI_HELPER_WRITES = {
    **HELPER_WRITES,
    # beryllium-cheri: STCE and CRE.
    MVP_STCE: [("henvcfg", "w", ("const", ARMED_HENVCFG["cheri"]))],
    MVP_ARM: [("vstimecmp", "w", ("const", MASK64)),
              # beryllium-cheri: and cause 28, the CHERI fault.
              ("hedeleg", "w", ("const", 0x1000B15D)),
              ("hideleg", "w", ("const", 0x40)),
              ("hcounteren", "w", ("const", 0x2)),
              ("hstatus", "c", ("const", HSTATUS_CLEARED)),
              ("sie", "s", ("const", SIE_SSIE)),
              ("sscratch", "w", ARG_A1),
              # beryllium-cheri: then sscratchc, ddc at a1, whole
              # (check_sscratchc checks its source too).
              ("sscratch", "w", ARG_A1)] +
             [(name, "w", ("mem", "a2", index * 8, MASK64))
              for index, name in enumerate(VCSRS)],
    # beryllium-cheri: between vstval and vsepc, vsepcc takes sepcc and
    # sepcc vstvecc, whole, in Capability Pointer Mode; then vsepc's
    # integer write sets only vsepcc's address.
    MVP_INJECT: [("vscause", "w", ARG_A0), ("vstval", "w", ARG_A1),
                 ("vsepc", "w", ("csr", "sepc", MASK64)),
                 ("sepc", "w", ("csr", "vstvec", MASK64)),
                 ("vsepc", "w", ARG_A2), ("vsstatus", "w", ARG_A3)],
    MVP_BUDGET: [("stimecmp", "w", ARG_A0),
                 ("sie", "s", ("const", SIE_SSIE | SIE_STIE)),
                 ("sscratch", "w", ARG_A1),
                 # beryllium-cheri: then sscratchc, ddc at a1, whole.
                 ("sscratch", "w", ARG_A1)],
}
# What the helpers that write nothing read, and nothing more.
HELPER_READS = {MVP_WAIT: ["sip", "time"], MVP_PARK: [], MVP_TIME: ["time"],
                MVP_SSIP: ["sip"]}
# The arm helper's readback: struct be_mvp_controls offset -> CSR.
CONTROL_SLOTS = {0: "hip", 8: "hstatus", 16: "hedeleg", 24: "hideleg",
                 32: "hie", 40: "hvip", 48: "hcounteren", 56: "htimedelta",
                 64: "henvcfg", 72: "hgeie", 80: "vstimecmp", 88: "sie",
                 96: "sstatus", 104: "hgatp", 112: "vsatp", 120: "sscratch"}
# The arm helper's set readback: word offset -> CSR (enum be_mvp_vcsr).
VCSR_SLOTS = {index * 8: name for index, name in enumerate(VCSRS)}
# The injection helper's readback: word offset -> CSR (BE_MVP_INJECT_*).
INJECT_SLOTS = {index * 8: name for index, name in enumerate(INJECTED)}

# The guest DT contract (planning/mvp-m0-plan.md, Guest software: B7's
# tree with the MVP model and compatible, and a guest ID after --) and the
# change each DTB variant makes to it, in which domain's DTB.
BOOTARGS = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
GUEST_ID_ARGS = " -- be.guest={}"
ISA_EXTENSIONS = ("i", "m", "a", "c", "zicsr", "zifencei", "zihintpause",
                  "zba", "zbb", "zbs", "sstc", "svade")
# beryllium-cheri: each guest flavour's further extensions, after svade
# (--guest-flavour; tools/gen-dts.py): the CHERI Linux guest's DTBs also
# name Zcherihybrid and Zcheripurecap.
FLAVOUR_EXTENSIONS = {"linux": (),
                      "cheri-linux": ("zcherihybrid", "zcheripurecap")}
DTB_VARIANTS = ("init-exit", "rdcycle", "sbi-time", "hostile")
# The guests whose DTB each DTB variant changes.
DTB_VARIANT_GUESTS = {"init-exit": (1,), "rdcycle": (0,), "sbi-time": (0, 1),
                      "hostile": (0,)}
# The init variant each rdinit= DTB variant names (guest/mvp-init.c): M7-4's
# hostile guest (planning/mvp-m7-plan.md, D-4) among them.
DTB_VARIANT_INITS = {"init-exit": "init-exit", "rdcycle": "init-rdcycle",
                     "hostile": "init-hostile"}
MONITOR_VARIANTS = ("exit-budget", "run-timeout", "ring-full", "hart-start")
# te-poc's two variants (planning/mvp-m1-plan.md, Q11), each its monitor:
# reader-write's root builder, and no-inject without the denial entry.
TE_POC_VARIANTS = ("reader-write", "no-inject")
# beryllium-cheri: the CHERI-aware monitor's te-poc variant (--monitor
# cheri; planning/cheri-enforcement-plan.md, section 6, B2), its monitor:
# channel-cw, whose root builder also sets CW in each channel leaf, which
# the walker refuses at boot. select_variant() adds it, and with the CHERI
# Linux guest, the variants of CHERI_VARIANT_HEDELEG and
# CHERI_DTB_VARIANT_INITS.
CHERI_TE_POC_VARIANTS = ("channel-cw",)
# beryllium-cheri: the CHERI Linux guest's te-poc variant (C3), its monitor:
# cheri-fault-hs, whose arm helper writes this hedeleg, without cause 28,
# the CHERI fault (cheri_variant_check()).
CHERI_VARIANT_HEDELEG = {"cheri-fault-hs": 0xB15D}
# beryllium-cheri: the CHERI Linux guest's te-poc DTB variant (CE-4; B3 and
# B4): cap-store, its monitor te-poc's with its own launch registers and G0's
# DTB te-poc's with rdinit=/init-cap-store before the "--" (tools/gen-dts.py),
# whose init loads the capability-store module. select_variant() adds it.
CHERI_DTB_VARIANT_INITS = {"cap-store": "init-cap-store"}
# anchor's three runtime negatives built here (planning/mvp-m2-plan.md,
# Q10), each its monitor: the page builder's two defects, which the page
# check refuses, and the perturbed expected measurement.
ANCHOR_VARIANTS = ("secret-shared", "response-writable", "wrong-measurement",
                   "no-grant-check")
# M11-7's hostile-monitor images (planning/mvp-m11-plan.md, D-10), anchor's
# monitor with the hook, each its own variant; and their -off copies,
# below, each checked as its variant against anchor-off.
BREACH_VARIANTS = ("breach-g0", "breach-g1", "breach-c")
ANCHOR_VARIANTS += BREACH_VARIANTS
# M7-4's console variant of each scenario (planning/mvp-m7-plan.md, Q4),
# SCENARIO-shell: its monitor the scenario's with console input granted to
# each domain a shell runs in, its only change the MVP core profile's grant
# words, and each such domain's DTB the scenario's with rdinit=/init-shell,
# pinned as mvp-guest-g<g>-SHELL_DTBS[scenario].dtb; the protected domain
# (role prot) keeps its own DTB and has no grant (Q27).
SHELL_DTBS = {"two-guests": "shell", "te-poc": "te-poc-shell",
              "anchor": "anchor-shell"}
CONSOLE_VARIANTS = tuple(f"{name}-shell" for name in SHELL_DTBS)
SHELL_INIT = "/init-shell"
# M9's self-report-flip (planning/mvp-m9-plan.md, D-4): anchor's image with
# one bit of the inert canary flipped after the link.
FLIP_VARIANT = "self-report-flip"
# M11-7's off copies (planning/mvp-m11-plan.md, D-12): each scenario's
# image built without the physical boundary, its monitor its own, which
# must pass the MVP profile itself with no boundary symbol, and its boot
# image the reference's but for the shim and the monitor; shim-rule is
# two-guests-off's, and is checked against it.
OFF_COPIES = {"two-guests-off": "two-guests", "te-poc-off": "te-poc",
              "anchor-off": "anchor"}
# A monitor variant built without the boundary (ring-full's, D-12): the
# variant it copies, checked as that variant against its scenario's off
# copy.
OFF_VARIANTS = {"ring-full-off": "ring-full", "breach-g0-off": "breach-g0",
                "breach-g1-off": "breach-g1", "breach-c-off": "breach-c"}
VARIANTS = ("payload",) + DTB_VARIANTS + MONITOR_VARIANTS + ("shim-rule",) + \
    TE_POC_VARIANTS + ANCHOR_VARIANTS + CONSOLE_VARIANTS + (FLIP_VARIANT,) + \
    tuple(OFF_COPIES) + tuple(OFF_VARIANTS)
# A v2 or v3 scenario's own DTB pair, named for it (tools/gen-dts.py):
# te-poc's and anchor's; guest/pins.txt must pin te-poc's, and anchor's
# once its scenario is checked.
SCENARIO_DTB_VARIANTS = ("te-poc", "anchor")
PINNED_SCENARIO_DTBS = ("te-poc",)
# A scenario with pages names this expectation schema.
EXPECT_PAGES = "be-mvp-expect-v3"
# The channel record's words (struct be_mvp_gstage_channel) and the rights
# a grant's permissions give (mvp-gstage.h, BE_MVP_GSTAGE_RIGHT_*).
CHANNEL_WORDS = ("gpa", "hpa", "bytes", "writer_domain", "reader_domain",
                 "writer_rights", "reader_rights")
RIGHTS = {"read": 1, "write": 2, "execute": 4}
IDENTITY_BYTES = 32
# A page's words (struct be_mvp_gstage_page), its kinds, and the endpoint
# that names no domain (mvp-gstage.h, BE_MVP_PAGE_*); the shared pages and
# the secret's size (src/mvp-layout.h); a SHA-256 digest's size.
PAGE_WORDS = ("gpa", "hpa", "bytes", "kind", "writer", "reader", "rights0",
              "rights1")
PAGE_CHANNEL, PAGE_SECRET, PAGE_NONE = 0, 1, 0xFF
SHARED_PAGES = LAYOUT["SHARED_PAGES_HPA"]
SHARED_PAGES_BYTES = LAYOUT["SHARED_PAGES_BYTES"]
PAGES_MAX = LAYOUT["PAGES_MAX"]
SECRET_BYTES = LAYOUT["SECRET_BYTES"]
DIGEST_BYTES = 32
# A sealed management grant (struct be_mvp_mgmt_grant), and the
# permissions' bits (BE_MVP_MGMT_PAUSE and BE_MVP_MGMT_TERMINATE).
GRANT_WORDS = ("from", "to", "permissions")
MGMT_PERMISSIONS = {"pause": 1, "terminate": 2}
MGMT_GRANTS_MAX = 4
KERNEL_MAGIC2_AT = 0x3B
FDT_MAGIC = 0xD00DFEED


class ImageError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ImageError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def align_up(value, alignment):
    return (value + alignment - 1) // alignment * alignment


# ---------------------------------------------------------- linker script
def strip_comments(text):
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def parse_phdrs(text):
    block = re.search(r"\bPHDRS\s*\{(.*?)\}", text, re.S)
    require(block is not None, "the linker script has no PHDRS")
    phdrs = re.findall(r"(\w+)\s+PT_LOAD\s+FLAGS\((\d+)\)\s*;", block.group(1))
    return [(name, int(flags)) for name, flags in phdrs]


def split_top(text, separator):
    """Split at separator outside parentheses and string literals."""
    parts, depth, quoted, start, index = [], 0, False, 0, 0
    while index < len(text):
        char = text[index]
        if char == '"':
            quoted = not quoted
        elif not quoted and char == "(":
            depth += 1
        elif not quoted and char == ")":
            depth -= 1
        elif not quoted and depth == 0 and text.startswith(separator, index):
            parts.append(text[start:index])
            index += len(separator)
            start = index
            continue
        index += 1
    parts.append(text[start:])
    return parts


def parse_asserts(text):
    """Return the condition conjuncts of every ASSERT(condition, message)."""
    conjuncts = []
    for match in re.finditer(r"\bASSERT\s*\(", text):
        depth, index, quoted = 1, match.end(), False
        while depth:
            require(index < len(text), "unterminated ASSERT")
            char = text[index]
            if char == '"':
                quoted = not quoted
            elif not quoted and char == "(":
                depth += 1
            elif not quoted and char == ")":
                depth -= 1
            index += 1
        body = text[match.end():index - 1]
        parts = split_top(body, ",")
        require(len(parts) == 2, f"ASSERT without one message: {body!r}")
        conjuncts.extend(" ".join(part.split())
                         for part in split_top(parts[0], "&&"))
    return conjuncts


TOKEN = re.compile(r"\s*(0[xX][0-9a-fA-F]+|\d+|[A-Za-z_]\w*|==|<=|>=|[<>()&-])")


def tokenize(expression):
    tokens, index = [], 0
    while index < len(expression):
        match = TOKEN.match(expression, index)
        require(match is not None, f"cannot parse {expression!r}")
        tokens.append(match.group(1))
        index = match.end()
        while index < len(expression) and expression[index].isspace():
            index += 1
    return tokens


def evaluate(conjunct, symbols):
    """Evaluate one ASSERT conjunct: difference CMP difference, or (M11-8)
    DEFINED(symbol) ? difference CMP difference : 1, which holds where the
    image does not define the symbol."""
    guarded = re.fullmatch(r"DEFINED\((\w+)\) \? (.+) : 1", conjunct)
    if guarded:
        if guarded.group(1) not in symbols:
            return True
        conjunct = guarded.group(2)
    tokens = tokenize(conjunct)
    position = 0

    def take():
        nonlocal position
        require(position < len(tokens), f"truncated {conjunct!r}")
        position += 1
        return tokens[position - 1]

    def primary():
        token = take()
        if token == "(":
            value = conjunction()
            require(take() == ")", f"unbalanced {conjunct!r}")
            return value
        if token[0].isdigit():
            return int(token, 0)
        require(symbols.get(token) is not None,
                f"symbol {token} is missing or ambiguous")
        return symbols[token]

    def difference():
        value = primary()
        while position < len(tokens) and tokens[position] == "-":
            take()
            value -= primary()
        return value

    def conjunction():
        value = difference()
        while position < len(tokens) and tokens[position] == "&":
            take()
            value &= difference()
        return value

    left = difference()
    operator = take()
    right = difference()
    require(position == len(tokens), f"trailing tokens in {conjunct!r}")
    outcomes = {"==": left == right, "<=": left <= right, ">=": left >= right,
                "<": left < right, ">": left > right}
    require(operator in outcomes, f"unknown comparison in {conjunct!r}")
    return outcomes[operator]


def mvp_layout(lds_path):
    """The MVP-owned linker script's PHDRS and ASSERT conjuncts
    (planning/mvp-m6-plan.md, D-4): its seven segments, and every
    conjunct, the checker's own (MVP_CONJUNCTS) among them."""
    text = strip_comments(pathlib.Path(lds_path).read_text())
    phdrs = parse_phdrs(text)
    require(phdrs == PHDRS, f"{lds_path}'s PHDRS {phdrs} are not {PHDRS}")
    conjuncts = parse_asserts(text)
    missing = [conjunct for conjunct in MVP_CONJUNCTS
               if conjunct not in conjuncts]
    require(not missing, f"{lds_path} does not assert {missing}")
    return phdrs, conjuncts


# -------------------------------------------------------------------- ELF
class Elf:
    def __init__(self, data):
        require(data[:7] == b"\x7fELF\x02\x01\x01", "not little-endian ELF64")
        e_type, e_machine = struct.unpack_from("<HH", data, 16)
        require(e_type == 2 and e_machine == 243, "not a RISC-V ET_EXEC")
        self.data = data
        self.entry, phoff, shoff = struct.unpack_from("<QQQ", data, 24)
        phentsize, phnum, shentsize, shnum, shstrndx = struct.unpack_from(
            "<HHHHH", data, 54)
        self.segments = []
        self.program_types = []
        # File offsets, for the mutation test: each PT_LOAD's header, each
        # section's header, and each named symbol's entries.
        self.segment_headers = []
        self.section_headers = {}
        self.symbol_entries = {}
        for index in range(phnum):
            (p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz,
             _align) = struct.unpack_from("<IIQQQQQQ", data,
                                          phoff + index * phentsize)
            self.program_types.append(p_type)
            if p_type == 1:  # PT_LOAD
                self.segments.append((p_vaddr, p_paddr, p_offset, p_filesz,
                                      p_memsz, p_flags))
                self.segment_headers.append(phoff + index * phentsize)
        sections = [struct.unpack_from("<IIQQQQIIQQ", data,
                                       shoff + index * shentsize)
                    for index in range(shnum)]
        names = sections[shstrndx][4]
        self.sections = {}
        for index, section in enumerate(sections):
            end = data.index(b"\0", names + section[0])
            name = data[names + section[0]:end].decode()
            self.sections[name] = section
            self.section_headers[name] = shoff + index * shentsize
        self.symbols = {}
        self.functions = []
        self.objects = []
        self.undefined = []
        for section in sections:
            if section[1] != 2:  # SHT_SYMTAB
                continue
            sym_offset, sym_size, sym_link = section[4], section[5], section[6]
            strtab = sections[sym_link][4]
            for entry in range(sym_offset, sym_offset + sym_size, 24):
                st_name, st_info, _, st_shndx, value, size = \
                    struct.unpack_from("<IBBHQQ", data, entry)
                end = data.index(b"\0", strtab + st_name)
                name = data[strtab + st_name:end].decode()
                self.symbol_entries.setdefault(name, []).append(entry)
                if name and st_shndx == 0:
                    self.undefined.append(name)
                if not name or name.startswith("$") or st_shndx == 0:
                    continue
                # A name defined twice (two local statics) is unusable.
                self.symbols[name] = value if self.symbols.get(
                    name, value) == value else None
                if st_info & 0xF == 2 and size:  # STT_FUNC
                    self.functions.append((value, size, name))
                elif st_info & 0xF == 1 and size:  # STT_OBJECT
                    self.objects.append((value, size, name))

    def section_bytes(self, name):
        section = self.sections.get(name)
        if section is None or section[1] == 8:  # absent or SHT_NOBITS
            return b""
        return self.data[section[4]:section[4] + section[5]]

    def architecture(self):
        """Tag_RISCV_arch from .riscv.attributes, or None."""
        attributes = self.section_bytes(".riscv.attributes")
        start = attributes.find(b"rv64")
        if start < 0:
            return None
        return attributes[start:attributes.index(b"\0", start)].decode()


def instructions(flat, start, end, base):
    """Decode [start, end) as RISC-V instructions: [(pc, size, word)]."""
    decoded, pc = [], start
    while pc < end:
        offset = pc - base
        require(0 <= offset and offset + 2 <= len(flat),
                f"instruction at 0x{pc:x} is outside the image")
        half = struct.unpack_from("<H", flat, offset)[0]
        if half & 3 == 3:
            require(pc + 4 <= end, f"instruction at 0x{pc:x} crosses its end")
            decoded.append((pc, 4, struct.unpack_from("<I", flat, offset)[0]))
            pc += 4
        else:
            decoded.append((pc, 2, half))
            pc += 2
    return decoded


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def system_kind(word):
    """Classify one 32-bit SYSTEM-opcode word, or None."""
    if word & 0x707F == FENCE_I:
        return "fence.i"
    if word & 0x7F != 0x73:
        return None
    funct3 = (word >> 12) & 7
    if funct3 == 0:
        if word == 0x00000073:
            return "ecall"
        if word == 0x00100073:
            return "ebreak"
        if word == 0x10200073:
            return "sret"
        if word == 0x30200073:
            return "mret"
        if word == 0x10500073:
            return "wfi"
        funct7 = word >> 25
        if word & 0x7FFF == 0x73 and funct7 == 0x09:
            return "sfence.vma"
        if word & 0x7FFF == 0x73 and funct7 == 0x31:
            return "hfence.gvma"
        if word & 0x7FFF == 0x73 and funct7 == 0x11:
            return "hfence.vvma"
        return "system-other"
    if funct3 == 4:
        return "hlsv"
    return "csr"


def csr_write(word):
    """The CSR number a CSR instruction writes, or None for a pure read."""
    funct3 = (word >> 12) & 7
    source = (word >> 15) & 0x1F
    if funct3 in (1, 5) or source != 0:
        return word >> 20
    return None


def floating_point(word, size):
    """Whether a word is an F, D, or V instruction (RV64 encodings)."""
    if size == 4:
        return word & 0x7F in (0x07, 0x27, 0x43, 0x47, 0x4B, 0x4F, 0x53,
                               0x57)
    quadrant, funct3 = word & 3, (word >> 13) & 7
    return quadrant in (0, 2) and funct3 in (1, 5)


CALLER_SAVED = (1, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 28, 29, 30, 31)


def decode(word, size, pc):
    """The accepted R5 checker's word decoder (tests/r5/check-image.mjs).

    Keys: rd, base and offset (an address formed from a base register),
    value (an auipc result), jump/branch targets, call, stop, indirect,
    narrow, and unknown.
    """
    def field(high, low):
        return (word >> low) & ((1 << (high - low + 1)) - 1)

    if size == 4:
        rd, funct3, base = field(11, 7), field(14, 12), field(19, 15)
        offset = signed(word >> 20, 12)
        opcode = word & 0x7F
        if opcode == 0x17:
            return {"rd": rd, "value": pc + signed(word & 0xFFFFF000, 32)}
        if opcode == 0x37:
            return {"rd": rd}
        if opcode == 0x6F:
            target = pc + signed(field(31, 31) << 20 | field(19, 12) << 12 |
                                 field(20, 20) << 11 | field(30, 21) << 1, 21)
            return {"rd": rd, "jump": target, "call": rd != 0,
                    "stop": rd == 0}
        if opcode == 0x67:
            return {"rd": rd, "base": base, "offset": offset,
                    "indirect": True, "call": rd != 0, "stop": rd == 0}
        if opcode == 0x63:
            return {"branch": pc + signed(field(31, 31) << 12 |
                                          field(7, 7) << 11 |
                                          field(30, 25) << 5 |
                                          field(11, 8) << 1, 13)}
        if opcode == 0x03:
            return {"rd": rd, "base": base, "offset": offset}
        if opcode == 0x23:
            return {"base": base,
                    "offset": signed(field(31, 25) << 5 | field(11, 7), 12)}
        if opcode == 0x2F:
            return {"rd": rd, "base": base, "offset": 0}
        if opcode == 0x13:
            return {"rd": rd, "base": base, "offset": offset} \
                if funct3 == 0 else {"rd": rd}
        if opcode == 0x1B:
            return {"rd": rd, "base": base, "offset": offset,
                    "narrow": True} if funct3 == 0 else {"rd": rd}
        if opcode in (0x33, 0x3B):
            return {"rd": rd}
        if opcode == 0x0F:
            return {}
        if opcode == 0x73:
            if funct3 == 0:
                return {"call": word == 0x73,
                        "stop": word in (0x10200073, 0x30200073)}
            return {"rd": rd}
        return {"unknown": True}
    rd, rs2 = field(11, 7), field(6, 2)
    rdc, rs1c = 8 + field(4, 2), 8 + field(9, 7)
    scaled4 = field(12, 10) << 3 | field(6, 6) << 2 | field(5, 5) << 6
    scaled8 = field(12, 10) << 3 | field(6, 5) << 6
    kind = (word & 3) << 3 | field(15, 13)
    if kind == 0:
        return {"rd": rdc, "base": 2, "offset": field(10, 7) << 6 |
                field(12, 11) << 4 | field(5, 5) << 3 | field(6, 6) << 2} \
            if word else {"unknown": True}
    if kind == 2:
        return {"rd": rdc, "base": rs1c, "offset": scaled4}
    if kind == 3:
        return {"rd": rdc, "base": rs1c, "offset": scaled8}
    if kind == 6:
        return {"base": rs1c, "offset": scaled4}
    if kind == 7:
        return {"base": rs1c, "offset": scaled8}
    if kind == 8:
        return {"rd": rd, "base": rd,
                "offset": signed(field(12, 12) << 5 | rs2, 6)} if rd else {}
    if kind == 9:
        return {"rd": rd, "base": rd,
                "offset": signed(field(12, 12) << 5 | rs2, 6), "narrow": True}
    if kind in (10, 16):
        return {"rd": rd}
    if kind == 11:
        if rd == 2:
            return {"rd": rd, "base": rd, "offset": signed(
                field(12, 12) << 9 | field(4, 3) << 7 | field(5, 5) << 6 |
                field(2, 2) << 5 | field(6, 6) << 4, 10)}
        return {"rd": rd}
    if kind == 12:
        return {"rd": rs1c}
    if kind == 13:
        return {"jump": pc + signed(field(12, 12) << 11 | field(11, 11) << 4 |
                                    field(10, 9) << 8 | field(8, 8) << 10 |
                                    field(7, 7) << 6 | field(6, 6) << 7 |
                                    field(5, 3) << 1 | field(2, 2) << 5, 12),
                "stop": True}
    if kind in (14, 15):
        return {"branch": pc + signed(field(12, 12) << 8 |
                                      field(11, 10) << 3 |
                                      field(6, 5) << 6 | field(4, 3) << 1 |
                                      field(2, 2) << 5, 9)}
    if kind == 18:
        return {"rd": rd, "base": 2, "offset": field(12, 12) << 5 |
                field(6, 4) << 2 | field(3, 2) << 6}
    if kind == 19:
        return {"rd": rd, "base": 2, "offset": field(12, 12) << 5 |
                field(6, 5) << 3 | field(4, 2) << 6}
    if kind == 20:
        if rs2:
            return {"rd": rd} if field(12, 12) else \
                {"rd": rd, "base": rs2, "offset": 0}
        if not rd:
            return {}
        if field(12, 12):
            return {"rd": 1, "base": rd, "offset": 0, "indirect": True,
                    "call": True}
        return {"base": rd, "offset": 0, "indirect": True, "stop": True}
    if kind == 22:
        return {"base": 2, "offset": field(12, 9) << 2 | field(8, 7) << 6}
    if kind == 23:
        return {"base": 2, "offset": field(12, 10) << 3 | field(9, 7) << 6}
    return {"unknown": True}


def references(decoded, owner="function"):
    """Every jal target and auipc-formed address: [(pc, target, link)].

    An auipc result is tracked per register along every path through the
    function, to a fixed point, until the register is written or a call
    clobbers it; where paths join, a register keeps a result only if every
    path into the join brings the same one (Clang keeps a symbol's address
    in a callee-saved register across a loop). An instruction no path
    reaches starts from nothing known. An auipc whose result is never used
    as a base while tracked fails closed: a reference this decoding cannot
    see is rejected rather than missed.
    """
    insns = [(pc, decode(word, size, pc)) for pc, size, word in decoded]
    at = {pc: index for index, (pc, _) in enumerate(insns)}

    def successors(index):
        insn = insns[index][1]
        target = insn.get("branch", insn.get("jump"))
        following = [index + 1] if index + 1 < len(insns) else []
        if insn.get("branch") is not None:
            return following + ([at[target]] if target in at else [])
        if insn.get("call"):
            return following
        if insn.get("stop"):
            return [at[target]] if target in at else []
        return following

    def step(state, pc, insn, found, used):
        if insn.get("jump") is not None:
            found.append((pc, insn["jump"], insn.get("rd", 0)))
        base = insn.get("base")
        if base in state:
            origin, value = state[base]
            used.add(origin)
            address = value + insn["offset"]
            if insn.get("narrow"):
                address = signed(address & 0xFFFFFFFF, 32)
            if insn.get("indirect"):
                address &= ~1
            found.append((pc, address & 0xFFFFFFFFFFFFFFFF,
                          insn.get("rd", 0) if insn.get("indirect")
                          else None))
        if insn.get("unknown"):
            state.clear()
        state.pop(insn.get("rd"), None)
        if insn.get("call"):
            for register in CALLER_SAVED:
                state.pop(register, None)
        if insn.get("value") is not None and insn.get("rd"):
            state[insn["rd"]] = (pc, insn["value"])

    entry = [None] * len(insns)
    for root in range(len(insns)):
        if entry[root] is not None:
            continue
        entry[root] = {}
        work = [root]
        while work:
            index = work.pop()
            state = dict(entry[index])
            step(state, *insns[index], [], set())
            for following in successors(index):
                if entry[following] is None:
                    merged = dict(state)
                else:
                    merged = {register: value for register, value in
                              entry[following].items()
                              if state.get(register) == value}
                if merged != entry[following]:
                    entry[following] = merged
                    work.append(following)
    found, used = [], set()
    for index, (pc, insn) in enumerate(insns):
        step(dict(entry[index]), pc, insn, found, used)
    pending = [pc for pc, insn in insns
               if insn.get("value") is not None and insn.get("rd") and
               pc not in used]
    require(not pending,
            f"auipc at {', '.join(hex(pc) for pc in sorted(pending))} in "
            f"{owner} is not used as a base while its result is known")
    return found


def function_map(elf, start, end):
    """Function symbols inside [start, end), merged by identical extent."""
    extents = {}
    for value, size, name in elf.functions:
        if start <= value < end:
            require(value + size <= end,
                    f"function {name} leaves its code extent")
            extents.setdefault((value, size), []).append(name)
    ordered = sorted(extents.items())
    for (left, right) in zip(ordered, ordered[1:]):
        require(left[0][0] + left[0][1] <= right[0][0],
                f"functions {left[1]} and {right[1]} overlap")
    return [(value, size, sorted(names)) for (value, size), names in ordered]


def check_padding_words(flat, base, start, end):
    for pc, size, word in instructions(flat, start, end, base):
        require((size == 4 and word == NOP) or
                (size == 2 and word in (C_NOP, 0)),
                f"instruction 0x{word:x} at 0x{pc:x} is outside every "
                f"function")


def check_padding(flat, base, start, end, constants=()):
    cursor = start
    for low, high in sorted(constants):
        if high <= cursor or low >= end:
            continue
        check_padding_words(flat, base, cursor, max(cursor, low))
        cursor = max(cursor, high)
    check_padding_words(flat, base, cursor, end)


# ----------------------------------------------------- value tracking
def track(decoded, preserve_at_joins=()):
    """Constant and CSR-value tracking over the MVP's straight-line assembly.

    A register holds ("const", n), ("csr", name, mask), ("arg", "a0") to
    ("arg", "a4") (the incoming arguments), a doubleword
    loaded from an argument, ("mem", argument, offset, mask), or nothing
    known. Returns
    (writes, reads, checks, stores): CSR writes [(index, csr, op, value)]
    with op w, s, or c; CSR reads [(index, csr)]; conditional branches on
    a tracked value [(index, kind, subject, mask, value)], kind "eq" when
    falling through requires equality (bne) and "ne" when it requires
    inequality (beq); and doubleword stores [(index, base, offset, value)].
    State is dropped at every jump or branch target and after any call or
    stop, so a join never carries a value it might not hold. A caller may
    name registers whose value it separately requires to be invariant
    across every branch to a join.
    """
    joins = set()
    for pc, size, word in decoded:
        insn = decode(word, size, pc)
        for key in ("jump", "branch"):
            if insn.get(key) is not None:
                joins.add(insn[key])
    initial = {0: ("const", 0), 10: ARG_A0, 11: ARG_A1, 12: ARG_A2,
               13: ARG_A3, 14: ARG_A4}
    regs = dict(initial)
    writes, reads, checks, stores = [], [], [], []
    for index, (pc, size, word) in enumerate(decoded):
        if pc in joins:
            regs = {register: regs[register]
                    for register in (0, *preserve_at_joins)
                    if register in regs}
        if size != 4:
            regs = {0: ("const", 0)}
            continue
        opcode, rd = word & 0x7F, (word >> 7) & 0x1F
        funct3, rs1, rs2 = (word >> 12) & 7, (word >> 15) & 0x1F, \
            (word >> 20) & 0x1F
        imm = signed(word >> 20, 12)
        result, writes_rd = None, True
        a, b = regs.get(rs1), regs.get(rs2)
        if opcode == 0x37:
            result = ("const", signed(word & 0xFFFFF000, 32) & MASK64)
        elif opcode == 0x17:
            result = ("const", (pc + signed(word & 0xFFFFF000, 32)) & MASK64)
        elif opcode == 0x03:
            if funct3 == 3 and a and a[0] == "arg":
                result = ("mem", a[1], imm, MASK64)
        elif opcode == 0x13:
            if funct3 == 0 and a and a[0] == "const":
                result = ("const", (a[1] + imm) & MASK64)
            elif funct3 == 0 and imm == 0:
                result = a
            elif funct3 == 7 and a and a[0] == "const":
                result = ("const", a[1] & imm & MASK64)
            elif funct3 == 7 and a and a[0] == "csr":
                result = ("csr", a[1], a[2] & imm & MASK64)
            elif funct3 == 7 and a and a[0] == "mem":
                result = ("mem", a[1], a[2], a[3] & imm & MASK64)
            elif funct3 == 1 and word >> 26 == 0 and a and a[0] == "const":
                result = ("const", (a[1] << ((word >> 20) & 0x3F)) & MASK64)
        elif opcode == 0x1B:
            if funct3 == 0 and a and a[0] == "const":
                result = ("const",
                          signed((a[1] + imm) & 0xFFFFFFFF, 32) & MASK64)
        elif opcode == 0x33:
            if funct3 == 7 and word >> 25 == 0:
                for x, y in ((a, b), (b, a)):
                    if x and y and x[0] == "csr" and y[0] == "const":
                        result = ("csr", x[1], x[2] & y[1])
            # beryllium-cheri: SCADDR's result has rs2's value as its
            # address, and SCBNDSR's keeps rs1's; a capability's tracked
            # value is its address.
            elif MONITOR == "cheri" and funct3 == 1 and word >> 25 == 0x06:
                result = b
            elif MONITOR == "cheri" and funct3 == 1 and word >> 25 == 0x07:
                result = a
        elif opcode == 0x73 and funct3 not in (0, 4):
            csr = CSR_NAMES.get(word >> 20, f"0x{word >> 20:x}")
            operation = {1: "w", 2: "s", 3: "c"}[funct3 & 3]
            value = ("const", rs1) if funct3 >= 5 else a
            if funct3 in (1, 5) or rs1 != 0:
                writes.append((index, csr, operation, value))
            if rd != 0 or funct3 not in (1, 5):
                reads.append((index, csr))
            result = ("csr", csr, MASK64)
        elif opcode == 0x63:
            writes_rd = False
            kind = {0: "ne", 1: "eq"}.get(funct3)
            for x, y in ((a, b), (b, a)):
                if kind and x and y and x[0] in ("csr", "arg") and \
                        y[0] in ("const", "arg", "mem") and x != y:
                    subject = x[1] if x[0] == "csr" else f"arg:{x[1]}"
                    mask = x[2] if x[0] == "csr" else MASK64
                    value = y[1] if y[0] == "const" else \
                        f"arg:{y[1]}" if y[0] == "arg" else \
                        f"mem:{y[1]}+{y[2]}&0x{y[3]:x}"
                    checks.append((index, kind, subject, mask, value))
                    break
        elif opcode == 0x23:
            writes_rd = False
            if funct3 == 3:
                stores.append((index, a, signed((word >> 25) << 5 |
                                                (word >> 7) & 0x1F, 12), b))
        elif opcode in (0x6F, 0x67):
            regs = {0: ("const", 0)} if rd == 0 else {
                register: value for register, value in regs.items()
                if register not in CALLER_SAVED}
        elif opcode == 0x73 and word in (0x10200073, 0x30200073):
            regs = {0: ("const", 0)}
            writes_rd = False
        if writes_rd and rd != 0 and opcode not in (0x6F, 0x67):
            if result is None:
                regs.pop(rd, None)
            else:
                regs[rd] = result
    return writes, reads, checks, stores


def function_words(elf, flat, name, base):
    """The decoded instructions of one named function."""
    found = [(value, size) for value, size, label in elf.functions
             if label == name]
    require(len(found) == 1, f"{name} is not one function")
    return instructions(flat, found[0][0], found[0][0] + found[0][1], base)


def check_sscratchc(name, decoded):
    """beryllium-cheri: the helper's sscratchc is the monitor's ddc with its
    address set to the incoming a1 (SCADDR rd, rs1, a1, rs1 read from
    ddc), written whole in Capability Pointer Mode; nothing writes a1
    before it, nor its result's register before the write. rs1's last
    write before the SCADDR is the ddc read (F4 of the CHERI rules'
    review)."""
    words = [word for _, _, word in decoded]
    for index, word in enumerate(words):
        if word & 0xFE00707F != 0x0C001033 or (word >> 20) & 0x1F != 11:
            continue
        source, result = (word >> 15) & 0x1F, (word >> 7) & 0x1F
        writers = [earlier for earlier in words[:index]
                   if writes_register(earlier, source)]
        require(writers and ddc_access(writers[-1]) == ("read", source),
                f"{name} takes SCADDR's base, x{source}, from other than "
                f"its ddc read")
        if any((earlier & 0x7F) not in (0x23, 0x63) and
               (earlier >> 7) & 0x1F == 11 for earlier in words[:index]):
            continue
        write = (0x140 << 20) | (result << 15) | (1 << 12) | 0x73
        for later in range(index + 1, len(words)):
            if words[later] == write:
                if MODESW_CAP in words[index + 1:later] and \
                        MODESW_INT not in words[words.index(
                            MODESW_CAP, index + 1):later]:
                    return
                break
            if (words[later] & 0x7F) not in (0x23, 0x63) and \
                    (words[later] >> 7) & 0x1F == result:
                break
    require(False, f"{name} does not write sscratchc whole as ddc at a1")


def check_cheri_helper(name, decoded):
    """beryllium-cheri: a CHERI helper (arm, budget, inject) holds no
    compressed instruction, as the trap entry and the resume tail hold
    none, since its rules scan 32-bit words (F4 of the CHERI rules'
    review); and it enters Capability Pointer Mode once and then returns
    to Integer Pointer Mode once (F3, and its kin in arm and budget)."""
    require(all(size == 4 for _, size, _ in decoded),
            f"{name} holds a compressed instruction")
    words = [word for _, _, word in decoded]
    require(words.count(MODESW_CAP) == 1 and words.count(MODESW_INT) == 1
            and words.index(MODESW_CAP) < words.index(MODESW_INT),
            f"{name} does not enter Capability Pointer Mode once and then "
            f"return to Integer Pointer Mode once")


def check_frame_clear(name, decoded):
    """beryllium-cheri: the arm helper nulls the capability frame, SC of x0
    at CAP_FRAME + 16k through a1 for k = 0 to 32, each once, before it
    enters Capability Pointer Mode and before its three SCs through t1
    fill the frame (F5 of the CHERI rules' review)."""
    words = [word for _, _, word in decoded]
    clears = [index for index, value in enumerate(words)
              if sc_fields(value) is not None and
              sc_fields(value)[:2] == (0, 11)]
    fills = [index for index, value in enumerate(words)
             if sc_fields(value) is not None and sc_fields(value)[1] == 6]
    require(sorted(sc_fields(words[index])[2] for index in clears) ==
            [CAP_FRAME + 16 * slot for slot in range(33)] and
            max(clears) < words.index(MODESW_CAP) and len(fills) == 3 and
            max(clears) < min(fills),
            f"{name} does not null the capability frame, CAP_FRAME + 16k "
            f"through a1 for k = 0 to 32, before Capability Pointer Mode "
            f"and the frame's fill")


def check_frame_fill(name, decoded):
    """beryllium-cheri: what the arm helper stores through sscratchc's
    capability (T5 of the CHERI rules' review, its r5). The helper accesses
    ddc once, by a read. It makes exactly three SCs through the register
    that its last write of sscratch takes: at CAP_MON_DDC, at CAP_FRAME
    (slot 0), and at CAP_FRAME + 16 * 11 (slot 11, a1's). Nothing writes
    the ddc read's register from the read to the value's last use. The
    stores at CAP_MON_DDC and in slot 0 take that register. Slot 11's takes
    the device tree's capability: an SCBNDSR whose bounds register holds
    BE_MVP_DTB_BYTES, of an SCADDR of the ddc read's register whose address
    register holds BE_MVP_DTB_GPA. Every source is its operand's nearest
    earlier writer, and each constant is evaluated from the words that
    materialize it (materialized()), against mvp-layout.h's values."""
    words = [word for _, _, word in decoded]
    access = [index for index, value in enumerate(words)
              if csr_number(value) == DDC_CSR]
    require(len(access) == 1 and ddc_access(words[access[0]]) is not None
            and ddc_access(words[access[0]])[0] == "read",
            f"{name} does not access ddc exactly once, by a read")
    read_at, held = access[0], ddc_access(words[access[0]])[1]
    sscratch = [index for index, value in enumerate(words)
                if writes_csr(value, SSCRATCH)]
    top = nearest_writer(words, sscratch[-1],
                         (words[sscratch[-1]] >> 15) & 0x1F) \
        if sscratch else None
    through = {}
    for index, value in enumerate(words):
        fields = sc_fields(value)
        if top is not None and fields is not None and \
                nearest_writer(words, index, fields[1]) == top:
            through.setdefault(fields[2], []).append(index)
    slots = (CAP_MON_DDC, CAP_FRAME, CAP_FRAME + 16 * 11)
    require(sorted(through) == sorted(slots) and
            all(len(through[slot]) == 1 for slot in slots),
            f"{name} does not make exactly three stores through sscratchc's "
            f"capability, at CF_MON_DDC, CF, and CF + 16 * 11")
    monitor_at, guest_at, dtb_at = (through[slot][0] for slot in slots)
    bound_at = nearest_writer(words, dtb_at, sc_fields(words[dtb_at])[0])
    bound = words[bound_at] if bound_at is not None else 0
    address_at = nearest_writer(words, bound_at, (bound >> 15) & 0x1F) \
        if bound & R_TYPE_MASK == SCBNDSR_WORD else None
    address = words[address_at] if address_at is not None else 0
    last_use = max([monitor_at, guest_at] +
                   ([address_at] if address & R_TYPE_MASK == SCADDR_WORD
                    else []))
    require(not any(writes_register(words[at], held)
                    for at in range(read_at + 1, last_use)),
            f"{name} writes its ddc read's register, x{held}, before the "
            f"value's last use")
    require(all(nearest_writer(words, at, sc_fields(words[at])[0]) ==
                read_at for at in (monitor_at, guest_at)),
            f"{name} does not store its ddc read's register at CF_MON_DDC "
            f"and in slot 0")
    require(bound & R_TYPE_MASK == SCBNDSR_WORD and
            address & R_TYPE_MASK == SCADDR_WORD and
            nearest_writer(words, address_at, (address >> 15) & 0x1F) ==
            read_at and
            materialized(words, address_at, (address >> 20) & 0x1F) ==
            LAYOUT["DTB_GPA"] and
            materialized(words, bound_at, (bound >> 20) & 0x1F) == DTB_BYTES,
            f"{name} does not store in slot 11 the device tree's capability, "
            f"its ddc read at BE_MVP_DTB_GPA bounded to BE_MVP_DTB_BYTES")


def check_inject_moves(name, decoded):
    """beryllium-cheri: between the injection helper's one entry into
    Capability Pointer Mode and its one return lie exactly its four
    capability moves, sepcc to vsepcc and vstvecc to sepcc, each a whole
    read and a whole write through one register; vsepc's and vsstatus's
    integer writes, from a2 and a3, and the four readbacks all follow the
    return (F3 of the CHERI rules' review)."""
    words = [word for _, _, word in decoded]
    enter, leave = words.index(MODESW_CAP), words.index(MODESW_INT)
    moves = words[enter + 1:leave]
    held = [csr_read_whole(moves[0], SEPC), csr_read_whole(moves[2], VSTVEC)] \
        if len(moves) == 4 else [None, None]
    readbacks = [index for index, value in enumerate(words)
                 if any(csr_read_whole(value, csr) is not None
                        for csr in (VSCAUSE, VSTVAL, VSEPC, VSSTATUS))]
    require(None not in held and
            moves[1] == csr_write_word(VSEPC, held[0]) and
            moves[3] == csr_write_word(SEPC, held[1]) and
            csr_write_word(VSEPC, 12) in words[leave + 1:] and
            csr_write_word(VSSTATUS, 13) in words[leave + 1:] and
            len(readbacks) == 4 and min(readbacks) > leave,
            f"{name} does not make exactly its four capability moves, "
            f"sepcc to vsepcc and vstvecc to sepcc, in Capability Pointer "
            f"Mode, with vsepc's and vsstatus's integer writes and the "
            f"readbacks after it")


def check_tick_deadline(name, decoded):
    """One time read plus BE_MVP_TICK_TICKS written to stimecmp."""
    words = [word for _, _, word in decoded]
    writes = [index for index, word in enumerate(words)
              if csr_number(word) == 0x14D and
              (word >> 12) & 7 == 1]
    require(len(writes) == 1, f"{name} has {len(writes)} stimecmp writes")
    write = writes[0]
    result = (words[write] >> 15) & 0x1F
    add = nearest_writer(words, write, result)
    require(add is not None and words[add] & 0xFE00707F == 0x00000033,
            f"{name} does not add time and the tick period")
    sources = ((words[add] >> 15) & 0x1F, (words[add] >> 20) & 0x1F)
    constant = [register for register in sources
                if materialized(words, add, register) ==
                LAYOUT["TICK_TICKS"]]
    timers = []
    for register in sources:
        at = nearest_writer(words, add, register)
        if at is not None and csr_number(words[at]) == 0xC01 and \
                (words[at] >> 12) & 7 == 2 and \
                (words[at] >> 15) & 0x1F == 0:
            timers.append(register)
    require(len(constant) == 1 and len(timers) == 1 and
            constant[0] != timers[0],
            f"{name} does not write time + 0x{LAYOUT['TICK_TICKS']:x}")


def check_helpers(elf, flat, base, symbols, profile):
    """The values the MVP's helpers write, and what they read back."""
    helper_writes = dict(HELPER_WRITES)
    helper_reads = dict(HELPER_READS)
    if profile == "mvp":
        helper_writes[MVP_ARM] = [
            (csr, operation,
             ("const", SIE_SSIE | SIE_STIE)
             if csr == "sie" else value)
            for csr, operation, value in helper_writes[MVP_ARM]]
        helper_writes[MVP_TICK] = [("stimecmp", "w", None)]
        helper_writes[MVP_PARK] = [("stimecmp", "w", None)]
        helper_reads[MVP_TICK] = ["time"]
        helper_reads.pop(MVP_PARK, None)
    if MONITOR == "cheri":
        # beryllium-cheri: the CHERI helpers' own rules and their
        # sscratchc first; after the values each helper writes, the arm
        # helper's frame and the injection's moves (below).
        for name in (MVP_ARM, MVP_BUDGET, MVP_INJECT):
            check_cheri_helper(name, function_words(elf, flat, name, base))
        for name in (MVP_ARM, MVP_BUDGET):
            check_sscratchc(name, function_words(elf, flat, name, base))
    for name, expected in helper_writes.items():
        decoded = function_words(elf, flat, name, base)
        writes, reads, _, stores = track(decoded)
        actual = [(csr, operation, value) for _, csr, operation, value
                  in writes]
        for (csr, operation, value), wanted in zip(actual, expected):
            require((csr, operation) == wanted[:2] and value == wanted[2],
                    f"{name}: {csr} written as {value!r}, expected "
                    f"{wanted[2]!r}")
        require(actual == expected,
                f"{name} writes {actual}, expected {expected}")
        if profile == "mvp" and name in (MVP_TICK, MVP_PARK):
            require([csr for _, csr in reads] == ["time"],
                    f"{name} reads {reads}, expected time only")
            check_tick_deadline(name, decoded)
        slots = {offset: value[1] for _, base_value, offset, value in stores
                 if base_value == ARG_A0 and value and value[0] == "csr" and
                 value[2] == MASK64}
        if name in helper_reads:
            require([csr for _, csr in reads] == helper_reads[name] and
                    not stores,
                    f"{name} reads {reads} or stores {stores}, expected "
                    f"{helper_reads[name]} only")
        if name == MVP_INJECT:
            inject_slots = {offset: value[1] for _, base_value, offset, value
                            in stores if base_value == ARG_A4 and value and
                            value[0] == "csr" and value[2] == MASK64}
            if MONITOR == "cheri":
                # beryllium-cheri: sepcc and vstvecc are read, whole, for the
                # capability moves; the four readbacks follow every write.
                moves = [csr for _, csr in reads][:2]
                reads = reads[2:]
                require(moves == ["sepc", "vstvec"],
                        f"{name} reads {moves} for its capability moves, "
                        f"expected sepc and vstvec")
            require([csr for _, csr in reads] == list(INJECTED) and
                    max(index for index, _, _, _ in writes) <
                    min(index for index, _ in reads) and
                    inject_slots == INJECT_SLOTS and
                    len(stores) == len(INJECT_SLOTS),
                    f"{name} reads back {sorted(inject_slots.items())} "
                    f"(reads {[csr for _, csr in reads]}), expected each of "
                    f"{list(INJECTED)} after the writes, into "
                    f"{sorted(INJECT_SLOTS.items())}")
        if name != MVP_ARM:
            continue
        require(slots == CONTROL_SLOTS,
                f"{name} reads back {sorted(slots.items())}, expected "
                f"{sorted(CONTROL_SLOTS.items())}")
        set_slots = {offset: value[1] for _, base_value, offset, value in
                     stores if base_value == ARG_A3 and value and
                     value[0] == "csr" and value[2] == MASK64}
        require(set_slots == VCSR_SLOTS and
                len(stores) == len(CONTROL_SLOTS) + len(VCSRS),
                f"{name} reads the set back as {sorted(set_slots.items())}, "
                f"expected {sorted(VCSR_SLOTS.items())}")
        order = {csr: index for index, csr, _, _ in reversed(writes)}
        first_read = {csr: index for index, csr in reversed(reads)}
        require(order["vstimecmp"] < first_read["hip"] < order["hideleg"],
                f"{name} does not disarm vstimecmp, then read hip, before "
                f"delegating VSTI")
    if MONITOR == "cheri":
        # beryllium-cheri: the arm helper's frame (F5) and what it stores
        # there (T5), and the injection's moves (F3), after the values the
        # helpers write.
        check_frame_clear(MVP_ARM, function_words(elf, flat, MVP_ARM, base))
        check_frame_fill(MVP_ARM, function_words(elf, flat, MVP_ARM, base))
        check_inject_moves(MVP_INJECT,
                           function_words(elf, flat, MVP_INJECT, base))


def check_instructions(elf, flat, base, extents, symbols, profile="mvp",
                       inject_sites=0, boundary=False, breach_map=None,
                       scenario_kind=(False, False), breach_role=None):
    """The ecall/sret/fence/CSR rules over the monitor's code: the accepted
    code extent and the MVP region's text, each [start, end); the injection
    helper with inject_sites call sites (1 in an image that accepts
    denials, else 0); in a boundary-on image (M11-7) its stub and
    extension calls (check_boundary_code()), and (M11-8) its constants and
    placement (check_role_constants(), SCENARIO_KIND its scenario's
    (management, pages)); and in a breach image (M11-7, BREACH_MAP its link map) its
    hook's sites, writers, instructions, and calls (check_breach_code(), by
    its BREACH_ROLE, M11-8)."""
    require(not boundary or profile == "mvp",
            f"a boundary-on image of profile {profile}: only an MVP "
            f"scenario image has the control role whose rules the "
            f"boundary needs")
    install_extra, hgatp_extra, _ = PROFILES[profile]
    if profile == "mvp":
        require("be_mvp_send_ipi" not in symbols and
                "be_mvp_exec_send_ipi" not in symbols,
                "a scenario image retains an IPI send call")
    csr_writers = dict(CSR_WRITERS)
    csr_writers["hgatp"] = CSR_WRITERS["hgatp"] | set(hgatp_extra)
    if profile == "mvp":
        csr_writers["stimecmp"] = CSR_WRITERS["stimecmp"] | {
            MVP_TICK, MVP_PARK}
    install_callers = INSTALL_CALLERS + list(install_extra)
    expected_sites = {kind: dict(owners)
                      for kind, owners in INSTRUCTION_SITES.items()}
    if breach_map is not None:
        for kind, owners in BREACH_SITES.items():
            expected_sites[kind].update(owners)
        for name, owners in BREACH_WRITERS.items():
            csr_writers[name] = csr_writers[name] | owners
    sites = {kind: {} for kind in INSTRUCTION_SITES}
    writers = {}
    kinds = {}
    decoded_all = []
    constant_ranges = tuple(
        (symbols[start], symbols[end]) for start, end in (
            ("__be_monitor_shared_constants_start",
             "__be_monitor_shared_constants_end"),
            ("__be_mvp_control_constants_start",
             "__be_mvp_control_constants_end"),
            ("__be_mvp_domain_constants_start",
             "__be_mvp_domain_constants_end"))
        if start in symbols and end in symbols)
    functions = []
    for code_start, code_end in extents:
        extent = function_map(elf, code_start, code_end)
        require(extent, f"no function symbols in 0x{code_start:x}-"
                f"0x{code_end:x}")
        functions += extent
        decoded_all += scan_functions(elf, flat, base, code_start, code_end,
                                      extent, sites, writers, csr_writers,
                                      constant_ranges, kinds)
    if boundary:
        # M11-8: the control hart's confined entry's seven words first, so
        # that a defect in them is reported as C2's or C14's, not as a rule
        # that its changed call or stack would also break.
        check_control_entry(dict(decoded_all)[CONTROL_ENTRY], symbols)
    if breach_map is not None:
        check_breach_kinds(kinds)
    check_sites(sites, writers, csr_writers, expected_sites)
    found = check_references(functions, decoded_all, symbols, install_extra,
                             install_callers, inject_sites, boundary)
    nodes = role_nodes(functions, decoded_all)
    check_domain_reach(elf, functions, found, symbols, profile)
    _, domain = check_role_reach(
        elf, functions, decoded_all, symbols, DOMAIN_ROOTS,
        DOMAIN_CODE_EXTENTS,
        DOMAIN_REFERENCE_EXTENTS if profile == "mvp"
        else PROBE_REFERENCE_EXTENTS,
        "VS-domain-hart", nodes)
    if profile == "mvp":
        control = check_control_reach(elf, functions, decoded_all, symbols,
                                      nodes, boundary)
    # M11-7: after the role rules, so that each of their defects is still
    # reported as theirs.
    if boundary:
        check_boundary_code(functions, decoded_all, found, symbols, nodes,
                            control)
        # M11-8: the constants and placement rules, after the code's.
        check_role_constants(elf, flat, nodes, control, domain, symbols,
                             scenario_kind)
    if breach_map is not None:
        check_breach_code(functions, found, symbols, breach_map,
                          breach_role, boundary)
    check_canary(elf, flat, base, found, symbols)
    by_name = {owner: decoded for owner, decoded in decoded_all}
    # beryllium-cheri: the monitor variant's trap entry and resume tail.
    cheri = MONITOR == "cheri"
    (check_trap_entry_cheri if cheri else check_trap_entry)(
        by_name[MVP_VECTOR], symbols)
    resume = [(value, size) for value, size, names in functions
              if MVP_RESUME in names][0]
    (check_resume_cheri if cheri else check_resume)(
        by_name[MVP_RESUME], symbols, resume[0], resume[0] + resume[1],
        profile)
    check_hart_entry(by_name[MVP_ENTRY], symbols)
    check_helpers(elf, flat, base, symbols, profile)
    if hgatp_extra:
        require([word for _, _, word in by_name[PROBE_SWITCH]] ==
                list(PROBE_SWITCH_WORDS),
                f"{PROBE_SWITCH} is not the raw write, its readback, and "
                f"its return")
    total = sum(len(decoded) for _, decoded in decoded_all)
    return len(functions), total


def breach_kind(word, width):
    """A breach image's hook's own instruction (BREACH_KINDS), or None: an
    AMO, LR, or SC; a cache-block operation; or a jalr whose link is not
    ra or zero."""
    if width != 4:
        return None
    opcode = word & 0x7F
    if opcode == 0x2F:
        return {0x02: "lr", 0x03: "sc"}.get(word >> 27, "amo")
    if opcode == 0x0F and (word >> 12) & 7 == 2:
        return {0: "cbo.inval", 4: "cbo.zero"}.get(word >> 20, "cbo")
    if opcode == 0x67 and (word >> 7) & 0x1F not in (0, 1):
        return "jalr-link"
    return None


def scan_functions(elf, flat, base, code_start, code_end, functions, sites,
                   writers, csr_writers, constants=(), kinds=None):
    """One code extent's instruction words, sites, and CSR writers; and,
    into KINDS, each function's breach_kind() words."""
    cursor = code_start
    decoded_all = []
    for value, size, names in functions:
        check_padding(flat, base, cursor, value, constants)
        owner = names[0] if len(names) == 1 else "/".join(names)
        decoded = instructions(flat, value, value + size, base)
        decoded_all.append((owner, decoded))
        for pc, width, word in decoded:
            kind = breach_kind(word, width)
            if kind is not None and kinds is not None:
                counted = kinds.setdefault(owner, {})
                counted[kind] = counted.get(kind, 0) + 1
            require(not floating_point(word, width),
                    f"F, D, or V instruction 0x{word:x} at 0x{pc:x} in "
                    f"{owner}")
            if width == 2:
                require(word != 0x9002, f"c.ebreak at 0x{pc:x} in {owner}")
                continue
            kind = system_kind(word)
            if kind is None:
                continue
            require(kind != "system-other",
                    f"unknown SYSTEM word 0x{word:08x} at 0x{pc:x} in "
                    f"{owner}")
            if kind == "csr":
                name = CSR_NAMES.get(word >> 20)
                require(name not in FORBIDDEN_CSRS,
                        f"{owner} accesses {name} at 0x{pc:x}")
                csr = csr_write(word)
                if csr is None:
                    continue
                name = CSR_NAMES.get(csr)
                require(name is not None and name in csr_writers,
                        f"{owner} writes unlisted CSR 0x{csr:x}")
                writers.setdefault(name, set()).add(owner)
                continue
            sites[kind][owner] = sites[kind].get(owner, 0) + 1
        cursor = value + size
    check_padding(flat, base, cursor, code_end, constants)
    return decoded_all


def check_sites(sites, writers, csr_writers, expected_sites=None):
    """The instruction-site table and the CSR writer table, over all
    code."""
    for kind, expected in (expected_sites or INSTRUCTION_SITES).items():
        require(sites[kind] == expected,
                f"{kind} sites {sorted(sites[kind].items())} != "
                f"{sorted(expected.items())}")
    for name, expected in csr_writers.items():
        actual = writers.get(name, set())
        require(actual == expected,
                f"{name} written by {sorted(actual)}, expected "
                f"{sorted(expected)}")


def check_references(functions, decoded_all, symbols, install_extra,
                     install_callers, inject_sites=0, boundary=False):
    """Pool names, the ecall site's callers, R3 call sites, the injection
    helper's call sites, be_reset's targets, the executor's seam
    (planning/mvp-m6-plan.md, D-5), and the firmware console read's one
    target (planning/mvp-m7-plan.md, D-1), over all code."""
    # Pool addresses, the ecall site's callers, R3 call sites, be_reset.
    # The MVP pool ends where the hart region starts, which the vector,
    # the resume tail, and the hart entry name: its end is not its own.
    pools = ((symbols["__be_mvp_pool_start"],
              symbols["__be_mvp_pool_end"] - 1, MVP_POOL_USERS,
              "the MVP G-stage pool"),)
    sbi_call = symbols[R3_SBI]
    reset = [(value, size) for value, size, names in functions
             if "be_reset" in names]
    require(len(reset) == 1, "be_reset is not one function")
    callers, reset_targets = set(), set()
    install_sites, forbidden_sites, inject_found = [], [], []
    helper_sites = {R3_INSTALL: [], MVP_INJECT: []}
    helpers = {value: name for name, value in symbols.items()
               if name.startswith(PRIVILEGED_PREFIXES)}
    text = (symbols["__be_mvp_text_start"], symbols["__be_mvp_text_end"])
    region = {names[0] if len(names) == 1 else "/".join(names)
              for value, _, names in functions if text[0] <= value < text[1]}
    seam = []
    found = {}
    # The probe images keep no console read (--gc-sections drops it) but
    # probe-console-input, whose hart 0 polls the firmware console (M7).
    reads = [(value, value + size) for value, size, names in functions
             if EXEC_CONSOLE_READ in names]
    require(len(reads) <= 1, f"{EXEC_CONSOLE_READ} is not one function")
    read_targets = set()
    for owner, decoded in decoded_all:
        found[owner] = references(decoded, owner)
        for pc, target, link in found[owner]:
            if owner == EXEC_CONSOLE_READ and \
                    not reads[0][0] <= target < reads[0][1]:
                read_targets.add(target)
            for start, end, users, label in pools:
                require(not start <= target <= end or owner in users,
                        f"{owner} names {label} at 0x{pc:x}")
            if target == sbi_call:
                callers.add(owner)
            if target == symbols[R3_INSTALL]:
                helper_sites[R3_INSTALL].append(owner)
            if target == symbols[EXEC_INSTALL]:
                install_sites.append((owner, pc))
            if target == symbols[MVP_INJECT]:
                helper_sites[MVP_INJECT].append(owner)
            if target == symbols.get(EXEC_INJECT, -1):
                inject_found.append((owner, pc, link))
            if target in helpers and owner in region and \
                    not owner.startswith(EXECUTOR_PREFIX) and \
                    owner != MVP_FW_CALL and owner not in MVP_ASSEMBLY and \
                    not (boundary and owner == MVP_CONFINE_ENTRY):
                seam.append((owner, helpers[target], hex(pc)))
            if target == symbols[R3_ENTER] or \
                    target == symbols.get(R3_ARM, -1):
                forbidden_sites.append((owner, pc))
            if owner == "be_reset" and link is not None and not \
                    reset[0][0] <= target < reset[0][0] + reset[0][1]:
                reset_targets.add(target)
    require(callers and callers <= PLATFORM_HELPERS,
            f"{R3_SBI} is reached from {sorted(callers)}, not only the "
            f"accepted platform helpers")
    require(helper_sites[R3_INSTALL] == [EXEC_INSTALL],
            f"{R3_INSTALL} install call sites in "
            f"{helper_sites[R3_INSTALL]}, expected one, in {EXEC_INSTALL}")
    require(len(install_sites) == INSTALL_CALL_SITES + len(install_extra) and
            sorted(owner for owner, _ in install_sites) ==
            sorted(install_callers),
            f"install call sites {install_sites}, expected one each in "
            f"{install_callers}")
    require(not forbidden_sites,
            f"{R3_ENTER} or {R3_ARM} has call sites {forbidden_sites}")
    require(helper_sites[MVP_INJECT] == [EXEC_INJECT] * inject_sites,
            f"{MVP_INJECT} inject call sites in {helper_sites[MVP_INJECT]}, "
            f"expected {inject_sites}, in {EXEC_INJECT}")
    require(len(inject_found) == inject_sites and
            all(owner in INJECT_CALLERS and link == 1
                for owner, _, link in inject_found),
            f"inject call sites "
            f"{[(owner, hex(pc)) for owner, pc, _ in inject_found]}, "
            f"expected {inject_sites}, a call from the denial action")
    expected_targets = {symbols[B1_QUIESCE], symbols[MVP_MAIN],
                        symbols[R3_HALT]}
    require(reset_targets == expected_targets,
            "be_reset calls or tails something other than be_b1_quiesce, "
            "be_mvp_runtime_main, and be_r3_arch_halt")
    require(not seam, f"privileged helpers named outside the executor: "
            f"{seam}")
    require(not reads or read_targets == {symbols[MVP_FW_CALL]},
            f"{EXEC_CONSOLE_READ} reaches "
            f"{sorted(hex(target) for target in read_targets)}, expected "
            f"{MVP_FW_CALL} alone")
    return found


def reachable_functions(functions, found, symbols, roots, label,
                        skip=None):
    """The transitive function closure from named roots, but for the edges
    SKIP(source owner, target) names."""
    extents = sorted((value, value + size,
                      names[0] if len(names) == 1 else "/".join(names))
                     for value, size, names in functions)
    starts = [start for start, _, _ in extents]

    def owner_at(address):
        index = bisect.bisect_right(starts, address) - 1
        if index >= 0 and address < extents[index][1]:
            return extents[index][2]
        return None

    reached = {owner_at(symbols[name]) for name in roots}
    require(None not in reached, f"a {label} root is not a function")
    parent = {owner: None for owner in reached}
    work = sorted(reached)
    while work:
        source = work.pop()
        for _, target, _ in found[source]:
            if skip is not None and skip(source, target):
                continue
            owner = owner_at(target)
            if owner is not None and owner not in reached:
                reached.add(owner)
                parent[owner] = source
                work.append(owner)
    return extents, reached, parent


def check_domain_reach(elf, functions, found, symbols, profile="mvp"):
    """The code a VS-domain hart runs, transitively from its two roots."""
    _, reached, _ = reachable_functions(
        functions, found, symbols, DOMAIN_ROOTS, "VS-domain-hart")
    names = {name for owner in reached for name in owner.split("/")}
    for name in HART0_CODE:
        require(name not in names,
                f"the domain-hart entry reaches {name}")
    for name in DOMAIN_MGMT_CODE:
        require(name not in symbols or name in names,
                f"the domain-hart entry does not reach {name}")
    if profile == "mvp":
        require(INPUT_SERVE in names,
                f"the domain-hart entry does not reach {INPUT_SERVE}")
        require(EXEC_CONSOLE_READ in symbols,
                f"the image links no {EXEC_CONSOLE_READ}")
    objects = [(name, symbols[name], symbol_size(elf, name))
               for name in HART0_ONLY if name in symbols]
    for owner in sorted(reached):
        for pc, target, _ in found[owner]:
            for name, start, size in objects:
                require(not start <= target < start + size,
                        f"{owner}, which a domain hart runs, names {name} "
                        f"at 0x{pc:x}")
    return names


def role_nodes(functions, decoded_all):
    """The role rules' graph, once per image: each function's (start, end,
    owner, its references, its words by pc)."""
    require(len(functions) == len(decoded_all),
            "the role reachability inputs differ in length")
    nodes = []
    for (start, size, names), (owner, decoded) in zip(functions, decoded_all):
        nodes.append((start, start + size, owner,
                      references(decoded, f"{owner}@0x{start:x}"),
                      {pc: (width, word) for pc, width, word in decoded}))
    return nodes


def node_owner(nodes):
    """The index of the node whose extent holds an address, or None."""
    starts = [node[0] for node in nodes]

    def owner_at(address):
        index = bisect.bisect_right(starts, address) - 1
        return index if index >= 0 and address < nodes[index][1] else None
    return owner_at


def check_role_reach(elf, functions, decoded_all, symbols, roots, allowed,
                     reference_extents, label, nodes=None):
    """A duplicate-symbol-safe transitive role and data closure."""
    if nodes is None:
        nodes = role_nodes(functions, decoded_all)
    owner_at = node_owner(nodes)
    reached = {owner_at(symbols[root]) for root in roots}
    require(None not in reached, f"a {label} root is not a function")
    parent = {index: None for index in reached}
    work = sorted(reached)
    # The shared trap vector serves both roles: each role's reach skips
    # exactly the vector's edges to the other role's side (the VS-domain
    # harts' to hart 0's terminal; M11-8, hart 0's to the dispatch and the
    # VS-domain hart's terminal, which its stack top never selects).
    skipped = {"VS-domain-hart": (MVP_TERMINAL,),
               "control": (MVP_DISPATCH, MVP_HART_TERMINAL)}.get(label, ())
    skip = {symbols[name] for name in skipped if name in symbols}
    while work:
        source = work.pop()
        for _, target, _ in nodes[source][3]:
            if nodes[source][0] == symbols[MVP_VECTOR] and target in skip:
                continue
            owner = owner_at(target)
            if owner is not None and owner not in reached:
                reached.add(owner)
                parent[owner] = source
                work.append(owner)
    for index in sorted(reached):
        start, end, owner, refs, words = nodes[index]
        path = [index]
        while parent[path[-1]] is not None:
            path.append(parent[path[-1]])
        path.reverse()
        require(any(low <= start and end <= high for low, high in allowed),
                f"the {label} roots reach {owner} at 0x{start:x}-0x{end:x}, "
                f"outside their executable role extents, through "
                f"{' -> '.join(nodes[item][2] for item in path)}")
        for pc, target, link in refs:
            if link is not None or owner_at(target) is not None:
                continue
            width, word = words[pc]
            access = None
            if width == 4:
                access = "r" if word & 0x7f == 0x03 else \
                    "w" if word & 0x7f in (0x23, 0x2f) else None
            else:
                kind = (word & 3) << 3 | (word >> 13) & 7
                access = "r" if kind in (2, 3, 18, 19) else \
                    "w" if kind in (6, 7, 22, 23) else None
            boundary = [name for name, value in symbols.items()
                        if value == target and name.startswith("__be_")]
            if boundary and access is None:
                continue
            sections = [(name, section) for name, section in
                        elf.sections.items() if section[2] & SHF_ALLOC and
                        section[3] <= target < section[3] + section[5]]
            if not sections:
                require(boundary,
                        f"the {label} roots reach {owner}, which forms "
                        f"unallocated address 0x{target:x} at 0x{pc:x}")
                continue
            require(len(sections) == 1,
                    f"0x{target:x} lies in multiple allocated sections")
            section_name, _ = sections[0]
            granted = [name for name, low, high, rights in reference_extents
                       if low <= target < high and
                       (access is None or access in rights)]
            require(granted,
                    f"the {label} roots reach {owner}, whose "
                    f"{access or 'address'} "
                    f"reference at 0x{pc:x} targets 0x{target:x} in "
                    f"{section_name}, outside the role's profile")
    return nodes, reached


def check_control_reach(elf, functions, decoded_all, symbols, nodes=None,
                        confined=False):
    """The post-barrier control loop and synchronous-exception terminal,
    and in a step-2 image (CONFINED; M11-8, rule C4) the control hart's
    confined entry, whose reach must hold the shared trap vector whole;
    returns the control role's reached nodes."""
    roots = (CONTROL_LOOP, MVP_TERMINAL) + ((CONTROL_ENTRY,) if confined
                                            else ())
    nodes, reached = check_role_reach(
        elf, functions, decoded_all, symbols, roots,
        CONTROL_CODE_EXTENTS, CONTROL_REFERENCE_EXTENTS, "control", nodes)
    vector = next(index for index, node in enumerate(nodes)
                  if node[0] == symbols[MVP_VECTOR])
    require(any(target == symbols[MVP_TERMINAL]
                for _, target, _ in nodes[vector][3]),
            "the shared trap vector does not reach the control terminal")
    require(not confined or vector in reached,
            f"the control roots do not reach the shared trap vector {MVP_VECTOR}, "
            f"which hart 0's confined entry installs (C4)")
    return reached


# M11-8 (planning/mvp-m11-plan.md, D-4 rule 1; I22 (b)): the objects that
# boot code hands to hart 0's state (rule C9), each with the rights hart 0
# uses on it. By the registration calls before the barrier: by pointer,
# be_mvp_control_mgmt() the management state (be_mvp_ctl's mgmt) and the
# grants (the state's grants), which the control loop reads after the
# barrier through those pointers alone (no instruction of its own forms
# the grants' address); filled by boot code and then addressed by the
# control loop itself, the three ring views (ring_views(): their buffer
# and index pointers into the mailboxes) and the console input state and
# its buffer (be_mvp_input_arm()); by copy, be_mvp_control_pages() or
# be_mvp_control_channel() and seal_windows() the sealed pages or channel
# and each map's window into be_mvp_ctl, after which the control loop
# reads only the copies. Every boundary-on scenario image links the names
# of HANDED_EVERY; the others by the scenario's kind (handed_names()).
HANDED_OVER = (
    (MVP_GRANTS_SYMBOL, "r"), (MVP_MGMT_STATE_SYMBOL, "rw"),
    ("be_mvp_maps", "r"), ("be_mvp_sealed_pages", "r"),
    ("be_mvp_sealed_channel", "r"), ("be_mvp_inbound", "rw"),
    ("be_mvp_outbound", "rw"), (MVP_INPUT_RINGS_SYMBOL, "rw"),
    (MVP_CONSOLE_IN_SYMBOL, "rw"), (MVP_CONSOLE_BUFFER_SYMBOL, "rw"))
HANDED_EVERY = ("be_mvp_maps", "be_mvp_sealed_pages", "be_mvp_inbound",
                "be_mvp_outbound", MVP_INPUT_RINGS_SYMBOL,
                MVP_CONSOLE_IN_SYMBOL, MVP_CONSOLE_BUFFER_SYMBOL)
# Each role's constant ranges, by their link symbols: rule C8 reads the
# control role's, rule C10 all three.
ROLE_CONSTANTS = (
    ("control", "__be_mvp_control_constants_start",
     "__be_mvp_control_constants_end"),
    ("shared", "__be_monitor_shared_constants_start",
     "__be_monitor_shared_constants_end"),
    ("VS-domain-hart", "__be_mvp_domain_constants_start",
     "__be_mvp_domain_constants_end"))
# A breach image's table of attempts holds its targets' addresses as
# numbers (M11-7), which the breach rules judge: no pointer is read there.
ADDRESS_NUMBERS = ("be_mvp_breach_attempts",)
# Rule C10's role extents, each with the roles whose reach may hold it.
ROLE_CODE = (
    ("monitor control text", "MONITOR_CONTROL_TEXT", ("control",)),
    ("monitor shared text", "MONITOR_SHARED_TEXT",
     ("control", "VS-domain-hart")),
    ("monitor VS-domain-hart text", "MONITOR_DOMAIN_TEXT",
     ("VS-domain-hart",)),
    ("MVP control text", "MVP_CONTROL_TEXT", ("control",)),
    ("MVP VS-domain-hart text", "MVP_DOMAIN_TEXT", ("VS-domain-hart",)))


def handed_names(mgmt, pages):
    """The names of HANDED_OVER that a boundary-on image links by its
    scenario's kind: HANDED_EVERY; the grants and the management state with
    the management extension (MGMT); the sealed channel record where the
    scenario has no pages (PAGES), a channel or none."""
    return set(HANDED_EVERY) | \
        ({MVP_GRANTS_SYMBOL, MVP_MGMT_STATE_SYMBOL} if mgmt else set()) | \
        (set() if pages else {"be_mvp_sealed_channel"})


def boot_reach(nodes, owner_at, symbols):
    """The nodes reached from be_reset, every edge followed but the
    formation, as data, of the control hart's confined entry's address
    (M11-8): the entry is the MVP region's first byte, whose start hart 0's
    region check forms (rule C3). Returns them and the addresses they form
    outside every function."""
    entry = symbols.get(CONTROL_ENTRY)
    start = owner_at(symbols["be_reset"])
    reached = {start}
    work = [start]
    while work:
        source = work.pop()
        for _, target, link in nodes[source][3]:
            if link is None and target == entry:
                continue
            owner = owner_at(target)
            if owner is not None and owner not in reached:
                reached.add(owner)
                work.append(owner)
    return reached, data_targets(nodes, owner_at, reached)


def closure(nodes, owner_at, starts):
    """The nodes reached from the node indices STARTS, every edge followed,
    and the addresses they form outside every function."""
    reached = set(starts)
    work = sorted(reached)
    while work:
        source = work.pop()
        for _, target, _ in nodes[source][3]:
            owner = owner_at(target)
            if owner is not None and owner not in reached:
                reached.add(owner)
                work.append(owner)
    return reached, data_targets(nodes, owner_at, reached)


def data_targets(nodes, owner_at, reached):
    """The addresses that the reached nodes form outside every function."""
    return {target for index in reached
            for _, target, link in nodes[index][3]
            if link is None and owner_at(target) is None}


def constant_finder(elf, symbols):
    """A function from an address to the constant that holds it in a role's
    constant range (ROLE_CONSTANTS): its sized object, else (a jump table,
    a string) the bytes from the address to the next symbol or the
    range's end; (start, end, name), or None outside every range. A
    constant without a symbol of its own is so taken to run on to the next
    symbol: a merged string that only boot code names, after one that a
    role names and before the next symbol, is held by that role's."""
    ranges = [(symbols[low], symbols[high]) for _, low, high in
              ROLE_CONSTANTS if symbols.get(low) is not None and
              symbols.get(high) is not None]
    objects = sorted(elf.objects)
    starts = [value for value, _, _ in objects]
    longest = max((size for _, size, _ in objects), default=0)
    values = sorted({value for value in symbols.values()
                     if value is not None})

    def find(address):
        held = [high for low, high in ranges if low <= address < high]
        if not held:
            return None
        index = bisect.bisect_right(starts, address) - 1
        while index >= 0 and objects[index][0] + longest > address:
            value, size, name = objects[index]
            if value <= address < value + size:
                return value, value + size, name
            index -= 1
        following = bisect.bisect_right(values, address)
        end = values[following] if following < len(values) else held[0]
        return address, min(end, held[0]), f"0x{address:x}"
    return find


def pointer_closure(flat, find, addresses, check=None):
    """The constants that ADDRESSES fall in, and those that their 8-byte
    words name in turn, transitively; CHECK(name, at, start, word) sees
    each word that is an address inside the image. Returns {start: (end,
    name)} and every image address those words hold."""
    found, named = {}, set()
    work = sorted(addresses)
    while work:
        extent = find(work.pop())
        if extent is None or extent[0] in found:
            continue
        start, end, name = extent
        found[start] = (end, name)
        if name in ADDRESS_NUMBERS:
            continue
        for at in range(start + (-start) % 8, end - 7, 8):
            word = struct.unpack_from("<Q", flat, at - BASE)[0]
            if not BASE <= word < BASE + SPAN:
                continue
            if check is not None:
                check(name, at, start, word)
            named.add(word)
            work.append(word)
    return found, named


def check_role_constants(elf, flat, nodes, control, domain, symbols,
                         kind=(False, False)):
    """M11-8's rules C8 to C10 in a boundary-on image (planning/
    mvp-m11-plan.md, D-4 rule 1; I22).

    C8: each constant that control-reached code names, in the MVP control
    constants or the monitor's shared constants, and each constant its
    words name in turn, holds no 8-byte word that is an image address
    outside the control profile, but be_mvp_bindings' two G-stage root
    words, which the binding rule pins as numbers. C9: each object that
    boot code hands to hart 0's state (HANDED_OVER) lies in the control
    profile with the rights hart 0 uses, and the image links each one that
    its scenario's KIND, (management, pages), has (handed_names()). C10:
    no function in a role's text extents and no constant in a role's
    constant range is reached from the boot roots without being reached
    from that role (for the shared extents, from either role); what no
    root reaches is not refused, and a constant without a symbol is taken
    to run on to the next symbol (constant_finder()), so that a merged
    string only boot code names is not refused where it follows one that
    the role names."""
    owner_at = node_owner(nodes)
    find = constant_finder(elf, symbols)
    roots = (LAYOUT["G0_ROOT_HPA"], LAYOUT["G1_ROOT_HPA"])

    def profile(name, at, start, word):
        if name == MVP_BINDINGS_SYMBOL and (at - start) % 24 == 16 and \
                word in roots:
            return
        require(any(low <= word < high
                    for _, low, high, _ in CONTROL_REFERENCE_EXTENTS),
                f"the control role's constant {name} holds 0x{word:x} at "
                f"0x{at:x}, an address outside the control profile")
    control_constants, control_named = pointer_closure(
        flat, find, data_targets(nodes, owner_at, control), profile)
    handed = set()
    linked = handed_names(*kind)
    for name, rights in HANDED_OVER:
        if name not in symbols:
            require(name not in linked,
                    f"the image links no {name}, which boot code hands to "
                    f"hart 0's state in every image of its kind (C9)")
            continue
        start = symbols[name]
        require(start is not None, f"{name} is not one symbol")
        end = start + symbol_size(elf, name)
        require(any(low <= start and end <= high and rights in held
                    for _, low, high, held in CONTROL_REFERENCE_EXTENTS),
                f"{name}, which boot code hands to hart 0's state, lies at "
                f"0x{start:x}-0x{end:x}, outside the control profile with "
                f"rights {rights} (C9)")
        handed.add(start)
    handed_constants, handed_named = pointer_closure(flat, find, handed,
                                                     profile)
    control_constants.update(handed_constants)
    boot, boot_data = boot_reach(nodes, owner_at, symbols)
    boot_constants, boot_named = pointer_closure(flat, find, boot_data)
    domain_constants, domain_named = pointer_closure(
        flat, find, data_targets(nodes, owner_at, domain))

    def functions(reached, named):
        return reached | {owner_at(address) for address in named
                          if owner_at(address) is not None}
    reach = {"control": (functions(control, control_named | handed_named),
                         control_constants),
             "VS-domain-hart": (functions(domain, domain_named),
                                domain_constants)}
    boot = functions(boot, boot_named)
    for label, extent, roles in ROLE_CODE:
        low = LAYOUT[f"{extent}_HPA"]
        high = low + LAYOUT[f"{extent}_BYTES"]
        for index in sorted(boot):
            start, end, owner, _, _ = nodes[index]
            require(not low <= start < high or
                    any(index in reach[role][0] for role in roles),
                    f"{owner} at 0x{start:x}-0x{end:x} lies in the {label} "
                    f"and only boot code reaches it (C10)")
    for label, start_symbol, end_symbol in ROLE_CONSTANTS:
        low, high = symbols[start_symbol], symbols[end_symbol]
        roles = ("control", "VS-domain-hart") if label == "shared" \
            else (label,)
        held = [(begin, finish) for role in roles
                for begin, (finish, _) in reach[role][1].items()]
        for start, (end, name) in sorted(boot_constants.items()):
            require(not low <= start < high or
                    any(begin <= start < finish for begin, finish in held),
                    f"the constant {name} at 0x{start:x}-0x{end:x} lies in "
                    f"the {label} constants and only boot code reaches it "
                    f"(C10)")


def store_fields(word):
    """(source, base, offset) of an sd, or None."""
    if word & 0x707F != 0x3023:
        return None
    return ((word >> 20) & 0x1F, (word >> 15) & 0x1F,
            signed((word >> 25) << 5 | (word >> 7) & 0x1F, 12))


def load_fields(word):
    """(destination, base, offset) of an ld, or None."""
    if word & 0x707F != 0x3003:
        return None
    return (word >> 7) & 0x1F, (word >> 15) & 0x1F, signed(word >> 20, 12)


def sc_fields(word):
    """beryllium-cheri: (source, base, offset) of an SC, or None."""
    if word & 0x707F != 0x4023:
        return None
    return ((word >> 20) & 0x1F, (word >> 15) & 0x1F,
            signed((word >> 25) << 5 | (word >> 7) & 0x1F, 12))


def lc_fields(word):
    """beryllium-cheri: (destination, base, offset) of an LC, or None."""
    if word & 0x707F != 0x400F:
        return None
    return (word >> 7) & 0x1F, (word >> 15) & 0x1F, signed(word >> 20, 12)


def ddc_access(word):
    """beryllium-cheri: ("read", rd) for csrrs rd, ddc, zero; ("write", rs1)
    for csrrw zero, ddc, rs1; else None."""
    if word & 0x7F != 0x73 or word >> 20 != DDC_CSR:
        return None
    funct3, rd, rs1 = (word >> 12) & 7, (word >> 7) & 0x1F, \
        (word >> 15) & 0x1F
    if funct3 == 2 and rs1 == 0:
        return "read", rd
    if funct3 == 1 and rd == 0:
        return "write", rs1
    return None


def csr_number(word):
    """beryllium-cheri: the CSR a Zicsr instruction names, else None."""
    if word & 0x7F != 0x73 or (word >> 12) & 7 in (0, 4):
        return None
    return word >> 20


def csr_read_whole(word, csr):
    """beryllium-cheri: rd for csrrs rd, csr, zero (in Capability Pointer
    Mode, a read of the whole capability); else None."""
    if word & 0x707F == 0x2073 and (word >> 15) & 0x1F == 0 and \
            word >> 20 == csr:
        return (word >> 7) & 0x1F
    return None


def csr_write_word(csr, rs1):
    """beryllium-cheri: the word of csrrw zero, csr, rs1."""
    return csr << 20 | rs1 << 15 | 1 << 12 | 0x73


def writes_csr(word, csr):
    """beryllium-cheri: whether the word writes csr (a CSRRW always; a set
    or clear only with a source other than zero)."""
    if csr_number(word) != csr:
        return False
    return (word >> 12) & 7 in (1, 5) or (word >> 15) & 0x1F != 0


def writes_register(word, register):
    """beryllium-cheri: whether the 32-bit word writes register (x0 never
    holds a write; stores and branches have no destination)."""
    return register != 0 and (word & 0x7F) not in (0x23, 0x63) and \
        (word >> 7) & 0x1F == register


def nearest_writer(words, index, register):
    """beryllium-cheri: the index of the last word before words[index] that
    writes register, or None (x0 has none)."""
    for at in range(index - 1, -1, -1):
        if writes_register(words[at], register):
            return at
    return None


def materialized(words, index, register):
    """beryllium-cheri: the constant that register holds at words[index],
    evaluated back through each nearest earlier writer with track()'s
    semantics for x0, lui, addi, addiw, and slli; None when the chain
    holds any other writer, or ends without one."""
    if register == 0:
        return 0
    at = nearest_writer(words, index, register)
    if at is None:
        return None
    word = words[at]
    opcode, funct3 = word & 0x7F, (word >> 12) & 7
    if opcode == 0x37:
        return signed(word & 0xFFFFF000, 32) & MASK64
    if (opcode, funct3) not in ((0x13, 0), (0x13, 1), (0x1B, 0)) or \
            (opcode, funct3) == (0x13, 1) and word >> 26 != 0:
        return None
    source = materialized(words, at, (word >> 15) & 0x1F)
    if source is None:
        return None
    if opcode == 0x1B:
        return signed((source + signed(word >> 20, 12)) & 0xFFFFFFFF,
                      32) & MASK64
    if funct3 == 1:
        return (source << ((word >> 20) & 0x3F)) & MASK64
    return (source + signed(word >> 20, 12)) & MASK64


def check_structure(elf):
    """The accepted R5 checker's structure rules, moved to the K3 base."""
    require(3 not in elf.program_types, "image requests an interpreter")
    require(2 not in elf.program_types, "image carries a dynamic segment")
    allocated = {name for name, section in elf.sections.items()
                 if section[2] & SHF_ALLOC}
    require(allocated == ALLOCATED_SECTIONS,
            f"allocated sections {sorted(allocated)} differ from the "
            f"layout's {sorted(ALLOCATED_SECTIONS)}")
    for name, section in elf.sections.items():
        require(section[1] not in (4, 9),
                f"image carries relocations ({name})")
    require(not elf.undefined,
            f"unresolved symbols: {sorted(set(elf.undefined))}")
    architecture = elf.architecture()
    require(architecture is not None, "missing RISC-V architecture attributes")
    for part in ("_h1p0", "_zicsr2p0", "_zifencei2p0"):
        require(part in architecture, f"ELF attributes omit {part}")
    for pattern in (r"_f\d", r"_d\d", r"_v\d"):
        require(re.search(pattern, architecture) is None,
                f"ELF attributes include {pattern}")
    for name in elf.symbols:
        require(re.search(r"(^|_)r6(_|$)|be_r6", name, re.I) is None,
                f"hidden R6 symbol {name}")
    for name, (address, size, required, forbidden) in \
            EXPECTED_SECTIONS.items():
        section = elf.sections.get(name)
        require(section is not None, f"missing section {name}")
        have = {"W": section[2] & SHF_WRITE, "A": section[2] & SHF_ALLOC,
                "X": section[2] & SHF_EXECINSTR}
        if address is not None:
            require(section[3] == address, f"{name} address moved")
        if size is not None:
            require(section[5] == size, f"{name} size changed")
        for flag in required:
            require(have[flag], f"{name} lost flag {flag}")
        for flag in forbidden:
            require(not have[flag], f"{name} gained flag {flag}")
    for name in (".gstage.g0", ".gstage.g1", ".published.g0",
                 ".published.g1", ".mailbox.control.g0",
                 ".mailbox.control.g1", ".mailbox.hart.g0",
                 ".mailbox.hart.g1", ".private.g0", ".private.g1"):
        require(elf.sections[name][1] == 8, f"{name} is not NOLOAD")
    data = elf.sections[".monitor.data"]
    require(data[3] + data[5] <= MONITOR_DATA_LIMIT,
            "monitor data overruns the diagnostic page")
    # The MVP region's sections, in order, inside it and never inside the
    # core (Plan revision M0-A.1).
    cursor = REGION
    for name in REGION_SECTIONS:
        section = elf.sections[name]
        start, end = section[3], section[3] + section[5]
        require(not (start < BASE + CORE_SPAN and BASE < end),
                f"{name} 0x{start:x}+0x{section[5]:x} lies inside the "
                f"core")
        require(cursor <= start and end <= REGION + REGION_BYTES,
                f"{name} 0x{start:x}+0x{section[5]:x} leaves the MVP region "
                f"0x{REGION:x}+0x{REGION_BYTES:x}")
        cursor = end
    return architecture


def check_trap_entry(decoded, symbols):
    """Sscratch pivot, the whole record, SPV, and the dispatch call."""
    require(all(size == 4 for _, size, _ in decoded),
            "trap entry holds a compressed instruction")
    words = [word for _, _, word in decoded]
    require(words[0] == CSRRW_SP_SSCRATCH_SP,
            "trap entry does not first exchange sp with sscratch")
    stores = {fields for fields in map(store_fields, words) if fields}
    frame = 5  # t0 holds the saved page
    for number in range(1, 32):
        offset = (number - 1) * 8
        if number in (2, 5, 6):  # sp, t0, t1 arrive through scratch
            saved = any(base == frame and at == offset
                        for _, base, at in stores)
        else:
            saved = (number, frame, offset) in stores
        require(saved, f"trap entry does not save x{number} at {offset}")
    # The saved page is the hart's own, from sscratch: each CSR is read
    # into a register and stored from it at its offset in the record.
    stored = set()
    for word, following in zip(words, words[1:]):
        fields = store_fields(following)
        if system_kind(word) == "csr" and csr_write(word) is None and \
                fields and fields[1] == frame and \
                fields[0] == (word >> 7) & 0x1F:
            stored.add((fields[2], CSR_NAMES.get(word >> 20)))
    words_after = [(name, FRAME_TRAP_CSRS + index * 8)
                   for index, name in enumerate(TRAP_CSRS)] + \
        list(EXIT_WORDS)
    for name, offset in words_after:
        require((offset, name) in stored,
                f"trap entry does not store {name} at {offset}")
    require((0, frame, FRAME_RESERVED) in stores,
            "trap entry does not seal the reserved frame word")
    _, reads, checks, _ = track(decoded)
    require([csr for _, csr in reads].count("vsstatus") == 1,
            "trap entry does not read vsstatus exactly once")
    require([check[1:] for check in checks] ==
            [("ne", "hstatus", HSTATUS_SPV, 0)],
            f"trap entry does not fail closed on hstatus.SPV: {checks}")
    targets = {(target, link) for _, target, link in references(decoded)}
    require((symbols[MVP_DISPATCH], 1) in targets,
            "trap entry does not call be_mvp_dispatch")
    require((symbols[MVP_HART_TERMINAL], 0) in targets and
            (symbols[MVP_TERMINAL], 0) in targets and
            (symbols[R3_HALT], 0) in targets,
            "trap entry does not end every failure in a terminal path")
    check_block_arithmetic(decoded, symbols, MVP_VECTOR)


def check_trap_entry_cheri(decoded, symbols):
    """Sscratch pivot, the whole record, SPV, and the dispatch call.

    beryllium-cheri: the CHERI-aware monitor's (--monitor cheri). It enters
    Capability Pointer Mode first, then exchanges csp with sscratchc and
    spills ct0 and ct1 below the trusted top; it saves every guest register
    whole in the capability frame (CAP_FRAME + 16 * n) and the guest's ddc
    in its slot 0, and installs the monitor's ddc (CAP_MON_DDC) before it
    returns to Integer Pointer Mode, where a CSR write would set only an
    address; and it writes each register's address into the integer
    record, from the frame, before the CSRs. The review of the CHERI rules
    added: one ddc read then one ddc write (F1); ct0, ct1, and csp saved
    from where they are held, and sscratchc restored whole (F2). Since
    M11-3 its first checks are the trusted top's two comparisons with the
    private blocks' stack tops, each branch to its own target, before the
    SPV check.
    """
    require(all(size == 4 for _, size, _ in decoded),
            "trap entry holds a compressed instruction")
    words = [word for _, _, word in decoded]
    require(words[0] == MODESW_CAP,
            "trap entry does not first enter Capability Pointer Mode")
    require(words[1] == CSRRW_SP_SSCRATCH_SP,
            "trap entry does not then exchange sp with sscratch")
    require(sc_fields(words[2]) == (5, 2, -32) and
            sc_fields(words[3]) == (6, 2, -16),
            "trap entry does not spill ct0 and ct1 below the trusted top")
    integer_at = words.index(MODESW_INT) if MODESW_INT in words else 0
    require(integer_at > 3, "trap entry never returns to Integer Pointer "
            "Mode")
    capabilities = {fields for fields in map(sc_fields, words[:integer_at])
                    if fields}
    for number in range(1, 32):
        offset = CAP_FRAME + 16 * number
        if number in (2, 5, 6):  # csp, ct0, ct1 arrive through scratch
            saved = any(base == 2 and at == offset
                        for _, base, at in capabilities)
        else:
            saved = (number, 2, offset) in capabilities
        require(saved, f"trap entry does not save c{number} whole at "
                f"{offset}")
    pairs = list(zip(words[:integer_at], words[1:integer_at]))
    # One ddc read and one ddc write: the read saves the guest's ddc whole
    # in slot 0 and the write installs the monitor's from CAP_MON_DDC, the
    # save first, both in Capability Pointer Mode, so that the resume tail
    # gives back the guest's own ddc, never the monitor's (F1 of the CHERI
    # rules' review).
    ddc = [index for index, value in enumerate(words)
           if csr_number(value) == DDC_CSR]
    kinds = [ddc_access(words[index]) for index in ddc]
    require(len(ddc) == 2 and None not in kinds and
            sorted(kind[0] for kind in kinds) == ["read", "write"],
            "trap entry does not hold exactly one ddc read and one ddc "
            "write")
    read_at, write_at = (ddc[[kind[0] for kind in kinds].index(access)]
                         for access in ("read", "write"))
    require(read_at + 1 < len(words) and
            sc_fields(words[read_at + 1]) ==
            (ddc_access(words[read_at])[1], 2, CAP_FRAME),
            "trap entry does not save the guest's ddc whole")
    require(write_at > 0 and lc_fields(words[write_at - 1]) ==
            (ddc_access(words[write_at])[1], 2, CAP_MON_DDC),
            "trap entry does not install the monitor's ddc in Capability "
            "Pointer Mode")
    require(read_at < write_at < integer_at,
            "trap entry does not save the guest's ddc before it installs "
            "the monitor's, both in Capability Pointer Mode")
    # Where csp, ct0, and ct1 come from (F2): ct0 and ct1 from their spills
    # below the trusted top, each loaded whole and at once stored whole in
    # its slot; csp from sscratchc, read whole and at once stored; then
    # sscratchc is the trusted top again, whole, before Integer Pointer
    # Mode, by sscratch's one write after the exchange.
    for spill, number, register in ((-32, 5, "ct0"), (-16, 6, "ct1")):
        require(any(lc_fields(first) is not None and
                    lc_fields(first)[1:] == (2, spill) and
                    sc_fields(second) == (lc_fields(first)[0], 2,
                                          CAP_FRAME + 16 * number)
                    for first, second in pairs),
                f"trap entry does not save {register} whole from its "
                f"spill at {spill}")
    csp = [index for index, (first, second) in enumerate(pairs)
           if csr_read_whole(first, SSCRATCH) is not None and
           sc_fields(second) == (csr_read_whole(first, SSCRATCH), 2,
                                 CAP_FRAME + 16 * 2)]
    require(csp, "trap entry does not save csp whole from sscratchc")
    sscratch_writes = [index for index, value in enumerate(words)
                       if writes_csr(value, SSCRATCH)]
    require(len(sscratch_writes) == 2 and sscratch_writes[0] == 1 and
            words[sscratch_writes[1]] == CSRW_SSCRATCH_SP and
            csp[0] + 1 < sscratch_writes[1] < integer_at,
            "trap entry does not restore sscratchc to the trusted top, "
            "whole, before Integer Pointer Mode, as sscratch's one write "
            "after the exchange")
    stores = {fields for fields in map(store_fields, words) if fields}
    for number in range(1, 32):
        offset = (number - 1) * 8
        require(any(load_fields(first) == (5, 2, CAP_FRAME + 16 * number) and
                    store_fields(second) == (5, 2, offset)
                    for first, second in pairs),
                f"trap entry does not record x{number} at {offset}")
    frame = 5  # t0 holds the saved page, from sp, in Integer Pointer Mode
    # The saved page is the hart's own, from sscratch: each CSR is read
    # into a register and stored from it at its offset in the record.
    stored = set()
    for word, following in zip(words, words[1:]):
        fields = store_fields(following)
        if system_kind(word) == "csr" and csr_write(word) is None and \
                fields and fields[1] == frame and \
                fields[0] == (word >> 7) & 0x1F:
            stored.add((fields[2], CSR_NAMES.get(word >> 20)))
    words_after = [(name, FRAME_TRAP_CSRS + index * 8)
                   for index, name in enumerate(TRAP_CSRS)] + \
        list(EXIT_WORDS)
    for name, offset in words_after:
        require((offset, name) in stored,
                f"trap entry does not store {name} at {offset}")
    require((0, frame, FRAME_RESERVED) in stores,
            "trap entry does not seal the reserved frame word")
    _, reads, checks, _ = track(decoded)
    require([csr for _, csr in reads].count("vsstatus") == 1,
            "trap entry does not read vsstatus exactly once")
    # Since M11-3 the trusted top, t0 by mv t0, sp after the exchange, is
    # compared with each private block's stack top, exactly, before any
    # other check: beq past the second comparison on the first block's,
    # then bne to the bad-stack path off the second's. The tracker holds
    # both, as it does not in the RISC-V monitor's vector, whose t0 is
    # sp + 16 after sp - 16, a value it does not hold.
    tops = [block + LAYOUT["BLOCK_STACK_TOP_OFFSET"] for block in BLOCKS]
    require([check[1:] for check in checks[:2]] ==
            [("ne", "sscratch", MASK64, tops[0]),
             ("eq", "sscratch", MASK64, tops[1])],
            f"trap entry does not require exactly the private blocks' "
            f"stack tops {[hex(top) for top in tops]}, in order, of its "
            f"trusted top: {checks}")
    require([check[1:] for check in checks[2:]] ==
            [("ne", "hstatus", HSTATUS_SPV, 0)],
            f"trap entry does not fail closed on hstatus.SPV: {checks}")
    at = {pc: index for index, (pc, _, _) in enumerate(decoded)}
    first, second = (decode(words[index], 4, decoded[index][0])["branch"]
                     for index, *_ in checks[:2])
    require(checks[1][0] + 1 < len(decoded) and
            first == decoded[checks[1][0] + 1][0],
            "trap entry's first block comparison does not land just after "
            "its second")
    # The bad-stack path: back in Integer Pointer Mode with sp 16 below
    # the top, as the RISC-V monitor's vector leaves it, and from there no
    # call and every path to hart 0's terminal or the halt.
    start = at.get(second)
    require(start is not None and
            words[start:start + 2] == [MODESW_INT, ADDI_SP_SP_M16] and
            path_ends(decoded, start) ==
            {symbols[MVP_TERMINAL], symbols[R3_HALT]},
            "trap entry's second block comparison does not land on its "
            "bad-stack path")
    targets = {(target, link) for _, target, link in references(decoded)}
    require((symbols[MVP_DISPATCH], 1) in targets,
            "trap entry does not call be_mvp_dispatch")
    require((symbols[MVP_HART_TERMINAL], 0) in targets and
            (symbols[MVP_TERMINAL], 0) in targets and
            (symbols[R3_HALT], 0) in targets,
            "trap entry does not end every failure in a terminal path")
    check_block_arithmetic(decoded, symbols, MVP_VECTOR)


def path_ends(decoded, start):
    """beryllium-cheri: the tail targets in which the paths from
    decoded[start] end, each branch followed both ways and each jump
    inside DECODED to its target; None when a path calls (an ecall
    among calls), meets a word it cannot decode, returns by sret or mret,
    branches out of DECODED, leaves by a jump whose target is unknown, or
    runs off DECODED's end."""
    at = {pc: index for index, (pc, _, _) in enumerate(decoded)}
    tails = {pc: target for pc, target, link in references(decoded)
             if link == 0}
    ends, seen, work = set(), set(), [start]
    while work:
        index = work.pop()
        if index in seen:
            continue
        seen.add(index)
        if index >= len(decoded):
            return None
        pc, size, word = decoded[index]
        insn = decode(word, size, pc)
        if insn.get("call") or insn.get("unknown"):
            return None
        if insn.get("branch") is not None:
            if insn["branch"] not in at:
                return None
            work += [index + 1, at[insn["branch"]]]
        elif insn.get("stop"):
            target = insn.get("jump", tails.get(pc))
            if target in at:
                work.append(at[target])
            elif target is not None:
                ends.add(target)
            else:
                return None
        else:
            work.append(index + 1)
    return ends


def check_block_arithmetic(decoded, symbols, owner):
    """The two private blocks, or their saved-page tops, exactly."""
    region = symbols["__be_mvp_hart_region_start"]
    require(region == HART_REGION,
            f"the hart region starts at 0x{region:x}, not 0x{HART_REGION:x}")
    require(all(size == 4 for _, size, _ in decoded),
            f"{owner} uses a compressed instruction in its block check")
    words = [word for _, _, word in decoded]
    compared = []
    for index, word in enumerate(words):
        if word & 0x7F != 0x63:
            continue
        for register in ((word >> 15) & 0x1F, (word >> 20) & 0x1F):
            value = materialized(words, index, register)
            if value is not None:
                compared.append(value)
    entry = owner in (MVP_ENTRY, MVP_CONFINE_ENTRY)
    offset = 0 if entry else LAYOUT["BLOCK_SAVED_OFFSET"]
    wanted = tuple(block + offset for block in BLOCKS)
    require(all(compared.count(address) == 1 for address in wanted),
            f"{owner} does not require exactly the private blocks "
            f"{[hex(address) for address in wanted]}")
    if entry:
        stack_adds = []
        for index, word in enumerate(words):
            if word & 0xFE00707F == 0x33 and (word >> 7) & 0x1F == 2 and \
                    (word >> 15) & 0x1F == 11:
                stack_adds.append(materialized(
                    words, index, (word >> 20) & 0x1F))
        require(stack_adds == [LAYOUT["BLOCK_STACK_TOP_OFFSET"]],
                f"{owner} does not take the block's stack top at "
                f"+0x{LAYOUT['BLOCK_STACK_TOP_OFFSET']:x}")


def check_hart_entry(decoded, symbols, owner=MVP_ENTRY, call=MVP_HART_MAIN):
    """A started hart: sp at its block's stack top before any memory
    access, then its C, or the park; in a boundary-on image the confining
    stub (OWNER) too, whose C is the executor's confine (CALL)."""
    label = "hart entry" if owner == MVP_ENTRY else owner
    require(all(size == 4 for _, size, _ in decoded),
            f"{label} holds a compressed instruction")
    words = [word for _, _, word in decoded]
    require(not any(word & 0x7F in (0x03, 0x23, 0x2F) or
                    system_kind(word) is not None for word in words),
            f"{label} accesses memory or a CSR")
    stack = [index for index, word in enumerate(words)
             if word & 0xFE00707F == 0x33 and (word >> 7) & 0x1F == 2]
    require(len(stack) == 1 and (words[stack[0]] >> 15) & 0x1F == 11 and
            words[stack[0] - 1] & 0x7F == 0x37 and
            (words[stack[0] - 1] >> 7) & 0x1F ==
            (words[stack[0]] >> 20) & 0x1F and
            words[stack[0] - 1] & 0xFFFFF000 ==
            LAYOUT["BLOCK_STACK_TOP_OFFSET"],
            f"{label} does not set sp to a1 plus the block's stack top")
    targets = [(target, link) for _, target, link in references(decoded)
               if link is not None]
    require(targets == [(symbols[call], 1), (symbols[MVP_PARK], 0)],
            f"{label} does not call {call} and else park")
    check_block_arithmetic(decoded, symbols, owner)


def resume_checks(symbols, profile):
    """Every check the resume tail must make, and nothing else."""
    return {
        ("eq", "sscratch", MASK64, "arg:a0"),
        ("ne", "sscratch", MASK64,
         LAYOUT["G0_BLOCK_HPA"] + LAYOUT["BLOCK_SAVED_OFFSET"]),
        ("eq", "sscratch", MASK64,
         LAYOUT["G1_BLOCK_HPA"] + LAYOUT["BLOCK_SAVED_OFFSET"]),
        ("eq", "satp", MASK64, 0),
        ("eq", "stvec", MASK64, symbols[MVP_VECTOR]),
        ("eq", "sie", MASK64,
         SIE_SSIE | SIE_STIE if profile == "mvp" else SIE_SSIE),
        ("eq", "sstatus", 0xDE722, f"mem:a0+{EXIT_WORDS[0][1]}&0x100"),
        ("eq", "hstatus", 0x73F380 & ~HSTATUS_SPVP, 0x80),
        ("eq", "hedeleg", MASK64, "arg:a2"),
        ("eq", "hideleg", MASK64, 0x40),
        ("eq", "hie", MASK64 & ~0x40, 0),
        ("eq", "hvip", 0x444, 0),
        ("eq", "hcounteren", MASK64, 0x2),
        ("eq", "htimedelta", MASK64, 0),
        ("eq", "henvcfg", MASK64, ARMED_HENVCFG[MONITOR]),
        ("eq", "hgeie", MASK64, 0),
        ("eq", "hgatp", MASK64, "arg:a1"),
    }


def check_resume(decoded, symbols, start, end, profile):
    """Call free; sepc and the GPRs; one SRET; the plan's checks."""
    require(all(size == 4 for _, size, _ in decoded),
            "resume tail holds a compressed instruction")
    words = [word for _, _, word in decoded]
    loads = [load_fields(word) for word in words]
    frame = 31  # t6 holds the saved page
    for number in range(1, 32):
        require((number, frame, (number - 1) * 8) in loads,
                f"resume tail does not restore x{number} from the frame")
    sepc = [index for index, fields in enumerate(loads)
            if fields and fields[1:] == (frame, FRAME_SEPC)]
    require(len(sepc) == 1 and index_writes(words, sepc[0] + 1, 0x141,
                                            loads[sepc[0]][0]),
            "resume tail does not restore sepc from the frame")
    terminal = symbols[MVP_HART_TERMINAL]
    pairs = {pc: (target, link)
             for pc, target, link in references(decoded, MVP_RESUME)}
    for pc, _, word in decoded:
        opcode = word & 0x7F
        if opcode == 0x63:
            offset = (word >> 31) << 12 | ((word >> 7) & 1) << 11 | \
                ((word >> 25) & 0x3F) << 5 | ((word >> 8) & 0xF) << 1
            target = pc + signed(offset, 13)
            require(start <= target < end,
                    f"resume tail branches out at 0x{pc:x}")
        elif opcode == 0x6F:
            require((word >> 7) & 0x1F == 0 and
                    start <= pairs[pc][0] < end,
                    f"resume tail calls or jumps out at 0x{pc:x}")
        elif opcode == 0x67:
            require((word >> 7) & 0x1F == 0 and pc in pairs and
                    pairs[pc][0] == terminal,
                    f"resume tail leaves other than to the terminal at "
                    f"0x{pc:x}")
    srets = [index for index, word in enumerate(words) if word == 0x10200073]
    last_load = max(index for index, fields in enumerate(loads) if fields)
    require(len(srets) == 1 and srets[0] == last_load + 1,
            "resume tail does not end its GPR restore in its one SRET")
    writes, reads, checks, _ = track(decoded, (29, 30, 31))
    actual_writes = [(csr, operation, value)
                     for _, csr, operation, value in writes]
    require(actual_writes ==
            [("sstatus", "c", ("const", 0x100)),
             ("sstatus", "s", ("mem", "a0", EXIT_WORDS[0][1],
                               HSTATUS_SPVP)),
             ("sepc", "w", ("mem", "a0", FRAME_SEPC, MASK64))],
            "resume tail does not clear SPP, set it from the saved SPVP, "
            f"and then write only sepc from the frame: {actual_writes}")
    found = {check[1:] for check in checks}
    wanted = resume_checks(symbols, profile)
    require(len(checks) == len(found) and found == wanted,
            f"resume checks differ: missing "
            f"{sorted(map(str, wanted - found))}, extra "
            f"{sorted(map(str, found - wanted))}")
    require("vsatp" not in {csr for _, csr in reads},
            "resume tail reads vsatp, which the guest owns")
    check_block_arithmetic(decoded, symbols, MVP_RESUME)


def check_resume_cheri(decoded, symbols, start, end, profile):
    """Call free; sepc and the GPRs; one SRET; the plan's checks: the
    CHERI-aware monitor's (beryllium-cheri, --monitor cheri)."""
    require(all(size == 4 for _, size, _ in decoded),
            "resume tail holds a compressed instruction")
    words = [word for _, _, word in decoded]
    loads = [load_fields(word) for word in words]
    frame = 31  # t6 holds the saved page
    # beryllium-cheri: every register returns whole from the capability
    # frame, by LC through ct6, sscratchc, in Capability Pointer Mode, after
    # the guest's ddc; a register the dispatch changed returns as its
    # integer, untagged (the merge: an integer store over the slot's
    # address and a zero store over its metadata). The merge's loop is
    # checked for those two stores, not proved.
    capability_at = max((index for index, word in enumerate(words)
                         if word == MODESW_CAP), default=-1)
    require(capability_at >= 0 and
            capability_at + 1 < len(words) and
            words[capability_at + 1] == CSRRS_CT6_SSCRATCH,
            "resume tail does not take ct6 from sscratchc in Capability "
            "Pointer Mode")
    tail = [lc_fields(word) for word in words[capability_at + 2:]]
    for number in range(1, 32):
        require((number, frame, CAP_FRAME + 16 * number) in tail,
                f"resume tail does not restore c{number} whole from the "
                f"capability frame")
    tail_pairs = list(zip(words[capability_at + 2:],
                          words[capability_at + 3:]))
    require(any(lc_fields(first) is not None and
                lc_fields(first)[1:] == (frame, CAP_FRAME) and
                ddc_access(second) == ("write", lc_fields(first)[0])
                for first, second in tail_pairs),
            "resume tail does not restore the guest's ddc whole")
    merges = [store_fields(word) for word in words[:capability_at]]
    require(any(fields and fields[0] == 0 and fields[2] == 8
                for fields in merges) and
            any(fields and fields[0] != 0 and fields[2] == 0
                for fields in merges),
            "resume tail does not untag a changed register's slot")
    sepc = [index for index, fields in enumerate(loads)
            if fields and fields[1:] == (frame, FRAME_SEPC)]
    require(len(sepc) == 1 and index_writes(words, sepc[0] + 1, 0x141,
                                            loads[sepc[0]][0]),
            "resume tail does not restore sepc from the frame")
    terminal = symbols[MVP_HART_TERMINAL]
    pairs = {pc: (target, link)
             for pc, target, link in references(decoded, MVP_RESUME)}
    for pc, _, word in decoded:
        opcode = word & 0x7F
        if opcode == 0x63:
            offset = (word >> 31) << 12 | ((word >> 7) & 1) << 11 | \
                ((word >> 25) & 0x3F) << 5 | ((word >> 8) & 0xF) << 1
            target = pc + signed(offset, 13)
            require(start <= target < end,
                    f"resume tail branches out at 0x{pc:x}")
        elif opcode == 0x6F:
            require((word >> 7) & 0x1F == 0 and
                    start <= pairs[pc][0] < end,
                    f"resume tail calls or jumps out at 0x{pc:x}")
        elif opcode == 0x67:
            require((word >> 7) & 0x1F == 0 and pc in pairs and
                    pairs[pc][0] == terminal,
                    f"resume tail leaves other than to the terminal at "
                    f"0x{pc:x}")
    srets = [index for index, word in enumerate(words) if word == 0x10200073]
    last_load = max(index for index, word in enumerate(words)
                    if lc_fields(word))
    require(len(srets) == 1 and srets[0] == last_load + 1 and
            lc_fields(words[last_load]) == (frame, frame,
                                             CAP_FRAME + 16 * frame),
            "resume tail does not end its restore, ct6 last, in its one SRET")
    writes, reads, checks, _ = track(decoded, (29, 30, 31))
    actual_writes = [(csr, operation, value)
                     for _, csr, operation, value in writes if csr != "ddc"]
    require(actual_writes ==
            [("sstatus", "c", ("const", 0x100)),
             ("sstatus", "s", ("mem", "a0", EXIT_WORDS[0][1],
                               HSTATUS_SPVP)),
             ("sepc", "w", ("mem", "a0", FRAME_SEPC, MASK64))],
            "resume tail does not clear SPP, set it from the saved SPVP, "
            f"and then write only sepc from the frame: {actual_writes}")
    found = {check[1:] for check in checks}
    wanted = resume_checks(symbols, profile)
    require(len(checks) == len(found) and found == wanted,
            f"resume checks differ: missing "
            f"{sorted(map(str, wanted - found))}, extra "
            f"{sorted(map(str, found - wanted))}")
    require("vsatp" not in {csr for _, csr in reads},
            "resume tail reads vsatp, which the guest owns")
    check_block_arithmetic(decoded, symbols, MVP_RESUME)


def index_writes(words, index, csr, register):
    """Whether words[index] writes csr from register."""
    if index >= len(words):
        return False
    word = words[index]
    return system_kind(word) == "csr" and csr_write(word) == csr and \
        (word >> 15) & 0x1F == register and (word >> 12) & 7 == 1


def call_target(flat, offset, pc):
    """Target of an auipc ra / jalr ra pair at offset, or None."""
    auipc, jalr = struct.unpack_from("<II", flat, offset)
    if auipc & 0xFFF != 0x097 or jalr & 0xFFFFF != 0x080E7:
        return None
    return pc + signed(auipc & 0xFFFFF000, 32) + signed(jalr >> 20, 12)


def check_layout(elf, flat, base, layout):
    phdrs, conjuncts = layout
    require(elf.entry == base, f"entry 0x{elf.entry:x} != base 0x{base:x}")
    require(elf.symbols.get("be_reset") == base, "be_reset is not the base")
    require(len(elf.segments) == len(phdrs),
            f"{len(elf.segments)} PT_LOAD segments, expected {len(phdrs)}")
    require(len(flat) == SPAN,
            f"flat image is 0x{len(flat):x} bytes, not 0x{SPAN:x}")
    covered = bytearray(SPAN)
    previous_end = base
    for (vaddr, paddr, offset, filesz, memsz, flags), (name, wanted) in zip(
            elf.segments, phdrs):
        require(vaddr == paddr, f"{name} 0x{vaddr:x} has paddr 0x{paddr:x}")
        require(not (flags & PF_W and flags & PF_X),
                f"{name} 0x{paddr:x} is writable and executable")
        require(flags == wanted, f"{name} flags {flags} != expected {wanted}")
        if (name, wanted) == POOL_PHDR:
            require(paddr == POOL and memsz == POOL_BYTES and filesz == 0,
                    f"MVP pool segment 0x{paddr:x}+0x{memsz:x} (file "
                    f"0x{filesz:x}) is not NOLOAD 0x{POOL_BYTES:x} bytes at "
                    f"0x{POOL:x}")
            previous_end = paddr + memsz
            continue
        if (name, wanted) == HART_PHDR:
            require(paddr == HART_REGION and memsz == HART_REGION_BYTES and
                    filesz == 0,
                    f"MVP hart segment 0x{paddr:x}+0x{memsz:x} (file "
                    f"0x{filesz:x}) is not NOLOAD "
                    f"0x{HART_REGION_BYTES:x} bytes at 0x{HART_REGION:x}")
            previous_end = paddr + memsz
            continue
        require(previous_end <= paddr and paddr + memsz <= base + SPAN,
                f"{name} 0x{paddr:x}+0x{memsz:x} is out of order or leaves "
                f"the span")
        start = paddr - base
        require(flat[start:start + filesz] ==
                elf.data[offset:offset + filesz],
                f"flat image differs from {name} at 0x{paddr:x}")
        covered[start:start + filesz] = b"\1" * filesz
        previous_end = paddr + memsz
    require(all(byte == 0 for byte, inside in zip(flat, covered)
                if not inside),
            "flat image has nonzero bytes outside the loaded segments")
    for conjunct in conjuncts:
        require(evaluate(conjunct, elf.symbols), f"ASSERT fails: {conjunct}")
    check_core(elf)


def check_core(elf):
    """The M11-3 core: each section in its first 0x20000 bytes is one of
    CORE_SECTIONS, inside its extent, so none lies
    in the unused span, which check_layout requires to be zero; the
    configuration in the input section."""
    for name, section in elf.sections.items():
        start, end = section[3], section[3] + section[5]
        if not BASE <= start < BASE + CORE_SPAN:
            continue
        require(name in CORE_SECTIONS,
                f"{name} at 0x{start:x} lies in the core, not one of its "
                f"sections")
        low, high = CORE_EXTENTS[CORE_SECTIONS[name]]
        require(low <= start and end <= high,
                f"{name} 0x{start:x}+0x{section[5]:x} leaves the core's "
                f"{CORE_SECTIONS[name]} extent 0x{low:x}-0x{high:x}")
    for name in CONFIG_SYMBOLS:
        value = elf.symbols.get(name)
        require(value is not None and elf.symbols["__be_input_start"] <=
                value < elf.symbols["__be_input_end"],
                f"{name} is not in the core's input section")


# One input section in a link map: GNU ld's, whose section name stands on
# its own line when it is long, and lld's, OBJECT:(SECTION). lld folds
# merged constants into <internal> sections, which name no object.
GNU_MAP_ENTRY = re.compile(
    r"^ (?P<section>[^\s*]\S*)\s+0x(?P<address>[0-9a-f]+)\s+"
    r"0x(?P<size>[0-9a-f]+)\s+(?P<object>\S+\.o)$", re.M)
LLD_MAP_ENTRY = re.compile(
    r"^\s+(?P<address>[0-9a-f]+)\s+[0-9a-f]+\s+(?P<size>[0-9a-f]+)\s+"
    r"\d+\s+(?P<object>\S+\.o):\((?P<section>[^)]+)\)$", re.M)


def map_entries(map_text):
    """Every input section the map places in the flat image with bytes:
    [(address, size, object file name, section)]."""
    entries = []
    for pattern in (GNU_MAP_ENTRY, LLD_MAP_ENTRY):
        for match in pattern.finditer(map_text):
            address = int(match.group("address"), 16)
            size = int(match.group("size"), 16)
            if size and BASE <= address < BASE + SPAN:
                entries.append((address, size,
                                pathlib.PurePath(match.group("object")).name,
                                match.group("section")))
    return entries


def check_placement(symbols, map_text, probe, extra_assembly):
    """M11-3's role layout: MVP inputs lie in the monitor role extents or
    the MVP region, accepted inputs never enter the MVP region, and the
    generated configuration alone occupies .monitor.input."""
    code = (symbols["__be_monitor_code_start"],
            symbols["__be_monitor_code_end"])
    data = (symbols["__be_monitor_data_start"],
            symbols["__be_monitor_data_end"])
    text = (symbols["__be_mvp_text_start"], symbols["__be_mvp_text_end"])
    region = (symbols["__be_mvp_region_start"],
              symbols["__be_mvp_region_end"])
    config = (symbols["__be_input_start"], symbols["__be_input_end"])
    for name in MVP_ASSEMBLY + extra_assembly:
        value = symbols.get(name)
        require(value is not None and
                (code[0] <= value < code[1] or text[0] <= value < text[1]),
                f"{name} at 0x{value or 0:x} is outside the two executable "
                "role sections")
    for name in MVP_C_ENTRIES + ((PROBE_HGATP,) if probe == "probe-platform"
                                 else ()):
        value = symbols.get(name)
        require(value is not None and
                (code[0] <= value < code[1] or text[0] <= value < text[1]),
                f"{name} at 0x{value or 0:x} is outside the executable "
                "role sections")
    require(map_text is not None, "no link map beside the monitor ELF")
    seen = set()
    for address, size, name, section in map_entries(map_text):
        roles = [(role, end, allowed) for role, start, end, allowed in
                 ROLE_EXTENTS if start <= address < end]
        require(len(roles) == 1,
                f"{name}'s {section} at 0x{address:x} is outside every "
                "role extent")
        role, end, allowed = roles[0]
        require(address + size <= end,
                f"{name}'s {section} at 0x{address:x}+0x{size:x} leaves "
                f"the {role} extent")
        require(name in allowed,
                f"{name}'s {section} at 0x{address:x} is not permitted "
                f"in the {role} extent")
        if name == "mvp-config.o" or config[0] <= address < config[1]:
            require(name == "mvp-config.o" and config[0] <= address and
                    address + size <= config[1],
                    f"{name}'s {section} at 0x{address:x}: the input "
                    f"section holds the configuration's constants alone")
            continue
        inside = (BASE <= address and address + size <= BASE + CORE_SPAN) or \
            (region[0] <= address and address + size <= region[1])
        if name in ("mvp-trap.o", "mvp-hartentry.o", "mvp-probe-arch.o") + \
                BREACH_OBJECTS:
            require(inside, f"{name}'s {section} at 0x{address:x} lies "
                    "outside the executable role extents")
            continue
        if name not in MVP_C_OBJECTS:
            require(not region[0] <= address < region[1],
                    f"{name}'s {section} at 0x{address:x} lies in the MVP "
                    f"region")
            continue
        require(inside, f"{name}'s {section} at 0x{address:x} lies outside "
                "the monitor and MVP role extents")
        seen.add(name)
    # The probe images place no payload and, running no control loop and
    # serving no console read, keep none of console input's code (M7); the
    # MVP image links no probe.
    wanted = set(MVP_C_OBJECTS) - ({"mvp-payload.o", "mvp-input.o"} if probe
                                   else {"mvp-probe.o"})
    require(seen == wanted,
            f"the link map places {sorted(seen)} in the MVP region, not "
            f"{sorted(wanted)}")


def payload_constants(elf, flat, base):
    """struct be_mvp_payload_layout as linked into the monitor."""
    address = elf.symbols.get(MVP_LAYOUT_SYMBOL)
    require(address is not None and base <= address and
            address + 64 <= base + len(flat),
            f"{MVP_LAYOUT_SYMBOL} is not in the flat image")
    names = ("staging_hpa", "kernel_offset", "kernel_bytes",
             "kernel_image_size", "dtb0_offset", "dtb1_offset", "dtb_bytes",
             "image_bytes")
    return dict(zip(names, struct.unpack_from("<8Q", flat, address - base)))


def linked_words(elf, flat, base, name, count):
    """count doublewords at a linked monitor symbol, from the flat image."""
    address = elf.symbols.get(name)
    require(address is not None and base <= address and
            address + 8 * count <= base + len(flat),
            f"{name} is not in the flat image")
    return struct.unpack_from(f"<{count}Q", flat, address - base)


def check_guests(elf, flat, base, variant=None, expect=None):
    """The two domains' windows, roots, VMIDs, hgatps, and harts, as
    linked."""
    words = linked_words(elf, flat, base, MVP_DESCS_SYMBOL, 12)
    descs = [dict(zip(("gpa", "hpa", "size", "pool", "vmid", "hart"),
                      words[domain * 6:domain * 6 + 6]))
             for domain in (0, 1)]
    hgatps = linked_words(elf, flat, base, MVP_HGATPS_SYMBOL, 2)
    words = linked_words(elf, flat, base, MVP_BINDINGS_SYMBOL, 6)
    bindings = [dict(zip(("hart", "vmid", "root"),
                         words[domain * 3:domain * 3 + 3]))
                for domain in (0, 1)]
    first, second = descs
    require(not (first["hpa"] < second["hpa"] + second["size"] and
                 second["hpa"] < first["hpa"] + first["size"]),
            f"the guest windows overlap: 0x{first['hpa']:x}+"
            f"0x{first['size']:x} and 0x{second['hpa']:x}+"
            f"0x{second['size']:x}")
    require(not (first["pool"] < second["pool"] + GUEST_POOL_BYTES and
                 second["pool"] < first["pool"] + GUEST_POOL_BYTES),
            f"the guest pools share a page: 0x{first['pool']:x} and "
            f"0x{second['pool']:x}")
    require(first["vmid"] != second["vmid"] and first["vmid"] and
            second["vmid"],
            f"the guest VMIDs are {first['vmid']} and {second['vmid']}, not "
            f"distinct and nonzero")
    require(hgatps[0] != hgatps[1],
            f"both guests' hgatp is 0x{hgatps[0]:x}")
    require(first["hart"] != second["hart"] and
            LAYOUT["CONTROL_HART"] not in (first["hart"], second["hart"]),
            f"the domain harts are {first['hart']} and {second['hart']}, "
            f"not distinct and other than the control hart")
    harts = list(HARTS)
    if variant == "hart-start":
        harts[1] = LAYOUT["VARIANT_HART_START_HART"]
    for guest, (desc, hgatp) in enumerate(zip(descs, hgatps)):
        require(hgatp == 8 << 60 | desc["vmid"] << 44 | desc["pool"] >> 12,
                f"G{guest} hgatp 0x{hgatp:x} is not Sv39x4 with VMID "
                f"{desc['vmid']} at its root 0x{desc['pool']:x}")
        require(POOL <= desc["pool"] and
                desc["pool"] + GUEST_POOL_BYTES <= POOL + POOL_BYTES and
                desc["pool"] % 0x4000 == 0,
                f"G{guest} root 0x{desc['pool']:x} is not a 16 KiB-aligned "
                f"pool inside the MVP pool")
        wanted = {"gpa": LAYOUT["GUEST_GPA"], "hpa": WINDOWS[guest],
                  "size": WINDOW_BYTES, "pool": ROOTS[guest],
                  "vmid": VMIDS[guest], "hart": harts[guest]}
        require(desc == wanted, f"G{guest} configuration {desc} is not "
                f"the layout's {wanted}")
        require(hgatp == HGATPS[guest],
                f"G{guest} hgatp 0x{hgatp:x} is not the layout's "
                f"0x{HGATPS[guest]:x}")
        require(bindings[guest] == {"hart": desc["hart"],
                                    "vmid": desc["vmid"],
                                    "root": desc["pool"]},
                f"G{guest} binding {bindings[guest]} is not its window's "
                f"hart, VMID, and root")
        if expect is not None and variant is None:
            domain = expect["domains"][guest]
            require({"hart": domain["hart"], "vmid": domain["vmid"],
                     "root": domain["root"]} == bindings[guest] and
                    domain["hgatp"] == hgatp and
                    domain["block"] == BLOCKS[guest],
                    f"G{guest} binding {bindings[guest]} is not the "
                    f"scenario's")
    return descs, hgatps


def check_region(constants):
    """The two private blocks and writer-owned mailboxes."""
    region, size = constants["HART_REGION_HPA"], constants["HART_REGION_BYTES"]
    block = constants["BLOCK_BYTES"]
    require(region == HART_REGION and size == HART_REGION_BYTES and
            region % 0x4000 == 0 and block == 0x4000,
            f"the hart region 0x{region:x}+0x{size:x} is not the layout's")
    require(constants["G0_HART_MAILBOX_HPA"] == region and
            constants["G1_HART_MAILBOX_HPA"] ==
            region + constants["HART_MAILBOX_BYTES"] and
            constants["G0_BLOCK_HPA"] ==
            region + 2 * constants["HART_MAILBOX_BYTES"] and
            constants["G1_BLOCK_HPA"] ==
            constants["G0_BLOCK_HPA"] + block and
            constants["G1_BLOCK_HPA"] + block == region + size,
            "the hart mailboxes and private blocks are not in order")
    for ring in RINGS:
        value = constants[ring]
        require(value and value & (value - 1) == 0,
                f"{ring} 0x{value:x} is not a power of two")
    cursor = 0
    for name, offset, length in BLOCK_AREAS:
        require(constants[offset] == cursor and constants[length] > 0,
                f"the block's {name} at +0x{constants[offset]:x} is not "
                f"at its offset +0x{cursor:x}")
        cursor += constants[length]
    require(cursor == block,
            f"the block's areas end at +0x{cursor:x}, not +0x{block:x}")
    top = constants["BLOCK_STACK_TOP_OFFSET"]
    require(top == constants["BLOCK_STACK_OFFSET"] +
            constants["BLOCK_STACK_BYTES"] == constants["BLOCK_SAVED_OFFSET"],
            f"the stack top +0x{top:x} is not the stack's end and the saved "
            f"page's start")
    require(constants["VARIANT_OUTBOUND_RING_BYTES"] <=
            constants["OUTBOUND_RING_BYTES"],
            "the ring-full variant's ring is larger than the outbound ring")
    require(constants["BLOCK_INBOUND_OFFSET"] == 0 and
            constants["INPUT_RING_OFFSET"] ==
            constants["INBOUND_RING_BYTES"] and
            constants["CONTROL_OUTBOUND_TAIL_OFFSET"] + 0x40 <=
            constants["CONTROL_MAILBOX_BYTES"] and
            constants["BLOCK_OUTBOUND_OFFSET"] == 0 and
            constants["HART_INPUT_TAIL_OFFSET"] + 0x40 <=
            constants["HART_MAILBOX_BYTES"],
            "the mailbox buffers and index lines leave their extents")


class Scenario:
    """The scenario an image is built for: two-guests (M0's, v1) when no
    --expect names another, te-poc (M1's, v2) with its expectation and
    authority report (planning/mvp-m1-plan.md, "Tests and evidence"), or
    one with pages, anchor (M2's, v3), whose expectation names
    EXPECT_PAGES and whose report gives its pages and grants; and whether
    its accepted-exit set names the management extension."""

    def __init__(self, expect=None, report=None):
        self.expect = expect
        self.report = report
        self.name = expect["scenario"] if expect else "two-guests"
        self.pages = bool(expect) and expect.get("schema") == EXPECT_PAGES
        # A v2 scenario stages its own DTB pair, with its roles' bootargs.
        self.dtb_variant = self.name if self.name in SCENARIO_DTB_VARIANTS \
            else None
        self.bootargs = [domain["bootargs"] for domain in
                         expect["domains"]] if expect else None
        # M0's v1 expectations name no accepted-exit set: M0's, no denial.
        self.denial = bool(expect) and \
            "denial" in expect.get("accepted_exits", [])
        # Only a v3 expectation names the management extension (M2).
        self.mgmt = bool(expect) and \
            "mgmt" in expect.get("accepted_exits", [])
        require(self.dtb_variant is None or report is not None,
                f"scenario {self.name} needs its authority report (--report)")
        require(report is None or self.dtb_variant is not None,
                f"scenario {self.name} has no authority report")

    def accepts_denial(self, variant=None):
        """Whether an image of this scenario names the denial entry: the
        scenario's accepted-exit set does, and the image is not no-inject."""
        return self.denial and variant != "no-inject"


TWO_GUESTS = Scenario()


def report_channel(report):
    """The channel record the authority report gives: the page's GPA (each
    endpoint's derived GPA), HPA, and size (its object's extent), and each
    endpoint's domain and rights (its memory grant's permissions)."""
    subjects = {subject["name"]: subject["domain_index"]
                for subject in report["subjects"]}
    objects = {item["name"]: item for item in report["objects"]}
    ends = {}
    for grant in report["grants"]:
        if grant["class"] == "channel":
            for permission in grant["permissions"]:
                require(permission in ("send", "receive") and
                        permission not in ends,
                        f"the report's channel grants are not one send and "
                        f"one receive: {grant}")
                ends[permission] = (grant["subject"], grant["object"])
    require(set(ends) == {"send", "receive"} and
            ends["send"][1] == ends["receive"][1],
            "the report holds no one channel with a sender and a receiver")
    extent = objects[ends["send"][1]]["extent"]
    pages = [name for name, item in objects.items()
             if item["class"] == "memory" and item["extent"] == extent]
    require(len(pages) == 1, "the report's channel has no one memory object")
    record = {"hpa": int(extent["base"], 16), "bytes": int(extent["size"], 16)}
    gpas = set()
    for side, prefix in (("send", "writer"), ("receive", "reader")):
        subject = ends[side][0]
        grants = [grant for grant in report["grants"]
                  if grant["subject"] == subject and
                  grant["object"] == pages[0] and grant["class"] == "memory"]
        require(len(grants) == 1,
                f"the report gives {subject} no one grant on {pages[0]}")
        gpas.add(int(grants[0]["derived"]["gpa"], 16))
        require(int(grants[0]["derived"]["size"], 16) == record["bytes"],
                f"{subject}'s grant on {pages[0]} is not the page's size")
        record[f"{prefix}_domain"] = subjects[subject]
        record[f"{prefix}_rights"] = sum(
            RIGHTS[permission] for permission in grants[0]["permissions"]
            if permission != "map")
    require(len(gpas) == 1, "the report's endpoints map the page at two GPAs")
    record["gpa"] = gpas.pop()
    return record


def check_channel_record(elf, flat, base, scenario):
    """The linked channel record and configuration identity: the authority
    report's for a scenario with a channel; else all zero and none."""
    require(elf.symbols.get(MVP_CHANNEL_SYMBOL) is not None,
            f"symbol {MVP_CHANNEL_SYMBOL} is missing")
    words = linked_words(elf, flat, base, MVP_CHANNEL_SYMBOL,
                         len(CHANNEL_WORDS))
    record = dict(zip(CHANNEL_WORDS, words))
    identity = elf.symbols.get(MVP_IDENTITY_SYMBOL)
    if scenario.report is None:
        require(not any(words),
                f"the linked channel record {record} is not all zero in a "
                f"scenario without a channel")
        require(MVP_IDENTITY_SYMBOL not in elf.symbols,
                f"{MVP_IDENTITY_SYMBOL} is linked in a scenario without a "
                f"channel")
        return record
    wanted = report_channel(scenario.report)
    require(record == wanted,
            f"the linked channel record {record} is not the report's "
            f"{wanted}")
    require(identity is not None and base <= identity and
            identity + IDENTITY_BYTES <= base + len(flat),
            f"{MVP_IDENTITY_SYMBOL} is not in the flat image")
    linked = flat[identity - base:identity - base + IDENTITY_BYTES]
    require(linked.hex() ==
            scenario.report["identity"]["configuration_identity"],
            f"the linked configuration identity {linked.hex()} is not the "
            f"report's")
    return record


def report_pages(report):
    """The pages the authority report gives (planning/mvp-m2-plan.md, Q1),
    in HPA order: each memory object inside the shared pages, its GPA
    (every grant's derived GPA), HPA, and size (its extent), and each
    domain's rights (its memory grant's permissions); a channel when a
    channel object has its extent, its writer the subject that sends and
    its reader the subject that receives; else a secret page, no writer,
    its reader the one subject granted it."""
    subjects = {subject["name"]: subject["domain_index"]
                for subject in report["subjects"]}
    objects = [item for item in report["objects"]
               if item["class"] == "memory" and
               SHARED_PAGES <= int(item["extent"]["base"], 16) <
               SHARED_PAGES + SHARED_PAGES_BYTES]
    require(1 <= len(objects) <= PAGES_MAX,
            f"the report gives {len(objects)} shared pages, not 1 to "
            f"{PAGES_MAX}")
    pages = []
    for item in sorted(objects, key=lambda item: int(item["extent"]["base"],
                                                     16)):
        extent = item["extent"]
        page = {"hpa": int(extent["base"], 16),
                "bytes": int(extent["size"], 16), "rights0": 0,
                "rights1": 0}
        gpas = set()
        holders = []
        for grant in report["grants"]:
            if grant["class"] != "memory" or grant["object"] != item["name"]:
                continue
            domain = subjects[grant["subject"]]
            require(page[f"rights{domain}"] == 0,
                    f"the report grants {grant['subject']} {item['name']} "
                    f"twice")
            page[f"rights{domain}"] = sum(
                RIGHTS[permission] for permission in grant["permissions"]
                if permission != "map")
            gpas.add(int(grant["derived"]["gpa"], 16))
            holders.append(domain)
        require(len(gpas) == 1,
                f"the report's grants map {item['name']} at {len(gpas)} "
                f"GPAs")
        page["gpa"] = gpas.pop()
        ends = {}
        for channel in report["objects"]:
            if channel["class"] != "channel" or channel["extent"] != extent:
                continue
            for grant in report["grants"]:
                if grant["class"] == "channel" and \
                        grant["object"] == channel["name"]:
                    for permission in grant["permissions"]:
                        require(permission not in ends,
                                f"{channel['name']} has two of {permission}")
                        ends[permission] = subjects[grant["subject"]]
        if ends:
            require(set(ends) == {"send", "receive"},
                    f"{item['name']}'s channel is not one send and one "
                    f"receive")
            page.update(kind=PAGE_CHANNEL, writer=ends["send"],
                        reader=ends["receive"])
        else:
            require(len(holders) == 1,
                    f"the report's secret page {item['name']} has "
                    f"{len(holders)} readers")
            page.update(kind=PAGE_SECRET, writer=PAGE_NONE,
                        reader=holders[0])
        pages.append(page)
    return pages


def symbol_size(elf, name):
    """A linked object's st_size, from its one symbol entry."""
    entries = elf.symbol_entries.get(name, [])
    require(len(entries) == 1, f"{name} is not one symbol")
    return struct.unpack_from("<Q", elf.data, entries[0] + 16)[0]


def inside_section(elf, name, address, size):
    """Whether [address, address + size) lies in a section."""
    section = elf.sections.get(name)
    return section is not None and section[3] <= address and \
        address + size <= section[3] + section[5]


def check_page_record(elf, flat, base, scenario):
    """An image with pages (planning/mvp-m2-plan.md): the linked pages, by
    their own rules and the layout's, and the scenario's report's; no
    channel record, since the denial path takes each root's walked leaves
    of every page (M2-3); the configuration identity the report's; and
    where the secret lies. Returns no channel record, and the pages."""
    symbols = elf.symbols
    for name in PAGE_SYMBOLS + (MVP_IDENTITY_SYMBOL,):
        require(symbols.get(name) is not None, f"symbol {name} is missing")
    require(MVP_CHANNEL_SYMBOL not in symbols,
            f"{MVP_CHANNEL_SYMBOL} is linked in an image with pages")
    size = symbol_size(elf, MVP_PAGES_SYMBOL)
    count = size // (8 * len(PAGE_WORDS))
    require(size == count * 8 * len(PAGE_WORDS) and 1 <= count <= PAGES_MAX,
            f"{MVP_PAGES_SYMBOL} is 0x{size:x} bytes, not 1 to {PAGES_MAX} "
            f"pages")
    words = linked_words(elf, flat, base, MVP_PAGES_SYMBOL,
                         count * len(PAGE_WORDS))
    pages = [dict(zip(PAGE_WORDS, words[index * len(PAGE_WORDS):
                                        (index + 1) * len(PAGE_WORDS)]))
             for index in range(count)]
    for index, page in enumerate(pages):
        rights = {domain: page[f"rights{domain}"] for domain in (0, 1)}
        if page["kind"] == PAGE_CHANNEL:
            valid = page["writer"] in (0, 1) and page["reader"] in (0, 1) \
                and page["writer"] != page["reader"] and \
                rights[page["writer"]] == RIGHTS["read"] | RIGHTS["write"] \
                and rights[page["reader"]] == RIGHTS["read"]
        else:
            valid = page["kind"] == PAGE_SECRET and \
                page["writer"] == PAGE_NONE and page["reader"] in (0, 1) and \
                rights[page["reader"]] == RIGHTS["read"] and \
                rights[1 - page["reader"]] == 0
        offset = page["hpa"] - SHARED_PAGES
        require(valid and page["bytes"] == PAGE and offset % PAGE == 0 and
                0 <= offset < SHARED_PAGES_BYTES and
                page["gpa"] == LAYOUT["CHANNEL_GPA"] + offset and
                all(other["hpa"] != page["hpa"] for other in pages[:index]),
                f"the linked page {index} {page} breaks the pages' rules")
    if scenario.report is not None:
        wanted = report_pages(scenario.report)
        require(pages == wanted,
                f"the linked pages {pages} are not the report's {wanted}")
    identity = symbols[MVP_IDENTITY_SYMBOL]
    require(base <= identity and identity + IDENTITY_BYTES <= base + len(flat),
            f"{MVP_IDENTITY_SYMBOL} is not in the flat image")
    if scenario.report is not None:
        linked = flat[identity - base:identity - base + IDENTITY_BYTES]
        require(linked.hex() ==
                scenario.report["identity"]["configuration_identity"],
                f"the linked configuration identity {linked.hex()} is not "
                f"the report's")
    for name, wanted_size in ((MVP_SECRET_SYMBOL, SECRET_BYTES),
                              (MVP_IDENTITY_SYMBOL, IDENTITY_BYTES)):
        require(inside_section(elf, ".mvp.rodata", symbols[name],
                               wanted_size) and
                symbol_size(elf, name) == wanted_size,
                f"{name} at 0x{symbols[name]:x} is not {wanted_size} bytes "
                f"in .mvp.rodata")
    return None, pages


def check_log_record(elf, flat, base, probe, scenario, pages):
    """The measurement log's linked objects (mvp/docs/log-profile.md, 2
    and 3.1; planning/mvp-m9-plan.md, D-1 to D-4): hart 0's page, 4 KiB
    and 4 KiB aligned, and its registers, each wholly inside the MVP
    region's BSS; the constants in .mvp.rodata, their sequence the
    image's, their count that sequence's with or without R2's five
    records, their scenario digest the expectation's, their
    configuration and policy identities the report's, or zero without
    one, and a probe's launch registers zero; the canary strictly inside
    the mvp-rodata range; and each R2 range's symbols, exactly its
    section's extent. Returns the
    constants, with the secret page's reader and the secret page as the
    image places it (None without pages), for the launch registers."""
    symbols = elf.symbols
    bss = (symbols["__be_mvp_bss_start"], symbols["__be_mvp_bss_end"])
    for name, size, align in ((MVP_LOG_SYMBOL, LOG_PAGE_BYTES,
                               LOG_PAGE_BYTES),
                              (MVP_LOG_REGISTERS_SYMBOL, LOG_REGISTERS_BYTES,
                               1)):
        require(symbols.get(name) is not None, f"symbol {name} is missing")
        address = symbols[name]
        require(symbol_size(elf, name) == size and address % align == 0 and
                bss[0] <= address and address + size <= bss[1],
                f"{name} at 0x{address:x} is not {size} bytes"
                f"{', 4 KiB aligned,' if align > 1 else ''} in the MVP "
                f"region's BSS")
    name = MVP_LOG_CONSTANTS_SYMBOL
    require(symbols.get(name) is not None, f"symbol {name} is missing")
    require(inside_section(elf, ".mvp.rodata", symbols[name],
                           LOG_CONSTANTS_BYTES) and
            symbol_size(elf, name) == LOG_CONSTANTS_BYTES,
            f"{name} at 0x{symbols[name]:x} is not {LOG_CONSTANTS_BYTES} "
            f"bytes in .mvp.rodata")
    ranges = {}
    for label, section, start, end in LOG_R2_RANGES:
        for name in (start, end):
            require(symbols.get(name) is not None,
                    f"symbol {name} is missing")
        extent = elf.sections.get(section)
        require(extent is not None and symbols[start] == extent[3] and
                symbols[end] == extent[3] + extent[5],
                f"the R2 range {label} 0x{symbols[start]:x}-"
                f"0x{symbols[end]:x} is not {section}'s extent")
        ranges[label] = (symbols[start], symbols[end])
    canary = symbols[MVP_LOG_CANARY_SYMBOL]
    require(ranges["mvp-rodata"][0] < canary and
            canary + LOG_CANARY_BYTES < ranges["mvp-rodata"][1],
            f"{MVP_LOG_CANARY_SYMBOL} at 0x{canary:x} is not strictly "
            f"inside the mvp-rodata range")
    at = symbols[MVP_LOG_CONSTANTS_SYMBOL] - base
    raw = flat[at:at + LOG_CONSTANTS_BYTES]
    count, sequence, r2 = struct.unpack_from("<III", raw, 160)
    constants = {"scenario": raw[0:32].hex(), "configuration":
                 raw[32:64].hex(), "policy": raw[64:96].hex(),
                 "launch": [raw[96:128].hex(), raw[128:160].hex()],
                 "count": count, "sequence": sequence, "r2": r2}
    wanted = 4 if probe else 3 if scenario.pages else \
        2 if scenario.report is not None else 1
    require(sequence == wanted,
            f"the linked log sequence {sequence} is not the image's {wanted}")
    require(r2 in (0, 1) and count == LOG_COUNTS[sequence] +
            LOG_R2_RECORDS * r2,
            f"the linked expected count {count} is not sequence "
            f"{sequence}'s with r2={r2}")
    zero = bytes(32).hex()
    identities = (zero, zero) if scenario.report is None or probe else (
        scenario.report["identity"]["configuration_identity"],
        scenario.report["identity"]["policy_identity"])
    require((constants["configuration"], constants["policy"]) == identities,
            f"the linked log identities {constants['configuration']} "
            f"{constants['policy']} are not {identities}")
    require(scenario.expect is None or probe or
            constants["scenario"] == scenario.expect["scenario_sha256"],
            f"the linked scenario digest {constants['scenario']} is not the "
            f"expectation's")
    require(not probe or constants["launch"] == [zero, zero],
            "a probe image's linked launch registers are not zero")
    constants["secret"] = None
    if pages:
        page = [page for page in pages if page["kind"] == PAGE_SECRET][0]
        secret = symbols[MVP_SECRET_SYMBOL] - base
        constants["secret"] = (page["reader"], bytes(
            flat[secret:secret + SECRET_BYTES]).ljust(PAGE, b"\0"))
    return constants


def check_launch_registers(constants, data, boot, variant=None):
    """Each domain's linked expected launch register (mvp/docs/
    log-profile.md, 2.6 and 2.7): from 32 zero bytes, R := SHA-256(R ||
    digest) over the SHA-256 of the domain's kernel, the file's length,
    and of its device tree, as the boot image DATA stages them, and, for
    the secret page's reader, of the secret page; wrong-measurement's
    with bit 0 of that domain's first byte flipped (Q16)."""
    kernel = data[KERNEL_OFFSET:KERNEL_OFFSET + boot["kernel_bytes"]]
    for domain in (0, 1):
        dtb = data[boot[f"dtb{domain}_offset"]:
                   boot[f"dtb{domain}_offset"] + DTB_BYTES]
        objects = [kernel, dtb]
        if constants["secret"] is not None and \
                constants["secret"][0] == domain:
            objects.append(constants["secret"][1])
        register = bytes(32)
        for item in objects:
            register = hashlib.sha256(
                register + hashlib.sha256(item).digest()).digest()
        if variant == "wrong-measurement" and len(objects) == 3:
            register = bytes([register[0] ^ 1]) + register[1:]
        require(constants["launch"][domain] == register.hex(),
                f"the linked launch register of domain {domain} "
                f"{constants['launch'][domain]} is not {register.hex()}, "
                f"its launch objects' in the boot image")


def check_canary(elf, flat, base, found, symbols):
    """The canary (planning/mvp-m9-plan.md, D-4): one 16-byte object in
    .mvp.rodata, and inert: no instruction forms an address inside it,
    and no aligned word of the flat image holds one."""
    require(symbols.get(MVP_LOG_CANARY_SYMBOL) is not None,
            f"symbol {MVP_LOG_CANARY_SYMBOL} is missing")
    canary = symbols[MVP_LOG_CANARY_SYMBOL]
    require(inside_section(elf, ".mvp.rodata", canary, LOG_CANARY_BYTES) and
            symbol_size(elf, MVP_LOG_CANARY_SYMBOL) == LOG_CANARY_BYTES,
            f"{MVP_LOG_CANARY_SYMBOL} at 0x{canary:x} is not "
            f"{LOG_CANARY_BYTES} bytes in .mvp.rodata")
    for owner, references in found.items():
        for pc, target, _ in references:
            require(not canary <= target < canary + LOG_CANARY_BYTES,
                    f"{owner} refers to {MVP_LOG_CANARY_SYMBOL} at 0x{pc:x}")
    for at in range(0, len(flat) - 7, 8):
        value = struct.unpack_from("<Q", flat, at)[0]
        require(not canary <= value < canary + LOG_CANARY_BYTES,
                f"the word at 0x{base + at:x} refers to "
                f"{MVP_LOG_CANARY_SYMBOL}")


def report_grants(report):
    """The management grants the authority report gives
    (planning/mvp-m2-plan.md, Q3), in its order: each domain grant's
    requester and target as domain indices and its permissions as
    bits."""
    subjects = {subject["name"]: subject["domain_index"]
                for subject in report["subjects"]}
    grants = []
    for grant in report["grants"]:
        if grant["class"] != "domain":
            continue
        require(grant["permissions"] and
                set(grant["permissions"]) <= set(MGMT_PERMISSIONS),
                f"the report's domain grant {grant} is not pause or "
                f"terminate")
        grants.append({"from": subjects[grant["subject"]],
                       "to": subjects[grant["object"]],
                       "permissions": sum(MGMT_PERMISSIONS[permission]
                                          for permission in
                                          grant["permissions"])})
    return grants


def check_mgmt_placement(elf, scenario):
    """Where the management extension's objects lie (planning/mvp-m2-plan.md;
    M11-8): in an image of a scenario with the extension, its symbols
    linked, the grants 1 to MGMT_GRANTS_MAX whole grants in the MVP control
    constants and hart 0's management state in the control writable-data
    extent; in any other image, none of them linked. Checked before the
    code's rules, so that each object's placement is refused in its own
    words where a more general rule (M11-8's C9 or C10) would otherwise
    see the misplaced object first. Returns the grants' count, or None."""
    symbols = elf.symbols
    if not scenario.mgmt:
        for name in MGMT_SYMBOLS:
            require(name not in symbols,
                    f"{name} is linked in an image without the management "
                    f"extension")
        return None
    for name in MGMT_SYMBOLS:
        require(symbols.get(name) is not None, f"symbol {name} is missing")
    address = symbols[MVP_GRANTS_SYMBOL]
    size = symbol_size(elf, MVP_GRANTS_SYMBOL)
    count = size // (8 * len(GRANT_WORDS))
    low = symbols["__be_mvp_control_constants_start"]
    high = symbols["__be_mvp_control_constants_end"]
    require(size == count * 8 * len(GRANT_WORDS) and
            1 <= count <= MGMT_GRANTS_MAX and
            low <= address and address + size <= high,
            f"{MVP_GRANTS_SYMBOL} at 0x{address:x} is not 1 to "
            f"{MGMT_GRANTS_MAX} grants in the MVP control constants")
    state = symbols[MVP_MGMT_STATE_SYMBOL]
    state_size = symbol_size(elf, MVP_MGMT_STATE_SYMBOL)
    require(state_size and symbols["__be_control_data_start"] <= state and
            state + state_size <= symbols["__be_control_data_end"],
            f"{MVP_MGMT_STATE_SYMBOL} at 0x{state:x} is not in the control "
            f"writable-data extent")
    return count


def check_mgmt_record(elf, flat, base, scenario):
    """An image of a scenario with the management extension
    (planning/mvp-m2-plan.md): the linked grants, by their own rules and
    the scenario's report's and expectation's; where they and hart 0's
    management state lie (check_mgmt_placement()); and the extension's
    functions linked. An image of any other scenario links none of them.
    Returns the grants."""
    count = check_mgmt_placement(elf, scenario)
    if count is None:
        return None
    words = linked_words(elf, flat, base, MVP_GRANTS_SYMBOL,
                         count * len(GRANT_WORDS))
    grants = [dict(zip(GRANT_WORDS, words[index * len(GRANT_WORDS):
                                          (index + 1) * len(GRANT_WORDS)]))
              for index in range(count)]
    for index, grant in enumerate(grants):
        require(grant["from"] in (0, 1) and grant["to"] in (0, 1) and
                grant["from"] != grant["to"] and
                grant["permissions"] in (1, 2, 3) and
                all((other["from"], other["to"]) !=
                    (grant["from"], grant["to"]) for other in grants[:index]),
                f"the linked grant {index} {grant} breaks the grants' rules")
    expected = [{"from": grant["from"], "to": grant["to"],
                 "permissions": sum(MGMT_PERMISSIONS[permission]
                                    for permission in grant["permissions"])}
                for grant in scenario.expect.get("grants", [])]
    require(grants == expected,
            f"the linked grants {grants} are not the expectation's "
            f"{expected}")
    if scenario.report is not None:
        wanted = report_grants(scenario.report)
        require(grants == wanted,
                f"the linked grants {grants} are not the report's {wanted}")
    return grants


def check_mvp_layout(constants):
    """The MVP region and the flat image (Plan revision M0-A.1): the region
    at most 0x40000 bytes, 16 KiB aligned, right after the hart region, and
    ending the flat image, whose first bytes are the core."""
    region, size = constants["REGION_HPA"], constants["REGION_BYTES"]
    image = constants["IMAGE_BYTES"]
    require(size <= 0x40000,
            f"the MVP region is 0x{size:x} bytes, more than 0x40000")
    require(region % 0x4000 == 0 and region ==
            constants["HART_REGION_HPA"] + constants["HART_REGION_BYTES"],
            f"the MVP region 0x{region:x} does not follow the hart region, "
            f"16 KiB aligned")
    require(region + size == constants["MONITOR_HPA"] + image and
            constants["CORE_BYTES"] == CORE_SPAN,
            f"the MVP region's end 0x{region + size:x} does not end the "
            f"flat image of 0x{image:x} bytes after the core")


def profile_count(entries, label):
    """NAPOT-shaped entries, coalesced when adjacent with equal rights."""
    ordered = sorted(entries, key=lambda entry: entry[1])
    merged = []
    for name, base, size, rights in ordered:
        require(size >= 0x1000 and size & (size - 1) == 0 and
                base & (size - 1) == 0,
                f"{label}'s {name} extent 0x{base:x}+0x{size:x} is not "
                "power-of-two sized and aligned")
        require(not merged or merged[-1][1] <= base,
                f"{label}'s {name} extent overlaps its preceding entry")
        if merged and merged[-1][1] == base and merged[-1][2] == rights:
            merged[-1] = (merged[-1][0], base + size, rights)
        else:
            merged.append((base, base + size, rights))
    return len(merged)


def check_profiles(constants, scenario):
    """D-5's control and VS-domain-hart profiles, each at most nine."""
    control = [
        ("monitor control", constants["MONITOR_CONTROL_TEXT_HPA"],
         constants["MONITOR_CONTROL_TEXT_BYTES"], "rx"),
        ("monitor shared", constants["MONITOR_SHARED_TEXT_HPA"],
         constants["MONITOR_SHARED_TEXT_BYTES"], "rx"),
        ("MVP control", constants["MVP_CONTROL_TEXT_HPA"],
         constants["MVP_CONTROL_TEXT_BYTES"], "rx"),
        ("control data", constants["CONTROL_PROFILE_HPA"],
         constants["CONTROL_PROFILE_BYTES"], "rw"),
        ("sealed", constants["MVP_SEALED_HPA"],
         constants["MVP_SEALED_BYTES"], "r"),
        ("measurement log", constants["MVP_LOG_HPA"],
         constants["MVP_LOG_BYTES"], "r"),
        ("G0 control mailbox", constants["G0_CONTROL_MAILBOX_HPA"],
         constants["CONTROL_MAILBOX_BYTES"], "rw"),
        ("G1 control mailbox", constants["G1_CONTROL_MAILBOX_HPA"],
         constants["CONTROL_MAILBOX_BYTES"], "rw"),
        ("hart mailbox pair", constants["G0_HART_MAILBOX_HPA"],
         2 * constants["HART_MAILBOX_BYTES"], "r"),
    ]
    count = profile_count(control, "control profile")
    require(count == 8,
            f"the control profile uses {count} entries, not 8")

    page_rights = [[], []]
    if scenario.report is not None:
        if scenario.pages:
            for page in report_pages(scenario.report):
                for domain in (0, 1):
                    if page[f"rights{domain}"]:
                        page_rights[domain].append(
                            (f"declared page {len(page_rights[domain])}",
                             page["hpa"], page["bytes"],
                             f"page-{page[f'rights{domain}']}"))
        else:
            channel = report_channel(scenario.report)
            page_rights[channel["writer_domain"]].append(
                ("declared channel", channel["hpa"], channel["bytes"],
                 f"page-{channel['writer_rights']}"))
            page_rights[channel["reader_domain"]].append(
                ("declared channel", channel["hpa"], channel["bytes"],
                 f"page-{channel['reader_rights']}"))

    expected = {"two-guests": (6, 6), "te-poc": (7, 7),
                "anchor": (8, 9)}[scenario.name]
    domains = (1, 0) if scenario.name == "anchor" else (0, 1)
    for domain in domains:
        root = constants[f"G{domain}_ROOT_HPA"]
        entries = [
            ("monitor shared", constants["MONITOR_SHARED_TEXT_HPA"],
             constants["MONITOR_SHARED_TEXT_BYTES"], "rx"),
            ("monitor VS-domain-hart", constants["MONITOR_DOMAIN_TEXT_HPA"],
             constants["MONITOR_DOMAIN_TEXT_BYTES"], "rx"),
            ("MVP VS-domain-hart", constants["MVP_DOMAIN_TEXT_HPA"],
             constants["MVP_DOMAIN_TEXT_BYTES"], "rx"),
            ("read cluster", root, constants["READ_CLUSTER_BYTES"], "r"),
            ("private state", constants[f"G{domain}_BLOCK_HPA"],
             constants["BLOCK_BYTES"], "rw"),
            ("hart mailbox", constants[f"G{domain}_HART_MAILBOX_HPA"],
             constants["HART_MAILBOX_BYTES"], "rw"),
            ("VS-domain window", constants[f"G{domain}_HPA"],
             constants["GUEST_BYTES"], "rwx"),
        ] + page_rights[domain]
        count = profile_count(entries, f"{scenario.name} G{domain} profile")
        require(count <= 9,
                f"the {scenario.name} G{domain} profile uses {count} "
                "entries, more than 9")
        require(count == expected[domain],
                f"the {scenario.name} G{domain} profile uses {count} "
                f"entries, not {expected[domain]}")


def check_control_entry_slot(elf, symbols, constants, boundary=False):
    """The control confined-entry slot, wholly inside its role: in a
    boundary-on image (M11-8, rule C1) the control hart's confined entry
    alone (at the slot's first byte by the linker script's ASSERT); in any
    other image, empty."""
    start = symbols["__be_control_confined_entry_slot_start"]
    end = symbols["__be_control_confined_entry_slot_end"]
    wanted = constants["CONTROL_CONFINED_ENTRY_HPA"]
    size = constants["CONTROL_CONFINED_ENTRY_BYTES"]
    control = (symbols["__be_mvp_control_text_start"],
               symbols["__be_mvp_control_text_end"])
    require((start, end) == (wanted, wanted + size),
            f"the control confined-entry slot is 0x{start:x}-0x{end:x}, "
            f"not 0x{wanted:x}-0x{wanted + size:x}")
    require(control[0] <= start < end <= control[1],
            "the control confined-entry slot leaves the control "
            "executable extent")
    overlaps = sorted((value, name) for value, length, name in elf.functions
                      if value < end and start < value + length)
    if not boundary:
        require(not overlaps,
                f"functions overlap the reserved control entry slot: "
                f"{sorted(name for _, name in overlaps)}")
        return
    # The entry's address, the slot's first byte, is the linker script's
    # ASSERT, which parse_asserts() requires and evaluate() re-evaluates.
    require([name for _, name in overlaps] == [CONTROL_ENTRY],
            f"the control entry slot holds "
            f"{[name for _, name in overlaps]}, not {CONTROL_ENTRY} alone "
            f"(C1)")


def check_park_entry_page(elf, symbols, constants):
    """The park OpenSBI domain's page holds its entry and no other code."""
    start = constants["PARK_HPA"]
    end = start + constants["PARK_BYTES"]
    occupants = sorted(
        (name, value, symbol_size(elf, name))
        for name, value in symbols.items()
        if value is not None and start <= value < end and
        not name.startswith("__be_"))
    functions = [(value, length, name) for value, length, name in elf.functions
                 if start <= value < end]
    require(occupants == [(MVP_PARK_ENTRY, symbols[MVP_PARK_ENTRY],
                           symbol_size(elf, MVP_PARK_ENTRY))] and
            functions == [(symbols[MVP_PARK_ENTRY],
                            symbol_size(elf, MVP_PARK_ENTRY),
                            MVP_PARK_ENTRY)] and
            symbols[MVP_PARK_ENTRY] == start and
            symbols[MVP_PARK_ENTRY] +
            symbol_size(elf, MVP_PARK_ENTRY) <= end,
            f"the park page 0x{start:x}-0x{end:x} holds "
            f"{[(name, hex(value), hex(length)) for name, value, length in occupants]}")


def check_monitor(toolchain, elf_data, flat, base, layout, map_text=None,
                  profile="mvp", variant=None, expect=None,
                  constants=LAYOUT, scenario=TWO_GUESTS):
    elf = Elf(elf_data)
    symbols = elf.symbols
    architecture = check_structure(elf)
    if map_text is not None:
        for section in MAP_SECTIONS:
            require(section in map_text, f"link map lacks {section}")
    _, hgatp_extra, probe = PROFILES[profile]
    # A probe image places the stub, not the payload: no payload layout.
    required = tuple(name for name in REQUIRED_SYMBOLS
                     if not probe or
                     name not in (MVP_LAYOUT_SYMBOL, CONTROL_LOOP)) + \
        ((PROBE_STUB,) if probe else ())
    for name in required + hgatp_extra + REGION_SYMBOLS:
        require(symbols.get(name) is not None, f"symbol {name} is missing")
    # M11-7: the boundary's symbols exactly in a boundary-on image.
    image = variant or scenario.name
    boundary = not probe and boundary_image(image)
    for name in BOUNDARY_SYMBOLS:
        require((name in symbols) == boundary,
                f"{name} is {'missing from' if boundary else 'linked in'} "
                f"the boundary-{'on' if boundary else 'off'} image {image}")
    # M11-7: a breach image's hook (D-10); every other image links none.
    breach = image in BREACH
    if breach:
        require(map_text is not None, f"the breach image {image} needs its "
                f"link map")
    else:
        check_no_breach(symbols, map_text, image)
    for name in symbols:
        require(not name.startswith("be_r4_"),
                f"R4 mechanism symbol {name} is linked")
        require(not name.startswith("be_r5_"),
                f"R5 symbol {name} is linked")
        require(probe or not name.startswith("be_mvp_probe"),
                f"probe symbol {name} is linked into the MVP image")
        require(name != PROBE_SWITCH or hgatp_extra,
                f"{PROBE_SWITCH} is linked outside the VMID images")
    check_layout(elf, flat, base, layout)
    check_control_entry_slot(elf, symbols, constants, boundary)
    check_park_entry_page(elf, symbols, constants)
    # An image with pages links them, and the secret, exactly when its
    # scenario declares pages (planning/mvp-m2-plan.md).
    pages = MVP_PAGES_SYMBOL in symbols
    require(pages == scenario.pages,
            f"the image {'links' if pages else 'does not link'} "
            f"{MVP_PAGES_SYMBOL}, but scenario {scenario.name} declares "
            f"{'no ' if not scenario.pages else ''}pages")
    for name in PAGE_SYMBOLS:
        require(pages or name not in symbols,
                f"{name} is linked in an image without pages")
    check_placement(symbols, map_text, profile if probe else None,
                    hgatp_extra)
    code_start = symbols["__be_monitor_code_start"]
    code_end = symbols["__be_monitor_code_end"]
    require(code_end <= MONITOR_TEXT_LIMIT, "monitor text overflow")
    require(symbols["__be_bss_end"] <= MONITOR_DATA_LIMIT,
            "monitor data overflow")
    quiesce = symbols[B1_QUIESCE]
    require(code_start <= quiesce < code_end,
            "be_b1_quiesce is outside monitor text")
    require(call_target(flat, 0, base) == quiesce,
            "be_reset does not first call be_b1_quiesce")
    require(struct.unpack_from("<I", flat, 8)[0] == RISCV_MV_S0_A0,
            "the accepted be_reset sequence does not follow the call")
    for name, (size, digest) in B2_R3_FUNCTIONS[toolchain].items():
        function = [(value, length) for value, length, label in elf.functions
                    if label == name]
        require(len(function) == 1 and function[0][1] == size,
                f"{name} is not one function of 0x{size:x} bytes")
        start = function[0][0] - base
        require(sha256(flat[start:start + size]) == digest,
                f"{name} differs from B2's")
    # The management objects' placement, before the code's rules (M11-8).
    check_mgmt_placement(elf, scenario)
    functions, words = check_instructions(
        elf, flat, base, ((code_start, code_end),
                          (symbols["__be_mvp_text_start"],
                           symbols["__be_mvp_text_end"])), symbols, profile,
        1 if scenario.accepts_denial(variant) else 0, boundary,
        map_text if breach else None, (scenario.mgmt, scenario.pages),
        BREACH[image][1] if breach else None)
    if boundary:
        check_partition_identity(elf, flat, base, symbols, image)
    check_guests(elf, flat, base, variant, expect)
    if pages:
        channel, pages = check_page_record(elf, flat, base, scenario)
    else:
        channel, pages = check_channel_record(elf, flat, base,
                                              scenario), None
    grants = check_mgmt_record(elf, flat, base, scenario)
    log = check_log_record(elf, flat, base, probe, scenario, pages)
    check_region(constants)
    check_mvp_layout(constants)
    check_profiles(constants, scenario)
    return {
        "channel": channel,
        "pages": pages,
        "grants": grants,
        "log": log,
        "architecture": architecture,
        "text_end": code_end,
        "data_end": symbols["__be_bss_end"],
        "mvp_text_end": symbols["__be_mvp_text_end"],
        "mvp_end": symbols["__be_mvp_region_end"],
        "functions": functions,
        "instructions": words,
        "payload": None if probe else payload_constants(elf, flat, base),
        "elf": elf,
        "boundary": boundary,
    }


# ----------------------------------------------------------- guest inputs
def read_pins(path):
    """guest/pins.txt: {file name: (sha256, bytes)} and the kernel facts."""
    files, kernel = {}, {}
    for number, line in enumerate(pathlib.Path(path).read_text(
            encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"file (\S+) sha256=([0-9a-f]{64}) "
                             r"bytes=([0-9]+)", line)
        if match:
            files[match.group(1)] = (match.group(2), int(match.group(3)))
            continue
        match = re.fullmatch(r"kernel (image_size|text_offset)=(0x[0-9a-f]+)",
                             line)
        if match:
            kernel[match.group(1)] = int(match.group(2), 16)
    for name in ("Image",) + tuple(dtb_name(guest) for guest in (0, 1)) + \
            tuple(dtb_name(guest, variant) for variant in DTB_VARIANTS
                  for guest in DTB_VARIANT_GUESTS[variant]) + \
            tuple(dtb_name(guest, variant) for variant in PINNED_SCENARIO_DTBS
                  for guest in (0, 1)) + \
            tuple(dtb_name(guest, SHELL_DTBS["two-guests"])
                  for guest in (0, 1)):
        require(name in files, f"{path} has no pin for {name}")
    require(set(kernel) == {"image_size", "text_offset"},
            f"{path} lacks the kernel image_size or text_offset pin")
    return files, kernel


def dtb_name(guest, variant=None):
    """A guest DTB's file name: mvp-guest-g<g>[-<variant>].dtb."""
    return f"mvp-guest-g{guest}" + (f"-{variant}" if variant else "") + \
        ".dtb"


def kernel_facts(kernel):
    """An independent RISC-V Image header reader: (bytes, image_size)."""
    require(len(kernel) >= 64, "kernel is shorter than its header")
    (_, _, text_offset, image_size, flags, _, _, _, magic, magic2,
     _) = struct.unpack_from("<IIQQQIIQ8s4sI", kernel)
    require(magic == b"RISCV\0\0\0", f"kernel magic {magic!r}")
    require(magic2 == b"RSC\x05", f"kernel magic2 {magic2!r}")
    require(text_offset == LAYOUT["KERNEL_TEXT_OFFSET"],
            f"kernel text_offset 0x{text_offset:x}")
    require(flags & 1 == 0, "kernel is big-endian")
    require(len(kernel) <= LAYOUT["KERNEL_FILE_MAX"],
            f"kernel file 0x{len(kernel):x} exceeds its budget")
    require(len(kernel) <= image_size <= LAYOUT["KERNEL_IMAGE_SIZE_MAX"],
            f"kernel image_size 0x{image_size:x} is below the file or over "
            f"its budget")
    require(LAYOUT["KERNEL_GPA"] + image_size <= LAYOUT["DTB_GPA"],
            "kernel span reaches the DTB slot")
    return len(kernel), image_size


def parse_fdt(blob):
    """An FDT reader: (reserve-map entries, {path: {property: bytes}})."""
    require(len(blob) >= 40, "DTB is shorter than its header")
    (magic, total, off_struct, off_strings, off_rsvmap, version, _, _,
     size_strings, size_struct) = struct.unpack_from(">10I", blob)
    require(magic == FDT_MAGIC, f"DTB magic 0x{magic:x}")
    require(total == len(blob) == DTB_BYTES,
            f"DTB totalsize 0x{total:x}, file 0x{len(blob):x}")
    require(version == 17, f"DTB version {version}")
    for offset, size in ((off_struct, size_struct),
                         (off_strings, size_strings), (off_rsvmap, 16)):
        require(40 <= offset and offset + size <= total,
                "DTB block leaves the blob")
    reserved, at = [], off_rsvmap
    while True:
        address, size = struct.unpack_from(">QQ", blob, at)
        if address == 0 and size == 0:
            break
        reserved.append((address, size))
        at += 16
    nodes, path, at = {}, [], off_struct
    end = off_struct + size_struct
    while at < end:
        token = struct.unpack_from(">I", blob, at)[0]
        at += 4
        if token == 1:  # FDT_BEGIN_NODE
            name_end = blob.index(b"\0", at)
            path.append(blob[at:name_end].decode("ascii"))
            at = align_up(name_end + 1, 4)
            key = "/" + "/".join(path[1:])
            require(key not in nodes, f"DTB node {key} appears twice")
            nodes[key] = {}
        elif token == 2:  # FDT_END_NODE
            require(path, "DTB ends a node it never began")
            path.pop()
        elif token == 3:  # FDT_PROP
            length, name_offset = struct.unpack_from(">II", blob, at)
            at += 8
            name_end = blob.index(b"\0", off_strings + name_offset)
            name = blob[off_strings + name_offset:name_end].decode("ascii")
            require(path, f"DTB property {name} outside a node")
            nodes["/" + "/".join(path[1:])][name] = blob[at:at + length]
            at = align_up(at + length, 4)
        elif token == 4:  # FDT_NOP
            continue
        elif token == 9:  # FDT_END
            break
        else:
            raise ImageError(f"DTB token 0x{token:x}")
    require(not path, "DTB leaves a node open")
    return reserved, nodes


def check_dt_pair(first, second):
    """The two guests' DTBs: equal but for /chosen/bootargs."""
    _, nodes = parse_fdt(first)
    _, other = parse_fdt(second)
    require(nodes["/chosen"]["bootargs"] != other["/chosen"]["bootargs"],
            "the guests' DTBs have equal bootargs")
    for tree in (nodes, other):
        del tree["/chosen"]["bootargs"]
    require(nodes == other,
            "the guests' DTBs differ in more than /chosen/bootargs")


def strings(*values):
    return b"".join(value.encode("ascii") + b"\0" for value in values)


def cells(*values):
    return b"".join(struct.pack(">I", value) for value in values)


def dt_contract(guest, variant=None, scenario_bootargs=None):
    """The plan's device tree for one guest, with one variant's change; for
    a v2 scenario's own DTB (te-poc's), the guest's bootargs followed by its
    role's arguments, as the scenario's expectation gives them."""
    gpa, size = LAYOUT["GUEST_GPA"], LAYOUT["GUEST_BYTES"]
    bootargs, isa = BOOTARGS + GUEST_ID_ARGS.format(guest), ISA_EXTENSIONS
    if variant in CONSOLE_VARIANTS:
        # A shell's: the guest's bootargs with rdinit=/init-shell before
        # the "--", then its role's arguments, if any, as its scenario's.
        head = BOOTARGS + f" rdinit={SHELL_INIT}" + GUEST_ID_ARGS.format(
            guest)
        require(scenario_bootargs is not None and (
            scenario_bootargs == head or
            scenario_bootargs.startswith(head + " be.role=")),
            f"G{guest}'s {variant} bootargs {scenario_bootargs!r} are not "
            f"the guest's with rdinit={SHELL_INIT}")
        bootargs = scenario_bootargs
    elif variant in CHERI_DTB_VARIANT_INITS and \
            guest in DTB_VARIANT_GUESTS[variant]:
        # beryllium-cheri: cap-store's G0: te-poc's with its init's rdinit=
        # before the "--", then its role's arguments.
        head = BOOTARGS + f" rdinit=/{CHERI_DTB_VARIANT_INITS[variant]}" + \
            GUEST_ID_ARGS.format(guest)
        require(scenario_bootargs is not None and
                scenario_bootargs.startswith(head + " be.role="),
                f"G{guest}'s {variant} bootargs {scenario_bootargs!r} are not "
                f"te-poc's with rdinit=/{CHERI_DTB_VARIANT_INITS[variant]}")
        bootargs = scenario_bootargs
    elif variant in SCENARIO_DTB_VARIANTS:
        require(scenario_bootargs is not None and
                scenario_bootargs.startswith(bootargs + " be.role="),
                f"G{guest}'s {variant} bootargs {scenario_bootargs!r} are not "
                f"the guest's with its role's arguments")
        bootargs = scenario_bootargs
    elif variant is not None and guest in DTB_VARIANT_GUESTS[variant]:
        if variant in DTB_VARIANT_INITS:
            bootargs = BOOTARGS + " rdinit=/" + DTB_VARIANT_INITS[variant] + \
                GUEST_ID_ARGS.format(guest)
        elif variant == "sbi-time":
            isa = tuple(name for name in isa if name != "sstc")
    return {
        "/": {"#address-cells": cells(2), "#size-cells": cells(2),
              "compatible": strings("beryllium,mvp-guest"),
              "model": strings("Beryllium MVP guest")},
        "/chosen": {"bootargs": strings(bootargs)},
        "/cpus": {"#address-cells": cells(1), "#size-cells": cells(0),
                  "timebase-frequency": cells(LAYOUT["TIMEBASE_HZ"])},
        "/cpus/cpu@0": {"device_type": strings("cpu"), "reg": cells(0),
                        "compatible": strings("riscv"),
                        "mmu-type": strings("riscv,sv39"),
                        "riscv,isa-base": strings("rv64i"),
                        "riscv,isa-extensions": strings(*isa)},
        "/cpus/cpu@0/interrupt-controller": {
            "compatible": strings("riscv,cpu-intc"),
            "interrupt-controller": b"", "#interrupt-cells": cells(1)},
        f"/memory@{gpa:x}": {"device_type": strings("memory"),
                             "reg": cells(gpa >> 32, gpa & 0xFFFFFFFF,
                                          size >> 32, size & 0xFFFFFFFF)},
    }


def check_dt(blob, guest, variant=None, scenario_bootargs=None):
    """The DT contract: these nodes and properties exactly, no reserve."""
    reserved, nodes = parse_fdt(blob)
    require(not reserved, f"DTB reserves memory: {reserved}")
    wanted = dt_contract(guest, variant, scenario_bootargs)
    require(set(nodes) == set(wanted),
            f"DTB nodes {sorted(nodes)} != {sorted(wanted)}")
    for path, properties in wanted.items():
        for name, value in properties.items():
            have = nodes[path].get(name)
            label = "memory node" if path.startswith("/memory") else \
                f"{path} {name}"
            require(have == value, f"DTB {label} is {have!r}, expected "
                    f"{value!r}")
        require(set(nodes[path]) == set(properties),
                f"DTB {path} has properties {sorted(nodes[path])}")


# ------------------------------------------------------------- boot image
def load_b3():
    spec = importlib.util.spec_from_file_location("check_b3_image",
                                                  B3_CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_ranges(image_size, constants=LAYOUT, channel=None, pages=None):
    """The eight ranges pairwise disjoint and inside S-mode RAM: the core,
    the pool, the hart region, the MVP region, the staged image, both
    windows, and the shared pages
    (planning/mvp-m2-plan.md, Q1), which lie above G1's window and begin
    with M1's channel page (planning/mvp-m1-plan.md, Q1); a linked channel
    record (channel) must name that page, and linked pages (pages) lie in
    the shared pages."""
    staging = constants["STAGING_HPA"]
    ranges = (("the core", constants["MONITOR_HPA"],
               constants["CORE_BYTES"]),
              ("the pool", constants["POOL_HPA"], constants["POOL_BYTES"]),
              ("the hart region", constants["HART_REGION_HPA"],
               constants["HART_REGION_BYTES"]),
              ("the MVP region", constants["REGION_HPA"],
               constants["REGION_BYTES"]),
              ("the staged image", staging, image_size),
              ("G0's window", constants["G0_HPA"], constants["GUEST_BYTES"]),
              ("G1's window", constants["G1_HPA"], constants["GUEST_BYTES"]),
              ("the shared pages", constants["SHARED_PAGES_HPA"],
               constants["SHARED_PAGES_BYTES"]))
    for index, (name, start, size) in enumerate(ranges):
        require(SMODE_RAM[0] <= start and start + size <= SMODE_RAM[1],
                f"{name} 0x{start:x}+0x{size:x} leaves S-mode RAM")
        for other, other_start, other_size in ranges[index + 1:]:
            require(not (start < other_start + other_size and
                         other_start < start + size),
                    f"{other} 0x{other_start:x}+0x{other_size:x} overlaps "
                    f"{name} 0x{start:x}+0x{size:x}")
    require(constants["SHARED_PAGES_HPA"] >=
            constants["G1_HPA"] + constants["GUEST_BYTES"],
            f"the shared pages 0x{constants['SHARED_PAGES_HPA']:x} are not "
            f"above G1's window")
    require(constants["CHANNEL_HPA"] == constants["SHARED_PAGES_HPA"] and
            constants["CHANNEL_BYTES"] <= constants["SHARED_PAGES_BYTES"],
            f"the channel page 0x{constants['CHANNEL_HPA']:x} is not the "
            f"shared pages' first page")
    require(channel is None or not channel["bytes"] or
            (channel["hpa"], channel["bytes"]) ==
            (constants["CHANNEL_HPA"], constants["CHANNEL_BYTES"]),
            f"the linked channel page {channel} is not the layout's")
    for page in pages or ():
        require(constants["SHARED_PAGES_HPA"] <= page["hpa"] and
                page["hpa"] + page["bytes"] <=
                constants["SHARED_PAGES_HPA"] +
                constants["SHARED_PAGES_BYTES"],
                f"the linked page 0x{page['hpa']:x} is not in the shared "
                f"pages")


def boot_parts(data, kernel_bytes):
    """(flat, kernel, gap, dtb0, dtb1) of a boot image, by the layout."""
    dtb_offset = align_up(KERNEL_OFFSET + kernel_bytes, PAGE)
    require(len(data) == dtb_offset + 2 * DTB_BYTES,
            f"boot image is 0x{len(data):x} bytes, not G1's DTB's end "
            f"0x{dtb_offset + 2 * DTB_BYTES:x}")
    return (data[MONITOR_OFFSET:MONITOR_OFFSET + SPAN],
            data[KERNEL_OFFSET:KERNEL_OFFSET + kernel_bytes],
            data[KERNEL_OFFSET + kernel_bytes:dtb_offset],
            data[dtb_offset:dtb_offset + DTB_BYTES],
            data[dtb_offset + DTB_BYTES:])


def ecall_sites(decoded):
    """The constant a7 (EID) and a6 (FID) at each ecall: [(pc, eid, fid)].

    Constants come from lui, addi, and addiw; anything else, or a join,
    leaves a register unknown (None), and an ecall leaves a0 and a1 so.
    """
    joins = set()
    for pc, size, word in decoded:
        insn = decode(word, size, pc)
        for key in ("jump", "branch"):
            if insn.get(key) is not None:
                joins.add(insn[key])
    regs, sites = {0: 0}, []
    for pc, size, word in decoded:
        if pc in joins:
            regs = {0: 0}
        opcode, rd = word & 0x7F, (word >> 7) & 0x1F
        source = regs.get((word >> 15) & 0x1F)
        if word == 0x00000073:
            sites.append((pc, regs.get(17), regs.get(16)))
            regs.pop(10, None)
            regs.pop(11, None)
            continue
        if size != 4 or rd == 0 or opcode in (0x23, 0x63):
            continue
        if opcode == 0x37:
            regs[rd] = signed(word & 0xFFFFF000, 32) & MASK64
        elif opcode in (0x13, 0x1B) and (word >> 12) & 7 == 0 and \
                source is not None:
            value = (source + signed(word >> 20, 12)) & MASK64
            regs[rd] = value if opcode == 0x13 else \
                signed(value & 0xFFFFFFFF, 32) & MASK64
        else:
            regs.pop(rd, None)
    return sites


# The shim's SBI calls (EID, FID): B3's DBCN write and SRST, and the start
# rule's HSM hart_start; the QEMU-only shim-rule variant adds a second
# hart_start and two hart_stop (planning/mvp-m0-plan.md, Image checker),
# and its start rule's wait for hart 0 adds hart_get_status and a second
# SRST, for its FAIL line (mvp/README.md, item 137).
SBI_DBCN, SBI_SRST, SBI_HSM = 0x4442434E, 0x53525354, 0x48534D
SHIM_CALLS = {
    False: sorted([(SBI_DBCN, 0), (SBI_SRST, 0), (SBI_HSM, 0)]),
    True: sorted([(SBI_DBCN, 0), (SBI_SRST, 0), (SBI_SRST, 0), (SBI_HSM, 0),
                  (SBI_HSM, 0), (SBI_HSM, 1), (SBI_HSM, 1), (SBI_HSM, 2)]),
}
# Every SYSTEM instruction the shim holds: B3's SIE clear, fence.i, and
# park, and the ecalls above; the shim-rule variant's wait adds two reads
# of time (csrrs rd, time, zero).
SHIM_SYSTEM = {False: {"csr": 1, "fence.i": 1, "wfi": 1},
               True: {"csr": 3, "fence.i": 1, "wfi": 1}}
SHIM_SIE_CLEAR = 0x10017073
SHIM_RDTIME, SHIM_RDTIME_MASK = 0xC0102073, 0xFFFFF07F
# The start rule's report line, beside B3's two.
SHIM_TEMPLATE = b"BE_MVP_SHIM: boot_hart=0x" + b"?" * 16 + \
    b" starting hart 0\n"
# The shim-rule variant's FAIL line, in its image alone (item 137).
SHIM_FAIL_TEMPLATE = b"BE_MVP_SHIM: FAIL hart 0 not started error=0x" + \
    b"?" * 16 + b" status=0x" + b"?" * 16 + b"\n"
# M11-7: a boundary-on boot image's shim has no start rule (D-6, D-12): its
# report line ends "refused", and its SBI calls are B3's DBCN write and
# SRST alone.
SHIM_TEMPLATE_ON = b"BE_MVP_SHIM: boot_hart=0x" + b"?" * 16 + b" refused\n"
SHIM_CALLS_ON = sorted([(SBI_DBCN, 0), (SBI_SRST, 0)])


def shim_template(boundary):
    """The start rule's report line, or a boundary-on shim's."""
    return SHIM_TEMPLATE_ON if boundary else SHIM_TEMPLATE


def check_shim(data, rule, boundary=False):
    """B3's instructions plus the start rule's ecall; hart_stop only in
    the shim-rule variant, with its wait's hart_get_status, second SRST,
    and two reads of time; no HSM call in a boundary-on image's."""
    require(not (rule and boundary),
            "the shim-rule variant is built with the boundary")
    b3 = load_b3()
    findings = []
    entry = b3.check_header(data, LAYOUT["UBOOT_TEXT_OFFSET"],
                            findings)["entry"]
    require(entry is not None, "the shim has no entry")
    end = data.index(b3.TEMPLATES[0])
    while end > entry and data[end - 4:end] == bytes(4):
        end -= 4
    decoded = instructions(data, entry, end, 0)
    require(all(size == 4 for _, size, _ in decoded),
            "the shim holds a compressed instruction")
    kinds = {}
    for pc, _, word in decoded:
        require(not floating_point(word, 4) and
                not decode(word, 4, pc).get("unknown"),
                f"the shim holds 0x{word:08x} at +0x{pc:x}")
        kind = system_kind(word)
        if kind is not None and kind != "ecall":
            kinds[kind] = kinds.get(kind, 0) + 1
            allowed = word == SHIM_SIE_CLEAR or \
                rule and word & SHIM_RDTIME_MASK == SHIM_RDTIME
            require(kind != "csr" or allowed,
                    f"the shim accesses a CSR other than sstatus.SIE"
                    f"{' and time' if rule else ''} at +0x{pc:x}")
    require(kinds == SHIM_SYSTEM[rule],
            f"the shim's SYSTEM instructions {kinds} != {SHIM_SYSTEM[rule]}")
    times = sum(word & SHIM_RDTIME_MASK == SHIM_RDTIME
                for _, _, word in decoded)
    require(times == (2 if rule else 0), f"the shim reads time {times} times")
    calls = sorted((call[1:] for call in ecall_sites(decoded)),
                   key=lambda call: (call[0] is None, call[0] or 0,
                                     call[1] is None, call[1] or 0))
    wanted = SHIM_CALLS_ON if boundary else SHIM_CALLS[rule]
    require(calls == wanted,
            f"the shim calls {[(hex(e or 0), f) for e, f in calls]}, "
            f"expected {[(hex(e), f) for e, f in wanted]}")


def check_descriptor(b3, data, findings):
    """B3's descriptor rule (magic, destination, length, payload offset),
    with the MVP flat image's length (Plan revision M0-A.1) for B2's."""
    if len(data) < b3.DESCRIPTOR_OFFSET + b3.DESCRIPTOR.size:
        findings.append("image shorter than the descriptor")
        return
    magic, dest, size, offset = b3.DESCRIPTOR.unpack_from(
        data, b3.DESCRIPTOR_OFFSET)
    if magic != b3.DESCRIPTOR_MAGIC:
        findings.append(f"descriptor magic {magic!r} != "
                        f"{b3.DESCRIPTOR_MAGIC!r}")
    if dest != BASE:
        findings.append(f"descriptor destination 0x{dest:x} != 0x{BASE:x}")
    if size != SPAN:
        findings.append(f"descriptor length 0x{size:x} != 0x{SPAN:x}")
    if offset != MONITOR_OFFSET:
        findings.append(f"descriptor payload offset 0x{offset:x} != "
                        f"0x{MONITOR_OFFSET:x}")


def check_boot(data, text_offset, flat, pins, kernel_expect, variant=None,
               constants=LAYOUT, scenario=TWO_GUESTS, channel=None,
               pages=None, boundary=None):
    """B3's header and descriptor, the ranges, and the placed payload, with
    the scenario's DTBs; the shim of a boundary-on image (BOUNDARY, else
    the image's own state by its name) without the start rule."""
    if boundary is None:
        boundary = boundary_image(variant or scenario.name)
    b3 = load_b3()
    files, kernel_pins = pins
    findings = []
    header = b3.check_header(data, text_offset, findings)
    image_size = header["image_size"] if header else len(data)
    check_ranges(image_size, constants, channel, pages)
    require(not findings, "; ".join(findings))
    check_descriptor(b3, data, findings)
    for template in b3.TEMPLATES + (shim_template(boundary),):
        if data[:b3.STUB_PAGE].count(template) != 1:
            findings.append("a shim report-line template is missing")
    rule = variant == "shim-rule"
    if data[:b3.STUB_PAGE].count(SHIM_FAIL_TEMPLATE) != int(rule):
        findings.append("the shim-rule variant's FAIL line template " + (
            "is missing" if rule else "outside that variant"))
    require(not findings, "; ".join(findings))
    check_shim(data, rule, boundary)
    require(len(data) <= LAYOUT["BOOT_IMAGE_MAX"],
            f"boot image 0x{len(data):x} exceeds its budget")
    image_pin, image_bytes = files["Image"]
    monitor, kernel, gap, *dtbs = boot_parts(data, image_bytes)
    require(monitor == flat, "flat image at 0x1000 differs from the monitor")
    require(not any(gap), "bytes between the kernel and the DTBs")
    for guest, dtb in enumerate(dtbs):
        dt_variant, bootargs, name = dtb_plan(guest, variant, scenario)
        check_dt(dtb, guest, dt_variant, bootargs)
        require(name in files, f"no pin for {name}")
        require(sha256(dtb) == files[name][0], f"DTB differs from {name}")
    check_dt_pair(*dtbs)
    if variant == "payload":
        require(kernel[KERNEL_MAGIC2_AT] == 0 and
                kernel[:KERNEL_MAGIC2_AT] ==
                kernel_expect[:KERNEL_MAGIC2_AT] and
                kernel[KERNEL_MAGIC2_AT + 1:] ==
                kernel_expect[KERNEL_MAGIC2_AT + 1:],
                "payload variant kernel is not the pinned kernel with "
                "magic2 RSC\\0")
    else:
        size, image_size_field = kernel_facts(kernel)
        require(size == image_bytes and sha256(kernel) == image_pin,
                "kernel differs from its pin")
        require(image_size_field == kernel_pins["image_size"],
                "kernel image_size differs from its pin")
    require(kernel_expect is None or sha256(kernel_expect) == image_pin,
            "the --kernel file differs from its pin")
    dtb_offset = KERNEL_OFFSET + len(kernel) + len(gap)
    return {"image_size": image_size, "kernel_bytes": image_bytes,
            "kernel_image_size": kernel_pins["image_size"],
            "dtb0_offset": dtb_offset, "dtb1_offset": dtb_offset + DTB_BYTES}


def shell_guests(scenario):
    """The guests a console variant runs a shell in: every one but the
    protected domain (Q27)."""
    roles = [domain.get("role") for domain in scenario.expect["domains"]] \
        if scenario.expect else [None, None]
    return tuple(guest for guest in (0, 1) if roles[guest] != "prot")


def dtb_plan(guest, variant, scenario):
    """GUEST's DTB in an image of VARIANT (None for the scenario's own):
    (dt_contract's variant, the bootargs it is given, the pin's name). A
    console variant's own expectation (its board run's image check,
    tools/k3-run.sh with tests/check-capture.py --check-image) holds the
    shell's bootargs already: rdinit=/init-shell is inserted only into a
    scenario's own."""
    if variant in CONSOLE_VARIANTS and guest in shell_guests(scenario):
        base = scenario.bootargs[guest] if scenario.bootargs else \
            BOOTARGS + GUEST_ID_ARGS.format(guest)
        shell = f" rdinit={SHELL_INIT} -- "
        return variant, base if shell in base else \
            base.replace(" -- ", shell, 1), \
            dtb_name(guest, SHELL_DTBS[scenario.name])
    if variant in CHERI_DTB_VARIANT_INITS:
        # beryllium-cheri: cap-store's G0 DTB its own, G1's te-poc's.
        if guest not in DTB_VARIANT_GUESTS[variant]:
            return scenario.dtb_variant, scenario.bootargs[guest], \
                dtb_name(guest, scenario.dtb_variant)
        return variant, scenario.bootargs[guest].replace(
            " -- ", f" rdinit=/{CHERI_DTB_VARIANT_INITS[variant]} -- ", 1), \
            dtb_name(guest, variant)
    dt_variant = variant if variant in DTB_VARIANTS else scenario.dtb_variant
    return dt_variant, scenario.bootargs[guest] if scenario.dtb_variant \
        else None, dtb_name(guest, dt_variant if dt_variant in
                            SCENARIO_DTB_VARIANTS or dt_variant and guest in
                            DTB_VARIANT_GUESTS[dt_variant] else None)


def launch_span(elf):
    """The flat image's span of the linked constants' two expected launch
    registers (src/mvp-log.h), which an image's own payload decides."""
    return (elf.symbols[MVP_LOG_CONSTANTS_SYMBOL] - BASE + LOG_LAUNCH_AT,
            2 * DIGEST_BYTES)


def own_spans(elf):
    """The flat image's spans that an image's own inputs decide: its
    expected launch registers (M9), and in a boundary-on image its
    descriptor's identity (M11-7), which rule 5 checks against that
    descriptor."""
    spans = [launch_span(elf)]
    if MVP_PARTITION_IDENTITY in elf.symbols:
        spans.append((elf.symbols[MVP_PARTITION_IDENTITY] - BASE, 32))
    return spans


def check_console_grants(elf_data, flat, reference_flat, scenario):
    """A console variant's monitor: its flat image the reference's but for
    its own spans (own_spans()) and bytes inside be_mvp_proposal, the MVP
    core profile's domain requests, each a grant's word going from 0 to 1,
    one per shell guest (mvp-config.c's BE_MVP_CORE_DOMAIN<d>_CONSOLE)."""
    elf = Elf(elf_data)
    entries = elf.symbol_entries.get("be_mvp_proposal", [])
    require(len(entries) == 1, "be_mvp_proposal is not one symbol")
    start = elf.symbols["be_mvp_proposal"] - BASE
    size = struct.unpack_from("<Q", elf.data, entries[0] + 16)[0]
    spans = own_spans(elf)
    require(len(flat) == len(reference_flat),
            "the console variant's flat image is not the reference's size")
    changed = [index for index in range(len(flat))
               if flat[index] != reference_flat[index] and
               not any(at <= index < at + length for at, length in spans)]
    require(all(start <= index < start + size for index in changed),
            f"the console variant's monitor differs from the scenario's "
            f"outside be_mvp_proposal, at 0x{BASE + changed[0]:x}"
            if changed else "")
    require(all(reference_flat[index] == 0 and flat[index] == 1
                for index in changed) and
            len(changed) == len(shell_guests(scenario)),
            f"the console variant's monitor changes {len(changed)} bytes of "
            f"be_mvp_proposal, not one grant word, 0 to 1, for each of its "
            f"{len(shell_guests(scenario))} shell domains")


def check_payload_constants(constants, boot):
    """The monitor's link-time payload layout equals the boot image's."""
    kernel = boot["kernel_bytes"]
    expected = {"staging_hpa": STAGING, "kernel_offset": KERNEL_OFFSET,
                "kernel_bytes": kernel,
                "kernel_image_size": boot["kernel_image_size"],
                "dtb0_offset": boot["dtb0_offset"],
                "dtb1_offset": boot["dtb1_offset"], "dtb_bytes": DTB_BYTES,
                "image_bytes": boot["image_size"]}
    for name, value in expected.items():
        require(constants[name] == value,
                f"payload constant {name} 0x{constants[name]:x} != "
                f"0x{value:x}")


def check_boot_elf(elf_data, data, boot):
    """The QEMU boot ELF: linked at L, and its loads are the file."""
    elf = Elf(elf_data)
    require(elf.entry == STAGING, f"boot ELF entry 0x{elf.entry:x} is not L")
    require([flags for *_, flags in elf.segments] == [5, 6, 4, 4],
            "boot ELF PT_LOAD flags are not R-X, RW, R, R")
    image = bytearray(len(data))
    for vaddr, paddr, offset, filesz, memsz, _ in elf.segments:
        require(vaddr == paddr and filesz == memsz and STAGING <= paddr and
                paddr + filesz <= STAGING + len(data),
                f"boot ELF segment 0x{paddr:x} leaves the image")
        image[paddr - STAGING:paddr - STAGING + filesz] = \
            elf.data[offset:offset + filesz]
    require(bytes(image) == data, "boot ELF loads differ from the boot image")
    for name, offset in (("be_mvp_guest_kernel", KERNEL_OFFSET),
                         ("be_mvp_guest_dtb0", boot["dtb0_offset"]),
                         ("be_mvp_guest_dtb1", boot["dtb1_offset"]),
                         ("__be_b3_image_end", len(data))):
        require(elf.symbols.get(name) == STAGING + offset,
                f"boot ELF {name} is not at L+0x{offset:x}")


def check_pic(img_path, data):
    """The second link, when the build left it beside the image."""
    pic = pathlib.Path(img_path).with_name("be-mvp-boot-pic.img")
    if pic.is_file():
        require(pic.read_bytes() == data,
                "the second link's image differs")


BOOT_TEXT_OFFSET = LAYOUT["UBOOT_TEXT_OFFSET"]


def check_image(toolchain, elf_data, flat, boot_img, pins, kernel, layout,
                map_text=None, boot_elf_data=None, img_path=None,
                profile="mvp", expect=None, constants=LAYOUT,
                scenario=TWO_GUESTS):
    """One toolchain's monitor and board boot image, together."""
    report = check_monitor(toolchain, elf_data, flat, BASE, layout, map_text,
                           profile, None, expect, constants, scenario)
    boot = check_boot(boot_img, BOOT_TEXT_OFFSET, flat, pins, kernel,
                      constants=constants, scenario=scenario,
                      channel=report["channel"], pages=report["pages"],
                      boundary=report["boundary"])
    if report["payload"] is not None:
        check_payload_constants(report["payload"], boot)
        check_launch_registers(report["log"], boot_img, boot)
    if boot_elf_data is not None:
        check_boot_elf(boot_elf_data, boot_img, boot)
    if img_path is not None:
        check_pic(img_path, boot_img)
    return report, boot


def outside(data, reference, allowed):
    """Offsets where data and reference differ outside the allowed spans."""
    require(len(data) == len(reference),
            f"size 0x{len(data):x} differs from the reference's "
            f"0x{len(reference):x}")
    edges = [0]
    for start, size in sorted(allowed):
        edges += [start, start + size]
    edges.append(len(data))
    for start, end in zip(edges[::2], edges[1::2]):
        if data[start:end] != reference[start:end]:
            return next(index for index in range(start, end)
                        if data[index] != reference[index])
    return None


def variant_monitor(name, monitor, flat, reference, layout, scenario, boot,
                    data):
    """A variant's own monitor: its boot image's, passing the MVP profile
    itself, its payload constants and expected launch registers its boot
    image's. Returns its ELF."""
    require(monitor is not None,
            f"variant {name} needs its monitor ELF and flat image")
    elf_data, monitor_flat, map_text = monitor
    require(monitor_flat == flat,
            f"variant {name}'s flat image is not its boot image's")
    report = check_monitor(reference["toolchain"], elf_data, monitor_flat,
                           BASE, layout, map_text, "mvp", name,
                           scenario=scenario)
    check_payload_constants(report["payload"], boot)
    check_launch_registers(report["log"], data, boot, name)
    return report["elf"]


def check_flip(name, elf, flat, data, reference, img_path):
    """self-report-flip (planning/mvp-m9-plan.md, D-4): its monitor and
    boot image the reference's but for bit 0 of be_mvp_log_canary's first
    byte, and its metadata, beside the image, naming both images'
    SHA-256."""
    canary = elf.symbols[MVP_LOG_CANARY_SYMBOL] - BASE
    for label, mine, theirs, at in (
            ("monitor", flat, reference["flat"], canary),
            ("boot image", data, reference["boot"], MONITOR_OFFSET + canary)):
        changed = [index for index in range(len(mine))
                   if mine[index] != theirs[index]] if \
            len(mine) == len(theirs) else None
        require(changed == [at] and mine[at] ^ theirs[at] == 1,
                f"variant {name}'s {label} is not the reference's with bit "
                f"0 of {MVP_LOG_CANARY_SYMBOL} flipped")
    require(img_path is not None, f"variant {name} needs its metadata")
    metadata = json.loads(read(pathlib.Path(img_path).with_name(
        "self-report-flip.json")))
    require(metadata.get("symbol") == MVP_LOG_CANARY_SYMBOL and
            metadata.get("bit") == 0 and
            metadata.get("nominal_image_sha256") == sha256(reference["boot"])
            and metadata.get("mutated_image_sha256") == sha256(data),
            f"variant {name}'s metadata does not name the canary's bit 0 "
            f"and both images' SHA-256")


def check_variant(name, boot_elf_data, data, reference, pins, kernel,
                  img_path=None, monitor=None, layout=None,
                  scenario=TWO_GUESTS):
    """A negative variant: the boot rules with its change, and no other."""
    require(name in VARIANTS, f"unknown variant {name}")
    # A console variant is its own scenario's, SCENARIO-shell; an off copy
    # its scenario's, SCENARIO-off; an off variant its variant's.
    copied = OFF_VARIANTS.get(name, name)
    require(name == f"{scenario.name}-shell" if name in CONSOLE_VARIANTS
            else OFF_COPIES[name] == scenario.name if name in OFF_COPIES
            else (copied in TE_POC_VARIANTS) == (scenario.name == "te-poc")
            and (copied in ANCHOR_VARIANTS + (FLIP_VARIANT,)) ==
            (scenario.name == "anchor"),
            f"variant {name} is not a variant of scenario {scenario.name}")
    flat = data[MONITOR_OFFSET:MONITOR_OFFSET + SPAN]
    boot = check_boot(data, BOOT_TEXT_OFFSET, flat, pins, kernel, name,
                      scenario=scenario)
    check_boot_elf(boot_elf_data, data, boot)
    if img_path is not None:
        check_pic(img_path, data)
    if name == "payload":
        allowed = [(KERNEL_OFFSET + KERNEL_MAGIC2_AT, 1)]
    elif name in DTB_VARIANTS:
        # Since M9 its own monitor, the reference's but for its expected
        # launch registers, which its DTBs change, and since M11-7 its
        # own descriptor's identity (own_spans()).
        elf = variant_monitor(name, monitor, flat, reference, layout,
                              scenario, boot, data)
        stray = outside(flat, reference["flat"], own_spans(elf))
        require(stray is None,
                f"variant {name}'s monitor differs from the reference's "
                f"outside its launch registers and identity, at "
                f"0x{BASE + stray:x}" if stray is not None else "")
        allowed = [(MONITOR_OFFSET, SPAN)] + [
            (boot[f"dtb{guest}_offset"], DTB_BYTES)
            for guest in DTB_VARIANT_GUESTS[name]]
    elif name == "shim-rule":
        require(not boundary_image(reference.get("name", scenario.name)),
                "shim-rule's reference is a boundary-on image, not "
                "two-guests-off")
        allowed = [(0, MONITOR_OFFSET)]
    elif name in OFF_COPIES:
        # Its own monitor, without the boundary; the payload the
        # reference's. Where the reference is built without the boundary
        # too (every CHERI-aware image, D-12), the off copy is the same
        # build, so the reference itself, byte for byte.
        variant_monitor(name, monitor, flat, reference, layout, scenario,
                        boot, data)
        allowed = [(0, MONITOR_OFFSET + SPAN)] if \
            boundary_image(scenario.name) else []
    elif name == FLIP_VARIANT:
        elf = variant_monitor(name, monitor, flat, reference, layout,
                              scenario, boot, data)
        check_flip(name, elf, flat, data, reference, img_path)
        allowed = [(MONITOR_OFFSET, SPAN)]
    elif name in CONSOLE_VARIANTS:
        # The monitor's grant words, which pass the MVP profile, its
        # launch registers, and each shell guest's DTB.
        variant_monitor(name, monitor, flat, reference, layout, scenario,
                        boot, data)
        check_console_grants(monitor[0], flat, reference["flat"], scenario)
        allowed = [(MONITOR_OFFSET, SPAN)] + [
            (boot[f"dtb{guest}_offset"], DTB_BYTES)
            for guest in shell_guests(scenario)]
    else:
        # A monitor variant's one compile-time switch changes code, not a
        # linked word: its monitor must pass the MVP profile itself; a
        # breach image's table is the declaration's (M11-7).
        elf = variant_monitor(name, monitor, flat, reference, layout,
                              scenario, boot, data)
        if name in BREACH:
            check_breach_table(name, elf, flat, data, boot)
        allowed = [(MONITOR_OFFSET, SPAN)]
    stray = outside(data, reference["boot"], allowed)
    require(stray is None,
            f"variant {name} differs from the reference at 0x{stray:x}"
            if stray is not None else "")
    require(data != reference["boot"] or
            name in OFF_COPIES and not boundary_image(scenario.name),
            f"variant {name} is the reference")
    return boot


def off_copy_mutations(name, boot_elf, data, reference, pins, kernel,
                       monitor, layout, scenario):
    """An off copy of an image built without the boundary (every
    CHERI-aware image, D-12): its own files with bit 0 of
    be_mvp_log_canary's first byte flipped (self-report-flip's change,
    which every other rule accepts), so no longer the reference, must be
    refused. Returns their number."""
    label = "its canary's bit 0 flipped"
    elf_data, flat, map_text = monitor
    canary = Elf(elf_data).symbols[MVP_LOG_CANARY_SYMBOL]
    value = bytes([flat[canary - BASE] ^ 1])
    mutated_elf, mutated_flat = bytearray(elf_data), bytearray(flat)
    mutated_data, mutated_boot_elf = bytearray(data), bytearray(boot_elf)
    patch(mutated_elf, mutated_flat, mutated_data, canary, value, BASE)
    # The boot ELF's load of the same byte, which its loads must match.
    address = STAGING + MONITOR_OFFSET + canary - BASE
    for vaddr, _, offset, filesz, _, _ in Elf(boot_elf).segments:
        if vaddr <= address < vaddr + filesz:
            mutated_boot_elf[offset + address - vaddr] ^= 1
            break
    try:
        check_variant(name, bytes(mutated_boot_elf), bytes(mutated_data),
                      reference, pins, kernel, None,
                      (bytes(mutated_elf), bytes(mutated_flat), map_text),
                      layout, scenario)
    except ImageError as error:
        require("differs from the reference at" in str(error),
                f"variant {name}'s mutation {label!r} rejected for another "
                f"reason: {error}")
        return 1
    raise ImageError(f"variant {name}'s mutation {label!r} was accepted")


def shim_rule_mutations(data, pins, kernel, scenario):
    """The shim-rule variant's wait for hart 0 (mvp/README.md, item 137):
    each rule of check_shim() and check_boot() on it refuses its mutation
    of the variant's boot image. Returns their number."""
    b3 = load_b3()
    entry = b3.check_header(data, LAYOUT["UBOOT_TEXT_OFFSET"], [])["entry"]
    decoded = instructions(data, entry, data.index(b3.TEMPLATES[0]), 0)

    def at(value):
        found = [pc for pc, _, word in decoded if word == value]
        require(len(found) == 1, f"the shim-rule shim holds 0x{value:08x} "
                f"{len(found)} times")
        return found[0]
    rdtime = next(pc for pc, _, word in decoded
                  if word & SHIM_RDTIME_MASK == SHIM_RDTIME)
    srst = min(pc for pc, eid, _ in ecall_sites(decoded) if eid == SBI_SRST)
    cycle = struct.unpack_from("<I", data, rdtime)[0] & ~(1 << 20)
    mutations = [
        ("its FAIL line's template missing", data.index(SHIM_FAIL_TEMPLATE),
         b"X", "template is missing"),
        ("a read of cycle for time", rdtime, struct.pack("<I", cycle),
         "a CSR other than sstatus.SIE and time"),
        ("a third read of time", at(LUI_T0_WAIT),
         struct.pack("<I", SHIM_RDTIME | 5 << 7), "SYSTEM instructions"),
        ("a read of time for the SIE clear", at(SHIM_SIE_CLEAR),
         struct.pack("<I", SHIM_RDTIME | 5 << 7), "reads time 3 times"),
        ("hart_get_status's FID another", at(LI_A6_2),
         struct.pack("<I", LI_A6_2 + (1 << 20)), "the shim calls"),
        ("an SRST removed", srst, struct.pack("<I", NOP), "the shim calls"),
    ]
    for name, offset, value, wanted in mutations:
        mutated = bytearray(data)
        mutated[offset:offset + len(value)] = value
        try:
            check_boot(bytes(mutated), BOOT_TEXT_OFFSET,
                       bytes(mutated[MONITOR_OFFSET:MONITOR_OFFSET + SPAN]),
                       pins, kernel, "shim-rule", scenario=scenario)
        except ImageError as error:
            require(wanted in str(error), f"shim-rule's mutation {name!r} "
                    f"rejected for another reason: {error}")
            continue
        raise ImageError(f"shim-rule's mutation {name!r} was accepted")
    return len(mutations)


def cheri_variant_check(name, *args):
    """beryllium-cheri: check_variant() for variant NAME, with a CHERI
    variant's own arm helper hedeleg (CHERI_VARIANT_HEDELEG) in
    HELPER_WRITES while its monitor is checked."""
    global HELPER_WRITES
    saved = HELPER_WRITES
    if name in CHERI_VARIANT_HEDELEG:
        HELPER_WRITES = dict(saved, **{MVP_ARM: [
            (csr, operation, ("const", CHERI_VARIANT_HEDELEG[name])
             if csr == "hedeleg" else value)
            for csr, operation, value in saved[MVP_ARM]]})
    try:
        return check_variant(name, *args)
    finally:
        HELPER_WRITES = saved


def cheri_variant_mutations(name, reference, pins, kernel, layout,
                            scenario):
    """beryllium-cheri: a CHERI variant's mutations (planning/
    cheri-enforcement-plan.md, section 6), each rejected for its own
    reason: channel-cw's builder without its defect, the reference's own
    monitor and boot image under channel-cw's name, which the variant rule
    refuses as the reference (the image check reads no C code, so the CW
    the defect writes is the host tests', the walker's, and the run's);
    cheri-fault-hs's hedeleg with cause 28, the reference's under its name,
    whose arm helper writes the reference's hedeleg; cap-store's G0 DTB
    te-poc's, the reference's under its name, whose G0 bootargs lack
    rdinit=/init-cap-store. Returns their number."""
    expected = {"channel-cw": f"variant {name} is the reference",
                "cheri-fault-hs": "hedeleg written as",
                "cap-store": "DTB /chosen bootargs is"}[name]
    label = {"channel-cw": "the builder without its defect",
             "cheri-fault-hs": "hedeleg with the CHERI fault",
             "cap-store": "G0's DTB te-poc's"}[name]
    mutants = ((label, reference["boot_elf"], reference["boot"],
                reference["boot_path"],
                (reference["elf_data"], reference["flat"],
                 reference["map_text"]), expected),)
    for label, boot_elf, data, img_path, monitor, expected in mutants:
        try:
            cheri_variant_check(name, boot_elf, data, reference, pins,
                                kernel, img_path, monitor, layout, scenario)
        except ImageError as error:
            require(expected in str(error),
                    f"variant {name}'s mutation {label!r} rejected for "
                    f"another reason: {error}")
            continue
        raise ImageError(f"variant {name}'s mutation {label!r} was accepted")
    return len(mutants)


# ------------------------------------------------------- QEMU-only images
# The U-Boot rehearsal's images (planning/mvp-m5-plan.md, "Tool changes
# (M5-2)"): QEMU's booti moves an image to its RAM base, 0x8000_0000, plus
# text_offset, so each board image has a copy holding QEMU's.
QEMU_TEXT_OFFSET = LAYOUT["QEMU_TEXT_OFFSET"]


def check_qemu_image(qemu, board):
    """A QEMU-only image: the board image's bytes but text_offset, header
    bytes 8 to 15, which hold BE_MVP_QEMU_TEXT_OFFSET where the board
    image's hold BE_MVP_UBOOT_TEXT_OFFSET."""
    for name, data, offset in (("QEMU", qemu, QEMU_TEXT_OFFSET),
                               ("board", board, BOOT_TEXT_OFFSET)):
        require(len(data) >= 16, f"the {name} image has no header")
        value = struct.unpack_from("<Q", data, 8)[0]
        require(value == offset, f"the {name} image's text_offset "
                                 f"0x{value:x} is not 0x{offset:x}")
    stray = outside(qemu, board, [(8, 8)])
    require(stray is None,
            f"the QEMU image differs from the board image at 0x{stray:x}"
            if stray is not None else "")


def qemu_image_mutations(qemu, board):
    """The QEMU-image rule's defects, each rejected for its own reason;
    returns their number."""
    def patched(data, at, value):
        return data[:at] + value + data[at + len(value):]

    def flipped(data, at):
        return patched(data, at, bytes([data[at] ^ 1]))
    differs = "the QEMU image differs from the board image at 0x"
    mutants = (
        ("a byte before text_offset", flipped(qemu, 0), board,
         differs + "0"),
        ("a byte after text_offset", flipped(qemu, 16), board,
         differs + "10"),
        ("the last byte", flipped(qemu, len(qemu) - 1), board,
         f"{differs}{len(qemu) - 1:x}"),
        ("the board's text_offset left in place",
         patched(qemu, 8, struct.pack("<Q", BOOT_TEXT_OFFSET)), board,
         "the QEMU image's text_offset"),
        ("a byte appended", qemu + bytes(1), board, "size 0x"),
        ("a board image with QEMU's text_offset", qemu,
         patched(board, 8, struct.pack("<Q", QEMU_TEXT_OFFSET)),
         "the board image's text_offset"))
    for name, data, reference, expected in mutants:
        try:
            check_qemu_image(data, reference)
        except ImageError as error:
            require(expected in str(error), f"QEMU-image mutation {name!r} "
                                            f"rejected for another reason: "
                                            f"{error}")
            continue
        raise ImageError(f"QEMU-image mutation {name!r} was accepted")
    return len(mutants)


def image_label(path):
    """An image's TOOLCHAIN[/NAME], from its directory in the build tree."""
    parts = pathlib.Path(path).parent.parts
    marks = [index for index, part in enumerate(parts)
             if part in ("gcc", "clang")]
    return "/".join(parts[marks[-1]:]) if marks else parts[-1]


# ---------------------------------------------------------- mutation test
def patch(elf_data, flat, boot_img, address, value, base):
    """Write value at address in the ELF segment, the flat image, and the
    boot image's copy of it."""
    elf = Elf(bytes(elf_data))
    for vaddr, _, offset, filesz, _, _ in elf.segments:
        if vaddr <= address and address + len(value) <= vaddr + filesz:
            start = offset + address - vaddr
            elf_data[start:start + len(value)] = value
            break
    else:
        raise ImageError(f"0x{address:x} is not in a loaded segment")
    at = address - base
    flat[at:at + len(value)] = value
    boot_img[MONITOR_OFFSET + at:MONITOR_OFFSET + at + len(value)] = value


def function_start(elf, name):
    found = [(value, size) for value, size, label in elf.functions
             if label == name]
    require(len(found) == 1, f"{name} is not one function")
    return found[0]


def nth_word(elf, flat, name, base, index=0):
    """Address of the index-th 32-bit instruction of a function."""
    value, size = function_start(elf, name)
    words = [pc for pc, width, _ in instructions(flat, value, value + size,
                                                 base) if width == 4]
    require(len(words) > index, f"{name} is too short")
    return words[index]


def word_slots(elf, flat, name, base, count):
    """Address of the first run of count adjacent 32-bit instructions."""
    value, size = function_start(elf, name)
    decoded = instructions(flat, value, value + size, base)
    for index in range(len(decoded) - count + 1):
        if all(width == 4 for _, width, _ in decoded[index:index + count]):
            return decoded[index][0]
    raise ImageError(f"no {count} adjacent 32-bit instructions in {name}")


# The resume tail's copy of its third argument, the armed hedeleg
# readback (addi t4, a2, 0), and the mutation's copy of a1 instead.
MV_T4_A2 = 12 << 15 | 29 << 7 | 0x13
MV_T4_A1 = 11 << 15 | 29 << 7 | 0x13


def matching_word(elf, flat, name, base, predicate):
    """Address of the first 32-bit instruction of name that matches."""
    value, size = function_start(elf, name)
    for pc, width, word in instructions(flat, value, value + size, base):
        if width == 4 and predicate(word):
            return pc, word
    raise ImageError(f"{name} has no matching instruction")


def branch_constant_writer(elf, flat, name, base, constant):
    """The ADDIW that contributes a named constant to a branch operand."""
    value, size = function_start(elf, name)
    decoded = instructions(flat, value, value + size, base)
    require(all(width == 4 for _, width, _ in decoded),
            f"{name} has a compressed instruction")
    words = [word for _, _, word in decoded]
    for index, word in enumerate(words):
        if word & 0x7F != 0x63:
            continue
        for register in ((word >> 15) & 0x1F, (word >> 20) & 0x1F):
            if materialized(words, index, register) != constant:
                continue
            writer = nearest_writer(words, index, register)
            while writer is not None and \
                    (words[writer] & 0x707F) == 0x1013:
                register = (words[writer] >> 15) & 0x1F
                writer = nearest_writer(words, writer, register)
            require(writer is not None and
                    (words[writer] & 0x707F) in (0x13, 0x1B),
                    f"{name}'s branch constant 0x{constant:x} has no "
                    "ADDI/ADDIW")
            return decoded[writer][0], words[writer]
    raise ImageError(f"{name} does not branch on constant 0x{constant:x}")


def add_immediate(value):
    """addi or addiw with this 12-bit immediate."""
    return lambda word: word & 0x707F in (0x13, 0x1B) and \
        signed(word >> 20, 12) == value


def with_immediate(word, value):
    return word & 0xFFFFF | (value & 0xFFF) << 20


def call_pair(pc, target, register=1):
    """auipc register + jalr ra, register: call target from pc."""
    delta = target - pc
    upper = (delta + 0x800) & ~0xFFF
    lower = delta - upper
    return struct.pack("<II", (upper & 0xFFFFF000) | register << 7 | 0x17,
                       (lower & 0xFFF) << 20 | register << 15 | 1 << 7 |
                       0x67)


def tail_pair(pc, target, register=6):
    """auipc register + jalr zero, register: tail-call target from pc."""
    delta = target - pc
    upper = (delta + 0x800) & ~0xFFF
    lower = delta - upper
    return struct.pack("<II", (upper & 0xFFFFF000) | register << 7 | 0x17,
                       (lower & 0xFFF) << 20 | register << 15 | 0x67)


def call_site(elf, flat, name):
    """The auipc of the MVP text's first call pair (auipc, jalr ra) to
    name."""
    code = (elf.symbols["__be_mvp_text_start"],
            elf.symbols["__be_mvp_text_end"])
    for value, size, names in function_map(elf, *code):
        owner = names[0] if len(names) == 1 else "/".join(names)
        decoded = instructions(flat, value, value + size, BASE)
        for pc, target, link in references(decoded, owner):
            word = struct.unpack_from("<I", flat, pc - 4 - BASE)[0]
            if target == elf.symbols[name] and link == 1 and \
                    word & 0x7F == 0x17:
                return pc - 4
    raise ImageError(f"no call pair to {name}")


def pool_reference(pc, address, register):
    """auipc register + addi register: form address at pc."""
    delta = address - pc
    upper = (delta + 0x800) & ~0xFFF
    lower = delta - upper
    return struct.pack("<II", (upper & 0xFFFFF000) | register << 7 | 0x17,
                       (lower & 0xFFF) << 20 | register << 15 |
                       register << 7 | 0x13)


def load_reference(pc, address, register):
    """auipc register + ld register: read the doubleword at address from
    pc."""
    delta = address - pc
    upper = (delta + 0x800) & ~0xFFF
    lower = delta - upper
    return struct.pack("<II", (upper & 0xFFFFF000) | register << 7 | 0x17,
                       (lower & 0xFFF) << 20 | register << 15 | 3 << 12 |
                       register << 7 | 0x03)


def lui_with(value):
    """Matches lui with this upper immediate (li of a 2^12 multiple)."""
    return lambda word: word & 0x7F == 0x37 and word >> 12 == value >> 12


def preceding_word(elf, flat, name, base, predicate):
    """Address and word of the 32-bit instruction before the first match."""
    value, size = function_start(elf, name)
    decoded = instructions(flat, value, value + size, base)
    for index, (_, width, word) in enumerate(decoded):
        if width == 4 and predicate(word) and index and \
                decoded[index - 1][1] == 4:
            return decoded[index - 1][0], decoded[index - 1][2]
    raise ImageError(f"{name} has no matching instruction")


def shim_ecall(data, eid):
    """Offset of the shim's ecall for the SBI extension eid."""
    b3 = load_b3()
    entry = b3.check_header(data, LAYOUT["UBOOT_TEXT_OFFSET"], [])["entry"]
    decoded = instructions(data, entry, data.index(b3.TEMPLATES[0]), 0)
    found = [pc for pc, call, _ in ecall_sites(decoded) if call == eid]
    require(len(found) == 1, f"the shim has {len(found)} ecalls for {eid}")
    return found[0]


# The SBI argument a6 = 0 (HSM hart_start), = 1 (hart_stop), and = 2
# (hart_get_status); the shim-rule variant's wait loads its deadline's
# 2^27 ticks into t0 with one lui (item 137).
LI_A6_0, LI_A6_1, LI_A6_2 = 0x00000813, 0x00100813, 0x00200813
LUI_T0_WAIT = 0x080002B7
CSRS_SIE_T0 = 0x1042A073


def map_rename(map_text, predicate, name):
    """The link map with its first input section in the flat image that
    predicate(address, size, object, section) accepts attributed to object
    file name."""
    for pattern in (GNU_MAP_ENTRY, LLD_MAP_ENTRY):
        for match in pattern.finditer(map_text):
            path = pathlib.PurePath(match.group("object"))
            address = int(match.group("address"), 16)
            if int(match.group("size"), 16) and \
                    BASE <= address < BASE + SPAN and predicate(
                        address, int(match.group("size"), 16), path.name,
                        match.group("section")):
                start, end = match.span("object")
                return map_text[:start] + str(path.with_name(name)) + \
                    map_text[end:]
    raise ImageError(f"no input section in the link map for {name}")


def symbol_value(elf, name, value):
    """An elf mutation: the one symbol name's st_value set to value."""
    entries = elf.symbol_entries.get(name, [])
    require(len(entries) == 1, f"{name} is not one symbol")
    return entries[0] + 8, struct.pack("<Q", value)


def symbol_size_value(elf, name, size):
    """An elf mutation: the one symbol name's st_size set to size."""
    entries = elf.symbol_entries.get(name, [])
    require(len(entries) == 1, f"{name} is not one symbol")
    return entries[0] + 16, struct.pack("<Q", size)


def run_mutations(toolchain, elf_data, flat, boot_img, pins, kernel, layout,
                  mutations, profile="mvp", map_text=None,
                  scenario=TWO_GUESTS):
    """Apply each mutation alone; each must be rejected for its reason.

    A mutation patches the monitor's loaded bytes (monitor), the boot image
    (boot), the ELF file alone (elf: a header or symbol), the layout's
    constants (layout), the link map's text (map), or the flat image and
    its copy in the boot image at an offset, or its length (flat).
    """
    results = []
    for name, kind, address, value, expected in mutations:
        mutated_elf, mutated_flat = bytearray(elf_data), bytearray(flat)
        mutated_boot = bytearray(boot_img)
        mutated_map = map_text
        constants = LAYOUT
        if kind == "monitor":
            patch(mutated_elf, mutated_flat, mutated_boot, address, value,
                  BASE)
        elif kind == "boot":
            mutated_boot[address:address + len(value)] = value
        elif kind == "elf":
            mutated_elf[address:address + len(value)] = value
        elif kind == "map":
            mutated_map = value(map_text)
        elif kind == "flat" and address is not None:
            mutated_flat[address:address + len(value)] = value
            at = MONITOR_OFFSET + address
            mutated_boot[at:at + len(value)] = value
        elif kind == "flat":
            mutated_flat += value
        else:
            constants = dict(LAYOUT, **value)
        require(bytes(mutated_elf) != elf_data or
                bytes(mutated_flat) != flat or
                bytes(mutated_boot) != boot_img or constants != LAYOUT or
                mutated_map != map_text,
                f"mutation {name!r} changed nothing")
        try:
            check_image(toolchain, bytes(mutated_elf), bytes(mutated_flat),
                        bytes(mutated_boot), pins, kernel, layout,
                        mutated_map, profile=profile, constants=constants,
                        scenario=scenario)
        except ImageError as error:
            require(expected in str(error),
                    f"mutation {name!r} rejected for another reason: {error}")
            results.append(name)
            continue
        raise ImageError(f"mutation {name!r} was accepted")
    return results


def cheri_rule_mutations(elf, flat):
    """beryllium-cheri: the mutations of the review of the CHERI rules, F1
    to F5, each a defect that the rules before the review accepted:
    (name, address, bytes, the new rule's message), in-place word
    replacements, some over several words."""
    def word(value):
        return struct.pack("<I", value)

    def words_at(address, count):
        return list(struct.unpack_from(f"<{count}I", flat, address - BASE))

    def find(name, predicate):
        return matching_word(elf, flat, name, BASE, predicate)[0]

    def reads_ddc(value):
        return ddc_access(value) is not None and \
            ddc_access(value)[0] == "read"

    # F1: the vector's ddc block, read and save, then load and install.
    vector_read = find(MVP_VECTOR, reads_ddc)
    read, save, load, install = words_at(vector_read, 4)
    held = ddc_access(read)[1]
    require(sc_fields(save) == (held, 2, CAP_FRAME) and
            lc_fields(load) == (held, 2, CAP_MON_DDC) and
            ddc_access(install) == ("write", held),
            "the vector's ddc block is not read, save, load, install")
    # F2: ct0's and ct1's reloads from their spills, csp's read from
    # sscratchc, and the restore of sscratchc; and the bad-stack path's
    # step back below the top, where a third write of sscratch, or a
    # second of ddc, could stand.
    reload = find(MVP_VECTOR, lambda value: lc_fields(value) == (5, 2, -32))
    reload_ct1 = find(MVP_VECTOR,
                      lambda value: lc_fields(value) == (5, 2, -16))
    csp_read = find(MVP_VECTOR, lambda value:
                    csr_read_whole(value, SSCRATCH) is not None)
    restore = find(MVP_VECTOR, lambda value: value == CSRW_SSCRATCH_SP)
    bad_stack = find(MVP_VECTOR, lambda value: value == 0xFF010113)
    # F3: the injection helper's mode switches, and the integer write of
    # vsepc that follows the return.
    inject_enter = find(MVP_INJECT, lambda value: value == MODESW_CAP)
    inject_leave = find(MVP_INJECT, lambda value: value == MODESW_INT)
    require(words_at(inject_leave, 2) == [MODESW_INT,
                                          csr_write_word(VSEPC, 12)],
            "the injection helper's return is not followed by vsepc's "
            "write from a2")
    # F4: the arm helper's ddc read and its SCADDR from a1, and the budget
    # helper's ret.
    arm_read = find(MVP_ARM, reads_ddc)
    arm_window = words_at(arm_read, 3)
    require(arm_window[1] & 0xFE00707F == 0x0C001033 and
            (arm_window[1] >> 20) & 0x1F == 11 and
            (arm_window[1] >> 15) & 0x1F == ddc_access(arm_window[0])[1],
            "the arm helper's ddc read is not followed by its SCADDR from "
            "a1")
    addi_base_zero = (arm_window[1] >> 15 & 0x1F) << 7 | 0x13
    budget_ret = find(MVP_BUDGET, lambda value: value == 0x00008067)
    return [
        ("vector installs the monitor's ddc before it saves the guest's",
         vector_read, b"".join(map(word, (load, install, read, save))),
         "does not save the guest's ddc before it installs the monitor's"),
        ("vector writes ddc on its bad-stack path", bad_stack,
         word(csr_write_word(DDC_CSR, 5)),
         "does not hold exactly one ddc read and one ddc write"),
        ("vector saves ct0 from ct1's spill", reload,
         word(with_immediate(words_at(reload, 1)[0], -16)),
         "does not save ct0 whole from its spill"),
        ("vector saves ct1 from ct0's spill", reload_ct1,
         word(with_immediate(words_at(reload_ct1, 1)[0], -32)),
         "does not save ct1 whole from its spill"),
        ("vector saves ct1 as csp", csp_read, word(NOP),
         "does not save csp whole from sscratchc"),
        ("vector leaves sscratchc unrestored", restore, word(NOP),
         "does not restore sscratchc to the trusted top"),
        ("vector restores sscratchc from the guest's csp", restore,
         word(csr_write_word(SSCRATCH, 5)),
         "does not restore sscratchc to the trusted top"),
        ("vector writes sscratch on its bad-stack path", bad_stack,
         word(CSRW_SSCRATCH_SP),
         "does not restore sscratchc to the trusted top"),
        ("the injection helper moves in Integer Pointer Mode", inject_enter,
         word(NOP), "does not enter Capability Pointer Mode once"),
        ("the injection helper stays in Capability Pointer Mode",
         inject_leave, word(NOP),
         "does not enter Capability Pointer Mode once"),
        ("the injection helper writes vsepc from a2 in Capability Pointer "
         "Mode", inject_leave,
         word(csr_write_word(VSEPC, 12)) + word(MODESW_INT),
         "does not make exactly its four capability moves"),
        ("the arm helper stays in Capability Pointer Mode",
         find(MVP_ARM, lambda value: value == MODESW_INT), word(NOP),
         "does not enter Capability Pointer Mode once"),
        ("the budget helper stays in Capability Pointer Mode",
         find(MVP_BUDGET, lambda value: value == MODESW_INT), word(NOP),
         "does not enter Capability Pointer Mode once"),
        ("the arm helper's sscratchc from a base set to 0 after the ddc "
         "read", arm_read,
         b"".join(map(word, (arm_window[0], addi_base_zero, arm_window[1]))),
         "takes SCADDR's base, x5, from other than its ddc read"),
        ("the budget helper returns by c.jr", budget_ret,
         struct.pack("<HH", 0x8082, 0x0001),
         "holds a compressed instruction"),
        ("the arm helper leaves a frame slot unnulled",
         find(MVP_ARM, lambda value:
              sc_fields(value) == (0, 11, CAP_FRAME + 16 * 16)),
         word(NOP), "does not null the capability frame"),
    ]


def cheri_fill_mutations(elf, flat):
    """beryllium-cheri: the mutations of T5 of the review of the CHERI rules
    (its r5), on what the arm helper stores through sscratchc's capability,
    each a defect that the rules before T5 accepted: (name, address, bytes,
    the rule's message), in-place replacements of one word."""
    def word(value):
        return struct.pack("<I", value)

    def word_at(address):
        return struct.unpack_from("<I", flat, address - BASE)[0]

    def find(predicate):
        return matching_word(elf, flat, MVP_ARM, BASE, predicate)[0]

    def with_field(value, shift, field):
        return value & ~(0x1F << shift) | field << shift

    def stored(offset):
        return find(lambda value: sc_fields(value) is not None and
                    sc_fields(value)[1:] == (6, offset))

    read = find(lambda value: ddc_access(value) is not None and
                ddc_access(value)[0] == "read")
    held = ddc_access(word_at(read))[1]
    # The word after the SCADDR from a1: li t2, BE_MVP_DTB_GPA's first,
    # addiw t2, zero, 1055 with GCC and addi t2, zero, 1055 with Clang,
    # each then shifted by slli t2, t2, 21.
    li_first = word_at(read + 8)
    require((li_first & 0x7F) in (0x13, 0x1B) and
            (li_first >> 12) & 7 == 0 and (li_first >> 15) & 0x1F == 0 and
            (li_first >> 7) & 0x1F == 7,
            "the arm helper's SCADDR from a1 is not followed by li t2's "
            "first word")
    monitor, guest, dtb = (stored(slot) for slot in
                           (CAP_MON_DDC, CAP_FRAME, CAP_FRAME + 16 * 11))
    address = find(lambda value: value & R_TYPE_MASK == SCADDR_WORD and
                   (value >> 20) & 0x1F != 11)
    bound = find(lambda value: value & R_TYPE_MASK == SCBNDSR_WORD)
    length = find(lambda value: value & 0x7F == 0x37 and
                  (value >> 7) & 0x1F == (word_at(bound) >> 20) & 0x1F)
    require(read < address < length < bound < monitor,
            "the arm helper's device tree capability is not li, SCADDR, "
            "lui, SCBNDSR, before the frame's fill")
    a2_slot = CAP_FRAME + 16 * 12
    return [
        ("the arm helper stores t3 as the monitor's ddc", monitor,
         word(with_field(word_at(monitor), 20, 28)),
         "does not store its ddc read's register at CF_MON_DDC"),
        ("the arm helper gives the guest a null first ddc", guest,
         word(with_field(word_at(guest), 20, 0)),
         "does not store its ddc read's register at CF_MON_DDC"),
        ("the arm helper hands the guest its unbounded ddc as the device "
         "tree", dtb, word(with_field(word_at(dtb), 20, held)),
         "does not store in slot 11 the device tree's capability"),
        ("the arm helper's device tree capability at another address",
         read + 8,
         word(with_immediate(li_first, signed(li_first >> 20, 12) - 1)),
         "does not store in slot 11 the device tree's capability"),
        ("the arm helper bounds the device tree by a1's value", bound,
         word(with_field(word_at(bound), 20, 11)),
         "does not store in slot 11 the device tree's capability"),
        ("the arm helper bounds the device tree to two pages", length,
         word((word_at(length) + (1 << 12)) & 0xFFFFFFFF),
         "does not store in slot 11 the device tree's capability"),
        ("the arm helper bases the device tree on a null capability",
         address, word(with_field(word_at(address), 15, 0)),
         "does not store in slot 11 the device tree's capability"),
        ("the arm helper stores the device tree in a2's slot", dtb,
         word(word_at(dtb) & 0x01FFF07F | (a2_slot >> 5) << 25 |
              (a2_slot & 0x1F) << 7),
         "does not make exactly three stores through sscratchc's "
         "capability"),
        ("the arm helper zeroes its ddc read's register before the frame's "
         "fill", read + 8, word(held << 7 | 0x13),
         "writes its ddc read's register"),
        ("the arm helper reads ddc twice", read + 8,
         word(DDC_CSR << 20 | 2 << 12 | 7 << 7 | 0x73),
         "does not access ddc exactly once, by a read"),
    ]


def cheri_block_mutations(elf, flat):
    """beryllium-cheri: the mutations of the vector's two comparisons of
    its trusted top with the private blocks' stack tops (M11-3), each a
    defect that check_trap_entry_cheri() rejects: a constant a block or a
    page off, a branch's sense flipped, a comparison removed, the two in
    the other order, another register compared, and a branch or the
    bad-stack path's jump landing elsewhere: (name, address, bytes, the
    rule's message), in-place replacements."""
    def word(value):
        return struct.pack("<I", value)

    def li_t1(value):
        # lui t1, addiw t1, t1, slli t1, t1, 12: a page multiple in t1.
        upper = value >> 12
        high = (upper + 0x800) >> 12
        return b"".join(map(word, (
            (high & 0xFFFFF) << 12 | 6 << 7 | 0x37,
            ((upper - (high << 12)) & 0xFFF) << 20 | 6 << 15 | 6 << 7 |
            0x1B,
            12 << 20 | 6 << 15 | 1 << 12 | 6 << 7 | 0x13)))

    def branch_to(pc, value, target):
        offset = target - pc
        return word(value & 0x01FFF07F | (offset >> 12 & 1) << 31 |
                    (offset >> 5 & 0x3F) << 25 | (offset >> 1 & 0xF) << 8 |
                    (offset >> 11 & 1) << 7)

    def jump_to(pc, target):
        offset = target - pc
        return word((offset >> 20 & 1) << 31 | (offset >> 1 & 0x3FF) << 21 |
                    (offset >> 11 & 1) << 20 | (offset >> 12 & 0xFF) << 12 |
                    0x6F)

    start, size = function_start(elf, MVP_VECTOR)
    decoded = instructions(flat, start, start + size, BASE)
    words = [value for _, _, value in decoded]
    tops = [block + LAYOUT["BLOCK_STACK_TOP_OFFSET"] for block in BLOCKS]

    def li_t1_before(index):
        # lui t1, then addi or addiw t1, t1, then slli t1, t1.
        lui, add, shift = words[index - 3:index]
        return lui & 0xFFF == 6 << 7 | 0x37 and \
            add & 0xFFFFF in (6 << 15 | 6 << 7 | 0x13,
                              6 << 15 | 6 << 7 | 0x1B) and \
            shift & 0xFC0FFFFF == 6 << 15 | 1 << 12 | 6 << 7 | 0x13

    compared = [index for index, value in enumerate(words)
                if value & 0x7F == 0x63 and
                materialized(words, index, 6) in tops]
    require(len(compared) == 2 and
            [materialized(words, index, 6) for index in compared] == tops
            and compared[1] == compared[0] + 4 and
            all(li_t1_before(index) for index in compared),
            "the vector's block comparisons are not li t1 and a branch, "
            "twice")
    first, second = compared
    first_pc, second_pc = decoded[first][0], decoded[second][0]
    stack_ok = decoded[second + 1][0]
    bad = decode(words[second], 4, second_pc)["branch"]
    at = {pc: index for index, (pc, _, _) in enumerate(decoded)}
    require(bad in at and
            words[at[bad]:at[bad] + 2] == [MODESW_INT, ADDI_SP_SP_M16] and
            words[at[bad] + 2] & 0xFFF == 0x6F,
            "the vector's bad-stack path is not its mode switch, its step "
            "back, and a jump")
    jump_pc = decoded[at[bad] + 2][0]
    move, _ = matching_word(elf, flat, MVP_VECTOR, BASE,
                            lambda value: value == 2 << 15 | 5 << 7 | 0x13)
    tops_message = "does not require exactly the private blocks' stack tops"
    first_message = "first block comparison does not land just after its " \
        "second"
    bad_message = "second block comparison does not land on its bad-stack " \
        "path"
    return [
        ("the vector's first block top a block on, the second's",
         decoded[first - 3][0], li_t1(tops[0] + BLOCK_BYTES), tops_message),
        ("the vector's first block top a page on",
         decoded[first - 3][0], li_t1(tops[0] + PAGE), tops_message),
        ("the vector's second block top a block back, the first's",
         decoded[second - 3][0], li_t1(tops[1] - BLOCK_BYTES), tops_message),
        ("the vector's second block top a page on",
         decoded[second - 3][0], li_t1(tops[1] + PAGE), tops_message),
        ("the vector's first block comparison's sense flipped", first_pc,
         word(words[first] ^ 1 << 12), tops_message),
        ("the vector's second block comparison's sense flipped", second_pc,
         word(words[second] ^ 1 << 12), tops_message),
        ("the vector without its first block comparison", first_pc,
         word(NOP), tops_message),
        ("the vector without its second block comparison", second_pc,
         word(NOP), tops_message),
        ("the vector compares the second block's top first",
         decoded[first - 3][0],
         li_t1(tops[1]) + word(words[first]) + li_t1(tops[0]), tops_message),
        ("the vector compares the guest's gp, not its trusted top", move,
         word(3 << 15 | 5 << 7 | 0x13), tops_message),
        ("the vector's first block comparison lands on the bad-stack path",
         first_pc, branch_to(first_pc, words[first], bad), first_message),
        ("the vector's second block comparison lands past itself",
         second_pc, branch_to(second_pc, words[second], stack_ok),
         bad_message),
        ("the vector's second block comparison lands past the mode switch",
         second_pc, branch_to(second_pc, words[second], bad + 4),
         bad_message),
        ("the vector's bad-stack path jumps to its saves", jump_pc,
         jump_to(jump_pc, stack_ok), bad_message),
    ]


def mutation_test(toolchain, elf_path, bin_path, boot_path, pins, kernel,
                  layout, scenario=TWO_GUESTS):
    elf_data = open(elf_path, "rb").read()
    flat = open(bin_path, "rb").read()
    boot_img = open(boot_path, "rb").read()
    map_text = read_map(elf_path)
    check_image(toolchain, elf_data, flat, boot_img, pins, kernel, layout,
                map_text, scenario=scenario)
    elf = Elf(elf_data)
    symbols = elf.symbols
    word = lambda value: struct.pack("<I", value)  # noqa: E731
    quad = lambda value: struct.pack("<Q", value)  # noqa: E731
    arm_hedeleg, arm_word = matching_word(elf, flat, MVP_ARM, BASE,
                                          add_immediate(0x15D))
    arm_hstatus, hstatus_word = matching_word(
        elf, flat, MVP_ARM, BASE,
        lambda value: value & 0x707F == 0x3073 and value >> 20 == 0x600)
    arm_sie, sie_word = preceding_word(
        elf, flat, MVP_ARM, BASE, lambda value: value == CSRS_SIE_T0)
    budget_stie, stie_word = matching_word(
        elf, flat, MVP_BUDGET, BASE, add_immediate(SIE_SSIE | SIE_STIE))
    tick_period, tick_period_word = matching_word(
        elf, flat, MVP_TICK, BASE,
        lambda value: value & 0x7F == 0x37 and
        value & 0xFFFFF000 == LAYOUT["TICK_TICKS"])
    tick_write, tick_write_word = matching_word(
        elf, flat, MVP_TICK, BASE,
        lambda value: csr_number(value) == 0x14D and
        (value >> 12) & 7 == 1)
    park_write, park_write_word = matching_word(
        elf, flat, MVP_PARK, BASE,
        lambda value: csr_number(value) == 0x14D and
        (value >> 12) & 7 == 1)
    resume_hedeleg, _ = matching_word(
        elf, flat, MVP_RESUME, BASE, lambda value: value == MV_T4_A2)
    resume_spvp, spvp_word = matching_word(
        elf, flat, MVP_RESUME, BASE,
        lambda value: value & 0x707F == 0x7013 and
        signed(value >> 20, 12) == HSTATUS_SPVP)
    resume_hvip, hvip_word = matching_word(
        elf, flat, MVP_RESUME, BASE,
        lambda value: value & 0x707F == 0x7013 and
        signed(value >> 20, 12) == 0x444)
    dispatch_slot = word_slots(elf, flat, MVP_DISPATCH, BASE, 2)
    control_slot = word_slots(elf, flat, CONTROL_LOOP, BASE, 2)
    boot_slot = word_slots(elf, flat, "be_mvp_block_fill", BASE, 2)
    spv_test = matching_word(elf, flat, MVP_VECTOR, BASE,
                             lambda value: value & 0x707F == 0x7013 and
                             signed(value >> 20, 12) == HSTATUS_SPV)[0]
    arm_senvcfg, senvcfg_word = matching_word(
        elf, flat, MVP_ARM, BASE,
        lambda value: load_fields(value) == (5, 12, 80))
    top = lui_with(LAYOUT["BLOCK_STACK_TOP_OFFSET"])
    entry_top, entry_word = matching_word(elf, flat, MVP_ENTRY, BASE, top)
    vector_top, vector_word = branch_constant_writer(
        elf, flat, MVP_VECTOR, BASE,
        LAYOUT["G0_BLOCK_HPA"] + LAYOUT["BLOCK_SAVED_OFFSET"])
    descs = symbols[MVP_DESCS_SYMBOL]
    hgatps = symbols[MVP_HGATPS_SYMBOL]
    bindings = symbols[MVP_BINDINGS_SYMBOL]
    moved_top = LAYOUT["BLOCK_STACK_TOP_OFFSET"] + 0x1000
    monitor = [
        ("hedeleg immediate", arm_hedeleg,
         word(with_immediate(arm_word, 0x15F)), "hedeleg written as"),
        ("VTW set by the arm immediate", arm_hstatus,
         word(hstatus_word & ~0x1000), "hstatus written as"),
        ("SSIE missing from the arm immediate", arm_sie,
         word(with_immediate(sie_word, SIE_STIE)), "sie written as"),
        ("STIE missing from the arm immediate", arm_sie,
         word(with_immediate(sie_word, SIE_SSIE)), "sie written as"),
        ("STIE missing from the budget immediate", budget_stie,
         word(with_immediate(stie_word, SIE_SSIE)), "sie written as"),
        ("tick period changed", tick_period,
         word(tick_period_word + 0x1000), "does not write time +"),
        ("tick comparator write missing", tick_write, word(NOP),
         "stimecmp written by"),
        ("park comparator write missing", park_write, word(NOP),
         "stimecmp written by"),
        ("resume hedeleg check", resume_hedeleg, word(MV_T4_A1),
         "resume checks differ"),
        ("resume SPP not from SPVP", resume_spvp,
         word(with_immediate(spvp_word, 0x80)), "does not clear SPP"),
        ("resume tests all of hvip", resume_hvip,
         word(with_immediate(hvip_word, -1)), "resume checks differ"),
        ("missing fence.i", symbols[MVP_FENCE_I], word(NOP),
         "fence.i sites"),
        ("a seventh wfi", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x10500073), "wfi sites"),
        ("missing wait wfi", matching_word(
            elf, flat, MVP_WAIT, BASE, lambda value: value == 0x10500073)[0],
         word(NOP), "wfi sites"),
        ("missing park wfi", matching_word(
            elf, flat, MVP_PARK, BASE, lambda value: value == 0x10500073)[0],
         word(NOP), "wfi sites"),
        ("extra hfence.vvma", nth_word(elf, flat, MVP_RESUME, BASE, 1),
         word(0x22000073), "hfence.vvma sites"),
        ("hlv.d in the dispatch", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x6C0542F3), "hlsv sites"),
        ("hlvx.hu in the dispatch", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x643542F3), "hlsv sites"),
        ("extra sret", nth_word(elf, flat, MVP_RESUME, BASE, 1),
         word(0x10200073), "sret sites"),
        ("a second install call", dispatch_slot,
         call_pair(dispatch_slot, symbols[R3_INSTALL]), "install call sites"),
        ("the control loop reaches VS-domain-hart code", control_slot,
         call_pair(control_slot, symbols[MVP_HART_MAIN]),
         "the control roots reach"),
        ("the control loop reads boot-only data", control_slot,
         load_reference(control_slot, symbols["__be_mvp_rodata_start"], 15),
         "outside the role's profile"),
        ("the VS-domain hart reads control data", dispatch_slot,
         load_reference(dispatch_slot, symbols["__be_control_data_start"], 15),
         "outside the role's profile"),
        ("R3 entry called", dispatch_slot,
         call_pair(dispatch_slot, symbols[R3_ENTER]), "has call sites"),
        ("a time read outside the executor", dispatch_slot,
         call_pair(dispatch_slot, symbols[MVP_TIME]), "outside the executor"),
        ("vector writes hvip", nth_word(elf, flat, MVP_VECTOR, BASE, 1),
         word(0x64501073), "hvip written by"),
        ("resume writes vsatp", nth_word(elf, flat, MVP_RESUME, BASE, 1),
         word(0x28001073), "vsatp written by"),
        ("dispatch writes vsstatus", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x20051073), "vsstatus written by"),
        ("dispatch writes senvcfg", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x10A51073), "senvcfg written by"),
        ("a stimecmp write outside the budget helper",
         nth_word(elf, flat, MVP_DISPATCH, BASE), word(0x14D51073),
         "stimecmp written by"),
        ("dispatch sets sie", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x10452073), "sie written by"),
        ("sip cleared outside the SSIP helper",
         nth_word(elf, flat, MVP_DISPATCH, BASE), word(0x14417073),
         "sip written by"),
        ("a raw hgatp write in the MVP image",
         nth_word(elf, flat, MVP_DISPATCH, BASE), word(0x68051073),
         "hgatp written by"),
        ("resume writes hgatp", nth_word(elf, flat, MVP_RESUME, BASE, 1),
         word(0x68001073), "hgatp written by"),
        ("extra hfence.gvma", nth_word(elf, flat, MVP_RESUME, BASE, 1),
         word(0x62000073), "hfence.gvma sites"),
        ("arm helper loads senvcfg's word wrong", arm_senvcfg,
         word(with_immediate(senvcfg_word, 72)), "senvcfg written as"),
        ("arm helper skips a set readback", matching_word(
            elf, flat, MVP_ARM, BASE,
            lambda value: store_fields(value) == (5, 13, 80))[0],
         word(NOP), "reads the set back"),
        ("arm helper skips the hgatp readback", matching_word(
            elf, flat, MVP_ARM, BASE,
            lambda value: store_fields(value) == (5, 10, 104))[0],
         word(NOP), "reads back"),
        ("extra ecall", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x00000073), "ecall sites"),
        ("henvcfg outside the Sstc helper", nth_word(elf, flat, MVP_TIMER,
                                                     BASE),
         word(0x60A01073), "henvcfg written by"),
        ("hstateen0 read", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x60C022F3), "accesses hstateen0"),
        ("hvictl read", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x609022F3), "accesses hvictl"),
        ("F instruction", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x02000053), "F, D, or V instruction"),
        ("R3 install changed", symbols[R3_INSTALL] + 4, word(NOP),
         "differs from B2's"),
        ("entry without quiesce", BASE, word(NOP) + word(NOP),
         "first call be_b1_quiesce"),
    ] + ([
        # beryllium-cheri: s2 is saved whole in the capability frame, and
        # its address recorded from there; and the CHERI rules' mutations.
        ("vector skips s2", matching_word(
            elf, flat, MVP_VECTOR, BASE,
            lambda value: sc_fields(value) == (18, 2, CAP_FRAME + 16 * 18))[0],
         word(NOP), "does not save c18 whole"),
        ("vector records no s2", matching_word(
            elf, flat, MVP_VECTOR, BASE,
            lambda value: store_fields(value) == (5, 2, 136))[0],
         word(NOP), "does not record x18 at 136"),
        ("vector stays in Integer Pointer Mode",
         nth_word(elf, flat, MVP_VECTOR, BASE), word(NOP),
         "does not first enter Capability Pointer Mode"),
        ("vector installs a null ddc", matching_word(
            elf, flat, MVP_VECTOR, BASE,
            lambda value: value == 0x41629073)[0],
         word(0x41601073), "does not install the monitor's ddc"),
        ("resume restores a null ddc", matching_word(
            elf, flat, MVP_RESUME, BASE,
            lambda value: value == 0x41629073)[0],
         word(0x41601073), "does not restore the guest's ddc whole"),
        ("the injection helper returns to a2, not vstvecc", matching_word(
            elf, flat, MVP_INJECT, BASE,
            lambda value: value == 0x14129073)[0],
         word(0x14161073), "sepc written as"),
    ] + cheri_rule_mutations(elf, flat) + cheri_fill_mutations(elf, flat) \
        + cheri_block_mutations(elf, flat) if MONITOR == "cheri" else [
        ("vector skips s2", matching_word(
            elf, flat, MVP_VECTOR, BASE,
            lambda value: store_fields(value) == (18, 5, 136))[0],
         word(NOP), "does not save x18"),
    ]) + [
        ("vector skips htinst", matching_word(
            elf, flat, MVP_VECTOR, BASE,
            lambda value: store_fields(value) == (6, 5, 328))[0],
         word(NOP), "does not store htinst"),
        ("vector skips SPV", spv_test, word(NOP),
         "does not fail closed on hstatus.SPV"),
        ("a block offset moved in the vector", vector_top,
         word(with_immediate(vector_word,
                             signed(vector_word >> 20, 12) + 1)),
         "does not require exactly the private blocks"),
        ("a block offset moved in the hart entry", entry_top,
         word(entry_word & 0xFFF | moved_top), "stack top"),
        ("hart entry reads its block first", entry_top,
         word(0x0005B283), "accesses memory"),
    ] + ([
        # beryllium-cheri: s3 returns whole, by LC from the capability frame.
        ("resume skips s3", matching_word(
            elf, flat, MVP_RESUME, BASE,
            lambda value: lc_fields(value) == (19, 31, CAP_FRAME + 16 * 19))[0],
         word(NOP), "does not restore c19 whole"),
    ] if MONITOR == "cheri" else [
        ("resume skips s3", matching_word(
            elf, flat, MVP_RESUME, BASE,
            lambda value: load_fields(value) == (19, 31, 144))[0],
         word(NOP), "does not restore x19"),
    ]) + [
        ("resume calls out", nth_word(elf, flat, MVP_RESUME, BASE, 1),
         word(0x000000EF), "calls or jumps out"),
        ("exit path names the MVP pool", dispatch_slot,
         pool_reference(dispatch_slot, symbols["__be_mvp_pool_start"] + 0x40,
                        15), "names the MVP G-stage pool"),
        ("unused auipc", nth_word(elf, flat, MVP_DISPATCH, BASE),
         word(0x00000F17), "is not used as a base"),
        ("payload constant", symbols[MVP_LAYOUT_SYMBOL] + 16,
         quad(pins[0]["Image"][1] + 8), "payload constant kernel_bytes"),
        ("G1's DTB offset", symbols[MVP_LAYOUT_SYMBOL] + 40,
         quad(align_up(KERNEL_OFFSET + pins[0]["Image"][1], PAGE)),
         "payload constant dtb1_offset"),
        ("equal VMIDs", descs + 10 * 8, quad(VMIDS[0]), "VMIDs are"),
        ("a zero VMID", descs + 4 * 8, quad(0), "VMIDs are"),
        ("equal roots", hgatps + 8, quad(HGATPS[0]), "hgatp is"),
        ("hgatp without its VMID", hgatps, quad(HGATPS[0] & ~(0x3FFF << 44)),
         "is not Sv39x4 with VMID"),
        ("overlapping windows", descs + 7 * 8, quad(WINDOWS[0] + 0x2000000),
         "guest windows overlap"),
        ("pools sharing a page", descs + 9 * 8, quad(ROOTS[0] + 0x4000),
         "guest pools share a page"),
        ("a moved window", descs + 7 * 8, quad(WINDOWS[1] + WINDOW_BYTES),
         "is not the layout's"),
        ("equal domain harts", descs + 11 * 8, quad(HARTS[0]),
         "domain harts are"),
        ("a domain on the control hart", descs + 5 * 8,
         quad(LAYOUT["CONTROL_HART"]), "domain harts are"),
        ("a binding not its window's", bindings + 3 * 8, quad(HARTS[0]),
         "is not its window's"),
    ]
    # The MVP region (Plan revision M0-A.1): the link map's placement of
    # the MVP C objects, the region's sections, segments, and symbols, the
    # MVP's code on either side of its boundary, and the flat image.
    code = (symbols["__be_monitor_code_start"],
            symbols["__be_monitor_code_end"])
    data = (symbols["__be_monitor_data_start"],
            symbols["__be_monitor_data_end"])
    mvp_data = elf.sections[".mvp.data"]
    mvp_ro = [header for header, segment in zip(elf.segment_headers,
                                                elf.segments)
              if segment[0] == elf.sections[".mvp.rodata"][3]]
    maps = [
        ("an MVP C function in the core's code extent",
         lambda text: map_rename(
             text, lambda address, _, name, __: name == "privileged.o" and
             code[0] <= address < code[1], "mvp-sbi.o"),
         "is not permitted in the monitor boot extent"),
        ("MVP C constants in the core's data",
         lambda text: map_rename(
             text, lambda address, _, name, __: name == "manifest.o" and
             data[0] <= address < data[1], "mvp-sbi.o"),
         "is not permitted in the monitor read-only extent"),
        ("another object's constants in the input section",
         lambda text: map_rename(
             text, lambda _, __, name, ___: name == "mvp-config.o", "r3.o"),
         "is not permitted in the monitor input extent"),
        ("an accepted object's code in the MVP region",
         lambda text: map_rename(
             text, lambda _, __, name, ___: name == "mvp-ring.o",
             "state.o"),
         "is not permitted in the monitor shared extent"),
    ]
    elfs = [
        ("an unlisted allocated section",
         elf.section_headers[".symtab"] + 8,
         quad(elf.sections[".symtab"][2] | SHF_ALLOC),
         "allocated sections"),
        ("an MVP section inside the core",
         elf.section_headers[".mvp.rodata"] + 16,
         quad(BASE + CORE_SPAN - 0x4000), ".mvp.rodata address moved"),
        ("a section in the core's unused span",
         elf.section_headers[".monitor.rodata"] + 16,
         quad(CONTROL_STACK_END), ".monitor.rodata address moved"),
        ("the configuration outside the input section",
         *symbol_value(elf, "be_mvp_proposal", symbols["__be_input_end"]),
         "be_mvp_proposal is not in the core's input section"),
        ("the MVP region's data past its end",
         elf.section_headers[".mvp.data"] + 32,
         quad(REGION + REGION_BYTES - mvp_data[3] + 0x10),
         ".mvp.data size changed"),
        ("the hart entry in the MVP region",
         *symbol_value(elf, MVP_ENTRY, symbols["__be_mvp_text_start"]),
         "ASSERT fails: be_mvp_hart_entry"),
        ("the dispatch in the core's code extent",
         *symbol_value(elf, MVP_DISPATCH, code[0] + 0x40),
         "overlap"),
        ("the control confined-entry slot leaves its role",
         *symbol_value(elf, "__be_control_confined_entry_slot_end",
                       symbols["__be_mvp_control_text_end"] + 4),
         "control confined-entry slot"),
        ("the park entry covers boot code",
         *symbol_size_value(elf, MVP_PARK_ENTRY,
                            LAYOUT["PARK_BYTES"] + 4),
         "the park page"),
        ("the MVP region's end past 0x1_020a_4000",
         *symbol_value(elf, "__be_mvp_region_end",
                       REGION + REGION_BYTES + 0x1000),
         "ASSERT fails: __be_mvp_region_end"),
        ("the MVP region's constants executable", mvp_ro[0] + 4,
         struct.pack("<I", 5), "mvp_ro flags 5"),
    ]
    dtb0_offset = align_up(KERNEL_OFFSET + pins[0]["Image"][1], PAGE)
    dtb1_offset = dtb0_offset + DTB_BYTES
    dtb1 = boot_img[dtb1_offset:]
    window_cells = cells(0, LAYOUT["GUEST_GPA"], 0, WINDOW_BYTES)
    memory_at = dtb1_offset + dtb1.index(window_cells) + 12
    guest_id_at = dtb1_offset + dtb1.index(b"be.guest=1 ") + 9 \
        if scenario.dtb_variant else \
        dtb1_offset + dtb1.index(b"be.guest=1") + 9
    on = boundary_image(scenario.name)
    if not on:
        start_rule = shim_ecall(boot_img, SBI_HSM)
        start_fid = start_rule - 4 * next(
            back for back in range(1, 8)
            if struct.unpack_from("<I", boot_img, start_rule - 4 * back)[0]
            == LI_A6_0)
    # Item 137: room for the shim-rule variant's FAIL line in this image's
    # stub page, after its report lines.
    spare = align_up(boot_img.index(b"\n", boot_img.index(
        SHIM_TEMPLATE[:25])) + 1, 8)
    require(boot_img[spare:spare + len(SHIM_FAIL_TEMPLATE)] ==
            bytes(len(SHIM_FAIL_TEMPLATE)) and
            spare + len(SHIM_FAIL_TEMPLATE) <= MONITOR_OFFSET,
            "no room after the shim's report lines")
    boot = [
        ("payload byte flip", KERNEL_OFFSET + 0x1000,
         bytes([boot_img[KERNEL_OFFSET + 0x1000] ^ 0x40]),
         "kernel differs from its pin"),
        ("kernel magic2", KERNEL_OFFSET + KERNEL_MAGIC2_AT, b"\x00",
         "kernel magic2"),
        ("larger DTB memory node", memory_at, cells(2 * WINDOW_BYTES),
         "DTB memory node"),
        ("the staged image overlapping G0's window", 16,
         struct.pack("<Q", WINDOWS[0] - STAGING + PAGE),
         "overlaps the staged image"),
        ("equal bootargs", guest_id_at, b"0", "bootargs"),
        ("G1's DTB in G0's slot", dtb0_offset, dtb1[:DTB_BYTES],
         "bootargs"),
        ("text_offset", 8, struct.pack("<Q", 0x200000), "text_offset"),
        ("descriptor destination", 0x48, struct.pack("<Q", WINDOWS[1]),
         "descriptor destination"),
        ("monitor copy", MONITOR_OFFSET + 0x100,
         bytes([boot_img[MONITOR_OFFSET + 0x100] ^ 1]),
         "flat image at 0x1000 differs"),
        ("the descriptor's length the core's", 0x50,
         struct.pack("<Q", CORE_SPAN), "descriptor length"),
    ] + ([
        ("an HSM hart_stop in the board shim", start_fid,
         struct.pack("<I", LI_A6_1), "the shim calls"),
        ("the start rule's ecall removed", start_rule,
         struct.pack("<I", NOP), "the shim calls"),
        ("a start-rule template missing", boot_img.index(SHIM_TEMPLATE),
         b"X", "template is missing"),
    ] if not on else boundary_boot_mutations(boot_img)) + [
        ("a read of time in the shim",
         boot_img.index(struct.pack("<I", SHIM_SIE_CLEAR)),
         struct.pack("<I", SHIM_RDTIME | 6 << 7),
         "a CSR other than sstatus.SIE at"),
        ("the shim-rule variant's FAIL line in another image", spare,
         SHIM_FAIL_TEMPLATE, "outside that variant"),
    ]
    layouts = [
        ("a block offset moved in the layout",
         {"BLOCK_INBOUND_OFFSET": LAYOUT["BLOCK_INBOUND_OFFSET"] + 0x1000},
         "mailbox buffers and index lines leave their extents"),
        ("a ring size that is not a power of two",
         {"OUTBOUND_RING_BYTES": 0x6000}, "is not a power of two"),
        ("a block outside its place in the region",
         {"G1_BLOCK_HPA": LAYOUT["G1_BLOCK_HPA"] + 0x1000},
         "hart mailboxes and private blocks are not in order"),
        ("an MVP region over 256 KiB",
         {"REGION_BYTES": REGION_BYTES + 0x8000}, "more than 0x40000"),
        ("the MVP region not after the hart region",
         {"REGION_HPA": REGION + 0x4000}, "does not follow the hart region"),
        ("a role extent not aligned to its size",
         {"MONITOR_CONTROL_TEXT_HPA":
          LAYOUT["MONITOR_CONTROL_TEXT_HPA"] + 0x1000},
         "is not power-of-two sized and aligned"),
        ("a flat image the MVP region does not end",
         {"IMAGE_BYTES": SPAN + 0x1000}, "does not end the flat image"),
        ("the staged image on the MVP region",
         {"STAGING_HPA": REGION + 0x8000}, "overlaps the MVP region"),
    ]
    if scenario.name == "anchor":
        layouts.append(
            ("a tenth protected VS-domain-hart profile entry",
             {"MONITOR_DOMAIN_TEXT_HPA":
              LAYOUT["MONITOR_DOMAIN_TEXT_HPA"] + 0x2000},
             "anchor G1 profile uses 10 entries, more than 9"))
    # The denial path (planning/mvp-m1-plan.md, "Tests and evidence"): the
    # injection helper's writers, call sites, and readback, the vector's
    # vsstatus, and the channel page among the extents; then, in an image
    # that links a channel, the denial path's hgatp rule and the linked
    # configuration.
    monitor += [
        ("a vscause write outside the injection helper",
         nth_word(elf, flat, MVP_DISPATCH, BASE), word(0x24251073),
         "vscause written by"),
        ("a second call site of the injection helper", dispatch_slot,
         call_pair(dispatch_slot, symbols[MVP_INJECT]), "inject call sites"),
        ("the injection helper skips the vsstatus readback", matching_word(
            elf, flat, MVP_INJECT, BASE,
            lambda value: store_fields(value) == (5, 14, 24))[0],
         word(NOP), "reads back"),
        ("the injection helper writes vsepc from a1", matching_word(
            elf, flat, MVP_INJECT, BASE,
            lambda value: value == 0x24161073)[0],
         word(0x24159073), "vsepc written as"),
        ("the vector skips vsstatus", matching_word(
            elf, flat, MVP_VECTOR, BASE,
            lambda value: store_fields(value) == (7, 5, 352))[0],
         word(NOP), "does not store vsstatus at 352"),
    ]
    layouts.append(("the shared pages inside G1's window",
                    {"SHARED_PAGES_HPA": WINDOWS[1] + 0x1000},
                    "overlaps G1's window"))
    if scenario.report is not None:
        denial_path = [owner for owner, _, _ in inject_call_sites(elf, flat)]
        identity = symbols[MVP_IDENTITY_SYMBOL]
        monitor += [
            ("an hgatp write on the denial path",
             nth_word(elf, flat, denial_path[0], BASE), word(0x68051073),
             "hgatp written by"),
            ("the linked identity differing from the report", identity + 31,
             bytes([flat[identity + 31 - BASE] ^ 1]),
             "configuration identity"),
        ]
    if scenario.report is not None and not scenario.pages:
        channel = symbols[MVP_CHANNEL_SYMBOL]
        monitor.append(
            ("the reader's linked rights with write",
             channel + 8 * CHANNEL_WORDS.index("reader_rights"),
             quad(RIGHTS["read"] | RIGHTS["write"]),
             "linked channel record"))
    # An image with pages (planning/mvp-m2-plan.md): a linked page that
    # breaks the pages' rules, the secret out of the constants, and the
    # channel page not the shared pages' first.
    if scenario.pages:
        pages = symbols[MVP_PAGES_SYMBOL]
        count = symbol_size(elf, MVP_PAGES_SYMBOL) // (8 * len(PAGE_WORDS))
        linked = [dict(zip(PAGE_WORDS, struct.unpack_from(
            f"<{len(PAGE_WORDS)}Q", flat,
            pages - BASE + 8 * index * len(PAGE_WORDS))))
            for index in range(count)]
        secret_page = [index for index, page in enumerate(linked)
                       if page["kind"] == PAGE_SECRET][0]
        other = 1 - linked[secret_page]["reader"]
        monitor.append(
            ("the secret page readable by its other domain",
             pages + 8 * (secret_page * len(PAGE_WORDS) +
                          PAGE_WORDS.index(f"rights{other}")),
             quad(RIGHTS["read"]), f"the linked page {secret_page}"))
        elfs += [
            ("the secret in the MVP region's data",
             *symbol_value(elf, MVP_SECRET_SYMBOL,
                           elf.sections[".mvp.data"][3]),
             f"{MVP_SECRET_SYMBOL} at"),
        ]
        layouts.append(("the channel page not the shared pages' first",
                        {"CHANNEL_HPA": SHARED_PAGES + PAGE},
                        "is not the shared pages' first page"))
    # The management extension (planning/mvp-m2-plan.md, "The management
    # extension" and "The measurement"): code a domain hart runs that
    # reads hart 0's management state, forms the grants' address, or calls
    # the decision or hart 0's entry; linked grants that break their rules
    # or differ from the report's; and hart 0's state out of its BSS.
    if scenario.mgmt:
        grants = symbols[MVP_GRANTS_SYMBOL]
        state = symbols[MVP_MGMT_STATE_SYMBOL]
        wait_slot = word_slots(elf, flat, MVP_WAIT_SERVE, BASE, 2)
        monitor += [
            ("a domain-hart function reads the management state",
             dispatch_slot, load_reference(dispatch_slot, state + 16, 15),
             f"names {MVP_MGMT_STATE_SYMBOL}"),
            ("the domain hart's wait forms the grants' address", wait_slot,
             pool_reference(wait_slot, grants, 15),
             f"names {MVP_GRANTS_SYMBOL}"),
            ("the domain hart calls the decision", dispatch_slot,
             call_pair(dispatch_slot, symbols[MVP_DECIDE]),
             f"reaches {MVP_DECIDE}"),
            ("the domain hart calls hart 0's entry", wait_slot,
             call_pair(wait_slot, symbols[MVP_MAIN]),
             f"reaches {MVP_MAIN}"),
            ("a linked grant on its requester itself",
             grants + 8 * GRANT_WORDS.index("to"),
             quad(struct.unpack_from("<Q", flat, grants - BASE)[0]),
             "the linked grant 0"),
            ("a linked grant without terminate",
             grants + 8 * GRANT_WORDS.index("permissions"),
             quad(MGMT_PERMISSIONS["pause"]), "the linked grants"),
        ]
        moved = elf.sections[".mvp.rodata"][3]
        elfs.append(
            ("the management state in the MVP region's constants",
             *symbol_value(elf, MVP_MGMT_STATE_SYMBOL, moved),
             f"{MVP_MGMT_STATE_SYMBOL} at 0x{moved:x} is not in the control "
             f"writable-data extent"))
    # The measurement log (planning/mvp-m9-plan.md, D-1 to D-4; I19): code
    # a domain hart runs that reads hart 0's page or registers; the page
    # unaligned or outside the MVP region's BSS, the registers or the
    # constants outside their sections; a linked count, sequence, or
    # launch register not the image's; the canary outside the constants,
    # an instruction forming its address, or a word holding it; and an R2
    # range's end short of its section's.
    log_page = symbols[MVP_LOG_SYMBOL]
    log_constants = symbols[MVP_LOG_CONSTANTS_SYMBOL]
    canary = symbols[MVP_LOG_CANARY_SYMBOL]
    count, sequence = struct.unpack_from("<II", flat,
                                         log_constants - BASE + 160)
    monitor += [
        ("a domain-hart function reads the log page", dispatch_slot,
         load_reference(dispatch_slot, log_page + 8, 15),
         f"names {MVP_LOG_SYMBOL} at"),
        ("a domain-hart function reads the log registers", dispatch_slot,
         load_reference(dispatch_slot,
                        symbols[MVP_LOG_REGISTERS_SYMBOL] + 8, 15),
         f"names {MVP_LOG_REGISTERS_SYMBOL} at"),
        ("a linked launch register not the boot image's",
         log_constants + LOG_LAUNCH_AT,
         bytes([flat[log_constants + LOG_LAUNCH_AT - BASE] ^ 1]),
         "the linked launch register of domain 0"),
        ("a linked expected count off by one", log_constants + 160,
         struct.pack("<I", count + 1), "the linked expected count"),
        ("a linked sequence not the image's", log_constants + 164,
         struct.pack("<I", sequence % 3 + 1), "the linked log sequence"),
        ("an instruction forms the canary's address", boot_slot,
         pool_reference(boot_slot, canary, 15),
         f"refers to {MVP_LOG_CANARY_SYMBOL}"),
        ("a constant word holds the canary's address",
         align_up(log_constants, 8), struct.pack("<Q", canary + 1),
         f"refers to {MVP_LOG_CANARY_SYMBOL}"),
    ]
    elfs += [
        ("the log page not 4 KiB aligned",
         *symbol_value(elf, MVP_LOG_SYMBOL, log_page + 8),
         f"{MVP_LOG_SYMBOL} at"),
        ("the log page past the MVP region's BSS",
         *symbol_value(elf, MVP_LOG_SYMBOL,
                       align_up(symbols["__be_mvp_bss_end"], LOG_PAGE_BYTES)),
         f"{MVP_LOG_SYMBOL} at"),
        ("the log registers in the MVP region's constants",
         *symbol_value(elf, MVP_LOG_REGISTERS_SYMBOL,
                       elf.sections[".mvp.rodata"][3]),
         f"{MVP_LOG_REGISTERS_SYMBOL} at"),
        ("the log constants in the MVP region's data",
         *symbol_value(elf, MVP_LOG_CONSTANTS_SYMBOL,
                       elf.sections[".mvp.data"][3]),
         f"{MVP_LOG_CONSTANTS_SYMBOL} at"),
        ("the canary in the MVP region's data",
         *symbol_value(elf, MVP_LOG_CANARY_SYMBOL,
                       elf.sections[".mvp.data"][3]),
         f"{MVP_LOG_CANARY_SYMBOL} at"),
        ("the mvp-rodata range's end short of its section",
         *symbol_value(elf, "__be_mvp_rodata_end",
                       symbols["__be_mvp_rodata_end"] - 16),
         "the R2 range mvp-rodata"),
    ]
    if scenario.report is not None:
        monitor.append(
            ("a linked log configuration identity not the report's",
             log_constants + 32, bytes([flat[log_constants + 32 - BASE] ^ 1]),
             "the linked log identities"))
    # Console input (planning/mvp-m7-plan.md, D-1 and D-3): code a domain
    # hart runs that reads hart 0's console input or its read buffer, forms
    # its input rings' address, or calls the firmware console read or the
    # routing; the domain hart's service of a granted read unreached; the
    # firmware console read reaching more than be_mvp_fw_call; and the
    # input ring out of its place or size.
    serve_site = call_site(elf, flat, INPUT_SERVE)
    read_tail, read_word = matching_word(
        elf, flat, EXEC_CONSOLE_READ, BASE, lambda value: value & 0x7F == 0x17)
    monitor += [
        ("a domain-hart function reads hart 0's console input",
         dispatch_slot,
         load_reference(dispatch_slot, symbols[MVP_CONSOLE_IN_SYMBOL] + 8,
                        15), f"names {MVP_CONSOLE_IN_SYMBOL}"),
        ("a domain-hart function reads hart 0's console read buffer",
         dispatch_slot,
         load_reference(dispatch_slot, symbols[MVP_CONSOLE_BUFFER_SYMBOL],
                        15), f"names {MVP_CONSOLE_BUFFER_SYMBOL}"),
        ("a domain-hart function forms the input rings' address",
         dispatch_slot,
         pool_reference(dispatch_slot, symbols[MVP_INPUT_RINGS_SYMBOL], 15),
         f"names {MVP_INPUT_RINGS_SYMBOL}"),
        ("the domain hart calls the firmware console read", dispatch_slot,
         call_pair(dispatch_slot, symbols[EXEC_CONSOLE_READ]),
         f"reaches {EXEC_CONSOLE_READ}"),
        ("the domain hart routes console input", dispatch_slot,
         call_pair(dispatch_slot, symbols[INPUT_ROUTING[0]]),
         f"reaches {INPUT_ROUTING[0]}"),
        ("the domain hart's read service unreached", serve_site,
         call_pair(serve_site, symbols["be_mvp_input_rearm"]),
         f"does not reach {INPUT_SERVE}"),
        ("the firmware console read tails the time helper", read_tail,
         tail_pair(read_tail, symbols[MVP_TIME], (read_word >> 7) & 0x1F),
         f"{EXEC_CONSOLE_READ} reaches"),
    ]
    layouts += [
        ("the input ring not after the outbound ring",
         {"INPUT_RING_OFFSET": LAYOUT["INPUT_RING_OFFSET"] + 0x1000},
         "mailbox buffers and index lines leave their extents"),
        ("an input ring size that is not a power of two",
         {"INPUT_RING_BYTES": 0x1800},
         "INPUT_RING_BYTES 0x1800 is not a power of two"),
    ]
    if on:
        monitor += boundary_mutations(elf, flat, symbols, dispatch_slot,
                                      boot_slot)
        placed, moved = placement_mutations(elf, flat, symbols,
                                            dispatch_slot, control_slot)
        monitor += placed
        elfs += moved
        placed, moved = step_two_mutations(elf, flat, symbols, boot_slot,
                                           control_slot)
        monitor += placed
        elfs += moved
    mutations = [(name, "monitor", address, value, expected)
                 for name, address, value, expected in monitor] + \
        [(name, "boot", address, value, expected)
         for name, address, value, expected in boot] + \
        [(name, "layout", None, value, expected)
         for name, value, expected in layouts] + \
        [(name, "map", None, value, expected)
         for name, value, expected in maps] + \
        [(name, "elf", address, value, expected)
         for name, address, value, expected in elfs] + \
        [("a flat image a page too long", "flat", None, bytes(PAGE),
          f"not 0x{SPAN:x}"),
         ("a byte in the core's unused span", "flat",
          CONTROL_STACK_END - BASE + 0x10, b"\x01",
          "nonzero bytes outside the loaded segments")]
    return run_mutations(toolchain, elf_data, flat, boot_img, pins, kernel,
                         layout, mutations, map_text=map_text,
                         scenario=scenario)


def call_site_in(elf, flat, caller, callee):
    """The auipc of caller's first call pair (auipc, jalr ra) to callee."""
    value, size = function_start(elf, caller)
    decoded = instructions(flat, value, value + size, BASE)
    for pc, target, link in references(decoded, caller):
        word = struct.unpack_from("<I", flat, pc - 4 - BASE)[0]
        if target == elf.symbols[callee] and link == 1 and \
                word & 0x7F == 0x17:
            return pc - 4
    raise ImageError(f"no call pair from {caller} to {callee}")


def placement_mutations(elf, flat, symbols, dispatch_slot, control_slot):
    """M11-8's placement rules, each one's defect in a boundary-on
    monitor: a role's edge into boot text, which a name missing from the
    linker script's lists gives (the role rules refuse it); a pointer word
    of a control constant into MVP boot rodata (C8); an object handed to
    hart 0's state out of its profile (C9); in an image with the
    management extension, the grants in the profile but out of the MVP
    control constants (the grants rule, which C9 lets pass); and a function
    that only boot code reaches left in the control, VS-domain-hart, and
    shared text, each by its one role call removed (C10)."""
    nops = struct.pack("<II", NOP, NOP)
    rodata = symbols["__be_mvp_rodata_start"] + 0x20
    monitor = [
        ("the control loop reaches boot code", control_slot,
         call_pair(control_slot, symbols["be_mvp_log_append"]),
         "through control_loop -> be_mvp_log_append"),
        ("a VS-domain hart reaches boot code", dispatch_slot,
         call_pair(dispatch_slot, symbols["be_mvp_hsm_census_add"]),
         f"{MVP_DISPATCH} -> be_mvp_hsm_census_add"),
        ("a control constant's word names MVP boot rodata",
         symbols["drop_names"], struct.pack("<Q", symbols[MVP_DESCS_SYMBOL]),
         "the control role's constant drop_names holds"),
        ("the control text keeps a function only boot code reaches",
         call_site_in(elf, flat, "be_mvp_input_flush",
                      "be_mvp_sha256_update"), nops,
         "be_mvp_sha256_update at"),
        ("the VS-domain-hart text keeps a function only boot code reaches",
         call_site_in(elf, flat, MVP_HART_MAIN, EXEC_STCE), nops,
         f"{MVP_STCE} at"),
        ("the shared text keeps a function only boot code reaches",
         call_site_in(elf, flat, "be_mvp_block_check",
                      "be_mvp_bindings_valid"), nops,
         "be_mvp_bindings_valid at"),
    ]
    moved = [
        ("be_mvp_maps, handed to hart 0, in MVP boot rodata",
         *symbol_value(elf, "be_mvp_maps", rodata),
         f"be_mvp_maps, which boot code hands to hart 0's state, lies at "
         f"0x{rodata:x}-"),
    ]
    if MVP_GRANTS_SYMBOL in symbols:
        # On hart 0's stack: inside its profile, with read rights (C9
        # holds), named by no code a domain hart runs, but not among the
        # MVP control constants.
        moved.append(
            ("the grants in hart 0's data, not its constants",
             *symbol_value(elf, MVP_GRANTS_SYMBOL,
                           symbols["__be_control_stack_start"]),
             "grants in the MVP control constants"))
    return monitor, moved


def formation_site(elf, flat, owner, target):
    """The auipc of OWNER's adjacent auipc and addi pair that forms TARGET's
    address."""
    decoded = function_words(elf, flat, owner, BASE)
    for pc, address, link in references(decoded, owner):
        word = struct.unpack_from("<I", flat, pc - 4 - BASE)[0]
        if address == target and link is None and word & 0x7F == 0x17:
            return pc - 4
    raise ImageError(f"{owner} forms 0x{target:x} with no adjacent auipc")


def between_starts_site(elf, flat, symbols):
    """The auipc of start_harts' first call pair to one of
    START_TAIL_HELPERS that the walk from a start visits and that lies
    before the last start's call by address (R2-1): a call that runs
    between the starts, and that an address-order rule from the last
    start would not see."""
    node = function_node(elf, flat, START_HARTS)
    calls, _ = start_tail_paths(node, symbols)
    last = max(pc for pc, target, link in node[3]
               if (target, link) == (symbols[EXEC_HART_START], 1))
    helpers = {symbols[name] for name in START_TAIL_HELPERS
               if name in symbols}
    sites = sorted(pc - 4 for pc, target, link in calls
                   if link == 1 and target in helpers and pc < last and
                   struct.unpack_from("<I", flat, pc - 4 - BASE)[0] & 0xFFF ==
                   1 << 7 | 0x17)
    require(sites, f"{START_HARTS} has no call pair to a helper before its "
            f"last start's call on a path from a start")
    return sites[0]


def step_two_mutations(elf, flat, symbols, boot_slot, control_slot):
    """M11-8's step-2 rules, each one's defect in a boundary-on monitor:
    the confined entry off its slot's first byte (the linker script's
    ASSERT), or another function in the slot (C1); the entry's stack, call, or class changed (C2, C14);
    its address formed by boot code (C3); the confined C calling boot code,
    or installing no vector (C4); boot code reaching the control loop (C5);
    a call after the last start before hart 0's confine, one between the
    starts that lies before the last start's call, and a helper that calls
    the firmware (C7); and the control loop calling the firmware itself
    (C13). C6's defect, a further call of the executor's confine, is
    M11-7's mutation of its one call."""
    entry = symbols[CONTROL_ENTRY]
    pcs = [pc for pc, _, _ in function_words(elf, flat, CONTROL_ENTRY, BASE)]
    between_starts = between_starts_site(elf, flat, symbols)
    helper_slot = word_slots(elf, flat, "be_mvp_control_started", BASE, 2)
    stack, klass = (struct.unpack_from("<I", flat, pcs[index] - BASE)[0]
                    for index in (1, 4))
    monitor = [
        ("the control entry's stack 16 bytes high", pcs[1],
         struct.pack("<I", with_immediate(stack,
                                          signed(stack >> 20, 12) + 16)),
         f"{CONTROL_ENTRY} is not sp formed as __be_control_stack_end in "
         f"its place (C2)"),
        ("the control entry calls another function", pcs[2],
         call_pair(pcs[2], symbols[CONTROL_LOOP]),
         f"{CONTROL_ENTRY} is not the call of {CONTROL_CONFINED} in its "
         f"place (C2)"),
        ("the control entry passes another class", pcs[4],
         struct.pack("<I", with_immediate(klass, 12)),
         "to the terminal, not BE_MVP_CLASS_EXCEPTION"),
        ("boot code forms the control entry's address", boot_slot,
         pool_reference(boot_slot, entry, 15),
         f"{CONTROL_ENTRY}'s address is formed"),
        ("the confined control hart calls boot code",
         call_site_in(elf, flat, CONTROL_CONFINED, WAIT_READY),
         call_pair(call_site_in(elf, flat, CONTROL_CONFINED, WAIT_READY),
                   symbols[MVP_MAIN]),
         f"through {CONTROL_ENTRY} -> {CONTROL_CONFINED} -> {MVP_MAIN}"),
        ("the confined control hart installs no vector",
         formation_site(elf, flat, CONTROL_CONFINED, symbols[MVP_VECTOR]),
         struct.pack("<II", NOP, NOP),
         "the control roots do not reach the shared trap vector"),
        ("boot code reaches the control loop",
         call_site_in(elf, flat, START_HARTS, EXEC_CONFINE),
         call_pair(call_site_in(elf, flat, START_HARTS, EXEC_CONFINE),
                   symbols[CONTROL_LOOP]),
         f"boot code reaches {CONTROL_LOOP}"),
        ("a console write between the last start and the confine",
         call_site_in(elf, flat, START_HARTS, "be_mvp_control_started"),
         call_pair(call_site_in(elf, flat, START_HARTS,
                                "be_mvp_control_started"),
                   symbols["be_mvp_exec_console_write"]),
         "on a path from a start to hart 0's confine"),
        # R2-1: a call that runs between the starts and lies before the
        # last start's call by address, which an address-order rule admits.
        ("a console write between the starts, before the last start's call",
         between_starts, call_pair(between_starts,
                                   symbols["be_mvp_exec_console_write"]),
         "on a path from a start to hart 0's confine"),
        # R2-2: a helper start_harts may call there, calling the firmware.
        ("a start helper calls the firmware", helper_slot,
         call_pair(helper_slot, symbols[MVP_FW_CALL]),
         f"be_mvp_control_started, which {START_HARTS} may call between "
         f"the starts and hart 0's confine, reaches {MVP_FW_CALL}"),
        ("the control loop calls the firmware itself", control_slot,
         call_pair(control_slot, symbols[MVP_FW_CALL]),
         f"the control roots reach {MVP_FW_CALL} through"),
    ]
    elfs = [
        ("the control entry off its slot's first byte",
         *symbol_value(elf, CONTROL_ENTRY, entry + 4),
         f"ASSERT fails: DEFINED({CONTROL_ENTRY}) ? {CONTROL_ENTRY} == "
         f"0x{entry:x} : 1"),
        ("a second function in the control entry slot",
         *symbol_value(elf, WAIT_READY, entry + 0x100),
         "the control entry slot holds"),
    ]
    return monitor, elfs


def boundary_mutations(elf, flat, symbols, dispatch_slot, boot_slot):
    """M11-7's rules, each one's defect in a boundary-on monitor: the stub
    without its block check, a second call site of the executor's confine,
    an instruction forming the hart entry's address, the identity read
    called from a domain hart (M11-3's role extents refuse it) or from
    other boot code, a domain hart calling the firmware, and the linked
    identity not the descriptor's."""
    stub = function_words(elf, flat, MVP_CONFINE_ENTRY, BASE)
    check = next(pc for pc, _, word in stub if word & 0x7F == 0x63)
    identity = symbols[MVP_PARTITION_IDENTITY]
    word = lambda value: struct.pack("<I", value)  # noqa: E731
    return [
        ("the stub without its block check", check, word(NOP),
         "does not require exactly the private blocks"),
        ("a second call site of the executor's confine", boot_slot,
         call_pair(boot_slot, symbols[EXEC_CONFINE]),
         f"{EXEC_CONFINE} call sites"),
        ("an instruction forms the hart entry's address", boot_slot,
         pool_reference(boot_slot, symbols[MVP_ENTRY], 15),
         f"{MVP_ENTRY}'s address is formed"),
        ("a domain hart reads the identity", dispatch_slot,
         call_pair(dispatch_slot, symbols[EXEC_IDENTITY]),
         "outside their executable role extents"),
        ("other boot code reads the identity", boot_slot,
         call_pair(boot_slot, symbols[EXEC_IDENTITY]),
         f"{EXEC_IDENTITY} call sites"),
        ("a domain hart calls the firmware", dispatch_slot,
         call_pair(dispatch_slot, symbols[MVP_FW_CALL]),
         f"reach {MVP_FW_CALL} in a boundary-on image"),
        ("the linked identity not the descriptor's", identity + 31,
         bytes([flat[identity + 31 - BASE] ^ 1]),
         "is not the identity of"),
    ]


def boundary_boot_mutations(boot_img):
    """A boundary-on shim's defects: its refused report line missing, and an
    HSM hart_start, the start rule's call, in place of its DBCN write (its
    EID's two instructions, lui and addiw into a7, rewritten)."""
    dbcn = shim_ecall(boot_img, SBI_DBCN)
    lui = next(dbcn - 4 * back for back in range(1, 16)
               if struct.unpack_from("<I", boot_img, dbcn - 4 * back)[0] ==
               (SBI_DBCN + 0x800 >> 12 << 12) | 17 << 7 | 0x37)
    hsm = (SBI_HSM + 0x800 >> 12 << 12) | 17 << 7 | 0x37, \
        (SBI_HSM & 0xFFF) << 20 | 17 << 15 | 17 << 7 | 0x1B
    return [
        ("the refused report line missing", boot_img.index(SHIM_TEMPLATE_ON),
         b"X", "template is missing"),
        ("an HSM hart_start in the boundary-on shim", lui,
         struct.pack("<II", *hsm), "the shim calls"),
    ]


def inject_call_sites(elf, flat):
    """The executor's injection's call sites, the denial action's:
    [(owner, pc, link)]."""
    code = (elf.symbols["__be_mvp_text_start"],
            elf.symbols["__be_mvp_text_end"])
    found = []
    for value, size, names in function_map(elf, *code):
        owner = names[0] if len(names) == 1 else "/".join(names)
        decoded = instructions(flat, value, value + size, BASE)
        found += [(owner, pc, link) for pc, target, link in
                  references(decoded, owner)
                  if target == elf.symbols[EXEC_INJECT]]
    return found


def probe_mutation_test(probe, toolchain, elf_path, bin_path, boot_path,
                        pins, kernel, layout):
    """The probe profile's own defects: a probe image's hgatp writers and
    install call sites, and its log's launch registers (M9)."""
    elf_data = open(elf_path, "rb").read()
    flat = open(bin_path, "rb").read()
    boot_img = open(boot_path, "rb").read()
    map_text = read_map(elf_path)
    check_image(toolchain, elf_data, flat, boot_img, pins, kernel, layout,
                map_text, profile=probe)
    elf = Elf(elf_data)
    symbols = elf.symbols
    dispatch_slot = word_slots(elf, flat, MVP_DISPATCH, BASE, 2)
    mutations = [
        ("a raw hgatp write in the dispatch", "monitor",
         nth_word(elf, flat, MVP_DISPATCH, BASE),
         struct.pack("<I", 0x68051073), "hgatp written by"),
        ("another install call", "monitor", dispatch_slot,
         call_pair(dispatch_slot, symbols[R3_INSTALL]),
         "install call sites"),
        ("a probe's linked launch register nonzero", "monitor",
         symbols[MVP_LOG_CONSTANTS_SYMBOL] + LOG_LAUNCH_AT, b"\x01",
         "linked launch registers are not zero"),
    ]
    if probe == "probe-platform":
        site = [pc for pc, target, link in references(
            function_words(elf, flat, PROBE_HGATP, BASE), PROBE_HGATP)
            if target == symbols[EXEC_INSTALL] and link == 1]
        mutations.append(("the probe's install call removed", "monitor",
                          site[0] - 4, struct.pack("<II", NOP, NOP),
                          "install call sites"))
        mutations.append(("the probe's hgatp probe in the accepted code "
                          "extent", "elf", *symbol_value(
                              elf, PROBE_HGATP,
                              symbols["__be_monitor_code_start"] + 0x40),
                          "overlap"))
    else:
        mutations.append(("the raw switch fenced", "monitor",
                          symbols[PROBE_SWITCH] + 4,
                          struct.pack("<I", 0x62000073), "hfence.gvma sites"))
        mutations.append(("the raw switch in the control entry slot", "elf",
                          *symbol_value(elf, PROBE_SWITCH,
                                        symbols["__be_mvp_text_start"]),
                          "functions overlap the reserved control entry slot"))
    return run_mutations(toolchain, elf_data, flat, boot_img, pins, kernel,
                         layout, mutations, probe, map_text)


# ------------------------------------------------------------------- main
def number(text):
    return int(text, 0)


def read_map(elf_path):
    """The link map beside an ELF (NAME.map for NAME.elf), when present."""
    path = pathlib.Path(elf_path).with_suffix(".map")
    return path.read_text() if path.is_file() else None


def read(path):
    return open(path, "rb").read()


def select_boundary(images, pairing, reports):
    """M11-7: the boundary-on IMAGES, the pairing file's pairs (each line
    "RUN-IMAGE PAIRED-IMAGE"), and the identities of REPORTS' descriptors,
    before any check."""
    global BOUNDARY_IMAGES
    BOUNDARY_IMAGES = frozenset(images)
    if pairing:
        for number_, text in enumerate(read(pairing).decode().splitlines(),
                                       1):
            text = text.strip()
            if not text or text.startswith("#"):
                continue
            fields = text.split()
            require(len(fields) == 2 and fields[0] != fields[1] and
                    fields[0] not in PAIRING,
                    f"{pairing}:{number_}: not one pair of two images")
            PAIRING[fields[0]] = fields[1]
    for path in reports:
        report = json.loads(read(path))
        for descriptor in report["descriptors"]:
            image, identity = descriptor["image"], descriptor["identity"]
            require(re.fullmatch(r"[0-9a-f]{64}", identity) and
                    PARTITION_IDENTITIES.get(image, identity) == identity,
                    f"{path}: descriptor {image} has no one identity")
            PARTITION_IDENTITIES[image] = identity


def boundary_image(name):
    """Whether image NAME's monitor is built with the boundary: a run image
    paired with another runs that image's monitor."""
    return PAIRING.get(name, name) in BOUNDARY_IMAGES


def check_partition_identity(elf, flat, base, symbols, image):
    """Rule 5: be_mvp_partition_identity, 32 bytes of the MVP boot
    read-only extent, is the identity of IMAGE's descriptor (its pair's)."""
    pair = PAIRING.get(image, image)
    require(pair in PARTITION_IDENTITIES,
            f"no partition descriptor of {pair} (--partition-report)")
    address = symbols[MVP_PARTITION_IDENTITY]
    size = symbol_size(elf, MVP_PARTITION_IDENTITY)
    low = LAYOUT["MVP_BOOT_RODATA_HPA"]
    require(size == 32 and low <= address and
            address + size <= low + LAYOUT["MVP_BOOT_RODATA_BYTES"],
            f"{MVP_PARTITION_IDENTITY} is not 32 bytes of the MVP boot "
            f"read-only extent")
    linked = flat[address - base:address - base + size]
    require(linked == bytes.fromhex(PARTITION_IDENTITIES[pair]),
            f"{MVP_PARTITION_IDENTITY} {linked.hex()} is not the identity "
            f"of {pair}'s descriptor, {PARTITION_IDENTITIES[pair]}")


def check_control_entry(decoded, symbols):
    """Rules C2 and C14 (M11-8): the control hart's confined entry is
    exactly sp formed as hart 0's stack top, the call of its C side, the
    exception class in a0, and the tail of the terminal: seven words, no
    load or store, no other instruction."""
    words = [word for _, width, word in decoded]
    require(len(decoded) == 7 and all(width == 4 for _, width, _ in decoded),
            f"{CONTROL_ENTRY} is {len(decoded)} instructions, not seven "
            f"words (C2)")
    pcs = [pc for pc, _, _ in decoded]
    found = {pc: (target, link)
             for pc, target, link in references(decoded, CONTROL_ENTRY)}
    shape = [
        (words[0] & 0xFFF == (2 << 7 | 0x17), "auipc sp"),
        (words[1] & 0xFFFFF == (2 << 15 | 2 << 7 | 0x13), "addi sp, sp"),
        (found.get(pcs[1]) == (symbols["__be_control_stack_end"], None),
         "sp formed as __be_control_stack_end"),
        (words[2] & 0xFFF == (1 << 7 | 0x17), "auipc ra"),
        (words[3] & 0xFFFFF == (1 << 15 | 1 << 7 | 0x67), "jalr ra, ra"),
        (found.get(pcs[3]) == (symbols[CONTROL_CONFINED], 1),
         f"the call of {CONTROL_CONFINED}"),
        (words[4] & 0xFFFFF == (10 << 7 | 0x13), "addi a0, zero"),
        (words[5] & 0xFFF == (6 << 7 | 0x17), "auipc t1"),
        (words[6] & 0xFFFFF == (6 << 15 | 0x67), "jalr zero, t1"),
        (found.get(pcs[6]) == (symbols[MVP_TERMINAL], 0),
         f"the tail of {MVP_TERMINAL}")]
    for ok, what in shape:
        require(ok, f"{CONTROL_ENTRY} is not {what} in its place (C2)")
    wanted = class_number("BE_MVP_CLASS_EXCEPTION")
    require(signed(words[4] >> 20, 12) == wanted,
            f"{CONTROL_ENTRY} passes class {signed(words[4] >> 20, 12)} to "
            f"the terminal, not BE_MVP_CLASS_EXCEPTION, {wanted} (C14)")


def function_node(elf, flat, name):
    """Function NAME as role_nodes() gives each: (start, end, owner, its
    references, its words by pc)."""
    value, size = function_start(elf, name)
    decoded = instructions(flat, value, value + size, BASE)
    return (value, value + size, name, references(decoded, name),
            {pc: (width, word) for pc, width, word in decoded})


def start_tail_paths(node, symbols):
    """C7's walk (M11-8, R2-1) over start_harts, NODE as role_nodes() gives
    it: from the return of each call of the executor's hart_start, every
    path, each ending at the call of the executor's confine or at a call,
    or a tail call out of the function, to any other function, which the
    rule judges. Returns ([(pc, target, link)], each call and tail call out
    on those paths; the pcs the walk visits). A path that returns, runs
    past the function's end, branches out of it, or takes a jump or call
    that the walk cannot follow is refused."""
    low, high, _, refs, words = node
    pcs = sorted(words)
    at = {pc: index for index, pc in enumerate(pcs)}
    transfers = {pc: (target, link) for pc, target, link in refs
                 if link is not None}
    start, confine = symbols[EXEC_HART_START], symbols[EXEC_CONFINE]
    ends = {symbols[name] for name in START_TAIL_ENDS if name in symbols}
    starts = [at[pc] for pc in pcs if transfers.get(pc) == (start, 1)]
    confines = [pc for pc in pcs if transfers.get(pc) == (confine, 1)]
    require(starts and len(confines) == 1,
            f"{START_HARTS} calls {EXEC_HART_START} at "
            f"{[hex(pcs[index]) for index in starts]} and {EXEC_CONFINE} at "
            f"{[hex(pc) for pc in confines]}, not the confine once after "
            f"the starts (C7)")
    calls, seen = [], set()
    work = [index + 1 for index in starts]
    while work:
        index = work.pop()
        if index in seen:
            continue
        require(index < len(pcs), f"{START_HARTS} runs past its end on a "
                f"path from a start (C7)")
        seen.add(index)
        pc = pcs[index]
        width, word = words[pc]
        insn = decode(word, width, pc)
        target, link = transfers.get(pc, (None, None))
        if link == 1:
            calls.append((pc, target, link))
            if target != confine and target not in ends:
                work.append(index + 1)
            continue
        if link == 0:
            if low <= target < high:
                require(target in at, f"{START_HARTS} jumps into an "
                        f"instruction at 0x{target:x} (C7)")
                work.append(at[target])
            else:
                calls.append((pc, target, link))
            continue
        require(not insn.get("unknown"), f"{START_HARTS} has an instruction "
                f"at 0x{pc:x} that the walk cannot decode (C7)")
        require(not (insn.get("indirect") and insn.get("stop") and
                     insn.get("base") == 1),
                f"{START_HARTS} returns at 0x{pc:x}, on a path from a start, "
                f"before hart 0's confine (C7)")
        require(not insn.get("call") and not insn.get("stop"),
                f"{START_HARTS} has a jump or call at 0x{pc:x}, on a path "
                f"from a start to hart 0's confine, that the walk cannot "
                f"follow (C7)")
        if insn.get("branch") is not None:
            require(low <= insn["branch"] < high and insn["branch"] in at,
                    f"{START_HARTS} branches out of itself at 0x{pc:x} (C7)")
            work.append(at[insn["branch"]])
        work.append(index + 1)
    return calls, {pcs[index] for index in seen}


def check_start_tail(nodes, symbols):
    """Rule C7 (M11-8; D-6 step 6; R2-1, R2-2), by start_harts' control
    flow: on every path from the return of a call of the executor's
    hart_start to the call of its confine (start_tail_paths()), each call
    is to hart_start again, to one of START_TAIL_HELPERS, which return, or
    to one of START_TAIL_ENDS, which do not and so end the path, and each
    tail call out of the function to one of START_TAIL_ENDS; and each of
    START_TAIL_HELPERS reaches no firmware call (CONTROL_FIRMWARE) and no
    ring function (RING_PREFIX, the only code that reads a mailbox). So
    hart 0 makes no firmware call and reads no ring between the starts, and
    none after the second start before its own confine."""
    owner_at = node_owner(nodes)
    index = owner_at(symbols[START_HARTS])
    require(index is not None and nodes[index][0] == symbols[START_HARTS],
            f"{START_HARTS} is not one function in the image (C7)")
    calls, _ = start_tail_paths(nodes[index], symbols)
    names = {symbols[name]: name for name in START_TAIL_HELPERS +
             START_TAIL_ENDS + (EXEC_HART_START, EXEC_CONFINE)
             if name in symbols}
    ends = {symbols[name] for name in START_TAIL_ENDS if name in symbols}
    for pc, target, link in calls:
        label = names.get(target, f"0x{target:x}")
        if link:
            require(target in names,
                    f"{START_HARTS} calls {label} at 0x{pc:x}, on a path from "
                    f"a start to hart 0's confine, where only "
                    f"{EXEC_HART_START} again, "
                    f"{', '.join(START_TAIL_HELPERS)}, and "
                    f"{', '.join(START_TAIL_ENDS)} may be called (C7)")
        else:
            require(target in ends,
                    f"{START_HARTS} tail-calls {label} at 0x{pc:x}, on a "
                    f"path from a start to hart 0's confine, where only "
                    f"{', '.join(START_TAIL_ENDS)}, which do not return, may "
                    f"end it (C7)")
    for name in START_TAIL_HELPERS:
        if name not in symbols:
            continue
        reached, _ = closure(nodes, owner_at, [owner_at(symbols[name])])
        found = sorted({part for item in reached
                        for part in nodes[item][2].split("/")
                        if part in CONTROL_FIRMWARE or
                        part.startswith(RING_PREFIX)})
        require(not found,
                f"{name}, which {START_HARTS} may call between the starts and "
                f"hart 0's confine, reaches {', '.join(found)}: a firmware "
                f"call or a ring (C7)")


def check_boundary_code(functions, decoded_all, found, symbols, nodes=None,
                        control=None):
    """Rules 1 to 4 of a boundary-on image (planning/mvp-m11-plan.md, D-6
    and D-8): the stub, in MVP boot text past the park page, checks its
    block and sets sp as the hart entry does, then calls the executor's
    confine, or parks; confine and the identity read each reach
    be_mvp_fw_call alone, the read from hart 0's firmware probe alone; no
    instruction names the hart entry, and hart 0's start names the stub,
    once; and no code a VS-domain hart runs, from the hart entry or the
    trap vector, reaches a firmware call. And step 2's (M11-8, D-6 step
    6): the control hart's confined entry (whose words, C2 and C14,
    check_instructions() reads first), whose address no code forms but as
    the MVP region's start in hart 0's region check (C3); boot code that
    reaches none
    of the control hart's confined code (C5); the executor's confine
    called twice, by the stub and by start_harts (C6), with no firmware
    call and no ring read on any path from a start to it (C7); and the
    control roots' firmware calls through the console write, the reset, and
    the console read alone (C13)."""
    by_name = dict(decoded_all)
    stub = symbols[MVP_CONFINE_ENTRY]
    boot = LAYOUT["MVP_BOOT_TEXT_HPA"]
    require(boot + LAYOUT["PARK_BYTES"] <= stub <
            boot + LAYOUT["MVP_BOOT_TEXT_BYTES"],
            f"{MVP_CONFINE_ENTRY} at 0x{stub:x} is not in MVP boot text past "
            f"the park page")
    check_hart_entry(by_name[MVP_CONFINE_ENTRY], symbols, MVP_CONFINE_ENTRY,
                     EXEC_CONFINE)
    sites = {name: [] for name in (EXEC_CONFINE, EXEC_IDENTITY,
                                   MVP_CONFINE_ENTRY, MVP_ENTRY,
                                   CONTROL_ENTRY)}
    for owner, references_ in found.items():
        for pc, target, link in references_:
            for name in sites:
                if target == symbols[name]:
                    sites[name].append((owner, hex(pc), link))
    # The entry is the MVP region's first byte, which hart 0's region check
    # forms as the region's start: that one formation, as data, and no
    # call or jump.
    require(len(sites[CONTROL_ENTRY]) <= 1 and
            all(owner in REGION_CHECK_OWNERS and link is None
                for owner, _, link in sites[CONTROL_ENTRY]),
            f"{CONTROL_ENTRY}'s address is formed at {sites[CONTROL_ENTRY]}, "
            f"not only as the MVP region's start by hart 0's region check; "
            f"only the device tree names the entry (C3)")
    if nodes is not None:
        reached = {name for index in
                   boot_reach(nodes, node_owner(nodes), symbols)[0]
                   for name in nodes[index][2].split("/")}
        for name in CONTROL_ONLY:
            require(name not in reached,
                    f"boot code reaches {name}, which only hart 0's "
                    f"confined entry may reach (C5)")
    require(sorted((owner, link) for owner, _, link in sites[EXEC_CONFINE])
            == sorted([(MVP_CONFINE_ENTRY, 1), (START_HARTS, 1)]),
            f"{EXEC_CONFINE} call sites {sites[EXEC_CONFINE]}, expected two, "
            f"the stub's call and {START_HARTS}' (C6)")
    check_start_tail(nodes, symbols)
    require(sites[EXEC_IDENTITY] and
            all(owner in BOUNDARY_PROBE_OWNERS
                for owner, _, _ in sites[EXEC_IDENTITY]),
            f"{EXEC_IDENTITY} call sites {sites[EXEC_IDENTITY]}, expected "
            f"hart 0's firmware probe's alone")
    for name in (EXEC_CONFINE, EXEC_IDENTITY):
        targets = {target for _, target, _ in found[name]}
        require(targets == {symbols[MVP_FW_CALL]},
                f"{name} reaches "
                f"{sorted(hex(target) for target in targets)}, expected "
                f"{MVP_FW_CALL} alone")
    require(not sites[MVP_ENTRY],
            f"{MVP_ENTRY}'s address is formed at {sites[MVP_ENTRY]} in a "
            f"boundary-on image")
    require(len(sites[MVP_CONFINE_ENTRY]) == 1 and
            sites[MVP_CONFINE_ENTRY][0][0] in BOUNDARY_START_OWNERS and
            sites[MVP_CONFINE_ENTRY][0][2] is None,
            f"{MVP_CONFINE_ENTRY} is named at {sites[MVP_CONFINE_ENTRY]}, "
            f"expected once, by hart 0's start")
    _, reached, parent = reachable_functions(
        functions, found, symbols, DOMAIN_ROOTS, "VS-domain-hart",
        skip=lambda source, target: MVP_VECTOR in source.split("/") and
        target == symbols[MVP_TERMINAL])
    for owner in sorted(reached):
        for name in owner.split("/"):
            path = [owner]
            while parent[path[-1]] is not None:
                path.append(parent[path[-1]])
            require(name not in VS_UNREACHABLE and
                    not name.startswith(VS_UNREACHABLE_PREFIX),
                    f"the VS-domain-hart roots reach {name} in a "
                    f"boundary-on image, through "
                    f"{' -> '.join(reversed(path))}")
    if nodes is not None and control is not None:
        check_control_firmware(nodes, control, symbols)


def check_control_firmware(nodes, control, symbols):
    """Rule C13 (M11-8; D-8): the control roots reach the firmware
    (be_mvp_fw_call, be_r3_arch_sbi_call) only through the console write,
    the reset, and the console read: a reach from them that stops at those
    three holds neither; and the control reach (CONTROL) holds none of the
    boot code's firmware helpers (hart_start, hart_status, the probes,
    confine, the identity read, an IPI send, the boundary-off console
    write)."""
    for index in sorted(control):
        for name in nodes[index][2].split("/"):
            require(name not in CONTROL_UNREACHABLE,
                    f"the control roots reach {name}, a firmware helper of "
                    f"boot code's (C13)")
    owner_at = node_owner(nodes)
    skip = {symbols[name] for name in (MVP_DISPATCH, MVP_HART_TERMINAL)
            if name in symbols}
    roots = [owner_at(symbols[name]) for name in
             (CONTROL_LOOP, MVP_TERMINAL, CONTROL_ENTRY)]
    parent = {index: None for index in roots}
    work = list(roots)
    while work:
        source = work.pop()
        names = nodes[source][2].split("/")
        path = [source]
        while parent[path[-1]] is not None:
            path.append(parent[path[-1]])
        firmware = [name for name in names if name in CONTROL_FIRMWARE]
        require(not firmware,
                f"the control roots reach {firmware[0] if firmware else ''} "
                f"through "
                f"{' -> '.join(nodes[item][2] for item in reversed(path))}, "
                f"not through {', '.join(CONTROL_FIRMWARE_CALLERS)} (C13)")
        if any(name in CONTROL_FIRMWARE_CALLERS for name in names):
            continue
        for _, target, _ in nodes[source][3]:
            if nodes[source][0] == symbols[MVP_VECTOR] and target in skip:
                continue
            owner = owner_at(target)
            if owner is not None and owner not in parent:
                parent[owner] = source
                work.append(owner)


def check_breach_kinds(kinds):
    """A breach image's hook's own instructions (BREACH_KINDS): each once,
    in its attempt helper, and none in any other function."""
    require(kinds == {BREACH_ATTEMPT: BREACH_KINDS},
            f"the hook's instructions are in {sorted(kinds.items())}, not "
            f"{BREACH_KINDS} in {BREACH_ATTEMPT} alone, outside which none "
            f"may be")


def breach_executor(helper):
    """The executor function of a hook helper."""
    return BREACH_EXEC_PREFIX + helper[len("be_mvp_breach_arch_"):]


def check_breach_code(functions, found, symbols, map_text, role=0,
                      boundary=True):
    """A breach image's hook (planning/mvp-m11-plan.md, D-10; M11-7): its
    functions in MVP VS text; one call of the hook, from the dispatch; each
    helper named by its executor function alone, and the vector by the
    entry alone; and each executor function called from the hook's object
    (mvp-breach.o) alone. M11-8: the control hart's (ROLE BREACH_CONTROL)
    in MVP control text, its one call from hart 0's confined entry, or in
    its -off copy (not BOUNDARY) from start_run() or the main it is folded
    into."""
    control = role == BREACH_CONTROL
    text = "MVP_CONTROL_TEXT" if control else "MVP_DOMAIN_TEXT"
    low = LAYOUT[f"{text}_HPA"]
    high = low + LAYOUT[f"{text}_BYTES"]
    hook = BREACH_CONTROL_HOOK if control else BREACH_HOOK
    callers = ((CONTROL_CONFINED,) if boundary else BREACH_OFF_CALLERS) \
        if control else (MVP_DISPATCH,)
    named = (hook, BREACH_VECTOR) + BREACH_ARCH + tuple(
        breach_executor(helper) for helper in BREACH_ARCH)
    for name in named:
        require(symbols.get(name) is not None,
                f"{name} is missing from a breach image")
    for value, size, names in functions:
        if any(name.startswith(BREACH_PREFIXES) for name in names):
            require(low <= value and value + size <= high,
                    f"{'/'.join(names)} at 0x{value:x} is outside MVP "
                    f"{'control' if control else 'VS'} text")
    hook_text = [(address, address + size) for address, size, name, section
                 in map_entries(map_text) if name == "mvp-breach.o" and
                 section.startswith(".text")]
    require(hook_text, "the link map places no text of mvp-breach.o")
    sites = {name: [] for name in named}
    for owner, references_ in found.items():
        for pc, target, link in references_:
            for name in named:
                if target == symbols[name]:
                    sites[name].append((owner, pc, link))
    require(len(sites[hook]) == 1 and sites[hook][0][2] == 1 and
            sites[hook][0][0] in callers,
            f"{hook} is named at {sites[hook]}, expected one call, from "
            f"{' or '.join(callers)}")
    for helper in BREACH_ARCH:
        require([owner for owner, _, link in sites[helper]
                 if link is not None] == [breach_executor(helper)] and
                len(sites[helper]) == 1,
                f"{helper} is named at {sites[helper]}, expected one call, "
                f"from {breach_executor(helper)}")
    require([(owner, link) for owner, _, link in sites[BREACH_VECTOR]] ==
            [(BREACH_ENTER, None)],
            f"{BREACH_VECTOR} is named at {sites[BREACH_VECTOR]}, expected "
            f"once, by {BREACH_ENTER}")
    for helper in BREACH_ARCH:
        callers = sites[breach_executor(helper)]
        require(callers and all(
            link is not None and any(start <= pc < end
                                     for start, end in hook_text)
            for _, pc, link in callers),
                f"{breach_executor(helper)} is named at {callers}, expected "
                f"calls from mvp-breach.o alone")


def check_no_breach(symbols, map_text, image):
    """An image that is not a breach image links no hook symbol and no
    hook object."""
    linked = sorted(name for name in symbols
                    if name.startswith(BREACH_PREFIXES))
    require(not linked, f"{image}, not a breach image, links {linked}")
    require(map_text is None or not any(
        name in BREACH_OBJECTS for _, _, name, _ in map_entries(map_text)),
            f"{image}, not a breach image, places a hook object")


def load_breach_tool():
    spec = importlib.util.spec_from_file_location("mvp_gen_breach",
                                                  BREACH_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def breach_rows(name, elf):
    """tools/gen-breach.py's rows and facts for breach image NAME,
    resolved through ELF's symbols."""
    declaration_path, domain = BREACH[name]
    tool = load_breach_tool()
    declaration = tool.load(declaration_path)
    facts = tool.Facts(LAYOUT, tool.defines(BREACH_HEADER),
                       declaration.get("devices", {}), domain)
    symbols = {key: value for key, value in elf.symbols.items()
               if value is not None}
    try:
        rows = tool.resolve(declaration, facts, name.endswith("-off"),
                            symbols)
    except tool.Refused as error:
        raise ImageError(f"{name}'s declaration: {error}") from error
    return tool, facts, rows


def sized_symbols(elf):
    """[(start, end, name)] of every symbol with a size."""
    out = []
    for name, entries in elf.symbol_entries.items():
        for entry in entries:
            value, size = struct.unpack_from("<QQ", elf.data, entry + 8)
            if name and size:
                out.append((value, value + size, name))
    return out


def check_breach_table(name, elf, flat, data, boot):
    """A breach image's linked table and modes (BREACH_TABLE,
    BREACH_MODES_TABLE), decoded, are tools/gen-breach.py's from the
    declaration, through the image's symbols and the layout; each word a
    row writes inside the image is zero padding that no object holds but
    the log page's unused tail; and each window's DTB blocks (its header,
    memory reservation map, structure, and strings; the rest of the page
    is dtc -S's free space, inside the blob's totalsize, which no reader
    walks) end below each word a row writes in its page."""
    tool, facts, rows = breach_rows(name, elf)
    table = elf.symbols.get(BREACH_TABLE)
    modes = elf.symbols.get(BREACH_MODES_TABLE)
    require(table is not None and modes is not None,
            f"{name} links no {BREACH_TABLE} or {BREACH_MODES_TABLE}")
    width = facts.header["BREACH_ROW_BYTES"]
    require(symbol_size(elf, BREACH_TABLE) == width * len(rows),
            f"{name}'s {BREACH_TABLE} holds "
            f"{symbol_size(elf, BREACH_TABLE) // width} rows, the "
            f"declaration {len(rows)}")
    for index, row in enumerate(rows):
        got = struct.unpack_from("<5Q", flat, table - BASE + width * index)
        wanted = (row["kind"], row["access"], row["value"], row["extra"],
                  row["call"])
        require(got == wanted, f"{name}'s table row {row['row']} is "
                f"{tuple(hex(value) for value in got)}, the declaration's "
                f"{tuple(hex(value) for value in wanted)}")
    # The hooked role's modes, as many as the header gives it (gen-breach's
    # Facts requires that).
    count = len(facts.modes)
    require(symbol_size(elf, BREACH_MODES_TABLE) == 24 * count and
            struct.unpack_from(f"<{3 * count}Q", flat, modes - BASE) ==
            tuple(value for mode in facts.modes for value in mode),
            f"{name}'s {BREACH_MODES_TABLE} is not the declaration's")
    sized = sized_symbols(elf)
    pages = [(guest, LAYOUT[f"G{guest}_HPA"] + LAYOUT["DTB_GPA"] -
              LAYOUT["GUEST_GPA"]) for guest in (0, 1)]
    for row in rows:
        if row["op"] not in tool.WRITES or row["at"] is None:
            continue
        for low, high in tool.span(row):
            if BASE <= low and high <= BASE + len(flat):
                require(flat[low - BASE:high - BASE] == bytes(high - low),
                        f"{name}'s row {row['row']} writes 0x{low:x}, which "
                        f"is not zero in the image")
                holders = [symbol for start, end, symbol in sized
                           if start < high and low < end and not (
                               symbol == MVP_LOG_SYMBOL and
                               low >= start + LOG_USED_BYTES)]
                require(not holders, f"{name}'s row {row['row']} writes "
                        f"0x{low:x}, which {sorted(set(holders))} hold")
            for guest, page in pages:
                if page <= low < page + LAYOUT["DTB_BYTES"]:
                    used = dtb_blocks_end(
                        data[boot[f"dtb{guest}_offset"]:
                             boot[f"dtb{guest}_offset"] +
                             LAYOUT["DTB_BYTES"]])
                    require(used <= low - page,
                            f"{name}'s row {row['row']} writes inside G"
                            f"{guest}'s DTB blocks, which end at {used} "
                            f"bytes")
    return len(rows)


def dtb_blocks_end(blob):
    """The end of a flattened device tree's last block: its 40-byte header,
    its memory reservation map to the zero entry, its structure block, and
    its strings block, each inside the blob's totalsize."""
    magic, total, structure, strings, reserved = struct.unpack_from(
        ">5I", blob, 0)
    strings_size, structure_size = struct.unpack_from(">2I", blob, 32)
    require(magic == 0xD00DFEED and total <= len(blob) and total >= 40,
            f"a DTB with magic 0x{magic:x} and totalsize {total}")
    entry = reserved
    while True:
        require(entry + 16 <= total, "a DTB's reservation map has no end")
        if struct.unpack_from(">2Q", blob, entry) == (0, 0):
            break
        entry += 16
    ends = (40, entry + 16, structure + structure_size,
            strings + strings_size)
    require(max(ends) <= total, f"a DTB's blocks end at {max(ends)}, past "
            f"its totalsize {total}")
    return max(ends)


def breach_mutations(name, toolchain, monitor, layout, scenario, data,
                     boot):
    """A breach image's mutations, each refused for its own reason: a hook
    instruction (an AMO) in the dispatch (M11-8: the control hart's, in
    its control loop), outside the helpers; a table row changed; both DTBs'
    strings blocks grown to their totalsize, so that a row's word in a DTB
    page is inside its blocks; and the image under anchor's name, which
    links the hook. Returns their number."""
    elf_data, flat, map_text = monitor
    elf = Elf(elf_data)
    amo = matching_word(elf, flat, BREACH_ATTEMPT, BASE,
                        lambda value: value & 0x7F == 0x2F and
                        value >> 27 == 0)[1]
    host = CONTROL_LOOP if BREACH[name][1] == BREACH_CONTROL else \
        MVP_DISPATCH
    slot, _ = matching_word(elf, flat, host, BASE,
                            lambda value: value & 0x7F in (0x03, 0x23))
    table = elf.symbols[BREACH_TABLE]
    mutants = []
    mutated_elf, mutated_flat = bytearray(elf_data), bytearray(flat)
    patch(mutated_elf, mutated_flat, bytearray(len(data)), slot,
          struct.pack("<I", amo), BASE)
    mutants.append((f"an AMO in {host}", lambda: check_monitor(
        toolchain, bytes(mutated_elf), bytes(mutated_flat), BASE, layout,
        map_text, "mvp", name, scenario=scenario),
        "the hook's instructions are in"))
    changed = bytearray(flat)
    changed[table - BASE + 8] ^= 0x08
    mutants.append(("a table row's address changed", lambda: check_breach_table(
        name, elf, bytes(changed), data, boot), "table row"))
    grown = bytearray(data)
    for guest in (0, 1):
        offset = boot[f"dtb{guest}_offset"]
        total, _, strings = struct.unpack_from(">3I", grown, offset + 4)
        struct.pack_into(">I", grown, offset + 32, total - strings)
    mutants.append(("the DTBs' strings grown to their totalsize",
                    lambda: check_breach_table(name, elf, flat, bytes(grown),
                                               boot),
                    "DTB blocks, which end at 4096 bytes"))
    mutants.append(("the image under anchor's name", lambda: check_no_breach(
        elf.symbols, map_text, scenario.name), "not a breach image, links"))
    for label, call, expected in mutants:
        try:
            call()
        except ImageError as error:
            require(expected in str(error),
                    f"{name}'s mutation {label!r} rejected for another "
                    f"reason: {error}")
            continue
        raise ImageError(f"{name}'s mutation {label!r} was accepted")
    return len(mutants)


def select_variant(monitor, flavour):
    """beryllium-cheri: the rules of MONITOR and FLAVOUR, before any
    check."""
    global MONITOR, GUEST_FLAVOUR, HELPER_WRITES, ISA_EXTENSIONS
    global TE_POC_VARIANTS, VARIANTS, CHERI_TE_POC_VARIANTS, DTB_VARIANTS
    MONITOR, GUEST_FLAVOUR = monitor, flavour
    if monitor == "cheri":
        CSR_NAMES.update(CHERI_CSR_NAMES)
        CSR_WRITERS.update(CHERI_CSR_WRITERS)
        HELPER_WRITES = CHERI_HELPER_WRITES
        if flavour == "cheri-linux":
            CHERI_TE_POC_VARIANTS += tuple(CHERI_VARIANT_HEDELEG) + \
                tuple(CHERI_DTB_VARIANT_INITS)
            DTB_VARIANTS += tuple(CHERI_DTB_VARIANT_INITS)
            DTB_VARIANT_GUESTS.update(dict.fromkeys(CHERI_DTB_VARIANT_INITS,
                                                    (0,)))
        TE_POC_VARIANTS += CHERI_TE_POC_VARIANTS
        VARIANTS += CHERI_TE_POC_VARIANTS
    ISA_EXTENSIONS = ISA_EXTENSIONS + FLAVOUR_EXTENSIONS[flavour]


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", type=number, default=BASE)
    parser.add_argument("--lds", default=str(MONITOR_LDS))
    parser.add_argument("--pins", required=True)
    parser.add_argument("--kernel", required=True)
    parser.add_argument("--dtb0", required=True)
    parser.add_argument("--dtb1", required=True)
    parser.add_argument("--expect")
    parser.add_argument("--report")
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--probe", action="append", default=[])
    parser.add_argument("--reference")
    parser.add_argument("--variant-dtbs", action="append", default=[])
    parser.add_argument("--variant", action="append", default=[])
    parser.add_argument("--mutation-test")
    parser.add_argument("--mutation-probe", action="append", default=[])
    parser.add_argument("--qemu-image", action="append", default=[])
    parser.add_argument("--board-image", action="append", default=[])
    # beryllium-cheri: the monitor variant and the guest flavour.
    parser.add_argument("--monitor", choices=("riscv", "cheri"),
                        default="riscv")
    parser.add_argument("--guest-flavour", choices=tuple(FLAVOUR_EXTENSIONS),
                        default="linux")
    # M11-7: the boundary-on images, the pairing, and the descriptors.
    parser.add_argument("--boundary-image", action="append", default=[])
    parser.add_argument("--pairing")
    parser.add_argument("--partition-report", action="append", default=[])
    # M11-7: each breach image, its declaration, and its hooked VS domain,
    # or since M11-8 control, the control hart.
    parser.add_argument("--breach", action="append", default=[])
    args = parser.parse_args(argv[1:])
    select_variant(args.monitor, args.guest_flavour)
    if not (args.image or args.probe or args.variant or args.mutation_test
            or args.variant_dtbs or args.mutation_probe or args.qemu_image):
        parser.error("nothing to check")
    if args.variant and not args.reference:
        parser.error("--variant needs --reference")
    if len(args.qemu_image) != len(args.board_image):
        parser.error("each --qemu-image needs its --board-image")
    checked = []
    try:
        select_boundary(args.boundary_image, args.pairing,
                        args.partition_report)
        for spec in args.breach:
            fields = spec.split(":")
            require(len(fields) == 3 and fields[0] in VARIANTS and
                    OFF_VARIANTS.get(fields[0], fields[0]) in
                    BREACH_VARIANTS and
                    fields[2] in ("0", "1", BREACH_CONTROL),
                    f"--breach {spec} is not NAME:DECLARATION:DOMAIN of a "
                    f"breach image")
            BREACH[fields[0]] = (fields[1], fields[2] if fields[2] ==
                                 BREACH_CONTROL else int(fields[2]))
        require(args.base == BASE, f"base 0x{args.base:x} is not 0x{BASE:x}")
        pins = read_pins(args.pins)
        kernel = read(args.kernel)
        require(sha256(kernel) == pins[0]["Image"][0],
                "the --kernel file differs from its pin")
        kernel_facts(kernel)
        expect = json.loads(read(args.expect)) if args.expect else None
        report = json.loads(read(args.report)) if args.report else None
        if report is not None:
            require(expect is not None and
                    sha256(read(args.report)) == expect["report"]["sha256"],
                    "the --report file is not the expectation's report")
        scenario = Scenario(expect, report)
        # The expectation (tools/gen-scenario.py's) declares the boundary
        # exactly where the build put it.
        require(expect is None or ("boundary" in expect) ==
                boundary_image(expect["image"]),
                f"the expectation of {expect and expect['image']} and the "
                f"build disagree on its boundary")
        dtbs = [read(args.dtb0), read(args.dtb1)]
        for guest, dtb in enumerate(dtbs):
            check_dt(dtb, guest, scenario.dtb_variant,
                     scenario.bootargs[guest] if scenario.dtb_variant
                     else None)
            pinned = dtb_name(guest, scenario.dtb_variant)
            require(pinned in pins[0], f"no pin for {pinned}")
            require(sha256(dtb) == pins[0][pinned][0],
                    f"the --dtb{guest} file differs from its pin")
        check_dt_pair(*dtbs)
        if expect is not None:
            for guest, dtb in enumerate(dtbs):
                require(parse_fdt(dtb)[1]["/chosen"]["bootargs"] ==
                        strings(expect["domains"][guest]["bootargs"]),
                        f"the --dtb{guest} bootargs are not the scenario's")
        layout = mvp_layout(args.lds)
        asserts = len(layout[1])
        check_region(LAYOUT)
        flats = {}
        for spec in args.image:
            toolchain, elf_path, bin_path, boot_elf, boot_path = \
                spec.split(":")
            require(toolchain in ("gcc", "clang"),
                    f"unknown toolchain {toolchain}")
            flat, boot_img = read(bin_path), read(boot_path)
            report, boot = check_image(
                toolchain, read(elf_path), flat, boot_img, pins, kernel,
                layout, read_map(elf_path), read(boot_elf), boot_path,
                expect=expect, scenario=scenario)
            flats[toolchain] = flat
            label = toolchain if scenario.report is None else \
                f"{scenario.name} {toolchain}"
            print(f"{label}: text_end=0x{report['text_end']:x} "
                  f"data_end=0x{report['data_end']:x} "
                  f"mvp_text_end=0x{report['mvp_text_end']:x} "
                  f"mvp_end=0x{report['mvp_end']:x} functions="
                  f"{report['functions']} words={report['instructions']} "
                  f"asserts={asserts} flat_bytes=0x{len(flat):x} "
                  f"boot_bytes=0x{len(boot_img):x} "
                  f"dtb0_offset=0x{boot['dtb0_offset']:x} "
                  f"dtb1_offset=0x{boot['dtb1_offset']:x} "
                  f"bin_sha256={sha256(flat)} boot_sha256={sha256(boot_img)}")
            checked.append(label.replace(" ", "-"))
        if len(flats) == 2:
            require(flats["gcc"] != flats["clang"],
                    "GCC and Clang flat images are identical")
        for spec in args.probe:
            probe, toolchain, elf_path, bin_path, boot_elf, boot_path = \
                spec.split(":")
            require(probe in PROBES and toolchain in ("gcc", "clang"),
                    f"unknown probe image {probe} or toolchain {toolchain}")
            flat, boot_img = read(bin_path), read(boot_path)
            report, _ = check_image(
                toolchain, read(elf_path), flat, boot_img, pins, kernel,
                layout, read_map(elf_path), read(boot_elf), boot_path,
                profile=probe)
            print(f"{probe} {toolchain}: text_end=0x{report['text_end']:x} "
                  f"data_end=0x{report['data_end']:x} "
                  f"mvp_end=0x{report['mvp_end']:x} functions="
                  f"{report['functions']} words={report['instructions']} "
                  f"bin_sha256={sha256(flat)} boot_sha256={sha256(boot_img)}")
            checked.append(f"{probe}-{toolchain}")
        reference = None
        if args.reference:
            toolchain, elf_path, bin_path, boot_elf, boot_path = \
                args.reference.split(":")
            require(toolchain in ("gcc", "clang"),
                    f"unknown toolchain {toolchain}")
            flat, boot_img = read(bin_path), read(boot_path)
            report, _ = check_image(toolchain, read(elf_path), flat,
                                    boot_img, pins, kernel, layout,
                                    read_map(elf_path), read(boot_elf),
                                    boot_path, expect=expect,
                                    scenario=scenario)
            reference = {"elf": report["elf"], "flat": flat,
                         "boot": boot_img, "toolchain": toolchain}
            if MONITOR == "cheri":
                # beryllium-cheri: the reference's files, for the CHERI
                # variants' mutations (cheri_variant_mutations()).
                reference.update(elf_data=read(elf_path),
                                 map_text=read_map(elf_path),
                                 boot_elf=read(boot_elf),
                                 boot_path=boot_path)
        for spec in args.variant_dtbs:
            name, *paths = spec.split(":")
            require(name in DTB_VARIANTS and len(paths) == 2,
                    f"unknown DTB variant {spec}")
            pair = [read(path) for path in paths]
            for guest, data in enumerate(pair):
                check_dt(data, guest, name)
                pinned = dtb_name(guest, name if guest in
                                  DTB_VARIANT_GUESTS[name] else None)
                require(sha256(data) == pins[0][pinned][0],
                        f"the {name} G{guest} DTB differs from {pinned}")
            check_dt_pair(*pair)
            checked.append(f"dtb-{name}")
        copies = {}
        for spec in args.variant:
            name, *paths = spec.split(":")
            require(len(paths) in (2, 4), f"malformed variant {spec}")
            monitor = None
            if len(paths) == 4:
                monitor = (read(paths[0]), read(paths[1]),
                           read_map(paths[0]))
            boot_elf, boot_path = paths[-2:]
            data = read(boot_path)
            # M11-7: a variant whose boundary is not the reference's is
            # checked against the scenario's off copy (shim-rule's always
            # is), checked first in the same run.
            against = reference
            if name not in OFF_COPIES and \
                    boundary_image(name) != boundary_image(scenario.name):
                off = f"{scenario.name}-off"
                require(off in copies,
                        f"variant {name} needs {off} checked before it")
                against = copies[off]
            # beryllium-cheri: a CHERI variant's own arm helper values.
            cheri_variant_check(name, read(boot_elf), data, against, pins,
                                kernel, boot_path, monitor, layout, scenario)
            if name in OFF_COPIES:
                copies[name] = dict(reference, name=name,
                                    flat=data[MONITOR_OFFSET:
                                              MONITOR_OFFSET + SPAN],
                                    boot=data)
            print(f"variant {name}: boot_sha256={sha256(data)}")
            checked.append(f"variant-{name}")
            if name in OFF_COPIES and monitor is not None and \
                    not boundary_image(scenario.name):
                # An off copy of an image built without the boundary: its
                # mutation, rejected.
                count = off_copy_mutations(name, read(boot_elf), data,
                                           against, pins, kernel, monitor,
                                           layout, scenario)
                print(f"variant {name}: mutations rejected: {count}")
                checked.append(f"variant-{name}-mutations={count}")
            if name in BREACH and monitor is not None:
                # M11-7: the hook's rules, each refusing its mutation.
                elf = Elf(monitor[0])
                flat = monitor[1]
                boot = check_boot(data, BOOT_TEXT_OFFSET,
                                  data[MONITOR_OFFSET:MONITOR_OFFSET + SPAN],
                                  pins, kernel, name, scenario=scenario)
                rows = check_breach_table(name, elf, flat, data, boot)
                count = breach_mutations(name, against["toolchain"], monitor,
                                         layout, scenario, data, boot)
                print(f"variant {name}: breach rows={rows} mutations "
                      f"rejected: {count}")
                checked.append(f"variant-{name}-breach-mutations={count}")
            if name == "shim-rule":
                # Item 137: its wait's rules, each refusing its mutation.
                count = shim_rule_mutations(data, pins, kernel, scenario)
                print(f"variant {name}: mutations rejected: {count}")
                checked.append(f"variant-{name}-mutations={count}")
            if name in CHERI_TE_POC_VARIANTS:
                # beryllium-cheri: its mutations, each rejected.
                count = cheri_variant_mutations(name, reference, pins,
                                                kernel, layout, scenario)
                print(f"variant {name}: mutations rejected: {count}")
                checked.append(f"variant-{name}-mutations={count}")
        if args.mutation_test:
            toolchain, elf_path, bin_path, _, boot_path = \
                args.mutation_test.split(":")
            results = mutation_test(toolchain, elf_path, bin_path, boot_path,
                                    pins, kernel, layout, scenario)
            label = toolchain if scenario.report is None else \
                f"{scenario.name} {toolchain}"
            print(f"{label}: mutations rejected: {len(results)}")
            checked.append(f"mutations={len(results)}")
        for spec in args.mutation_probe:
            probe, toolchain, elf_path, bin_path, _, boot_path = \
                spec.split(":")
            require(probe in PROBES, f"unknown probe image {probe}")
            results = probe_mutation_test(probe, toolchain, elf_path,
                                          bin_path, boot_path, pins, kernel,
                                          layout)
            print(f"{probe} {toolchain}: mutations rejected: {len(results)}")
            checked.append(f"{probe}-{toolchain}-mutations={len(results)}")
        for qemu_path, board_path in zip(args.qemu_image, args.board_image):
            qemu, board = read(qemu_path), read(board_path)
            check_qemu_image(qemu, board)
            mutations = qemu_image_mutations(qemu, board)
            label = image_label(qemu_path)
            print(f"BE_MVP_QEMU_IMAGE[{label}]: PASS {qemu_path} "
                  f"bytes=0x{len(qemu):x} sha256={sha256(qemu)} "
                  f"text_offset=0x{QEMU_TEXT_OFFSET:x} board={board_path} "
                  f"board_sha256={sha256(board)} "
                  f"board_text_offset=0x{BOOT_TEXT_OFFSET:x} "
                  f"mutations={mutations}")
            checked.append(f"qemu-{label.replace('/', '-')}")
    except (ImageError, OSError, ValueError, KeyError, IndexError,
            struct.error) as error:
        print(f"BE_MVP_IMAGE_CHECK: FAIL {error}")
        return 1
    print(f"BE_MVP_IMAGE_CHECK: PASS {' '.join(checked)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
