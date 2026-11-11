<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Security model v1

## Decision record

The responsible human accepted this document as security model v1 at exact
commit `0e3eec8b4fd74003f8cedbf2ca66871c31412624` (parent
`3d1b19135d6ae894b72e933a9c6a8e33aa374218`) on 2026-10-22. The
instruction, given in reply to the
[review packet](security-model-v1-review-summary.md)'s request to accept,
revise, or defer that exact commit, was `accept 0e3eec8b`, which resolves
uniquely to that commit.

- **Scope:** acceptance covers exactly the document text at that commit.
  Everything after this section is the document as accepted, including
  the pre-decision status text below; only this section and the
  acceptance fields in the status record were set afterwards.
- **Open questions:** V1 to V4 were not answered, so the defaults the
  document applies stand: validate, with compile as a later optimization
  (V1); the `domain` class defined and granted to no static subject (V2);
  the single static shared page acceptable as static, not revocable, and
  single writer for U1 and U2, and forbidden for U3 (V3); and the first
  MVP milestone's guest memory kept `read write execute` (V4).
- **Review note:** before deciding, the responsible human asked where
  registers are covered. They are covered in Part 1 only, by the
  `vcpu_state` class and invariant I5, a mechanism invariant; Part 2
  declares no `vcpu_state` class, so no policy rule or Part 3 analysis
  covers register state. No revision was requested.
- **Effect:** this document is the accepted statement of Beryllium's
  security properties and planning input to S3. It authorizes no
  implementation, no Model 0.2 change, no management-request vocabulary,
  no runtime mechanism, protected service, specification tool, or
  encoding, no push or merge into the development branch, and not S3,
  which needs its own direction and plan.
- **Revision 1 (2026-10-28):** the responsible human accepted the
  additive section [Revision 1: the hart binding and the third
  instance](#revision-1-2026-10-28-the-hart-binding-and-the-third-instance),
  work package M3-1 of the accepted [M3 plan](mvp-m3-plan.md), at exact
  commit `019cca64971d2399faba3d768d6f5b1fc9145198` (parent `9063b7a5`)
  by the instruction `accept 019cca64`; its first candidate `32298add`
  is superseded. The accepted text of Parts 1 to 7 is byte-identical
  across both commits; the revision's own status line and record carry
  the decision, and
  [`security-model-v1-revision-1-review-summary.md`](security-model-v1-revision-1-review-summary.md)
  is its review and acceptance record. Under the accepted M3 plan, the
  acceptance lets work packages M3-2 to M3-6 begin.
- **Revision 2 (2026-11-01):** the responsible human accepted the
  additive section [Revision 2: the console
  path](#revision-2-2026-11-01-the-console-path), work package M7-5's
  Part 1 revision under the accepted [M7 plan](mvp-m7-plan.md) (D-7),
  at exact commit `afd395b8a80b6baa1f5f0946cd0bff91ad806cc9` (parent
  `641389eb`, on branch `beryllium/mvp-m7`) by the instruction `accept
  afd395b8` (2026-11-01, 14:57 in the human's time zone; the
  abbreviation resolves uniquely). The accepted text of Parts 1 to 7 and
  Revision 1 is byte-identical across the two commits; the revision's
  own status line and addendum carry the decision, and
  [`security-model-v1-revision-2-review-summary.md`](security-model-v1-revision-2-review-summary.md)
  is its review and acceptance record. The acceptance lets M7-5's claim
  and ledger rows cite I17 and I18; it authorizes no code, no model
  change, and no claim change of its own.
- **Revision 3 (2026-11-03):** the responsible human accepted the
  additive section [Revision 3: the measurement
  log](#revision-3-2026-11-03-the-measurement-log), work package M9-2's
  Part 1 revision under the accepted [M9 plan](mvp-m9-plan.md) (D-8), at
  exact commit `4bc079dbb96540cb44008a53df857701696e9bad` (parent
  `bc80b620`, the M9 plan's acceptance record, on branch
  `beryllium/mvp-m9`) by the instruction `accept 4bc079db` (2026-11-03,
  00:46 in the human's time zone; the abbreviation resolves uniquely).
  The accepted text of Parts 1 to 7 and Revisions 1 and 2 is
  byte-identical across the two commits; the revision's own status line
  and addendum carry the decision, and
  [`security-model-v1-revision-3-review-summary.md`](security-model-v1-revision-3-review-summary.md)
  is its review and acceptance record. The acceptance lets M9-5's claim
  and ledger rows cite I19 and I20; the claim's sentences take effect
  through the M9 result's acceptance.

## Status

Proposed for responsible-human review; not accepted. This is the S2
deliverable, written under the accepted [S2 plan](s2-security-model-plan.md)
(exact commit `5ce7827f`, accepted 2026-10-19, instruction `accept 5ce782`)
as its work packages S2-1 to S2-7, with Q1 answered A (the policy notation
is defined in full in this document, with no parser or tool) and Q2 to Q7 at
their defaults. It fills the seven-part definition of S2 accepted as RP-3
(`1ac7080f`) and applies Model 0.1 plan revision M01-A (`95ef0f6c`) and the
revised S1 synthesis (`fd670dcd`).

This document is a specification and a set of definitions. It implements
nothing, runs nothing, proves nothing, selects no runtime mechanism, no
protected service, and no specification tool, and changes nothing under
`model/` or in any accepted R0-R7 or B0-B7 target. Accepting it would make
security model v1 the accepted statement of what Beryllium's security
properties are, as planning input to S3 and the first MVP milestone; it
would authorize no implementation and not S3.

Line references are to the development branch at `0eb37570`.

## How to read this document

Part 1 says what exists and what is trusted. Part 2 defines the policy
notation and writes two policies in it. Part 3 defines the analyses that
decide whether a policy and a manifest say what is intended. Part 4 relates
the policy to the canonical manifest and restores the offline pipeline as a
goal. Part 5 evaluates the two triggers that Model 0.1 keeps for runtime
mechanisms. Part 6 defines the authority ceiling for the case in which an
untrusted management domain creates domains at run time. Part 7 lists what
in Model 0.2 would change. The closing sections give the claim boundary,
the open questions, and the status record.

Throughout, **policy** means the declarative specification of Part 2;
**manifest** means the canonical sealed state of Model 0.2 (the proposal
after validation and sealing); **mappings** means the derived G-stage
leaves; and **enforcement** means what the installed mappings and the
monitor's checked transitions deny or allow at run time. The order of
authority is policy, then manifest, then mappings: each later layer is
derived from, and no more permissive than, the one before it.

## Part 1: objects, invariants, threat model, and trusted computing base

### Object classes

The model governs the following classes. Each row names the class, what
instances exist in the two configurations this document uses as instances
(the fixed two-domain profile of R0-R7 and B0-B4, and the expected first
MVP milestone of two Linux guests), and where its authority is recorded.

| Class | Instances today | Authority recorded in |
| --- | --- | --- |
| `domain` | the management and protected domains of the fixed profile; guests G0 and G1 of B7 | the manifest's domain and binding records |
| `memory` | private regions (one per domain), the shared region, monitor-owned regions (code, data, root pools, trusted stacks, saved state), and guest-code regions | the manifest's extent and ownership records; the derived mappings |
| `vcpu_state` | one saved architectural state per domain: GPRs, the VS CSRs the B7 record enumerates, and the saved frame | the saved-state binding; the monitor's save and restore sequence |
| `root` | one G-stage root per domain, each in a monitor-owned pool | the derived enforcement state; the `hgatp` value and its readback |
| `channel` | the one directional shared region of the fixed profile; none between Linux guests yet | the manifest's channel record (endpoints, direction, rights) |
| `notification` | none; named for the first protected-domain milestone | a later manifest record |
| `timer` | the HS Sstc slice and each guest's `vstimecmp` (B5-B7) | monitor-owned; not a manifest object today |
| `interrupt` | the HS supervisor timer interrupt (B7); no injected interrupt | monitor-owned; `hvip` injection is excluded by the B-series stops |
| `manifest` | the sealed canonical state and its configuration identity | itself; Model 0.2's sealing |
| `policy` | the specification of Part 2 | this document; later, a policy source artifact |
| `measurement` | none; named as an unimplemented asset | a later milestone |

Identifiers are not authority (S1 H03): a type, a domain index, a GPA, a
VMID, or a class name names something; only the manifest, the derived
mappings, and the monitor's checked transitions grant access.

### Invariants

The invariants are stated in prose. For each, the table names the Model 0.1
or Model 0.2 obligation that already covers its fixed-instance form, or
says that none does.

| # | Invariant | Fixed-instance obligation | Status beyond the fixed instance |
| --- | --- | --- | --- |
| I1 | Every private memory region has exactly one owning domain, and no other domain's root maps it | `unique_private_ownership`, `monitor_exclusion`, `mapping_soundness` | none for B6/B7, whose windows are link-time constants |
| I2 | Monitor-owned state (code, data, root pools, trusted stacks, saved state) is mapped by no domain root | `monitor_exclusion` | none for B5-B7 |
| I3 | All cross-domain storage is an explicit channel with fixed endpoints, a direction, and rights no greater than the policy allows | `directional_channel_confinement`, `derived_rights_bounded` | no channel exists between Linux guests |
| I4 | Every derived mapping right is a nonempty subset of the manifest's rights for that domain, GPA, and frame, and the manifest's rights are a subset of what the policy allows (Part 4) | `derived_rights_bounded`, `derived_root_soundness` | the policy half is new to this document |
| I5 | A domain transition updates only the source domain's saved state and reads only the target's; neither reads or writes the other's | `saved_state_separation` | B7 saves and restores per-guest state with readback; no proof (S1 H17) |
| I6 | No domain runs before validation, sealing, and root derivation complete; a failed or partial proposal publishes no authority | `sealing_requires_validation`, `root_derivation_requires_sealing`, `failed_validation_no_publication`, `terminal_fail_closed_behavior` | B5-B7 build and re-walk before install; no proof |
| I7 | After a root switch, the target does not execute until the required translation invalidation completes and the new root is read back | `switch_freshness`, `pre_fence_target_entry_denied`; R7's `Switch` bytes | B7 fences and reads back on every switch; VMID tagging on K3 is trusted, not tested |
| I8 | The sealed manifest is immutable after sealing, and no proposed, guest, report, or derived data can create or modify canonical authority | `canonical_state_immutable_after_sealing`, `accepted_proposal_has_no_direct_authority` | the seal is an API property; what protects it inside the TCB is stated in the TCB table |
| I9 | Every hypercall, exit, shared buffer, descriptor, and configuration artifact is an untrusted input, checked before use | none by name; B5's refused DBCN and SRST inputs; R6's catalogue | B5-B7 host tests; no proof |
| I10 | The policy is total: for every (source type, target type, class, permission) it answers allow or deny, with deny the default | new; Part 2 | no obligation |
| I11 | The manifest conforms to the policy: every right the manifest grants is allowed by the policy, and every flow the manifest creates is a declared channel | new; Parts 3 and 4 | no obligation; the analyses of Part 3 define the check |
| I12 | In the dynamic case, every grant management creates is a subset of authority the policy delegates to management, and anything outside fails closed | new; Part 6 | no mechanism exists |

I1 to I9 are the mechanism invariants Models 0.1 and 0.2 and the R-series
already state, restated against the object classes above; I10 to I12 are
the specification invariants this document adds. None of I1 to I12 is
proved for B5-B7 or for any Linux guest; the B-series records are
diagnostic bring-up evidence for one board.

### Threat model v0, restated for K3

The implementation plan's threat model v0 (L481-L532) stands. Restated for
the configurations that exist:

- **Attackers.** Every non-Beryllium domain, from its first instruction:
  today the two synthetic domains of the fixed profile and the Linux test
  payloads of B6 and B7; later the management domain, every protected
  research domain, and every I/O, policy, or service domain. All may be
  mutually hostile. Malformed boot artifacts and management requests are
  attackers' inputs.
- **Linux's role today.** The B6 and B7 guests are untrusted test payloads
  with no devices and no management authority; they are not the
  management domain of threat model v0, which does not yet exist. The
  model treats them as hostile domains with private memory and saved
  state and nothing else.
- **Assets.** Each domain's private memory and saved vCPU state; the
  monitor's code, data, root pools, trusted stacks, and saved-state areas;
  the manifest and its configuration identity; the policy; and, when they
  exist, channels' direction and rights, measurements, and attestation
  evidence.
- **Allowed effects.** A domain may crash itself. Management may pause,
  starve, or terminate protected work. Architectural timing differences
  and documented microarchitectural leakage remain possible. An
  intentionally shared page is an intended channel, and side channels
  through it are in scope for the policy's flow analysis only as declared
  flows.
- **Required containment.** No domain reads or writes another's private
  state or the monitor's; no flow exists between domains except declared
  channels in their declared direction; no domain gains authority by
  performing management or I/O work; shared writable memory exists only
  through explicit, revocable grants; compromise of one domain does not
  compromise Beryllium or another domain's confidentiality or integrity.
- **Deferred, unchanged.** Host-independent availability; comprehensive
  microarchitectural noninterference; physical attacks; compromised vendor
  roots; a firmware-hostile launch.

### Trusted computing base

| Trusted element | Evidence class today | Note |
| --- | --- | --- |
| The Beryllium HS code of the configuration in use: the accepted R1-R5 mechanism as ported, and the B5-B7 monitor layers | R1-R5: host tests, semantic image checks, QEMU, R6's catalogue, R7's bounded proof of eleven wrapper symbols; B5-B7: host tests, image checker, QEMU, board runs; no proof | R7's fifteen cut points are unproved; "The B7 monitor layer has no proof" |
| Boot and exception-entry assembly, including B1's handoff quiesce and B3's shim | R7 for the R5 wrappers; otherwise review and test | |
| The sealed manifest's protection inside HS | none: the seal is an API property, and any HS C code can write the sealed state (S1 H05) | the model states this as an open obligation on the first protected-domain milestone |
| OpenSBI 1.6 (SBI 2.0) on the COM260: trap delegation, `menvcfg.STCE`, SRST behavior, the 24 MHz timebase | board observation (B0-B7) | SRST halts without power-off; `hedeleg` is WARL (cause 0 reads zero) |
| The RISC-V H-extension, Sv39x4, Sstc, and VMID tagging as implemented on K3 | board observation; VMID tagging trusted, not tested (B7) | `htval` and `htinst` values never recorded |
| The hardware and processor microcode | assumed | |
| The toolchains that produce the images: pinned for R3-R7, unpinned for the B-series | locks (R3-R7); workstation versions recorded (B-series) | no source-to-binary correspondence exists |
| The loader path: Fedora `kexec_load` or U-Boot `booti`, RAM-only | procedure | not part of the running TCB after entry |
| The initial measured configuration and policy | none: no measurement exists | named as an asset; unimplemented |

The TCB does not include the Linux guests, the guest kernels, or any
userland; the monitor does not trust them, and the model claims nothing
about them beyond the lines the records show they printed.

## Part 2: the policy specification

### Notation

The policy is written in a small declarative notation in the Type
Enforcement family. Its abstract syntax and semantics are defined here in
full; there is no parser, tool, or file format, and the concrete syntax
below is for reading. Where the concrete syntax matches SELinux's TE
statements, that is deliberate reuse of a familiar form, not a dependency.

**Abstract syntax.** A policy is a tuple `(T, C, P, R)`:

- `T` is a finite set of **types**. A type is a policy identity assigned to
  a subject or an object; it carries no authority by itself.
- `C` is a finite set of **object classes**. Each class `c` has a finite
  set of **permissions** `P(c)`.
- `P` is the family of permission sets, one per class.
- `R` is a finite set of **rules**, each a tuple
  `allow(s, t, c, Q)` with `s` a source type, `t` a target type, `c` a
  class, and `Q` a nonempty subset of `P(c)`.

**Concrete syntax.** One statement per line:

```text
type <name>;
class <name> { <permission> ... }
allow <source_type> <target_type> : <class> { <permission> ... };
```

A policy declares all its types and classes before its rules. A type or
class used before declaration, an unknown permission, or an empty
permission set makes the policy ill-formed, and an ill-formed policy is
rejected before any semantics is assigned.

**Semantics.** The policy denotes a total function

```text
decide : T x T x C x P(c) -> { allow, deny }
decide(s, t, c, p) = allow   if some allow(s, t, c, Q) in R has p in Q
decide(s, t, c, p) = deny    otherwise
```

Properties that follow from the definition:

- **Total and deterministic.** `decide` is defined for every argument and
  depends only on `R`.
- **Default deny.** Anything no rule allows is denied.
- **Conflict resolution.** There is only one rule form, and the effect of
  several rules is their union, so no two rules conflict. If a later
  revision adds any rule form with a different effect (a deny, an audit
  rule, a transition), it must define the resolution order in this
  section before use; until then, union is the whole resolution rule.
- **Monotone in `R`.** Adding a rule never denies anything that was
  allowed; removing a rule never allows anything that was denied.
- **Permission aggregation (Helium POL-FIN-003).** A request for several
  permissions on one object is allowed only if each permission is allowed;
  rules may be matched separately for each permission. Beryllium's answer
  is therefore "unioned across rules, conjunctive across permissions".

**Labeling.** A **labeling** `L` assigns one type to every subject (each
domain) and one type to every object (each memory region, channel, and
other governed object) of a configuration. The pair `(policy, L)` is what
the manifest is checked against in Part 4. Labeling is part of the
specification, not of the mechanism: the monitor never consults types at
run time under this document; it consults the manifest and the mappings
derived from it.

**Object classes for v1.** The classes and permissions this version uses:

```text
class memory   { read write execute map }
class channel  { send receive }
class domain   { enter switch_to terminate pause }
class manifest { read }
```

`map` on `memory` is the right to have the region appear in the subject's
root at all; `read`, `write`, and `execute` are the leaf rights derived for
it. `channel` permissions name the direction: the writer holds `send`, the
reader `receive`. The `domain` class governs the monitor's transitions on
behalf of one domain toward another and is used by Part 6; in the static
instances only the monitor itself performs transitions, so no domain holds
a `domain` permission there. `manifest : read` is reserved for a future
authority report consumer and is granted to no domain in v1.

### Instance 1: the fixed two-domain profile

This is the configuration R0 froze, R1-R7 and B0-B4 run, and Model 0.1 and
0.2 model: a management domain and a protected domain, each with one
private page and one guest-code page, one directional shared page (the
management domain writes, the protected domain reads), and monitor-owned
code, data, root pools, trusted stacks, and saved-state areas.

```text
type monitor_t;        type mgmt_t;          type prot_t;
type mgmt_private_t;   type prot_private_t;
type mgmt_code_t;      type prot_code_t;
type shared_mp_t;      type monitor_mem_t;

class memory  { read write execute map }
class channel { send receive }

allow mgmt_t mgmt_private_t : memory { read write map };
allow mgmt_t mgmt_code_t    : memory { read execute map };
allow mgmt_t shared_mp_t    : memory { read write map };
allow mgmt_t shared_mp_t    : channel { send };

allow prot_t prot_private_t : memory { read write map };
allow prot_t prot_code_t    : memory { read execute map };
allow prot_t shared_mp_t    : memory { read map };
allow prot_t shared_mp_t    : channel { receive };
```

Labeling: the management domain is `mgmt_t`; the protected domain is
`prot_t`; R0 resources 9 and 12 are `mgmt_private_t` and `mgmt_code_t`;
resources 10 and 13 are `prot_private_t` and `prot_code_t`; resource 11 is
`shared_mp_t`; resources 1-8 are `monitor_mem_t`; the monitor is
`monitor_t`. No rule names `monitor_t` as a source or `monitor_mem_t` as a
target, so every domain access to monitor memory is denied by default, and
the monitor's own access is outside the policy's subject set, as the
mechanism invariants require.

What the policy says that the manifest, mappings, and records then show:
`prot_t` has no rule for `mgmt_private_t`, so B2's denied load (cause 21)
is the policy's deny; `prot_t` has `read` but not `write` on `shared_mp_t`,
so B2's denied store (cause 23) is the policy's deny; and the flow relation
of Part 3 contains exactly one pair, `mgmt_t -> prot_t`, through
`shared_mp_t`, which is the declared channel. The two denials B2 recorded
are therefore instances of this specification; they were not, and could
not be, evidence about whether a specification is needed (M01-A).

### Instance 2: the expected first MVP milestone

Two Linux guests, a writer and a reader, each in its own 64 MiB window, as
in B7, plus one shared page that the writer may read and write and the
reader may only read, with private memory denied and the monitor injecting
the faults and logging each denial (implementation plan L1996-L2001). B7
has no shared page, so this instance is a specification of what the
milestone must build, not of what exists.

```text
type monitor_t;      type writer_t;       type reader_t;
type writer_mem_t;   type reader_mem_t;   type shared_wr_t;
type monitor_mem_t;

class memory  { read write execute map }
class channel { send receive }

allow writer_t writer_mem_t : memory { read write execute map };
allow writer_t shared_wr_t  : memory { read write map };
allow writer_t shared_wr_t  : channel { send };

allow reader_t reader_mem_t : memory { read write execute map };
allow reader_t shared_wr_t  : memory { read map };
allow reader_t shared_wr_t  : channel { receive };
```

Labeling: G0 is `writer_t` and G1 is `reader_t`; each guest's 64 MiB
window is `writer_mem_t` or `reader_mem_t`; the shared page is
`shared_wr_t`; the monitor's image, pool, staging region, and kexec FDT
slot are `monitor_mem_t`. The guests' windows are `read write execute`
because an unmodified Linux kernel runs in them; B6's "All RAM is RWX"
(B6 plan L448) is this rule, now stated as policy rather than as a
link-time constant. The flow relation is `writer_t -> reader_t` through
`shared_wr_t` and nothing else; the reader's attempted write to the shared
page and either guest's access outside its window are the milestone's
logged denials.

Two differences from B7 follow from the policy and are S3's to build: B7's
pair check "refuses shared pages", so the root derivation must admit the
one declared channel; and B7 treats every unexpected exit as terminal,
while the milestone logs guest faults and resumes (S1 H15, H55).

### What the notation does not express in v1

- Rules about the monitor's own behavior. The monitor is not a subject of
  the policy; its obligations are the mechanism invariants I1 to I9.
- Dynamic operations: creating domains, relabeling, revoking a grant. Part
  6 states what the policy must bound in that case and which vocabulary is
  missing.
- Information-flow labels in the MLS sense, declassification, roles, or
  attributes. If a later version needs them, it adds classes or rule forms
  under the conflict-resolution rule above.
- Device, DMA, IOMMU, or interrupt-injection objects. None exists in any
  configuration; the classes are added when the first does.

## Part 3: the analyses

Each analysis is a decidable check over a finite policy `(T, C, P, R)`, a
finite labeling `L`, and, where stated, a finite manifest `M`. Each is
defined by what it computes and what a failure means. None is implemented
by this document (Q4); the final table says which of them Model 0.2's
validator already performs in extensional form on the fixed instance.

**A1. Well-formedness.** Every type and class in `R` is declared; every
permission in a rule belongs to its class; every rule's permission set is
nonempty; `L` assigns exactly one type to every subject and object of the
configuration, and every assigned type is in `T`. Failure: the policy or
labeling is rejected; nothing downstream is evaluated.

**A2. Unreachable authority.** A rule `allow(s, t, c, Q)` is unreachable
under `L` if no subject is labeled `s` or no object of class `c` is labeled
`t`. Failure means dead policy: a rule that grants nothing in this
configuration, which is a specification error to fix or a deliberate
template rule to annotate; it is not a security failure by itself.

**A3. Contradictory authority.** With only `allow` rules there is no
rule-level contradiction (Part 2). The analysis therefore checks the policy
against the invariants: any rule granting a domain type any permission on
`monitor_mem_t` (I2); any rule granting a domain type `map` on another
domain's private type (I1); and any `channel` rule without a matching
`memory` rule on the same target for the same source (a channel with no
storage, or storage with no declared channel). Failure is a specification
error that would make the manifest violate an invariant if it were obeyed.

**A4. Over-broad authority.** Given a declared **need set** `N(s, t, c)`
per (source type, target type, class), the set of permissions the use case
requires, the analysis reports every rule whose `Q` is not a subset of
`N(s, t, c)`, and every (s, t, c) with a rule but no need entry. Failure
means the policy grants more than the use case needs. The need sets for
the two instances are the permission sets written in Part 2, so both pass
by construction; the analysis has force when a policy is edited.

**A5. Non-revocable authority.** For every rule granting `write` on
`memory` to a target type that some other subject type may `read` (that
is, shared writable storage), the analysis requires a revocation path: a
manifest or management operation that can remove the grant. In the static
instances there is no revocation operation and no shared writable storage
with two writers, so the check reports the shared page of each instance as
"static, not revocable, single writer", which threat model v0 permits for
a static configuration and Part 6 forbids for the dynamic case. Failure in
the dynamic case means shared writable memory exists without an explicit
revocable grant.

**A6. Information flow modulo the declared channels.** Define the **flow
relation** `F` on subject types: `s1 F s2` if there is an object type `t`
and class `memory` with `write` in some `allow(s1, t, memory, Q1)` and
`read` in some `allow(s2, t, memory, Q2)`, `s1 != s2`. Define the
**declared channel relation** `D`: `s1 D s2` if some rule grants `s1`
`channel : send` and some rule grants `s2` `channel : receive` on the same
target type. The analysis computes `F` and its transitive closure `F+` and
requires `F+ = D+`: every flow, direct or transitive, is a declared
channel, and every declared channel is realized by storage. Failure means
either an undeclared flow (a specification error, or a covert path through
a shared object) or a declared channel with no storage. For both
instances, `F = D = {(writer, reader)}` with the instance's names, and
`F+ = F`.

**A7. Authority non-amplification.** For the dynamic case (Part 6): given
the policy, a delegating subject type `m` (management), and a proposed
grant `allow(s, t, c, Q)` that `m` requests, the analysis requires
`Q` to be a subset of the permissions the policy allows `m` to delegate on
`(t, c)`, and the resulting policy to pass A3 and A6. In the static
instances there is no delegation, so A7 is vacuous. Failure means a
management request would create authority the policy does not delegate,
which Part 6 requires to fail closed.

**A8. Manifest conformance.** Given `M`, the sealed manifest of Model 0.2:
for every extent ownership, binding, channel, and right in `M`, there is a
rule under `L` allowing it (`map` for presence in a root; `read`, `write`,
`execute` for the leaf rights; `send` or `receive` for a channel
endpoint); and for every rule, the manifest grants no more than the rule
allows. Failure means the manifest does not conform to the policy, which
I11 forbids. A8 is the validate direction of Part 4.

| Analysis | Model 0.2 validator today (fixed instance, extensional) | Status |
| --- | --- | --- |
| A1 | structural validation of the proposal | partly: the proposal's structure, not a policy's |
| A2 | none | defined only |
| A3 | `monitor_exclusion`, `unique_private_ownership`, `directional_channel_confinement` check the manifest, not a policy | the manifest half exists; the policy half is defined only |
| A4 | none | defined only |
| A5 | none (no revocation exists) | defined only |
| A6 | `directional_channel_confinement` for one channel | the fixed instance's `F` is checked extensionally; the general analysis is defined only |
| A7 | none (no delegation exists) | defined only |
| A8 | `derived_rights_bounded`, `mapping_soundness` relate mappings to the manifest; nothing relates the manifest to a policy | the manifest-to-mappings half exists; the policy-to-manifest half is defined only |

## Part 4: the policy, the manifest, and the pipeline

### Compile or validate

S2 decides **validate**: the canonical manifest is written as Model 0.2
already defines it (a proposal, copied, validated, sealed) and is checked
against the policy and labeling by A8, with A1 to A6 run on the policy
first. The alternative, **compile**, generates the manifest from the
policy, the labeling, and the platform description.

Reasons: validate keeps Model 0.2's seam and its 23 obligations unchanged,
so the accepted mechanism is not reopened (Part 7); it keeps the manifest
reviewable on its own, as the B-series records review each milestone's
configuration; and it keeps the policy-to-manifest relation a check that
can be implemented independently twice (an offline tool and a Rocq
decision procedure) and compared, which is the implementation plan's
differential method (L945). The cost is that two artifacts, policy and
manifest, must be kept consistent by a check rather than by construction;
A8 is that check, and it must run before sealing in any implementation.

Compile stays available as a later step: once A8 is implemented, a
generator that emits a manifest satisfying A8 by construction is an
optimization of the authoring path, not a change to the model. The
decision is recorded here so that S3 can plan either.

### The pipeline, restored as a goal

The implementation plan's offline pipeline (L401) is restored as a goal
with the policy at its head:

```text
policy source (Part 2 notation) + labeling + platform description
  -> analyses A1-A7 on the policy
  -> proposal (as Model 0.2 defines it)
  -> canonical validation (Model 0.2) + A8 against the policy
  -> sealed manifest with its configuration identity
  -> derived roots and mappings (Model 0.2; R2 on the fixed profile)
  -> Rocq configuration + authority report + audit record
```

The Rocq configuration is the intended consumer of the sealed manifest and
the policy: the accepted obligations of Models 0.1 and 0.2 are stated over
the manifest, and this document adds I10 to I12 to be stated over the
policy and its relation to the manifest. The authority report and the audit
record are the offline, human- and tool-readable outputs. Nothing in this
pipeline runs in HS: the monitor consumes the sealed manifest and derives
enforcement, as Model 0.2 requires; it never parses the policy source or
evaluates `decide` at run time under this document.

Measurement and attestation binding (policy source identity, compiled
artifact, active generation) are named as the pipeline's last stage and
are unimplemented; no configuration identity today is a measurement.

### The authority report schema

The authority report is derived from the sealed manifest and the derived
roots, is never parsed by the monitor, and grants no authority (S1 H29,
adapted). Its schema, in the same abstract-syntax style as the policy:

```text
report := { identity, policy, labeling, subjects, objects, grants, flows, checks }
identity := { manifest_identity, policy_identity, labeling_identity }
subjects := list of { name, type, domain_index }
objects  := list of { name, type, class, extent }           # extent as in R0: base, size
grants   := list of { subject, object, class, permissions, source }
            # source: the rule that allows it, or "none" (an A8 failure)
flows    := list of { from_subject, to_subject, via_object, declared }  # declared: yes/no
checks   := list of { analysis, result, detail }            # A1-A8
```

A report with any grant whose `source` is `none`, any flow whose
`declared` is `no`, or any check whose `result` is not `pass` describes a
configuration that must not be sealed. The schema is a definition; no
generator exists, and the encoding (text, JSON, or other) is S3's choice.
Where practical the encoding should allow the report to be consumed by
offline audit tools in the `cheriot-audit` pattern the implementation plan
names (L416); that is a compatibility goal, not a tool selection.

## Part 5: the triggers

Under M01-A, two triggers gate runtime mechanisms; the specification of
Part 2 is not trigger-gated and is needed in every case. Each trigger is
evaluated against three use cases (Q3): U1, the fixed two-domain profile;
U2, the expected first MVP milestone; U3, the dynamic management case, in
which an untrusted management domain creates protected domains and
channels at run time. A result of "fires" selects nothing; it records that
a later plan must design the mechanism.

### The capability trigger

Add software capabilities only if a use case requires runtime designation
plus delegation, attenuation, holder transfer, or revocation that static
owner/channel records cannot express without ambient authority or
per-caller special cases (Model 0.1, unchanged by M01-A).

| Use case | Result | Evidence |
| --- | --- | --- |
| U1 | does not fire | Every grant is static and in the manifest; nothing is designated, delegated, or revoked at run time. B0-B4 ran it with none. |
| U2 | does not fire | The shared page and both windows are static manifest entries; the milestone injects faults and logs denials but creates, delegates, and revokes nothing. |
| U3 | undecidable without a later input | Management must designate a new domain's resources and may need to revoke a channel. Whether that needs capabilities, or is expressible as policy-bounded manifest operations with revocation as a manifest transition (Part 6), depends on the management-request vocabulary that Part 6 says a later plan designs. The policy's `domain` class and A7 are written so that either answer can be stated against them. |

### The runtime-check trigger

Add a runtime TE check only if a use case contains an ownership-valid or
capability-valid operation that must still be denied at run time by a rule
the derived mappings do not express, with at least one independently
observable case where designation and discretionary rights allow but TE
denies, and TE allows but no valid designation exists so access still
denies (M01-A).

| Use case | Result | Evidence |
| --- | --- | --- |
| U1 | does not fire | Both denials are mappings derived from the policy (Part 2, Instance 1); there is no operation the mappings allow that the policy denies. B2's result is consistent with this and is not a test of the trigger (M01-A). |
| U2 | does not fire | The same: the reader's write and the out-of-window accesses are absent mappings; fault injection and logging are monitor behavior on an already-denied access, not a policy decision on an allowed one. |
| U3 | undecidable without a later input | Whether a management request is a mapping-time check (the request is validated against the policy before any mapping changes, which is A7 at run time and needs no per-access decision) or a per-access decision depends on the same vocabulary as above. Under the specification's order of authority, the first form is preferred and keeps enforcement derived; the second is what the trigger would select. |

### Consequence

Neither trigger fires for the configurations that exist or for the first
MVP milestone. Both are undecidable for the dynamic case until the
management-request vocabulary exists; Part 6 names what that vocabulary
must contain, and S3 or a later plan designs it. The specification itself
is unaffected by either answer: it is what the manifest is checked against
in every case.

## Part 6: the dynamic authority ceiling

The implementation plan's policy invariant (L890-L901) states the ceiling.
Restated against this model:

1. The policy and the initial sealed manifest define an immutable authority
   ceiling: the set of all (subject type, object type, class, permission)
   the policy allows, under the labeling, is the most any configuration
   reachable at run time may grant.
2. Management is a subject type, `mgmt_t`, with `domain` permissions
   (`enter`, `switch_to`, `terminate`, `pause`) on the domain types it may
   manage and, in a delegated-administration profile, a delegation
   envelope: for each (object type, class), the permissions it may grant to
   domains it creates. The envelope is a subset of the policy; a strict
   profile has an empty envelope and may only narrow or revoke.
3. Every dynamic grant management requests is checked by A7 before any
   mapping changes: it must be within the envelope and leave A3 and A6
   passing. A request that fails is denied and logged, and no partial
   authority is published (I6, I12).
4. Management cannot create root authority, relabel or reassign
   monitor-owned objects, alter the policy or the manifest's configuration
   identity, or bypass the checked transition path.
5. Revocation is a manifest transition that removes a grant and triggers the
   translation invalidation of I7; A5 requires every shared writable grant
   created at run time to have one.
6. Policy-domain failure, a malformed request, a stale generation, or an
   unverifiable ancestry fails closed.

What the policy of Part 2 expresses directly: items 1, 4, and the `domain`
class of item 2. What needs a vocabulary this document does not define: the
form of a management request (create domain, assign region, create
channel, revoke), the delegation envelope's representation, generations
and their freshness, and the audit record of each request. Those belong to
S3 and to the first protected-domain milestone, together with the trigger
answers for U3. The labeling of a newly created domain is management's
request and the policy's constraint: management may propose a type for the
new domain only from the types its envelope permits.

## Part 7: Model 0.2 change inventory

Model 0.2's seam, state, fixtures, and proofs are listed with what this
document would change. Nothing here is made (Q4); each row is an input to a
later plan.

| Element | Change | Where it would land |
| --- | --- | --- |
| Core phases (`empty -> inventory bound -> proposal copied -> canonical validation complete -> sealed -> roots derived -> active`) | None to the phases. A8 (and A1 to A6 on the policy) run before `sealed` as part of canonical validation, so that sealing implies policy conformance | abstract model and C validator, as a new validation step |
| Proposed state | None | |
| Canonical sealed state | Add the policy identity and labeling identity to the configuration identity, so that one sealed state binds one policy | abstract model, C state, fixtures |
| Derived enforcement state | None; mappings stay derived from the manifest | |
| Mechanism invariants 1-13 | None changed. Add I10 (policy totality), I11 (manifest conformance), I12 (dynamic ceiling) as specification invariants | abstract model |
| The 23 Rocq obligations | None changed. Add obligations for I10 (totality of `decide` is by construction; the theorem is that the notation's semantics is a function), I11 (A8 soundness: a manifest that passes A8 grants no right the policy denies), and the invariance of A6's flow relation under the derived mappings (`derived_rights_bounded` composed with A8) | `model/proof/`, new module |
| Fixtures (minimal-ownership and fixed-TE topologies) | Add the two labeled policies of Part 2 as fixture inputs; the fixed-TE fixture's topology is Instance 1 | `model/` fixtures |
| Executable model and host checker | Add A1 to A6 and A8 as checks over policy and manifest inputs; A7 only when a request vocabulary exists | `model/src/` |
| Non-goals | Remove "define identities, roles, labels, classifications" to the extent of the types and classes of Part 2; keep every other non-goal, in particular no dynamic delegation, revocation, relabeling, or policy update until a later plan | planning text |
| Fail-closed behavior | None; an A8 failure is a validation failure and ends in `terminal failure` | |

The inventory is not empty, but every change is additive and leaves the
accepted obligations and their statements as they are; no accepted target
is reopened. A plan for these changes would be the first implementation
consequence of this document and needs its own authorization.

## Claim boundary and non-claims

Security model v1 supports saying: Beryllium's security properties are
specified by a declarative, total, default-deny policy in the Type
Enforcement family with a defined notation, defined analyses, a defined
relation to the canonical manifest, and a defined authority ceiling for
the dynamic case; the fixed two-domain profile and the expected first MVP
milestone are written as instances of it; and neither runtime trigger
fires for them.

It does not:

- implement, run, prove, or test anything; the analyses are definitions,
  and no instance has been machine-checked;
- transfer any Helium, Model, R-series, or B-series result, or claim that
  any existing obligation establishes I10 to I12;
- select a runtime mechanism, a protected service, an SBI or firmware
  boundary, a specification tool, or an encoding;
- change any accepted target or anything under `model/`;
- claim hardware validation, formal verification, or that B5-B7 or any
  Linux guest satisfies I1 to I12; or
- authorize S3, the first MVP milestone, or any implementation.

## Open questions and defaults

The plan's Q1 to Q7 were decided by its acceptance (Q1 as A; Q2 to Q7 at
their defaults), and this document follows them. Questions this document
raises for the responsible human, with the defaults it applies:

| ID | Question | Default applied | Alternative |
| --- | --- | --- | --- |
| V1 | Compile or validate (Part 4)? | Validate, with compile as a later optimization | Compile from the start |
| V2 | Is the `domain` class part of v1? | Yes, defined and granted to no static subject, so Part 6 can refer to it | Omit it until the dynamic plan |
| V3 | Is the single static shared page acceptable as "static, not revocable, single writer" under A5? | Yes for U1 and U2; forbidden for U3 | Require a revocation path even for static instances |
| V4 | Does the first MVP milestone's guest memory stay `read write execute`? | Yes, because an unmodified Linux kernel runs in it | Split kernel text from data, which needs a guest-visible layout the milestone does not have |

## Status record

```text
security_model_v1_status=accepted
security_model_v1_target=0e3eec8b4fd74003f8cedbf2ca66871c31412624
security_model_v1_acceptance_instruction=accept-0e3eec8b
security_model_v1_acceptance_date=2026-10-22
security_model_v1_open_questions=V1-V4-defaults
security_model_v1_plan=5ce7827f9c2ffc6e0f88568692ab238e5feca49f
security_model_v1_definition=1ac7080f3375dfbfb8358706db767a8a89678a78
security_model_v1_inputs_m01a=95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab
security_model_v1_inputs_s1=fd670dcd54ff4f2c66349d377be914698b9dda3b
security_model_v1_base=0eb37570f9cb901ef994cc10aef8c7890c6134e9
security_model_v1_notation=te-family-allow-rules-defined-in-document
security_model_v1_classes=memory,channel,domain,manifest
security_model_v1_instances=fixed-two-domain,first-mvp-two-linux-guests
security_model_v1_analyses=A1-A8-defined-not-implemented
security_model_v1_manifest_relation=validate
security_model_v1_capability_trigger=U1-no,U2-no,U3-undecidable
security_model_v1_runtime_check_trigger=U1-no,U2-no,U3-undecidable
security_model_v1_model_0_2_changes=inventoried-not-made
security_model_v1_code_change=none
security_model_v1_model_change=none
s3_authorization=none
```

## Revision 1 (2026-10-28): the hart binding and the third instance

**Status: accepted on 2026-10-28 at exact commit `019cca64`
(instruction `accept 019cca64`; the first candidate `32298add`
superseded); see the document's [decision record](#decision-record).
As presented: proposed as an additive revision; not accepted.** This
section is work package M3-1 of the accepted [M3 plan](mvp-m3-plan.md)
(exact commit `c2c249f4`, accepted 2026-10-28), which the accepted
[MVP plan](mvp-plan.md)'s M3 requires as "an additive revision of
security model v1, as its own exact commit for acceptance before any
model work". It is appended to the accepted text, which it quotes and
does not edit: every change below is stated as an addition to a named
part, and the accepted parts, analyses, instances, claims, and status
record above keep their text. It changes no accepted analysis, instance,
or claim; it is the one planned change that the MVP plan's stop
condition 1 admits. It implements, runs, proves, and tests nothing; the
proofs it names are M3-3's, after this revision's acceptance.

Facts below come from the accepted documents, the MVP line at the M2
result `18d552bc` (the `anchor` scenario's `policy.te` at `f149eea0`,
SHA-256 `bfecfa92…`, and `scenario.json`; `src/mvp-layout.h`;
`src/mvp-hart.h`), the accepted Model 0.2 sources at `f8f89758`, and the
M0 to M2 plans; *fact* marks what a record or source shows.

### R1.1 Part 1, object classes: the `hart` class and the binding

Part 1's table gains one row and one row's instances column grows; the
other rows are unchanged:

| Class | Instances today | Authority recorded in |
| --- | --- | --- |
| `hart` (new) | the MVP's control hart 0 and domain harts 1 and 2 (M0 to M2; harts 3 to 7 are never started). The fixed profile of R0-R7 and B0-B4 runs both its domains on one hart by checked switches and is outside I13 to I16's scope (R1.2) | monitor-owned; the manifest's binding records (the scenario's `domains[].hart`, M0 plan "Hart identifiers"), the hart region (`0x102044000`, `0x20000` bytes) with one 64 KiB block per domain hart (`0x102044000` for G0's, `0x102054000` for G1's; `mvp-layout.h`), and the start rule (hart 0 starts each domain hart through SBI HSM once, before the barrier) |
| `domain` (instances column, added) | … and, in the MVP, each domain's binding to its one hart: G0 to hart 1, G1 to hart 2 (scenario data, not architecture) | the manifest's domain and binding records (unchanged) |

Hart identifiers are configuration, not authority (M0 plan, "Hart
identifiers"; S1 H03): a hart number names a hart; only the binding
record, the start rule, and the monitor's checked transitions give a
domain a hart. The control hart is fixed at 0 because the accepted R3
boot check and B3 shim require it, not because hart 0 is special to the
architecture.

### R1.2 Part 1, invariants: I13 to I16

Part 1's invariant table gains four rows after I12. They are the
invariants the MVP plan's revision 1 relies on (MVP plan, M3 deliverable
1; "Method per claim", the per-hart-state row), and their **scope is
the MVP's static-binding configurations** (MVP 1.0 under static
ownership: one control hart, one hart per domain, no scheduler), the
`te-poc` and `anchor` scenarios among them. The fixed two-domain profile
of R0-R7, B0-B4, and Model 0.2 runs both domains on one hart by checked
switches (I5, I7) and is outside their scope: I13 does not hold for it
and is not asserted of it. Their fixed-instance status is therefore
"not applicable", no obligation exists, and M3-3 is to prove them over
the MVP's static binding in the abstract model, not for the
implementation. The objects they name are R1.1's and the MVP's hart
page (`mvp-platform.h`, `struct be_mvp_hart_page`: the state page, the
walked map and leaves hart 0 copies in, and the hart's two ring views):

| # | Invariant | Fixed-instance obligation | Status beyond the fixed instance |
| --- | --- | --- | --- |
| I13 | Each hart runs at most one domain | not applicable (one hart, two domains, by switches) | the MVP's binding is injective (G0 on hart 1, G1 on hart 2); no proof |
| I14 | Each domain runs on exactly one hart, and that hart is not the control hart | not applicable | the MVP's binding is total into the domain harts; no proof. I13 and I14 say nothing about harts that run no domain (harts 3 to 7); no coverage of the started harts is asserted |
| I15 | Per-hart monitor state is private to its hart, **after the barrier**: before the barrier the control hart alone writes every word of a domain hart's block, initializing it (the whole hart page zeroed, then the descriptor, the first-entry frame, the walked map and leaves, the state's configuration, and both ring views); after the barrier the domain hart's trusted stack (block offset `0x0`, `0x2000` bytes), its saved frame (`0x2000`, `0x1000`), and the words of its state page it alone writes and no other hart reads (`controls`, `state`, `entered`) are written by no other hart and read by no other hart, and the whole block is mapped by no domain root | not applicable (`monitor_exclusion` covers the fixed profile's monitor memory, not per-hart state) | the hart region is `monitor_mem_t` in the `te-poc` and `anchor` scenarios, so no root maps it; the writer and reader discipline is the sources' (`mvp-hart.h`, `struct be_mvp_state_page`; `mvp-runtime.c`'s publication; `mvp-hartmain.c`'s entry); no proof |
| I16 | Every monitor-owned word shared between harts has one writer: before the barrier only the control hart writes (I15's initialization, and the generation word last); after the barrier the shared words are of two kinds, **immutable published data**, written by the control hart before the barrier and only read after it (each block's descriptor with its generation, the first-entry frame, the walked map and leaves, the state's configuration, and hart 0's binding table), and **ring state**, in which every mutable cross-hart word is a ring word with one writer: a ring's records and head are written only by its writer hart and its tail only by its reader hart, and each is read by the other (the inbound ring: hart 0 writes records and head, the domain hart writes the tail; the outbound ring: the reverse). The control hart's own state, the management state among it, is read by no domain hart and is not shared | not applicable | the MVP's rings and state page as `mvp-hart.h` documents them ("After the barrier hart 0 writes only the inbound ring's head and the outbound ring's tail") and `mvp-ring.c` implements them (the writer reads the reader's tail to find room; the reader reads the writer's head); no proof |

The MVP plan's sentence "the control hart is the only writer of shared
monitor state" is made precise by I16 rather than taken literally: the
outbound rings are shared monitor state that the domain harts write, by
the MVP's design (M0 plan, the substrate; M0-C's drain order). I15 and
I16 concern the static binding and the writer of each word; they say
nothing about concurrent execution, memory ordering, the IPI protocol,
or the barrier's implementation, which the MVP plan names as unmodeled.

**I5 and I7 under the binding.** The accepted I5 ("A domain transition
updates only the source domain's saved state and reads only the
target's; neither reads or writes the other's") and I7 ("After a root
switch, the target does not execute until the required translation
invalidation completes and the new root is read back") are stated for
switches between domains on one hart, which the MVP does not make. Their
text is unchanged, and the MVP plan's departure row 4 is realized by two
consequences of the binding rather than by applying them literally: a
hart's first entry reads only its own domain's published entry frame
(copied into its saved page) and writes only its own saved state, and
M2's `pause` and `terminate` save the paused domain's exit into its own
hart's saved frame and never restore it (M2 plan Q4, Q15), so no
transition on one hart reads or writes another domain's saved state;
and each hart writes `hgatp` once, fences, and reads it back before its
domain runs (M0 plan), which is I7's requirement for the one switch each
hart makes.

### R1.3 Parts 2 and 3: the hart binding is outside A8

Part 2's notation gains no class and no rule form: running on a hart is
the monitor's static assignment of a resource, not an access a subject
exercises, so the policy stays about authority (M3 plan Q1).

**An interpretation of A8's wording, for acceptance with this
revision.** The accepted A8 names "every extent ownership, binding,
channel, and right in `M`" and gives, in its parenthesis, the permission
that allows each kind of element: `map` for presence in a root, `read`,
`write`, `execute` for leaf rights, `send` or `receive` for a channel
endpoint. It gives no permission for a *structural* binding, the
manifest's binding of a domain to its vCPU, root, VMID, trusted stack,
and saved state (Model 0.2, `struct be_domain_desc`), and no rule class
names those monitor-owned objects (Part 1: `vcpu_state` and `root` are
outside the rule classes), so under a reading in which A8 requires a
rule for a structural binding no instance could pass A8. This revision
therefore reads A8's "binding" as the domain's binding to its own
extents, which the ownership and presence rules allow, and states that
**structural bindings, the hart binding among them, are mechanism
metadata outside A8**, checked by the mechanism invariants (I1, I2, I5,
I7, and now I13 to I16). This is the reading the MVP's offline checker
implements (`mvp/tools/policy-check.py`, `a8`, whose grants are each
domain's window, pages, channel endpoints, and `domain` permissions),
and the reading M3's Rocq and C analyses will implement. It fixes an
ambiguity in A8's accepted wording rather than changing what any
accepted text asserts (no accepted text states an A8 verdict for an
instance); it is recorded here as an interpretation the responsible
human accepts or rejects with this revision, and A8's accepted text is
not edited. If rejected, the M3 plan needs a revision before M3-3.

### R1.4 Part 2: Instance 3, the anchor scenario

Part 2 gains a third instance after Instance 2. It is M2's `anchor`
scenario (M2 plan, "The policy, the labeling, and the manifest"), run
on the COM260 in the accepted M2 result (`18d552bc`): an untrusted
Linux domain (`host_t`, G0, hart 1) and a protected Linux domain
(`prot_t`, G1, hart 2), each in its own 64 MiB window; a request page
the host writes and the protected domain reads; a response page the
protected domain writes and the host reads; a secret page only the
protected domain's root maps, which the monitor fills with a 32-byte
test secret before any hart starts; and the first `domain` rule held by
a domain, giving `host_t` exactly `pause` and `terminate` on `prot_t`.
The policy, verbatim from `mvp/scenarios/anchor/policy.te` (its
comments omitted here; its identity is the SHA-256 of the whole file,
`bfecfa92…`):

```text
type monitor_t;    type host_t;        type prot_t;
type host_mem_t;   type prot_mem_t;
type req_t;        type resp_t;        type secret_t;
type monitor_mem_t;

class memory  { read write execute map }
class channel { send receive }
class domain  { enter switch_to terminate pause }

allow host_t host_mem_t : memory { read write execute map };
allow host_t req_t      : memory { read write map };
allow host_t req_t      : channel { send };
allow host_t resp_t     : memory { read map };
allow host_t resp_t     : channel { receive };
allow host_t prot_t     : domain { pause terminate };

allow prot_t prot_mem_t : memory { read write execute map };
allow prot_t req_t      : memory { read map };
allow prot_t req_t      : channel { receive };
allow prot_t resp_t     : memory { read write map };
allow prot_t resp_t     : channel { send };
allow prot_t secret_t   : memory { read map };
```

Labeling (`scenario.json`, `labeling`): G0 is `host_t` and G1 is
`prot_t`; G0's window (`0x110000000`, 64 MiB) is `host_mem_t` and G1's
(`0x114000000`) is `prot_mem_t`; the request page (`0x118000000`) is
`req_t`, the response page (`0x118001000`) `resp_t`, and the secret page
(`0x118002000`) `secret_t`, each one 4 KiB page, with the request and
response channels labeled `req_t` and `resp_t` on their pages; the
accepted image (`0x102000000`), the pool, the hart region, the MVP
region, the staging region, and the kexec FDT slot are `monitor_mem_t`;
the monitor is `monitor_t`. The need sets are the rules' permission sets
(`scenario.json`, `need`). The hart binding (R1.1): G0 on hart 1, G1 on
hart 2, the control hart 0; it is outside the policy (R1.3).

What the policy says that the manifest, the mappings, and the records
then show (facts from the M2 result's board record,
`mvp/results/20261028-com260-m2a/`): `prot_t` has `read` and `map` but
not `write` on `req_t`, so the protected domain's store to the request
page is denied (`DENY … kind=read-only gpa=0x84000ff8`); `host_t` has no
rule on `secret_t`, so the host's load from the secret page is denied
(`kind=unmapped gpa=0x84002000`), as are its load from the protected
domain's window (`gpa=0x114000000`) and from monitor memory
(`gpa=0x102064000`), and its store to the response page is denied
(`kind=read-only gpa=0x84001ff8`); `host_t` holds `pause` and
`terminate` on `prot_t`, so the host's `pause 1` and `terminate 1` are
delivered and the protected domain is paused and then terminated with
its measurement unaltered, while `prot_t` holds no `domain` permission,
so its `terminate 0` and `pause 0` are refused `SBI_ERR_DENIED`. The
analyses, as the MVP's checker reports them (`BE_MVP_POLICY: PASS
scenario=anchor grants=12 flows=2 checks=8`, configuration identity
`336bfddc…`): A1 passes (9 types, 3 classes, 12 rules; 3 subjects and 13
objects, each labeled once); A2 passes (each rule reachable); A3 passes
(no domain type holds a permission on `monitor_mem_t` or `map` on another
domain's private type; every channel rule has its storage and every
shared storage its channel rules; the one `domain` rule names another
domain's type); A4 passes (each rule within its need set); A5 reports
`req_t` as static, not revocable, single writer `host_t`, and `resp_t`
as static, not revocable, single writer `prot_t`, which V3's default
permits for a static instance; A6 passes with `F = D = {(host_t, prot_t),
(prot_t, host_t)}` and `F+ = D+`; A7 is vacuous (`pause` and `terminate`
make no grant, and no delegation exists); A8 passes (12 grants, each
allowed by its rule). The two denied-by-the-policy requests and the five
denied accesses are instances of this specification, as Instance 1's
two denials are of its.

Two things Instance 3 shows that Instances 1 and 2 do not: a `domain`
rule held by a domain, under which the first management operations
(`pause`, `terminate`; no `enter`, `switch_to`, resume, or delegation)
are static grants of the sealed manifest, validated offline against the
policy's `domain` class (A8) and decided at run time by the control hart
from the sealed grants alone, with no policy evaluation in HS, so that
neither trigger of Part 5 fires for it (M2 plan, "The management
extension", "The triggers for Instance 3"); and a memory
object (`secret_t`) that one domain may read and no domain may write,
whose content the monitor places, which is `memory` in the policy and a
measured input in the mechanism (M2 plan, "The measurement"), not a new
class.

**Instance 2 and the `te-poc` scenario.** The MVP's `te-poc` scenario
(M1) realizes Instance 2 and extends its labeling: Instance 2 labels the
monitor's image, pool, staging region, and kexec FDT slot
`monitor_mem_t`; `te-poc` labels, in addition, the hart region and the
MVP region, which M0 added, `monitor_mem_t` too
(`mvp/scenarios/te-poc/scenario.json`). Its policy is Instance 2's.
Where the M3 plan speaks of "Instance 2" as a fixture generated from
`te-poc`, the fixture is this extension; Instance 2's accepted text is
unchanged.

### R1.5 Part 7: the inventory, extended

Part 7's table gains three rows, and its "Fixtures" row an entry; the
accepted rows keep their text:

| Element | Change | Where it would land |
| --- | --- | --- |
| The hart binding and the `hart` class (new row) | Add a binding function from domains to harts with the control hart, and the obligations I13 and I14 over it (injective, total, into the non-control harts; nothing about harts that run no domain) | abstract model (a new module; the accepted modules unchanged); C: a bounded binding view |
| Per-hart monitor state (new row) | Add the per-hart objects of I15 by phase (control-initialized before the barrier; the stack, the saved frame, and the hart's own state-page words private after it) as monitor-owned objects disjoint from each other's and from every domain's memory, and unmapped by every root | abstract model; C view |
| Shared words by kind (new row) | Add I16's two kinds of post-barrier shared words, immutable published data and ring state, the rings as monitor-owned objects with one writer hart and one reader hart each, the records and head the writer's and the tail the reader's, and the pre-barrier phase in which only the control hart writes | abstract model, over an enumerated transition vocabulary with total write footprints |
| Fixtures (accepted row; entry added) | … and Instance 3 (R1.4) as a fixture input, beside the two labeled policies of Part 2 | `model/` fixtures, as the plan that implements the inventory places them |

**Erratum, recorded and not edited.** The accepted "Fixtures" row says
"the fixed-TE fixture's topology is Instance 1". Fact (`model/proof/
Model.v`, `platform_inventory`, `read_write_rights`, `read_rights`,
and `canonical_authority`; `model/src/fixtures.c`): Model 0.2's
fixed-TE fixture has eleven frames (monitor code and data, two root
frames, two trusted stacks, two saved states, two private frames, one
shared frame), two guest-physical addresses, and four non-executable
mappings (each domain's private mapping and the producer's shared
mapping read-write, the consumer's shared mapping read-only;
`right_execute := false` in every rights record); it has no guest-code
frame and grants no `execute`. Instance 1 (Part 2) labels R0 resources 12 and
13 as `mgmt_code_t` and `prot_code_t` with `execute`. Model 0.2's fixture
is therefore a **projection** of Instance 1, without the two guest-code
resources and their `execute` right, and a plan that states Instance 1
in the model states it for that projection unless it adds the frames
(M3 plan Q3 keeps the projection and does not widen the model). The
accepted sentence stands as written; this paragraph is its correction.

### R1.6 What this revision does not change

The notation and its conflict-resolution rule; A1 to A8; Instances 1 and
2; I1 to I12; Parts 4, 5, and 6; the claim boundary, which gains only
what R1.1 to R1.5 state (the hart binding and I13 to I16 as
specification, Instance 3 as an instance, the erratum as a recorded
fact); V1 to V4; and the accepted status record. Nothing here implements,
proves, or tests anything. I13 to I16 are specification: no claim is
made that the implementation or the hardware satisfies them, and
Instance 3's board facts are the accepted M2 result's diagnostic
bring-up evidence, cited, not re-claimed.

### Revision status record

```text
security_model_v1_revision_1_status=accepted
security_model_v1_revision_1_target=019cca64971d2399faba3d768d6f5b1fc9145198
security_model_v1_revision_1_acceptance_instruction=accept-019cca64
security_model_v1_revision_1_acceptance_date=2026-10-28
security_model_v1_revision_1_first_candidate=32298add-superseded
security_model_v1_revision_1_record=security-model-v1-revision-1-review-summary.md
security_model_v1_revision_1_plan=mvp-m3-plan.md;c2c249f4c3d364590d2e505a4f6fb5e65456ff81;M3-1
security_model_v1_revision_1_base=97be918d
security_model_v1_revision_1_classes_added=hart
security_model_v1_revision_1_invariants_added=I13,I14,I15,I16
security_model_v1_revision_1_instances_added=instance-3-anchor;policy-bfecfa92;config-identity-336bfddc
security_model_v1_revision_1_a8_reading=interpretation-for-acceptance;structural-bindings-outside-a8;binding-means-extent-grants;accepted-a8-text-unchanged
security_model_v1_revision_1_scope=mvp-static-binding-configurations;fixed-profile-and-model-0.2-not-applicable
security_model_v1_revision_1_instance_2_note=te-poc-extends-instance-2-labeling-by-hart-and-mvp-regions
security_model_v1_revision_1_part_7_rows_added=hart-binding,per-hart-state,shared-words-by-kind;fixtures-row-instance-3
security_model_v1_revision_1_erratum=fixed-te-fixture-is-a-projection-of-instance-1-four-non-executable-mappings;accepted-text-unchanged
security_model_v1_revision_1_review=gpt-5.6-sol-second-round-2026-10-28;findings-incorporated;first-candidate-32298add-superseded
security_model_v1_revision_1_accepted_text_changed=none
security_model_v1_revision_1_code_change=none
security_model_v1_revision_1_model_change=none
```

## Revision 2 (2026-11-01): the console path

**Status: accepted on 2026-11-01 at exact commit `afd395b8`
(instruction `accept afd395b8`); see the document's
[decision record](#decision-record). As presented: proposed as an
additive revision; not accepted.** This section
is the Part 1 revision that work package M7-5 of the accepted
[M7 plan](mvp-m7-plan.md) (exact commit `4f4d094e`, accepted 2026-11-01;
design D-7) carries, which Plan revision S3-C of the
[MVP plan](mvp-plan.md) admits by name in its amendment of stop
condition 1 ("the additive security model v1 Part 1 revisions (threat
model, assets, TCB) that the M7 and M9 plans carry, each as its own exact
commit"). It is appended to the accepted text, which it quotes and does
not edit: every change below is stated as an addition to a named part,
and the accepted parts, Revision 1, the analyses, instances, claims, and
status record above keep their text. It changes no accepted analysis,
instance, or claim; it adds no object class to Part 1's table and no
class to Part 2's notation (S3-C's Q43, at its default: console input is
monitor mechanism outside the policy, as console output already is). It
implements, runs, proves, and tests nothing; the code it describes is
M7-2 to M7-4's, and the `InputRing.v` module it names is M7-5's, after
this revision's acceptance.

Facts below come from the accepted M7 plan (its "Facts the design rests
on", read in the tree at `f5dc770b`), the MVP line at the plan's
acceptance record `ae3e9537` (`src/mvp-layout.h`, `src/mvp-sbi.c`,
`src/mvp-hartmain.c`, `src/mvp-runtime.c`), and the accepted M0 to M2
plans; *fact* marks what a source shows. The console path's terms are the
M7 plan's: the **focus** is the one domain the operator has selected to
receive typed bytes; the **console grant** is the per-domain configuration
fact `console_input`, sealed with the rest of the configuration before any
domain runs; the **input ring** is the dedicated single-writer,
single-reader ring per domain hart that carries typed bytes from the
control hart.

### R2.1 Part 1, object classes: no new class; the console as configuration

Part 1's object-class table gains no row. The console line is not an
object the policy governs: it is the operator's channel to the monitor,
and the monitor's to the operator, outside every domain. What the console
path adds to the model is **configuration, not authority**, in the sense
Revision 1 gave hart identifiers (R1.1): the console grant names which
domains may receive typed bytes, and the focus names which of them does
at a given moment. Neither is a right of one domain over another's
objects; neither appears in a `allow` rule; both are read by the control
hart alone. The `domain` row's "Authority recorded in" column is read as
also naming the manifest's configuration records, where `console_input`
is recorded beside the hart binding.

The input ring is monitor-owned memory of the `memory` class under the
hart region (`0x102044000`, `0x20000` bytes; Revision 1's `hart` row): one
4 KiB ring per domain hart in the block's previously unused bytes at
offset `0xd000` (M7 plan D-1; *fact*: `BE_MVP_BLOCK_UNUSED_OFFSET 0xd000`,
`BE_MVP_BLOCK_UNUSED_BYTES 0x3000`, `mvp-layout.h`), mapped by no domain
root like the rest of the block (I15), and governed by I16's one-writer
rule with the control hart as its writer and the domain hart as its
reader.

### R2.2 Part 1, invariants: I17 and I18

Part 1's invariant table gains two rows after Revision 1's I16. Their
scope is the MVP's static-binding configurations whose sealed
configuration grants console input to at least one domain (the `shell`
variant images the M7 plan defines); in every other configuration the
console read path is never armed and I17 holds vacuously. Their
fixed-instance status is "not applicable" (the fixed profile has no
console input), no Model 0.1 or 0.2 obligation exists, and the M7 plan
names the evidence: host tests of the parser over every byte in every
state, host tests of the write-authority rule and the ring's drop rule,
the capture checker's reconciliation of the control hart's accounting
with the keystroke log and the session file in QEMU, and, on the board,
one typed characterization; `InputRing.v` (M7 plan D-8) states the ring's
discipline beside `Binding.v`, which it does not edit.

| # | Invariant | Fixed-instance obligation | Status beyond the fixed instance |
| --- | --- | --- | --- |
| I17 | Every typed byte the control hart delivers goes to the announced focus, a domain whose sealed configuration grants console input and which is running, and to no other domain; a byte for which no such domain is the focus (no focus yet, a domain without the grant, a paused, terminated, or shut-down domain, a full input ring, input before the path is armed, or a malformed focus sequence) is dropped and counted by reason, never delivered elsewhere and never a cause of failure of any hart or of the run; the domain hart copies delivered bytes into the guest only into a range inside the domain's own window (never the channel page or a declared page), checked before any byte moves, and a refused call consumes no queued byte | not applicable (no console input in the fixed profile) | the M7 plan's D-1 and D-3: the focus parser as a pure table over three states, host-tested on every byte value; the write-authority check through `be_mvp_gstage_translate` (*fact*: the function refuses a range outside the window, `mvp-gstage.c`); the control hart's per-run accounting (bytes read; per domain, bytes delivered and their SHA-256; drops per reason) printed as `BE_MVP:18` and reconciled by the checker; no proof of the C |
| I18 | No guest byte outside printable ASCII (`0x20` to `0x7e`) reaches the operator's terminal, and every line the monitor prints begins with a monitor tag or the domain's prefix, so that no guest byte begins a printed line; an unterminated line of a domain that is paused or terminated is flushed with its prefix or lost, never emitted bare | not applicable | unchanged mechanism (*fact*: `be_mvp_console_feed` stores any byte outside `0x20`-`0x7e` as `?` and posts one LINE record per line, `mvp-sbi.c`; hart 0 prefixes the line and re-checks every byte, `mvp-hart.c`); stated here because the console path makes the operator's terminal a target: the first clause stops a guest from making the terminal answer a query into the focused domain, the two together stop a guest from forging a monitor or log line; a hostile-guest test in the host tests and a QEMU variant; relaxing either is a stop (S3-C's (h)) |

I17 and I18 are mechanism invariants of the control hart and the domain
hart; neither is a policy statement, and neither is an obligation of
Part 3's analyses, which do not see the console. I9's clause "every
hypercall, exit, shared buffer, descriptor, and configuration artifact
is an untrusted input, checked before use" covers the served read's
arguments (`a0`, `a1`, `a2`) as it covers DBCN write's today; I17 adds
what the check must guarantee.

### R2.3 Part 1, threat model: the operator, the typing tool, and the console

The threat model's lists gain the following; nothing in them is removed
or reworded.

- **Attackers** (added): every domain may also try, through the console
  path, to forge a monitor or log line or an operator prompt, to make the
  operator's terminal answer a query into the focused domain (a terminal
  escape sequence), to read or redirect typed bytes meant for another
  domain, to move or learn the focus, or to exhaust the control hart's
  attention by output or the input ring by input. I18 bounds the first
  two; I17 bounds the next two; the last is an availability matter
  (below).
- **Trusted inputs** (new list): the **operator** at the serial console
  and the **typing tool** that types a session file on the operator's
  behalf under board policy item 8 are trusted inputs. What they type is
  theirs; the model does not treat the operator as an attacker of the
  domains, and it does not treat the operator's **relay** (reading one
  domain's output and typing it into another) as a flow the policy
  governs: the operator can carry bytes between domains by hand, as any
  human reading two consoles could, and nothing in the claim or the
  analyses says otherwise. The operator's and the tool's keystrokes are
  recorded; the record is evidence of what was typed, not a control on
  it.
- **Linux's role today** (added): a Linux guest with a shell is still an
  untrusted test payload. The shell, BusyBox, and musl are guest software
  of the attacker's domain and are trusted for nothing; a shell in a
  domain is a demonstration of what an attacker can do from inside it,
  not evidence that arbitrary guests are contained.
- **Assets** (added): the focus state and the console grants, which are
  the control hart's alone; the operator's terminal, in the sense of I18
  (its integrity against guest bytes); and, unchanged, the protected
  domain's secret in `anchor`, which no shell can reach because its
  domain has no grant (S3-C's Q27) and whose bytes never appear in a
  capture (the M7 plan's checker rule).
- **Allowed effects** (added): a domain may fill its own output ring
  with unbounded output and so fail its own hart and end the run (the
  M7 plan's D-2: a documented bound, not backpressure); typed bytes may
  be lost before the control hart reads them, because the firmware
  console keeps no input buffer (M7 plan "Facts"); the first typed byte
  after two seconds of silence may reach the guest up to two seconds
  later (the `hvc` driver's idle back-off). All three are availability or
  latency effects and no confidentiality or integrity effect.
- **Required containment** (added): no typed byte reaches a domain other
  than the announced focus holding the grant; no guest byte reaches the
  operator's terminal unfiltered or at the start of a line; a domain
  cannot change, request, or learn the focus through any monitor
  interface.
- **Deferred, unchanged**, with one named addition: the loss of typed
  bytes under load, and any timing channel through the operator's typing
  cadence or the control hart's poll, are outside the model (host-
  independent availability and microarchitectural noninterference were
  already deferred).

### R2.4 Part 1, trusted computing base: three rows

The TCB table gains three rows; the existing rows are unchanged, and the
closing sentence ("The TCB does not include the Linux guests…") now also
excludes the shell, BusyBox, and musl by name.

| Trusted element | Evidence class today | Note |
| --- | --- | --- |
| The control hart's console input path: the executor's firmware read, the focus parser, the routing to the input rings, and the accounting (M7-3) | planned: host tests (the parser over every byte in every state; the routing and accounting over scripted streams), the image checker, QEMU sessions judged by the capture checker; no proof of the C; `InputRing.v` for the ring's discipline in the abstract model | HS code, as the rest of the monitor; its one new privileged effect is the firmware read |
| The domain hart's served DBCN read and its write-authority check (M7-3) | planned: host tests of every refusal case; QEMU sessions; no proof | reuses the write path's `be_mvp_gstage_translate` (*fact*), the window-only map |
| OpenSBI 1.6's console read path on the COM260 (`sbi_debug_console_read`; the uart8250 driver, which keeps no input buffer and reports no overrun) | planned: one typed and recorded board characterization (M7 plan D-12; S3-C's stop (f) if it fails); QEMU's read path is not the board's | a dependency for availability only: a lost or corrupted typed byte is a lost command, never a byte delivered to the wrong domain, because the firmware never sees the focus |

The operator and the typing tool are **not** TCB rows: they execute
nothing in HS. They are trusted inputs (R2.3), and the claim's required
limit says so in the words the M7 plan fixes.

### R2.5 Scope, and what this revision does not say

- The invariants and the containment clauses above hold for the MVP's
  console path as the M7 plan designs it and are claimed only as the
  M7 result's evidence supports them; they are not proved for the
  implementation.
- Nothing here changes Part 2's notation, the instances, Part 3's
  analyses, Part 4's pipeline, Part 5's triggers, or Part 6. The M7
  plan's D-6 records the evaluation of the two triggers for the console
  path (neither fires) in the pattern of M2's for Instance 3; this
  revision adds no trigger evaluation of its own.
- The console grant is not a `channel`: it creates no flow between
  domains, only between the operator and one domain at a time. If a
  later milestone lets a domain hold or pass the focus, lets the grant
  change at run time, or gives two domains a console at once, the
  question of a console class (S3-C's Q43 alternative) and Part 6's
  dynamic rules reopen.
- Nothing is said about the operator's own conduct, about what a
  researcher types, or about the loss of typed bytes.

### R2.6 What this revision does not change

The accepted text of Parts 1 to 7 and of Revision 1 is byte-identical to
its accepted form; this section is appended. No code, no model file, no
claim text, and no accepted plan changes with it; the claim sentences the
M7 plan fixes take effect through the M7 result's acceptance, not this
revision's.

### Status record addendum (Revision 2)

```text
security_model_v1_revision_2=accepted
security_model_v1_revision_2_target=afd395b8a80b6baa1f5f0946cd0bff91ad806cc9
security_model_v1_revision_2_acceptance_instruction=accept-afd395b8
security_model_v1_revision_2_acceptance_date=2026-11-01
security_model_v1_revision_2_record=security-model-v1-revision-2-review-summary.md
security_model_v1_revision_2_plan=mvp-m7-plan.md;4f4d094efb3985435673f7bda62f35ad51c6165e;M7-5;D-7
security_model_v1_revision_2_admitted_by=mvp-plan.md-S3-C-stop-condition-1-amended-by-name
security_model_v1_revision_2_base=ae3e9537
security_model_v1_revision_2_classes_added=none;console-input-is-configuration-not-authority;Q43-default
security_model_v1_revision_2_invariants_added=I17,I18
security_model_v1_revision_2_threat_model_added=attackers-console-attempts;trusted-inputs-operator-and-typing-tool;linux-role-shell;assets-focus-grants-terminal;allowed-effects-availability-and-latency;containment-three-clauses;deferred-loss-and-cadence
security_model_v1_revision_2_tcb_rows_added=control-hart-input-path;domain-hart-served-read;firmware-console-read-path
security_model_v1_revision_2_scope=mvp-static-binding-configurations-with-a-console-grant;fixed-profile-not-applicable
security_model_v1_revision_2_accepted_text_changed=none
security_model_v1_revision_2_code_change=none
security_model_v1_revision_2_model_change=none
```

## Revision 3 (2026-11-03): the measurement log

**Status: accepted on 2026-11-03 at exact commit `4bc079db`
(instruction `accept 4bc079db`); see the document's
[decision record](#decision-record). As presented: proposed as an
additive revision; not accepted.** This section
is the Part 1 revision that work package M9-2 of the accepted
[M9 plan](mvp-m9-plan.md) (exact commit `4f4a8f76`, accepted 2026-11-03;
design D-8) carries, which Plan revision S3-C of the
[MVP plan](mvp-plan.md) admits by name in its amendment of stop
condition 1 ("the additive security model v1 Part 1 revisions (threat
model, assets, TCB) that the M7 and M9 plans carry, each as its own exact
commit"). It is appended to the accepted text, which it quotes and does
not edit: every change below is stated as an addition to a named part,
and the accepted parts, Revisions 1 and 2, the analyses, instances,
claims, and status records above keep their text. It changes no accepted
analysis, instance, or claim; it adds no object class to Part 1's table
(the `measurement` row exists, "named as an unimplemented asset", and is
instantiated here) and no class to Part 2's notation. It implements,
runs, proves, and tests nothing; the code it describes is M9-3's and
M9-4's, after this revision's acceptance, and its invariants are
specification, not proofs: M8's stage 1 abstracts the launch gate as a
predicate (the M8 plan's D-1), and nothing here is a theorem of it.

Facts below come from the accepted M9 plan (its "Facts the design rests
on", read in the tree at `6fbcc3d1`, corrected by the steering review the
plan records), the MVP line at that commit (`src/mvp-runtime.c`,
`src/mvp-core.c`, `src/mvp-core.h`, `src/mvp-layout.h`,
`src/mvp-monitor.lds`), and the accepted M0 to M2 plans; *fact* marks
what a source shows. The terms are the M9 plan's: the **log page** is the
4 KiB page of hart 0's MVP-region BSS that holds the log's header and
records; the **registers** are the four 32-byte values beside it, one per
stream, each extended by the measured records' digests in order; a
**launch record** is a measured record of a domain's kernel Image or
device tree as placed (and `anchor`'s secret page); the **launch gate**
is hart 0's comparison of a domain's launch register with the image's
expected value before that domain's hart starts; the **reference
manifest** is the per-image, post-link file the generator writes, which
says what every record must be; the **loader observation** is U-Boot's
`md5sum` of the loaded boot image on the board (`crc32` in the U-Boot
rehearsal; none in a direct QEMU boot); the **platform observation** is
the human's read-only probe of the board's lifecycle and debug state,
recorded on the plan's template with one of four outcome classes.

### R3.1 Part 1, object classes: the `measurement` asset, instantiated

Part 1's object-class table gains no row. Its `measurement` row, which
the accepted text fills with "none; named as an unimplemented asset" and
"a later milestone", is read after this revision as naming the log page
and the registers: monitor-owned memory of the `memory` class, hart 0's
(the M9 plan's D-1: `be_mvp_log`, 4 KiB aligned and wholly inside hart
0's MVP-region BSS between `__be_mvp_bss_start` and `__be_mvp_bss_end`,
and `be_mvp_log_registers`, 128 bytes beside it; *fact*: the MVP region's
BSS lies inside the `.mvp.data` output section, `mvp-monitor.lds`), mapped
by no domain root (I2: "monitor-owned state … is mapped by no domain
root"), excluded from every domain's window and from every declared page
(*fact*: the windows and the channel pages are the only guest-mapped
ranges, `mvp-layout.h`), and governed by I15 and I16 with hart 0 as the
one writer. "Authority recorded in" is read as: the reference manifest
(what the records must be) and the sealed configuration's expected
launch registers (what the gate compares against), both build products
the image carries or the record retains; the log holds no authority of
its own and grants none.

Two things the asset is not. It is **not a secret**: its records are
digests of placed bytes and build-recorded identities, printed on the
console in full, and the integrity I19 and I20 state is the asset's
whole value; "no secrecy" is said of this log and its test secrets,
which are public (`anchor`'s secret page is a 32-byte test value the
record prints), and is not generalized to a future low-entropy secret or
a confidential policy, whose measurement would need its own treatment.
It is **not evidence against an adversary who alters the monitor**: the
monitor's digest of its own text and read-only data (the plan's R2, if
kept) is a **self-report**, compared offline and gating nothing, and
code able to alter the monitor can fabricate every record; the log is a
local identity, not attestation, with no key, nonce, freshness, or root
of trust (the plan's D-9 words).

### R3.2 Part 1, invariants: I19 and I20

Part 1's invariant table gains two rows after Revision 2's I18. Their
scope is the MVP's static-binding configurations as the M9 plan builds
them (every scenario and variant image, the probe images, and the
negatives, each under the plan's per-image contract); their
fixed-instance status is "not applicable" (the fixed profile measures
nothing), no Model 0.1 or 0.2 obligation exists, and the M9 plan names
the evidence: host tests of the encoding offset by offset and of the
register recurrence against `mvp-sha256.c`, the image checker's rules
(the page's alignment and containment; the `HART0_ONLY` reachability of
the page and the registers), the capture checker's rebuild of the page
from hart 0's printed lines, its replay of the registers, its independent
recomputation of every digest from the build's inputs, its field-by-field
comparison with the reference manifest, and its enforcement of the
global order in QEMU for every image, and, on the board, one correlation
boot when a session is scheduled; no proof of the C, and no theorem of
M8's stage 1, which abstracts the gate.

| # | Invariant | Fixed-instance obligation | Status beyond the fixed instance |
| --- | --- | --- | --- |
| I19 | Hart 0 alone writes the log page and the registers, and only before any domain hart starts: every record is appended, every register extended, and the close record written with the expected count before `BE_MVP:07` and before the first SBI HSM start; after the close no record is appended and no register is extended but the terminal rendering, which prints and does not write; a page that cannot close, or a record that would exceed the capacity, fails the run before any hart starts (`BE_MVP_CLASS_LOG`); no domain hart reads the page or the registers | not applicable (the fixed profile measures nothing) | the M9 plan's D-1: the explicit encoding and the capacity (41 records, the close included; at most 15 expected per image); the global rule; the image checker's `HART0_ONLY` rule extended to the page and the registers with negative cases; the capture checker's rebuild and global-order check; no proof of the C |
| I20 | No domain hart starts unless every launch comparison the image's per-image contract requires has **succeeded** (each domain's launch register equal to the image's expected value, the record's outcome `gated-pass`) and the log is closed; each domain's launch records and its gate's comparison precede that domain's `HART_STARTED`; a failed comparison fails the run before any hart starts, with both values printed, and the run's images are the checker's finding against the nominal reference, never an accepted result | not applicable | the M9 plan's D-2 (the per-image contract and the `gated-fail` outcome), D-4 (the checker requires each `gated-pass` and `:06 LAUNCH` before that domain's `:08 HART_STARTED`, and the close before `:07`), the `wrong-measurement` image, and the capture mutations with the reference frozen; no proof |

I19 and I20 are mechanism invariants of the control hart; neither is a
policy statement, and neither is an obligation of Part 3's analyses,
which do not see the log. I9's clause covers the log's inputs as it
covers every configuration artifact: the placed bytes are hashed as they
lie after the placements the M1 and M2 plans fix, and the build-recorded
identities are the image's constants; nothing the log records is read
from a domain after that domain runs. What the registers bind is stated
exactly: each stream's register commits to the ordered sequence of the
measured records' **digest values** under the hash assumption, and to
nothing else; a record's object, range, type, or outcome, the header, the
informational records, and the interleaving across streams are bound
only by the checker's field-by-field comparison with the reference
manifest, and the close record is structural, not cryptographic (the M9
plan's D-1). Quoting the four registers therefore does not authenticate
the log; the plan's D-9 says so, and no later milestone may assume
otherwise without a key and a root of trust (2.0's attestation line).

### R3.3 Part 1, threat model: the measurement's place

The threat model's lists gain the following; nothing in them is removed
or reworded.

- **Attackers** (added): every domain may also try, through its
  console output, to forge a `BE_MVP:19 LOG` or `BE_MVP:20 REGISTERS`
  line (I18 bounds it: a guest line begins with the domain's prefix and
  the checker accepts records from hart 0's unprefixed stream alone), and
  may try to alter its own placed kernel, device tree, or secret page
  after the launch, which the log does not see (a launch record speaks
  of the bytes at the point of measurement and not after; the plan's
  D-9). Code able to alter the monitor is outside the model's attackers
  as before (the deferred "firmware-hostile launch"); its effect on the
  log is named in R3.1, not defended.
- **Trusted inputs** (added to Revision 2's list): the **reference
  manifest** and the **generator** that writes it, the **loader
  observation** (U-Boot's `md5sum`, by an unmeasured U-Boot identified by
  its banner; *fact*: `tools/k3-env.sh`'s `be_ld` line), and the
  **platform observation** (the human's read-only probe, a human input
  and not HS code; its outcome class dated). Each is evidence of a
  different kind and the three are **never one chain**: the log and the
  launch gate are the monitor's software record; the loader observation
  is attribution of a board run to its image and nothing more; the
  platform observation is a dated assumption about the board's lifecycle
  and debug state. A shared record identifier may associate them in a
  run's record; it does not make one evidence for another.
- **Assets** (added): the log page and the registers (R3.1; integrity,
  no secrecy); the expected launch registers and the configuration
  constants baked into the image before the link (what the gate
  compares against); the reference manifest (what the checker compares
  against; a build product, regenerated and never edited).
- **Allowed effects** (added): hart 0's hashing of two placed kernel
  Images, two device trees, and a secret page before the barrier, and the
  rendering of the log's lines, lengthen the boot by an amount the plan
  measures and records in every run (*fact*: a retained RC3 `anchor` run
  spent `0xc81d8` ticks, 34.2 ms at 24 MHz, on M2's one measurement of a
  1,907,940-byte Image); the console volume grows by the `:19` and `:20`
  lines (about 89 ms per KiB at 115200 baud). Both are availability and
  latency effects, measured and reported, and no confidentiality or
  integrity effect; the operational budget is armed after them.
- **Required containment** (added): no domain hart writes or reads the
  log page or the registers; no domain starts before every required
  launch comparison has succeeded and the log is closed; no guest line is
  taken for a record; no record is taken as evidence of bytes after the
  point of measurement, of the firmware, of the loader, or of the
  board's lifecycle state.
- **Deferred, unchanged**, with three named additions: the measurement
  of SPL, OpenSBI, U-Boot, and the board's device tree (the plan's D-12:
  unmeasured, and said to be); a root of trust, a key, a nonce, freshness,
  and attestation (2.0's line, D20's "measure first, then attest"); and
  what the boot ROM does or does not authenticate, which is the
  disposition of Q14: a documented platform assumption, dated with the
  probe, on which no 1.0 claim relies.

### R3.4 Part 1, trusted computing base: the running TCB and the evidence TCB

The TCB table's row "The initial measured configuration and policy"
("none: no measurement exists"; "named as an asset; unimplemented") is
read after this revision as filled by the rows below. The table gains
them; the existing rows are unchanged. This revision also makes a
distinction the accepted table did not need: the **running TCB** (HS
code and the hardware and firmware beneath it, trusted for the claim's
containment) and the **offline evidence TCB** (the tools trusted for the
evidence's integrity, which execute nothing in HS). The generator, the
reference manifest, and the checker's replay are of the second kind; a
defect in them weakens the evidence, never the containment.

| Trusted element | Evidence class today | Note |
| --- | --- | --- |
| Hart 0's measurement path: the SHA-256 (`mvp-sha256.c`, FIPS 180-4 and RFC 4231 vectors in `tests/sha256-test.c`), the log's append, close, extend, and render (`mvp-log.c`, M9-3), and the launch gate | planned: host tests of the encoding and the recurrence; the image checker; QEMU runs of every image judged by the capture checker; no proof of the C; M8's stage 1 abstracts the gate as a predicate and does not prove the logging | HS code, as the rest of the monitor (running TCB); it writes hart 0's own memory before the barrier and nothing of a domain's |
| The generator's expected launch registers and configuration constants, baked into the image before the link | planned: the same bytes hashed offline by the generator and recomputed by the checker; the `wrong-measurement` image | evidence TCB; a wrong expected value fails the run closed, it does not open it |
| The reference manifest and the generator that writes it (`tools/gen-reference.py`, M9-4) | planned: deterministic (no timestamp, no absolute path); the host's and the evaluator's references compared byte for byte; pinned by the image checker; copied into every retained record | evidence TCB; regenerated on every build, never edited |
| The capture checker's log module: rebuild, replay, independent recomputation, field-by-field comparison, the global order, the export (M9-4) | planned: its negatives in the plan's five kinds, each with the reference frozen; a round-trip self-test | evidence TCB; its replay values are labelled `unprotected`; its recomputation, not the printed digests, is what it trusts |
| U-Boot's `md5sum` of the loaded boot image on the board (the loader observation; `crc32` in the rehearsal) | board observation (M5 onward); the staging record's MD5 and SHA-256 | an unmeasured U-Boot identified by its banner; attribution of a run to its image and nothing more; never in the page; MD5 has no registry entry |
| The human's read-only probe of the board's lifecycle and debug state (the platform observation) | the plan's template, dated, with one of four outcome classes, or "not performed" with the date | a human input, not HS code; a dated assumption in the claim's required limit; its absence is an honest outcome the plan's words carry |

The closing sentence of the accepted table ("The TCB does not include
the Linux guests…") stands; the log measures a guest's kernel Image and
device tree as placed and trusts nothing inside them, and it measures no
file inside a guest (D20: IMA is never used, and the plan makes the
exclusion testable).

### R3.5 Scope, and what this revision does not say

- The invariants and the containment clauses above hold for the MVP's
  measurement log as the M9 plan designs it and are claimed only as the
  M9 result's evidence supports them; they are not proved for the
  implementation, and they are not theorems of M8's stage 1, which
  abstracts the launch gate as a predicate on the pre-entry state (the
  M8 plan's D-1 and P7). When M8's result and M9's are both accepted, the
  correspondence between stage 1's gate predicate and M9's global rule
  (every comparison succeeded and the log closed) is re-read at
  integration under the re-proof rule (M10's gates); this revision does
  not assert it.
- Nothing here changes Part 2's notation, the instances, Part 3's
  analyses, Part 4's pipeline, Part 5's triggers, or Part 6. The M9 plan
  evaluates no trigger: the log is monitor mechanism outside the policy,
  as the console path is; a domain's own measurement register that a
  guest could extend (the plan's crosswalk route (b)) would be a new
  interface and reopens the question, and is 2.0's.
- The log is not a `channel`, a `notification`, or a `manifest`: it
  flows to no domain, signals nothing, and seals nothing; it records what
  was sealed and placed.
- Nothing is said about the bytes of a kernel, device tree, or secret
  page after the point of measurement, about the firmware's or the
  loader's integrity, about the board's boot ROM, or about any run on
  which the loader observation or the platform observation is absent
  beyond what the plan's D-9 words say of each.

### R3.6 What this revision does not change

The accepted text of Parts 1 to 7 and of Revisions 1 and 2 is
byte-identical to its accepted form; this section is appended. No code,
no model file, no claim text, and no accepted plan changes with it; the
claim sentences the M9 plan fixes (D-9) take effect through the M9
result's acceptance, not this revision's.

### Status record addendum (Revision 3)

```text
security_model_v1_revision_3=accepted
security_model_v1_revision_3_target=4bc079dbb96540cb44008a53df857701696e9bad
security_model_v1_revision_3_acceptance_instruction=accept-4bc079db
security_model_v1_revision_3_acceptance_date=2026-11-03
security_model_v1_revision_3_record=security-model-v1-revision-3-review-summary.md
security_model_v1_revision_3_plan=mvp-m9-plan.md;4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33;M9-2;D-8
security_model_v1_revision_3_admitted_by=mvp-plan.md-S3-C-stop-condition-1-amended-by-name
security_model_v1_revision_3_base=bc80b620
security_model_v1_revision_3_classes_added=none;the-measurement-row-instantiated
security_model_v1_revision_3_invariants_added=I19,I20
security_model_v1_revision_3_threat_model_added=attackers-forged-lines-and-post-measurement-alteration;trusted-inputs-reference-manifest-generator-loader-observation-platform-observation-never-one-chain;assets-log-registers-expected-values-reference;allowed-effects-hashing-and-rendering-time;containment-four-clauses;deferred-firmware-root-of-trust-boot-rom
security_model_v1_revision_3_tcb_rows_added=hart-0-measurement-path;expected-values;reference-manifest-and-generator;checker-log-module;loader-observation;platform-observation
security_model_v1_revision_3_tcb_distinction=running-TCB-vs-offline-evidence-TCB
security_model_v1_revision_3_scope=mvp-static-binding-configurations-under-the-per-image-contract;fixed-profile-not-applicable
security_model_v1_revision_3_accepted_text_changed=none
security_model_v1_revision_3_code_change=none
security_model_v1_revision_3_model_change=none
```

## Revision 4 (2026-11-11): the physical boundary under the monitor

**Status.** Proposed by the commit that adds this section, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If the commit that adds
this section is on the public `main` with the responsible human's
`Signed-off-by`, this revision is accepted as written. Any other answer
needs a revised commit before the sign-off. The signed commit differs
from the one reviewed only by that line and its committer date; if it
must be rebased first, the internal record says so. The project's
internal records keep both commit IDs and the instruction, as they do
for Plan revision S3-D. This document's decision record, above, is not
updated for a revision accepted this way: the signed commit on the
public `main` is the record.

This section is the Part 1 revision that Plan revision S3-D of the
[MVP plan](mvp-plan.md) calls for in its decision D26 and its
requirement M11-R8. S3-D's amendment of stop condition 1 admits it by
name: "the additive security model v1 Part 1 Revision 4 that M11 needs
(M11-R8), which goes to the responsible human as its own exact commit".
It comes before M11's plan.

- It is appended to this document's accepted text, which it quotes
  and does not edit. Every change below is stated as an addition to a
  named part, or as a reading of an accepted sentence; R4.5 lists the
  readings. The accepted parts, Revisions 1 to 3, the analyses,
  instances, claims, and status records above keep their text. One
  pin of the claim ledger changes with it (R4.6).
- It adds one attacker, four object classes, and eight invariants to
  Part 1. It adds no class to Part 2's notation, and it changes no
  analysis, instance, or claim.
- It selects no design. It says what any design of the boundary has to
  provide, in terms that do not depend on the mechanism. M11's plan
  chooses the mechanism and names the evidence.
- It implements, runs, proves, and tests nothing. Its invariants are
  specification.

**Terms.** S3-D.2's, and these. "Domain" alone, in the accepted text
above, means VS domain.

- A **VS domain** is the security model's `domain`. A **VS-domain
  hart** is the accepted "domain hart".
- A **physical access profile**, or **profile**, is "the set of
  physical extents, with rights, that one hart may reach after its
  activation, enforced by M-mode" (S3-D.2). A hart is **confined** from
  the moment M-mode installs its profile. Before that it has its
  **boot access**: whatever the boot gives it. M11-R6 calls that the
  hart's "boot profile".
- **A hart's activation** is the event after which its HS-mode code is
  S3-D.1's attacker. The word is used here of a hart only. Model 0.2
  uses "active" and "activation" of the whole configuration; that use
  is unchanged.
  - A VS-domain hart's activation is its first guest entry.
  - The control hart's activation is, in S3-D.1's words, "the control
    hart's boot barrier". This revision reads that as **the end of the
    control hart's boot work, the hart starts included**. In I15 and
    I16, in Revision 3 (I19's `BE_MVP:07`), and in R4.1's `hart` row,
    "the barrier" stays the publication of the blocks.
  - The plans use the words in this revision's sense. D15 has "SBI
    HSM `hart_start` once per domain hart before the boot barrier".
    Stop condition 3 excludes "a hart started or stopped after the
    boot barrier". The M0 plan says of its step of hart starts: "After
    this step no hart is started or stopped".
  - *Fact*: the source gives the name to an earlier event, the
    publication of the blocks (`BE_MVP:07`), and the control hart
    starts the VS-domain harts after it (`mvp-runtime.c`:
    `publish_blocks()`, then `start_harts()`). Revision 1's acceptance
    record notes the same order.
  - Why the reading matters: a hart start names a hart and the address
    at which it begins. Made by boot code, that is trusted. Made after
    the control hart's activation, it would be an attacker's choice.
  - The bounds. The reading puts the event after the hart starts. I26
    puts it no earlier than the control hart's confinement, where a
    configuration confines that hart, and no later than the first
    input that the control hart takes from an activated VS-domain
    hart. M11's plan fixes the event.
- A **parked** hart is one that the configuration does not use. It
  executes nothing outside M-mode, or it is confined to parking code
  that lies outside the monitor's memory: its rules deny it the
  monitor's memory and every VS domain's. S3-D.4: such harts "are
  parked under rules that deny them the monitor's memory". A VS-domain
  hart that the monitor "parks" after a pause, a terminate, a
  shutdown, or a failure is not parked in this sense: it keeps its
  role and its profile (I25).
- A **shared region** is a physical extent that more than one hart may
  reach after their activations: under its profile, or, for a hart that
  a configuration leaves unconfined, without one.
- A **mailbox** is an extent of a shared region that one hart writes
  and other harts read. A ring is two mailboxes: its records and head,
  which its writer writes, and its tail, which its reader writes (I16).
  S3-D.1's "mailboxes between harts, which both ends write by design"
  are the rings.
- The **partition descriptor**, or **descriptor**, is M11-R1's: it is
  "generated offline from the scenario and the layout, with an
  identity".
- A **firmware call** is a service that M-mode performs for a hart at
  that hart's request. What M-mode does for a hart in handling a trap,
  such as an access that it emulates, is treated beside it
  (I27 (e)).
- The **boundary** is the whole arrangement: the descriptor, the
  profiles, and M-mode's enforcement of them.

**Facts.** *Fact* marks what a source shows. The sources are the
accepted S3-D text, the M0 plan, Revision 1's acceptance record, and
the MVP line at this revision's base, `b332f658` (under `mvp/src`:
`mvp-layout.h`, `mvp-runtime.c`, `mvp-hartmain.c`, `mvp-hart.h`,
`mvp-executor.c`, `mvp.h`), which this revision does not change. The
characterization that S3-D.5 describes is reading, and
emulation in scratch outside the repository. It informed this text and
is not evidence for it.

### R4.1 Part 1, object classes: the profile, the shared region, the descriptor, and the firmware call

Part 1's table gains four rows, and the `hart` row's instances column
grows. The other rows are unchanged.

| Class | Instances today | Authority recorded in |
| --- | --- | --- |
| `profile` (new) | none. MVP 1.0 uses no physical memory protection (*fact*: no source under `mvp/src` names it), and what the board's firmware programs was never recorded. M11 is to give one to each hart that the monitor uses, and to park the rest | the descriptor; the rules that M-mode installs from it |
| `shared_region` (new) | none as an object. What the harts share today, they share by convention: the monitor's code and constants; what the control hart publishes before the VS-domain harts start; the rings between the control hart and each VS-domain hart (I16); and the declared pages that two VS domains map | the descriptor: for each region, the harts that are party to it, each party's rights, and its one writer, if any |
| `descriptor` (new) | none | itself: built offline, immutable from the build on, with an identity |
| `firmware_call` (new) | the calls that the monitor makes to the firmware below it, listed under this table. No record says which hart may make which call | after M11, the allowlist of M11-R2: for each hart, by its role and whether it is confined, the calls that M-mode performs |
| `hart` (instances column, added) | … and, under the boundary, each hart's **role** (the control hart, a VS-domain hart, or parked) and whether it is confined yet. *Fact*: the monitor starts only the harts of its binding. Before the barrier it asks the firmware once for the state of every hart but itself (`BE_MVP:02`), and accepts at most one other started hart: the boot hart that the shim's start rule left idle (the M0 plan's revision M0-A). The board has execution contexts beyond the eight harts that the monitor counts; R4.3 and R4.4 name them | unchanged, and the descriptor |

The firmware calls that the monitor makes today (*fact*:
`mvp-executor.c`, `mvp-runtime.c`, `mvp-hartmain.c`, `mvp.h`):

- the control hart: the version and probe calls, the hart status and
  hart start calls, the IPI, the console's write and read, and the
  system reset;
- a VS-domain hart: the IPI, and, on its failure path, the console's
  write and the system reset;
- no guest request is forwarded to the firmware.

Four things about these classes.

- **A profile is not policy.** It is not a `domain`, it has no type,
  and no `allow` rule names it. It is mechanism under the policy, as
  the hart binding is (Revision 1). The accepted text says that "the
  monitor's own access is outside the policy's subject set", and that
  stays so.
- **It stands beside the order of authority, not in it.** That order
  is "policy, then manifest, then mappings", and it bounds each guest.
  The descriptor and its profiles bound each hart. I22 (a) ties the
  two: a profile gives a hart no more of a VS domain's memory than the
  mappings give that VS domain.
- **A profile is not a supervisor domain.** This revision names no
  Beryllium unit a supervisor domain, an RDSM, or an SDSM, and gives
  none an SDID or a memory protection table (S3-D's stop (k)).
- **Identifiers are still not authority** (S1 H03). A hart number, a
  profile's place in the descriptor, and a region's name each name
  something. For a confined hart, only the descriptor, as M-mode
  installed it, gives access.

### R4.2 Part 1, invariants: I21 to I28

Part 1's invariant table gains eight rows after Revision 3's I20.

- **Scope.** The MVP's static-binding configurations that are built
  with the boundary: the images that M11's plan, or a later plan such
  as M12's, defines. They are not asserted of an image without it.
  MVP 1.0's images are without it, and so is any variant that a plan
  builds with the boundary off. M11's plan lists the images. The probe
  images, in which two harts write one structure, are among those that
  it has to decide.
- **Fixed-instance status:** "not applicable". The fixed profile of
  R0 to R7 runs on one hart and has no boundary under the monitor. No
  Model 0.1 or 0.2 obligation exists.
- **Evidence:** none. No configuration with a profile exists. M11's
  plan names the evidence, under M11-R5 to M11-R7, which include: "A
  hart that merely stops is not a pass". Until M11's result is
  accepted, nothing here is claimed of any image.

I22, I23, I26, and I27 have clauses, which follow the table.

| # | Invariant | Fixed-instance obligation | Status beyond the fixed instance |
| --- | --- | --- | --- |
| I21 | **Confinement.** From the moment it is confined, a hart can read, write, or execute only the physical memory that its profile allows, with the profile's rights. This holds for every access made on the hart, in HS, VS, or VU mode. An access that the profile forbids reads nothing and changes nothing. The rule is enforced below HS mode, and nothing that HS-mode code can execute changes it | not applicable | none; M11 |
| I22 | **What a profile may hold.** A profile allows only what its hart's role needs from its confinement on: clauses (a) to (f) | not applicable | none; M11. Clause (d) is how I8 is to hold against the HS-mode code of a confined hart |
| I23 | **Shared regions.** Every extent that more than one hart may reach after their activations is a shared region that the descriptor lists, with its parties, each party's rights, and its one writer, if any | not applicable | none; M11. I16 states the one-writer rule for words; this states it for the extents that a profile can tell apart. *Fact*: today one state page holds both writers' ring words and the control hart's published words (`mvp-hart.h`), so I22 and I23 need the layout of M11-R4 |
| I24 | **The descriptor, and where a profile comes from.** The descriptor is built offline from the same scenario and layout as the image's sealed configuration. It is immutable from the build on, and it has an identity. Its profiles satisfy I22 and I23 against that configuration. M-mode installs a profile only from the descriptor. It selects the profile from what it knows itself: the hart that it is running on, and whether it has confined that hart. In installing or selecting a profile, it takes no range, no profile, and no hart from HS-mode code | not applicable | none; M11. M11-R1 says the same. S3-D's stop (n) bars a design that does it after activation |
| I25 | **Confinement is one-way.** Within one boot, nothing gives a confined hart its boot access back, or any other profile: no firmware call, no trap, no interrupt, and no suspend, resume, stop, or start of that hart or of another. A system reset ends the boot, and the next boot begins in boot code | not applicable | none; M11 |
| I26 | **Order.** Confinement comes before exposure: clauses (a) to (d) | not applicable | none; M11 |
| I27 | **Firmware calls.** For a confined hart, M-mode performs only the calls that the allowlist gives the hart's role, and touches for it only memory that its profile allows: clauses (a) to (e) | not applicable | none; M11 |
| I28 | **Every context is accounted for.** Every execution context that can address physical memory is one of three things: a confined hart; a parked hart; or a context named in the trusted computing base, with the evidence for what it can reach | not applicable | none; M11. I13 and I14 "say nothing about harts that run no domain"; this does |

**I22, the clauses.** A profile allows only the following.

- (a) Of VS domains' memory and declared pages: a VS-domain hart's
  profile allows no frame and no right beyond what the sealed
  configuration's mappings give the VS domain bound to that hart. The
  control hart's profile allows none.
- (b) Of the monitor's memory:
  - the code and constants of the hart's role;
  - read-only, the data that was fixed before the hart's activation
    and that its role reads. For a VS-domain hart that is what the
    control hart published to it (I16), its own G-stage tables among
    them. For the control hart it is the sealed configuration, and
    the log page and its registers (I19);
  - the hart's own private state (I15, as Revision 1's acceptance
    record corrects it; for the control hart, I16's "own state");
  - the hart's side of each shared region that it is party to.
- (c) A device's registers, only where the descriptor assigns that
  device to the hart's role. No scenario assigns one.

A parked hart's profile allows its parking code alone, to read and
execute, and nothing of (a) to (c).

Nothing else. In particular, no profile allows:

- (d) a write to the monitor's code or constants, to the sealed
  configuration, to a G-stage table, or to the log page or its
  registers (I19);
- (e) any place where the boot chain or boot code put a copy of a
  secret, other than the declared page that the secret's VS domain may
  read: neither its source among the monitor's constants, nor a copy
  of the boot image that a loader left in memory;
- (f) M-mode's memory, or another hart's private state.

In (b) and (d), "the sealed configuration" is what the control hart
validated, sealed, and derived before any VS-domain hart started: the
sealed state and its identity, and the derived maps and page leaves.
*Fact*: today those lie among the control hart's mutable data
(`mvp-runtime.c`), so (d) needs the layout of M11-R4 too.

**I23, the kinds.** A shared region of the monitor's memory is of one
of two kinds.

- An **immutable** region is one that no party's profile allows a
  write to.
- A **mailbox** has one writing hart. The writer's profile allows the
  write, and every other party's profile allows reading only.

A declared page that two VS domains map is shared with each VS
domain's rights (I22 (a)). What a hart reads from a region that another
hart can write is untrusted input, checked before use (I9). The reader
attributes it to the region's writer, never to a field that the writer
supplied.

**I26, the clauses.**

- (a) Every hart that a configuration confines is confined no later
  than its activation. For a VS-domain hart, that is before its first
  guest entry.
- (b) Every such hart is confined before it takes as input anything
  that another confined hart can write after that other hart's
  activation.
- (c) Before its activation, a hart's HS-mode code is boot code: it
  runs no guest, and every input that it takes is checked (I9).
- (d) The control hart's activation comes no later than the first
  input that it takes that a VS-domain hart can write after that
  hart's activation.

In (b) and (d), an input counts once it is taken after the activation
of a hart that can write it. Console input counts as written by each
hart whose allowlist keeps the console write (R4.3).

**I27, the clauses.** For a confined hart:

- (a) M-mode performs only the calls on the allowlist for the hart's
  role, as confined. Any other call is absent or refused.
- (b) A call that reads or writes memory for its caller touches only
  memory that the caller's profile allows, with the right that the
  access needs. That holds for every address and length that the
  caller can give, at the call and whenever M-mode later acts on what
  the call registered.
- (c) No call changes another hart's profile, private state, or run
  state, unless the descriptor names that effect for that pair of
  harts. A system reset, where the allowlist has it, is the one
  exception: it ends the boot (I25).
- (d) A refused call changes no memory, in whole or in part.
- (e) What M-mode does for the hart in handling a trap obeys (b) to
  (d) as a call does. The allowlist of (a) is of calls, and does not
  apply to it.

Eight readings that keep these exact.

- **I21 and the G-stage.** I21 adds a bound and removes none. The
  G-stage still bounds each guest (I1 to I4). A profile bounds the
  hart, and so also what a forged `hgatp` can reach: the write to the
  register is not stopped, and the accesses that follow it are.
- **I21 is about memory, not about what happens next.** Whether a
  forbidden access is reported to the hart's own HS-mode code, stops
  the hart, or is counted is the design's. M11-R7 asks for M-mode's
  count as the witness of a test.
- **I22 (d) and I8.** The accepted TCB table says of "The sealed
  manifest's protection inside HS": "none: the seal is an API
  property, and any HS C code can write the sealed state (S1 H05)",
  and its note calls that an "open obligation on the first
  protected-domain milestone". I22 (d) states that obligation for a
  confined hart. For HS-mode code that is not confined, the accepted
  row stands.
- **I22 (e) and the test secret.** The MVP's secret is a public test
  value (Revision 3, R3.1). The clause is about structure: a real
  secret placed the same way would be covered.
- **I22 (f) and M-mode's memory.** Keeping M-mode's memory out of
  every profile is the firmware's work, as it is today (S3-D.1). It is
  listed so that no descriptor may say otherwise.
- **I23 and the hub.** A mailbox is written by a hart that may be
  breached, so its reader's parser is attack surface, in both
  directions.
  - A breached VS-domain hart can attack the control hart through the
    mailboxes that it writes. A breached control hart can attack every
    VS-domain hart through the mailboxes that it writes, and a
    VS-domain hart breached that way reaches its own VS domain.
  - I21 and I22 bound what each confined hart that such an attack
    breaches can reach to that hart's own profile. They do not prevent
    the attack or its continuation. S3-D.1 says as much: "The control
    hart stays a hub".
  - What the boundary changes: where the control hart is confined,
    reaching another VS domain's memory directly takes a breach of a
    reader in the control hart, and then of that VS domain's own hart.
    Where the control hart is not confined, the first breach is
    enough. Without the boundary, one breached trap path is enough.
  - What it does not change: a VS domain whose sealed configuration
    grants console input is open to a breached control hart through
    that console, as it is to the operator. While it has the focus, it
    is also open to what a breached hart's console write makes the
    operator's terminal answer (R4.3).
- **I24, I27, and what M-mode can know.** M-mode does not see a
  VS-domain hart's first guest entry. What it knows of a hart's phase
  is its own record: whether it has confined that hart. The allowlist
  of I27 (a) is therefore keyed by that. Confinement comes no later
  than activation (I26 (a)), so whatever M-mode refuses a confined
  hart, it refuses after the hart's activation, as M11-R2 asks.
- **A hart that is not confined.** S3-D orders M11's work under
  emulation: "the VS-domain harts confined first … then the control
  hart narrowed". In a configuration of the first kind, the control
  hart is not confined, and no profile bounds it. I21, I22, and I27
  say nothing of what it reaches or calls, and I26 (a) and (b) nothing
  of its order. I23, I24, I25, I26 (c) and (d), and I28 still apply:
  I28 has it named in the trusted computing base (R4.4). I26 (b)
  speaks of input from confined harts only, because nothing contains
  an unconfined one in any case (R4.3).

I21 to I28 are mechanism invariants of M-mode and of the offline
derivation. None is a policy statement, and none is an obligation of
Part 3's analyses, which do not see profiles.

**The control hart's own invariants.** I17 and I18, the routing of
typed bytes and the form of printed lines, are kept by HS-mode code,
the control hart's last; so is the rendering of the log (I19). The
boundary does not keep them for a control hart that is breached. R4.3
lists that as an allowed effect, and R4.5 as a limit on evidence.

### R4.3 Part 1, threat model: the breached hart

The threat model's lists gain the following. Nothing in them is removed
or reworded.

- **Attackers** (added). **HS-mode code on a hart, after that hart's
  activation** (S3-D's D26, on the human's direction to "assume
  breach").
  - It may execute any instruction that HS mode allows, write any
    register that HS mode can write, access any address, and make any
    firmware call with any argument.
  - Several harts may be breached at once, and may cooperate with each
    other and with any VS domain.
  - How a hart comes to be breached is not modelled. The expected
    routes are these: a flaw in a hart's trap path that its guest
    exploits; for any hart, a flaw in what reads a mailbox that a
    breached hart writes; and, for the control hart, a flaw in what
    reads console input, which a breached hart that has the console
    write can shape through the operator's terminal.
  - **Containment is required against such code on a confined hart.**
    Against such code on a hart that a configuration leaves
    unconfined, nothing is contained: that code is named in the
    trusted computing base of that configuration (R4.4). That is a
    limit of the configuration, and not a change of the attacker.
- **How this reads with the accepted text.**
  - The accepted list begins "Every non-Beryllium domain, from its
    first instruction". That stands. The new attacker is Beryllium's
    own code, on one hart, after a point in time.
  - Revision 3 says: "Code able to alter the monitor is outside the
    model's attackers as before (the deferred "firmware-hostile
    launch")". That stands.
    - In an image with the boundary, the new attacker on a confined
      hart alters the monitor's behaviour on its own hart and no more.
      It is not code able to alter the monitor in Revision 3's sense.
    - On a hart that a configuration leaves unconfined, the new
      attacker is such code. As in Revision 3, its effect is named and
      not defended, and R4.4 names that code in the trusted computing
      base.
    - Boot code writes the log page and the registers before any
      hart's activation (I19), and I22 (d) keeps every confined hart
      from writing them later. What a breached control hart prints of
      them is evidence of nothing.
  - Boot code on a hart before its activation is not an attacker, and
    its inputs stay untrusted and checked, as today. M-mode's firmware
    and the offline tools are not attackers either (R4.4).
- **Assets** (added): the profiles as installed; the descriptor;
  M-mode's own state. Where the descriptor lies at run time decides
  which clause protects it: I22 (f) in M-mode's memory, and I22 (d)
  among the monitor's constants.
- **Allowed effects** (added). A breached hart may:
  - do whatever its own VS domain may do, and read or damage that VS
    domain;
  - write anything into the mailboxes that it writes, or nothing;
  - stop, spin, or withhold its work;
  - make any firmware call that its role's allowlist keeps. Where that
    includes the system reset, it can end the boot;
  - falsify what it reports. A breached VS-domain hart's ring records
    still reach the console only through the control hart, under its
    VS domain's prefix (I18). Where its role's allowlist keeps the
    firmware's console write, as today's failure path has it, the hart
    can also print anything directly. That bypasses I18: it can forge
    any line, and it can send bytes that make the operator's terminal
    answer into the VS domain that has the focus.

  A breached control hart may also:
  - pause or terminate a VS domain. The accepted model already allows
    management that much: it "may pause, starve, or terminate
    protected work";
  - use the console path as the operator can: see every line that any
    VS domain prints, and supply input to any VS domain whose sealed
    configuration grants console input. Where that VS domain's guest
    offers a shell on its console, it can do whatever that shell can;
  - print anything. The console is then evidence of no hart's
    containment.

  None of these lets a breached, confined hart itself read or write
  another VS domain's memory, or a declared page beyond the rights of
  I22 (a). What it sends reaches another VS domain only as that VS
  domain's console input, under its grant, or through a further breach
  (the hub, above).
- **Required containment** (added). A breached, confined hart does not
  read or write:
  - another VS domain's memory;
  - a declared page beyond its own VS domain's rights, the secret page
    among them;
  - another hart's private state;
  - M-mode's memory.

  It does not write the monitor's code or constants, the sealed
  configuration, a G-stage table, or the log page or its registers. It
  does not change its own profile or another hart's. A breached,
  confined control hart reads and writes no VS domain's memory at all.

  S3-D.1 lists what a boundary would protect, "so that no later text
  overstates it". Four items here are not in that list:
  - the monitor's code and constants. Unless they are protected, none
    of S3-D.1's items holds: a hart that could rewrite them would run
    as every hart;
  - the log page and its registers, from I19;
  - the profiles, from S3-D's stop (n);
  - M-mode's memory, which S3-D.1 leaves "the firmware's to protect".
- **Deferred, unchanged**, with three named additions:
  - cache and timing channels between harts, which the boundary does
    nothing against;
  - a defective or hostile M-mode firmware, and a boot chain that
    delivers another firmware or another descriptor. The firmware's
    role grows with this revision. Its trust is stated in R4.4, and it
    is not defended;
  - the board's other execution contexts, and whatever addresses
    memory without one, such as a device that masters the bus or the
    debug module, until an inventory shows what they can reach.

### R4.4 Part 1, trusted computing base: what the boundary trusts

The TCB table gains the rows below. The existing rows are unchanged.
Revision 3's distinction applies: the **running TCB** is trusted for
containment, and the **offline evidence TCB** for the evidence.

| Trusted element | Evidence class today | Note |
| --- | --- | --- |
| The M-mode firmware that installs and enforces the profiles, serves the firmware calls, and handles a forbidden access | none for this role. The accepted row for the board's firmware describes MVP 1.0, which asks no boundary of it | running TCB. S3-D.5: a boundary against a breached hart needs a firmware build of the project's own. M11's plan fixes its language rules, licence, location, and build first (S3-D's stop (m)) |
| The hardware's physical memory protection as the board implements it: the number of rules, their grain, their locking, and their application to every access of I21, the implicit accesses of both translation stages among them | none. The characterization's emulation only; the board's is unread | running TCB |
| The monitor's boot code on each hart, before that hart's activation | as the monitor's code today | running TCB of every profile: until the hart is confined, it runs with the hart's boot access |
| HS-mode code on a hart of the monitor that a configuration leaves unconfined | as the monitor's code today | running TCB of every profile in that configuration. S3-D's attacker on that hart is not contained (R4.3) |
| The descriptor's generator | none; M11 | running TCB, by its output: a profile that is too wide weakens containment with no sign at run time |
| The offline check of the descriptor against the image | none; M11 | offline evidence TCB. It has to be independent of the generator |
| The boot chain that delivers the firmware and the descriptor | assumed. No stage of it is measured (Revision 3, R3.3), and the state of the board's signature checks is unread | running TCB |
| The board's other execution contexts. By the vendor's documents and published source: a second cluster of eight harts without the H extension, and cores that run the vendor's real-time firmware | none. Whether this board runs them, and what they can reach, is not established (S3-D.5) | named here under I28, with that evidence once an inventory, or a rule that M-mode holds, gives it |

Two accepted rows are read with this revision, and neither is edited.

- **"The Beryllium HS code of the configuration in use".** For an
  image with the boundary, this row is read by phase. Boot code before
  a hart's activation is trusted as before. The HS-mode code of a
  confined hart after its activation stays trusted for these: the
  containment of its own guest by the G-stage; its own VS domain's
  protection from the hart itself; availability; what it reports; and,
  on the control hart, I17, I18, and the rendering of the log. It is
  no longer trusted for the containment that R4.3 adds.
- **"The sealed manifest's protection inside HS".** For an image with
  the boundary, the row's open obligation is I22 (d) for a confined
  hart. Its evidence class stays "none" until M11's result is
  accepted.

Revision 3 defines the running TCB as "HS code and the hardware and
firmware beneath it, trusted for the claim's containment". For the
containment that R4.3 adds, the running TCB is the rows above, with
the accepted rows for the hardware and the toolchains. It does not
include the HS-mode code of a confined hart after its activation. The
TCB still does not include the guests.

### R4.5 Scope, and what this revision does not say

- **The readings.** This revision reads four accepted texts and edits
  none of them: S3-D.1's "the control hart's boot barrier" (the terms);
  two rows of the trusted computing base (R4.4); and Revision 3's
  sentence on code able to alter the monitor (R4.3). D26's attacker is
  taken as written, and containment is required for confined harts.
- **Images without the boundary.** MVP 1.0's images, and any image
  built with the boundary off, keep the accepted threat model: the
  monitor's HS-mode code is trusted whole, and I21 to I28 are not
  asserted of them. MVP 1.0's claim is unchanged.
- **No mechanism, and no firmware.** "M-mode" and "profile" are all
  that this text assumes. Whether profiles are PMP rules or OpenSBI
  domains, how many rules a profile takes, and which firmware installs
  them is for M11's plan. Memory protection tables are M12's lane, and
  M11-R10 asks that the descriptor carry over to them unchanged. The
  accepted claim boundary says that this document does not "select a
  runtime mechanism, a protected service, an SBI or firmware
  boundary"; that stays so.
- **Not proved.** The invariants are specification. Nothing here is a
  theorem of the abstract model or of M8's stage 1. Stage 1's premises
  on hart start and on IPIs may not survive M11's design; M11-R9's
  proof-impact review decides what is re-read and re-proved.
- **Parts 2 to 7 are unchanged.** Profiles are outside the policy's
  notation and its analyses, and "Nothing in this pipeline runs in HS"
  stays true of the descriptor's derivation too. This revision
  evaluates neither trigger of Part 5. If M11's design adds a decision
  at run time, M11's plan evaluates them.
- **No measurement is added.** The descriptor has an identity that a
  measurement could bind (M11-R10). Whether and where it is measured
  is for M11's plan. I19 and I20 are unchanged.
- **No device and no injected-interrupt object.** Part 2 adds notation
  classes for "Device, DMA, IOMMU, or interrupt-injection objects"
  when the first of them exists; none does. Part 1's `interrupt` row
  is unchanged. Meanwhile I22 (c) says what a profile may hold of a
  device, and I27 (a) keeps whatever M-mode does about interrupts at a
  hart's request to the allowlist. What addresses memory without an
  execution context is outside I28, as devices are outside the
  accepted model.
- **Availability and side channels** are outside it, as they are
  outside the accepted model.
- **Evidence.** What a breached hart prints proves nothing about that
  hart, and what a breached control hart prints proves nothing about
  any hart. What counts as evidence of containment is for M11's plan,
  under M11-R6 and M11-R7.

### R4.6 What this revision does not change

The text above this section is byte-identical to its accepted form:
Parts 1 to 7, Revisions 1 to 3, the decision record, and the status
records. This section is appended. No code, no model file, no claim
text, and no accepted plan changes with it.

One accepted document does change, by one pin. Appending this section
changes this file's SHA-256. The claim ledger records that value as
evidence for its row on the launch gate (I19 and I20), and the
ledger's check compares it. The same commit therefore refreshes that
pin and its note. S3-D did not authorize a change to the ledger: the
refresh is here for the responsible human's decision with the
revision. The row's claim, methods, and non-claim are unchanged.

### Status record addendum (Revision 4)

```text
security_model_v1_revision_4=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
security_model_v1_revision_4_base=b332f65854a20c641a251852ee8b991f84515120
security_model_v1_revision_4_plan=mvp-plan.md;Plan-revision-S3-D;D26;M11-R8;before-the-M11-plan
security_model_v1_revision_4_admitted_by=mvp-plan.md-S3-D-stop-condition-1-amended-by-name
security_model_v1_revision_4_classes_added=profile;shared_region;descriptor;firmware_call;hart-instances-role-and-confinement
security_model_v1_revision_4_invariants_added=I21,I22,I23,I24,I25,I26,I27,I28
security_model_v1_revision_4_threat_model_added=attacker-HS-mode-code-on-a-hart-after-its-activation;containment-required-for-confined-harts;assets-profiles-descriptor-M-mode-state;allowed-effects-own-VS-domain-mailboxes-availability-firmware-calls-of-the-allowlist-console-path-evidence;containment-other-VS-domains-declared-pages-other-harts-M-mode-monitor-code-and-constants-sealed-configuration-G-stage-tables-log-page-and-registers-profiles;deferred-side-channels-firmware-and-boot-chain-other-contexts
security_model_v1_revision_4_tcb_rows_added=M-mode-firmware;physical-memory-protection-hardware;boot-code-before-activation;unconfined-HS-mode-code;descriptor-generator;offline-check-of-the-descriptor;boot-chain;other-execution-contexts
security_model_v1_revision_4_readings=control-hart-activation-as-the-end-of-its-boot-work-the-plans'-sense-of-the-boot-barrier;the-HS-code-TCB-row-by-phase;the-sealed-manifest-TCB-row-as-I22d;Revision-3's-code-able-to-alter-the-monitor
security_model_v1_revision_4_scope=mvp-static-binding-configurations-built-with-the-boundary;images-without-it-keep-the-accepted-threat-model
security_model_v1_revision_4_design=not-selected;mechanism-neutral;chosen-in-the-M11-plan
security_model_v1_revision_4_accepted_text_changed=none-in-this-document;the-claim-ledger's-pin-of-this-file-and-its-note-in-the-same-commit-for-the-responsible-human's-decision
security_model_v1_revision_4_code_change=none
security_model_v1_revision_4_model_change=none
security_model_v1_revision_4_claim_change=none
```
