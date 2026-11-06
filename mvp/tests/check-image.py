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

The MVP links none of the R5 switch, so this is an MVP-specific checker,
as B1's to B7's are. Every address and budget comes from src/mvp-layout.h.
B7's rules hold, adapted for two domain harts under static ownership; the
plan's image checker (planning/mvp-m0-plan.md, "Tests and evidence") adds
or changes these, the MVP profile:

Monitor (ELF and its flat image):

- the core (planning/mvp-m6-plan.md, D-4), laid out by the MVP-owned
  linker script (src/mvp-monitor.lds), whose seven PT_LOAD segments the
  ELF has and every one of whose ASSERT conjuncts holds, the checker's own
  (MVP_CONJUNCTS) among them: the flat image's first 0x34000 bytes hold
  the code extent [0x1_0200_0000, 0x1_0200_8000), .monitor.text; the
  data extent [0x1_0200_8000, 0x1_0201_0000), the input section, the
  constants, the data section, which holds nothing, and the diagnostic
  page; and hart 0's stack, .stack.control, NOLOAD, 0x2000 bytes at
  0x1_0201_0000; no other section, and no section outside its extent;
  the rest, the unused span, zero;
- the fourth PT_LOAD segment is the MVP pool and the hart region: NOLOAD,
  RW, exactly 0x30000 bytes at 0x1_0203_4000, with the script's four pool
  and four hart-region conjuncts;
- the MVP region (Plan revision M0-A.1): the fifth to seventh PT_LOAD
  segments, R-X, R, and RW, hold .mvp.text at 0x1_0206_4000, .mvp.rodata,
  and .mvp.data, in order, inside the region's 0x40000 bytes and never
  inside the core, with the script's four region conjuncts; the flat
  image is exactly 0xa4000 bytes, the region ending it;
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
  exactly one fence.i, in be_mvp_arch_fence_i; exactly five wfi (the
  accepted halts' three, hart 0's wait, be_mvp_arch_wait, and the domain
  park, be_mvp_arch_park); hgatp writes and hfence.gvma only in the accepted
  R3 functions; no hfence.vvma, H load or store (hlv, hlvx, hsv), mret,
  ebreak, or F, D, or V instruction; no access at all to hstateen0, hvictl,
  hvien, hviprio1, or hviprio2;
- the CSR writer table: vsstatus, vsie, vstvec, vsscratch, vsepc,
  vscause, vstval, vsatp, scounteren, and senvcfg written after the R3
  reset only by the arm helper, be_mvp_arch_arm_controls; vstimecmp also
  by the TIME helper; vscause, vstval, vsepc, and vsstatus also by the
  injection helper, be_mvp_arch_inject (planning/mvp-m1-plan.md, "Tests
  and evidence"); stimecmp only by hart 0's budget helper,
  be_mvp_arch_arm_budget, and B1's quiesce; sie by the arm and budget
  helpers; sip cleared only by the IPI's SSIP helper,
  be_mvp_arch_clear_ssip; hstatus only cleared, so VTW is never set;
- the values the helpers write, by constant tracking: the Sstc helper's
  henvcfg STCE; the arm helper's vstimecmp ~0, then hip read, then hedeleg
  0xb15d, hideleg 0x40, hcounteren 0x2, hstatus VTVM, VTW, and VTSR
  cleared (0x700000), sie SSIE set (0x2), sscratch the trusted top, and
  the eleven per-domain CSRs from its third argument's words 0-10, in
  order, with every control read back into its first argument and the set
  into its fourth; the budget helper's stimecmp from its argument, sie
  SSIE and STIE set (0x22), and sscratch; the TIME helper's vstimecmp from
  its argument; the injection helper's vscause, vstval, vsepc, and
  vsstatus from its first four arguments, in that order, each then read
  back, in that order, into its fifth argument's four words, and no other
  CSR; the SSIP helper's clear of sip.SSIP, one csrrc that reads sip as
  it was and nothing else (planning/mvp-m2-plan.md, Q14); the wait helper
  writes no CSR and reads only sip and time; the park writes and reads
  none;
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
  satp, stvec, sie SSIE only, sstatus under its mask against the saved
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
  the sealed grants (be_mvp_grants), one to four in .mvp.rodata, each
  from one domain to the other with pause (1), terminate (2), or both,
  no pair twice, and equal to the domain grants of the scenario's
  authority report and its expectation's; hart 0's management state
  (be_mvp_mgmt_state) in the MVP region's BSS; and the domain hart's
  request and wait (be_mvp_post_mgmt_request, be_mvp_wait_serve) and
  hart 0's setup (be_mvp_control_mgmt) linked. An image of any other
  scenario links none of these;
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
  shim-rule variant;
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
  which ends the file (at most 4 MiB);
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
# The flat image (Plan revision M0-A.1): the core's 0x34000 bytes
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
MONITOR_TEXT_LIMIT = 0x102008000
MONITOR_DATA_LIMIT = 0x10200F000
CONTROL_STACK = LAYOUT["CONTROL_STACK_HPA"]
CONTROL_STACK_END = CONTROL_STACK + LAYOUT["CONTROL_STACK_BYTES"]
# The core's extents (planning/mvp-m6-plan.md, D-4), and the extent each of
# its sections lies in; the rest of the core, from hart 0's stack's end,
# holds no section and is zero.
CORE_EXTENTS = {
    "code": (BASE, LAYOUT["DATA_HPA"]),
    "data": (LAYOUT["DATA_HPA"], LAYOUT["DATA_HPA"] + LAYOUT["DATA_BYTES"]),
    "stack": (CONTROL_STACK, CONTROL_STACK_END),
}
CORE_SECTIONS = {".monitor.text": "code", ".monitor.input": "data",
                 ".monitor.rodata": "data", ".monitor.data": "data",
                 ".diagnostic": "data", ".stack.control": "stack"}
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
               ("state page", "BLOCK_STATE_OFFSET", "BLOCK_STATE_BYTES"),
               ("inbound ring", "BLOCK_INBOUND_OFFSET",
                "INBOUND_RING_BYTES"),
               ("outbound ring", "BLOCK_OUTBOUND_OFFSET",
                "OUTBOUND_RING_BYTES"),
               ("input ring", "INPUT_RING_OFFSET", "INPUT_RING_BYTES"),
               ("unused tail", "BLOCK_UNUSED_OFFSET", "BLOCK_UNUSED_BYTES"))
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
         ("mvp_pool", 6), ("mvp_text", 5), ("mvp_ro", 4), ("mvp_data", 6)]
MVP_CONJUNCTS = (
    f"be_reset == 0x{BASE:x}",
    f"__be_monitor_code_start == 0x{BASE:x}",
    f"__be_monitor_code_end <= 0x{MONITOR_TEXT_LIMIT:x}",
    f"__be_monitor_data_start == 0x{MONITOR_TEXT_LIMIT:x}",
    f"__be_bss_end <= 0x{MONITOR_DATA_LIMIT:x}",
    f"__be_monitor_data_end == 0x{CONTROL_STACK:x}",
    f"__be_control_stack_start == 0x{CONTROL_STACK:x}",
    f"__be_control_stack_end == 0x{CONTROL_STACK_END:x}",
    "be_mvp_trap_vector >= __be_monitor_code_start",
    "be_mvp_trap_vector < __be_monitor_code_end",
    f"__be_mvp_pool_start == 0x{POOL:x}",
    f"__be_mvp_pool_end == 0x{POOL + POOL_BYTES:x}",
    "(__be_mvp_pool_start & 0x3fff) == 0",
    "__be_control_stack_end <= __be_mvp_pool_start",
    f"__be_mvp_hart_region_start == 0x{HART_REGION:x}",
    f"__be_mvp_hart_region_end == 0x{HART_REGION + HART_REGION_BYTES:x}",
    "(__be_mvp_hart_region_start & 0x3fff) == 0",
    "__be_mvp_pool_end <= __be_mvp_hart_region_start",
    f"__be_mvp_region_start == 0x{REGION:x}",
    f"__be_mvp_region_end <= 0x{REGION + REGION_BYTES:x}",
    "(__be_mvp_region_start & 0x3fff) == 0",
    "__be_mvp_hart_region_end <= __be_mvp_region_start",
)
POOL_PHDR = ("mvp_pool", 6)
# The MVP layer's C objects, which only the MVP region holds; the MVP's
# assembly (mvp-trap.o, mvp-hartentry.o, and the probe images'
# mvp-probe-arch.o) stays with the core's code.
MVP_C_OBJECTS = ("mvp-runtime.o", "mvp-hartmain.o", "mvp-sbi.o",
                 "mvp-hart.o", "mvp-ring.o", "mvp-gstage.o", "mvp-payload.o",
                 "mvp-probe.o", "mvp-sha256.o", "mvp-core.o",
                 "mvp-executor.o", "mvp-input.o", "mvp-log.o")
# The region's sections, and its linked symbols beyond the ASSERTs'.
REGION_SECTIONS = (".mvp.text", ".mvp.rodata", ".mvp.data")
REGION_SYMBOLS = ("__be_mvp_region_start", "__be_mvp_region_end",
                  "__be_mvp_text_start", "__be_mvp_text_end",
                  "__be_mvp_bss_start", "__be_mvp_bss_end")

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
MVP_BUDGET = "be_mvp_arch_arm_budget"
MVP_WAIT = "be_mvp_arch_wait"
MVP_SSIP = "be_mvp_arch_clear_ssip"
MVP_TIME = "be_mvp_arch_read_time"
MVP_PARK = "be_mvp_arch_park"
MVP_FENCE_I = "be_mvp_arch_fence_i"
MVP_VECTOR = "be_mvp_trap_vector"
MVP_RESUME = "be_mvp_arch_resume"
MVP_ENTRY = "be_mvp_hart_entry"
MVP_MAIN = "be_mvp_runtime_main"
MVP_HART_MAIN = "be_mvp_hart_main"
MVP_DISPATCH = "be_mvp_dispatch"
MVP_TERMINAL = "be_mvp_runtime_terminal"
MVP_HART_TERMINAL = "be_mvp_hart_terminal"
MVP_FW_CALL = "be_mvp_fw_call"
MVP_INJECT = "be_mvp_arch_inject"
# The executor's install and injection (planning/mvp-m6-plan.md, D-5).
EXEC_INSTALL = "be_mvp_exec_install_hgatp"
EXEC_INJECT = "be_mvp_exec_inject"
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
    "be_reset", B1_QUIESCE, MVP_MAIN, MVP_HART_MAIN, MVP_DISPATCH,
    MVP_VECTOR, MVP_RESUME, MVP_ENTRY, MVP_STCE, MVP_ARM, MVP_TIMER,
    MVP_BUDGET, MVP_WAIT, MVP_SSIP, MVP_TIME, MVP_PARK, MVP_FENCE_I,
    MVP_TERMINAL, MVP_HART_TERMINAL, MVP_FW_CALL, MVP_INJECT, EXEC_INSTALL,
    MVP_LAYOUT_SYMBOL, MVP_BINDINGS_SYMBOL, MVP_DESCS_SYMBOL,
    MVP_HGATPS_SYMBOL,
    "__be_mvp_pool_start", "__be_mvp_pool_end", "__be_mvp_hart_region_start",
    "__be_mvp_hart_region_end", R3_RESET, R3_INSTALL, R3_ENTER, R3_SBI,
    R3_HALT,
)

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
            MVP_PARK: 1},
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
SHF_WRITE, SHF_ALLOC, SHF_EXECINSTR = 1, 2, 4
# The accepted R5 checker's section table, without the fixture sections
# (planning/mvp-m6-plan.md, D-4), at the K3 addresses: (address or None,
# size or None, required flags, forbidden flags).
EXPECTED_SECTIONS = {
    ".monitor.text": (BASE, None, "AX", "W"),
    ".monitor.input": (MONITOR_TEXT_LIMIT, None, "A", "WX"),
    ".monitor.rodata": (None, None, "A", "WX"),
    ".monitor.data": (None, None, "WA", "X"),
    ".diagnostic": (MONITOR_DATA_LIMIT, 0x1000, "WA", "X"),
    ".stack.control": (CONTROL_STACK, LAYOUT["CONTROL_STACK_BYTES"], "WA",
                       "X"),
    # lld gives an output section without input sections the previous
    # section's flags masked to A and W; the PT_LOAD is RW in both images.
    ".gstage.root.mvp": (POOL, POOL_BYTES, "A", "X"),
    ".hart.mvp": (HART_REGION, HART_REGION_BYTES, "A", "X"),
    # The MVP region (Plan revision M0-A.1): code, constants, then data and
    # BSS, from its fixed start.
    ".mvp.text": (REGION, None, "AX", "W"),
    ".mvp.rodata": (None, None, "A", "WX"),
    ".mvp.data": (None, None, "WA", "X"),
}
MAP_SECTIONS = (".monitor.input", ".stack.control", ".gstage.root.mvp",
                ".hart.mvp") + REGION_SECTIONS
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
# anchor's three runtime negatives built here (planning/mvp-m2-plan.md,
# Q10), each its monitor: the page builder's two defects, which the page
# check refuses, and the perturbed expected measurement.
ANCHOR_VARIANTS = ("secret-shared", "response-writable", "wrong-measurement",
                   "no-grant-check")
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
VARIANTS = ("payload",) + DTB_VARIANTS + MONITOR_VARIANTS + ("shim-rule",) + \
    TE_POC_VARIANTS + ANCHOR_VARIANTS + CONSOLE_VARIANTS + (FLIP_VARIANT,)
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
    """Evaluate one ASSERT conjunct: difference CMP difference."""
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


def check_padding(flat, base, start, end):
    for pc, size, word in instructions(flat, start, end, base):
        require((size == 4 and word == NOP) or
                (size == 2 and word in (C_NOP, 0)),
                f"instruction 0x{word:x} at 0x{pc:x} is outside every "
                f"function")


# ----------------------------------------------------- value tracking
def track(decoded):
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
    stop, so a join never carries a value it might not hold.
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
            regs = {0: ("const", 0)}
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


def check_helpers(elf, flat, base, symbols):
    """The values the MVP's helpers write, and what they read back."""
    for name, expected in HELPER_WRITES.items():
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
        slots = {offset: value[1] for _, base_value, offset, value in stores
                 if base_value == ARG_A0 and value and value[0] == "csr" and
                 value[2] == MASK64}
        if name in HELPER_READS:
            require([csr for _, csr in reads] == HELPER_READS[name] and
                    not stores,
                    f"{name} reads {reads} or stores {stores}, expected "
                    f"{HELPER_READS[name]} only")
        if name == MVP_INJECT:
            inject_slots = {offset: value[1] for _, base_value, offset, value
                            in stores if base_value == ARG_A4 and value and
                            value[0] == "csr" and value[2] == MASK64}
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


def check_instructions(elf, flat, base, extents, symbols, profile="mvp",
                       inject_sites=0):
    """The ecall/sret/fence/CSR rules over the monitor's code: the accepted
    code extent and the MVP region's text, each [start, end); the injection
    helper with inject_sites call sites (1 in an image that accepts
    denials, else 0)."""
    install_extra, hgatp_extra, _ = PROFILES[profile]
    csr_writers = dict(CSR_WRITERS)
    csr_writers["hgatp"] = CSR_WRITERS["hgatp"] | set(hgatp_extra)
    install_callers = INSTALL_CALLERS + list(install_extra)
    sites = {kind: {} for kind in INSTRUCTION_SITES}
    writers = {}
    decoded_all = []
    functions = []
    for code_start, code_end in extents:
        extent = function_map(elf, code_start, code_end)
        require(extent, f"no function symbols in 0x{code_start:x}-"
                f"0x{code_end:x}")
        functions += extent
        decoded_all += scan_functions(elf, flat, base, code_start, code_end,
                                      extent, sites, writers, csr_writers)
    check_sites(sites, writers, csr_writers)
    found = check_references(functions, decoded_all, symbols, install_extra,
                             install_callers, inject_sites)
    check_domain_reach(elf, functions, found, symbols, profile)
    check_canary(elf, flat, base, found, symbols)
    by_name = {owner: decoded for owner, decoded in decoded_all}
    check_trap_entry(by_name[MVP_VECTOR], symbols)
    resume = [(value, size) for value, size, names in functions
              if MVP_RESUME in names][0]
    check_resume(by_name[MVP_RESUME], symbols, resume[0],
                 resume[0] + resume[1])
    check_hart_entry(by_name[MVP_ENTRY], symbols)
    check_helpers(elf, flat, base, symbols)
    if hgatp_extra:
        require([word for _, _, word in by_name[PROBE_SWITCH]] ==
                list(PROBE_SWITCH_WORDS),
                f"{PROBE_SWITCH} is not the raw write, its readback, and "
                f"its return")
    total = sum(len(decoded) for _, decoded in decoded_all)
    return len(functions), total


def scan_functions(elf, flat, base, code_start, code_end, functions, sites,
                   writers, csr_writers):
    """One code extent's instruction words, sites, and CSR writers."""
    cursor = code_start
    decoded_all = []
    for value, size, names in functions:
        check_padding(flat, base, cursor, value)
        owner = names[0] if len(names) == 1 else "/".join(names)
        decoded = instructions(flat, value, value + size, base)
        decoded_all.append((owner, decoded))
        for pc, width, word in decoded:
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
    check_padding(flat, base, cursor, code_end)
    return decoded_all


def check_sites(sites, writers, csr_writers):
    """The instruction-site table and the CSR writer table, over all
    code."""
    for kind, expected in INSTRUCTION_SITES.items():
        require(sites[kind] == expected,
                f"{kind} sites {sorted(sites[kind].items())} != "
                f"{sorted(expected.items())}")
    for name, expected in csr_writers.items():
        actual = writers.get(name, set())
        require(actual == expected,
                f"{name} written by {sorted(actual)}, expected "
                f"{sorted(expected)}")


def check_references(functions, decoded_all, symbols, install_extra,
                     install_callers, inject_sites=0):
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
                    owner != MVP_FW_CALL:
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


def check_domain_reach(elf, functions, found, symbols, profile="mvp"):
    """The code a domain hart runs (planning/mvp-m2-plan.md, "The
    measurement"): from the hart entry and the vector, every function a
    call or a formed address in their instruction words reaches,
    transitively. None of them names a byte of hart 0's own objects
    (HART0_ONLY); hart 0's entry, the management decision, hart 0's
    management setup, and, since M7, the firmware console read and hart
    0's routing of console input are not among them (HART0_CODE); the
    domain hart's request and wait, where linked, are, and in every image
    but the probes the service of a granted console read
    (planning/mvp-m7-plan.md, D-1). Returns the names of the functions
    reached."""
    extents = sorted((value, value + size,
                      names[0] if len(names) == 1 else "/".join(names))
                     for value, size, names in functions)
    starts = [start for start, _, _ in extents]

    def owner_at(address):
        index = bisect.bisect_right(starts, address) - 1
        if index >= 0 and address < extents[index][1]:
            return extents[index][2]
        return None

    reached = {owner_at(symbols[name]) for name in DOMAIN_ROOTS}
    require(None not in reached, "a domain-hart entry is not a function")
    work = sorted(reached)
    while work:
        for _, target, _ in found[work.pop()]:
            owner = owner_at(target)
            if owner is not None and owner not in reached:
                reached.add(owner)
                work.append(owner)
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


def check_structure(elf):
    """The accepted R5 checker's structure rules, moved to the K3 base."""
    require(3 not in elf.program_types, "image requests an interpreter")
    require(2 not in elf.program_types, "image carries a dynamic segment")
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
    # The core's data section holds nothing since the MVP layer's data
    # moved to the MVP region (Plan revision M0-A.1): the ported accepted
    # objects have none. GNU ld drops ALLOC from such an empty output
    # section and lld keeps it as NOBITS, so only its emptiness and X are
    # checked.
    require(elf.sections.get(".monitor.data") is not None and
            elf.sections[".monitor.data"][5] == 0,
            "the core's data section .monitor.data holds bytes")
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
        for flag in required if name != ".monitor.data" else "":
            require(have[flag], f"{name} lost flag {flag}")
        for flag in forbidden:
            require(not have[flag], f"{name} gained flag {flag}")
    require(elf.sections[".gstage.root.mvp"][1] == 8,  # SHT_NOBITS
            "the MVP pool is not NOLOAD")
    require(elf.sections[".hart.mvp"][1] == 8,  # SHT_NOBITS
            "the hart region is not NOLOAD")
    require(elf.sections[".monitor.text"][5] <= 0x8000,
            "monitor text outgrew its reserved window")
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


def check_block_arithmetic(decoded, symbols, owner):
    """A block's stack top, tested or formed by the hart region's shifts.

    The hart region's start, its size's shift, the block's shift (as the
    left shift that keeps a block offset), and the stack top's offset in
    the block, each as src/mvp-layout.h gives it.
    """
    region = symbols["__be_mvp_hart_region_start"]
    require(region == HART_REGION,
            f"the hart region starts at 0x{region:x}, not 0x{HART_REGION:x}")
    named = [target for _, target, link in references(decoded, owner)
             if link is None]
    shifts, upper = set(), set()
    for _, size, word in decoded:
        if size == 4 and word & 0x707F in (0x1013, 0x5013) and \
                word >> 26 == 0:
            shifts.add(("slli" if word & 0x7000 == 0x1000 else "srli",
                        (word >> 20) & 0x3F))
        elif size == 4 and word & 0x7F == 0x37:
            upper.add(word & 0xFFFFF000)
    require(named.count(region) == 1,
            f"{owner} does not test its block against the hart region")
    require(("srli", HART_REGION_BYTES.bit_length() - 1) in shifts and
            ("slli", 64 - (BLOCK_BYTES.bit_length() - 1)) in shifts,
            f"{owner} does not bound its block by the region's "
            f"0x{HART_REGION_BYTES:x} bytes and the block's "
            f"0x{BLOCK_BYTES:x}")
    require(LAYOUT["BLOCK_STACK_TOP_OFFSET"] in upper,
            f"{owner} does not take the block's stack top at "
            f"+0x{LAYOUT['BLOCK_STACK_TOP_OFFSET']:x}")


def check_hart_entry(decoded, symbols):
    """A started hart: sp at its block's stack top before any memory
    access, then its C, or the park."""
    require(all(size == 4 for _, size, _ in decoded),
            "hart entry holds a compressed instruction")
    words = [word for _, _, word in decoded]
    require(not any(word & 0x7F in (0x03, 0x23, 0x2F) or
                    system_kind(word) is not None for word in words),
            "hart entry accesses memory or a CSR")
    stack = [index for index, word in enumerate(words)
             if word & 0xFE00707F == 0x33 and (word >> 7) & 0x1F == 2]
    require(len(stack) == 1 and (words[stack[0]] >> 15) & 0x1F == 11 and
            words[stack[0] - 1] & 0x7F == 0x37 and
            (words[stack[0] - 1] >> 7) & 0x1F ==
            (words[stack[0]] >> 20) & 0x1F and
            words[stack[0] - 1] & 0xFFFFF000 ==
            LAYOUT["BLOCK_STACK_TOP_OFFSET"],
            "hart entry does not set sp to a1 plus the block's stack top")
    targets = [(target, link) for _, target, link in references(decoded)
               if link is not None]
    require(targets == [(symbols[MVP_HART_MAIN], 1), (symbols[MVP_PARK], 0)],
            "hart entry does not call be_mvp_hart_main and else park")
    check_block_arithmetic(decoded, symbols, MVP_ENTRY)


def resume_checks(symbols):
    """Every check the resume tail must make, and nothing else."""
    return {
        ("eq", "sscratch", MASK64, "arg:a0"),
        ("eq", "satp", MASK64, 0),
        ("eq", "stvec", MASK64, symbols[MVP_VECTOR]),
        ("eq", "sie", MASK64, SIE_SSIE),
        ("eq", "sstatus", 0xDE722, f"mem:a0+{EXIT_WORDS[0][1]}&0x100"),
        ("eq", "hstatus", 0x73F380 & ~HSTATUS_SPVP, 0x80),
        ("eq", "hedeleg", MASK64, "arg:a2"),
        ("eq", "hideleg", MASK64, 0x40),
        ("eq", "hie", MASK64 & ~0x40, 0),
        ("eq", "hvip", 0x444, 0),
        ("eq", "hcounteren", MASK64, 0x2),
        ("eq", "htimedelta", MASK64, 0),
        ("eq", "henvcfg", MASK64, 1 << 63),
        ("eq", "hgeie", MASK64, 0),
        ("eq", "hgatp", MASK64, "arg:a1"),
    }


def check_resume(decoded, symbols, start, end):
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
    writes, reads, checks, _ = track(decoded)
    require([(csr, operation, value) for _, csr, operation, value in writes]
            == [("sstatus", "c", ("const", 0x100)),
                ("sstatus", "s", ("mem", "a0", EXIT_WORDS[0][1],
                                  HSTATUS_SPVP)),
                ("sepc", "w", ("mem", "a0", FRAME_SEPC, MASK64))],
            "resume tail does not clear SPP, set it from the saved SPVP, "
            "and then write only sepc from the frame")
    found = {check[1:] for check in checks}
    wanted = resume_checks(symbols)
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
            require(paddr == POOL and
                    memsz == POOL_BYTES + HART_REGION_BYTES and filesz == 0,
                    f"MVP pool segment 0x{paddr:x}+0x{memsz:x} (file "
                    f"0x{filesz:x}) is not NOLOAD "
                    f"0x{POOL_BYTES + HART_REGION_BYTES:x} bytes at "
                    f"0x{POOL:x}")
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
    """The core (planning/mvp-m6-plan.md, D-4): each section in its first
    0x34000 bytes is one of CORE_SECTIONS, inside its extent, so none lies
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
    """The MVP region holds the MVP layer's C objects and nothing else, and
    the MVP's assembly stays in the core's code extent (Plan revision
    M0-A.1): by symbol, the assembly's functions and the C entry points; by
    the link map, every input section of the MVP C objects, and the input
    section holds the configuration's alone (planning/mvp-m6-plan.md,
    D-1)."""
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
        require(value is not None and code[0] <= value < code[1],
                f"{name} at 0x{value or 0:x} is outside the core's code "
                f"extent 0x{code[0]:x}-0x{code[1]:x}")
    for name in MVP_C_ENTRIES + ((PROBE_HGATP,) if probe == "probe-platform"
                                 else ()):
        value = symbols.get(name)
        require(value is not None and text[0] <= value < text[1],
                f"{name} at 0x{value or 0:x} is outside the MVP region's "
                f"text 0x{text[0]:x}-0x{text[1]:x}")
    require(map_text is not None, "no link map beside the monitor ELF")
    seen = set()
    for address, size, name, section in map_entries(map_text):
        if name == "mvp-config.o" or config[0] <= address < config[1]:
            require(name == "mvp-config.o" and config[0] <= address and
                    address + size <= config[1],
                    f"{name}'s {section} at 0x{address:x}: the input "
                    f"section holds the configuration's constants alone")
            continue
        inside = region[0] <= address and address + size <= region[1]
        if name not in MVP_C_OBJECTS:
            require(not region[0] <= address < region[1],
                    f"{name}'s {section} at 0x{address:x} lies in the MVP "
                    f"region")
            continue
        where = "in the core's code extent" \
            if code[0] <= address < code[1] else "in the core's data" \
            if data[0] <= address < data[1] else "outside the MVP region"
        require(inside, f"{name}'s {section} at 0x{address:x} lies {where}")
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
    """The hart region's blocks at their offsets, the rings powers of two.

    Each block is its areas in order, from its start to its end, and the
    stack top the vector, the resume tail, and the hart entry test is the
    stack's end and the saved page's start.
    """
    region, size = constants["HART_REGION_HPA"], constants["HART_REGION_BYTES"]
    block = constants["BLOCK_BYTES"]
    require(region == HART_REGION and size == 2 * block and
            size & (size - 1) == 0 and region % 0x4000 == 0,
            f"the hart region 0x{region:x}+0x{size:x} is not two "
            f"power-of-two blocks at 0x{HART_REGION:x}")
    for guest, key in enumerate(("G0_BLOCK_HPA", "G1_BLOCK_HPA")):
        require(constants[key] == region + guest * block,
                f"G{guest}'s block 0x{constants[key]:x} is not at "
                f"+0x{guest * block:x} in the hart region")
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


def check_mgmt_record(elf, flat, base, scenario):
    """An image of a scenario with the management extension
    (planning/mvp-m2-plan.md): the linked grants, by their own rules and
    the scenario's report's and expectation's; where they and hart 0's
    management state lie; and the extension's functions linked. An image
    of any other scenario links none of them. Returns the grants."""
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
    require(size == count * 8 * len(GRANT_WORDS) and
            1 <= count <= MGMT_GRANTS_MAX and
            inside_section(elf, ".mvp.rodata", address, size),
            f"{MVP_GRANTS_SYMBOL} at 0x{address:x} is not 1 to "
            f"{MGMT_GRANTS_MAX} grants in .mvp.rodata")
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
    state = symbols[MVP_MGMT_STATE_SYMBOL]
    state_size = symbol_size(elf, MVP_MGMT_STATE_SYMBOL)
    require(state_size and symbols["__be_mvp_bss_start"] <= state and
            state + state_size <= symbols["__be_mvp_bss_end"],
            f"{MVP_MGMT_STATE_SYMBOL} at 0x{state:x} is not in the MVP "
            f"region's BSS")
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
                     if not probe or name != MVP_LAYOUT_SYMBOL) + \
        ((PROBE_STUB,) if probe else ())
    for name in required + hgatp_extra + REGION_SYMBOLS:
        require(symbols.get(name) is not None, f"symbol {name} is missing")
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
    functions, words = check_instructions(
        elf, flat, base, ((code_start, code_end),
                          (symbols["__be_mvp_text_start"],
                           symbols["__be_mvp_text_end"])), symbols, profile,
        1 if scenario.accepts_denial(variant) else 0)
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
# hart_start and two hart_stop (planning/mvp-m0-plan.md, Image checker).
SBI_DBCN, SBI_SRST, SBI_HSM = 0x4442434E, 0x53525354, 0x48534D
SHIM_CALLS = {
    False: sorted([(SBI_DBCN, 0), (SBI_SRST, 0), (SBI_HSM, 0)]),
    True: sorted([(SBI_DBCN, 0), (SBI_SRST, 0), (SBI_HSM, 0), (SBI_HSM, 0),
                  (SBI_HSM, 1), (SBI_HSM, 1)]),
}
# Every SYSTEM instruction the shim holds: B3's SIE clear, fence.i, and
# park, and the ecalls above.
SHIM_SYSTEM = {"csr": 1, "fence.i": 1, "wfi": 1}
SHIM_SIE_CLEAR = 0x10017073
# The start rule's report line, beside B3's two.
SHIM_TEMPLATE = b"BE_MVP_SHIM: boot_hart=0x" + b"?" * 16 + \
    b" starting hart 0\n"


def check_shim(data, rule):
    """B3's instructions plus the start rule's ecall; hart_stop only in
    the shim-rule variant."""
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
            require(kind != "csr" or word == SHIM_SIE_CLEAR,
                    f"the shim accesses a CSR other than sstatus.SIE at "
                    f"+0x{pc:x}")
    require(kinds == SHIM_SYSTEM,
            f"the shim's SYSTEM instructions {kinds} != {SHIM_SYSTEM}")
    calls = sorted((call[1:] for call in ecall_sites(decoded)),
                   key=lambda call: (call[0] is None, call[0] or 0,
                                     call[1] is None, call[1] or 0))
    require(calls == SHIM_CALLS[rule],
            f"the shim calls {[(hex(e or 0), f) for e, f in calls]}, "
            f"expected {[(hex(e), f) for e, f in SHIM_CALLS[rule]]}")


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
               pages=None):
    """B3's header and descriptor, the ranges, and the placed payload, with
    the scenario's DTBs."""
    b3 = load_b3()
    files, kernel_pins = pins
    findings = []
    header = b3.check_header(data, text_offset, findings)
    image_size = header["image_size"] if header else len(data)
    check_ranges(image_size, constants, channel, pages)
    require(not findings, "; ".join(findings))
    check_descriptor(b3, data, findings)
    for template in b3.TEMPLATES + (SHIM_TEMPLATE,):
        if data[:b3.STUB_PAGE].count(template) != 1:
            findings.append("a shim report-line template is missing")
    require(not findings, "; ".join(findings))
    check_shim(data, variant == "shim-rule")
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


def check_console_grants(elf_data, flat, reference_flat, scenario):
    """A console variant's monitor: its flat image the reference's but for
    its expected launch registers (M9) and bytes inside be_mvp_proposal,
    the MVP core profile's domain requests, each a grant's word going from
    0 to 1, one per shell guest (mvp-config.c's
    BE_MVP_CORE_DOMAIN<d>_CONSOLE)."""
    elf = Elf(elf_data)
    entries = elf.symbol_entries.get("be_mvp_proposal", [])
    require(len(entries) == 1, "be_mvp_proposal is not one symbol")
    start = elf.symbols["be_mvp_proposal"] - BASE
    size = struct.unpack_from("<Q", elf.data, entries[0] + 16)[0]
    launch, launch_bytes = launch_span(elf)
    require(len(flat) == len(reference_flat),
            "the console variant's flat image is not the reference's size")
    changed = [index for index in range(len(flat))
               if flat[index] != reference_flat[index] and
               not launch <= index < launch + launch_bytes]
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
                      channel=report["channel"], pages=report["pages"])
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
    # A console variant is its own scenario's, SCENARIO-shell.
    require(name == f"{scenario.name}-shell" if name in CONSOLE_VARIANTS
            else (name in TE_POC_VARIANTS) == (scenario.name == "te-poc") and
            (name in ANCHOR_VARIANTS + (FLIP_VARIANT,)) ==
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
        # launch registers, which its DTBs change.
        elf = variant_monitor(name, monitor, flat, reference, layout,
                              scenario, boot, data)
        stray = outside(flat, reference["flat"], [launch_span(elf)])
        require(stray is None,
                f"variant {name}'s monitor differs from the reference's "
                f"outside its launch registers, at 0x{BASE + stray:x}"
                if stray is not None else "")
        allowed = [(MONITOR_OFFSET, SPAN)] + [
            (boot[f"dtb{guest}_offset"], DTB_BYTES)
            for guest in DTB_VARIANT_GUESTS[name]]
    elif name == "shim-rule":
        allowed = [(0, MONITOR_OFFSET)]
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
        # linked word: its monitor must pass the MVP profile itself.
        variant_monitor(name, monitor, flat, reference, layout, scenario,
                        boot, data)
        allowed = [(MONITOR_OFFSET, SPAN)]
    stray = outside(data, reference["boot"], allowed)
    require(stray is None,
            f"variant {name} differs from the reference at 0x{stray:x}"
            if stray is not None else "")
    require(data != reference["boot"], f"variant {name} is the reference")
    return boot


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


# The SBI argument a6 = 0 (HSM hart_start) and = 1 (hart_stop).
LI_A6_0, LI_A6_1 = 0x00000813, 0x00100813
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
    arm_ssie, ssie_word = preceding_word(
        elf, flat, MVP_ARM, BASE, lambda value: value == CSRS_SIE_T0)
    budget_stie, stie_word = matching_word(
        elf, flat, MVP_BUDGET, BASE, add_immediate(SIE_SSIE | SIE_STIE))
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
    spv_test = matching_word(elf, flat, MVP_VECTOR, BASE,
                             lambda value: value & 0x707F == 0x7013 and
                             signed(value >> 20, 12) == HSTATUS_SPV)[0]
    arm_senvcfg, senvcfg_word = matching_word(
        elf, flat, MVP_ARM, BASE,
        lambda value: load_fields(value) == (5, 12, 80))
    top = lui_with(LAYOUT["BLOCK_STACK_TOP_OFFSET"])
    entry_top, entry_word = matching_word(elf, flat, MVP_ENTRY, BASE, top)
    vector_top, vector_word = matching_word(elf, flat, MVP_VECTOR, BASE, top)
    descs = symbols[MVP_DESCS_SYMBOL]
    hgatps = symbols[MVP_HGATPS_SYMBOL]
    bindings = symbols[MVP_BINDINGS_SYMBOL]
    moved_top = LAYOUT["BLOCK_STACK_TOP_OFFSET"] + 0x1000
    monitor = [
        ("hedeleg immediate", arm_hedeleg,
         word(with_immediate(arm_word, 0x15F)), "hedeleg written as"),
        ("VTW set by the arm immediate", arm_hstatus,
         word(hstatus_word & ~0x1000), "hstatus written as"),
        ("SSIE missing from the arm immediate", arm_ssie,
         word(with_immediate(ssie_word, 0)), "sie written as"),
        ("STIE missing from the budget immediate", budget_stie,
         word(with_immediate(stie_word, SIE_SSIE)), "sie written as"),
        ("resume hedeleg check", resume_hedeleg, word(MV_T4_A1),
         "resume checks differ"),
        ("resume SPP not from SPVP", resume_spvp,
         word(with_immediate(spvp_word, 0x80)), "does not clear SPP"),
        ("resume tests all of hvip", resume_hvip,
         word(with_immediate(hvip_word, -1)), "resume checks differ"),
        ("missing fence.i", symbols[MVP_FENCE_I], word(NOP),
         "fence.i sites"),
        ("a sixth wfi", nth_word(elf, flat, MVP_DISPATCH, BASE),
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
        ("vector skips s2", matching_word(
            elf, flat, MVP_VECTOR, BASE,
            lambda value: store_fields(value) == (18, 5, 136))[0],
         word(NOP), "does not save x18"),
        ("vector skips htinst", matching_word(
            elf, flat, MVP_VECTOR, BASE,
            lambda value: store_fields(value) == (6, 5, 328))[0],
         word(NOP), "does not store htinst"),
        ("vector skips SPV", spv_test, word(NOP),
         "does not fail closed on hstatus.SPV"),
        ("a block offset moved in the vector", vector_top,
         word(vector_word & 0xFFF | moved_top), "block's stack top"),
        ("a block offset moved in the hart entry", entry_top,
         word(entry_word & 0xFFF | moved_top), "stack top"),
        ("hart entry reads its block first", entry_top,
         word(0x0005B283), "accesses memory"),
        ("resume skips s3", matching_word(
            elf, flat, MVP_RESUME, BASE,
            lambda value: load_fields(value) == (19, 31, 144))[0],
         word(NOP), "does not restore x19"),
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
             code[0] <= address < code[1], "mvp-runtime.o"),
         "in the core's code extent"),
        ("MVP C constants in the core's data",
         lambda text: map_rename(
             text, lambda address, _, name, __: name == "manifest.o" and
             data[0] <= address < data[1], "mvp-sbi.o"),
         "in the core's data"),
        ("another object's constants in the input section",
         lambda text: map_rename(
             text, lambda _, __, name, ___: name == "mvp-config.o", "r3.o"),
         "holds the configuration's constants alone"),
        ("an accepted object's code in the MVP region",
         lambda text: map_rename(
             text, lambda _, __, name, ___: name == "mvp-ring.o", "r3.o"),
         "lies in the MVP region"),
    ]
    elfs = [
        ("an MVP section inside the core",
         elf.section_headers[".mvp.rodata"] + 16,
         quad(BASE + CORE_SPAN - 0x4000), "inside the core"),
        ("a section in the core's unused span",
         elf.section_headers[".monitor.rodata"] + 16,
         quad(CONTROL_STACK_END), "leaves the core's data extent"),
        ("the configuration outside the input section",
         *symbol_value(elf, "be_mvp_proposal", symbols["__be_input_end"]),
         "be_mvp_proposal is not in the core's input section"),
        ("the MVP region's data past its end",
         elf.section_headers[".mvp.data"] + 32,
         quad(REGION + REGION_BYTES - mvp_data[3] + 0x10),
         "leaves the MVP region"),
        ("the hart entry in the MVP region",
         *symbol_value(elf, MVP_ENTRY, symbols["__be_mvp_text_start"]),
         "be_mvp_hart_entry at"),
        ("the dispatch in the core's code extent",
         *symbol_value(elf, MVP_DISPATCH, code[0] + 0x40),
         "be_mvp_dispatch at"),
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
    start_rule = shim_ecall(boot_img, SBI_HSM)
    start_fid = start_rule - 4 * next(
        back for back in range(1, 8)
        if struct.unpack_from("<I", boot_img, start_rule - 4 * back)[0] ==
        LI_A6_0)
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
        ("an HSM hart_stop in the board shim", start_fid,
         struct.pack("<I", LI_A6_1), "the shim calls"),
        ("the start rule's ecall removed", start_rule,
         struct.pack("<I", NOP), "the shim calls"),
        ("a start-rule template missing", boot_img.index(SHIM_TEMPLATE),
         b"X", "template is missing"),
        ("the descriptor's length the core's", 0x50,
         struct.pack("<Q", CORE_SPAN), "descriptor length"),
    ]
    layouts = [
        ("a block offset moved in the layout",
         {"BLOCK_INBOUND_OFFSET": LAYOUT["BLOCK_INBOUND_OFFSET"] + 0x1000},
         "is not at its offset"),
        ("a ring size that is not a power of two",
         {"OUTBOUND_RING_BYTES": 0x6000}, "is not a power of two"),
        ("a block outside its place in the region",
         {"G1_BLOCK_HPA": LAYOUT["G1_BLOCK_HPA"] + 0x1000},
         "in the hart region"),
        ("an MVP region over 256 KiB",
         {"REGION_BYTES": REGION_BYTES + 0x4000}, "more than 0x40000"),
        ("the MVP region not after the hart region",
         {"REGION_HPA": REGION + 0x4000}, "does not follow the hart region"),
        ("a flat image the MVP region does not end",
         {"IMAGE_BYTES": SPAN + 0x1000}, "does not end the flat image"),
        ("the staged image on the MVP region",
         {"STAGING_HPA": REGION + 0x8000}, "overlaps the MVP region"),
    ]
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
        elfs.append(
            ("the management state in the MVP region's constants",
             *symbol_value(elf, MVP_MGMT_STATE_SYMBOL,
                           elf.sections[".mvp.rodata"][3]),
             f"{MVP_MGMT_STATE_SYMBOL} at"))
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
        ("an instruction forms the canary's address", dispatch_slot,
         pool_reference(dispatch_slot, canary, 15),
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
         "the block's input ring at"),
        ("an input ring size that is not a power of two",
         {"INPUT_RING_BYTES": 0x1800},
         "INPUT_RING_BYTES 0x1800 is not a power of two"),
    ]
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
                          f"{PROBE_HGATP} at"))
    else:
        mutations.append(("the raw switch fenced", "monitor",
                          symbols[PROBE_SWITCH] + 4,
                          struct.pack("<I", 0x62000073), "hfence.gvma sites"))
        mutations.append(("the raw switch in the MVP region", "elf",
                          *symbol_value(elf, PROBE_SWITCH,
                                        symbols["__be_mvp_text_start"]),
                          f"{PROBE_SWITCH} at"))
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
    args = parser.parse_args(argv[1:])
    if not (args.image or args.probe or args.variant or args.mutation_test
            or args.variant_dtbs or args.mutation_probe or args.qemu_image):
        parser.error("nothing to check")
    if args.variant and not args.reference:
        parser.error("--variant needs --reference")
    if len(args.qemu_image) != len(args.board_image):
        parser.error("each --qemu-image needs its --board-image")
    checked = []
    try:
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
        for spec in args.variant:
            name, *paths = spec.split(":")
            require(len(paths) in (2, 4), f"malformed variant {spec}")
            monitor = None
            if len(paths) == 4:
                monitor = (read(paths[0]), read(paths[1]),
                           read_map(paths[0]))
            boot_elf, boot_path = paths[-2:]
            data = read(boot_path)
            check_variant(name, read(boot_elf), data, reference, pins,
                          kernel, boot_path, monitor, layout, scenario)
            print(f"variant {name}: boot_sha256={sha256(data)}")
            checked.append(f"variant-{name}")
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
