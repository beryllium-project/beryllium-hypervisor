<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The Beryllium log profile, version 1

This document fixes the MVP's measurement log byte for byte: the 4 KiB page
hart 0 keeps and the four registers beside it (section 2), the records each
image's log must hold (section 3), the `BE_MVP:19 LOG` and `BE_MVP:20
REGISTERS` lines that render them (section 4), the JSON export the capture
checker writes and the post-link reference manifest it compares against
(section 5), the profile's relation to the TCG Canonical Event Log (section
6), the allowlist that keeps IMA out (section 7), and what the profile does
not say (section 8). It is work package M9-2's deliverable under the
accepted [M9 plan](../../planning/mvp-m9-plan.md) (exact commit `4f4a8f76`;
its D-1 to D-5, Q2, Q3, Q4, Q7, Q15, Q18, and Q19), and it is the document
M9-3 (the monitor, the generator, and `tests/log-test.c`) and M9-4 (the
reference tool and the capture checker) implement against. Its terms are
those of [security model v1](../../planning/security-model-v1.md)'s Revision
3 (proposed at `4bc079db`): the **log page**, the **registers**, a **launch
record**, the **launch gate**, the **reference manifest**, the **loader
observation**, and the **platform observation**.

## 1. Purpose and status

- **Version 1.** The page's `version` field is `1`, the records' content
  type is `beryllium-log-v1`, the export's schema `be-mvp-log-v1`, and the
  reference manifest's `be-mvp-log-reference-v1`. A change to any encoding,
  enumeration, serialization, line form, or JSON field below is a new
  version of the profile (`2`, `beryllium-log-v2`, and so on), never an edit
  of version 1.
- **Status.** Written in M9-2, before M9-3 and M9-4 start. Nothing in it is
  implemented at the commit that adds it, and it is reviewed with M9's
  result. Where the plan leaves a choice open, this profile makes it; the
  choices are listed at the end of this section.
- **Derived from CEL; not CEL.** A JSON profile derived from the TCG
  Canonical Event Log Format, version 1.1 revision 11, 2025-10-09; not a
  conforming CEL; no interoperability with any TPM-facing tool is claimed
  (section 6). S3-C.5's "CEL-JSON" is read as this profile (the plan's Q7),
  a reading recorded for the responsible human's acceptance with M9's
  result.
- **The TCG document**, as the plan's steering review recorded it (its
  source W1, in `planning/mvp-m9-plan-review-gpt-6-astra.md`): the file
  `TCG_Canonical_Event_Log_Format_v1_1_pub_3327b8de56.pdf` on the TCG's
  host `medias.cdn.trustedcomputinggroup.org`, SHA-256
  `142dce159a3d223a0dd1d274750c8750bbcefbd349a1915ba130eaa317b47695`. The
  full URL is the one W1 records; it is not repeated here because its path
  holds one of the literals [claim.md](claim.md) forbids in this directory.
  Fetched again from that URL for this profile on 2026-11-03 at 08:42 UTC:
  956,322 bytes, SHA-256
  `142dce159a3d223a0dd1d274750c8750bbcefbd349a1915ba130eaa317b47695`, equal
  to the review's. Section 6 cites it by section and table.
- **What it governs.** The page, the registers, the lines, the export
  (`log.json` in a run record), and the reference manifest. The loader
  observation (U-Boot's MD5 of the loaded boot image on the board, a CRC-32
  in the U-Boot rehearsal, none in a direct QEMU boot) and the platform
  observation (the human's read-only probe, recorded on
  `planning/mvp-m9-platform-probe.md`) are other evidence classes: neither
  enters the page, the lines, the export, or the reference, and none of the
  three is evidence for another (D-6; Revision 3, R3.3).

The choices this profile makes where the plan leaves them open, for review
with M9's result:

1. the enumerations' numbers (2.4);
2. the console grants' serialization (2.8);
3. which record carries a domain's gate outcome: its last launch record
   (2.9);
4. the close's expected count is the image's pre-link constant, and a page
   whose count would differ cannot close (2.5);
5. hart 0 renders the log on three paths only: after the close, on a failed
   gate, and on a log failure; on any other failure it renders nothing
   (4.5);
6. the `magic=` field in the header line, and the `0x` prefix on the
   fixed-width hexadecimal fields, as the shim's line has it (4.1 to 4.3);
7. the barrier's `:20` line carries the hashing total (D-10), saturated at
   `0xffffffff` so that the line fits hart 0's 320-byte line buffer; the
   terminal one carries none (4.4);
8. the places of the `:06 LAUNCH` lines, the block, and both `:20` lines in
   hart 0's stream, and `BE_MVP:FAIL log` without a `DETAIL` line (4.5);
9. stream 0 is compared with the reference through its records only, so
   that `self-report-flip` gives exactly one finding (4.7);
10. the JSON field names, shapes, serialization, and bounds (section 5).

## 2. The page encoding

### 2.1 Conventions

- Every integer is unsigned and little-endian, written and read by its
  width at its fixed offset: never a C structure's native layout.
- A byte string (the magic, every digest and identity, every register) is
  stored in the order it is produced, SHA-256's output order for a digest,
  and rendered as lowercase hexadecimal, two digits per byte, in storage
  order, as `sha256sum` prints a digest.
- Every reserved byte, every byte of a record slot at or after `count`, and
  the page's last 32 bytes (offsets 4,064 to 4,095) are zero. A page so
  written is the **canonical representation**. There is no timing field, no
  pointer, and no address of the page itself.
- The page, `be_mvp_log`, is 4 KiB, 4 KiB aligned, and wholly inside hart
  0's MVP-region BSS (between `__be_mvp_bss_start` and `__be_mvp_bss_end`,
  inside the `.mvp.data` output section), zero from hart 0's clearing of
  that BSS; the registers, `be_mvp_log_registers`, are 128 bytes of the same
  BSS outside the page. Hart 0 alone writes both, and only before any domain
  hart starts; no domain hart reads them (I19). The image checker checks the
  alignment, the containment, and the `HART0_ONLY` reachability of both
  (D-1).

### 2.2 The header (offsets 0 to 127)

| Offset | Width | Field | Encoding | Allowed values |
| --- | --- | --- | --- | --- |
| 0 | 8 | magic | ASCII bytes | `BEMVPLOG` (`42 45 4d 56 50 4c 4f 47`) |
| 8 | 2 | version | u16 | `1` |
| 10 | 2 | header length | u16 | `128` |
| 12 | 2 | record length | u16 | `96` |
| 14 | 2 | capacity | u16 | `41` (records, the close included) |
| 16 | 2 | count | u16 | `0` to `41`: the records appended, the close included |
| 18 | 1 | state | u8 | `0` open, `1` closed, `2` overflow |
| 19 | 1 | reserved | u8 | `0` |
| 20 | 2 | algorithm | u16 | `0x000B`, SHA-256 in the TCG algorithm registry (the only one in version 1) |
| 22 | 10 | reserved | bytes | zero |
| 32 | 32 | scenario | bytes | the image's scenario digest: the generator's `scenario_sha256`, the SHA-256 of the scenario's `scenario.json` as read |
| 64 | 32 | configuration identity | bytes | the authority report's `configuration_identity`, equal to the `configuration-identity` record's digest; all zero exactly when the log holds the `policy-absent` record |
| 96 | 32 | reserved | bytes | zero |

### 2.3 The records (record i at offset 128 + 96·i)

| Offset | Width | Field | Encoding | Allowed values |
| --- | --- | --- | --- | --- |
| 0 | 2 | sequence | u16 | `i`, from `0` |
| 2 | 1 | producer | u8 | `0`, hart 0 (the only producer in version 1) |
| 3 | 1 | type | u8 | `1` measured, `2` informational, `3` close |
| 4 | 1 | stream | u8 | `0` to `3`; `0xff` for the close |
| 5 | 1 | object | u8 | `0` to `13` (2.4) |
| 6 | 1 | representation | u8 | `0` to `3` (2.4) |
| 7 | 1 | outcome | u8 | `0` to `3` (2.4) |
| 8 | 8 | range base | u64 | the host physical address (HPA) of the first byte hashed; `0` for an `as-computed`, `build-recorded`, or `none` record |
| 16 | 8 | range length | u64 | the number of bytes hashed; `0` where the base is `0` |
| 24 | 2 | digest length | u16 | `32`, in every record |
| 26 | 2 | per-stream record number | u16 | the number of earlier records of the same stream, measured and informational alike; `0` for the close |
| 28 | 2 | expected count | u16 | in the close, the log's expected count, equal to the header's count; `0` in every other record |
| 30 | 2 | reserved | u16 | `0` |
| 32 | 32 | digest | bytes | the record's digest (2.7); zero for `policy-absent` and the close, whose meaning is the object, never the hash of an absence |
| 64 | 32 | reserved | bytes | zero |

Record `i` occupies offsets `128 + 96·i` to `128 + 96·i + 95` for `i` from 0
to 40; `128 + 41·96 = 4,064`, so offsets 4,064 to 4,095 hold no record and
are zero.

### 2.4 The enumerations

The page holds the number; the lines and the export print the name. No
other value is valid (section 7).

| Type | Name | Meaning |
| --- | --- | --- |
| 1 | `measured` | hart 0 computed the digest and extended its stream's register with it |
| 2 | `informational` | a value the image carries, logged and never extended |
| 3 | `close` | the log's last record; it carries the expected count |

| Stream | Name | Register |
| --- | --- | --- |
| 0 | platform and monitor (R2) | `r0` |
| 1 | configuration (R3) | `r1` |
| 2 | domain 0 (R4) | `r2`, domain 0's launch register |
| 3 | domain 1 (R4) | `r3`, domain 1's launch register |
| 255 (`0xff`) | the close | none |

| Object | Name | Object | Name |
| --- | --- | --- | --- |
| 0 | `monitor-text` | 7 | `configuration-identity` |
| 1 | `monitor-rodata` | 8 | `policy-identity` |
| 2 | `monitor-input` | 9 | `policy-absent` |
| 3 | `mvp-text` | 10 | `kernel-image` |
| 4 | `mvp-rodata` | 11 | `device-tree` |
| 5 | `core-identity` | 12 | `secret-page` |
| 6 | `console-grants` | 13 | `close` |

| Representation | Name | Meaning |
| --- | --- | --- |
| 0 | `as-placed` | the bytes of one HPA range as they lay in memory, loaded or placed, when hart 0 hashed them |
| 1 | `as-computed` | a digest hart 0 computed over canonical serialized fields, not over one contiguous range |
| 2 | `build-recorded` | a value the build computed and the image carries as a constant |
| 3 | `none` | the close |

| Outcome | Name | Meaning |
| --- | --- | --- |
| 0 | `recorded` | logged; hart 0 compared nothing at this record |
| 1 | `gated-pass` | the record ends its domain's launch records, and the domain's register equalled the image's expected launch register |
| 2 | `gated-fail` | as `gated-pass`, but the values differed: no domain hart starts |
| 3 | `none` | the close |

| State | Name |
| --- | --- |
| 0 | `open` |
| 1 | `closed` |
| 2 | `overflow` |

The algorithm's one value is `0x000B` (`TPM_ALG_SHA256`), printed
`alg=0x000b` and exported as `"hashAlg": "sha256"`.

### 2.5 Appending and closing

- Hart 0 appends a record by writing slot `count` and adding 1 to `count`;
  the state is `open` until the close.
- When `count` is 40 (the capacity less one), only the close may be
  appended. Appending any other record there sets the state to `overflow`,
  writes nothing, leaves `count` at 40, and fails the run
  (`BE_MVP_CLASS_LOG`, printed `BE_MVP:FAIL log`).
- Hart 0 appends the close only when `count + 1` equals the image's expected
  count, a pre-link constant the generator writes from the image's contract
  (section 3). It writes that count in the close's expected-count field and
  sets the state to `closed`; after the close nothing is appended and no
  register is extended. Otherwise the page cannot close: no close is
  written, the state stays `open`, and the run fails the same way.
- Every declared image's expected count is at most 15 (`anchor` with R2
  kept), so the page never fills in a declared image; overflow and a page
  that cannot close come only from a defect, which the host test provokes.
- **The global rule** (D-1): every launch comparison the image's contract
  requires succeeds and the log closes before `BE_MVP:07` and before any SBI
  HSM start, or no domain hart starts (I20).

### 2.6 The registers (128 bytes beside the page)

| Offset | Width | Register | Stream |
| --- | --- | --- | --- |
| 0 | 32 | `r0` | 0, platform and monitor |
| 32 | 32 | `r1` | 1, configuration |
| 64 | 32 | `r2` | 2, domain 0's launch register |
| 96 | 32 | `r3` | 3, domain 1's launch register |

- Each register starts as 32 zero bytes. For each record, in sequence
  order, whose type is `measured`, hart 0 sets `R := SHA-256(R || digest)`,
  `R` the register of the record's stream: the SHA-256 of 64 bytes, the
  register's 32 followed by the digest's 32. Informational records and the
  close extend nothing.
- `r0` stays zero when R2 is dropped (Q4), since the image then has no
  stream-0 record; the reference manifest's `r2` field says which.
- **The launch gate.** After a domain's last launch record, hart 0 compares
  the domain's register (`r2` or `r3`) with the image's expected launch
  register for that domain, a pre-link constant the generator computes over
  the same bytes with the same recurrence (the reference's
  `launch_expected`). The result is that record's outcome (2.9).
- **What the registers bind.** Each register commits, under the hash
  assumption, to its stream's ordered sequence of measured digests and to
  nothing else: not to a record's object, range, type, or outcome, not to
  the header or the informational records, and not to the interleaving
  across streams. Those are bound by the checker's field-by-field
  comparison with the reference (4.7); the close is structural, not
  cryptographic (D-1; Revision 3, R3.2). They are registers in hart 0's
  memory, never PCRs.

### 2.7 The objects

| No. | Object | Type | Stream | Representation | Range (base, length) | Digest | In |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `monitor-text` | measured | 0 | as-placed | `.monitor.text` as loaded, `__be_monitor_code_start` to `__be_monitor_code_end` | SHA-256 of the range's bytes | every image, R2 kept |
| 1 | `monitor-rodata` | measured | 0 | as-placed | `.monitor.rodata` as loaded, by the start and end symbols M9-3 adds | as above | as above |
| 2 | `monitor-input` | measured | 0 | as-placed | `.monitor.input` (the generated inventory and proposal, Q19), `__be_input_start` to `__be_input_end` | as above | as above |
| 3 | `mvp-text` | measured | 0 | as-placed | `.mvp.text`, `__be_mvp_text_start` to `__be_mvp_text_end` | as above | as above |
| 4 | `mvp-rodata` | measured | 0 | as-placed | `.mvp.rodata`, by the start and end symbols M9-3 adds | as above | as above |
| 5 | `core-identity` | measured | 1 | as-computed | 0, 0 | the core identity itself: `be_mvp_core_identity()`'s SHA-256 over the canonical fields `mvp-core.h` lists, the 32 bytes whose first 8 `CONFIG_SEALED` prints; not a hash of it | every image |
| 6 | `console-grants` | measured | 1 | as-computed | 0, 0 | SHA-256 of 2.8's two bytes | every image |
| 7 | `configuration-identity` | informational | 1 | build-recorded | 0, 0 | the authority report's `configuration_identity`, which the image carries | `te-poc`, `anchor`, and their variants |
| 8 | `policy-identity` | informational | 1 | build-recorded | 0, 0 | the authority report's `policy_identity`, the SHA-256 of `policy.te`, which the image carries | as above |
| 9 | `policy-absent` | informational | 1 | build-recorded | 0, 0 | zero | `two-guests`, its variants, and the probes |
| 10 | `kernel-image` | measured | 2 or 3 | as-placed | the domain's kernel as placed: its destination HPA, the window's HPA plus `0x200000` (`0x110200000`, `0x114200000`), and the kernel file's length, not the Image header's memory size | SHA-256 of the destination bytes | every Linux-guest image, once per domain, even where both domains boot one file |
| 11 | `device-tree` | measured | 2 or 3 | as-placed | the domain's device tree as placed: the window's HPA plus `0x3e00000` (`0x113e00000`, `0x117e00000`), 4,096 bytes | as above | every Linux-guest image, once per domain, the image's own device trees |
| 12 | `secret-page` | measured | 3 | as-placed | the secret page as placed: `0x118002000`, 4,096 bytes, the secret zero-padded | as above | `anchor` and its variants |
| 13 | `close` | close | 255 | none | 0, 0 | zero | every log that closes |

The addresses are the layout's (`mvp/src/mvp-layout.h`), which M9 does not
change (D-11). R2's ranges are fixed by the link; the reference manifest
records each as a final loaded HPA range with its offset in the boot image
(5.3). There is no initramfs record: both domains boot one Image with an
embedded initramfs, and nothing in HS parses it (D-2).

### 2.8 The console grants' serialization

The `console-grants` digest is the SHA-256 of one byte per domain, in
domain index order: `0x01` when the sealed configuration grants that domain
console input (its derived root's grant, bit `d` of
`be_mvp_core_console()`'s result), else `0x00`. With the MVP's two domains
the input is two bytes. This is the profile's serialization (the plan
leaves it to the profile, Q18); M9-3 may refine it only by bumping the
version. The four values:

| Domain 0, domain 1 | Bytes | Digest |
| --- | --- | --- |
| none, none | `00 00` | `96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7` |
| granted, none | `01 00` | `47dc540c94ceb704a23875c11273e16bb0b8a87aed84de911f2133568115f254` |
| none, granted | `00 01` | `b413f47d13ee2fe6c845b2ee141af81de858df4ec549a58b7970bb96645bc8d2` |
| granted, granted | `01 01` | `9dcf97a184f32623d11a73124ceb99a5709b083721e878a16d78f596718ba7b2` |

At `4bc079db` the scenarios' own images grant no domain console input,
`two-guests-shell` and `te-poc-shell` grant both, and `anchor-shell` grants
domain 0 only (the scenarios' `console_input` entries), so a shell image's
`r1` differs from its scenario's while the core identity, and the prefix
`CONFIG_SEALED` prints, stay the scenario's (Q18; item 108).

### 2.9 Outcomes: which record carries the gate

- R2's and R3's records are `recorded`: R2 never gates (an expected value
  inside the measured range would be a fixed point), and R3 is the
  checker's alone.
- A domain's launch records come in its stream in the order `kernel-image`,
  `device-tree`, and, for `anchor`'s domain 1, `secret-page`. All but the
  last are `recorded`; the last carries the domain's gate: `gated-pass`
  when the domain's register equals the image's expected launch register,
  `gated-fail` otherwise. After a `gated-fail` record hart 0 appends
  nothing, renders the log (4.5), and fails the run `BE_MVP:FAIL
  measurement`.
- The close's outcome is `none`. A probe image has no launch record and no
  gate.

### 2.10 Test vectors

Section 5.4's `te-poc` example gives this canonical page; its 4,096 bytes
have the SHA-256
`4435113d8276c4444630b2be8fd3ff60929f68723a121b8c6574f049488b1184`.
The header (offsets 0 to 127):

```text
0000  42 45 4d 56 50 4c 4f 47 01 00 80 00 60 00 29 00
0010  0e 00 01 00 0b 00 00 00 00 00 00 00 00 00 00 00
0020  5c 74 d0 dc de 52 a6 a6 c1 ff cc 50 d1 76 f5 1d
0030  74 e7 b6 69 a8 c7 60 8b 6d 5c 99 55 ee 34 a9 ba
0040  9f 6f 6d 94 0a 41 d7 af 49 4a 1e 4c 1a fe 1b 6e
0050  dc f8 79 39 12 b5 75 5d e3 7d 57 b9 ad b0 88 49
0060  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
0070  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Record 9, domain 0's `kernel-image` (offsets 992 to 1087):

```text
03e0  09 00 00 01 02 0a 00 00 00 00 20 10 01 00 00 00
03f0  c4 7c 1f 00 00 00 00 00 20 00 00 00 00 00 00 00
0400  11 a3 89 6e 8a 92 b0 07 f3 ad 6d 26 d5 21 88 3d
0410  c7 19 d0 8f f0 fe 11 2d 1e 4f 79 07 f3 bd ce 07
0420  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
0430  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Record 13, the close (offsets 1376 to 1471):

```text
0560  0d 00 00 03 ff 0d 03 03 00 00 00 00 00 00 00 00
0570  00 00 00 00 00 00 00 00 20 00 00 00 0e 00 00 00
0580  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
0590  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
05a0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
05b0  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

## 3. The per-image contract

The plan's D-2 table, in substance, for each image class: the records in
order, whether the gate applies, the completion state the checker
requires, and the terminal prefix it accepts. A record the table requires
and the log lacks, a record it does not list, or a prefix other than the
declared one is the checker's finding. The table is the checker's data: the
generator writes each image's expected sequence from it (D-2).

| Image class | Required records (the header; then, in order) | Gate | Completion | Terminal prefix the checker accepts |
| --- | --- | --- | --- | --- |
| `two-guests` (v1) and its `shell` and `live` variants | R2 (if kept); `core-identity`; `console-grants`; `policy-absent` (informational, digest zero: the v1 scenario has no authority report, so neither a configuration identity nor a policy identity exists, and the header's configuration identity is zero); R4 for domains 0 and 1 (each kernel and device tree as placed, the variant's own device trees); the close | per domain | closed before `:07` | a complete closed log, both gates `gated-pass` |
| `te-poc` (v2) and its variants | R2 (if kept); `core-identity`; `console-grants`; `configuration-identity`; `policy-identity` (build-recorded, the report's); R4 for both domains; the close | per domain | closed before `:07` | a complete closed log |
| `anchor` (v3) and its variants | as `te-poc`, with `secret-page` (stream 3, as placed) after domain 1's device tree | per domain | closed before `:07` | a complete closed log |
| the probe images (M0's and M7's, on `two-guests`' configuration) | R2 (if kept); `core-identity`; `console-grants`; `policy-absent`; the close; no R4: a probe places a synthetic stub and starts domain 0 alone, so no Linux launch evidence is claimed and no stub is called an Image | none | closed before the probe's start | a complete closed log, and no `:06 LAUNCH` |
| negatives that fail before the measurement step (`gstage`, `payload`, and their kin) | the header and the records appended before the failure, or none | not reached | `open` | the declared prefix for that negative, exactly, and no close |
| `wrong-measurement` | the log through the failing domain's last launch record, with outcome `gated-fail`, then `BE_MVP:FAIL measurement` | fails | `open`; no close; no hart starts | the declared prefix, the `gated-fail` record, and the `DETAIL` with both values |
| `self-report-flip` (D-4) | a complete closed log, the `mvp-rodata` record's digest unlike the reference's | per domain | closed | a complete closed log, the run to its terminal marker, and exactly the finding `self-report differs: mvp-rodata` |
| a failure after the launch (a domain fails or terminates in the run) | the closed boot log as above; the terminal registers printed before `:14` | passed | closed | the closed log and the terminal registers; the run's own declared lines |

### 3.1 The record sequences

"R2" stands for the five records `monitor-text`, `monitor-rodata`,
`monitor-input`, `mvp-text`, and `mvp-rodata`, in that order, present when
R2 is kept and absent when it is dropped (Q4). The counts include the
close: with R2 kept, and in parentheses without it. "(gate)" marks the
record that carries a domain's gate outcome.

| Sequence | Images | Records, in order | Count |
| --- | --- | --- | --- |
| `v1` | `two-guests` and its variants | R2, `core-identity`, `console-grants`, `policy-absent`, `kernel-image` (domain 0), `device-tree` (domain 0, gate), `kernel-image` (domain 1), `device-tree` (domain 1, gate), `close` | 13 (8) |
| `v2` | `te-poc` and its variants | R2, `core-identity`, `console-grants`, `configuration-identity`, `policy-identity`, `kernel-image` (domain 0), `device-tree` (domain 0, gate), `kernel-image` (domain 1), `device-tree` (domain 1, gate), `close` | 14 (9) |
| `v3` | `anchor` and its variants | R2, `core-identity`, `console-grants`, `configuration-identity`, `policy-identity`, `kernel-image` (domain 0), `device-tree` (domain 0, gate), `kernel-image` (domain 1), `device-tree` (domain 1), `secret-page` (domain 1, gate), `close` | 15 (10) |
| `probe` | the probe images | R2, `core-identity`, `console-grants`, `policy-absent`, `close` | 9 (4) |

### 3.2 The run classes

| Run class | The table's row | What hart 0's stream shows |
| --- | --- | --- |
| `complete` | the scenarios' rows and the probes' | the whole sequence, state `closed`, each domain's `:06 LAUNCH` (none in a probe), the barrier's `:20`, and the terminal `:20` immediately before `BE_MVP:14` |
| `pre-measurement` | the negatives that fail before the measurement step | no `:19` and no `:20` line: hart 0 renders the log on the three paths of 4.5 only, so this class's declared prefix is the empty one |
| `gate-fail` | `wrong-measurement` | domain 0's `:06 LAUNCH`; the block, its header with state `open` and count 14 (9), its records the `v3` sequence through domain 1's `secret-page`, whose outcome is `gated-fail`; no close and no `:20`; then `BE_MVP:FAIL measurement` and `BE_MVP:DETAIL domain=1 hart=2 computed=<r3> expected=<the image's expected value>` |
| `self-report-flip` | `self-report-flip` | as `complete`, with `mvp-rodata`'s digest unlike the reference's, and the run to its terminal marker |
| `post-launch-failure` | a failure after the launch | as `complete` up to the run's failure, then the terminal `:20` immediately before hart 0's first `BE_MVP:FAIL` line, then the run's own declared lines; in the `ring-full` fallback (Plan revision M0-A.3), where hart 0 prints no terminal line, no terminal `:20` |

The expectations at `4bc079db`, by run class (the generator's data, not
this table, decides each one):

| Run class | Expectations |
| --- | --- |
| `complete` | `two-guests`, `te-poc`, `anchor`; `sbi-time`, `shim-rule`, `hostile`, `two-guests-shell`, `te-poc-shell`, `anchor-shell`, and the `live` builds of the shell images; the probe images |
| `pre-measurement` | `payload` (`payload`), `no-sstc` (`sstc`), `sbi-3.0` (`boot`), `reader-write`, `secret-shared`, and `response-writable` (`gstage`) |
| `gate-fail` | `wrong-measurement` |
| `post-launch-failure` | `exit-budget`, `run-timeout`, `ring-full`, `hart-start`, `init-exit`, `rdcycle`, `no-inject`, `no-grant-check` |
| `self-report-flip` | the variant M9-3 adds (D-4) |

## 4. The line grammar

### 4.1 Field forms

| Form | Pattern | Fields |
| --- | --- | --- |
| decimal | `0`, or a nonzero digit followed by digits (`0\|[1-9][0-9]*`), no larger than the field's width allows | counts, sequence numbers, numbered enumerations |
| hex64 | `0x` and exactly 16 lowercase hexadecimal digits | the range's base and length |
| hex16 | `0x` and exactly 4 lowercase hexadecimal digits | the algorithm |
| digest | exactly 64 lowercase hexadecimal digits, no prefix, as `sha256=` and `config=` print today | digests, identities, registers |
| name | a name from 2.4 | the state, type, object, representation, and outcome |
| hex | `0x` and 1 to 16 lowercase hexadecimal digits without leading zeros: the tree's `0x%x`, the capture checker's `HEX` | the `ticks` of `:06 LAUNCH` and `DOMAIN_TERMINATED` |
| ticks | as hex, with at most 8 digits | the barrier's hashing total |

Each line is one of the forms below exactly: the fields in the order shown,
each `name=value`, separated by one space, with no other text and no
trailing space, in printable ASCII, and at most 319 characters before its
line feed (hart 0's line buffer, `BE_MVP_LINE_CAPACITY`, is 320 bytes). The
longest header line is 255 characters, the longest record line the per-object
rules allow is 282, the barrier's `:20` line at most 319, and the terminal
one 303.

### 4.2 The header line

```text
BE_MVP:19 LOG header magic=BEMVPLOG version=<decimal> hlen=<decimal> rlen=<decimal> capacity=<decimal> count=<decimal> state=<name> alg=<hex16> scenario=<digest> config=<digest>
```

The header's fields (2.2) in their order, reserved ones omitted; `magic` is
printed as its 8 ASCII characters.

### 4.3 The record line

```text
BE_MVP:19 LOG record seq=<decimal> producer=<decimal> type=<name> stream=<decimal> object=<name> repr=<name> outcome=<name> base=<hex64> length=<hex64> dlen=<decimal> srec=<decimal> expected=<decimal> digest=<digest>
```

One line per record, in sequence order: the record's fields (2.3) in their
order, reserved ones omitted, `stream` as its number (255 for the close).

### 4.4 The registers line

```text
BE_MVP:20 REGISTERS at=barrier r0=<digest> r1=<digest> r2=<digest> r3=<digest> ticks=<ticks>
BE_MVP:20 REGISTERS at=terminal r0=<digest> r1=<digest> r2=<digest> r3=<digest>
```

- `r0` to `r3` are the registers (2.6).
- `ticks`, on the barrier's line only, is hart 0's hashing time for the
  log's records in timebase ticks, a cost recorded beside the log and
  outside its canonical representation (D-10). It is printed as the smaller
  of the total and `0xffffffff`: the line is 302 characters without the
  field, and the field, nine characters before at most 8 digits, brings it
  to 319. The checker records the value and judges its form only. The
  terminal line has none: nothing is hashed after the close.

### 4.5 Where the lines stand in hart 0's stream

Hart 0 renders the log, the header line followed by one record line per
record in sequence order (the **block**), on exactly one of three paths,
and on no other:

1. **After the close**, in every image whose log closes: the block and the
   barrier's `:20` immediately precede `BE_MVP:07 BLOCKS_PUBLISHED`; in a
   Linux-guest image each domain's `BE_MVP:06 LAUNCH` line, printed at its
   gate, immediately precedes the block, after the `:06 PAYLOAD_PLACED`
   lines.
2. **On a failed gate**: the `:06 LAUNCH` line of each domain whose gate
   passed, the block (state `open`, through the `gated-fail` record), then
   `BE_MVP:FAIL measurement` and its `DETAIL` line. No `:20` line.
3. **On a log failure** (overflow, or a page that cannot close): the block
   (state `overflow` or `open`), then `BE_MVP:FAIL log`, with no `DETAIL`
   line. No `:20` line.

On any other failure before the close (`boot`, `firmware`, `sstc`,
`gstage`, `payload`, ...) hart 0 renders nothing. The terminal `:20` line is
printed exactly when the barrier's was, immediately before hart 0's
terminal line: `BE_MVP:14 SHUTDOWN` on a run that completes, after
`BE_MVP:13`, or hart 0's first `BE_MVP:FAIL` line on a run that fails after
the barrier. A completing Linux-guest image's stream therefore reads:

```text
BE_MVP:06 PAYLOAD_PLACED domain=0 ...
BE_MVP:06 PAYLOAD_PLACED domain=1 ...
BE_MVP:06 LAUNCH domain=0 hart=1 register=<r2> expected=match ticks=...
BE_MVP:06 LAUNCH domain=1 hart=2 register=<r3> expected=match ticks=...
BE_MVP:19 LOG header ...
BE_MVP:19 LOG record seq=0 ...
...
BE_MVP:19 LOG record seq=<count - 1> ... type=close ...
BE_MVP:20 REGISTERS at=barrier ... ticks=...
BE_MVP:07 BLOCKS_PUBLISHED ...
...
BE_MVP:13 RUN_COMPLETE ...
BE_MVP:20 REGISTERS at=terminal ...
BE_MVP:14 SHUTDOWN type=0 reason=0
```

A probe image's block and barrier line also immediately precede its
`BE_MVP:07`, and its terminal line its `BE_MVP:14`. The hashing and the
whole first rendering precede the barrier and the arming of the operational
budget (D-10). Section 5.4's example renders to 4,557 bytes of `:19` and
`:20` text with their line feeds, about 0.4 s at 115,200 baud.

### 4.6 Acceptance, rebuild, and replay

- **Acceptance.** Lines are taken from hart 0's unprefixed monitor stream
  only. A `BE_MVP:19` or `BE_MVP:20` text in a domain's stream, behind
  `BE_MVP_G<d>: `, is that domain's line, never a record or a register,
  whatever it holds (I18; Revision 3, R3.3); a line with text before its
  tag is refused, as any marker line is.
- **Rebuild.** The checker parses each line by its form (4.1 to 4.4) and
  rebuilds the canonical page: the header from the header line, record `i`
  from the `i`-th record line, and every reserved byte, every slot from
  `count` to 40, and offsets 4,064 to 4,095 zero. The lines are the
  observation; the page's padding is covered by the host test's
  byte-for-byte rebuild (`tests/log-test.c`), not by the lines. A line set
  that does not rebuild is refused:
  - a `:19` or `:20` line that does not match its form exactly, or a
    decimal wider than its field;
  - more than one block, a block that is not contiguous, a header line
    that does not open it, or a record line outside it;
  - a `seq` that is not the line's position in the block (a gap, a
    duplicate, a reorder), or a number of record lines other than `count`;
  - a `magic` other than `BEMVPLOG`, a `version` other than 1, `hlen` other
    than 128, `rlen` other than 96, `capacity` other than 41, `alg` other
    than `0x000b`, `dlen` other than 32, or `producer` other than 0;
  - a name or number outside its enumeration (section 7);
  - a record outside its object's row of 2.7 (its type, stream,
    representation, or outcome, a nonzero base or length where the row has
    none, a nonzero digest in `policy-absent` or the close), or a nonzero
    `expected` in a record other than the close;
  - an `srec` other than the number of earlier records of its stream (0 for
    the close);
  - a state at odds with the records: `closed` without a close as the last
    record; a close that is not the last record, or whose `expected` is not
    `count`; a close in an `open` or `overflow` log; `overflow` with a
    `count` other than 40;
  - a header `config` that is not the `configuration-identity` record's
    digest, or is nonzero beside `policy-absent`, or a log with both or
    neither of those records;
  - a `:20 at=barrier` line where the log is not closed, or not immediately
    after the block; a `:20 at=terminal` line without the barrier's, or not
    immediately before hart 0's terminal line; more than one of either;
    `ticks` absent from the barrier's line or present on the terminal's.
- **Replay.** The checker computes the registers from the rebuilt records by
  2.6 and labels its values `unprotected`; each printed `:20` value must
  equal its replay, or the registers do not replay.

### 4.7 Comparison with the reference

- Every header field and every record field, `srec` included, equals the
  reference manifest's `expected` (5.3), record by record, through the
  prefix the image's run class declares (3.2): the whole log for
  `complete`, `self-report-flip`, and `post-launch-failure`; for
  `gate-fail`, the records through the failing domain's last launch record
  (domain 1's `secret-page` for `wrong-measurement`), whose outcome is
  `gated-fail` where the reference has `gated-pass`, with state `open` and
  `count` the number of those records; for `pre-measurement`, no block at
  all.
- The checker recomputes every digest itself rather than trusting the
  printed one: each R4 object from the build input the reference's range
  table names, each R2 range from the boot image's bytes at the recorded
  offset, and the core identity and the console grants from the generator's
  canonical inputs. Each must equal the printed digest and the reference's.
- **Stream 0 is a self-report.** An R2 record whose digest differs from the
  reference's is the finding `self-report differs: <object>`, one per
  record; it gates nothing and does not refuse the log. `r0` is compared
  with the replay only, so a self-report difference is reported once, as
  that finding (`self-report-flip`'s one finding).
- Each `:06 LAUNCH` line's `register=` equals the reference's
  `launch_expected` for its domain and the replayed register of its stream;
  each domain's `gated-pass` record and `:06 LAUNCH` line precede its
  `BE_MVP:08 HART_STARTED`, and every `:19` line and the barrier's `:20`
  precede `BE_MVP:07` (D-4).
- For `gate-fail`, the `DETAIL` line's `computed=` is the replayed register
  of the failing domain's stream, and its `expected=` is the reference's
  `launch_expected` for that domain; for `wrong-measurement` the two differ
  in bit 0 of the first byte alone (Q16).
- The run's boot image has the reference's `boot_image_sha256`, or its
  `mutated_image_sha256` for `self-report-flip`; its toolchain and variant
  are the reference's.

### 4.8 The lines the plan fixes beside the log

These are D-2's; restated here so that the grammar is in one place.

```text
BE_MVP:06 LAUNCH domain=<decimal> hart=<decimal> register=<digest> expected=match ticks=<hex>
BE_MVP:DETAIL domain=<decimal> hart=<decimal> computed=<digest> expected=<digest>
BE_MVP:12 DOMAIN_TERMINATED hart=<decimal> domain=<decimal> by=<decimal> exits=<decimal> sha256=<digest> ticks=<hex>
```

- `BE_MVP:06 LAUNCH` replaces `BE_MVP:06 MEASURED`: one line per domain in
  every Linux-guest image, printed at the domain's gate when it passes;
  `register=` is the domain's launch register and `ticks=` that domain's
  hashing time, a cost.
- `BE_MVP:DETAIL … computed= expected=` keeps its form and follows
  `BE_MVP:FAIL measurement`: the failing domain's launch register and the
  image's expected value.
- `DOMAIN_TERMINATED` keeps its fields; its `sha256=` is now the
  terminated domain's launch register, which every Linux-guest domain has,
  so the `-` the line prints today for an unmeasured domain no longer
  occurs: the stored value read again at termination, not a second hash of
  the domain's memory (D-9).

## 5. The JSON profile

### 5.1 Writing and reading

- **Writing.** Both files are written as Python's `json.dumps(value,
  indent=1, sort_keys=True)` followed by one line feed, the tree's form for
  the authority report and the platform record: ASCII, keys sorted, no
  time, and no absolute path, so the same inputs give the same bytes. A
  64-bit field (a range's base or length, an image offset) is a string of
  `0x` and 16 lowercase hexadecimal digits, as the lines print it; a digest
  is 64 lowercase hexadecimal digits; counts and numbers are JSON integers.
- **Reading.** A reader refuses a file over 262,144 bytes; a duplicate key
  at any level; a key its schema does not name, or one it requires missing;
  a value of another JSON type; a string not of its field's form; more than
  41 records; a name outside section 7's allowlist; and a `schema` other
  than the one it reads.

### 5.2 The export, `log.json`

The capture checker writes the rebuilt log as `log.json` in the run record;
a run that printed no `:19` line has none. The export rebuilds the page byte
for byte (the round-trip page, lines, rebuild, export, rebuild is the
checker's self-test, D-4): `dlen` is 32 by the profile, the reserved bytes
are zero, and nothing else is omitted.

| Field | Type | Contents |
| --- | --- | --- |
| `schema` | string | `be-mvp-log-v1` |
| `header` | object | `magic` (`"BEMVPLOG"`), `version` (1), `header_length` (128), `record_length` (96), `capacity` (41), `count` (integer), `state` (`"open"`, `"closed"`, or `"overflow"`), `hashAlg` (`"sha256"`, the algorithm `0x000B`), `scenario_sha256` (digest), `configuration_identity` (digest) |
| `records` | array | the records in sequence order, each an object of the six fields below |
| `records[].recnum` | integer | the record's global sequence number, the page's `seq` |
| `records[].register` | integer or null | the record's stream, 0 to 3, the register it names; `null` for the close. An informational record names its stream's register and does not extend it |
| `records[].srec` | integer | the per-stream record number |
| `records[].digests` | array | one object: `hashAlg` (`"sha256"`) and `digest` (digest; zero for `policy-absent` and the close) |
| `records[].content_type` | string | `beryllium-log-v1` |
| `records[].content` | object | `producer` (0), `type`, `object`, `representation`, and `outcome` (names), `base` and `length` (hex64 strings), `expected` (integer: the close's expected count, 0 otherwise) |
| `registers` | object | `barrier` and `terminal`: the four values (`r0` to `r3`, digests) the `:20` lines printed, each `null` where the run printed no such line; `replayed`: the four values the checker's replay of the records gives; `replayed_label`: `"unprotected"` |

### 5.3 The reference manifest

`tools/gen-reference.py` (M9-4) writes one reference per image and
toolchain, `build/mvp/references/<toolchain>/<image>.json`, after the link
(D-3). It is regenerated on every build and never edited; it holds no time
stamp and no absolute path, so the host's and the evaluator's are compared
byte for byte as the images are; the image checker pins its SHA-256 beside
the image's; it is copied into every retained record and evidence bundle
(the development bundle keeps every reference, and a board record those of
the images its runs ran, each with its pin; `tools/evidence.py`, M9-6); and
it is a build product, never tracked as source (Q6).

| Field | Type | Contents |
| --- | --- | --- |
| `schema` | string | `be-mvp-log-reference-v1` |
| `source` | object | `commit` (40 lowercase hexadecimal digits) and `tree_state` (`"clean"`, or `"dirty changed=<n>"`, the evidence bundle's form) |
| `image` | string | the image's name: its scenario's, its variant's, or its probe's |
| `scenario` | string | the scenario's name |
| `variant` | string or null | the variant's name; `null` for a scenario image or a probe |
| `toolchain` | string | `"gcc"` or `"clang"` |
| `contract` | object | `sequence` (`"v1"`, `"v2"`, `"v3"`, or `"probe"`; 3.1) and `run` (`"complete"`, `"pre-measurement"`, `"gate-fail"`, `"self-report-flip"`, or `"post-launch-failure"`; 3.2) |
| `r2` | string | `"kept"` or `"dropped"` (Q4) |
| `authority_report_sha256` | digest or null | the authority report's SHA-256; `null` for an image without one (`two-guests`, its variants, and the probes) |
| `elf_sha256`, `boot_image_sha256` | digest | the nominal build's monitor ELF and boot image |
| `mutated_image_sha256` | digest or null | `self-report-flip`'s mutated boot image, beside the nominal `boot_image_sha256`, which it keeps; `null` in every other reference |
| `ranges` | array | the measured range table, one entry per R2 range and R4 object, in record order: `object`; `domain` (0 or 1 for an R4 object, else `null`); `base` and `length` (hex64: the final loaded HPA range); `image_offset` (hex64: the range's offset in the boot image, `base - 0x102000000 + 0x1000`, for an R2 range; `null` for R4); `source` (`"boot-image"` for R2; for R4 the build input's path relative to `build/mvp/`, or `"scenario-secret"` for the secret page, the scenario's secret zero-padded to 4,096 bytes); `digest` (the SHA-256 of the range's bytes from its source) |
| `launch_expected` | array of digests | per launched domain, in index order, the expected launch register the image carries as a pre-link constant, which its gate compares with; empty for a probe; for `wrong-measurement`, domain 1's is the nominal value with bit 0 of its first byte flipped (Q16) |
| `expected` | object | `header` and `records` in the export's shapes, the image's complete log as the build defines it, and `registers`, the four final register values (digests) |

Only pre-link values enter the compiled image (each domain's expected
launch register and the configuration constants); the R2 digests, the final
image's SHA-256, and the reference's own SHA-256 stay outside it, so no
self-reference enters R2 (D-3, Q4).

### 5.4 Example: `te-poc`, R2 kept, GCC

The values are illustrative unless said otherwise: every digest and
identity is the SHA-256 of an ASCII label `beryllium-log-profile-v1
example: <label>` (the labels `scenario te-poc`, `monitor-text`,
`monitor-rodata`, `monitor-input`, `mvp-text`, `mvp-rodata`,
`core-identity`, `configuration-identity`, `policy-identity`,
`kernel-image`, `device-tree d0`, `device-tree d1`, `authority-report`,
`elf`, and `boot-image`), except the console grants', which is `te-poc`'s
true value under 2.8. The R2 ranges' lengths, and the bases of
`.monitor.rodata` and `.mvp.rodata` that follow from them, the kernel
file's length (2,063,556 bytes, the pinned Image's at `4bc079db`), the
ticks, and the commit are illustrative; the other bases are the link's
fixed addresses and the layout's. Both domains boot one kernel file, so the
two `kernel-image` digests are equal. The registers are the recurrence over
these digests, so the example is consistent with itself and serves as a
test vector for the encoding (2.10), the rendering, the replay, and the
export.

The lines:

```text
BE_MVP:06 LAUNCH domain=0 hart=1 register=b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792 expected=match ticks=0x10a2c0
BE_MVP:06 LAUNCH domain=1 hart=2 register=7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5 expected=match ticks=0x10a1f8
BE_MVP:19 LOG header magic=BEMVPLOG version=1 hlen=128 rlen=96 capacity=41 count=14 state=closed alg=0x000b scenario=5c74d0dcde52a6a6c1ffcc50d176f51d74e7b669a8c7608b6d5c9955ee34a9ba config=9f6f6d940a41d7af494a1e4c1afe1b6edcf8793912b5755de37d57b9adb08849
BE_MVP:19 LOG record seq=0 producer=0 type=measured stream=0 object=monitor-text repr=as-placed outcome=recorded base=0x0000000102000000 length=0x0000000000004540 dlen=32 srec=0 expected=0 digest=96704ef2f5b319b854004242adf83cea20e272e01697402d9d968650f0f0c392
BE_MVP:19 LOG record seq=1 producer=0 type=measured stream=0 object=monitor-rodata repr=as-placed outcome=recorded base=0x0000000102008610 length=0x00000000000002e8 dlen=32 srec=1 expected=0 digest=ab1aea296cbff86a1cb5156562601b239f292db71c89b5399a222fe8ca6bdc73
BE_MVP:19 LOG record seq=2 producer=0 type=measured stream=0 object=monitor-input repr=as-placed outcome=recorded base=0x0000000102008000 length=0x0000000000000610 dlen=32 srec=2 expected=0 digest=8b876a7e36e8161d6b2199a998d6213e1448cf46699dce4fbf80b277eb08564e
BE_MVP:19 LOG record seq=3 producer=0 type=measured stream=0 object=mvp-text repr=as-placed outcome=recorded base=0x0000000102064000 length=0x0000000000006a40 dlen=32 srec=3 expected=0 digest=ec6d6ddf35da0c8bcd41de09b0e3c1e34e3aec6fc50c0835749797309d272039
BE_MVP:19 LOG record seq=4 producer=0 type=measured stream=0 object=mvp-rodata repr=as-placed outcome=recorded base=0x000000010206aa40 length=0x0000000000001238 dlen=32 srec=4 expected=0 digest=06a35b4b92030141900fc59c7db016bb483c37ddd1962a4f8ee739c72279b5aa
BE_MVP:19 LOG record seq=5 producer=0 type=measured stream=1 object=core-identity repr=as-computed outcome=recorded base=0x0000000000000000 length=0x0000000000000000 dlen=32 srec=0 expected=0 digest=f958c31fd593ea0db3bd787a5e45bf2383fdeb8f831d5a451c89a4c3171a933b
BE_MVP:19 LOG record seq=6 producer=0 type=measured stream=1 object=console-grants repr=as-computed outcome=recorded base=0x0000000000000000 length=0x0000000000000000 dlen=32 srec=1 expected=0 digest=96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7
BE_MVP:19 LOG record seq=7 producer=0 type=informational stream=1 object=configuration-identity repr=build-recorded outcome=recorded base=0x0000000000000000 length=0x0000000000000000 dlen=32 srec=2 expected=0 digest=9f6f6d940a41d7af494a1e4c1afe1b6edcf8793912b5755de37d57b9adb08849
BE_MVP:19 LOG record seq=8 producer=0 type=informational stream=1 object=policy-identity repr=build-recorded outcome=recorded base=0x0000000000000000 length=0x0000000000000000 dlen=32 srec=3 expected=0 digest=04687fe4d6177770e89b698f53d82ed52b266c793f5c46318bf8308f020e01aa
BE_MVP:19 LOG record seq=9 producer=0 type=measured stream=2 object=kernel-image repr=as-placed outcome=recorded base=0x0000000110200000 length=0x00000000001f7cc4 dlen=32 srec=0 expected=0 digest=11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f3bdce07
BE_MVP:19 LOG record seq=10 producer=0 type=measured stream=2 object=device-tree repr=as-placed outcome=gated-pass base=0x0000000113e00000 length=0x0000000000001000 dlen=32 srec=1 expected=0 digest=acb0cc67e2c3326bd3ffaab74989b2e3d621a55dabb28fad3420669abf3be755
BE_MVP:19 LOG record seq=11 producer=0 type=measured stream=3 object=kernel-image repr=as-placed outcome=recorded base=0x0000000114200000 length=0x00000000001f7cc4 dlen=32 srec=0 expected=0 digest=11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f3bdce07
BE_MVP:19 LOG record seq=12 producer=0 type=measured stream=3 object=device-tree repr=as-placed outcome=gated-pass base=0x0000000117e00000 length=0x0000000000001000 dlen=32 srec=1 expected=0 digest=03e25ec8838e5999d0806c526a6e41b6f51d990b1cd9f77d707ae7d68bfbf863
BE_MVP:19 LOG record seq=13 producer=0 type=close stream=255 object=close repr=none outcome=none base=0x0000000000000000 length=0x0000000000000000 dlen=32 srec=0 expected=14 digest=0000000000000000000000000000000000000000000000000000000000000000
BE_MVP:20 REGISTERS at=barrier r0=e0ea07e6f0a2a8cf3b01451611ad099709dd9a2e68cfb605310284e49e04fa33 r1=2241f9eb0370fc6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1 r2=b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792 r3=7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5 ticks=0x2a3f10
BE_MVP:20 REGISTERS at=terminal r0=e0ea07e6f0a2a8cf3b01451611ad099709dd9a2e68cfb605310284e49e04fa33 r1=2241f9eb0370fc6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1 r2=b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792 r3=7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5
```

The export, displayed with each record on eight lines; it is the same JSON
value as the canonical file (5.1), whose 8,153 bytes have the SHA-256
`2337149b55e10cf8b03e464638e686f7a2c0673dc6e8aadc48bfffc09b2142dc`:

```json
{
 "header": {"capacity": 41, "configuration_identity":
   "9f6f6d940a41d7af494a1e4c1afe1b6edcf8793912b5755de37d57b9adb08849",
  "count": 14, "hashAlg": "sha256", "header_length": 128, "magic": "BEMVPLOG",
  "record_length": 96, "scenario_sha256":
   "5c74d0dcde52a6a6c1ffcc50d176f51d74e7b669a8c7608b6d5c9955ee34a9ba",
  "state": "closed", "version": 1},
 "records": [
  {"content": {"base": "0x0000000102000000", "expected": 0, "length": "0x0000000000004540",
    "object": "monitor-text", "outcome": "recorded", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "96704ef2f5b319b854004242adf83cea20e272e01697402d9d968650f0f0c392",
    "hashAlg": "sha256"}],
   "recnum": 0, "register": 0, "srec": 0},
  {"content": {"base": "0x0000000102008610", "expected": 0, "length": "0x00000000000002e8",
    "object": "monitor-rodata", "outcome": "recorded", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "ab1aea296cbff86a1cb5156562601b239f292db71c89b5399a222fe8ca6bdc73",
    "hashAlg": "sha256"}],
   "recnum": 1, "register": 0, "srec": 1},
  {"content": {"base": "0x0000000102008000", "expected": 0, "length": "0x0000000000000610",
    "object": "monitor-input", "outcome": "recorded", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "8b876a7e36e8161d6b2199a998d6213e1448cf46699dce4fbf80b277eb08564e",
    "hashAlg": "sha256"}],
   "recnum": 2, "register": 0, "srec": 2},
  {"content": {"base": "0x0000000102064000", "expected": 0, "length": "0x0000000000006a40",
    "object": "mvp-text", "outcome": "recorded", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "ec6d6ddf35da0c8bcd41de09b0e3c1e34e3aec6fc50c0835749797309d272039",
    "hashAlg": "sha256"}],
   "recnum": 3, "register": 0, "srec": 3},
  {"content": {"base": "0x000000010206aa40", "expected": 0, "length": "0x0000000000001238",
    "object": "mvp-rodata", "outcome": "recorded", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "06a35b4b92030141900fc59c7db016bb483c37ddd1962a4f8ee739c72279b5aa",
    "hashAlg": "sha256"}],
   "recnum": 4, "register": 0, "srec": 4},
  {"content": {"base": "0x0000000000000000", "expected": 0, "length": "0x0000000000000000",
    "object": "core-identity", "outcome": "recorded", "producer": 0,
    "representation": "as-computed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "f958c31fd593ea0db3bd787a5e45bf2383fdeb8f831d5a451c89a4c3171a933b",
    "hashAlg": "sha256"}],
   "recnum": 5, "register": 1, "srec": 0},
  {"content": {"base": "0x0000000000000000", "expected": 0, "length": "0x0000000000000000",
    "object": "console-grants", "outcome": "recorded", "producer": 0,
    "representation": "as-computed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7",
    "hashAlg": "sha256"}],
   "recnum": 6, "register": 1, "srec": 1},
  {"content": {"base": "0x0000000000000000", "expected": 0, "length": "0x0000000000000000",
    "object": "configuration-identity", "outcome": "recorded", "producer": 0,
    "representation": "build-recorded", "type": "informational"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "9f6f6d940a41d7af494a1e4c1afe1b6edcf8793912b5755de37d57b9adb08849",
    "hashAlg": "sha256"}],
   "recnum": 7, "register": 1, "srec": 2},
  {"content": {"base": "0x0000000000000000", "expected": 0, "length": "0x0000000000000000",
    "object": "policy-identity", "outcome": "recorded", "producer": 0,
    "representation": "build-recorded", "type": "informational"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "04687fe4d6177770e89b698f53d82ed52b266c793f5c46318bf8308f020e01aa",
    "hashAlg": "sha256"}],
   "recnum": 8, "register": 1, "srec": 3},
  {"content": {"base": "0x0000000110200000", "expected": 0, "length": "0x00000000001f7cc4",
    "object": "kernel-image", "outcome": "recorded", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f3bdce07",
    "hashAlg": "sha256"}],
   "recnum": 9, "register": 2, "srec": 0},
  {"content": {"base": "0x0000000113e00000", "expected": 0, "length": "0x0000000000001000",
    "object": "device-tree", "outcome": "gated-pass", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "acb0cc67e2c3326bd3ffaab74989b2e3d621a55dabb28fad3420669abf3be755",
    "hashAlg": "sha256"}],
   "recnum": 10, "register": 2, "srec": 1},
  {"content": {"base": "0x0000000114200000", "expected": 0, "length": "0x00000000001f7cc4",
    "object": "kernel-image", "outcome": "recorded", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f3bdce07",
    "hashAlg": "sha256"}],
   "recnum": 11, "register": 3, "srec": 0},
  {"content": {"base": "0x0000000117e00000", "expected": 0, "length": "0x0000000000001000",
    "object": "device-tree", "outcome": "gated-pass", "producer": 0,
    "representation": "as-placed", "type": "measured"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "03e25ec8838e5999d0806c526a6e41b6f51d990b1cd9f77d707ae7d68bfbf863",
    "hashAlg": "sha256"}],
   "recnum": 12, "register": 3, "srec": 1},
  {"content": {"base": "0x0000000000000000", "expected": 14, "length": "0x0000000000000000",
    "object": "close", "outcome": "none", "producer": 0,
    "representation": "none", "type": "close"},
   "content_type": "beryllium-log-v1",
   "digests": [{"digest":
    "0000000000000000000000000000000000000000000000000000000000000000",
    "hashAlg": "sha256"}],
   "recnum": 13, "register": null, "srec": 0}
 ],
 "registers": {
  "barrier": [
   "e0ea07e6f0a2a8cf3b01451611ad099709dd9a2e68cfb605310284e49e04fa33",
   "2241f9eb0370fc6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1",
   "b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792",
   "7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5"
  ],
  "replayed": [
   "e0ea07e6f0a2a8cf3b01451611ad099709dd9a2e68cfb605310284e49e04fa33",
   "2241f9eb0370fc6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1",
   "b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792",
   "7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5"
  ],
  "replayed_label": "unprotected",
  "terminal": [
   "e0ea07e6f0a2a8cf3b01451611ad099709dd9a2e68cfb605310284e49e04fa33",
   "2241f9eb0370fc6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1",
   "b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792",
   "7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5"
  ]
 },
 "schema": "be-mvp-log-v1"
}
```

The reference manifest, displayed the same way; the canonical file's
10,993 bytes have the SHA-256
`608dc4d4de3782cef2c8ca4c79e79865f4225aaee7df42a579e053f351b9a74c`:

```json
{
 "authority_report_sha256":
  "e4b51e9e61a8f8a7a914342e783e6914d6849512028dfc463a9783d0f090fef7",
 "boot_image_sha256":
  "0949dab4b1345237f023f9498026ac053fab7f96af9d67e241d3dd0ca1874ed2",
 "contract": {"run": "complete", "sequence": "v2"},
 "elf_sha256":
  "ee910a9ec479845d6d370613cafaa1ec4bb053a7183eea546fa7109d1c0c7af4",
 "expected": {
  "header": {"capacity": 41, "configuration_identity":
    "9f6f6d940a41d7af494a1e4c1afe1b6edcf8793912b5755de37d57b9adb08849",
   "count": 14, "hashAlg": "sha256", "header_length": 128, "magic": "BEMVPLOG",
   "record_length": 96, "scenario_sha256":
    "5c74d0dcde52a6a6c1ffcc50d176f51d74e7b669a8c7608b6d5c9955ee34a9ba",
   "state": "closed", "version": 1},
  "records": [
   {"content": {"base": "0x0000000102000000", "expected": 0, "length": "0x0000000000004540",
     "object": "monitor-text", "outcome": "recorded", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "96704ef2f5b319b854004242adf83cea20e272e01697402d9d968650f0f0c392",
     "hashAlg": "sha256"}],
    "recnum": 0, "register": 0, "srec": 0},
   {"content": {"base": "0x0000000102008610", "expected": 0, "length": "0x00000000000002e8",
     "object": "monitor-rodata", "outcome": "recorded", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "ab1aea296cbff86a1cb5156562601b239f292db71c89b5399a222fe8ca6bdc73",
     "hashAlg": "sha256"}],
    "recnum": 1, "register": 0, "srec": 1},
   {"content": {"base": "0x0000000102008000", "expected": 0, "length": "0x0000000000000610",
     "object": "monitor-input", "outcome": "recorded", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "8b876a7e36e8161d6b2199a998d6213e1448cf46699dce4fbf80b277eb08564e",
     "hashAlg": "sha256"}],
    "recnum": 2, "register": 0, "srec": 2},
   {"content": {"base": "0x0000000102064000", "expected": 0, "length": "0x0000000000006a40",
     "object": "mvp-text", "outcome": "recorded", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "ec6d6ddf35da0c8bcd41de09b0e3c1e34e3aec6fc50c0835749797309d272039",
     "hashAlg": "sha256"}],
    "recnum": 3, "register": 0, "srec": 3},
   {"content": {"base": "0x000000010206aa40", "expected": 0, "length": "0x0000000000001238",
     "object": "mvp-rodata", "outcome": "recorded", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "06a35b4b92030141900fc59c7db016bb483c37ddd1962a4f8ee739c72279b5aa",
     "hashAlg": "sha256"}],
    "recnum": 4, "register": 0, "srec": 4},
   {"content": {"base": "0x0000000000000000", "expected": 0, "length": "0x0000000000000000",
     "object": "core-identity", "outcome": "recorded", "producer": 0,
     "representation": "as-computed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "f958c31fd593ea0db3bd787a5e45bf2383fdeb8f831d5a451c89a4c3171a933b",
     "hashAlg": "sha256"}],
    "recnum": 5, "register": 1, "srec": 0},
   {"content": {"base": "0x0000000000000000", "expected": 0, "length": "0x0000000000000000",
     "object": "console-grants", "outcome": "recorded", "producer": 0,
     "representation": "as-computed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7",
     "hashAlg": "sha256"}],
    "recnum": 6, "register": 1, "srec": 1},
   {"content": {"base": "0x0000000000000000", "expected": 0, "length": "0x0000000000000000",
     "object": "configuration-identity", "outcome": "recorded", "producer": 0,
     "representation": "build-recorded", "type": "informational"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "9f6f6d940a41d7af494a1e4c1afe1b6edcf8793912b5755de37d57b9adb08849",
     "hashAlg": "sha256"}],
    "recnum": 7, "register": 1, "srec": 2},
   {"content": {"base": "0x0000000000000000", "expected": 0, "length": "0x0000000000000000",
     "object": "policy-identity", "outcome": "recorded", "producer": 0,
     "representation": "build-recorded", "type": "informational"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "04687fe4d6177770e89b698f53d82ed52b266c793f5c46318bf8308f020e01aa",
     "hashAlg": "sha256"}],
    "recnum": 8, "register": 1, "srec": 3},
   {"content": {"base": "0x0000000110200000", "expected": 0, "length": "0x00000000001f7cc4",
     "object": "kernel-image", "outcome": "recorded", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f3bdce07",
     "hashAlg": "sha256"}],
    "recnum": 9, "register": 2, "srec": 0},
   {"content": {"base": "0x0000000113e00000", "expected": 0, "length": "0x0000000000001000",
     "object": "device-tree", "outcome": "gated-pass", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "acb0cc67e2c3326bd3ffaab74989b2e3d621a55dabb28fad3420669abf3be755",
     "hashAlg": "sha256"}],
    "recnum": 10, "register": 2, "srec": 1},
   {"content": {"base": "0x0000000114200000", "expected": 0, "length": "0x00000000001f7cc4",
     "object": "kernel-image", "outcome": "recorded", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f3bdce07",
     "hashAlg": "sha256"}],
    "recnum": 11, "register": 3, "srec": 0},
   {"content": {"base": "0x0000000117e00000", "expected": 0, "length": "0x0000000000001000",
     "object": "device-tree", "outcome": "gated-pass", "producer": 0,
     "representation": "as-placed", "type": "measured"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "03e25ec8838e5999d0806c526a6e41b6f51d990b1cd9f77d707ae7d68bfbf863",
     "hashAlg": "sha256"}],
    "recnum": 12, "register": 3, "srec": 1},
   {"content": {"base": "0x0000000000000000", "expected": 14, "length": "0x0000000000000000",
     "object": "close", "outcome": "none", "producer": 0,
     "representation": "none", "type": "close"},
    "content_type": "beryllium-log-v1",
    "digests": [{"digest":
     "0000000000000000000000000000000000000000000000000000000000000000",
     "hashAlg": "sha256"}],
    "recnum": 13, "register": null, "srec": 0}
  ],
  "registers": [
   "e0ea07e6f0a2a8cf3b01451611ad099709dd9a2e68cfb605310284e49e04fa33",
   "2241f9eb0370fc6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1",
   "b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792",
   "7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5"
  ]
 },
 "image": "te-poc",
 "launch_expected": [
  "b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792",
  "7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5"
 ],
 "mutated_image_sha256": null,
 "r2": "kept",
 "ranges": [
  {"base": "0x0000000102000000", "digest":
    "96704ef2f5b319b854004242adf83cea20e272e01697402d9d968650f0f0c392",
   "domain": null, "image_offset": "0x0000000000001000", "length": "0x0000000000004540",
   "object": "monitor-text", "source": "boot-image"},
  {"base": "0x0000000102008610", "digest":
    "ab1aea296cbff86a1cb5156562601b239f292db71c89b5399a222fe8ca6bdc73",
   "domain": null, "image_offset": "0x0000000000009610", "length": "0x00000000000002e8",
   "object": "monitor-rodata", "source": "boot-image"},
  {"base": "0x0000000102008000", "digest":
    "8b876a7e36e8161d6b2199a998d6213e1448cf46699dce4fbf80b277eb08564e",
   "domain": null, "image_offset": "0x0000000000009000", "length": "0x0000000000000610",
   "object": "monitor-input", "source": "boot-image"},
  {"base": "0x0000000102064000", "digest":
    "ec6d6ddf35da0c8bcd41de09b0e3c1e34e3aec6fc50c0835749797309d272039",
   "domain": null, "image_offset": "0x0000000000065000", "length": "0x0000000000006a40",
   "object": "mvp-text", "source": "boot-image"},
  {"base": "0x000000010206aa40", "digest":
    "06a35b4b92030141900fc59c7db016bb483c37ddd1962a4f8ee739c72279b5aa",
   "domain": null, "image_offset": "0x000000000006ba40", "length": "0x0000000000001238",
   "object": "mvp-rodata", "source": "boot-image"},
  {"base": "0x0000000110200000", "digest":
    "11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f3bdce07",
   "domain": 0, "image_offset": null, "length": "0x00000000001f7cc4",
   "object": "kernel-image", "source": "guest/Image"},
  {"base": "0x0000000113e00000", "digest":
    "acb0cc67e2c3326bd3ffaab74989b2e3d621a55dabb28fad3420669abf3be755",
   "domain": 0, "image_offset": null, "length": "0x0000000000001000",
   "object": "device-tree", "source": "guest/mvp-guest-g0-te-poc.dtb"},
  {"base": "0x0000000114200000", "digest":
    "11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f3bdce07",
   "domain": 1, "image_offset": null, "length": "0x00000000001f7cc4",
   "object": "kernel-image", "source": "guest/Image"},
  {"base": "0x0000000117e00000", "digest":
    "03e25ec8838e5999d0806c526a6e41b6f51d990b1cd9f77d707ae7d68bfbf863",
   "domain": 1, "image_offset": null, "length": "0x0000000000001000",
   "object": "device-tree", "source": "guest/mvp-guest-g1-te-poc.dtb"}
 ],
 "scenario": "te-poc",
 "schema": "be-mvp-log-reference-v1",
 "source": {"commit": "0123456789abcdef0123456789abcdef01234567", "tree_state": "clean"},
 "toolchain": "gcc",
 "variant": null
}
```

## 6. The mapping to CEL 1.1

CEL 1.1, the document section 1 identifies, defines a Canonical Event Log
Record of four fields, a record number, a PCR or NV index, the digests
extended, and the content (its section 4.2 and Table 1), with a content
type that the JSON and CBOR encodings carry beside the content (Table 2).
The section and table numbers below are CEL 1.1's. The profile maps onto
those fields as follows.

| Profile field (export) | Page | CEL 1.1 field | Relation |
| --- | --- | --- | --- |
| `srec` | per-stream record number (offset 26) | `recnum` (4.2.2; Table 1, 0) | Mapped: from zero, one sequence per index, incremented for every record of the stream, informational ones included, as 4.2.2 requires of a log with several indices |
| `recnum` | sequence (offset 0) | `recnum` | Same name, other scope: CEL keeps its record number per PCR or NV index in such a log (4.2.2, item 3); the profile's `recnum` is global across the four streams |
| `register` | stream (offset 4) | `pcr` (4.2.3; Table 1, 1) or `nv_index` (2) | Position only: CEL names a TPM PCR (0 to `0xFFFFFF`) or NV index; the profile names one of four software registers in hart 0's memory (2.6), never a PCR, and `null` for the close. As CEL's unmeasured event names a PCR it does not affect (4.2.3), an informational record names its stream's register and does not extend it |
| `digests` | digest (offset 32), digest length (24), the header's algorithm (20) | `digests` (4.2.4; `TPML_DIGEST_VALUES` of `TPMT_HA` with `hashAlg` and `digest`, 5.2; `TPM_ALG_SHA256` written `"sha256"`) | Shape mapped, one bank, SHA-256. A measured record's digest is the value extended, as CEL's "digest values Extended", by the extend's form `R := SHA-256(R \|\| digest)`; an informational record's is not extended; `policy-absent`'s and the close's are zero |
| `content_type` | none (the page's magic and version) | `content_type` (Table 2: `cel` 4, `pcclient_std` 5, `ima_template` 7, `ima_tlv` 8, `systemd` 9) | Not mapped: `beryllium-log-v1` is a private value no CEL table registers |
| `content` | the record's other fields | `content` (4.2.5; defined by its content type's custodian) | A container only: its fields are the profile's own, below |

Unmapped, with no CEL counterpart: the header (magic, version, lengths,
capacity, count, state, algorithm, scenario digest, configuration
identity), for which CEL has no log header (its nearest is the unmeasured
`cel_version` management event, 4.4.1, which the profile does not emit);
the close and its expected count (CEL's `firmware_end`, 4.4.2, marks a
phase and is not emitted); the per-stream number kept beside a global
sequence; the producer; the type (CEL tells measured from unmeasured events
by each content type's own rules); the object, representation, outcome, base, length,
and expected count; and the registers' values, printed at the barrier and
the terminal and replayed, which CEL carries nowhere (a TPM supplies a
PCR's value), and which the profile interprets as software values in hart
0's memory, labelled `unprotected` when replayed. The reference manifest
has no CEL counterpart.

No interoperability is claimed: no CEL reader, TPM event-log tool, or
systemd tool is expected to read the export, and no `.pcrlock` file
(systemd v259, whose JSON uses `pcr` and `digests`) is read or written. CEL
1.1's section 5.2 says that CEL-JSON is specified authoritatively by the
TCG TSS 2.0 JSON Data Types and Policy Language Specification; the profile
neither consults nor follows it. A lossless adapter to the TCG and systemd
model is one route of the crosswalk M9-5 writes (D-7), analysed and not
implemented.

## 7. The allowlist (D-5)

The capture checker and the reference reader accept exactly these values
and refuse anything else, in a line, an export, or a reference manifest:

- **objects**: `monitor-text`, `monitor-rodata`, `monitor-input`,
  `mvp-text`, `mvp-rodata`, `core-identity`, `console-grants`,
  `configuration-identity`, `policy-identity`, `policy-absent`,
  `kernel-image`, `device-tree`, `secret-page`, `close` (numbers 0 to 13);
- **content type**: `beryllium-log-v1`;
- **schemas**: `be-mvp-log-v1` (the export) and `be-mvp-log-reference-v1`
  (the reference manifest);
- **algorithm**: `0x000B`, `alg=0x000b`, `"hashAlg": "sha256"`;
- **types**: `measured`, `informational`, `close`; **streams**: 0 to 3 and
  255; **representations**: `as-placed`, `as-computed`, `build-recorded`,
  `none`; **outcomes**: `recorded`, `gated-pass`, `gated-fail`, `none`;
  **states**: `open`, `closed`, `overflow`; **producer**: 0;
- **reference fields** (5.3): `contract.sequence` `v1`, `v2`, `v3`,
  `probe`; `contract.run` `complete`, `pre-measurement`, `gate-fail`,
  `self-report-flip`, `post-launch-failure`; `r2` `kept`, `dropped`;
  `ranges[].source` `boot-image`, `scenario-secret`, or a path relative to
  `build/mvp/` naming a kernel Image or device tree the build made, with no
  `..` component and no leading `/`.

So an IMA measurement list, a CEL content type other than the profile's
(`cel`, `pcclient_std`, `ima_template`, `ima_tlv`, `systemd`), an IMA
template name (`ima`, `ima-ng`, `ima-sig`, `ima-buf`, `ima-modsig`), a
`boot_aggregate` record, a file path as an object, or an object number
above 13 is refused, and so is a reference manifest that names one. This is
one of D-5's three checks; the other two are `tools/guest-pins.py`'s
refusal of `CONFIG_IMA`, `CONFIG_IMA_*`, and `CONFIG_EVM` in any guest
configuration Beryllium builds (M9-3), and the claim ledger's boundary row
(M9-5), each with its negative case (Q15). The log measures images,
configuration, and policy at the domain boundary, never files inside a
guest.

## 8. What the profile does not say

- **The log is a local identity, not attestation**: it has no key, nonce,
  freshness, or root of trust, so code able to alter the monitor can
  fabricate its records, and a record does not show the bytes unchanged
  after the point of measurement (D-9).
- **The registers bind digest values only**: each binds its stream's
  ordered measured digests and nothing else; the objects, ranges, types,
  outcomes, header, informational records, and the order across streams are
  bound only by the checker's comparison with the reference, and the close
  is structural. Quoting the four registers does not authenticate the log
  (Revision 3, R3.2).
- Stream 0 is a self-report: compared offline, gating nothing, and no
  evidence against an adversary who alters the monitor; that no domain hart
  reads the page is a code discipline within HS, not hardware protection.
- The export is not a TPM event log, the registers are not PCRs, and the
  profile is not CEL (section 6).
- SPL, OpenSBI, U-Boot, and the board's device tree are unmeasured; the
  loader observation and the platform observation are other evidence
  classes, never in the log, and the three are never one chain (D-6).
- Nothing is said about the bytes of a kernel, device tree, or secret page
  after the point of measurement, about any file inside a guest, or about
  the firmware's, the loader's, or the boot ROM's integrity.
- The claim's words are [claim.md](claim.md)'s, with the sentences D-9
  fixes taking effect through M9's result; this profile adds none.
