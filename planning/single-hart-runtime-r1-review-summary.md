<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R1 responsible-human review summary

> **Repository rehoming note (current-line editorial context):** This record
> preserves packet-time references to former private repository
> `jamorris_microsoft/beryllium`, its remotes, and historical absolute checkout
> paths. The current active private repository is
> `beryllium-project/beryllium-hypervisor`. Use
> [project orientation](project-orientation.md) for current commands; do not
> reinterpret historical remote-containment or publication facts.

## Decision record

Responsible-human review **accepted exact commit**
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. The explicit
instruction was: `accept exact commit a6e0bb1`.

This decision applies only to that immutable mechanism commit. It does not
authorize an R1 tag, a private push, public release, R2 implementation, or any
other successor work.

## 1. Decision summary

| Field | Required content |
| --- | --- |
| Review target | Exact commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` with parent `41fa0564c47234305fb1d17fd4f8d93991118a48` |
| Current status | R1 pure-C mechanism implemented, tested, and accepted at exact commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28 |
| Decision requested | Decision recorded: accept this exact commit |
| Successor status | R2 has not started; no R1 tag or push has occurred |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`; accepted mechanism commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` and this follow-up decision record remain local until separately pushed; public release remains blocked |

No further acceptance decision is pending for this exact SHA. Any tag, push,
public release, or R2 start requires separate explicit authorization.

## 2. Deliverables

`git diff --name-only 41fa0564c47234305fb1d17fd4f8d93991118a48 a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` reports 93 changed paths. The review-relevant source-of-truth content is:

| Deliverable | Paths | Purpose | Trust / privilege boundary | Most important human review question |
| --- | --- | --- | --- | --- |
| Fixed R1 contract surface | `include/be/manifest.h`, `include/be/state.h`, `include/be/r1-config.h`, `include/be/types.h` | Freeze the full-profile data model, phase machine, checker results, and accessors | Non-privileged restricted C only; copied inputs are non-authoritative until validated/sealed/derived | Do these headers state the exact R1 scope without implying R2, Sv39x4, boot, or QEMU behavior? |
| Frozen full-profile fixture | `virt/be/r1-config.c` | Encode the exact R1 inventory/proposal at accepted R0 addresses | Review data only; grants no runtime authority by itself | Does the fixture match the accepted full profile: 13 resources, 6 authorities, 2 abstract roots with 3 mappings each? |
| Pure-C mechanism | `virt/be/manifest.c`, `virt/be/state.c` | Copy, validate, canonicalize, seal, abstract-derive, report, and fail closed | No assembly, boot path, privileged instruction, page-table backend, or linked image | Are authority exclusion, sealing, derivation, integrity, and terminal-failure boundaries implemented exactly as claimed? |
| Host tests and retained evidence | `tests/Makefile`, `tests/r1/r1-check.c`, `tests/r1/r1-report.c`, `tests/r1/check-report.mjs`, `tests/r1/generate-evidence.sh` | GCC/Clang host tests, deterministic report, semantic report checking, evidence packaging | Host-only evidence; no Beryllium QEMU or hardware execution | Do the negative tests and retained artifacts cover the load-bearing failure modes and exact claim ledger? |
| Wrapper/build/documentation updates | `Makefile`, `be`, `scripts/check-be.sh`, `planning/HANDOFF.md`, `planning/README.md`, `planning/implementation-plan.md`, `planning/research-provenance.md`, `planning/research-synthesis.md`, `planning/single-hart-runtime-plan.md`, `planning/single-hart-runtime-r0-freeze.md`, `planning/single-hart-runtime-r1-evidence.md` | Expose R1 in the stable interface and keep maintained claims aligned | Source-of-truth prose and wrapper surface; generated `docs/html/**` are derivative, not normative | Do the maintained claims stay inside the exact evidence boundary and avoid silently starting R2 or public release work? |

## 3. Claim boundary

### Supported by this exact commit

- R1 is pure non-privileged restricted C only:
  `copy -> validate -> canonicalize -> seal -> abstract derive -> report -> terminal failure`.
- The fixed full profile has 13 resources, 6 authorities, and 2 abstract roots with 3 mappings each.
- Terminal failure is sticky across the public R1 APIs.
- The deterministic configuration identity is for reporting/equivalence only.
- The exact commit includes the required Copilot trailers and no human `Signed-off-by`.

### Trusted or assumed

- Caller-owned C storage integrity remains a trusted assumption: a trusted caller can overwrite or discard an instance out of band.
- Later platform code must discard a failed instance and follow the accepted shutdown path; terminal shutdown integration is not implemented here.

### Unavailable or `NOT RUN`

- Beryllium QEMU execution, linked-image behavior, K3 hardware validation, formal verification, and Model 0.2 refinement evidence are not available for R1.
- Retained Helium evidence does not validate R1.

### Explicitly not implemented here

- No active-domain phase.
- No Sv39x4 page tables or page-table backend.
- No assembly, boot path, trap path, `HGATP` work, or fences.
- No linked Beryllium image.
- No Beryllium QEMU result.
- No hardware validation.
- No formal verification claim.
- No R2 behavior.

## 4. Security and correctness invariants

| Invariant | Contract | Implementation | Test / evidence |
| --- | --- | --- | --- |
| Exact full-profile shape is fixed and closed | `include/be/manifest.h`, `include/be/r1-config.h` | `virt/be/r1-config.c`, `be_check_inventory()`, `be_canonicalize()` | `tests/r1/r1-check.c`: positive flow, inventory rejections, proposal closure failures |
| No direct authority before seal; canonical state becomes authoritative exactly once; derived state comes only from sealed canonical state | `include/be/manifest.h`, `include/be/state.h` | `virt/be/manifest.c` rejects published roots/mappings/active domain; `virt/be/state.c` seal/derive path | `tests/r1/r1-check.c`: direct-authority rejection, seal-integrity, derive-integrity, no-partial-output cases |
| Domain/root/stack/saved-state bindings stay exact and distinct | `include/be/manifest.h` domain/root/saved-state contracts | `check_canonical_domains()`, `be_check_enforcement()` in `virt/be/manifest.c` | `tests/r1/r1-check.c`: binding rejections and positive root/state checks |
| Authority boundary is fixed: private `rw`, shared management `rw` to protected `r`, guest-code `rx`, monitor/root/stack/state excluded | `include/be/manifest.h` rights/channel model | `check_canonical_authorities()`, `be_check_enforcement()` in `virt/be/manifest.c` | `tests/r1/r1-check.c`: ownership/authority/channel negative tests; `tests/r1/check-report.mjs` checks final 6 authorities and 6 mappings |
| Failure is terminal across public R1 APIs and failed outputs are zeroed as documented | `include/be/state.h` | `fail_runtime()` and report handling in `virt/be/state.c` | `tests/r1/r1-check.c`: null/wrong-phase, report-zeroing, failed-state-sticky |
| Configuration identity is deterministic reporting/equivalence only, not attestation | `include/be/manifest.h`, `planning/single-hart-runtime-r1-evidence.md` | `be_configuration_identity()` in `virt/be/manifest.c`; report emission in `tests/r1/r1-report.c` | `tests/r1/r1-check.c`: source/vocabulary/proposal-id equivalence; `tests/r1/check-report.mjs` validates the report surface |

## 5. Review history and resolved findings

Independent review found and closed these issues before this packet:

| Finding | Resolution |
| --- | --- |
| Stale report filename / stale evidence references | `tests/Makefile`, `tests/r1/generate-evidence.sh`, and `planning/single-hart-runtime-r1-evidence.md` now consistently retain and reference `build/r1/reports/runtime.json` and `build/r1/reports/report-check.txt`. |
| Omitted source-manifest dependencies in retained evidence | `tests/r1/generate-evidence.sh` now hashes the full R1 source-of-truth set that affects the retained evidence, including wrapper/build/planning/test inputs. |
| Overly broad reset/recovery claim | `include/be/state.h`, `virt/be/state.c`, `planning/single-hart-runtime-r1-evidence.md`, and `planning/HANDOFF.md` now say only that failure is terminal across the R1 APIs; caller-owned storage integrity stays a trusted assumption, fresh initialization is not in-run recovery evidence, and terminal shutdown integration remains unimplemented. |

No open automated-review defect is recorded here; the remaining questions are responsible-human judgment about scope, assumptions, and acceptance.

## 6. Validation and retained evidence

| Command / check | Result | Boundary / coverage |
| --- | --- | --- |
| `git --no-pager show --format=fuller --stat --summary a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` | Reviewed while drafting | Confirms exact commit, parent relation, required Copilot trailers, and absence of a human `Signed-off-by` |
| `make check` | **Passed on 2026-07-28 for the exact staged content before commit** | Repository gate covering `be-check`, Helium `check`, Model 0.2 `check`, `make -C tests r0-freeze`, `make -C tests r1-check`, and retained-evidence checksum checks; exact clean detached-worktree result is separate |
| `make -C tests r1-check` / `./be r1-check` | Recorded as passing in the exact commit’s maintained evidence | Covers GCC/Clang host builds, adversarial R1 tests, deterministic report generation, semantic report checking, and R1 evidence packaging |
| `build/r1/reports/runtime.json`, `build/r1/reports/report-check.txt`, `build/r1/evidence/source-state.txt`, `tool-versions.txt`, `source.sha256`, `artifacts.sha256`, `claim-status.txt` | Retained evidence set | Hashes the current evidence tree and records its source state; `tests/r1/check-acceptance.sh` separately requires the R1 mechanism/build/host-test inputs to match accepted commit `a6e0bb1` before emitting accepted status |
| Fresh detached-worktree `make check` at exact commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` | **Passed on 2026-07-28** | Ran the complete repository gate from an isolated detached worktree using the repository’s existing installed `node_modules`; the temporary worktree was removed afterward |

## 7. Recommended human review sequence

### Prepare an isolated detached worktree

```sh
cd /home/jamorris/src/beryllium
git worktree add --detach ../beryllium-r1-review-a6e0bb1 \
  a6e0bb178c10a7e68c9447a8e58affb94b8ecadb
cd ../beryllium-r1-review-a6e0bb1
git status --short --branch
npm ci
```

### Read-only review passes

1. Confirm the immutable target and changed-path inventory:

   ```sh
   git --no-pager show --stat --summary a6e0bb178c10a7e68c9447a8e58affb94b8ecadb
   git --no-pager diff --name-status \
     41fa0564c47234305fb1d17fd4f8d93991118a48 \
     a6e0bb178c10a7e68c9447a8e58affb94b8ecadb
   ```

2. Review policy, plan, accepted R0 boundary, and maintained R1 claims:

   ```sh
   git --no-pager show \
     a6e0bb178c10a7e68c9447a8e58affb94b8ecadb:LLM_POLICY_ALIGNMENT.md
   git --no-pager diff \
     41fa0564c47234305fb1d17fd4f8d93991118a48 \
     a6e0bb178c10a7e68c9447a8e58affb94b8ecadb -- \
     planning/single-hart-runtime-plan.md \
     planning/single-hart-runtime-r0-freeze.md \
     planning/single-hart-runtime-r1-evidence.md \
     planning/HANDOFF.md
   ```

3. Review the exact R1 contract and mechanism:

   ```sh
   git --no-pager diff \
     41fa0564c47234305fb1d17fd4f8d93991118a48 \
     a6e0bb178c10a7e68c9447a8e58affb94b8ecadb -- \
     include/be/types.h \
     include/be/manifest.h \
     include/be/state.h \
     include/be/r1-config.h \
     virt/be/r1-config.c \
     virt/be/manifest.c \
     virt/be/state.c
   ```

4. Review the host tests, report checker, evidence packaging, wrapper gating, and maintained support documents:

   ```sh
   git --no-pager diff \
     41fa0564c47234305fb1d17fd4f8d93991118a48 \
     a6e0bb178c10a7e68c9447a8e58affb94b8ecadb -- \
     tests/Makefile \
     tests/r1/r1-check.c \
     tests/r1/r1-report.c \
     tests/r1/check-report.mjs \
     tests/r1/generate-evidence.sh \
     Makefile \
     be \
     scripts/check-be.sh \
     planning/README.md \
     planning/implementation-plan.md \
     planning/research-provenance.md \
     planning/research-synthesis.md
   ```

5. Treat `docs/html/**` as generated derivatives only if you want a publication-consistency spot check; do not use them as the normative source over the Markdown/planning files above.

### Optional execution in the isolated worktree

```sh
make -C tests r1-check
make check
```

### Cleanup after review

```sh
cd /home/jamorris/src/beryllium
git worktree remove ../beryllium-r1-review-a6e0bb1
```

## 8. Human decision checklist

- [ ] The exact scope still matches the accepted single-hart runtime plan and does not start R2.
- [ ] The claims stay within evidence: 13 resources, 6 authorities, 2 abstract roots with 3 mappings each; no Sv39x4, boot, linked image, Beryllium QEMU, hardware, or formal-verification claim.
- [ ] The trust assumptions are acceptable: caller-owned C storage integrity is trusted and terminal shutdown integration is not implemented.
- [ ] Negative-path coverage is sufficient for inventory closure, direct-authority rejection, binding uniqueness, channel rights, integrity mutation, wrong-phase use, and terminal failure.
- [ ] The exact commit metadata is acceptable: required Copilot trailers present, no human `Signed-off-by`, no R1 tag/push, public release still blocked.
- [x] Decision recorded: accept exact commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28.

## 9. After the decision

- **Accepted and recorded:** exact SHA `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` was accepted on 2026-07-28. Acceptance alone does **not** authorize tagging, pushing, public release, or starting R2.
- **Request revisions:** create a new corrective commit and a new review packet for that new SHA. Do not silently treat `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` as accepted.
- **Defer:** keep current status unchanged. Do not tag, push, publish, or start dependent work.

**Status:** exact commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` is implemented, evidence-backed, exact-commit gate tested, and responsible-human accepted on 2026-07-28.

**Next:** preserve this exact acceptance record. R2 remains not started, and no tag or push has occurred.

**Action required from you:** none for acceptance recording. Separately
authorize any tag, private push, or R2 work if desired.
