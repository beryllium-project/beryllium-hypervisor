<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# After release candidate 3: the candidates, on one page

Decision support for the responsible human, 2026-10-31, after the
instruction `because we have a review release published, we can take a
bit more time if needed to get to a useful MVP 1.0. make the one page
comparison`. It compares what could be pulled into MVP 1.0 before the
release path's steps 2 to 7 against what stays after. It selects
nothing; every row needs its own bounded plan, and adding one to MVP 1.0
is a revision of the [MVP plan](mvp-plan.md) (the next would be S3-C).
Sources: [implementation plan](implementation-plan.md) milestones 3 to
10; the MVP plan's D5 and "Release path"; the
[security model](security-model-v1.md); the
[project snapshot](project-snapshot-mvp-1.0-rc2.md) section 8; the
[hardware roadmap](riscv-security-hardware.md); `mvp/README.md`.

## Where MVP 1.0 stands

Release candidate 3 (`89ef04e9`, accepted 2026-10-31) is published as a
review snapshot. A researcher can build it, run the three scenarios in
QEMU and on a COM260, read the authority report and the ledger, and
write a scenario. They cannot type into a guest (console output only;
the guest kernel already has the SBI console driver, `CONFIG_HVC_RISCV_SBI`,
which polls `sbi_debug_console_read` and gets nothing), the guests are
`nolibc` programs in an initramfs with no device, and nothing is proved
about the monitor's C beyond host tests and the checkers.

## The candidates

Size is in this project's own units: M1 was about 1,800 monitor lines
plus checking and one board campaign in one day of sessions; M2 2,641
plus 4,877; M6 3,258 in one day; M5 7,439 in a day and a half.

| Candidate | What a researcher gains | Size | Board time and new facts | Depends on | Risk to the claim and the model | Where it is recorded |
| --- | --- | --- | --- | --- | --- | --- |
| **A. Interactive guests**: console input and a pinned BusyBox/musl userland (reverses MVP plan D5) | A shell in each Linux guest over the one serial line, with a focus key choosing the domain: live demonstrations (touch the other guest's page, get `SIGSEGV`; write the shared page from the writer, read it from the reader), scripted sessions as evidence | M1-sized. Monitor: hart 0 polls OpenSBI's DBCN read (one new executor function; hart 0 already writes through DBCN) into a per-domain input ring, the reverse of today's rings, served to the guest's `dbcn_read`; a declared console-input object in the policy. Tools: two pinned sources (BusyBox, musl) in `build-guest.sh`, a scripted-session checker, a guest-typing mode for the console tool with its own keystroke record | One campaign; the only new fact is DBCN read from HS on this firmware (OpenSBI 1.6 implements it; untested here) | Nothing | Low. A new channel (hart 0 to a domain) that the policy must declare; the claim's text would gain a sentence; no model change | D5 ("Not in MVP 1.0; `nolibc` programs"); B7 plan's deferred list; roadmap "Planned sequence" |
| **B. First verification plan**, stage 1 and a refinement pilot (snapshot section 8) | Something proved about the monitor's own C: a Rocq operational model of the rings, barrier, and denial path, and one C function (`mvp-ring.c`) refined to it by CN or Frama-C/WP, chosen on the same leaf | M3-sized for the model (M3 was 3,044 Rocq lines); the pilot is a tool evaluation with an unknown tail | None; no board | M6's executor seam (done) | None to the claim's current text; it adds rows to the ledger. Tool qualification risk (CN is not packaged; Frama-C and Why3 are) | Snapshot section 8; S1 H22, H38, H41; implementation plan "Selected proof ecosystem" |
| **C. Milestone 3's dynamic part**: domain restart, notifications, a management vocabulary | A protected domain that can be restarted after a tested compromise, and told things; the security-research platform's control plane | M2-sized or larger | One campaign; no new hardware fact | A, for anyone to drive it live | Medium: dynamic authority under the M01-A ceiling, which the security model found undecidable in the dynamic case; a Model 0.2 change is likely | Implementation plan 3; MVP plan Q/D on M2 "stays static"; security model v1 "dynamic authority ceiling" |
| **D. Measured launch, bounded** (milestone 7's first step) | The monitor measures its own image, configuration, and policy and reports the digests; the chain from M2's measurement extended upward | Small to medium | Facts about the board's secure boot and eFuse state, which no record holds (the hardware roadmap lists them as unknown) | Nothing | Low on the code; the claim must say "local measured identity, not attestation" because there is no root of trust the project has characterized | Implementation plan 7; hardware roadmap "Secure boot and lifecycle" |
| **E. One pass-through device** under IOMMU/IOPMP with guest external interrupts (milestone 5's precursor) | A Linux guest with a real NIC or NVMe: a normal OS one can install packages on | Several M5s: IOMMU and IOPMP programming from HS, AIA guest interrupt files (the board reports seven) and `hvip` routing, a device tree with the device, the policy's device objects | Heavy: a characterization campaign first (locate the IOMMU for the device's PCIe root, SIDs, default deny, IOPMP ownership), then the milestone's own | A (to use it), and the device inventory | High: new object classes in the policy (registers, DMA buffers), new assumptions about firmware ownership of the fabric; the claim's "architectural only" boundary widens | Implementation plan 5; hardware roadmap "Physical and I/O protection" ("locate and characterize") |
| **F. The I/O service domain** proper (milestone 5) | Devices owned by one restartable service domain, other domains served over a grant/queue protocol: the architecture's intended shape | E plus a protocol and a second guest side: the largest unbuilt piece | E's, then more | E; probably fires the capability trigger (S2) | High; it is where the policy substrate (milestone 6) is likely to be forced | Implementation plan 5 and 6 |
| **G. Dynamic multicore** (milestone 4) | Migration, overcommit, a control lock | Large | Heavy | Nothing a researcher needs now | High; re-proves isolation under serialized multicore | Implementation plan 4 |
| **H. Policy substrate** (milestone 6) | Capabilities or a runtime TE check | Gated | None until a trigger fires | A trigger, which F would supply | By design | Security model v1; implementation plan 6 |
| Milestones 8 (Arm), 9 (assurance release), 10 (upstream) | Later by their own gates | | | 9 depends on B's line; 10 on the clean public repository | | Implementation plan 8 to 10 |
| **Release path steps 2 to 7** as they stand | A clean public repository of the reviewed MVP | Docs and selection; one gates run in the clean repository | None | Your selection (step 2) | None | MVP plan "Release path"; the review snapshot is a bounded first form of steps 2 to 4 |

## Three readings of "useful"

- **Useful to show.** A alone changes the demonstration from scripted
  output to a live shell in two isolated Linux guests on one board. It
  is the cheapest row and the only one the public snapshot's audience
  would see at once.
- **Useful to build on.** A plus C gives a platform someone can drive:
  start, compromise, restart, observe. C is where the model and the
  security model begin to move, so it is the first row that spends
  review time outside `mvp/`.
- **Useful to trust.** B is the first proof about the monitor's own
  code. It changes nothing a user runs; it changes what the claim ledger
  may say and what a reviewer of the snapshot can check. It needs no
  board and can run beside A.

E and F are where a "normal Linux guest" with storage and network lives;
they are the largest and the most hardware-bound, and they are the first
rows that need facts about the K3 no record holds.

## A sequence, if asked

Not a decision: A first (one bounded plan, S3-C adding M7, about a day
of sessions and one campaign when the board is free); B beside it on its
own branch, board-free; then the release path's steps 2 to 7 for an MVP
1.0 that has both; then D as a small follow-on; E and F as MVP 2.0's
spine after a device-characterization campaign; C when the research use
case asks for restart. The board is in the other project's use today,
so B is the row that can start now.

## Directions recorded the same day (the responsible human, 2026-10-31)

After this page was read, the responsible human gave the ladder's shape
and three directions in conversation. They are direction, not an accepted
plan; the next MVP plan revision (S3-C) is where they become one.

- **The ladder.** MVP 1.0, "something useful": interactive guests
  (console input and a BusyBox/musl userland; D5 reversed) and the first
  verification plan, which resolves Helium's H38 and H41; measurement
  (below) joins it. MVP 2.0, "finalize core architecture and formalize":
  the device path and the service domain (E and F above), H06 and H07
  (policy semantics), H08 and H09 (the two triggers), H57 and H58
  analyses, and, on this page's advice, dynamic management (C). MVP 3.0,
  "composition and extension": MPT, CoVE, CHERI, and policy composition
  (MCS or MLS, a security model v2), investigation-grade unless hardware
  arrives. MVP 4.0: the general-guest work (an immutable image-based
  guest such as ParticleOS), with stage work in parallel as community
  resourcing allows. Revisit after MVP 1.0's release.
- **Measurement first, then attestation.** `we want to measure and
  attest, but start with measurement`. A hardware root of trust is to be
  simulated for the proof of concept: the human has physical access to
  the board, its GPIO pins and JTAG, and possibly the carrier's
  management chip, and controls the ESP32 dongle. Today the monitor
  measures the protected domain's kernel and device tree before entry
  (M2; the `wrong-measurement` negative), and U-Boot's `md5sum` of the
  loaded image in `be_ld` is a digest by the stage below, used as run
  attribution, not as a chain. Measurement in MVP 1.0 would make the
  chain explicit (the stage below measures the monitor; the monitor
  measures its configuration, policy, and domains; a measurement log);
  attestation (a key, a nonce, a signed quote) with the simulated root
  of trust in MVP 2.0.
- **IMA is never used.** `we are not using IMA ever`. Beryllium measures
  at the domain boundary (images, configuration, policy), not files
  inside a guest. Recorded as a standing decision.
- **systemd's measured boot** (immutable image-based guests, UKIs,
  `systemd-pcrphase`, `systemd-pcrlock`, `systemd-measure`) is to be
  looked at where applicable. It targets a TPM 2.0 the guests do not
  have; applicability means a measurement interface Beryllium offers a
  guest (a PCR-like extension per domain, or later a minimal vTPM), and
  the authority report already plays the role `pcrlock`'s expected
  measurements play.
- **Ammutable** is a company (Germany; the systemd and UAPI-group core),
  not a typo for "immutable": its measurement and image-based boot work
  is to be looked at where applicable, alongside systemd's measured boot
  above.
- A second board, a **K3 Mini-ITX**, is expected within about a week and
  is likely usable during MVP 2.0 (a second platform record; the COM260
  stays the MVP 1.0 board).
- After S3-C is written, the human will run a separate review with a
  different agent and have it write a report as steering input; S3-C is
  therefore written to be read on its own.

## LiteBox, analyzed for MVP 2.0 (2026-10-31)

This rechecks the [LiteBox and minimal VS runtimes
sidebar](sidebar-minimal-vs-runtimes.md) of 2026-07-23, which read the
repository at `28918b64` (2026-07-22) and retained LiteBox "as an x86
LVBS/library-OS architecture reference", not a RISC-V runtime, with Hermit
and a purpose-built stub as the leading candidates for a first Rust
service domain and the bake-off left to its own plan. That disposition
still holds; what follows is what has changed and where a port would fit.

[microsoft/litebox](https://github.com/microsoft/litebox) at `df2433ba`
(2026-10-29; "actively evolving", MIT): a security-focused library OS in
Rust, about 106,000 lines in 23 crates, built on stable Rust. Since the
July reading the tree gained `litebox_service_heki` and lost
`litebox_platform_multiplex`; the architecture list is unchanged. A "North"
shim gives programs an ABI (`litebox_shim_linux`, the Linux syscall ABI
for unmodified Linux programs, 2,400 lines; `litebox_shim_optee`, the
OP-TEE trusted-application API); a "South" `Platform` supplies threads,
timers, signals, mutexes, time, and IP packets (`litebox/src/platform`);
platforms exist for Linux userland, the Linux kernel, Windows userland,
SEV-SNP, and Hyper-V VTL1 (`litebox_platform_lvbs`, "work in progress").
`litebox_service_heki` is a VTL0 kernel-integrity service (kernel, module,
and kexec integrity, text patching) written over a `Vtl0Gate` with no
knowledge of Hyper-V. Architectures: x86_64 (203 `target_arch` sites) and
aarch64 (43); the core's `arch/` has those two; there is no RISC-V port.

Where it would fit Beryllium:

| Use | What it gives | What it needs | Fit |
| --- | --- | --- | --- |
| A protected-domain runtime | The anchor's protected domain is a whole Linux kernel with a `nolibc` program. LiteBox with the Linux shim on a Beryllium South platform would run the same program with no kernel in the domain: a smaller protected-domain TCB, in Rust, which the direction already allows for VS components (the Rust sidebar; "Rust outside the initial core") | A `litebox/src/arch/riscv64` port (entry, memory management, TLS: real work, upstream's or ours) and a `litebox_platform_beryllium` crate over the B5 SBI subset and the channel pages; a second pinned external input beside Linux, with its own reproducible build | MVP 2.0, "finalize core architecture": the first non-Linux domain, and a test of the SBI subset and the channel protocol from a second client |
| An integrity service over the anchor pattern | HEKI's shape, a service in the protected domain enforcing the untrusted Linux domain's kernel integrity, is the "runtime integrity-monitor experiment" of implementation-plan milestone 7 and the question of the LVBS-equivalence sidebar, with Beryllium as the hypervisor and the anchor's request and response pages as the gate | The runtime above, plus a gate protocol and mappings of the untrusted domain's kernel text into the service's view (a policy object class: another domain's memory, read-only), and the measurement chain of MVP 1.0 to anchor it | MVP 2.0 or 3.0, after measurement and attestation exist |
| The syscall rewriter and the LVBS platform as references | Their shapes, not their code: x86-only, Hyper-V-specific | Reading | Design input to MVP 2.0's service-domain protocol |

What it does not change: the core stays restricted C; the claim's text;
the policy's role. The risks to record for the 2.0 plan: an external
project whose interfaces are changing; a RISC-V port that does not exist;
Rust's toolchain joining the tool lock and the evaluator; MIT in a
GPL-3.0-only distribution (compatible, with the notice carried). The
choice between a LiteBox port and the sidebar's candidates is the bake-off
the sidebar left to its own plan; MVP 2.0's plan is where it is decided.
Nothing here authorizes it.
