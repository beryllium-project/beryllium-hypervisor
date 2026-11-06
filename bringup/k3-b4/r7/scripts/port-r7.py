#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Generate the K3 (B4) copy of the accepted R7 bounded exact-byte proof.

  port-r7.py ROOT OUT            derive the copy from ROOT into OUT
  port-r7.py --check ROOT OUT    re-derive and require OUT to match exactly
  port-r7.py --verify-git ROOT   require every pin to equal `git show
                                 COMMIT:PATH` at its accepted commit
  port-r7.py --inventory ROOT DIR  require DIR/*.v to carry exactly the
                                 accepted R7 Theorem and Lemma inventory
  port-r7.py --scan DIR          refuse a forbidden declaration in DIR/*.v
  port-r7.py --assumptions LOG   require a closed Print Assumptions in LOG
  port-r7.py --provenance r1|r2 ROOT
                                 print the R1 or R2 provenance keys the trace
                                 needs, from git history and the port pins
  port-r7.py --shellcheck ROOT OUT
                                 require the copied check-disassembly.sh to
                                 keep exactly its inherited shellcheck finding
  port-r7.py --self-test ROOT    require every guard to refuse its case
  port-r7.py --inputs            print the pinned input paths
  port-r7.py --table             print the substitution table

The input is the accepted R7 package (exact commit 9bf22913) that the K3
proof needs: the direct ELF extractor, the independent objdump cross-check,
the exact-input generator, the configuration-trace generator and checker,
and the seven maintained proof modules, plus the accepted R1 and R2 report
generators and checkers that produce the configuration facts. Every input
is read from its accepted commit with `git show COMMIT:PATH`, never from the
working tree, and must match its SHA-256 pin. Only the two tool locks that
the copies read at run time (READ_IN_PLACE) are checked where they live.

The copy lives four directories deeper than the accepted tree
(build/k3-b4/r7/port/tests/r7 instead of tests/r7), reads B2's K3 images
(build/k3-b2/{gcc,clang}/be-k3-b2.elf) instead of the accepted R5 QEMU
images, and writes only under build/k3-b4/r7. Each change is a rule in
RULES that must apply exactly its expected number of times, with its reason.
Changes to the proof modules are restricted to literals: after every numeric
and digest literal is masked, each ported module must equal its accepted
module, and the Theorem and Lemma inventory must be unchanged. No residual
literal of the accepted QEMU image range [0x80200000, 0x80234000] may remain
in a ported proof module or R1/R2 tool. The one line of the accepted
check-disassembly.sh that shellcheck flags (SC1007, `CDPATH= cd`) may change
only by the counted repository-root rule.
"""

import hashlib
import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys

ACCEPTED_R7 = "9bf22913d67e9b72286813cd5f7993a9ad3857a8"
ACCEPTED_R1 = "a6e0bb178c10a7e68c9447a8e58affb94b8ecadb"
ACCEPTED_R2 = "6e1cb579257c5dbe3234bd484fd091629e87181b"

# B2's rebase (bringup/k3-b2/scripts/port.py): the accepted R5 image spans
# exactly [0x80200000, 0x80234000] and moves to 0x1_0200_0000.
QEMU_IMAGE_BASE = 0x80200000
QEMU_IMAGE_LIMIT = 0x80234000
K3_DELTA = 0x81E00000
# The eleven scoped symbols move 16 bytes further: be_reset (outside the
# scope) grows by the 8-byte call to be_b1_quiesce, which the 16-byte
# function alignment that follows it rounds up to 0x10.
K3_SCOPED_DELTA = K3_DELTA + 0x10

PROOF_MODULES = ["ISA", "Exact", "Entry", "Trap", "Switch", "Configuration",
                 "Claims"]

# path -> (accepted commit, SHA-256 of `git show COMMIT:PATH`)
PINS = {
    "tests/r7/extract-exact-image.mjs": (
        ACCEPTED_R7,
        "f4483e15f4d2d6fa2964f2464bee29619565835f442f26219c9072299b044982"),
    "tests/r7/check-disassembly.sh": (
        ACCEPTED_R7,
        "152bf05f02162f15bf038ab75c512f2b38a3ac91a0bcfd3e18e50d575684d034"),
    "tests/r7/generate-exact-input.mjs": (
        ACCEPTED_R7,
        "65b9c11ec0fd4f65144965d86f329c56e6a33491f23267d8f87428d9bedeb72f"),
    "tests/r7/check-configuration-trace.mjs": (
        ACCEPTED_R7,
        "0b12f57cbcc4428010a7f6f596b7b168e8d4b1fe55d5b19de18cb06127938cc8"),
    "tests/r7/proof/ISA.v": (
        ACCEPTED_R7,
        "d38f6e68569fe8282de7dc6750cea6481ff47f4f8d693ce3ac8baf4956ea26ca"),
    "tests/r7/proof/Exact.v": (
        ACCEPTED_R7,
        "7c5833bf7f0d0dab1b286785b7b86c8b4aa2b334b328c322f378b980f1e53aac"),
    "tests/r7/proof/Entry.v": (
        ACCEPTED_R7,
        "20ac52854865bb520bc7191fa2c8936f0c5a62ed81eada94d6cce3793e9a4a10"),
    "tests/r7/proof/Trap.v": (
        ACCEPTED_R7,
        "41eb4492d3fd62831d6d63f4076f2584254a73904c4f5bb9a76042a6707f7aea"),
    "tests/r7/proof/Switch.v": (
        ACCEPTED_R7,
        "65246fd91c0617697011b812bb1cfb26105c5a8346cbcdf6d1e63b0f5764655f"),
    "tests/r7/proof/Configuration.v": (
        ACCEPTED_R7,
        "63b89ad99466584b7a8f777d6d5bafbadc87a775a1eec66b78f9d5b986f4476f"),
    "tests/r7/proof/Claims.v": (
        ACCEPTED_R7,
        "374473af6bf5eda197915862514eb9e1a59edc4e45c4f6e4abbd3e3755305dbe"),
    "tests/r1/r1-report.c": (
        ACCEPTED_R1,
        "3b6202902b7bda7a360cc54df27f3fff0369a4a5bf7642bf90b02d4a811bd420"),
    "tests/r1/check-report.mjs": (
        ACCEPTED_R1,
        "51c02c4a6206e86ed3307d01f06bddf6bd1642a488d42025b01f329879a00548"),
    "tests/r2/r2-report.c": (
        ACCEPTED_R2,
        "86850b3548bff15013b8a8a8a0741b713e424d590d037e6fbcf9ef470810f7b6"),
    "tests/r2/check-report.mjs": (
        ACCEPTED_R2,
        "366976a9fd823b0bfdb7bc43e34753b4c7107de1dc6e6b6d309feb860303f549"),
}

# Read in place by the copies (tool bindings), never copied or changed.
READ_IN_PLACE = {
    "tests/r7/tool-lock.conf": (
        ACCEPTED_R7,
        "0e374b4b713413beabae3aa675c87de7beef306c8a7f3d0db12c2994bafaa1db"),
    "tests/r3/tool-lock.conf": (
        ACCEPTED_R7,
        "c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b"),
}

# R1 and R2 provenance for the K3 configuration facts, without running the
# accepted acceptance interfaces (they also pin the root Makefile, which the
# facts do not depend on). For each stage: the accepted commit, the accepted
# interface read for the commit and date it records, the R1/R2 mechanism
# inputs the facts consume through B2's port, and the report tools B4 copies.
B2_PORT_SCRIPT = "bringup/k3-b2/scripts/port.py"
B2_PORT_DIR = "build/k3-b2/port"
B4_PORT_DIR = "build/k3-b4/r7/port"
PROVENANCE = {
    "r1": (ACCEPTED_R1, "tests/r1/check-acceptance.sh", [
        "include/be/types.h", "include/be/manifest.h", "include/be/state.h",
        "include/be/r0-config.h", "include/be/r1-config.h",
        "arch/riscv/be/r0-layout.h", "virt/be/manifest.c",
        "virt/be/state.c", "virt/be/r1-config.c",
    ], ["tests/r1/r1-report.c", "tests/r1/check-report.mjs"]),
    "r2": (ACCEPTED_R2, "tests/r2/check-acceptance.sh", [
        "include/be/r2.h", "arch/riscv/be/sv39x4.c",
    ], ["tests/r2/r2-report.c", "tests/r2/check-report.mjs"]),
}

# The accepted check-disassembly.sh carries one shellcheck finding, SC1007 on
# its `CDPATH= cd` line (line 22, column 15). The copy must keep it exactly:
# that line may change only by the repository-root rule, and shellcheck must
# report the same findings for the copy as for the accepted file.
DISASSEMBLY_PATH = "tests/r7/check-disassembly.sh"
SC1007_LINE = 22
SC1007_MARK = "CDPATH= cd --"

# The accepted R7 inventory: 135 Theorem and 4 Lemma declarations.
ACCEPTED_THEOREMS = 135
ACCEPTED_LEMMAS = 4

WHY_ROOT = ("the copy lives four directories deeper than tests/r7, so the "
            "repository root is six levels up")
WHY_OUT = ("every generated output goes under build/k3-b4/r7, never into "
           "the accepted build/r7")
WHY_ELF = "the inputs are B2's K3 images, not the accepted R5 QEMU images"


def exact(old, new, count, why):
    return ("exact", old, new, count, why)


def rebase(kind, count, why):
    return (kind, None, None, count, why)


# ------------------------------------------------------------- scripts
EXTRACTOR = [
    exact("export const root = resolve(here, '../..')",
          "export const root = resolve(here, '../../../../../..')", 1,
          WHY_ROOT),
    exact("'build/r5/gcc/beryllium.elf'", "'build/k3-b2/gcc/be-k3-b2.elf'",
          1, WHY_ELF),
    exact("'build/r5/clang/beryllium.elf'",
          "'build/k3-b2/clang/be-k3-b2.elf'", 1, WHY_ELF),
    exact("const hex = (value, digits) => "
          "`0x${(value >>> 0).toString(16).padStart(digits, '0')}`",
          "// K3 (B4): the accepted formatter goes through `>>> 0`, which is\n"
          "// exact only below 2^32, and B2's K3 image is linked at\n"
          "// 0x1_0200_0000. This form prints every value below 2^32\n"
          "// exactly as the accepted one does, prints the K3 addresses\n"
          "// exactly, and refuses anything that is not a non-negative safe\n"
          "// integer instead of wrapping it.\n"
          "const hex = (value, digits) => {\n"
          "  if (!Number.isSafeInteger(value) || value < 0)\n"
          "    throw new Error(`value ${value} is not a non-negative safe "
          "integer`)\n"
          "  return `0x${value.toString(16).padStart(digits, '0')}`\n"
          "}", 1,
          "the accepted 32-bit formatter would truncate every K3 address "
          "(0x102006aa0 prints as 0x02006aa0); both the objdump cross-check "
          "and the Rocq entry pin refuse the truncated form"),
    exact("build/r7", "build/k3-b4/r7", 4, WHY_OUT),
]

DISASSEMBLY = [
    exact('root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)',
          'root=$(CDPATH= cd -- "$(dirname "$0")/../../../../../.." '
          '&& pwd -P)', 1, WHY_ROOT),
    exact("actual=$(/usr/bin/sha256sum \"$resolved\" | /usr/bin/cut -d' ' "
          "-f1)\n"
          "[ \"$actual\" = \"$objdump_sha256\" ] || {\n"
          "\tprintf 'R7 disassembly check rejects objdump executable digest "
          "drift\\n' >&2\n"
          "\texit 1\n"
          "}\n",
          "# K3 (B4): the accepted R3 lock pins the digest of GNU objdump\n"
          "# 2.46-1.fc44; this host has binutils 2.46.1-1.fc44. As in B2, the\n"
          "# lock's absolute command and resolved path still bind the tool,\n"
          "# but its digest is recorded by the B4 report, not required.\n",
          1, "this host's objdump is binutils 2.46.1, not the locked 2.46"),
    exact("actual=$(/usr/bin/sha256sum \"$resolved_node\" | /usr/bin/cut "
          "-d' ' -f1)\n"
          "[ \"$actual\" = \"$node_sha256\" ] || {\n"
          "\tprintf 'R7 disassembly check rejects node executable digest "
          "drift\\n' >&2\n"
          "\texit 1\n"
          "}\n",
          "# K3 (B4): likewise the locked node v22.22.2 digest; this host has\n"
          "# node v22.23.1, bound by the lock's command and resolved path.\n",
          1, "this host's node is v22.23.1, not the locked v22.22.2"),
    exact("build/r5/{gcc,clang}/beryllium.elf",
          "build/k3-b2/{gcc,clang}/be-k3-b2.elf", 1, WHY_ELF),
    exact("build/r5/$toolchain/beryllium.elf",
          "build/k3-b2/$toolchain/be-k3-b2.elf", 1, WHY_ELF),
    exact("build/r5/gcc/beryllium.elf", "build/k3-b2/gcc/be-k3-b2.elf", 1,
          WHY_ELF),
    exact("build/r5/clang/beryllium.elf", "build/k3-b2/clang/be-k3-b2.elf",
          1, WHY_ELF),
    exact("build/r7", "build/k3-b4/r7", 15, WHY_OUT),
]

GENERATOR = [
    exact("  '   Generated by tests/r7/generate-exact-input.mjs. Data only: "
          "this module',\n"
          "  '   asserts no instruction semantics and no proof claim of its "
          "own. It is',\n"
          "  '   the exact, twice-reproducible byte/address/target record "
          "extracted',\n"
          "  '   directly from the accepted R5 GCC and Clang RISC-V ELF64 "
          "images and',\n"
          "  '   independently cross-checked against locked GNU objdump by',\n"
          "  '   tests/r7/check-disassembly.sh. Do not hand-edit: regenerate "
          "with',\n"
          "  '   tests/r7/generate-exact-input.mjs.',\n",
          "  '   Generated by the K3 (B4) copy of tests/r7/"
          "generate-exact-input.mjs.',\n"
          "  '   Data only: this module asserts no instruction semantics and "
          "no proof',\n"
          "  '   claim of its own. It is the exact, twice-reproducible byte/"
          "address/',\n"
          "  '   target record extracted directly from the B2 K3 GCC and "
          "Clang RISC-V',\n"
          "  '   ELF64 images (bringup/k3-b2, accepted at 898af4e0) and "
          "independently',\n"
          "  '   cross-checked against GNU objdump by the B4 copy of',\n"
          "  '   tests/r7/check-disassembly.sh. Do not hand-edit.',\n",
          1, "the generated data names its real K3 source"),
    exact("build/r7", "build/k3-b4/r7", 4, WHY_OUT),
]

TRACE = [
    exact("const ROOT = resolve(dirname(SELF_PATH), '..', '..')",
          "const ROOT = resolve(dirname(SELF_PATH), '..', '..', '..', '..', "
          "'..', '..')", 1, WHY_ROOT),
    exact("const R1_MAKE_DIR = 'tests'\n",
          "const R1_MAKE_DIR = 'bringup/k3-b4/r7'\n", 1,
          "the K3 R1 report is built by the B4 Makefile from B2's port"),
    exact("const R1_REPORT_REL = 'build/r1/reports/runtime.json'",
          "const R1_REPORT_REL = 'build/k3-b4/r7/r1/reports/runtime.json'",
          1, WHY_OUT),
    exact("const R1_CHECKER_REL = 'tests/r1/check-report.mjs'",
          "const R1_CHECKER_REL = 'build/k3-b4/r7/port/tests/r1/"
          "check-report.mjs'", 1, "the K3 copy of the accepted R1 checker"),
    exact("const R2_MAKE_DIR = 'tests/r2'",
          "const R2_MAKE_DIR = 'bringup/k3-b4/r7'", 1,
          "the K3 R2 report is built by the B4 Makefile from B2's port"),
    exact("const R2_REPORT_REL = 'build/r2/reports/sv39x4.json'",
          "const R2_REPORT_REL = 'build/k3-b4/r7/r2/reports/sv39x4.json'",
          1, WHY_OUT),
    exact("const R2_CHECKER_REL = 'tests/r2/check-report.mjs'",
          "const R2_CHECKER_REL = 'build/k3-b4/r7/port/tests/r2/"
          "check-report.mjs'", 1, "the K3 copy of the accepted R2 checker"),
    exact("const R5_REPORT_REL = 'build/r5/reports/checked-switch.json'\n"
          "const R5_CHECKER_REL = 'tests/r5/check-report.mjs'\n"
          "const R5_ACCEPTANCE_REL = 'tests/r5/check-acceptance.sh'\n"
          "const R5_CWD_REL = 'tests/r5'\n",
          "// K3 (B4): B2's port manifest stands where the accepted R5 QEMU\n"
          "// report stood, B2's port script is its checker, and the accepted\n"
          "// R5 acceptance interface is read for its accepted commit and "
          "date,\n"
          "// never run.\n"
          "const R5_REPORT_REL = 'build/k3-b2/port/PORT-MANIFEST.txt'\n"
          "const R5_CHECKER_REL = 'bringup/k3-b2/scripts/port.py'\n"
          "const R5_ACCEPTANCE_REL = 'tests/r5/check-acceptance.sh'\n"
          "const R5_CWD_REL = 'build/k3-b2/port'\n"
          "const PYTHON_BIN = '/usr/bin/python3'\n"
          "const B4_PORT_SCRIPT_REL = "
          "'bringup/k3-b4/r7/scripts/port-r7.py'\n", 1,
          "the K3 images are B2's counted port of the accepted R5 inputs, "
          "not the accepted R5 QEMU images"),
    exact("// addition to the git-level drift rejection already performed by "
          "each\n"
          "// stage's own check-acceptance.sh. Hashing these here protects "
          "the\n"
          "// integrity of the *generated trace artifact* itself (catches a "
          "hand-edited\n"
          "// or stale configuration-trace.json even when the working tree "
          "still\n"
          "// matches its accepted commit exactly).\n"
          "const PINNED_SOURCE_FILES = [\n"
          "  'planning/single-hart-runtime-r7-plan.md',\n"
          "  'include/be/manifest.h',\n"
          "  'include/be/state.h',\n"
          "  'include/be/r2.h',\n"
          "  'virt/be/r1-config.c',\n"
          "  'arch/riscv/be/sv39x4.c',\n"
          "  'tests/r1/r1-report.c',\n"
          "  'tests/r2/r2-report.c',\n"
          "  'tests/r1/check-report.mjs',\n"
          "  'tests/r2/check-report.mjs',\n"
          "  'tests/r5/check-report.mjs'\n"
          "]\n",
          "// addition to the git-level drift rejection already performed by "
          "the\n"
          "// K3 provenance checks (port-r7.py --provenance for R1/R2, B2's "
          "port\n"
          "// check for R5). Hashing these here protects the integrity of "
          "the\n"
          "// *generated trace artifact* itself (catches a hand-edited or "
          "stale\n"
          "// configuration-trace.json even when every input still matches "
          "its\n"
          "// accepted bytes exactly).\n"
          "const PINNED_SOURCE_FILES = [\n"
          "  'planning/single-hart-runtime-r7-plan.md',\n"
          "  'build/k3-b2/port/include/be/manifest.h',\n"
          "  'build/k3-b2/port/include/be/state.h',\n"
          "  'build/k3-b2/port/include/be/r2.h',\n"
          "  'build/k3-b2/port/virt/be/r1-config.c',\n"
          "  'build/k3-b2/port/arch/riscv/be/sv39x4.c',\n"
          "  'build/k3-b4/r7/port/tests/r1/r1-report.c',\n"
          "  'build/k3-b4/r7/port/tests/r2/r2-report.c',\n"
          "  'build/k3-b4/r7/port/tests/r1/check-report.mjs',\n"
          "  'build/k3-b4/r7/port/tests/r2/check-report.mjs',\n"
          "  'bringup/k3-b2/scripts/port.py'\n"
          "]\n", 1,
          "pin the K3 inputs that produce the facts: B2's ported R1/R2 "
          "sources, the K3 copies of the report tools, and B2's port script"),
    exact("// Shells out to an already-accepted rN check-acceptance.sh "
          "--require rather\n"
          "// than reimplementing any git-diff/acceptance logic here.\n"
          "function requireAcceptance (stage, scriptRel, cwdRel) {\n",
          "// K3 (B4): R5 provenance is B2's own port check, which re-derives\n"
          "// the port from the SHA-256-pinned accepted R5 bytes and requires\n"
          "// a byte-identical tree, bound to the commit and date the "
          "accepted\n"
          "// R5 acceptance interface records (read, not run).\n"
          "function requireB2Port () {\n"
          "  runRequired(PYTHON_BIN, ['-B', resolve(ROOT, R5_CHECKER_REL), "
          "'--check', ROOT,\n"
          "    resolve(ROOT, R5_CWD_REL)], { cwd: ROOT }, 'B2 port check')\n"
          "  const header = readFileSync(resolve(ROOT, R5_REPORT_REL), "
          "'utf8').split('\\n', 1)[0]\n"
          "  const ported = /^# K3 port of accepted R5 ([0-9a-f]{40})$/"
          ".exec(header)\n"
          "  assert(ported, 'B2 port manifest does not name the accepted R5 "
          "commit it ported')\n"
          "  const record = parseKeyValueLines(readFileSync(resolve(ROOT, "
          "R5_ACCEPTANCE_REL), 'utf8'))\n"
          "  assert(record.accepted_commit === ported[1],\n"
          "    'B2 ported a commit other than the one the accepted R5 record "
          "names')\n"
          "  assert(/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(record.accepted_at || "
          "''),\n"
          "    'the accepted R5 record names no acceptance date')\n"
          "  return {\n"
          "    r5_acceptance: 'accepted',\n"
          "    r5_accepted_commit: ported[1],\n"
          "    r5_accepted_at: record.accepted_at,\n"
          "    r5_accepted_mechanism_match: 'yes'\n"
          "  }\n"
          "}\n"
          "\n"
          "// K3 (B4): R1 and R2 provenance does not run the accepted rN\n"
          "// check-acceptance.sh, which also pins the root Makefile that "
          "these\n"
          "// facts do not depend on. port-r7.py --provenance requires the\n"
          "// accepted commit's own bytes in git history to equal B2's pins "
          "for\n"
          "// the R1/R2 mechanism inputs and B4's pins for the report "
          "tools,\n"
          "// with both copies freshly re-derived, reads the commit and date "
          "the\n"
          "// accepted interface records (never running it), and prints the "
          "same\n"
          "// four keys, so every assertion below is unchanged.\n"
          "function requireAcceptance (stage, scriptRel, cwdRel) {\n"
          "  if (stage === 'r5') return requireB2Port()\n", 1,
          "R5 provenance for the K3 images is B2's port of the accepted R5 "
          "inputs; R1 and R2 provenance is described by the next rule"),
    exact("  const res = runRequired(SH_BIN, [scriptAbs, '--require'], "
          "{ cwd }, `${stage} acceptance`)\n",
          "  const res = runRequired(PYTHON_BIN, ['-B', resolve(ROOT, "
          "B4_PORT_SCRIPT_REL), '--provenance',\n"
          "    stage, ROOT], { cwd }, `${stage} provenance`)\n", 1,
          "R1/R2 provenance from git history and the port pins, not the "
          "accepted interfaces, which also pin the root Makefile"),
    exact("// R5's own report generation is the heavy full riscv cross-build "
          "plus six\n"
          "// QEMU runs; this script deliberately does not trigger it. It "
          "reads and\n"
          "// revalidates the existing accepted report and fails closed with "
          "an\n"
          "// actionable message if it is not already present.\n"
          "function loadR5Report () {\n"
          "  const acceptance = requireAcceptance('r5', R5_ACCEPTANCE_REL, "
          "R5_CWD_REL)\n"
          "  const reportAbs = resolve(ROOT, R5_REPORT_REL)\n"
          "  assert(\n"
          "    existsSync(reportAbs),\n"
          "    `r5 report missing at ${R5_REPORT_REL} -- run "
          "'./tests/r5/run-make.sh r5-evidence' ` +\n"
          "    \"(or './tests/r5/run-make.sh r5-check') first; this script "
          "deliberately \" +\n"
          "    'does not auto-regenerate the heavy R5 QEMU pipeline. Inside "
          "the R7 graph ' +\n"
          "    \"the r7-extract stage delegates that rebuild, and "
          "'--verify-prerequisites' \" +\n"
          "    'proves the delegation actually produced this report on this "
          "run'\n"
          "  )\n"
          "  runRequired(\n"
          "    NODE_BIN, [resolve(ROOT, R5_CHECKER_REL), reportAbs],\n"
          "    { cwd: resolve(ROOT, R5_CWD_REL) }, 'r5 report checker'\n"
          "  )\n"
          "  const raw = readFileSync(reportAbs)\n"
          "  return { acceptance, path: R5_REPORT_REL, json: "
          "JSON.parse(raw.toString('utf8')), sha256: sha256Hex(raw) }\n"
          "}\n",
          "// K3 (B4): the accepted R5 QEMU report describes the accepted QEMU\n"
          "// images, not B2's K3 images, and B4 runs no QEMU, so it is not an\n"
          "// input here. B2's port manifest is bound instead, after B2's own\n"
          "// port check has re-derived it.\n"
          "function loadR5Report () {\n"
          "  const acceptance = requireAcceptance('r5', R5_ACCEPTANCE_REL, "
          "R5_CWD_REL)\n"
          "  const raw = readFileSync(resolve(ROOT, R5_REPORT_REL))\n"
          "  return { acceptance, path: R5_REPORT_REL, json: null, sha256: "
          "sha256Hex(raw) }\n"
          "}\n", 1,
          "no R5 QEMU report exists for the K3 images; B4 binds B2's port "
          "manifest instead"),
    exact("  // R5 cross-check: corroborating dynamic QEMU evidence for the "
          "same\n"
          "  // rights/denial facts. This is bound here as evidence per the "
          "task's\n"
          "  // explicit R1/R2/R5 requirement, but it is NOT part of the "
          "Configuration.v\n"
          "  // obligation itself -- that obligation is limited to the static "
          "R1/R2\n"
          "  // configuration facts above, not R5's dynamic QEMU trace.\n"
          "  const r5j = r5.json\n"
          "  assert(r5j.schema === 'be-r5-checked-switch-v1', `unexpected r5 "
          "schema: ${r5j.schema}`)\n"
          "  const iso = r5j.isolation || {}\n"
          "  for (const [k, v] of Object.entries(EXPECTED_ISOLATION)) {\n"
          "    assert(iso[k] === v, `r5 isolation.${k} = "
          "${JSON.stringify(iso[k])}, expected ${JSON.stringify(v)}`)\n"
          "  }\n"
          "  assert(\n"
          "    r5j.authorization && r5j.authorization.r5_accepted_commit === "
          "r5.acceptance.r5_accepted_commit,\n"
          "    'r5 report authorization.r5_accepted_commit does not match "
          "live r5 acceptance'\n"
          "  )\n"
          "  const r5CrossCheck = {\n"
          "    schema: r5j.schema,\n"
          "    isolation: { ...EXPECTED_ISOLATION },\n"
          "    accepted_commit: r5.acceptance.r5_accepted_commit\n"
          "  }\n",
          "  // K3 (B4): no dynamic cross-check. The accepted R5 QEMU isolation\n"
          "  // runs are evidence about the QEMU images, and B4 runs neither "
          "QEMU\n"
          "  // nor the board, so nothing dynamic is bound. As in accepted R7,\n"
          "  // the Configuration.v obligation is limited to the static R1/R2\n"
          "  // facts above; this record binds B2's port of the accepted R5\n"
          "  // inputs and states that the dynamic cross-check did not run.\n"
          "  const r5CrossCheck = {\n"
          "    schema: 'be-k3-b4-b2-port-binding-v1',\n"
          "    dynamic_isolation_cross_check: 'NOT-RUN-in-k3-b4',\n"
          "    accepted_commit: r5.acceptance.r5_accepted_commit\n"
          "  }\n", 1,
          "the accepted R5 QEMU isolation runs are not evidence about the "
          "K3 images, so none is bound"),
    exact("  lines.push(' * Produced by tests/r7/check-configuration-trace.mjs "
          "--generate.')\n",
          "  lines.push(' * Produced by the K3 (B4) copy of "
          "tests/r7/check-configuration-trace.mjs.')\n", 1,
          "the generated data names its real producer"),
    exact("  lines.push(' * R5 checked-switch isolation facts are "
          "corroborating dynamic evidence')\n"
          "  lines.push(' * bound in the companion JSON trace only; they are "
          "deliberately not')\n"
          "  lines.push(' * represented as Rocq data here because "
          "Configuration.v\\'s obligation is')\n"
          "  lines.push(' * limited to the static R1/R2 configuration facts "
          "below.')\n",
          "  lines.push(' * K3 (B4): the R1/R2 facts below come from the "
          "accepted R1/R2 report')\n"
          "  lines.push(' * generators compiled against B2\\'s K3 port. No "
          "dynamic isolation')\n"
          "  lines.push(' * facts are bound; the companion JSON trace binds "
          "B2\\'s port of the')\n"
          "  lines.push(' * accepted R5 inputs instead.')\n", 1,
          "the generated data states its real K3 provenance"),
    exact("  const r5c = trace.r5_cross_check\n"
          "  assert(r5c && r5c.schema === 'be-r5-checked-switch-v1', "
          "'r5_cross_check.schema tampered')\n"
          "  for (const [k, v] of Object.entries(EXPECTED_ISOLATION)) {\n"
          "    assert(r5c.isolation && r5c.isolation[k] === v, "
          "`r5_cross_check.isolation.${k} tampered`)\n"
          "  }\n",
          "  const r5c = trace.r5_cross_check\n"
          "  assert(r5c && r5c.schema === 'be-k3-b4-b2-port-binding-v1', "
          "'r5_cross_check.schema tampered')\n"
          "  assert(r5c.dynamic_isolation_cross_check === 'NOT-RUN-in-k3-b4',\n"
          "    'r5_cross_check.dynamic_isolation_cross_check tampered')\n"
          "  assert(Object.keys(r5c).length === 3, 'r5_cross_check has "
          "unexpected keys')\n", 1,
          "the independent checker refuses any dynamic claim for the K3 "
          "trace"),
    exact("    { name: 'forged-r5-isolation', mutate: (c) => { "
          "c.r5_cross_check.isolation.protectedReadOfManagementPrivate = "
          "'permitted' } },\n",
          "    { name: 'forged-r5-isolation', mutate: (c) => { "
          "c.r5_cross_check.dynamic_isolation_cross_check = 'PASS' } },\n",
          1, "the K3 form of a forged dynamic isolation claim"),
    exact("build/r7", "build/k3-b4/r7", 13, WHY_OUT),
]

# ----------------------------------------------------------- R1/R2 tools
R1_REPORT = []
R1_CHECKER = [
    rebase("rebase-hex16", 13,
           "the thirteen R1 frame bases move with the image, as B2's "
           "r0-config.h and r0-layout.h move them"),
]
R2_REPORT = [
    rebase("rebase-hex8", 2,
           "the two fixed pool bases are the root-table frames, which move "
           "with the image"),
]
R2_CHECKER = [
    exact("const MANAGEMENT_POOL_BASE = 0x80214000n;",
          "const MANAGEMENT_POOL_BASE = 0x102014000n;", 1,
          "the management root-table frame moves with the image (hgatp PPN "
          "0x102014, as B2's r3.h)"),
    exact("const PROTECTED_POOL_BASE = 0x8021c000n;",
          "const PROTECTED_POOL_BASE = 0x10201c000n;", 1,
          "the protected root-table frame moves with the image (hgatp PPN "
          "0x10201c, as B2's r3.h)"),
    exact("l1_ppn: '0x00000080218'", "l1_ppn: '0x00000102018'", 1,
          "pointer-table PPNs follow the management pool base"),
    exact("l0_ppn: '0x00000080219'", "l0_ppn: '0x00000102019'", 1,
          "pointer-table PPNs follow the management pool base"),
    exact("l1_ppn: '0x00000080220'", "l1_ppn: '0x00000102020'", 1,
          "pointer-table PPNs follow the protected pool base"),
    exact("l0_ppn: '0x00000080221'", "l0_ppn: '0x00000102021'", 1,
          "pointer-table PPNs follow the protected pool base"),
    rebase("rebase-hex16", 8,
           "the two pool bases and six leaf backing pages move with the "
           "image; guest-physical addresses do not"),
]

# --------------------------------------------------------- proof modules
# Exact.v pins the image identity, the allocated-section table, the scoped
# layout, and the C cut-point addresses. Each K3 value below was measured
# from B2's images (flat SHA-256 9c145f00... GCC, 47be17e3... Clang) by the
# K3 copy of the accepted extractor and cross-checked by GNU objdump; the
# cut points are the ELF symbols be_r5_trap_dispatch and
# be_r5_runtime_terminal, which the B4 report re-reads from the symbol table.
WHY_ALLOC = ("B2's K3 image: the allocated-image identity covers the "
             "rebased layout constants, the be_b1_quiesce call in be_reset, "
             "and the quiesce routine itself")
WHY_TEXT = (".monitor.text is 112 bytes longer: be_reset's 8-byte call "
            "moves the code after it by 0x10, and B1's 96 bytes of quiesce "
            "code (be_b1_quiesce, be_b1_skip, be_b1_halt) follow the last "
            "accepted function; its code also forms rebased addresses")
WHY_INPUT = (".monitor.input holds the rebased R0 layout and the K3 "
             "profile constants")
WHY_RODATA = (".monitor.rodata holds the K3 R1 profile, identity, and SBI "
              "version constants")
WHY_COUNTS = ("measured K3 allocated file/memory bytes (the 112 extra text "
              "bytes) and symbol-table entries (B1's three quiesce symbols "
              "and the extra mapping and local symbols of b1-handoff.o)")
WHY_CUT = ("measured K3 address of the named C cut point; C code moves by "
           "the toolchain's own alignment, not by a uniform delta")
EXACT = [
    exact('"46fdf832d26e3e8f3212a0fa78adc56bf45afcad11225656ab5b5d1dcab73d27"',
          '"ef2b1af6dca6d28aaee2c43e6cf237b8796abe37cc7bf4c35b2e0e4029cd9dee"',
          1, WHY_ALLOC),
    exact('"162a96462e722a622f6b362e10fa27517a08b16d7ae2f765070cfee580211994"',
          '"4dd9a6138ac0cf2c5e6b1c34a09f57c3c3428f605ff881b9ebb7145c631bc9c5"',
          1, WHY_ALLOC),
    exact("16 46856 153352\n                    entry_address 386",
          "16 46968 153464\n                    entry_address 391", 2,
          WHY_COUNTS),
    exact("16 46096 152592\n                    entry_address 521",
          "16 46208 152704\n                    entry_address 530", 2,
          WHY_COUNTS),
    exact("be_r7_section_size := 30224;\n      be_r7_section_sha256 := "
          '"4f5d43803d58246ceefde126b091a84ee01b3dc9ed5da5a4a461441ff4d1564e"',
          "be_r7_section_size := 30336;\n      be_r7_section_sha256 := "
          '"504db5421d17ed47bd165a68f633cdee3487dd2cbcaee0e9f26a6507191a66b0"',
          1, WHY_TEXT),
    exact('"fbe427d9541e75e55cee6e4e67164fd0ad95d5eebc7da5cc0f3acb2e55071219"',
          '"acc1b4379718bb3ae199c84d93315ab36cb6600cf3687dfef980462975d670fd"',
          1, WHY_INPUT),
    exact('"ad209889856cfc0a8253365dfaf917951c26371986ffbc034a55d733e3510c32"',
          '"b4fd7261f4b338f7da969e9707565e0f0472dd033a0336109bd00802ec2ef9c7"',
          1, WHY_RODATA),
    exact("be_r7_section_size := 30272;\n      be_r7_section_sha256 := "
          '"0b3a5e06a7cd0ce145f9d054a7d94eb9b6e87dc6095186c71a82a27e903bb578"',
          "be_r7_section_size := 30384;\n      be_r7_section_sha256 := "
          '"ec72ebd73dee186dd4e0acfbba1b3f755951e08bc092ead24569815a7d9e32be"',
          1, WHY_TEXT),
    exact('"e24da06e5ad1da2d5a23aae8c46a212b868674628e20f2a1a4cba7876884403d"',
          '"fb6db018b42897f1d61a45254b4d7cb804bbaab0758abdc0db88ea00a5a3931e"',
          1, WHY_INPUT),
    exact('"8d0abfe264f00bcb95ec4021920cb5bd5d45af0c877e05b76709d0aa8d6e0d55"',
          '"a22637c7cf185cd2ce6bb6e8a1b7189b6ac1204d9b987e8629cbc976c229c964"',
          1, WHY_RODATA),
    exact("gcc_cut_dispatch : Z := 0x80205d2a.",
          "gcc_cut_dispatch : Z := 0x102005d38.", 1, WHY_CUT),
    exact("gcc_cut_terminal : Z := 0x80205b1a.",
          "gcc_cut_terminal : Z := 0x102005b28.", 1, WHY_CUT),
    exact("clang_cut_dispatch : Z := 0x80205f38.",
          "clang_cut_dispatch : Z := 0x102005f50.", 1, WHY_CUT),
    exact("clang_cut_terminal : Z := 0x80205e98.",
          "clang_cut_terminal : Z := 0x102005eb0.", 1, WHY_CUT),
    rebase("rebase-row", 22,
           "each scoped symbol moves with the image plus the 0x10 that "
           "be_reset's quiesce call adds ahead of it; sizes and unit counts "
           "are unchanged"),
    rebase("rebase-hex8", 37,
           "the entry point, all 32 allocated-section addresses, and the "
           "four trusted-stack/saved-page extents move exactly with the "
           "image"),
]
CONFIGURATION = [
    rebase("rebase-dec", 26,
           "the thirteen R1 resource bases, pinned once as nat and once as "
           "Z, move exactly with the image; guest-physical addresses, sizes, "
           "rights, and the matrix do not change"),
]

RULES = {
    "tests/r7/extract-exact-image.mjs": EXTRACTOR,
    "tests/r7/check-disassembly.sh": DISASSEMBLY,
    "tests/r7/generate-exact-input.mjs": GENERATOR,
    "tests/r7/check-configuration-trace.mjs": TRACE,
    "tests/r7/proof/Exact.v": EXACT,
    "tests/r7/proof/Configuration.v": CONFIGURATION,
    "tests/r1/r1-report.c": R1_REPORT,
    "tests/r1/check-report.mjs": R1_CHECKER,
    "tests/r2/r2-report.c": R2_REPORT,
    "tests/r2/check-report.mjs": R2_CHECKER,
}

# Files whose output must carry no literal of the accepted QEMU image range.
RANGE_CLEAN = [path for path in PINS
               if path.endswith(".v") or path.startswith(("tests/r1/",
                                                          "tests/r2/"))]

HEX8 = re.compile(r"\b0[xX]8[0-9a-fA-F]{7}\b")
HEX16 = re.compile(r"\b0x0{8}8[0-9a-f]{7}\b")
DEC = re.compile(r"(?<![0-9A-Za-z_])[0-9]{10}(?![0-9A-Za-z_])")
ROW = re.compile(r'(mk_row "[a-z0-9_]+" )0x([0-9a-f]+)')


def in_image(value):
    return QEMU_IMAGE_BASE <= value <= QEMU_IMAGE_LIMIT


def apply_rebase(kind, text):
    """Rebase one literal class; return (text, count)."""
    count = 0

    def hex8(match):
        nonlocal count
        value = int(match.group(0), 16)
        if not in_image(value):
            return match.group(0)
        count += 1
        return f"0x{value + K3_DELTA:x}"

    def hex16(match):
        nonlocal count
        value = int(match.group(0), 16)
        if not in_image(value):
            return match.group(0)
        count += 1
        return f"0x{value + K3_DELTA:016x}"

    def dec(match):
        nonlocal count
        value = int(match.group(0))
        if not in_image(value):
            return match.group(0)
        count += 1
        return str(value + K3_DELTA)

    def row(match):
        nonlocal count
        value = int(match.group(2), 16)
        if not in_image(value):
            return match.group(0)
        count += 1
        return f"{match.group(1)}0x{value + K3_SCOPED_DELTA:x}"

    patterns = {"rebase-hex8": (HEX8, hex8), "rebase-hex16": (HEX16, hex16),
                "rebase-dec": (DEC, dec), "rebase-row": (ROW, row)}
    pattern, function = patterns[kind]
    return pattern.sub(function, text), count


def range_residue(text):
    left = [literal for literal in HEX8.findall(text)
            if in_image(int(literal, 16))]
    left += [literal for literal in HEX16.findall(text)
             if in_image(int(literal, 16))]
    left += [literal for literal in DEC.findall(text)
             if in_image(int(literal))]
    return left


# Mask every numeric and digest literal: what remains is proof structure.
MASK = re.compile(r'"[0-9a-f]{64}"|\b0[xX][0-9a-fA-F]+\b|\b[0-9]+\b')


def structure(text):
    return MASK.sub("#", text)


DECLARATION = re.compile(r"^(Theorem|Lemma)\s+([A-Za-z0-9_']+)", re.M)

# The accepted R7 FORBIDDEN_DECLS (tests/r7/Makefile) and its closed-
# assumption test, in one place for the gate, the report, and the negative
# tests: a module that could assert rather than prove, or disable a kernel
# check, fails; so does any assumption behind be_r7_claims_hold.
FORBIDDEN = re.compile(
    r"(^|[^A-Za-z0-9_])(Admitted|Abort|Axiom|Axioms|Conjecture|Hypotheses|"
    r"Hypothesis|Parameter|Parameters|Variable|Variables|admit|give_up|"
    r"exact_no_check|vm_cast_no_check|native_cast_no_check|"
    r"Unset\s+(Guard|Positivity|Universe)\s+Checking)([^A-Za-z0-9_]|$)",
    re.M)
ASSUMPTION_LINE = re.compile(
    r"^(Axioms|Parameters|Variables|Section Variables|Anonymous axioms):",
    re.M)
CLOSED = "Closed under the global context"


def scan(directory):
    """Refuse any .v in DIR that carries a forbidden declaration."""
    found = []
    for source in sorted(directory.glob("*.v")):
        for number, line in enumerate(source.read_text().splitlines(), 1):
            match = FORBIDDEN.search(line)
            if match:
                found.append(f"{source.name}:{number}: {match.group(2)}")
    if found:
        raise ValueError(f"forbidden declarations: {found[:5]}")
    return len(list(directory.glob("*.v")))


def assumptions(log):
    """Require Print Assumptions to report a closed bundle and nothing else."""
    text = log.read_text(errors="replace")
    if CLOSED not in text.splitlines():
        raise ValueError(f"{log.name}: the bundle is not closed under the "
                         "global context")
    if ASSUMPTION_LINE.search(text):
        raise ValueError(f"{log.name}: Print Assumptions lists an "
                         "assumption")


def inventory(texts):
    """Ordered (kind, module, name) declarations over modules in order."""
    found = []
    for module in PROOF_MODULES:
        for kind, name in DECLARATION.findall(texts[module]):
            found.append((kind, module, name))
    return found


def git_show(root, commit, path):
    """PATH as committed at COMMIT, whatever the working tree holds."""
    return subprocess.run(["git", "-C", str(root), "show",
                           f"{commit}:{path}"], check=True,
                          capture_output=True).stdout


def read_pinned(root, path, pins):
    """PATH's bytes, refused unless they equal its pin.

    A copied input is read from its accepted commit, and a READ_IN_PLACE
    lock from the working tree, where the copies read it at run time.
    """
    commit, pin = pins[path]
    if path in READ_IN_PLACE:
        data = (root / path).read_bytes()
    else:
        data = git_show(root, commit, path)
    digest = hashlib.sha256(data).hexdigest()
    if digest != pin:
        raise ValueError(f"{path}: input differs from accepted "
                         f"{commit[:12]} (sha256 {digest})")
    return data


def derive(root):
    """Return {path: (ported text, report lines)} or raise ValueError."""
    unknown = sorted(set(RULES) - set(PINS))
    if unknown:
        raise ValueError(f"rules for unpinned inputs: {unknown}")
    for path in READ_IN_PLACE:
        read_pinned(root, path, READ_IN_PLACE)
    ported = {}
    accepted_proof = {}
    for path in PINS:
        text = read_pinned(root, path, PINS).decode("utf-8")
        accepted = text
        report = []
        for kind, old, new, count, _why in RULES.get(path, []):
            if kind == "exact":
                found = text.count(old)
                if found != count:
                    raise ValueError(f"{path}: {old[:60]!r} found {found} "
                                     f"times, expected {count}")
                text = text.replace(old, new)
                report.append(f"exact x{count}: {old.splitlines()[0][:60]!r}")
            else:
                text, found = apply_rebase(kind, text)
                if found != count:
                    raise ValueError(f"{path}: {kind} rebased {found} "
                                     f"literals, expected {count}")
                report.append(f"{kind} x{count}")
        if path in RANGE_CLEAN:
            left = range_residue(text)
            if left:
                raise ValueError(f"{path}: QEMU image-range literals "
                                 f"remain: {left}")
        if path == DISASSEMBLY_PATH:
            check_sc1007_line(accepted, text)
        if path.endswith(".v"):
            module = pathlib.PurePosixPath(path).stem
            if structure(text) != structure(accepted):
                raise ValueError(f"{path}: a change is not literal-only")
            accepted_proof[module] = (accepted, text)
        ported[path] = (text, report)
    accepted_inventory = inventory({m: a for m, (a, _) in
                                    accepted_proof.items()})
    ported_inventory = inventory({m: p for m, (_, p) in
                                  accepted_proof.items()})
    check_inventory(accepted_inventory)
    if ported_inventory != accepted_inventory:
        raise ValueError("the ported Theorem/Lemma inventory differs")
    return ported


def check_inventory(found):
    theorems = sum(1 for kind, _, _ in found if kind == "Theorem")
    lemmas = sum(1 for kind, _, _ in found if kind == "Lemma")
    if (theorems, lemmas) != (ACCEPTED_THEOREMS, ACCEPTED_LEMMAS):
        raise ValueError(f"inventory has {theorems} Theorem and {lemmas} "
                         f"Lemma declarations, accepted R7 has "
                         f"{ACCEPTED_THEOREMS} and {ACCEPTED_LEMMAS}")


def check_directory_inventory(root, directory):
    """Require DIR/*.v to carry exactly the accepted inventory."""
    accepted = {}
    for module in PROOF_MODULES:
        path = f"tests/r7/proof/{module}.v"
        accepted[module] = read_pinned(root, path, PINS).decode("utf-8")
    present = {}
    for module in PROOF_MODULES:
        present[module] = (directory / f"{module}.v").read_text()
    expected = inventory(accepted)
    found = inventory(present)
    if found != expected:
        missing = sorted(set(expected) - set(found))
        extra = sorted(set(found) - set(expected))
        raise ValueError(f"inventory differs: missing {missing[:3]} "
                         f"extra {extra[:3]}")
    check_inventory(found)
    return found


def sc1007_lines(text):
    return [(number, line) for number, line in
            enumerate(text.splitlines(), 1) if SC1007_MARK in line]


def check_sc1007_line(accepted, ported):
    """The inherited SC1007 line changes only by the repository-root rule."""
    root_rule = DISASSEMBLY[0]
    if sc1007_lines(accepted) != [(SC1007_LINE, root_rule[1])]:
        raise ValueError(f"{DISASSEMBLY_PATH}: the accepted SC1007 line is "
                         "not the one the root rule names")
    if sc1007_lines(ported) != [(SC1007_LINE, root_rule[2])]:
        raise ValueError(f"{DISASSEMBLY_PATH}: the inherited SC1007 line "
                         "changed beyond the repository-root rule")


def shellcheck_findings(path, text=None):
    """[(line, column, level, code)] from `shellcheck -f gcc PATH`.

    With PATH `-`, shellcheck reads TEXT from stdin.
    """
    result = subprocess.run(["shellcheck", "-f", "gcc", str(path)],
                            input=text, capture_output=True, text=True,
                            check=False)
    findings = []
    pattern = re.compile(r"^[^:]+:(\d+):(\d+): (\w+): .* \[(SC\d+)\]$")
    for line in result.stdout.splitlines():
        match = pattern.match(line)
        if not match:
            raise ValueError(f"unexpected shellcheck output: {line!r}")
        findings.append((int(match.group(1)), int(match.group(2)),
                         match.group(3), match.group(4)))
    if result.returncode not in (0, 1) or result.stderr.strip():
        raise ValueError(f"shellcheck failed: {result.stderr.strip()}")
    return findings


def check_shellcheck(root, out):
    """The copy keeps exactly the accepted file's shellcheck findings."""
    accepted_text = read_pinned(root, DISASSEMBLY_PATH, PINS).decode("utf-8")
    copy = out / DISASSEMBLY_PATH
    check_sc1007_line(accepted_text, copy.read_text())
    accepted = shellcheck_findings("-", accepted_text)
    ported = shellcheck_findings(copy)
    inherited = [finding for finding in accepted if finding[3] == "SC1007"]
    if [finding[:1] + finding[3:] for finding in inherited] != \
            [(SC1007_LINE, "SC1007")]:
        raise ValueError(f"the accepted file's SC1007 finding moved: "
                         f"{accepted}")
    shape = sorted(finding[1:] for finding in accepted)
    if sorted(finding[1:] for finding in ported) != shape or \
            [f for f in ported if f[3] == "SC1007"] != inherited:
        raise ValueError(f"shellcheck findings differ: accepted {accepted}, "
                         f"copy {ported}")
    return inherited[0], len(ported)


def git_sha256(root, commit, path):
    return hashlib.sha256(git_show(root, commit, path)).hexdigest()


def load_b2(root):
    spec = importlib.util.spec_from_file_location("b2_port",
                                                  root / B2_PORT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def provenance(stage, root):
    """The four provenance keys the trace needs for R1 or R2.

    The accepted commit's own bytes in git history must equal B2's pins for
    the R1/R2 mechanism inputs the facts consume and B4's pins for the report
    tools; B2's port and B4's copies must each be byte-identical to a fresh
    derivation; and the commit and date come from the accepted interface,
    which is read and never run.
    """
    commit, record_path, mechanism, tools = PROVENANCE[stage]
    record = {}
    for line in (root / record_path).read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator and key in ("accepted_commit", "accepted_at"):
            record.setdefault(key, value)
    if record.get("accepted_commit") != commit:
        raise ValueError(f"{record_path} records "
                         f"{record.get('accepted_commit')}, not {commit}")
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                        record.get("accepted_at", "")):
        raise ValueError(f"{record_path} records no acceptance date")
    b2 = load_b2(root)
    b2_ported = b2.derive(root)
    for path in mechanism:
        if b2.PINS[path] != git_sha256(root, commit, path):
            raise ValueError(f"B2's pin for {path} is not {commit[:12]}")
        if (root / B2_PORT_DIR / path).read_bytes() != \
                b2_ported[path][0].encode("utf-8"):
            raise ValueError(f"{B2_PORT_DIR}/{path} differs from B2's "
                             "fresh derivation")
    ours = derive(root)
    for path in tools:
        if PINS[path] != (commit, git_sha256(root, commit, path)):
            raise ValueError(f"B4's pin for {path} is not {commit[:12]}")
        if (root / B4_PORT_DIR / path).read_bytes() != \
                ours[path][0].encode("utf-8"):
            raise ValueError(f"{B4_PORT_DIR}/{path} differs from a fresh "
                             "derivation")
    return [f"{stage}_acceptance=accepted",
            f"{stage}_accepted_commit={commit}",
            f"{stage}_accepted_at={record['accepted_at']}",
            f"{stage}_accepted_mechanism_match=yes",
            f"{stage}_provenance=git-history-b2-pins-b4-pins-record-read",
            f"{stage}_mechanism_files={len(mechanism)}",
            f"{stage}_report_tools={len(tools)}"]


def verify_git(root):
    for path, (commit, pin) in {**PINS, **READ_IN_PLACE}.items():
        digest = git_sha256(root, commit, path)
        if digest != pin:
            raise ValueError(f"{path}: pin differs from git show "
                             f"{commit[:12]} (sha256 {digest})")


def self_test(root):
    """Each guard must refuse its case; the unmodified table must pass."""
    global RULES, PINS
    scratch = root / "build" / "k3-b4" / "r7" / "port-self-test"
    shutil.rmtree(scratch, ignore_errors=True)
    derive(root)
    saved = RULES
    saved_pins = PINS
    exact_v = "tests/r7/proof/Exact.v"
    switch_v = "tests/r7/proof/Switch.v"
    cases = [
        ("wrong-rule-count", "expected 99", {exact_v: [exact(
            "entry_address", "entry_address", 99, "count")] + EXACT}),
        ("structural-proof-change", "not literal-only", {exact_v: EXACT + [
            exact("Proof. vm_compute. reflexivity. Qed.\n\nTheorem "
                  "clang_image_identity_is_exact",
                  "Proof. exact I. Qed.\n\nTheorem "
                  "clang_image_identity_is_exact", 1, "structure")]}),
        ("removed-theorem", "not literal-only", {switch_v: [exact(
            "Theorem gcc_read_controls_is_exact :",
            "Example gcc_read_controls_is_exact :", 1, "removed")]}),
        ("residual-qemu-literal", "image-range literals remain",
         {exact_v: EXACT[:-1]}),
        ("rule-for-unpinned-input", "unpinned inputs",
         {"tests/r7/Makefile": []}),
        ("sc1007-line-changed", "SC1007 line", {DISASSEMBLY_PATH:
         DISASSEMBLY + [exact("CDPATH= cd --", "CDPATH='' cd --", 1,
                              "fix")]}),
    ]
    refused = 0

    def refuse(name, expected, action):
        nonlocal refused
        try:
            action()
        except ValueError as error:
            if expected not in str(error):
                raise ValueError(f"self-test case {name} was refused for "
                                 f"another reason: {error}") from error
            refused += 1
            return
        raise ValueError(f"self-test case {name} was not refused")

    try:
        for name, expected, change in cases:
            RULES = {**saved, **change}
            refuse(name, expected, lambda: derive(root))
        RULES = saved
        # A scratch root holding every input: a tampered working-tree copy
        # of a copied input changes nothing, because copied inputs come from
        # git, but a tampered in-place tool lock is refused, and so is a pin
        # that the accepted bytes do not match. Then a proof directory
        # missing one theorem.
        copy = scratch / "root"
        for path in {**PINS, **READ_IN_PLACE}:
            (copy / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, copy / path)
        target = copy / "tests/r7/proof/Trap.v"
        target.write_text(target.read_text() + "(* tampered *)\n")
        if derive(copy) != derive(root):
            raise ValueError("self-test: a working-tree copy of a copied "
                             "input changed the derivation")
        lock = copy / "tests/r3/tool-lock.conf"
        lock.write_text(lock.read_text() + "# tampered\n")
        refuse("tampered-in-place-lock", "input differs from accepted",
               lambda: derive(copy))
        PINS = {**saved_pins,
                "tests/r7/proof/Trap.v": (ACCEPTED_R7, "0" * 64)}
        refuse("pin-mismatch", "input differs from accepted",
               lambda: derive(root))
        PINS = saved_pins
        proof = scratch / "proof"
        proof.mkdir()
        ported = derive(root)
        for module in PROOF_MODULES:
            text = ported[f"tests/r7/proof/{module}.v"][0]
            if module == "Switch":
                text = text.replace("Theorem gcc_read_controls_is_exact :",
                                    "Example gcc_read_controls_is_exact :")
            (proof / f"{module}.v").write_text(text)
        refuse("missing-theorem-inventory", "inventory differs",
               lambda: check_directory_inventory(root, proof))
    finally:
        RULES = saved
        PINS = saved_pins
        shutil.rmtree(scratch, ignore_errors=True)
    return refused


def table_lines():
    lines = []
    for path, rules in RULES.items():
        for kind, old, _new, count, why in rules:
            what = kind if old is None else \
                f"exact {old.splitlines()[0].strip()[:56]!r}"
            lines.append(f"{path}\t{what}\tx{count}\t{why}")
    return lines


def write_or_check(out, ported, check):
    manifest = [f"# K3 B4 copy of accepted R7 {ACCEPTED_R7}",
                "# input-sha256 output-sha256 path"]
    for path, (text, report) in ported.items():
        target = out / path
        data = text.encode("utf-8")
        if check:
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError(f"{path} differs from a fresh derivation")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest.append(f"{PINS[path][1]} {hashlib.sha256(data).hexdigest()} "
                        f"{path}")
        for line in report:
            manifest.append(f"#   {path}: {line}")
    manifest_text = "\n".join(manifest) + "\n"
    manifest_path = out / "PORT-MANIFEST.txt"
    if check:
        expected = {out / path for path in ported} | {manifest_path}
        present = {path for path in out.rglob("*") if path.is_file()}
        if present != expected:
            extra = sorted(str(path.relative_to(out))
                           for path in present - expected)
            missing = sorted(str(path.relative_to(out))
                             for path in expected - present)
            raise ValueError(f"port file set differs: extra {extra} "
                             f"missing {missing}")
        if manifest_path.read_text() != manifest_text:
            raise ValueError("manifest differs")
    else:
        manifest_path.write_text(manifest_text)


def main(argv):
    try:
        if len(argv) == 2 and argv[1] == "--inputs":
            print(" ".join(PINS))
            return 0
        if len(argv) == 2 and argv[1] == "--table":
            print("\n".join(table_lines()))
            return 0
        if len(argv) == 3 and argv[1] == "--self-test":
            refused = self_test(pathlib.Path(argv[2]))
            print(f"BE_B4_R7_PORT_SELF_TEST: PASS refused={refused} "
                  f"baseline=derived")
            return 0
        if len(argv) == 3 and argv[1] == "--verify-git":
            verify_git(pathlib.Path(argv[2]))
            print(f"BE_B4_R7_PINS: PASS pins={len(PINS) + len(READ_IN_PLACE)}"
                  f" git=verified")
            return 0
        if len(argv) == 4 and argv[1] == "--provenance" and \
                argv[2] in PROVENANCE:
            print("\n".join(provenance(argv[2], pathlib.Path(argv[3]))))
            return 0
        if len(argv) == 4 and argv[1] == "--shellcheck":
            (line, column, _, code), findings = check_shellcheck(
                pathlib.Path(argv[2]), pathlib.Path(argv[3]))
            print(f"BE_B4_R7_SHELLCHECK: PASS inherited={code}@{line}:"
                  f"{column} findings={findings} new=0")
            return 0
        if len(argv) == 3 and argv[1] == "--scan":
            count = scan(pathlib.Path(argv[2]))
            print(f"BE_B4_R7_SCAN: PASS modules={count} forbidden=0")
            return 0
        if len(argv) == 3 and argv[1] == "--assumptions":
            assumptions(pathlib.Path(argv[2]))
            print("BE_B4_R7_ASSUMPTIONS: PASS be_r7_claims_hold=closed")
            return 0
        if len(argv) == 4 and argv[1] == "--inventory":
            found = check_directory_inventory(pathlib.Path(argv[2]),
                                              pathlib.Path(argv[3]))
            theorems = sum(1 for kind, _, _ in found if kind == "Theorem")
            print(f"BE_B4_R7_INVENTORY: PASS theorems={theorems} "
                  f"lemmas={len(found) - theorems} names=accepted")
            return 0
        check = len(argv) == 4 and argv[1] == "--check"
        if not check and len(argv) != 3:
            print(__doc__)
            return 2
        root, out = pathlib.Path(argv[-2]), pathlib.Path(argv[-1])
        ported = derive(root)
        write_or_check(out, ported, check)
    except (OSError, ValueError, UnicodeDecodeError,
            subprocess.CalledProcessError) as error:
        print(f"BE_B4_R7_PORT: FAIL {error}")
        return 1
    changed = sum(1 for _, report in ported.values() if report)
    rules = sum(len(rules) for rules in RULES.values())
    print(f"BE_B4_R7_PORT: {'CHECK ' if check else ''}PASS files={len(ported)}"
          f" changed={changed} rules={rules} accepted_r7={ACCEPTED_R7[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
