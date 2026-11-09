<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# The CHERI stack and its research records

This directory holds what Beryllium's CHERI work needs from outside the
MVP's tool lock: the pins of the CHERI stack, the tools that fetch and
build it, and the CHERI emulator's two local changes. It also keeps the
records of the CHERI experiments that led to the CHERI platform work
(`planning/cheri-platform.md`). The CHERI-aware monitor and its guests
are a build variant of the MVP, run on CHERI v0.9.3 under emulation;
nothing here is evidence for MVP 1.0's claim (`mvp/docs/claim.md`).

## Where it came from

Everything here came from beryllium-cheri, the responsible human's CHERI
research repository, at its commit
`316ad8c48de39e97084d0bfaaf023ed61c88e1c8`. That repository was local and
never published, so its commits do not resolve here. It moved into
Beryllium as work package CI-3 of the CHERI integration plan, an
internal planning record accepted on 2026-11-09, and is now closed and
kept read-only as an archive.

[`provenance.txt`](provenance.txt) lists the 49 files copied from it,
each with its SHA-256 there, its path there, and its path here. Each was
copied byte for byte. Four of them, the scripts in `tools/`, were then
adapted to this tree, and its `README.md` was rewritten as this file.
Its handoff, its collaboration ledger, its instructions and AI policy,
its licence files, its Git configuration files, and its import patches
for Beryllium, with the two scripts that checked them, stayed there.
The rest of its `docs/`, the research dossier, the executive summary,
and the dossier's review with its brief, stayed there too, being not
public-safe copy or not yet reviewed by the responsible human.

## What it holds

| Path | What it is | Kind |
| --- | --- | --- |
| [`pins.txt`](pins.txt) | The CHERI stack's lock: every external pin of the stack and the research, by commit, tag, or archive, with its SHA-256 where it was fetched | Tool input |
| [`tools/`](tools/) | `fetch-stack.sh`, `build-stack.sh`, `build-qemu.sh`, and `build-qemu-vs-reset.sh`, which fetch and build the stack from the pins | Tools |
| [`patches/`](patches/) | The CHERI QEMU's two local changes, which `tools/build-qemu-vs-reset.sh` applies | Tool input |
| [`experiments/`](experiments/) | The research's experiments: their scripts, notes, results, and patch series | Records |
| [`provenance.txt`](provenance.txt) | Where each copied file came from | Record |

### Tools and records

The tools are maintained here. They read their pins from `pins.txt`
alone, and the MVP's CHERI tools, `mvp/tools/cheri-check.sh` and
`mvp/tools/cheri-live.sh`, read the same file.

The records are kept as they were at `316ad8c`. No check or gate runs
them, and they are not changed to fit this tree. They name
beryllium-cheri's paths: its `tools/pins.txt` is `pins.txt` here, its
`experiments/fetch-stack.sh`, `build-stack.sh`, `build-qemu.sh`, and
`build-qemu-vs-reset.sh` are in `tools/`, and its other `experiments/`
files are under `experiments/`. Some records link or name files that
stayed in the research repository, such as its collaboration ledger, its
import package, and the dossier's review. Most commits they name are
beryllium-cheri's or those of Beryllium's internal repository, which do
not resolve here. Each record describes the code of its own date, not
this tree.

## Building the stack

The tools build the stack under a stack root, `CHERI_DIR`, which each
takes as its last argument; by default it is `build/cheri/` in this
repository, which Git ignores. From the repository's root:

```sh
cheri/tools/fetch-stack.sh
cheri/tools/build-stack.sh
cheri/tools/build-qemu-vs-reset.sh --ia-fix
```

1. `fetch-stack.sh` fetches each pinned source into
   `build/cheri/toolchains/`, in the directories that cheribuild uses,
   and requires each commit's `git archive` SHA-256 to be its pin's.
2. `build-stack.sh` builds the CHERI Alliance SDK with the pinned
   cheribuild from those sources, unchanged: LLVM, musl, the Linux
   kernel, BusyBox, and the SDK's purecap OpenSBI, for CHERI v0.9.3. Then
   `build-qemu.sh` builds the pinned QEMU unchanged, and the Python
   environment, with the pinned `distlib`, that QEMU 8.1's `configure`
   needs.
3. `build-qemu-vs-reset.sh --ia-fix` copies the pinned QEMU source to
   `build/cheri/build/qemu-ia-fix/`, applies both patches there, and
   builds the CHERI emulator that the CHERI tools run. Without
   `--ia-fix` it applies the first patch alone, in
   `build/cheri/build/qemu-vs-reset/`.

The tools need no root access. Besides Git, they need curl, rsync,
Python 3 with its `venv` module, clang, make, and what cheribuild and
QEMU's build need. In beryllium-cheri the stack took about 20 GB, and
`experiments/README.md` records about 25 minutes for the build on 28
cores; `JOBS` sets the parallel jobs (default 28).

Under the stack root the layout is beryllium-cheri's, `toolchains/` and
`build/`, so a checkout of it with its stack built serves as a stack
root too.

## Using the stack

`mvp/tools/cheri-check.sh` and `mvp/tools/cheri-live.sh` take the stack
from `build/cheri/`, or from the stack root given as their last
argument:

```sh
mvp/tools/cheri-check.sh
mvp/tools/cheri-check.sh /path/to/stack-root
```

Each prints its description with `--help`, and
`planning/cheri-platform.md` describes the check, its parts, and the live
runs. The check builds the CHERI Linux guests from the stack's sources
and compares each output with `mvp/guest/cheri-pins.txt`, which also
pins the SDK's OpenSBI firmware that the emulator boots.
