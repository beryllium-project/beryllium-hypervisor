<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Supervisory security policy and attestable enforcement

## Status and purpose

This document captures the 2026-07-22 analysis of whether Rego could provide
a top-level policy framework for a higher-assurance, policy-driven hyperscale
architecture spanning:

- access control and privilege management;
- signature-verified code integrity;
- image-based Linux and Linux Integrity Policy Enforcement (IPE);
- HVCI-, UMCI-, and enclave-style code-integrity profiles;
- measured boot, attestation, and reference values;
- image and component composition;
- confidential computing, including Confidential Azure Container Instances
  (C-ACI) and Confidential Containers; and
- a possible future relationship to Beryllium.

The term **supervisory security policy** is a candidate abstraction in this
document, not an already selected Beryllium component or stable interface.
The terminology is descriptive: this public-source analysis makes no novelty
claim and does not incorporate or cite non-public organizational material.

This document does not:

- add Rego, OPA, Cedar, or another policy engine to Beryllium;
- select a manifest encoding or hyperscale control-plane architecture;
- authorize a runtime, confidential-computing, CAP+TE, HVCI, UMCI, IPE, or
  enclave implementation;
- claim formal verification of Rego, OPA, C-ACI, Confidential Containers, or
  a proposed composition; or
- change the Model 0.1 ownership and explicit-channel baseline.

This material is retained for a later evaluation phase. Architecture Model
0.2 first refines the policy-neutral core hypervisor mechanism and does not
evaluate Rego, Cedar, supervisory-policy integration, or other policy
frameworks.

## Core conclusion

Rego is a strong candidate for the **policy authoring, composition, admission,
and attestation-appraisal plane**. Rego or OPA should not be the normative root
of a higher-assurance security architecture.

The normative root should instead be an engine-independent, signed,
content-addressed supervisory contract that defines:

- the component and image graph;
- trust roots and delegated issuers;
- policy identities and scopes;
- expected measurements and reference values;
- required enforcement profiles;
- policy precedence and conflict behavior;
- security versions and rollback rules;
- permitted dynamic transitions; and
- audit and attestation bindings.

Rego may author or evaluate parts of that contract. The security meaning must
remain stable if a policy engine is replaced.

## C-ACI evidence

C-ACI provides strong evidence for a bounded policy-and-attestation pattern:

1. A customer CCE policy is generated or authored in Rego.
2. Its SHA-256 digest is placed in the AMD SEV-SNP `HOST_DATA` field and is
   therefore authenticated in the attestation report.
3. The utility VM (UVM) has a separate launch measurement and security version
   number (SVN), carried in Microsoft-signed reference information.
4. The policy is enforced inside the protected UVM against host-requested
   operations such as image-layer mounting, container creation, command and
   environment selection, and process execution.
5. A relying party checks the AMD evidence chain, debug state, UVM
   measurement, UVM freshness, expected policy digest, and report freshness
   before releasing sensitive material.

The CCE policy can permit signed policy fragments identified by issuer and
feed and bounded by a minimum SVN. This provides a practical model for
delegated, updateable policy composition without trusting an unsigned mutable
namespace.

C-ACI does not establish Rego as a universal policy framework. It establishes
the more precise pattern:

```text
expected policy digest
AND measured and endorsed enforcer
AND fresh hardware evidence
AND complete enforcement hooks
  -> relying-party acceptance
```

The policy digest alone is insufficient. A relying party must also trust the
identity and freshness of the code that interprets and enforces the policy.

## Confidential Containers evidence

Confidential Containers uses multiple cooperating policies:

| Policy | Enforcement point | Purpose |
| --- | --- | --- |
| Kata agent policy | Kata agent inside the TEE | Constrain agent and workload operations |
| Attestation service policy | Trustee attestation service | Appraise evidence against reference values |
| KBS resource policy | Trustee KBS | Decide which resources or secrets may be released |

The Kata policy can be delivered through measured init-data. The attestation
service can reflect that evidence in an attestation token, and the KBS policy
can require the expected init-data or policy identity before releasing a
secret.

This is evidence for a **federation of scoped policies**, not one policy
language replacing all security mechanisms. It also motivates a supervisory
contract that defines how workload, appraisal, resource-release, platform,
and tenant policies compose.

## Distinct security roles

A holistic architecture must not collapse several different operations into
the word "policy":

| Role | Security function |
| --- | --- |
| Signature verification | Establish artifact provenance and delegated authority |
| Hashing and measurement | Identify exact content and launch/configuration state |
| Attestation | Convey authenticated, fresh evidence about an attester |
| Reference-value appraisal | Compare evidence with endorsed or expected state |
| Authorization policy | Decide whether a requested action is permitted |
| Enforcement | Preserve the permitted state and mediate operations |
| Information-flow analysis | Constrain what data may influence which destinations |
| Audit/transparency | Record decisions, updates, and provenance for later review |

Rego is well suited to decisions over normalized structured claims. It does
not produce hardware evidence, preserve executable-page integrity, install
G-stage mappings, or prove noninterference.

OPA includes cryptographic and token-related built-ins, but a higher-assurance
design should authenticate evidence and signatures in dedicated, bounded
verification code. Rego should normally consume already authenticated,
normalized claims rather than duplicate vendor evidence parsers and trust
stores inside policy.

## Candidate supervisory contract

A future supervisory contract could have the following shape:

```text
Signed supervisory security manifest
  |-- trust roots, delegated issuers, and administrative roles
  |-- component/image composition graph and content digests
  |-- kernel, initrd, firmware, policy, and data-bundle identities
  |-- dm-verity roots, fs-verity digests, and code-signing roots
  |-- expected measurements and reference-value set identities
  |-- policy engine, version, feature profile, and input/output schema
  |-- required HVCI, UMCI, IPE, enclave, CAP/TE, IOMMU profiles
  |-- policy precedence, deny semantics, and conflict rules
  |-- security version, epoch, update authority, and rollback floor
  |-- permitted delegation, release, and declassification transitions
  `-- audit, transparency, and attestation claim requirements
                         |
                  compile or appraise
                         v
Scoped policy modules
  workload / authorization / attestation / resource release / network
                         |
                         v
Enforcement adapters
  Beryllium / HVCI / UMCI / IPE / enclave loader / runtime / IOMMU
                         |
                         v
Evidence and attestation
  RATS roles / EAT or platform tokens / CoRIM / measured-boot logs
```

The supervisory contract is a policy of policies. It specifies which
subordinate policy authorities exist, what each may decide, how conflicts are
resolved, which evidence each decision requires, and how updates change the
attestable state.

The manifest should be content-addressed and signed. Its digest, or a digest
of an unambiguous canonical representation, should be bound into
platform-specific attested owner/configuration data where the platform
supports that operation. The attestation must also identify the enforcer and
its security version.

Hardware platforms expose different measurement and owner-data fields. The
architecture must define per-platform evidence adapters rather than claim
that every platform extends the same manifest digest into one identical
measurement register.

## Binding requirements

A credible binding between policy, code integrity, composition, and
attestation requires all of the following:

1. **Canonical identity:** every component, policy bundle, reference-value
   set, and enforcement profile has an unambiguous digest.
2. **Authenticated provenance:** signatures and delegation chains identify
   who may approve each artifact or policy scope.
3. **Measured or attested configuration:** evidence binds the expected
   manifest or policy digest to the launched environment.
4. **Enforcer identity:** evidence identifies the code and configuration that
   interpret and enforce the policy.
5. **Freshness and rollback resistance:** nonce handling, SVN or monotonic
   epochs, revocation, and update floors prevent acceptance of known-old
   policy or code.
6. **Complete mediation:** each relevant operation reaches an enforcement
   adapter with the actual subject, object, operation, and policy generation.
7. **State-transition control:** dynamic policy, image, signer, or authority
   changes are authorized, versioned, audited, and reflected in later
   evidence.
8. **Composite evidence:** CPU, firmware, hypervisor, guest, device, and
   workload claims are joined without treating an unmeasured layer as
   measured.

An attestation says what evidence an attester can provide. The verifier
authenticates and appraises that evidence. The relying party still decides
whether the result is sufficient for a specific action.

## Code-integrity and image-composition adapters

| Mechanism | Suitable supervisory binding |
| --- | --- |
| Image-based Linux | Signed image/component graph plus dm-verity root identities |
| IPE | Required policy identity, version, trusted keyrings, dm-verity/fs-verity properties, and activation state |
| IMA/EVM | Measurement-log and protected-metadata claims used as additional evidence |
| HVCI-style enforcement | Hypervisor/secure-kernel identity, code-signing policy, writable/executable transition rules, and enforcement mode |
| UMCI-style enforcement | User-mode signer/hash policy and loader/runtime enforcement identity |
| Enclave loading | Initial measurement, signer/product/security version, debug state, and dynamic-page policy |
| Container composition | Ordered image-layer identities, overlay rules, commands, environment, mounts, capabilities, and runtime identity |
| Supply chain | TUF/in-toto/SLSA/Sigstore provenance referenced by, but not substituted for, runtime policy |

IPE is especially compatible with fixed, image-based Linux systems because it
can make decisions from immutable properties such as dm-verity roots,
fs-verity digests, and trusted signatures. IPE is an enforcement adapter, not
the supervisory architecture. Its policy signature and versioning rules must
also be bound into the deployment contract.

HVCI, UMCI, and enclave mechanisms should similarly be modeled as enforcement
profiles. Rego can decide whether reported claims satisfy a profile; it does
not replace the privileged mechanism that prevents unauthorized executable
code or mutable executable mappings.

## Rego role and required profile

Rego is attractive because it:

- evaluates structured evidence and configuration;
- composes policy from multiple organizational scopes;
- has a broad cloud-native ecosystem;
- supports offline testing, partial evaluation, and WebAssembly compilation;
- supports signed OPA bundles; and
- already appears in C-ACI and Confidential Containers policy paths.

For a higher-assurance supervisory use, unrestricted Rego is too broad. A
defined profile should require:

- one pinned Rego language version and policy-engine implementation/profile;
- fixed input and output schemas;
- a total top-level decision with explicit default denial;
- explicit deny/forbid precedence and conflict reporting;
- a bounded allowlist of deterministic built-ins;
- no network, wall-clock, random, or mutable external-data built-ins during a
  security decision;
- bounded input sizes, evaluation time, memory, and output cardinality;
- signed, content-addressed bundles;
- an externally enforced monotonic policy epoch or SVN;
- canonical normalization of vendor evidence before evaluation;
- tests for independent allow, deny, malformed, stale, and conflicting cases;
- policy coverage and static-analysis gates; and
- engine conformance or differential testing against a reference
  implementation.

Rego remains dynamically evaluated over structured data. OPA schemas, strict
mode, and linting catch important errors but do not provide a machine-checked
refinement from policy source to an enforcement result.

OPA bundle signatures establish bundle integrity and provenance. A bundle
revision field does not by itself establish monotonic rollback prevention; the
supervisory contract and deployment system must enforce freshness.

WebAssembly compilation changes the deployment and isolation shape. It does
not prove the compiler, policy, host built-ins, or WebAssembly runtime correct.

## Candidate alternatives and complements

No single candidate covers authorization, integrity, attestation,
information flow, and enforcement.

| Candidate | Strongest role | Important limit |
| --- | --- | --- |
| Rego/OPA | General policy composition, admission, and evidence appraisal | No verified engine or native information-flow model |
| Cedar | Bounded principal/action/resource authorization with analyzable semantics | Not an attestation, integrity, or system-construction language |
| KeyNote, SecPAL, RT | Signed delegation and distributed trust management | Older or research-oriented ecosystems |
| NIST NGAC | Unified graph-based access-control and administrative policy | Does not provide code integrity or attestation |
| CEL | Constrained embedded predicates and admission checks | Less expressive as a complete authorization model |
| CUE or Dhall | Typed manifest construction and configuration constraints | Not an enforcement or authorization architecture |
| SELinux CIL | Linux TE, RBAC, MLS/MCS policy intermediate representation | Linux MAC scope rather than hyperscale supervisory policy |
| seL4 capDL | Static capability/system construction with strong assurance lineage | Not a hyperscale dynamic policy control plane |
| RATS, EAT, CoRIM | Attestation roles, claims, and reference values | Standards and formats, not authorization languages |
| TUF, in-toto, SLSA, Sigstore | Distribution and supply-chain provenance | Do not decide or enforce runtime access |
| IPE, IMA, fs-verity, dm-verity | Linux integrity enforcement and evidence | Domain mechanisms rather than supervisory policy |

Cedar has a Lean formalization and proofs about the language, with
differential randomized testing against the Rust production implementation.
That is stronger language evidence than Rego currently provides, but it is not
an end-to-end proof of the production engine.

KeyNote is particularly relevant to signed policy composition because its
model combines local policy, public-key principals, signed delegation
credentials, and a compliance checker. Its concepts are useful even if its
implementation ecosystem is not selected.

NGAC is relevant when evaluating a single graph-based administrative model
that can represent multiple access-control styles. It remains complementary
to measurement, code integrity, and attestation.

## Possible future Beryllium relationship

Beryllium could eventually be framed as a minimal enforcement and evidence
root beneath a hyperscale supervisory policy architecture:

- consume only a compact, validated canonical manifest and bounded
  enforcement tables;
- enforce an immutable ceiling over CPU, memory, devices, channels, and any
  later approved capability or mandatory-policy state;
- bind manifest, authority-graph, policy-generation, and enforcement-profile
  identities into platform evidence;
- allow a rich VS policy service to evaluate Rego, Cedar, or another language
  and propose narrower decisions;
- independently reject proposals that exceed the measured ceiling;
- preserve ceiling enforcement when the rich policy service is unavailable;
- model every accepted dynamic authority transition; and
- prove local authority and global information-flow properties independently
  of policy-engine testing.

Full OPA, Rego, Cedar, or another application policy engine should not execute
inside a small HS isolation core. Rich authoring and appraisal tools belong
offline, in a policy domain, or in a remote verifier. HS should consume
bounded data and perform deterministic validation and enforcement.

This framing is consistent with the existing offline pipeline in
[`implementation-plan.md`](implementation-plan.md):

```text
system source + board description + policy source
  -> typed IR
  -> normalized platform descriptor
  -> canonical security manifest
  -> Rocq configuration
  -> authority graph
  -> audit report
  -> measurement inputs
```

That existing direction should remain language-neutral. Rego convergence at
the control and appraisal layers must not create a Rego dependency in the
Beryllium core.

## Supportable conclusion and required limit

**Supportable conclusion:** C-ACI and Confidential Containers demonstrate
useful Rego-based policy, signed-fragment, measured-configuration, attestation
appraisal, and secret-release patterns. Rego is a credible common language for
some hyperscale control-plane and verifier policies.

**Required limit:** those systems do not establish Rego as a universal
security policy or a high-assurance enforcement core. A future supervisory
architecture must define language-independent composition semantics, trusted
enforcement adapters, freshness, complete mediation, and evidence bindings.

## References

- Open Policy Agent,
  [Rego policy language](https://www.openpolicyagent.org/docs/policy-language).
- Open Policy Agent,
  [policy bundles and signing](https://www.openpolicyagent.org/docs/management-bundles).
- Microsoft,
  [Attestation in Confidential Containers on Azure Container Instances](https://learn.microsoft.com/en-us/azure/container-instances/confidential-containers-attestation-concepts).
- Microsoft,
  [Confidential ACI verification scheme](https://github.com/microsoft/confidential-aci-examples/blob/main/docs/Confidential_ACI_SCHEME.md).
- Confidential Containers,
  [Policies](https://confidentialcontainers.org/docs/attestation/policies/).
- IETF,
  [RFC 9334: Remote ATtestation procedureS Architecture](https://www.rfc-editor.org/rfc/rfc9334.html).
- Linux kernel,
  [Integrity Policy Enforcement](https://docs.kernel.org/admin-guide/LSM/ipe.html).
- Cedar Policy,
  [Cedar formalization and differential testing](https://github.com/cedar-policy/cedar-spec).
- Blaze et al.,
  [RFC 2704: The KeyNote Trust-Management System Version 2](https://www.rfc-editor.org/rfc/rfc2704.html).
- NIST,
  [Policy Machine and Next Generation Access Control](https://www.nist.gov/identity-access-management/projects/policy-machine-and-next-generation-access-control).
