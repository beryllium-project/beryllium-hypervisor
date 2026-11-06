#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Write the concise B4 R7 report from the artefacts of one gate run.

  report.py ROOT          print the report for ROOT/build/k3-b4/r7
  report.py --self-test   require NOT-RUN and FAIL for absent or broken
                          proof artefacts, and PASS only for complete ones

The proof status is derived from the artefacts, never from the Makefile:
proof=PASS needs all nine compiled modules, closed assumptions for
be_r7_claims_hold, a `rocq check` of every module, proof sources equal to
the checked port and the twice-generated inputs, the accepted inventory,
and no forbidden declaration. Absent artefacts are NOT-RUN; anything else
short of that is FAIL. The report exits non-zero unless proof=PASS and
every other stage transcript it summarises shows its PASS line.
"""

import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("port_r7", HERE / "port-r7.py")
PORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PORT)

MODULES = ["ISA", "ExactInput", "Exact", "Entry", "Trap", "Switch",
           "ConfigurationTrace", "Configuration", "Claims"]
GENERATED = {"ExactInput": "generated/ExactInput.v",
             "ConfigurationTrace": "configuration-trace/ConfigurationTrace.v"}
# Stage transcripts and the PASS lines each must carry.
STAGES = [
    ("pins", "logs/pins.txt", ["BE_B4_R7_PINS: PASS"]),
    ("port-check", "logs/port-check.txt", ["BE_B4_R7_PORT: CHECK PASS"]),
    ("shellcheck", "logs/shellcheck.txt", ["BE_B4_R7_SHELLCHECK: PASS"]),
    ("images", "images/images.txt", ["BE_B4_R7_IMAGES: PASS"]),
    ("extract", "logs/extract.txt", ["BE_R7_EXTRACT: PASS"]),
    ("objdump-cross-check", "logs/disassembly.txt",
     ["BE_R7_DISASSEMBLY_CHECK: PASS"]),
    ("exact-input", "logs/exact-input.txt", ["BE_R7_EXACT_INPUT: PASS"]),
    ("r1-report", "r1/reports/report-check.txt", ["BE_R1_REPORT: PASS"]),
    ("r2-report", "r2/reports/report-check.txt", ["BE_R2_REPORT: PASS"]),
    ("configuration-trace", "logs/trace.txt",
     ["BE_R7_CONFIGURATION_TRACE: PASS mode=generate"]),
    ("configuration-trace-check", "logs/trace-check.txt",
     ["BE_R7_CONFIGURATION_TRACE: PASS mode=check"]),
    ("inputs-twice", "logs/inputs.txt", ["BE_B4_R7_INPUTS: PASS"]),
    ("inventory", "logs/inventory.txt", ["BE_B4_R7_INVENTORY: PASS"]),
    ("proof", "logs/proof.txt", ["BE_B4_R7_PROOF: PASS"]),
    ("self-tests", "logs/self-test.txt", [
        "BE_R7_EXTRACT_SELF_TEST: PASS",
        "BE_R7_DISASSEMBLY_CHECK_SELF_TEST: PASS",
        "BE_R7_EXACT_INPUT_SELF_TEST: PASS",
        "BE_R7_CONFIGURATION_TRACE: PASS mode=self-test",
        "BE_B4_R7_PORT_SELF_TEST: PASS",
        "BE_B4_R7_REPORT_SELF_TEST: PASS"]),
    ("negative", "logs/negative.txt", ["BE_B4_R7_NEGATIVE: PASS"]),
]

ACCEPTED = {
    "r7": "9bf22913d67e9b72286813cd5f7993a9ad3857a8",
    "r7_plan": "18c43596d308052cfad67edc6e2cb8f543f75600",
    "r5": "165f4d001a2b59b582b397bdea79ec4826168fdb",
    "r1": "a6e0bb178c10a7e68c9447a8e58affb94b8ecadb",
    "r2": "6e1cb579257c5dbe3234bd484fd091629e87181b",
    "b2": "898af4e02fd36744a93b0eef99bc159955409d25",
    "b3": "9b4860a049646d8878a31ecea8957e95b045550f",
}

# Accepted R7 measurements (planning/single-hart-runtime-r7-evidence.md).
ACCEPTED_COUNTS = "images=2 symbols=22 words=1420 targets=144 " \
    "alloc_sections=32 modules=9 theorems=135 lemmas=4"

# The accepted R7 ledger, carried verbatim (tests/r7/generate-report.mjs).
CUT_POINTS = [
    ("c-mechanism", "R3/R4/R5 restricted C mechanism bodies",
     "unproved-cut-point"),
    ("c-trap-dispatch",
     "the C trap dispatch body reached from be_r5_trap_vector",
     "unproved-cut-point"),
    ("c-pending-binding", "the C-formed pending switch binding consumed by "
     "the published tails", "unproved-assumed-precondition"),
    ("c-validator", "the R1 canonical validator implementation",
     "unproved-cut-point"),
    ("c-pte-builder", "the R2 Sv39x4 page-table builder implementation",
     "unproved-cut-point"),
    ("fact-linkage", "the link from R1/R2 C state to the generated "
     "configuration facts", "unproved-cut-point"),
    ("elf-parser", "tests/r7/extract-exact-image.mjs direct ELF parser",
     "trusted-cross-checked-by-objdump"),
    ("objdump", "the locked GNU objdump used as the independent cross-check",
     "trusted-tool"),
    ("input-generator", "tests/r7/generate-exact-input.mjs data rendering",
     "trusted-twice-reproduced"),
    ("rocq", "Rocq's kernel, rocq check, and the pinned host platform",
     "trusted-tool"),
    ("compiler", "GCC, Clang, GNU ld, and lld outside the extracted symbols",
     "trusted-tool"),
    ("firmware", "the pinned OpenSBI handoff below HS", "trusted-assumed"),
    ("emulator", "QEMU, which no R7 theorem consumes", "trusted-assumed"),
    ("architecture", "the ratified RISC-V privileged/hypervisor "
     "specification versus the bounded local semantics", "assumed-faithful"),
    ("profile", "single hart, no DMA, no devices, no guest SBI, fixed "
     "synthetic two-domain profile", "assumed"),
]
TRUSTED = [
    "the ratified RISC-V privileged and hypervisor specification is "
    "faithfully represented by the bounded local semantics",
    "the direct ELF parser and the independent objdump cross-check identify "
    "the intended linked bytes",
    "Rocq's kernel, rocq check, and the pinned host platform execute "
    "correctly",
    "the C cut points satisfy their stated contracts",
    "GCC, Clang, GNU ld, and lld compiled and linked the surrounding image "
    "correctly",
    "the pinned OpenSBI provides the frozen handoff",
    "QEMU implements the relevant architecture",
    "single hart, no DMA, no devices, no guest SBI, and the fixed synthetic "
    "profile hold",
    "the recorded proof-object and bundle digests are the identities this "
    "run produced; they are not reproducible identities and are not claimed "
    "to be re-derivable on a later run or another host",
    "the recorded whole-ELF-file digest is an observed run identity: the "
    "accepted R5 recipes compile with -g3 -gdwarf-4 and embed "
    "DW_AT_comp_dir, so two correct builds of identical sources at "
    "different absolute paths differ in non-allocated .debug_* bytes; only "
    "the recorded allocated-image digest is claimed to be build-path "
    "independent",
]
PLAN_SUBSTITUTION = (
    "trap-guest-gpr-clearing: the plan's 'clears live guest GPR authority' "
    "is delivered only as the narrower byte-true property that every value "
    "the trap wrapper forms and passes across the C dispatch cut point is "
    "monitor-derived; the saved guest GPR contents stay live in the frame "
    "(unproved-plan-obligation-substitution, carried unchanged from "
    "accepted R7)")
# What K3 adds to the ledger, and how accepted items read for K3.
K3_LEDGER = [
    ("k3-be-reset-quiesce-call", "be_reset's added `call be_b1_quiesce`, "
     "B2's one code delta; be_reset was never in the R7 scope",
     "outside-scope-not-proved"),
    ("k3-b1-quiesce", "B1's 96 bytes of quiesce code "
     "(bringup/k3-b1/src/b1-handoff.S: be_b1_quiesce, be_b1_skip with its "
     "own SRET, be_b1_halt) at the end of .monitor.text, which returns with "
     "stvec at be_b1_halt until a reset sequence installs the trap sink; "
     "only the "
     "pinned .monitor.text digest covers these bytes, the sole-SRET theorems "
     "speak only of the scoped symbols, and Exact.v proves no scoped symbol "
     "has a control edge to them", "outside-scope-not-proved"),
    ("k3-port", "B2's counted port of the accepted R5 sources "
     "(bringup/k3-b2/scripts/port.py) and B4's counted copy of the accepted "
     "R7 tooling (scripts/port-r7.py)",
     "trusted-counted-substitutions"),
    ("k3-tools", "this host's unpinned GNU objdump 2.46.1 and node v22.23.1 "
     "(the accepted R3 lock pins 2.46 and v22.22.2); versions and digests "
     "are recorded below", "trusted-tool-unpinned"),
    ("k3-firmware", "the K3 OpenSBI 1.6 (SBI 2.0) handoff on the COM260; no "
     "B4 theorem consumes firmware behaviour", "trusted-assumed"),
    ("k3-dynamic", "the dynamic R5 isolation cross-check: B4 runs no QEMU "
     "and no board, so the configuration trace binds no dynamic evidence",
     "NOT-RUN"),
]
K3_LEDGER_NOTES = [
    "objdump: for K3 the cross-check uses the lock's command path, not its "
    "digest (see k3-tools)",
    "firmware, emulator: no B4 theorem consumes OpenSBI or QEMU behaviour; "
    "the K3 firmware is k3-firmware",
]

CLAIM = (
    "For B2's two K3 images (bringup/k3-b2, accepted at 898af4e0; GCC/GNU "
    "ld and Clang/lld, the accepted R5 recipes rebased to 0x1_0200_0000), a "
    "machine-checked bounded Rocq development consumes exact linked bytes "
    "of the eleven scoped privileged-wrapper symbols, independently "
    "cross-checks those bytes with GNU objdump, decodes the enumerated "
    "subset, checks the fixed entry, trap-frame, root-install/fence/"
    "readback, restore, and return properties, and checks generated "
    "fixed-configuration facts from B2's K3 port against the accepted "
    "two-domain access matrix. The C implementation, be_reset and its call "
    "to be_b1_quiesce, the quiesce routine, the direct ELF parser, the "
    "compiler, the linker outside the extracted symbols, B2's port, "
    "OpenSBI, QEMU, RISC-V hardware, and the connection from C state to "
    "the generated configuration facts remain explicit assumptions.")
NON_CLAIMS = [
    "not formal verification of Beryllium; a bounded proof over extracted "
    "bytes of two images only",
    "not a whole-ELF or whole-hypervisor proof; be_reset, the quiesce, C "
    "handlers, diagnostics, SBI calls, and guest fixtures are not covered",
    "not a C refinement or source-to-binary validation result",
    "not hardware validation: these exact images ran on the COM260 in "
    "B2/B3, but this proof transfers no board claim and the board is "
    "NOT RUN here",
    "not an arbitrary-guest, arbitrary-page-table, information-flow, "
    "availability, timing, or side-channel result",
    "no Model 0.2, Helium, or accepted QEMU R7 theorem, object, or claim "
    "transfers to K3; every result is re-derived here",
    "no claim that the trap wrapper clears live guest GPR authority (see "
    "the plan-obligation substitution)",
    "no claim that the report bytes, ELF file digests, or .vo objects are "
    "byte-reproducible across paths or hosts",
    "not an acceptance of B4 and no authorization of any successor, "
    "publication, tag, push, or release",
]


class ReportError(Exception):
    pass


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proof_status(out, port_dir, root):
    """('PASS'|'FAIL'|'NOT-RUN', reasons) from the proof artefacts alone."""
    proof = out / "proof-build"
    compile_log = proof / "proof-compile.log"
    if not proof.is_dir() or not compile_log.is_file():
        return "NOT-RUN", ["no proof-build directory or compile log"]
    reasons = []
    for module in MODULES:
        source, obj = proof / f"{module}.v", proof / f"{module}.vo"
        if not source.is_file() or not obj.is_file() or obj.stat().st_size == 0:
            reasons.append(f"{module}: source or compiled object missing")
        elif obj.stat().st_mtime < source.stat().st_mtime:
            reasons.append(f"{module}: compiled object is older than source")
    try:
        PORT.assumptions(compile_log)
    except ValueError as error:
        reasons.append(str(error))
    check_log = proof / "proof-check.log"
    checked = check_log.read_text(errors="replace").splitlines() \
        if check_log.is_file() else []
    for module in MODULES:
        if f"Checking library: {module}" not in checked:
            reasons.append(f"rocq check did not check {module}")
    if "Modules were successfully checked" not in checked:
        reasons.append("rocq check did not succeed")
    for module in PORT.PROOF_MODULES:
        ported = port_dir / "tests" / "r7" / "proof" / f"{module}.v"
        built = proof / f"{module}.v"
        if not ported.is_file() or not built.is_file() or \
                ported.read_bytes() != built.read_bytes():
            reasons.append(f"{module}.v is not the checked port")
    digests = out / "proof-inputs.sha256"
    recorded = {}
    if digests.is_file():
        for line in digests.read_text().splitlines():
            digest, _, path = line.partition("  ")
            recorded[pathlib.Path(path).name] = digest
    for module, relative in GENERATED.items():
        built = proof / f"{module}.v"
        if not built.is_file() or \
                recorded.get(f"{module}.v") != sha256(built) or \
                not (out / relative).is_file() or \
                sha256(out / relative) != recorded.get(f"{module}.v"):
            reasons.append(f"{module}.v is not the twice-generated input")
    try:
        PORT.scan(proof)
    except ValueError as error:
        reasons.append(str(error))
    try:
        PORT.check_directory_inventory(root, proof)
    except (OSError, ValueError) as error:
        reasons.append(f"inventory: {error}")
    return ("FAIL", reasons) if reasons else ("PASS", [])


def stage_status(out):
    lines, failed = [], []
    for name, relative, markers in STAGES:
        path = out / relative
        text = path.read_text(errors="replace") if path.is_file() else ""
        if not text:
            status = "NOT-RUN"
        elif all(any(line.startswith(marker) for line in text.splitlines())
                 for marker in markers):
            status = "PASS"
        else:
            status = "FAIL"
        if status != "PASS":
            failed.append(name)
        lines.append(f"stage {name}={status}")
    return lines, failed


def tool_lines(root):
    def first_line(command):
        try:
            result = subprocess.run(command, capture_output=True, text=True,
                                    check=False)
        except OSError:
            return "missing"
        return (result.stdout or result.stderr).splitlines()[0].strip()

    def lock(path, key):
        for line in (root / path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1]
        return ""

    lines = []
    bound = [
        ("rocq", "/usr/bin/rocq", ["/usr/bin/rocq", "--version"],
         lock("tests/r7/tool-lock.conf", "R7_ROCQ_SHA256")),
        ("node", "/usr/bin/node", ["/usr/bin/node", "--version"],
         lock("tests/r3/tool-lock.conf", "R3_TOOL_node_sha256")),
        ("objdump", "/usr/bin/riscv64-linux-gnu-objdump",
         ["/usr/bin/riscv64-linux-gnu-objdump", "--version"],
         lock("tests/r3/tool-lock.conf", "R3_TOOL_cross_objdump_sha256")),
        ("bash", "/usr/bin/bash", ["/usr/bin/bash", "--version"],
         lock("tests/r3/tool-lock.conf", "R3_TOOL_shell_sha256")),
    ]
    for name, command, version, pinned in bound:
        resolved = pathlib.Path(command).resolve()
        digest = sha256(resolved)
        lines.append(f"tool {name} version={first_line(version)!r} "
                     f"sha256={digest} accepted_lock_digest="
                     f"{'match' if digest == pinned else 'differs'}")
    for name, version in [
            ("cross-gcc", ["riscv64-linux-gnu-gcc", "--version"]),
            ("clang", ["clang", "--version"]),
            ("lld", ["ld.lld", "--version"]),
            ("host-gcc", ["gcc", "--version"]),
            ("python", [sys.executable, "--version"])]:
        lines.append(f"tool {name} version={first_line(version)!r}")
    return lines


def load(out, relative):
    return json.loads((out / relative).read_text())


def image_lines(out):
    records = {}
    for line in (out / "images/images.txt").read_text().splitlines():
        if line.startswith(("gcc ", "clang ")):
            name, *fields = line.split()
            records[name] = dict(field.split("=", 1) for field in fields)
    lines, totals = [], {"symbols": 0, "words": 0, "words4": 0, "words2": 0,
                         "targets": 0, "alloc_sections": 0}
    for toolchain in ("gcc", "clang"):
        image = load(out, f"extract/{toolchain}.json")
        elf, record = image["elf"], records[toolchain]
        lines.append(
            f"image {toolchain} bin_sha256={record['bin_sha256']} "
            f"(B2 accepted) elf_sha256={record['elf_sha256']} (observed run "
            f"identity) alloc_sha256={elf['allocSha256']} "
            f"entry={elf['entry']} alloc_sections={elf['allocSectionCount']}"
            f" alloc_file_bytes={elf['allocFileBytes']} "
            f"alloc_memory_bytes={elf['allocMemoryBytes']} "
            f"symtab_entries={elf['symbolTableEntries']}")
        lines.append(
            f"image {toolchain} be_reset={record['be_reset']} "
            f"be_b1_quiesce={record['be_b1_quiesce']} "
            f"be_r5_trap_dispatch={record['be_r5_trap_dispatch']} "
            f"be_r5_runtime_terminal={record['be_r5_runtime_terminal']}")
        for symbol in image["symbols"]:
            wide = sum(1 for unit in symbol["units"] if unit["length"] == 4)
            narrow = len(symbol["units"]) - wide
            lines.append(
                f"symbol {toolchain} {symbol['name']} "
                f"address={symbol['address']} size={symbol['size']} "
                f"words={len(symbol['units'])} words32={wide} "
                f"words16={narrow} targets={len(symbol['targets'])}")
            totals["symbols"] += 1
            totals["words"] += len(symbol["units"])
            totals["words4"] += wide
            totals["words2"] += narrow
            totals["targets"] += len(symbol["targets"])
        totals["alloc_sections"] += len(image["allocSections"])
    return lines, totals, records


def cut_point_lines(root, records):
    """The four Exact.v cut points must be the ELF's own C symbols."""
    exact_v = (root / "build/k3-b4/r7/port/tests/r7/proof/Exact.v").read_text()
    lines, mismatched = [], []
    for toolchain in ("gcc", "clang"):
        for kind, symbol in (("dispatch", "be_r5_trap_dispatch"),
                             ("terminal", "be_r5_runtime_terminal")):
            match = re.search(rf"{toolchain}_cut_{kind} : Z := (0x[0-9a-f]+)",
                              exact_v)
            pinned = match.group(1) if match else "missing"
            elf = records[toolchain][symbol]
            agree = pinned == elf
            if not agree:
                mismatched.append(f"{toolchain}_cut_{kind}")
            lines.append(f"cut_point {toolchain}_cut_{kind}={pinned} "
                         f"elf_{symbol}={elf} "
                         f"agree={'yes' if agree else 'no'}")
    return lines, mismatched


def inventory_lines(out):
    proof = out / "port" / "tests" / "r7" / "proof"
    lines, theorems, lemmas = [], 0, 0
    for module in PORT.PROOF_MODULES:
        text = (proof / f"{module}.v").read_text()
        found = PORT.DECLARATION.findall(text)
        module_theorems = sum(1 for kind, _ in found if kind == "Theorem")
        module_lemmas = len(found) - module_theorems
        theorems += module_theorems
        lemmas += module_lemmas
        accepted = PORT.PINS[f"tests/r7/proof/{module}.v"][1]
        ported = hashlib.sha256(text.encode()).hexdigest()
        lines.append(f"module {module} theorems={module_theorems} "
                     f"lemmas={module_lemmas} sha256={ported} "
                     f"accepted_sha256={accepted} "
                     f"changed={'yes' if ported != accepted else 'no'}")
    for module, relative in GENERATED.items():
        lines.append(f"module {module} generated=yes "
                     f"sha256={sha256(out / relative)}")
    return lines, theorems, lemmas


def configuration_lines(out):
    trace = load(out, "configuration-trace/configuration-trace.json")
    r1 = load(out, "r1/reports/runtime.json")
    profile = trace["profile"]
    resources = {resource["id"]: resource for resource in trace["resources"]}
    identities = trace["identities"]
    lines = [
        f"configuration r1_identity={r1['summary']['configuration_identity']}"
        f" resources={profile['resource_count']} "
        f"authorities={profile['authority_count']} "
        f"domains={profile['domain_count']} roots={profile['root_count']} "
        f"leaves_per_root={profile['leaves_per_root']}",
    ]
    for root in trace["roots"]:
        gpas = ",".join(mapping["gpa"] for mapping in root["mappings"])
        lines.append(f"configuration root {root['domain']} "
                     f"hgatp={root['hgatp']} gpas={gpas}")
    for label, key in (("management_private", "management_private_frame"),
                       ("protected_private", "protected_private_frame"),
                       ("shared", "shared_frame")):
        frame = resources[identities[key]]
        lines.append(f"configuration backing {label} frame={frame['id']} "
                     f"base={frame['base']}")
    lines.append(f"configuration r5_binding="
                 f"{trace['r5_cross_check']['schema']} dynamic="
                 f"{trace['r5_cross_check']['dynamic_isolation_cross_check']}")
    return lines


def delta_lines():
    lines = []
    for path, rules in PORT.RULES.items():
        for kind, old, _new, count, why in rules:
            what = kind if old is None else \
                "exact " + old.splitlines()[0].strip()[:48]
            lines.append(f"delta {path} | {what} | x{count} | {why}")
    return lines


def build(root):
    out = root / "build" / "k3-b4" / "r7"
    status, reasons = proof_status(out, out / "port", root)
    stages, failed = stage_status(out)
    lines = ["schema=be-k3-b4-r7-report-v1",
             "scope=bounded-exact-byte-proof-over-b2-k3-images"]
    lines += [f"accepted_{name}={commit}" for name, commit in ACCEPTED.items()]
    lines.append(f"accepted_r7_measured {ACCEPTED_COUNTS}")
    lines += stages
    mismatched, errors = [], []
    try:
        images, totals, records = image_lines(out)
        cuts, mismatched = cut_point_lines(root, records)
        modules, theorems, lemmas = inventory_lines(out)
        configuration = configuration_lines(out)
        lines += images
        lines.append(
            f"totals images=2 symbols={totals['symbols']} "
            f"words={totals['words']} words32={totals['words4']} "
            f"words16={totals['words2']} targets={totals['targets']} "
            f"alloc_sections={totals['alloc_sections']} "
            f"modules={len(MODULES)} theorems={theorems} lemmas={lemmas}")
        lines += cuts + modules + configuration
        lines.append(
            f"port b2_manifest_sha256="
            f"{sha256(root / 'build/k3-b2/port/PORT-MANIFEST.txt')} "
            f"b4_manifest_sha256={sha256(out / 'port/PORT-MANIFEST.txt')} "
            f"b4_files={len(PORT.PINS)} b4_rules="
            f"{sum(len(rules) for rules in PORT.RULES.values())}")
    except (OSError, KeyError, ValueError, IndexError) as error:
        errors.append(f"missing or malformed artefact: {error}")
    lines += delta_lines()
    lines.append(f"claim {CLAIM}")
    lines += [f"cut_point_ledger {i} | {b} | {s}" for i, b, s in CUT_POINTS]
    lines += [f"trusted_boundary {item}" for item in TRUSTED]
    lines += [f"k3_ledger {i} | {b} | {s}" for i, b, s in K3_LEDGER]
    lines += [f"k3_ledger_note {note}" for note in K3_LEDGER_NOTES]
    lines.append(f"plan_obligation_substitution {PLAN_SUBSTITUTION}")
    lines += [f"non_claim {item}" for item in NON_CLAIMS]
    try:
        lines += tool_lines(root)
    except OSError as error:
        errors.append(f"tool identity: {error}")
    lines.append("hardware=NOT-RUN qemu=NOT-RUN board_claim=none")
    lines += [f"report_error {error}" for error in errors]
    lines += [f"proof_reason {reason}" for reason in reasons]
    lines.append(f"proof={status}")
    ok = status == "PASS" and not failed and not mismatched and not errors
    lines.append(f"BE_B4_R7_REPORT: {'PASS' if ok else 'FAIL'} "
                 f"proof={status} stages_failed={len(failed)} "
                 f"cut_point_mismatches={len(mismatched)} "
                 f"report_errors={len(errors)}")
    return lines, ok


def self_test():
    """Synthetic proof directories: absent, broken, and complete."""
    root = HERE.parents[3]
    scratch = root / "build" / "k3-b4" / "r7" / "report-self-test"
    shutil.rmtree(scratch, ignore_errors=True)
    port = scratch / "port"
    proof_sources = port / "tests" / "r7" / "proof"
    proof_sources.mkdir(parents=True)
    ported = PORT.derive(root)
    for module in PORT.PROOF_MODULES:
        (proof_sources / f"{module}.v").write_text(
            ported[f"tests/r7/proof/{module}.v"][0])
    out = scratch
    results = []
    try:
        results.append(("absent", proof_status(out, port, root)[0],
                        "NOT-RUN"))
        proof = out / "proof-build"
        proof.mkdir()
        (out / "generated").mkdir()
        (out / "configuration-trace").mkdir()
        digests = []
        for module in MODULES:
            if module in GENERATED:
                text = f"(* synthetic {module} *)\n"
                (out / GENERATED[module]).write_text(text)
                digests.append(f"{hashlib.sha256(text.encode()).hexdigest()}"
                               f"  {out / GENERATED[module]}")
            else:
                text = (proof_sources / f"{module}.v").read_text()
            (proof / f"{module}.v").write_text(text)
            (proof / f"{module}.vo").write_bytes(b"synthetic")
        (out / "proof-inputs.sha256").write_text("\n".join(digests) + "\n")
        (proof / "proof-compile.log").write_text(
            "Closed under the global context\n")
        check = [f"Checking library: {module}" for module in MODULES]
        check.append("Modules were successfully checked")
        (proof / "proof-check.log").write_text("\n".join(check) + "\n")
        results.append(("complete", proof_status(out, port, root)[0],
                        "PASS"))
        breakages = [
            ("open-assumptions", "proof-compile.log",
             "Axioms:\nfree_lunch : False\n"),
            ("check-failed", "proof-check.log", "Error: bad object\n"),
            ("admitted", "Switch.v", None),
            ("stale-input", "ExactInput.v", "(* different *)\n"),
            ("missing-object", "Trap.vo", ""),
        ]
        for name, filename, content in breakages:
            target = proof / filename
            saved = target.read_bytes()
            if content is None:
                target.write_text(saved.decode().replace(
                    "Proof. vm_compute. reflexivity. Qed.", "Admitted.", 1))
            else:
                target.write_text(content)
            results.append((name, proof_status(out, port, root)[0], "FAIL"))
            target.write_bytes(saved)
            for module in MODULES:
                (proof / f"{module}.vo").write_bytes(b"synthetic")
        results.append(("restored", proof_status(out, port, root)[0],
                        "PASS"))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    wrong = [f"{name}={got} (want {want})" for name, got, want in results
             if got != want]
    if wrong:
        raise ReportError(f"self-test: {', '.join(wrong)}")
    return len(results)


def main(argv):
    try:
        if len(argv) == 2 and argv[1] == "--self-test":
            cases = self_test()
            print(f"BE_B4_R7_REPORT_SELF_TEST: PASS cases={cases} "
                  "not-run=1 fail=5 pass=2")
            return 0
        if len(argv) != 2:
            print(__doc__)
            return 2
        lines, ok = build(pathlib.Path(argv[1]).resolve())
    except (ReportError, OSError, ValueError) as error:
        print(f"BE_B4_R7_REPORT: FAIL {error}")
        return 1
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
