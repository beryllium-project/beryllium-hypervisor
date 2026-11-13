#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""The firmware's own tests (planning/mvp-m11-plan.md, M11-6).

  fwtest.py run --firmware-dir DIR --payload ELF --qemu QEMU --dtc DTC
                --nm NM --out DIR [--mode plain|smepmp|both] [ROW ...]
  fwtest.py list

Purpose: run each test row on QEMU's k3-like machine (the machine and CPU
of tests/run-qemu.sh), with eight harts, on the patched firmware, in plain
PMP and in Smepmp mode, and judge it from what the QEMU oracle
(tests/qemu_oracle.py) reads with the machine stopped: every hart's PMP
registers, menvcfg, mseccfg and pc, the payload's step results and entry
records, and the firmware's table of per-hart commit records, found by its
symbol in the firmware's ELF. The console gives the firmware's own lines:
its boot banner, its domain dump, and its commit report.

Each row writes a device tree of its own from the tree that the locked
QEMU dumps for the same machine and CPU, compiled by the locked dtc, and a
script of steps for the payload (fwtest.h). A row passes when every
expectation holds; each failure is a named finding.

Trust: test-only. It writes only under --out. It starts QEMU only through
the oracle, with no network and no display, and never stops a run at a
fixed time where the payload runs: hart 0 ends those with its own
shutdown, after waits bounded in one place (WAIT_TICKS, RUN_SECONDS).

Scope: the firmware additions of the patch series in firmware/patches
and the base code that they rely on. The expected PMP tables are computed
here, independently of the firmware, from the regions that the firmware
prints for each domain, after those regions are checked against the tree.
"""

import argparse
import dataclasses
import json
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
MVP = HERE.parent.parent
sys.path.insert(0, str(MVP / "tests"))
import qemu_oracle as oracle  # noqa: E402

# Every bound on waiting, in one place. QEMU's virt timer runs at 10 MHz.
TIMEBASE_HZ = 10_000_000
WAIT_TICKS = 60 * TIMEBASE_HZ       # a payload's wait for another hart
SETTLE_TICKS = TIMEBASE_HZ // 5     # a pause for another hart to reach a
                                    # state it cannot report (stopped in
                                    # M-mode, or halfway through a call)
RUN_SECONDS = 300                   # a run whose payload ends it
NO_PAYLOAD_SECONDS = 30             # a run whose payload never starts
SETTLE_SECONDS = 2                  # after the line that ends such a run


def read_layout():
    values = {}
    for line in (HERE / "fwtest.h").read_text(encoding="utf-8").splitlines():
        match = re.match(r"#define (FWT_[A-Z0-9_]+)\s+(0x[0-9a-f]+|[0-9]+)\b",
                         line)
        if match:
            values[match.group(1)[4:]] = int(match.group(2), 0)
    return values


L = read_layout()
HARTS = L["HARTS"]
RAM_BASE, RAM_SIZE = 0x80000000, 8 << 30
FIRMWARE_END = 0x80080000

# SBI extensions and functions the steps use
BASE, HSM, IPI, SRST, DBCN = 0x10, 0x48534D, 0x735049, 0x53525354, 0x4442434E
DCOMMIT, TIME, RFENCE, PMU = 0x08004246, 0x54494D45, 0x52464E43, 0x504D55
OK, FAILED, NOT_SUPPORTED, INVALID_PARAM, DENIED = 0, -1, -2, -3, -4
ANY = 0xFFFFFFFF
R, W, X = 0x8, 0x10, 0x20

DIGEST = (0x0123_4567, 0x89AB_CDEF, 0xFEDC_BA98, 0x7654_3210,
          0x0F1E_2D3C, 0x4B5A_6978, 0x8796_A5B4, 0xC3D2_E1F0)

HS, VS, VU = L["MODE_HS"], L["MODE_VS"], L["MODE_VU"]


def state(hart, word=0):
    return L["STATE_BASE"] + hart * L["STATE_STRIDE"] + 8 * word


def work(page):
    return L["WORK_BASE"] + page * 0x1000


def msg(hart):
    return state(hart) + L["MSG_BYTE_OFF"]


MSG_LEN = len("fwtest: console\n")


def k3_like():
    text = (MVP / "tests" / "run-qemu.sh").read_text(encoding="utf-8")
    machine = re.search(r"^k3_machine='([^']+)'$", text, re.M).group(1)
    cpu = re.search(r"^k3_cpu='([^']+)'$", text, re.M).group(1)
    return machine, cpu


# ------------------------------------------------------------- the trees

@dataclasses.dataclass(frozen=True)
class Region:
    label: str
    base: int
    order: int


TEXT = Region("text", L["TEXT_BASE"], L["TEXT_ORDER"])
SCRIPT = Region("script", L["SCRIPT_BASE"], L["SCRIPT_ORDER"])
STATES = Region("states", L["STATE_BASE"], 16)


def STATE(hart):
    return Region(f"state{hart}", state(hart), L["STATE_ORDER"])


def WORK(page, order=12, offset=0, label=None):
    return Region(label or f"work{page}", work(page) + offset, order)


@dataclasses.dataclass
class Domain:
    name: str
    harts: list
    boot: int
    order: int
    regions: list
    allow: list | None = None
    reset: bool = False
    inherit_all: bool = False
    next_arg1: int = 0
    next_addr: int = TEXT.base


def own(hart):
    return [(TEXT, R | X), (SCRIPT, R), (STATE(hart), R | W)]


CONSOLE_WRITE = (DBCN, 0, ANY, 0)
SHUTDOWN_ONLY = (SRST, 0, 0, 0)
COMMIT_CALL = (DCOMMIT, 0, ANY, 0)


def standard():
    """D-6's shape: a boot domain for harts 0 to 2, one narrow domain for
    each of them, and the other harts parked."""
    return {
        "boot": Domain("boot", [0, 1, 2], 0, 1, [], inherit_all=True,
                       reset=True, next_arg1=0x100),
        "h0": Domain("h0", [0], 0, 10, own(0) + [(STATES, R)],
                     allow=[CONSOLE_WRITE, SHUTDOWN_ONLY], reset=True,
                     next_arg1=0x200),
        "h1": Domain("h1", [1], 1, 11, own(1), allow=[], next_arg1=0x201),
        "h2": Domain("h2", [2], 2, 12, own(2), allow=[], next_arg1=0x202),
        "park": Domain("park", [3, 4, 5, 6, 7], 0, 100, [(WORK(15), X)],
                       next_arg1=0x300, next_addr=work(15)),
    }


def cpu_ref(hart):
    return f"&{{/cpus/cpu@{hart}}}"


def tree_source(base_name, domains, digest, extra=""):
    regions = {}
    for dom in domains:
        for region, _ in dom.regions:
            regions[region.label] = region
    lines = [f'/include/ "{base_name}"', "/ {", "\tchosen {",
             "\t\t/delete-property/ rng-seed;",
             "\t\topensbi-config {",
             '\t\t\tcompatible = "opensbi,config";',
             f"\t\t\tcold-boot-harts = <{cpu_ref(0)}>;", "\t\t};",
             "\t\topensbi-domains {",
             '\t\t\tcompatible = "opensbi,domain,config";']
    if digest is not None:
        lines.append("\t\t\tconfig-digest = <" +
                     " ".join(f"0x{cell:08x}" for cell in digest) + ">;")
    for label, region in sorted(regions.items()):
        lines.append(
            f"\t\t\t{label}: {label} {{ compatible = "
            f'"opensbi,domain,memregion"; base = <0x{region.base >> 32:x} '
            f"0x{region.base & 0xFFFFFFFF:x}>; order = <{region.order}>; }};")
    for dom in domains:
        lines += [f"\t\t\t{dom.name} {{",
                  '\t\t\t\tcompatible = "opensbi,domain,instance";',
                  "\t\t\t\tpossible-harts = <" +
                  " ".join(cpu_ref(h) for h in dom.harts) + ">;"]
        if dom.regions:
            lines.append("\t\t\t\tregions = " + ", ".join(
                f"<&{region.label} 0x{access:x}>"
                for region, access in dom.regions) + ";")
        if dom.inherit_all:
            lines.append('\t\t\t\troot-regions-inheritance = "all";')
        lines += [f"\t\t\t\tboot-hart = <{cpu_ref(dom.boot)}>;",
                  f"\t\t\t\tnext-addr = <0x{dom.next_addr >> 32:x} "
                  f"0x{dom.next_addr & 0xFFFFFFFF:x}>;",
                  f"\t\t\t\tnext-arg1 = <0x0 0x{dom.next_arg1:x}>;",
                  "\t\t\t\tnext-mode = <0x1>;",
                  f"\t\t\t\tinit-order = <{dom.order}>;"]
        if dom.reset:
            lines.append("\t\t\t\tsystem-reset-allowed;")
        if dom.allow is not None:
            cells = " ".join(f"0x{value:x}" for entry in dom.allow
                             for value in entry)
            lines.append(f"\t\t\t\tecall-allowlist = <{cells}>;"
                         if cells else "\t\t\t\tecall-allowlist;")
        lines.append("\t\t\t};")
    lines += [extra, "\t\t};", "\t};", "};", ""]
    return "\n".join(lines)


# ------------------------------------------------------------- the steps

def step(op, *operands, mode=HS):
    words = [L[f"OP_{op}"] | (mode << 8)] + list(operands)
    return words + [0] * (8 - len(words))


def sbi(ext, fid, a0=0, a1=0, a2=0):
    return step("SBI", ext, fid, a0, a1, a2)


COMMIT = sbi(DCOMMIT, 0)
SHUTDOWN = sbi(SRST, 0, 0, 0)


def digest_word(index):
    return sbi(DCOMMIT, 1, index)


def hsm_start(hart):
    return sbi(HSM, 0, hart, TEXT.base, 0x100 + hart)


def hsm_status(hart):
    return sbi(HSM, 2, hart)


def send_ipi(hart):
    return sbi(IPI, 0, 1 << hart, 0)


def wait_word(address, value=1):
    return step("WAIT", address, value, WAIT_TICKS)


def wait_flag(hart, value=1):
    return wait_word(state(hart, L["ST_FLAG"]), value)


def wait_done(hart):
    return wait_word(state(hart, L["ST_DONE"]), 1)


def set_flag(hart, value=1):
    return step("STORE", state(hart, L["ST_FLAG"]), value)


def load(address, mode=HS, width=8):
    return step("LOAD", address, width, mode=mode)


def store(address, value, mode=HS):
    return step("STORE", address, value, mode=mode)


def fetch(address, argument=0, mode=HS):
    return step("FETCH", address, argument, mode=mode)


def cbo(address, mode=HS):
    return step("CBO", address, mode=mode)


def amo(address, addend=1, mode=HS):
    return step("AMO", address, addend, mode=mode)


def console(length, address, a2=0):
    return step("CONSOLE", length, address, a2)


def csrw(csr, value):
    return step("CSRW", L[f"CSR_{csr}"], value)


def csrr(csr):
    return step("CSRR", L[f"CSR_{csr}"])


def delay(ticks):
    return step("DELAY", ticks)


def suspend(kind, ticks):
    return step("SUSPEND", kind, ticks)


def script_image(scripts):
    data = bytearray(L["SCRIPT_STRIDE"] * HARTS)
    for hart, steps in scripts.items():
        if len(steps) > L["STEPS_MAX"]:
            raise SystemExit(f"hart {hart}: too many steps")
        offset = hart * L["SCRIPT_STRIDE"]
        data[offset:offset + 8] = len(steps).to_bytes(8, "little")
        for number, words in enumerate(steps):
            at = offset + 8 * (L["STEP_OFF"] + number * L["STEP_WORDS"])
            for index, word in enumerate(words):
                data[at + 8 * index:at + 8 * index + 8] = \
                    (word & (1 << 64) - 1).to_bytes(8, "little")
    return bytes(data)


# ------------------------------------------------------------- a row

@dataclasses.dataclass
class Case:
    name: str
    domains: dict
    scripts: dict
    digest: tuple | None = DIGEST
    pages: dict = dataclasses.field(default_factory=dict)
    final: dict = dataclasses.field(default_factory=dict)
    payload: bool = True
    end_line: str = ""
    cpu_extra: str = ""
    extra_dts: str = ""
    witness: dict = dataclasses.field(default_factory=dict)
    report: bool = True
    boot_print: bool = True
    check: object = None
    notes: list = dataclasses.field(default_factory=list)


class Findings:
    def __init__(self):
        self.items = []

    def expect(self, condition, text):
        if not condition:
            self.items.append(text)
        return condition

    def equal(self, seen, wanted, text):
        return self.expect(seen == wanted,
                           f"{text}: {fmt(seen)}, expected {fmt(wanted)}")


def fmt(value):
    if isinstance(value, int):
        return hex(value) if value > 9 or value < -9 else str(value)
    return repr(value)


def signed(value):
    return value - (1 << 64) if value & (1 << 63) else value


@dataclasses.dataclass
class Hart:
    entries: list
    results: list
    done: int
    flag: int
    magic: int
    pc: int
    pmpcfg: list
    pmpaddr: list
    menvcfg: int | None
    mseccfg: int | None
    record: dict


RECORD_FIELDS = ("committed", "pmp_faults", "blocked_calls", "failed_calls",
                 "menvcfg", "mseccfg")
RECORD_WORDS = 24


def table_address(nm, elf):
    out = subprocess.run([nm, str(elf)], capture_output=True, text=True,
                         check=True).stdout
    match = re.search(r"^([0-9a-f]+) [BbDd] sbi_dcommit_harts$", out, re.M)
    if not match:
        raise SystemExit("sbi_dcommit_harts is not in the firmware's ELF")
    return RAM_BASE + int(match.group(1), 16)


def words_for(case, table):
    words = []
    for hart in range(HARTS):
        for index in range(RECORD_WORDS):
            words.append(oracle.NamedWord(f"t{hart}-{index}",
                                          table + 8 * (hart * RECORD_WORDS
                                                       + index), None))
        count = len(case.scripts.get(hart, []))
        wanted = list(range(8))
        wanted += [L["ENTRY_OFF"] + i for i in
                   range(L["ENTRIES_MAX"] * L["ENTRY_WORDS"])]
        wanted += [L["RES_OFF"] + i for i in range(count * L["RES_WORDS"])]
        for word in wanted:
            words.append(oracle.NamedWord(f"s{hart}-{word}",
                                          state(hart, word), None))
    for name, address in sorted(case.witness.items()):
        words.append(oracle.NamedWord(f"w-{name}", address, None))
    return tuple(words)


def decode(case, record):
    values = {item["name"]: int(item["value"], 16) for item in record["words"]}
    harts = []
    for hart in range(HARTS):
        rec_words = [values[f"t{hart}-{i}"] for i in range(RECORD_WORDS)]
        rec = dict(zip(RECORD_FIELDS, rec_words[:6]))
        cfg = rec_words[6].to_bytes(8, "little") + \
            rec_words[7].to_bytes(8, "little")
        rec["pmpcfg"] = list(cfg)
        rec["pmpaddr"] = rec_words[8:24]
        st = {word: values.get(f"s{hart}-{word}", 0)
              for word in range(L["RES_OFF"] + L["STEPS_MAX"] *
                                L["RES_WORDS"])}
        entries = []
        for number in range(min(st[L["ST_ENTRIES"]], L["ENTRIES_MAX"])):
            base = L["ENTRY_OFF"] + number * L["ENTRY_WORDS"]
            entries.append([st[base + i] for i in range(L["ENTRY_WORDS"])])
        results = []
        for number in range(len(case.scripts.get(hart, []))):
            base = L["RES_OFF"] + number * L["RES_WORDS"]
            results.append({
                "status": st[base + L["RES_STATUS"]],
                "error": signed(st[base + L["RES_ERROR"]]),
                "value": st[base + L["RES_VALUE"]],
                "cause": st[base + L["RES_CAUSE"]],
                "tval": st[base + L["RES_TVAL"]],
                "extra": st[base + L["RES_EXTRA"]],
            })
        regs = record["harts"][hart]
        cfg = int(regs["pmpcfg0"], 16).to_bytes(8, "little") + \
            int(regs["pmpcfg2"], 16).to_bytes(8, "little")
        harts.append(Hart(
            entries=entries, results=results, done=st[L["ST_DONE"]],
            flag=st[L["ST_FLAG"]], magic=st[L["ST_MAGIC"]],
            pc=int(regs["pc"], 16), pmpcfg=list(cfg),
            pmpaddr=[int(value, 16) for value in regs["pmpaddr"]],
            menvcfg=(int(regs["menvcfg"], 16)
                     if regs["menvcfg"].startswith("0x") else None),
            mseccfg=(int(regs["mseccfg"], 16)
                     if regs["mseccfg"].startswith("0x") else None),
            record=rec))
    witness = {name: values[f"w-{name}"] for name in case.witness}
    return harts, witness


# ------------------------------------------------------------- the console

DUMP = re.compile(r"^Domain(\d+) (Name|Region(\d+)|HARTs|Init Order|Boot HART)"
                  r"\s*: (.*)$")
REGION = re.compile(r"^0x([0-9a-f]{16})-0x([0-9a-f]{16}) M: (\([A-Z,]*\)) "
                    r"S/U: (\([A-Z,]*\))$")
REPORT = re.compile(r"^Domain commit hart(\d+): (.*)$")


def parse_console(text):
    domains, index_names = {}, {}
    report, banner = {}, {}
    for line in text.splitlines():
        line = line.rstrip("\r")
        match = DUMP.match(line)
        if match:
            index, kind, region, value = match.groups()
            index = int(index)
            if kind == "Name":
                index_names[index] = value
                domains[value] = {"regions": [], "index": index}
            elif kind.startswith("Region") and index in index_names:
                fields = REGION.match(value)
                if fields:
                    domains[index_names[index]]["regions"].append(
                        (int(fields.group(1), 16), int(fields.group(2), 16),
                         fields.group(3), fields.group(4)))
            elif index in index_names:
                domains[index_names[index]][kind] = value
            continue
        match = REPORT.match(line)
        if match:
            report.setdefault(int(match.group(1)), []).append(match.group(2))
            continue
        if " : " in line:
            key, _, value = line.partition(" : ")
            banner.setdefault(key.strip(), value.strip())
    return domains, report, banner


# ------------------------------------------------------------- PMP tables

PERMS = {"R": 1, "W": 2, "X": 4}


def perms(text):
    value = 0
    for flag in text.strip("()").split(","):
        value |= PERMS.get(flag, 0)
    return value


def expected_table(regions, smepmp, count=16):
    """The PMP entries for a domain's regions in printed order: cfg bytes
    and NAPOT addresses, independently of the firmware."""
    cfg, addr = [0] * count, [None] * count
    for number, (start, end, mflags, suflags) in enumerate(regions):
        size = (end - start + 1) & ((1 << 64) - 1)
        order = 64 if size == 0 else size.bit_length() - 1
        index = number + 1 if smepmp else number
        if index >= count:
            continue
        if not smepmp:
            value = perms(suflags)
        elif suflags == "()" and mflags != "()":
            value = 0x80 | perms(mflags)
        elif mflags == "()" or not perms(mflags):
            value = perms(suflags)
        else:
            raise SystemExit("a shared region in a domain under test")
        cfg[index] = value | (0x10 if order == 2 else 0x18)
        addr[index] = ((1 << 64) - 1 if order == 64 else
                       (start >> 2) | ((1 << (order - 3)) - 1))
    return cfg, addr


def compare_table(findings, what, cfg, addr, want_cfg, want_addr):
    for index in range(16):
        findings.equal(cfg[index], want_cfg[index],
                       f"{what} pmp{index}cfg")
        if want_cfg[index] & 0x18:
            findings.equal(addr[index], want_addr[index],
                           f"{what} pmpaddr{index}")


def region_set(regions):
    return sorted(regions)


def tree_regions(dom, root_regions):
    wanted = []
    for region, access in dom.regions:
        su = ",".join(flag for flag, bit in (("R", R), ("W", W), ("X", X))
                      if access & bit)
        size = 1 << region.order
        wanted.append((region.base, region.base + size - 1, "()",
                       f"({su})"))
    for start, end, mflags, suflags in root_regions:
        if suflags == "()":
            wanted.append((start, end, mflags, suflags))
    return sorted(wanted)


# ------------------------------------------------------------- a run

class Runner:
    def __init__(self, args):
        self.args = args
        self.machine, self.cpu = k3_like()
        self.firmware = pathlib.Path(args.firmware_dir) / \
            "platform/generic/firmware/fw_dynamic.bin"
        self.table = table_address(args.nm, pathlib.Path(args.firmware_dir) /
                                   "platform/generic/firmware/fw_dynamic.elf")
        self.out = pathlib.Path(args.out)
        self.bases = {}
        self.measured = {}

    def measure(self, mode):
        """Root's M-mode-only regions and the PMP entry count that the
        firmware prints for this machine and mode (F13's budget)."""
        if mode in self.measured:
            return self.measured[mode]
        case = Case("measure", standard(), {0: [SHUTDOWN]}, report=False)
        directory = self.run_case(case, mode)
        text = (directory / "console.log").read_bytes().decode("utf-8",
                                                                "replace")
        domains, _, banner = parse_console(text)
        inherited = [region for region in domains["root"]["regions"]
                     if region[3] == "()"]
        count = int(banner["Boot HART PMP Count"])
        self.measured[mode] = (len(inherited), count)
        return self.measured[mode]

    def cpu_for(self, mode, case):
        return self.cpu + (",smepmp=true" if mode == "smepmp" else "") + \
            case.cpu_extra

    def base_tree(self, cpu):
        if cpu in self.bases:
            return self.bases[cpu]
        name = f"base-{len(self.bases)}"
        dtb = self.out / f"{name}.dtb"
        subprocess.run([self.args.qemu, "-machine",
                        f"{self.machine},dumpdtb={dtb}", "-cpu", cpu,
                        "-smp", str(HARTS), "-m", "8G", "-display", "none",
                        "-bios", str(self.firmware)],
                       check=True, capture_output=True)
        subprocess.run([self.args.dtc, "-q", "-I", "dtb", "-O", "dts",
                        "-o", str(self.out / f"{name}.dts"), str(dtb)],
                       check=True)
        self.bases[cpu] = f"{name}.dts"
        return self.bases[cpu]

    def run(self, case, mode):
        directory = self.run_case(case, mode)
        return self.judge(case, mode, directory)

    def run_case(self, case, mode):
        directory = self.out / mode / case.name
        directory.mkdir(parents=True)
        cpu = self.cpu_for(mode, case)
        base = self.base_tree(cpu)
        shutil.copyfile(self.out / base, directory / base)
        source = tree_source(base, list(case.domains.values()), case.digest,
                             case.extra_dts)
        (directory / "test.dts").write_text(source, encoding="utf-8")
        subprocess.run([self.args.dtc, "-q", "-I", "dts", "-O", "dtb",
                        "-i", str(directory), "-o",
                        str(directory / "test.dtb"),
                        str(directory / "test.dts")], check=True)
        (directory / "script.bin").write_bytes(script_image(case.scripts))
        argv = [self.args.qemu, "-machine", self.machine, "-cpu", cpu,
                "-smp", str(HARTS), "-m", "8G", "-bios", str(self.firmware),
                "-dtb", str(directory / "test.dtb"),
                "-kernel", self.args.payload,
                "-device", f"loader,file={directory / 'script.bin'},"
                f"addr=0x{L['SCRIPT_BASE']:x},force-raw=on"]
        for page, data in sorted(case.pages.items()):
            path = directory / f"page{page}.bin"
            path.write_bytes(data)
            argv += ["-device",
                     f"loader,file={path},addr=0x{work(page):x},force-raw=on"]
        argv += ["-display", "none", "-serial",
                 f"file:{directory / 'console.log'}", "-no-reboot"]
        config = oracle.OracleConfig(
            HARTS, "k3-like", False, "readable", "readable",
            "readable" if mode == "smepmp" else "absent", RAM_BASE, RAM_SIZE,
            words_for(case, self.table))
        record = directory / "oracle.json"
        with open(directory / "qemu.txt", "w", encoding="utf-8") as output:
            process = oracle.OracleProcess.launch(
                argv, config, str(record), stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT)
            if case.payload:
                end = process.wait_end(RUN_SECONDS)
                outcome = process.finish(
                    end=end,
                    harness_reason=None if end else "run-limit")
            else:
                end = wait_for_line(process, directory / "console.log",
                                    case.end_line)
                outcome = process.finish(end=end, harness_reason="fixed-time",
                                         harness_pass=True)
        (directory / "outcome.txt").write_text(
            f"{'PASS' if outcome.passed else 'FAIL'} {outcome.detail}\n",
            encoding="utf-8")
        return directory

    def judge(self, case, mode, directory):
        findings = Findings()
        outcome = (directory / "outcome.txt").read_text(encoding="utf-8")
        if not findings.expect(outcome.startswith("PASS"),
                               f"oracle: {outcome.strip()}"):
            return findings.items
        record = directory / "oracle.json"
        data = json.loads(record.read_text(encoding="utf-8"))
        text = (directory / "console.log").read_bytes().decode(
            "utf-8", "replace")
        harts, witness = decode(case, data)
        domains, report, banner = parse_console(text)
        view = View(case, mode, harts, witness, domains, report, banner,
                    text)
        judge_common(view, findings)
        if case.check:
            case.check(view, findings)
        (directory / "findings.txt").write_text(
            "".join(f"{item}\n" for item in findings.items) or "none\n",
            encoding="utf-8")
        if case.notes:
            (directory / "notes.txt").write_text(
                "".join(f"{note}\n" for note in case.notes),
                encoding="utf-8")
        return findings.items


def wait_for_line(process, console, line):
    import time
    deadline = time.monotonic() + NO_PAYLOAD_SECONDS
    while time.monotonic() < deadline:
        end = process.poll_end()
        if end is not None:
            return end
        if console.exists() and line and line.encode() in \
                console.read_bytes():
            time.sleep(SETTLE_SECONDS)
            return None
        time.sleep(0.2)
    return None


@dataclasses.dataclass
class View:
    case: Case
    mode: str
    harts: list
    witness: dict
    domains: dict
    report: dict
    banner: dict
    text: str

    @property
    def smepmp(self):
        return self.mode == "smepmp"

    def result(self, hart, number):
        return self.harts[hart].results[number]


# ------------------------------------------------------------- judgement

def judge_common(view, findings):
    case = view.case
    if case.boot_print:
        findings.equal(view.banner.get("Boot HART ID"), "0", "Boot HART ID")
    if not case.payload:
        return
    findings.equal(view.banner.get("Standard SBI Extensions"),
                   "ipi,base,hsm,srst,dbcn", "standard SBI extensions")
    findings.equal(view.banner.get("Experimental SBI Extensions"),
                   "dcommit", "experimental SBI extensions")
    root = view.domains.get("root", {}).get("regions", [])
    # The firmware's regions of each domain are the tree's plus root's
    # M-mode-only ones, so the expected tables below rest on the tree.
    for dom in case.domains.values():
        if dom.inherit_all:
            continue
        printed = view.domains.get(dom.name)
        if not findings.expect(printed is not None,
                               f"domain {dom.name} is not in the dump"):
            continue
        findings.equal(region_set(printed["regions"]),
                       tree_regions(dom, root), f"domain {dom.name} regions")
    digest = "".join(f"{cell:08x}" for cell in case.digest) \
        if case.digest else None
    if digest:
        findings.equal(view.banner.get("Domain commit digest"), digest,
                       "printed digest")
    for hart, final in case.final.items():
        judge_final(view, findings, hart, final)
    for hart in range(HARTS):
        rec = view.harts[hart].record
        if hart not in case.final:
            findings.equal(rec["committed"], 0, f"hart{hart} committed")
        judge_report(view, findings, hart)


def judge_final(view, findings, hart, final):
    """final: the domain the hart ends in (None for a hart that never
    leaves the firmware, "wide" for one that stays in the boot domain or
    root), whether it is committed, whether it is stopped in M-mode, and
    its expected counts."""
    h = view.harts[hart]
    domain = final.get("domain")
    counts = final.get("counts", (0, 0, 0))
    rec = h.record
    for field, wanted in zip(("pmp_faults", "blocked_calls", "failed_calls"),
                             counts):
        findings.equal(rec[field], wanted, f"hart{hart} {field}")
    if domain is None or final.get("in_firmware"):
        findings.expect(RAM_BASE <= h.pc < FIRMWARE_END,
                        f"hart{hart} pc {h.pc:#x} is not in the firmware")
    if domain is None:
        findings.equal(rec["committed"], 0, f"hart{hart} committed")
        findings.equal(h.magic, 0, f"hart{hart} ran the payload")
        return
    if domain.startswith("wide"):
        findings.equal(rec["committed"], 0, f"hart{hart} committed")
        findings.equal((h.menvcfg or 0) >> 4 & 3, 3,
                       f"hart{hart} menvcfg.CBIE")
        return
    committed = final.get("committed", 1)
    findings.equal(rec["committed"], committed, f"hart{hart} committed")
    if not committed:
        return
    printed = view.domains.get(domain)
    if not findings.expect(printed is not None,
                           f"hart{hart}: domain {domain} not printed"):
        return
    cfg, addr = expected_table(printed["regions"], view.smepmp)
    compare_table(findings, f"hart{hart} oracle", h.pmpcfg, h.pmpaddr,
                  cfg, addr)
    if committed:
        compare_table(findings, f"hart{hart} record", rec["pmpcfg"],
                      rec["pmpaddr"], cfg, addr)
        findings.equal(rec["menvcfg"], h.menvcfg, f"hart{hart} record menvcfg")
        findings.equal((h.menvcfg or 0) >> 4 & 3, 0, f"hart{hart} menvcfg.CBIE")
        findings.equal(rec["mseccfg"], h.mseccfg if view.smepmp else 0,
                       f"hart{hart} record mseccfg")
        if view.smepmp:
            findings.expect((h.mseccfg or 0) & 1, f"hart{hart} mseccfg.MML")


def judge_report(view, findings, hart):
    rec = view.harts[hart].record
    lines = view.report.get(hart, [])
    if view.case.digest is None:
        findings.equal(lines, [], f"hart{hart} report lines")
        return
    want = [f"committed={rec['committed']} pmp_faults={rec['pmp_faults']} "
            f"blocked_calls={rec['blocked_calls']} "
            f"failed_calls={rec['failed_calls']}"]
    if rec["committed"]:
        want.append(f"menvcfg=0x{rec['menvcfg']:016x} "
                    f"mseccfg=0x{rec['mseccfg']:016x}")
        want.append("pmpcfg=" + "".join(f"{b:02x}" for b in rec["pmpcfg"]))
        for first in (0, 8):
            want.append(f"pmpaddr{first}=" + ",".join(
                f"0x{value:016x}" for value in rec["pmpaddr"][first:first + 8]))
    if view.case.report:
        findings.equal(lines, want, f"hart{hart} report lines")
    else:
        findings.equal(lines, [], f"hart{hart} report lines")


def expect_steps(view, findings, hart, expected):
    """expected: one tuple per step: (status, error, value) with None for
    a field that is not checked."""
    results = view.harts[hart].results
    for number, wanted in enumerate(expected):
        if number >= len(results):
            findings.expect(False, f"hart{hart} step {number}: no result")
            continue
        got = results[number]
        status, error, value = (list(wanted) + [None, None])[:3]
        findings.equal(got["status"], status,
                       f"hart{hart} step {number} status")
        if error is not None:
            findings.equal(got["error"], error,
                           f"hart{hart} step {number} error")
        if value is not None:
            findings.equal(got["value"], value,
                           f"hart{hart} step {number} value")


S_DONE, S_TRAPPED, S_ENTERED, S_RUNNING = (L["S_DONE"], L["S_TRAPPED"],
                                           L["S_ENTERED"], L["S_RUNNING"])


def expect_trap(view, findings, hart, number, cause, tval=None, virt=None):
    got = view.harts[hart].results[number]
    findings.equal(got["status"], S_TRAPPED, f"hart{hart} step {number} trap")
    findings.equal(got["cause"], cause, f"hart{hart} step {number} cause")
    if tval is not None:
        findings.equal(got["tval"], tval, f"hart{hart} step {number} stval")
    if virt is not None:
        findings.equal(bool(got["extra"] & 0x80), virt,
                       f"hart{hart} step {number} hstatus.SPV")


# ------------------------------------------------------------- the rows

ROWS = {}


def row(name, modes=("plain", "smepmp")):
    def register(function):
        ROWS[name] = (function, modes)
        return function
    return register


def parked(final):
    for hart in range(3, HARTS):
        final.setdefault(hart, {"domain": None})
    return final


def digest_value(index):
    return DIGEST[2 * index] << 32 | DIGEST[2 * index + 1]


def d6(name, control_first):
    """D-6's sequence: the boot code on hart 0 starts harts 1 and 2, each
    hart commits to its own narrow domain, in either order, and hart 0
    ends the run from its narrow domain."""
    s0 = [sbi(BASE, 0), sbi(BASE, 3, DCOMMIT)]
    s0 += [digest_word(index) for index in range(5)]
    s0 += [hsm_status(1), hsm_status(2), hsm_status(3), send_ipi(3),
           hsm_start(1), hsm_start(2)]
    if control_first:
        s0 += [COMMIT, wait_flag(1), wait_flag(2)]
    else:
        s0 += [wait_flag(1), wait_flag(2), hsm_status(1), send_ipi(1),
               hsm_start(3), COMMIT]
    s0 += [console(MSG_LEN, msg(0)), wait_done(1), wait_done(2), SHUTDOWN]

    def follower(hart):
        # Control first: hart 0 has come back in at its narrow domain
        steps = [wait_word(state(0, L["ST_ENTRIES"]), 2)] \
            if control_first else []
        return steps + [
            csrw("STIMECMP", 0x7000_0000_0000_0000 + hart),
            csrw("HGATP", 8 << 60 | hart << 44 | 0x80000),
            csrw("VSATP", 8 << 60 | 0x1000 + hart),
            csrr("STIMECMP"), csrr("HGATP"), csrr("VSATP"), COMMIT,
            csrr("STIMECMP"), csrr("HGATP"), csrr("VSATP"), set_flag(hart)]

    def check(view, findings):
        head = [(S_DONE, OK, 0x3000000), (S_DONE, OK, 1)]
        head += [(S_DONE, OK, digest_value(i)) for i in range(4)]
        head += [(S_DONE, INVALID_PARAM), (S_DONE, OK, 1), (S_DONE, OK, 1),
                 (S_DONE, INVALID_PARAM), (S_DONE, INVALID_PARAM),
                 (S_DONE, OK), (S_DONE, OK)]
        if control_first:
            tail = [(S_ENTERED, None, 1), (S_DONE,), (S_DONE,)]
        else:
            tail = [(S_DONE,), (S_DONE,), (S_DONE, INVALID_PARAM),
                    (S_DONE, INVALID_PARAM), (S_DONE, INVALID_PARAM),
                    (S_ENTERED, None, 1)]
        tail += [(S_DONE, OK, MSG_LEN), (S_DONE,), (S_DONE,), (S_RUNNING,)]
        expect_steps(view, findings, 0, head + tail)
        for hart in (0, 1, 2):
            entries = view.harts[hart].entries
            if not findings.equal(len(entries), 2, f"hart{hart} entries"):
                continue
            first, moved = entries
            findings.equal(first[L["EN_A0"]], hart, f"hart{hart} entry a0")
            if hart:
                findings.equal(first[L["EN_A1"]], 0x100 + hart,
                               f"hart{hart} entry a1")
            findings.equal(moved[L["EN_A0"]], hart, f"hart{hart} move a0")
            findings.equal(moved[L["EN_A1"]], 0x200 + hart,
                           f"hart{hart} move a1")
            for word, wanted in (("STVEC", TEXT.base), ("SSCRATCH", 0),
                                 ("SIE", 0), ("SATP", 0)):
                findings.equal(moved[L[f"EN_{word}"]], wanted,
                               f"hart{hart} {word.lower()} after the move")
        for hart in (1, 2):
            pre = [(S_DONE, OK)] if control_first else []
            res = view.harts[hart].results
            base = len(pre)
            expect_steps(view, findings, hart, pre + [
                (S_DONE, OK), (S_DONE, OK), (S_DONE, OK), (S_DONE, OK),
                (S_DONE, OK), (S_DONE, OK), (S_ENTERED, None, 1),
                (S_DONE, OK, res[base + 3]["value"]),
                (S_DONE, OK, res[base + 4]["value"]),
                (S_DONE, OK, res[base + 5]["value"]), (S_DONE,)])
            moved = view.harts[hart].entries[-1]
            findings.equal(moved[L["EN_HGATP"]], res[base + 4]["value"],
                           f"hart{hart} hgatp at the move")
            findings.equal(moved[L["EN_VSATP"]], res[base + 5]["value"],
                           f"hart{hart} vsatp at the move")
            findings.equal(moved[L["EN_STIMECMP"]], res[base + 3]["value"],
                           f"hart{hart} stimecmp at the move")
        times = [view.harts[hart].entries[-1][L["EN_TIME"]]
                 for hart in (0, 1, 2) if len(view.harts[hart].entries) == 2]
        if len(times) == 3:
            first = min(range(3), key=lambda i: times[i])
            findings.equal(first, 0 if control_first else first,
                           "the first hart to resume")
            if not control_first:
                findings.expect(times[0] > max(times[1:]),
                                "hart 0 resumed before harts 1 and 2")

    return Case(name, standard(), {0: s0, 1: follower(1), 2: follower(2)},
                final=parked({0: {"domain": "h0"}, 1: {"domain": "h1"},
                              2: {"domain": "h2"}}),
                check=check)


@row("d6-vs-first")
def d6_vs_first(runner, mode):
    return d6("d6-vs-first", False)


@row("d6-control-first")
def d6_control_first(runner, mode):
    return d6("d6-control-first", True)


def wide_boot(harts=(0, 1, 2)):
    return Domain("boot", list(harts), 0, 1, [], inherit_all=True,
                  reset=True, next_arg1=0x100)


@row("guard-caller")
def guard_caller(runner, mode):
    """Condition 1: a hart in root may not commit; the second commit of a
    committed hart is refused, and counts, its domain listing the call.
    No domain lists hart 0, so it runs in root; n1 allows no reset and
    hart 1 never calls one."""
    domains = {
        "b1": Domain("b1", [1], 1, 1, own(1), next_arg1=0x101),
        "n1": Domain("n1", [1], 1, 2, own(1), allow=[COMMIT_CALL],
                     next_arg1=0x201),
    }
    scripts = {0: [COMMIT, digest_word(0), wait_done(1), SHUTDOWN],
               1: [COMMIT, COMMIT]}

    def check(view, findings):
        expect_steps(view, findings, 0, [(S_DONE, DENIED), (S_DONE, DENIED),
                                         (S_DONE,), (S_RUNNING,)])
        expect_steps(view, findings, 1, [(S_ENTERED, None, 1),
                                         (S_DONE, DENIED)])
        findings.expect("0x0*" in view.domains["root"].get("HARTs", ""),
                        "the dump does not show hart 0 in root")
        findings.equal(view.domains["b1"].get("HARTs"), "0x1*",
                       "b1 harts in the dump")

    return Case("guard-caller", domains, scripts, check=check,
                final=parked({0: {"domain": "wide-root"},
                              1: {"domain": "n1", "counts": (0, 0, 1)},
                              2: {"domain": None}}))


@row("guard-targets")
def guard_targets(runner, mode):
    """Condition 2: a hart with no other domain, and a hart with two."""
    domains = {
        "boot": wide_boot(),
        "n2a": Domain("n2a", [2], 2, 5, own(2), allow=[], next_arg1=0x2a),
        "n2b": Domain("n2b", [2], 2, 6, own(2), allow=[], next_arg1=0x2b),
    }
    scripts = {0: [hsm_start(1), hsm_start(2), wait_done(1), wait_done(2),
                   SHUTDOWN],
               1: [COMMIT], 2: [COMMIT]}

    def check(view, findings):
        for hart in (1, 2):
            expect_steps(view, findings, hart, [(S_DONE, DENIED)])

    return Case("guard-targets", domains, scripts, check=check,
                final=parked({0: {"domain": "wide"}, 1: {"domain": "wide"},
                              2: {"domain": "wide"}}))


@row("guard-domains")
def guard_domains(runner, mode):
    """Condition 3: the other domain boots another hart; condition 4: it
    has no allowlist."""
    domains = {
        "boot": wide_boot(),
        "n1": Domain("n1", [1], 2, 5, own(1), allow=[], next_arg1=0x201),
        "n2": Domain("n2", [2], 2, 6, own(2), next_arg1=0x202),
    }
    scripts = {0: [hsm_start(1), hsm_start(2), wait_done(1), wait_done(2),
                   SHUTDOWN],
               1: [COMMIT], 2: [COMMIT]}

    def check(view, findings):
        for hart in (1, 2):
            expect_steps(view, findings, hart, [(S_DONE, DENIED)])

    return Case("guard-domains", domains, scripts, check=check,
                final=parked({0: {"domain": "wide"}, 1: {"domain": "wide"},
                              2: {"domain": "wide"}}))


@row("filter")
def filter_row(runner, mode):
    """The allowlist: an empty list refuses everything, a listed call with
    an argument above its limit is refused, and each refusal counts."""
    refused1 = [sbi(BASE, 0), hsm_start(3), hsm_status(1), sbi(HSM, 1),
                sbi(HSM, 3, 0, TEXT.base, 0), send_ipi(2),
                console(MSG_LEN, msg(1)), sbi(DBCN, 2, ord("x")), SHUTDOWN,
                COMMIT, digest_word(0), sbi(0x0A000000, 0)]
    refused0 = [sbi(BASE, 0), hsm_status(1), send_ipi(1),
                sbi(DBCN, 2, ord("x")), sbi(DBCN, 1, 8, msg(0), 0),
                sbi(SRST, 0, 1, 0), digest_word(0)]
    scripts = {
        0: [hsm_start(1), hsm_start(2), COMMIT] + refused0 +
           [console(MSG_LEN, msg(0)), wait_flag(1), wait_done(2), SHUTDOWN],
        1: [COMMIT] + refused1 + [set_flag(1)],
        2: [COMMIT],
    }

    def check(view, findings):
        expect_steps(view, findings, 0, [(S_DONE, OK), (S_DONE, OK),
                                         (S_ENTERED,)] +
                     [(S_DONE, DENIED)] * len(refused0) +
                     [(S_DONE, OK, MSG_LEN), (S_DONE,), (S_DONE,),
                      (S_RUNNING,)])
        expect_steps(view, findings, 1, [(S_ENTERED,)] +
                     [(S_DONE, DENIED)] * len(refused1) + [(S_DONE,)])

    return Case("filter", standard(), scripts, check=check,
                final=parked({0: {"domain": "h0",
                                  "counts": (0, len(refused0), 0)},
                              1: {"domain": "h1",
                                  "counts": (0, len(refused1), 0)},
                              2: {"domain": "h2"}}))


@row("console-checks")
def console_checks(runner, mode):
    """F6: the console's own checks of an allowlisted call, each refusal
    counted as a failed call; nothing reaches a page outside the domain."""
    domains = standard()
    domains["h0"].allow = [CONSOLE_WRITE, (DBCN, 1, ANY, 0), SHUTDOWN_ONLY]
    outside = work(5)
    scripts = {0: [COMMIT, console(MSG_LEN, msg(0)), console(16, outside),
                   console((1 << 64) - 16, msg(0)), console(0, outside),
                   console(MSG_LEN, msg(0), 1),
                   sbi(DBCN, 1, 16, outside, 0), SHUTDOWN]}

    def check(view, findings):
        expect_steps(view, findings, 0, [
            (S_ENTERED,), (S_DONE, OK, MSG_LEN), (S_DONE, INVALID_PARAM),
            (S_DONE, INVALID_PARAM), (S_DONE, OK, 0), (S_DONE, FAILED),
            (S_DONE, INVALID_PARAM), (S_RUNNING,)])
        findings.equal(view.witness["outside"], 0x5A5A5A5A5A5A5A5A,
                       "the page outside h0")

    return Case("console-checks", domains, scripts, check=check,
                pages={5: bytes([0x5A]) * 4096},
                witness={"outside": outside},
                final=parked({0: {"domain": "h0", "counts": (0, 0, 4)},
                              1: {"domain": None}, 2: {"domain": None}}))


@row("faults")
def faults(runner, mode):
    """F2: every access outside the domain, from HS, VS and VU alike, comes
    back to HS-mode as an access fault, counted, and changes nothing."""
    outside = work(6)
    script_witness = L["SCRIPT_BASE"] + 7 * L["SCRIPT_STRIDE"] + 0x800
    edge = state(1) + L["STATE_STRIDE"] - 4
    steps1 = [COMMIT, load(outside), store(outside, 1), fetch(outside),
              store(script_witness, 1), load(edge),
              load(outside, VS), store(outside, 2, VS),
              load(outside, VU), store(outside, 3, VU), set_flag(1)]
    scripts = {0: [hsm_start(1), COMMIT, wait_flag(1), SHUTDOWN],
               1: steps1}

    def check(view, findings):
        expect_steps(view, findings, 0, [(S_DONE, OK), (S_ENTERED,),
                                         (S_DONE,), (S_RUNNING,)])
        expect_steps(view, findings, 1, [(S_ENTERED,)])
        expect_trap(view, findings, 1, 1, 5, outside, False)
        expect_trap(view, findings, 1, 2, 7, outside, False)
        expect_trap(view, findings, 1, 3, 1, outside, False)
        expect_trap(view, findings, 1, 4, 7, script_witness, False)
        expect_trap(view, findings, 1, 5, 5, None, False)
        findings.expect(view.result(1, 5)["tval"] in
                        (edge, state(1) + L["STATE_STRIDE"]),
                        "hart1 step 5: the straddling load's stval")
        for number, cause in ((6, 5), (7, 7), (8, 5), (9, 7)):
            expect_trap(view, findings, 1, number, cause, outside, True)
        findings.equal(view.witness["outside"], 0x6666666666666666,
                       "the page outside h1")
        findings.equal(view.witness["script"], 0, "the read-only page")

    return Case("faults", standard(), scripts, check=check,
                pages={6: bytes([0x66]) * 4096},
                witness={"outside": outside, "script": script_witness},
                final=parked({0: {"domain": "h0"},
                              1: {"domain": "h1", "counts": (9, 0, 0)},
                              2: {"domain": None}}))


@row("shared-page")
def shared_page(runner, mode):
    """F1: one page writable by h1, readable by h2 and absent from h0; the
    lowest PMP entry wins where regions overlap; a region finer than a
    page."""
    domains = standard()
    page = WORK(7, label="spage")
    extent = WORK(16, order=16, label="extent")
    inner = WORK(17, label="inner")
    fine = WORK(8, order=3, offset=0x10, label="fine")
    domains["h1"].regions += [(page, R | W), (extent, R | W), (inner, R),
                              (fine, R | W)]
    domains["h2"].regions += [(page, R)]
    scripts = {
        0: [hsm_start(1), hsm_start(2), COMMIT, load(page.base),
            wait_done(1), wait_done(2), SHUTDOWN],
        1: [COMMIT, store(page.base, 0xABC), store(work(16) + 8, 0x16),
            store(inner.base, 0x17), load(inner.base),
            store(fine.base, 0xF1), store(fine.base + 8, 0xF2)],
        2: [COMMIT, wait_word(page.base, 0xABC), load(page.base),
            store(page.base, 0xDEF)],
    }

    def check(view, findings):
        expect_steps(view, findings, 0, [(S_DONE, OK), (S_DONE, OK),
                                         (S_ENTERED,)])
        expect_trap(view, findings, 0, 3, 5, page.base)
        expect_steps(view, findings, 1, [(S_ENTERED,), (S_DONE,), (S_DONE,)])
        expect_trap(view, findings, 1, 3, 7, inner.base)
        findings.equal(view.result(1, 4)["value"], 0x7777777777777777,
                       "hart1 load of the read-only extent")
        findings.equal(view.result(1, 5)["status"], S_DONE,
                       "hart1 store into the fine region")
        expect_trap(view, findings, 1, 6, 7, fine.base + 8)
        expect_steps(view, findings, 2, [(S_ENTERED,), (S_DONE,),
                                         (S_DONE, None, 0xABC)])
        expect_trap(view, findings, 2, 3, 7, page.base)
        findings.equal(view.witness["page"], 0xABC, "the shared page")
        findings.equal(view.witness["inner"], 0x7777777777777777,
                       "the read-only extent")
        findings.equal(view.witness["fine-next"], 0x8888888888888888,
                       "the word after the fine region")

    return Case("shared-page", domains, scripts, check=check,
                pages={17: bytes([0x77]) * 4096, 8: bytes([0x88]) * 4096},
                witness={"page": page.base, "inner": inner.base,
                         "fine-next": fine.base + 8},
                final=parked({0: {"domain": "h0", "counts": (1, 0, 0)},
                              1: {"domain": "h1", "counts": (2, 0, 0)},
                              2: {"domain": "h2", "counts": (1, 0, 0)}}))


def fillers(count, first):
    return [(WORK(first + i, label=f"fill{first + i}"), R)
            for i in range(count)]


@row("budget")
def budget(runner, mode):
    """F13 at the move: a domain at the PMP budget commits with every entry
    in use; one region over, the switch stops the hart in M-mode."""
    inherited, count = runner.measure(mode)
    usable = count - (1 if mode == "smepmp" else 0)
    own_regions = usable - inherited
    domains = standard()
    domains["h1"].regions += fillers(own_regions - 3, 32)
    domains["h2"].regions += fillers(own_regions - 2, 64)
    running = state(2, L["RES_OFF"] + L["RES_STATUS"])
    scripts = {0: [hsm_start(1), hsm_start(2), wait_flag(1),
                   wait_word(running, S_RUNNING), delay(SETTLE_TICKS),
                   SHUTDOWN],
               1: [COMMIT, set_flag(1)], 2: [COMMIT]}

    def check(view, findings):
        expect_steps(view, findings, 1, [(S_ENTERED,), (S_DONE,)])
        expect_steps(view, findings, 2, [(S_RUNNING,)])
        used = [cfg for cfg in view.harts[1].pmpcfg[:count] if cfg & 0x18]
        findings.equal(len(used), usable, "hart1 PMP entries in use")
        findings.expect("insufficient PMP entries" in view.text,
                        "no line for the PMP entries running out")
        findings.expect("protection for domain h2 failed" in view.text,
                        "no line for the stopped switch")

    case = Case("budget", domains, scripts, check=check,
                final=parked({0: {"domain": "wide"}, 1: {"domain": "h1"},
                              2: {"domain": "h2", "committed": 0,
                                  "in_firmware": True}}))
    case.notes.append(f"{mode}: {count} PMP entries, {inherited} inherited "
                      f"M-mode-only regions; h1 has {own_regions} regions "
                      f"of its own, h2 {own_regions + 1}")
    return case


@row("budget-boot")
def budget_boot(runner, mode):
    """F13 at boot: a boot domain one region over its budget stops the
    cold boot before S-mode."""
    inherited, count = runner.measure(mode)
    usable = count - (1 if mode == "smepmp" else 0)
    over = usable - inherited + 1
    domains = {"boot": Domain("boot", [0, 1, 2], 0, 1,
                              own(0) + fillers(over - 3, 32), reset=True,
                              next_arg1=0x100)}

    def check(view, findings):
        findings.expect("hart protection configure failed" in view.text,
                        "the cold boot did not stop at its PMP")
        findings.equal(view.harts[0].magic, 0, "the payload ran")

    case = Case("budget-boot", domains, {0: [SHUTDOWN]}, payload=False,
                end_line="hart protection configure failed", check=check)
    case.notes.append(f"{mode}: {count} PMP entries, {inherited} inherited "
                      f"M-mode-only regions; boot has {over} of its own")
    return case


@row("cut-short")
def cut_short(runner, mode):
    """The readback: a region that the PMP cannot express is skipped by
    the base, which reports success; the readback stops the hart."""
    domains = standard()
    domains["h1"].regions.append((Region("far", 1 << 56, 12), R))
    running = state(1, L["RES_OFF"] + L["RES_STATUS"])
    scripts = {0: [hsm_start(1), wait_word(running, S_RUNNING),
                   delay(SETTLE_TICKS), SHUTDOWN],
               1: [COMMIT]}

    def check(view, findings):
        expect_steps(view, findings, 1, [(S_RUNNING,)])
        findings.expect("PMP does not match domain h1" in view.text,
                        "no line for the readback")
        findings.expect("protection for domain h1 failed" in view.text,
                        "no line for the stopped switch")

    return Case("cut-short", domains, scripts, check=check,
                final=parked({0: {"domain": "wide"},
                              1: {"domain": "h1", "committed": 0,
                                  "in_firmware": True},
                              2: {"domain": None}}))


CBO_INVAL_A1 = 0x0005A00F


@row("cache-block")
def cache_block(runner, mode):
    """F22: menvcfg.CBIE is cleared at the commit; cbo.inval then traps
    as an illegal instruction from HS and from VS."""
    scripts = {0: [hsm_start(1), wait_flag(1), SHUTDOWN],
               1: [cbo(state(1, 0x100)), COMMIT, cbo(state(1, 0x100)),
                   cbo(state(1, 0x100), VS), set_flag(1)]}

    def check(view, findings):
        expect_steps(view, findings, 1, [(S_DONE,), (S_ENTERED,)])
        expect_trap(view, findings, 1, 2, 2, CBO_INVAL_A1, False)
        expect_trap(view, findings, 1, 3, 2, CBO_INVAL_A1, True)

    return Case("cache-block", standard(), scripts, check=check,
                final=parked({0: {"domain": "wide"}, 1: {"domain": "h1"},
                              2: {"domain": None}}))


@row("trap-paths")
def trap_paths(runner, mode):
    """Each trap path that M-mode performs for a hart, from a committed
    hart: illegal instructions, M-mode's instruction fetch for a hart, a
    load decoded from an execute-only page, a misaligned atomic, and a
    misaligned load that the hart performs itself."""
    domains = standard()
    xpage = WORK(9, label="xpage")
    domains["h1"].regions.append((xpage, X))
    code = bytearray(4096)
    code[0x10:0x18] = bytes.fromhex("0335060067800000")
    outside = work(10)
    data = state(1, 0x200)
    scripts = {0: [hsm_start(1), wait_flag(1), SHUTDOWN],
               1: [COMMIT, step("ILL32"), step("ILL16"), fetch(xpage.base),
                   fetch(xpage.base + 0x10, outside),
                   store(data, 0x1122334455667788),
                   store(data + 8, 0x99AABBCCDDEEFF00),
                   amo(data + 2), load(data), load(data + 1),
                   fetch(outside), set_flag(1)]}

    def check(view, findings):
        expect_steps(view, findings, 1, [(S_ENTERED,)])
        expect_trap(view, findings, 1, 1, 2, 0x0000000B)
        expect_trap(view, findings, 1, 2, 2, 0)
        expect_trap(view, findings, 1, 3, 1, xpage.base)
        expect_trap(view, findings, 1, 4, 5, outside)
        got = view.result(1, 7)
        findings.equal(got["status"], S_TRAPPED, "the misaligned atomic")
        findings.expect(got["cause"] in (4, 6),
                        f"the misaligned atomic's cause {got['cause']}")
        view.case.notes.append(f"{view.mode}: the misaligned atomic came "
                               f"back with cause {got['cause']}")
        findings.equal(view.result(1, 8)["value"], 0x1122334455667788,
                       "the word under the misaligned atomic")
        findings.equal(view.result(1, 9)["status"], S_DONE,
                       "the misaligned load")
        findings.equal(view.result(1, 9)["value"], 0x0011223344556677,
                       "the misaligned load's value")
        expect_trap(view, findings, 1, 10, 1, outside)

    return Case("trap-paths", domains, scripts, check=check,
                pages={9: bytes(code)},
                final=parked({0: {"domain": "wide"},
                              1: {"domain": "h1", "counts": (3, 0, 0)},
                              2: {"domain": None}}))


@row("stop-suspend-reset")
def stop_suspend_reset(runner, mode):
    """F11: a committed hart that stops cannot be started again from the
    boot domain; one that suspends wakes with its narrow PMP and the
    cache-block control in place, after a retentive and after a
    non-retentive suspend; a shutdown that its domain may not make stops
    only that hart."""
    domains = standard()
    domains["h1"].allow = [(HSM, 1, ANY, 0)]
    domains["h2"].allow = [(HSM, 3, ANY, 0), SHUTDOWN_ONLY]
    outside = work(11)
    tick = TIMEBASE_HZ // 1000
    scripts = {
        0: [hsm_start(1), hsm_start(2), wait_flag(1), delay(SETTLE_TICKS),
            hsm_status(1), hsm_start(1), wait_flag(2, 2),
            delay(SETTLE_TICKS), SHUTDOWN],
        1: [COMMIT, set_flag(1), sbi(HSM, 1)],
        2: [COMMIT, suspend(0, tick), load(outside), cbo(state(2, 0x100)),
            suspend(0x80000000, tick), load(outside),
            cbo(state(2, 0x100)), set_flag(2, 2), SHUTDOWN],
    }

    def check(view, findings):
        expect_steps(view, findings, 0, [(S_DONE, OK), (S_DONE, OK),
                                         (S_DONE,), (S_DONE,),
                                         (S_DONE, INVALID_PARAM),
                                         (S_DONE, INVALID_PARAM),
                                         (S_DONE,), (S_DONE,), (S_RUNNING,)])
        expect_steps(view, findings, 1, [(S_ENTERED,), (S_DONE,),
                                         (S_RUNNING,)])
        expect_steps(view, findings, 2, [(S_ENTERED,), (S_DONE, OK)])
        expect_trap(view, findings, 2, 2, 5, outside)
        expect_trap(view, findings, 2, 3, 2, CBO_INVAL_A1)
        expect_steps(view, findings, 2, [(S_ENTERED,), (S_DONE, OK),
                                         (S_TRAPPED,), (S_TRAPPED,),
                                         (S_ENTERED, None, 2)])
        expect_trap(view, findings, 2, 5, 5, outside)
        expect_trap(view, findings, 2, 6, 2, CBO_INVAL_A1)
        findings.equal(view.result(2, 8)["status"], S_RUNNING,
                       "hart2 shutdown")
        findings.equal(view.harts[2].entries[-1][L["EN_A1"]], 0,
                       "hart2 resume a1")

    return Case("stop-suspend-reset", domains, scripts, check=check,
                final=parked({0: {"domain": "wide"},
                              1: {"domain": "h1", "in_firmware": True},
                              2: {"domain": "h2", "in_firmware": True,
                                  "counts": (2, 0, 0)}}))


@row("assignment")
def assignment(runner, mode):
    """F8: a hart listed by two domains is assigned to the one of lesser
    initialization order, whatever their order in the tree; root's order
    is the greatest."""
    domains = {
        "x": Domain("x", [1], 1, 30, own(1), next_arg1=0x30),
        "y": Domain("y", [1], 1, 20, own(1), next_arg1=0x20),
    }
    scripts = {0: [wait_done(1), SHUTDOWN], 1: []}

    def check(view, findings):
        findings.equal(view.domains["y"].get("HARTs"), "0x1*",
                       "y's harts in the dump")
        findings.equal(view.domains["x"].get("HARTs"), "0x1",
                       "x's harts in the dump")
        findings.equal(view.domains["root"].get("Init Order"), "0xffffffff",
                       "root's init order")
        findings.equal(view.harts[1].entries[0][L["EN_A1"]], 0x20,
                       "hart1 started in y")

    return Case("assignment", domains, scripts, check=check,
                final=parked({0: {"domain": "wide-root"},
                              1: {"domain": "wide-y"},
                              2: {"domain": None}}))


@row("alloc-fail")
def alloc_fail(runner, mode):
    """The cold boot allocation of the switch contexts: when the heap
    cannot hold them, the cold boot stops before S-mode."""
    domains = standard()
    for number in range(10):
        domains[f"a{number}"] = Domain(f"a{number}", list(range(HARTS)), 0,
                                       50 + number, own(0),
                                       next_arg1=0x400 + number)

    def check(view, findings):
        findings.expect("domain context allocation failed" in view.text,
                        "the cold boot did not stop at the allocation")
        findings.equal(view.harts[0].magic, 0, "the payload ran")

    return Case("alloc-fail", domains, {0: [SHUTDOWN]}, payload=False,
                end_line="domain finalize failed", check=check,
                boot_print=False)


@row("bad-properties")
def bad_properties(runner, mode):
    """Rule 3: a property that the parser cannot read whole stops the
    cold boot: a digest of seven cells, an argument index of 6, and an
    allowlist of nine entries."""
    cases = []
    for name, change in (
            ("digest-7", lambda c: setattr(c, "digest", DIGEST[:7])),
            ("argument-6",
             lambda c: setattr(c.domains["h1"], "allow", [(BASE, 0, 6, 0)])),
            ("entries-9",
             lambda c: setattr(c.domains["h1"], "allow",
                               [(BASE, i, ANY, 0) for i in range(9)]))):
        def check(view, findings):
            findings.expect("domain finalize failed" in view.text,
                            "the cold boot did not stop")
            findings.equal(view.harts[0].magic, 0, "the payload ran")

        case = Case(f"bad-properties-{name}", standard(), {0: [SHUTDOWN]},
                    payload=False, end_line="domain finalize failed",
                    check=check, boot_print=False)
        change(case)
        cases.append(case)
    return cases


@row("vector", modes=("plain",))
def vector(runner, mode):
    """The switch contexts' vector areas, sized at cold boot, on harts
    with the vector extension: D-6's sequence as in d6-vs-first."""
    case = d6("vector", False)
    case.cpu_extra = ",v=true"
    return case


# ------------------------------------------------------------- main

def main(argv):
    parser = argparse.ArgumentParser(prog="fwtest.py")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--firmware-dir", required=True)
    run.add_argument("--payload", required=True)
    run.add_argument("--qemu", required=True)
    run.add_argument("--dtc", required=True)
    run.add_argument("--nm", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--mode", choices=("plain", "smepmp", "both"),
                     default="both")
    run.add_argument("rows", nargs="*")
    sub.add_parser("list")
    args = parser.parse_args(argv)
    if args.command == "list":
        for name, (_, modes) in ROWS.items():
            print(name, ",".join(modes))
        return 0
    unknown = [name for name in args.rows if name not in ROWS]
    if unknown:
        parser.error(f"unknown rows: {' '.join(unknown)}")
    out = pathlib.Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    runner = Runner(args)
    runs = failed = 0
    lines = []
    for name in args.rows or list(ROWS):
        function, modes = ROWS[name]
        for mode in modes:
            if args.mode != "both" and mode != args.mode:
                continue
            cases = function(runner, mode)
            for case in cases if isinstance(cases, list) else [cases]:
                runs += 1
                items = runner.run(case, mode)
                verdict = "FAIL" if items else "PASS"
                failed += bool(items)
                lines.append(f"BE_MVP_FIRMWARE_TEST_ROW: {verdict} "
                             f"{case.name} {mode}")
                print(lines[-1], flush=True)
                for item in items:
                    print(f"  finding: {item}", flush=True)
    verdict = "FAIL" if failed else "PASS"
    summary = f"BE_MVP_FIRMWARE_TEST: {verdict} runs={runs} failed={failed}"
    (out / "summary.txt").write_text("\n".join(lines + [summary]) + "\n",
                                     encoding="utf-8")
    print(summary)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
