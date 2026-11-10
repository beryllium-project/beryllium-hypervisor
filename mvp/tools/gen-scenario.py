#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Generate the MVP build header and expectation files from a scenario.

  gen-scenario.py --scenario JSON --layout H --dts-tool PY [--policy-tool PY]
                  --guest DIR --out DIR [--negative NAME]
  gen-scenario.py --scenario JSON --layout H --dts-tool PY [--policy-tool PY]
                  --guest DIR --self-test

beryllium-cheri: either form also takes --monitor riscv|cheri and
--guest-flavour linux|cheri-linux (planning/cheri-platform.md; the
defaults are riscv and linux): the monitor variant's armed henvcfg in
each BE_MVP:09 line, and the guest flavour's kernel release in the domain
lines (FLAVOUR_LINES). scenario.json is read, and its SHA-256 taken, as
it is. For the CHERI enforcement plan (planning/cheri-enforcement-plan.md,
CE-2), the CHERI Linux guest's images also require its root capability's
line and its capability-write PTE line (FLAVOUR_ADDED), and the
CHERI-aware monitor's te-poc has the variant channel-cw (CHANNEL_CW). For
its CE-3, each CHERI Linux guest's domain with an M1 role also requires
its init's lines of its own CHERI faults (CHERI_TEST_LINES), every CHERI
Linux guest's lines reject the guest kernel's CHERI exception report, and
that guest's te-poc has the variant cheri-fault-hs (CHERI_FAULT_HS). For
its CE-4, that te-poc also has the variant cap-store (CHERI_CAP_STORE),
whose G0's module stores a tagged capability into the channel page, and
that image's control run, the expectation cap-store-control.

Purpose: a scenario is data (planning/mvp-m0-plan.md, "Scenarios and the
harness", Q9): scenarios/<name>/scenario.json names the domains, their harts,
windows, roots, VMIDs, DTB bootargs, guest programs, and expected outcomes.
This one generator turns it into everything the build and the checkers read,
so a scenario change is a rebuild, never a run-time selection:

  DIR/mvp-scenario.h        the build header: the scenario's name, the
                            platform's harts, each domain's hart, VMID, and
                            root, the ring sizes, and the binding initializer,
                            with static assertions against src/mvp-layout.h
  DIR/expect/<image>.json   one expectation file per image: the scenario
                            (two-guests), each negative variant, and each
                            probe image (S1 H27), with the control-hart lines
                            in order as templates and regular expressions
                            (a probe image's whole sequence, its probe lines
                            in place), each domain's required lines, the
                            rejected substrings, the counters, the accepted
                            exit classes, the concurrency floors, and the
                            variant's or probe's own outcome; the capture
                            checker (tests/check-capture.py) reads them
  DIR/expect/SCENARIO.txt   the file list and the scenario's SHA-256

Schemas: be-mvp-scenario-v1 (M0's two-guests, whose expectation files keep
schema be-mvp-expect-v1 byte for byte, and whose header declares no channel
and no denial entry) and be-mvp-scenario-v2 (planning/mvp-m1-plan.md,
"Scenarios and the harness", Q10: v1's fields, with no probe image (Q13),
plus the policy, labeling, need sets, manifest objects and channels,
accepted exits, each domain's role, denials, and window rights, and the
expected denials and report). Each schema refuses a field it does not
define. For a v2 scenario it first runs tools/policy-check.py's analyses
(--policy-tool) and writes nothing unless they pass (Part 4: such a
configuration "must not be sealed"); then it also writes

  DIR/authority-report.json the policy check's authority report
  DIR/mvp-scenario.h        with the sealed channel record, the accepted
                            denial entry, and the configuration identity
  DIR/expect/<image>.json   schema be-mvp-expect-v2: each domain's own lines
                            (its command line, then its role's MVPINIT 07
                            and 08 lines after MVPINIT 02), the channel's
                            :03 and :05 lines, each expected denial with its
                            BE_MVP:DENY line, the exit sum, the accepted
                            exits, the report's identity, and the variants'
                            DETAIL lines

and --negative NAME applies the scenario's build-time negative image
(negatives/NAME.json, read by tools/policy-check.py), which must write
nothing.

be-mvp-scenario-v3 (planning/mvp-m2-plan.md, "Scenarios and the harness",
Q12: anchor) is v2 with the pages in place of the channel (Q1: a request
page the host writes, a response page the protected domain writes, and a
secret page it alone reads), the management grants (Q3), the secret (Q5),
and the measurement's inputs (Q7); each role's domain lines, management
calls, and requests in its expect; and the plan's four runtime negatives.
Its policy check (A1 to A8 with the domain class) and, given --kernel and
--dtb, the protected domain's kernel and DTB as built, the expected
measurement come first; then the management calls are checked against
hart 0's decision (Q3, Q14) and the requests' HMAC-SHA-256 digests
computed (Q6, Q8), and it writes the report with the management grants
and the measurement, a header with the pages, the secret, the expected
measurement, and the grants (BE_MVP_PAGE_* and BE_MVP_MGMT_* are M2-2's
and M2-3's names), and expectations of schema be-mvp-expect-v3: v2's
fields with each role's MVPINIT 07 PAGES, 08, 09, and 10 lines, the
:03 PAGE_CHECKED, :05 PAGE_CLEARED and SECRET_PLACED, :06 MEASURED, :12
DOMAIN_PAUSED and DOMAIN_TERMINATED lines, each domain's BE_MVP:MGMT
lines, the pages and leaves, grants, secret, measurement and its inputs,
requests and digests, and each runtime negative's failure; each
domain's :11 line carries spv=<S> (Plan revision M2-A.1: the PONG's SPV,
1, or 0 inside a management wait of its hart, which the capture checker
resolves).

Trust: it checks the scenario against src/mvp-layout.h (the platform's harts,
the control hart, every window, root, VMID, block, ring, and limit) and
against tools/gen-dts.py (each domain's bootargs, which the pinned DTBs carry);
a domain hart must exist on the platform, differ from the control hart and the
other domain's, and is otherwise only a name. Nothing here selects a hart at
run time: the monitor reads the generated header, and hart 0 validates the
binding at boot through the firmware.

Every schema's domains carry, since M7 (planning/mvp-m7-plan.md, D-5),
"console_input": true or false, present and boolean: whether the domain
is granted console input, a configuration fact outside the policy, which
the generated proposal (mvp-config.c) carries into the configuration hart
0 validates, seals, and derives at boot. The schema strings are
unchanged: the accepted model's policy fixture generator
(model/tools/gen-policy-fixtures.mjs) reads te-poc's and anchor's
scenarios and names exactly v2 and v3.

M7-4's console variants (planning/mvp-m7-plan.md, Q4, Q8, D-4, D-11), in
any schema's variants: SCENARIO-shell, whose domains with a shell
(rdinit=/init-shell, tools/gen-dts.py's shell DTBs) are granted console
input (never anchor's protected domain, Q27) and whose session file,
sessions/<name>.json (be-mvp-session-v1: focus, send, expect, and
negative steps, NONCE the run's nonce), tests/session-typist.py types;
and two-guests' QEMU-only hostile, G0's DTB with rdinit=/init-hostile.
Its monitor seals the variant's grants (mvp-config.c, under
BE_MVP_VARIANT_<NAME>, outside the core identity), and its expectation is
the scenario's with the variant's command lines and inits, each shell's
lines (its line 11, each send's echo and the lines the command prints,
its exit), BE_MVP:15 and :16 FOCUS none after :07 and :18 before :13, the
console_input section (the grants, the prefix, the session's file,
SHA-256, and steps, each with the bytes it types and the lines it waits
for, the focus order, and the drops it provokes), dbcn_input among sbi's
terms, a granted domain's dbcn_read=0, and, with a role, the session's
denials, management calls, and requests in place of the role's; or the
hostile guest's lines and its forged look-alikes. A session is refused
unless each expect is in its focused domain's last send's lines, each
command is one the generator knows, every shell exits, and no step's
expected lines could exceed the outbound ring's peak budget,
BE_MVP_RING_PEAK_BUDGET (D-2, session_bound(): each line a LINE record,
16 bytes and its payload padded to 8 per 256 bytes of line, each
placeholder counted as 64 bytes, and 512 bytes of slack).

M9 (planning/mvp-m9-plan.md, D-1 to D-4; mvp/docs/log-profile.md, the
Beryllium log profile version 1) replaces M2's one measurement by the
log: from --guest DIR, the guest build directory (the Image and every
device tree tools/gen-dts.py makes), it computes each image's records as
its monitor logs them (R2's five ranges as slots, which only the link
fixes; R3's core identity, console grants, and the configuration and
policy identities or policy-absent; R4's kernel and device trees as
placed, and anchor's secret page), each domain's expected launch register
by the profile's recurrence, and the image's expected count; it writes
them into the header (BE_MVP_LAUNCH_REGISTER_0 and _1, BE_MVP_LOG_*,
under the image's variant macro where they differ from the scenario's,
and under BE_MVP_PROBE_IMAGE for the probes) and the expected :06 LAUNCH,
:19 LOG, and :20 REGISTERS lines into each expectation in the profile's
positions for the image's run class (3.2), with a `log` section in the
export's shapes; wrong-measurement carries its protected domain's
expected launch register with bit 0 of its first byte flipped (Q16); and
anchor's self-report-flip variant, its image's be_mvp_log_canary flipped
by one bit after the link (tools/flip-canary.py), a complete run, expects
one finding, `self-report differs: mvp-rodata`.

Scope: M0's binding of two domains; M1's channel, denials, and identity;
M2's pages, secret, management calls, and requests; M7's console input
grant; M7-4's console variants and sessions; M9's log.
--self-test checks the generator's own refusals on mutated copies of the
scenario, and for v2 and v3 the policy check's structural refusals and
the generated lines (v3's: the pages', the measurement's, the management
calls', the roles', the probe's spv=<S>, and the negatives' DETAIL lines)
and header; and, for each scenario, its console variants' and session's
refusals and the D-2 bound.
"""

import argparse
import copy
import hashlib
import hmac
import importlib.util
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
SCHEMA = "be-mvp-scenario-v1"
SCHEMA_V2 = "be-mvp-scenario-v2"
SCHEMA_V3 = "be-mvp-scenario-v3"
EXPECT_SCHEMA = "be-mvp-expect-v1"
EXPECT_SCHEMA_V2 = "be-mvp-expect-v2"
EXPECT_SCHEMA_V3 = "be-mvp-expect-v3"
TERMINAL_REGEX = "BE_MVP:14 SHUTDOWN|BE_MVP:FAIL|BE_K3_B3: FAIL"
DOMAINS = 2
# Each schema's fields (Q10: the generator refuses unknown fields); v2
# keeps every v1 field.
FIELDS = {1: {"top": {"spdx", "copyright", "purpose", "trust", "scope",
                      "schema", "name", "platform", "rings", "limits",
                      "domains", "expect", "variants", "probes"},
              "domain": {"index", "name", "prefix", "hart", "vmid", "root",
                         "block", "window", "kernel", "dtb", "bootargs",
                         "program", "console_input"},
              "window": {"gpa", "hpa", "bytes"},
              "expect": {"domain_lines", "rejected", "counters",
                         "exit_classes", "concurrency"}}}
FIELDS[2] = {"top": FIELDS[1]["top"] | {"policy", "labeling", "need",
                                        "objects", "channels",
                                        "accepted_exits"},
             "domain": FIELDS[1]["domain"] | {"role", "deny"},
             "window": FIELDS[1]["window"] | {"rights"},
             "expect": FIELDS[1]["expect"] | {"denials", "report"}}
# v3 (planning/mvp-m2-plan.md, Q12): v2's fields, with the pages in place
# of the channel and no probes, the management grants, the secret, and
# the measurement's inputs; its expect holds each role's domain lines, and
# each domain's management calls and the requests.
FIELDS[3] = {"top": FIELDS[2]["top"] - {"channels", "probes"} | {
    "pages", "grants", "secret", "measurement"},
    "domain": FIELDS[2]["domain"], "window": FIELDS[2]["window"],
    "expect": FIELDS[2]["expect"] | {"mgmt", "requests"}}
SECTIONS = {"platform": {"harts", "control_hart", "timebase_hz"},
            "rings": {"inbound_bytes", "outbound_bytes"},
            "limits": {"exit_ceiling", "run_budget_ticks", "hart_start_ticks",
                       "ready_ticks", "fail_ack_ticks"}}
# Q1's channel page, which the layout's BE_MVP_CHANNEL_* must name.
Q1_CHANNEL = {"gpa": 0x84000000, "hpa": 0x118000000, "bytes": 0x1000}
# The channel record's rights as M1-2's channel check admits them: one
# writer's read and write, the reader's read (src/mvp-gstage.h).
CHANNEL_RIGHTS = {"writer": ["read", "write"], "reader": ["read"]}
# V4: each window stays read, write, and execute.
WINDOW_RIGHTS = ["read", "write", "execute"]
# The guest-page fault each denied access takes and the access fault it is
# delivered as (planning/mvp-m1-plan.md, Q4 and Q5; Q3: no scenario access
# is a fetch, so cause 20 is the host tests' alone).
CAUSES = {"load": 21, "store": 23}
INJECTED = {20: 1, 21: 5, 23: 7}
# The writer's flag (ASCII BEM1CHAN) at the page's offset 0, before the
# pattern ("Guest software"); and the placeholders of the roles' lines
# ("Markers"): <x> a digest, <n> a count, <v> the access's virtual address,
# <p> its instruction's.
CHANNEL_FLAG = 0x42454d314348414e
FLAG_BYTES = 8
ROLE_PLACEHOLDERS = {"<x>": r"0x[0-9a-f]+", "<n>": r"[0-9]+",
                     "<v>": r"0x[0-9a-f]+", "<p>": r"0x[0-9a-f]+"}
BOOTARGS_TEMPLATE = "[<s>] Kernel command line: <bootargs>"
REPORT_FILE = "authority-report.json"
HSM_STOPPED = 1
# The plan's Markers, as generated from the binding: <T> ticks, <N> a count,
# <K> and <S> the kernel's bytes and image_size, <B> bytes, <h> the hedeleg
# readback, <f> the FDT pointer; every one but <N> is lower-case hex. <H> is
# a hart's HSM state that may be STARTED (0) or STOPPED (1), and <W>
# BE_MVP:02's started hart, a number or none (Plan revision M0-A.2): which
# hart may be STARTED is the capture checker's to judge, against the shim's
# boot_hart line.
PLACEHOLDERS = {
    "<T>": r"0x[0-9a-f]+",
    "<K>": r"0x[0-9a-f]+",
    "<S>": r"0x[0-9a-f]+",
    "<B>": r"0x[0-9a-f]+",
    "<X>": r"0x[0-9a-f]+",
    "<h>": r"0x[0-9a-f]+",
    "<f>": r"[0-9a-f]{16}",
    "<N>": r"[0-9]+",
    "<I>": r"-?[0-9]+",
    "<H>": r"[01]",
    "<W>": r"(?:none|[0-9]+)",
    # M7-4's BE_MVP:18 (planning/mvp-m7-plan.md, D-3): a delivered SHA-256's
    # first 16 hex digits, and the drops by reason, or none.
    "<Q>": r"[0-9a-f]{16}",
    "<D>": r"(?:none|[a-z-]+:[0-9]+(?:,[a-z-]+:[0-9]+)*)",
    # M9's log lines (mvp/docs/log-profile.md, 4.1): a value only the link
    # fixes, a hex64 (<Y>) or a digest (<Z>), which the capture checker
    # takes from the image's reference manifest; and the barrier's hashing
    # ticks (<U>), at most eight digits.
    "<Y>": r"0x[0-9a-f]{16}",
    "<Z>": r"[0-9a-f]{64}",
    "<U>": r"0x(?:0|[1-9a-f][0-9a-f]{0,7})",
}
# Plan revision M2-A.1 (planning/mvp-m2-plan.md): in the BE_MVP:11 line of
# an image with the management extension (a v3 scenario's, and its
# runtime negatives'), and there alone, <S> is the PONG's SPV, 1, or 0
# where the PING reached the domain's hart while it waited in HS for hart
# 0's answer to a management request (Q14); the line's regular expression
# admits either, and the capture checker resolves which against the
# capture's BE_MVP:MGMT lines. M0's and M1's lines keep spv=1.
SPV = "<S>"
SPV_PLACEHOLDERS = dict(PLACEHOLDERS, **{SPV: r"[01]"})
CLASSES = ("boot", "gstage", "sstc", "controls", "payload", "interrupt",
           "guest-page-fault", "virtual-instruction", "access-fault",
           "illegal-instruction", "exception", "exit-budget", "run-timeout",
           "resume", "console", "guest-failure", "guest-reboot",
           "shutdown-returned", "firmware", "hart-start", "hart-ready",
           "ring", "ipi", "measurement", "mgmt", "log")
PROBE_LINES = {
    "hsm": "BE_MVP:PROBE hsm status={status}",
    "hgatp": "BE_MVP:PROBE hgatp vmid=0x3fff sv48x4=<X> sv57x4=<X> "
             "sv39x4=<X> vmid_bits=<N> restored=<X>",
    "gpf": "BE_MVP:PROBE gpf access={access} gpa=<X> scause=<X> stval=<X> "
           "htval=<X> htinst=<X> sepc=<X> gva=<N>",
    "ipi": "BE_MVP:PROBE ipi mode={mode} sent=100 delivered=<N> min=<T> "
           "median=<T> max=<T> spv=<N>",
    "order": "BE_MVP:PROBE order mode={mode} iterations=10000 stale=<N>",
    "vmid": "BE_MVP:PROBE vmid mode={mode} gpa=<X> hgatp_a=<X> hgatp_b=<X> "
            "value_a=<X> value_b=<X> reads=10 before=<X> after=<X>",
    # probe-console-input (planning/mvp-m7-plan.md, D-12): its window, and
    # its counts with every byte's SHA-256; the lines of the bytes received
    # between them, as many as were, are the capture checker's.
    "input-window": "BE_MVP:PROBE console-input window_ticks=<X> "
                    "prefix=none",
    "input-total": "BE_MVP:PROBE console-input total=<N> polls=<N> "
                   "nonzero_polls=<N> max_per_poll=<N> errors=<N> "
                   "sha256=<Q>",
}
PROBE_ARGUMENTS = {"gpf": ("load", "store", "fetch"), "ipi": ("hs", "vs"),
                   "order": ("unfenced", "fenced")}
VARIANT_KEYS = {"name", "toolchains", "where", "change", "fail", "after",
                "detail", "fallback", "domain", "hart", "cause", "pass",
                "time_above_zero", "shim_line", "exit_ceiling",
                "run_budget_ticks", "outbound_bytes", "drain_delay_ticks",
                "rdinit", "console_input", "session", "mutate", "findings"}
# A v2 variant may also name the leaf a refused channel check walked and
# declared (reader-write), or each domain's first fault and the accepted
# exits it builds with (no-inject).
VARIANT_KEYS_V2 = VARIANT_KEYS | {"walked", "declared", "first_fault",
                                  "accepted_exits"}
# A v3 variant's (planning/mvp-m2-plan.md, Scenarios and the harness):
# the page whose leaf the refused page check walked and declared
# (secret-shared, response-writable); the measured domain whose
# measurement differs (wrong-measurement); or, under the variant's run
# budget, the domain another terminates and each domain's management
# calls (no-grant-check); and M9's post-link mutation and its finding
# (self-report-flip).
VARIANT_KEYS_V3 = {"name", "toolchains", "where", "change", "fail", "after",
                   "detail", "page", "domain", "hart", "walked", "declared",
                   "run_budget_ticks", "terminated", "mgmt", "pass",
                   "rdinit", "console_input", "session",
                   "mutate", "findings"}
# A variant's one compile-time change, as the layout names its value.
VARIANT_VALUES = {"exit_ceiling": "VARIANT_EXIT_CEILING",
                  "run_budget_ticks": "VARIANT_RUN_BUDGET",
                  "outbound_bytes": "VARIANT_OUTBOUND_RING_BYTES",
                  "drain_delay_ticks": "VARIANT_DRAIN_DELAY_TICKS"}
# M2 (planning/mvp-m2-plan.md): the management extension's functions and
# the SBI results hart 0's decision gives (Q3, Q14), or the requester's
# hart for another FID, the states hart 0 prints; Q5's 32-byte secret;
# Q8's 64-byte request message; the leaf
# rights the page check admits, by page kind and end (Q1); and the
# no-grant-check variant's run budget, 2^27 ticks (Q10, Budgets).
MGMT_FIDS = {0: "pause", 1: "terminate"}
SBI_SUCCESS, SBI_NOT_SUPPORTED, SBI_INVALID_PARAM = 0, -2, -3
SBI_DENIED, SBI_INVALID_STATE = -4, -10
SECRET_BYTES, REQUEST_BYTES = 32, 64
PAGE_RIGHTS = {"channel": {"writer": ["read", "write"], "reader": ["read"]},
               "secret": {"reader": ["read"]}}
MGMT_RUN_BUDGET = 1 << 27
HMAC_TEXT = ("HMAC-SHA-256 (RFC 2104, FIPS 180-4), key the secret's 32 "
             "bytes, message the request's sequence number as 8 "
             "little-endian bytes and then its message, zero-padded to "
             "64 bytes")
# The MVP core profile's C names (src/mvp-core.h; the R1 enums of the MVP
# port's include/be/manifest.h), by the codes tools/policy-check.py's
# core() gives them, and the generated file (planning/mvp-m6-plan.md, D-1).
KINDS = ("MONITOR_CODE", "MONITOR_DATA", "ROOT_TABLE", "TRUSTED_STACK",
         "SAVED_STATE", "ASSIGNABLE", "GUEST_CODE")
FRAMES = KINDS[:5] + ("PRIVATE", "SHARED", "GUEST_CODE")
DOMAIN_IDS = ("INVALID", "MANAGEMENT", "PROTECTED")
RIGHT_BITS = {"read": 1, "write": 2, "execute": 4}
CONFIG_FILE = "mvp-config.c"
# The kernel's line when each v3 init loads the management module, an
# out-of-tree one (planning/mvp-m2-plan.md, Guest software), between its
# MVPINIT 02 and 07 lines.
MODULE_LINE = "[<s>] be_mgmt: loading out-of-tree module taints kernel."


# beryllium-cheri: the monitor variant's armed henvcfg, which its
# BE_MVP:09 HART_READY lines carry: the RISC-V monitor's STCE only, or the
# CHERI-aware monitor's STCE and CHERI v0.9.3's CRE (src/mvp.h,
# BE_MVP_HENVCFG_ARMED); main() selects it (--monitor).
ARMED_HENVCFG = {"riscv": "0x8000000000000000",
                 "cheri": "0x8000000010000000"}
MONITOR = "riscv"
# beryllium-cheri: the guest flavour's domain lines (--guest-flavour).
# scenario.json states the Linux guest's kernel release, v7.2's, and the
# CHERI Linux guest's, CHERI Alliance Linux v7.1's (guest/cheri-pins.txt's
# banner; guest/mvp-init.c's EXPECTED_RELEASE), replaces it in the two
# lines of each domain's that name it.
FLAVOUR_LINES = {
    "linux": (),
    "cheri-linux": (("[<s>] Linux version 7.2.0 <banner>",
                     "[<s>] Linux version 7.1.0 <banner>"),
                    ("MVPINIT 02 UNAME release=7.2.0 machine=riscv64",
                     "MVPINIT 02 UNAME release=7.1.0 machine=riscv64")),
}
# beryllium-cheri: the lines the guest flavour adds to each domain's lines
# (planning/cheri-enforcement-plan.md, CE-2, Q6), each beside a line of
# the scenario's, before it (0) or after it (1): the CHERI Linux guest's
# root capability, which its kernel prints before its banner and requires
# to be the whole address space with every permission, its address and
# raw words the flavour's placeholders; and its kernel's probe of the
# capability-write PTE bit, which the CHERI emulator's Zcheripte makes
# yes, after its timer line. FLAVOUR_PLACEHOLDERS go into each
# expectation's domain_placeholders, which the capture checker reads.
FLAVOUR_ADDED = {
    "linux": (),
    "cheri-linux": (
        ("[<s>] Linux version 7.1.0 <banner>", 0,
         "[<s>] CHERI: Root capability: <capaddr>[V:1111:C:rwxCalse:1:.:"
         "0x0000000000000000-0xffffffffffffffff] (1:<capword>:<capword>)"),
        ("[<s>] riscv-timer: Timer interrupt in S-mode is available via "
         "sstc extension", 1, "[<s>] CHERI: Selected SATP mode: "
         "0x8000000000000000 PTE.CW support: yes")),
}
FLAVOUR_PLACEHOLDERS = {"linux": {},
                        "cheri-linux": {"<capaddr>": r"0x[0-9a-f]{16}",
                                        "<capword>": r"[0-9a-f]{16}"}}
# beryllium-cheri: the CHERI-aware monitor's variant of a scenario with a
# channel (--monitor cheri; planning/cheri-enforcement-plan.md, section 6,
# B2), which monitor_variants() adds after the scenario's own: channel-cw,
# whose root builder also sets CW in each channel leaf, which the walker
# refuses at domain 0's root, before any root's line: BE_MVP:FAIL gstage
# after BE_MVP:02, with no DETAIL line, and no domain hart started.
CHANNEL_CW = {"name": "channel-cw", "toolchains": ["gcc", "clang"],
              "where": ["qemu"],
              "change": "the root builder also sets CW, the capability-"
                        "write bit, in each channel leaf (a compile-time "
                        "switch in src/mvp-gstage.c, under BE_MVP_CHERI); "
                        "the sealed record is unchanged",
              "fail": "gstage", "after": "BE_MVP:02"}
# beryllium-cheri: te-poc's two roles' own CHERI faults (planning/
# cheri-enforcement-plan.md, CE-3 and section 6, C1 and C2), which the
# CHERI Linux guest's init makes after its line 02 in each domain with an
# M1 role, whose lines name its channel (guest/cheri/cheri-tests.c): the
# exception-trace sysctl written 0, so that the kernel prints no report of
# the one user fault; a child's load one byte past a capability bounded to
# 16 bytes at the probe page, delivered to its handler as SIGSEGV with
# SEGV_CAPBOUNDSERR at the base plus 16; a write of 64 bytes from that
# capability, EFAULT, and from one bounded to 64; and the sysctl written 1.
# Every value is fixed, the probe page's address too. The report, which
# begins with CHERI_REPORT, is rejected in every CHERI Linux guest's lines.
CHERI_PROBE_VA = 0x100000000
CHERI_TEST_LINES = (
    "MVPINIT 14 CHERI exception-trace=0",
    f"MVPINIT 14 CHERI bounds signo=11 code=12 base={CHERI_PROBE_VA:#x} "
    f"addr={CHERI_PROBE_VA + 16:#x}",
    "MVPINIT 14 CHERI write bound=16 bytes=64 result=-1 errno=14",
    "MVPINIT 14 CHERI write bound=64 bytes=64 result=64 errno=0",
    "MVPINIT 14 CHERI exception-trace=1")
CHERI_TEST_ROLES = "MVPINIT 07 CHANNEL role="
CHERI_TEST_AFTER = FLAVOUR_LINES["cheri-linux"][1][1]
CHERI_REPORT = "===== CHERI exception"
# beryllium-cheri: the CHERI Linux guest's te-poc variant (section 6, C3),
# which monitor_variants() adds after channel-cw: cheri-fault-hs, whose
# hedeleg leaves out cause 28, so that the first child's bounds fault
# reaches HS: BE_MVP:FAIL exception after the domains' entries, with the
# DETAIL of either domain's fault (CHERI_FAULT_DETAIL: cause 0x1c from VU
# mode, tval the faulting address, and no guest-page fault's htval or
# htinst), no line of its child, the faulting domain's last line its
# exception-trace line, and each BE_MVP:09's hedeleg a WARL reading of
# 0xb15d holding 0xb10c (cheri_fault_images()).
CHERI_FAULT_HS = {"name": "cheri-fault-hs", "toolchains": ["gcc", "clang"],
                  "where": ["qemu"],
                  "change": "hedeleg and its required set leave out cause "
                            "28, the CHERI fault (a compile-time switch over "
                            "src/mvp.h's and src/mvp-trap.S's values, under "
                            "BE_MVP_CHERI)",
                  "fail": "exception", "after": "BE_MVP:10"}
CHERI_FAULT_DETAIL = ("BE_MVP:DETAIL domain={index} hart={hart} cause=0x1c "
                      f"pc=<X> tval={CHERI_PROBE_VA + 16:#x} htval=0x0 "
                      "htinst=0x0 spvp=0 vsatp=<X> exits=<N>")
# beryllium-cheri: the CHERI Linux guest's te-poc variant cap-store (CE-4;
# section 6, B3), which monitor_variants() adds after cheri-fault-hs: G0's
# device tree is tools/gen-dts.py's cap-store, whose init, /init-cap-store,
# loads the capability-store module (guest/cheri/be-cheri-store.c) with the
# channel's GPA before its pattern write. The module stores a tagged
# capability into its own data, an integer at the channel page's offset 64,
# and the mapping's tagged capability at offset 128, which the page's
# G-stage leaf, without CW, faults under Zcheripte: BE_MVP:FAIL
# guest-page-fault after the domains' entries, with G0's DETAIL
# (CAP_STORE_DETAIL: cause 23 from VS mode, htval the store's GPA >> 2, no
# transformed instruction, a nonzero vsatp, and tval's page offset 0x080),
# and G0's last lines the kernel's taint line and the module's first two
# (CAP_STORE_LINES), so that the module printed nothing after its store
# (cap_store_images()). Its control, cap-store-control (B4), the same image
# without Zcheripte, passes as te-poc does, with G0's lines its device
# tree's and the module's and the init's after its own CHERI faults' lines,
# the tag landing (cap_store_control()).
CHERI_CAP_STORE = {"name": "cap-store", "toolchains": ["gcc", "clang"],
                   "where": ["qemu"],
                   "change": "G0's device tree names rdinit=/init-cap-store, "
                             "whose init loads the capability-store module "
                             "with the channel's GPA before its pattern "
                             "write; the monitor is te-poc's with its own "
                             "launch registers",
                   "fail": "guest-page-fault", "after": "BE_MVP:10"}
CAP_STORE_INIT, CAP_STORE_OFFSET = "/init-cap-store", 0x80
CAP_STORE_LINES = (
    "[<s>] be_cheri_store: loading out-of-tree module taints kernel.",
    "[<s>] be_cheri_store: own tag=1",
    f"[<s>] be_cheri_store: channel gpa={Q1_CHANNEL['gpa']:#x} offset=0x40 "
    "value=0x5678",
    f"[<s>] be_cheri_store: channel offset={CAP_STORE_OFFSET:#x} tag=1",
    f"MVPINIT 14 CHERI cap-store gpa={Q1_CHANNEL['gpa']:#x} result=0 "
    "errno=0")
CAP_STORE_DETAIL = (
    "BE_MVP:DETAIL domain=0 hart={hart} cause=0x17 pc=<X> tval=<O> "
    f"htval={(Q1_CHANNEL['gpa'] + CAP_STORE_OFFSET) >> 2:#x} htinst=0x0 "
    "spvp=1 vsatp=<V> exits=<N>")
CAP_STORE_PLACEHOLDERS = dict(PLACEHOLDERS, **{
    "<O>": r"0x[0-9a-f]*080", "<V>": r"0x[0-9a-f]*[1-9a-f][0-9a-f]*"})


class ScenarioError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ScenarioError(message)


def flavour_lines(scenario, flavour):
    """beryllium-cheri: SCENARIO with FLAVOUR's domain lines: each line
    FLAVOUR_LINES replaces, found once in each domain's lines."""
    lines = scenario.get("expect", {}).get("domain_lines")
    for own in lines.values() if isinstance(lines, dict) else [lines]:
        for old, new in FLAVOUR_LINES[flavour]:
            found = own.count(old) if isinstance(own, list) else 0
            require(found == 1, f"expect.domain_lines holds {old!r} "
                    f"{found} times, not once, for the {flavour} guest")
            own[own.index(old)] = new
    return scenario


def flavour_images(images, flavour):
    """beryllium-cheri: each image's domain lines with the lines
    FLAVOUR_ADDED adds beside theirs, each found once in each domain's
    lines, and its domain placeholders with FLAVOUR_PLACEHOLDERS beside its
    own; for the CHERI Linux guest, each domain's lines with an M1 role's
    with CHERI_TEST_LINES after its line 02, and each image's rejected
    substrings with CHERI_REPORT. They are added to the images as
    generated, so that the generator's rules and its self-test, which name
    the scenario's lines' places, read the scenario's lines."""
    for image in images.values() if FLAVOUR_ADDED[flavour] else ():
        if "rejected" in image:
            image["rejected"] = image["rejected"] + [CHERI_REPORT]
        lines = image.get("domain_lines")
        if lines is None:
            continue
        added = {}
        for key, own in lines.items() if isinstance(lines, dict) else [
                (None, lines)]:
            own = list(own)
            tests = ((CHERI_TEST_AFTER, 1, CHERI_TEST_LINES),) if any(
                text.startswith(CHERI_TEST_ROLES) for text in own) else ()
            for beside, after, new in FLAVOUR_ADDED[flavour] + tests:
                found = own.count(beside)
                require(found == 1, f"{image['image']}'s domain lines hold "
                        f"{beside!r} {found} times, not once, for the "
                        f"{flavour} guest")
                at = own.index(beside) + after
                own[at:at] = [new] if isinstance(new, str) else list(new)
            added[key] = own
        image["domain_lines"] = added if isinstance(lines, dict) else \
            added[None]
        image["domain_placeholders"] = dict(
            image.get("domain_placeholders") or {},
            **FLAVOUR_PLACEHOLDERS[flavour])
    return images


def cheri_fault_images(images):
    """beryllium-cheri: cheri-fault-hs's outcome (CHERI_FAULT_HS): either
    domain's DETAIL, its child's line absent, the faulting domain's last
    line, and the hedeleg its BE_MVP:09 lines read, with what must hold."""
    image = images.get(CHERI_FAULT_HS["name"])
    if image is not None:
        image["outcome"].update(
            detail_lines=[line(CHERI_FAULT_DETAIL.format(**domain))
                          for domain in image["domains"]],
            absent=["MVPINIT 14 CHERI bounds"],
            last_lines=[CHERI_TEST_LINES[0]], hedeleg=["0xb15d", "0xb10c"])
    return images


def cap_store_images(images):
    """beryllium-cheri: cap-store's outcome (CHERI_CAP_STORE): G0's DETAIL,
    and G0's last lines, the taint line and the module's first two."""
    image = images.get(CHERI_CAP_STORE["name"])
    if image is not None:
        image["outcome"].update(
            detail_lines=[line(CAP_STORE_DETAIL.format(
                hart=image["domains"][0]["hart"]), CAP_STORE_PLACEHOLDERS)],
            last_lines=list(CAP_STORE_LINES[:3]))
    return images


def cap_store_control(images):
    """beryllium-cheri: cap-store's control (CE-4; section 6, B4), the same
    image without Zcheripte, whose expectation is cap-store's with te-poc's
    passing outcome, denials, and complete log; G0's lines with its device
    tree's command line and init (console_head()) and, after its own CHERI
    faults' lines, the module's four and the init's (CAP_STORE_LINES); and
    each domain's capability-write PTE line reading no."""
    image = images.get(CHERI_CAP_STORE["name"])
    if image is None:
        return images
    control = copy.deepcopy(image)
    control.update(
        image=image["image"] + "-control", outcome={"pass": True},
        denials=copy.deepcopy(images[image["scenario"]]["denials"]),
        change="cap-store's image, run without the CHERI emulator's "
               "Zcheripte: the module's capability store lands, and the "
               "pattern's integer stores clear its tag")
    control["log"].update(run="complete", terminal="before-shutdown")
    own = control["domain_lines"]["0"]
    bootargs = image["domains"][0]["bootargs"].replace(
        " -- ", f" rdinit={CAP_STORE_INIT} -- ", 1)
    after = own.index(CHERI_TEST_LINES[-1]) + 1
    control["domain_lines"]["0"] = console_head(
        own, CAP_STORE_INIT, bootargs, CHERI_TEST_LINES[-1]) + \
        list(CAP_STORE_LINES) + own[after:]
    for key, lines in control["domain_lines"].items():
        control["domain_lines"][key] = [
            text.replace("PTE.CW support: yes", "PTE.CW support: no")
            for text in lines]
    images[control["image"]] = control
    return images


def monitor_variants(scenario, flavour):
    """beryllium-cheri: SCENARIO with the monitor variant's own variants
    after its own: the CHERI-aware monitor's channel-cw in a scenario with
    a channel (a v2 scenario, te-poc), and for its CHERI Linux guest,
    cheri-fault-hs and cap-store."""
    if MONITOR == "cheri" and version_of(scenario) == 2:
        scenario["variants"] = scenario.get("variants", []) + [
            copy.deepcopy(CHANNEL_CW)] + ([
                copy.deepcopy(CHERI_FAULT_HS), copy.deepcopy(CHERI_CAP_STORE)]
                if flavour == "cheri-linux" else [])
    return scenario


def layout_constants(path):
    """Every BE_MVP_* literal of mvp-layout.h, as integers."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    values = {}
    for name, value in re.findall(
            r"^#define\s+BE_MVP_(\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|\d+)\)",
            text, re.M):
        require(name not in values, f"BE_MVP_{name} is defined twice")
        values[name] = int(value, 0)
    return values


def load_tool(path, name):
    """A sibling tool as a module (tools/gen-dts.py, tools/policy-check.py),
    so that the generator and the tool share one implementation."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def number(value, label):
    """A JSON integer, or a string holding one (hex for addresses)."""
    if isinstance(value, bool):
        raise ScenarioError(f"{label} is not a number")
    if isinstance(value, int):
        return value
    require(isinstance(value, str) and
            re.fullmatch(r"0x[0-9a-f]+|[0-9]+", value) is not None,
            f"{label} is not a number: {value!r}")
    return int(value, 0)


def hgatp(vmid, root):
    return 8 << 60 | vmid << 44 | root >> 12


def known(value, fields, label):
    """An object holding only fields its schema defines (Q10)."""
    require(isinstance(value, dict), f"{label} is not an object")
    unknown = sorted(set(value) - fields)
    require(not unknown, f"{label} has unknown fields {unknown}")
    return value


def version_of(scenario):
    require(isinstance(scenario, dict), "the scenario is not an object")
    version = {SCHEMA: 1, SCHEMA_V2: 2, SCHEMA_V3: 3}.get(
        scenario.get("schema"))
    require(version is not None,
            f"schema is not {SCHEMA}, {SCHEMA_V2}, or {SCHEMA_V3}")
    return version


# The grammar of an image name, one path component under expect/ and the
# build directory: the scenario's has no separator, dot, or upper case; a
# variant's may also hold a dot between two characters (M0's accepted
# `sbi-3.0`), never leading, trailing, or doubled, so `.`, `..`, hidden
# names, and paths are out; a probe's is probe- and letters.
SCENARIO_NAME = r"[a-z][a-z0-9-]{0,31}"
VARIANT_NAME = r"(?=.{1,32}$)[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)*"
PROBE_NAME = r"probe-[a-z][a-z-]{0,25}"


def check(scenario, layout, dts):
    """Every rule both schemas share; return the normalized binding."""
    version = version_of(scenario)
    fields = FIELDS[version]
    known(scenario, fields["top"], "the scenario")
    name = scenario.get("name")
    require(isinstance(name, str) and
            re.fullmatch(SCENARIO_NAME, name) is not None,
            f"scenario name {name!r} is not a short lower-case name")
    platform = known(scenario.get("platform", {}), SECTIONS["platform"],
                     "platform")
    harts = number(platform.get("harts"), "platform.harts")
    control = number(platform.get("control_hart"), "platform.control_hart")
    require(harts == layout["HARTS"],
            f"platform.harts {harts} is not the layout's {layout['HARTS']}")
    require(control == layout["CONTROL_HART"] == 0,
            "the control hart is not hart 0, which the accepted R3 boot "
            "check requires")
    require(number(platform.get("timebase_hz"), "platform.timebase_hz") ==
            layout["TIMEBASE_HZ"], "platform.timebase_hz is not the layout's")
    rings = known(scenario.get("rings", {}), SECTIONS["rings"], "rings")
    inbound = number(rings.get("inbound_bytes"), "rings.inbound_bytes")
    outbound = number(rings.get("outbound_bytes"), "rings.outbound_bytes")
    require(inbound == layout["INBOUND_RING_BYTES"] and
            outbound == layout["OUTBOUND_RING_BYTES"],
            "the ring sizes are not the layout's")
    limits = known(scenario.get("limits", {}), SECTIONS["limits"], "limits")
    for key, constant in (("exit_ceiling", "EXIT_CEILING"),
                          ("run_budget_ticks", "RUN_BUDGET"),
                          ("hart_start_ticks", "HART_START_TICKS"),
                          ("ready_ticks", "READY_TICKS"),
                          ("fail_ack_ticks", "FAIL_ACK_TICKS")):
        require(number(limits.get(key), f"limits.{key}") == layout[constant],
                f"limits.{key} is not the layout's BE_MVP_{constant}")
    domains = scenario.get("domains")
    require(isinstance(domains, list) and len(domains) == DOMAINS,
            f"the scenario does not name exactly {DOMAINS} domains")
    binding = []
    for index, domain in enumerate(domains):
        label = f"domains[{index}]"
        known(domain, fields["domain"], label)
        require(number(domain.get("index"), f"{label}.index") == index,
                f"{label} is out of order")
        require(domain.get("name") == f"G{index}" and
                domain.get("prefix") == f"BE_MVP_G{index}: ",
                f"{label} is not named G{index} with prefix BE_MVP_G{index}: ")
        hart = number(domain.get("hart"), f"{label}.hart")
        require(hart != control and hart < harts,
                f"{label}.hart {hart} is the control hart or not on the "
                f"platform's {harts}")
        vmid = number(domain.get("vmid"), f"{label}.vmid")
        root = number(domain.get("root"), f"{label}.root")
        block = number(domain.get("block"), f"{label}.block")
        window = known(domain.get("window", {}), fields["window"],
                       f"{label}.window")
        gpa = number(window.get("gpa"), f"{label}.window.gpa")
        hpa = number(window.get("hpa"), f"{label}.window.hpa")
        size = number(window.get("bytes"), f"{label}.window.bytes")
        prefix = f"G{index}_"
        require(vmid == layout[prefix + "VMID"] and
                root == layout[prefix + "ROOT_HPA"] and
                block == layout[prefix + "BLOCK_HPA"],
                f"{label}'s VMID, root, or block is not the layout's")
        require(hgatp(vmid, root) == layout[prefix + "HGATP"],
                f"{label}'s hgatp is not the layout's")
        require(gpa == layout["GUEST_GPA"] and hpa == layout[prefix + "HPA"]
                and size == layout["GUEST_BYTES"],
                f"{label}'s window is not the layout's")
        # A v2 scenario's DTBs carry its roles' arguments, so they are its
        # own (gen-dts.py's naming of a variant DTB); check_v2() checks
        # their bootargs.
        dtb = f"mvp-guest-g{index}.dtb" if version == 1 else \
            f"mvp-guest-g{index}-{name}.dtb"
        require(domain.get("kernel") == "Image" and domain.get("dtb") == dtb,
                f"{label} does not name the pinned Image and its own DTB")
        require(version != 1 or
                domain.get("bootargs") == dts.guest_bootargs(index),
                f"{label}.bootargs differs from tools/gen-dts.py's, which "
                "the pinned DTBs carry")
        require(domain.get("program") == "/init",
                f"{label}.program is not /init")
        # M7 (planning/mvp-m7-plan.md, D-5): a configuration fact, stated.
        console = domain.get("console_input")
        require(isinstance(console, bool),
                f"{label}.console_input is not true or false")
        binding.append({"index": index, "hart": hart, "vmid": vmid,
                        "root": root, "hgatp": hgatp(vmid, root),
                        "block": block, "gpa": gpa, "hpa": hpa,
                        "bytes": size, "prefix": domain["prefix"],
                        "bootargs": domain.get("bootargs"),
                        "console_input": console})
    first, second = binding
    for key in ("hart", "vmid", "root", "block", "hpa"):
        require(first[key] != second[key],
                f"both domains share their {key}")
    expect = known(scenario.get("expect", {}), fields["expect"], "expect")
    # A v3 scenario's domain lines are its roles' (check_v3()).
    for key in ("domain_lines", "rejected", "exit_classes")[
            1 if version == 3 else 0:]:
        require(isinstance(expect.get(key), list) and expect[key] and
                all(isinstance(item, str) and item for item in expect[key]),
                f"expect.{key} is not a list of text")
    require(isinstance(expect.get("counters"), dict),
            "expect.counters is not an object")
    for counter, rule in expect["counters"].items():
        require(isinstance(rule, dict) and set(rule) in ({"exact"},
                                                         {"min", "max"}),
                f"counter {counter} is neither exact nor a range")
    concurrency = expect.get("concurrency", {})
    require(concurrency == {"overlap": "half-of-shorter", "alternations": 8},
            "expect.concurrency is not Q5's floors (half of the shorter "
            "interval, K = 8)")
    names = set()
    variant_keys = {1: VARIANT_KEYS, 2: VARIANT_KEYS_V2,
                    3: VARIANT_KEYS_V3}[version]
    for variant in scenario.get("variants", []):
        require(isinstance(variant, dict) and set(variant) <= variant_keys,
                f"variant {variant!r} has unknown keys")
        # A variant's name is an image name and a file name under expect/,
        # as the scenario's is: the scenario's grammar with an interior
        # dot, and not the scenario's own name (row F of the RC3 snapshot
        # reviews, 2026-11-01).
        require(isinstance(variant.get("name"), str) and
                re.fullmatch(VARIANT_NAME, variant["name"]) is not None,
                f"variant name {variant.get('name')!r} is not a short "
                "lower-case name")
        require(variant["name"] != name,
                f"variant {variant['name']} is named like the scenario")
        require(variant["name"] not in names,
                f"variant {variant['name']} appears twice")
        names.add(variant["name"])
        require(("fail" in variant) != bool(variant.get("pass")),
                f"variant {variant['name']} neither passes nor fails")
        require("fail" not in variant or variant["fail"] in CLASSES,
                f"variant {variant['name']} fails with an unknown class")
        require(set(variant.get("toolchains", ())) <= {"gcc", "clang"} and
                variant.get("toolchains"),
                f"variant {variant['name']} names no toolchain")
        # A v3 variant's run budget is the plan's (check_v3()).
        for key, constant in VARIANT_VALUES.items() if version < 3 else ():
            require(key not in variant or
                    number(variant[key], key) == layout[constant],
                    f"variant {variant['name']}'s {key} is not the layout's "
                    f"BE_MVP_{constant}")
        # M9's self-report-flip (planning/mvp-m9-plan.md, D-4): the one
        # variant that names a post-link mutation, one bit of the canary,
        # and its one finding; none where R2 is dropped (Q4).
        require(("mutate" in variant or "findings" in variant) ==
                (variant["name"] == SELF_REPORT_FLIP) and (
                    variant["name"] != SELF_REPORT_FLIP or LOG_R2 and
                    variant.get("pass") is True and
                    variant.get("mutate") == CANARY and
                    variant.get("findings") == [SELF_REPORT_FINDING]),
                f"variant {variant['name']} is not M9's self-report-flip, "
                "one bit of be_mvp_log_canary and its one finding")
        # A v2 variant's hart is the one its DETAIL names (check_v2()).
        if "hart" in variant and version == 1:
            require(number(variant["hart"], "hart") ==
                    layout["VARIANT_HART_START_HART"] and
                    variant.get("domain") == 1,
                    f"variant {variant['name']} does not name the layout's "
                    "absent hart for domain 1")
    # Q13: M0's platform record stands, so a v2 scenario has no probes.
    require(version == 1 or not scenario.get("probes"),
            "a v2 scenario declares no probe images (M1 plan, Q13)")
    for probe in scenario.get("probes", []):
        require(isinstance(probe, dict) and
                isinstance(probe.get("name"), str) and
                re.fullmatch(PROBE_NAME, probe["name"]),
                f"probe {probe!r} is not named probe-*")
        require(probe["name"] not in names and probe["name"] != name,
                f"probe {probe['name']} is named like another image")
        names.add(probe["name"])
        require(all(line in PROBE_LINES for line in probe.get("lines", ())),
                f"probe {probe['name']} names an unknown line")
    return binding


def policy_input(scenario_path, scenario, policy, negative=None):
    """A v2 scenario's policy (its .te file, beside it) and, for NEGATIVE,
    the scenario and policy of that build-time negative image (negatives/
    NEGATIVE.json, as tools/policy-check.py applies it)."""
    directory = pathlib.Path(scenario_path).parent
    name = scenario.get("policy")
    require(isinstance(name, str) and
            re.fullmatch(r"[a-z0-9][a-z0-9-]*\.te", name) is not None,
            "policy does not name a .te file beside the scenario")
    policy_bytes = (directory / name).read_bytes()
    if negative is not None:
        scenario, policy_bytes, _ = policy.negative(directory, negative,
                                                    scenario, policy_bytes)
    return scenario, policy_bytes


def policy_check(policy, scenario, policy_bytes, layout):
    """tools/policy-check.py's analyses, before anything else: the
    authority report, or why the configuration must not be sealed (security
    model v1, Part 4), in which case nothing is written."""
    try:
        report = policy.analyze(scenario, policy_bytes, layout)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise ScenarioError(f"the policy check refuses the scenario: "
                            f"{error}") from None
    problems = policy.problems(report)
    require(not problems, "the policy check fails, so no header: " +
            "; ".join(problems))
    return report


def denied_accesses(deny, label):
    """A domain's denied accesses, [(access, GPA)], in the init's order."""
    require(isinstance(deny, list) and all(
        isinstance(entry, dict) and set(entry) == {"access", "gpa"}
        for entry in deny), f"{label}.deny is not a list of access and gpa")
    for entry in deny:
        require(entry["access"] in CAUSES, f"{label}.deny names "
                f"{entry['access']!r}, not a load or a store (Q3)")
    return [(entry["access"], number(entry["gpa"], f"{label}.deny gpa"))
            for entry in deny]


def pte(hpa, flags):
    return (hpa >> 12) << 10 | flags


def check_v2(scenario, layout, dts, binding, report, policy):
    """M1's rules (planning/mvp-m1-plan.md, "Scenarios and the harness"),
    after the policy check: the sealed channel record, each domain's role,
    window rights, bootargs, and denials, the accepted exits, the expected
    denials and report, and the variants; return what the header and the
    expectations add to M0's."""
    expect = scenario["expect"]
    channels = scenario["channels"]
    require(len(channels) == 1 == layout.get("CHANNELS_MAX"),
            "the scenario does not declare exactly one channel, the "
            "layout's BE_MVP_CHANNELS_MAX")
    channel = channels[0]
    page = [item for item in scenario["objects"]
            if item["name"] == channel["object"]][0]
    record = {"gpa": number(channel["gpa"], "the channel's gpa"),
              "hpa": number(page["hpa"], "the channel page's hpa"),
              "bytes": number(page["bytes"], "the channel page's bytes")}
    require(record == Q1_CHANNEL and all(
        layout.get(f"CHANNEL_{key.upper()}") == value
        for key, value in Q1_CHANNEL.items()), "the channel page is not "
        "Q1's, which the layout's BE_MVP_CHANNEL_* name")
    indices = {domain["name"]: domain["index"]
               for domain in scenario["domains"]}
    ends = {role: indices.get(channel[role]) for role in CHANNEL_RIGHTS}
    for role, rights in CHANNEL_RIGHTS.items():
        require(channel[f"{role}_rights"] == rights,
                f"the channel's {role}_rights are not {' '.join(rights)}, "
                "which M1-2's channel check admits")
    require(all(f"G{index}_LEVEL0_HPA" in layout for index in range(DOMAINS)),
            "the layout names no level-0 page in each pool")
    # Each endpoint's leaf from the report's derived flags (map V U A, read
    # R, write W D): the flags the CHANNEL_CHECKED line shows.
    flags = {grant["subject"]: int(grant["derived"]["flags"], 16)
             for grant in report["grants"]
             if grant["object"] == page["name"] and
             grant["class"] == "memory"}
    leaves = {role: pte(record["hpa"], flags[channel[role]])
              for role in CHANNEL_RIGHTS}
    roles, denials, firsts = {}, {}, []
    templates = expect["domain_lines"]
    require(templates.count(BOOTARGS_TEMPLATE) == 1 and
            sum("<bootargs>" in text for text in templates) == 1 and
            sum(text.startswith("MVPINIT 02 ") for text in templates) == 1,
            f"expect.domain_lines does not hold one {BOOTARGS_TEMPLATE!r} "
            "and one MVPINIT 02 line")
    for domain, bound in zip(scenario["domains"], binding):
        index, label = bound["index"], f"domains[{bound['index']}]"
        ended = [name for name, end in ends.items() if end == index]
        require(len(ended) == 1, f"{label} is not one end of "
                f"{channel['name']}")
        role = roles[index] = ended[0]
        require(domain.get("role") == role,
                f"{label}.role is not {role}, its end of {channel['name']}")
        require(domain["window"].get("rights") == WINDOW_RIGHTS,
                f"{label}.window.rights are not read write execute (V4)")
        accesses = denied_accesses(domain.get("deny"), label)
        entries = denials[str(index)] = []
        for seq, (access, gpa) in enumerate(accesses, 1):
            where = f"{label}.deny[{seq - 1}]"
            # Doubleword-aligned, so the access lies in one page; below
            # 2^41, so htval = GPA >> 2 stays below 2^39 (Q4).
            require(gpa % 8 == 0 and gpa >> 2 < 1 << 39,
                    f"{where} is not a doubleword-aligned GPA below 2^41")
            require(not bound["gpa"] <= gpa < bound["gpa"] + bound["bytes"],
                    f"{where} is in its own window, which its root maps")
            on_page = record["gpa"] <= gpa < record["gpa"] + record["bytes"]
            require(not on_page or (access == "store" and role == "reader"),
                    f"{where} is an access the channel page grants")
            entries.append({"seq": seq, "access": access,
                            "kind": "read-only" if on_page else "unmapped",
                            "gpa": f"{gpa:#x}"})
        if entries:
            firsts.append({"domain": index, "hart": bound["hart"],
                           "cause": CAUSES[entries[0]["access"]],
                           "htval": f"{accesses[0][1] >> 2:#x}"})
        try:
            bootargs = dts.guest_bootargs(index, init=dts.role_arguments(
                role, record["gpa"], accesses))
        except ValueError as error:
            raise ScenarioError(f"{label}: {error}") from None
        require(domain.get("bootargs") == bootargs,
                f"{label}.bootargs differs from tools/gen-dts.py's, which "
                "the pinned DTBs carry")
    require(expect.get("denials") == denials, "expect.denials is not each "
            "domain's denied accesses, in order, with the kind the sealed "
            "record gives each")
    exits = expect["exit_classes"] + (["denial"] if firsts else [])
    require(scenario.get("accepted_exits") == exits, "accepted_exits is not "
            "M0's exit classes plus denial, the one denial entry (Q4)")
    require(expect.get("report") == {"grants": len(report["grants"]),
                                     "flows": report["flows"]},
            "expect.report is not the authority report's grants and flows")
    reader = ends["reader"]
    # reader-write: the builder writes W and D into the reader's leaf, so
    # the check walks the reader's flags with write's against its declared
    # leaf.
    widened = flags[channel["reader"]] | policy.FLAGS["write"]
    walked = {"fail": "gstage", "after": "BE_MVP:03", "detail": "channel",
              "domain": reader, "hart": binding[reader]["hart"],
              "walked": f"{pte(record['hpa'], widened):#x}",
              "declared": f"{leaves['reader']:#x}"}
    # no-inject: te-poc without the denial entry; either domain's first
    # denied access ends the run.
    unaccepted = {"fail": "guest-page-fault", "after": "BE_MVP:10",
                  "detail": "domain", "first_fault": firsts,
                  "accepted_exits": [name for name in exits
                                     if name != "denial"]}
    for variant in scenario.get("variants", []):
        if {"walked", "declared"} & set(variant):
            require({key: variant.get(key) for key in walked} == walked,
                    f"variant {variant['name']} is not the reader's leaf "
                    "with W and D refused against its declared leaf")
        if {"first_fault", "accepted_exits"} & set(variant):
            require(firsts and {key: variant.get(key) for key in unaccepted}
                    == unaccepted, f"variant {variant['name']} is not "
                    "te-poc without its denial entry, ended by either "
                    "domain's first denied access")
    return {"channel": dict(record, index=0, writer=ends["writer"],
                            reader=reader, writer_pte=leaves["writer"],
                            reader_pte=leaves["reader"],
                            level0=[layout[f"G{index}_LEVEL0_HPA"]
                                    for index in range(DOMAINS)],
                            config=report["identity"][
                                "configuration_identity"]),
            "roles": roles, "denials": denials, "accepted_exits": exits,
            "report": report,
            "config": report["identity"]["configuration_identity"]}


def management(grants, calls, checked=True):
    """Each domain's management calls (expect.mgmt, or a variant's) with
    the result each gets (planning/mvp-m2-plan.md, Q3, Q14, and "The
    management extension"): another FID is answered not supported on the
    requester's hart, without a request, so hart 0 has no entry for it;
    hart 0 decides the rest, one entry per request (a call's count
    repeats it), numbered per requester: an unknown target an invalid
    parameter, a call without the requester's grant for its function
    denied (when CHECKED), and a terminated target, or a pause of a
    paused one, an invalid state. Each domain's calls in order, domain
    0's first; a declared result the decision does not give is refused.
    Returns hart 0's entries and the domains' final states."""
    require(isinstance(calls, dict) and sorted(calls) == [
        str(index) for index in range(DOMAINS)] and all(
        isinstance(rows, list) for rows in calls.values()),
        "expect.mgmt is not each domain's management calls")
    allowed = {(grant["from"], grant["to"]): grant["permissions"]
               for grant in grants}
    states, out = ["running"] * DOMAINS, {}
    for domain in sorted(calls):
        rows = out[domain] = []
        for call in calls[domain]:
            require(isinstance(call, dict) and {"fid", "target", "result"}
                    <= set(call) <= {"fid", "target", "result", "count"}
                    and all(type(value) is int for value in call.values())
                    and call.get("count", 1) >= 1, f"management call "
                    f"{call!r} is not a FID, a target, a result, and a count")
            fid, target, name = call["fid"], call["target"], MGMT_FIDS.get(
                call["fid"])
            for _ in range(call.get("count", 1)):
                if name is None:
                    result = SBI_NOT_SUPPORTED
                elif not 0 <= target < DOMAINS:
                    result = SBI_INVALID_PARAM
                elif checked and name not in allowed.get(
                        (int(domain), target), ()):
                    result = SBI_DENIED
                elif states[target] == "terminated" or (
                        name == "pause" and states[target] == "paused"):
                    result = SBI_INVALID_STATE
                else:
                    result = SBI_SUCCESS
                    states[target] = {"pause": "paused",
                                      "terminate": "terminated"}[name]
                require(result == call["result"], f"domain {domain}'s call "
                        f"{name or fid} of {target} gets {result} " + (
                            "on its own hart, without a request" if name is
                            None else "from hart 0's decision") +
                        f" (Q3, Q14), not {call['result']}")
                if name is not None:
                    rows.append({"seq": len(rows) + 1, "fid": fid,
                                 "fid_name": name, "target": target,
                                 "result": result, "target_state":
                                 states[target] if result == SBI_SUCCESS
                                 else "-"})
    return out, states


def check_v3(scenario, layout, dts, binding, report, policy):
    """M2's rules (planning/mvp-m2-plan.md, "Scenarios and the harness"),
    after the policy check: the pages with the rights the page check
    admits and their leaves (Q1); one host and one protected domain, their
    window rights, bootargs, and denials; the secret (Q5); the measured
    domain, whose launch records end with the secret page (Q7, M9); the
    management calls against hart 0's decision (Q3, Q14); the requests and their HMAC-SHA-256 digests
    (Q6, Q8); the accepted exits; the expected report; and the four
    runtime negatives; return what the header and the expectations add to
    M0's."""
    expect, domains = scenario["expect"], scenario["domains"]
    roles = [domain.get("role") for domain in domains]
    require(sorted(map(str, roles)) == ["host", "prot"],
            "the domains' roles are not host and prot (Guest software)")
    host, prot = roles.index("host"), roles.index("prot")
    require(all(f"G{index}_LEVEL0_HPA" in layout for index in range(DOMAINS)),
            "the layout names no level-0 page in each pool")
    # Each leaf from the report's derived flags (map V U A, read R, write
    # W D), as the PAGE_CHECKED line shows it.
    flags = {(grant["subject"], grant["object"]): int(
        grant["derived"]["flags"], 16) for grant in report["grants"]
        if grant["derived"]}
    pages = []
    for page in scenario["pages"]:
        ends = {end: page[end] for end in ("writer", "reader") if end in page}
        rights = [PAGE_RIGHTS[page["kind"]].get(next(
            (end for end, at in ends.items() if at == index), ""), [])
            for index in range(DOMAINS)]
        require(page["rights"] == rights, f"pages[{page['index']}]'s rights "
                f"are not {rights}, which the page check admits (Q1)")
        hpa = number(page["hpa"], "a page's hpa")
        pages.append(dict(ends, index=page["index"], name=page["name"],
                          kind=page["kind"], gpa=number(page["gpa"], "a gpa"),
                          hpa=hpa, bytes=number(page["bytes"], "bytes"),
                          rights=rights, leaves=[pte(hpa, flags[(
                              domains[index]["name"], page["name"])])
                              if rights[index] else None
                              for index in range(DOMAINS)]))
    request, response, secret_page = ([page for page in pages if (
        page["kind"], page.get("writer")) == key] for key in (
        ("channel", host), ("channel", prot), ("secret", None)))
    require(len(request) == len(response) == len(secret_page) == 1 ==
            len(pages) - 2 and secret_page[0]["reader"] == prot,
            "the pages are not the host's request page, the protected "
            "domain's response page, and its secret page (Q1)")
    response, secret_page = response[0], secret_page[0]
    secret = scenario["secret"]
    require(isinstance(secret, dict) and set(secret) == {
        "page", "bytes", "hex"} and secret["page"] == secret_page["index"]
        and number(secret["bytes"], "secret.bytes") == SECRET_BYTES and
        re.fullmatch(r"[0-9a-f]{64}", str(secret["hex"])) is not None,
        "the secret is not Q5's 32 bytes in lower-case hex on the secret "
        "page")
    # The field stays M2's, with Q7's inputs (it is in the manifest
    # identity); since M9 it names the domain whose launch records end
    # with the secret page.
    require(scenario["measurement"] == {"domain": prot, "inputs": [
        "kernel", "dtb", "secret_page", "configuration_identity"]},
        "the measurement is not the protected domain's, over Q7's inputs "
        "in order")
    lines = expect.get("domain_lines")
    require(isinstance(lines, dict) and sorted(lines) == ["host", "prot"]
            and all(isinstance(own, list) and all(
                isinstance(text, str) and text for text in own) and
                own.count(BOOTARGS_TEMPLATE) == 1 and
                sum("<bootargs>" in text for text in own) == 1 and
                sum(text.startswith("MVPINIT 02 ") for text in own) == 1
                for own in lines.values()), "expect.domain_lines is not "
            f"each role's text, with one {BOOTARGS_TEMPLATE!r} and one "
            "MVPINIT 02 line")
    denials = {}
    for domain, bound in zip(domains, binding):
        index, label = bound["index"], f"domains[{bound['index']}]"
        require(domain["window"].get("rights") == WINDOW_RIGHTS,
                f"{label}.window.rights are not read write execute (V4)")
        accesses = denied_accesses(domain.get("deny"), label)
        entries = denials[str(index)] = []
        for seq, (access, gpa) in enumerate(accesses, 1):
            where = f"{label}.deny[{seq - 1}]"
            require(gpa % 8 == 0 and gpa >> 2 < 1 << 39,
                    f"{where} is not a doubleword-aligned GPA below 2^41")
            require(not bound["gpa"] <= gpa < bound["gpa"] + bound["bytes"],
                    f"{where} is in its own window, which its root maps")
            held = next((page["rights"][index] for page in pages
                         if page["gpa"] <= gpa < page["gpa"] + page["bytes"]),
                        [])
            require(not held or access == "store" and "write" not in held,
                    f"{where} is an access its page's leaf grants")
            entries.append({"seq": seq, "access": access, "kind":
                            "read-only" if held else "unmapped",
                            "gpa": f"{gpa:#x}"})
        try:
            bootargs = dts.guest_bootargs(index, init=dts.page_arguments(
                roles[index], [page["gpa"] for page in pages], accesses))
        except ValueError as error:
            raise ScenarioError(f"{label}: {error}") from None
        require(domain.get("bootargs") == bootargs,
                f"{label}.bootargs differs from tools/gen-dts.py's, which "
                "the pinned DTBs carry")
    require(expect.get("denials") == denials, "expect.denials is not each "
            "domain's denied accesses, in order, with the kind its leaves "
            "give each")
    exits = expect["exit_classes"] + ["denial", "mgmt"]
    require(scenario.get("accepted_exits") == exits, "accepted_exits is not "
            "M0's exit classes plus denial and mgmt, the denial and the "
            "management entries")
    grants = [dict(grant) for grant in scenario["grants"]]
    mgmt, _ = management(grants, expect.get("mgmt"))
    # A call another FID names is answered on its own hart, one of M0's
    # refused calls; the host is the domain that shuts down.
    local = sum(call.get("count", 1) for call in expect["mgmt"][str(host)]
                if call["fid"] not in MGMT_FIDS)
    require(expect["counters"].get("refused") == {"exact": local},
            f"expect.counters.refused is not exactly the host's {local} "
            "calls answered on its own hart")
    require([(entry["fid_name"], entry["target"]) for entry in mgmt[str(
        host)] if entry["result"] == SBI_SUCCESS] == [
        ("pause", prot), ("terminate", prot)] and not any(
        entry["result"] == SBI_SUCCESS for entry in mgmt[str(prot)]),
        "the host's granted calls are not a pause and then a termination "
        "of the protected domain, or a protected domain's call is granted")
    requests = expect.get("requests")
    require(isinstance(requests, list) and len(requests) > 1 and all(
        isinstance(item, dict) and set(item) - {"timeout"} == {
            "n", "message"} and item.get("timeout", True) is True and
        type(item["n"]) is int and re.fullmatch(
            r"[ -~]{1,64}", str(item["message"])) for item in requests) and [
        item["n"] for item in requests] == list(range(1, len(requests) + 1))
        and ["timeout" in item for item in requests] == [False] * (
            len(requests) - 1) + [True], "expect.requests is not n = 1, 2, "
        "..., each a printable message of at most 64 bytes, the last one "
        "unanswered (Q8)")
    key, messages = bytes.fromhex(secret["hex"]), []
    for item in requests:
        message = item["message"].encode("ascii").ljust(REQUEST_BYTES, b"\0")
        messages.append(dict(n=item["n"], message=item["message"],
                             message_hex=message.hex(), **({"timeout": True}
                             if item.get("timeout") else {"digest": hmac.new(
                                 key, item["n"].to_bytes(8, "little") +
                                 message, hashlib.sha256).hexdigest()})))
    managed = [{key: grant[key] for key in ("subject", "object",
                                            "permissions", "source")}
               for grant in report["grants"] if grant["class"] == "domain"]
    require(expect.get("report") == {"grants": len(report["grants"]),
                                     "flows": report["flows"],
                                     "management": managed},
            "expect.report is not the authority report's grants, flows, "
            "and management grants")
    # The plan's four runtime negatives, as this scenario gives them, and
    # M9's self-report-flip: secret-shared's and response-writable's walked
    # and declared leaves,
    # wrong-measurement's domain, and no-grant-check's budget, calls, and
    # the termination of the host they end in.
    hart = [bound["hart"] for bound in binding]
    expected = {
        "secret-shared": dict(
            fail="gstage", after="BE_MVP:03", detail="page",
            page=secret_page["index"], domain=host, hart=hart[host],
            walked=f"{secret_page['leaves'][prot]:#x}", declared="0x0"),
        "response-writable": dict(
            fail="gstage", after="BE_MVP:03", detail="page",
            page=response["index"], domain=host, hart=hart[host],
            walked=f"{response['leaves'][host] | policy.FLAGS['write']:#x}",
            declared=f"{response['leaves'][host]:#x}"),
        "wrong-measurement": dict(fail="measurement", after="BE_MVP:19",
                                  detail="measurement", domain=prot,
                                  hart=hart[prot]),
        "no-grant-check": dict(fail="run-timeout", after="BE_MVP:10",
                               detail="ticks",
                               run_budget_ticks=MGMT_RUN_BUDGET,
                               terminated={"domain": host, "by": prot})}
    # M9's self-report-flip (planning/mvp-m9-plan.md, D-4), while the image
    # logs R2 (Q4): a complete run of anchor's image with one bit of the
    # canary flipped, and its one finding.
    if LOG_R2:
        expected[SELF_REPORT_FLIP] = {"pass": True, "mutate": CANARY,
                                      "findings": [SELF_REPORT_FINDING]}
    variants = [variant for variant in scenario.get("variants", [])
                if variant not in console_variants(scenario)]
    require(sorted(variant["name"] for variant in variants) == sorted(
        expected), f"the variants are not the plan's {sorted(expected)}")
    unchecked = None
    for variant in variants:
        name, got = variant["name"], dict(variant)
        if "run_budget_ticks" in got:
            got["run_budget_ticks"] = number(got["run_budget_ticks"],
                                             "run_budget_ticks")
        wanted = expected[name]
        require({key: got.get(key) for key in wanted} == wanted and set(
            got) - set(wanted) - {"name", "toolchains", "where", "change"}
            == ({"mgmt"} if name == "no-grant-check" else set()),
            f"variant {name} is not the plan's, as {wanted}")
        if name == "no-grant-check":
            unchecked, states = management(grants, variant["mgmt"], False)
            require(variant["mgmt"][str(host)] == [] and [
                {key: call[key] for key in call if key != "result"}
                for call in variant["mgmt"][str(prot)]] == [
                {key: call[key] for key in call if key != "result"}
                for call in expect["mgmt"][str(prot)]] and states[host] ==
                "terminated", "variant no-grant-check's calls are not the "
                "protected domain's, ending the host, with none of its own")
    return {"pages": pages, "roles": roles, "host": host, "prot": prot,
            "denials": denials, "accepted_exits": exits, "report": report,
            "config": report["identity"]["configuration_identity"],
            "secret": secret["hex"], "secret_page": secret_page,
            "mgmt": mgmt, "calls": expect["mgmt"], "requests": messages,
            "grants": grants, "unchecked": unchecked,
            "level0": [layout[f"G{index}_LEVEL0_HPA"]
                       for index in range(DOMAINS)]}


def seal(scenario, policy_bytes, layout, dts, policy):
    """For a v2 or v3 scenario the policy check first, then every rule:
    the binding, and what a v2 or v3 scenario adds (None for v1)."""
    version = version_of(scenario)
    if version == 1:
        binding = check(scenario, layout, dts)
        check_console(scenario, binding, layout, dts, version)
        return binding, None
    require(policy is not None, "a v2 scenario needs --policy-tool, "
            "tools/policy-check.py")
    report = policy_check(policy, scenario, policy_bytes, layout)
    binding = check(scenario, layout, dts)
    sealed = check_v2(scenario, layout, dts, binding, report, policy) \
        if version == 2 else check_v3(scenario, layout, dts, binding, report,
                                      policy)
    # M7-4's console variants, after every rule of the scenario's own.
    check_console(scenario, binding, layout, dts, version)
    # The MVP core profile, which must be the report's (stop condition 11).
    sealed["core"] = core_config(policy, scenario, binding, layout)
    core_agrees(report, sealed["core"])
    return binding, sealed


def core_config(policy, scenario, binding, layout):
    """BINDING's MVP core profile (tools/policy-check.py's core()): the
    layout's extents, each domain's binding and window, and a v2 or v3
    manifest's pages."""
    pages = policy.core_inputs(scenario, policy.manifest(scenario))[1] \
        if version_of(scenario) > 1 else []
    return policy.core([dict(domain, rights=WINDOW_RIGHTS)
                        for domain in binding], pages, layout)


def core_agrees(report, core):
    """The report's memory grants are the proposal's authorities exactly,
    and its memory objects the inventory's resources, each object tiled by
    the resources inside it, each resource in one object and owned
    (planning/mvp-m6-plan.md, D-1; stop condition 11)."""
    require(core["identity"] == report["identity"].get("core_identity"),
            "the authority report's core identity is not the proposal's")
    extents = {o["name"]: tuple(int(o["extent"][key], 16) for key in (
        "base", "size")) for o in report["objects"] if o["class"] == "memory"}
    resources = {row[0]: (row[1], row[2]) for row in core["resources"]}
    granted = sorted((int(g["subject"][1:]) + 1, int(g["derived"]["gpa"], 16),
                      extents.get(g["object"]), sum(RIGHT_BITS[perm] for perm
                                                    in g["permissions"] if
                                                    perm != "map"))
                     for g in report["grants"] if g["derived"])
    authorities = sorted((row[0], row[1], resources.get(row[2]), row[3])
                         for row in core["authorities"])
    require(granted == authorities, f"the report's grants {granted} are not "
            f"the proposal's authorities {authorities}")
    for name, (base, size) in extents.items():
        inside = sorted(extent for extent in resources.values()
                        if base <= extent[0] < base + size)
        require(inside and inside[0][0] == base and all(
            first[0] + first[1] == second[0] for first, second in zip(
                inside, inside[1:])) and sum(extent[1] for extent in inside)
            == size, f"{name} is not tiled by the inventory's resources")
    require(all(any(base <= extent[0] < base + size for base, size in
                    extents.values()) for extent in resources.values()),
            "a resource lies in no object of the authority report")
    require(all(row[3] <= 5 or row[4] or any(channel[3] == row[0] for channel
                                              in core["channels"])
                for row in core["requests"]),
            "a resource has no owner: neither the monitor's, a domain's, "
            "nor a channel's")


def sealed_line(core):
    """BE_MVP:00 CONFIG_SEALED for CORE (src/mvp-runtime.c's seal_config()):
    its counts, its harts, and its identity's first 16 hex digits."""
    return (f"BE_MVP:00 CONFIG_SEALED inventory={len(core['resources'])} "
            f"authorities={len(core['authorities'])} "
            f"roots={len(core['domains'])} harts="
            f"{','.join(str(hart) for hart in core['harts'])} "
            f"identity={core['identity'][:16]}")


def config_source(name, digest, core, variants, console, consoles=()):
    """CONFIG_FILE: CORE's inventory and proposal as initializers, and its
    identity; VARIANTS, [(macro, its core)], name a domain's other hart
    under the macro, as the hart-start variant does; CONSOLE, each
    domain's console input grant, ends its request (M7, D-5), and
    CONSOLES, [(macro, each domain's grant)], name a console variant's
    grants under its macro (M7-4), which the grant's identity does not
    cover (src/mvp-core.c)."""
    def rights(bits):
        return " | ".join(f"BE_RIGHT_{right}" for right, bit in (
            ("READ", 1), ("WRITE", 2), ("EXECUTE", 4)) if bits & bit)

    lines = [
        "// SPDX-License-Identifier: GPL-3.0-only",
        "/*",
        " * Generated by mvp/tools/gen-scenario.py; do not edit.",
        f" * Scenario {name}, scenario.json sha256 {digest}:",
        " * the MVP core profile's inventory and proposal",
        " * (planning/mvp-m6-plan.md, D-1), which hart 0 copies, validates,",
        " * seals, and derives at boot (src/mvp-core.h).",
        " */",
        '#include "mvp-core.h"', ""]
    branch = "#if"
    for macro, other in variants:
        lines.append(f"{branch} defined({macro})")
        lines += [f"#define BE_MVP_CORE_DOMAIN{index}_HART\t{hart}U"
                  for index, hart in enumerate(other["harts"][1:])]
        lines.append("#define BE_MVP_CORE_IDENTITY_HEX\t"
                     f'"{other["identity"]}"')
        branch = "#elif"
    lines += ["#else"] if variants else []
    lines += [f"#define BE_MVP_CORE_DOMAIN{index}_HART\t{hart}U"
              for index, hart in enumerate(core["harts"][1:])] + [
        f'#define BE_MVP_CORE_IDENTITY_HEX\t"{core["identity"]}"']
    lines += ["#endif"] if variants else []
    branch = "#if"
    for macro, grants in consoles:
        lines.append(f"{branch} defined({macro})")
        lines += [f"#define BE_MVP_CORE_DOMAIN{index}_CONSOLE\t"
                  f"{int(grant)}U" for index, grant in enumerate(grants)]
        branch = "#elif"
    if consoles:
        lines += ["#else"] + [
            f"#define BE_MVP_CORE_DOMAIN{index}_CONSOLE\t{int(grant)}U"
            for index, grant in enumerate(console)] + ["#endif"]
    lines += [
        "", "const struct be_platform_inventory be_mvp_inventory = {",
        "\t.configuration_version = BE_CONFIGURATION_VERSION,",
        "\t.architecture = BE_ARCH_RISCV64,",
        "\t.profile = BE_PROFILE_MVP_CORE,",
        f"\t.hart_id = {core['harts'][0]}U,",
        f"\t.hart_count = {core['hart_count']}U,",
        f"\t.resource_count = {len(core['resources'])}U,",
        "\t.resources = {"] + [
        f"\t\t{{ {ident}U, BE_U64_C(0x{base:x}), BE_U64_C(0x{size:x}), "
        f"BE_RESOURCE_{KINDS[kind - 1]} }}, /* {label} */"
        for (ident, base, size, kind), label in zip(core["resources"],
                                                   core["names"])] + [
        "\t},", "};", "",
        "const struct be_proposal be_mvp_proposal = {",
        f"\t.proposal_id = BE_U64_C(0x{core['proposal_id']:x}),",
        "\t.source_vocabulary = BE_VOCABULARY_A,",
        f"\t.domain_count = {len(core['domains'])}U,", "\t.domains = {"] + [
        f"\t\t{{ BE_DOMAIN_{DOMAIN_IDS[row[0]]}, "
        + ", ".join(f"{value}U" for value in row[1:8]) +
        f", BE_MVP_CORE_DOMAIN{index}_HART, " + (
            f"BE_MVP_CORE_DOMAIN{index}_CONSOLE" if consoles else
            f"{int(console[index])}U") + " },"
        for index, row in enumerate(core["domains"])] + [
        "\t},", f"\t.resource_count = {len(core['requests'])}U,",
        "\t.resources = {"] + [
        f"\t\t{{ {ident}U, BE_U64_C(0x{base:x}), BE_U64_C(0x{size:x}), "
        f"BE_FRAME_{FRAMES[frame - 1]}, BE_DOMAIN_{DOMAIN_IDS[owner]} }},"
        for ident, base, size, frame, owner in core["requests"]] + [
        "\t},", f"\t.authority_count = {len(core['authorities'])}U,",
        "\t.authorities = {"] + [
        f"\t\t{{ BE_DOMAIN_{DOMAIN_IDS[domain]}, BE_U64_C(0x{gpa:x}), "
        f"{ident}U, {rights(bits)} }},"
        for domain, gpa, ident, bits in core["authorities"]] + [
        "\t},", f"\t.channel_count = {len(core['channels'])}U,"] + [
        "\t.channels = {"] * bool(core["channels"]) + [
        f"\t\t{{ {ident}U, BE_DOMAIN_{DOMAIN_IDS[source]}, "
        f"BE_DOMAIN_{DOMAIN_IDS[target]}, {resource}U, {rights(first)}, "
        f"{rights(second)} }},"
        for ident, source, target, resource, first, second in
        core["channels"]] + ["\t},"] * bool(core["channels"]) + ["};"]
    mappings = max(sum(1 for row in core["authorities"] if row[0] == domain)
                   for domain in range(1, len(DOMAIN_IDS)))
    limits = [(len(core["resources"]), "RESOURCES"),
              (len(core["requests"]), "RESOURCES"),
              (len(core["authorities"]), "AUTHORITIES"),
              (len(core["channels"]), "CHANNELS"),
              (len(core["domains"]), "DOMAINS"),
              (len(core["domains"]), "ROOTS"), (mappings, "MAPPINGS"),
              (len(core["harts"]), "HARTS")]
    lines += ["", "_Static_assert(" + " &&\n\t       ".join(
        f"{count}U <= BE_MAX_{name}" for count, name in limits if count) +
        ",\n\t       \"the MVP core profile's limits hold the "
        "configuration\");"]
    return "\n".join(lines) + "\n"


def regex(template, placeholders=None):
    """The template as a full-line regular expression; PLACEHOLDERS, the
    line's own (default PLACEHOLDERS)."""
    placeholders = placeholders or PLACEHOLDERS
    out = ""
    for part in re.split(r"(<[A-Za-z]>)", template):
        out += placeholders[part] if part in placeholders else \
            re.escape(part)
    return "^" + out + "$"


def line(template, placeholders=None):
    return {"template": template, "regex": regex(template, placeholders)}


def control_lines(name, binding, layout, outbound, budget, time="0",
                  channel=None, extra=None, refused="0", spv="1", core=None):
    """The control-hart lines before and after the domains' lines, from the
    MVP's boot (planning/mvp-m6-plan.md, D-3: BOOT_VALIDATED, then CORE's
    CONFIG_SEALED, sealed_line()); TIME is
    each BE_MVP:12's time field (<N> where SBI TIME is the guests'), and
    REFUSED its refused field (a v3 scenario's expected count: the host's
    call of another management FID, M2 plan, Q9); SPV is each BE_MVP:11's
    spv field, M0's 1, or SPV for an image with the management extension
    (Plan revision M2-A.1). A CHANNEL adds its two lines (M1 plan,
    Markers): CHANNEL_CHECKED after the roots' BE_MVP:03 lines,
    CHANNEL_CLEARED after the windows' :05. EXTRA ({"03": [...], "05":
    [...], "06": [...]}) adds a v3 scenario's page, secret, and
    measurement lines after each group's (M2 plan, Markers)."""
    extra = extra or {}
    harts = ",".join(str(hart) for hart in [0] +
                     [domain["hart"] for domain in binding])
    # Both domain harts STOPPED; any other hart STOPPED or the start rule's
    # boot hart, STARTED (Plan revision M0-A.2).
    domain_harts = {domain["hart"] for domain in binding}
    status = ",".join(f"{hart}:{HSM_STOPPED}" if hart in domain_harts else
                      f"{hart}:<H>" for hart in range(1, layout["HARTS"]))
    before = [
        f"BE_K3_B3: SHIM hart=0x{0:016x} "
        f"shim=0x{layout['STAGING_HPA']:016x} fdt=0x<f> "
        f"dest=0x{layout['MONITOR_HPA']:016x} "
        f"bytes=0x{layout['IMAGE_BYTES']:016x}",
        "BE_MVP:00 BOOT_VALIDATED", sealed_line(core),
        f"BE_MVP:01 SCENARIO name={name} domains={len(binding)} "
        f"harts={harts} of={layout['HARTS']} ring_bytes=0x{outbound:x} "
        f"mvp_region=0x{layout['REGION_HPA']:x} "
        f"mvp_bytes=0x{layout['REGION_BYTES']:x} "
        f"image_bytes=0x{layout['IMAGE_BYTES']:x}",
        f"BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status={status} "
        "started=<W>",
    ]
    for domain in binding:
        before.append(
            f"BE_MVP:03 GSTAGE_BUILT_REWALKED domain={domain['index']} "
            f"hart={domain['hart']} gpa=0x{domain['gpa']:x} "
            f"hpa=0x{domain['hpa']:x} size=0x{domain['bytes']:x} "
            f"leaves={layout['GUEST_LEAVES']} root=0x{domain['root']:x} "
            f"vmid={domain['vmid']}")
    if channel:
        before.append(
            f"BE_MVP:03 CHANNEL_CHECKED channel={channel['index']} "
            f"writer={channel['writer']} reader={channel['reader']} "
            f"gpa=0x{channel['gpa']:x} hpa=0x{channel['hpa']:x} "
            f"bytes=0x{channel['bytes']:x} level0="
            + ",".join(f"0x{page:x}" for page in channel["level0"]) +
            f" writer_pte=0x{channel['writer_pte']:x} "
            f"reader_pte=0x{channel['reader_pte']:x} "
            f"config={channel['config']}")
    before += extra.get("03", [])
    before.append("BE_MVP:04 PAYLOAD_CHECKED kernel_bytes=<K> "
                  "image_size=<S>")
    for domain in binding:
        before.append(f"BE_MVP:05 DOMAIN_RAM_CLEARED "
                      f"domain={domain['index']} gpa=0x{domain['gpa']:x} "
                      f"size=0x{domain['bytes']:x} ticks=<T>")
    if channel:
        before.append(f"BE_MVP:05 CHANNEL_CLEARED channel={channel['index']} "
                      f"hpa=0x{channel['hpa']:x} "
                      f"bytes=0x{channel['bytes']:x} ticks=<T>")
    before += extra.get("05", [])
    for domain in binding:
        before.append(f"BE_MVP:06 PAYLOAD_PLACED domain={domain['index']} "
                      f"kernel=0x{layout['KERNEL_GPA']:x} kernel_bytes=<K> "
                      f"image_size=<S> dtb=0x{layout['DTB_GPA']:x} "
                      f"dtb_bytes=0x{layout['DTB_BYTES']:x} ticks=<T>")
    before += extra.get("06", [])
    before.append(f"BE_MVP:07 BLOCKS_PUBLISHED "
                  f"region=0x{layout['HART_REGION_HPA']:x} "
                  f"bytes=0x{layout['HART_REGION_BYTES']:x} "
                  f"generation={layout['GENERATION']} "
                  f"budget_ticks=0x{budget:x}")
    for domain in binding:
        before.append(f"BE_MVP:08 HART_STARTED hart={domain['hart']} "
                      f"domain={domain['index']} result=0 status=0 "
                      "ticks=<T>")
    for domain in binding:
        before.append(f"BE_MVP:09 HART_READY hart={domain['hart']} "
                      f"domain={domain['index']} "
                      f"hgatp=0x{domain['hgatp']:x} hstatus_controls=0x180 "
                      "hedeleg=<h> hideleg=0x40 hcounteren=0x2 sie=0x2 "
                      # beryllium-cheri: the monitor variant's.
                      f"henvcfg={ARMED_HENVCFG[MONITOR]} "
                      "vstimecmp=0xffffffffffffffff")
    for domain in binding:
        before.append(f"BE_MVP:10 DOMAIN_ENTERED hart={domain['hart']} "
                      f"domain={domain['index']} "
                      f"pc=0x{layout['KERNEL_GPA']:x} a0=0x0 "
                      f"a1=0x{layout['DTB_GPA']:x} ticks=<T>")
    per_domain = {}
    for domain in binding:
        per_domain[str(domain["index"])] = [line(
            f"BE_MVP:11 IPI_PROBE hart={domain['hart']} "
            f"domain={domain['index']} sent=<T> received=<T> answered=<T> "
            f"spv={spv}", SPV_PLACEHOLDERS), line(
            f"BE_MVP:12 DOMAIN_SHUTDOWN hart={domain['hart']} "
            f"domain={domain['index']} exits=<N> sbi=<N> ipi=1 base=<N> "
            f"time={time} dbcn_write=<N> dbcn_read=<N> dbcn_byte=0 srst=1 "
            f"refused={refused} lines=<N> ring_peak=<B> entered=<T> "
            "ticks=<T>")]
    after = [f"BE_MVP:13 RUN_COMPLETE domains={len(binding)} records=<N> "
             "wakes=<N> idle_ticks=<T> overlap_ticks=<T> ticks=<T>",
             "BE_MVP:14 SHUTDOWN type=0 reason=0"]
    return ([line(text) for text in before], per_domain,
            [line(text) for text in after])


def probe_lines(probe, layout):
    status = ",".join(f"{hart}:<N>" for hart in range(1, layout["HARTS"]))
    counters = {}
    out = []
    for kind in probe["lines"]:
        template = PROBE_LINES[kind]
        if kind == "hsm":
            template = template.format(status=status)
        elif kind == "gpf":
            template = template.format(
                access=PROBE_ARGUMENTS[kind][counters.get(kind, 0)])
        elif kind in ("ipi", "order"):
            template = template.format(
                mode=PROBE_ARGUMENTS[kind][counters.get(kind, 0)])
        elif kind == "vmid":
            template = template.format(
                mode=probe["name"].rsplit("-", 1)[1])
        counters[kind] = counters.get(kind, 0) + 1
        out.append(line(template))
    out.append(line("BE_MVP:14 SHUTDOWN type=0 reason=0"))
    return out


def probe_control_lines(probe, binding, layout, core):
    """A probe image's whole control-hart sequence before BE_MVP:14, as
    src/mvp-runtime.c prints it: the scenario's prelude with domain 0 alone
    started (its hart the only domain hart BE_MVP:02 holds STOPPED), no
    payload lines, the stub entered with a1 = 0, and the probe's lines in
    place: hsm after BE_MVP:02, hgatp after both roots, the rest after the
    stub's entry."""
    scenario, _, _ = control_lines(probe["name"], binding, layout,
                                   layout["OUTBOUND_RING_BYTES"],
                                   layout["RUN_BUDGET"], core=core)
    first = binding[0]
    status = ",".join(f"{hart}:{HSM_STOPPED}" if hart == first["hart"] else
                      f"{hart}:<H>" for hart in range(1, layout["HARTS"]))
    probes = probe_lines(probe, layout)[:-1]
    placed = {"hsm": [], "hgatp": [], "run": []}
    for kind, entry in zip(probe["lines"], probes):
        placed[kind if kind in ("hsm", "hgatp") else "run"].append(entry)
    out = []
    for entry in scenario:
        tag = entry["template"].split(" ", 1)[0]
        text = entry["template"]
        if tag in ("BE_MVP:04", "BE_MVP:06") or (
                tag in ("BE_MVP:08", "BE_MVP:09", "BE_MVP:10") and
                f" domain={first['index']} " not in text):
            continue
        if tag == "BE_MVP:01":
            text = (f"BE_MVP:01 SCENARIO name={probe['name']} domains=1 "
                    f"harts=0,{first['hart']} of={layout['HARTS']} "
                    + text.split(f" of={layout['HARTS']} ", 1)[1])
        elif tag == "BE_MVP:02":
            text = (f"BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status={status} "
                    "started=<W>")
        elif tag == "BE_MVP:10":
            text = text.replace(f" a1=0x{layout['DTB_GPA']:x} ", " a1=0x0 ")
        out.append(line(text))
        if tag == "BE_MVP:02":
            out += placed["hsm"]
        elif tag == "BE_MVP:03" and f" domain={binding[-1]['index']} " in text:
            out += placed["hgatp"]
    return out + placed["run"]


def channel_header(sealed):
    """The header's channel record, accepted-exit set, and configuration
    identity (defines, static assertions): none for a v1 scenario, whose
    header differs from M0's only by declaring no channel and no denial
    entry (M1 plan, Scenarios and the harness)."""
    if sealed is None:
        return [
            "/* No channel and no denial entry: M0's accepted exits. */",
            "#define BE_MVP_SCENARIO_CHANNELS\tBE_MVP_C(0)",
            "#define BE_MVP_SCENARIO_CHANNEL_INITIALIZER\t"
            "{ 0, 0, 0, 0, 0, 0, 0 }",
            "#define BE_MVP_SCENARIO_ACCEPT_DENIAL\tBE_MVP_C(0)",
            "",
        ], []
    channel, identity = sealed["channel"], sealed["channel"]["config"]
    rights = {"read": "BE_MVP_GSTAGE_RIGHT_READ",
              "write": "BE_MVP_GSTAGE_RIGHT_WRITE"}
    octets = [f"0x{octet:02x}" for octet in bytes.fromhex(identity)]
    prefix = "#define BE_MVP_SCENARIO_CHANNEL0_"
    defines = [
        "/*",
        " * The sealed channel record, in struct be_mvp_gstage_channel's",
        " * order, its rights mvp-gstage.h's BE_MVP_GSTAGE_RIGHT_*; the",
        " * accepted-exit set, M0's plus the denial entry; and the",
        " * configuration identity, the SHA-256 of the authority report's",
        " * manifest, policy, and labeling identities (not a measurement),",
        " * which tools/policy-check.py computed before this header.",
        " */",
        "#define BE_MVP_SCENARIO_CHANNELS\tBE_MVP_C(1)",
        f"{prefix}GPA\tBE_MVP_C(0x{channel['gpa']:x})",
        f"{prefix}HPA\tBE_MVP_C(0x{channel['hpa']:x})",
        f"{prefix}BYTES\tBE_MVP_C(0x{channel['bytes']:x})",
        f"{prefix}WRITER\tBE_MVP_C({channel['writer']})",
        f"{prefix}READER\tBE_MVP_C({channel['reader']})",
        f"{prefix}WRITER_RIGHTS \\",
        "\t(" + " | ".join(rights[right] for right in
                           CHANNEL_RIGHTS["writer"]) + ")",
        f"{prefix}READER_RIGHTS \\",
        "\t(" + " | ".join(rights[right] for right in
                           CHANNEL_RIGHTS["reader"]) + ")",
        "#define BE_MVP_SCENARIO_CHANNEL_INITIALIZER { \\",
        "\tBE_MVP_SCENARIO_CHANNEL0_GPA, BE_MVP_SCENARIO_CHANNEL0_HPA, \\",
        "\tBE_MVP_SCENARIO_CHANNEL0_BYTES, "
        "BE_MVP_SCENARIO_CHANNEL0_WRITER, \\",
        "\tBE_MVP_SCENARIO_CHANNEL0_READER, \\",
        "\tBE_MVP_SCENARIO_CHANNEL0_WRITER_RIGHTS, \\",
        "\tBE_MVP_SCENARIO_CHANNEL0_READER_RIGHTS, \\",
        "}",
        "#define BE_MVP_SCENARIO_ACCEPT_DENIAL\tBE_MVP_C("
        f"{int('denial' in sealed['accepted_exits'])})",
        "#define BE_MVP_SCENARIO_CONFIG_IDENTITY_HEX \\",
        f'\t"{identity}"',
        "#define BE_MVP_SCENARIO_CONFIG_IDENTITY { \\",
    ] + ["\t" + ", ".join(octets[start:start + 8]) + ", \\"
         for start in range(0, len(octets), 8)] + ["}", ""]
    asserts = [
        "_Static_assert(BE_MVP_SCENARIO_CHANNELS <= BE_MVP_CHANNELS_MAX &&",
        "\t       BE_MVP_SCENARIO_CHANNEL0_GPA == BE_MVP_CHANNEL_GPA &&",
        "\t       BE_MVP_SCENARIO_CHANNEL0_HPA == BE_MVP_CHANNEL_HPA &&",
        "\t       BE_MVP_SCENARIO_CHANNEL0_BYTES == BE_MVP_CHANNEL_BYTES,",
        '\t       "the scenario\'s channel page is the layout\'s");',
        "_Static_assert(BE_MVP_SCENARIO_CHANNEL0_WRITER < BE_MVP_DOMAINS &&",
        "\t       BE_MVP_SCENARIO_CHANNEL0_READER < BE_MVP_DOMAINS &&",
        "\t       BE_MVP_SCENARIO_CHANNEL0_WRITER !=",
        "\t       BE_MVP_SCENARIO_CHANNEL0_READER,",
        '\t       "the channel joins the scenario\'s two domains");',
    ]
    return defines, asserts


def octet_lines(name, text):
    """A 32-byte value's initializer, eight octets a line, as v2's
    configuration identity's."""
    octets = [f"0x{octet:02x}" for octet in bytes.fromhex(text)]
    return [f"#define {name} {{ \\"] + [
        "\t" + ", ".join(octets[start:start + 8]) + ", \\"
        for start in range(0, len(octets), 8)] + ["}"]


def pages_header(sealed):
    """A v3 header's sealed pages, secret, measurement, management grants,
    accepted exits, and configuration identity (defines, static
    assertions), by the names M2-2 and M2-3 read (planning/mvp-m2-plan.md,
    Work packages): BE_MVP_PAGE_CHANNEL, BE_MVP_PAGE_SECRET,
    BE_MVP_PAGE_NONE, BE_MVP_MGMT_PAUSE, and BE_MVP_MGMT_TERMINATE are
    theirs; the assertions use the layout's names alone."""
    rights = {"read": "BE_MVP_GSTAGE_RIGHT_READ",
              "write": "BE_MVP_GSTAGE_RIGHT_WRITE"}
    pages, grants = sealed["pages"], sealed["grants"]
    defines = [
        "/*",
        " * The sealed pages (planning/mvp-m2-plan.md, Q1), each in the page",
        " * record's order: GPA, HPA, bytes, kind (BE_MVP_PAGE_*), writer",
        " * (BE_MVP_PAGE_NONE for the secret page), reader, and each",
        " * domain's rights (mvp-gstage.h's BE_MVP_GSTAGE_RIGHT_*); the",
        " * secret page and the 32-byte test secret, public by design (Q5);",
        " * the measured domain, whose launch records end with the secret",
        " * page (Q7; M9's log, mvp/docs/log-profile.md, whose constants",
        " * follow); the management grants (BE_MVP_MGMT_*, Q3); the",
        " * accepted-exit set, M0's plus the denial and management entries;",
        " * and the configuration identity, which tools/policy-check.py",
        " * computed before this header.",
        " */",
        f"#define BE_MVP_SCENARIO_PAGES\t\tBE_MVP_C({len(pages)})"]
    asserts = []
    initializer = ["#define BE_MVP_SCENARIO_PAGE_INITIALIZER { \\"]
    for page in pages:
        name = f"BE_MVP_SCENARIO_PAGE{page['index']}_"
        offset = f" + BE_MVP_C(0x{page['index'] * 0x1000:x})" if page[
            "index"] else ""
        defines += [
            f"#define {name}GPA\tBE_MVP_C(0x{page['gpa']:x})",
            f"#define {name}HPA\tBE_MVP_C(0x{page['hpa']:x})",
            f"#define {name}BYTES\tBE_MVP_C(0x{page['bytes']:x})",
            f"#define {name}KIND\tBE_MVP_PAGE_{page['kind'].upper()}",
            f"#define {name}WRITER\t" + (f"BE_MVP_C({page['writer']})"
                                         if "writer" in page else
                                         "BE_MVP_PAGE_NONE"),
            f"#define {name}READER\tBE_MVP_C({page['reader']})"]
        for index, held in enumerate(page["rights"]):
            value = " | ".join(rights[right] for right in held)
            defines += [f"#define {name}DOMAIN{index}_RIGHTS \\",
                        f"\t({value})"] if len(held) > 1 else [
                f"#define {name}DOMAIN{index}_RIGHTS " +
                (f"({value})" if held else "BE_MVP_C(0)")]
        initializer += [
            f"\t{{ {name}GPA, {name}HPA, \\",
            f"\t  {name}BYTES, {name}KIND, \\",
            f"\t  {name}WRITER, {name}READER, \\",
            f"\t  {{ {name}DOMAIN0_RIGHTS, \\",
            f"\t    {name}DOMAIN1_RIGHTS }} }}, \\"]
        asserts += [
            f"_Static_assert({name}GPA ==",
            f"\t       BE_MVP_CHANNEL_GPA{offset} &&",
            f"\t       {name}HPA ==",
            f"\t       BE_MVP_CHANNEL_HPA{offset} &&",
            f"\t       {name}BYTES == BE_MVP_CHANNEL_BYTES &&"] + ([
                f"\t       {name}WRITER < BE_MVP_DOMAINS &&",
                f"\t       {name}WRITER != {name}READER &&"]
                if "writer" in page else []) + [
            f"\t       {name}READER < BE_MVP_DOMAINS,",
            f"\t       \"page {page['index']} is Q1's page {page['index']}, "
            "of the scenario's domains\");"]
    secret_page = sealed["secret_page"]["index"]
    defines += initializer + [
        "}",
        f"#define BE_MVP_SCENARIO_SECRET_PAGE\tBE_MVP_C({secret_page})",
        "#define BE_MVP_SCENARIO_SECRET_HEX \\",
        f'\t"{sealed["secret"]}"'] + octet_lines(
        "BE_MVP_SCENARIO_SECRET", sealed["secret"]) + [
        f"#define BE_MVP_SCENARIO_MEASURED_DOMAIN\tBE_MVP_C({sealed['prot']})",
        f"#define BE_MVP_SCENARIO_GRANTS\t\tBE_MVP_C({len(grants)})"]
    initializer = ["#define BE_MVP_SCENARIO_GRANT_INITIALIZER { \\"]
    for index, grant in enumerate(grants):
        name = f"BE_MVP_SCENARIO_GRANT{index}_"
        defines += [
            f"#define {name}FROM\tBE_MVP_C({grant['from']})",
            f"#define {name}TO\tBE_MVP_C({grant['to']})",
            f"#define {name}PERMISSIONS \\",
            "\t(" + " | ".join(f"BE_MVP_MGMT_{permission.upper()}"
                               for permission in grant["permissions"]) + ")"]
        initializer += [f"\t{{ {name}FROM, {name}TO, \\",
                        f"\t  {name}PERMISSIONS }}, \\"]
        asserts += [
            f"_Static_assert({name}FROM < BE_MVP_DOMAINS &&",
            f"\t       {name}TO < BE_MVP_DOMAINS &&",
            f"\t       {name}FROM != {name}TO,",
            f"\t       \"grant {index} joins two of the scenario's "
            "domains\");"]
    defines += initializer + [
        "}",
        "#define BE_MVP_SCENARIO_ACCEPT_DENIAL\tBE_MVP_C("
        f"{int('denial' in sealed['accepted_exits'])})",
        "#define BE_MVP_SCENARIO_ACCEPT_MGMT\tBE_MVP_C("
        f"{int('mgmt' in sealed['accepted_exits'])})",
        "#define BE_MVP_SCENARIO_CONFIG_IDENTITY_HEX \\",
        f'\t"{sealed["config"]}"'] + octet_lines(
        "BE_MVP_SCENARIO_CONFIG_IDENTITY", sealed["config"]) + [""]
    asserts += [
        "_Static_assert(BE_MVP_SCENARIO_MEASURED_DOMAIN < BE_MVP_DOMAINS &&",
        "\t       BE_MVP_SCENARIO_SECRET_PAGE < BE_MVP_SCENARIO_PAGES,",
        '\t       "the measured domain and the secret page are the '
        'scenario\'s");']
    return defines, asserts


def header(name, binding, digest, layout, sealed=None, log=None):
    """The scenario's header; LOG, its log constants' lines
    (log_header())."""
    defines, asserts = (pages_header if sealed and "pages" in sealed else
                        channel_header)(sealed)
    defines += log or []
    lines = [
        "/* SPDX-License-Identifier: GPL-3.0-only */",
        "/*",
        " * Generated by mvp/tools/gen-scenario.py; do not edit.",
        f" * Scenario {name}, scenario.json sha256 {digest}:",
        " * the binding of each domain to its hart, VMID, and root, which",
        " * the monitor validates at boot; hart IDs are names, not authority.",
        " */",
        "",
        "#ifndef BE_MVP_SCENARIO_H",
        "#define BE_MVP_SCENARIO_H",
        "",
        '#include "mvp-layout.h"',
        "",
        f'#define BE_MVP_SCENARIO_NAME\t\t"{name}"',
        f"#define BE_MVP_SCENARIO_HARTS\t\tBE_MVP_C({layout['HARTS']})",
    ]
    for domain in binding:
        index = domain["index"]
        lines += [
            f"#define BE_MVP_SCENARIO_DOMAIN{index}_HART\t"
            f"BE_MVP_C({domain['hart']})",
            f"#define BE_MVP_SCENARIO_DOMAIN{index}_VMID\t"
            f"BE_MVP_C({domain['vmid']})",
            f"#define BE_MVP_SCENARIO_DOMAIN{index}_ROOT\t"
            f"BE_MVP_C(0x{domain['root']:x})",
        ]
    lines += [
        "#define BE_MVP_SCENARIO_BINDINGS_INITIALIZER { \\",
        "\t{ BE_MVP_SCENARIO_DOMAIN0_HART, BE_MVP_SCENARIO_DOMAIN0_VMID, "
        "\\",
        "\t  BE_MVP_SCENARIO_DOMAIN0_ROOT }, \\",
        "\t{ BE_MVP_SCENARIO_DOMAIN1_HART, BE_MVP_SCENARIO_DOMAIN1_VMID, "
        "\\",
        "\t  BE_MVP_SCENARIO_DOMAIN1_ROOT }, \\",
        "}",
        "",
    ] + defines + [
        "#ifndef __ASSEMBLER__",
        "_Static_assert(BE_MVP_SCENARIO_HARTS == BE_MVP_HARTS,",
        '\t       "the scenario\'s platform is the layout\'s");',
        "_Static_assert(BE_MVP_SCENARIO_DOMAIN0_HART != BE_MVP_CONTROL_HART "
        "&&",
        "\t       BE_MVP_SCENARIO_DOMAIN1_HART != BE_MVP_CONTROL_HART &&",
        "\t       BE_MVP_SCENARIO_DOMAIN0_HART != "
        "BE_MVP_SCENARIO_DOMAIN1_HART &&",
        "\t       BE_MVP_SCENARIO_DOMAIN0_HART < BE_MVP_HARTS &&",
        "\t       BE_MVP_SCENARIO_DOMAIN1_HART < BE_MVP_HARTS,",
        '\t       "each domain has its own hart on the platform, never the '
        'control hart");',
        "_Static_assert(BE_MVP_SCENARIO_DOMAIN0_VMID == BE_MVP_G0_VMID &&",
        "\t       BE_MVP_SCENARIO_DOMAIN1_VMID == BE_MVP_G1_VMID &&",
        "\t       BE_MVP_SCENARIO_DOMAIN0_ROOT == BE_MVP_G0_ROOT_HPA &&",
        "\t       BE_MVP_SCENARIO_DOMAIN1_ROOT == BE_MVP_G1_ROOT_HPA,",
        '\t       "the scenario\'s VMIDs and roots are the layout\'s pools");',
    ] + asserts + [
        "#endif",
        "",
        "#endif",
    ]
    return "\n".join(lines) + "\n"


def expectations(scenario, binding, layout, digest, core_of):
    """{image: expectation} for the scenario, its variants, its probes;
    CORE_OF gives a binding's MVP core profile (core_config())."""
    name = scenario["name"]
    before, per_domain, after = control_lines(
        name, binding, layout, layout["OUTBOUND_RING_BYTES"],
        layout["RUN_BUDGET"], core=core_of(binding))
    common = {
        "schema": EXPECT_SCHEMA,
        "scenario": name,
        "scenario_sha256": digest,
        "terminal_regex": TERMINAL_REGEX,
        "domains": [{key: domain[key] for key in
                     ("index", "hart", "vmid", "root", "hgatp", "block",
                      "gpa", "hpa", "bytes", "prefix", "bootargs")}
                    for domain in binding],
        "domain_lines": scenario["expect"]["domain_lines"],
        "rejected": scenario["expect"]["rejected"],
        "counters": scenario["expect"]["counters"],
        "exit_classes": scenario["expect"]["exit_classes"],
        "concurrency": scenario["expect"]["concurrency"],
    }
    images = {name: dict(common, image=name, outcome={"pass": True},
                         toolchains=["gcc", "clang"],
                         control_lines=before,
                         domain_control_lines=per_domain,
                         final_lines=after)}
    for variant in scenario.get("variants", []):
        if variant in console_variants(scenario):
            continue  # console_images()
        outcome = {key: variant[key] for key in variant
                   if key not in ("name", "toolchains", "where", "change")}
        # The variant's one change shows in the lines that print it.
        changed = copy.deepcopy(binding)
        if "hart" in variant:
            changed[variant["domain"]]["hart"] = variant["hart"]
        lines = control_lines(
            name, changed, layout,
            number(variant.get("outbound_bytes",
                               layout["OUTBOUND_RING_BYTES"]), "outbound"),
            number(variant.get("run_budget_ticks", layout["RUN_BUDGET"]),
                   "budget"),
            "<N>" if variant.get("time_above_zero") else "0",
            core=core_of(changed))
        images[variant["name"]] = dict(
            common, image=variant["name"], outcome=outcome,
            toolchains=variant["toolchains"], where=variant["where"],
            change=variant["change"], control_lines=lines[0],
            domain_control_lines=lines[1], final_lines=lines[2])
    for probe in scenario.get("probes", []):
        images[probe["name"]] = {
            "schema": EXPECT_SCHEMA, "scenario": name,
            "scenario_sha256": digest, "image": probe["name"],
            "terminal_regex": TERMINAL_REGEX,
            "toolchains": probe["toolchains"],
            "outcome": {"probe": True},
            "probe_lines": probe_lines(probe, layout),
            "control_lines": probe_control_lines(probe, binding, layout,
                                                 core_of(binding)),
            "final_lines": [line("BE_MVP:14 SHUTDOWN type=0 reason=0")],
            "domains": common["domains"],
        }
    return images


def role_lines(role, channel, entries):
    """A domain's lines after MVPINIT 02 (Markers): its role's MVPINIT 07
    CHANNEL line, then one MVPINIT 08 DENIED line per denied access."""
    pattern = channel["bytes"] - FLAG_BYTES
    out = [f"MVPINIT 07 CHANNEL role={role} gpa=0x{channel['gpa']:x} "
           f"bytes={pattern} digest=<x> " +
           (f"flag=0x{CHANNEL_FLAG:x}" if role == "writer" else
            "polls=<n> match=1")]
    return out + [denied_line(entry) for entry in entries]


def denied_line(entry):
    """M1's MVPINIT 08 DENIED line for one denied access (Markers)."""
    return (f"MVPINIT 08 DENIED n={entry['seq']} kind={entry['access']} "
            f"gpa={entry['gpa']} va=<v> pc=<p> signo=11 code=2 observed=1" +
            (" unchanged=1" if entry["kind"] == "read-only" else ""))


def mgmt_report(call):
    """A guest's MVPINIT 10 line for one management call (planning/
    mvp-m2-plan.md, Guest software): FID 0 and 1 by name, another by its
    number; a call of count n > 1 is a burst, its results run-length
    coded."""
    fid = MGMT_FIDS.get(call["fid"], str(call["fid"]))
    count = call.get("count", 1)
    return (f"MVPINIT 10 MGMT burst={count} fid={fid} target={call['target']}"
            f" results={call['result']}x{count}" if count > 1 else
            f"MVPINIT 10 MGMT fid={fid} target={call['target']} "
            f"result={call['result']}")


def role_lines_v3(role, index, sealed):
    """A v3 domain's lines after MVPINIT 02 (planning/mvp-m2-plan.md,
    Guest software): the kernel's line for the management module the init
    loads (MODULE_LINE), MVPINIT 07 PAGES with the pages its root maps,
    its child's MVPINIT 08 lines (M1's), then the host's answered requests
    and its management calls, its unanswered request after its granted
    pause, or the protected domain's management calls and its responses,
    each digest the HMAC-SHA-256 of the request."""
    calls = sealed["calls"][str(index)]
    out = [MODULE_LINE, f"MVPINIT 07 PAGES role={role} count="
           f"{sum(bool(page['rights'][index]) for page in sealed['pages'])}"
           ] + [denied_line(entry) for entry in sealed["denials"][str(index)]]
    answered = [item for item in sealed["requests"] if "digest" in item]
    if role == "prot":
        return out + [mgmt_report(call) for call in calls] + [
            f"MVPINIT 09 RESPONSE n={item['n']} digest={item['digest']}"
            for item in answered]
    paused = next(at for at, call in enumerate(calls) if call["fid"] == 0
                  and call["result"] == SBI_SUCCESS) + 1
    return out + [f"MVPINIT 09 REQUEST n={item['n']} digest={item['digest']}"
                  for item in answered] + [
        mgmt_report(call) for call in calls[:paused]] + [
        f"MVPINIT 09 REQUEST n={item['n']} timeout=1"
        for item in sealed["requests"] if "timeout" in item] + [
        mgmt_report(call) for call in calls[paused:]]


def deny_lines(binding, sealed):
    """Each domain's expected denials with the BE_MVP:DENY line hart 0
    prints for each (Markers): the GPA, htval = GPA >> 2, the cause, and
    the access fault injected for it (Q5); placeholders for the rest."""
    out = {}
    for domain in binding:
        rows = out[str(domain["index"])] = []
        for entry in sealed["denials"][str(domain["index"])]:
            gpa, cause = int(entry["gpa"], 16), CAUSES[entry["access"]]
            rows.append(dict(
                entry, cause=cause, injected=INJECTED[cause],
                htval=f"{gpa >> 2:#x}", line=line(
                    f"BE_MVP:DENY hart={domain['hart']} "
                    f"domain={domain['index']} seq={entry['seq']} "
                    f"kind={entry['kind']} cause={cause:#x} "
                    f"injected={INJECTED[cause]:#x} gpa={gpa:#x} "
                    f"htval={gpa >> 2:#x} htinst=<X> stval=<X> sepc=<X> "
                    "vsstatus=<X> vstvec=<X> ticks=<T> service=<T>")))
    return out


def expectations_v2(scenario, binding, layout, digest, sealed, report_sha):
    """{image: expectation} for a v2 scenario and its variants (schema
    be-mvp-expect-v2): v1's fields, with each domain's own required lines
    and their placeholders, the channel's two control lines, the expected
    denials, the exit sum, the accepted exits, and the authority report."""
    name, expect = scenario["name"], scenario["expect"]
    channel, report = sealed["channel"], sealed["report"]
    before, per_domain, after = control_lines(
        name, binding, layout, layout["OUTBOUND_RING_BYTES"],
        layout["RUN_BUDGET"], channel=channel, core=sealed["core"])
    lines = {}
    for domain in binding:
        index = domain["index"]
        own = lines[str(index)] = []
        for template in expect["domain_lines"]:
            own.append(template.replace("<bootargs>", domain["bootargs"]))
            if template.startswith("MVPINIT 02 "):
                own += role_lines(sealed["roles"][index], channel,
                                  sealed["denials"][str(index)])
    common = {
        "schema": EXPECT_SCHEMA_V2,
        "scenario": name,
        "scenario_sha256": digest,
        "terminal_regex": TERMINAL_REGEX,
        "domains": [dict({key: domain[key] for key in
                          ("index", "hart", "vmid", "root", "hgatp",
                           "block", "gpa", "hpa", "bytes", "prefix",
                           "bootargs")},
                         role=sealed["roles"][domain["index"]])
                    for domain in binding],
        "domain_lines": lines,
        "domain_placeholders": ROLE_PLACEHOLDERS,
        "rejected": expect["rejected"],
        "counters": expect["counters"],
        "exit_classes": expect["exit_classes"],
        "exit_sum": ["sbi", "ipi", "denials"],
        "accepted_exits": sealed["accepted_exits"],
        "concurrency": expect["concurrency"],
        "denials": deny_lines(binding, sealed),
        "report": {"file": REPORT_FILE, "sha256": report_sha,
                   "configuration_identity":
                       report["identity"]["configuration_identity"],
                   "grants": len(report["grants"]),
                   "flows": report["flows"]},
    }
    images = {name: dict(common, image=name, outcome={"pass": True},
                         toolchains=["gcc", "clang"],
                         control_lines=before,
                         domain_control_lines=per_domain,
                         final_lines=after)}
    for variant in scenario.get("variants", []):
        if variant in console_variants(scenario):
            continue  # console_images()
        outcome = {key: variant[key] for key in variant
                   if key not in ("name", "toolchains", "where", "change",
                                  "accepted_exits")}
        image = dict(common, image=variant["name"], outcome=outcome,
                     toolchains=variant["toolchains"],
                     where=variant["where"], change=variant["change"],
                     control_lines=before, domain_control_lines=per_domain,
                     final_lines=after)
        if "walked" in variant:
            # The refused check prints its DETAIL in place of the channel's
            # line, and no domain runs.
            image["control_lines"] = [
                entry for entry in before if not entry["template"]
                .startswith("BE_MVP:03 CHANNEL_CHECKED ")]
            outcome["detail_lines"] = [line(
                f"BE_MVP:DETAIL channel={channel['index']} "
                f"domain={variant['domain']} hart={variant['hart']} "
                f"walked={variant['walked']} declared={variant['declared']}")]
            outcome["absent"] = ["BE_MVP:03 CHANNEL_CHECKED"]
        if "first_fault" in variant:
            # M0's exit DETAIL for either domain's first denied access, from
            # VU mode (Q4: SPVP 0); nothing is logged or reported.
            outcome["detail_lines"] = [line(
                f"BE_MVP:DETAIL domain={fault['domain']} "
                f"hart={fault['hart']} cause={fault['cause']:#x} pc=<X> "
                f"tval=<X> htval={fault['htval']} htinst=<X> spvp=0 "
                "vsatp=<X> exits=<N>") for fault in variant["first_fault"]]
            outcome["absent"] = ["BE_MVP:DENY", "MVPINIT 08"]
            image["accepted_exits"] = variant["accepted_exits"]
        image["denials"] = {str(domain["index"]): [] for domain in binding}
        images[variant["name"]] = image
    return images


def page_lines(sealed, binding):
    """A v3 scenario's control-hart lines (planning/mvp-m2-plan.md,
    Markers): one :03 PAGE_CHECKED per page, its leaves from the report's
    derived flags; and a :05 PAGE_CLEARED per channel page, then the
    secret page's :05 SECRET_PLACED (its address and bytes, never its
    contents). M2's :06 MEASURED is gone: since M9 each domain's :06 LAUNCH
    is the log's (apply_log())."""
    level0 = ",".join(f"0x{page:x}" for page in sealed["level0"])
    checked, cleared = [], []
    for page in sealed["pages"]:
        ends = ("writer", "reader") if "writer" in page else ("reader",)
        checked.append(
            f"BE_MVP:03 PAGE_CHECKED page={page['index']} kind={page['kind']}"
            + "".join(f" {end}={page[end]}" for end in ends) +
            f" gpa=0x{page['gpa']:x} hpa=0x{page['hpa']:x} "
            f"bytes=0x{page['bytes']:x} level0={level0}" +
            "".join(f" {end}_pte=0x{page['leaves'][page[end]]:x}"
                    for end in ends) + f" config={sealed['config']}")
        cleared += [f"BE_MVP:05 PAGE_CLEARED page={page['index']} "
                    f"hpa=0x{page['hpa']:x} bytes=0x{page['bytes']:x} "
                    "ticks=<T>"] if page["kind"] == "channel" else []
    secret = sealed["secret_page"]
    return {"03": checked, "05": cleared + [
        f"BE_MVP:05 SECRET_PLACED page={secret['index']} "
        f"hpa=0x{secret['hpa']:x} bytes=0x{SECRET_BYTES:x} ticks=<T>"]}


def mgmt_lines(binding, mgmt):
    """Each domain's management requests with the BE_MVP:MGMT line hart 0
    prints for each (planning/mvp-m2-plan.md, Markers): the requester's
    hart and domain, its sequence number, the function, the target, the
    signed result, and the target's state after a granted call (- for a
    refused one)."""
    return {domain: [dict(entry, line=line(
        f"BE_MVP:MGMT hart={binding[int(domain)]['hart']} domain={domain} "
        f"seq={entry['seq']} fid={entry['fid_name']} "
        f"target={entry['target']} result={entry['result']} "
        f"target_state={entry['target_state']} ticks=<T> service=<T>"))
        for entry in entries] for domain, entries in mgmt.items()}


def expectations_v3(scenario, binding, layout, digest, sealed, report_sha):
    """{image: expectation} for a v3 scenario and its four runtime
    negatives (schema be-mvp-expect-v3): v2's fields, with each role's
    lines, M1's exit sum, sbi's terms, among them the management requests
    (mgmt), which the :12 line does not print, so sbi less the printed
    terms, with each domain's count (sbi_derived), the pages and their
    leaves, the grants, the secret, the measured domain (its launch
    inputs are the log's, apply_log()), the requests with their digests,
    each domain's management calls with hart 0's lines, the pause and the
    termination, each domain's BE_MVP:11 line with spv=<S> (Plan revision
    M2-A.1), and each negative's failure (wrong-measurement's, the log's
    failed gate, apply_log())."""

    def derived(mgmt):
        # The plan's "counted in sbi": hart 0's requests, one per line.
        return {"mgmt": {domain: {"exact": len(entries)}
                         for domain, entries in mgmt.items()}}

    name, expect, report = scenario["name"], scenario["expect"], sealed[
        "report"]
    host, prot = sealed["host"], sealed["prot"]
    hart = [domain["hart"] for domain in binding]
    extra = page_lines(sealed, binding)
    # The host's DOMAIN_SHUTDOWN shows its refused calls (its FID 7,
    # answered on its hart): the counters' exact value.
    refused = str(expect["counters"].get("refused", {}).get("exact", "<N>"))
    before, per_domain, after = control_lines(
        name, binding, layout, layout["OUTBOUND_RING_BYTES"],
        layout["RUN_BUDGET"], extra=extra, refused=refused, spv=SPV,
        core=sealed["core"])
    # The protected domain ends paused, then terminated, by the host, its
    # launch register unaltered (Markers; M9's D-9: apply_log() writes it).
    per_domain[str(prot)] = per_domain[str(prot)][:1] + [line(
        f"BE_MVP:12 DOMAIN_PAUSED hart={hart[prot]} domain={prot} "
        f"by={host} exits=<N> ticks=<T>"), line(
        f"BE_MVP:12 DOMAIN_TERMINATED hart={hart[prot]} domain={prot} "
        f"by={host} exits=<N> sha256=- ticks=<T>")]
    lines = {}
    for domain in binding:
        index = domain["index"]
        role = sealed["roles"][index]
        own = lines[str(index)] = []
        for template in expect["domain_lines"][role]:
            own.append(template.replace("<bootargs>", domain["bootargs"]))
            if template.startswith("MVPINIT 02 "):
                own += role_lines_v3(role, index, sealed)
    mgmt = mgmt_lines(binding, sealed["mgmt"])
    paused = next(entry["seq"] for entry in mgmt[str(host)]
                  if entry["fid_name"] == "pause" and entry["result"] == 0)
    common = {
        "schema": EXPECT_SCHEMA_V3,
        "scenario": name,
        "scenario_sha256": digest,
        "terminal_regex": TERMINAL_REGEX,
        "domains": [dict({key: domain[key] for key in
                          ("index", "hart", "vmid", "root", "hgatp",
                           "block", "gpa", "hpa", "bytes", "prefix",
                           "bootargs")},
                         role=sealed["roles"][domain["index"]])
                    for domain in binding],
        "domain_lines": lines,
        "domain_placeholders": ROLE_PLACEHOLDERS,
        "rejected": expect["rejected"],
        "counters": expect["counters"],
        "exit_classes": expect["exit_classes"],
        "exit_sum": ["sbi", "ipi", "denials"],
        "sbi_terms": [term for term in expect["exit_classes"]
                      if term != "ipi"] + ["mgmt"],
        "sbi_derived": derived(mgmt),
        "accepted_exits": sealed["accepted_exits"],
        "concurrency": expect["concurrency"],
        "denials": deny_lines(binding, sealed),
        "report": {"file": REPORT_FILE, "sha256": report_sha,
                   "configuration_identity": sealed["config"],
                   "grants": len(report["grants"]),
                   "flows": report["flows"],
                   "management": expect["report"]["management"]},
        "pages": [dict({key: page[key] for key in page if key not in (
            "gpa", "hpa", "bytes", "leaves")}, gpa=f"{page['gpa']:#x}",
            hpa=f"{page['hpa']:#x}", bytes=f"{page['bytes']:#x}",
            leaves=[None if leaf is None else f"{leaf:#x}"
                    for leaf in page["leaves"]]) for page in sealed["pages"]],
        "grants": sealed["grants"],
        "secret_hex": sealed["secret"],
        "secret": {"page": sealed["secret_page"]["index"],
                   "hpa": f"{sealed['secret_page']['hpa']:#x}",
                   "bytes": SECRET_BYTES},
        "measurement": {"domain": prot, "hart": hart[prot]},
        "requests": {"hmac": HMAC_TEXT, "requester": host, "server": prot,
                     "messages": sealed["requests"],
                     "unanswered_after_seq": paused},
        "mgmt": mgmt,
        "order": [entry["template"].split(" exits=")[0] for entry in
                  per_domain[str(prot)][1:] + per_domain[str(host)][1:]] + [
            "BE_MVP:13 RUN_COMPLETE"],
    }
    images = {name: dict(common, image=name, outcome={"pass": True},
                         toolchains=["gcc", "clang"],
                         control_lines=before,
                         domain_control_lines=per_domain,
                         final_lines=after)}
    for variant in scenario.get("variants", []):
        if variant in console_variants(scenario):
            continue  # console_images()
        outcome = {key: variant[key] for key in variant
                   if key not in ("name", "toolchains", "where", "change",
                                  "mgmt")}
        if variant.get("pass"):
            # self-report-flip (M9, D-4): the scenario's own run; its log
            # and its finding are apply_log()'s.
            images[variant["name"]] = dict(
                copy.deepcopy(images[name]), image=variant["name"],
                outcome=outcome, toolchains=variant["toolchains"],
                where=variant["where"], change=variant["change"])
            continue
        image = dict(common, image=variant["name"], outcome=outcome,
                     toolchains=variant["toolchains"],
                     where=variant["where"], change=variant["change"],
                     control_lines=before, domain_control_lines=per_domain,
                     final_lines=after, order=[],
                     denials={str(index): [] for index in range(DOMAINS)},
                     mgmt={str(index): [] for index in range(DOMAINS)})
        if variant["fail"] == "gstage":
            # The page check prints the pages' lines only after every page
            # passes, so the refused page's DETAIL stands in place of all
            # three, and no domain runs.
            image["control_lines"] = [entry for entry in before if not entry[
                "template"].startswith("BE_MVP:03 PAGE_CHECKED ")]
            outcome["detail_lines"] = [line(
                f"BE_MVP:DETAIL page={variant['page']} "
                f"domain={variant['domain']} hart={variant['hart']} "
                f"walked={variant['walked']} declared={variant['declared']}")]
            outcome["absent"] = ["BE_MVP:03 PAGE_CHECKED"]
        elif variant["fail"] == "measurement":
            # The image carries the protected domain's expected launch
            # register with bit 0 of its first byte flipped (Q16); its
            # failed gate's lines are the log's (apply_log()).
            pass
        else:
            # no-grant-check: hart 0 delivers the protected domain's
            # terminate 0, which ends the host wherever its run is, and the
            # run, the protected domain never ending, times out under the
            # variant's budget. The host's lines and denials are a prefix
            # of its own (terminated); the protected domain's lines end at
            # its management calls, its responses then depending on what
            # the host had requested. DOMAIN_TERMINATED carries the host's
            # launch register (M9's D-9; apply_log()).
            budget = number(variant["run_budget_ticks"], "run_budget_ticks")
            image["control_lines"], chains, _ = control_lines(
                name, binding, layout, layout["OUTBOUND_RING_BYTES"], budget,
                extra=extra, spv=SPV, core=sealed["core"])
            killed = line(f"BE_MVP:12 DOMAIN_TERMINATED hart={hart[host]} "
                          f"domain={host} by={prot} exits=<N> sha256=- "
                          "ticks=<T>")
            chains[str(host)] = chains[str(host)][:1] + [killed]
            chains[str(prot)] = chains[str(prot)][:1]
            image["mgmt"] = unchecked = mgmt_lines(binding,
                                                   sealed["unchecked"])
            image["domain_control_lines"] = chains
            image["denials"] = common["denials"]
            served = lines[str(prot)]
            cut = max(at for at, text in enumerate(served) if text.startswith(
                ("MVPINIT 07 ", "MVPINIT 08 "))) + 1
            image["domain_lines"] = {
                str(host): lines[str(host)], str(prot): served[:cut] + [
                    mgmt_report(call) for call in variant["mgmt"][str(prot)]]}
            outcome["required_lines"] = [unchecked[str(prot)][0]["line"],
                                         killed]
            outcome["absent"] = ["BE_MVP:12 DOMAIN_PAUSED",
                                 "BE_MVP:12 DOMAIN_SHUTDOWN", "BE_MVP:13",
                                 "BE_MVP:14"]
            outcome["prefix_domains"] = [host]
        image["sbi_derived"] = derived(image["mgmt"])
        images[variant["name"]] = image
    return images


# ---------------------------------------------- M7-4: the console variants
# planning/mvp-m7-plan.md, Q4, Q8, Q12, Q15, D-2, D-4, D-5, and D-11: each
# scenario's `shell` variant, SCENARIO-shell, whose domains with
# rdinit=/init-shell hold the console input grant (anchor's protected
# domain keeps its role and no grant, Q27) and whose session file is typed
# in QEMU
# (tests/session-typist.py); and two-guests' QEMU-only `hostile` variant,
# G0 with /init-hostile and no grant (D-4). A console variant names, per
# domain, its init variant or null ("rdinit") and, with a grant, each
# domain's grant ("console_input") and its session ("session"); its
# monitor seals the grants (config_source()), and its DTBs are
# tools/gen-dts.py's variants of the scenario's.
CONSOLE_KEYS = {"rdinit", "console_input", "session"}
SHELL_INIT, HOSTILE_INIT = "/init-shell", "/init-hostile"
CONSOLE_DTBS = {SHELL_INIT: {1: "shell", 2: "te-poc-shell", 3: "anchor-shell"},
                HOSTILE_INIT: {1: "hostile"}}
SESSION_SCHEMA = "be-mvp-session-v1"
SESSION_FIELDS = {"spdx", "copyright", "purpose", "trust", "scope", "schema",
                  "name", "steps"}
SESSION_NAME = r"sessions/[a-z][a-z0-9-]{0,31}\.json"
# The negatives (Q8) and the drop each provokes, its first one printing
# BE_MVP:17; the typed text of each, the run nonce, the shell's prompt,
# and the line mode's end (Enter, CR). The focus prefix is mvp-input.h's
# (Q1), `~`, 0x7e, which BE_MVP:15 prints.
SESSION_NEGATIVES = {"before-focus": "no-focus", "no-grant": "no-grant",
                     "bad-sequence": "bad-sequence", "literal": None}
FOCUS_PREFIX, INPUT_PREFIX = "~", 0x7e
ENTER, NONCE, NONCE_TEMPLATE = "\r", "NONCE", "<nonce>"
NONCE_REGEX = r"[0-9a-f]{16}"
PROMPT = "# "
# `~~` at a line's start delivers one `~`, which the shell expands to its
# HOME, /, so the literal negative's line runs //bin/echo.
NEGATIVE_TEXT = {"before-focus": "echo before-focus" + ENTER,
                 "bad-sequence": FOCUS_PREFIX + "x",
                 "literal": FOCUS_PREFIX * 2 + "/bin/echo literal" + ENTER}
LITERAL_LINES = (PROMPT + "~/bin/echo literal", "literal")
SHELL_START = "MVPINIT 11 SHELL tty=/dev/hvc0 role={}"
SHELL_END = ["MVPINIT 11 SHELL exit=0", "MVPINIT 05 RESULT pass",
             "MVPINIT 06 POWER_OFF", "[<s>] reboot: Power down"]
RUN_LINE = "[<s>] Run {} as init process"
# A session's words: printable, and the shell's own (no quoting, glob,
# expansion, or redirection), NONCE among them.
WORD = r"[A-Za-z0-9_.:=/@%+,-]+"
WORDS = rf"{WORD}(?: {WORD})*"
# D-2's documented output bound: a step's expected lines, each one LINE
# record (a 16-byte header and its payload padded to 8), each placeholder
# counted as 64 bytes, and 512 bytes of slack, within the outbound ring's
# peak budget, BE_MVP_RING_PEAK_BUDGET.
RECORD_HEADER, PLACEHOLDER_BYTES, BOUND_SLACK = 16, 64, 512
# The hostile guest's look-alike lines (guest/mvp-init.c, /init-hostile).
FORGED = ["BE_MVP:13 RUN_COMPLETE forged", "BE_MVP_G1: forged"]
LINE_BYTES = 256
# A kernel line's stamp at boot, "[    0.000000]".
STAMP_BYTES = 14


def session_context(sealed, bins):
    """What a session's commands print from (session_command()): each
    domain's role and denials, the channel's GPA, the secret, and the
    count of /bin's entries."""
    return {"roles": sealed["roles"] if sealed else [None] * DOMAINS,
            "bins": bins,
            "channel": sealed["channel"]["gpa"] if sealed and
            "channel" in sealed else None,
            "secret": sealed.get("secret") if sealed else None,
            "denials": [sealed["denials"][str(index)] if sealed else []
                        for index in range(DOMAINS)]}


def console_variants(scenario):
    """The scenario's console variants, in order."""
    return [variant for variant in scenario.get("variants", [])
            if CONSOLE_KEYS & set(variant)]


def check_console(scenario, binding, layout, dts, version):
    """M7-4's rules for each console variant: its keys, one init variant
    per domain (a shell, the hostile guest, or none), a grant exactly where
    a shell runs (never the protected domain's, Q27), a session where
    there is a grant, a passing outcome, and each domain's bootargs those
    of tools/gen-dts.py's DTB variant, the scenario's with the init's
    rdinit= before the "--"; returns {name: [bootargs]}."""
    out = {}
    roles = [domain.get("role") for domain in scenario["domains"]]
    for variant in console_variants(scenario):
        name = variant["name"]
        require(set(variant) <= CONSOLE_KEYS | {
            "name", "toolchains", "where", "change", "pass"} and
            variant.get("pass") is True, f"variant {name} is a console "
            "variant with other keys, or one that does not pass")
        inits = variant.get("rdinit")
        require(isinstance(inits, list) and len(inits) == DOMAINS and all(
            init in (None, SHELL_INIT, HOSTILE_INIT) for init in inits) and
            any(inits), f"variant {name}.rdinit is not each domain's init "
            "variant, a shell or the hostile guest, or null")
        grants = variant.get("console_input", [False] * DOMAINS)
        require(isinstance(grants, list) and len(grants) == DOMAINS and all(
            isinstance(grant, bool) for grant in grants),
            f"variant {name}.console_input is not each domain's grant")
        require(grants == [init == SHELL_INIT for init in inits],
                f"variant {name} grants console input other than to the "
                "domains its shells run in")
        require("prot" not in [role for role, grant in zip(roles, grants)
                               if grant], f"variant {name} grants console "
                "input to the protected domain (Q27)")
        require(("session" in variant) == any(grants) and
                ("console_input" in variant) == any(grants),
                f"variant {name} names a session and grants where it has a "
                "shell, and only there")
        # One shell variant per scenario, named for it: image names are
        # unique across the scenarios' expectations (tools/evidence.py).
        require(not any(grants) or name == f"{scenario['name']}-shell",
                f"variant {name} has a shell but is not named "
                f"{scenario['name']}-shell")
        require(HOSTILE_INIT not in inits or version == 1,
                f"variant {name}: the hostile guest is two-guests'")
        bootargs = []
        for index, (domain, init) in enumerate(zip(binding, inits)):
            base = domain["bootargs"]
            if init is None:
                bootargs.append(base)
                continue
            dtb = CONSOLE_DTBS[init].get(version)
            require(dtb is not None, f"variant {name}: no DTB of {init} for "
                    "this scenario")
            wanted = dts.values(layout, index, dtb)["BOOTARGS"]
            require(wanted == base.replace(" -- ", f" rdinit={init} -- ", 1),
                    f"variant {name}: G{index}'s DTB {dtb} is not the "
                    f"scenario's with rdinit={init}")
            bootargs.append(wanted)
        out[name] = bootargs
    return out


def load_session(scenario_path, name):
    """A console variant's session file (Q8): (the session, its SHA-256),
    each step one of {"focus": "g<d>"}, {"send": LINE}, {"expect":
    TEXT}, or {"negative": KIND}, LINE and TEXT printable ASCII, LINE
    never at a prefix."""
    require(isinstance(name, str) and re.fullmatch(SESSION_NAME, name),
            f"session {name!r} is not sessions/<name>.json")
    data = (pathlib.Path(scenario_path).parent / name).read_bytes()
    return parse_session(json.loads(data), name), \
        hashlib.sha256(data).hexdigest()


def parse_session(session, name):
    """A session file's content (load_session()), its steps checked."""
    require(isinstance(session, dict), "the session is not an object")
    known(session, SESSION_FIELDS, "the session")
    require(session.get("schema") == SESSION_SCHEMA,
            f"the session's schema is not {SESSION_SCHEMA}")
    require(session.get("name") == pathlib.PurePosixPath(name).stem,
            f"the session {name} is not named for its file")
    steps = session.get("steps")
    require(isinstance(steps, list) and steps, "the session has no steps")
    for index, step in enumerate(steps):
        where = f"session step {index}"
        require(isinstance(step, dict) and len(step) == 1,
                f"{where} is not one action")
        (kind, value), = step.items()
        require(kind in ("focus", "send", "expect", "negative"),
                f"{where}: unknown action {kind!r}")
        if kind == "focus":
            require(value in [f"g{index}" for index in range(DOMAINS)],
                    f"{where}: focus {value!r} names no domain")
        elif kind == "negative":
            require(value in SESSION_NEGATIVES,
                    f"{where}: unknown negative {value!r}")
        else:
            require(isinstance(value, str) and
                    re.fullmatch(r"[ -~]{1,120}", value) and
                    value == value.strip(), f"{where}: {kind} {value!r} is "
                    "not 1 to 120 printable bytes")
            require(kind != "send" or not value.startswith(FOCUS_PREFIX),
                    f"{where}: a line begins with the focus prefix")
    return session


def session_bound(lines, budget, where):
    """D-2: a step's expected lines within the outbound ring's peak budget
    (RECORD_HEADER, PLACEHOLDER_BYTES, BOUND_SLACK)."""
    total = BOUND_SLACK
    for text in lines:
        size = len(text) + PLACEHOLDER_BYTES * len(re.findall(
            r"<[A-Za-z]+>", text))
        # One record per 256 bytes of line, each with its header and at
        # most 7 bytes of padding.
        records = max(1, -(-size // LINE_BYTES))
        total += records * (RECORD_HEADER + 8) + size
    require(total <= budget, f"{where}: its expected output, {total} bytes "
            f"with slack, could exceed the outbound ring's peak budget "
            f"0x{budget:x} (D-2)")
    return total


def session_command(command, domain, context, state, where):
    """The lines one typed COMMAND makes DOMAIN print after its echo, as
    templates, and what it adds to the run (STATE: the channel's text,
    each domain's demonstrated denials and management calls, the requests,
    the module, the ended domains)."""
    role, record = context["roles"][domain], context["denials"][domain]
    if command == "exit":
        state["ended"].add(domain)
        return list(SHELL_END)
    match = re.fullmatch(rf"echo ({WORDS})", command)
    if match:
        return [match.group(1).replace(NONCE, NONCE_TEMPLATE)]
    if command == "ls /bin | wc -l":
        return [str(context["bins"])]
    match = re.fullmatch(rf"be-chan write ({WORDS})", command)
    if match or command == "be-chan read":
        require(role == "writer" or command == "be-chan read" and
                role == "reader", f"{where}: {command!r} in a domain whose "
                f"role is {role}")
        if match:
            text = match.group(1)
            size = len(text.replace(NONCE, "0" * 16))
            require(size <= 64, f"{where}: the channel's text is over 64 "
                    "bytes")
            state["text"] = (text.replace(NONCE, NONCE_TEMPLATE), size)
        require("text" in state, f"{where}: a read before any write")
        text, size = state["text"]
        return [f"MVPINIT 12 CHAN {'write' if match else 'read'} "
                f"gpa=0x{context['channel']:x} bytes={size} text={text}"]
    match = re.fullmatch(r"be-deny (load-unmapped|store-shared)", command)
    if match:
        access = "load" if match.group(1) == "load-unmapped" else "store"
        entry = next((entry for entry in record if entry["access"] ==
                      access), None)
        shown = state["denials"][domain]
        require(entry is not None and entry["gpa"] not in [
            row["gpa"] for row in shown], f"{where}: {command!r}: the role "
            f"has no {access} to deny, or it was denied already")
        shown.append(dict(entry, seq=len(shown) + 1))
        return [denied_line(entry)]
    match = re.fullmatch(r"be-anchor request ([1-9][0-9]{0,8})", command)
    if match or command in ("be-anchor pause", "be-anchor terminate"):
        require(role == "host", f"{where}: {command!r} in a domain whose "
                f"role is {role}")
    if match:
        number = int(match.group(1))
        require(number not in state["requests"],
                f"{where}: request {number} twice")
        state["requests"].append(number)
        return [f"MVPINIT 09 REQUEST n={number} "
                f"digest={request_digest(context['secret'], number)}"]
    if command in ("be-anchor pause", "be-anchor terminate"):
        call = {"fid": 0 if command.endswith("pause") else 1,
                "target": DOMAINS - 1 - domain, "result": SBI_SUCCESS}
        state["calls"][domain].append(call)
        out = [] if state["module"] else [MODULE_LINE]
        state["module"] = True
        return out + [mgmt_report(call)]
    raise ScenarioError(f"{where}: {command!r} is no command a session's "
                        "expectation knows")


def request_message(number):
    """The host's request N's message, as guest/mvp-init.c makes it (Q8)."""
    return f"BE-MVP-M2-REQ-{number}"


def request_digest(secret, number):
    """HMAC_TEXT's digest of request NUMBER under the secret's hex."""
    message = request_message(number).encode("ascii").ljust(REQUEST_BYTES,
                                                            b"\0")
    return hmac.new(bytes.fromhex(secret), number.to_bytes(8, "little") +
                    message, hashlib.sha256).hexdigest()


def session_plan(session, digest, path, grants, context, budget):
    """The session's steps as the typist types and waits for them, and as
    the expectation requires them: (the console_input section, each
    domain's session lines, and STATE). Every expect is a line its
    focused domain's last send makes; every shell ends with exit."""
    granted = [index for index, grant in enumerate(grants) if grant]
    ungranted = [index for index, grant in enumerate(grants) if not grant]
    state = {"ended": set(), "denials": {index: [] for index in
                                         range(DOMAINS)},
             "calls": {index: [] for index in range(DOMAINS)},
             "requests": [], "module": False}
    lines = {index: [] for index in range(DOMAINS)}
    steps, focus, drops, current, made = [], [], [], None, None
    for index, step in enumerate(session["steps"]):
        (kind, value), = step.items()
        where = f"session step {index}"
        entry = {"index": index, "kind": kind, "value": value, "typed": "",
                 "waits": []}
        if kind in ("send", "expect") or value == "literal":
            # An expect may follow a shell's exit: its lines are the last
            # send's.
            require(current is not None and (
                kind == "expect" or current not in state["ended"]),
                f"{where}: no running domain has the focus")
            entry["domain"] = current
        if kind == "focus":
            current = int(value[1:])
            require(current in granted and current not in state["ended"],
                    f"{where}: focus on a domain without the grant, or "
                    "ended")
            focus.append(current)
            entry.update(domain=current, typed=FOCUS_PREFIX + value[1:],
                         waits=[{"monitor": f"BE_MVP:16 FOCUS {value}"}])
            made = None
        elif kind == "send":
            made = session_command(value, current, context, state, where)
            echo = PROMPT + value
            lines[current] += [echo.replace(NONCE, NONCE_TEMPLATE)] + made
            session_bound([echo] + made, budget, where)
            entry.update(typed=value + ENTER,
                         waits=[{"domain": current, "line": echo}])
        elif kind == "expect":
            token = value.replace(NONCE, NONCE_TEMPLATE)
            require(made is not None and any(token in text for text in made),
                    f"{where}: {value!r} is in none of the lines its "
                    "domain's last send makes")
            entry["waits"] = [{"domain": current, "contains": value}]
        elif value == "literal":
            made = list(LITERAL_LINES[1:])
            lines[current] += list(LITERAL_LINES)
            entry.update(typed=NEGATIVE_TEXT[value], waits=[
                {"domain": current, "line": text} for text in
                LITERAL_LINES])
        else:
            reason = SESSION_NEGATIVES[value]
            require(reason not in drops, f"{where}: {value} again; only a "
                    "reason's first drop prints its line")
            require(value != "before-focus" or not focus,
                    f"{where}: before-focus after a focus")
            require(value != "no-grant" or ungranted,
                    f"{where}: no-grant with every domain granted")
            drops.append(reason)
            entry.update(typed=NEGATIVE_TEXT.get(value, FOCUS_PREFIX + str(
                ungranted[0] if ungranted else 0)), waits=[
                {"monitor": f"BE_MVP:17 INPUT_DROP {reason}"}])
        steps.append(entry)
    require(set(granted) <= state["ended"], "the session leaves a shell "
            "running, so the run cannot end")
    ready = [{"monitor": f"BE_MVP:15 INPUT_ARMED grants=" +
              ",".join(f"g{index}" for index in granted) +
              f" prefix=0x{INPUT_PREFIX:x}"},
             {"monitor": "BE_MVP:16 FOCUS none"}] + [
        {"domain": index, "contains": SHELL_START.split(" role=")[0]}
        for index in granted]
    section = {"grants": granted, "prefix": f"0x{INPUT_PREFIX:x}",
               "session": {"file": path, "name": session["name"],
                           "sha256": digest},
               "ready": ready, "steps": steps, "focus": focus,
               "drops": drops, "shells": granted}
    return section, lines, state


def monitor_lines(raw):
    """A guest's output RAW (bytes) as the monitor prints its lines
    (src/mvp-sbi.c, be_mvp_console_feed): CR dropped, LF ending a line,
    any other byte outside 0x20 to 0x7e as ?, and a full 256-byte buffer
    posted as its own line."""
    out, line = [], ""
    for byte in raw:
        if byte == 0x0d:
            continue
        if byte == 0x0a:
            out.append(line)
            line = ""
            continue
        if len(line) == LINE_BYTES:
            out.append(line)
            line = ""
        line += chr(byte) if 0x20 <= byte <= 0x7e else "?"
    return out


def hostile_lines():
    """/init-hostile's lines after its line 01 (guest/mvp-init.c), as the
    monitor prints them (monitor_lines()): every byte value in eight
    lines of 32, the look-alike lines, the terminal query and the window
    title, and the 300-byte line."""
    raw = b""
    for block in range(8):
        raw += f"MVPINIT 13 HOSTILE bytes={block} ".encode() + bytes(
            range(block * 32, block * 32 + 32)) + b"\n"
    raw += "".join(text + "\n" for text in FORGED).encode()
    raw += b"MVPINIT 13 HOSTILE query=\x1b[6n title=\x1b]0;forged\x07\n"
    head = b"MVPINIT 13 HOSTILE long=300 "
    raw += head + b"x" * (300 - len(head)) + b"\n"
    return monitor_lines(raw)


def console_head(templates, init, bootargs, through):
    """A domain's lines up to its init's line THROUGH, with its command
    line and the init the kernel runs those of its variant. The command
    line, behind the boot's stamp ([    0.000000], STAMP_BYTES), may be
    longer than the monitor's line buffer: its first LINE_BYTES then end
    one line and the rest is the next (monitor_lines())."""
    out = []
    for template in templates:
        if "] Kernel command line: " in template:
            head = "Kernel command line: " + bootargs
            cut = LINE_BYTES - STAMP_BYTES - 1
            out += ["[<s>] " + head[:cut]] + ([head[cut:]] if head[cut:]
                                              else [])
            continue
        if template == RUN_LINE.format("/init"):
            template = RUN_LINE.format(init)
        out.append(template)
        if template.startswith(through):
            return out
    raise ScenarioError(f"the domain lines hold no {through!r} line")


def console_images(scenario, scenario_path, images, binding, layout, dts,
                   sealed, budget, bins):
    """{image: expectation} for the scenario's console variants, each from
    the scenario's own expectation (IMAGES[name]): the variant's bootargs
    and domain lines (a shell's: its head, line 11, the session's lines,
    and its end; the hostile guest's: its head, its lines, and its end;
    any other domain's, the scenario's, the protected domain's with the
    session's responses); with a grant, BE_MVP:15 and :16 after :07, :18
    before :13, the console_input section, and dbcn_input among sbi's
    terms; a v2 or v3 scenario's denials, and a v3 one's management calls,
    requests, and refused count, the session's; the hostile variant's
    forged lines."""
    version, name = version_of(scenario), scenario["name"]
    base = images[name]
    bootargs = check_console(scenario, binding, layout, dts, version)
    roles = sealed["roles"] if sealed else [None] * DOMAINS
    out = {}
    for variant in console_variants(scenario):
        image = copy.deepcopy(base)
        image.update(image=variant["name"], outcome={"pass": True},
                     toolchains=variant["toolchains"],
                     where=variant["where"], change=variant["change"])
        inits, grants = variant["rdinit"], variant.get("console_input",
                                                       [False] * DOMAINS)
        own = base["domain_lines"]
        own = {str(index): list(own) for index in range(DOMAINS)} \
            if isinstance(own, list) else copy.deepcopy(own)
        for index, args in enumerate(bootargs[variant["name"]]):
            image["domains"][index]["bootargs"] = args
        state = None
        if any(grants):
            session, digest = load_session(scenario_path,
                                           variant["session"])
            section, lines, state = session_plan(
                session, digest, variant["session"], grants,
                session_context(sealed, bins), budget)
            image["console_input"] = section
            for index, init in enumerate(inits):
                if init == SHELL_INIT:
                    own[str(index)] = console_head(
                        own[str(index)], init, bootargs[variant["name"]][
                            index], "MVPINIT 02 ") + [SHELL_START.format(
                                roles[index] or "none")] + lines[index]
            image["control_lines"] = console_control(image["control_lines"],
                                                     grants)
            # A granted domain's every read is served, so counted in
            # dbcn_input, never refused as dbcn_read (src/mvp-sbi.c).
            for index in (index for index, grant in enumerate(grants)
                          if grant):
                image["domain_control_lines"][str(index)] = [line(
                    entry["template"].replace(" dbcn_read=<N> ",
                                              " dbcn_read=0 ", 1))
                    if " dbcn_read=<N> " in entry["template"] else entry
                    for entry in image["domain_control_lines"][str(index)]]
            image["final_lines"] = [line(
                "BE_MVP:18 INPUT read=<N> " + " ".join(
                    f"g{index}=<N>:<Q>" for index in range(DOMAINS)) +
                " dropped=<D>")] + image["final_lines"]
            image["exit_classes"] = base["exit_classes"] + ["dbcn_input"]
            terms = base.get("sbi_terms", [term for term in base[
                "exit_classes"] if term != "ipi"])
            image["sbi_terms"] = terms + ["dbcn_input"]
            image["sbi_derived"] = dict(base.get("sbi_derived", {}), **{
                "dbcn_input": {str(index): {"min": 1, "max": layout[
                    "EXIT_CEILING"]} if grant else {"exact": 0}
                    for index, grant in enumerate(grants)}})
        for index, init in enumerate(inits):
            if init == HOSTILE_INIT:
                own[str(index)] = console_head(
                    own[str(index)], init, bootargs[variant["name"]][index],
                    "MVPINIT 01 ") + hostile_lines() + SHELL_END[1:]
                image["forged"] = {str(index): list(FORGED)}
        image["domain_lines"] = own
        image["domain_placeholders"] = dict(base.get(
            "domain_placeholders", {}), **{NONCE_TEMPLATE: NONCE_REGEX})
        if state is not None and version >= 2:
            console_roles(image, state, binding, sealed, layout, version)
        out[variant["name"]] = image
    return out


def console_control(entries, grants):
    """The control lines with BE_MVP:15 and :16 FOCUS none after :07: hart
    0 arms console input after the barrier, before any hart starts
    (src/mvp-runtime.c, arm_input())."""
    at = next(index for index, entry in enumerate(entries)
              if entry["template"].startswith("BE_MVP:07 ")) + 1
    armed = "BE_MVP:15 INPUT_ARMED grants=" + ",".join(
        f"g{index}" for index, grant in enumerate(grants) if grant) + \
        f" prefix=0x{INPUT_PREFIX:x}"
    return entries[:at] + [line(armed), line("BE_MVP:16 FOCUS none")] + \
        entries[at:]


def console_roles(image, state, binding, sealed, layout, version):
    """A v2 or v3 shell variant's denials, the session's; and a v3 one's
    management calls (the host's, the session's; the protected domain's,
    its role's), their BE_MVP:MGMT lines, refused, the requests and the
    protected domain's responses to them, and the host's :12 line."""
    denials = {str(index): [] for index in range(DOMAINS)}
    for index in range(DOMAINS):
        denials[str(index)] = state["denials"][index] if index in \
            image["console_input"]["grants"] else \
            sealed["denials"][str(index)]
    image["denials"] = deny_lines(binding, {"denials": denials})
    if version != 3:
        return
    host, prot = sealed["host"], sealed["prot"]
    calls = {str(host): state["calls"][host],
             str(prot): sealed["calls"][str(prot)]}
    mgmt, _ = management(sealed["grants"], calls)
    image["mgmt"] = mgmt_lines(binding, mgmt)
    image["sbi_derived"]["mgmt"] = {domain: {"exact": len(entries)}
                                    for domain, entries in mgmt.items()}
    refused = sum(1 for call in state["calls"][host]
                  if call["fid"] not in MGMT_FIDS)
    image["counters"]["refused"] = {"exact": refused}
    chain = image["domain_control_lines"][str(host)]
    chain[-1] = line(chain[-1]["template"].replace(
        " refused=1 ", f" refused={refused} ", 1))
    messages = [dict(n=number, message=request_message(number),
                     message_hex=request_message(number).encode(
                         "ascii").ljust(REQUEST_BYTES, b"\0").hex(),
                     digest=request_digest(sealed["secret"], number))
                for number in state["requests"]]
    image["requests"] = dict(image["requests"], messages=messages,
                             unanswered_after_seq=None)
    served = role_lines_v3("prot", prot, dict(sealed, requests=messages))
    head = image["domain_lines"][str(prot)]
    cut = next(at for at, text in enumerate(head)
               if text.startswith("MVPINIT 02 ")) + 1
    image["domain_lines"][str(prot)] = head[:cut] + served


def console_self_test(scenario_path, scenario, layout, dts, binding, sealed,
                      bins):
    """M7-4's console variants and sessions: each mutation refused for its
    own reason (check_console(), parse_session(), session_plan(),
    session_bound()), and the scenario's own variants accepted; returns
    (the cases, the failures)."""
    version = version_of(scenario)
    variants = console_variants(scenario)
    shell = next(variant for variant in variants
                 if variant.get("session"))
    at = scenario["variants"].index(shell)
    session, _ = load_session(scenario_path, shell["session"])
    grants = shell["console_input"]
    granted = [index for index, grant in enumerate(grants) if grant]
    budget = layout["RING_PEAK_BUDGET"]
    context = session_context(sealed, bins)
    roles = context["roles"]
    # The session's first focus step, and the negative before any focus.
    first = next(index for index, row in enumerate(session["steps"])
                 if "focus" in row)
    before = {"negative": "before-focus"}

    def variant(key, value):
        def mutate(data):
            if value is None:
                del data["variants"][at][key]
            else:
                data["variants"][at][key] = value
        return ("variant", mutate)

    def steps(change):
        def mutate(data):
            data["steps"] = change(list(data["steps"]))
        return ("session", mutate)

    def field(key, value):
        def mutate(data):
            data[key] = value
        return ("session", mutate)

    cases = [
        ("a console variant's unknown key", variant("cause", 1),
         "a console variant with other keys"),
        ("a console variant that fails", variant("pass", False),
         "a console variant with other keys, or one that does not pass"),
        ("an init variant not a shell", variant("rdinit", [
            "/init-exit"] + shell["rdinit"][1:]), "init variant"),
        ("a grant without a shell", variant("console_input", [
            True, True] if None in shell["rdinit"] else [True, False]),
         "grants console input other than to the domains its shells run "
         "in"),
        ("a grant without a session", variant("session", None),
         "names a session and grants where it has a shell"),
        ("a shell variant's name", variant("name", "shell"),
         "has a shell but is not named"),
        ("a session's name", variant("session", "shell.json"),
         "is not sessions/<name>.json"),
        ("the session's schema", field("schema", "be-mvp-session-v0"),
         "the session's schema is not be-mvp-session-v1"),
        ("the session's name", field("name", "other"),
         "is not named for its file"),
        ("an unknown action", steps(lambda rows: rows[:1] + [
            {"type": "ls"}] + rows[1:]), "unknown action"),
        ("a focus on no domain", steps(lambda rows: [{"focus": "g2"}] +
                                      rows), "names no domain"),
        ("a line at the prefix", steps(lambda rows: rows[:1] + [
            {"send": "~0"}] + rows[1:]), "a line begins with the focus "
         "prefix"),
        ("an unprintable line", steps(lambda rows: rows[:1] + [
            {"send": "echo \t"}] + rows[1:]), "printable bytes"),
        ("an unknown negative", steps(lambda rows: [{"negative": "loss"}] +
                                      rows), "unknown negative"),
        ("an unknown command", steps(lambda rows: rows[:-2] + [
            {"send": "cat /dev/mem"}] + rows[-2:]),
         "no command a session's expectation knows"),
        ("an expect its send does not print", steps(
            lambda rows: rows[:first + 2] + [{"expect": "not-printed"}] +
            rows[first + 2:]), "is in none of the lines its domain's last "
         "send makes"),
        ("an expect before any send", steps(
            lambda rows: rows[:first + 1] + [{"expect": "#"}] +
            rows[first + 1:]), "is in none of the lines"),
        ("a send before any focus", steps(lambda rows: [
            {"send": "echo NONCE"}] + rows), "no running domain has the "
         "focus"),
        ("a shell left running", steps(lambda rows: rows[:-2]),
         "leaves a shell running"),
        ("a line after its shell's exit", steps(lambda rows: rows + [
            {"send": "echo NONCE"}]), "no running domain has the focus"),
        ("a reason provoked twice", steps(lambda rows: rows[:-2] + [
            {"negative": "bad-sequence"}] * 2 + rows[-2:]),
         "again; only a reason's first drop prints its line"),
        ("input before any focus, after one", steps(
            lambda rows: [row for row in rows if row != before][:2] + [
                before] + [row for row in rows if row != before][2:]),
         "before-focus after a focus"),
        ("a channel write's text over 64 bytes", steps(
            lambda rows: rows[:2] + [{"send": "echo " + "x" * 59}] + rows[2:]
            if roles[granted[0]] != "writer" else rows[:2] + [
                {"send": "be-chan write " + "x" * 65}] + rows[2:]),
         "over 64 bytes" if roles[granted[0]] == "writer" else None),
        ("a denial its role does not have", steps(
            lambda rows: rows[:first + 1] + [
                {"send": "be-deny store-shared"}] + rows[first + 1:]),
         None if roles[granted[0]] in ("host", "reader") else
         "has no store to deny"),
    ]
    if version == 1:
        cases += [
            ("a no-grant with every domain granted", steps(
                lambda rows: rows[:-2] + [{"negative": "no-grant"}] +
                rows[-2:]), "no-grant with every domain granted"),
            ("the hostile guest's grant", ("scenario", lambda data: data[
                "variants"][next(index for index, row in enumerate(data[
                    "variants"]) if row.get("rdinit") and HOSTILE_INIT in
                    row["rdinit"])].update(console_input=[True, False],
                                           session=shell["session"])),
             "grants console input other than to the domains its shells "
             "run in")]
    if version == 3:
        cases += [
            ("a grant to the protected domain", ("variant", lambda data: data[
                "variants"][at].update(rdinit=[SHELL_INIT] * DOMAINS,
                                       console_input=[True] * DOMAINS)),
             "grants console input to the protected domain (Q27)"),
            ("a focus on the ungranted domain", steps(
                lambda rows: rows[:-2] + [{"focus": "g1"}] + rows[-2:]),
             "focus on a domain without the grant"),
            ("a request twice", steps(lambda rows: rows[:3] + [
                {"send": "be-anchor request 7"}] + rows[3:]),
             "request 7 twice")]
    if version >= 2:
        cases.append(("the hostile guest beyond two-guests", (
            "scenario", lambda data: data["variants"].append(dict(
                name="hostile", toolchains=["gcc"], where=["qemu"],
                change="x", **{"pass": True},
                rdinit=[HOSTILE_INIT, None])) or None),
            "the hostile guest is two-guests'"))
    failed, total = [], 0
    for name, (kind, mutate), expected in cases:
        if expected is None:
            continue
        total += 1
        try:
            if kind == "session":
                data = copy.deepcopy(session)
                mutate(data)
                session_plan(parse_session(data, shell["session"]), "0" * 64,
                             shell["session"], grants, context, budget)
            else:
                data = copy.deepcopy(scenario)
                mutate(data)
                check_console(data, binding, layout, dts, version)
                for row in console_variants(data):
                    if row.get("session"):
                        load_session(scenario_path, row["session"])
        except ScenarioError as error:
            if expected not in str(error):
                failed.append(f"{name}: refused for another reason: {error}")
            continue
        failed.append(f"{name}: accepted")
    # D-2's bound: 64 full lines of 256 bytes exceed 0x4000 with slack;
    # the session's own steps stay within it.
    total += 2
    try:
        session_bound(["x" * LINE_BYTES] * 64, budget, "the bound")
        failed.append("the D-2 bound: 64 lines of 256 bytes accepted")
    except ScenarioError as error:
        if "peak budget" not in str(error):
            failed.append(f"the D-2 bound: refused for another reason: "
                          f"{error}")
    try:
        session_plan(session, "0" * 64, shell["session"], grants, context,
                     budget)
    except ScenarioError as error:
        failed.append(f"the scenario's own session: {error}")
    return total, failed


# --------------------------------------------- M9: the measurement log
# The Beryllium log profile, version 1 (mvp/docs/log-profile.md; planning/
# mvp-m9-plan.md, D-1 to D-4): each image's log as its monitor writes it,
# the records in the order of the profile's sequences (3.1), each R3 and
# R4 digest computed here from the build's inputs (the guest's Image and
# the image's own device trees as built, the secret zero-padded, the core
# identity, the console grants), and each domain's expected launch
# register by the profile's recurrence over its launch records' digests
# (tools/policy-check.py's log_register()); the pre-link constants the
# header carries for each image (BE_MVP_LAUNCH_REGISTER_0 and _1, the
# expected count, the scenario's digest, the configuration and policy
# identities, the sequence, and the R2 switch), under the image's variant
# macro where its launch registers differ from the scenario's; and the
# expected :06 LAUNCH, :19, and :20 lines in the profile's positions (4.5)
# for the image's run class (3.2), with each R2 field the link fixes in a
# slot: <Y> a hex64, <Z> a digest, <U> the barrier's ticks. The
# expectation's `log` section holds the same in the export's shapes (5.2),
# a null for a value only the link fixes, and the R4 objects' sources.
# R2 (Q4) is kept: both toolchains' builds reproduce the five ranges'
# bytes exactly, and hart 0 hashes those bytes as the boot image holds
# them (M9-3's determination, recorded in its result).
LOG_R2 = True
LOG_OBJECTS = ("monitor-text", "monitor-rodata", "monitor-input", "mvp-text",
               "mvp-rodata", "core-identity", "console-grants",
               "configuration-identity", "policy-identity", "policy-absent",
               "kernel-image", "device-tree", "secret-page", "close")
R2_OBJECTS = LOG_OBJECTS[:5]
# The R2 ranges whose base the link fixes (src/mvp-monitor.lds's ASSERTs).
R2_BASES = {"monitor-text": "MONITOR_HPA", "monitor-input": "DATA_HPA",
            "mvp-text": "REGION_HPA"}
# Each sequence's count without R2, the close included (3.1).
LOG_COUNTS = {"v1": 8, "v2": 9, "v3": 10, "probe": 4}
LOG_SEQUENCES = {"v1": 1, "v2": 2, "v3": 3, "probe": 4}
LOG_CAPACITY, LOG_ZERO, LOG_LINE_MAX = 41, "00" * 32, 319
SELF_REPORT_FLIP = "self-report-flip"
CANARY = {"symbol": "be_mvp_log_canary", "bit": 0}
SELF_REPORT_FINDING = "self-report differs: mvp-rodata"


def image_dtbs(scenario, variant, dts):
    """An image's device trees, one file name per domain: the scenario's;
    a console variant's tools/gen-dts.py variant where its domain runs
    another init (M7-4); or a variant's own where gen-dts.py makes one for
    that guest (two-guests' init-exit, rdcycle, and sbi-time)."""
    own = [domain["dtb"] for domain in scenario["domains"]]
    if variant is None:
        return own
    if "rdinit" in variant:
        return [own[index] if init is None else
                f"mvp-guest-g{index}-"
                f"{CONSOLE_DTBS[init][version_of(scenario)]}.dtb"
                for index, init in enumerate(variant["rdinit"])]
    listed = {(name, guest) for name, guest, _ in dts.DTBS}
    return [f"mvp-guest-g{index}-{variant['name']}.dtb"
            if (f"mvp-guest-g{index}-{variant['name']}.dtb", index) in listed
            else own[index] for index in range(DOMAINS)]


def run_class(variant, probe=False):
    """The image's run class (3.2): complete, pre-measurement (a failure
    declared before BE_MVP:07 but measurement's), gate-fail (measurement),
    post-launch-failure, or self-report-flip."""
    if probe or variant is None or (variant.get("pass") and
                                    variant["name"] != SELF_REPORT_FLIP):
        return "complete"
    if variant["name"] == SELF_REPORT_FLIP:
        return SELF_REPORT_FLIP
    if variant["fail"] == "measurement":
        return "gate-fail"
    after = variant["after"]
    return "pre-measurement" if after == "none" or after < "BE_MVP:07" \
        else "post-launch-failure"


def guest_files(guest, dts, layout):
    """The guest's Image and every device tree tools/gen-dts.py makes,
    {file name: bytes}, from the guest build directory GUEST; each device
    tree exactly BE_MVP_DTB_BYTES."""
    require(guest, "the log's expected values need --guest, the guest "
            "build directory (the Image and the device trees)")
    directory = pathlib.Path(guest)
    files = {"Image": (directory / "Image").read_bytes()}
    for name, _, _ in dts.DTBS:
        if (directory / name).is_file():
            files[name] = (directory / name).read_bytes()
            require(len(files[name]) == layout["DTB_BYTES"],
                    f"{name} is not {layout['DTB_BYTES']} bytes")
    return files


def hex64(value):
    return None if value is None else f"0x{value:016x}"


def image_log(scenario, variant, probe, binding, layout, files, core, sealed,
              policy, dts, digest):
    """One image's log (sections 2 and 3): its sequence, run class, and
    expected count; its records in the export's shapes (5.2), R2's link-
    fixed values null; each R4 object's source; each domain's expected
    launch register, and the constant the image carries (wrong-measurement's
    one bit off, Q16); and the registers."""
    version = version_of(scenario)
    sequence = "probe" if probe else f"v{version}"
    run = run_class(variant, probe)
    grants = variant["console_input"] if variant and \
        "console_input" in variant else [domain["console_input"]
                                         for domain in binding]
    configured = version > 1
    config = sealed["config"] if configured else LOG_ZERO
    records, ranges, launch = [], [], []
    count = LOG_COUNTS[sequence] + (len(R2_OBJECTS) if LOG_R2 else 0)

    def add(kind, stream, name, representation, base=0, length=0,
            value=LOG_ZERO, domain=None, source=None):
        index = len(records)
        records.append({
            "content": {"base": hex64(base), "expected": 0,
                        "length": hex64(length), "object": name,
                        "outcome": "recorded", "producer": 0,
                        "representation": representation, "type": kind},
            "content_type": "beryllium-log-v1",
            "digests": [{"digest": value, "hashAlg": "sha256"}],
            "recnum": index, "register": stream,
            "srec": sum(1 for record in records
                        if record["register"] == stream)})
        if source is not None:
            ranges.append({"base": hex64(base), "digest": value,
                           "domain": domain, "length": hex64(length),
                           "object": name, "source": source})

    for name in R2_OBJECTS if LOG_R2 else ():
        fixed = layout[R2_BASES[name]] if name in R2_BASES else None
        add("measured", 0, name, "as-placed", fixed, None, None,
            source="boot-image")
    add("measured", 1, "core-identity", "as-computed",
        value=core["identity"])
    add("measured", 1, "console-grants", "as-computed",
        value=policy.console_grants_digest(grants))
    if configured and not probe:
        add("informational", 1, "configuration-identity", "build-recorded",
            value=config)
        add("informational", 1, "policy-identity", "build-recorded",
            value=sealed["report"]["identity"]["policy_identity"])
    else:
        add("informational", 1, "policy-absent", "build-recorded")
    dtbs = image_dtbs(scenario, variant, dts)
    kernel = hashlib.sha256(files["Image"]).hexdigest()
    for domain in range(0 if probe else DOMAINS):
        window = binding[domain]["hpa"] - layout["GUEST_GPA"]
        stream, start = 2 + domain, len(records)
        require(dtbs[domain] in files, f"{dtbs[domain]} is not in --guest")
        add("measured", stream, "kernel-image", "as-placed",
            window + layout["KERNEL_GPA"], len(files["Image"]), kernel,
            domain, "guest/Image")
        add("measured", stream, "device-tree", "as-placed",
            window + layout["DTB_GPA"], layout["DTB_BYTES"],
            hashlib.sha256(files[dtbs[domain]]).hexdigest(), domain,
            "guest/" + dtbs[domain])
        if version == 3 and domain == sealed["prot"]:
            page = sealed["secret_page"]
            secret = bytes.fromhex(sealed["secret"])
            add("measured", stream, "secret-page", "as-placed", page["hpa"],
                page["bytes"], hashlib.sha256(secret + bytes(
                    page["bytes"] - len(secret))).hexdigest(), domain,
                "scenario-secret")
        records[-1]["content"]["outcome"] = "gated-pass"
        launch.append(policy.log_register(
            record["digests"][0]["digest"] for record in records[start:]))
    carried = list(launch)
    if run == "gate-fail":
        prot = sealed["prot"]
        carried[prot] = f"{int(launch[prot][:2], 16) ^ 1:02x}" + \
            launch[prot][2:]
    records.append({
        "content": {"base": hex64(0), "expected": count, "length": hex64(0),
                    "object": "close", "outcome": "none", "producer": 0,
                    "representation": "none", "type": "close"},
        "content_type": "beryllium-log-v1",
        "digests": [{"digest": LOG_ZERO, "hashAlg": "sha256"}],
        "recnum": len(records), "register": None, "srec": 0})
    require(len(records) == count <= 15,
            f"the log holds {len(records)} records, not its sequence's "
            f"{count}, or more than fifteen (stop 6)")
    registers = [None if LOG_R2 else LOG_ZERO, policy.log_register(
        record["digests"][0]["digest"] for record in records
        if record["register"] == 1 and record["content"]["type"] ==
        "measured")] + (launch if launch else [LOG_ZERO] * DOMAINS)
    return {"profile": 1, "sequence": sequence, "run": run,
            "r2": "kept" if LOG_R2 else "dropped", "count": count,
            "header": {"capacity": LOG_CAPACITY,
                       "configuration_identity": config, "count": count,
                       "hashAlg": "sha256", "header_length": 128,
                       "magic": "BEMVPLOG", "record_length": 96,
                       "scenario_sha256": digest, "state": "closed",
                       "version": 1},
            "records": records, "ranges": ranges, "registers": registers,
            "launch_expected": carried, "launch": launch,
            "dtbs": dtbs, "policy": None if not configured or probe else
            sealed["report"]["identity"]["policy_identity"]}


def record_line(record):
    """A record's BE_MVP:19 line (4.3), a slot for each value null."""
    content = record["content"]
    return (f"BE_MVP:19 LOG record seq={record['recnum']} producer=0 "
            f"type={content['type']} stream="
            f"{255 if record['register'] is None else record['register']} "
            f"object={content['object']} repr={content['representation']} "
            f"outcome={content['outcome']} base={content['base'] or '<Y>'} "
            f"length={content['length'] or '<Y>'} dlen=32 "
            f"srec={record['srec']} expected={content['expected']} "
            f"digest={record['digests'][0]['digest'] or '<Z>'}")


def log_lines(log, binding):
    """The image's :06 LAUNCH, block, and :20 lines (4.2 to 4.5), and for
    a failed gate (gate-fail) its block through the gated-fail record and
    its DETAIL line: {"launch", "block", "barrier", "terminal", "detail"}."""
    header = log["header"]
    records = log["records"]
    domains = range(DOMAINS) if log["launch"] else ()
    failing = None
    if log["run"] == "gate-fail":
        failing = next(index for index, value in enumerate(
            log["launch_expected"]) if value != log["launch"][index])
        end = max(index for index, record in enumerate(records)
                  if record["register"] == 2 + failing) + 1
        records = [dict(record) for record in records[:end]]
        records[-1] = dict(records[-1], content=dict(
            records[-1]["content"], outcome="gated-fail"))
        domains = [domain for domain in domains if domain < failing]
    state, count = ("open", len(records)) if failing is not None else (
        "closed", header["count"])
    registers = [value or "<Z>" for value in log["registers"]]
    out = {"launch": [
        f"BE_MVP:06 LAUNCH domain={domain} hart={binding[domain]['hart']} "
        f"register={log['launch'][domain]} expected=match ticks=<T>"
        for domain in domains],
        "block": [
            f"BE_MVP:19 LOG header magic=BEMVPLOG version=1 hlen=128 rlen=96 "
            f"capacity={LOG_CAPACITY} count={count} state={state} "
            f"alg=0x000b scenario={header['scenario_sha256']} "
            f"config={header['configuration_identity']}"] + [
            record_line(record) for record in records],
        "barrier": "BE_MVP:20 REGISTERS at=barrier " + " ".join(
            f"r{index}={value}" for index, value in enumerate(registers)) +
        " ticks=<U>",
        "terminal": "BE_MVP:20 REGISTERS at=terminal " + " ".join(
            f"r{index}={value}" for index, value in enumerate(registers)),
        "detail": None if failing is None else
        f"BE_MVP:DETAIL domain={failing} hart={binding[failing]['hart']} "
        f"computed={log['launch'][failing]} "
        f"expected={log['launch_expected'][failing]}"}
    for text in out["launch"] + out["block"] + [out["barrier"],
                                                out["terminal"]]:
        require(len(text.replace("<Z>", "0" * 64).replace(
            "<Y>", "0x" + "0" * 16).replace("<U>", "0xffffffff").replace(
            "<T>", "0x" + "f" * 16)) <= LOG_LINE_MAX,
                f"a log line is longer than {LOG_LINE_MAX} characters: "
                f"{text}")
    return out


def apply_log(image, log, binding):
    """The log's lines in the image's expectation (4.5): each domain's
    :06 LAUNCH (a probe's none), the block, and the barrier's :20 before
    BE_MVP:07; the terminal :20 before BE_MVP:14; each DOMAIN_TERMINATED
    with the domain's launch register (D-9); for a failed gate, the block
    through the gated-fail record, no :20, and both values in its DETAIL;
    and the `log` section: the sequence, the run class, the count, the
    header, records, ranges, and registers, the launch constants, and the
    lines."""
    lines = log_lines(log, binding)
    entries = [entry for entry in image["control_lines"]
               if not entry["template"].startswith("BE_MVP:06 MEASURED ")]
    at = next(index for index, entry in enumerate(entries)
              if entry["template"].startswith("BE_MVP:07 "))
    added = lines["launch"] + lines["block"] + (
        [lines["barrier"]] if lines["detail"] is None else [])
    image["control_lines"] = entries[:at] + [line(text) for text in added] \
        + entries[at:]
    final = image["final_lines"]
    shutdown = next(index for index, entry in enumerate(final)
                    if entry["template"].startswith("BE_MVP:14 "))
    image["final_lines"] = final[:shutdown] + [line(lines["terminal"])] + \
        final[shutdown:]

    def terminated(entry):
        text = entry["template"]
        if not text.startswith("BE_MVP:12 DOMAIN_TERMINATED "):
            return entry
        domain = int(re.search(r" domain=([0-9]+) ", text).group(1))
        return line(re.sub(r" sha256=\S+ ", f" sha256={log['launch'][domain]} ",
                           text))

    if "domain_control_lines" in image:
        image["domain_control_lines"] = {
            domain: [terminated(entry) for entry in chain]
            for domain, chain in image["domain_control_lines"].items()}
    outcome = image["outcome"]
    if "required_lines" in outcome:
        outcome["required_lines"] = [terminated(entry) for entry in
                                     outcome["required_lines"]]
    if lines["detail"] is not None:
        outcome["detail_lines"] = [line(lines["detail"])]
        failing = int(lines["detail"].split(" domain=", 1)[1].split()[0])
        outcome["absent"] = [f"BE_MVP:06 LAUNCH domain={failing}",
                             "BE_MVP:20", "BE_MVP:07"]
        outcome["expected_hex"] = log["launch_expected"][failing]
    terminal = "none" if log["run"] in ("pre-measurement", "gate-fail") or \
        outcome.get("fallback") else "before-fail" if log["run"] == \
        "post-launch-failure" else "before-shutdown"
    if "measurement" in image:
        # A v3 image's measured domain: its launch inputs, the log's.
        image["measurement"] = dict(image["measurement"], inputs=[
            {"name": name, "bytes": int(entry["length"], 16),
             "sha256": entry["digest"], **({"file": entry["source"][6:]}
                                          if entry["source"].startswith(
                                              "guest/") else {})}
            for name, entry in zip(("kernel", "dtb", "secret_page"), (
                entry for entry in log["ranges"] if entry["domain"] ==
                image["measurement"]["domain"]))])
    image["log"] = dict({key: log[key] for key in (
        "profile", "sequence", "run", "r2", "count", "header", "records",
        "ranges", "registers", "launch_expected")}, terminal=terminal,
        lines=lines, **({"findings": [SELF_REPORT_FINDING], "mutate": CANARY}
                        if log["run"] == SELF_REPORT_FLIP else {}))
    return image


def octets(text):
    return ", ".join(f"0x{octet:02x}" for octet in bytes.fromhex(text))


def log_header(scenario, logs, probes):
    """The header's log constants (struct be_mvp_log_constants,
    src/mvp-log.h): the R2 switch, the scenario's digest, the configuration
    and policy identities, and, for the probes (BE_MVP_PROBE_IMAGE), for
    each variant whose launch registers differ from the scenario's (its
    macro, as the Makefile defines it), and for the scenario's own images,
    the sequence, the expected count, and each domain's expected launch
    register (zero in a probe)."""
    name = scenario["name"]
    base = logs[name]

    def value(macro, text):
        data = bytes.fromhex(text)
        return [f"#define {macro} {{ \\"] + [
            "\t" + ", ".join(f"0x{octet:02x}" for octet in data[at:at + 8]) +
            ", \\" for at in range(0, len(data), 8)] + ["}"]

    def branch(log):
        launch = log["launch_expected"] or [LOG_ZERO] * DOMAINS
        return [f"#define BE_MVP_LOG_SEQUENCE\t\tBE_MVP_C("
                f"{LOG_SEQUENCES[log['sequence']]})",
                f"#define BE_MVP_LOG_EXPECTED_COUNT\tBE_MVP_C({log['count']})"
                ] + value("BE_MVP_LAUNCH_REGISTER_0", launch[0]) + value(
            "BE_MVP_LAUNCH_REGISTER_1", launch[1])

    out = [
        "/*",
        " * The log's pre-link constants (mvp/docs/log-profile.md, 2.5, 2.6;",
        " * planning/mvp-m9-plan.md, D-1 to D-3): whether the image logs",
        " * R2 (Q4); the scenario's digest; the configuration and policy",
        " * identities, zero for a scenario without a report; and, per image,",
        " * its sequence (3.1), its expected count, the close included, and",
        " * each domain's expected launch register, which hart 0's gate",
        " * compares with the domain's register (zero in a probe image).",
        " */",
        f"#define BE_MVP_LOG_R2\t\t\tBE_MVP_C({int(LOG_R2)})"] + value(
        "BE_MVP_LOG_SCENARIO_SHA256", base["header"]["scenario_sha256"]) + \
        value("BE_MVP_LOG_CONFIGURATION_SHA256",
              base["header"]["configuration_identity"]) + value(
        "BE_MVP_LOG_POLICY_SHA256", base["policy"] or LOG_ZERO)
    keyword = "#if"
    if probes:
        out += [f"{keyword} defined(BE_MVP_PROBE_IMAGE)"] + branch(
            logs[probes[0]])
        keyword = "#elif"
    for variant in scenario.get("variants", []):
        log = logs[variant["name"]]
        if log["launch_expected"] == base["launch_expected"]:
            continue
        macro = "BE_MVP_VARIANT_" + variant["name"].upper().replace("-", "_")
        require(re.fullmatch(r"BE_MVP_VARIANT_[A-Z0-9_]+", macro),
                f"variant {variant['name']} has no macro")
        out += [f"{keyword} defined({macro})"] + branch(log)
        keyword = "#elif"
    out += (["#else"] if keyword == "#elif" else []) + branch(base) + (
        ["#endif"] if keyword == "#elif" else []) + [""]
    return out


def bin_count(layout_path):
    """The entries of the guest's /bin (guest/initramfs.list.in, beside
    the layout's src/), which `ls /bin | wc -l` counts."""
    listing = pathlib.Path(layout_path).resolve().parents[1] / "guest" / \
        "initramfs.list.in"
    return len(re.findall(r"^(?:file|slink) /bin/\S+ ", listing.read_text(
        encoding="ascii"), re.M))


def scenario_logs(scenario, binding, layout, files, core_of, sealed, policy,
                  dts, digest):
    """Each image's log (image_log()): the scenario's, each variant's (a v1
    variant with a hart of its own bound to it, its core identity its
    own), and each probe's; and each image's binding."""
    version = version_of(scenario)
    logs, bindings = {}, {}
    for variant in [None] + scenario.get("variants", []):
        changed = copy.deepcopy(binding)
        if variant and "hart" in variant and version == 1:
            changed[variant["domain"]]["hart"] = variant["hart"]
        name = variant["name"] if variant else scenario["name"]
        bindings[name] = changed
        logs[name] = image_log(scenario, variant, False, changed, layout,
                               files, core_of(changed), sealed, policy, dts,
                               digest)
    for probe in scenario.get("probes", []):
        bindings[probe["name"]] = binding
        logs[probe["name"]] = image_log(scenario, None, True, binding,
                                        layout, files, core_of(binding),
                                        sealed, policy, dts, digest)
    return logs, bindings


def generate(scenario_path, layout_path, dts_path, out, policy_path=None,
             negative=None, guest=None, flavour="linux"):
    data = pathlib.Path(scenario_path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    scenario = monitor_variants(flavour_lines(json.loads(data), flavour),
                                flavour)
    layout = layout_constants(layout_path)
    policy_bytes = None
    version = version_of(scenario)
    require(policy_path, "the MVP core profile needs --policy-tool, "
            "tools/policy-check.py")
    policy = load_tool(policy_path, "mvp_policy_check")
    dts = load_tool(dts_path, "mvp_gen_dts")
    # beryllium-cheri: the flavour's DTBs (cap-store's for the CHERI
    # Linux guest).
    dts.select_flavour(flavour)
    if version >= 2:
        scenario, policy_bytes = policy_input(scenario_path, scenario,
                                              policy, negative)
    require(negative is None or version >= 2,
            "--negative names a v2 scenario's build-time negative image")
    binding, sealed = seal(scenario, policy_bytes, layout, dts, policy)
    # A build-time negative never yields a header: the check above stops it.
    require(negative is None, f"the negative image {negative} passes the "
            "policy check")
    files = guest_files(guest, dts, layout)
    out = pathlib.Path(out)
    (out / "expect").mkdir(parents=True, exist_ok=True)

    def core_of(changed):
        return core_config(policy, scenario, changed, layout)

    core = sealed["core"] if sealed else core_of(binding)
    variants = []
    for variant in scenario.get("variants", []) if version == 1 else ():
        if "hart" in variant:
            changed = copy.deepcopy(binding)
            changed[variant["domain"]]["hart"] = variant["hart"]
            variants.append(("BE_MVP_VARIANT_" + variant["name"].upper()
                             .replace("-", "_"), core_of(changed)))
    consoles = [("BE_MVP_VARIANT_" + variant["name"].upper().replace(
        "-", "_"), variant["console_input"]) for variant in
        console_variants(scenario) if "console_input" in variant]
    source = config_source(scenario["name"], digest, core, variants,
                           [domain["console_input"] for domain in binding],
                           consoles)
    (out / CONFIG_FILE).write_text(source, encoding="utf-8")
    listing = [f"scenario {scenario['name']} sha256={digest}",
               f"config {CONFIG_FILE} sha256="
               f"{hashlib.sha256(source.encode()).hexdigest()} "
               f"identity={core['identity']}"]
    config = sealed and sealed.get("config", sealed.get("channel", {}).get(
        "config"))
    if sealed is None:
        images = expectations(scenario, binding, layout, digest, core_of)
    else:
        report = policy.render(sealed["report"])
        report_sha = hashlib.sha256(report).hexdigest()
        (out / REPORT_FILE).write_bytes(report)
        images = (expectations_v2 if version == 2 else expectations_v3)(
            scenario, binding, layout, digest, sealed, report_sha)
        listing += [f"policy {scenario['policy']} "
                    f"sha256={hashlib.sha256(policy_bytes).hexdigest()}",
                    f"report {REPORT_FILE} sha256={report_sha} "
                    f"config={config}"]
    images.update(console_images(
        scenario, scenario_path, images, binding, layout, dts, sealed,
        layout["RING_PEAK_BUDGET"], bin_count(layout_path)))
    # beryllium-cheri: the guest flavour's added lines, and cheri-fault-hs's
    # and cap-store's outcomes.
    cap_store_images(cheri_fault_images(flavour_images(images, flavour)))
    # M9's log (mvp/docs/log-profile.md): each image's constants, records,
    # and lines; the header carries the constants.
    logs, bindings = scenario_logs(scenario, binding, layout, files, core_of,
                                   sealed, policy, dts, digest)
    require(sorted(logs) == sorted(images), "the logs are not the images'")
    for name, image in images.items():
        apply_log(image, logs[name], bindings[name])
    # beryllium-cheri: cap-store's control run, its image's, logged.
    cap_store_control(images)
    (out / "mvp-scenario.h").write_text(
        header(scenario["name"], binding, digest, layout, sealed,
               log_header(scenario, logs, [probe["name"] for probe in
                                           scenario.get("probes", [])])),
        encoding="utf-8")
    listing += [f"session {image['console_input']['session']['file']} "
                f"sha256={image['console_input']['session']['sha256']} "
                f"image={name}" for name, image in sorted(images.items())
                if "console_input" in image]
    listing += [f"log image={name} sequence={log['sequence']} "
                f"run={log['run']} r2={log['r2']} count={log['count']} "
                f"launch={','.join(log['launch_expected']) or 'none'}"
                for name, log in sorted(logs.items())]
    expect_dir = (out / "expect").resolve()
    for image, expectation in images.items():
        path = out / "expect" / f"{image}.json"
        # check() admits only the grammars above; this holds whatever the
        # caller passed.
        require(path.resolve().parent == expect_dir,
                f"image name {image!r} escapes {expect_dir}")
        path.write_text(
            json.dumps(expectation, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
    listing += [f"expect {image}.json" for image in sorted(images)]
    (out / "expect" / "SCENARIO.txt").write_text("\n".join(listing) + "\n",
                                                 encoding="utf-8")
    print(f"BE_MVP_SCENARIO: PASS name={scenario['name']} "
          f"harts=0,{binding[0]['hart']},{binding[1]['hart']} "
          f"images={len(images)} sha256={digest[:12]} "
          f"core={core['identity'][:16]}" +
          (f" config={config}" if sealed else "") +
          f" log={logs[scenario['name']]['sequence']}:"
          f"{logs[scenario['name']]['count']}")


# The profile's run classes at 4bc079db (mvp/docs/log-profile.md, 3.2),
# by image, which the generator's run_class() must give.
PROFILE_RUNS = {
    "complete": ("two-guests", "te-poc", "anchor", "sbi-time", "shim-rule",
                 "hostile", "two-guests-shell", "te-poc-shell",
                 "anchor-shell", "probe-platform", "probe-vmid-distinct",
                 "probe-vmid-shared", "probe-console-input"),
    "pre-measurement": ("payload", "no-sstc", "sbi-3.0", "reader-write",
                        "secret-shared", "response-writable"),
    "gate-fail": ("wrong-measurement",),
    "post-launch-failure": ("exit-budget", "run-timeout", "ring-full",
                            "hart-start", "init-exit", "rdcycle",
                            "no-inject", "no-grant-check"),
    SELF_REPORT_FLIP: (SELF_REPORT_FLIP,)}


def log_self_test(scenario, scenario_path, binding, sealed, layout, files,
                  policy, dts, images):
    """M9's log in the scenario's IMAGES (their expectations as
    generate() builds them): each image's run class the profile's; its
    sequence, count, records, and srec; each launch register from the
    build's bytes; the lines in their places, within the line buffer,
    matching samples; the shell variant's console grants and r1 its own
    with the core identity and CONFIG_SEALED the scenario's; and, where
    the scenario has them, the device-tree variants' registers, the failed
    gate, and the terminated domains' registers. Returns (cases,
    failures)."""
    version, name = version_of(scenario), scenario["name"]
    digest = hashlib.sha256(pathlib.Path(scenario_path).read_bytes()) \
        .hexdigest()

    def core_of(changed):
        return core_config(policy, scenario, changed, layout)

    logs, bindings = scenario_logs(scenario, binding, layout, files, core_of,
                                   sealed, policy, dts, digest)
    for image, expectation in images.items():
        apply_log(expectation, logs[image], bindings[image])
    runs = {image: run for run, names in PROFILE_RUNS.items()
            for image in names}
    failed = []

    def own(log, image):
        """The image's launch registers from the build's bytes, here."""
        out = []
        for domain, dtb in enumerate(log["dtbs"] if log["launch"] else ()):
            values = [hashlib.sha256(files["Image"]).digest(),
                      hashlib.sha256(files[dtb]).digest()]
            if version == 3 and domain == sealed["prot"]:
                secret = bytes.fromhex(sealed["secret"])
                values.append(hashlib.sha256(secret + bytes(
                    0x1000 - len(secret))).digest())
            register = bytes(32)
            for value in values:
                register = hashlib.sha256(register + value).digest()
            out.append(register.hex())
        return out

    def sample(text):
        return text.replace("<Z>", "ab" * 32).replace(
            "<Y>", "0x0000000102008610").replace("<U>", "0x2a3f10").replace(
            "<T>", "0x10a2c0")

    for image, log in sorted(logs.items()):
        lines = images[image]["log"]["lines"]
        records = log["records"]
        streams = [record["register"] for record in records]
        checks = [
            ("the run class", log["run"] == runs.get(image)),
            ("the count", log["count"] == len(records) == LOG_COUNTS[
                log["sequence"]] + 5 * LOG_R2 and records[-1]["content"][
                "object"] == "close" and records[-1]["content"][
                "expected"] == log["count"]),
            ("the sequence", [record["recnum"] for record in records] ==
             list(range(len(records))) and all(
                 record["srec"] == streams[:index].count(record["register"])
                 for index, record in enumerate(records[:-1]))),
            ("the objects' order", [record["content"]["object"] for record
                                    in records] == list(R2_OBJECTS) * LOG_R2
             + ["core-identity", "console-grants"] + (
                 ["configuration-identity", "policy-identity"] if version >
                 1 and log["sequence"] != "probe" else ["policy-absent"]) + (
                 ["kernel-image", "device-tree"] * 2 + ["secret-page"] * (
                     version == 3) if log["sequence"] != "probe" else []) +
             ["close"]),
            ("the gates", [record["content"]["outcome"] for record in records
                           if record["content"]["outcome"] != "recorded"] == (
                ["gated-pass"] * 2 if log["sequence"] != "probe" else []) +
             ["none"]),
            ("the launch registers", log["launch"] == own(log, image)),
            ("the lines' bound and samples", all(
                len(sample(text)) <= LOG_LINE_MAX and re.fullmatch(
                    regex(text), sample(text)) for text in lines["launch"] +
                lines["block"] + [lines["barrier"], lines["terminal"]])),
        ]
        templates = [entry["template"] for entry in images[image][
            "control_lines"]]
        if log["run"] != "gate-fail":
            at = next(index for index, text in enumerate(templates)
                      if text.startswith("BE_MVP:07 "))
            added = len(lines["launch"]) + len(lines["block"]) + 1
            checks.append(("the lines' places", templates[at - added:at] ==
                           lines["launch"] + lines["block"] + [
                               lines["barrier"]] and (log["sequence"] ==
                                                      "probe" or templates[
                               at - added - 1].startswith(
                               "BE_MVP:06 PAYLOAD_PLACED domain=1 ")) and [
                entry["template"] for entry in images[image]["final_lines"]
                ][-2:] == [lines["terminal"],
                           "BE_MVP:14 SHUTDOWN type=0 reason=0"]))
        failed += [f"{image}: {label}" for label, holds in checks
                   if not holds]
    cases = len(logs) * 8
    # The shell variant's grants (Q18): its console-grants record and r1
    # its own, its core identity and CONFIG_SEALED the scenario's.
    shell = f"{name}-shell"
    base = logs[name]
    console = [record["digests"][0]["digest"] for record in logs[shell][
        "records"] if record["content"]["object"] in ("core-identity",
                                                      "console-grants")]
    wanted = policy.console_grants_digest(next(
        variant["console_input"] for variant in scenario["variants"]
        if variant["name"] == shell))
    sealed_lines = {image: next(entry["template"] for entry in images[image][
        "control_lines"] if entry["template"].startswith(
            "BE_MVP:00 CONFIG_SEALED ")) for image in (name, shell)}
    if not (console == [base["records"][5 * LOG_R2]["digests"][0]["digest"],
                        wanted] and logs[shell]["registers"][1] != base[
            "registers"][1] and sealed_lines[name] == sealed_lines[shell]):
        failed.append(f"{shell}: the console grants, r1, or CONFIG_SEALED")
    cases += 1
    if version == 1:
        # The device-tree variants: each domain whose device tree is the
        # variant's own has a launch register of its own, the other the
        # scenario's.
        changed = {image: [index for index in range(DOMAINS) if logs[image][
            "launch"][index] != base["launch"][index]] for image in (
            "init-exit", "rdcycle", "sbi-time", "hostile", shell)}
        if changed != {"init-exit": [1], "rdcycle": [0], "sbi-time": [0, 1],
                       "hostile": [0], shell: [0, 1]}:
            failed.append(f"the device-tree variants' registers {changed}")
        cases += 1
    if version == 3:
        # wrong-measurement (Q16): the protected domain's carried register
        # one bit off; its block through the secret page, gated-fail; both
        # values in its DETAIL; and each terminated domain's register.
        prot, host = sealed["prot"], sealed["host"]
        wrong = images["wrong-measurement"]
        nominal = base["launch"][prot]
        flipped = f"{int(nominal[:2], 16) ^ 1:02x}" + nominal[2:]
        block = [text for text in wrong["log"]["lines"]["block"]]
        terminated = [entry["template"] for entry in images[name][
            "domain_control_lines"][str(prot)] if entry["template"].startswith(
                "BE_MVP:12 DOMAIN_TERMINATED ")] + [
            entry["template"] for entry in images["no-grant-check"]["outcome"][
                "required_lines"] if entry["template"].startswith(
                    "BE_MVP:12 DOMAIN_TERMINATED ")]
        if not (logs["wrong-measurement"]["launch_expected"] == [
                base["launch"][host], flipped] and len(block) == base[
                "count"] and " count=14 state=open " in block[0] and block[
                -1].split(" object=")[1].startswith("secret-page ") and
                " outcome=gated-fail " in block[-1] and wrong["outcome"][
                "detail_lines"][0]["template"] == (
                    f"BE_MVP:DETAIL domain={prot} hart="
                    f"{binding[prot]['hart']} computed={nominal} "
                    f"expected={flipped}") and wrong["log"]["lines"][
                "launch"] == images[name]["log"]["lines"]["launch"][:1] and
                not any(text.startswith(("BE_MVP:20 ", "BE_MVP:06 LAUNCH "
                                         "domain=1 ")) for text in [
                    entry["template"] for entry in wrong["control_lines"]])
                and [text.split(" sha256=")[1].split()[0] for text in
                     terminated] == [nominal, base["launch"][host]]):
            failed.append("wrong-measurement's failed gate, or the terminated "
                          "domains' registers")
        cases += 1
        # self-report-flip (D-4): anchor's registers and lines, and its one
        # finding.
        flip = images[SELF_REPORT_FLIP]
        if not (logs[SELF_REPORT_FLIP]["launch_expected"] == base[
                "launch_expected"] and flip["log"]["findings"] == [
                SELF_REPORT_FINDING] and flip["log"]["lines"] == images[
                name]["log"]["lines"] and flip["outcome"]["pass"] is True):
            failed.append("self-report-flip's registers, lines, or finding")
        cases += 1
    return cases, failed


def self_test(scenario_path, layout_path, dts_path, policy_path=None,
              guest=None, flavour="linux"):
    """Each mutation of the scenario must be refused for its own reason."""
    data = pathlib.Path(scenario_path).read_bytes()
    scenario = monitor_variants(flavour_lines(json.loads(data), flavour),
                                flavour)
    layout = layout_constants(layout_path)
    dts = load_tool(dts_path, "mvp_gen_dts")
    # beryllium-cheri: the flavour's DTBs (cap-store's for the CHERI
    # Linux guest).
    dts.select_flavour(flavour)
    require(policy_path, "the MVP core profile needs --policy-tool, "
            "tools/policy-check.py")
    policy = load_tool(policy_path, "mvp_policy_check")
    files = guest_files(guest, dts, layout)
    if version_of(scenario) >= 2:
        if version_of(scenario) == 3:
            return self_test_v3(scenario_path, scenario, layout, dts,
                                policy, files, bin_count(layout_path))
        return self_test_v2(scenario_path, scenario, layout, dts, policy,
                            bin_count(layout_path), files)
    check(scenario, layout, dts)

    def domain(index, key, value):
        def mutate(data):
            data["domains"][index][key] = value
        return mutate

    def window(index, key, value):
        def mutate(data):
            data["domains"][index]["window"][key] = value
        return mutate

    def absent(index, key):
        def mutate(data):
            del data["domains"][index][key]
        return mutate

    def top(key, value):
        def mutate(data):
            data[key] = value
        return mutate

    def nested(outer, key, value):
        def mutate(data):
            data[outer][key] = value
        return mutate

    def variant(index, key, value):
        def mutate(data):
            data["variants"][index][key] = value
        return mutate

    cases = [
        ("schema", top("schema", "v0"), "schema"),
        ("name", top("name", "Two Guests"), "short lower-case name"),
        ("platform harts", nested("platform", "harts", 4), "platform.harts"),
        ("control hart", nested("platform", "control_hart", 1),
         "control hart is not hart 0"),
        ("timebase", nested("platform", "timebase_hz", 10000000),
         "timebase_hz"),
        ("ring size", nested("rings", "outbound_bytes", 1024), "ring sizes"),
        ("limit", nested("limits", "ready_ticks", "0x1"), "ready_ticks"),
        ("domain hart is hart 0", domain(1, "hart", 0), "control hart"),
        ("domain hart off the platform", domain(0, "hart", 8),
         "not on the platform"),
        ("both domains on one hart", domain(1, "hart", 1),
         "share their hart"),
        ("equal VMIDs", domain(1, "vmid", 1), "VMID, root, or block"),
        ("moved root", domain(0, "root", "0x102038000"),
         "VMID, root, or block"),
        ("moved block", domain(1, "block", "0x102044000"),
         "VMID, root, or block"),
        ("moved window", window(1, "hpa", "0x118000000"), "window"),
        ("bootargs", domain(0, "bootargs", "console=hvc0 -- be.guest=0"),
         "bootargs differs"),
        ("prefix", domain(0, "prefix", "BE_MVP_G1: "), "prefix"),
        ("domain order", domain(1, "index", 0), "out of order"),
        ("dtb", domain(1, "dtb", "mvp-guest-g0.dtb"), "own DTB"),
        ("not a number", domain(0, "vmid", "one"), "not a number"),
        ("concurrency", nested("expect", "concurrency",
                               {"overlap": "any", "alternations": 1}),
         "Q5's floors"),
        ("variant value", variant(1, "run_budget_ticks", "0x200000"),
         "BE_MVP_VARIANT_RUN_BUDGET"),
        ("variant drain delay", variant(3, "drain_delay_ticks", "0x1000000"),
         "BE_MVP_VARIANT_DRAIN_DELAY_TICKS"),
        ("variant hart", variant(4, "hart", 3), "absent hart"),
        # Row F of the RC3 snapshot reviews: a variant's or a probe's name
        # is a file name under expect/ and an image name.
        ("variant named with a path", variant(0, "name", "../x"),
         "variant name '../x' is not a short lower-case name"),
        ("variant named with an absolute path",
         variant(0, "name", "/tmp/x"),
         "variant name '/tmp/x' is not a short lower-case name"),
        ("variant named with a hidden name", variant(0, "name", ".x"),
         "variant name '.x' is not a short lower-case name"),
        ("variant named like the scenario", variant(0, "name", "two-guests"),
         "variant two-guests is named like the scenario"),
        # M9's self-report-flip (planning/mvp-m9-plan.md, D-4): a post-link
        # mutation in that variant alone (anchor's; self_test_v3()).
        ("a mutation in another variant", variant(0, "mutate", CANARY),
         "variant payload is not M9's self-report-flip"),
        ("probe named with a path", nested(
            "probes", 0, dict(scenario["probes"][0], name="probe-../x")),
         "is not named probe-*"),
        ("probe named like a variant", variant(0, "name", "probe-platform"),
         "probe probe-platform is named like another image"),
        # Q10: v1 has no field for a policy or a role.
        ("a v2 field", top("policy", "policy.te"),
         "unknown fields ['policy']"),
        ("a v2 domain field", domain(0, "role", "writer"),
         "unknown fields ['role']"),
        # M7 (planning/mvp-m7-plan.md, D-5): the grant is stated, a boolean.
        ("console input absent", absent(1, "console_input"),
         "domains[1].console_input is not true or false"),
        ("console input a number", domain(0, "console_input", 1),
         "domains[0].console_input is not true or false"),
        ("console input text", domain(1, "console_input", "true"),
         "domains[1].console_input is not true or false"),
    ]
    failed = 0
    for name, mutate, expected in cases:
        data = copy.deepcopy(scenario)
        mutate(data)
        try:
            check(data, layout, dts)
        except ScenarioError as error:
            if expected in str(error):
                continue
            print(f"FAIL {name}: refused for another reason: {error}")
            failed += 1
            continue
        print(f"FAIL {name}: accepted")
        failed += 1
    probes = [probe_lines(probe, layout) for probe in scenario["probes"]]
    templates = [entry["template"] for entry in probes[0]]
    binding = check(scenario, layout, dts)
    core = core_config(policy, scenario, binding, layout)
    firmware = control_lines(scenario["name"], binding,
                             layout, layout["OUTBOUND_RING_BYTES"],
                             layout["RUN_BUDGET"], core=core)[0][4]["regex"]
    platform = probe_control_lines(scenario["probes"][0], binding, layout,
                                   core)
    # The MVP core profile (planning/mvp-m6-plan.md, D-1): the layout's
    # fourteen extents, each window an authority, no channel, and the
    # hart-start variant's hart 9 under its macro, with its own identity.
    changed = copy.deepcopy(binding)
    changed[1]["hart"] = 9
    other = core_config(policy, scenario, changed, layout)
    source = config_source("two-guests", "0" * 64, core,
                           [("BE_MVP_VARIANT_HART_START", other)],
                           [False, True])
    cores = [sealed_line(core).split(" identity=")[0] ==
             "BE_MVP:00 CONFIG_SEALED inventory=14 authorities=2 roots=2 "
             "harts=0,1,2", other["harts"] == [0, 1, 9] and
             other["identity"] != core["identity"], not core["channels"] and
             [row[3] for row in core["authorities"]] == [7, 7],
             "#if defined(BE_MVP_VARIANT_HART_START)\n#define BE_MVP_CORE_"
             "DOMAIN0_HART\t1U\n#define BE_MVP_CORE_DOMAIN1_HART\t9U\n" in
             source and source.count("BE_MVP_CORE_DOMAIN0_HART, 0U }") == 1
             and source.count("BE_MVP_CORE_DOMAIN1_HART, 1U }") == 1]
    for index, held in enumerate(cores):
        if not held:
            print(f"FAIL the MVP core profile, check {index}")
            failed += 1
    sequence = [entry["template"].split(" ", 2)[:2] for entry in platform]
    by_tag = {entry["template"].split(" ", 1)[0]: entry["regex"]
              for entry in platform}
    samples = (
        (probes[0][0]["regex"],
         "BE_MVP:PROBE hsm status=1:1,2:1,3:1,4:1,5:1,6:1,7:1", True),
        (regex("BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 "
               "status=0 ticks=<T>"),
         "BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 "
         "ticks=0x2c26", True),
        (firmware, "BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 "
         "status=1:1,2:1,3:0,4:1,5:1,6:1,7:1 started=3", True),
        (firmware, "BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 "
         "status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none", True),
        (firmware, "BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 "
         "status=1:1,2:0,3:1,4:1,5:1,6:1,7:1 started=2", False),
        (by_tag["BE_MVP:01"], "BE_MVP:01 SCENARIO name=probe-platform "
         "domains=1 harts=0,1 of=8 ring_bytes=0x8000 mvp_region=0x102064000 "
         "mvp_bytes=0x40000 image_bytes=0xa4000", True),
        (by_tag["BE_MVP:02"], "BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 "
         "status=1:1,2:0,3:1,4:1,5:1,6:1,7:1 started=2", True),
        (by_tag["BE_MVP:02"], "BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 "
         "status=1:0,2:1,3:1,4:1,5:1,6:1,7:1 started=1", False),
        (by_tag["BE_MVP:10"], "BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 "
         "pc=0x80200000 a0=0x0 a1=0x0 ticks=0x5a6d", True))
    for regular, sample, matches in samples:
        if (re.fullmatch(regular, sample) is not None) != matches:
            verdict = "rejects" if matches else "admits"
            print(f"FAIL regex {regular!r} {verdict} {sample!r}")
            failed += 1
    if len(templates) != 10 or not templates[-1].startswith("BE_MVP:14"):
        print("FAIL the platform probe's lines")
        failed += 1
    # The platform probe's order (src/mvp-runtime.c): hsm after BE_MVP:02,
    # hgatp after both roots, one domain started, no payload lines.
    wanted = ["BE_K3_B3: SHIM", "BE_MVP:00", "BE_MVP:00", "BE_MVP:01",
              "BE_MVP:02", "BE_MVP:PROBE hsm", "BE_MVP:03",
         "BE_MVP:03", "BE_MVP:PROBE hgatp", "BE_MVP:05", "BE_MVP:05",
         "BE_MVP:07", "BE_MVP:08", "BE_MVP:09", "BE_MVP:10"] + \
        ["BE_MVP:PROBE " + kind for kind in scenario["probes"][0]["lines"]
         if kind not in ("hsm", "hgatp")]
    got = [" ".join(pair) if pair[0] in ("BE_K3_B3:", "BE_MVP:PROBE")
           else pair[0] for pair in sequence]
    if got != wanted:
        print(f"FAIL the platform probe's sequence {got}")
        failed += 1
    consoles, failures = console_self_test(
        scenario_path, scenario, layout, dts, binding, None,
        bin_count(layout_path))
    images = expectations(scenario, binding, layout, "0" * 64,
                          lambda changed: core_config(policy, scenario,
                                                      changed, layout))
    images.update(console_images(scenario, scenario_path, images, binding,
                                 layout, dts, None,
                                 layout["RING_PEAK_BUDGET"],
                                 bin_count(layout_path)))
    logged, more = log_self_test(scenario, scenario_path, binding, None,
                                 layout, files, policy, dts, images)
    failures += more
    for failure in failures:
        print(f"FAIL {failure}")
    failed += len(failures)
    total = len(cases) + len(samples) + 2 + len(cores) + consoles + logged
    print(f"BE_MVP_SCENARIO_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total}")
    return 0 if not failed else 1


def self_test_v2(scenario_path, scenario, layout, dts, policy, bins, files):
    """A v2 scenario: each mutation refused for its own reason, among them
    the policy check's structural refusals (tools/policy-check.py's own
    self-test has its analyses) and each build-time negative image; and the
    generated channel, role, denial, and DETAIL lines against the M1 plan's
    text (Markers; Scenarios and the harness)."""
    _, policy_bytes = policy_input(scenario_path, scenario, policy)
    binding, sealed = seal(scenario, policy_bytes, layout, dts, policy)
    config = sealed["channel"]["config"]

    def at(path, value=None, table="scenario"):
        """Set (or, with no value, drop) PATH in a copy of the scenario or
        of the layout."""
        def mutate(data, values):
            node = data if table == "scenario" else values
            for step in path[:-1]:
                node = node[step]
            if value is None:
                del node[path[-1]]
            else:
                node[path[-1]] = value
        return mutate

    def both(*mutations):
        def mutate(data, values):
            for one in mutations:
                one(data, values)
        return mutate

    g1 = scenario["domains"][1]["bootargs"]
    cases = [
        ("an unknown field", at(("delegations",), []),
         "unknown fields ['delegations']"),
        ("an unknown domain field", at(("domains", 0, "colour"), "red"),
         "domains[0] has unknown fields ['colour']"),
        ("a moved pool", at(("objects", 1, "bytes"), "0x8000"),
         "pool is not the layout's extent"),
        ("a channel GPA not Q1's", at(("channels", 0, "gpa"), "0x84001000"),
         "channel0's GPA is not Q1's"),
        ("a window over the channel page", both(
            at(("domains", 1, "window", "hpa"), "0x114001000"),
            at(("G1_HPA",), 0x114001000, "layout")),
         "G1's window overlaps shared_page"),
        ("the layout's channel elsewhere",
         at(("CHANNEL_HPA",), 0x119000000, "layout"),
         "BE_MVP_CHANNEL_HPA is not Q1's"),
        ("a layout without the channel",
         at(("CHANNEL_GPA",), None, "layout"),
         "BE_MVP_CHANNEL_GPA is not Q1's"),
        ("a monitor extent left out", at(("objects", 0)),
         "lacks a monitor extent"),
        ("rights out of order",
         at(("channels", 0, "writer_rights"), ["write", "read"]),
         "is not rights in the order"),
        ("two channels allowed", at(("CHANNELS_MAX",), 2, "layout"),
         "exactly one channel"),
        ("no level-0 page", at(("G1_LEVEL0_HPA",), None, "layout"),
         "no level-0 page"),
        ("a policy outside the directory", at(("policy",), "../x.te"),
         "policy does not name a .te file"),
        ("a swapped role", at(("domains", 0, "role"), "reader"),
         "domains[0].role is not writer"),
        ("a denied fetch", at(("domains", 0, "deny", 0, "access"), "fetch"),
         "not a load or a store (Q3)"),
        ("a denial in the window",
         at(("domains", 0, "deny", 0, "gpa"), "0x80001000"),
         "in its own window"),
        ("the writer's store to the page", at(
            ("domains", 0, "deny", 0), {"access": "store",
                                        "gpa": "0x84000ff8"}),
         "an access the channel page grants"),
        ("a misaligned denial",
         at(("domains", 1, "deny", 1, "gpa"), "0x90000004"),
         "doubleword-aligned"),
        ("a denial above 2^41",
         at(("domains", 1, "deny", 1, "gpa"), "0x20000000000"),
         "below 2^41"),
        ("expected denials of another kind",
         at(("expect", "denials", "1", 0, "kind"), "unmapped"),
         "expect.denials"),
        ("no denial entry", at(("accepted_exits",),
                               scenario["expect"]["exit_classes"]),
         "accepted_exits is not"),
        ("window rights", at(("domains", 1, "window", "rights"),
                             ["read", "write"]), "(V4)"),
        ("M0's DTB", at(("domains", 1, "dtb"), "mvp-guest-g1.dtb"),
         "own DTB"),
        ("bootargs", at(("domains", 1, "bootargs"),
                        g1.rsplit(" be.deny=", 1)[0]), "bootargs differs"),
        ("a command line with no <bootargs>",
         at(("expect", "domain_lines", 2), "[<s>] Kernel command line: x"),
         "does not hold one"),
        ("the report's grants", at(("expect", "report", "grants"), 7),
         "expect.report"),
        ("reader-write's walked leaf",
         at(("variants", 0, "walked"), "0x46000053"),
         "variant reader-write is not"),
        ("no-inject's first faults",
         at(("variants", 1, "first_fault", 1, "htval"), "0x21000400"),
         "variant no-inject is not"),
        ("no-inject with the denial entry",
         at(("variants", 1, "accepted_exits"), scenario["accepted_exits"]),
         "variant no-inject is not"),
        ("variant named with a path", at(("variants", 0, "name"), "../x"),
         "variant name '../x' is not a short lower-case name"),
        ("variant named like the scenario",
         at(("variants", 0, "name"), "te-poc"),
         "variant te-poc is named like the scenario"),
        ("a probe image", at(("probes",), [{"name": "probe-platform",
                                            "lines": ["hsm"]}]),
         "no probe images"),
    ]
    negatives = sorted(path.stem for path in (pathlib.Path(
        scenario_path).parent / "negatives").glob("*.json"))
    failed = []
    for name, mutate, expected in cases + [
            (f"negative {negative}", negative, "the policy check fails, "
             "so no header") for negative in negatives]:
        data, values = copy.deepcopy(scenario), dict(layout)
        try:
            if isinstance(mutate, str):
                data, text = policy_input(scenario_path, data, policy,
                                          mutate)
            else:
                mutate(data, values)
                data, text = policy_input(scenario_path, data, policy)
            seal(data, text, values, dts, policy)
        except ScenarioError as error:
            if expected not in str(error):
                failed.append(f"{name}: refused for another reason: "
                              f"{error}")
            continue
        failed.append(f"{name}: accepted")
    # The MVP core profile against the report (stop condition 11): an
    # authority no grant has, and a resource no object holds.
    agreements = (("an authority dropped", "authorities", None,
                   "are not the proposal's authorities"),
                  ("a resource outside the objects", "resources",
                   [99, 0x200000000, 0x1000, 6], "lies in no object"))
    for name, key, row, expected in agreements:
        core = copy.deepcopy(sealed["core"])
        core[key].append(row) if row else core[key].pop()
        try:
            core_agrees(sealed["report"], core)
            failed.append(f"{name}: accepted")
        except ScenarioError as error:
            if expected not in str(error):
                failed.append(f"{name}: refused for another reason: "
                              f"{error}")
    # The generated lines, as the M1 plan states them.
    before = [entry["template"] for entry in control_lines(
        scenario["name"], binding, layout, layout["OUTBOUND_RING_BYTES"],
        layout["RUN_BUDGET"], channel=sealed["channel"],
        core=sealed["core"])[0]]
    tags = [" ".join(text.split(" ", 2)[:2]) for text in before]
    images = expectations_v2(scenario, binding, layout, "0" * 64, sealed,
                             "0" * 64)
    mine, deny = images[scenario["name"]], images[scenario["name"]][
        "denials"]
    plan_lines = {
        "0": ["MVPINIT 07 CHANNEL role=writer gpa=0x84000000 bytes=4088 "
              "digest=<x> flag=0x42454d314348414e",
              "MVPINIT 08 DENIED n=1 kind=load gpa=0x84001000 va=<v> pc=<p> "
              "signo=11 code=2 observed=1"],
        "1": ["MVPINIT 07 CHANNEL role=reader gpa=0x84000000 bytes=4088 "
              "digest=<x> polls=<n> match=1",
              "MVPINIT 08 DENIED n=1 kind=store gpa=0x84000ff8 va=<v> "
              "pc=<p> signo=11 code=2 observed=1 unchanged=1",
              "MVPINIT 08 DENIED n=2 kind=load gpa=0x90000000 va=<v> "
              "pc=<p> signo=11 code=2 observed=1"]}
    stem = "earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1"
    checks = [
        ("the bootargs", [domain["bootargs"] for domain in binding] == [
            f"{stem} -- be.guest=0 be.role=writer be.channel=0x84000000 "
            "be.deny=load@0x84001000",
            f"{stem} -- be.guest=1 be.role=reader be.channel=0x84000000 "
            "be.deny=store@0x84000ff8,load@0x90000000"]),
        ("CHANNEL_CHECKED", before[tags.index("BE_MVP:03 CHANNEL_CHECKED")]
         == "BE_MVP:03 CHANNEL_CHECKED channel=0 writer=0 reader=1 "
         "gpa=0x84000000 hpa=0x118000000 bytes=0x1000 "
         "level0=0x102039000,0x102041000 writer_pte=0x460000d7 "
         f"reader_pte=0x46000053 config={config}"),
        ("the channel lines' places", tags[5:13] == [
            "BE_MVP:03 GSTAGE_BUILT_REWALKED"] * 2 + [
            "BE_MVP:03 CHANNEL_CHECKED", "BE_MVP:04 PAYLOAD_CHECKED"] + [
            "BE_MVP:05 DOMAIN_RAM_CLEARED"] * 2 + [
            "BE_MVP:05 CHANNEL_CLEARED", "BE_MVP:06 PAYLOAD_PLACED"]),
        ("CHANNEL_CLEARED", re.fullmatch(mine["control_lines"][11]["regex"],
                                         "BE_MVP:05 CHANNEL_CLEARED "
                                         "channel=0 hpa=0x118000000 "
                                         "bytes=0x1000 ticks=0x1f2e")),
        ("the roles' lines", {
            index: [text for text in lines if text.startswith(
                ("MVPINIT 07", "MVPINIT 08"))]
            for index, lines in mine["domain_lines"].items()} == plan_lines
         and [lines.index(text) for lines in mine["domain_lines"].values()
              for text in lines if text.startswith(("MVPINIT 02",
                                                    "MVPINIT 07"))]
         == [7, 8, 7, 8]),
        ("a DENY line", re.fullmatch(
            deny["1"][0]["line"]["regex"], "BE_MVP:DENY hart=2 domain=1 "
            "seq=1 kind=read-only cause=0x17 injected=0x7 gpa=0x84000ff8 "
            "htval=0x210003fe htinst=0x0 stval=0x3fd77f2ff8 sepc=0x10b2c "
            "vsstatus=0x200000020 vstvec=0xffffffff80a01234 ticks=0x5d21a "
            "service=0x3c")),
        ("a load's DENY line injects 0x5", deny["0"][0]["line"][
            "template"].count(" cause=0x15 injected=0x5 ") == 1 and
         [len(deny[index]) for index in ("0", "1")] == [1, 2]),
        ("reader-write's DETAIL", images["reader-write"]["outcome"][
            "detail_lines"][0]["template"] == "BE_MVP:DETAIL channel=0 "
         "domain=1 hart=2 walked=0x460000d7 declared=0x46000053" and
         "BE_MVP:03 CHANNEL_CHECKED" not in str(
             images["reader-write"]["control_lines"])),
        ("no-inject's DETAIL", [bool(re.fullmatch(
            entry["regex"], "BE_MVP:DETAIL domain=1 hart=2 cause=0x17 "
            "pc=0x10b2c tval=0x3fd77f2ff8 htval=0x210003fe htinst=0x0 "
            "spvp=0 vsatp=0x8000000000081234 exits=97"))
            for entry in images["no-inject"]["outcome"]["detail_lines"]]
         == [False, True] and "denial" not in images["no-inject"][
             "accepted_exits"]),
        ("the header's record and identity", all(text in header(
            scenario["name"], binding, "0" * 64, layout, sealed) for text in (
            "#define BE_MVP_SCENARIO_ACCEPT_DENIAL\tBE_MVP_C(1)",
            "(BE_MVP_GSTAGE_RIGHT_READ | BE_MVP_GSTAGE_RIGHT_WRITE)",
            f'"{config}"', f"0x{config[:2]}, 0x{config[2:4]}, "))),
    ]
    failed += [f"{name}: differs" for name, holds in checks if not holds]
    consoles, failures = console_self_test(scenario_path, scenario, layout,
                                           dts, binding, sealed, bins)
    failed += failures
    images.update(console_images(scenario, scenario_path, images, binding,
                                 layout, dts, sealed,
                                 layout["RING_PEAK_BUDGET"], bins))
    logged, failures = log_self_test(scenario, scenario_path, binding, sealed,
                                     layout, files, policy, dts, images)
    failed += failures
    for failure in failed:
        print(f"FAIL {failure}")
    total = len(cases) + len(negatives) + len(checks) + len(agreements) + \
        consoles + logged
    print(f"BE_MVP_SCENARIO_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total}")
    return 0 if not failed else 1


def self_test_v3(scenario_path, scenario, layout, dts, policy, files,
                 bins):
    """A v3 scenario: each mutation refused for its own reason, among them
    the policy check's structural refusals and each build-time negative
    image; the generated page, secret, management, request, role, and
    DETAIL lines and the header against the M2 plan's text (Markers; Q1,
    Q3, Q5 to Q10), and the probe's spv=<S> (Plan revision M2-A.1); and
    M9's log (log_self_test())."""
    _, policy_bytes = policy_input(scenario_path, scenario, policy)
    binding, sealed = seal(scenario, policy_bytes, layout, dts, policy)
    config = sealed["config"]

    def at(path, value=None):
        """Set (or, with no value, drop) PATH in a copy of the scenario."""
        def mutate(data, values):
            node = data
            for step in path[:-1]:
                node = node[step]
            if value is None:
                del node[path[-1]]
            else:
                node[path[-1]] = value
        return mutate

    def both(*mutations):
        def mutate(data, values):
            for one in mutations:
                one(data, values)
        return mutate

    g1, calls = scenario["domains"][1]["bootargs"], scenario["expect"]["mgmt"]
    flip = next(index for index, entry in enumerate(scenario["variants"])
                if entry["name"] == SELF_REPORT_FLIP)
    cases = [
        ("an unknown field", at(("delegations",), []),
         "unknown fields ['delegations']"),
        ("a v2 channel", at(("channels",), []), "unknown fields ['channels']"),
        ("variant named with a path", at(("variants", 0, "name"), "../x"),
         "variant name '../x' is not a short lower-case name"),
        ("variant named like the scenario",
         at(("variants", 0, "name"), "anchor"),
         "variant anchor is named like the scenario"),
        # M9's self-report-flip (planning/mvp-m9-plan.md, D-4): the canary's
        # one bit and its one finding, and the variant itself.
        ("self-report-flip without its finding",
         at(("variants", flip, "findings"), []),
         "is not M9's self-report-flip"),
        ("self-report-flip of another constant",
         at(("variants", flip, "mutate"),
            {"symbol": "be_mvp_log_constants", "bit": 0}),
         "is not M9's self-report-flip"),
        ("self-report-flip missing", at(("variants",), [
            entry for entry in scenario["variants"]
            if entry["name"] != SELF_REPORT_FLIP]),
         "the variants are not the plan's"),
        ("a probe image", at(("probes",), []), "unknown fields ['probes']"),
        ("an unknown domain field", at(("domains", 0, "colour"), "red"),
         "domains[0] has unknown fields ['colour']"),
        ("a page outside Q1's", at(("pages", 2, "gpa"), "0x84003000"),
         "secret_page is not Q1's page 2"),
        ("a second grant, with no rule", at(("grants",), scenario["grants"] + [
            {"from": 1, "to": 0, "permissions": ["pause"]}]),
         "the policy check fails, so no header"),
        ("a role of M1's", at(("domains", 0, "role"), "writer"),
         "roles are not host and prot"),
        ("swapped roles", both(at(("domains", 0, "role"), "prot"),
                               at(("domains", 1, "role"), "host")),
         "the pages are not the host's request page"),
        ("a response page the host does not read",
         at(("pages", 1, "rights", 0), []), "pages[1]'s rights are not"),
        ("a 31-byte secret", both(at(("secret", "hex"), "00" * 31),
                                  at(("secret", "bytes"), "0x1f")),
         "the secret is not Q5's 32 bytes"),
        ("the host measured", at(("measurement", "domain"), 0),
         "the measurement is not the protected domain's"),
        ("a measurement without the identity",
         at(("measurement", "inputs"), ["kernel", "dtb", "secret_page"]),
         "the measurement is not the protected domain's"),
        ("wrong-measurement after M2's measurement line",
         at(("variants", 2, "after"), "BE_MVP:06"),
         "variant wrong-measurement is not"),
        ("a denial in the window",
         at(("domains", 0, "deny", 1, "gpa"), "0x80001000"),
         "in its own window"),
        ("the host's load from the request page",
         at(("domains", 0, "deny", 1), {"access": "load",
                                        "gpa": "0x84000000"}),
         "an access its page's leaf grants"),
        ("the protected domain's store to the response page",
         at(("domains", 1, "deny", 0, "gpa"), "0x84001ff8"),
         "an access its page's leaf grants"),
        ("bootargs", at(("domains", 1, "bootargs"),
                        g1.rsplit(" be.deny=", 1)[0]), "bootargs differs"),
        ("expected denials of another kind",
         at(("expect", "denials", "0", 1, "kind"), "read-only"),
         "expect.denials"),
        ("no management entry", at(("accepted_exits",),
                                   scenario["expect"]["exit_classes"] +
                                   ["denial"]), "accepted_exits is not"),
        ("the host's pause denied", at(("expect", "mgmt", "0", 5, "result"),
                                       SBI_DENIED),
         "gets 0 from hart 0's decision"),
        ("FID 7 answered by hart 0", at(("expect", "mgmt", "0", 3,
                                         "result"), SBI_SUCCESS),
         "gets -2 on its own hart, without a request"),
        ("FID 7 not a refused call", at(("expect", "counters", "refused"),
                                        {"exact": 0}),
         "expect.counters.refused is not exactly the host's 1 calls"),
        ("the host's terminate before its pause",
         at(("expect", "mgmt", "0"), calls["0"][:5] + calls["0"][:4:-1]),
         "gets -10 from hart 0's decision"),
        ("the protected domain's pause granted",
         at(("expect", "mgmt", "1", 1, "result"), SBI_SUCCESS),
         "gets -4 from hart 0's decision"),
        ("a burst of none", at(("expect", "mgmt", "0", 4, "count"), 0),
         "is not a FID, a target, a result, and a count"),
        ("an answered fifth request",
         at(("expect", "requests", 4), {"n": 5, "message": "x"}),
         "expect.requests is not"),
        ("a 65-byte message", at(("expect", "requests", 0, "message"),
                                 "x" * 65), "expect.requests is not"),
        ("domain lines without the protected domain's",
         at(("expect", "domain_lines", "prot")), "expect.domain_lines"),
        ("the report's management grants",
         at(("expect", "report", "management"), []), "expect.report"),
        ("secret-shared's walked leaf",
         at(("variants", 0, "walked"), "0x46000053"),
         "variant secret-shared is not"),
        ("response-writable's declared leaf",
         at(("variants", 1, "declared"), "0x460004d7"),
         "variant response-writable is not"),
        ("wrong-measurement on the host", at(("variants", 2, "domain"), 0),
         "variant wrong-measurement is not"),
        ("no-grant-check under M0's budget",
         at(("variants", 3, "run_budget_ticks"), "0x100000"),
         "variant no-grant-check is not"),
        ("no-grant-check's pause granted",
         at(("variants", 3, "mgmt", "1", 1, "result"), SBI_SUCCESS),
         "gets -10 from hart 0's decision"),
        ("a runtime negative missing", at(("variants",),
                                          scenario["variants"][:3]),
         "the variants are not the plan's"),
    ]
    negatives = sorted(path.stem for path in (pathlib.Path(
        scenario_path).parent / "negatives").glob("*.json"))
    failed = []
    for name, mutate, expected in cases + [
            (f"negative {negative}", negative, "the policy check fails, "
             "so no header") for negative in negatives]:
        data = copy.deepcopy(scenario)
        try:
            if isinstance(mutate, str):
                data, text = policy_input(scenario_path, data, policy,
                                          mutate)
            else:
                mutate(data, None)
                data, text = policy_input(scenario_path, data, policy)
            seal(data, text, layout, dts, policy)
        except ScenarioError as error:
            if expected not in str(error):
                failed.append(f"{name}: refused for another reason: "
                              f"{error}")
            continue
        failed.append(f"{name}: accepted")
    # The generated lines and the header, as the plan states them.
    images = expectations_v3(scenario, binding, layout, "0" * 64, sealed,
                             "0" * 64)
    mine = images[scenario["name"]]
    before = [entry["template"] for entry in mine["control_lines"]]
    tags = [" ".join(text.split(" ", 2)[:2]) for text in before]
    level0 = "level0=0x102039000,0x102041000"
    lines = mine["domain_lines"]
    digest = "cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251"
    detail = {name: images[name]["outcome"].get("detail_lines", [{}])[0].get(
        "template") for name in images if name != scenario["name"]}
    checks = [
        ("the bootargs", [domain["bootargs"].split(" -- ")[1]
                          for domain in binding] == [
            "be.guest=0 be.role=host be.pages=0x84000000,0x84001000,"
            "0x84002000 be.deny=store@0x84001ff8,load@0x84002000,"
            "load@0x114000000,load@0x102064000", "be.guest=1 be.role=prot "
            "be.pages=0x84000000,0x84001000,0x84002000 "
            "be.deny=store@0x84000ff8"]),
        ("Q1's leaves", [page["leaves"] for page in mine["pages"]] == [
            ["0x460000d7", "0x46000053"], ["0x46000453", "0x460004d7"],
            [None, "0x46000853"]]),
        ("the PAGE_CHECKED lines", [text for text in before if text.startswith(
            "BE_MVP:03 PAGE_CHECKED ")] == [
            "BE_MVP:03 PAGE_CHECKED page=0 kind=channel writer=0 reader=1 "
            f"gpa=0x84000000 hpa=0x118000000 bytes=0x1000 {level0} "
            f"writer_pte=0x460000d7 reader_pte=0x46000053 config={config}",
            "BE_MVP:03 PAGE_CHECKED page=1 kind=channel writer=1 reader=0 "
            f"gpa=0x84001000 hpa=0x118001000 bytes=0x1000 {level0} "
            f"writer_pte=0x460004d7 reader_pte=0x46000453 config={config}",
            "BE_MVP:03 PAGE_CHECKED page=2 kind=secret reader=1 "
            f"gpa=0x84002000 hpa=0x118002000 bytes=0x1000 {level0} "
            f"reader_pte=0x46000853 config={config}"]),
        ("the lines' places", tags[5:17] == [
            "BE_MVP:03 GSTAGE_BUILT_REWALKED"] * 2 + [
            "BE_MVP:03 PAGE_CHECKED"] * 3 + ["BE_MVP:04 PAYLOAD_CHECKED"] + [
            "BE_MVP:05 DOMAIN_RAM_CLEARED"] * 2 + [
            "BE_MVP:05 PAGE_CLEARED"] * 2 + ["BE_MVP:05 SECRET_PLACED",
                                             "BE_MVP:06 PAYLOAD_PLACED"]
         and tags[17:19] == ["BE_MVP:06 PAYLOAD_PLACED",
                             "BE_MVP:07 BLOCKS_PUBLISHED"]),
        ("PAGE_CLEARED and SECRET_PLACED", re.fullmatch(
            mine["control_lines"][13]["regex"], "BE_MVP:05 PAGE_CLEARED "
            "page=0 hpa=0x118000000 bytes=0x1000 ticks=0x1f2e") and before[
            15] == "BE_MVP:05 SECRET_PLACED page=2 hpa=0x118002000 "
            "bytes=0x20 ticks=<T>"),
        ("the pause and the termination", [entry["template"] for entry in
                                           mine["domain_control_lines"]["1"]
                                           ][1:] == [
            "BE_MVP:12 DOMAIN_PAUSED hart=2 domain=1 by=0 exits=<N> "
            "ticks=<T>", "BE_MVP:12 DOMAIN_TERMINATED hart=2 domain=1 by=0 "
            "exits=<N> sha256=- ticks=<T>"]),
        ("the MGMT lines", [len(mine["mgmt"][index]) for index in "01"] == [
            13, 2] and re.fullmatch(mine["mgmt"]["0"][11]["line"]["regex"],
                                    "BE_MVP:MGMT hart=1 domain=0 seq=12 "
                                    "fid=pause target=1 result=0 "
                                    "target_state=paused ticks=0x5d21a "
                                    "service=0x3c") and mine["mgmt"]["0"][2][
            "line"]["template"].startswith("BE_MVP:MGMT hart=1 domain=0 "
                                           "seq=3 fid=pause target=2 "
                                           "result=-3 target_state=- ")
            and 7 not in [entry["fid"] for entry in mine["mgmt"]["0"]] and
            mine["requests"]["unanswered_after_seq"] == 12),
        ("mgmt a term of sbi", [(images[name]["exit_sum"], images[name][
            "sbi_terms"][-2:], images[name]["sbi_derived"]) for name in (
                "anchor", "no-grant-check")] == [
            (["sbi", "ipi", "denials"], ["refused", "mgmt"], {"mgmt": {
                "0": {"exact": exact}, "1": {"exact": 2}}})
            for exact in (13, 0)]),
        ("the host's lines", lines["0"][8:25] == [
            MODULE_LINE, "MVPINIT 07 PAGES role=host count=2",
            "MVPINIT 08 DENIED n=1 kind=store gpa=0x84001ff8 va=<v> pc=<p> "
            "signo=11 code=2 observed=1 unchanged=1"] + [
            f"MVPINIT 08 DENIED n={n} kind=load gpa={gpa} va=<v> pc=<p> "
            "signo=11 code=2 observed=1" for n, gpa in (
                (2, "0x84002000"), (3, "0x114000000"), (4, "0x102064000"))]
            + [f"MVPINIT 09 REQUEST n=1 digest={digest}"] + [
            text for text in lines["0"][15:18] if text.startswith(
                "MVPINIT 09 REQUEST n=")] + [
            "MVPINIT 10 MGMT fid=pause target=0 result=-4",
            "MVPINIT 10 MGMT fid=terminate target=0 result=-4",
            "MVPINIT 10 MGMT fid=pause target=2 result=-3",
            "MVPINIT 10 MGMT fid=7 target=1 result=-2",
            "MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8",
            "MVPINIT 10 MGMT fid=pause target=1 result=0",
            "MVPINIT 09 REQUEST n=5 timeout=1"] and lines["0"][25:27] == [
            "MVPINIT 10 MGMT fid=terminate target=1 result=0",
            "MVPINIT 03 STEP n=<i>/8 rounds=<r> t_ms=<t>"]),
        ("the protected domain's lines", lines["1"][8:] == [
            MODULE_LINE, "MVPINIT 07 PAGES role=prot count=3",
            "MVPINIT 08 DENIED n=1 kind=store gpa=0x84000ff8 va=<v> pc=<p> "
            "signo=11 code=2 observed=1 unchanged=1",
            "MVPINIT 10 MGMT fid=terminate target=0 result=-4",
            "MVPINIT 10 MGMT fid=pause target=0 result=-4",
            f"MVPINIT 09 RESPONSE n=1 digest={digest}"] + [
            text.replace("REQUEST", "RESPONSE")
            for text in lines["0"][15:18]]),
        ("the host's refused call", " srst=1 refused=1 lines=<N> " in
         mine["domain_control_lines"]["0"][-1]["template"]),
        ("the probe's spv=<S> (Plan revision M2-A.1), 0 or 1 alone", [
            (entry["template"].rsplit(" ", 1)[1], [bool(re.fullmatch(
                entry["regex"], entry["template"].replace(
                    "<T>", "0x2359c1").replace(SPV, value)))
                for value in ("0", "1", "0x1")])
            for name in ("anchor", "no-grant-check")
            for entry in (chain[0] for chain in images[name][
                "domain_control_lines"].values())] == [
            ("spv=<S>", [True, True, False])] * 4),
        ("the negatives' DETAIL lines", detail == {
            "secret-shared": "BE_MVP:DETAIL page=2 domain=0 hart=1 "
            "walked=0x46000853 declared=0x0",
            "response-writable": "BE_MVP:DETAIL page=1 domain=0 hart=1 "
            "walked=0x460004d7 declared=0x46000453",
            "wrong-measurement": None, "no-grant-check": None,
            SELF_REPORT_FLIP: None}),
        ("the negatives' places", [[entry["template"].split(" ", 3)[2]
                                    for entry in images[name][
                                        "control_lines"] if entry[
                                        "template"].startswith(
                                            "BE_MVP:03 PAGE_CHECKED ")]
                                   for name in ("secret-shared",
                                                "response-writable",
                                                "wrong-measurement")] == [
            [], [], ["page=0", "page=1", "page=2"]] and [
            images[name]["outcome"]["absent"] for name in (
                "secret-shared", "response-writable")] == [
            ["BE_MVP:03 PAGE_CHECKED"]] * 2 and [
            entry["template"].rsplit(" ", 1)[1] for entry in images[
                "no-grant-check"]["control_lines"] if entry[
                "template"].startswith("BE_MVP:07 ")] == [
            "budget_ticks=0x8000000"]),
        ("no-grant-check's termination", [entry["template"] for entry in
                                          images["no-grant-check"]["outcome"][
                                              "required_lines"]] == [
            "BE_MVP:MGMT hart=2 domain=1 seq=1 fid=terminate target=0 "
            "result=0 target_state=terminated ticks=<T> service=<T>",
            "BE_MVP:12 DOMAIN_TERMINATED hart=1 domain=0 by=1 exits=<N> "
            "sha256=- ticks=<T>"] and images["no-grant-check"][
            "domain_lines"]["1"][-2:] == [
            "MVPINIT 10 MGMT fid=terminate target=0 result=0",
            "MVPINIT 10 MGMT fid=pause target=0 result=-10"]),
        ("the header's pages, secret, measured domain, and grants", all(
            text in header(scenario["name"], binding, "0" * 64, layout,
                           sealed) for text in (
                "#define BE_MVP_SCENARIO_PAGES\t\tBE_MVP_C(3)",
                "#define BE_MVP_SCENARIO_PAGE2_WRITER\tBE_MVP_PAGE_NONE",
                "#define BE_MVP_SCENARIO_PAGE2_DOMAIN0_RIGHTS BE_MVP_C(0)",
                "#define BE_MVP_SCENARIO_PAGE1_KIND\tBE_MVP_PAGE_CHANNEL",
                "#define BE_MVP_SCENARIO_SECRET_PAGE\tBE_MVP_C(2)",
                "#define BE_MVP_SCENARIO_MEASURED_DOMAIN\tBE_MVP_C(1)",
                "\t(BE_MVP_MGMT_PAUSE | BE_MVP_MGMT_TERMINATE)",
                "#define BE_MVP_SCENARIO_ACCEPT_MGMT\tBE_MVP_C(1)",
                f'"{config}"',
                "\t0x42, 0x45, 0x2d, 0x4d, 0x56, 0x50, 0x2d, 0x4d, \\"))),
    ]
    failed += [f"{name}: differs" for name, holds in checks if not holds]
    consoles, failures = console_self_test(scenario_path, scenario, layout,
                                           dts, binding, sealed, bins)
    failed += failures
    images.update(console_images(scenario, scenario_path, images, binding,
                                 layout, dts, sealed,
                                 layout["RING_PEAK_BUDGET"], bins))
    logged, failures = log_self_test(scenario, scenario_path, binding, sealed,
                                     layout, files, policy, dts, images)
    failed += failures
    for failure in failed:
        print(f"FAIL {failure}")
    total = len(cases) + len(negatives) + len(checks) + consoles + logged
    print(f"BE_MVP_SCENARIO_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total}")
    return 0 if not failed else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--dts-tool", required=True)
    parser.add_argument("--policy-tool")
    parser.add_argument("--out")
    parser.add_argument("--negative")
    parser.add_argument("--guest")
    parser.add_argument("--self-test", action="store_true")
    # beryllium-cheri: the monitor variant and the guest flavour.
    parser.add_argument("--monitor", choices=tuple(ARMED_HENVCFG),
                        default="riscv")
    parser.add_argument("--guest-flavour", choices=tuple(FLAVOUR_LINES),
                        default="linux")
    args = parser.parse_args(argv[1:])
    global MONITOR
    MONITOR = args.monitor
    # beryllium-cheri: the CHERI-aware monitor's channel-cw, a
    # pre-measurement image by 3.2's rule (run_class()), and its CHERI Linux
    # guest's cheri-fault-hs and cap-store, post-launch failures.
    if MONITOR == "cheri":
        PROFILE_RUNS["pre-measurement"] += (CHANNEL_CW["name"],)
    if MONITOR == "cheri" and args.guest_flavour == "cheri-linux":
        PROFILE_RUNS["post-launch-failure"] += (CHERI_FAULT_HS["name"],
                                                CHERI_CAP_STORE["name"])
    try:
        if args.self_test:
            return self_test(args.scenario, args.layout, args.dts_tool,
                             args.policy_tool, args.guest,
                             args.guest_flavour)
        if not args.out:
            parser.error("--out is required")
        generate(args.scenario, args.layout, args.dts_tool, args.out,
                 args.policy_tool, args.negative, args.guest,
                 args.guest_flavour)
    except (ScenarioError, OSError, ValueError, KeyError, TypeError,
            AttributeError, IndexError) as error:
        print(f"BE_MVP_SCENARIO: FAIL {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
