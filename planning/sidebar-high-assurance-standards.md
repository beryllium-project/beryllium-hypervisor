<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Sidebar: high-assurance standards, certification, and open formal tooling

## Status and scope

This is research input for future assurance planning. It does not claim that
Beryllium, Model 0.2, Helium, or any future deployment is certified.

No single standard certifies "high-assurance computing" in the abstract.
Practical programs combine:

- a product security or safety evaluation;
- lifecycle and tool evidence;
- validation of bounded cryptographic modules where applicable; and
- a structured assurance case linking claims to exact artifacts.

Beryllium's selected posture remains profile-neutral: build reusable proofs,
tests, assumptions, configuration evidence, and source-to-artifact identities,
then assemble a deployment-specific crosswalk with an evaluator.

## Do not conflate four outcomes

| Outcome | What it means | Representative regimes |
| --- | --- | --- |
| Product certification | An evaluator certifies one named version, target, configuration, and claim set | Common Criteria, sector product assessments |
| Process or lifecycle compliance | The development and verification process satisfies required objectives | DO-178C, IEC 61508, ISO 26262 |
| Module validation | A bounded component is validated for a narrow function | FIPS 140-3 cryptographic modules |
| Assurance case | Claims, assumptions, argument, and evidence are linked and reviewable | GSN, CAE, NIST systems-security engineering |

A proof does not itself issue a certificate. A certificate does not imply that
all implementation behavior was formally proved.

## Standards typically encountered

### Common Criteria and separation kernels

ISO/IEC 15408 defines the Common Criteria security evaluation model;
ISO/IEC 18045 defines evaluator actions. A Security Target identifies the
exact Target of Evaluation, threat model, security functions, configuration,
and assurance requirements. Evaluation Assurance Levels are packages, not
universal quality rankings.

For Beryllium, the most relevant historical profile is the public
**Separation Kernel Protection Profile (SKPP)**. Its concerns include:

- data separation;
- controlled information flow;
- sanitization of reused resources;
- fault isolation;
- complete mediation; and
- correspondence between policy model, design, and implementation.

The SKPP is useful as a requirements crosswalk even though it is based on an
older Common Criteria revision. A future evaluation would need a current
Protection Profile or an evaluator-approved Security Target; copying "EAL6"
or "EAL7" language into project claims would be misleading.

### Avionics and high-integrity software

DO-178C/ED-12C is objective-based airborne software guidance. Related
supplements matter as much as the base document:

- DO-333 permits formal-method evidence to replace or support selected
  verification activities when its assumptions and coverage are justified;
- DO-330 governs qualification of tools whose output is not otherwise fully
  checked;
- DO-331 addresses model-based development; and
- DO-332 addresses object-oriented technology.

FAA AC 20-193 and EASA AMC 20-193 replace CAST-32A as current multicore
interference guidance for relevant airborne systems. They make shared-cache,
memory-controller, interconnect, interrupt, and worst-case execution effects
explicit evidence obligations. They are relevant only after Beryllium
authorizes multicore work.

### Functional-safety families

IEC 61508 is the general functional-safety lifecycle standard. Sector
derivatives include ISO 26262 for road vehicles and railway standards such as
EN 50716. They typically require:

- hazard and risk analysis;
- integrity-level allocation;
- requirements traceability;
- independence and verification rigor scaled by integrity level;
- tool-confidence or qualification evidence;
- configuration control; and
- evidence that systematic and random failures are addressed.

These standards are deployment-specific. A hypervisor component may support a
SIL or ASIL safety case, but the integrity level applies to a safety function
and its system context, not to an open-source repository in isolation.

### Cryptography, engineering frameworks, and embedded profiles

FIPS 140-3 validates a bounded cryptographic module. It would apply to a
future Beryllium crypto or key-service module, not to the isolation engine as
a whole.

NIST SP 800-160 provides systems-security and cyber-resiliency engineering
guidance; NIST SP 800-53 provides controls; NIST SP 800-218 provides the SSDF.
These are valuable for lifecycle and assurance-case structure but are not
formal-verification standards.

GlobalPlatform SESIP and PSA Certified offer modular embedded-platform
assurance schemes. They become relevant only for a concrete device profile or
root-of-trust integration.

## Formal technologies used in high-assurance systems

| Purpose | Public precedent | Open technologies Beryllium can use |
| --- | --- | --- |
| Kernel functional correctness | seL4 | Isabelle/HOL; Rocq for Beryllium's selected stack |
| C contracts and refinement | seL4 C parser/AutoCorres; VST projects | Rocq/VST, Frama-C/WP, RefinedC after license and maintenance review |
| Bounded C checking | firmware and infrastructure projects | CBMC, KLEE, sanitizers, fuzzers |
| Protocol and concurrency models | industrial distributed systems | TLA+/TLC/TLAPS, Alloy, Apalache where suitable |
| ISA and language semantics | CHERI and RISC-V formal models | Sail, Isla/Islaris, Cerberus |
| Verified functional compilation | CakeML | HOL4/CakeML |
| SPARK deductive verification | Muen and safety-critical Ada | GNATprove community tooling |
| Rust bounded/deductive checking | emerging kernels and libraries | Kani, Verus, Creusot, Flux, Aeneas/Charon |
| Binary correspondence | seL4 configuration-specific work | No complete open RISC-V/Rocq path is currently selected |
| Assurance argument | safety and security cases | GSN or CAE, preferably in reviewable text/source form |

### The main open-tool gap

CompCert demonstrates verified C compilation and has important qualification
precedent, but its complete optimized distribution is not available under a
license suitable for Beryllium's normative open pipeline. It remains a
methodology reference, not a normative dependency.

The missing capability is a complete, maintained, open source-to-binary
correspondence path for the selected restricted-C RISC-V core. Until one is
validated, compiler and linker correctness remain explicit assumptions.

Open MC/DC evidence and reusable open qualification kits are also unresolved.
`gcov` or `llvm-cov` branch coverage must not be described as MC/DC.

## A profile-neutral Beryllium assurance program

The reusable core evidence should be organized independently of any one
certificate:

1. versioned security and safety claims;
2. explicit threat, fault, and environmental assumptions;
3. canonical configuration and authority semantics;
4. requirements-to-contract-to-theorem-to-test traceability;
5. proof objects and closed assumption reports;
6. C contracts, bounded checks, static analysis, and negative tests;
7. exact compiler, linker, source, binary, and tool identities;
8. reproducible evaluator workflows;
9. vulnerability analysis and evidence-invalidation rules;
10. an assurance argument identifying every trusted cut point.

A deployment can then assemble a crosswalk:

| Deployment goal | Reused core evidence | Additional deployment evidence |
| --- | --- | --- |
| Common Criteria | security model, correspondence, vulnerability analysis | Security Target, evaluated configuration, evaluator actions |
| DO-333/DO-330 | formal obligations, tool behavior, traceability | DAL allocation, independence, qualification plan, coverage |
| IEC 61508/ISO 26262 | systematic evidence, tool confidence, failure behavior | hazard analysis, safety function, target metrics, assessor review |
| FIPS 140-3 | isolation around a crypto boundary | validated algorithms/module, entropy, key lifecycle, CMVP certificate |
| NIST/SSDF | provenance, review, vulnerability handling | organizational controls and deployment-specific assessment |

## Candidate future work

1. Build a Common Criteria/SKPP-inspired claim matrix without selecting an
   EAL.
2. Build a DO-333/DO-330-style proof and tool-use ledger for the current Rocq,
   GCC, Clang, Node.js, and container pipeline.
3. Add a plain-text GSN/CAE prototype that references exact Model 0.2 theorem
   and test identifiers.
4. Evaluate open MC/DC tools; use a non-claiming placeholder if none meets the
   maintenance and licensing policy.
5. Evaluate seL4-style binary correspondence and Cambridge/REMS tooling as an
   independent open workstream.
6. Do not choose a certification target until a deployment, evaluator, and
   bounded product configuration exist.

## Primary references

Checked 2026-07-23:

- Common Criteria portal:
  <https://www.commoncriteriaportal.org/>
- ISO/IEC 15408-1 catalogue:
  <https://www.iso.org/standard/72891.html>
- Separation Kernel Protection Profile:
  <https://www.commoncriteriaportal.org/files/ppfiles/pp_skpp_hr_v1.03.pdf>
- FAA AC 20-193:
  <https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentID/1036408>
- EASA AMC 20-193:
  <https://www.easa.europa.eu/en/document-library/acceptable-means-of-compliance-and-guidance-materials/amc-20-amendment-20>
- NIST FIPS 140-3 and CMVP:
  <https://csrc.nist.gov/pubs/fips/140-3/final>,
  <https://csrc.nist.gov/projects/cryptographic-module-validation-program>
- NIST SP 800-160:
  <https://csrc.nist.gov/pubs/sp/800/160/v1/r1/final>
- NIST SP 800-218 SSDF:
  <https://csrc.nist.gov/pubs/sp/800/218/final>
- GlobalPlatform SESIP:
  <https://globalplatform.org/sesip/>
- seL4 verification and proofs:
  <https://sel4.systems/Verification/>,
  <https://github.com/seL4/l4v>
- CompCert license:
  <https://compcert.org/download.html>
- Frama-C:
  <https://www.frama-c.com/>
- CBMC:
  <https://github.com/diffblue/cbmc>
- CakeML:
  <https://cakeml.org/>
- GNATprove community package:
  <https://alire.ada.dev/crates/gnatprove>
- TLA+ and TLAPS:
  <https://lamport.azurewebsites.net/tla/tla.html>,
  <https://tla.msr-inria.fr/tlaps/>
- Existing project tooling policy:
  [Open tooling](open-tooling.md)
