<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The model evaluator's packages at the release's step 4

`./be evaluate`, the seventh of the gates the release path's step 4 ran
(`RELEASE.md`, "Gate results (step 4)"), builds its rootless image by
installing the model's tools from Fedora's repositories by package name,
so a later build of the image may hold later builds of those packages
(`README.md`, "Known limitations of this release"). This record keeps
what the image held when the gate passed, from a clean local clone of
this repository at commit `d6f96ddd56533853f52f201536d9ab04897433d9` on
2026-11-08:

- `rootless-image.txt`: the image's ID and digest, as the gate's
  evidence wrote them (`podman image inspect`'s `{{.Id}} {{.Digest}}`);
- `rpms.txt`: the image's 846 packages, one
  `NAME-EPOCH:VERSION-RELEASE.ARCH` per line, sorted, read with
  `rpm -qa` from that image after the gates ended, with no network.

This is a record, not a pin: no later build of the image is checked
against it.
