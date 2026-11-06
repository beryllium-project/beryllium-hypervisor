<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B2 COM260 results, 2026-10-06

These are the retained records of four RAM-only B2 runs on the SpacemiT K3
COM260, three with the GCC image and one with the Clang image. They also
include the read-only preflight and the two non-disruptive load checks that
preceded the runs. `summary.md` is the reproducibility table.

## Inputs

- **Images:** both are 212,992 bytes (`0x34000`).
  - GCC: `build/k3-b2/gcc/be-k3-b2.bin`, SHA-256
    `9c145f000067d36035a18cc27c53bbbf231d41cb2088a7765ed5742323a08c79`.
  - Clang: `build/k3-b2/clang/be-k3-b2.bin`, SHA-256
    `47be17e39350b468b528d09bd37ed8897b2eeaae575363cc7dff0252c16c54fe`.
  - Commit `d834aeb7` generated and built both from the accepted R5 sources
    (`165f4d00`) through `bringup/k3-b2/scripts/port.py`.
  - `make -C bringup/k3-b2 image` reproduces both.
- **Tooling:** the commit `d834aeb7` tooling, run unmodified. Every board
  step came after that commit.
- **Board:**
  - Fedora `7.1.5-201.0.riscv64.omni.fc44` on the COM260, with OpenSBI 1.6
    (SBI 2.0).
  - Reached as `fedora@k3e` over a direct Ethernet link at the Linux
    Plumbers Conference venue.
- **Serial:** the operator's `picocom -g` log of `/dev/ttyUSB0` at 115200
  8N1, followed read-only with `K3_SERIAL_LOG`.

## Sequence (UTC)

| Step | Time | Record |
| --- | --- | --- |
| Read-only preflight | 11:35:29 | `preflight.txt` |
| Load check, GCC: raw load at `0x1_0200_0000`, FDT at `0x1_0210_0000`, verify, unload; no kexec | 11:35:37 | `load-check/20261006T113537Z/` |
| Load check, Clang | 11:35:50 | `load-check/20261006T113550Z/` |
| Run 1, GCC (boot `cabaf3c9`) | 11:36:05 | `20261006T113605Z/` |
| Human reset; Fedora autoboot | | |
| Run 2, GCC (boot `915986fd`) | 11:57:00 | `20261006T115700Z/` |
| Human reset; Fedora autoboot | | |
| Run 3, GCC (boot `9da563a7`) | 12:05:30 | `20261006T120530Z/` |
| Human reset; Fedora autoboot | | |
| Run 4, Clang (boot `c5d5df0e`) | 12:06:57 | `20261006T120657Z/` |

Runs 2-4 were started by `bringup/k3-b0/scripts/k3-campaign.sh`, which
only waits for Fedora to answer SSH with a new boot ID after each human
reset. Every run printed all 22 accepted R3/R4/R5 markers in order;
`k3-run.sh` observed the terminal marker 8 to 11 seconds after each kexec
request. After `BE_R5:12 SHUTDOWN type=0 reason=0`, OpenSBI halted the
board without powering it off, and no `BE_R5:SRST_RETURNED` followed.

## Files

Run records, under `<run>/`:

| File | Content |
| --- | --- |
| `run.txt` | Run metadata: image and on-board hashes, boot ID, kernel, lockdown, loader line, kexec timing, outcome |
| `load.txt` | `kexec-load.py raw` probe and load output |
| `check.txt`, `result.json` | `bringup/k3-b2/tests/check-b2-markers.py` output for the full capture, checked against `--base 0x102000000` |
| `handoff-excerpt.log` | The capture from Linux's kexec handoff through the last B2 marker |

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

The excerpts pass the B2 marker checker on their own:

```sh
for run in bringup/k3-b2/results/20261006-com260/2026*/; do
    python3 bringup/k3-b2/tests/check-b2-markers.py \
        "$run/handoff-excerpt.log" --base 0x102000000
done
(cd bringup/k3-b2/results/20261006-com260 && sha256sum -c MANIFEST.sha256)
```

This is diagnostic bring-up evidence for one board, one firmware build, and
one Linux handoff path. It is not formal verification, hardware
qualification, or a transfer of the accepted QEMU R3/R4/R5 claims.
