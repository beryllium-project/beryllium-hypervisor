<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium hypervisor architecture notes: M-mode, SBI, and VS service decomposition

## Status and provenance

This page is a curated incorporation of the user-provided conversation export
`beryllium-hypervisor-notes.md`, added on 2026-07-22 as project design input.
It is not primary-source evidence and does not override selected decisions in
the architecture plans.

The source notes were corrected at incorporation time to match the project's
claim boundary:

- Beryllium and its HS core are **not** formally verified.
- Model 0.2 is a bounded abstract proof and host-test model, not a runtime.
- SBI compatibility for a future guest is distinct from selecting OpenSBI.
- The location and trust boundary of a future guest-facing SBI implementation
  remain open.
- A monolithic or decomposed VS control plane is a future runtime design gate,
  not a Model 0.2 decision.

## Incorporated design conclusions

| Topic | Current project treatment |
| --- | --- |
| Primary architecture | RISC-V H extension remains primary; Arm is conditional future portability work |
| Core boundary | Small HS isolation mechanism with rich services outside the trusted core remains selected |
| Assurance wording | Proof-oriented and incrementally machine checked; never describe the runtime or project as formally verified |
| Firmware | M-mode and firmware handoff are explicit trusted assumptions until a bounded runtime plan selects a decomposition |
| SBI | Future Linux-class RISC-V guests will require compatible SBI behavior; the provider and routing remain open |
| OpenSBI | Useful implementation and bring-up option, not an architectural requirement |
| VS control plane | Rich control-plane behavior belongs outside HS; monolithic versus multiple isolated VS services remains open |
| CHERI and compartmentalization | Strategic alignment input only; no CHERI, capability IPC, or service decomposition is authorized now |

## Arm and RISC-V orientation

| Axis | Arm AArch64 | RISC-V H extension | Planning significance |
| --- | --- | --- | --- |
| Hypervisor privilege | EL2 | HS-mode with virtualization state | Backend entry and trap contracts differ |
| Trap routing | `HCR_EL2` and exception controls | machine/supervisor and hypervisor delegation registers | Interception and delegation require architecture-specific models |
| Interrupt virtualization | GIC/vGIC | AIA with IMSIC/APLIC | Interrupt ownership and injection are separate backend obligations |
| Firmware ABI | PSCI/SMCCC | SBI | Boot, power, timer, and CPU-start interfaces differ |
| Bring-up implementation | EL3/firmware ecosystem | H extension may be exposed by an emulator beneath HS | Prototype trust boundaries must be explicit |

Both architectures provide two-stage translation:

```text
Arm:    guest VA -> IPA -> PA
RISC-V: guest VA -> GPA -> system PA
```

That similarity supports a common abstract translation contract, but it does
not make page-table formats, invalidation, interrupt behavior, or firmware
interfaces interchangeable.

## RISC-V M-mode boundary

M-mode is the highest mandatory RISC-V privilege and commonly owns some
combination of:

- early boot and hardware initialization;
- trap and interrupt delegation;
- hart bring-up;
- machine timers and interrupts;
- platform reset and power control; and
- SBI implementation.

For planning purposes, M-mode is closer to an Arm EL3/firmware boundary than
to the guest-visible HS isolation mechanism.

The selected Beryllium direction remains:

```text
M-mode firmware/runtime assumptions
                |
                v
small HS isolation mechanism
                |
                v
untrusted VS management, policy, I/O, and protected domains
```

The phrase “small HS isolation mechanism” is architectural intent. No current
Beryllium runtime implements or proves this stack.

## SBI and OpenSBI are different decisions

SBI is an architectural supervisor interface. OpenSBI is one implementation.

Linux-class supervisor software commonly expects SBI behavior for operations
such as:

- timer programming;
- hart start/stop and status;
- interprocessor interrupts;
- reset and power operations; and
- selected platform services.

A future Beryllium runtime therefore needs a bounded answer for how
SBI-compatible guest requests are trapped, validated, routed, and completed.
That answer need not require OpenSBI inside Beryllium.

### Candidate firmware decompositions

#### OpenSBI below HS

```text
OpenSBI in M-mode
        |
Beryllium in HS-mode
        |
VS domains
```

Benefits:

- fastest ecosystem-compatible bring-up;
- existing machine-level initialization and SBI implementation; and
- continuity with the completed Helium pathfinder.

Costs:

- OpenSBI and its configuration remain below the proof boundary;
- M-mode ownership and delegation assumptions stay trusted; and
- guest-facing SBI virtualization still needs an explicit HS/VS design.

The accepted bounded single-hart runtime plan uses this decomposition only for
its fixed synthetic first profile. Implementation was separately authorized on
2026-07-25. It provides no guest-visible SBI and does not select OpenSBI for a
later Linux profile.

#### Beryllium-owned M-mode component

```text
Beryllium M-mode component
        |
Beryllium HS isolation mechanism
        |
VS domains
```

Potential benefit:

- tighter ownership of the complete boot and delegation contract.

Costs:

- substantially larger implementation and assurance scope;
- machine-timer, interrupt, reset, and platform support burden; and
- a wider architecture-specific trusted base.

This option is not selected.

#### Minimal independent M-mode runtime

```text
minimal M-mode runtime
        |
Beryllium HS isolation mechanism
        |
VS domains
```

The M-mode component could be limited to boot, delegation, machine-level
timer/interrupt ownership, reset, and a narrow SBI bridge. This is a candidate
boundary to compare with OpenSBI reuse, not an approved implementation.

## What happens to a VS guest SBI call

An SBI call from a VS guest is not a direct call to OpenSBI. The guest places
the SBI extension, function, arguments, and return registers according to the
SBI binary convention and executes `ecall`. The H extension reports this as
the environment-call-from-VS exception. When M-mode delegates that exception,
HS receives it; the corresponding `hedeleg` bit is not writable, so HS cannot
delegate the same call straight back to VS.

The normal routing shape is:

```text
VS guest -- SBI ecall --> HS virtual-SBI dispatcher
                           |-- emulate virtual behavior in HS
                           |-- validate and forward a bounded request to M-mode
                           |-- RPC to a designated VS control service
                           `-- reject with a defined SBI error
```

HS must identify the current domain and validate the extension, function,
addresses, hart masks, target vCPUs, rights, and lifecycle phase before any
route can affect platform state. Physical hart operations are not blindly
equivalent to a guest's virtual hart request. Linux KVM and Xvisor both
implement guest SBI dispatch at the hypervisor layer and selectively emulate
or forward operations.

### Is there an OpenSBI module in VS?

Ordinary OpenSBI is M-mode-oriented platform firmware. It expects machine-mode
trap, interrupt, and platform facilities and supplies SBI to the next
supervisor layer. Calling an ordinary peer-VS component "OpenSBI for the
guest" would therefore be misleading.

Three descriptions remain accurate:

- In one deployment option, OpenSBI runs in M-mode below Beryllium, while HS
  implements guest-visible virtual SBI behavior.
- HS provides a guest-visible SBI subset, independently or by reusing bounded
  OpenSBI behavior, without running OpenSBI in VS.
- A separate VS service implements selected paravirtual firmware or control
  behavior, but HS traps, authenticates, mediates, and completes every guest
  SBI call.

A separate VS service is possible when higher-level lifecycle, virtual-device,
attestation, or policy behavior is large enough to justify another domain. It
is not more privileged than the calling VS domain. It cannot directly program
G-stage state, inject interrupts, change vCPU lifecycle, or call M-mode on
another domain's behalf without HS validation. It also adds scheduling,
restart, replay, timeout, and reply-validation obligations. Service failure
must deny or return a bounded guest-visible error rather than create
authority.

The selected planning candidate is narrower than that comparison point: its
synthetic VS stubs have no guest-visible SBI, and their exact `ecall` events
are a private test protocol. A small HS virtual-SBI adapter remains a later
Linux-planning question. A separate VS service should be evaluated only if
concrete rich behavior would otherwise expand HS materially.

Nested virtualization is different. A VS-resident L1 hypervisor may provide
virtual SBI to its L2 guests only when L0 emulates the required H-extension
and nested state. That does not make a peer VS service the direct recipient of
another guest's SBI `ecall`.

## Guest-facing SBI decision gate

A future runtime plan must distinguish at least three interfaces:

1. the SBI implementation used by HS during platform boot;
2. the virtualized SBI interface exposed to a VS management or guest domain;
3. the internal HS-to-M-mode call or forwarding contract.

It must answer:

- Which SBI extensions are required by the first bounded guest?
- Which requests are emulated in HS, delegated to a VS service, or forwarded
  to M-mode?
- Which caller identity and resource ownership checks precede each request?
- How are timer, interrupt, hart, reset, and power operations constrained?
- What state is trusted, copied, validated, measured, or assumed?
- What is the failure behavior for unsupported, stale, or malicious requests?
- Which OpenSBI behavior is reused, and which behavior is independently
  implemented?

Model 0.2 deliberately models none of these operations.

## VS control-plane decomposition

The selected high-level rule is mechanism in HS and rich control behavior in
mutually untrusted VS domains. The exact VS decomposition remains open.

### One management/control domain

```text
HS isolation mechanism
        |
one VS management/control domain
        |
managed VS guests
```

Potential benefits:

- smaller initial protocol surface;
- simpler bring-up and debugging; and
- easier reuse of existing Linux/VMM tooling.

Risks:

- large failure and compromise domain;
- policy, lifecycle, device, and attestation code become mutually exposed; and
- later decomposition may require interface redesign.

### Multiple isolated VS services

```text
HS isolation mechanism
        |
        +-- VM lifecycle service
        +-- device service
        +-- scheduling-policy service
        +-- attestation service
        +-- orchestration service
```

Potential benefits:

- narrower service authority;
- independent restart and update boundaries;
- stronger fault containment; and
- alignment with CHERI/CHERIoT compartmentalization principles.

Costs:

- more explicit channels and protocol validation;
- more lifecycle, dependency, and availability behavior;
- larger configuration and proof surface; and
- risk of prematurely designing a microservice architecture without a
  concrete need.

No current phase selects either shape. A later bounded runtime plan should
start with the least decomposition needed to test an unresolved core
mechanism, then require explicit evidence before adding services.

## Relationship to the current design process

These notes add two explicit future review gates:

1. **M-mode and SBI boundary:** select and justify the firmware reuse,
   guest-facing SBI virtualization, and HS-to-M-mode contract.
2. **VS control-plane boundary:** decide whether the first bounded runtime
   needs one management domain or multiple isolated services.

Responsible-human acceptance of Model 0.2 on 2026-07-24 satisfied the first
prerequisite for considering these gates. The selected planning candidate
uses OpenSBI below HS and no guest SBI only for one synthetic profile. The
exact fixed implementation was authorized on 2026-07-25, while the later Linux
and decomposed-service gates remain open.

## Primary references

Checked 2026-07-24:

- RISC-V Hypervisor Extension, including VS exception and trap delegation:
  <https://docs.riscv.org/reference/isa/priv/hypervisor.html>
- RISC-V SBI binary encoding:
  <https://github.com/riscv-non-isa/riscv-sbi-doc/blob/master/src/binary-encoding.adoc>
- RISC-V SBI nested-acceleration extension:
  <https://github.com/riscv-non-isa/riscv-sbi-doc/blob/master/src/ext-nested-acceleration.adoc>
- OpenSBI library integration:
  <https://github.com/riscv-software-src/opensbi/blob/master/docs/library_usage.md>
- Linux KVM RISC-V virtual SBI dispatch:
  <https://github.com/torvalds/linux/blob/master/arch/riscv/kvm/vcpu_exit.c>,
  <https://github.com/torvalds/linux/blob/master/arch/riscv/kvm/vcpu_sbi.c>,
  <https://github.com/torvalds/linux/blob/master/arch/riscv/kvm/vcpu_sbi_hsm.c>
