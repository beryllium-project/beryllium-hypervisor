<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R0 fixed-profile freeze

## Status and claim boundary

R0 is the fixed-profile-and-layout package of the accepted
[bounded single-hart runtime plan](single-hart-runtime-plan.md). This document
is the authoritative, maintained R0 freeze and evidence record.

R0 **freezes and machine-checks declarations and consistency only**. It does
not implement, link, or execute a privileged runtime. Precise claims:

- R0 adds no privileged Beryllium C or assembly, no boot/trap/root-builder/SBI
  implementation, and no linked image.
- QEMU runtime results remain **NOT RUN** for Beryllium; the pinned command
  boots only OpenSBI during platform verification.
- Retained Helium evidence does not transfer. It is cited for method only.
- The Model 0.2 Rocq proof applies only to its bounded abstract model. The
  eleven-resource core projection is a **trace**, not a C refinement.
- The full thirteen-resource profile and its two R-X guest-code overlays are
  **unproved and unrefined**; they are an explicit operational extension and
  proof/correspondence cut point.
- K3 hardware remains **NOT RUN**. Public release remains **blocked**.

**R0 implementation and freeze are complete and accepted.** Responsible-human
review accepted the exact freeze commit
`64a88b15a6c35d522fa997699c4fb514b15da314` on 2026-07-27. The R1 pure-C
mechanism is documented separately in
[`single-hart-runtime-r1-evidence.md`](single-hart-runtime-r1-evidence.md),
and responsible-human review accepted exact R1 commit
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. Neither
acceptance transfers Model 0.2 or Helium claims or authorizes R2.

## 1. Tool, source, and platform lock

Verified in the pinned open environment (Fedora 44). The machine-readable lock
is `arch/riscv/be/r0-platform.conf` and is checked by
`tests/r0/check-tools.sh`.

| Component | Version | Exact NEVRA / identity |
| --- | --- | --- |
| OS base | Fedora 44 | `registry.fedoraproject.org/fedora@sha256:daf897befd7a78a52f11db5ca2229a4923991bb30709932770cb493f7a000cf0` |
| GNU Make | 4.4.1 | `make-4.4.1-12.fc44.x86_64` |
| GCC (host) | 16.1.1 | `gcc-16.1.1-2.fc44.x86_64` |
| Clang/LLVM | 22.1.8 | `clang-22.1.8-1.fc44.x86_64` |
| GNU ld (binutils) | 2.46.1 | `binutils-2.46.1-1.fc44.x86_64` |
| LLD | 22.1.8 | `lld-22.1.8-1.fc44.x86_64` |
| Node.js | v22.22.2 | `nodejs22-bin-22.22.2-3.fc44.noarch` |
| Rocq | 9.2 | retained for the combined gate; not used by R0 execution |
| RISC-V cross GCC | 16.1.1 | `gcc-riscv64-linux-gnu-16.1.1-1.fc44` (image toolchain for R1+, not built at R0) |
| QEMU | 10.2.2 | `qemu-system-riscv-core-10.2.2-1.fc44.x86_64` |
| OpenSBI firmware | `OpenSBI v1.7` banner | `/usr/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin`, SHA-256 `49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705` |

**OpenSBI provenance residual (stated honestly):** the firmware ships inside
the QEMU RPM (`-bios default`). Its exact upstream source commit is not
independently traceable from the packaged blob, so R0 pins it by byte SHA-256,
banner version, and owning NEVRA rather than inventing a source identity.

### Frozen QEMU command

```
qemu-system-riscv64 \
  -machine virt,aia=none \
  -cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,\
sstc=false,smstateen=false,svadu=false,debug=false \
  -smp 1 \
  -m 128M \
  -bios default \
  -kernel <beryllium-image.elf> \
  -nographic \
  -no-reboot
```

Each property was verified against QEMU 10.2.2:

- `h=true` enables the hypervisor extension; `-smp 1` instantiates hart zero
  only.
- `f=false,d=false,v=false` remove the floating-point and vector register
  files. The generic `rv64` CPU enables `zfa`, which **requires** F; R0 must
  therefore add `zfa=false`. With this string the OpenSBI boot report shows
  **Boot HART Base ISA `rv64imach`**, confirming F/D/V are absent. The
  plan-revision contingency is **not** triggered: F/D/V exclusion is supported,
  so no FPR/vector save-restore is required.
- **C stays enabled** (default). It adds no register file, base ISA is
  `rv64imach`, and the packaged OpenSBI uses compressed instructions.
- `sv48=off,sv57=off` fix HS Sv39 addressing; G-stage uses Sv39x4.
- Optional architectural state is disposed with supported properties:
  `sstc=false` (no Sstc timer CSRs), `smstateen=false` (no state-enable CSRs),
  `svadu=false` (no hardware A/D update; the root builder pre-sets A/D),
  `debug=false` (no Sdtrig triggers), and `-machine virt,aia=none` (no AIA
  IMSIC/APLIC). Counters (`zicntr`, `zihpm`) remain present at M-level for
  OpenSBI and are gated from VS/S via `hcounteren=0`/`scounteren=0` rather than
  removed.

### Verified OpenSBI handoff

`-bios default` on the pinned QEMU produces: Firmware Base `0x80000000`; Next
Mode **S-mode**; Boot HART Base ISA **`rv64imach`**; `a0` = hart id **0**;
`a1` = firmware/DTB pointer (recorded for diagnostics, never dereferenced);
PMP count 16 (M-mode owned); `MIDELEG=0x1666`, `MEDELEG=0xf4b509` at handoff
(M-mode owned, trusted assumption). The Beryllium image entry is `0x80200000`,
immediately above the OpenSBI-reserved region.

## 2. Complete physical memory and linker map

DRAM window (`-m 128M`) is `[0x80000000, 0x88000000)`. OpenSBI-reserved is
`[0x80000000, 0x80200000)`. The Beryllium image begins at `0x80200000`. The
authoritative table is `arch/riscv/be/r0-layout.h`; the
inspectable linker PLAN is
`arch/riscv/be/beryllium.lds.plan` (not a build target).

| # | Extent | Base | Size | End | Class / rights | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| — | opensbi-reserved | `0x80000000` | `0x200000` | `0x80200000` | firmware | M-mode |
| 1 | monitor-code | `0x80200000` | `0x8000` | `0x80208000` | R-X | monitor |
| 2 | monitor-data | `0x80208000` | `0x8000` | `0x80210000` | RW | monitor |
| — | diagnostic page | `0x8020f000` | `0x1000` | `0x80210000` | RW (in monitor data) | monitor |
| G | guard-image | `0x80210000` | `0x4000` | `0x80214000` | none | monitor |
| 3 | root-pool-management | `0x80214000` | `0x8000` | `0x8021c000` | table (16 KiB aligned) | monitor |
| 4 | root-pool-protected | `0x8021c000` | `0x8000` | `0x80224000` | table (16 KiB aligned) | monitor |
| G | guard-root | `0x80224000` | `0x1000` | `0x80225000` | none | monitor |
| 5 | trusted-stack-management | `0x80225000` | `0x2000` | `0x80227000` | RW | monitor |
| G | guard-stack-management | `0x80227000` | `0x1000` | `0x80228000` | none | monitor |
| 6 | trusted-stack-protected | `0x80228000` | `0x2000` | `0x8022a000` | RW | monitor |
| G | guard-stack-protected | `0x8022a000` | `0x1000` | `0x8022b000` | none | monitor |
| 7 | saved-state-management | `0x8022b000` | `0x1000` | `0x8022c000` | RW | monitor |
| 8 | saved-state-protected | `0x8022c000` | `0x1000` | `0x8022d000` | RW | monitor |
| G | guard-saved | `0x8022d000` | `0x1000` | `0x8022e000` | none | monitor |
| 9 | private-management | `0x8022e000` | `0x1000` | `0x8022f000` | RW (guest stack) | management |
| 10 | private-protected | `0x8022f000` | `0x1000` | `0x80230000` | RW (guest stack) | protected |
| 11 | shared | `0x80230000` | `0x1000` | `0x80231000` | RW→R directional | channel |
| G | guard-wx | `0x80231000` | `0x1000` | `0x80232000` | none (W^X separation) | monitor |
| 12 | guest-code-management | `0x80232000` | `0x1000` | `0x80233000` | R-X (extension) | management |
| 13 | guest-code-protected | `0x80233000` | `0x1000` | `0x80234000` | R-X (extension) | protected |
| — | reserved DRAM | `0x80234000` | … | `0x88000000` | unused (DTB near `0x87e00000`) | firmware |

**Alignment and non-overlap.** All extents are 4 KiB aligned and page-multiple
sized. Both root pools are 16 KiB aligned (`0x80214000` and `0x8021c000`).
Every pair of frozen extents is disjoint and the entire `[0x80200000,
0x80234000)` span is covered by resources and guards with no gaps or overlap.
This is machine-checked now by `tests/r0/r0-check.c` against `r0-layout.h`.

**W^X.** No extent is both writable and executable. Monitor code (1) and both
guest-code overlays (12, 13) are R-X; all data, stacks, saved-state, private,
and shared extents are RW-NX; a guard page separates the RW region from the
R-X guest-code overlays.

### Sv39x4 page-table pool sizing (complete pool, not a bare root)

Each domain reserves one **32 KiB (eight 4 KiB page)** pool, 16 KiB aligned.
The complete pool for the fixed mapping set is:

| Pool page(s) | Role | Status |
| --- | --- | --- |
| 0–3 (16 KiB) | Sv39x4 level-2 root (2048 × 8 B) | used |
| 4 | level-1 table (512 × 8 B) | used |
| 5 | level-0 table (512 × 8 B) | used |
| 6–7 (8 KiB) | reserved spare | unused |

A 16 KiB root alone is **not** a complete 4 KiB-leaf pool. The frozen mappings
of each root all share one level-2 slot (VPN2=1) and one level-1 slot (VPN1=0),
so exactly one level-1 and one level-0 table complete the walk to 4 KiB leaves:
**6 used pages, 2 spare pages** per pool. `tests/r0/r0-check.c` proves the
shared-slot property by computing the Sv39x4 VPN indices of every frozen leaf.

## 3. Frozen configuration and Model 0.2 core-projection trace

The frozen inventory and copied proposal are reviewable restricted-C
initializers in `virt/be/r0-config.c`, with constants in
`include/be/r0-config.h`. They express the
**eleven-resource Model 0.2 core projection** (resources 1–11) at the real R0
physical addresses.

The accepted Model 0.2 host validator (`be_check_inventory`, `be_canonicalize`,
`be_check_canonical`, `be_derive_enforcement`, `be_check_enforcement`) accepts
the core projection under both GCC and Clang and produces a **byte-identical**
deterministic trace, `build/r0/reports/core-projection.json`. The trace shows
every frozen constant instantiating the accepted abstract domains, frames,
channel, and rights. The Model 0.2 composition constraint (1 monitor-code,
1 monitor-data, 2 root-table, 2 trusted-stack, 2 saved-state, 3 assignable) is
satisfied exactly.

Guest-physical addresses (VS-stage Bare, so GVA = GPA for the fixtures):
management private `0x40000000`, protected private `0x40001000`, shared
`0x40002000`. Directional channel: source `management` (RW) → target
`protected` (R) on the shared frame.

**Core projection vs. full profile.** The full R0 profile has thirteen
resources; the two guest-code overlays (12, 13) at GPAs `0x40010000` and
`0x40011000` with R-X authorities are an **operational extension**. Model 0.2
models no guest-code frame class, so the full profile is **not** a Model 0.2
refinement and is **not** covered by the eleven-resource C fixture or the Rocq
proof. The precise eleven-resource projection is preserved for traceability;
the full profile is checked independently for alignment, non-overlap, W^X,
monitor exclusion, and pool sizing by `tests/r0/r0-check.c`.

## 4. VS/HS register-state matrix

The authoritative matrix is enumerated and machine-checked in
`arch/riscv/be/r0-registers.h`. Every accessible element
has exactly one disposition: **S** saved/restored per domain, **R**
reset+verified per entry, **D** denied under a checked control, **C** constant
trusted assumption, or **X** explicitly excluded/absent.

| Group | Elements | Disposition |
| --- | --- | --- |
| Integer + guest | `x1`–`x31`, `sp` via `sscratch`, guest PC (`vsepc`), guest stack | S; `x0` X |
| VS CSRs | `vsepc`,`vscause`,`vstval`,`vstvec` S; `vsstatus`,`vsie`,`vsscratch`,`vsip` R; `vsatp`=Bare written+verified every entry | S/R |
| HS hypervisor | `hstatus` with **VTVM=1** (also SPV=1, SPVP=1, VTSR=1, VTW=1) R; `hedeleg`=0,`hideleg`=0,`hie`=0,`hvip`=0,`hcounteren`=0,`htimedelta`=0,`henvcfg` (STCE=0) R; `hip`,`hgeie`,`hgeip` D | R/D |
| HS trap | `scause`,`sepc`,`stval`,`htval` S; `sstatus`,`stvec`,`sscratch`,`sie`,`senvcfg`,`scounteren` R; `sip` D; HS `satp`=Bare C; `htinst` may be 0 X | S/R/D/C/X |
| Active binding | active `HGATP`, trusted stack, saved-state identity S; VMID=0 C | S/C |
| Counters/PMU | VS/U counter views D via `hcounteren`/`scounteren`=0; `mcounteren`/`mcountinhibit`/`mhpm*` C | D/C |
| Floating-point/vector | `f0`–`f31`/`fcsr`, `v0`–`v31`/`vcsr`/`vl`/`vtype` | X (absent, `rv64imach`) |
| Optional state | AIA/Ssaia, Sstc, Smstateen, Sdtrig, debug/trace | X (absent via CPU/machine props) |
| Machine mode | PMP/ePMP/`mseccfg`, `misa`/`medeleg`/`mideleg`, IOMMU/IOPMP | C; IOMMU/IOPMP X |

**Correction applied vs. Helium (do not transfer Helium behavior):** before
every VS entry HS sets and verifies **`hstatus.VTVM=1`** and writes+verifies
**`vsatp.MODE=Bare`**. Any guest `satp` write or trapped translation-management
instruction is a virtual-instruction event (`scause=22`) → terminal failure.
Helium clears VTVM; R0 sets it.

**Context-switch order (must be enforced and tested at R4/R5):** validate
source binding → save source state → select target root/VMID/stack/saved-state
as one pending binding → write `HGATP` → local-hart `HFENCE.GVMA x0,x0` →
restore target state → publish active → execute. No target instruction may run
before the fence.

## 5. HS-to-M SBI allowlist and error matrix

Exactly three extensions, machine-checked in
`arch/riscv/be/r0-sbi.h`. Binary convention: `a7`=EID,
`a6`=FID, `a0`=error, `a1`=value. Every call lives in the assembly/platform
boundary, uses HS-owned memory, no guest-controlled pointer, no ambient
forwarding, and deterministic failure.

| Purpose | EID | FID | Notes |
| --- | --- | --- | --- |
| Discovery | Base `0x10` | 0 `get_spec_version`, 3 `probe_extension` | Must explicitly probe DBCN and SRST; the spec version alone is not evidence either exists |
| Diagnostics | DBCN `0x4442434E` | 0 `console_write` | Physical range split lo/hi, never a guest VA; inside the HS diagnostic page; test evidence only |
| Termination | SRST `0x53525354` | 0 `system_reset` | type=0 shutdown, reason=0; does not return on success |

No legacy console/shutdown (EID `0x01`/`0x08`), no guest SBI, and no timer,
IPI, remote-fence, hart-state, PMU, suspend, or vendor extension.

**DBCN constraints.** The diagnostic buffer lies inside the one HS-owned
diagnostic page (`0x8020f000`), is range-checked without overflow, satisfies the
SBI physical-address rules, never overlaps guest/proposal/canonical/root/stack/
saved-state, and is inaccessible to both VS roots.

**Bounded retry.** A successful DBCN write may consume 0..N bytes. Progress is
accumulated with one fixed cap `BE_R0_SBI_DBCN_MAX_ITERATIONS = 256` (chosen
because the fixed diagnostic strings are short and constant, so a compliant
console drains within the cap; a single constant, never data-dependent).

| Outcome | Return | Deterministic handling |
| --- | --- | --- |
| DBCN SUCCESS, value = N (incl. 0) | 0..num_bytes | Accumulate; advance base; continue up to the cap |
| DBCN cap exhausted, bytes pending | — | Diagnostics unavailable → fixed failure path; authority unchanged |
| DBCN `INVALID_PARAM`/`INVALID_ADDRESS` | −3 / −5 | Terminal (programming/layout error); no retry |
| DBCN `DENIED`/`FAILED` | −4 / −1 | Diagnostics unavailable → fixed failure path |
| DBCN malformed (value > num_bytes, undefined error) | — | Terminal; never advance progress |
| Probe reports DBCN or SRST absent, or `NOT_SUPPORTED` | −2 | Profile **fails closed**; never an undocumented fallback |
| SRST success | (no return) | Expected terminus |
| SRST `INVALID_PARAM`/`NOT_SUPPORTED`/`FAILED` | — | Terminal (platform may deny shutdown; accepted residual) |

## 6. Fixture and evidence plan

R0 **specifies** the complete fixture matrix and **executes** only the
non-privileged consistency, tool, layout, and trace checks. Positive, negative,
image, exact-byte, and QEMU fixtures are specified for R1–R7 and their review
gates; they are **not** implemented at R0.

### Executes now (R0)

- Model 0.2 core-projection trace (GCC/Clang byte-identical JSON).
- Positive abstract accesses on the core projection: management/protected
  private RW, management shared write, protected shared read; cross-private and
  protected-shared-write denials (via `be_model_access`).
- Layout: alignment, non-overlap, DRAM containment, 16 KiB root alignment,
  monitor exclusion, W^X, diagnostic-page containment, pool sizing.
- Register-matrix group completeness and F/D/V exclusion.
- SBI allowlist (exactly three EIDs), fail-closed probe, non-returning SRST,
  nonzero retry bound.
- Tool/firmware lock incl. OpenSBI SHA-256; frozen QEMU command boots OpenSBI.

### Specified now, executed later

| Class | Examples | Executes at |
| --- | --- | --- |
| Positive | private RW, channel write/read, VS ecall, saved-state restoration | R4–R5 QEMU |
| Negative — G-stage | cross-private fault (`scause=21`), shared-write fault (`scause=23`), `satp`/sfence virtual-instruction (`scause=22`) | R4–R6 QEMU |
| Negative — control | wrong root/binding/PC/event, wrong phase, skipped fence, partial publication, malformed input | R4–R6 (some already abstract in Model 0.2) |
| Negative — SBI | partial/zero DBCN, `INVALID_PARAM`/`DENIED`/`FAILED`, retry exhausted, extension absent, output loss | R3 |
| Unsupported state | F/D/V access (illegal), unsupported instruction | R4 (CPU pinned at R0) |
| Image / exact-byte | linker placement/ASSERTs, ELF/binary/disassembly/map identities, exact wrapper bytes | R3, R7 |
| Ordered evidence | ordered serial/event markers, tool-drift, reproducibility bundle | R7 |

## 7. Claim and cut-point ledger

| Item | R0 status | Remaining obligation |
| --- | --- | --- |
| Eleven-resource core projection | Traced through Model 0.2 host validator (GCC/Clang) | Not a C refinement; no proof transfer |
| Full thirteen-resource profile | Consistency-checked (layout, W^X, exclusion, pools) | Unproved/unrefined; guest-code overlays are a code cut point |
| Two R-X guest-code authorities | Specified in the extension; excluded from Model 0.2 | Future proposal must carry them from sealed authority |
| Register matrix | Enumerated + group-complete; VTVM=1 correction recorded | Completeness is an assumption until R4 save/restore evidence |
| SBI allowlist | Frozen + machine-checked | Behavior unproved until R3 boundary tests |
| Sv39x4 root builder | Pool sizing frozen | No builder exists until R2 |
| Assembly boundary | Declared only | Unproved until R7 exact-byte adaptation |
| OpenSBI / QEMU / firmware / hardware | Pinned; boots OpenSBI only | Not verified; K3 NOT RUN |

## 8. R0 checks and retained evidence

Non-privileged, using existing open tooling:

- `make -C tests toolcheck` — pinned tools, cross GCC, QEMU, and OpenSBI digest.
- `make -C tests r0-check` — GCC+Clang consistency checker and byte-identical
  core-projection trace.
- `make -C tests r0-freeze` — toolcheck, r0-check, and evidence generation.
- `./be r0-check` and `./be r0-freeze` delegate to the above; `make check`
  includes `r0-check` and `evidence-check` verifies
  `build/r0/evidence/source.sha256`.

Retained evidence identities under `build/r0/evidence/`: `source.sha256`
(frozen R0 files), `artifacts.sha256` (the trace JSON), `tool-versions.txt`,
`source-state.txt`, and `claim-status.txt`
(`privileged_code=no`, `qemu_beryllium_result=NOT-RUN`,
`r0_acceptance=accepted`, historical R0-era
`r1_authorized=authorized-next-not-started`, and `public_release=blocked`).
That retained artifact is part of the frozen R0 evidence set; it does not
describe the current local R1 worktree status.

## Primary references

- [Bounded single-hart runtime plan](single-hart-runtime-plan.md)
- [Architecture Model 0.2](architecture-model-0.2.md) and its
  [implementation and evidence](architecture-model-0.2-evidence.md)
- [Handoff record](HANDOFF.md)
- RISC-V Privileged/Hypervisor, SBI Base/DBCN/SRST specifications, and the
  QEMU RISC-V `virt` platform (see the runtime plan reference list)
