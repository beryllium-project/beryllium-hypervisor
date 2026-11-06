#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Independent cross-check of tests/r7/extract-exact-image.mjs's per-symbol
# address, raw words, and resolved control-flow targets against the locked
# GNU objdump named by tests/r3/tool-lock.conf. This script never imports or
# calls extract-exact-image.mjs's own ELF parser: it disassembles the same
# real GCC and Clang R5 images (build/r5/{gcc,clang}/beryllium.elf) with a
# wholly separate tool, parses objdump's own text output with a small
# self-contained JS reader, and only then compares the two independently
# derived views for the eleven required symbols. It also independently
# recomputes each image's SHA-256 from the raw file bytes, rather than
# trusting the extractor's own recorded digest.
#
# Every resolved control-flow target is confirmed only by objdump's own
# decoded operand or comment field for that exact instruction. The
# instruction's address column and its raw encoding word are deliberately
# excluded from that evidence, so a target forged as pc+0, as the instruction
# address, or as the raw encoding word cannot confirm itself.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
lock="$root/tests/r3/tool-lock.conf"

objdump_command=$(/usr/bin/sed -n 's/^R3_TOOL_cross_objdump_command=//p' "$lock")
objdump_resolved=$(/usr/bin/sed -n 's/^R3_TOOL_cross_objdump_resolved=//p' "$lock")
objdump_sha256=$(/usr/bin/sed -n 's/^R3_TOOL_cross_objdump_sha256=//p' "$lock")
node_command=$(/usr/bin/sed -n 's/^R3_TOOL_node_command=//p' "$lock")
node_resolved=$(/usr/bin/sed -n 's/^R3_TOOL_node_resolved=//p' "$lock")
node_sha256=$(/usr/bin/sed -n 's/^R3_TOOL_node_sha256=//p' "$lock")

[ -n "$objdump_command" ] && [ -n "$objdump_resolved" ] && [ -n "$objdump_sha256" ] || {
	printf 'R7 disassembly check rejects unbound cross_objdump bindings\n' >&2
	exit 1
}
[ -n "$node_command" ] && [ -n "$node_resolved" ] && [ -n "$node_sha256" ] || {
	printf 'R7 disassembly check rejects unbound node bindings\n' >&2
	exit 1
}
case "$objdump_command" in
	/*) ;;
	*)
		printf 'R7 disassembly check rejects a non-absolute objdump command\n' >&2
		exit 1
		;;
esac
[ -f "$objdump_command" ] && [ -x "$objdump_command" ] || {
	printf 'R7 disassembly check rejects a missing or non-executable objdump command\n' >&2
	exit 1
}
resolved=$(/usr/bin/readlink -f "$objdump_command")
[ "$resolved" = "$objdump_resolved" ] || {
	printf 'R7 disassembly check rejects objdump resolved path drift: expected %s, got %s\n' \
		"$objdump_resolved" "$resolved" >&2
	exit 1
}
actual=$(/usr/bin/sha256sum "$resolved" | /usr/bin/cut -d' ' -f1)
[ "$actual" = "$objdump_sha256" ] || {
	printf 'R7 disassembly check rejects objdump executable digest drift\n' >&2
	exit 1
}
resolved_node=$(/usr/bin/readlink -f "$node_command")
[ "$resolved_node" = "$node_resolved" ] || {
	printf 'R7 disassembly check rejects node resolved path drift: expected %s, got %s\n' \
		"$node_resolved" "$resolved_node" >&2
	exit 1
}
actual=$(/usr/bin/sha256sum "$resolved_node" | /usr/bin/cut -d' ' -f1)
[ "$actual" = "$node_sha256" ] || {
	printf 'R7 disassembly check rejects node executable digest drift\n' >&2
	exit 1
}

/usr/bin/mkdir -p "$root/build/r7/home" "$root/build/r7/tmp" "$root/build/r7/extract"

# The comparator is a single script, run in both --self-test and the default
# real-image mode: R7_DISASM_MODE selects the branch, so the parsing and
# comparison logic under test is never duplicated or forked between modes.
read -r -d '' node_script <<'NODE_SCRIPT' || true
const fs = require('node:fs');
const crypto = require('node:crypto');

// Parse GNU objdump -d text into independent per-symbol label addresses and
// per-instruction-address raw hex/line lookups. This never reads the ELF
// container itself: it trusts only objdump's own textual disassembly.
function parseObjdump(text) {
  const labels = new Map();
  const labelRe = /^([0-9a-f]+) <([^>]+)>:$/gm;
  let m;
  while ((m = labelRe.exec(text))) {
    const name = m[2];
    const addr = parseInt(m[1], 16);
    if (!labels.has(name)) labels.set(name, []);
    labels.get(name).push(addr)
  }
  const instructions = new Map();
  const instrRe = /^\s*([0-9a-f]+):\t([0-9a-f]+)\s*\t(.*)$/gm;
  while ((m = instrRe.exec(text))) {
    const addr = parseInt(m[1], 16);
    if (instructions.has(addr)) throw new Error(`objdump text: instruction address ${m[1]} appears more than once`);
    // `hex` is the raw encoding column, `text` is objdump's own decoded
    // mnemonic/operand/comment column, and they are kept strictly apart: the
    // address column and the raw word are never usable as target evidence.
    instructions.set(addr, { hex: m[2].toLowerCase(), text: m[3], line: m[0] })
  }
  return { labels, instructions }
}

// The decoded evidence objdump offers for one instruction, split into the
// operand field (after the mnemonic, before any comment) and the comment
// field (after `#`). A resolved target may be confirmed only by these two:
// never by the instruction's own address column, never by its raw encoding
// word, and never by a neighbouring instruction's text. That distinction is
// the whole point of this cross-check -- a forged target of pc+0, of the
// instruction address, or of the raw word must not be confirmable by the
// very bytes it claims to describe.
function decodedEvidence(entry) {
  const text = entry.text;
  const hash = text.indexOf('#');
  const body = hash < 0 ? text : text.slice(0, hash);
  const comment = hash < 0 ? '' : text.slice(hash + 1);
  const separator = body.search(/[\s,(]/);
  const operands = separator < 0 ? '' : body.slice(separator);
  return `${operands} ${comment}`
}

// Independently re-derive and compare one extracted image's ELF identity,
// per-symbol address, raw units, and resolved targets against objdump's own
// disassembly. Throws on the first mismatch; never silently tolerates one.
function checkImage(image, elfBytes, disasmText, label) {
  if (image.schema !== 'be-r7-exact-image-v1')
    throw new Error(`${label}: unexpected extraction schema ${image.schema}`)
  const actualSha256 = crypto.createHash('sha256').update(elfBytes).digest('hex');
  if (actualSha256 !== image.elf.sha256)
    throw new Error(`${label}: ELF sha256 mismatch: declared ${image.elf.sha256}, actual ${actualSha256}`)
  const { labels, instructions } = parseObjdump(disasmText);
  let words = 0;
  let targets = 0;
  for (const symbol of image.symbols) {
    const addresses = labels.get(symbol.name) || [];
    if (addresses.length === 0) throw new Error(`${label}: symbol ${symbol.name} not found in objdump output`)
    if (addresses.length > 1) throw new Error(`${label}: symbol ${symbol.name} is labeled more than once in objdump output`)
    const [objdumpAddr] = addresses;
    const jsonAddr = parseInt(symbol.address, 16);
    if (objdumpAddr !== jsonAddr)
      throw new Error(`${label}: symbol ${symbol.name} address mismatch: json ${symbol.address}, objdump 0x${objdumpAddr.toString(16)}`)
    for (const unit of symbol.units) {
      const instrAddr = jsonAddr + unit.offset;
      const entry = instructions.get(instrAddr);
      if (!entry)
        throw new Error(`${label}: symbol ${symbol.name} offset ${unit.offset}: no objdump instruction at 0x${instrAddr.toString(16)}`)
      const expectedHex = unit.hex.replace(/^0x/, '').toLowerCase().padStart(unit.length * 2, '0');
      if (entry.hex !== expectedHex)
        throw new Error(`${label}: symbol ${symbol.name} offset ${unit.offset}: word mismatch: json ${expectedHex}, objdump ${entry.hex}`)
      words += 1;
    }
    for (const target of symbol.targets) {
      const instrAddr = jsonAddr + target.offset;
      const entry = instructions.get(instrAddr);
      if (!entry)
        throw new Error(`${label}: symbol ${symbol.name} offset ${target.offset}: no objdump instruction at 0x${instrAddr.toString(16)} for target check`)
      const expectedTarget = parseInt(target.address, 16);
      const evidence = decodedEvidence(entry);
      const tokens = evidence.match(/\b[0-9a-f]{6,16}\b/g) || [];
      const confirmed = tokens.some((tok) => parseInt(tok, 16) === expectedTarget);
      if (!confirmed)
        throw new Error(`${label}: symbol ${symbol.name} offset ${target.offset}: resolved target ${target.address} is not named by objdump's decoded operand or comment for the instruction at 0x${instrAddr.toString(16)}`)
      targets += 1;
    }
  }
  return { words, targets }
}

// A small synthetic fixture exercising the same textual conventions as real
// objdump -d output (label line, tab-separated address/hex/mnemonic, an
// operand-carried target, and a trailing "# <addr> <sym>" annotation), used
// only by --self-test.
function buildFixture() {
  const elfBytes = Buffer.from('synthetic-r7-disassembly-fixture');
  const sha256 = crypto.createHash('sha256').update(elfBytes).digest('hex');
  const image = {
    schema: 'be-r7-exact-image-v1',
    toolchain: 'self-test',
    elf: { sha256, sizeBytes: elfBytes.length },
    symbols: [{
      name: 'fixture_symbol_one',
      address: '0x80001000',
      size: 12,
      units: [
        { offset: 0, length: 4, hex: '0x00000013' },
        { offset: 4, length: 4, hex: '0x00028513' },
        { offset: 8, length: 4, hex: '0x0080006f' }
      ],
      targets: [
        { offset: 4, format: 'auipc-pair', address: '0x80001010' },
        { offset: 8, format: 'J-type', address: '0x80001010' }
      ]
    }]
  };
  const disasmText = [
    '0000000080001000 <fixture_symbol_one>:',
    '    80001000:\t00000013          \tnop',
    '    80001004:\t00028513          \tmv\ta0,t0 # 80001010 <fixture_symbol_two>',
    '    80001008:\t0080006f          \tj\t80001010 <fixture_symbol_two>',
    ''
  ].join('\n');
  return { image, elfBytes, disasmText }
}

function expectRejected(label, mutate) {
  const fixture = buildFixture();
  mutate(fixture);
  let threw = false;
  try {
    checkImage(fixture.image, fixture.elfBytes, fixture.disasmText, label)
  } catch {
    threw = true
  }
  if (!threw) throw new Error(`self-test: mutation '${label}' was not rejected`)
}

function runSelfTest() {
  const baseline = buildFixture();
  checkImage(baseline.image, baseline.elfBytes, baseline.disasmText, 'self-test-baseline');

  const mutations = [
    ['wrong-word', (f) => { f.image.symbols[0].units[0].hex = '0x00000067' }],
    ['wrong-symbol-address', (f) => { f.image.symbols[0].address = '0x80009000' }],
    ['missing-symbol', (f) => { f.image.symbols[0].name = 'fixture_symbol_absent' }],
    ['missing-instruction', (f) => {
      f.disasmText = f.disasmText.split('\n').filter((line) => !line.includes('80001004:')).join('\n')
    }],
    ['unconfirmed-target', (f) => { f.image.symbols[0].targets[0].address = '0x8000ffff' }],
    // The three attacks the address/raw-word columns would otherwise confirm.
    ['target-forged-as-instruction-address', (f) => { f.image.symbols[0].targets[0].address = '0x80001004' }],
    ['target-forged-as-raw-encoding-word', (f) => { f.image.symbols[0].targets[0].address = '0x00028513' }],
    ['target-forged-as-pc-plus-zero', (f) => {
      f.image.symbols[0].targets.push({ offset: 0, format: 'J-type', address: '0x80001000' })
    }],
    // A target named only by a neighbouring instruction's text is not
    // evidence for this instruction.
    ['target-confirmed-by-another-instruction', (f) => {
      f.disasmText = f.disasmText.replace('\tj\t80001010 <fixture_symbol_two>', '\tj\t80001020 <fixture_symbol_three>')
    }],
    ['elf-sha256-mismatch', (f) => { f.image.elf.sha256 = '0'.repeat(64) }],
    ['duplicate-label', (f) => {
      f.disasmText = `${f.disasmText}0000000080001000 <fixture_symbol_one>:\n`
    }]
  ];
  for (const [label, mutate] of mutations) expectRejected(label, mutate);
  console.log(`BE_R7_DISASSEMBLY_CHECK_SELF_TEST: PASS baseline=accepted mutations=${mutations.length} all-rejected=yes`)
}

function runCheck() {
  const toolchains = ['gcc', 'clang'];
  let totalWords = 0;
  let totalTargets = 0;
  let totalSymbols = 0;
  for (const toolchain of toolchains) {
    const upper = toolchain.toUpperCase();
    const image = JSON.parse(fs.readFileSync(process.env[`R7_${upper}_JSON`], 'utf8'));
    const elfBytes = fs.readFileSync(process.env[`R7_${upper}_ELF`]);
    const disasmText = fs.readFileSync(process.env[`R7_${upper}_DISASM`], 'utf8');
    const { words, targets } = checkImage(image, elfBytes, disasmText, toolchain);
    totalWords += words;
    totalTargets += targets;
    totalSymbols += image.symbols.length;
  }
  console.log(`BE_R7_DISASSEMBLY_CHECK: PASS toolchains=${toolchains.length} symbols=${totalSymbols} words=${totalWords} targets=${totalTargets}`)
}

const mode = process.env.R7_DISASM_MODE;
if (mode === 'self-test') runSelfTest();
else if (mode === 'check') runCheck();
else throw new Error(`unknown R7_DISASM_MODE: ${mode}`)
NODE_SCRIPT

self_test=0
if [ "${1:-}" = "--self-test" ]; then
	self_test=1
fi

if [ "$self_test" -eq 1 ]; then
	/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
		HOME="$root/build/r7/home" TMPDIR="$root/build/r7/tmp" \
		R7_DISASM_MODE=self-test \
		"$node_command" <<<"$node_script"
	exit 0
fi

for toolchain in gcc clang; do
	elf="$root/build/r5/$toolchain/beryllium.elf"
	json="$root/build/r7/extract/$toolchain.json"
	[ -f "$elf" ] || {
		printf 'R7 disassembly check: missing %s (run tests/r5/run-make.sh r5-evidence first)\n' "$elf" >&2
		exit 1
	}
	[ -f "$json" ] || {
		printf 'R7 disassembly check: missing %s (run extract-exact-image.mjs first)\n' "$json" >&2
		exit 1
	}
	disasm="$root/build/r7/extract/$toolchain-objdump.txt"
	/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
		HOME="$root/build/r7/home" TMPDIR="$root/build/r7/tmp" \
		"$objdump_command" -d "$elf" >"$disasm"
done

/usr/bin/env -i PATH=/usr/bin LANG=C LC_ALL=C \
	HOME="$root/build/r7/home" TMPDIR="$root/build/r7/tmp" \
	R7_DISASM_MODE=check \
	R7_GCC_JSON="$root/build/r7/extract/gcc.json" \
	R7_GCC_DISASM="$root/build/r7/extract/gcc-objdump.txt" \
	R7_GCC_ELF="$root/build/r5/gcc/beryllium.elf" \
	R7_CLANG_JSON="$root/build/r7/extract/clang.json" \
	R7_CLANG_DISASM="$root/build/r7/extract/clang-objdump.txt" \
	R7_CLANG_ELF="$root/build/r5/clang/beryllium.elf" \
	"$node_command" <<<"$node_script"
