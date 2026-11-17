#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""The QEMU end-of-run oracle.

  qemu_oracle.py run --record FILE --exit-file FILE --qemu-output FILE
      --terminal-file FILE --terminal-regex REGEX --timeout S --grace S
      --harts N --machine-class NAME [--boundary-on]
      --pmp CLASS --menvcfg CLASS --mseccfg CLASS [--pmp-mode MODE]
      --ram-base ADDRESS --ram-size BYTES
      --elf-word NAME=ELF [--record-table FW_ELF --nm NM]
      [--words FILE] -- QEMU ARG...
  qemu_oracle.py result FILE
  qemu_oracle.py not-attached FILE
  qemu_oracle.py --self-test --scratch DIR

Purpose: launch QEMU with a private QMP socketpair, observe the end of a
run, stop a run whose harness limit fires, read each hart's final PMP and
control state plus named physical words while the machine is stopped,
then end QEMU with QMP quit.  The launchers keep judging the serial
capture exactly as before; this module supplies the additional pass rule.

The QMP channel is one end of socket.socketpair().  QEMU inherits the
other end through -chardev socket,fd=N and uses it only for a control-mode
monitor.  No listener, pathname, or network socket exists.

Record: UTF-8 JSON with schema be-mvp-qemu-oracle-v1.  It contains no
host path or time.  Register values and physical words are fixed-width
hexadecimal strings.  A passing run has a guest SHUTDOWN event with
guest=true and reason=guest-shutdown, matching stopped states before and
after the read, all reads complete, and QEMU exit status zero after quit.

Trust: a test harness client.  It accepts only exact QMP and HMP reply
forms used below, validates every memory range before QEMU starts, writes
only the record paths its caller gives, and uses the Python standard
library only.

Scope: QEMU system emulation.  The HMP register and physical-memory reads
are carried by QMP human-monitor-command with an explicit cpu-index.

The CHERI-aware monitor keeps its existing launcher rule instead: its
emulator's test finisher exits QEMU directly, outside QEMU's shutdown
request path, so no stopped machine exists for this client.  Those attempts
run without QMP and carry the fixed one-line NOT-ATTACHED record written by
the `not-attached` command.

M11-7 (planning/mvp-m11-plan.md, D-10, D-12): a boundary-on run declares
its PMP mode, plain or smepmp, and is refused before QEMU starts unless it
is on k3-like with the PMP registers and menvcfg readable and mseccfg
readable under Smepmp and absent under plain PMP (the decision record's
erratum to `oracle: absent`); a boundary-off run declares none.
--record-table names the firmware's commit records, sbi_dcommit_harts in
FW_ELF by the lock's nm, 24 words per hart (t<hart>-<index>), which the
boundary's checker (tests/check-boundary.py) judges. --words FILE names
further RAM words and device registers; a device register must be one of
a closed list, each read with no side effect at its own width: the UART's
scratch register and the S-level APLIC's source configurations.
"""

import argparse
import dataclasses
import json
import os
import pathlib
import re
import select
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time

SCHEMA = "be-mvp-qemu-oracle-v1"
QMP_TIMEOUT = 10.0
QUIT_TIMEOUT = 10.0
MAX_LINE = 1024 * 1024
NAME = re.compile(r"[a-z][a-z0-9-]{0,63}")
HEX_REPLY = re.compile(r"(?:0|0x[0-9a-f]+)\r\n")
PC_REPLY = re.compile(r"^ pc +([0-9a-f]{16})\r$", re.M)
MHARTID_REPLY = re.compile(r"^ mhartid +([0-9a-f]{16})\r$", re.M)
UNKNOWN_REGISTER = 'unknown register\r\nTry "help p" for more information\r\n'
REGISTER_CLASSES = ("readable", "absent")
PMP_REGISTERS = ("pmpcfg0", "pmpcfg2",
                 *(f"pmpaddr{number}" for number in range(16)))
PMP_MODES = ("plain", "smepmp", "none")
WORDS_SCHEMA = "be-mvp-oracle-words-v1"
# The firmware's ELF addresses are offsets from QEMU virt's RAM base, where
# -bios loads it; its commit record of a hart is 24 words (struct
# sbi_dcommit_hart: six words, sixteen configuration bytes, sixteen
# addresses).
FIRMWARE_BASE = 0x80000000
RECORD_SYMBOL = "sbi_dcommit_harts"
RECORD_WORDS = 24
NM_LINE = re.compile(r"([0-9a-f]+) ([A-Za-z]) (\S+)")
HEX_TEXT = re.compile(r"0x[0-9a-f]{1,16}")
# The device registers a run may name, each read without a side effect at
# its width: the UART's scratch register, and the S-level APLIC's
# sourcecfg[1..96] (k3-like's base tree: riscv,num-sources = 96).
DEVICE_WIDTHS = dict([(0x10000007, 1)] +
                     [(0x0d000000 + 4 * source, 4)
                      for source in range(1, 97)])
DEVICE_UNITS = {1: ("b", 2), 4: ("w", 8)}


class OracleError(Exception):
    """An input, protocol reply, or end state the oracle refuses."""


@dataclasses.dataclass(frozen=True)
class NamedWord:
    """One named little-endian 64-bit physical word."""

    name: str
    address: int
    expected: int | None


@dataclasses.dataclass(frozen=True)
class DeviceWord:
    """One named device register of DEVICE_WIDTHS, read at its width."""

    name: str
    address: int
    expected: int | None


@dataclasses.dataclass(frozen=True)
class OracleConfig:
    """The machine facts a launcher states before QEMU starts."""

    harts: int
    machine: str
    boundary_on: bool
    pmp: str
    menvcfg: str
    mseccfg: str
    ram_base: int
    ram_size: int
    words: tuple[NamedWord, ...]
    pmp_mode: str = "none"
    devices: tuple[DeviceWord, ...] = ()

    def validate(self):
        if self.harts < 1:
            raise OracleError("the expected hart count is not positive")
        if not NAME.fullmatch(self.machine):
            raise OracleError("the machine class has an invalid name")
        declarations = (self.pmp, self.menvcfg, self.mseccfg)
        if any(value not in REGISTER_CLASSES for value in declarations):
            raise OracleError("a register class declaration is invalid")
        if self.pmp_mode not in PMP_MODES:
            raise OracleError("the PMP mode is not plain, smepmp, or none")
        if self.boundary_on:
            mseccfg = "readable" if self.pmp_mode == "smepmp" else "absent"
            if self.machine != "k3-like" or self.pmp_mode == "none" or \
                    declarations != ("readable", "readable", mseccfg):
                raise OracleError(
                    "a boundary-on run must be on k3-like in a PMP mode, "
                    "with PMP and menvcfg readable and mseccfg readable "
                    "under smepmp and absent under plain")
        elif self.pmp_mode != "none":
            raise OracleError("a boundary-off run declares no PMP mode")
        if self.ram_base < 0 or self.ram_size <= 0 or \
                self.ram_base + self.ram_size > 1 << 64:
            raise OracleError("the RAM range is not a 64-bit range")
        names = set()
        for word in self.words:
            if not NAME.fullmatch(word.name) or word.name in names:
                raise OracleError("a named word has an invalid or repeated name")
            names.add(word.name)
            if word.address & 7:
                raise OracleError(f"named word {word.name} is not 8-byte aligned")
            if word.address < self.ram_base or \
                    word.address + 8 > self.ram_base + self.ram_size:
                raise OracleError(f"named word {word.name} is outside RAM")
            if word.expected is not None and not 0 <= word.expected < 1 << 64:
                raise OracleError(f"named word {word.name} has no 64-bit value")
        for device in self.devices:
            if not NAME.fullmatch(device.name) or device.name in names:
                raise OracleError("a named word has an invalid or repeated name")
            names.add(device.name)
            width = DEVICE_WIDTHS.get(device.address)
            if width is None:
                raise OracleError(f"device word {device.name} is not on the "
                                  f"device list")
            if device.expected is not None and \
                    not 0 <= device.expected < 1 << (8 * width):
                raise OracleError(f"device word {device.name} has no "
                                  f"{8 * width}-bit value")


@dataclasses.dataclass(frozen=True)
class EndState:
    """How the run ended before the oracle read."""

    kind: str
    reason: str


@dataclasses.dataclass(frozen=True)
class Outcome:
    """The result that a launcher applies beside its capture verdict."""

    passed: bool
    detail: str
    qemu_exit: str


def hex64(value):
    return f"0x{value:016x}"


def exit_text(status):
    if status is None:
        return "none"
    if status < 0:
        return f"signal-{abs(status)}"
    return f"0x{status:08x}"


def launcher_exit(status):
    """The launchers' existing text form for a process return code."""
    if status is None:
        return "killed:none"
    if status < 0:
        return f"killed:{status}"
    return str(status)


def first_load(path):
    """The first ELF64 little-endian PT_LOAD: address and first 8 bytes."""
    data = pathlib.Path(path).read_bytes()
    if len(data) < 64 or data[:6] != b"\x7fELF\x02\x01":
        raise OracleError("the named-word input is not ELF64 little-endian")
    if struct.unpack_from("<H", data, 18)[0] != 243:
        raise OracleError("the named-word ELF is not RISC-V")
    phoff = struct.unpack_from("<Q", data, 32)[0]
    phentsize = struct.unpack_from("<H", data, 54)[0]
    phnum = struct.unpack_from("<H", data, 56)[0]
    if phentsize != 56 or phnum == 0 or phoff + phentsize * phnum > len(data):
        raise OracleError("the named-word ELF has an invalid program table")
    for number in range(phnum):
        fields = struct.unpack_from("<IIQQQQQQ",
                                    data, phoff + number * phentsize)
        kind, _, offset, _, physical, filesz, _, _ = fields
        if kind != 1:
            continue
        if filesz < 8 or offset + 8 > len(data):
            raise OracleError("the first loadable segment has no complete word")
        return physical, data[offset:offset + 8]
    raise OracleError("the named-word ELF has no loadable segment")


def word_from_elf(name, path):
    address, data = first_load(path)
    return NamedWord(name, address, int.from_bytes(data, "little"))


def word_from_image(name, path, address):
    data = pathlib.Path(path).read_bytes()
    if len(data) < 8:
        raise OracleError("the named-word image has no complete word")
    return NamedWord(name, address, int.from_bytes(data[:8], "little"))


def word_from_binary_elf(name, binary, elf):
    """The first word QEMU loads from a flat binary, located by its ELF."""
    address, elf_data = first_load(elf)
    binary_data = pathlib.Path(binary).read_bytes()
    if len(binary_data) < 8 or binary_data[:8] != elf_data:
        raise OracleError("the flat binary's first word differs from its ELF")
    return NamedWord(name, address, int.from_bytes(binary_data[:8], "little"))


def parse_nm(text, names):
    """Each of NAMES's address in nm's output, each defined once."""
    found = {}
    for line in text.splitlines():
        match = NM_LINE.fullmatch(line)
        if match and match.group(3) in names:
            if match.group(3) in found:
                raise OracleError(f"{match.group(3)} is defined twice")
            found[match.group(3)] = int(match.group(1), 16)
    missing = sorted(set(names) - set(found))
    if missing:
        raise OracleError(f"the firmware's ELF has no {', '.join(missing)}")
    return found


def symbol_addresses(nm, elf, names):
    output = subprocess.run([str(nm), str(elf)], capture_output=True,
                            text=True, check=True).stdout
    return parse_nm(output, names)


def table_words(table, harts):
    """The commit records' words, t<hart>-<index>, from TABLE's address."""
    return tuple(NamedWord(f"t{hart}-{index}",
                           table + 8 * (hart * RECORD_WORDS + index), None)
                 for hart in range(harts) for index in range(RECORD_WORDS))


def record_table_words(nm, elf, harts):
    symbol = symbol_addresses(nm, elf, (RECORD_SYMBOL,))[RECORD_SYMBOL]
    return table_words(FIRMWARE_BASE + symbol, harts)


def words_from_file(path):
    """--words FILE: (RAM words, device registers), each entry a name, a
    hexadecimal address, and a hexadecimal expected value or null."""
    try:
        value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OracleError("the words file is not JSON") from error
    if not isinstance(value, dict) or \
            set(value) != {"schema", "words", "devices"} or \
            value["schema"] != WORDS_SCHEMA:
        raise OracleError("the words file is not of its schema")
    out = []
    for kind, make in (("words", NamedWord), ("devices", DeviceWord)):
        if not isinstance(value[kind], list):
            raise OracleError("the words file is not of its schema")
        rows = []
        for row in value[kind]:
            if not isinstance(row, dict) or \
                    set(row) != {"name", "address", "expected"} or \
                    not isinstance(row["name"], str) or \
                    not isinstance(row["address"], str) or \
                    not HEX_TEXT.fullmatch(row["address"]) or \
                    not (row["expected"] is None or
                         (isinstance(row["expected"], str) and
                          HEX_TEXT.fullmatch(row["expected"]))):
                raise OracleError("a words-file entry is malformed")
            rows.append(make(row["name"], int(row["address"], 16),
                             None if row["expected"] is None
                             else int(row["expected"], 16)))
        out.append(tuple(rows))
    return out[0], out[1]


def write_new(path, data):
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(data)


def write_failure_record(path, detail, status=None):
    """Write the fixed record shape when QMP setup itself did not complete."""
    value = {
        "schema": SCHEMA,
        "result": {
            "verdict": "FAIL",
            "detail": detail,
        },
        "end": {
            "kind": "error",
            "reason": "oracle-setup",
        },
        "register_classes": None,
        "status_before": None,
        "harts": [],
        "words": [],
        "status_after": None,
        "qemu_exit": exit_text(status),
    }
    write_new(path, json.dumps(value, indent=2, ensure_ascii=True) + "\n")


def write_not_attached_record(path):
    """The fixed one-line record for the CHERI-aware monitor's attempts."""
    value = {
        "schema": SCHEMA,
        "result": {
            "verdict": "NOT-ATTACHED",
            "detail": ("CHERI emulator test finisher exits directly; no "
                       "shutdown event or stopped state"),
        },
        "end": {
            "kind": "not-attached",
            "reason": "test-finisher-exit",
        },
        "register_classes": None,
        "status_before": None,
        "harts": [],
        "words": [],
        "status_after": None,
        "qemu_exit": "not-recorded",
    }
    write_new(path, json.dumps(value, separators=(",", ":"),
                               ensure_ascii=True) + "\n")


class QMPClient:
    """One strict QMP connection with an asynchronous reader."""

    def __init__(self, channel, timeout=QMP_TIMEOUT):
        self.channel = channel
        self.stream = channel.makefile("rwb", buffering=0)
        self.condition = threading.Condition()
        self.responses = {}
        self.events = []
        self.fatal = None
        self.closed = False
        self.expect_close = False
        self.next_id = 1
        self.send_lock = threading.Lock()
        greeting = self._read_message(timeout)
        self._greeting(greeting)
        self._send({"execute": "qmp_capabilities", "id": 0})
        while True:
            message = self._read_message(timeout)
            if message.get("id") == 0:
                if set(message) != {"return", "id"} or message["return"] != {}:
                    raise OracleError("QMP capability negotiation failed")
                break
            self._early(message)
        self.reader = threading.Thread(target=self._read_loop,
                                       name="qemu-oracle-qmp", daemon=True)
        self.reader.start()

    def _read_message(self, timeout):
        ready, _, _ = select.select([self.channel], [], [], timeout)
        if not ready:
            raise OracleError("QMP did not reply within its limit")
        line = self.stream.readline(MAX_LINE + 1)
        if not line:
            raise OracleError("QMP channel closed")
        if len(line) > MAX_LINE or not line.endswith(b"\n"):
            raise OracleError("QMP sent an overlong or incomplete line")
        try:
            message = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OracleError("QMP sent a malformed line") from error
        if not isinstance(message, dict):
            raise OracleError("QMP sent a non-object")
        return message

    @staticmethod
    def _greeting(message):
        if set(message) != {"QMP"} or not isinstance(message["QMP"], dict):
            raise OracleError("QMP sent no greeting")
        greeting = message["QMP"]
        if set(greeting) != {"version", "capabilities"} or \
                not isinstance(greeting["version"], dict) or \
                not isinstance(greeting["capabilities"], list):
            raise OracleError("QMP sent a malformed greeting")

    def _early(self, message):
        if "event" not in message:
            raise OracleError("QMP sent an unexpected message before setup")
        self.events.append(message)

    def _send(self, message):
        data = json.dumps(message, separators=(",", ":"),
                          ensure_ascii=True).encode("ascii") + b"\r\n"
        with self.send_lock:
            try:
                self.stream.write(data)
            except (BrokenPipeError, OSError) as error:
                raise OracleError("QMP channel closed while sending") from error

    def _read_loop(self):
        try:
            while True:
                line = self.stream.readline(MAX_LINE + 1)
                if not line:
                    with self.condition:
                        self.closed = True
                        if not self.expect_close:
                            self.fatal = self.fatal or "QMP channel closed"
                        self.condition.notify_all()
                    return
                if len(line) > MAX_LINE or not line.endswith(b"\n"):
                    raise OracleError("QMP sent an overlong or incomplete line")
                try:
                    message = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise OracleError("QMP sent a malformed line") from error
                if not isinstance(message, dict):
                    raise OracleError("QMP sent a non-object")
                with self.condition:
                    if "event" in message:
                        self.events.append(message)
                    elif "id" in message:
                        ident = message["id"]
                        if ident in self.responses:
                            raise OracleError("QMP repeated a command response")
                        self.responses[ident] = message
                    else:
                        raise OracleError("QMP sent neither event nor response")
                    self.condition.notify_all()
        except (OracleError, OSError, ValueError) as error:
            with self.condition:
                if not self.expect_close:
                    self.fatal = str(error)
                self.condition.notify_all()

    def command(self, execute, arguments=None, timeout=QMP_TIMEOUT):
        with self.condition:
            ident = self.next_id
            self.next_id += 1
        message = {"execute": execute}
        if arguments is not None:
            message["arguments"] = arguments
        message["id"] = ident
        self._send(message)
        deadline = time.monotonic() + timeout
        with self.condition:
            while ident not in self.responses:
                if self.fatal:
                    raise OracleError(self.fatal)
                if self.closed:
                    raise OracleError("QMP channel closed before a reply")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise OracleError(f"QMP {execute} did not reply")
                self.condition.wait(remaining)
            response = self.responses.pop(ident)
        if set(response) == {"error", "id"}:
            error = response["error"]
            kind = error.get("class") if isinstance(error, dict) else None
            if not isinstance(kind, str):
                kind = "error"
            raise OracleError(f"QMP {execute} returned {kind}")
        if set(response) != {"return", "id"}:
            raise OracleError(f"QMP {execute} returned an unexpected object")
        return response["return"]

    @staticmethod
    def _shutdown(message):
        if set(message) - {"event", "data", "timestamp"} or \
                message.get("event") != "SHUTDOWN":
            return None
        data = message.get("data")
        if not isinstance(data, dict) or set(data) != {"guest", "reason"} or \
                not isinstance(data["guest"], bool) or \
                not isinstance(data["reason"], str):
            raise OracleError("QMP SHUTDOWN has unexpected fields")
        guest, reason = data["guest"], data["reason"]
        if guest and reason == "guest-shutdown":
            return EndState("guest-shutdown", reason)
        if guest and reason == "guest-reset":
            return EndState("reset", reason)
        if not guest:
            return EndState("host-shutdown", reason)
        return EndState("error", reason)

    def poll_end(self):
        with self.condition:
            if self.fatal:
                raise OracleError(self.fatal)
            for message in self.events:
                end = self._shutdown(message)
                if end is not None:
                    return end
            if self.closed:
                raise OracleError("QMP channel closed before the run ended")
        return None

    def wait_end(self, timeout):
        deadline = time.monotonic() + timeout
        with self.condition:
            while True:
                if self.fatal:
                    raise OracleError(self.fatal)
                for message in self.events:
                    end = self._shutdown(message)
                    if end is not None:
                        return end
                if self.closed:
                    raise OracleError("QMP channel closed before the run ended")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self.condition.wait(remaining)

    def quit(self):
        self.expect_close = True
        with self.condition:
            ident = self.next_id
            self.next_id += 1
        self._send({"execute": "quit", "id": ident})

    def close(self):
        self.expect_close = True
        try:
            self.stream.close()
        except OSError:
            pass
        try:
            self.channel.close()
        except OSError:
            pass


class OracleProcess:
    """A QEMU process and its private QMP oracle."""

    def __init__(self, process, qmp, config, record):
        self.process = process
        self.qmp = qmp
        self.config = config
        self.record = pathlib.Path(record)
        self.finished = False
        self.status_before = None
        self.status_after = None
        self.harts = []
        self.words = []

    @classmethod
    def launch(cls, argv, config, record, **popen):
        config.validate()
        record = pathlib.Path(record)
        if record.exists():
            raise OracleError("the oracle record already exists")
        parent, child = socket.socketpair()
        descriptor = child.fileno()
        command = list(argv) + [
            "-no-shutdown",
            "-chardev", f"socket,id=be-oracle,fd={descriptor}",
            "-mon", "chardev=be-oracle,mode=control",
        ]
        process = None
        try:
            process = subprocess.Popen(command, pass_fds=(descriptor,), **popen)
            child.close()
            qmp = QMPClient(parent)
            return cls(process, qmp, config, record)
        except Exception:
            child.close()
            parent.close()
            if process is not None:
                process.kill()
                try:
                    process.wait(timeout=QUIT_TIMEOUT)
                except subprocess.TimeoutExpired:
                    pass
            raise

    def poll_end(self):
        return self.qmp.poll_end()

    def wait_end(self, timeout):
        return self.qmp.wait_end(timeout)

    @staticmethod
    def _status(value):
        if not isinstance(value, dict) or \
                set(value) - {"running", "status", "singlestep"} or \
                set(value) < {"running", "status"} or \
                not isinstance(value["running"], bool) or \
                not isinstance(value["status"], str) or \
                ("singlestep" in value and
                 not isinstance(value["singlestep"], bool)):
            raise OracleError("query-status returned an unexpected form")
        return {"running": value["running"], "status": value["status"],
                "singlestep": value.get("singlestep")}

    def _hmp(self, command, cpu_index):
        value = self.qmp.command("human-monitor-command",
                                 {"command-line": command,
                                  "cpu-index": cpu_index})
        if not isinstance(value, str):
            raise OracleError("human-monitor-command returned a non-string")
        return value

    def _register(self, cpu_index, name, declaration):
        reply = self._hmp(f"p /x ${name}", cpu_index)
        if declaration != "readable":
            if reply != UNKNOWN_REGISTER:
                raise OracleError(f"{name} of hart {cpu_index}: readable "
                                  f"but declared {declaration}")
            return declaration
        if reply == UNKNOWN_REGISTER:
            raise OracleError(f"{name} of hart {cpu_index}: unknown register")
        if not HEX_REPLY.fullmatch(reply):
            raise OracleError(f"{name} of hart {cpu_index}: unexpected reply")
        value = int(reply.strip(), 0)
        if not 0 <= value < 1 << 64:
            raise OracleError(f"{name} of hart {cpu_index}: not 64-bit")
        return hex64(value)

    def _identity(self, cpu_index):
        reply = self._hmp("info registers", cpu_index)
        pcs, harts = PC_REPLY.findall(reply), MHARTID_REPLY.findall(reply)
        if len(pcs) != 1:
            raise OracleError(f"pc of hart {cpu_index}: unexpected reply")
        if len(harts) != 1:
            raise OracleError(f"mhartid of hart {cpu_index}: unexpected reply")
        return hex64(int(pcs[0], 16)), hex64(int(harts[0], 16))

    def _cpus(self):
        cpus = self.qmp.command("query-cpus-fast")
        if not isinstance(cpus, list) or any(not isinstance(cpu, dict)
                                             for cpu in cpus):
            raise OracleError("query-cpus-fast returned an unexpected form")
        indices = [cpu.get("cpu-index") for cpu in cpus]
        if indices != list(range(self.config.harts)):
            raise OracleError(f"QEMU has {len(cpus)} harts, expected "
                              f"{self.config.harts}")

    def _read_harts(self):
        self._cpus()
        for cpu_index in range(self.config.harts):
            pc, mhartid = self._identity(cpu_index)
            pmp = {name: self._register(cpu_index, name, self.config.pmp)
                   for name in PMP_REGISTERS}
            self.harts.append({
                "cpu_index": hex64(cpu_index),
                "mhartid": mhartid,
                "pc": pc,
                "pmpcfg0": pmp["pmpcfg0"],
                "pmpcfg2": pmp["pmpcfg2"],
                "pmpaddr": [pmp[f"pmpaddr{number}"] for number in range(16)],
                "menvcfg": self._register(cpu_index, "menvcfg",
                                           self.config.menvcfg),
                "mseccfg": self._register(cpu_index, "mseccfg",
                                           self.config.mseccfg),
            })

    def _read_words(self):
        for word in self.config.words:
            reply = self._hmp(f"xp /1gx 0x{word.address:016x}", 0)
            pattern = re.compile(
                rf"{word.address:016x}: 0x([0-9a-f]{{16}})\r\n")
            match = pattern.fullmatch(reply)
            if not match:
                raise OracleError(f"named word {word.name}: unexpected reply")
            value = int(match.group(1), 16)
            self.words.append({
                "name": word.name,
                "address": hex64(word.address),
                "value": hex64(value),
                "expected": (hex64(word.expected)
                             if word.expected is not None else None),
            })
            if word.expected is not None and value != word.expected:
                raise OracleError(f"named word {word.name}: value mismatch")

    def _read_devices(self):
        for device in self.config.devices:
            unit, digits = DEVICE_UNITS[DEVICE_WIDTHS[device.address]]
            reply = self._hmp(f"xp /1{unit}x 0x{device.address:016x}", 0)
            match = re.fullmatch(
                rf"{device.address:016x}: 0x([0-9a-f]{{{digits}}})\r\n",
                reply)
            if not match:
                raise OracleError(f"device word {device.name}: unexpected "
                                  f"reply")
            value = int(match.group(1), 16)
            self.words.append({
                "name": device.name,
                "address": hex64(device.address),
                "value": hex64(value),
                "expected": (hex64(device.expected)
                             if device.expected is not None else None),
            })
            if device.expected is not None and value != device.expected:
                raise OracleError(f"device word {device.name}: value "
                                  f"mismatch")

    def _snapshot(self):
        self.status_before = self._status(self.qmp.command("query-status"))
        if self.status_before["running"]:
            raise OracleError("the machine is running before the read")
        self._read_harts()
        self._read_words()
        self._read_devices()
        self.status_after = self._status(self.qmp.command("query-status"))
        if self.status_after["running"]:
            raise OracleError("the machine is running after the read")
        if self.status_after != self.status_before:
            raise OracleError("the machine status changed during the read")

    def _end_process(self):
        status = self.process.poll()
        if status is not None:
            return status
        try:
            self.qmp.quit()
            return self.process.wait(timeout=QUIT_TIMEOUT)
        except (OracleError, subprocess.TimeoutExpired):
            self.process.kill()
            try:
                return self.process.wait(timeout=QUIT_TIMEOUT)
            except subprocess.TimeoutExpired:
                return None

    @staticmethod
    def _end_detail(end):
        if end.kind == "guest-shutdown":
            return "guest shutdown"
        if end.kind == "reset":
            return "reset, not a guest shutdown"
        if end.kind == "host-shutdown":
            return f"host requested shutdown: {end.reason}"
        if end.kind == "stopped-by-harness":
            return f"stopped by the harness: {end.reason}"
        return f"unexpected shutdown: {end.reason}"

    def _record(self, passed, detail, end, qemu_exit):
        value = {
            "schema": SCHEMA,
            "result": {
                "verdict": "PASS" if passed else "FAIL",
                "detail": detail,
            },
            "end": {
                "kind": end.kind,
                "reason": end.reason,
            },
            "register_classes": {
                "pmp": self.config.pmp,
                "menvcfg": self.config.menvcfg,
                "mseccfg": self.config.mseccfg,
            },
            "status_before": self.status_before,
            "harts": self.harts,
            "words": self.words,
            "status_after": self.status_after,
            "qemu_exit": qemu_exit,
        }
        write_new(self.record, json.dumps(value, indent=2,
                                          ensure_ascii=True) + "\n")

    def finish(self, end=None, harness_reason=None, harness_pass=False):
        if self.finished:
            raise OracleError("the oracle was finished twice")
        self.finished = True
        error = None
        try:
            if end is None:
                end = self.qmp.poll_end()
            if end is None and harness_reason is not None:
                if self.process.poll() is not None:
                    raise OracleError("QEMU exited before the run ended")
                self.qmp.command("stop")
                end = EndState("stopped-by-harness", harness_reason)
            if end is None:
                raise OracleError("QEMU ended without a SHUTDOWN event")
            if self.process.poll() is not None:
                raise OracleError("QEMU exited before the end-of-run read")
            self._snapshot()
        except OracleError as failure:
            error = str(failure)
            if end is None:
                end = EndState("error", "oracle-error")
        status = self._end_process()
        self.qmp.close()
        qemu_exit = exit_text(status)
        end_detail = self._end_detail(end)
        allowed_end = end.kind == "guest-shutdown" or (
            harness_pass and end.kind == "stopped-by-harness")
        passed = error is None and allowed_end and qemu_exit == "0x00000000"
        if error is not None:
            detail = error
        elif not allowed_end:
            detail = end_detail
        elif qemu_exit != "0x00000000":
            detail = f"QEMU exit after quit is {qemu_exit}"
        else:
            detail = f"{end_detail}; read complete"
        self._record(passed, detail, end, qemu_exit)
        return Outcome(passed, detail, qemu_exit)


def direct_run(args):
    if args.timeout <= 0 or args.grace < 0:
        raise OracleError("the run limits are invalid")
    if not args.command:
        raise OracleError("no QEMU command was given")
    words, devices = [], ()
    for spec in args.elf_word:
        name, separator, path = spec.partition("=")
        if not separator:
            raise OracleError("--elf-word must be NAME=ELF")
        words.append(word_from_elf(name, path))
    if args.record_table:
        if not args.nm:
            raise OracleError("--record-table requires --nm")
        words += record_table_words(args.nm, args.record_table, args.harts)
    if args.words:
        extra, devices = words_from_file(args.words)
        words += extra
    config = OracleConfig(
        args.harts, args.machine_class, args.boundary_on, args.pmp,
        args.menvcfg, args.mseccfg, args.ram_base, args.ram_size,
        tuple(words), args.pmp_mode, devices)
    config.validate()
    terminal = re.compile(args.terminal_regex.encode("ascii"))
    terminal_file = pathlib.Path(args.terminal_file)
    if not terminal_file.is_file():
        raise OracleError("the terminal capture does not exist")
    started = time.monotonic()
    with open(args.qemu_output, "xb") as qemu_output:
        try:
            oracle = OracleProcess.launch(
                args.command, config, args.record, stdin=subprocess.DEVNULL,
                stdout=qemu_output, stderr=subprocess.STDOUT)
        except (OracleError, OSError):
            write_failure_record(args.record, "QEMU or QMP setup failed")
            write_new(args.exit_file, "killed:none\n")
            return 1
        deadline = started + args.timeout
        terminal_at = None
        end = None
        harness_reason = None
        while True:
            try:
                end = oracle.wait_end(0.05)
            except OracleError:
                break
            if end is not None:
                break
            if oracle.process.poll() is not None:
                break
            now = time.monotonic()
            data = terminal_file.read_bytes()
            if terminal_at is None and terminal.search(data):
                terminal_at = now
            if terminal_at is not None and now - terminal_at >= args.grace:
                harness_reason = "grace period after terminal marker"
                break
            if now >= deadline:
                harness_reason = "attempt timeout"
                break
        outcome = oracle.finish(end=end, harness_reason=harness_reason)
    status = oracle.process.returncode
    write_new(args.exit_file, launcher_exit(status) + "\n")
    return 0 if outcome.passed else 1


def result_line(path):
    try:
        value = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        result = value["result"]
        verdict, detail = result["verdict"], result["detail"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise OracleError("the oracle record is not of its schema") from error
    if value.get("schema") != SCHEMA or \
            verdict not in ("PASS", "FAIL", "NOT-ATTACHED") or \
            not isinstance(detail, str) or "\n" in detail or "\t" in detail:
        raise OracleError("the oracle record is not of its schema")
    return verdict, detail


class FakeProcess:
    """A process-shaped object for the socketpair self-test."""

    def __init__(self, status=0):
        self.status = status
        self.exited = False
        self.killed = False
        self.done = threading.Event()

    def poll(self):
        return self.status if self.exited else None

    def wait(self, timeout=None):
        if not self.done.wait(timeout):
            raise subprocess.TimeoutExpired("qemu", 0)
        return self.status

    def kill(self):
        self.killed = True
        self.status = -9
        self.exited = True
        self.done.set()


class ScriptedPeer:
    """A QMP peer whose individual defects are selected by name."""

    def __init__(self, channel, process, defect=None, end="guest-shutdown",
                 harts=2, classes=("readable", "readable", "absent"),
                 word=0x1122334455667788):
        self.channel = channel
        self.stream = channel.makefile("rwb", buffering=0)
        self.process = process
        self.defect = defect
        self.end = end
        self.harts = harts
        self.classes = dict(zip(("pmp", "menvcfg", "mseccfg"), classes))
        self.word = word
        self.status_calls = 0
        self.commands = 0
        self.thread = threading.Thread(target=self.run,
                                       name="qemu-oracle-peer", daemon=True)
        self.thread.start()

    def send(self, value):
        self.stream.write(json.dumps(value, separators=(",", ":"),
                                     ensure_ascii=True).encode("ascii") +
                          b"\r\n")

    def response(self, ident, value):
        if self.defect == "event-interleaved" and self.commands == 2:
            self.send({"event": "STOP"})
        self.send({"return": value, "id": ident})

    def shutdown(self):
        if self.end is None:
            return
        if self.end == "guest-shutdown":
            data = {"guest": True, "reason": "guest-shutdown"}
        elif self.end == "reset":
            data = {"guest": True, "reason": "guest-reset"}
        else:
            data = {"guest": False, "reason": "host-signal"}
        self.send({"event": "SHUTDOWN", "data": data})

    def hmp(self, command, cpu):
        if command == "info registers":
            return (f"\r\nCPU#{cpu}\r\n pc       {0x1000 + cpu:016x}\r\n"
                    f" mhartid  {cpu:016x}\r\n")
        if command.startswith("p /x $"):
            name = command.removeprefix("p /x $")
            register_class = ("pmp" if name.startswith(("pmpcfg", "pmpaddr"))
                              else name)
            declaration = self.classes[register_class]
            if declaration != "readable":
                if self.defect == "class-value" and name in (
                        "pmpcfg0", "menvcfg", "mseccfg"):
                    return "0x1\r\n"
                return UNKNOWN_REGISTER
            if self.defect == "mseccfg-missing" and name == "mseccfg":
                return UNKNOWN_REGISTER
            if self.defect == "required-unknown" and name == "pmpaddr7":
                return UNKNOWN_REGISTER
            if self.defect == "bad-register" and name == "pmpaddr7":
                return "17\r\n"
            value = (int(name.removeprefix("pmpaddr")) if
                name.startswith("pmpaddr") else 0x10 + cpu)
            return "0\r\n" if value == 0 else f"0x{value:x}\r\n"
        if command.startswith("xp /1gx "):
            if self.defect == "bad-memory":
                return "memory\r\n"
            value = self.word ^ (1 if self.defect == "word-mismatch" else 0)
            address = int(command.split()[-1], 0)
            return f"{address:016x}: 0x{value:016x}\r\n"
        if command.startswith(("xp /1bx ", "xp /1wx ")):
            if self.defect == "bad-device":
                return "device\r\n"
            digits = 2 if command.startswith("xp /1bx ") else 8
            value = (0xa5 if digits == 2 else 1) ^ (
                1 if self.defect == "device-mismatch" else 0)
            address = int(command.split()[-1], 0)
            return f"{address:016x}: 0x{value:0{digits}x}\r\n"
        return "unexpected\r\n"

    def run(self):
        try:
            self.send({"QMP": {
                "version": {"qemu": {"major": 8, "minor": 1, "micro": 0},
                            "package": ""},
                "capabilities": [],
            }})
            while True:
                line = self.stream.readline()
                if not line:
                    return
                message = json.loads(line)
                execute, ident = message["execute"], message["id"]
                self.commands += 1
                if execute == "qmp_capabilities":
                    self.response(ident, {})
                    if self.defect == "malformed-line":
                        self.stream.write(b"not-json\r\n")
                    else:
                        self.shutdown()
                elif self.defect == "error-reply":
                    self.send({"error": {"class": "GenericError",
                                         "desc": "planted"}, "id": ident})
                    self.defect = "error-reply-used"
                elif execute == "stop":
                    self.response(ident, {})
                    self.send({"event": "STOP"})
                elif execute == "query-status":
                    self.status_calls += 1
                    running = ((self.defect == "running-before" and
                                self.status_calls == 1) or
                               (self.defect == "running-after" and
                                self.status_calls == 2))
                    self.response(ident, {"running": running,
                                          "status": ("running" if running
                                                     else "shutdown")})
                elif execute == "query-cpus-fast":
                    count = self.harts - 1 if self.defect == "wrong-harts" \
                        else self.harts
                    self.response(ident, [
                        {"cpu-index": cpu, "thread-id": 100 + cpu,
                         "qom-path": f"/machine/cpu/{cpu}",
                         "target": "riscv64"} for cpu in range(count)])
                elif execute == "human-monitor-command":
                    command = message["arguments"]["command-line"]
                    cpu = message["arguments"]["cpu-index"]
                    if self.defect == "close-mid-read" and \
                            command == "p /x $pmpaddr7":
                        self.stream.close()
                        self.channel.close()
                        return
                    self.response(ident, self.hmp(command, cpu))
                elif execute == "quit":
                    self.response(ident, {})
                    self.process.exited = True
                    self.process.done.set()
                    self.stream.close()
                    self.channel.close()
                    return
        except (BrokenPipeError, OSError, ValueError, KeyError):
            return


def self_test(scratch):
    scratch = pathlib.Path(scratch)
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    cases = []
    word = NamedWord("entry-word", 0x80000000, 0x1122334455667788)

    devices = (DeviceWord("uart-scratch", 0x10000007, 0xa5),
               DeviceWord("aplic-s-source-9", 0x0d000024, 1))

    def run_one(name, defect=None, end="guest-shutdown",
                classes=("readable", "readable", "absent"),
                machine="test", boundary=False, harness=False, status=0,
                attached=()):
        client, server = socket.socketpair()
        process = FakeProcess(status)
        peer = ScriptedPeer(server, process, defect, end, 2, classes,
                            word.expected)
        record = scratch / f"{name}.json"
        qmp = QMPClient(client)
        oracle = OracleProcess(process, qmp, OracleConfig(
            2, machine, boundary, *classes, 0x80000000, 0x100000, (word,),
            devices=attached), record)
        finish_end = None
        if not harness:
            finish_end = oracle.wait_end(1)
        outcome = oracle.finish(end=finish_end,
                                harness_reason=("planted limit"
                                                if harness else None))
        peer.thread.join(timeout=1)
        return outcome, record.read_bytes()

    def case(name, test):
        try:
            ok, detail = test()
        except Exception as error:  # pylint: disable=broad-except
            ok, detail = False, f"raised {type(error).__name__}: {error}"
        cases.append((name, bool(ok), detail))

    case("normal sequence", lambda: (
        (outcome := run_one("normal")[0]).passed,
        outcome.detail))
    case("reset instead of shutdown", lambda: (
        not (outcome := run_one("reset", end="reset")[0]).passed and
        "reset, not a guest shutdown" in outcome.detail, outcome.detail))
    case("host requested shutdown", lambda: (
        not (outcome := run_one("host", end="host")[0]).passed and
        "host requested shutdown" in outcome.detail, outcome.detail))
    case("no event before the harness limit", lambda: (
        not (outcome := run_one("limit", end=None, harness=True)[0]).passed and
        "stopped by the harness" in outcome.detail, outcome.detail))
    case("event interleaved with a command reply", lambda: (
        (outcome := run_one("interleaved", "event-interleaved")[0]).passed,
        outcome.detail))
    for name, defect, wanted in (
            ("an error reply", "error-reply", "returned GenericError"),
            ("an unknown required register", "required-unknown",
             "pmpaddr7 of hart 0: unknown"),
            ("an unexpected register form", "bad-register",
             "pmpaddr7 of hart 0: unexpected"),
            ("an unexpected memory form", "bad-memory",
             "named word entry-word: unexpected"),
            ("a mismatching word", "word-mismatch", "value mismatch"),
            ("the machine running before the read", "running-before",
             "running before"),
            ("the machine running after the read", "running-after",
             "running after"),
            ("the wrong number of harts", "wrong-harts", "expected 2"),
            ("the peer closing in the read", "close-mid-read",
             "QMP channel closed")):
        case(name, lambda defect=defect, wanted=wanted, name=name: (
            not (outcome := run_one(re.sub(r"[^a-z]+", "-", name).strip("-"),
                                    defect)[0]).passed and
            wanted in outcome.detail, outcome.detail))
    case("an absent class answered unknown", lambda: (
        (outcome := run_one("absent",
                            classes=("absent", "readable", "absent"))[0]).passed,
        outcome.detail))
    case("an absent class answered with a value", lambda: (
        not (outcome := run_one(
            "absent-value", "class-value",
            classes=("absent", "readable", "absent"))[0]).passed and
        "readable but declared absent" in outcome.detail, outcome.detail))
    case("mseccfg unknown when declared readable", lambda: (
        not (outcome := run_one(
            "mseccfg-missing", "mseccfg-missing",
            classes=("readable", "readable", "readable"))[0]).passed and
        "mseccfg of hart 0: unknown" in outcome.detail, outcome.detail))
    case("mseccfg read when declared readable", lambda: (
        (outcome := run_one(
            "mseccfg", classes=("readable", "readable", "readable"))[0]).passed,
        outcome.detail))
    case("QEMU's status after quit", lambda: (
        not (outcome := run_one("exit", status=1)[0]).passed and
        outcome.qemu_exit == "0x00000001", outcome.detail))

    def malformed():
        try:
            run_one("malformed", "malformed-line")
        except OracleError as error:
            return "malformed" in str(error), str(error)
        return False, "the malformed line was accepted"
    case("a malformed line", malformed)

    def deterministic():
        first = run_one("repeat-a")[1]
        second = run_one("repeat-b")[1]
        value = json.loads(first)
        keys = ("schema", "result", "end", "register_classes",
                "status_before", "harts", "words", "status_after",
                "qemu_exit")
        return first == second and tuple(value) == keys, \
            "records differ" if first != second else "fixed layout"
    case("the record's fixed byte-identical layout", deterministic)

    def refused_config(word_value, wanted):
        try:
            OracleConfig(8, "test", False, "readable", "readable", "absent",
                         0x80000000, 0x1000, (word_value,)).validate()
        except OracleError as error:
            return wanted in str(error), str(error)
        return False, "the address was accepted"
    case("an unaligned address", lambda: refused_config(
        NamedWord("entry-word", 0x80000001, 0), "aligned"))
    case("an address outside RAM", lambda: refused_config(
        NamedWord("entry-word", 0x80001000, 0), "outside RAM"))

    def declared(boundary, machine, classes, mode):
        try:
            OracleConfig(8, machine, boundary, *classes, 0x80000000, 0x1000,
                         (word,), mode).validate()
        except OracleError as error:
            return str(error)
        return None
    plain = ("readable", "readable", "absent")
    smepmp = ("readable", "readable", "readable")
    for name, boundary, machine, classes, mode, wanted in (
            ("boundary-on plain", True, "k3-like", plain, "plain", None),
            ("boundary-on smepmp", True, "k3-like", smepmp, "smepmp", None),
            ("boundary-off without a mode", False, "rva23",
             ("absent", "readable", "absent"), "none", None),
            ("boundary-on plain with mseccfg readable", True, "k3-like",
             smepmp, "plain", "boundary-on run must be"),
            ("boundary-on smepmp with mseccfg absent", True, "k3-like",
             plain, "smepmp", "boundary-on run must be"),
            ("boundary-on with PMP absent", True, "k3-like",
             ("absent", "readable", "absent"), "plain",
             "boundary-on run must be"),
            ("boundary-on off k3-like", True, "plic", plain, "plain",
             "boundary-on run must be"),
            ("boundary-on without a mode", True, "k3-like", plain, "none",
             "boundary-on run must be"),
            ("boundary-off with a mode", False, "k3-like", plain, "plain",
             "declares no PMP mode"),
            ("an unknown mode", False, "k3-like", plain, "epmp",
             "not plain, smepmp, or none")):
        case(f"declaration: {name}", lambda boundary=boundary,
             machine=machine, classes=classes, mode=mode, wanted=wanted: (
                 (error := declared(boundary, machine, classes, mode),
                  error is None if wanted is None
                  else wanted in (error or ""))[1], error or "accepted"))

    case("device registers read at their widths", lambda: (
        (outcome := run_one("devices", attached=devices)[0]).passed and
        [item["value"] for item in json.loads(
            (scratch / "devices.json").read_text())["words"][1:]] ==
        [hex64(0xa5), hex64(1)], outcome.detail))
    for name, defect, wanted in (
            ("an unexpected device reply", "bad-device",
             "device word uart-scratch: unexpected"),
            ("a mismatching device value", "device-mismatch",
             "device word uart-scratch: value mismatch")):
        case(name, lambda defect=defect, wanted=wanted, name=name: (
            not (outcome := run_one(re.sub(r"[^a-z]+", "-", name).strip("-"),
                                    defect, attached=devices)[0]).passed and
            wanted in outcome.detail, outcome.detail))

    def refused_device(device, wanted):
        try:
            OracleConfig(8, "test", False, *plain, 0x80000000, 0x1000,
                         (word,), devices=(device,)).validate()
        except OracleError as error:
            return wanted in str(error), str(error)
        return False, "the device word was accepted"
    case("a device address off the list", lambda: refused_device(
        DeviceWord("uart-data", 0x10000000, None), "not on the device list"))
    case("an APLIC source past 96", lambda: refused_device(
        DeviceWord("aplic", 0x0d000000 + 4 * 97, None),
        "not on the device list"))
    case("a device value wider than its register", lambda: refused_device(
        DeviceWord("uart-scratch", 0x10000007, 0x100), "no 8-bit value"))
    case("a device name repeating a word's", lambda: refused_device(
        DeviceWord("entry-word", 0x10000007, None), "repeated name"))

    nm_text = ("0000000000000000 T _fw_start\n"
               "0000000000041230 B sbi_dcommit_harts\n"
               "0000000000052000 A _fw_end\n")

    def nm_case(text, names, wanted):
        try:
            found = parse_nm(text, names)
        except OracleError as error:
            return wanted in str(error), str(error)
        return wanted == found, str(found)
    case("nm: the symbols found", lambda: nm_case(
        nm_text, ("_fw_start", "_fw_end", RECORD_SYMBOL),
        {"_fw_start": 0, "_fw_end": 0x52000, RECORD_SYMBOL: 0x41230}))
    case("nm: a missing symbol", lambda: nm_case(
        nm_text, ("_fw_rw_start",), "has no _fw_rw_start"))
    case("nm: a symbol defined twice", lambda: nm_case(
        nm_text + "0000000000041230 b sbi_dcommit_harts\n",
        (RECORD_SYMBOL,), "defined twice"))

    def table_case():
        words = table_words(FIRMWARE_BASE + 0x41230, 8)
        first, last = words[0], words[-1]
        return (len(words) == 8 * RECORD_WORDS and
                first == NamedWord("t0-0", 0x80041230, None) and
                last == NamedWord("t7-23", 0x80041230 + 8 * (8 * 24 - 1),
                                  None)), f"{len(words)} words"
    case("the commit records' names and addresses", table_case)

    def words_file_case(content, wanted):
        path = scratch / "words.json"
        path.unlink(missing_ok=True)
        path.write_text(json.dumps(content), encoding="utf-8")
        try:
            found = words_from_file(path)
        except OracleError as error:
            return wanted in str(error), str(error)
        return found == wanted, str(found)
    good = {"schema": WORDS_SCHEMA,
            "words": [{"name": "g0-phase", "address": "0x102063130",
                       "expected": None}],
            "devices": [{"name": "uart-scratch", "address": "0x10000007",
                         "expected": "0xa5"}]}
    case("a words file", lambda: words_file_case(good, (
        (NamedWord("g0-phase", 0x102063130, None),),
        (DeviceWord("uart-scratch", 0x10000007, 0xa5),))))
    case("a words file of another schema", lambda: words_file_case(
        dict(good, schema="other"), "not of its schema"))
    case("a words-file entry with a decimal address", lambda: words_file_case(
        dict(good, words=[{"name": "w", "address": "4096",
                           "expected": None}]), "entry is malformed"))

    def not_attached_record():
        first, second = scratch / "not-attached-a.json", \
            scratch / "not-attached-b.json"
        write_not_attached_record(first)
        write_not_attached_record(second)
        verdict, detail = result_line(first)
        data = first.read_bytes()
        return data == second.read_bytes() and data.count(b"\n") == 1 and \
            verdict == "NOT-ATTACHED" and "test finisher" in detail
    case("the fixed not-attached record", lambda: (
        not_attached_record(), "one byte-identical line"))

    failures = 0
    for name, ok, detail in cases:
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    print("BE_MVP_QEMU_ORACLE_SELF_TEST: "
          f"{'PASS' if not failures else 'FAIL'} cases={len(cases)}")
    return 0 if not failures else 1


def integer(text):
    try:
        return int(text, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") \
            from error


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    commands = parser.add_subparsers(dest="command_name")
    run = commands.add_parser("run")
    run.add_argument("--record", required=True)
    run.add_argument("--exit-file", required=True)
    run.add_argument("--qemu-output", required=True)
    run.add_argument("--terminal-file", required=True)
    run.add_argument("--terminal-regex", required=True)
    run.add_argument("--timeout", type=float, required=True)
    run.add_argument("--grace", type=float, required=True)
    run.add_argument("--harts", type=int, required=True)
    run.add_argument("--machine-class", required=True)
    run.add_argument("--boundary-on", action="store_true")
    for register_class in ("pmp", "menvcfg", "mseccfg"):
        run.add_argument(f"--{register_class}", choices=REGISTER_CLASSES,
                         required=True)
    run.add_argument("--pmp-mode", choices=PMP_MODES, default="none")
    run.add_argument("--ram-base", type=integer, required=True)
    run.add_argument("--ram-size", type=integer, required=True)
    run.add_argument("--elf-word", action="append", default=[])
    run.add_argument("--record-table")
    run.add_argument("--nm")
    run.add_argument("--words")
    run.add_argument("command", nargs=argparse.REMAINDER)
    result = commands.add_parser("result")
    result.add_argument("record")
    not_attached = commands.add_parser("not-attached")
    not_attached.add_argument("record")
    args = parser.parse_args(argv[1:])
    try:
        if args.self_test:
            if args.command_name is not None or not args.scratch:
                parser.error("--self-test requires --scratch and no command")
            return self_test(args.scratch)
        if args.command_name == "run":
            if args.command[:1] == ["--"]:
                args.command = args.command[1:]
            return direct_run(args)
        if args.command_name == "result":
            verdict, detail = result_line(args.record)
            print(f"{verdict}\t{detail}")
            return 0
        if args.command_name == "not-attached":
            write_not_attached_record(args.record)
            return 0
        parser.error("run, result, not-attached, or --self-test")
    except (OracleError, OSError, ValueError) as error:
        print(f"BE_MVP_QEMU_ORACLE: FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
