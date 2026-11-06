<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B4, R7 half: the bounded exact-byte proof on B2's K3 images

This package re-derives the accepted R7 bounded exact-byte proof for the
two K3 images that [B2](../../k3-b2/README.md) builds. Accepted R7 is
`tests/r7` at `9bf22913d67e9b72286813cd5f7993a9ad3857a8`; B2 is accepted
at `898af4e02fd36744a93b0eef99bc159955409d25`. The proof runs on the
host with Rocq only: no QEMU, no board.

The package covers the same eleven privileged-wrapper symbols as accepted
R7. For each K3 image it:

- extracts the symbols' exact linked bytes;
- cross-checks every word and target independently with GNU objdump;
- generates the data-only Rocq input twice and byte-compares it;
- regenerates the fixed-configuration facts from B2's K3 port;
- compiles the accepted proof modules, with literal-only K3 changes;
- re-checks every compiled object with `rocq check`.

**Status:** `make -C bringup/k3-b4/r7 check` passes, with `proof=PASS`.
Every count equals accepted R7: 2 images, 22 symbols, 1,420 words,
144 relocation-resolved targets, 32 allocated sections, and 9 Rocq
modules with 135 Theorem and 4 Lemma declarations. Nothing is accepted:
B4 needs a responsible-human decision on an exact commit.

## What is reused unchanged

- **Proof modules:** `ISA.v`, `Entry.v`, `Trap.v`, `Switch.v`, and
  `Claims.v` are byte-identical to accepted R7. Every entry, trap-frame,
  root-transaction, restore, and return theorem is the accepted statement.
- **Unchanged statements:** in `Exact.v` and `Configuration.v`, every
  theorem statement keeps its accepted structure; only literals change
  (see below). These are unchanged on K3:
  - the cross-toolchain difference counts (2, 0, 0, 2, 9, 0, 0, 10, 12,
    3, 0) and classes (17, 9, 3, 9);
  - 14 materialized addresses and 9 external edges per image;
  - the per-symbol target counts;
  - the access matrix.
- **Stage logic:** the K3 copies of the accepted extractor, objdump
  cross-check, exact-input generator, and configuration-trace generator
  and checker keep their logic, refusals, and self-tests (24, 11, and 40
  mutations), apart from the substitutions below.
- **R1/R2 report tools:** the accepted R1 report generator
  `tests/r1/r1-report.c` is used unchanged.
- **Tool bindings:** Rocq is bound through the accepted R7 lock, and
  bash through the accepted R3 lock. Both digests match this host, so the
  Rocq binary is the one accepted R7 pinned.
- **Trace assertions:** the trace's provenance assertions are the
  accepted ones. For R1 and R2 they consume four keys that
  `port-r7.py --provenance` now supplies; see
  [Independence from the root Makefile](#independence-from-the-root-makefile).

Nothing under `tests/`, `include/`, `virt/`, `arch/`, or any other
`bringup/` package changes.

## How the copy is made

`scripts/port-r7.py` copies 15 pinned inputs into `build/k3-b4/r7/port/`:

- the four accepted R7 stage scripts;
- the seven maintained proof modules;
- the accepted R1 and R2 report generators and checkers.

The script works like B2's `port.py`:

- **Pins:** each input is read with `git show COMMIT:PATH` from its
  accepted commit (R7 `9bf22913`, R1 `a6e0bb17`, or R2 `6e1cb579`), not
  from the working tree, and must match its SHA-256 pin. The two tool
  locks the copies read at run time are pinned in place. `--verify-git`
  re-reads all 15, plus those two locks, from git.
- **Counted rules:** each change is a rule with an exact count and a
  reason, 59 in all. A count mismatch refuses the port.
- **Literal-only proof changes:** with every numeric and digest literal
  masked, each ported module must equal its accepted module, and the
  Theorem/Lemma inventory must be the accepted one.
- **No QEMU addresses left:** no proof module or R1/R2 tool may keep a
  literal of the accepted QEMU image range `[0x80200000, 0x80234000]`.
- **Exact re-derivation:** `--check` re-derives the copy and requires a
  byte-identical tree.
- **Inherited shellcheck finding:** the accepted `check-disassembly.sh`
  has one shellcheck finding, SC1007 at line 22, column 15, on its
  `CDPATH= cd` line. In the copy that line may change only by the
  repository-root rule, which deepens its relative path. `--shellcheck`
  also requires shellcheck to report the same findings for the copy as
  for the accepted file: the same SC1007, and nothing new.

### Proof-source changes

Only two modules change, and only in pinned constants:

| Module | Rule | Count | Why |
| --- | --- | --- | --- |
| `Exact.v` | Allocated-image SHA-256, GCC and Clang | 2 | B2's K3 images: rebased layout constants, the quiesce call in `be_reset`, and B1's quiesce code |
| `Exact.v` | Identity totals: allocated file/memory bytes and symbol-table entries | 4 (2 per toolchain, theorem and bundle) | GCC 46968/153464/391, Clang 46208/152704/530: 112 more text bytes, plus the quiesce symbols |
| `Exact.v` | `.monitor.text` size and SHA-256 | 2 | 30336 (GCC) and 30384 (Clang): be_reset's 8-byte call moves later code by 0x10, and 96 bytes of B1 quiesce code follow the last accepted function |
| `Exact.v` | `.monitor.input` and `.monitor.rodata` SHA-256 | 4 | the rebased R0 layout and the K3 profile, identity, and SBI constants |
| `Exact.v` | Named C cut points | 4 | Measured from the ELF symbols `be_r5_trap_dispatch` and `be_r5_runtime_terminal`: GCC `0x102005d38`/`0x102005b28`, Clang `0x102005f50`/`0x102005eb0`. The report re-reads them from each symbol table |
| `Exact.v` | Scoped layout rows rebased by `+0x81e00010` | 22 | The image delta plus the 0x10 from be_reset's call; sizes and unit counts unchanged |
| `Exact.v` | Image-range hex literals rebased by `+0x81e00000` | 37 | The entry point, 32 allocated-section addresses, and 4 trusted-stack/saved-page extents |
| `Configuration.v` | Image-range decimal literals rebased by `+0x81e00000` | 26 | The 13 R1 resource bases, pinned as `nat` and as `Z` |

No theorem is removed, weakened, narrowed, or `Admitted`, and no `Axiom`
or `Parameter` is added. `Print Assumptions be_r7_claims_hold` reports
`Closed under the global context`.

### Tool and data changes

| File | Rules | Why |
| --- | --- | --- |
| `extract-exact-image.mjs` | 5 | Repository root six levels up (1); B2's ELF paths (2); outputs under `build/k3-b4/r7` (4 occurrences); a 64-bit-exact address formatter (1, see [Findings](#findings)) |
| `check-disassembly.sh` | 8 | Root (1); B2's ELF paths (4); outputs (15 occurrences); two digest checks removed (2). The objdump and node digests no longer match the accepted R3 lock; its command and resolved-path bindings stay |
| `generate-exact-input.mjs` | 2 | The generated header names its K3 source (1); outputs (4 occurrences) |
| `check-configuration-trace.mjs` | 18 | Root (1); outputs (13 occurrences); the K3 R1/R2 report paths, checkers, and make targets (6); the pinned-source list and its comment name the K3 inputs (1); R1/R2 provenance from `port-r7.py --provenance` (1, see [Independence from the root Makefile](#independence-from-the-root-makefile)); the R5 binding (6, below); the generated header and comment (2) |
| `tests/r1/check-report.mjs` | 1 | 13 frame bases rebased, as B2 rebases `r0-config.h` and `r0-layout.h` |
| `tests/r2/r2-report.c` | 1 | 2 fixed pool bases rebased. The accepted R2 builder refuses the QEMU bases on the K3 port (`binding`) |
| `tests/r2/check-report.mjs` | 7 | 2 pool bases, 4 pointer-table PPNs, and 8 rebased 16-digit strings (pool bases and leaf pages); guest-physical addresses unchanged |

The K3 images are B2's port, not the accepted R5 QEMU images, so the
trace binds R5 provenance differently (6 rules):

- **Port check:** B2's `port.py --check` re-derives the port from the
  pinned accepted R5 bytes.
- **Manifest:** its manifest stands where the R5 QEMU report stood.
- **Commit and date:** they come from the accepted R5 record,
  `tests/r5/check-acceptance.sh`, which is read, not run.
- **No dynamic cross-check:** the R5 QEMU isolation runs are not
  evidence about the K3 images, and B4 runs no QEMU or board. The trace
  records `dynamic_isolation_cross_check=NOT-RUN-in-k3-b4`, and its
  checker refuses any other value.

Accepted R7 bound that dynamic cross-check as corroboration only. No
theorem consumed it.

### Independence from the root Makefile

Accepted R7's trace ran the accepted `tests/r1/check-acceptance.sh` and
`tests/r2/check-acceptance.sh` and asserted four keys from each. The R1
interface also pins the root `Makefile` SHA-256, which the configuration
facts do not depend on. The K3 facts come only from the accepted R1/R2
report generators, compiled against B2's port. B4 therefore runs neither
interface, nor any other acceptance-pin checker.

One counted rule makes the trace take those keys from
`port-r7.py --provenance r1|r2` instead. That mode prints the same four
keys only if all of these hold:

- the accepted commit's own bytes, read with `git show`, equal B2's pins
  for the R1/R2 mechanism inputs the facts consume (9 for R1, 2 for R2);
- the same holds for B4's pins of the two report tools;
- B2's port and B4's copy each re-derive byte-identically;
- the commit and date it prints are the ones the accepted interface
  records. The interface is read as a record and never run.

The trace's assertions, its independent check (which re-runs the same
provenance live), the double generation, and the Rocq obligations are
unchanged, and the generated facts are byte-identical to before.

The gate reads no root file and no acceptance pin. A later root
`Makefile` edit, such as root integration of the bring-up packages, needs
no refresh here. These files are still read:

- **Records:** the `accepted_commit=` and `accepted_at=` lines of the
  accepted R1, R2, and R5 acceptance interfaces;
- **Pinned tool locks:** `tests/r3/tool-lock.conf` and
  `tests/r7/tool-lock.conf`;
- **Accepted inputs:** read from and pinned to their accepted commits;
- **The R7 plan:** recorded by hash at run time, not pinned.

None of them changes when the root `Makefile` does.

## The gate

`make -C bringup/k3-b4/r7 check` runs, in order:

1. **Images:** `make -C bringup/k3-b2 image-check` builds B2's images
   and runs B2's layout check. `tests/check-images.py` then:
   - requires the flat-image SHA-256 values B2 accepted;
   - records the ELF SHA-256 values;
   - reads `be_reset`, `be_b1_quiesce`, and the two C cut points from
     each symbol table;
   - requires `be_b1_quiesce` outside the eleven scoped symbols.
2. **Port:** the copy, its byte-exact `--check`, `--verify-git`, and
   the inherited-shellcheck check `--shellcheck`.
3. **R1/R2 reports:** the accepted R1/R2 report generators, compiled
   against B2's port with GCC and Clang, required byte-identical, and
   checked by the K3 checkers. The K3 R1 identity must be B2's
   `0xa3d0c0f96f0ea58b`.
4. **Extract:** extraction, the objdump cross-check, and the exact input
   (extracted twice and rendered twice inside the generator).
5. **Trace:** the configuration trace and its independent re-check,
   with R1/R2 provenance from `port-r7.py --provenance`.
6. **Inputs:** digests of `ExactInput.v`, `ConfigurationTrace.v`, and
   the trace JSON. Both generators run again, and the proof does not
   start unless all three are byte-identical.
7. **Proof:** in a fresh directory:
   - the accepted inventory and forbidden-declaration scan;
   - `rocq compile` of the 9 modules in the accepted order;
   - closed assumptions;
   - `rocq check` of every object.
8. **Self-tests:** the accepted rejection suites of the copied stages,
   then `port-r7.py --self-test` (9 refusals) and
   `report.py --self-test`.
9. **Negative tests:** `tests/check-negative.py` (below).
10. **Report:** `build/k3-b4/r7/report/k3-b4-r7-report.txt`.

The report derives `proof=PASS|FAIL|NOT-RUN` from the proof artefacts
alone:

- **NOT-RUN:** the proof artefacts are absent.
- **FAIL:** any of these does not hold:
  - every object compiled and newer than its source;
  - a closed `Print Assumptions`;
  - every module checked by `rocq check`;
  - sources equal to the checked port and the twice-generated inputs;
  - the accepted inventory, and no forbidden declaration.

The report exits non-zero unless `proof=PASS` and every stage transcript
shows its PASS line. Its self-test covers absent, broken, and complete
proof directories.

### Negative tests

Each case mutates a copy under `build/k3-b4/r7/negative/` and runs the
gate's own checker on it. Stages that read images run from a relocated
scratch root, so B2's build is never touched. All 12 cases (16 refusals)
must be refused:

| Case | Refused by |
| --- | --- |
| One flipped byte in the GCC flat image | the image check |
| The Clang flat image presented as GCC | the image check |
| `csrw hgatp, a1` in `be_r5_arch_install_root` flipped to `csrw hgatp, a0` | the image check, and `Exact.v` at `gcc_image_identity_is_exact`. The copied stages accept the flipped ELF consistently, so the proof is what refuses it |
| `be_r5_switch_tail` renamed in `.strtab` | the extractor (`missing required symbol`) |
| The accepted 32-bit address formatter restored | the objdump cross-check (`address mismatch`) |
| A per-call token in the exact-input renderer | the generator's own twice-render comparison |
| A regenerated input differing by one byte | the input digest comparison |
| A weakened statement in the ported `Exact.v` | the byte-exact port check |
| The copied `check-disassembly.sh` with its SC1007 line "fixed", or with a new shellcheck finding | `--shellcheck`, for each |
| A theorem deleted from `Switch.v` | the inventory check and `rocq compile` |
| A proof replaced by `Admitted` | the scan, and a non-closed `Print Assumptions` |
| An `Axiom` appended to `Claims.v` | the scan |

## Measured results

Measured on 2026-10-06 in this worktree:

| Property | GCC | Clang |
| --- | --- | --- |
| Flat image SHA-256 (B2 accepted) | `9c145f00…a08c79` | `47be17e3…c54fe` |
| Allocated-image SHA-256 (pinned in Rocq) | `ef2b1af6dca6d28aaee2c43e6cf237b8796abe37cc7bf4c35b2e0e4029cd9dee` | `4dd9a6138ac0cf2c5e6b1c34a09f57c3c3428f605ff881b9ebb7145c631bc9c5` |
| Entry / allocated sections | `0x102000000` / 16 | `0x102000000` / 16 |
| Allocated file / memory bytes | 46968 / 153464 | 46208 / 152704 |
| Symbol-table entries | 391 | 530 |
| `be_b1_quiesce` (outside the scope) | `0x102007620` | `0x102007650` |

The ELF file SHA-256 is recorded in the report as an observed run
identity only. The accepted R5 recipes embed the build path
(`DW_AT_comp_dir`), as accepted R7 recorded. A clean clone of this branch
at a different absolute path also passes the gate:

- the flat images and the allocated-image identities pinned in Rocq are
  identical in both runs;
- only the two ELF file digests differ, and with them `ExactInput.v`,
  which records them.

| Symbol | GCC address | Clang address | Bytes | Words (32-bit + 16-bit) | Targets |
| --- | --- | --- | --- | --- | --- |
| `be_r3_arch_reset_state` | `0x102006aa0` | `0x102006ad0` | 426 | 107 (106 + 1) | 0 |
| `be_r3_arch_install_management` | `0x102006c50` | `0x102006c80` | 14 | 4 (3 + 1) | 0 |
| `be_r3_arch_enter_management` | `0x102006c60` | `0x102006c90` | 86 | 38 (5 + 33) | 0 |
| `be_r5_arch_reset_state` | `0x102006d00` | `0x102006d30` | 428 | 107 | 0 |
| `be_r5_trap_vector` | `0x102006eb0` | `0x102006ee0` | 360 | 90 | 8 |
| `be_r5_arch_read_controls` | `0x102007020` | `0x102007050` | 36 | 9 | 0 |
| `be_r5_arch_install_root` | `0x102007050` | `0x102007080` | 44 | 11 | 0 |
| `be_r5_arch_reset_target` | `0x102007080` | `0x1020070b0` | 516 | 129 | 25 |
| `be_r5_arch_restore_active` | `0x102007290` | `0x1020072c0` | 512 | 128 | 27 |
| `be_r5_switch_tail` | `0x102007490` | `0x1020074c0` | 212 | 53 | 12 |
| `be_r5_enter_guest_tail` | `0x102007570` | `0x1020075a0` | 136 | 34 | 0 |

Totals: 22 symbols, 1,420 words (1,350 32-bit, 70 16-bit),
144 relocation-resolved targets, and 32 allocated sections. Per image,
each count is half of the total. The direct parser and objdump agree on
every word and target.

The configuration facts, from the accepted R1/R2 report generators over
B2's port:

- **Identity:** R1 identity `0xa3d0c0f96f0ea58b`.
- **Profile:** 13 resources, 6 authorities, 2 domains, 2 roots,
  3 leaves per root.
- **Roots:** management `hgatp` `0x8000000000102014`, protected
  `0x800000000010201c`.
- **Backing pages:** management-private `0x1_0202_e000`,
  protected-private `0x1_0202_f000`, shared `0x1_0203_0000`.
- **Guest-physical addresses:** unchanged at `0x4000_0000`,
  `0x4000_1000`, `0x4000_2000`, `0x4001_0000`, and `0x4001_1000`.
- **Access matrix:** `Configuration.v` proves the accepted matrix
  unchanged.

Rocq modules (`ExactInput` and `ConfigurationTrace` are generated):

| Module | Theorem | Lemma | Changed from accepted R7 |
| --- | --- | --- | --- |
| `ISA` | 4 | 4 | no |
| `Exact` | 50 | 0 | literals only |
| `Entry` | 17 | 0 | no |
| `Trap` | 6 | 0 | no |
| `Switch` | 23 | 0 | no |
| `Configuration` | 34 | 0 | literals only |
| `Claims` | 1 | 0 | no |

## Findings

- **The accepted extractor's address formatter is 32-bit.**
  `extract-exact-image.mjs` formats addresses through `>>> 0`. That is
  exact below 2^32 only, so on K3 it prints `0x102006aa0` as
  `0x02006aa0`. Two independent layers refuse that output:
  - the objdump cross-check (`address mismatch`);
  - the Rocq entry pin.

  B4 replaces the formatter with a form that prints every value below
  2^32 exactly as before. It refuses anything that is not a non-negative
  safe integer. Accepted R7's QEMU addresses are below 2^32, so the
  accepted results are unaffected. A negative test keeps the control.
  B4 still applies this rule to the accepted extractor's bytes, read from
  git; the accepted extractor is fixed separately.
- **Code moves by more than the image rebase.** B2 rebases the image by
  `+0x81e00000`. The scoped symbols move by `+0x81e00010`, because
  `be_reset` grew by its call to `be_b1_quiesce`. The two C cut points
  move by toolchain-specific amounts (`+0x81e0000e` GCC, `+0x81e00018`
  Clang). They are therefore re-pinned from measurement and cross-checked
  against the symbol tables.
- **Nothing structural changed on K3.** Every accepted count holds
  unchanged: unit, width, target, difference, materialization, and
  external-edge counts. Only constants needed new values.
- **A flipped word is refused three times over.** First by B2's
  flat-image hash. Then by the pinned allocated image
  (`gcc_image_identity_is_exact`). In a diagnostic run with the identity
  pins re-aimed at the flipped image, `Exact.v` still refused, at
  `toolchain_identical_symbols_are_byte_identical`.
- **The quiesce code adds an SRET outside the scope.** `be_b1_skip`
  carries its own `SRET`, and `be_b1_quiesce` returns with `stvec` at
  `be_b1_halt` until a reset sequence installs the trap sink. Both are
  outside the proved scope. The sole-SRET theorems speak only of the
  scoped symbols.
- **An inherited shellcheck warning.** The accepted
  `check-disassembly.sh` carries one shellcheck SC1007 warning, on its
  `CDPATH= cd` line. The copy inherits it, and the gate's `--shellcheck`
  check now holds it there: the line changes only by the counted
  repository-root rule, and the copy has exactly the accepted file's
  findings. B4 adds no shell script of its own.

## Deviations from accepted R7

- **Build path:** the images come from B2 (`make -C bringup/k3-b2
  image-check`), not from the accepted R5 and R6 launchers. B4 runs no
  R5 or R6 pipeline and no QEMU.
- **No launcher or locks:** B4 has no `run-make.sh`, no parse-time Make
  controls, and no `check-tools.sh` lock verification. The accepted R3
  lock no longer matches this host's node and objdump; like B2, B4 uses
  the host tools and records their versions and digests.
- **No source inventory or evidence bundle:** there is no
  `check-sources.mjs` inventory, no `be-r7-exact-proof-evidence-v1`
  report, independent report checker, or evidence bundle, and no R0-R6
  predecessor acceptance measurement. In their place is one concise
  deterministic text report.
- **No acceptance interface run:** the trace runs no acceptance-pin
  checker. R1/R2 provenance comes from `port-r7.py --provenance`, so the
  gate does not depend on the root `Makefile` (see
  [Independence from the root Makefile](#independence-from-the-root-makefile)).
- **No dynamic cross-check:** the configuration trace binds no dynamic
  R5 cross-check (see above).
- **Extractor fix:** the extractor's address formatter is 64-bit exact.

## Supportable claim

> For B2's two K3 images, both pinned toolchains, and the fixed
> single-hart synthetic profile, a machine-checked bounded Rocq
> development consumes exact linked bytes of the eleven scoped
> privileged-wrapper symbols. The images are GCC/GNU ld and Clang/lld,
> built from the accepted R5 recipes rebased to `0x1_0200_0000`, with
> flat-image SHA-256 `9c145f00…a08c79` and `47be17e3…c54fe`. The
> development:
>
> - independently cross-checks those bytes with GNU objdump;
> - decodes the enumerated subset;
> - checks the fixed entry, trap-frame, root-install/fence/readback,
>   restore, and return properties;
> - checks generated fixed-configuration facts from B2's K3 port against
>   the accepted two-domain access matrix.
>
> These remain explicit assumptions:
>
> - the C implementation;
> - `be_reset` and its call to `be_b1_quiesce`, and the quiesce code;
> - the direct ELF parser, and the compiler and linker outside the
>   extracted symbols;
> - B2's port;
> - OpenSBI, QEMU, and RISC-V hardware;
> - the connection from C state to the generated configuration facts.
>
> This is not a statement that Beryllium is formally verified.

## Cut points and trusted boundaries

The report carries accepted R7's ledger verbatim:

- the 15 cut points;
- the 10 trusted boundaries;
- the plan-obligation substitution for guest-GPR clearing, delivered
  only as the narrower byte-true monitor-derived-values property.

It adds the K3 items:

| Item | Boundary | Status |
| --- | --- | --- |
| `k3-be-reset-quiesce-call` | `be_reset`'s added `call be_b1_quiesce`, B2's one code delta. `be_reset` was never in the R7 scope | outside the scope, not proved |
| `k3-b1-quiesce` | B1's 96 bytes of quiesce code, including `be_b1_skip`'s SRET and the temporary `stvec`. Only the pinned `.monitor.text` digest covers them; Exact.v proves no scoped symbol has a control edge to them | outside the scope, not proved |
| `k3-port` | B2's counted port and B4's counted copy | trusted counted substitutions |
| `k3-tools` | This host's unpinned objdump 2.46.1 and node v22.23.1 | trusted tool, unpinned |
| `k3-firmware` | The K3 OpenSBI 1.6 (SBI 2.0) handoff; no theorem consumes it | trusted, assumed |
| `k3-dynamic` | The dynamic R5 isolation cross-check | NOT RUN |

## Non-claims

- **Not formal verification of Beryllium:** this is a bounded proof
  over the extracted bytes of two images.
- **Not a whole-ELF or whole-hypervisor proof:** `be_reset`, the
  quiesce, C handlers, diagnostics, SBI calls, and guest fixtures are not
  covered.
- **Not a C refinement** or source-to-binary validation result.
- **Not hardware validation:** these exact images ran on the COM260 in
  B2 and B3, but this proof transfers no board claim. Hardware is NOT RUN
  here, as is QEMU.
- **Not a broader isolation result:** nothing about arbitrary guests,
  arbitrary page tables, information flow, availability, timing, or side
  channels.
- **No transferred theorems:** no Model 0.2, Helium, or accepted QEMU R7
  theorem, object, or claim transfers to K3. Everything is re-derived
  here.
- **No guest-GPR clearing claim:** nothing claims the trap wrapper
  clears live guest GPR authority.
- **No byte-reproducibility claim:** report bytes, ELF file digests,
  and `.vo` objects are not claimed reproducible across paths or hosts.
- **Not an acceptance:** this does not accept B4 and authorizes no
  successor, publication, tag, push, or release.

## Commands

```sh
make -C bringup/k3-b4/r7 check     # the complete gate (about 6 minutes)
make -C bringup/k3-b4/r7 report    # re-derive the report from artefacts
make -C bringup/k3-b4/r7 clean     # remove build/k3-b4/r7
```

Outputs go only under `build/k3-b4/r7/`; B2's own build writes
`build/k3-b2/`.

## Tools (this workstation)

| Tool | Version | Against the accepted lock |
| --- | --- | --- |
| Rocq | The Rocq Prover 9.2 (`rocq-runtime-9.2.0-1.fc44`) | digest matches accepted R7 |
| GNU objdump | 2.46.1-1.fc44 | differs (accepted lock: 2.46-1.fc44) |
| node | v22.23.1 | differs (accepted lock: v22.22.2) |
| bash | 5.3.9 | digest matches accepted R3 |
| riscv64-linux-gnu-gcc | 16.2.1 | B2's build |
| clang / ld.lld | 22.1.8 | B2's build |
| python3 | 3.14.7 | not in the accepted locks |
| shellcheck | 0.11.0 | not in the accepted locks; used by `--shellcheck` |
