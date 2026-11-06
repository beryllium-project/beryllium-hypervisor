<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B1 COM260 results, 2026-10-06

These are the retained records of three RAM-only B1 runs on the SpacemiT K3
COM260, plus the read-only preflight and non-disruptive load check that
preceded them. `summary.md` is the reproducibility table.

## Inputs

- **Image:** `build/k3-b1/gcc/be-k3-b1.bin`, the GCC build. It is 212,992
  bytes with SHA-256
  `43aaa948e3b464550cd520705e5ec56603d12a64f9cd715029b14ce375a56e4a`.
  - Commit `e391b55e` generated and built it from the accepted R4 sources
    (`0783dfc6`) through `bringup/k3-b1/scripts/port.py`.
  - `make -C bringup/k3-b1 image` reproduces it.
- **Tooling:** the commit `e391b55e` tooling, run unmodified. Every board
  step came after that commit (07:20:55 UTC); later commits changed only
  documentation.
- **Board:**
  - Fedora `7.1.5-201.0.riscv64.omni.fc44` on the COM260, with OpenSBI 1.6
    (SBI 2.0).
  - Reached as `fedora@k3e` over a direct Ethernet link.
  - Run 1 took place before the board travelled to the Linux Plumbers
    Conference venue; runs 2 and 3 took place there.
- **Serial:** the operator's `picocom -g` log of `/dev/ttyUSB0` at 115200
  8N1, followed read-only with `K3_SERIAL_LOG`.

## Sequence (UTC)

| Step | Time | Record |
| --- | --- | --- |
| Read-only preflight | 07:21:08 | `preflight.txt` |
| Load check: raw load at `0x1_0200_0000`, FDT at `0x1_0210_0000`, verify, unload; no kexec | 07:21:16 | `load-check/20261006T072116Z/` |
| Run 1 (boot `c69d166f`) | 07:21:37 | `20261006T072137Z/` |
| Board moved to the conference venue, re-cabled, Fedora autoboot | | |
| Run 2 (boot `c0633053`) | 09:32:48 | `20261006T093248Z/` |
| Human reset; Fedora autoboot | | |
| Run 3 (boot `56f41e63`) | 10:11:54 | `20261006T101154Z/` |

Every run printed all ten accepted R3/R4 markers. After `BE_R4:03` the
management guest spun in VS mode until a human reset, as in accepted R4.

## Files

Run records, under `<run>/`:

| File | Content |
| --- | --- |
| `run.txt` | Run metadata: image and on-board hashes, boot ID, kernel, lockdown, loader line, kexec timing, outcome |
| `load.txt` | `kexec-load.py raw` probe and load output |
| `check.txt`, `result.json` | `bringup/k3-b1/tests/check-b1-markers.py` output for the full capture, checked against `--base 0x102000000` |
| `handoff-excerpt.log` | The capture from Linux's kexec handoff through the last B1 marker |

Directory files:

| File | Content |
| --- | --- |
| `captures.txt` | SHA-256, bytes, and lines of each full serial capture |
| `originals.sha256` | SHA-256 of the original files behind every retained copy |
| `MANIFEST.sha256` | SHA-256 of every other file in this directory |

## Transformations

`bringup/k3-b0/tests/retain-results.py` built this directory:

- Absolute local paths are rewritten to `<repo>` or `<spacemit-k3>`.
- The root filesystem UUID is redacted.
- Carriage returns are removed.
- The full serial captures stay out of the repository because they include
  systemd terminal metadata such as the board's machine ID. They are
  retained privately, and `captures.txt` and `originals.sha256` identify
  them.

The excerpts pass the B1 marker checker on their own:

```sh
for run in bringup/k3-b1/results/20261006-com260/2026*/; do
    python3 bringup/k3-b1/tests/check-b1-markers.py \
        "$run/handoff-excerpt.log" --base 0x102000000
done
(cd bringup/k3-b1/results/20261006-com260 && sha256sum -c MANIFEST.sha256)
```

This is diagnostic bring-up evidence for one board, one firmware build, and
one Linux handoff path. It is not formal verification, hardware
qualification, or a transfer of the accepted QEMU R3/R4 claims.
