<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M9 crosswalk: the Beryllium log against the TCG and systemd model

**Status:** the analysis deliverable of the accepted [M9 plan](mvp-m9-plan.md)'s
D-7 (Q39: analysed, not implemented), written in work package M9-5 on
2026-11-03 against the log the M9 tree keeps
(`mvp/docs/log-profile.md`, version 1). It compares; it
selects nothing, implements nothing, and changes no claim. Every systemd
fact below is read from systemd **v259**'s own text (the manual sources at
the tag `v259` of `github.com/systemd/systemd`, `man/systemd.pcrlock.xml`,
`man/systemd-pcrlock.xml`, `man/systemd-measure.xml`,
`man/systemd-pcrphase.service.xml`, and `docs/TPM2_PCR_MEASUREMENTS.md`;
the rendered `systemd.pcrlock(5)` manual is at
`https://www.freedesktop.org/software/systemd/man/latest/systemd.pcrlock.html`),
read on 2026-11-03; `systemd-pcrlock` and `systemd-measure` say of
themselves that they are experimental and may change. Where this document
says what a tool does, it is that text's statement, not a test made here.
**No claim of stock systemd compatibility is made or implied until a
TPM-facing interface and an adapter exist**; the profile's own section 6
says the export is not CEL and no tool is expected to read it.

## 1. What is compared, and why

The MVP plan's D20 (`measure first, then attest`) puts measurement in
MVP 1.0 (M9) and attestation with a simulated root of trust in MVP 2.0,
and directs that systemd's measured-boot stack and Amutable's work be
analysed in M9 and implemented, if at all, from 2.0. M9 built one thing:
a bounded log in hart 0's memory of what the control hart placed or
sealed before any domain starts, with one software register per stream,
a per-domain launch gate against a pre-link constant, a post-link
reference per image, and a checker that rebuilds, replays, recomputes,
and compares (the M9 plan's D-1 to D-4). Three later routes could carry
that log toward the TCG and systemd model:

- **(a) a minimal vTPM per domain** with a standard TCG event log, so that
  a guest's own stack (systemd's included) sees PCRs and a log it already
  understands;
- **(b) a Beryllium measurement-register SBI extension**, one register set
  per domain that a guest extends through an SBI call and the monitor
  logs, with no TPM command set;
- **(c) a lossless adapter** from the Beryllium log profile to the TCG
  Canonical Event Log form and systemd's `.pcrlock` component files, run
  offline on the export and the reference, with no change to the monitor.

Section 2 crosswalks the four systemd pieces the plan names against the
log on five dimensions. Section 3 states what the reference manifest
already supplies toward each route. Section 4 is the requirements
crosswalk among (a), (b), and (c). Section 5 states what attestation with
a simulated root needs from the log. Section 6 shows how a guest's own
IMA stays outside Beryllium's evidence under (a) and (b). Section 7 places
the implementation plan's milestone 7 items. Section 8 records the one
Amutable lesson. Section 9 lists what this document does not decide.

## 2. systemd v259, piece by piece

The five dimensions are the plan's: the artifact boundaries (what is
measured, as which unit), the event and phase semantics (what a record
means and when it is made), the reference generation and update rule
(how the expected values come to exist and when they change), reset and
replay (what a reset does and how a reader re-derives the state), and the
verifier's trust (who checks, against what, trusting whom). The last row
of each table is the Beryllium log as M9 built it, for the comparison.

### 2.1 `systemd.pcrlock(5)` and `systemd-pcrlock(8)`

| Dimension | systemd v259 | Beryllium M9 |
| --- | --- | --- |
| Artifact boundaries | `*.pcrlock` files, each "one set of expected, ordered PCR measurements of a specific component of the boot", JSON arrays in "a subset of the TCG Canonical Event Log Format (CEL-JSON)" in which `recnum`, `content`, and `content_type` "are not used and ignored if present"; variants of a component in `NAME.pcrlock.d/*.pcrlock`; files ordered by their `NNN-component` names across the drop-in directories. Its inputs are the firmware's TPM2 event log, the userspace log `/run/log/systemd/tpm2-measure.log`, the TPM's current PCR values, and the component files | one page per boot, one export (`log.json`) per run, one reference per image and toolchain (`build/mvp/references/<toolchain>/<image>.json`); the component is the image, not a boot stage; variants are the image's variants (`wrong-measurement`, `self-report-flip`, the shells), each its own reference, not alternatives one policy admits |
| Event and phase semantics | well-known components `240` (SecureBoot policy, PCR 7) to `990` (final shutdown, PCR 11), with separators (`400`, `500`, `700`) marking where firmware control ends; a record is a PCR index and digests; phases are PCR 11 strings (2.3) | four streams of software registers, never PCRs; records typed `measured`, `informational`, `close`, with an object, a representation, and an outcome; no phase after start: the terminal `:20` line re-prints the barrier's values and extends nothing; the close marks the end of measurement, not a boot stage |
| Reference generation and update rule | `lock-*` commands write `.pcrlock` files from the current boot's event log "only ... if the event log matches the current TPM2 PCR state", from a PE or UKI file (`lock-pe`, `lock-uki`), from the GPT, the machine ID, or the SecureBoot variables; `predict` enumerates "all possible resulting PCR values for all combinations of component variants" and makes no prediction for a PCR whose log does not match, has unrecognized events, or lacks a defined component; `make-policy` stores a `PolicyPCR`/`PolicyOR` policy in a TPM2 NV index, "allocated on first invocation, and updated on subsequent invocations", under `PolicyAuthorizeNV`, with a recovery PIN; `unlock-*` before a firmware update, then `make-policy` again | the reference is generated from the linked image after every build and never edited (profile 5.3); the expected launch registers are pre-link constants in `.mvp.rodata`; the update rule is: a new build is a new reference and a new image, with no policy object and no state outside the image; nothing is predicted across variants, each image is compared with its own reference |
| Reset and replay | PCRs are reset by the platform; the policy predicts future boots; the NV index and the `.pcrlock` files persist in `/var/lib/`; `log` and `cel` replay the combined event log and validate it against the PCR values | the page and the registers are zero at every boot and live only in hart 0's BSS; nothing persists across a reset; the checker replays the registers from the printed records and compares them with both `:20` lines, labelling the replayed values `unprotected` |
| Verifier's trust | the TPM (its PCRs, its NV index, `PolicyAuthorizeNV`; "TPM 2.0 version 1.38 or newer"), the firmware's event log, and the local tool; the "verifier" is the TPM's policy evaluation when a secret is unsealed, not a remote party | the offline evidence TCB (security model v1 Revision 3): the checker, the reference tool, the generator, the build's inputs, and the human reading the record; no TPM, no key, no policy object; a consistency witness, not evidence against an adversary who alters the monitor |

### 2.2 `systemd-measure(1)` and UKIs (UAPI.5)

| Dimension | systemd v259 | Beryllium M9 |
| --- | --- | --- |
| Artifact boundaries | a Unified Kernel Image (UAPI.5, `https://uapi-group.org/specifications/specs/unified_kernel_image/`): one PE binary whose sections `.linux` (mandatory), `.osrel`, `.cmdline`, `.initrd`, `.ucode`, `.splash`, `.dtb`, `.uname`, `.sbat`, `.pcrpkey`, `.profile`, `.dtbauto`, `.hwids` are the units of measurement; `ukify` builds it and invokes `systemd-measure` | the boot image (one flat file U-Boot loads and attributes by MD5) holds the monitor and the staged guest inputs; the units of measurement are not sections of that file but the objects as placed: each domain's kernel Image and device tree in its window, `anchor`'s secret page, the monitor's five ranges as loaded; the kernel command line is inside the device tree, so it is measured with it; there is no initrd (the init is in the kernel) |
| Event and phase semantics | `systemd-stub` measures each UKI section into PCR 11 as a pair of `EV_IPL` records, the section name (with its trailing NUL) then the section data, in the UKI specification's canonical order (`docs/TPM2_PCR_MEASUREMENTS.md`); add-ons, credentials, and the command line go to PCR 12, sysexts to PCR 13; phases are the `--phase=` strings of 2.3 | each object is one record with its own name (`kernel-image`, `device-tree`, `secret-page`, …) in a fixed per-image order (profile 3.1); the name is a field of the record, not a separate measured event; one stream per domain so that a domain's launch register binds its own objects only |
| Reference generation and update rule | `calculate` pre-computes PCR 11 "in a fashion compatible with what `systemd-stub` does at boot" from the section files, starting from a zero PCR; `sign` signs the values per bank with an RSA key pair; `policy-digest` prints the policy digest for offline signing; `ukify` embeds the result in the UKI (`.pcrsig`, `.pcrpkey`); a new UKI is a new calculation | the generator computes each domain's expected launch register from the same inputs the monitor will measure, by the profile's recurrence, and links it as a constant; the reference tool recomputes the whole log after the link; no signature; a new build is a new constant and a new reference |
| Reset and replay | the expected value is a function of the UKI's bytes; `status` reads the live PCR 11 for comparison | the gate compares the live register with the constant before the domain starts; the checker recomputes every digest from the build's inputs and compares the printed registers with its replay |
| Verifier's trust | the signing key (and `--pcrpkey=`, the key the booted system locks resources to), the TPM evaluating the signed policy, and `systemd-stub`'s code; a secret unlocks for any kernel whose signed expected value is presented | the image's own constant (the gate trusts the image it is part of), and offline the checker and the build; nothing unlocks and nothing is signed |

### 2.3 `systemd-pcrphase.service(8)` and the NvPCRs

| Dimension | systemd v259 | Beryllium M9 |
| --- | --- | --- |
| Artifact boundaries | literal strings, not files: `enter-initrd`, `leave-initrd`, `sysinit`, `ready`, `shutdown`, `final` into PCR 11; the machine ID into PCR 15; file-system identity (type, UUID, label, partition UUIDs and label) into PCR 15; the product UUID into the NvPCR `hardware`; LUKS volume-key derivatives and key-slot facts into PCR 15 and the NvPCR `cryptsetup`; NvPCRs are TPM NV indexes of type `TPM2_NT_EXTEND`, named by `/usr/lib/nvpcr/*.nvpcr` files (v259) | no phase strings and no identity strings after start; the one identity-like record is the sealed core identity (`core-identity`, measured) and the console grants beside it; a run's later states (`DOMAIN_PAUSED`, `DOMAIN_TERMINATED`, the shutdown) are printed lines the checker judges, not measurements |
| Event and phase semantics | a phase string is a barrier "between the time where the kernel initializes and where the initrd starts operating", between initrd and host, before and after user log-in, at shutdown; the "phase path" (`enter-initrd:leave-initrd:sysinit:ready`) names a point in the boot; policy bound to a phase path is unusable after the next string is extended; the services run only when `systemd-stub` invoked the kernel | the log has exactly two points: the barrier (every record made, the page closed, both `:20` values printed) and the terminal line (the same values re-printed); a point between them would be a profile version 2 and a new record type; nothing in 1.0 binds authority to a point in time |
| Reference generation and update rule | the six strings are "just the default strings"; their `.pcrlock` components (`750`, `800`, `850`, `900`, `950`, `990`) are "statically defined"; `systemd-measure --phase=` pre-computes the value at each path | the expected count and registers are per image; there is no administrator-defined record |
| Reset and replay | NvPCRs "can be deleted by anyone with access to the TPM, and then be recreated", so systemd measures an anchoring secret into each NvPCR first, stored in `/run/`, `/var/lib/`, and the ESP; `docs/TPM2_PCR_MEASUREMENTS.md`: "any process with access to the TPM and read access to any of the storage locations of the anchor secret is considered part of the TCB, as they are able to replay the NvPCR with their own content at will" | the same shape of caveat, stated in the log's own terms: the registers are values in hart 0's memory with no anchor, so any code able to write that memory can replay them with its own content; the log's `unprotected` label says so, and U-12 keeps the obligation open |
| Verifier's trust | the TPM, `systemd-stub`, the services, and the anchor secret's storage | the checker and the build; the secret-free design has nothing to leak and nothing to anchor |

### 2.4 Reading the four together

systemd's model has three things the Beryllium log does not: a hardware
register (the PCR, or an NV index with an anchoring secret) that software
cannot write except by extension, a signing key that turns a predicted
value into a policy a TPM enforces, and a chain that begins in firmware
and is continued stage by stage into userspace. The Beryllium log has
three things systemd's model does not need: a per-domain launch gate
that stops a domain before it starts, a per-image post-link reference
that fixes the complete expected log and not only the final values, and
a checker that recomputes every digest from the build's inputs rather
than trusting any event's claimed digest. The first difference is the
one that matters for any later attestation (section 5); the second and
third are what an adapter (route (c)) would carry across unchanged.

## 3. What the reference manifest already supplies

The reference (`be-mvp-log-reference-v1`, profile 5.3) holds, per image
and toolchain: the source commit and tree state; the image, scenario,
variant, and toolchain; the contract (sequence and run class); whether R2
is kept; the authority report's SHA-256; the nominal ELF and boot image
digests and, for `self-report-flip`, the mutated image's; the measured
range table (object, domain, base, length, image offset, source, digest);
the expected launch registers; and the complete expected header, records,
and four final registers.

Toward each route:

| Route | What the reference supplies | What it does not |
| --- | --- | --- |
| (a) vTPM | the expected ordered digests per stream are what a `.pcrlock` component holds per PCR, so an image's reference can be rendered as one component with one variant per image (the `pcrlock` subset keeps only the index and the digests); the launch registers are what a `systemd-measure calculate` prints per bank | no PCR numbers (streams are not PCRs), no bank but SHA-256, no signature, no policy, no firmware or loader records, and no TPM to hold the state |
| (b) SBI extension | the monitor's own streams and their expected values, which a guest's extends must not reach (the gate precedes any guest code; I19 forbids a record after the close) | a guest-extended register class, a producer other than hart 0, and a record type for a guest's extend, all of which are a profile version 2 and an additive security model revision |
| (c) adapter | every field the CEL record form needs except `content_type` and a PCR index (profile section 6 maps `srec` to `recnum`, the stream to an index position, the digest to one `TPMT_HA`); the complete expected log, so the adapter's output is checkable against the reference, not only against the live page | a registered content type (the profile's is private), the firmware and loader records a CEL consumer expects before the first OS record, and any field CEL leaves to its content type's custodian, which Beryllium would have to be |

The reference also fixes the **update rule** the implementation plan's
milestone 7 gate asks about: a reference is a build product, regenerated
on every build, never edited, with no time stamp and no absolute path, so
host and evaluator references are compared byte for byte like the images;
an image's expected values change exactly when its inputs change, and the
`wrong-measurement` image shows what a stale or wrong value does (the gate
fails before any domain hart starts).

## 4. The requirements crosswalk among (a), (b), and (c)

Each row is one requirement a route would have to meet; the cells say what
the route needs from Beryllium, in the project's own units (a profile
version, a security model revision, a model instance, monitor code, a
proof obligation). Nothing here is scheduled; MVP 2.0's item (7) is the
first place attestation may be planned.

| Requirement | (a) minimal vTPM per domain | (b) measurement-register SBI extension | (c) lossless offline adapter |
| --- | --- | --- | --- |
| New guest-visible interface | a TPM 2.0 command subset over a device the guest's driver expects (MMIO or a transport the DTB names), with `PCR_Extend`, `PCR_Read`, `GetCapability`, and, for attestation, `Quote` and key handling: by far the largest surface, and the SBI version and the guest DTB change | one SBI extension (EID in the vendor space beside M2's management extension), FIDs for extend and read, per-domain registers; the SBI version changes, the DTB does not | none: the monitor, the SBI, and the guests are unchanged; the adapter reads `log.json` and the reference |
| Monitor code and the executor seam | a TPM state machine per domain in the proof-bearing subset, a device model or trap path in the executor, PCR banks, an event log the guest can read; the single-executor rule (C-41) applies to every new privileged effect | a small SBI handler and a per-domain register set in the hart page or the MVP region's BSS, under the hart-0-only and per-hart rules | none in the monitor; a Python tool beside `gen-reference.py` |
| Log profile | version 2: records a guest produces (`producer` other than 0), a guest-visible stream per domain, a content type for the guest's events, and a statement of which stream the launch gate binds (the monitor's, never the guest's) | version 2 likewise, smaller: one guest-extended register class, extend records with the guest's digest and a `producer` of that domain | version 1 unchanged; the adapter emits CEL-JSON with the profile's `content_type` and a mapping table in its own README |
| Security model v1 | an additive revision: a new object class (the vTPM state) owned by the monitor per domain, its invariants (a domain reads and extends only its own; no domain writes another's; the monitor's launch streams are not reachable), and the triggers re-evaluated for the new authority | an additive revision with the same shape, one object class (the register set) and the same two invariants | none |
| Model and proofs | a Model 0.2-style instance of the new object (stop (e) in 1.0: no model change), and the M8 stage-1 abstraction of the launch gate extended with "no guest extend precedes the gate" | the same, smaller | none |
| Reference and checker | the reference gains the guest-visible PCRs' expected initial state (what the monitor extends at launch, if anything) and the log of a run gains the guest's events, which the checker records and does **not** judge | the same: guest extends are recorded, compared with nothing, and never evidence | the adapter's output is checked for losslessness: adapter(export) rendered back equals the export byte for byte, and adapter(reference) is a `.pcrlock`-shaped file whose digests equal the reference's |
| IMA boundary (section 6) | the guest may run IMA against its vTPM's PCR 10; Beryllium records nothing from it | the guest may extend its register with an IMA aggregate; Beryllium records the extend as the guest's event and consumes nothing | none: the adapter carries the monitor's records only and the allowlist refuses any IMA content type |
| Board and QEMU evidence | new negative images (a domain extending another's PCR; a guest reading the monitor's stream) in QEMU; one board run of the new images | the same, smaller | host tests of the adapter alone; no board run |
| What it buys | a guest's unmodified measured-boot userspace (systemd's included) sees a TPM-shaped device and could later bind secrets to it; the heaviest route and the only one a stock guest stack can use | a Beryllium-native, small, guest-extensible register with no TPM semantics; usable by a guest built for Beryllium only | a reading of Beryllium's evidence in a form TCG and systemd tooling could parse, with the explicit statement that the registers are not PCRs; the cheapest route and the only one that changes no claim |
| What it does not buy | attestation: a vTPM whose state lives in hart 0's memory is as unanchored as the log (section 5); a quote from it proves what the monitor's code chose to put there | the same | nothing beyond a format: no consumer is expected to act on it (profile section 6) |

Reading the table: (c) is the only route M9's acceptance would leave
unchanged in every claim, and it is what makes the other two checkable
against something a TCG reader understands; (b) is the smallest change
that gives a guest a register; (a) is what a stock guest stack needs and
is a milestone of its own. None of the three gives attestation; section 5
says what would.

## 5. What attestation with a simulated root (MVP 2.0) needs from the log

The MVP plan's item (7) for 2.0 puts attestation "over M9's log with a
simulated root of trust (D20), after M9's event semantics, the verifier's
trust boundary, key custody, freshness, and replay rules are fixed". From
the log as built, such a design needs:

- **A key the monitor's code does not hold in the clear in the same image
  as the code that measures.** A quote is a signature over the registers
  and a challenge; if the signing key is a constant in `.mvp.rodata`, a
  monitor altered before it measures signs whatever it chose to record,
  and the quote adds a signature to the self-report, not evidence. The
  "simulated root" is therefore a separate component with its own
  identity (a simulated endorsement key) and a boundary the monitor cannot
  cross: on the COM260 there is no such component in 1.0 (no TPM, no
  authenticated boot ROM facts; the platform observation is a dated human
  input), so 2.0's root is **simulated** by design and its evidence is of
  the protocol, never of the platform. This is D20's own wording and the
  MVP plan's.
- **The registers as the quoted state, the log beside the quote.** The
  registers bind digest values only (Revision 3, R3.2), so a verifier
  needs the records to know what the values are digests of; the quote
  signs the registers and a nonce, the log and the reference travel
  unsigned, and the verifier replays the log and compares with the
  reference exactly as the checker does today: the checker's replay is
  the verifier's replay, which is why it was built to recompute every
  digest rather than trust the printed ones.
- **Freshness.** A verifier-supplied nonce in the quote, or a monotonic
  counter the root keeps across resets (sealed storage and anti-rollback
  are named in the MVP plan's 2.0 item as features of the simulated
  root; an eFuse-backed counter is stop (a)); the log itself is zero at
  every boot and has no time or counter field (the `ticks` in the `:06`
  and `:20` lines are costs, not time stamps).
- **A protocol and a transport.** Where the challenge arrives and the
  quote leaves: a management-style SBI call from a guest (M2's extension
  shape, decided by hart 0), the console (a typed challenge, under item
  8's rules), or a channel page; each is a new authority and an additive
  security model revision; none exists.
- **The verifier's reference.** The reference manifest, per image, is
  already the thing a verifier compares with, with its update rule
  stated; a verifier policy (which images, which variants) is the
  `.pcrlock`-variants question of section 2.1, which 1.0 answers "one
  image, one reference".
- **A statement of what a successful attestation would show** on this
  platform: that the monitor's code that ran the protocol recorded these
  values, under the assumption that the monitor was not altered before it
  measured, an assumption nothing below it establishes while SPL,
  OpenSBI, and U-Boot are unmeasured and the boot ROM's authentication of
  SPL is a dated platform assumption. The forbidden phrasings of
  `claim.md` keep `attested` and `remote attestation` out of release
  surfaces until that is otherwise.

## 6. How a guest's own IMA stays out of Beryllium's evidence

D20 says IMA is never used, and D-5 made it testable with three checks
(U-17). The question for the routes is not whether a guest may run IMA
(a guest is unmodified upstream Linux and may do as it likes inside its
window) but whether anything the guest measures can become Beryllium's
evidence:

- **Under (a)**, a guest with `CONFIG_IMA` would extend its vTPM's PCR 10
  with its file measurements and keep its own `ascii_runtime_measurements`
  list. Beryllium's log records the monitor's streams only; the vTPM's
  PCR 10 is guest state, never compared with a reference and never
  rendered in a `:19` line; the checker's allowlist (profile section 7)
  refuses `ima_template`, `ima_tlv`, `boot_aggregate`, a file path as an
  object, and any object number outside the enumeration, in a line, an
  export, or a reference; and Beryllium-built guests still may not set
  `CONFIG_IMA` (`guest-pins.py`), so the case arises only for a guest
  Beryllium did not build.
- **Under (b)**, a guest may extend its register with anything, an IMA
  aggregate included. The monitor logs the extend as that domain's event
  (`producer` the domain, in a profile version 2) and interprets nothing;
  the guest's register is not a launch stream, the gate precedes the
  first guest instruction, and I19 forbids a record after the close, so a
  guest extend cannot enter the monitor's streams or move a launch
  register. The checker records guest events and judges none.
- **Under (c)**, the adapter carries the monitor's records only.

In every case the boundary is the same sentence as U-17's: the monitor
measures only what it places or seals before entry, and Beryllium's
evidence consumes no measurement a guest made of itself.

## 7. The implementation plan's milestone 7, placed

[Milestone 7](implementation-plan.md) reads: "Deliver measured
core/configuration/policy, architecture-specific evidence adapters, and a
runtime integrity-monitor experiment. User benefit: cryptographically
verifiable remote evidence that the intended monitor, domain image,
configuration, and policy are running. Gate: document roots of trust,
replay/update behavior, and vendor assumptions."

| Milestone 7 item | M9's standing | Where it belongs |
| --- | --- | --- |
| measured core | delivered as the self-report (stream 0, R2 kept), with its limit stated: compared offline, gating nothing, no evidence against an adversary who alters the monitor | 1.0 (M9) |
| measured configuration | delivered: the sealed core identity and the console grants are measured records of stream 1; the configuration identity is build-recorded | 1.0 (M9) |
| measured policy | delivered as bound, not measured: the policy identity is a build-recorded record, and the authority report's SHA-256 is in the reference; the policy's bytes are not hashed by the monitor, which never holds them | 1.0 (M9); a measured policy record is a profile version 2 question for whoever makes the monitor carry the policy's bytes |
| domain images | delivered: each domain's kernel Image and device tree as placed, and `anchor`'s secret page, gated per domain | 1.0 (M9) |
| architecture-specific evidence adapters | not delivered; route (c) of section 4 is its first form, and the only route without a claim change | 2.0 or later, after a decision on the route |
| runtime integrity-monitor experiment | not delivered. Under D20's line it may measure only what the monitor places, seals, or can observe at the domain boundary at a later point (a window's pages at pause or termination, the G-stage mappings, the sealed state's own words), never a file inside a guest; reading a running guest's memory is a new authority, a TOCTOU-laden one, and an additive security model revision | 2.0 research at the earliest, under its own plan; D20 forbids its IMA-shaped form outright |
| cryptographically verifiable remote evidence | not delivered and not claimed; section 5 | 2.0's item (7), simulated root first |
| gate: document roots of trust | **discharged as "absent"**: the log has no root of trust; the platform's roots are the vendor's SPL, OpenSBI, and U-Boot as installed in NOR, unmeasured, identified by banner and SBI identity; whether the boot ROM authenticates SPL is the platform probe's or the vendor's documentation's answer, dated, and nothing in 1.0 depends on it (the M9 plan's D-6) | 1.0: the claim's required limit, U-16, and the platform-probe record when made |
| gate: replay/update behavior | **discharged as stated**: replay is the checker's, from the printed lines, with the registers `unprotected` and the page zero at every boot; update is "a new build is a new reference and a new constant", with `wrong-measurement` as the negative (section 3) | 1.0: the profile's 4.6 and 5.3, this document |
| gate: vendor assumptions | **discharged as dated**: the U-Boot command set as recorded (`mvp/results/20261030-uboot-help/`, 2026-10-30: `crc32` and `md5sum` present; `hash`, `sha1sum`, `sha256sum`, `tpm`, `tpm2`, `verify` absent), the SBI identity (OpenSBI 1.6, ID 0x1, version 0x10006), the NOR never rewritten to gain a SHA command (Q38), the boot-authentication disposition left to the probe | 1.0: the platform record and U-16 |

So M9 discharges milestone 7's gate for MVP 1.0 in the only way a design
without a root can: by documenting the roots as absent, the replay and
update rules as they are, and the vendor assumptions with their dates. It
delivers the measured core, configuration (measured), policy (bound), and
images, and defers the adapters, the integrity-monitor experiment, and
the remote evidence to MVP 2.0 and later, where each needs its own plan.

## 8. Amutable: one lesson, with its reason

**The primary document.** The plan's Q13 names "one public primary
document" and cites it as "Introducing Amutable Foundations", dated
2026-09-03. Amutable's blog carries two posts those words fit: **"Building
New Secure Foundations"** (`https://amutable.com/blog/building-new-secure-foundations`,
2026-09-03), the overview that opens its upstream series and says the
system is "designed to cryptographically prove what is running on your
infrastructure, not just assume or scan for it. Every component, update,
and configuration is measured and auditable, with trust rooted in
hardware and integrity that's remotely verifiable by system owners", and
names `systemd-pcrlock` and `systemd-report` as the tools it iterates
toward "measured boot with verification"; and **"Introducing Amutable
Foundations"** (`https://amutable.com/blog/introducing-amutable-foundations`,
2026-10-22), the preview announcement, which restates the approach in
more detail: "creators must sign and measure every artifact (including
configuration) that defines how a machine behaves"; configuration is
compiled "into its own signed, integrity-protected images rather than
writing loose files"; machines "measure what they boot" into a TPM or a
confidential VM's measurements; and "the control plane checks reports
against predicted state". The plan's citation joins the second's title to
the first's date; this document takes the 2026-09-03 post as the primary
document the plan dates and reads the 2026-10-22 post as the same
approach stated by its authors in full, both read on 2026-11-03. The
mismatch is recorded as an erratum to the M9 plan for the result packet,
not edited into the accepted text. Amutable's product assurances, its
hardware attestation, its signing, its update framework, and its control
plane are its own and transfer nothing to Beryllium; what is compared is
the shape of the approach.

**The lesson adopted.** Configuration is an artifact measured like code,
not loose state beside it. Amutable's words: "configuration almost always
sits outside of signed image data, and that means it sits outside what
hardware-backed trust can measure". M9 had already taken this shape from
S3-C.5's "images, configuration (measured), and policy (bound)" before the
posts were read for this document, and the log shows it: the sealed
configuration's core identity and console grants are measured records of
stream 1, extended into a register, gated nowhere but compared with the
reference; the policy's identity is build-recorded and bound through the
reference. The reason it fits this non-UEFI, non-TPM monitor: the
configuration is the one artifact Beryllium itself produces at boot from
a declaration (`scenario.json` through the generator, validated, sealed,
and derived by the ported accepted R1 mechanism), so measuring it is
measuring the monitor's own output from known inputs, which needs no
hardware root to be meaningful as a local identity. The shape
declaration → built artifact → predicted state → comparison is also the
shape of M9's pipeline (`scenario.json` → the generated configuration and
the image → the reference manifest → the checker), which is why the
comparison was easy to make.

**Deferred, with the reason.** Signing the artifacts and the reports, and
a verifier that compares a signed report with the predicted state
remotely: both need the key custody and the root section 5 describes, and
Beryllium's platform has neither in 1.0; the local checker is the
comparison without the signature. The update discipline (signed metadata
against "tampering, replay, mix-and-match, and rollback", atomic switch
with fallback): Beryllium has no update path in 1.0, each image being
loaded from the Beryllium partition by the human's session under S3-A's
board policy.

**Rejected for 1.0, with the reason.** Anchoring the machine's identity
in a TPM or a confidential VM's measurements: the COM260 has no TPM, the
monitor is not a confidential VM, and the firmware below it is unmeasured
and not known to be authenticated, so there is nothing to anchor to; the
MVP plan puts a simulated root in 2.0 for exactly this reason. The
"no shell, no SSH, structured interface only" posture: Beryllium's shell
in a domain (M7) is a demonstration the claim names as such, and the
operator's console is a trusted input, so the posture is not in tension
with the claim, but adopting it would be a product decision outside the
MVP.

## 9. What this document does not decide

- No route is selected; MVP 2.0's item (7) and a later plan decide.
- No systemd tool was run against the export or the reference; section 2
  reads systemd's text, and `systemd-pcrlock` and `systemd-measure`
  describe themselves as experimental at v259.
- The profile stays at version 1; every "version 2" above is a name for
  a change nobody has planned.
- The policy's bytes stay unmeasured by the monitor; its identity is
  bound through the reference.
- The claim's words are those of `claim.md` as D-9 fixed them, with the
  slots filled from the recorded outcomes; this document adds none.
