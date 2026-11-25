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

## Revision 5 (2026-11-25): the device and DMA object model

**Status.** Proposed by the commit that adds this section, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If the commit that adds
this section is on the public `main` with the responsible human's
`Signed-off-by`, this revision is accepted as written. Any other answer
needs a revised commit before the sign-off. The signed commit differs
from the one reviewed only by that line and its committer date; if it
must be rebased first, the internal record says so. The project's
internal records keep both commit IDs and the instruction. This
document's decision record, above, is not updated for a revision
accepted this way: the signed commit on the public `main` is the
record.

This section is the device and DMA object model: the second of MVP
2.0's seven steps in the [MVP plan](mvp-plan.md) (S3-C.2, step (2)). It
is work package M14-2 of the accepted [M14 plan](mvp-m14-plan.md),
whose acceptance amended the MVP plan's stop condition 1 by name: "its
exception list gains the additive security model v1 Revision 5, the
device and DMA object model, which goes to the responsible human as its
own exact commit". It comes before the plan of step (3), the device
path.

- It is appended to this document's accepted text, which it quotes and
  does not edit. Every change below is an addition to a named part, or
  a reading of an accepted sentence; R5.10 lists the readings. Parts 1
  to 7, Revisions 1 to 4, and the analyses, instances, claims, and
  status records above keep their text. One pin of the claim ledger
  changes with it (R5.11).
- To Part 1 it adds six object classes, ten invariants, three
  attackers, and nine rows of the trusted computing base. To Part 2 it
  adds one class, one kind of subject, and a fourth instance, worked by
  hand. To Part 3 it adds five analyses, and says how the accepted ones
  read once a device is a subject. It answers the two questions that
  the [synthesis](he-to-be-synthesis.md) handed forward as H06 and H07,
  where a device makes them concrete.
- It selects no device, no mechanism, and nobody to program one. It
  says what any device path has to provide, in terms that do not depend
  on the mechanism. The plan of step (3) chooses, on the facts.
- It implements, runs, proves, and tests nothing. Its invariants are
  specification, asserted of no image: no configuration gives a VS
  domain a device.

**Terms.** S3-D.2's, Revision 4's, and these.

- A **device** is a component of the platform that software drives
  through registers of its own, which the address map has or which are
  reached through another device, as a chip's on a serial bus are. It
  may also have interrupt sources; an identity as a bus master;
  **controls**, wherever their registers lie (its reset, its clocks,
  its power, its pins); and **persistent state**, which survives a
  system reset: its own firmware, its non-volatile memory, and, for a
  storage device, its media.
- A **bus master**, or **master**, is a device that issues requests of
  its own, reads and writes among them, that no hart makes. A request
  that a device passes on from a hart is the device's own where the
  device chooses its address. Where state of I32 fixes the address, as
  for a bridge's window or a configuration window, it is the hart's
  access to the registers behind (I30 (b)'s reading).
- A device's **holder** is whatever drives it: a VS domain; the
  monitor, in a hart's role; the firmware below the monitor; or an
  execution context that no configuration of the project's controls.
  Its **owner** is a holder that is a VS domain: the one to which the
  sealed configuration assigns the device.
- An **assignment unit**, or **unit**, is the smallest set of devices
  that can be assigned to one owner (I30). It is **exposed** from the
  moment that its owner can reach its registers. **Pass-through** means
  that a VS domain drives the device's own registers.
- A master's **reach** is the set of physical extents, memory and
  registers alike, with rights, that its own requests can read or
  write. Its **recorded reach** is the memory that the sealed
  configuration gives it, with rights. An **enforcing element** is
  hardware between a master and what it addresses that refuses a
  request, with the state that it is given. A master's requests may
  pass one such element or several. A master's **identity** is
  whatever an enforcing element attributes a request to. A master may
  be able to claim more than one: that depends on the device, on its
  place on the bus, on state that sets an identity, and on whether
  anything between it and an enforcing element checks one. A master is
  **confined** when every request that it issues passes enforcing
  elements that together apply its recorded reach to it: under every
  identity that it can claim, to every address, and whatever the
  request says of itself (I31, I32).
- A **message-signalled interrupt** (MSI) is an interrupt that a device
  raises by a write of its own. An **interrupt file** is the term of
  the RISC-V Advanced Interrupt Architecture (AIA) for the state in
  which such a write makes an interrupt pending: of one hart at one
  privilege level, or of one virtual hart. An APLIC is the AIA's
  controller for wired interrupts, which it may forward as MSIs.
- A **route** is the state, outside the unit's own registers, that
  decides where an interrupt of one source is delivered. Its **delivery
  point** is where that interrupt first becomes pending in an interrupt
  file, or in a controller's structure for a hart, on its way to the
  VS domain that is to receive it: an interrupt file of a controller,
  which the configuration gives that VS domain; or, where the monitor
  takes the interrupt on that VS domain's own hart and makes it
  pending for the VS domain, the interrupt file, or the controller's
  structure for that hart, at which the monitor takes it. Where an
  element stores an interrupt in a file that it keeps in memory, and
  gives notice of it by a message of its own, the delivery point is
  that file together with the place where the monitor takes the
  notice.
- A device is **quiesced** when no request of its, issued before or
  after, reads or changes anything, and no interrupt of its is
  delivered; and none of these can change that: a VS domain; a
  confined hart whose profile does not include the device's registers;
  a confined master. It is so because it is stopped, or because
  enforcing elements refuse its every request and no route delivers
  its interrupts.
- A **control operation** is an act on a device through one of its
  controls. A **boot source** is a unit from which the boot chain, or
  the monitor's boot code, reads anything that it runs or trusts
  without a check against a value that the unit's holder cannot
  change.
- The **platform description** is an account of the platform, built
  offline, as the implementation plan's "normalized platform
  descriptor" is to be.
- A configuration's **limit** is the part of a claim about it that
  says what the claim does not cover, as the boundary's claim has its
  required limit (`mvp/docs/claim-boundary.md`). The responsible human
  accepts it with the claim. To be named in it contains nothing.

A unit is "assigned to" its owner, a rule is "enforced by" an element,
and a profile "includes" an extent. Of an IOMMU's state for one device
this text uses the IOMMU specification's words, "device context" among
them. An IOMMU, and an IOPMP (I/O physical memory protection), appear
below only as what a platform may offer, and in facts. Neither is a
term of an invariant.

**Facts.** *Fact* marks what a source shows. The sources:

- M13's record of one K3 COM260 board, and M13's result, as the public
  `main` has them at `d6d5492c` (`planning/k3-com260-devices.md`, by
  its row numbers; `planning/mvp-m13-result.md`, section 3). They are
  diagnostic: facts from the vendor's documents and sources, and from
  one board, each row with its class. A *probe* row is one boot through
  that board's resident boot chain, and the record's lists of what
  devices share say "found so far". Nothing below rests on what the
  record marks "not established". The results of two of M13's probes
  are held under the M13 plan's rule 10: this revision does not rest on
  them, says of them only what M13's pages say, and reads the same
  whatever they show.
- The specifications at M13's pins: the RISC-V IOMMU specification,
  release `20260222`; the Advanced Interrupt Architecture (AIA) `1.0`,
  release `20250312`; the RISC-V IOPMP specification `v0.85`, a draft;
  and the ISA manual's cache-block chapter at `3142f66f`. Each is cited
  by its source file and section title.
- Upstream Linux at `v7.3` (`c03c1a14`). The PCI Express specification
  is not an open document, so a statement about PCI devices is written
  as what a source does, upstream Linux's or the emulator's, and cites
  it.
- The emulated machine of the project's gates: QEMU's `virt`, read from
  upstream's source and documentation at the tag `v10.2.2`
  (`f8ed8165`). The gates run a distribution's build of that release,
  whose patches and build configuration were not read. Nothing was
  run.
- Two precedents, each read for what it makes an object, and neither
  copied: seL4 at its release `17.0.0` (`62e345c2`), and capDL at
  `55d2ef24`.
- The MVP line at this revision's base, `d0ec2aee`, which this revision
  does not change.

### R5.1 Part 1, object classes: the device, the unit, the reach, the route, the control, and the platform description

Part 1's table gains six rows, and two accepted rows grow: each in its
instances column, and the `interrupt` row also in where its authority
is recorded. The other rows are unchanged.

| Class | Instances today | Authority recorded in |
| --- | --- | --- |
| `device` (new) | none that a VS domain or the monitor drives. *Fact*: "The monitor touches no device. Its console and its reset go through firmware calls" (the M11 plan, F17) | the platform description, for what exists and what it shares; the manifest's assignment record, for whose it is |
| `unit` (new) | none | the platform description, for the relations that close a unit (I30); the manifest's assignment record |
| `reach` (new) | none. *Fact*: M11's boundary confines harts, the monitor's three, each to a physical access profile, and its claim speaks of no other bus master (`mvp/docs/claim-boundary.md`) | the manifest's reach record for each master of an assigned unit; the state that enforcing elements are given from it |
| `route` (new) | none | the manifest's route record for each interrupt source of an assigned unit; the state derived from it |
| `control` (new) | none that a VS domain may ask for. *Fact*: the one such operation today is the system reset, a firmware call (R4.1) | the manifest's grant of an operation on a unit to that unit's owner; the element that performs it |
| `platform_description` (new) | none | itself: built offline, immutable from the build on, with an identity. It grants nothing |
| `interrupt` (instances and authority columns, added) | … and, once a unit is assigned, each interrupt source of that unit | for such a source, the route; the accepted entry stands for the monitor's own timer interrupt |
| `descriptor` (instances column, added) | … and, for a hart whose profile includes a unit's registers, that unit's entry in the descriptor's `devices` section, and its sources in `interrupts` (the M11 plan, D-3) | unchanged |

Four things about these classes.

- **Identifiers are still not authority** (S1 H03). A master's
  identity, an interrupt's number, the address that a device's
  registers give for a message-signalled interrupt, and a device's
  place on a bus each name something. Only the sealed configuration,
  and the state derived from it that an element enforces, give a
  device or its holder anything.
- **The platform description grants nothing.** The implementation plan
  says of its hardware input that it "Does not grant domain authority
  merely because a device or memory node exists". The description says
  what exists, what it shares, and what is not established. The
  manifest says whose a unit is.
- **A unit is mechanism and policy both.** Its closure is a fact of the
  platform, and of which of the platform's interrupt sources the
  configuration routes (I30 (b)). Its assignment, its reach, and its
  routes are grants of the policy (R5.6), which Part 3's analyses see
  (R5.7). A profile, by contrast, "is not policy" (R4.1).
- **No part of a device is assigned apart from the rest.** Its
  interrupt sources, its identities, and its registers go together, to
  its unit's one holder (I30), but for the registers that I32 and I34
  keep from every holder. Its controls are not assigned apart: an
  owner has one in its mappings only where I34 (a) allows, and
  otherwise asks for a control operation (I34 (b)).

### R5.2 Part 1, invariants: I29 to I38

Part 1's invariant table gains ten rows after Revision 4's I28.

- **Scope.** Configurations in which the sealed configuration assigns a
  unit to a VS domain. None exists; the plan of step (3), or a later
  plan, defines the first. I29 to I38 are not asserted of an image
  without one: there, devices are outside the model, as R4.5 says, and
  MVP 1.0's claim and the boundary's claim, with their limits, are
  unchanged.
- **A unit whose holder is the monitor.** A unit that the monitor
  itself drives, in a hart's role, is within I29, I30, and I38 alone.
  This revision gives such a unit no master, since I31 (c) would leave
  one nothing to reach. Its interrupts, its controls, its lifecycle,
  and the analyses that would check it are for the plan that first
  gives the monitor a device.
- **Fixed-instance status:** "not applicable": the fixed profile has no
  device, and no Model 0.1 or 0.2 obligation exists.
- **Evidence:** none. R5.3 says what would show each. Until a device
  path's result is accepted, nothing here is claimed of any image.

| # | Invariant | Fixed-instance obligation | Status beyond the fixed instance |
| --- | --- | --- | --- |
| I29 | **Every device and every bus master is accounted for.** Every device that the platform description lists has one holder, or none, and a device with none is quiesced. Every bus master is one of four things: confined; quiesced; a master whose holder the trusted computing base names, with what the evidence shows of what it can reach; or a master that the configuration's limit names as not confined | not applicable | none; step (3). I28 does this for execution contexts, and R4.5 left out "What addresses memory without an execution context"; this takes it up |
| I30 | **What is assigned is a unit, whole.** A unit is closed: with a device it has every device that cannot be told apart or kept apart from it (clauses (a) to (c)). All of a unit's devices, with their interrupt sources, their identities, and the registers that I32 and I34 leave a holder, have the unit's one holder. No device is in two units. A unit is assigned, to a VS domain or to the monitor in a hart's role, only where clause (d) allows | not applicable | none; step (3) |
| I31 | **Reach.** A confined master reads or writes only what its recorded reach allows, with the reach's rights; writes a message-signalled interrupt only where clause (d) allows; and reaches a device's registers only where clause (e) allows. That is so for every request that it issues, of every kind and under every identity that it can claim, whatever its holder writes to its registers and whatever the device itself does. A request, or a part of one, that this forbids reads nothing and changes nothing | not applicable | none; step (3). I21 says the same of a hart |
| I32 | **Where confinement comes from, and what protects it.** The state that decides what a master's requests reach is derived from the sealed configuration and the platform description; is installed before the unit's exposure; takes nothing from a VS domain, a device, or HS-mode code on a confined hart; and is out of the reach of every VS domain, confined master, and confined hart: clauses (a) to (d) | not applicable | none; step (3). I24 and I22 (d) say the like of a profile |
| I33 | **Interrupts.** Every interrupt of a source of an assigned unit is delivered to the unit's owner, at the delivery point of its route, or it is not delivered: clauses (a) to (f) | not applicable | none; step (3). The MVP plan's stop condition 3 names "guest-visible interrupt injection beyond each domain's own timer"; the plan of step (3) names it for the responsible human's decision |
| I34 | **Controls, and every other authority without a mapping.** A control operation, and anything else that is done for an owner for its unit's sake, is performed by an element of the trusted computing base, only as the sealed configuration grants it, and only on that owner's own unit and memory: clauses (a) to (d) | not applicable | none; step (3) |
| I35 | **Order: the first handoff.** Confinement comes before exposure: clauses (a) to (e) | not applicable | none; step (3). I26 says the same of a hart |
| I36 | **A unit follows its owner.** Its assignment does not change within a boot, and it is quiesced whenever its owner does not run: clauses (a) to (d) | not applicable | none; step (3) for (a), (b), and (d); for (c), the plan that builds a restart |
| I37 | **Persistent state, and the next boot.** What a unit keeps across a system reset is its holder's to change. No VS domain is given a boot source. What a unit's masters do between a system reset and the next boot's handoff is bounded by the platform's reset, or the limit names it: clauses (a) to (c) | not applicable | none; step (3) |
| I38 | **A hart whose profile includes a unit's registers.** A profile includes them only where the descriptor assigns the unit to that hart's role (I22 (c)). It does so only for a unit whose owner is the VS domain bound to that hart, or for a unit without a master whose holder is the monitor in that hart's role. Where a VS domain owns the unit, every master of it is confined, its recorded reach allows no extent and no right beyond that profile, and the unit's interrupts are delivered on that hart alone | not applicable | none; step (3). It reads I22 (c), whose "No scenario assigns one" is still so |

**The clauses.**

| Clause | Text |
| --- | --- |
| I30 (a) | **They cannot be told apart.** Two devices are in one unit if, at an enforcing element that is to confine them, a request of one can carry an identity that the other can claim; if a request of one can reach the other's registers, or a device to which the other passes requests on, without passing those elements; or if one can see the other's requests, or the answers to them, other than to pass them on, to refuse them, or to record them, as state of I32 directs. Each is judged under the state of I32 as the configuration installs it (I32 (a), (b)), and what that state cannot settle joins. That a master's requests reach memory without passing an element joins it to nothing: it is then a master that is not confined (I29) |
| I30 (b) | **What a holder is given cannot be divided.** Two devices are in one unit if an extent that has registers of one has registers of the other, at the grain at which a holder is given registers: the G-stage's page for a VS domain, and a profile's grain for a hart. Likewise if one is driven through registers of the other on any of its paths, as a chip on a serial bus is driven through the bus's controller; if both drive one bus or one medium inside the platform, other than the interconnect that carries requests to memory and to registers, on which each can see or change what the other sends; if one moves data for the other with requests of its own; if both can raise one interrupt source that has a route; or if an interrupt of one that has a route passes through the other, and a holder of the other can stop it or change it by an act that is not on state of I32 or on a control, which I32 and I34 keep from every owner |
| I30 (c) | **What the lifecycle needs cannot be divided.** Two devices are in one unit if the act that the configuration uses on one for I35 or I36, to quiesce it, to clear it, or to make it work again, changes state that the other depends on: a reset or a clock gate that serves both, or a physical-layer transceiver (PHY) that both use at once |
| I30 (d) | **A unit that cannot be assigned.** A unit is not assigned, to a VS domain or to the monitor, if a second holder drives a device of it once the boot chain has handed the unit on; or if the platform description marks as not established a fact that (a) to (d), or I37 (b), needs, a device's holders and whether the unit is a boot source among them. Nor is it assigned to a VS domain if that description establishes no enforcing elements for a master of it; if, from then on, the monitor, the firmware, or another element of the trusted computing base drives a device of it, other than to do for the unit what I32 to I36 have it do, or depends on one; or if it is a boot source (I37 (b)). A unit that has a master is not assigned to the monitor |
| I31 (a) | A master's recorded reach is in the sealed configuration. A master with none has an empty one |
| I31 (b) | The recorded reach allows no frame and no right beyond what the sealed configuration's mappings give the unit's owner. It may allow less, down to nothing. So it allows nothing of another VS domain's private memory, and no right on a declared page beyond its owner's |
| I31 (c) | No recorded reach includes the monitor's memory or M-mode's; a device's registers; the state of I32; or an interrupt file |
| I31 (d) | A message-signalled interrupt is a write by the master, and no part of its reach. The enforcing elements let it pass only to the delivery point of a route of the master's own unit, and any other request of the master's that reaches that delivery point reads nothing and changes nothing |
| I31 (e) | Clause (d)'s write apart, a master's request reaches a device's registers only if they are registers of its own unit that I32 and I34 (a) let its owner's mappings include, and the platform description says that the master's work needs them, as a controller that moves data for a device needs that device's; and only where everything in the extent that the elements let such a request reach belongs to that unit, and none of it is state of I32. That is no part of its recorded reach either |
| I32 (a) | The state is derived from the sealed configuration and the platform description, and what is in force can be checked against them |
| I32 (b) | It is installed before the unit's exposure: by boot code; by an element below HS mode; or by the monitor on a hart that the configuration leaves unconfined, which its trusted computing base then names (R4.4). In deriving or installing it, nothing takes an extent, an identity, or a right from a VS domain, from a device, or from HS-mode code on a confined hart after that hart's activation |
| I32 (c) | Nothing that a VS domain, a confined master, a quiesced device, or a confined hart can do widens what that state allows, or stops its enforcement. No VS domain's mappings and no recorded reach include it, and no profile allows a confined hart to write it. A master that is neither confined nor quiesced is outside this clause: where it can reach this state, what names it says so (I29) |
| I32 (d) | The state is everything that bounds what a master's requests reach: an enforcing element's registers, its tables that bound a reach, whatever else it reads in memory that directs what it does or where it writes, and what it has cached of them; whatever decides whether a request passes an element at all, or can carry another master's identity; whatever sets a master's identity, or makes a master; whatever decides where a device's registers are decoded; the state that routes an interrupt; and every place where an element writes of its own accord, its records and its own interrupts among them. A table that can only narrow a reach inside that bound is not this state |
| I33 (a) | No VS domain receives an interrupt of a unit's source unless that unit is its own. This says nothing of an interrupt that is no device's: the MVP plan's stop condition 3 still governs any beyond a VS domain's own timer |
| I33 (b) | No hart other than the one that the owner is bound to takes a trap, or does any work, for a unit's interrupt |
| I33 (c) | On that hart, a unit's interrupts do not keep the monitor from its own timer tick, nor from what it does on that tick |
| I33 (d) | Whatever the owner writes to its devices, and whatever a device does, an interrupt of the unit arrives at its delivery point or nowhere |
| I33 (e) | What the monitor reads at a delivery point that a device can write is untrusted input (I9). It attributes an interrupt to the units that are routed there, never to a number that a device supplied, and a delivery point at which the monitor takes interrupts has nothing else that the monitor relies on |
| I33 (f) | What an enforcing element signals when it refuses a unit's requests goes to the hart that the configuration names for it, and does not keep that hart from its other work at a rate that the unit chooses |
| I34 (a) | No VS domain's mappings, and no confined hart's profile, include a register that has a control, unless everything in that register's extent belongs to the holder's own unit and none of it is state of I32 |
| I34 (b) | Otherwise a control operation, or an access to a register of the unit that clause (a) or I32 keeps from the owner's mappings, is performed for the owner, at its request: by the monitor on a hart that is not confined, by an element below HS mode, or by an execution context that such an element asks. It is performed only if the sealed configuration grants it, on that unit, to that owner; only if it acts on that unit alone; and only if it leaves what the state of I32 allows as it was. A grant of an access names the registers, and the fields in them, that the access may read and may change. By the platform description, all are the unit's own, and none that it may change is a control or state of I32: an act through a control is a control operation, whichever register has the control. Where a control operation changes state of I32 on the way, as a reset can, whatever performs it installs that state again before the unit's registers are decoded again, and before any request of the unit's masters can read or change anything. Whatever performs an operation or an access knows the owner by the hart that asks, and the unit and the grant by the sealed configuration. From the request it takes which of the granted operations and accesses is asked for, and what an access is to write, and nothing else from HS-mode code on a confined hart after that hart's activation. Where M-mode performs it for a confined hart, it is a call of that hart's allowlist (I27). A refused request changes nothing |
| I34 (c) | A cache-block operation, by an owner or for it, acts only on memory that the owner's mappings allow, with the right that the operation needs. It makes nothing that another party wrote be lost, and brings back nothing that was cleared: so an owner's invalidate traps, or acts as a flush, wherever another party can write the block, and wherever the monitor cleared it and has not cleaned or flushed it since |
| I34 (d) | No authority over a device exists by default. What a master that is not confined can do to memory or to an interrupt file, and what a holder that no configuration of the project's controls can do to a device, only because nothing refuses it, is not authority: it is an effect, and I29 has it named. What nothing refuses an owner, or a confined master, is no such effect: it breaks I31 to I34 |
| I35 (a) | The monitor's boot code quiesces a unit before it does anything else with it. Before any VS domain's first guest entry, it has quiesced every assigned unit, and every master that the configuration records as quiesced is so (I29). Until then a device is as the boot chain left it, and the boot chain is trusted for that state (R5.5) |
| I35 (b) | Before the unit is exposed, nothing of what came before is left: no request in flight or queued; no interrupt pending for a source of it, at a controller or on its way to a delivery point; nothing pending at a delivery point of its routes, whatever raised it; and no data of an earlier holder's that the owner could read from the unit, or from the memory that its masters can reach |
| I35 (c) | Before the unit is exposed, and before any request of a master of it can read or change anything again, each master is confined and each route is installed (I31 to I33) |
| I35 (d) | A master is not coherent with the harts where a request that it can issue is not, as it reaches memory: by what the master is, by what the request says of itself, by what the memory that it addresses is, or by what an element makes of the request, whether from its own state or from a table that an owner may write. For memory that such a master can read, whatever the monitor wrote or cleared is visible to the master before any request of it can read it |
| I35 (e) | Boot code does (b) to (d) for a unit before its owner's first guest entry. If a unit cannot be quiesced, no VS domain is entered. If a later step cannot be completed, the unit stays quiesced. Either way the configuration fails closed, as a failed validation does (I6) |
| I36 (a) | Within one boot, a unit's assignment, its registers' extents, its recorded reach, and its routes do not change |
| I36 (b) | From I35 (a) on, the unit is quiesced whenever its owner does not run: until the owner's first guest entry, and after its pause, its termination, its shutdown, or a failure of it. That is so against everything but Revision 4's attacker on the hart that the owner is bound to (R5.4). The monitor reports a pause or a termination as done only once the unit is quiesced. The unit stays assigned to that owner |
| I36 (c) | A restart of an owner with its unit kept, where a plan builds one, does to the unit what I35 does, in I35's order: quiesced; reset and cleared, so that nothing of the run before is left; and exposed again only under the same recorded reach and the same routes, derived again from the same sealed configuration. Between the two runs the unit is quiesced |
| I36 (d) | A system reset ends the assignment for that boot. The next boot's handoff starts again from the state in which the boot chain leaves the unit (I35). No interrupt that was raised or left pending before the reset reaches a VS domain: a controller's reset need not clear one, so the next boot does (I35 (b)). What a unit's masters do between the reset and that handoff is I37 (c)'s |
| I37 (a) | A unit's persistent state is its holder's to change. The model promises nothing of what it has |
| I37 (b) | A boot source is assigned to no VS domain |
| I37 (c) | From a system reset until the next boot's code has quiesced a unit (I35 (a)), nothing that the project controls contains the unit's devices. They are the second attacker of R5.4, as every device is, with whatever the reset left in them: requests in flight, what was written to their registers, and the persistent state that an owner left. Whether a master of the unit reads or changes anything in that interval is a fact of the platform: of what its reset leaves each master and each enforcing element doing. Where the platform description establishes that none does, the effect is contained. Where it does not, the configuration's limit names the unit's owner as able to change what a later boot runs |

**What does not close a unit.** Only what clauses (a) to (c) name
closes a unit. These, which devices often share, close none: a power
domain or a clock that stays as the configuration set it; pins that
only the configuration, or a holder that the trusted computing base
names, sets; a PHY that the configuration gives to one of several
devices, the others then having none; a register that has one device's
control beside another's, where whatever performs the operation
changes that device's bits alone (I34 (b)); and a bridge, a port, or a
controller that passes a unit's requests or its interrupts on as state
of I32 directs. Each is a control or state of I32, which I34 and I32
keep from every owner. Where the act that the configuration uses to
quiesce a unit, to clear it, or to make it work again changes state
that another device depends on, I30 (c) applies, and the unit grows.

**Readings that keep these exact.**

| Of | Reading |
| --- | --- |
| I29 | **It names; it does not contain.** A master of the third or the fourth kind is contained by nothing. Naming it bounds what a claim may say, as I28 does for a context. The name comes with what, by the platform description, the master can reach. Where that includes the monitor's memory or M-mode's, the state of I32, an interrupt file, or a quiesced device's registers or controls, every statement of this revision holds only while that master leaves them alone. An enforcing element's own accesses to the state of I32 are apart: R5.5's first row trusts the element for them. No such master is a VS domain's: I30 (d) keeps its unit from every VS domain, as the accepted threat model requires, "No domain may DMA or inject interrupts outside explicit ownership" (the implementation plan, "Required containment") |
| I29 | **A device with no holder.** For most devices of a platform, "is quiesced" rests on three things: that the boot chain left the device so (R5.5); that no mapping and no profile includes its registers or its controls; and that no master can write them but one that the configuration names. So nothing that the model contains wakes it |
| I29 | **An element is a master too.** *Fact*: an IOMMU "is a bus access initiator for its implicit accesses" (`iommu_intro.adoc`, "Placement and data flow"): it reads its tables and writes its records, and an element may signal by a message of its own. An interrupt controller that forwards a wired interrupt as a message issues a write of its own as well. Each is a master of the third kind, and where it writes of its own accord, as I32 (d) has it, is state of I32. A core that runs software of its own is no master here: it is an execution context, which I28 names, though a record may list it among the bus masters, as M13's does (D-38) |
| I30 | **A unit is a fact of one platform, at one grain, for the elements that its platform description names and the interrupt sources that its configuration routes.** The same device may be a unit by itself on one platform and one of several on another, and two devices that one element tells apart, another may not. *Fact*: on the K3 COM260 board that M13 read, by the manual's address map, registers of different devices share a 4 KiB page; and the reset bits and clock gates of each bus master that the board's Linux drives are on pages of registers that have other devices' controls (M13's result, section 3). *Fact*: for PCI devices, upstream Linux treats as inseparable a device and every device whose identity its requests can carry; every device below a port from which the path to the root does not have four access-control features enabled, where it counts as enabled one that a port's access-control capability does not implement, and a port without that capability does not pass, unless a device-specific entry in Linux says that it does; and the functions of one multifunction device that do not have them enabled (`pci_for_each_dma_alias()`, `drivers/pci/search.c`; `pci_device_group()`, `drivers/iommu/iommu.c`; `pci_acs_enabled()`, `drivers/pci/pci.c`; `pci_dev_specific_acs_enabled()`, `drivers/pci/quirks.c`). That is clause (a), as Linux judges it. Its pass-through code (`drivers/vfio/pci/vfio_pci_core.c`, `vfio_pci_intrs.c`) deals with a page that two functions' registers share, a shared wired interrupt, and a reset of several functions by other means than joining them |
| I30 (b) | **A device behind a controller.** A device that is reached by acts on a controller's own registers, as a chip on a serial bus is, is in one unit with every controller that reaches it, and so those controllers are in one unit with each other. Where a bus gives each device registers of its own in an extent of its own, as a configuration window does, those are that device's registers. The page rule applies to them, and I32 and I34 keep from the owner's mappings whichever of them has state of I32 or a control. What the owner's driver needs of those is done for it as I34 (b) has it: by an access, which changes neither, or by a control operation that the owner has a grant for |
| I31 | **It is about what a request reaches: not about its address, and not about what it says of itself.** A reach is stated in physical extents. Where an enforcing element translates a master's addresses, the translation is part of the state of I32, and it leads only into the recorded reach. What an element itself reads or writes to serve a master's request, other than its accesses to the state of I32, counts as that master's request, wherever it lands. A translation that a master keeps for itself is the master's, and bounds nothing. *Fact*: an IOMMU refuses a request that a master marks as already translated unless the master's device context allows such requests. Where it does, either "the translation process is complete", or, by a control of that context, the second stage still translates the address (`iommu_data_structures.adoc`, "Process to translate an IOVA" and "Translation control (`tc`)"). *Fact*: an IOMMU's tables may be the tables of a hart's own translation (`iommu_intro.adoc`, "Introduction"). Where they are, they have nothing that clauses (c) to (e) keep from the master |
| I31 | **A refused request.** It reads nothing and changes nothing that any party can reach. Where an element sends a refused request to a place of its own, that place is state of I32, and a refused read returns nothing that a refused write left there. *Fact*: by the manual, on the K3 board some elements answer a failed check from a default target, and "What data or error a master then receives is not stated" (A-26) |
| I31 (b) | **A declared page.** A recorded reach may include a declared page that its owner maps, with no right beyond the owner's. The page's other party attributes what it reads there to the owner, as before: what a VS domain's device writes, that VS domain wrote (R5.7) |
| I31 (c), (e) | **A device's registers.** A master that could write a device's registers would drive that device. So no recorded reach includes any, and a request from a device to a device of another unit is refused like any other. Within a unit, what a master does to the unit's own registers, under clause (e)'s conditions, gives the owner nothing that I32 or I34 (a) keeps from it |
| I31 (d), I33 (d) | **Whoever sets the address, the elements decide whether the write lands, and where.** *Fact*: by the AIA, software that sets a device's MSI address and data "fully controls" which hart and which interrupt file the interrupt reaches (`IMSIC.adoc`, "MSI encoding"), and its chapter on interrupt files states no check of who writes to one. By R5.4, a hostile device may write to any address in any case. The AIA has two conditions before a guest is given direct control of a device that sends MSIs: a guest interrupt file for each virtual hart; and that "interrupts from the device must be signaled by wire through an APLIC that can translate these interrupts into MSIs, or the system must have an IOMMU that can translate the addresses of MSI memory writes made by the device itself" (`VSLevel.adoc`, "Direct control of a device by a guest OS") |
| I32 | **HS-mode code.** Against Revision 4's attacker, what installs, protects, and enforces a device's confinement after a hart's activation cannot be HS-mode code on a confined hart. That narrows the implementation plan's hypothesis, "The core owns IOMMU domains, interrupts, reset authority, and grant/revoke operations". On a hart that a configuration leaves unconfined, HS-mode code may still do it, and that configuration's trusted computing base then names it, as R4.4 has it. Which element it is, this revision does not choose; R5.5 names the candidates |
| I32 | **What an owner may write.** Clause (d)'s state is what bounds the reach. State that can only narrow a master's reach inside that bound may be its owner's to write. *Fact*: an IOMMU may take the first of its two stages of translation from tables that its second stage bounds, which "allows the guest OS to directly edit" them (`iommu_data_structures.adoc`, "First-Stage context (`fsc`)"). What the element reads of such tables counts as the master's request (I31) |
| I32 (d) | **What directs an element.** *Fact*: "Command queue is used by software to queue commands to be processed by the IOMMU", in memory whose place a register sets, and one command has the IOMMU store given data at a given address when it completes (`iommu_in_memory_queues.adoc`, "Command-Queue (CQ)" and "IOMMU Command-queue Fence commands"). Whoever could write that queue could have the element write wherever the element itself can. So the queue is state of I32, as the element's registers are |
| I32 | **What an element caches, changes, and does after a reset.** A state is in force when the elements apply it and nothing else. *Fact*: an IOMMU "may use the old value of the entry or the new value of the entry" until software invalidates what it cached (`iommu_data_structures.adoc`, "Updating in-memory data structure entries"), and it may itself set bits in the tables that it reads. It may leave reset in a mode in which no request passes, `Off`, or in one in which "All inbound memory accesses are passed through", `Bare` (`iommu_registers.adoc`, "Reset behavior" and "Device-directory-table pointer (`ddtp`)"). *Fact*: an IOPMP whose `enable` bit is programmable leaves reset with it clear, and the draft does not say what it does until the bit is set (`registers.adoc`, "Hardware Configuration 0 (`HWCFG0`) Register"). So whether a rule is in force before a master's first request is a fact of the platform |
| I32 (d) | **An identity that a register sets, a bypass, and a controller that writes.** *Fact*: an IOPMP's identities are formed in ways that are "implementation-defined and possibly integration-specific" (`terminology_and_concepts.adoc`, "Request Role ID (RRID)"). *Fact*: by the manual, M13's record has masters whose identity to an IOPMP is set in a register field (rows A-17, A-19, and A-36 to A-50), and one register field that decides whether three PCIe ports' requests pass the IOMMU (A-72). *Fact*: by upstream Linux's source, software writes the registers that place a PCI function's registers, and those by which a port lets a request from below it carry another's identity or not (`pci_std_update_resource()`, `drivers/pci/setup-res.c`; `pci_enable_acs()`, `drivers/pci/pci.c`). *Fact*: letting software set the addresses to which an interrupt controller sends messages "permits bypassing physical memory protection (PMP)" (the AIA, `AdvPLIC.adoc`, "Machine MSI address configuration") |
| I33 | **Two kinds of delivery.** An interrupt may become pending in an interrupt file that the configuration gives the owner, with no work by the monitor when it is delivered; or the monitor may take it on the owner's hart and make it pending for the owner, as it has to for a file that an element keeps in memory, which "cannot interrupt a hart directly" (the AIA, `IOMMU.adoc`, "Memory-resident interrupt files"). Both are routes. The second is what the MVP plan's stop condition 3 calls injection. Whatever a source needs done at a controller is part of its route: the owner does it only where I34 (a) allows, and otherwise it is done for the owner under I34 |
| I34 (c), I35 (d) | **Cache-block operations, and coherence.** *Fact*: by the cache-block chapter, an invalidate needs only the permission of a load, and at a lower privilege it "may result in a security hole"; the chapter lets more privileged software make it trap there, or act as a flush (`cmo.adoc`, "Page-Fault, Guest-Page-Fault, and Access-Fault Exceptions" and "CSR controls for CMO instructions"). *Fact*: by upstream Linux's source, a PCI function's request may say of itself that it need not be coherent, where a bit of the function's own register allows it, and an IOMMU may or may not override that (`PCI_EXP_DEVCTL_NOSNOOP_EN`, `include/uapi/linux/pci_regs.h`; `enforce_cache_coherency`, `include/linux/iommu.h`). *Fact*: an IOMMU that supports page-based memory types (PBMT) gives each request the type "as resolved between the first-stage and second-stage page table entries", and the checker of physical memory attributes (PMA) behind it "may use the provided PBMT to override the PMA(s) for the associated memory pages" (`iommu_intro.adoc`, "Placement and data flow"). The first stage may be its owner's to write (I32's reading). Whether a type that an owner sets so makes a request not coherent is a fact of the platform. *Fact*: under M11's boundary each of the three operations that Linux's driver path uses, a clean, an invalidate, and a flush, traps in a VS domain, by the monitor's source, the M11 plan, and the cache-block chapter (M13's result, section 3) |
| I36 (b) | **Who quiesces, and a breached hart.** Whatever may write what the quiescing needs does it: the monitor, only with what I32 and I34 leave it; otherwise an element below HS mode. A breached hart "keeps its own VS domain" (the boundary's limit), and it keeps that VS domain's units with it: its profile includes their registers (I38), so it can start a unit again after a pause. That is an allowed effect (R5.4), and I31 to I33 still bound the unit |
| I38 | **R4.3 with a device.** R4.3's containment of a breached, confined hart stays true of a hart whose profile includes a unit's registers only where I38 is kept: such a hart could otherwise reach, through the unit, what its profile denies it |

### R5.3 What would show each invariant

No test is written here. The table says what a device path would have
to show for each invariant, and the negative cases that it would have
to test. They are obligations for the plan of step (3), which may
refine them, and returns to the responsible human before it drops one,
as S3-D.4 has it for M11's requirements.

For a negative case the rule is M11-R7's, carried to a device, in I21's
words: the test passes when the forbidden request "reads nothing and
changes nothing", by a witness outside the device, its owner, and every
hart that the test treats as breached. What a breached hart prints is
not such a witness (R4.5). M11-R7 ends: "A hart that merely stops is
not a pass". Nor is a device that merely stops.

An enforcing element's record is such a witness only for the requests
that it has, and only for what it says of them. It has to be where no
such hart, and no master but the element itself, can write it, or make
the element record a request that the master named in the record did
not issue, and it has to be read from below HS mode or from outside
the machine. It shows
that the element refused a request; that the request read nothing and
changed nothing rests on R5.5's first row. *Fact*: an IOMMU keeps its
fault records in "an in-memory queue"; once that queue is full it
discards a record, and writes no more until software clears a bit; and
it writes one for whatever identity software gives its debug registers
(`iommu_in_memory_queues.adoc`, "Fault/Event-Queue (`FQ`)";
`iommu_registers.adoc`, "Fault queue CSR (`fqcsr`)";
`iommu_debug.adoc`, "Debug support"). An IOPMP's record "holds the
details of the first captured illegal transaction"
(`terminology_and_concepts.adoc`, "Error Capture Record"). A device
path that bounds a flood (I33 (f)) by suppressing an element's records
loses them, as an IOMMU whose queue has overflowed does; one that only
masks the element's interrupt keeps them where the element records
without it. An IOPMP records a request that it refuses only if it
"triggers an interrupt or returns a bus error for the transaction"
(the same section).

| # | What a device path would have to show | Negative cases |
| --- | --- | --- |
| I29 | The platform description lists every device and every master of the platform, with each device's holders and each master's identities, checked against a source that its generator did not use; each master's kind, with its evidence; and, for each quiesced device, what keeps it so | A master that the description leaves out, and a second holder of a device, each seeded, are caught by that check. A VS domain, a breached hart, and a master of another unit each try to wake a quiesced master: through its registers, and through a control |
| I30 | Each unit's closure, computed offline from the platform description, whose relations are checked against a source that its generator did not use | An owner tries to act on a device outside its unit through each thing that the two share: a neighbouring register, a control request, a shared line |
| I31 | For each master, each identity that it can claim, and each kind of request that it can issue: a request inside the recorded reach succeeds, and one outside is refused | The owner makes its device read, and write: the monitor's memory; M-mode's; another VS domain's; a declared page beyond the owner's right; a register of a device outside its unit; a register of its own unit in an extent that also has another device's control, or state of I32; the state of I32; an interrupt file that is not its route's. Also a request that lies partly outside the reach, of which nothing outside is read or changed; a request under an identity that has no recorded reach; a request that calls itself already translated; a table in the owner's memory that an element reads for the master, made to lead outside the reach; an address beyond the width that an element decodes; and a fetch |
| I32 | The state in force, read back once the elements have taken up the last change, compared offline with the sealed configuration by a check that is independent of what derived it; and, by I31's cases, that the elements apply what was read back | A VS domain, a device of an assigned unit, and a breached, confined hart each try to change the state, to change a master's identity, to move a device's registers, to make a request bypass an element, and to turn the enforcement off |
| I33 | Each source's interrupt arrives at its owner, on its owner's hart, and nowhere else; no other hart takes a trap for it | The owner aims its device's message-signalled interrupt at another VS domain's interrupt file, at M-mode's, at a controller's port for messages, and at a file of the monitor's, none of them its route's delivery point: nothing is raised. Its device writes every identity to its own delivery point, and each is attributed to its own unit alone. Under a flood of the unit's interrupts, and of its refused requests, the other harts' work is unchanged but for an element's signals to the hart that the configuration names for them, within I33 (f)'s bound, and a pause of the owner still takes effect. No interrupt of an earlier holder arrives |
| I34 | Each control operation that an owner may ask for, and each access that is made for it, acts on its unit alone, and leaves what the state of I32 allows as it was | An owner asks for a control operation on another unit, or for one that it has no grant for; for an access beyond its grant; and, through an access, for a change to a control or to state of I32. From its own hart it reads and writes a register that I34 (a) keeps from it. Each is refused, with nothing changed. After a reset that an owner asked for, the state of I32 is in force again before any request of the unit reads or changes anything. An owner with only the read right on a declared page cannot make what its writer stored there be lost, and no owner's invalidate brings back what the monitor cleared |
| I35 | The order, from the boot code's own record, with the unit quiesced before the rest | The boot chain leaves the device active, with a request queued, an interrupt pending, and data in it: nothing of them reaches the owner, and no request lands before the master is confined. A master's confinement cannot be installed, seeded: the unit stays quiesced and no VS domain starts. For a master that is not coherent with the harts: what was cleared is not read back by the device |
| I36 | No request of a paused, terminated, or failed owner's unit reads or changes anything, and no interrupt of it is delivered, unless Revision 4's attacker on the owner's hart starts the unit again (I38's row) | A request that was queued before a termination, or before a restart, does not land after it. A system reset in the middle of a handoff or of a restart: the next boot's handoff does I35's steps in order, from whatever state the unit was left in. A system reset with an interrupt pending or a route installed: no interrupt of the run before reaches a VS domain |
| I37 | No assigned unit is a boot source, by the platform description and the boot chain's own configuration. For each assigned unit with a master: that the platform's reset bounds the master, or the sentence of the limit that names the unit's owner | An owner rewrites its unit's persistent state: while that boot runs, the contents of every boot source, and the values that the launch gate compares (I20), are unchanged. Where the platform description says that a reset bounds a unit's masters: after a system reset in the middle of a transfer, and with a master that issues requests from the reset on, nothing is read or changed before boot code has quiesced the unit |
| I38 | I31's and I33's evidence, with the hart's profile as the bound | A hostile-monitor image on the owner's hart, as M11's are, drives the unit toward memory outside that hart's profile, also once its owner is paused |

### R5.4 Part 1, threat model: the device, its owner, and its hart

The threat model's lists gain the following. Nothing in them is removed
or reworded.

- **Attackers** (added). Three.
  - **A VS domain that owns a unit.** It may write anything to the
    registers of its unit's devices that its mappings include, and ask
    for any operation or access (I34 (b)), at any time, and so make the
    devices issue any request and raise any interrupt that they can.
    It is no new attacker: the accepted list begins "Every
    non-Beryllium domain, from its first instruction". The device is
    its new instrument.
  - **A device, or its firmware, that is hostile or defective.** It may
    issue any request, of any kind, to any address, under any identity
    that nothing between it and an enforcing element stops it from
    using, and raise any interrupt that it can, at any time, whatever
    its holder wrote to it. How it came to be so is not modelled: by
    design, by a defect, by what an earlier holder left in its
    persistent state, or by what reaches it from beyond the machine.
  - **Revision 4's attacker, on a hart whose profile includes a unit's
    registers.** It can do with the unit all that the first can, at
    any time, whether the unit's owner runs or not.

  Containment is required against all three where the master is
  confined. Against a master of I29's third or fourth kind nothing is
  contained: that is a limit of the configuration, which names it.
- **How this reads with the accepted text.**
  - Part 1 defers "physical attacks" and "compromised vendor roots",
    and they stay deferred. A hostile or defective device is modelled
    by the requests that it can issue, whatever made it so. An attack
    on the platform's own hardware, the enforcing elements among it, is
    not modelled; nor is a vendor's signing key that signs a hostile
    image.
  - Part 1 defers "a firmware-hostile launch", and R4.3 "a defective or
    hostile M-mode firmware, and a boot chain that delivers another
    firmware or another descriptor". They stay deferred, but for one
    effect that this revision takes up: what an owner changes, through
    what its unit keeps across a system reset, in what a later boot
    loads, which I37 (b) contains, and in what the unit's devices do
    before that boot's handoff, which I37 (c) contains where the
    platform's reset bounds them, and otherwise allows and names.
  - R4.3 defers "the board's other execution contexts, and whatever
    addresses memory without one, such as a device that masters the
    bus or the debug module, until an inventory shows what they can
    reach". M13's record is an inventory, for one board, of the bus
    masters and of the contexts that drive devices. It does not
    establish what bounds their accesses (M13's result, section 3).
    I29 takes them up as listed. The debug module stays deferred:
    whether JTAG is enabled on that board, and what bounds the debug
    module's accesses there, are not established.
- **Assets** (added): each recorded reach and each route, with the
  state derived from them; the platform description; the interrupt
  files; and what a unit has of one holder when another takes it.
- **Allowed effects** (added).
  - An owner may do anything to its own unit: stop it, break it, and
    rewrite its persistent state. It may use it on whatever lies beyond
    the device, a network or a medium. What leaves the machine through
    a VS domain's own device is that VS domain's doing, and the model
    says nothing of the world beyond the device, a flow between two VS
    domains through it among that (R5.10).
  - A device may read or damage whatever its recorded reach allows of
    its owner's memory, interrupt its owner at any rate, serve badly,
    or stop. That is why a recorded reach may be less than its owner's
    memory.
  - A VS domain that serves others through declared channels may serve
    them badly or not at all, as management "may pause, starve, or
    terminate protected work".
  - Revision 4's attacker on an owner's hart may do with that owner's
    units whatever the owner may, also while the owner is paused or
    once it is terminated. I31 to I33 bound the units as before, and
    I38 the hart.
  - What a unit's masters do between a system reset and the next
    boot's handoff of the unit, with whatever the reset left in them,
    where the platform's reset does not bound it. The configuration's
    limit then names the unit's owner (I37 (c)).
  - Timing effects on what devices and harts share, the bus among it:
    the accepted "Architectural timing differences", and R4.3's
    deferred channels.
- **Required containment** (added).
  - No master of an assigned unit reads or writes the monitor's memory
    or M-mode's, another VS domain's memory, a declared page beyond its
    owner's right, the registers of a device outside its unit, the
    state of I32, or an interrupt file other than at its route's
    delivery point.
  - No interrupt of a unit is delivered to anything but its owner, and
    no VS domain is interrupted by another's device.
  - No owner changes a device outside its unit: through a register,
    through a control, or through its own device.
  - No VS domain is given a boot source (I37 (b)). Where the
    platform's reset bounds a unit's masters, nothing of the unit reads
    or changes anything between a system reset and the next boot's
    handoff (I37 (c)).
  - A breached, confined hart gains nothing through a unit beyond its
    profile (I38).
- **Deferred** (added): what a hostile or defective device does to the
  machine before the monitor's boot code has quiesced it, beyond what
  I37 (c) says; and what devices do to each other and to the platform
  other than by requests and interrupts: power, heat, and signals.

### R5.5 Part 1, trusted computing base: what a device path trusts

The TCB table gains the rows below. The existing rows are unchanged.
Each is in the **running TCB** unless it says otherwise.

| Trusted element | Evidence class today | Note |
| --- | --- | --- |
| The enforcing elements, as a platform implements them: that every request of every master that they are to confine passes them, under every identity that the master can claim; that they attribute a request rightly, with whatever lies between the master and them; that they apply the recorded reach to every kind of request, whatever it says of itself; that a refused request reads nothing and changes nothing; and that an element's own reads and writes are those that the state of I32 directs, and no others | none | For the K3 board, M13's result: "the record shows no mechanism on this board that bounds the memory accesses of any bus master other than the harts. That says what the record's rows hold, the held results apart; it does not say what the hardware can do" |
| Whatever writes the state of I32, keeps it from being changed, and serves the elements while the system runs, their records and what they signal among it: boot code before the activation of the hart that writes it, an element below HS mode, or the monitor on a hart that the configuration leaves unconfined (R4.4) | none | The candidates, of which this revision chooses none: state that is locked until a reset; registers and tables that no confined hart's profile allows a write to (I22); and the M-mode firmware, which then takes nothing from HS-mode code (I32). *Fact*: an IOPMP's locks prevent "updates until the IOPMP is reset" for almost all of its state, but not for its error record, and an unlocked entry of higher priority overrides locked ones (`configuration_protection.adoc`, "Summary of Table, Register, and Field Locks" and "Entry Protection"). No lock of an IOMMU's state was found in its specification |
| The interrupt controllers, and whatever writes the routes | none for a device's interrupt | *Fact*: on the K3 board the M-level controllers are the resident firmware's, by its source; and, as booted under the resident boot chain, the S-level APLIC was read and written from HS mode (M13's result, section 3). *Fact*: by the AIA, upon reset of an IMSIC "all the state of its interrupt files becomes valid and consistent but otherwise UNSPECIFIED", and an APLIC's state likewise, but for a few registers (`IMSIC.adoc`, "Reset and revealed state"; `AdvPLIC.adoc`, "Reset"). So a reset need not clear a pending interrupt (I36 (d)) |
| Whatever performs control operations, and accesses that are made for an owner (I34 (b)) | none | *Fact*: on the K3 board, the reset bits and clock gates of each bus master that the board's Linux drives are in clock and reset blocks that Linux drives as a whole, and the real-time firmware maps two of those blocks as well (M13's result, section 3) |
| The platform description, and its generator | none | By its output: a master that it leaves out, a shared thing that it misses, or an identity that it gets wrong weakens containment with no sign at run time |
| The offline check of the platform description, and of the state of I32 as read back | none | Offline evidence TCB. Each has to be independent of the generator |
| The boot chain, for the state in which it leaves every device; each device's reset, for clearing what I35 (b) says is cleared in the unit itself; and the path between a master and what it addresses, through its enforcing elements, for bringing to an end every request that was issued before, whether or not an element has passed it | assumed | I35 (a), (b); I37 (c). *Fact*: on the K3 board the boot chain reads from devices, the MVP's boot media among them (the MVP plan, S3-A.1). *Fact*: an IOMMU's own fence has the requests that it has already processed "committed to a global ordering point"; for those that it has not yet processed, "Software must perform an interconnect-specific fence action"; and for accesses to I/O memory its ordering is "implementation and I/O protocol defined" (`iommu_in_memory_queues.adoc`, "IOMMU Command-queue Fence commands") |
| The devices, and the holders of devices, that no configuration of the project's controls | none. For the K3 board, M13's record lists them, and does not establish what bounds their accesses (M13's result, section 3) | Named under I29. M11's limit already has the real-time cores "outside the boundary and trusted" |
| The platform's reset, for I37 (c): that no master runs on across it, or that the enforcing elements refuse a master that does until they are given their state | none. *Fact*: M13's result lists what each reset scheme resets among what cannot be relied on for the K3 board; under M11's boundary the firmware's reset device only halts (its section 3) | Where the platform description does not establish it for a unit's masters, the limit names the unit's owner (I37 (c)) |

The TCB still does not include the VS domains. Within a boot an owner
is trusted for nothing: not for its device's requests, and not for
what it leaves in its unit. A configuration whose limit names an owner
under I37 (c) rests, at a later boot, on what that owner left.

### R5.6 Part 2: one class, a device as a subject, H06, H07, and Instance 4

Part 2 says of "Device, DMA, IOMMU, or interrupt-injection objects":
"None exists in any configuration; the classes are added when the first
does". This revision adds the class as specification, before any
configuration has a device, so that the plan of step (3) can be written
against it: the M14 plan's reading, accepted with it. No configuration
uses the class before that plan. The rule form, the union of rules, and
default deny are unchanged.

```text
class device { drive interrupt reset }
```

- `drive` is the right to drive the unit's registers. Those that a VS
  domain's mappings may include appear in the subject's G-stage root,
  with `read` and `write` and never `execute`: pass-through. An access
  to one that I32 or I34 (a) keeps out of the root is made for the
  subject, as the sealed configuration grants it (I34 (b)). Such an
  access changes no control and no state of I32: a control that I34
  (a) keeps out of the subject's mappings is worked only by a control
  operation, under that control's own permission.
- `interrupt` is the right to have the unit's interrupt sources routed
  to the subject.
- `reset` is the right to ask for the unit's reset, which is performed
  for the subject (I34 (b)). No permission is defined for a clock or
  for power: no owner asks for either until a use needs it, and a
  later revision then adds a permission under the same rule.

**A unit is an object, and a unit with a master is also a subject.**

- A labeling assigns one type to each unit, and that type labels
  nothing else. All of a unit's devices have it: they have one owner
  (I30), so no `device` rule could treat one differently.
- As an object, the unit is the target of `device` rules. Its registers
  are never the target of a `memory` rule: to write a device's
  registers is to drive it, which is more than to write bytes.
- As a subject, a unit with a master is the source of `memory` rules,
  with `read` and `write` alone: the bound of its masters' recorded
  reaches. Part 2 calls these "the leaf rights derived for" a region
  in a root. A device has no G-stage root, so for a unit they are the
  rights of a recorded reach, and `map` means nothing. It is given no
  `execute`: a master's fetch, where an element tells one from a read,
  is refused.
- The accepted text has a labeling assign a type "to every subject
  (each domain)". With a unit, the subjects are each VS domain and each
  unit that has a master. "the monitor never consults types at run
  time under this document" stays so.

**H06: authority without a mapping.** The synthesis asked "whether any
authority exists without a mapping". Instance 3 already has one:
`pause` and `terminate`, which the control hart performs on request, as
the sealed configuration grants them (R1.4). With a device, five more
kinds exist, and each has a named place where it is realized.

| Authority | Realized in |
| --- | --- |
| A master's reach | State derived from the sealed configuration, which enforcing elements apply (I31, I32). It need not be a hart's mapping, and a master's requests pass no hart; where an element shares a VS domain's G-stage tables, as an IOMMU may, those tables are both (I31's reading) |
| The delivery of a unit's interrupts | State derived from the sealed configuration: the route (I33) |
| A unit's reset | An operation that is performed at the owner's request, as the sealed configuration grants it and as I34 (b) says by whom. A clock or power has no permission, and so no owner asks for one, until a revision adds it |
| An access to a register of the owner's own unit that its mappings may not include, since the register's page has a control or state of I32 | The same: an operation performed for the owner, as the sealed configuration grants it, register by register and field by field. It changes no control and no state of I32. Its permission is `drive` |
| For a master that is not coherent with the harts, the cache-block operations that its driver needs, where the boundary makes them trap in a VS domain | The same: an operation performed for the owner, on the owner's own memory. It has no permission of its own: its bound is the owner's `memory` rights (I34 (c)) |

The M14 plan asks "whether any authority may exist with no derived
state that enforces it". A reset and a cache-block operation are
realized by an operation, not by derived state. So the answer is put
more widely: no authority exists with nothing in the trusted computing
base that realizes it, whether derived state or an operation that is
performed only as the sealed configuration grants. What exists only
because nothing refuses it is an effect, not authority (I34 (d)): a
master that nothing confines can reach all of memory, and the model
has it quiesced or named (I29). Helium's question came from a
permission that the policy alone had. Here `interrupt`, `reset`, and
each `memory` permission of a unit are realized as above, and `drive`
by a G-stage mapping or by an operation. A8 checks that the manifest
has none without its rule (R5.7).

**H07: when a finer type has security meaning.** The synthesis has the
rule: a finer type has security meaning "only when policy gives it
different authority". A device makes three cases concrete. The third
adds a condition of this revision's: that an element can enforce the
distinction.

- **Within an owner's memory.** The part that its device may reach and
  the part that it may not have different authority: one is the target
  of the unit's `memory` rule, and the other is not. So they have
  different types wherever the recorded reach is less than the owner's
  memory, as in Instance 4.
- **Registers and memory.** A device's registers are not `memory` of a
  finer type. They are an object of another class, because to have them
  is another kind of authority.
- **Within a unit.** No type is finer than a unit. As objects, its
  devices and its interrupt sources have one owner (I30, I33), so no
  rule could give them different authority. As subjects, masters that
  I30 (a) joins cannot be given different reaches, since no element
  tells them apart. Masters that only (b) or (c) join could be, and
  `M` may record less for one than for another, inside the unit's one
  rule; a type for each is for a later revision, when a policy needs
  to say so. A distinction that no element can enforce at its grain is
  not a type, and A11 refuses a labeling that makes one.

**Instance 4: one unit, its owner, and a VS domain that the owner
serves.** Part 2 gains a fourth instance. It is a specification of what
a device path would build, not of what exists, as Instance 2 was. It
names no device of any platform.

- Two VS domains, each on its own hart, each with its own window: a
  service VS domain, and a client VS domain that it serves.
- One declared page that the service writes and the client reads.
- One unit of one device. By the instance's platform description, the
  device is a bus master with one identity that no other device can
  claim; one enforcing element stands between it and all that it can
  address, tells extents apart at the grain of a page, and issues no
  request of its own (an element that does, as an IOMMU does, is a
  further master, which `H` then lists with what it reaches, and
  which the trusted computing base names, I29); every request that
  the device can issue is coherent with the harts; it signals by one
  message-signalled interrupt; its registers fill an extent of whole
  pages that has nothing else, no control and no state of I32; it has
  a reset of its own, which changes no other device's state, in a
  register that is not the unit's; a system reset stops it; it has one
  holder; and it is no boot source.
- The service's window has two parts: a pool that the device may reach,
  and the rest.

```text
type monitor_t;      type svc_t;        type client_t;
type svc_mem_t;      type svc_pool_t;   type client_mem_t;
type rx_t;           type dev_t;        type monitor_mem_t;

class memory  { read write execute map }
class channel { send receive }
class device  { drive interrupt reset }

allow svc_t svc_mem_t       : memory { read write execute map };
allow svc_t svc_pool_t      : memory { read write map };
allow svc_t rx_t            : memory { read write map };
allow svc_t rx_t            : channel { send };
allow svc_t dev_t           : device { drive interrupt reset };

allow client_t client_mem_t : memory { read write execute map };
allow client_t rx_t         : memory { read map };
allow client_t rx_t         : channel { receive };

allow dev_t svc_pool_t      : memory { read write };
```

Labeling: the service is `svc_t` and the client `client_t`; the
service's pool is `svc_pool_t` and the rest of its window `svc_mem_t`;
the client's window is `client_mem_t`; the declared page and its
channel are `rx_t`; the unit is `dev_t`; the monitor is `monitor_t`,
and its memory `monitor_mem_t`. The interrupt files and the state of
I32 are the monitor's, and outside the rule classes, as a G-stage root
is. The need sets are the rules' permission sets.

The manifest's records for the unit, beside those of the kinds that
Instance 3 has: its assignment to the service; its registers in the
service's G-stage root; one route, from its source to an interrupt file
that the configuration gives the service, on the service's hart; its
master's recorded reach, the pool's frames with `read` and `write`;
the grant of its reset to the service; and that reset as the act that
quiesces the unit, clears it, and makes it work again. It has no grant
of an access, and lets the master's requests reach no register.

What the policy says.

- `dev_t` has a rule on `svc_pool_t` alone. A request of the device to
  the rest of the service's window, to the client's, to the declared
  page, to the monitor's memory, or to any register is the policy's
  deny, and I31 has it read nothing and change nothing. Its interrupt
  is no part of its reach: the route admits that one write (I31 (d)).
- `client_t` has no `device` rule. The client reaches the device only
  through what the service writes to the declared page.
- **May the device's reach include the declared page?** It may: a rule
  `allow dev_t rx_t : memory { write };` passes A10, since `svc_t` has
  `write` on `rx_t`, and the flow stays `svc_t -> client_t` (R5.7).
  Here the need set does not have it, so A4 refuses it, and the service
  copies.

### R5.7 Part 3: five analyses, and the accepted ones with a unit

Each analysis below is a decidable check over a finite policy, a
labeling `L`, a manifest `M`, and, where stated, a finite platform
description `H`. None is implemented. For a policy with no `device`
rule, A1 to A8 are as accepted. Write `owner(u)` for the one subject
type that has a `device` permission on a unit's type `u` (A9).

**A3, A5, and A6, over owners.** Before A3's check of storage and
channels, A5's writers and readers, and A6's `F` and `D` are computed,
each unit's type is replaced, as a source, by its owner's. A unit has
nothing that its owner lacks (A10), so through `memory` it adds no
flow between subject types: what a VS domain's device reads or writes,
that VS domain reads or writes. Three kinds of flow are not A6's to
find, with a unit or without one. A flow through a device that two
units could both drive is excluded by I30, which makes them one unit
(A11). A flow between two VS domains of one type is invisible to an
analysis over types. And a flow through the world beyond two VS
domains' devices is outside the model (R5.10). A3 also refuses: a rule
that gives a unit's type, as a source, anything but `read` or `write`
on `memory`; a `memory` rule whose target is a unit's type; and any
permission of a unit's type on `monitor_mem_t`.

**A1 and A8, with a unit.** A1's labeling covers each unit, and a
unit's type labels that unit alone. A8 gains six kinds of record: for
a unit's registers in a G-stage root, `drive`, with the leaf rights
`read` and `write` alone, and likewise for a grant of an access that
is made for the owner, and for the unit's registers that a master's
requests may reach (I31 (e)); for a route, `interrupt`, which also
admits the master's write to the route's delivery point (I31 (d)); for a
recorded reach, `read` or `write` with the unit's type as the source;
and for a control grant, `reset`. R1.3's reading stands: these are
grants, not structural bindings.

| Analysis | What it requires | A failure means |
| --- | --- | --- |
| **A9. One owner** | For each unit's type `u`, at most one subject type has any `device` permission on `u`, and it is a VS domain's type. If `u` is the source of a rule, exactly one has. Given `M`: each unit is assigned to at most one VS domain, of that type; its registers are in that VS domain's G-stage root and in no other; and its routes, its masters' recorded reaches, and its grants name that VS domain alone | a unit with two owners, or a reach with no owner |
| **A10. Reach within the owner, and within memory** | For every `allow(u, t, memory, Q)` with `u` a unit's type, and each `p` in `Q`: `decide(owner(u), t, memory, p) = allow`. Given `M`: every frame of a recorded reach is mapped in its owner's G-stage root, with each right that the reach has on it. Given `H` and `M`: no object of class `memory` under `L`, no memory grant, and no recorded reach includes an extent that `H` gives to a device's registers, to the state of I32, or to an interrupt file; by `H`, everything in each page of a unit's registers in a G-stage root belongs to that unit, and none of it is state of I32; the registers that `M` lets a master's requests reach (I31 (e)) lie in such pages, and everything in the extents that the elements let those requests reach belongs to that unit, and none of it is state of I32; every register and field that a grant of an access names is, by `H`, that unit's, and none that the access may change is a control or state of I32; and the control of every control grant is, by `H`, that unit's | a device that could reach what its owner cannot (I31 (b)); a VS domain or a device that could drive another's device or change a confinement (I31 (c), I32); or an owner that could do either through what is done for it (I34 (b)) |
| **A11. Units are closed, and can be assigned** | Given `H` and `M`: every assigned unit is closed under I30 (a) to (c); no device is in two units; no assigned unit is one that I30 (d) bars; and `L` makes no distinction inside a unit, and none among extents that is finer than the grain at which `H` says it can be enforced | a unit that reaches into another holder's device, or a label that nothing enforces |
| **A12. Every device and every master is accounted for** | Given `H` and `M`: once the boot chain has handed it on, every device of `H` has at most one holder, the owner that `M` gives it counted. For every master of an assigned unit, `H` has enforcing elements that every request of the master passes, under every identity that it can claim and to every address that it can issue, and says that their state can apply the recorded reach, at its grain, to every kind of request that the master can issue; and either `H` establishes that the platform's reset bounds the master, or `M` records the unit's owner as one that the limit names (I37 (c)). For every other master of `H`, `M` records its kind: quiesced, named in the trusted computing base, or named in the limit; and, for one that is not quiesced, what `H` says that it can reach | a device with two holders; a master of no kind; an owner's master that nothing confines (I29); or an owner that the limit has to name and does not (I37 (c)) |
| **A13. Routes end at the owner** | Given `H` and `M`: every interrupt source of an assigned unit has one route; its delivery point is one that `M` gives the unit's owner, which has `interrupt` on the unit; by `H`, the place where the interrupt becomes pending, or where the monitor takes it or an element's notice of it, is on the hart that the owner is bound to; and no delivery point of one VS domain's is the target of a route of another's unit | an interrupt that reaches a VS domain that is not its owner, or a hart that is not its owner's (I33) |

**Instance 4, by hand.**

| Analysis | Result | Why |
| --- | --- | --- |
| A1 | passes | 9 types, 3 classes, 9 rules; 3 subjects (the two VS domains and the unit), each labeled once, and each object |
| A2 | passes | each rule has a subject of its source type and an object of its target type |
| A3 | passes | no type has a permission on `monitor_mem_t`; `rx_t`'s channel rules have their storage; `svc_pool_t` is shared by `svc_t` and its own unit alone; `dev_t` has `read` and `write` on `memory` and nothing else; no `memory` rule targets `dev_t` |
| A4 | passes | each rule is its need set |
| A5 | reports | `rx_t`: static, not revocable, single writer `svc_t`. `svc_pool_t` has one writer over owners, and no other reader |
| A6 | passes | over owners, `F = D = {(svc_t, client_t)}`, and `F+ = D+` |
| A7 | vacuous | no delegation |
| A8 | passes | 5 `memory` grants, 2 channel endpoints, the unit's registers in the service's G-stage root, one route, one recorded reach, and one control grant: each has its rule, and none exceeds it |
| A9 | passes | `svc_t` alone has `device` permissions on `dev_t`; one VS domain has that type; the unit's registers are in its root alone; and every record of the unit in `M` names it |
| A10 | passes | `dev_t` has `read` and `write` on `svc_pool_t`; so has `svc_t`. The reach's frames are the pool's, which the service's root maps with both rights. By the instance's `H`, no memory object has a register, state of I32, or an interrupt file; the pages of registers in the service's root have nothing but the unit's, and no state of I32; and the control grant's reset is the device's own. `M` has no grant of an access, and lets the master's requests reach no register |
| A11 | passes | by the instance's `H`, nothing shares the device's identity, its pages, or its source, and its reset changes no other device's state; I30 (d) bars nothing |
| A12 | passes | the device has one holder, the service; its every request passes the one element, which can apply the pool as its reach at the grain of a page; a system reset stops it; `H` has no other master |
| A13 | passes | one source, one route, to an interrupt file of the service's, on the service's hart; `svc_t` has `interrupt` |

Ten variants, each of which fails as it should. Some fail a second
analysis as well.

| Variant | Fails |
| --- | --- |
| `allow dev_t client_mem_t : memory { read };` | A10: `svc_t` has no rule on `client_mem_t`. Also A4; A6, since over owners `(client_t, svc_t)` is a flow that no channel declares; and A3, where its check of storage is read to refuse storage that no channel declares |
| `allow client_t dev_t : device { interrupt };` | A9: two owners. Also A4 |
| `allow svc_t dev_t : memory { read write map };` | A3: registers as `memory`. Also A4, and A2 reports the rule as unreachable |
| A second VS domain is labeled `svc_t`, and `M` puts the unit's registers in its root too | A9: the unit's registers are in two roots. A8 passes, since both have `svc_t`'s `drive` |
| In `M`, the recorded reach has a frame, labeled `svc_pool_t`, that the service's root does not map | A10: a reach beyond its owner's mappings. A8 passes |
| In `L`, a page that has registers of the device is an object of type `svc_pool_t` | A10: a register in a memory object, and in a reach |
| In `H`, the device shares a page of registers with a device that the firmware drives | A11: I30 (b), then (d). Also A10: the page in the service's root has another device's registers |
| In `H`, no enforcing element stands between the device and what it addresses | A12, and A11 by I30 (d): the unit cannot be assigned; its master is quiesced or named |
| In `M`, the route's delivery point is an interrupt file of the client's, or one on the client's hart | A13 |
| In `M`, the service has a grant of an access that may change the register that has the device's reset | A10: the access could change a control, in a register that is not the unit's. A8 passes, since `svc_t` has `drive` |

Status: A9 to A13 are defined only. Neither Model 0.2's validator nor
the MVP's checker (`mvp/tools/policy-check.py`) has them, and both are
unchanged.

### R5.8 Parts 4 to 7: the records, the triggers, the states, and the inventory

**Part 4.** "Validate" stands. The manifest's new records are checked
against the policy by A8, with A9 to A13 run before sealing. The
pipeline's first line already has a "platform description"; R5.1 says
what it is. The implementation plan has the core itself validate
"device/IOMMU ownership" before it activates a configuration: which of
these checks the monitor's boot code repeats before it seals is for the
plan of step (3). The authority report's schema is not changed. It
has a place for a unit as an object of class `device`; for a recorded
reach, as grants whose subject is the unit; and for A9 to A13, as
further entries of `checks`. It has none for a subject that is no VS
domain, since a subject's entry has a `domain_index`; for a unit with
more than one extent of registers; or for a route's delivery point.
The plan that builds a generator extends it.

**Where the authority is recorded.**

| Record | What it gains | Its identity |
| --- | --- | --- |
| The manifest | For each assigned unit: its assignment; its registers' extents in its owner's G-stage root; each route; each master's recorded reach, and the registers of the unit that its requests may reach (I31 (e)); each grant of a control operation, with its control; each grant of an access that is made for the owner, with the registers and fields that it may read and may change; and the acts by which the unit is quiesced, cleared, and made to work again (I30 (c)). For every other master of the platform, its kind under I29, and, for one that is not quiesced, what it can reach. Each owner that I37 (c) has the limit name | The configuration identity, which is to cover them |
| The partition descriptor | In `devices`: for a hart whose profile includes a unit's registers, the unit and those extents (I38). In `interrupts`: that unit's sources, beside the hart's own timer. Where an element below HS mode installs the state of I32 or performs control operations, what it installs and what it may perform, so that it takes nothing from HS-mode code (I24, I32, I34) | The descriptor's own |
| The platform description | Every device, with its registers' extents or the state that places them, its sources, its identities at each element, its controls, its persistent state, whether it is a boot source, and its holders: whatever outside the configuration drives it or depends on it, and when; every master, with the kinds of request that it can issue, whether each is coherent with the harts, whether anything that an owner may write can change that, and what a reset leaves it doing; the relations of I30; each enforcing element, with what passes it and what does not, the grain at which it tells extents apart, where it writes, and what it does after a reset until it is given its state; the interrupt files, each with its hart, or with where an element gives notice of it; and what is not established | Its own, which the configuration identity is to bind |

No measurement is added: I19 and I20 are unchanged. The log's record of
the configuration identity is informational and build-recorded
(`mvp/docs/log-profile.md`), and no register binds it; it would name a
configuration with these records as it names one today. Whether the
log also records the descriptor's identity, or the platform
description's own, is for the plan of step (3). No identity covers a
device's persistent state (I37 (a)). A master whose kind `M` records as
named in the limit is named, with what it can reach (I29's reading),
in the limit of every claim about the configuration. So is an owner
that I37 (c) has named.

**Part 5: the triggers, for the static device case.** U4, beside U1 to
U3: one unit, assigned to one VS domain by the sealed configuration,
with no change of assignment, and no restart, while the system runs.

| Trigger | Result for U4 | Evidence |
| --- | --- | --- |
| The capability trigger | does not fire | The assignment, the recorded reach, the routes, and the grants of operations are static records of the manifest. Nothing is designated, delegated, attenuated, or revoked at run time. An owner chooses its buffers by writing its device's registers, inside a reach that does not change |
| The runtime-check trigger | does not fire | Every denial follows from derived state alone: from the absence of an entry for the request in the enforcing elements' state, or from an entry or a setting there that allows less; from the absence of a route; and from the absence of a leaf for a register. A request for a control operation, or for an access that is made for the owner, is decided from the sealed grants alone, which name the control, or the registers and fields, as M2's `pause` and `terminate` are (R1.4). No case exists in which the derived state allows and the policy denies |

The second row reads the trigger's "a rule the derived mappings do not
express" with the state of I32 beside the G-stage leaves: both are
derived from the manifest, and neither is consulted as policy at run
time. A design in which an owner changes its device's reach while it
runs is not U4. For such a design, and for a restart, the plan that
builds it evaluates both triggers, as S3-C.2 has it for dynamic
management.

**Part 6.** Unchanged. A change of a unit's owner, a unit taken back,
hot-plug, and who may ask for a restart are dynamic operations, in the
vocabulary that Part 6 says is missing. They are step (5)'s.

**The states of a unit.** `with the boot chain`; `quiesced`; `cleared`
(I35 (b)); `confined and routed` (I35 (c)); `exposed`; and `quiesced,
with its owner` (I36 (b)). The first handoff passes through the first
five in that order, once. The unit enters the last whenever its owner
stops running, and a restart returns from there to `cleared` (I36
(c)). The static case has no other transition. Step (5) would add a
change of owner, and a return to `quiesced` with no owner. The
negative cases that those bring, beside R5.3's:

- the earlier owner still reaches the unit's registers after the
  change, through a mapping or a translation that was not withdrawn;
- a request that was queued under the earlier owner lands in either
  owner's memory after the change;
- an interrupt that was raised under the earlier owner reaches either
  owner after it;
- the new owner reads the earlier owner's data, from the device or
  from memory that the device can reach;
- a reset or a failure part-way leaves the unit with one owner's
  registers and the other's reach;
- the change races with a transition on another hart;
- the state of I32 cannot be changed, for want of room or by an error:
  the unit stays quiesced, with no owner.

**Part 7: the inventory, extended.** Nothing here is made.

| Element | Change | Where it would land |
| --- | --- | --- |
| The abstract model | Units, masters, and the platform description as inputs; A9 to A13 as decision procedures; A3, A5, and A6 over owners; and a statement that a policy that passes A10 has the same `F` over the VS domains' types with its units as without them | `model/proof/`, a new module; the accepted modules unchanged |
| The executable model and the MVP's policy checker | The `device` class, a unit as a subject, A9 to A13, and `H` as an input. The checker is a path that the proofs' records bind, so a change to it has those records derived again | `model/src/`; `mvp/tools/policy-check.py` |
| Model 0.2's validator, and what the monitor's boot code validates | For a unit's records, in extensional form: one owner, and its registers in that owner's root alone (A9); each recorded reach inside its owner's mappings; no register, state of I32, or interrupt file in a memory extent; and A10's checks of the registers of a root, of a master's requests, and of an access grant, and of a control grant's control (A10); one holder for each device (A12); and each delivery point on its owner's hart (A13) | `model/src/`; the monitor, as the plan of step (3) decides (Part 4) |
| The scenario's format | The units, their assignment, each recorded reach, each route, each grant of an operation or of an access with what it names, the kind of every other master, and the identity of `H` | `mvp/scenarios/`, `scenario.json` |
| The partition descriptor | The `devices` and `interrupts` entries above, and what an element below HS mode installs or may perform | The descriptor's schema, in a later version |
| Fixtures | Instance 4, with its ten variants | `model/` fixtures |

### R5.9 The model, tried on three instances

The M14 plan has the model tried on instances before it is proposed
(its rule 5). This is the trial's outcome. The tables for each master
and each device are the result's, which follows this revision's
sign-off. Nothing was run, and no device was chosen.

- **Instance 4** (R5.6, R5.7): on paper, eleven of the thirteen
  analyses pass, A5 reports, and A7 is vacuous; and each of ten
  variants fails at the analysis that names its defect.
- **One K3 COM260 board**, by M13's record, read as a platform
  description would have to be. Each row keeps its class: what a
  document or a source says, what the board's Linux showed, and what a
  probe read as booted through the resident boot chain.
- **QEMU's `virt`**, as the gates' `k3-like` row configures it
  (`virt,aia=aplic-imsic,aia-guests=7`, eight harts, no added device,
  and no IOMMU: `mvp/tests/run-qemu.sh`); as one gate, the U-Boot
  rehearsal, adds a disk to it
  (`mvp/tests/uboot-rehearsal/run-qemu-uboot.py`); and with what QEMU
  offers for it, from the source alone.

| The model's term | The K3 board, by M13's record | QEMU's `virt`, by its source |
| --- | --- | --- |
| Masters, and what would confine them (I29, I31, I32) | "the record shows no mechanism on this board that bounds the memory accesses of any bus master other than the harts. That says what the record's rows hold, the held results apart; it does not say what the hardware can do" (M13's result, section 3). As booted, the IOMMU's mode field read `Off`, and the bypass bits of PCIe ports A, B, and C were set (A-160, A-163); the sources read name the IOMMU for PCIe ports alone (A-69 to A-71); and the record does not establish the IOPMPs' state as booted (its "Not established" list, item 1). So the record establishes enforcing elements for no master, and on the record alone I30 (d) leaves no unit with a master to assign | As configured, two devices of the machine besides the harts address memory: the firmware-configuration device's DMA engine, started by a write to its register (`hw/nvram/fw_cfg.c`), and each APLIC, by its MSI writes (`hw/intc/riscv_aplic.c`). The rehearsal's disk is a third: a virtio block device on the memory-mapped transport, whose requests go to system memory (`hw/virtio/virtio-bus.c`). Nothing stands between any of them and memory. The two RISC-V IOMMU models see what a PCI function sends through its bus-master address space, and not all of that: not a virtio PCI device's data by default; not a function of the IOMMU's own class; and nothing on a root bus whose host bridge sets `bypass-iommu`, which is off by default (`hw/pci/pci.c`, `hw/pci/pci_host.c`, `hw/virtio/virtio-bus.c`, `hw/riscv/riscv-iommu.c`). They leave reset in `Off`, or in `Bare` by a property |
| Holders (I29, I30 (d)) | The SPL, U-Boot, the resident firmware, and the real-time cores' firmware drive devices, as far as the sources, the trees, and the board's Linux show it; what the boot ROM touches is not established (M13's result, section 3). More than one holder: the power-management chip, which the board's Linux drives and which the real-time firmware drives by its source and tree (D-34, D-71); and the GPIO block and the pin controller, which the real-time cores' trees enable and the board's Linux drives (D-15, D-16, D-37) | One array of harts, and no other execution context (`hw/riscv/virt.c`). "The monitor touches no device" (R5.1), so in the `k3-like` rows each device is the firmware's or has no holder; in the U-Boot rehearsal, U-Boot also drives the disk before it hands on. Which devices the firmware drives was not read |
| Units (I30) | Found so far: by the manual's address map, registers of several devices in one 4 KiB page (D-23 to D-26); one bus reset and one bus clock enable for the three storage card controllers (C-19); by the vendor's tree, one bus reset and one clock for eight DMA controllers, the manual's HDMA (C-24); and PHYs that serve a PCIe or a USB port, one at a time (D-33). By clause (d), no unit there can be assigned on the record alone: its list of what devices share is "found so far" | The wired interrupts of all PCI functions arrive on four APLIC sources (`hw/pci-host/gpex.c`, `hw/riscv/virt.c`), and functions behind a conventional bridge share one identity (`hw/pci/pci.c`): clauses (b) and (a). It has no clock or PHY, and no reset line for one device: clause (c) joins the functions below one bridge where the act that the configuration uses on one of them is the bridge's reset of the bus below it (`hw/pci/pci_bridge.c`). One device model, `edu`, defines no reset: a reset clears its configuration space alone (`hw/pci/pci.c`), not its registers, its buffer, or a queued transfer (`hw/misc/edu.c`) |
| Routes (I33) | An MSI is a write to the target interrupt file's own page (A-124), and "No row of the record shows anything that stops a device's write to a hart's S-level interrupt file on this board, the monitor's among them" (M13's result, section 3) | No model checks who writes an interrupt file: a 4-byte write of an identity at the start of its page makes that identity pending there (`hw/intc/riscv_imsic.c`). An IOMMU model redirects a PCI function's MSI only through an MSI page table (`hw/riscv/riscv-iommu.c`) |
| Controls (I34 (a), (b)) | "a device's reset or clock cannot be handed over by mapping its register: the page holds other devices' controls" (M13's result, section 3). So clause (b) applies to each bus master that the board's Linux drives; for the other devices the record lists no reset lines | One system reset for all devices (`hw/core/reset.c`); a bridge's reset of the bus below it (`hw/pci/pci_bridge.c`); a function's own reset where its model has one; and one register that asks for the power-off or the reset of the whole machine (`hw/misc/sifive_test.c`). No clock and no power control for one device |
| Caches (I34 (c), I35 (d)) | "By the trees that Linux uses, DMA on this SoC is not cache-coherent (A-116); the manual and the vendor's tree make the eight HDMA instances coherent (A-103, A-104)" (M13's result, section 3) | It cannot show them: "We don't emulate the cache-hierarchy" (`target/riscv/op_helper.c`) |
| Reset, and the next boot (I36 (d), I37) | The SPL takes what it runs from the NOR flash or from a microSD card, unchecked (the MVP plan, S3-E.1, statement 2): each is a boot source, and so is the identity EEPROM, whose product name chooses the firmware's device tree (the same). U-Boot loads the MVP's image from the NVMe drive (S3-A.1, item 1): that drive is one too, unless everything that U-Boot reads from it to run or to trust is checked. On a boot from a card, U-Boot also "takes `env_k3.txt` from any partition named `bootfs`" (S3-E.1, statement 6). M13's result lists what each reset scheme resets among what cannot be relied on, and under M11's boundary the firmware's reset device only halts (its section 3). By the manual, an IOPMP "passes every access after a power-on reset until it is enabled" (the same); and, by an inference from the manual that the record marks as one, after reset three PCIe ports' requests bypass the IOMMU (A-72, A-73) | Most gates' images come from the host. In the U-Boot rehearsal, U-Boot loads the image from the virtio disk and runs it with no check before (`mvp/tests/uboot-rehearsal/run-qemu-uboot.py`): that disk is a boot source. The gates run the machine with `-no-reboot`, by which a reset request ends the run (`mvp/tests/run-qemu.sh`; `system/runstate.c`): no system reset executes. Neither interrupt controller's model defines a reset (`hw/intc/riscv_imsic.c`, `hw/intc/riscv_aplic.c`) |

**What no instance shows.** A device path's plan says where it takes
R5.3's evidence for each of these.

- A restart with a unit kept (I36 (c)): no instance has one.
- A master that is not coherent with the harts (I34 (c), I35 (d)); a
  clock, a power, or a PHY control of one device; a device with two
  holders; and an identity that a register field sets: the board has
  each, by its record. The emulated machine has none of them but one
  identity that software sets, the bus number behind a bridge. Its
  IOMMU models fix a function's identity when they build its address
  space, from the bus number at that time, which for a device present
  at start is before any bus behind a bridge is numbered
  (`hw/pci/pci.c`), and mark the rest "FIXME: PCIe bus remapping for
  attached endpoints" (`hw/riscv/riscv-iommu.c`); the gates'
  configurations have no bridge. It has no model of an IOPMP, and no
  device model that was read picks its own identity, as R5.4's second
  attacker may.
- A system reset with a master active (I36 (d), I37 (c)): the gates
  execute none. By its source, the emulated machine's interrupt
  controllers would keep their state across one, and `edu` a queued
  transfer.
- On the board, each "as booted" fact is the resident boot chain's: "A
  step that builds on M11's boundary cannot take an "as booted" row as
  that chain's state; it has to read the state again under that chain"
  (M13's result, section 3).

**What the model does not express.** How a master behaves in time: bus
contention, and when a refused request is reported. What devices do to
each other other than by requests and interrupts (R5.4). The debug
module (R5.4). One device with two holders at once (R5.10). And an
emulator's own paths into memory, its loader and its monitor among
them, which are the host's.

### R5.10 Scope, and what this revision does not say

- **The readings.** This revision reads these accepted texts, and edits
  none of them.

  | Accepted text | Reading |
  | --- | --- |
  | Part 2: "None exists in any configuration; the classes are added when the first does" | Added now, as specification (R5.6) |
  | Part 1's `interrupt` row | Its instances grow, and a device's source has its authority in the route (R5.1). Its "`hvip` injection is excluded by the B-series stops" stays true of every image so far |
  | Part 2: a labeling assigns a type "to every subject (each domain)"; and A1's "`L` assigns exactly one type to every subject and object" | A unit with a master is a subject too, and a unit's type labels that unit alone (R5.6, R5.7) |
  | Part 2: "`read`, `write`, and `execute` are the leaf rights derived for it" | For a unit as a subject, `read` and `write` are the rights of a recorded reach (R5.6) |
  | A3, A5, A6; and A8's "right in `M`" | Taken over owners where a policy has a unit; six more kinds of record (R5.7) |
  | Part 4's report schema: a subject's `domain_index`, and one `extent` for each object | Not changed; what it lacks for a unit is named (R5.8) |
  | Part 5: "a rule the derived mappings do not express" | The state of I32 is read beside the G-stage leaves (R5.8) |
  | I9: "checked before use" | With a master, what the monitor reads of an owner's memory it reads once (below) |
  | I16 and I23: one writer | A master's write counts as its owner's: a recorded reach includes a declared page only with its owner's right (I31 (b)) |
  | I22 (c): "A device's registers, only where the descriptor assigns that device to the hart's role" | For a VS-domain hart, the descriptor assigns only a unit that the VS domain bound to that hart owns, and I38 says what else has to be so |
  | I27: the allowlist | A control operation, or an access, that M-mode performs for a confined hart is a call of it (I34 (b)) |
  | I28; R4.5's "What addresses memory without an execution context is outside I28" | I29 takes up the bus masters |
  | R4.4's row for the board's other execution contexts, whose note waits for an inventory | M13's record lists them for one board, and does not establish what bounds them (R5.4, R5.5) |
  | Part 1's and R4.3's deferred items | Each stays deferred, but for I37's one effect (R5.4) |
  | The implementation plan's "Required containment": "No domain may DMA or inject interrupts outside explicit ownership" | I31 and I33 say what that takes, and I30 (d) keeps from every VS domain a unit that cannot meet it |
  | The implementation plan's hypothesis: "The core owns IOMMU domains, interrupts, reset authority, and grant/revoke operations" | Narrowed for a breached hart: the state of I32, routes among it (I32's reading), and control operations (I34 (b)). Grants are static records here (R5.8) |
  | The M11 plan's descriptor: its `devices` and `interrupts` sections | Named as where a unit's entries would go (R5.1, R5.8). The schema is not changed |

- **What a device would make untrue.** These accepted statements stay
  true of a configuration with a device only where this revision's
  invariants are kept.
  - Part 1's required containment: "No domain reads or writes
    another's private state or the monitor's"; "no flow exists between
    domains except declared channels in their declared direction"; and
    "compromise of one domain does not compromise Beryllium or another
    domain's confidentiality or integrity". A VS domain could otherwise
    do each through its device. Within a boot they need I29 to I35.
    Across a system reset the last needs I37, and it does not hold of a
    later boot where I37 (c) has a limit name an owner. The second
    speaks of flows inside the platform: what two VS domains exchange
    through the world beyond their devices, the model does not see, and
    a claim about a configuration in which two VS domains own units
    says so.
  - I8; I16's "Every monitor-owned word shared between harts has one
    writer"; and I19's "Hart 0 alone writes the log page and the
    registers". Each needs I31 (c), with I29 and I35: a master could
    otherwise write the sealed state, such a word, or the log.
  - R4.3's containment of a breached, confined hart, which needs I38.

  No accepted claim rests on a configuration with a device: the claim
  ledger's row on the launch gate rests on I19 and I20 for images
  without one. So no claim changes, and the M14 plan's stop 5 is not
  met.
- **A fact that a master ends.** Until a VS domain owns a unit with a
  master, nothing but its own hart writes its private memory, so that
  memory does not change while that hart runs the monitor's code. A
  master of the unit can write it then. So can a master that a
  configuration's limit names, in any VS domain's memory that it
  reaches. I9 has every shared buffer "checked before use"; with such
  a master, what the monitor reads of that memory it has to read once.
  Whether a premise of a proof rests on the old fact is for the
  proof-impact review of the plan of step (3), as M11-R9 was for the
  boundary.
- **No device, no mechanism, and nobody to program one.** "Enforcing
  element", "identity", and "route" are all that this text assumes.
  Whether an IOMMU or an IOPMP confines a master, which device a VS
  domain is given, who writes the state of I32, and how a service
  speaks to those that it serves are for the plan of step (3). The
  accepted claim boundary of this document says that it does not
  "select a runtime mechanism"; that stays so.
- **The supervisor-domain specification.** Its frozen release `v0.9`
  (`9211c4cf`) has two chapters on what this revision models: "I/O MPT
  Checker" (`chapter6.adoc`) and "Supervisor Domain Interrupt
  Assignment" (`chapter7.adoc`). The first starts from a fact that this
  revision shares, that a device goes on issuing requests when no hart
  runs its holder: "DMA-capable devices connected to a supervisor
  domain remain continuously active". It also lets rules tell apart the
  requests of one device by a marking that the requests carry. This
  model does not express that: here a device has one holder (I30), and
  a marking that a device sets is an identity that a hostile device can
  claim (R5.4). This revision takes no term and no mechanism from
  either chapter, and names nothing of the project's by that
  specification's terms (S3-D's stop (k)). Whether a device path could
  be carried over to them is for MVP 2.0's last step (S3-D.3).
- **CHERI.** Nothing here uses a capability. A register extent, a
  master's reach, and an interrupt's route are each a bounded authority
  that a hardware capability could carry. That is a question for the
  CHERI platform line, and it is not answered here.
- **The precedents.** Neither is copied. seL4 `17.0.0` has no object
  for a whole device. It hands out device memory as ranges from which
  frames are made, and interrupts as one handler for each interrupt
  number, each apart; on x86 and on Arm, in configurations that are
  not verified, also an address space for a device's requests: on x86
  one for each PCI identity, and on Arm one that serves every stream
  that is bound to it. Its proofs "assume that these behaviours do not
  occur", a device's direct writes to memory among them, so that in
  its verified configurations "drivers handling such devices must be
  trusted to configure them safely" (`CAVEATS.md`, "Devices, DMA, and
  Device-Untypeds"). capDL describes, in one static specification, what
  is issued or is to be issued. It has an object type that joins a
  device's registers, its interrupt delivery, and its address space,
  and its tool does not check which capabilities such an object holds
  (`capDL-tool/doc/capDL.md`, "The Model"; `validObjCap`,
  `capDL-tool/CapDL/State.hs`). Both leave it to a trusted distributor
  to give a driver a consistent set. Here a unit is closed by rule
  (I30), the closure is checked (A11), and no owner is trusted for it.
- **Not proved, and not tried on a machine.** The invariants are
  specification, and the analyses are definitions, run by hand on one
  instance. Nothing here is a theorem of the abstract model.
- **Availability and side channels** are outside it, as they are
  outside the accepted model, but for what I33 (b), (c), and (f) say of
  a unit's interrupts. So is the world beyond a device.
- **Evidence.** R5.3 says what would show each invariant. What an owner
  reports of its device, and what a breached hart prints, show nothing.

### R5.11 What this revision does not change

The text above this section is byte-identical to its accepted form:
Parts 1 to 7, Revisions 1 to 4, the decision record, and the status
records. This section is appended. No code, no model file, no tool, no
scenario, no claim text, and no other accepted plan changes with it.
Two tools read this file, each finding a policy by its heading: the
MVP's policy checker compares the `te-poc` scenario's policy with
Instance 2's, and the model's fixture generator compares its own with
Instance 1's. What they read is unchanged, and this revision adds no
heading that either would match.

One accepted document does change, by one pin. Appending this section
changes this file's SHA-256. The claim ledger records that value as
evidence for its row on the launch gate (I19 and I20), and the ledger's
check compares it. The same commit therefore refreshes that pin and its
note, as Revision 4's commit did, and as the M14 plan's rule 10 has it.
The row's claim, methods, and non-claim are unchanged.

### Status record addendum (Revision 5)

```text
security_model_v1_revision_5=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
security_model_v1_revision_5_base=d0ec2aee4cf40d457139c900c71f4c9473762a1f
security_model_v1_revision_5_plan=mvp-m14-plan.md;work-package-M14-2;MVP-2.0-step-2-of-S3-C.2;before-the-plan-of-step-3
security_model_v1_revision_5_admitted_by=mvp-m14-plan.md-section-11;the-MVP-plan's-stop-condition-1-amended-by-name
security_model_v1_revision_5_classes_added=device;unit;reach;route;control;platform_description;interrupt-and-descriptor-instances
security_model_v1_revision_5_invariants_added=I29,I30,I31,I32,I33,I34,I35,I36,I37,I38
security_model_v1_revision_5_threat_model_added=attackers-a-VS-domain-that-owns-a-unit;a-hostile-or-defective-device;Revision-4's-attacker-on-a-hart-whose-profile-includes-a-unit's-registers;containment-required-where-the-master-is-confined;assets-recorded-reaches-routes-and-their-derived-state-the-platform-description-the-interrupt-files-what-a-unit-has-of-an-earlier-holder;allowed-effects-an-owner-on-its-own-unit-and-beyond-the-device;a-device-on-its-recorded-reach;a-breached-owner's-hart-on-its-units;a-unit's-masters-between-a-system-reset-and-the-next-handoff-named-in-the-limit-where-the-platform's-reset-does-not-bound-them;containment-the-monitor's-and-M-mode's-memory-other-VS-domains-declared-pages-other-units-the-enforced-state-interrupt-files-boot-sources;deferred-a-device-before-boot-code-has-quiesced-it;what-devices-do-other-than-by-requests-and-interrupts
security_model_v1_revision_5_tcb_rows_added=enforcing-elements;writer-and-protection-of-the-enforced-state;interrupt-controllers-and-routes;performer-of-control-operations-and-of-accesses-made-for-an-owner;platform-description-and-generator;offline-checks;boot-chain-device-reset-and-the-path-to-the-elements;devices-and-holders-outside-the-project's-control;platform-reset
security_model_v1_revision_5_notation_added=class-device-drive-interrupt-reset;a-unit-as-object-and-as-subject;Instance-4-worked-by-hand-with-ten-failing-variants
security_model_v1_revision_5_analyses_added=A9,A10,A11,A12,A13;A3-A5-A6-over-owners;A1-and-A8-extended;defined-only
security_model_v1_revision_5_h06=Instance-3-has-one-authority-without-a-mapping;a-device-adds-five-kinds-each-with-a-named-realization;none-by-default
security_model_v1_revision_5_h07=a-finer-type-only-where-the-policy-gives-different-authority;this-revision-adds-that-an-element-can-enforce-it
security_model_v1_revision_5_triggers_static_device_case=capability-trigger-does-not-fire;runtime-check-trigger-does-not-fire
security_model_v1_revision_5_tried_on=Instance-4;M13's-record-of-one-K3-COM260-board;QEMU-virt-at-v10.2.2-from-its-source;nothing-run
security_model_v1_revision_5_held_results=not-used;reads-the-same-whatever-they-show
security_model_v1_revision_5_readings=the-device-classes-added-before-a-configuration-has-a-device;a-unit-as-a-subject;A1-A3-A5-A6-A8-with-a-unit;the-report-schema;the-runtime-check-trigger-with-the-enforced-state;I9;I16-and-I23;I22c;I27;I28;R4.4's-row-for-other-contexts;the-deferred-lists;the-implementation-plan's-containment-and-hypothesis;the-descriptor's-devices-and-interrupts-sections
security_model_v1_revision_5_scope=configurations-in-which-the-sealed-configuration-assigns-a-unit-to-a-VS-domain;none-exists;a-unit-whose-holder-is-the-monitor-within-I29-I30-and-I38-alone;images-without-a-device-keep-the-accepted-model
security_model_v1_revision_5_design=not-selected;no-device;no-mechanism;nobody-to-program-one;chosen-in-the-plan-of-step-3
security_model_v1_revision_5_accepted_text_changed=none-in-this-document;the-claim-ledger's-pin-of-this-file-and-its-note-in-the-same-commit
security_model_v1_revision_5_code_change=none
security_model_v1_revision_5_model_change=none
security_model_v1_revision_5_claim_change=none
```
