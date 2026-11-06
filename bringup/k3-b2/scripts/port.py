#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Generate the K3 port of the accepted R5 image sources.

  port.py ROOT OUT           derive the port from ROOT into OUT
  port.py --check ROOT OUT   re-derive and require OUT to match exactly
  port.py --identities       print the accepted and K3 R1 identities
  port.py --inputs           print the pinned input paths

The input is the source closure of the accepted R5 image (exact commit
165f4d001a2b59b582b397bdea79ec4826168fdb, which re-executes the accepted R3
boot-and-first-entry prelude and the accepted R4 management prelude before
its checked switch), plus the accepted R4 and R3 host checks of the r4.c and
r3.c mechanisms it re-executes. Every input must match its pinned SHA-256.
The port applies only the substitutions in RULES, as B1 did for R4:

- rebase every image-layout literal in [0x80200000, 0x80234000] by
  +0x81e00000, so the image moves from the QEMU virt kernel slot
  0x80200000 to the free K3 window at 0x1_0200_0000 with every 4 KiB and
  16 KiB alignment preserved. The accepted R5 linker script places the
  image exactly there (be_reset == 0x80200000 to __be_guest_protected_end
  == 0x80234000); every other QEMU address is handled by an exact rule;
- the two Sv39x4 HGATP values follow their roots (PPN 0x80214 -> 0x102014,
  0x8021c -> 0x10201c); R5 installs both, the protected one at its switch;
- the DRAM window and OpenSBI-reserved prefix become the COM260's
  [0x1_0000_0000, 0x3_0000_0000) and [0x1_0000_0000, 0x1_0200_0000);
- the pinned SBI specification version becomes 2.0, as reported by the K3
  OpenSBI 1.6 firmware;
- the pinned R1 sealed configuration identity becomes the one the accepted
  R1 pipeline derives from the ported profile (bringup/k3-b1/tests/
  b1-identity.c, which reproduces the accepted 0x771e1e75110201ac from the
  accepted profile); the profile and its port are B1's, so is the value;
- the opaque host-test firmware pointer 0x87e00000 is rebased like the image;
- be_reset first calls be_b1_quiesce (bringup/k3-b1/src/b1-handoff.S), which
  disarms the interrupt sources a K3 firmware or Linux kexec handoff can
  leave pending, then returns to the unchanged accepted entry sequence.

Each rule must apply exactly its expected number of times, and no 8-digit
literal in the QEMU RAM range 0x8xxxxxxx may remain in the output.
"""

import hashlib
import pathlib
import re
import sys

ACCEPTED_R5 = "165f4d001a2b59b582b397bdea79ec4826168fdb"
QEMU_IMAGE_BASE = 0x80200000
QEMU_IMAGE_LIMIT = 0x80234000
K3_DELTA = 0x81E00000
QEMU_LITERAL = re.compile(r"\b0[xX]8[0-9a-fA-F]{7}\b")
ACCEPTED_IDENTITY = "0x771e1e75110201ac"
K3_IDENTITY = "0xa3d0c0f96f0ea58b"

# SHA-256 of each input at the accepted R5 commit (git show 165f4d00:PATH).
PINS = {
    # Headers the image and the host checks include, transitively.
    "include/be/types.h": "9977f54f8dd0cfb119c9eedbb03105f53b9d1a6f249caa8ad94ea4b13754597c",
    "include/be/manifest.h": "0f2220138bd55406191c5675764f5ac5eeaa9f380619513bf20a7d979f881867",
    "include/be/state.h": "206a5e1df4abfab7177a7ee04b63c2f4747e379cc57ff617c144f37d9c9370a7",
    "include/be/r0-config.h": "7699d8e8adaa798182ce2bcd2be20c70c5c9b9497a4ed7eb347edb5d71b6f4c6",
    "include/be/r1-config.h": "c03e314add372476a62bbdfc1c82151451e67ba773873a5b8ab51b1ba2ce87e1",
    "include/be/r2.h": "348ec6ba84d978e06c0c2c1c0b9a78cabd90a16348e3e58878ffa635de932e07",
    "include/be/r3.h": "0dbb0fc012c22e5110c73d370792f1e0004e79f68f1d54c6e24e768f4f886e1c",
    "include/be/r4.h": "61265a300d734dd0066692f2e31adf92f4031222df785f7959dbab4adf6e906d",
    "include/be/r5.h": "9b914876a0b46a7130d138c6fba040fc2d52a94b7e7c00d9af3d8d1ab9fb4335",
    "arch/riscv/be/r0-layout.h": "763f9d1962aad04a3a618301fb94d03d385988aae1f2531ddba855d9df01cb20",
    # Declared in the accepted R5 HEADERS list; no compiled file includes it.
    "arch/riscv/be/r0-registers.h": "d14aeac138f8448efc778ec6050a142e1f68ac1bec0254ac533836e64f862b56",
    "arch/riscv/be/r0-sbi.h": "78cde4314883510d581b6ff29b3973ab7c118b478f2c6d3dd3608013e1981923",
    "arch/riscv/be/r3-platform.h": "57fadf4a1b9a250206536a4d1ec2751919e38b0ee5c5a33c6e9b5e7d65ca4064",
    "arch/riscv/be/r5-platform.h": "13eb208460ffd1913759aa2414a40b1da3898108648df743b773a35286e8b384",
    "arch/riscv/be/r5-beryllium.lds": "0df278b45d33500af08204b364a3f3e61178a7cd9981cb499025d95411baa56a",
    # Image C sources (tests/r5/Makefile C_SOURCES).
    "virt/be/manifest.c": "048c607f83f26382e4a251285524747e85b4ab6b89bb0980efb0706971b206a4",
    "virt/be/state.c": "2461d6c831714f56a2f103697cae5868d5d4b7b5138930546d4fca6790c4aac3",
    "virt/be/r1-config.c": "0bb22238c6e99fdf33f0263fbb17c309fb12be7cd8e59f1511af3a37a29d8cb1",
    "virt/be/r3.c": "1e2cf52ff21271f795599029a5fd4cdd35618b21ca8f574a2dd122d2cb628b3f",
    "virt/be/r4.c": "9d9e487d1e979afd27e8352e438642737773553564a1e8e2141785b09d70c76e",
    "virt/be/r5.c": "8e56daa4cd4f54c252e8e16431622ba29ebd3f2361a19fa4bb2c1e3b9e618d53",
    "arch/riscv/be/sv39x4.c": "89a57333b93cc94d4554e99036891acf7d56881a87d43bab19c5302e7692ea08",
    "arch/riscv/be/platform.c": "e5c0242b7edc4eaa08fd61e39dfa251ce57bd85e5491f069c0d77e6e662c04aa",
    "arch/riscv/be/freestanding.c": "afbfa0efa8ecc12ef2470d17eb83c0c751d51bbed0f0c9f83958e4398d65e6b7",
    "arch/riscv/be/r5-runtime.c": "a221ce8ebb77e3feaa9d7799e3eb296fb8cd7aa9190e20f1970d7e9c95bcc6e4",
    # Image assembly sources (tests/r5/Makefile ASM_SOURCES).
    "arch/riscv/be/privileged.S": "a0c329c2f4cb7274f601b97ee0c96fbd6456eb5930810936a2e92a32d38883ea",
    "arch/riscv/be/r5-trap.S": "4721da5693b3bde3e91ca1dc36aa8042693d858f198ef06986881171f1216841",
    "arch/riscv/be/r5-guest.S": "cd1a0d719418b4a5b07b7fcace5b432be210a425ea4f7bfa8dff6f89d2cc764b",
    "arch/riscv/be/r5-entry.S": "a19068bbe1be5bd79e8942019f71ac7d6d470929e7193c6bb90774220debf0b4",
    # The accepted R5 host check, then the accepted R4 and R3 host checks of
    # the in-image r4.c and r3.c mechanisms (unchanged since accepted R4).
    "tests/r5/r5-check.c": "1c4460a04da999c91ca1c4fd5d4ae87dcd79e2a6c5a9399a7c1a0109e6708262",
    "tests/r4/r4-check.c": "8a46b8e315d0d7c32729e1d2d879ebcb51a2f0b5d94b188a39b7102ae4ad5e06",
    "tests/r3/r3-check.c": "6c590678f102b343728997a95f9e37be85a87a7445560a1be2be82e6d48609fc",
}

FIRMWARE_POINTER = ("BE_U64_C(0x87e00000)", "BE_U64_C(0x109c00000)", 1)

# path -> (exact substitutions [(old, new, count)], expected rebase count)
RULES = {
    "include/be/r0-config.h": ([
        ("OpenSBI-reserved region [0x80000000, 0x80200000).",
         "OpenSBI-reserved region [0x100000000, 0x102000000).", 1),
    ], 11),
    "arch/riscv/be/r0-layout.h": ([
        ("/* Fixed QEMU virt DRAM window for -m 128M and the OpenSBI-reserved prefix. */",
         "/* K3 COM260 DRAM window (8 GiB) and the OpenSBI-reserved prefix. */", 1),
        ("#define BE_R0_DRAM_BASE\t\t\tBE_U64_C(0x80000000)",
         "#define BE_R0_DRAM_BASE\t\t\tBE_U64_C(0x100000000)", 1),
        ("#define BE_R0_DRAM_END\t\t\tBE_U64_C(0x88000000)",
         "#define BE_R0_DRAM_END\t\t\tBE_U64_C(0x300000000)", 1),
        ("#define BE_R0_OPENSBI_RESERVED_BASE\tBE_U64_C(0x80000000)",
         "#define BE_R0_OPENSBI_RESERVED_BASE\tBE_U64_C(0x100000000)", 1),
        ("BE_R0_OPENSBI_RESERVED_BASE,\n\t  BE_U64_C(0x200000), BE_R0_CLASS_OPENSBI",
         "BE_R0_OPENSBI_RESERVED_BASE,\n\t  BE_U64_C(0x2000000), BE_R0_CLASS_OPENSBI", 1),
    ], 10),
    "include/be/r3.h": ([
        ("/** @BE_R3_OPENSBI_SPEC_VERSION: pinned firmware SBI specification version 3.0 */",
         "/** @BE_R3_OPENSBI_SPEC_VERSION: pinned firmware SBI specification version 2.0 */", 1),
        ("#define BE_R3_OPENSBI_SPEC_VERSION\tBE_U64_C(0x03000000)",
         "#define BE_R3_OPENSBI_SPEC_VERSION\tBE_U64_C(0x02000000)", 1),
        ("BE_U64_C(0x8000000000080214)", "BE_U64_C(0x8000000000102014)", 1),
        ("BE_U64_C(0x800000000008021c)", "BE_U64_C(0x800000000010201c)", 1),
        (f"BE_U64_C({ACCEPTED_IDENTITY})", f"BE_U64_C({K3_IDENTITY})", 1),
    ], 4),
    "include/be/r5.h": ([], 2),
    "virt/be/r3.c": ([], 13),
    "arch/riscv/be/sv39x4.c": ([], 2),
    "arch/riscv/be/r5-beryllium.lds": ([], 41),
    "arch/riscv/be/r5-entry.S": ([
        ("be_reset:\n\t/* Preserve OpenSBI a0/a1",
         "be_reset:\n\t/* K3 port (B2): disarm handoff interrupt sources first. */\n"
         "\tcall\tbe_b1_quiesce\n\t/* Preserve OpenSBI a0/a1", 1),
    ], 0),
    "tests/r5/r5-check.c": ([FIRMWARE_POINTER], 0),
    "tests/r4/r4-check.c": ([FIRMWARE_POINTER], 0),
    "tests/r3/r3-check.c": ([FIRMWARE_POINTER], 32),
}


def rebase(text):
    count = 0

    def substitute(match):
        nonlocal count
        value = int(match.group(0), 16)
        if not QEMU_IMAGE_BASE <= value <= QEMU_IMAGE_LIMIT:
            return match.group(0)
        count += 1
        return f"0x{value + K3_DELTA:x}"

    return QEMU_LITERAL.sub(substitute, text), count


def derive(root):
    """Return {path: (ported text, report lines)} or raise ValueError."""
    unknown = sorted(set(RULES) - set(PINS))
    if unknown:
        raise ValueError(f"rules for unpinned inputs: {unknown}")
    ported = {}
    for path, pin in PINS.items():
        data = (root / path).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != pin:
            raise ValueError(f"{path}: input differs from accepted R5 "
                             f"{ACCEPTED_R5[:12]} (sha256 {digest})")
        text = data.decode("utf-8")
        report = []
        exact, expected_rebase = RULES.get(path, ([], 0))
        for old, new, count in exact:
            found = text.count(old)
            if found != count:
                raise ValueError(f"{path}: {old!r} found {found} times, "
                                 f"expected {count}")
            text = text.replace(old, new)
            report.append(f"exact x{count}: {old!r} -> {new!r}")
        text, rebased = rebase(text)
        if rebased != expected_rebase:
            raise ValueError(f"{path}: rebased {rebased} literals, "
                             f"expected {expected_rebase}")
        if rebased:
            report.append(f"rebase x{rebased}: +0x{K3_DELTA:x}")
        left = QEMU_LITERAL.findall(text)
        if left:
            raise ValueError(f"{path}: QEMU RAM literals remain: {left}")
        ported[path] = (text, report)
    return ported


def main(argv):
    if len(argv) == 2 and argv[1] == "--identities":
        print(ACCEPTED_IDENTITY, K3_IDENTITY)
        return 0
    if len(argv) == 2 and argv[1] == "--inputs":
        print(" ".join(PINS))
        return 0
    check = len(argv) == 4 and argv[1] == "--check"
    if not check and len(argv) != 3:
        print(__doc__)
        return 2
    root, out = pathlib.Path(argv[-2]), pathlib.Path(argv[-1])
    try:
        ported = derive(root)
    except (OSError, ValueError) as error:
        print(f"BE_B2_PORT: FAIL {error}")
        return 1
    manifest = [f"# K3 port of accepted R5 {ACCEPTED_R5}",
                "# input-sha256 output-sha256 path"]
    for path, (text, report) in ported.items():
        target = out / path
        data = text.encode("utf-8")
        if check:
            if not target.is_file() or target.read_bytes() != data:
                print(f"BE_B2_PORT: FAIL {path} differs from a fresh derivation")
                return 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest.append(f"{PINS[path]} {hashlib.sha256(data).hexdigest()} {path}")
        for line in report:
            manifest.append(f"#   {path}: {line}")
    manifest_text = "\n".join(manifest) + "\n"
    manifest_path = out / "PORT-MANIFEST.txt"
    if check:
        expected_files = {out / path for path in ported} | {manifest_path}
        present = {path for path in out.rglob("*") if path.is_file()}
        if present != expected_files:
            extra = sorted(str(path.relative_to(out))
                           for path in present - expected_files)
            print(f"BE_B2_PORT: FAIL unexpected files in the port: {extra}")
            return 1
        if manifest_path.read_text() != manifest_text:
            print("BE_B2_PORT: FAIL manifest differs")
            return 1
    else:
        manifest_path.write_text(manifest_text)
    changed = sum(1 for _, report in ported.values() if report)
    print(f"BE_B2_PORT: {'CHECK ' if check else ''}PASS files={len(ported)} "
          f"changed={changed} accepted_r5={ACCEPTED_R5[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
