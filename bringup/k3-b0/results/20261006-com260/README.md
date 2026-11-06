<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B0 COM260 results, 2026-10-06

These are the retained records of three RAM-only B0 runs on the SpacemiT K3
COM260, with the board's read-only preflight and non-disruptive load check
that preceded them. `summary.md` is the reproducibility table.

## Inputs

- **Image:** `build/k3-b0/be-k3-b0.bin`, 4,633 bytes, SHA-256
  `fc6e12daca1cd8381463b2b93341c93699ba4bb08e29295e6271a04c3e7d36d3`. It is
  built from the B0 sources added in `62060e2d`, unchanged since, and
  `make -C bringup/k3-b0 image` reproduces it.
- **Tooling:** commit `60488c16`. The runs used the working tree that this
  commit then recorded without modification; every tooling file predates
  run 1 by its modification time.
- **Board:** Fedora `7.1.5-201.0.riscv64.omni.fc44` on the COM260, with
  OpenSBI 1.6 (SBI 2.0), reached as `fedora@k3e` over a direct Ethernet
  link.
- **Serial:** the operator's `picocom -g` log of `/dev/ttyUSB0` at 115200
  8N1, followed read-only with `K3_SERIAL_LOG`.

## Sequence (UTC)

| Step | Time | Record |
| --- | --- | --- |
| Read-only preflight | 06:12:05 | `preflight.txt` |
| Load check: load, verify, unload; no kexec | 06:12:28 | `load-check/20261006T061228Z/` |
| Run 1 | 06:13:06 | `20261006T061306Z/` |
| Human reset; Fedora autoboot | | |
| Run 2 | 06:17:33 | `20261006T061733Z/` |
| Human reset; Fedora autoboot | | |
| Run 3 | 06:20:50 | `20261006T062050Z/` |

After each run's SRST shutdown request, the board stayed powered with no
further serial output until the human reset it. The operator reports that
Fedora's `poweroff` has not powered the board off in testing so far.

## Files

| File | Content |
| --- | --- |
| `<run>/run.txt` | Run metadata: image and on-board hashes, boot ID, kernel, lockdown, loader line, kexec timing, outcome |
| `<run>/load.txt` | `kexec-load.py auto` probe and load output |
| `<run>/check.txt`, `<run>/result.json` | `tests/check-markers.py` output for the full capture, with `--base` taken from the loader line |
| `<run>/handoff-excerpt.log` | The capture from Linux's kexec handoff through the last B0 marker |
| `captures.txt` | SHA-256, bytes, and lines of each full serial capture |
| `originals.sha256` | SHA-256 of the original files behind every retained copy |
| `MANIFEST.sha256` | SHA-256 of every other file in this directory |

## Transformations

- Absolute local paths are rewritten to `<repo>` or `<spacemit-k3>`.
- The root filesystem UUID in `preflight.txt` is redacted.
- Carriage returns are removed.
- The full serial captures stay out of the repository: they include systemd
  terminal metadata such as the board's machine ID. They are retained
  privately, and `captures.txt` and `originals.sha256` identify them.

The excerpts pass the marker checker on their own:

```sh
for run in bringup/k3-b0/results/20261006-com260/2026*/; do
    python3 bringup/k3-b0/tests/check-markers.py "$run/handoff-excerpt.log" \
        --expect pass --base 0x102000000 --hart 0
done
(cd bringup/k3-b0/results/20261006-com260 && sha256sum -c MANIFEST.sha256)
```

This is diagnostic bring-up evidence for one board, one firmware build, and
one Linux handoff path. It is not formal verification, a KVM0 or retained
R8 result, or hardware qualification.
