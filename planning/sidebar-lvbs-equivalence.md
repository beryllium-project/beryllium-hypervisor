<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Sidebar: optional Linux VBS-equivalence

## Status and terminology

This page uses **LVBS-equivalence** as a Beryllium planning term for an optional
future Linux-oriented architecture with hypervisor-protected security
services. It is not a selected profile, a standard, or a claim of compatibility
with Microsoft VBS.

Microsoft's LiteBox repository also uses `lvbs` in an x86 VTL1 platform name,
but it does not define a portable Beryllium interface.

## The useful VBS reference properties

Windows VBS/Virtual Secure Mode combines a hypervisor-enforced higher trust
context with services that remain protected from a compromised normal kernel.
Representative services include:

- HVCI or memory integrity for kernel code-integrity decisions and W^X;
- App Control/UMCI policy for executable user and kernel code;
- Credential Guard/LSA isolation for secrets;
- virtual TPM and measured-boot services;
- VBS enclaves with narrow call gates; and
- per-VTL memory and processor state.

The transferable idea is not "copy VTL1." It is:

> Keep the smallest enforcement mechanism below the compromised OS, and place
> higher-level security services in protected contexts with narrow interfaces.

## Candidate Beryllium decomposition

```text
M-mode firmware and root-of-trust assumptions
                |
restricted-C HS isolation mechanism
                |
                +-- management Linux VS
                +-- code-integrity VS service
                +-- secrets/vTPM VS service
                +-- measurement/attestation VS service
                +-- optional policy-compilation/appraisal VS service
```

This requires more than Model 0.2:

- lifecycle and protected-domain creation;
- interrupt, timer, scheduling, and availability behavior;
- executable mapping transitions;
- measurements and hardware roots of trust;
- device/DMA isolation;
- rollback protection; and
- authenticated, versioned service protocols.

None is currently authorized.

## Candidate service roles

### HVCI-equivalent code-integrity service

The service could hold trusted signer, image, and policy identities. HS would
remain the enforcement point:

1. management Linux proposes an executable mapping;
2. HS identifies the exact domain, frame, image, rights, and generation;
3. a protected service evaluates the measured code identity;
4. HS installs an executable, non-writable mapping only if the response is
   valid and within the sealed authority ceiling.

The service must not write page tables directly. An authorization is not a
capability to exceed canonical ownership.

### UMCI/App-Control-equivalent service

Linux already has useful lower-layer adapters:

- IPE for immutable execution properties;
- fs-verity and dm-verity for measured immutable content;
- IMA/EVM for measurement and appraisal; and
- LSMs and Landlock for in-domain policy.

A protected VS service could independently appraise signer, digest, origin,
policy generation, or deployment profile. HS mediation of every user
`mprotect(PROT_EXEC)` would be too broad without a carefully bounded execution
model; a first experiment should use immutable executable objects, not general
JIT behavior.

### Secrets and key-guarding service

A secrets service could expose only operations such as:

- sign or verify;
- derive a session key;
- seal or unseal to a measured configuration;
- attest a service identity; and
- release a secret only to an approved channel endpoint.

The hard invariant should be that secret-bearing private pages are never
mapped into management Linux. The service-specific correctness and crypto
implementation would still be trusted for claims about key use.

### Measurement and attestation service

HS could emit immutable measurement events for:

- canonical configuration;
- service image and initial state;
- policy and enforcement profile;
- channel endpoints; and
- security version or rollback floor.

A protected service could format and sign evidence using RATS/EAT or a
deployment-specific protocol. It must not be able to forge HS measurements.

## Additional protected-service candidates

These candidates test different boundaries. Dynamic code integrity is close
to a VBS code-integrity service. Protected logging is a security service with
strict source and freshness limits. Driver domains are primarily an I/O
service-domain pattern rather than a VBS analogue.

### Dynamic component and JIT code integrity

A bounded loader could link or relocate signed components in service-private
staging memory that is never mapped into management Linux, then ask HS to
publish the exact final bytes as executable. A safe publication sequence is:

1. copy the candidate and metadata into private staging;
2. verify signer, manifest, dependency, relocation, and rollback constraints;
3. link or relocate while the output is writable and non-executable;
4. measure and authorize the exact final bytes after all mutation;
5. publish fresh frames only after removing every writable CPU and DMA alias;
6. install an RX, never W+X, consumer mapping; and
7. complete the architecture's instruction-fetch coherence protocol before
   entry.

Verifying guest-owned bytes and later remapping the same mutable frame would
leave a time-of-check/time-of-use gap. Checking only the consumer PTE would
also be insufficient if another root, the loader, or a device retains a
writable alias.

General JIT support is a larger claim than immutable component loading. The
JIT compiler, relocation logic, input policy, and final-byte authorization
join the code-integrity TCB. A signature over source components does not by
itself authorize the linked output. On RISC-V, local `FENCE.I` is not a
multihart publication protocol. The first bounded experiment should therefore
publish one fixed signed component on one hart, not support an arbitrary JIT.

### Protected security logging

A logging VS could keep an append key, sequence number, chain head, and
protected persistence or remote-anchor state outside management Linux. Each
accepted record could bind:

```text
sequence + event source + event bytes + previous head + configuration identity
```

with a MAC or signature. A protected monotonic anchor or externally retained
head can make later modification, replay, rollback, or truncation detectable.

The supportable property is narrow. If a compromised guest kernel is the
event source, it can omit an event, lie about its meaning or timestamp, flood
the service, block storage or networking, or reset the logger. The protected
service can authenticate what crossed a trusted hook; it cannot prove that an
event it never observed occurred. A complete design must define trusted event
origins, acknowledgement ordering, persistence failure, counter exhaustion,
restart, and availability.

CHERI could separate the untrusted parser/export path from a small key-holding
append compartment inside the logging VS. That limits in-domain authority; it
does not create a separately scheduled VS, establish event truth or
freshness, or replace a protected persistence and stage-2 boundary.

### Driver domains

A driver domain would place one hardware driver and backend protocol in a
dedicated VS domain. Consumers would use only explicit shared queues and
notifications. HS, not the driver, would retain ownership of:

- device assignment and MMIO extents;
- IOMMU translation and IOPMP protection state;
- interrupt routing and masking;
- DMA grant and invalidation;
- quiesce, reset, and reassignment; and
- the channel endpoints exposed to consumers.

G-stage isolation alone does not constrain a bus-mastering device. Restart is
safe only after DMA is quiesced, interrupts are masked, stale I/O translations
are invalidated, all coupled functions are reset, and shared firmware or
device state is understood. Peer-to-peer DMA, non-resettable devices, shared
IOMMU groups, stale interrupts, and compromised device firmware remain
explicit failure cases.

CHERI compartments may reduce the blast radius among parsers, protocol code,
and individual drivers inside that domain. They do not constrain DMA or
replace a distinct VS root, IOMMU/IOPMP ownership, or device reset. Driver
domains are necessarily later than Model 0.2 because devices, interrupts,
DMA, IOMMU/IOPMP, lifecycle, and restart are all currently excluded.

## Relevant open precedents

| System | Transferable lesson | Limit |
| --- | --- | --- |
| pKVM | ownership, donation, explicit sharing, compromised host threat | incomplete general VBS service stack; Arm-specific |
| RISC-V AP-TEE/CoVE | HS trusted manager and SBI host/guest interfaces | specification and ecosystem remain evolving |
| Coconut-SVSM | protected vTPM and service module above SEV-SNP VMPLs | AMD-specific and confidential-VM scoped |
| OpenHCL/OpenVMM | open Rust paravisor with vTPM, device, and confidential services | x86/Arm and cloud-specific trust model |
| Linux IPE/fs-verity/dm-verity | immutable code and image evidence | enforcement remains inside Linux unless independently checked |
| Keylime/RATS | open attestation infrastructure and role model | does not create the underlying isolation or measurements |

These are references, not dependencies selected for Beryllium.

## How Beryllium could go beyond existing VSM and sidecar designs

### Explicit authority instead of an implicit privilege hierarchy

Each service would receive only declared resources and channels. A higher
"trust level" would not automatically grant access to all lower domains.

### Multiple restartable security principals

Code integrity, secrets, attestation, and devices could have separate roots
and failure domains. A compromised code-integrity service should not read a
secrets service's private memory.

This decomposition is valuable only if protocol and lifecycle cost stays
smaller than the risk it removes.

### Open configuration and assurance

A deployment could publish:

- canonical authority and channel graphs;
- exact service and policy identities;
- proof assumptions;
- mapping and measurement reports;
- protocol state machines; and
- architecture-specific evidence adapters.

The goal would be an inspectable profile, not an undocumented secure-kernel
ABI.

### Cross-ISA service semantics

The service contract could be architecture-neutral while enforcement adapters
map to RISC-V G-stage, Arm stage-2/RME, or x86 EPT/NPT/VMPL/VTL mechanisms.
This is a long-term property, not current portability evidence.

### Secrets never enter management Linux

Management Linux could request an operation, but plaintext key material and
private service memory would never be mapped into its G-stage root. This is a
stronger review target than merely hardening a daemon inside Linux.

## Hard limits

- **DMA:** G-stage isolation is insufficient until IOMMU/IOPMP ownership and
  reset are enforced.
- **Availability:** a service or management domain can withhold scheduling or
  replies unless the runtime supplies independent scheduling and recovery.
- **Rollback:** old service, policy, or firmware images remain dangerous
  without a hardware-backed version floor.
- **Policy correctness:** correct enforcement does not prove that signer,
  digest, or release policy matches operator intent.
- **I/O and UI:** credential input, display, storage, and network paths may
  expose secrets outside the protected service.
- **Side channels:** shared caches, predictors, timers, and power behavior
  remain outside current claims.
- **Update atomicity:** service, policy, cache, and enforcement generations
  require one explicit commit protocol.
- **TCB growth:** every service needed for a property joins that property's
  TCB even if it is outside HS.

## Bounded future experiments

1. **Code-integrity gate:** one immutable image identity and one executable
   mapping transition; no general loader.
2. **Secrets isolation:** one test key and one signing operation; prove/test
   that management Linux never maps the private frame.
3. **Generation protocol:** update one policy generation and prove old replies
   cannot authorize new mappings.
4. **Measurement chain:** HS emits one configuration/image event and a
   protected service signs an evidence object.
5. **Service failure:** kill, stall, replay, and restart one service; confirm
   HS remains fail closed.
6. **Code publication:** publish one fixed linked image from private staging
   as RX and prove/test that no writable CPU or DMA alias remains.
7. **Protected log:** append one chained event, then test modification,
   replay, truncation, reset, and unavailable-anchor behavior.
8. **Driver domain:** only under a device-specific plan, assign one emulated
   device and test DMA, interrupt, crash, quiesce, reset, and reassignment
   containment.

Model 0.2 is accepted, but the selected synthetic runtime-planning phase
explicitly excludes these services. Every experiment still requires a later
explicit phase selection and new approved bounded plan.

## Future decision gate

An LVBS-equivalent path should remain optional unless a concrete protected
service demonstrates:

- a threat that in-Linux mechanisms cannot adequately address;
- a smaller and clearer TCB than available alternatives;
- complete authority, lifecycle, update, and availability contracts;
- a viable DMA/device story;
- measurable benefit over pKVM, CoVE, SVSM, or OpenHCL reuse; and
- assurance evidence that does not depend on proprietary tools or claims.

## Primary references

Checked 2026-07-24:

- Hyper-V VSM/VTL specification:
  <https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/tlfs/vsm>
- HVCI/memory integrity:
  <https://learn.microsoft.com/en-us/windows/security/hardware-security/enable-virtualization-based-protection-of-code-integrity>
- HVCI code-integrity checks and compatible-code constraints:
  <https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/code-integrity-checking>,
  <https://learn.microsoft.com/en-us/windows-hardware/drivers/driversecurity/implement-hvci-compatible-code>
- App Control for Business:
  <https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/appcontrol-and-applocker-overview>
- Credential Guard:
  <https://learn.microsoft.com/en-us/windows/security/identity-protection/credential-guard/how-it-works>
- VBS enclaves:
  <https://learn.microsoft.com/en-us/windows/win32/trusted-execution/vbs-enclaves>
- OpenHCL:
  <https://github.com/microsoft/openvmm/blob/main/Guide/src/reference/architecture/openhcl.md>
- pKVM:
  <https://www.kernel.org/doc/html/next/virt/kvm/arm/pkvm.html>
- RISC-V AP-TEE:
  <https://github.com/riscv-non-isa/riscv-ap-tee>
- Coconut-SVSM:
  <https://github.com/coconut-svsm/svsm>
- Linux IPE, fs-verity, and dm-verity:
  <https://docs.kernel.org/admin-guide/LSM/ipe.html>,
  <https://docs.kernel.org/filesystems/fsverity.html>,
  <https://docs.kernel.org/admin-guide/device-mapper/verity.html>
- RATS architecture:
  <https://www.rfc-editor.org/rfc/rfc9334.html>
- RISC-V instruction-fetch coherence:
  <https://docs.riscv.org/reference/isa/v20260120/unpriv/zifencei.html>
- Sinha et al., continuous TPM-backed tamper-proof logging:
  <https://aruneshsinha.net/Files/Other/Papers/tpm.trust.2014.pdf>
- Xen driver domains:
  <https://wiki.xenproject.org/wiki/Driver_Domain>
- CHERIoT compartment model:
  <https://cheriot.org/book/compartments.html>
- Existing project synthesis:
  [Supervisory security policy](supervisory-security-policy.md)
