<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M13-4: the probe images

The probes of `planning/mvp-m13-3-review-point.md` (sections 2 and 3), as
two small images booted by U-Boot's `booti` on the K3 COM260, and their
checks. Image 1 holds P1 and P7, image 2 P3, P4, and P2. A third image is
built from a table and an expected list given by path (`make -C mvp
k3-m13-held K3_M13_HELD=DIR`), with every output in that directory. The
board sessions use the MVP's board tools; nothing here touches a board.

## Files

| File | Role |
| --- | --- |
| `src/head.S` | the Image header (B3's, field for field); the entry and its hart check; the entry hart's trap vector; `be_m13_access`, the one routine that touches a device; Base, DBCN write-byte, and SRST calls; the park loop; the 8 KiB stack |
| `src/harts.S` | image 1 alone: P1 on a hart (`be_m13_p1`); the HSM start of another hart and the wait for its report (`be_m13_hart_run`); the started harts' entry and trap vector; four report slots |
| `src/m13.c` | the program: the SBI requirements, the table walked with its guards, every line printed, `END` or a `FAIL` line, SRST |
| `src/m13.h`, `src/m13.lds` | the shared layout and macros; the link (all PROGBITS, at most 64 KiB, the stack last) |
| `src/table-1.S`, `src/table-2.S` | the two tables |
| `tests/expect-1.txt`, `tests/expect-2.txt` | the expected lists, written apart from the tables |
| `tests/m13list.py` | the lists' parser, shared by both checks |
| `tests/check-image.py` | the image check, and its self-test |
| `tests/check-capture.py` | the capture check (`qemu`, `board`, `host`), `--sample`, and its self-test |
| `tests/run-qemu.sh` | the QEMU rows |
| `tests/test-m13.c` | the host test |
| `tests/held-dir.py` | the third image's held directory, checked before anything is made, with a self-test of each refusal |

`make -C mvp k3-m13-images` builds images 1 and 2 under `build/k3-m13/`:
`board/be-mvp-m13-probe{1,2}-gcc.img` (the names of the stage tool's
grammar), each with its ELF, and `qemu/probe{1,2}.{elf,bin}`. Each image is
linked at the board's `0x1_0220_0000` and at QEMU's `0x8020_0000`, and the
board image is made only if the two raw images are byte for byte equal:
the bytes hold no absolute address of the image's own. `make -C mvp
k3-m13-check` (part of `tools-check`) runs every check below.

## The boot path

- **Header and entry.** code0 jumps to `be_m13_entry` at +0x60;
  `text_offset` 0x20_0000; `image_size` the file's size, since the image is
  all PROGBITS. The entry clears `sstatus.SIE` and `sie` first, sets
  `stvec` and the stack, and refuses a hart above 2 (`FAIL entry`, then
  SRST) before any read.
- **SBI.** Base (the specification and implementation, and the probes of
  DBCN, SRST, and HSM), DBCN `debug_console_write_byte` (the byte in `a0`,
  so the firmware reads no memory of the image's), and SRST shutdown, each
  from one routine whose `ecall` has its own label; `satp` must be Bare.
- **Device accesses.** Every one is made by `be_m13_access(index)`: the
  address, the width, and a write's value are the table entry's, for an
  index below the table's length, aligned; a write is of width 4 alone.
  A load or store access fault at one of its three instructions is
  recorded (`fault=` and `tval=`) and passed over; any other trap prints
  `FAIL trap` and requests SRST.
- **Image 1's harts.** P1 runs on the entry hart, then on each other hart
  of 0 to 2, started by SBI HSM at `be_m13_secondary`, which checks `a0`
  again. The entry hart waits for each report at most **2^27 ticks of
  `time`** (about 5.6 s at the board's 24 MHz, 13.4 s at QEMU's 10 MHz),
  ending as soon as the hart reports. Started harts never print: they
  record into their slot and park; the entry hart prints every line.

## The lines

Each line is `BE_K3_M13: ` and a body, printable ASCII, at most 120
characters; every number is `0x` and 16 lower-case digits.

```
ENTRY image=N hart=HEX base=HEX fdt=HEX
SBI spec=HEX impl=HEX impl_version=HEX
EXT dbcn=1 srst=[01] hsm=[01] satp=HEX
HSM hart=HEX error=HEX state=(done|timeout|not-started|refused|trapped)
Pn NAME (read|csrr) a=HEX w=[48] value=HEX
Pn NAME (write|csrw) a=HEX w=[48] wrote=HEX
Pn NAME (read|write) a=HEX w=[48] fault=HEX tval=HEX
Pn NAME guard expect=HEX (pass|fail)
END image=N accesses=HEX faults=HEX
FAIL entry hart=HEX | FAIL sbi srst=[01] hsm=[01] satp=HEX
FAIL hart hart=HEX a0=HEX | FAIL trap hart=HEX scause=HEX sepc=HEX stval=HEX
FAIL table index=HEX
```

`END` or a `FAIL` line is the last line; SRST follows.

## The tables and the lists

A table entry is 64 bytes: address (or P1's CSR number), value, op, width,
probe, P1's hart, a guard's read by index, and a name of at most 23
characters. A list (`tests/m13list.py` has its grammar) states the same
entries apart, with `repeat` blocks for P1's three harts and P4's 31
regions. A guard ends its probe unless its read read its value; P7's
`guard-else` makes the one write that puts `sourcecfg[200]` back to 0,
then ends P7.

## The image check

`tests/check-image.py --image N --expect FILE [--other-base ELF] ELF IMG`
shows from the linked image, each rule a tag on its findings: the header
(B3's rule); the extent (the ELF's segments, PROGBITS, at most 64 KiB, the
stack last); the base (the build at QEMU's base gives the same bytes); the
table is the list; every write is one of the page's (P7's `sourcecfg[200]`
and `target[200]`, P1's `hgeie`); `be_m13_access`, the trap vector,
`be_m13_p1`, and `be_m13_hart_run` are their templates, instruction for
instruction; every store of the assembly lands inside one of the image's
data objects; the C holds no CSR access, `ecall`, AMO, or indirect jump;
every CSR write and read is one of a short list; every `ecall` is at its
label with its registers; HSM starts are made by image 1 alone, for harts
0 to 2; every jump and call goes where it may; no data word is a device
address. `--self-test` makes each mutation of the design (and one for each
rule that the design's table lacks) and requires each to fail by its own
rule.

What rests on code review, not on the image: the C's own loads and stores
through pointers (`m13.c` and B0's unchanged `b0-format.c`), which the
check counts but does not trace; that the program follows the table's
guards (shown by the host test, by QEMU, and by the capture check on every
run); what the firmware and the hardware do with each call and access;
and the wait in seconds: 2^27 ticks of `time` is a number in the image,
and the board's timebase is outside it.

## The capture check

`tests/check-capture.py --image N --mode qemu|board|host --expect FILE
[--qemu-harts H] [--image-file IMG] [--expect-end WORD] CAPTURE` judges a
console capture: from the first line that holds `BE_K3_M13: `, every line
the image's, judged against the list by walking it as the program does,
each outcome taken from the capture. Its verdict line names no directory:
`BE_K3_M13_CAPTURE: PASS|FAIL image=N mode=M end=WORD lines=K`, the end
word one of `end`, `fail-entry`, `fail-sbi`, `fail-hart`, `fail-trap`,
`fail-table`, `stopped`, and `none`.

- **qemu:** OpenSBI v1.6's banner, SBI 2.0, and its boot hart the entry
  hart; base `0x8020_0000`; a read of v1.6's own memory faults, a read of
  RAM above the image does not; no P7 write; HSM states as QEMU's harts
  give.
- **board** (`--image-file`, the staged image): each rule from the
  board's lines in the MVP's public records
  (`mvp/results/20261030-com260-rc2/`, `20261031-com260-rc3/`,
  `20261105-com260-rc4/`, each run's `handoff-excerpt.log`, lines 1 to
  26): one autoboot line; then, once each and in order, the image's size
  read, its MD5 from `0x1_4000_0000`, its move to `0x1_0220_0000` with its
  end, the blob, the blob booted, the device tree loaded to F, and
  `Starting kernel ...`; after it only blank lines, a stamp alone, and the
  BSP's two lines; `ENTRY`'s base `0x1_0220_0000` and its fdt F.
- **host:** the host test's captures, with no line before the image's.

`--sample` prints image N's lines as the board would print them were every
read 0 (P7's first guard then fails), for a stand-in board. `--self-test`
generates runs from the list, wraps each for each mode (the board's from
the RC4 record's loader lines, its size, MD5, and move set to a stand-in
image's), requires each to pass with its end, and then requires each
mutation to fail by its own rule.

## QEMU

`tests/run-qemu.sh` boots the board image's bytes under the pinned OpenSBI
v1.6 (its SHA-256 checked first, the tool lock's
`MVP_PIN_OPENSBI_BIN_SHA256`) and judges each console. This is that
binary's second use: the first is the firmware-version negative, which
`mvp/Makefile`:108-111 names. That file lies under a path that the
proofs' records bind (`planning/mvp-m13-plan.md`, rule 7), and the tool
lock pins the binary; neither changes here, and the binary is used as it
is.

| Row | Image | Machine | Harts | End |
| --- | --- | --- | --- | --- |
| `probe1` | 1 | the MVP's k3-like | 3 | `end`: both other harts done; P1 on three harts; P7's reads fault there, so its guard fails and nothing is written |
| `probe1-one-hart` | 1 | k3-like | 1 | `end`: both HSM starts refused, `not-started` |
| `probe1-no-h` | 1 | no H extension | 1 | `fail-trap`: the first `hgeie` read traps |
| `probe2` | 2 | k3-like | 1 | `end`: P3 and P2 fault (past RAM); P4's regions read RAM; its BARs fault in v1.6's memory |

## The third image

`make -C mvp k3-m13-held K3_M13_HELD=DIR`, run by hand and never in
`check`, builds a
third image from `DIR/table-3.S` on the public build's common objects (the
boot path that images 1 and 2 use), at both bases, and requires the two
raw images equal; checks it against `DIR/expect-3.txt`; runs both checks'
self-tests with that list; and runs it under QEMU (`k3-like`, one hart).
`tests/held-dir.py` checks `DIR` first: absolute, a directory of this
account's, mode 0700, outside this checkout, with both files. Every output
goes into a new `DIR/out-TIME` (mode 0700), and the target prints only
each step's PASS or FAIL.

## The host test

`tests/test-m13.c` links `m13.c` with a real table and stand-ins for the
assembly, and runs each scenario in a child: what QEMU cannot reach (P7's
writes, the else branch, a hart timed out, refused, or trapped, every
`FAIL`, no console). Each capture is judged by `check-capture.py --mode
host`.
