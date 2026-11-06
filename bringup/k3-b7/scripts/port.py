#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Generate the K3 B7 port from the accepted B2 port.

  port.py ROOT B2_PORT OUT           derive the B7 port into OUT
  port.py --check ROOT B2_PORT OUT   re-derive and require OUT to match exactly
  port.py --inputs                   print the ported paths (B2's)

B7 (planning/k3-b7-plan.md, "Port and copies") reuses B2's K3 port of
accepted R5 (B2 accepted at 898af4e0) unchanged except for the same five
counted rules and seven substitutions as B6's port (bringup/k3-b6/scripts/
port.py), with B7 names and the pool grown to two B6-shaped pools. This
script first runs B2's unchanged bringup/k3-b2/scripts/port.py --check on
B2_PORT, so B2_PORT must be B2's byte-identical re-derivation from the
pinned accepted inputs, and requires B2's PORT-MANIFEST.txt to match its
pinned SHA-256. It then copies every file B2's manifest lists from B2_PORT
to OUT and applies only these rules, each with an exact count:

- r5-entry.S: `call be_r5_runtime_main` becomes `call be_b7_runtime_main`
  (1) and `tail be_r5_arch_halt` becomes `tail be_r3_arch_halt` (1);
- r5-beryllium.lds: `be_r5_trap_vector` becomes `be_b7_trap_vector` (3);
  PHDRS gains a `b7_pool` PT_LOAD entry after `guest_protected` (1 block);
  and a NOLOAD `.gstage.root.b7` section at 0x1_0203_4000 (64 KiB, 16 KiB
  aligned: G0's 32 KiB pool, then G1's) follows the protected guest page,
  with its ASSERTs, before the accepted ASSERTs (1 block).

Every other byte, including every other accepted ASSERT and the management
fixture in its page, is B2's. --check re-derives the tree and requires OUT
to hold exactly those bytes, the same manifest, and no other file.
"""

import hashlib
import pathlib
import subprocess
import sys

ACCEPTED_B2 = "898af4e02fd36744a93b0eef99bc159955409d25"
B2_PORT_SCRIPT = "bringup/k3-b2/scripts/port.py"
# SHA-256 of B2's PORT-MANIFEST.txt, derived by B2's accepted port.py from
# the pinned accepted R5 inputs (bringup/k3-b2/README.md).
B2_MANIFEST_SHA256 = \
    "7c43e75b2066c86e01813143d2200be98a81f7dbd8773fad6c7785029b467878"
B2_PORTED_FILES = 32
ENTRY = "arch/riscv/be/r5-entry.S"
LDS = "arch/riscv/be/r5-beryllium.lds"

PHDR_ANCHOR = "\tguest_protected PT_LOAD FLAGS(5);\n"
POOL_PHDR = PHDR_ANCHOR + "\tb7_pool PT_LOAD FLAGS(6);\n"
ASSERT_ANCHOR = "\tASSERT(be_reset == 0x102000000, \"R5 entry moved\")\n"
POOL_SECTION = (
    "\t/* K3 B7: the B7-owned G-stage pool, G0's 32 KiB pool then G1's,\n"
    "\t * each a 16 KiB root and one level-1 page, the rest zero; outside\n"
    "\t * every accepted extent. */\n"
    "\t. = 0x102034000;\n"
    "\t.gstage.root.b7 (NOLOAD) : ALIGN(0x4000)\n"
    "\t{\n"
    "\t\t__be_b7_pool_start = .; . += 0x10000;\n"
    "\t\t__be_b7_pool_end = .;\n"
    "\t} :b7_pool\n"
    "\n"
    "\tASSERT(__be_b7_pool_start == 0x102034000 &&\n"
    "\t       __be_b7_pool_end == 0x102044000, \"B7 G-stage pool moved\")\n"
    "\tASSERT((__be_b7_pool_start & 0x3fff) == 0,\n"
    "\t       \"B7 G-stage pool alignment\")\n"
    "\tASSERT(__be_guest_protected_end <= __be_b7_pool_start,\n"
    "\t       \"B7 G-stage pool overlaps the protected guest page\")\n"
    "\n")

# path -> [(rule, old, new, count)], applied in order to B2's ported text.
RULES = {
    ENTRY: [
        ("runtime", "\tcall\tbe_r5_runtime_main\n",
         "\tcall\tbe_b7_runtime_main\n", 1),
        ("halt", "\ttail\tbe_r5_arch_halt\n", "\ttail\tbe_r3_arch_halt\n", 1),
    ],
    LDS: [
        ("trap-vector", "be_r5_trap_vector", "be_b7_trap_vector", 3),
        ("pool-phdr", PHDR_ANCHOR, POOL_PHDR, 1),
        ("pool-section", ASSERT_ANCHOR, POOL_SECTION + ASSERT_ANCHOR, 1),
    ],
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def b2_listing(root, b2_port):
    """Check B2's port with B2's own script; return its manifest entries."""
    check = subprocess.run(
        [sys.executable, "-B", str(root / B2_PORT_SCRIPT), "--check",
         str(root), str(b2_port)],
        capture_output=True, text=True, check=False)
    if check.returncode != 0 or not check.stdout.startswith(
            "BE_B2_PORT: CHECK PASS "):
        raise ValueError("B2 port.py --check failed: "
                         f"{(check.stdout + check.stderr).strip()}")
    manifest = (b2_port / "PORT-MANIFEST.txt").read_bytes()
    if sha256(manifest) != B2_MANIFEST_SHA256:
        raise ValueError("B2 PORT-MANIFEST.txt differs from the pinned "
                         f"SHA-256 (sha256 {sha256(manifest)})")
    entries = []
    for line in manifest.decode("utf-8").splitlines():
        if line.startswith("#"):
            continue
        _, output_sha256, path = line.split(" ")
        entries.append((path, output_sha256))
    if len(entries) != B2_PORTED_FILES:
        raise ValueError(f"B2 manifest lists {len(entries)} files, "
                         f"expected {B2_PORTED_FILES}")
    return entries


def derive(root, b2_port):
    """Return [(path, B2 sha256, B7 text, report lines)] or raise."""
    entries = b2_listing(root, b2_port)
    paths = [path for path, _ in entries]
    unknown = sorted(set(RULES) - set(paths))
    if unknown:
        raise ValueError(f"rules for paths outside B2's port: {unknown}")
    ported = []
    for path, b2_sha256 in entries:
        data = (b2_port / path).read_bytes()
        if sha256(data) != b2_sha256:
            raise ValueError(f"{path}: B2 port file differs from its manifest")
        text = data.decode("utf-8")
        report = []
        for rule, old, new, count in RULES.get(path, []):
            found = text.count(old)
            if found != count:
                raise ValueError(f"{path}: rule {rule}: {old!r} found "
                                 f"{found} times, expected {count}")
            text = text.replace(old, new)
            report.append(f"rule {rule} x{count}")
        ported.append((path, b2_sha256, text, report))
    return ported


def main(argv):
    if len(argv) == 2 and argv[1] == "--inputs":
        # B7 ports exactly the files B2 ports, so B2's list is B7's.
        root = pathlib.Path(__file__).resolve().parents[3]
        return subprocess.run([sys.executable, "-B",
                               str(root / B2_PORT_SCRIPT), "--inputs"],
                              check=False).returncode
    check = len(argv) == 5 and argv[1] == "--check"
    if not check and len(argv) != 4:
        print(__doc__)
        return 2
    root, b2_port, out = (pathlib.Path(argument) for argument in argv[-3:])
    try:
        ported = derive(root.resolve(), b2_port.resolve())
    except (OSError, ValueError, UnicodeDecodeError) as error:
        print(f"BE_B7_PORT: FAIL {error}")
        return 1
    manifest = [f"# K3 B7 port of accepted B2 {ACCEPTED_B2} "
                f"(B2 manifest sha256 {B2_MANIFEST_SHA256})",
                "# b2-port-sha256 b7-port-sha256 path"]
    for path, b2_sha256, text, report in ported:
        target = out / path
        data = text.encode("utf-8")
        if check:
            if not target.is_file() or target.read_bytes() != data:
                print(f"BE_B7_PORT: FAIL {path} differs from a fresh "
                      "derivation")
                return 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest.append(f"{b2_sha256} {sha256(data)} {path}")
        for line in report:
            manifest.append(f"#   {path}: {line}")
    manifest_text = "\n".join(manifest) + "\n"
    manifest_path = out / "PORT-MANIFEST.txt"
    if check:
        expected = {out / path for path, _, _, _ in ported} | {manifest_path}
        present = {path for path in out.rglob("*") if path.is_file()}
        if present != expected:
            extra = sorted(str(path.relative_to(out))
                           for path in present ^ expected)
            print(f"BE_B7_PORT: FAIL unexpected or missing files: {extra}")
            return 1
        if manifest_path.read_text() != manifest_text:
            print("BE_B7_PORT: FAIL manifest differs")
            return 1
    else:
        manifest_path.write_text(manifest_text)
    rules = sum(len(RULES[path]) for path in RULES)
    applied = sum(count for path in RULES for _, _, _, count in RULES[path])
    changed = sum(1 for _, _, _, report in ported if report)
    print(f"BE_B7_PORT: {'CHECK ' if check else ''}PASS files={len(ported)} "
          f"changed={changed} rules={rules} substitutions={applied} "
          f"b2_manifest={B2_MANIFEST_SHA256[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
