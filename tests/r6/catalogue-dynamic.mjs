// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Dynamic image-fixture rows, the control row, and implementation handlers.
//
// PARTITION-OWNED by the R6 dynamic-fixture agent.  The rows below were
// generated from the exact accepted R6 plan so that the shared framework can
// be validated before any fixture exists; they are the normative metadata and
// must not be renumbered, re-classed, re-sloted, or re-worded without a plan
// revision.  The dynamic agent implements `dynamicHandlers`, the per-fixture
// directories under tests/r6/fixtures/<id>/, tests/r6/check-dynamic.mjs, and
// tests/r6/run-qemu.sh, and edits no shared file.
//
// Every dynamic fixture must pass L3, L4, and L5 unchanged, reach exactly its
// declared L6 disposition, differ from the control image by exactly its
// declared delta at L8, and terminate fail-closed at L10.  A fixture that
// fails earlier is a fixture-design failure, not a result.

import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { consoleSequence, acceptedForbiddenMarkers, dynamicForbiddenMarkers }
  from './catalogue-schema.mjs'
import { root } from './tool-lock.mjs'

// The accepted image checker's frozen-fixture assertion, rendered exactly.
// tests/r5/check-image.mjs prints the guest physical address and both words in
// lower-case hexadecimal with no `0x` prefix, and the words zero-padded to
// eight digits.
const slotMessage = (domain, slot, defectWord, baseWord) =>
  `{toolchain}: ${domain} fixture slot ${slot.toString(16)} is ` +
  `${defectWord}, expected ${baseWord}`

const dynamicEntry = ({ classes, ...entry }) => ({
  partition: 'dynamic',
  handler: 'dynamic',
  declared_layer: 'L10',
  outcome: 'terminated-fail-closed',
  builds: true,
  expected_link: 'pass',
  message_completeness: 'complete',
  qemu: true,
  runs: 2,
  forbidden_markers: dynamicForbiddenMarkers,
  coverage: classes,
  ...entry
})

// One frozen guest instruction word is overwritten in a copy of
// arch/riscv/be/r5-guest.S, so the accepted image checker rejects the image
// with exactly one allowlisted assertion and L7 cannot run.
const guestWord = ({ domain, slot, file_offset, base_word, defect_word, classes,
  effect, ...entry }) => {
  const message = slotMessage(domain, slot, defect_word, base_word)

  return dynamicEntry({
    base: 'arch/riscv/be/r5-guest.S',
    defect: {
      kind: 'guest-word',
      summary: `${domain} ${slot.toString(16)}: ${base_word} -> ${defect_word}`,
      effect
    },
    accepted_image_check: { disposition: 'reject-with', messages: [message] },
    expected_messages: [message, `BE_R5:FAIL ${classes[0].class}`],
    declared_delta: {
      kind: 'guest-word',
      domain,
      slot,
      file_offset,
      base_word,
      defect_word,
      bytes: 4
    },
    classes,
    ...entry
  })
}

// Monitor logic is changed in a copy of an accepted monitor source.  The
// default base is arch/riscv/be/r5-runtime.c; D-15 overrides it with
// arch/riscv/be/r5-trap.S per plan revision R6-A, because the accepted switch
// tail rejects its arming before SRET.  No frozen guest word, pinned symbol
// address, marker set, call site, HGATP writer, or fence site moves in either
// case, so the accepted image checker must still pass and L7 runs.
const monitorRange = ({ classes, ...entry }) => dynamicEntry({
  base: 'arch/riscv/be/r5-runtime.c',
  accepted_image_check: { disposition: 'pass', messages: null },
  expected_messages: [`BE_R5:FAIL ${classes[0].class}`],
  declared_delta: {
    kind: 'monitor-range',
    sections: ['.monitor.text', '.monitor.rodata', '.monitor.data'],
    bytes: null
  },
  classes,
  ...entry
})

const primary = (name) => [{ class: name, role: 'primary' }]
const secondary = (name) => [{ class: name, role: 'secondary' }]

export const dynamicEntries = [
  guestWord({
    id: 'D-01',
    domain: 'protected',
    slot: 0x4001102c,
    file_offset: 0x3302c,
    base_word: '00200893',
    defect_word: '00900893',
    effect: 'addi a7,zero,9; ecall at 0x40011030, cause 10, a7=9',
    classes: primary('event-args'),
    last_marker: 'BE_R5:06',
    notes: 'Wrong event identifier on the protected switch ecall.'
  }),
  guestWord({
    id: 'D-02',
    domain: 'protected',
    slot: 0x40011004,
    file_offset: 0x33004,
    base_word: '03300313',
    defect_word: '03400313',
    effect: 'protected private page holds 52 at the first protected exit',
    classes: primary('backing'),
    last_marker: 'BE_R5:04',
    notes: 'Private-page backing value diverges from the accepted expectation.'
  }),
  guestWord({
    id: 'D-03',
    domain: 'protected',
    slot: 0x40011010,
    file_offset: 0x33010,
    base_word: '400003b7',
    defect_word: '400033b7',
    effect: 'cause 21 at 0x40011014, stval=0x40003000, htval=0x10000c00',
    classes: primary('gva'),
    last_marker: 'BE_R5:04',
    notes: 'Denied load moves to an unmapped guest virtual address.'
  }),
  guestWord({
    id: 'D-04',
    domain: 'protected',
    slot: 0x40011014,
    file_offset: 0x33014,
    base_word: '0003a483',
    defect_word: '0093a023',
    effect: 'sw s1,0(t2); cause 23 where 21 is expected, stval=0x40000000',
    classes: primary('cause'),
    last_marker: 'BE_R5:04',
    notes: 'Mutates the denied-load slot itself; D-07 mutates the lui that ' +
      'establishes t2 for it.'
  }),
  guestWord({
    id: 'D-05',
    domain: 'protected',
    slot: 0x40011028,
    file_offset: 0x33028,
    base_word: '00040513',
    defect_word: '00038067',
    effect: 'jr t2 into read-only shared 0x40002000, cause 20',
    classes: secondary('cause'),
    last_marker: 'BE_R5:06',
    notes: 'Deliberate secondary coverage of cause; D-04 is the primary.'
  }),
  guestWord({
    id: 'D-06',
    domain: 'protected',
    slot: 0x40011028,
    file_offset: 0x33028,
    base_word: '00040513',
    defect_word: '68002573',
    effect: 'csrr a0,hgatp from VS, cause 22 at 0x40011028',
    classes: secondary('cause'),
    last_marker: 'BE_R5:06',
    notes: 'First measurement. The plan asserts cause 22 (virtual ' +
      'instruction). If QEMU reports cause 2 instead, the expected class is ' +
      'still cause, but the recorded architectural justification is then ' +
      'false and the plan must be revised. The harness must not relax the ' +
      'expectation at run time.'
  }),
  guestWord({
    id: 'D-07',
    domain: 'protected',
    slot: 0x40011010,
    file_offset: 0x33010,
    base_word: '400003b7',
    defect_word: '0003a483',
    effect: 't2=0 at entry, cause 21 at 0x40011010, stval=0, htval=0',
    classes: primary('pc'),
    last_marker: 'BE_R5:04',
    notes: 'Fault program counter diverges from the accepted expectation.'
  }),
  guestWord({
    id: 'D-08',
    domain: 'management',
    slot: 0x40010028,
    file_offset: 0x32028,
    base_word: '00040513',
    defect_word: '00000513',
    effect: 'R4 private event reports a0=0, so be_r4_handle_trap returns ' +
      'event-args and the R5 runtime terminates with import',
    classes: primary('import'),
    last_marker: 'BE_R4:02',
    notes: 'The only fixture whose terminal class is produced by the R4 ' +
      'import boundary rather than an R5 check.'
  }),
  guestWord({
    id: 'D-09',
    domain: 'management',
    slot: 0x40010034,
    file_offset: 0x32034,
    base_word: '00300893',
    defect_word: '00400893',
    effect: 'final ecall carries event id 4',
    classes: secondary('event-args'),
    last_marker: 'BE_R5:10',
    notes: 'Deliberate secondary coverage of event-args; D-01 is the primary.'
  }),
  monitorRange({
    id: 'D-10',
    defect: {
      kind: 'c-argument',
      summary: 'switch_domain passes BE_R3_MANAGEMENT_HGATP to ' +
        'be_r5_arch_install_root instead of pending.target.hgatp'
    },
    classes: primary('target-readback'),
    last_marker: 'BE_R5:02',
    notes: 'Guest is never entered.'
  }),
  monitorRange({
    id: 'D-11',
    defect: {
      kind: 'c-statement',
      summary: 'one added line after be_r5_arch_install_root sets ack.fence_completed = 0U'
    },
    classes: primary('fence'),
    last_marker: 'BE_R5:02',
    notes: 'The safe dynamic skipped-fence probe. The fence is still ' +
      'executed, so no unfenced guest ever runs; only the acknowledgement is ' +
      'withheld. Not placed in r5-trap.S, whose instruction order the ' +
      'accepted image checker pins.'
  }),
  monitorRange({
    id: 'D-12',
    defect: {
      kind: 'c-statement',
      summary: 'one added line after be_r5_arch_install_root sets ' +
        'ack.source_hgatp = ack.hgatp_written'
    },
    classes: primary('hgatp'),
    last_marker: 'BE_R5:02',
    notes: 'Not placed in r5-trap.S, for the same reason as D-11.'
  }),
  monitorRange({
    id: 'D-13',
    defect: {
      kind: 'c-control-flow',
      summary: 'the single be_r5_publish_target call site is placed in a ' +
        'bounded loop whose trip count is 2'
    },
    classes: primary('invalid-phase'),
    last_marker: 'BE_R5:04',
    notes: 'A static volatile int trip counter initialised to 2 guards a ' +
      'while loop around the existing call, so neither GCC nor Clang can ' +
      'prove the trip count at -O2 or unroll it into two references. ' +
      'check-fixtures.mjs asserts exactly one <be_r5_publish_target> ' +
      'reference in the built image, so an optimiser change is reported ' +
      'rather than silently turned into a different fixture.'
  }),
  monitorRange({
    id: 'D-14',
    defect: {
      kind: 'c-argument',
      summary: 'be_r5_arch_reset_target is passed the management trusted SP 0x80227000'
    },
    classes: primary('saved-page'),
    last_marker: 'BE_R5:03',
    notes: 'Primary saved-page fixture at the switch_domain check; H-05 is ' +
      'the secondary at validate_entry_state.'
  }),
  monitorRange({
    id: 'D-15',
    base: 'arch/riscv/be/r5-trap.S',
    defect: {
      kind: 'asm-insertion',
      summary: 'be_r5_switch_tail arms hvip[2] then hie[2] with csrsi, after ' +
        'every entry-control readback and the last frame restore, immediately ' +
        'before .option pop and the jump to be_r5_enter_guest_tail'
    },
    // Plan revision R6-B, pinned exactly.  The two inserted instructions are
    // absorbed by the alignment padding the accepted tail already emits, so
    // `.monitor.text` keeps its accepted allocated size and nothing after the
    // insertion point moves; the flat-image delta is ten bytes in two runs,
    // because the byte between the relocated jump's opcode byte and its
    // changed immediate byte is coincidentally equal in both images.  The
    // top-level `bytes` stays null: the plan withdrew the fixed byte-growth
    // claim it once made, and the per-toolchain measurement below is the
    // flat-image delta rather than a section that grew.  L8 fails closed on
    // any other run, count, offset, or size, and must never widen, recompute,
    // or adopt an observed delta at run time.
    declared_delta: {
      kind: 'monitor-range',
      sections: ['.monitor.text', '.monitor.rodata', '.monitor.data'],
      bytes: null,
      layout: {
        gcc: {
          runs: [{ start: 30032, length: 9 }, { start: 30042, length: 1 }],
          bytes: 10,
          monitor_text_size: 0x7610
        },
        clang: {
          runs: [{ start: 30080, length: 9 }, { start: 30090, length: 1 }],
          bytes: 10,
          monitor_text_size: 0x7640
        }
      },
      // The one recorded difference the plan allows: a symbol-table size,
      // which is neither an address, an allocated-section size, nor a
      // flat-image byte.  Every other fixed or required allocated symbol keeps
      // its control address and its control size.
      symbol_sizes: { be_r5_switch_tail: { control: 212, fixture: 220 } }
    },
    classes: primary('interrupt'),
    last_marker: 'BE_R5:04',
    notes: 'Plan revision R6-A. The only dynamic fixture that enters the ' +
      'guest, preempted at 0x40011000 before any protected instruction ' +
      'retires, so the trace holds the two management VS entries only. ' +
      'Asserts scause=0x8000000000000002; a different observed cause is ' +
      'wrong-error-class and requires a plan revision, not a run-time ' +
      'relaxation. It cannot live in r5-runtime.c: the accepted ' +
      'be_r5_switch_tail re-reads hie and hvip and rejects a non-zero value ' +
      'before SRET, so any arming inside switch_domain terminates as ' +
      'entry-controls. The two csrsi instructions take a 5-bit immediate, ' +
      'read and write no GPR, add no call, no HGATP write, and no fence, and ' +
      'sit after the pinned readback order and after the eighth frame ' +
      'restore pair, so the accepted image checker still passes unchanged. ' +
      'Plan revision R6-B pins the resulting image exactly: ten differing ' +
      'flat-image bytes in two runs per toolchain, an unchanged .monitor.text ' +
      'allocated size, and unchanged addresses for every symbol L8 fixes or ' +
      'requires, with be_r5_switch_tail\'s symbol-table size the only ' +
      'permitted recorded difference. Non-allocated debug and symbol-table ' +
      'content is out of scope for L8 by construction and is never pinned.'
  })
]

// The control is the unmutated accepted build driven through the R6 path.  It
// is harness self-validation only: it is not new R5 evidence and not an R5
// re-acceptance.  Its L8 delta is the identity, which is what proves the R6
// differential checker is measuring the right two images.
export const controlEntries = [
  {
    id: 'C-01',
    partition: 'control',
    handler: 'control',
    base: 'tests/r5',
    defect: null,
    declared_layer: 'L10',
    outcome: 'control-accepted',
    builds: true,
    expected_link: 'pass',
    accepted_image_check: { disposition: 'pass', messages: null },
    expected_messages: consoleSequence,
    message_completeness: 'complete',
    declared_delta: { kind: 'identity', bytes: 0 },
    qemu: true,
    runs: 2,
    last_marker: 'BE_R5:12',
    forbidden_markers: acceptedForbiddenMarkers,
    coverage: [],
    notes: 'Unmutated accepted sources built and run through the R6 path. ' +
      'Must reproduce the exact 22-line accepted sequence with QEMU status 0.'
  }
]

// Implementation handler interface.  tests/r6/handlers.mjs enforces the exact
// shape; a handler that is not implemented must fail explicitly rather than
// report a success-shaped placeholder.
//
// Everything below is fixture behaviour, not catalogue metadata: the rows
// above stay normative and the handlers only prove that the checked-in
// per-fixture declarations agree with them, byte for byte.

const fail = (condition, text) => {
  if (!condition) throw new Error(`R6 dynamic: ${text}`)
}
const canonical = (value) => JSON.stringify(value)
const digestOf = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')
const value16 = /^[0-9a-f]{16}$/u

// Line-level difference by longest common subsequence.  The declared change of
// every dynamic fixture is checked against the recomputed hunks rather than
// against an opaque digest, so a reviewer reads the exact removed and added
// lines in the manifest and the handler proves they are the real difference.
const diffHunks = (base, defect) => {
  const n = base.length
  const m = defect.length
  const width = m + 1
  const table = new Uint32Array((n + 1) * width)

  for (let i = n - 1; i >= 0; i -= 1)
    for (let j = m - 1; j >= 0; j -= 1)
      table[i * width + j] = base[i] === defect[j]
        ? table[(i + 1) * width + j + 1] + 1
        : Math.max(table[(i + 1) * width + j], table[i * width + j + 1])

  const hunks = []
  let current = null
  let i = 0
  let j = 0
  const flush = () => {
    if (current !== null) hunks.push(current)
    current = null
  }
  const open = () => {
    if (current === null) current = { line: i + 1, removed: [], added: [] }
  }

  while (i < n && j < m) {
    if (base[i] === defect[j]) {
      flush()
      i += 1
      j += 1
      continue
    }
    open()
    if (table[(i + 1) * width + j] >= table[i * width + j + 1]) {
      current.removed.push(base[i])
      i += 1
    } else {
      current.added.push(defect[j])
      j += 1
    }
  }
  while (i < n) { open(); current.removed.push(base[i]); i += 1 }
  while (j < m) { open(); current.added.push(defect[j]); j += 1 }
  flush()
  return hunks
}

const checkRegisters = (id, registers, where) => {
  fail(registers !== null && typeof registers === 'object',
    `${id} declares no ${where}`)
  fail(canonical(Object.keys(registers).sort()) ===
    canonical(['a0', 'a1', 'a6', 'a7', 's0', 's1']),
    `${id} ${where} does not declare exactly s0,s1,a0,a1,a6,a7`)
  for (const [name, held] of Object.entries(registers))
    fail(value16.test(held), `${id} ${where} ${name} is not a 16-digit value`)
}

// Every checked-in dynamic declaration, proved against the catalogue row, the
// accepted source it mutates, and itself.  A manifest that agrees with none of
// those is refused before a scratch tree exists.
const validateManifest = (row) => {
  const directory = resolve(root, `tests/r6/fixtures/${row.id}`)
  const manifestPath = resolve(directory, 'fixture.json')

  fail(existsSync(manifestPath), `tests/r6/fixtures/${row.id}/fixture.json is absent`)

  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
  const identity = row.declared_delta.kind === 'identity'

  fail(manifest.schema === 'be-r6-fixture-v1', `${row.id} manifest schema differs`)
  fail(manifest.spdx_license_identifier === 'GPL-3.0-only',
    `${row.id} manifest declares no GPL-3.0-only licence`)
  fail(manifest.copyright ===
    'Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>',
    `${row.id} manifest declares no responsible-human copyright`)
  fail(manifest.id === row.id, `${row.id} manifest declares identifier ${manifest.id}`)
  fail(manifest.partition === row.partition,
    `${row.id} manifest declares partition ${manifest.partition}`)
  fail(canonical(manifest.declared_delta) === canonical(row.declared_delta),
    `${row.id} manifest delta differs from the catalogue row`)
  fail(canonical(manifest.accepted_image_check) === canonical(row.accepted_image_check),
    `${row.id} manifest L6 disposition differs from the catalogue row`)

  const defects = readdirSync(directory).filter((name) => name.endsWith('.defect')).sort()
  const expected = manifest.expected

  fail(expected !== null && typeof expected === 'object',
    `${row.id} manifest declares no run expectation`)
  fail(expected.outcome === row.outcome,
    `${row.id} declares outcome ${expected.outcome}, expected ${row.outcome}`)
  fail(expected.last_marker === row.last_marker,
    `${row.id} declares last marker ${expected.last_marker}, expected ${row.last_marker}`)
  fail(expected.qemu_status === 0, `${row.id} declares a non-zero expected status`)
  fail(expected.shutdown === 'monitor-issued-srst',
    `${row.id} declares shutdown ${expected.shutdown}`)
  fail(canonical(expected.forbidden_markers) === canonical(row.forbidden_markers),
    `${row.id} forbidden markers differ from the catalogue row`)
  fail(typeof expected.guest_entered === 'boolean',
    `${row.id} does not declare whether the protected guest is entered`)
  fail(Object.hasOwn(expected, 'preempted_entry'),
    `${row.id} does not declare whether a VS entry is preempted before it retires`)

  const marker = consoleSequence.findIndex((line) => line.startsWith(`${row.last_marker} `))

  fail(marker >= 0, `${row.id} last marker is not in the accepted console sequence`)

  const prefix = consoleSequence.slice(0, marker + 1)

  if (identity) {
    fail(expected.error_class === null, `${row.id} is the control and declares an error class`)
    fail(canonical(expected.console) === canonical(consoleSequence),
      `${row.id} does not declare the exact accepted 22-line console`)
    fail(manifest.defect_file === null && manifest.base === null &&
      manifest.base_sha256 === null && defects.length === 0,
      `${row.id} is the identity delta and carries a defect declaration`)
  } else {
    const errorClass = row.coverage[0].class

    fail(expected.error_class === errorClass,
      `${row.id} declares class ${expected.error_class}, expected ${errorClass}`)
    fail(canonical(expected.console) === canonical([...prefix, `BE_R5:FAIL ${errorClass}`]),
      `${row.id} console is not the accepted prefix through ${row.last_marker} ` +
      `followed by BE_R5:FAIL ${errorClass}`)
    fail(canonical(row.expected_messages.slice(-1)) === canonical([`BE_R5:FAIL ${errorClass}`]),
      `${row.id} catalogue message list does not end in its declared failure`)
    fail(defects.length === 1 && manifest.defect_file === defects[0],
      `${row.id} carries ${defects.length} defect copies or names another file`)
    fail(manifest.base === row.base, `${row.id} manifest base differs from the catalogue row`)

    const base = resolve(root, row.base)
    const defect = resolve(directory, manifest.defect_file)

    fail(existsSync(base), `${row.id} base ${row.base} is absent from the worktree`)
    fail(manifest.base_sha256 === digestOf(base),
      `${row.id} base digest drift; the accepted source moved under the fixture`)
    fail(manifest.defect_sha256 === digestOf(defect), `${row.id} defect copy digest drift`)

    const head = readFileSync(defect, 'utf8').split('\n').slice(0, 4).join('\n')

    fail(head.includes('SPDX-License-Identifier: GPL-3.0-only') &&
      head.includes('Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>'),
      `${row.id} defect copy lost the licence or copyright header`)

    const change = manifest.change
    const hunks = diffHunks(readFileSync(base, 'utf8').split('\n'),
      readFileSync(defect, 'utf8').split('\n'))
    const added = hunks.reduce((total, hunk) => total + hunk.added.length, 0)
    const removed = hunks.reduce((total, hunk) => total + hunk.removed.length, 0)

    fail(change !== null && typeof change === 'object', `${row.id} declares no change record`)
    fail(change.limit === 6, `${row.id} declares a change budget other than 6`)
    fail(added <= change.limit && removed <= change.limit,
      `${row.id} changes ${added} added and ${removed} removed lines, budget ${change.limit}`)
    fail(added > 0 || removed > 0, `${row.id} defect copy is identical to its base`)
    fail(change.added === added && change.removed === removed,
      `${row.id} declares ${change.added}/${change.removed} changed lines, ` +
      `the copy holds ${added}/${removed}`)
    fail(canonical(change.hunks) === canonical(hunks),
      `${row.id} declared change hunks differ from the real difference`)
    fail(change.sha256 === createHash('sha256').update(canonical(hunks)).digest('hex'),
      `${row.id} change digest differs from the real difference`)
    if (row.declared_delta.kind === 'guest-word')
      fail(hunks.length === 1 && added === 1 && removed === 1,
        `${row.id} is a single-word fixture but changes more than one source line`)
  }
  for (const line of expected.console)
    for (const forbidden of expected.forbidden_markers)
      fail(!line.includes(forbidden),
        `${row.id} declares forbidden marker ${forbidden} in its own console`)

  fail(Array.isArray(expected.guest_entries) && expected.guest_entries.length > 0,
    `${row.id} declares no VS entries`)
  for (const [index, held] of expected.guest_entries.entries()) {
    fail(canonical(Object.keys(held).sort()) ===
      canonical(['a0', 'a1', 'hstatus', 'pc', 's0']),
      `${row.id} VS entry ${index + 1} does not declare exactly pc,hstatus,s0,a0,a1`)
    for (const [name, one] of Object.entries(held))
      fail(value16.test(one), `${row.id} VS entry ${index + 1} ${name} is not a 16-digit value`)
  }
  fail(Array.isArray(expected.guest_exits) && expected.guest_exits.length > 0,
    `${row.id} declares no guest exits`)
  for (const [index, held] of expected.guest_exits.entries()) {
    fail(canonical(Object.keys(held).sort()) ===
      canonical(['htval', 'label', 'scause', 'sepc', 'stval']),
      `${row.id} guest exit ${index + 1} does not declare exactly label,scause,sepc,stval,htval`)
    for (const [name, one] of Object.entries(held))
      fail(name === 'label' ? typeof one === 'string' && one.length > 0 : value16.test(one),
        `${row.id} guest exit ${index + 1} ${name} is malformed`)
  }
  // A VS entry that is preempted before its first instruction retires leaves
  // no `V=1` dump, because the emulator dumps guest state when a translated
  // block starts and no block ever starts.  Such an entry is architecturally
  // real and is declared explicitly, so the entry-and-exit accounting stays
  // exact instead of being loosened for every fixture: it is the one and only
  // permitted asymmetry, it must be an interrupt exit, and it must not also
  // claim a dump.
  const preempted = expected.preempted_entry ?? null

  fail(preempted === null || value16.test(preempted),
    `${row.id} declares a malformed preempted VS entry`)
  if (preempted !== null) {
    fail(!expected.guest_entries.some((held) => held.pc === preempted),
      `${row.id} declares preempted entry ${preempted} that also has a V=1 dump`)

    const taken = expected.guest_exits.filter((held) => held.sepc === preempted)

    fail(taken.length === 1,
      `${row.id} declares ${taken.length} exits at preempted entry ${preempted}`)
    fail((BigInt(`0x${taken[0].scause}`) >> 63n) === 1n,
      `${row.id} preempted entry ${preempted} did not exit on an interrupt`)
  }
  fail(expected.guest_exits.length ===
    expected.guest_entries.length + (preempted === null ? 0 : 1),
    `${row.id} declares ${expected.guest_entries.length} entries, ` +
    `${expected.guest_exits.length} exits, and ` +
    `${preempted === null ? 'no' : 'one'} preempted entry; every entry ends ` +
    'in exactly one exit')

  const enteredProtected = expected.guest_entries
    .some((held) => held.pc === '0000000040011000') ||
    preempted === '0000000040011000'

  fail(enteredProtected === expected.guest_entered,
    `${row.id} declares guest_entered=${expected.guest_entered} but ` +
    `${enteredProtected ? 'declares' : 'declares no'} protected VS entry`)
  fail(Array.isArray(expected.root_installs), `${row.id} declares no published roots`)
  for (const held of expected.root_installs)
    fail(value16.test(held), `${row.id} published root ${held} is malformed`)
  checkRegisters(row.id, expected.final_registers, 'final register state')

  const backing = expected.backing

  fail(backing !== null && typeof backing === 'object', `${row.id} declares no backing`)
  fail(backing.management_private === 17 && backing.shared === 34,
    `${row.id} declares backing that contradicts the accepted R4 values`)
  fail(backing.protected_private === null || backing.protected_private === 51 ||
    backing.protected_private === 52,
    `${row.id} declares an unexpected protected private value`)
  fail(Array.isArray(backing.witnesses), `${row.id} declares no backing witnesses`)
  for (const witness of backing.witnesses) {
    fail(Object.hasOwn(expected.final_registers, witness.register),
      `${row.id} witnesses backing in unknown register ${witness.register}`)
    fail(Object.hasOwn(backing, witness.source) && backing[witness.source] === witness.value,
      `${row.id} backing witness ${witness.register} does not match ${witness.source}`)
    fail(expected.final_registers[witness.register] ===
      witness.value.toString(16).padStart(16, '0'),
      `${row.id} backing witness ${witness.register} contradicts the final register state`)
  }
  return manifest
}

// The observed run reduced to the vocabulary the catalogue permits.  A
// deviation is never absorbed: it is named with the forbidden outcome that
// describes it, so a fixture that fails differently is a reported result and
// never a pass.
const classify = (row, manifest, artifacts) => {
  const expected = manifest.expected
  const deviations = []
  const console = artifacts.console ?? []
  const failure = console.find((line) => line.startsWith('BE_R5:FAIL '))
  const observedClass = failure ? failure.slice('BE_R5:FAIL '.length).trim() : null
  const markers = console.filter((line) => /^BE_R[345]:\d\d /u.test(line))
  const lastMarker = markers.length === 0 ? null : markers[markers.length - 1].split(' ')[0]

  for (const forbidden of expected.forbidden_markers)
    if (console.some((line) => line.includes(forbidden)))
      deviations.push(`forbidden marker ${forbidden}`)
  if (canonical(console) !== canonical(expected.console))
    deviations.push('console differs from the declared sequence')
  if (artifacts.status !== expected.qemu_status)
    deviations.push(`status ${artifacts.status}`)
  if (observedClass !== expected.error_class)
    deviations.push(`class ${observedClass ?? 'none'}, expected ${expected.error_class ?? 'none'}`)
  if (lastMarker !== expected.last_marker)
    deviations.push(`last marker ${lastMarker ?? 'none'}, expected ${expected.last_marker}`)

  const outcome = () => {
    if (deviations.length === 0) return row.outcome
    if (console.some((line) => line.includes('BE_R5:SRST_RETURNED'))) return 'srst-returned'
    if (artifacts.status !== expected.qemu_status)
      return artifacts.status === 124 ? 'timeout' : 'qemu-nonzero'
    if (!expected.guest_entered && console.some((line) => line.startsWith('BE_R5:05')))
      return 'entered-guest-after-defect'
    if (expected.error_class !== null && observedClass === null) return 'built-and-accepted'
    if (observedClass !== expected.error_class) return 'wrong-error-class'
    if (lastMarker !== expected.last_marker) return 'marker-out-of-order'
    return 'missing-diagnostic'
  }
  return {
    outcome: outcome(),
    lastMarker,
    classes: observedClass === null ? [] : [observedClass],
    deviations
  }
}

const materialise = (partition) => (row, context = {}) => {
  fail(row?.partition === partition, `${row?.id} is not a ${partition} fixture`)

  const manifest = validateManifest(row)
  const declaredDelta = row.declared_delta
  const defectPath = manifest.defect_file === null ? null
    : (context.defect ?? resolve(root, `tests/r6/fixtures/${row.id}/${manifest.defect_file}`))

  return { defectPath, declaredDelta, manifest }
}

const classifier = (partition) => (row, context = {}, artifacts = {}) => {
  fail(row?.partition === partition, `${row?.id} is not a ${partition} fixture`)
  return classify(row, context.manifest ?? validateManifest(row), artifacts)
}

export const dynamicHandlers = {
  partition: 'dynamic',
  state: 'implemented',
  // (entry, context) => { defectPath, declaredDelta }
  materialiseDefect: materialise('dynamic'),
  // (entry, context, artifacts) => { outcome, lastMarker, classes }
  classifyRun: classifier('dynamic')
}

// The control partition is framework-owned so that the shared scratch and
// build path can be proved before any defect fixture exists.  Its L8, L9, and
// L10 handling is dynamic-owned, exactly like a `D-*` fixture.
export const controlHandlers = {
  partition: 'control',
  state: 'implemented',
  materialiseDefect: materialise('control'),
  classifyRun: classifier('control')
}
