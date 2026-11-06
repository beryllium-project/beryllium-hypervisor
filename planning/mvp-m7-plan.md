<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M7 plan: interactive guests

This is the bounded plan of milestone M7 of MVP 1.0, which Plan revision
S3-C of the [MVP plan](mvp-plan.md) defines (S3-C.3) and whose acceptance
on 2026-11-01 (exact commit `27d2e557`) authorizes writing. M7 lets a
researcher type into a Linux guest over the one serial console and see
the isolation live, and turns the same demonstrations into evidence a
checker judges. The plan is proposed, not accepted; its acceptance would
authorize M7-2 to M7-6 and nothing else.

## Decision record

The responsible human accepted this plan at exact commit
`4f4d094efb3985435673f7bda62f35ad51c6165e` (parent `f5dc770b`, the
development branch's tip, on branch `beryllium/mvp-m7-plan`) on
2026-11-01 (14:43 in the human's time zone) by the instruction `accept
4f4d094e`, the reply to the
[review packet](mvp-m7-plan-review-summary.md)'s request; the
abbreviation resolves uniquely. No question was answered, so Q1 to Q16
apply at their defaults.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this
  section and the status block's trailing lines were set afterwards.
- **Authorization:** M7-2 to M7-6 on branch `beryllium/mvp-m7` from the
  acceptance-record commit, coding on `claude-opus-5.5` sub-agents at
  the pinned effort and context tier under the session's orchestrating
  model, with Q1 to Q16 at their defaults, under the stop conditions;
  Part 1 Revision 2 as its own exact commit for the human's decision;
  board commands only after the human confirms the board free, with the
  human present, under board policy item 8; no push, merge, tag,
  publication, release step, or kexec use; no claim change beyond the
  sentences fixed in "Claim text"; nothing of M8, M9, or M10. The
  instruction directed no fast-forward or push: the development branch
  stays at `f5dc770b` and this branch is local.
- **Erratum 1 (2026-11-01, stop condition 9):** at the checkpoint after
  M7-4 the counted lines stood at 7,625 of the 8,000 soft limit, and
  M7-5's remaining tooling (the console tool's guest-typing mode with its
  dry-run cases and the `probe-console-input` image) would exceed it; the
  responsible human re-set the limit to **9,500** (instruction `limit
  9500; your choice; board presence`), under the standing rule that a
  soft limit is re-evaluated, never cut. The plan's "Soft limits" text
  is as accepted; this erratum governs.
- **The `model/Makefile` hook (same instruction, `your choice`):** the
  plan enumerated `InputRing.v` and no edit to an accepted model gate
  file (stop 4), so M7-5 gave the module its own gate script; the human
  left the one-line hook that runs it from `make -C model proof` to the
  session's choice, and it is added (`tests/run-input-ring.sh` after
  `tests/run-proofs.sh`), recorded as an M7 departure like debt sweep
  4's `toolcheck` line.
- **The result (2026-11-02):** the M7 result, exact commit
  `e1a6395e038d4dd095960f7a942a87399bdbce18` (parent `8418a377`, the
  gates' commit), is responsible-human accepted by the instruction
  `accept e1a6395e, move k3ctl pin to v1.1`, whose second part the human
  reversed two minutes later (`stop, keep k3ctl pin where it was for
  now, clone a copy if needed`: the pin is unchanged and the tools run a
  copy of the pinned bytes when the checkout's client differs); the
  [M7 result review and acceptance record](mvp-m7-result-review-summary.md)
  carries the decision and the eighteen plan-letter departures, and the
  [M7 evidence record](mvp-m7-evidence.md) the evidence. Only this
  bullet, erratum 2, and the status block's trailing lines were added
  afterwards; the plan text is as accepted.
- **Erratum 2 (noted at the result's acceptance; `mvp/README.md` item
  112):** D-11's session for `two-guests` says "write and read the
  channel" and names denials, but `two-guests`' domains have no role,
  channel, or denial (the scenario is policy-free); the session made and
  accepted with the result is the nonce in each domain, `ls /bin | wc
  -l`, the `bad-sequence` and `literal` negatives, and the exits, and
  the channel and denial demonstrations are `te-poc`'s and `anchor`'s.
  D-11's text is as accepted; this erratum governs.

## Status

```text
m7_status=accepted
m7_plan_target=4f4d094efb3985435673f7bda62f35ad51c6165e
m7_plan_parent=f5dc770b
m7_acceptance_instruction=accept-4f4d094e
m7_acceptance_date=2026-11-01
m7_acceptance_record=mvp-m7-plan-review-summary.md
m7_open_questions_answered=Q1-Q16-defaults
m7_authorization=M7-2..M7-6-on-beryllium/mvp-m7-from-the-acceptance-record;2026-11-01;board-after-the-human-confirms;no-ff-no-push-directed
m7_erratum_1=soft-limit-re-set-8000-to-9500;2026-11-01;instruction-limit-9500;7625-at-the-checkpoint-after-M7-4
m7_makefile_hook=added;model/Makefile-proof-runs-tests/run-input-ring.sh;instruction-your-choice;departure-recorded
m7_implementation_branch=beryllium/mvp-m7
m7_direction=go;2026-11-01;after-the-s3c-acceptance-accept-27d2e557-defaults-ff-push
m7_plan_branch=beryllium/mvp-m7-plan
m7_base=f5dc770b
m7_governing_text=mvp-plan.md-S3-C.3;S3-C.7;S3-C.8-stops-a-i;S3-C.9-item-8;Q27-Q46-defaults
m7_work_packages=M7-1..M7-6
m7_open_questions=Q1-Q16-defaults
m7_soft_limit_lines=8000
m7_board=typed-characterization-only;one-short-session-inside;no-campaign;after-the-human-confirms-the-board-free
m7_authorization_if_accepted=M7-2..M7-6-on-beryllium/mvp-m7-from-the-acceptance-record
m7_result=accepted-e1a6395e038d4dd095960f7a942a87399bdbce18;parent-8418a3777b005debbed8fb5d2d9de54c2bc55250-gates-commit;2026-11-02;instruction-accept-e1a6395e-move-k3ctl-pin-to-v1.1;pin-part-reversed-stop-keep-k3ctl-pin-where-it-was-for-now-clone-a-copy-if-needed;record-mvp-m7-result-review-summary.md;evidence-mvp-m7-evidence.md
m7_erratum_2=D-11-two-guests-session-has-no-channel-or-denial;item-112;noted-2026-11-02
m7_departures=18
m7_stops_fired=9-soft-limit-re-set-by-erratum-1
m7_code_lines=9092-of-9500
m7_checker_to_monitor=2.083
m7_gates=PASS-at-8418a377-2026-11-02-06:14-06:39-UTC;first-run-at-058fee76-failed-evaluate-snapshot-self-test-identity-fixed-in-8418a377
m7_board=20261102-com260-m7;typed-characterization-class-supplies-at-10-and-1-ms;one-two-guests-shell-session-PASS;restored
m7_k3ctl_pin=unchanged-7ca3d78a;copy-of-pinned-bytes-when-the-checkout-differs;item-114
m7_push=none-directed;dev-stays-f5dc770b
m7_successors=M8-M9-plans-on-go-either-first;M10-after-their-results
```

## Purpose

Give the MVP console input. Today the monitor only writes the console:
a guest's `sbi_debug_console_read` is refused for every domain, the
guests run fixed `nolibc` programs, and a reader of the records sees the
isolation only in the printed lines. After M7 a researcher at the serial
line, on the board or in QEMU, selects a domain with a two-byte focus
sequence, gets a BusyBox shell in it, and can: from the writer, write
the shared page and from the reader read it; from either, load an
address no root of that domain maps, or store to a page it may only
read, and get `SIGSEGV` as the denial log records the fault. In `anchor`
the untrusted domain gets the shell and the protected domain does not
(Q27 of S3-C): the secret's bytes never appear in a capture. Scripted
sessions, static files typed line by line, make the same demonstrations
evidence that the capture checker judges in QEMU as a gate; a live
session is a demonstration, not evidence. The claim gains the sentences
S3-C.7 pre-authorizes for M7, fixed in words below; nothing else about
the claim changes.

## Inputs

| Input | Exact commit | Role |
| --- | --- | --- |
| MVP plan with Plan revisions S3-A, S3-B, S3-C | `93967fba`; `0d134bbc`, `f8b77ac9`, `27d2e557` | M7's definition (S3-C.3), the lanes and pre-authorizations (S3-C.7), stops (a) to (i), board policy item 8 (S3-C.9), Q27 to Q46 at their defaults |
| M0 plan with Plan revisions M0-A to M0-C | `4d129808`; `30c5e1a8`, `77559def`, `260ceba6` | the layout, the block, the rings, deliverable 5's fail-closed rule, Q11's budget |
| M1 and M2 plans and results | `7b2c055c`, `ff84533c`; `854a5415`, `18d552bc` | the channel and the denial path; the pages, the management extension, the measurement, the trigger evaluation for Instance 3 |
| M5 plan and result | `0066794d`, `3867c66c` | the board policy as run, the console tool, the keystroke log, the attribution rule |
| M6 plan and result (release candidate 3) | `b2c62d54`, `89ef04e9` | the core profile, the executor and the seams, the markers, the budgets |
| Security model v1 with Revision 1 | `0e3eec8b`, `019cca64` | Part 1 (threat model, assets, TCB), which M7 revises additively; Part 5's triggers |
| M3 result | `b0a0f352` | `Binding.v`'s ring vocabulary, which M7 extends beside it or records as a gap |
| Debt sweeps 3 to 5 | `3b7ab0e3`, `d162c60d`, `e8ab73b7` | the hardened board tools, the one-autoboot rule, the closure from public sources |
| S1 synthesis | `fd670dcd` | H22 (pure parsers host-tested over every input), H08 and H09 (the triggers) |

## Facts the design rests on (read-only findings, 2026-11-01)

Every fact was read in the tree at `f5dc770b`; the line numbers are that
tree's.

- **The block has room.** Each domain hart's 64 KiB block holds the
  stack, the saved and state pages, the inbound ring (4 KiB at `0x4000`)
  and the outbound ring (32 KiB at `0x5000`), and an unused region of
  12 KiB at `0xd000` (`mvp/src/mvp-layout.h` L99-L114); a static assert
  requires the regions to fill the block in that order (L285-L296) and
  each ring's capacity to be a power of two (L297-L303). A record is a
  16-byte header (type, domain, length, reserved, the writer's time) and
  a payload of at most 256 bytes padded to 8 (`mvp-ring.h` L6-L11,
  L33-L40); there are 16 record types, `BE_MVP_RECORDS_INBOUND` the five
  hart 0 writes (`mvp.h` L510-L548), and `be_mvp_ring_init` admits only a
  type mask that is a subset of the outbound or the inbound set
  (`mvp-ring.c` L82-L86). A full ring makes `be_mvp_ring_post` return 0
  and fail the view for good (L170-L173); every writer treats that as a
  failure of the hart or the run (`mvp-hartmain.c` L249-L254,
  `mvp-runtime.c` L1580-L1594): M0 deliverable 5's rule.
- **Hart 0 wakes on IPIs and the budget timer, and on nothing else.**
  Its control loop waits in `wfi` for SSIP or STIP (`mvp-runtime.c`
  L2035-L2056; `mvp-trap.S` L320-L340), checks the budget
  (`be_mvp_control_wake`, `mvp-hart.c` L781-L807), and drains the two
  outbound rings round-robin, one record per domain per pass (M0-C.1;
  L1922-L1981). The one `stimecmp` writer is its executor's
  `be_mvp_exec_arm_budget`, armed once at the run's start (L2088-L2096;
  `mvp-trap.S` L301-L317). Hart 0 prints through the executor's console
  write, which calls firmware DBCN write (`mvp-executor.c` L70-L73;
  `arch/riscv/be/platform.c` L68-L100); the monitor never calls firmware
  DBCN read (`mvp-executor.c` L26-L79).
- **A domain hart reads its inbound ring at four points only**: the IPI
  exit, the management wait, while parked, and in the FAIL wait
  (`mvp-hartmain.c` L279-L352, L405-L407); a guest `wfi` runs natively
  (`mvp.h` L176); a guest DBCN read returns `SBI_ERR_DENIED` for every
  domain, counted (`mvp-sbi.c` L416-L418, L496-L497; `dbcn_read=43` per
  domain per `two-guests` run in the retained records).
- **The write path's window rule is one function.**
  `be_mvp_gstage_translate` refuses a null map, a zero length, a guest
  address below the window, an offset past it, and a length past its end
  with arithmetic that cannot overflow (`mvp-gstage.c` L1033-L1047); the
  map holds the window only, so the channel page and every declared page
  are outside it by construction (`mvp-gstage.h` L553-L566). DBCN write
  checks the whole requested range, then consumes at most 256 bytes
  (`mvp-sbi.c` L391-L414); the domain hart copies them into a stack
  buffer (`mvp-hartmain.c` L258-L273) and `be_mvp_console_feed` holds
  them until LF, stores any byte outside `0x20`-`0x7e` as `?`, and posts
  one LINE record per line (L941-L974); hart 0 prefixes the line and
  re-checks every byte (`mvp-hart.c` L339-L348, L893-L915). The prefixes
  are `BE_MVP_G0: ` and `BE_MVP_G1: ` (`mvp.h` L162-L164).
- **The firmware's identity and the budget.** `BE_MVP_SBI_IMPL_ID 0x4245`,
  version 3, or 4 when the image accepts the management extension
  (`mvp-layout.h` L215-L216; `mvp.h` L72-L82; `mvp-sbi.c` L374-L378); the
  expected kernel line names the version (`scenarios/two-guests/scenario.json`
  L66). The run budget is 2^32 ticks, 178 s at 24 MHz (`mvp-layout.h`
  L203, L401-L402), about 430 s in QEMU at 10 MHz; a guest reboot
  request, `panic=-1` included, ends the whole run (`mvp-sbi.c`
  L443-L447; `mvp-runtime.c` L1703-L1724).
- **The guest.** One Linux `v7.2` Image for both domains, tinyconfig plus
  B6's fragment plus the MVP's (`mvp/tools/build-guest.sh` L27-L40):
  `CONFIG_HVC_RISCV_SBI=y`, `TTY=y`, no `PROC_FS`, `SYSFS`, `DEVTMPFS`,
  `UNIX98_PTYS`, or `MULTIUSER`, no FPU; bootargs `earlycon=sbi
  console=hvc0 panic=-1 oops=panic panic_on_warn=1 -- be.guest=<g>`
  (`mvp/tools/gen-dts.py` L77, L195-L197), the QEMU variants selecting
  their program with `rdinit=` (L260-L271). The initramfs holds
  `/dev/console`, `/dev/mem`, `/dev/be-mgmt`, `/init`, the module, and
  two `argv[0]` symlinks; **no `/dev/hvc0`** (`mvp/guest/initramfs.list.in`
  L14-L21). The init is a static `nolibc` program that never reads
  input, forks a child with a `SIGSEGV` handler for the denials (M1-A),
  and powers off (`mvp/guest/mvp-init.c` L51-L58, L936-L975). Linux's
  `hvc` driver polls, 10 ms while the console is active, backing off to
  2 s when idle (`drivers/tty/hvc/hvc_console.c`, `MIN_TIMEOUT`,
  `MAX_TIMEOUT`). The Image is 1,899,716 bytes; the boot image is
  `0x277000` of its `0x400000` limit (`mvp/guest/pins.txt`;
  `mvp/README.md`), so the Image may grow by about 1.6 MiB.
- **The locked cross GCC has the soft-float multilib.**
  `riscv64-linux-gnu-gcc -print-multi-lib` lists `lib64/lp64` for
  `-march=rv64imac -mabi=lp64` beside `lp64d`, and a static link with
  `-lgcc` under that ABI resolves on this host (checked 2026-11-01): the
  rv64imac/lp64 BusyBox and musl build S3-C names is possible with the
  locked toolchain, without FP in the guest kernel.
- **QEMU and typing today.** `tests/run-qemu.sh` wires the serial line to
  a file and stdin to `/dev/null` (L231-L233); the one tool that types
  into QEMU is the U-Boot rehearsal's `run-qemu-uboot.py`, through a
  stdio chardev and a pipe, one key per 10 ms, Enter only when the echo
  matches, every key logged (L348-L439, L456-L471). On the board the
  console tool types templates through tmux in pieces of at most 60
  characters, echo-checked, every keystroke in `keys.log`, never during
  U-Boot without the gate, and an SPL banner during a wait is stop 12
  (`mvp/tools/k3-console.sh` L29-L86, L557-L582; `mvp/tools/k3-uboot.py`
  L28-L36, L126-L145). The capture checker requires required domain lines
  in order as a subsequence, rejects 20 substrings (`unhandled signal`
  among them), and has no run nonce (`mvp/tests/check-capture.py`
  L1119-L1180; `scenarios/two-guests/scenario.json` L79-L100).
- **Representation today.** The console is neither a policy grant nor a
  configuration fact: DBCN appears only in the exit classes
  (`scenario.json` L110; `gen-scenario.py` L643-L645), the authority
  report has no configuration section (`policy-check.py` L777-L843), and
  the read refusal is one hard-coded branch. The claim has no sentence on
  input, the operator, or the serial line (`mvp/docs/claim.md` L17-L53);
  Part 1 of security model v1 mentions the console once, as a refused
  input in I9 (`planning/security-model-v1.md` L134), and has no console
  or operator in its assets, attackers, or TCB (L145-L198). `Binding.v`'s
  `ring` is a closed inductive with two constructors and its
  `transition` a closed set of twenty (`model/proof/Binding.v` L95-L97,
  L266-L286): an importing module cannot add an input ring to them
  without editing the accepted file, which stop (e) forbids.
- **Sizes.** M1 added 1,614 monitor lines and 6,414 checking lines
  (`mvp/README.md` L4925-L4960); M5's tools came to 7,439 lines at `X2`
  against a limit the human re-set to 10,000. The monitor is 13,848
  lines today; the MVP region holds at most `0x9a88` of `0x40000` bytes
  (Clang `anchor`).

## Design

### D-1 The input path: hart 0 polls, a dedicated ring carries, the domain hart copies

Hart 0's executor gains one function that reads the firmware console
(`sbi_debug_console_read`, DBCN FID 1, into a 64-byte buffer in hart 0's
own HS data, never guest memory) and feeds the bytes to the focus parser
(D-3), which delivers them to the focused domain's **input ring** or
drops them. Hart 0 polls at a fixed cadence from a named wake: its own
Sstc timer, which today arms the run budget once. The timer is re-armed
at every wake to the earlier of the next poll (`BE_MVP_INPUT_POLL_TICKS`,
default 2^18 ticks: 10.9 ms on the board, 26 ms in QEMU; Q2) and the
budget's end, through the same executor function, so the "one `stimecmp`
writer" rule holds and `be_mvp_control_wake`'s budget check is
unchanged. A poll reads at most 256 bytes per wake, so a flooded line
cannot starve the drain, and runs after the drain, between printed
lines. Polling starts when hart 0 prints `BE_MVP:15 INPUT_ARMED` after
the barrier and only in images whose sealed configuration grants console
input to at least one domain (D-5); in every other image hart 0 never
calls the read, prints no new line, and behaves as it does today. Bytes
the firmware held before arming are read and discarded by the first
poll.

The **input ring** is one more single-writer, single-reader ring per
domain hart, 4 KiB at the block's unused offset `0xd000`
(`BE_MVP_INPUT_RING_BYTES 0x1000`; 8 KiB of the region stay unused; the
static asserts extend), hart 0 writing and the domain hart reading, with
the existing header and fences, one new record type `INPUT` (value 16,
payload 1 to 256 bytes) in a third type set of its own, and no IPI and
no control record: the control ring's views pass the five control types
explicitly. The existing `be_mvp_ring_*` functions serve it; `types_valid`
admits the new set. A full input ring **drops and counts** the bytes that
do not fit (D-4): this is the one departure from deliverable 5's rule
and holds for this ring alone, as S3-C's supersession table says.

The domain hart serves **DBCN read** (`a0` = count, `a1` = buffer, `a2`
must be 0) only for a domain whose sealed configuration grants console
input; otherwise `SBI_ERR_DENIED` as today, counted. A served call: a
zero count returns 0 at once; the whole range `[a1, a1 + a0)` is checked
with `be_mvp_gstage_translate` against the domain's own window, so an
overflowing addition, a range crossing the window's end, and a range
naming the channel page or a declared page are refused with
`SBI_ERR_INVALID_PARAM`, no guest byte changed, no queued byte consumed
(the **write-authority** rule, host-tested on each case); then the hart
takes records into a 256-byte staging buffer in its state page (if the
page's static assert admits it; else in the block's remaining unused
bytes), copies `min(a0, 256, queued)` bytes to the guest, keeps the
remainder staged for the next call, and returns the count. The domain
hart reads the input ring at the DBCN-read exit only; it needs no new
wake, because Linux's `hvc` polls. Consequence stated: the first typed
character after two seconds of silence reaches the guest up to 2 s
later (the driver's idle back-off); the typing tool's lockstep absorbs
it.

### D-2 Output volume: a documented bound, not backpressure

The outbound path does not change. A shell's output is unbounded and the
outbound ring fails closed, so this plan takes the first of S3-C's two
designs: a **documented output bound**. The bound is the ring's existing
peak budget, `BE_MVP_RING_PEAK_BUDGET` (`0x4000`, half the ring): a
session is written so that no command's output exceeds it before hart 0
drains, the session checker computes each command's expected output from
the session's expectations and refuses a session file that would exceed
the bound, and the capture checker already reports the ring's peak. A
live session that exceeds it fails the hart as `ring`, ends the run, and
says so: honest, visible, and an availability matter the claim excludes.
The alternative, backpressure through a short DBCN-write count derived
from the domain's own ring against a fixed share (never from the other
domain's demand), is Q3's alternative; it would make `hvc` retry tty
output and drop `printk` text on a zero count, and it changes the fail-
closed property of the outbound ring. Not chosen for 1.0.

### D-3 Focus: a two-byte sequence at line start, a pure parser, a hart-0 line

The focus parser is a pure function over bytes with three states
(`LINE_START`, `AFTER_PREFIX`, `IN_LINE`) and an output of exactly one of:
deliver this byte to the focus; set the focus to domain `d`; drop with a
reason. The prefix byte is `~` (`0x7e`; Q1). At `LINE_START`, `~`
enters `AFTER_PREFIX`; there, `0` or `1` sets the focus to that domain
and returns to `LINE_START`; a second `~` delivers one literal `~` and
enters `IN_LINE`; any other byte is dropped (`bad-sequence`) with the
state returned to `LINE_START`. Any other byte at `LINE_START` or
`IN_LINE` is delivered; CR or LF is delivered and returns the state to
`LINE_START`. There is no timeout and no implicit focus change: routing
never depends on arrival timing. The parser is host-tested over every
byte value in every state (H22), and its table is the specification.

A focus change makes hart 0 print `BE_MVP:16 FOCUS g<d>` (or `none`
before the first), and the typing tool waits for that line before the
next typed line: **lockstep**, one line, then its echo from the focused
domain or an expected token whose text differs from the echo; no
type-ahead. Bytes for no focus, for a domain without the grant, for a
domain that is paused, terminated, or shut down, for a full input ring,
before arming, or in a bad sequence are dropped and counted by reason;
the first drop of each reason prints `BE_MVP:17 INPUT_DROP <reason>`.
Hart 0 keeps per-run accounting (bytes read; per domain, bytes delivered
and a running SHA-256 of them, through the core-held SHA-256 M2 uses;
drops per reason) and prints it once before `BE_MVP:13`:
`BE_MVP:18 INPUT read=N g0=N:<16 hex> g1=N:<16 hex> dropped=<reason>:N,...`.
The record reconciles it with the keystroke log; on the board a mismatch
is a stop (D-9). Focus selects only among domains the configuration
grants; a sequence naming a domain without the grant is a drop
(`no-grant`), not a focus change. The focus bytes join the typing tools'
key sets.

### D-4 Output: unchanged, its two invariants stated and tested

The output path is unchanged in MVP 1.0 and its two invariants are
stated as claims the checker tests: **no guest byte outside `0x20`-`0x7e`
reaches the terminal**, and **every printed line starts with a monitor
tag or the domain's prefix**. Together they stop a guest from forging a
monitor or log line; the first alone stops a guest from making the
operator's terminal answer a query (an escape sequence) into the focused
domain. The console model is line mode (Q44's default): output is held
until LF, so the shell is blind before Enter and the focus line confirms
where input goes. A paused or terminated domain's unterminated last line
is flushed with its prefix by the domain hart before it parks (Q9). A
hostile-guest test (a program that prints every byte value, a look-alike
marker, and a terminal query) is in the host tests and, as a scenario
variant, in QEMU. Relaxing either invariant is stop (h).

### D-5 Representation: mechanism outside the policy; the grant a configuration fact

For MVP 1.0, console input and output are **monitor mechanism outside
the policy**, as console output already is (Q43's default). Which
domains may receive console input is a **configuration fact** of the
scenario: `scenario.json` gains, per domain, `"console_input": true|false`
(the schema version of each scenario increases by one), `gen-scenario.py`
carries it into the generated `mvp-config.c`, so it is validated, sealed,
and read by hart 0 and the domain hart from the sealed configuration,
and the authority report gains a `configuration` section listing it as
a configuration fact beside, and distinct from, `grants`. The policy
notation gains no class; `two-guests` stays policy-free; `anchor`'s
protected domain has `false` (Q27). The claim ledger carries the
non-claim (a new U row: console routing is a mechanism of the control
hart, not a policy-enforced property; the operator and the typing tool
are trusted inputs). The alternative, a console class in the security
model, is not taken.

### D-6 The triggers for console input and focus (H08, H09)

As M2's plan did for Instance 3, this plan evaluates security model v1's
two triggers (Part 5) for the console path. **The capability trigger does
not fire.** The console grant is a static configuration fact sealed
before any domain runs; focus selects only among the granted domains and
is changed only by the operator's typed sequence; nothing is delegated,
attenuated, transferred, or revoked at run time, and no domain can
request, move, or query focus through any monitor interface (a domain
sees only the bytes it is given). **The runtime-check trigger does not
fire.** Hart 0's routing reads the sealed grant and the operator's
selection; no operation is allowed by the mappings or grants and then
denied by a further rule: input to an ungranted domain has no authority
to begin with, like a load of an unmapped address, and the drop is the
absence of a path, not a check over a path. HS evaluates no policy; the
parser is a fixed table. If a later milestone lets a domain hold or pass
focus, or lets the grant change at run time, Part 6 and A7 reopen the
question. Neither answer selects a runtime mechanism; M7 adds no
`decide`, type, or label to HS for the console.

### D-7 Security model v1 Part 1: an additive revision for the console path

Revision 2 of `planning/security-model-v1.md`, appended text only, as
its own exact commit presented for the human's decision before the
result (stop condition 1 as S3-C amended it, by name): the serial console
as an input channel; the **operator and the typing tool as trusted
inputs** (what they type, and what they relay between domains' output
and input, is theirs: not an attacker, not an asset); the assets the
console path touches (the secret, whose bytes never reach a capture; the
focus state and the grants, hart 0's alone); the attackers' new attempts
(a domain forging a monitor line, answering with a terminal query,
influencing focus, or reading another domain's input) and why the two
output invariants and the routing rule bound them; the TCB's additions
(hart 0's poll and parser; the firmware console's read path, which keeps
no input buffer, so loss is possible: an availability matter); two
invariants, I17 (every delivered input byte went to the announced focus,
a domain holding the grant) and I18 (the output invariants); and the
scope line that nothing is claimed about the operator's own relaying.
The revision changes no accepted sentence.

### D-8 `Binding.v`: an importing module for the input ring, and a gap row

Because `Binding.v`'s `ring` and `transition` are closed, M7 adds a new
module `model/proof/InputRing.v` beside it, importing `Binding.v` and
`Policy.v` unedited, that models the input ring alone: its writer (hart
0) and reader (the domain hart), its footprint disjoint from the two
control rings and the guest window, the drop rule, and the single
statement that no transition of the input ring touches a control ring's
objects; three to five theorems, no axiom, `Print Assumptions` closed,
run by the existing gate's escape-pattern check. The ledger gains a gap
row saying `Binding.v`'s hart-binding proof does not cover the input
ring and `InputRing.v` covers it under its own assumptions. If the
module exceeds its soft size (Q10), the gap row alone is recorded and the
module is M8's. No accepted module or gate changes (stop (e)).

### D-9 Userland: BusyBox and musl as pinned external inputs; the shell as a variant

Two external inputs join Linux `v7.2`: **BusyBox** and **musl**, at the
latest upstream stable releases current when M7-2 starts (Q6), each
pinned by exact tag and commit, release-tarball SHA-256, and upstream
signature where published, recorded in `mvp/guest/pins.txt` and the lock
as the Linux pins are, fetched and built by `build-guest.sh`, never
committed. musl is built for `rv64imac`/`lp64` (soft float) with the
locked cross GCC's `lib64/lp64` multilib; BusyBox is built static against
it from an in-tree `.config` that is part of the pin, with the applets
the sessions use and no more (a shell, `echo`, `cat`, `ls`, `printf`,
`sleep`, `test`, `true`, `false`, `head`, `wc`, `hexdump`; Q7's list),
and an Image-size budget of `0x300000` bytes (Q13; the boot image's limit
is `0x400000`). `kernel-repro` grows by the two builds (BusyBox, musl's
`libc.a`) and compares them like the Image. BusyBox is GPL-2.0-only and
musl MIT: no project code is linked into them; `LICENSES/MIT` is added
with the licence check's row for it; no guest image is distributed in
MVP 1.0 (the build products stay under `build/`), and the guide says
how the pinned sources are obtained.

BusyBox lives in the **one Image** either way (Q27). The accepted roles
keep the in-tree init as PID 1; the shell is an `argv[0]` variant of it,
`/init-shell`, selected by `rdinit=/init-shell` in the bootargs of
**interactive variant images** (`shell`) of each scenario (Q4): PID 1
creates `/dev/hvc0` (`c 229 0`, added to the initramfs list), forks,
and in the child calls `setsid`, opens `/dev/hvc0` as the controlling
tty, duplicates it to the standard descriptors, and executes
`/bin/sh`; the parent waits and powers off when the shell exits. The
demonstrations are **helper verbs** of the same init binary, run from
the shell as `argv[0]` symlinks: `be-chan write <text>` and `be-chan
read` (M1's channel code over `/dev/mem`), `be-deny load-unmapped` and
`be-deny store-shared` (the handled-fault child of M1-A, printing the
accepted `SIGSEGV`/`SEGV_ACCERR` lines; never BusyBox `devmem`), and, in
`anchor`'s untrusted domain, `be-anchor request <n>` (M2's host side).
The kernel configuration delta for the shell is expected to be none
(`TTY` and `HVC_RISCV_SBI` are set; `PROC_FS` stays off, Q7); any option
M7-2 finds necessary is a pinned addition to the MVP fragment listed in
the result, and the B6 fragment is not edited. The `nolibc` programs of
M1 and M2 stay as the regression baseline; every accepted scenario
expectation stays intact, the SBI version line excepted (D-10).

### D-10 SBI: the read served, the version raised

`dbcn_read` is served as D-1 says, so the implementation version
increases by D8's rule: `BE_MVP_SBI_IMPL_VERSION` 3 becomes 5, and the
management form 4 becomes 6 (Q11), in every image, because the surface
exists in every image. The expected kernel line of each scenario changes
accordingly: the one change to an accepted scenario's declared lines
this plan makes, named here. `anchor`'s protected domain keeps
`SBI_ERR_DENIED` on read, a declared negative inside an accepted
scenario, now by its configuration fact rather than a universal branch.
The retained records keep their own expectations.

### D-11 Evidence: scripted sessions in QEMU, a session checker, a run nonce

A **session file** is static data: `schema be-mvp-session-v1`, a name,
and a list of steps, each `{"focus": "g0"|"g1"}`, `{"send": "<line>"}`,
or `{"expect": "<text>"}` (Q8), with `NONCE` in a line standing for the
run nonce. It is hashed into the run record (`session_sha256=`) and
never executed: the typist types its lines one by one. Each scenario's
`shell` variant declares one session: `two-guests` (focus each domain,
echo the nonce, write and read the channel, the writer's denied store to
the shared page it may only read, the reader's denied load of an
unmapped address, power off both); `te-poc` (the same with its
instance's denials); `anchor` (the untrusted domain only: the nonce, a
request through the pages and its response, the denials, the protected
domain's management as today, power off). Negatives per session: input
before any focus, a focus sequence naming the ungranted domain
(`anchor`), a literal `~~`, a bad sequence, a deliberate 300-byte line to
overflow the input ring once, and, in `anchor`, nothing typed to the
protected domain.

The **QEMU typist** (`mvp/tests/session-typist.py`, in the pattern of
`run-qemu-uboot.py`'s console class) runs the variant with a stdio
chardev and a pipe, waits for `BE_MVP:15 INPUT_ARMED`, then for each
step: a focus pair, then the `BE_MVP:16 FOCUS` line; a line at one key per
10 ms, then its echo from the focused domain's prefixed line, then the
expected text; every key with its UTC time in `typed.txt`; a 30 s
timeout per step and the run budget overall. Both toolchains run every
declared session as part of `./mvp/mvp check`. The run **nonce** is 16
hex digits the typist draws per run and types in `echo NONCE`; the
checker requires the nonce echoed by the focused domain in each focus
period and nowhere else, so a guest printing a look-alike marker or a
canned transcript satisfies nothing. Matching stays bound to the
accepted check rows: whole lines after the prefix, in order, counted.

The **capture checker** gains: the new monitor lines (`:15` to `:18`),
accepted only for images whose expectations declare console input and
required there; the reconciliation of `BE_MVP:18` with `typed.txt` and
the session file (bytes read ≥ delivered + dropped; per-domain delivered
counts and SHA-256 equal to the session's bytes for that domain's focus
periods; the drop reasons the session provokes present, no other); each
demonstrated denial's `DENIAL` line with its address and cause, the
protected data unchanged; the channel's text read back; the declared
negatives; in `anchor`, the protected domain's delivered count 0 and the
secret's bytes, raw and in hex, absent from the whole capture; and the
output invariants over every domain line. Its mutation self-test grows
by at least twelve: a misrouted byte, a missing focus line, a nonce in
the wrong period, a forged `:18`, a secret in hex, a byte outside the
printable range, a guest byte starting a line, each rejected. Loss,
pacing, and outbound overflow can be shown only on the board and are not
claimed from QEMU.

### D-12 The board: a typed and recorded characterization, no campaign

M7's board work is one **typed characterization** under board policy
item 8 (S3-C.9), after the human confirms the COM260 free and with the
human present: a probe image `probe-console-input` whose hart 0 polls
the firmware read for a fixed window and prints each received byte's
hex and running counts, while a named typist (the human, or the console
tool's guest-typing mode) types a fixed 64-byte text three times at
10 ms per byte and once at 1 ms per byte (Q14), then one short `shell`
session of `two-guests` typed by the tool. The record classifies the
firmware console as one of: supplies input; absent (every read returns
0); blocks (a read does not return; the run times out); loses (count
short, with the rate at each pacing); corrupts (bytes differ). Anything
but "supplies" at 10 ms per byte is stop (f), which returns M7's board
evidence to the human with the QEMU evidence intact. The console tool's
**guest-typing mode** types only the session file's lines and the focus
bytes, each after the hart-0 line that arms input and the focus line
that confirms it, re-gated on a line-start hart-0 line before every
piece, never during U-Boot, no reset during a session, every keystroke
in `keys.log`; a banner during a session aborts it (stop (b)). No
campaign: RC4's campaign (M10) runs the `shell` variants on the board.
Nothing types at U-Boot beyond the accepted templates.

## Claim text (pre-authorized by S3-C.7; fixed here)

The claim's blockquote in `mvp/docs/claim.md` gains, after the sentence
on the tested accesses, one sentence: *"Over the one serial console an
operator may type into a shell in a domain the configuration grants
console input, selecting the domain by a focus sequence; the control
hart delivers each typed byte to the selected domain and to no other,
and no guest byte outside printable ASCII, and no guest byte at the start
of a line, reaches the terminal."* The required limit gains: *"The
guests' software is a test input: unmodified Linux `v7.2`, a static
BusyBox with musl from pinned sources, and the in-tree `nolibc`
programs; a shell in a domain is a demonstration, not evidence that
arbitrary guests are contained. The operator at the console and the
typing tool are trusted inputs: what they type, and what they relay from
one domain's output into another's input, is outside the claim; so are
the loss of typed bytes the firmware console does not buffer and the
availability of a domain that fills its output ring."* The forbidden-
phrasing check must pass; any other claim change is stop (d). The
ledger gains claim rows for the routing and the two output invariants
(methods: host unit test, adversarial test, semantic checker, emulation;
the board column "diagnostic board run" only after the characterization
and RC4's campaign) and the non-claim rows of D-5 and D-8.

## Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M7-1 | This plan; the review packet | the plan accepted |
| M7-2 | Userland: the BusyBox and musl pins, `build-guest.sh`'s fetch, verification, and builds, the BusyBox `.config`, `/dev/hvc0` and `/bin/sh` in the initramfs, `/init-shell` and the helper verbs in `mvp-init.c`, the Image-size budget, `kernel-repro`'s new outputs, `LICENSES/MIT` and the licence check's row; the guide's pin instructions | `guest-pin-check`, `kernel-repro`, and the licence check PASS; the Image within budget; the shell starts on `hvc0` in a hand-run QEMU with the firmware's own console (no monitor input yet) |
| M7-3 | The monitor: the input ring and its type set, the focus parser, hart 0's poll and timer re-arm, the served DBCN read with the write-authority rule, the configuration fact in `mvp-config.c` and the sealed state, the four new lines, the accounting with the core SHA-256, the flush on pause and terminate, the SBI version; host tests (the parser over every byte in every state; the write-authority cases; the ring's drop rule; the accounting) with GCC and Clang output identical; the image checker's rules | `host-test` and `image-check` PASS; the accepted scenarios' QEMU lines and counts unchanged but the version line |
| M7-4 | The harness: the scenarios' schema step, `console_input`, the `shell` variants with their session files, the authority report's `configuration` section, the QEMU typist, the capture checker's rules and mutations, the hostile-guest variant, the session-file bound check, the records (`session_sha256`, `typed.txt`, the nonce); `./mvp/mvp check` | `check` PASS on both toolchains with every declared session typed and judged; the mutation count reported |
| M7-5 | The words and the model: Part 1 Revision 2 as its own commit (for the human); `InputRing.v` or the gap row; the claim sentences and the ledger rows; the guide's console section; `mvp/README.md`; the console tool's guest-typing mode with its dry-run cases (`run-tool-check`) and `probe-console-input` | the revision presented; `claim-ledger check`, `model-check`, and `run-tool-check` PASS |
| M7-6 | The gates from a clean checkout (the lock, `check`, `evaluate`, the U-Boot rehearsal, `kernel-repro`, `model-check`, the model's evaluator); the typed characterization when the human confirms the board; the records; the result packet | the packet presented, with the board step recorded or its wait stated |

Order: M7-2 and M7-3 (independent; M7-3 is testable with the typist
against the `nolibc` init before the shell exists), then M7-4, M7-5,
M7-6. Coding runs on `claude-opus-5.5` sub-agents in worktrees at the
pinned effort and context tier, as M5's and M6's did; the session model
plans, reviews each merge line by line, runs the gates, and writes the
records and the packet (the standing split; D22). Part 1 Revision 2 is
presented to the human as soon as it is written, so that its decision
need not wait for the result.

## Soft limits (re-evaluation stops)

**Counting rule:** added lines by `git diff --numstat` from the M7 base
(this plan's acceptance record) in C, assembly, linker scripts, Python,
shell, Make, and the wrapper, tests included; generated files, fixtures,
JSON (session files among them), Markdown, the BusyBox `.config`, and
the model's Rocq excluded and reported separately. **Limit: 8,000**
(Q41's guide, "M1's monitor work plus a tool effort on M5's scale":
1,614 and 7,439 as recorded). Estimate: the monitor 900 to 1,500; the
init's shell start and helper verbs 400 to 700; the guest build, pins,
and repro 400 to 600; the QEMU typist and session harness 700 to 1,000;
the capture checker and its mutations 800 to 1,300; host tests 900 to
1,300; the scenario generator and the authority report 200 to 400; the
console tool's guest-typing mode and dry-run cases 400 to 600: 4,700 to
7,400. `InputRing.v` reported; its soft size is Q10's. The checking-to-
monitor ratio is reported against M2's 2.3 and not limited (as M4 did).
Checkpoints after M7-3 and after M7-4. A limit exceeded is a stop for
re-evaluation of the limit, never a cut to the work (the human's
direction of 2026-10-28).

## Stop conditions (each returns to the human)

1. Any need to change an accepted R0-R7 or B0-B7 byte, the B6 kernel
   fragment, or an accepted document's text (this plan's own revision,
   Part 1 Revision 2's additive text, and the ports excepted).
2. Any claim-text change other than the sentences fixed above (S3-C's
   stop (d)).
3. Any need to move an MVP-owned extent, the image's base or size, the
   block's accepted regions, or the window, channel, or page addresses;
   the input ring is placed in the unused region only.
4. Any need to change an accepted model file or gate; a global axiom in
   `InputRing.v`; a theorem whose assumption the configuration violates
   (S3-C's stop (e)).
5. A change to an accepted scenario's declared lines or counts in QEMU
   other than the SBI version line; the `shell` variants are new images
   with their own expectations.
6. Any input byte delivered anywhere but to the announced focus holding
   the grant, before arming, or to a domain that is not running, in QEMU
   or on the board (S3-C's stop (g)); on the board, an accounting that
   does not reconcile with the keystroke log.
7. Any need to relax an output invariant (S3-C's stop (h)).
8. The Image over its budget, or a BusyBox or musl release whose tarball
   signature cannot be verified against a published key, or a userland
   that needs FP in the guest kernel (the soft-float build failing).
9. The soft limit exceeded (checkpoints after M7-3 and M7-4).
10. The firmware console absent, blocking, losing, or corrupting input at
    10 ms per byte in the typed characterization (S3-C's stop (f)); a
    banner during a session (stop (b)).
11. The board unavailable or in the other project's use (wait; no board
    command before the human's confirmation; the human present at the
    characterization).
12. Any push, merge, tag, publication, release step, or kexec use.
13. A session whose typed line is not in its file, or a typist that would
    type during U-Boot (item 8).

## Open questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | The focus prefix byte | `~` (`0x7e`): printable, typeable through picocom and tmux, the conserver convention; `~0`, `~1`, `~~` | a control byte (`0x1d`), which some terminals and tmux intercept |
| Q2 | Hart 0's poll cadence and wake | 2^18 ticks (10.9 ms on the board, 26 ms in QEMU) on its own Sstc timer, re-armed each wake to the earlier of the next poll and the budget's end, at most 256 bytes per poll | a shorter cadence; a VS timer interrupt to wake `hvc` (rejected: the driver polls) |
| Q3 | Output volume | the documented bound: a session command's output within the ring's peak budget `0x4000`, checked from the session file; a live overflow fails the hart as `ring` | backpressure by a short DBCN-write count from the domain's own ring |
| Q4 | Where the shells live | `shell` variant images of each scenario (`rdinit=/init-shell`), the accepted images and their expectations intact | a separate `interactive` scenario per instance |
| Q5 | The userland ABI | `rv64imac`/`lp64` soft float with the locked GCC's `lib64/lp64` multilib; no FPU in the guest kernel | FP in the guest kernel and `lp64d` (a monitor change to the guest's FS state; stop 8) |
| Q6 | BusyBox and musl versions | the latest upstream stable releases when M7-2 starts, named with tag, commit, tarball SHA-256, and signature in the pins | Fedora's source RPMs by NEVRA |
| Q7 | The applets, and `PROC_FS` | `sh`, `echo`, `cat`, `ls`, `printf`, `sleep`, `test`, `true`, `false`, `head`, `wc`, `hexdump`; no `PROC_FS` (no `ps`, `free`, `mount`) | more applets within the Image budget; `PROC_FS` as a pinned delta |
| Q8 | The session grammar | JSON `be-mvp-session-v1`: `focus`, `send`, `expect` steps; `NONCE` substituted at typing time; the file's SHA-256 in the record | a line-oriented text format |
| Q9 | A paused or terminated domain's unterminated line | flushed with its prefix by the domain hart before it parks | lost |
| Q10 | `InputRing.v` | written if it stays under 400 Rocq lines with three to five theorems and no axiom; else the gap row alone, the module M8's | the gap row alone |
| Q11 | The SBI version numbers | 5, and 6 with the management extension | 4 and 5 (renumbering the accepted mgmt form; rejected) |
| Q12 | The budget for sessions | scripted sessions within the accepted 2^32 ticks (178 s), each ending with both domains powered off; a `live` variant with 2^35 ticks (24 min on the board) for human sessions, a demonstration and never evidence: the departure from M0's Q11, named | one budget for all |
| Q13 | The Image budget | `0x300000` bytes (the boot image's `0x400000` limit less the monitor and two DTBs, with margin) | enable initramfs compression (`RD_GZIP`; a fragment change) |
| Q14 | The characterization's pacing and text | 64 printable bytes, three times at 10 ms per byte, once at 1 ms per byte; the hex of every received byte printed | more pacings |
| Q15 | The run nonce | 16 hex digits drawn by the typist per run, typed as `echo NONCE`, required echoed in each focus period | none (rejected: look-alike transcripts) |
| Q16 | A steering review of this plan by another model | none (the SOP; S3-C's Q42); run one if the human asks | one review before acceptance |

## What acceptance authorizes

M7-2 to M7-6 on branch `beryllium/mvp-m7` from the acceptance-record
commit, with Q1 to Q16 at their defaults unless answered, under the stop
conditions above; Part 1 Revision 2 as its own exact commit for the
human's decision; board commands only after the human confirms the board
free, with the human present, under board policy item 8; no push, merge,
tag, publication, release step, or kexec use; no change to the claim
beyond the sentences fixed above; nothing of M8, M9, or M10.
