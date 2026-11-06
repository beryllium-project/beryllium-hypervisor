# Open tooling and high-assurance evidence policy

## Hard requirements

Every tool used by the project to build, verify, analyze, test, document, package, sign, reproduce, or release Beryllium must:

- Be fully open source under a license permitting commercial and government use, modification, and redistribution.
- Be buildable from source without a closed compiler, plugin, service, or SaaS dependency.
- Have its exact source revision, build recipe, dependencies, configuration, and license recorded.
- Produce locally reproducible results.
- Prefer independently checkable output, proof terms, certificates, counterexamples, or deterministic artifacts.
- Prefer broadly adopted projects with active releases, multiple maintainers or organizations, public governance, public issue tracking, and durable archives.

Specialized research tools may be used only when:

- No broadly adopted open tool provides the required capability.
- Their role is narrow and replaceable.
- Their output is checked by a more mature open tool or small trusted checker.
- The plan records community, maintenance, licensing, and succession risk.

The normative project workflow and every release/assurance claim use only fully open tooling. A hosted service may mirror or transport artifacts only when the same operation is reproducible with fully open local tooling.

## Blocker escalation policy

When required open tooling does not exist or is not yet mature:

1. Align with and contribute to existing open Cambridge/REMS, seL4, CHERI, Linux, or broadly adopted tooling.
2. Use an explicit placeholder that fails closed or marks the property as unverified.
3. Record a possible Beryllium side project to implement the missing open capability.
4. Do not make the blocked security, proof, coverage, or certification claim.
5. If the placeholder blocks all meaningful progress, a proprietary tool may be used temporarily for exploration only.
6. Any proprietary exception must be time-limited, isolated, documented, approved as a direction review, and accompanied by an open replacement plan.
7. Proprietary results are non-normative and cannot support a release, assurance, certification, or upstream claim.
8. If no viable open replacement path exists, reassess the project architecture or direction.

## Certification reality

High-assurance standards generally qualify a tool's use in a process; they do not declare one universal approved tool list.

Relevant frameworks include:

- DO-178C with DO-333 formal-methods credit and DO-330 tool qualification.
- FAA AC 20-193 and EASA AMC 20-193 for multicore interference evidence.
- Common Criteria formal model and correspondence evidence.
- ISO 26262 tool confidence and qualification.
- IEC 61508 and EN 50716 tool classes.
- NIST SSDF, SBOM, provenance, and secure-development evidence.

Open-source tooling is acceptable when the project supplies adequate evidence. Beryllium should build its own open qualification and validation package rather than depend on a proprietary vendor kit.

For each load-bearing tool, retain:

- Tool operational requirements.
- Intended use and safety/security impact classification.
- Versioned source and reproducible build.
- Validation tests and expected results.
- Known limitations and unsupported inputs.
- Configuration and environment constraints.
- Change-impact procedure.
- Independent output checks where possible.
- Traceability from requirements to tool claims and evidence.

Proof-producing tools reduce trust when a small open checker independently validates the result. The checker and its logical assumptions remain part of the trusted toolchain.

## Selected assurance posture

Follow the seL4 model:

- Build reusable profile-neutral correctness and security evidence for the core.
- Publish every proof assumption and unverified boundary.
- Parameterize security properties by an explicit system configuration and authority graph.
- Connect abstract specification, executable model, C implementation, compiler output, linked image, and measured artifact.
- Let each deployment assemble its own certification case and evaluator-specific life-cycle evidence.
- Maintain crosswalks to standards without claiming that the core itself is certified.

Initial crosswalk targets:

- Common Criteria formal security-policy, correspondence, vulnerability-analysis, and configuration evidence.
- DO-333 formal-method credit and DO-330 tool-use evidence.
- FAA/EASA multicore interference guidance.
- ISO 26262 and IEC 61508 tool-confidence and safety-case evidence.
- EN 50716 rail formal-method and tool evidence.
- NIST SSDF and software-supply-chain evidence.

## Similar-project evidence

- seL4 uses restricted C and assembly, ordinary GCC/Clang builds, Isabelle/HOL refinement proofs, and separate binary/translation-validation work.
- CertiKOS demonstrates an all-verified-compiler approach, but its CompCert dependency is not available under a fully open license and is not usable by Beryllium.
- SeKVM and pKVM formal work use ordinary GNU C with focused Coq/CN-style verification of security-critical modules.
- TF-RMM uses ordinary GCC/Clang C with open CBMC, static analysis, fuzzing, and testing for selected properties.
- Bao and Jailhouse use small ordinary C/assembly cores but do not yet provide comparable whole-core proofs.
- Muen uses SPARK/Ada; Salus and Miralis use Rust.
- The AWS Nitro Isolation Engine is a new Rust separation kernel verified in Isabelle/HOL with the open MIT-licensed AutoCorrode infrastructure. Its source and project-specific proofs were not yet public in the reviewed July 2026 material, so it is methodological prior art rather than a reproducible dependency.

Primary alignment targets for missing tooling:

- seL4 `l4v`, AutoCorres, assumptions, and binary-verification work.
- Cambridge REMS Cerberus, CN, Sail, Isla/Islaris, and C/CHERI semantics.
- RISC-V International Sail models.
- Open proof-checking and translation-validation work from these communities.

Reuse qualification:

- seL4 binary-verification artifacts are Isabelle-based. Direct artifact reuse is not assumed under the Rocq-primary core proof.
- A bounded Isabelle binary-validation workstream is permitted to reuse open seL4 infrastructure without duplicating the Rocq functional proof.
- Any historic non-open solver dependency must be replaced or isolated under the blocker policy before a normative claim.
- If direct reuse is incompatible, treat seL4 as methodology and budget an open implementation rather than claiming reuse.

## Mandatory baseline candidates

All candidates require a final license and governance check at the pinned version.

### Build and binary tools

- Linux Kbuild and GNU Make.
- GCC.
- LLVM/Clang.
- GNU binutils and LLVM binary utilities.

Use both GCC and Clang builds to expose implementation-defined behavior and compiler-specific assumptions.

### ISA, firmware, emulation, and hardware

- RISC-V Sail model.
- QEMU.
- OpenSBI.
- Spike as an independent ISA cross-check.
- GDB and OpenOCD.

### Primary formal methods

- Rocq/Coq as the primary proof assistant and proof checker.
- Sail-generated Rocq definitions.
- Isabelle/HOL for selected seL4, CHERI, and Nitro-method comparison.
- TLA+/TLC/TLAPS for concurrent protocol models.
- Z3 and cvc5 as independently developed SMT backends where the frontend supports both.

### C analysis and verification

- Frama-C core with only open plugins such as Eva and WP.
- CBMC.
- Cerberus as the executable/formal C semantics reference for pointer provenance, undefined behavior, and CHERI-aligned memory-model work.
- CN as a scoped pilot because it is BSD-licensed and has pKVM case-study relevance; it is not load-bearing.
- VST's BSD-licensed opam distribution and open dependencies may be studied, but VST cannot verify the project's own C: translating it needs `clightgen`, whose passes depend on CompCert files outside the open licence (`mvp/README.md` item 103; corrected 2026-11-02 under the M8 plan's Q13); the non-free `compcert_new` subtree is never used.
- RefinedC only after confirming the exact upstream license, release process, and maintenance status.
- KLEE as supplementary symbolic execution, not primary proof evidence.

### Linux and compiler analysis

- sparse.
- smatch.
- Coccinelle.
- clang-tidy.
- GCC and Clang warnings.
- Address, undefined-behavior, memory, and concurrency sanitizers where the execution environment supports them.

### Testing, fuzzing, and coverage

- KUnit and kselftest for Linux integration surfaces.
- Project-native unit and conformance tests for the separate image.
- libFuzzer and AFL++.
- gcov/lcov and llvm-cov for available coverage metrics.

Open, maintained MC/DC coverage support must be confirmed or developed before claiming DO-178C-style structural coverage. Branch coverage is not MC/DC.

### Documentation and traceability

- Sphinx, matching Linux documentation practice.
- A VCS-native open requirements/traceability layer, with Sphinx-Needs and StrictDoc as candidates.
- Plain-text architecture decisions, threat models, assurance cases, and requirement identifiers.

### Reproducibility and supply chain

- Rootless Podman/Buildah and OCI images for a reproducible contributor environment.
- Nix, Guix, or another fully open reproducible package definition after a community and maintenance evaluation.
- SPDX and REUSE.
- in-toto and Sigstore components where signing/provenance is required, without depending solely on a public hosted service.
- Reproducible Builds practices and deterministic artifacts.

## Excluded normative tooling

- CompCert: the full compiler uses the INRIA non-commercial license and is not open source under the project's requirement.
- Proprietary static analyzers, coverage tools, compilers, requirements systems, model-based code generators, and qualification kits.
- Closed CodeQL engine or other source-visible but non-open analysis engines.
- Closed CI/CD, signing, artifact, or proof services as the only way to reproduce results.
- Commercial-only Frama-C plugins or TrustInSoft products.

These may be discussed as industry context. They may be executed only under the blocker escalation policy and never support a normative Beryllium claim.

## Tool selection scorecard

Score every mandatory candidate on:

1. License freedom and dependency closure.
2. Community size, diversity, and governance.
3. Maintenance history and release cadence.
4. High-assurance or production use.
5. Reproducible source build.
6. Independent checking and trust-base size.
7. RISC-V, Arm, x86, and CHERI relevance.
8. Linux upstream familiarity.
9. Automation and CI suitability.
10. Exit strategy if the project becomes unavailable.

## Future Rust verification research pool

Rust verification remains outside the initial restricted-C HS toolchain. For a
future separately authorized VS component:

- **[Verus](https://github.com/verus-lang/verus)** is the leading practical
  candidate for rich functional
  specifications, protocol/state-machine invariants, and selected concurrent
  data structures. Its result trusts the Verus/rustc integration, Z3,
  specifications, axioms, external bodies, and Rust code generation; it emits
  no Rocq-checkable proof object.
- **[Kani](https://github.com/model-checking/kani)** is complementary bounded
  checking for panic, arithmetic, ABI, and
  selected safe/unsafe wrapper cases; bounds and unsupported assembly or
  concurrency behavior remain explicit.
- **[Aeneas](https://github.com/AeneasVerif/aeneas) /
  [Charon](https://github.com/AeneasVerif/charon)** is the preferred direct
  Rocq-interoperability experiment
  for one safe sequential Rust core, while its alpha translation boundary and
  unsupported unsafe/concurrent behavior remain visible.
- **[RefinedRust](https://plv.mpi-sws.org/refinedrust/) /
  [RustBelt](https://plv.mpi-sws.org/rustbelt/)** is foundational Coq/Iris
  input for a concrete unsafe abstraction, not a turnkey component verifier.
- **[Creusot](https://github.com/creusot-rs/creusot),
  [Flux](https://github.com/flux-rs/flux), and
  [Prusti](https://github.com/viperproject/prusti-dev)** remain comparison
  candidates for sequential
  contracts or refinement types, with their non-Rocq backends and current
  maintenance status evaluated at the pinned revision.

Any future probe must pass this document's scorecard, pin the compiler,
verifier, solver, target, and linker, enumerate every assumed layout,
`external_body`, FFI, allocator, assembly, MMIO, and hardware contract, and
retain ordinary build/boot/adversarial tests. No result transfers to the HS
core, Model 0.2, RISC-V ISA, or hardware refinement.

## Open gaps

- Final load-bearing C refinement verifier: VST's open distribution, RefinedC, a direct Rocq development, or a combination.
- Open source-to-binary translation validation for the proof-bearing core.
- Maintained open MC/DC coverage suitable for certification evidence.
- Open requirements tooling with enough long-term community strength.
- Qualification evidence needed for the first selected assurance target.
- Whether an open Rust/Isabelle path should be retained as a later independently implemented comparison to the C core.
- Whether Verus, Aeneas/Charon, or RefinedRust can produce sustainable,
  independently reviewable evidence for a fixed `no_std` VS service core.

## Selected binary-assurance staging

Prototype milestones:

- Pin GCC and Clang versions and configurations.
- Build with both compilers.
- Reproduce source, preprocessed C, objects, linked image, and measurements.
- Treat compiler and linker correctness as explicit assumptions.
- Perform open disassembly, differential, and semantic checks where available.

Assurance-release milestone:

- Require a fully open translation-validation or equivalent binary-correspondence path for the proof-bearing subset.
- Align as closely as possible with open seL4/Cambridge/REMS techniques.
- Replace any placeholder before claiming binary-level assurance.
- If a proprietary exploratory tool was temporarily used, reproduce the result with the open path or remove the claim.
- Milestone 8 cannot be declared complete without this open binary-correspondence result. A provisional pre-assurance release may ship with the compiler explicitly trusted.

## Proof repository reproducibility

- In-tree proof manifests identify exact companion proof commits and tool manifests.
- The companion repository contains all source needed to rebuild proof checkers, models, and evidence.
- Hosted CI is not trusted; local reproducible commands are authoritative.
- Proof and code releases are paired and cryptographically attributable.
- A failed, stale, or missing proof run downgrades the in-tree status rather than silently retaining a claim.

## Selected Cerberus/CN role

Cerberus:

- Is the semantic reference for the restricted C profile.
- Provides an executable model for exploring allowed behavior and undefined behavior.
- Aligns with CTSRD-CHERI through its CHERI/Morello C memory-model work and Cambridge REMS provenance.
- Must be pinned and mirrored with a documented succession plan because its community is specialized.

CN:

- Is piloted only on single-hart or explicitly serialized ownership-heavy leaf modules such as allocators, page-table helpers, capability-table operations, and bounded parsers.
- Does not establish the whole-hypervisor proof.
- Does not currently provide the project's CHERI-C/purecap verification path.
- Does not cover the selected multicore concurrency model.
- Any Stage-2 use requires a precondition proving ownership of the global control lock or exclusive per-core state.
- Does not become load-bearing unless its Rocq proof-log path covers the required reasoning, results are independently checked, maintenance broadens, and a concurrency plan exists.
