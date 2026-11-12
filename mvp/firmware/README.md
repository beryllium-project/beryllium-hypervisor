<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M11 firmware base

This directory pins and builds the unmodified upstream OpenSBI source that
M11 uses as its firmware base. It is an unreleased development commit,
`ed70256dd22c09962d146e433834239825ef0616`, pinned with its Git tree in
`pins.mk`. The external source stays under `build/` and is never committed.

Build and check the default `generic` platform's `fw_dynamic.bin` with:

```sh
./mvp/mvp firmware
./mvp/mvp firmware FIRMWARE_GIT=/absolute/path/to/opensbi-mirror
```

The fetch checks the commit, tree, and clean checkout. The build uses the
tool lock's RISC-V GCC, archiver, linker, objcopy, DTC, Python, Make, shell,
and Git, with build information disabled and OpenSBI's reproducible mode
enabled. The `firmware` target checks the result against
`MVP_PIN_FIRMWARE_BIN_SHA256` in `mvp/tools/lock/tool-lock.conf`. The clean
evaluator receives the source through a read-only offline mount, rebuilds
it, and compares the binary with the host's through `images.sha256`.

Nothing boots this firmware yet. Existing runs continue to use the separately
pinned OpenSBI v1.6 binary. Patches, the M11 boundary extension, a reduced
configuration, and the switch of any image or run to this base belong to
later M11 work.
