// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Translate security model v1's instances into the policy layer's C data,
// Rocq terms, and MVP checker inputs at build time (planning/mvp-m3-plan.md,
// "The executable model and host checker (M3-4)", Q3).
//
//   node gen-policy-fixtures.mjs --output DIR
//
// Inputs: model/fixtures/instance-1/{policy.te,instance.json} (Instance 1,
// whose policy this checks is security model v1 Part 2's, verbatim), the
// MVP's mvp/scenarios/{te-poc,anchor}/{policy.te,scenario.json} (Instances
// 2 and 3), and model/fixtures/mutations.json (the seeded mutation set).
// Outputs, deterministic: DIR/fixtures.c, DIR/Instances.v, DIR/index.json,
// DIR/projection/policy.te, and the MVP checker's DIR/instances/<name>/ and
// DIR/mutations/<name>/. Identifiers follow the raw-term contract: types in
// declaration order, then undeclared names in order of first use (rules,
// labels, needs); classes and permissions at security model v1 Part 2's
// positions (include/be/policy.h); subjects the monitor, then the domains;
// objects in the labeling's order, then unlabeled ones in the
// configuration's. The view is policy-check.py's: its manifest(), paged(),
// and grants() order. A defect the raw terms cannot express (a syntax
// error, a non-v1 class, a malformed manifest) refuses generation.

import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const MODEL = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const REPOSITORY = path.dirname(MODEL)
const V1 = [
  ['memory', ['read', 'write', 'execute', 'map']],
  ['channel', ['send', 'receive']],
  ['domain', ['enter', 'switch_to', 'terminate', 'pause']],
  ['manifest', ['read']],
]
const V1_CLASSES = V1.map(([name]) => name)
const V1_PERMS = [...new Set(V1.flatMap(([, perms]) => perms))]
const RIGHTS = ['read', 'write', 'execute']
const NAME = /^(?!(?:type|class|allow)$)[A-Za-z_][A-Za-z0-9_]*$/
const MODEL_INSTANCE = 'be-model-policy-instance-v1'
// Model 0.2's platform inventory is R0 resources 1 to 11 (model/src/
// fixtures.c; model/proof/Model.v, platform_inventory): Instance 1 without
// its guest-code resources 12 and 13 (security model v1 Revision 1, R1.5).
const MODEL_0_2_RESOURCES = 11
export const SOURCES = [
  {
    name: 'instance1',
    directory: 'model/fixtures/instance-1',
    scenario: 'instance.json',
    description: 'Instance 1, the fixed two-domain profile',
  },
  {
    name: 'instance2',
    directory: 'mvp/scenarios/te-poc',
    scenario: 'scenario.json',
    description: 'Instance 2 as the te-poc scenario (Revision 1, R1.4)',
  },
  {
    name: 'instance3',
    directory: 'mvp/scenarios/anchor',
    scenario: 'scenario.json',
    description: 'Instance 3, the anchor scenario',
  },
]
const PROJECTION = {
  name: 'instance1_m02',
  description:
    "Model 0.2's projection of Instance 1 (Revision 1, R1.5): " +
    'resources 12 and 13 and execute dropped',
}

function refuse(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

function read(relative) {
  return fs.readFileSync(path.join(REPOSITORY, relative))
}

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex')
}

// Part 2's concrete syntax; each rule keeps its offsets for the mutator.
export function parsePolicy(text) {
  const body = text.replace(/#[^\n]*/g, (comment) => ' '.repeat(comment.length))
  const stray = body.search(/[^A-Za-z0-9_ \t\n{};:]/)
  refuse(stray < 0, `policy: ${JSON.stringify(body[stray])} is not in the notation`)
  const forms = [
    ['type', /type\s+(\w+)\s*;/y],
    ['class', /class\s+(\w+)\s*\{([\w\s]*)\}/y],
    ['allow', /allow\s+(\w+)\s+(\w+)\s*:\s*(\w+)\s*\{([\w\s]*)\}\s*;/y],
  ]
  const policy = { types: [], classes: [], rules: [] }
  let position = 0
  for (;;) {
    while (position < body.length && /\s/.test(body[position])) {
      position += 1
    }
    if (position >= body.length) {
      return policy
    }
    let keyword = null
    let match = null
    for (const [name, form] of forms) {
      form.lastIndex = position
      match = form.exec(body)
      if (match) {
        keyword = name
        break
      }
    }
    const line = body.slice(position).split('\n')[0]
    refuse(match, `policy: ${JSON.stringify(line)} is not a statement`)
    const words = match.slice(1, keyword === 'allow' ? 4 : 2)
    const perms = keyword === 'type' ? [] : match[match.length - 1].split(/\s+/)
    const names = [...words, ...perms.filter(Boolean)]
    refuse(names.every((word) => NAME.test(word)), `policy: ${match[0]} has a non-name`)
    refuse(keyword === 'allow' || policy.rules.length === 0, `policy: ${match[0]} is late`)
    if (keyword === 'type') {
      policy.types.push(words[0])
    } else if (keyword === 'class') {
      policy.classes.push({ name: words[0], perms: perms.filter(Boolean) })
    } else {
      policy.rules.push({
        source: words[0],
        target: words[1],
        cls: words[2],
        perms: perms.filter(Boolean),
        start: position,
        end: position + match[0].length,
      })
    }
    position += match[0].length
  }
}

function number(value) {
  refuse(
    (Number.isInteger(value) && value >= 0) ||
      /^(0x[0-9a-f]+|[0-9]+)$/.test(String(value)),
    `${JSON.stringify(value)} is not a number`,
  )
  return Number(value)
}

function rights(value) {
  refuse(
    Array.isArray(value) &&
      value.length > 0 &&
      value.join() === RIGHTS.filter((right) => value.includes(right)).join(),
    `${JSON.stringify(value)} is not rights in the order ${RIGHTS}`,
  )
  return value
}

// The MVP checker's manifest(), paged(), and grants(), and its labeling's
// matching: memory by extent and name, channels by name and object.
function mvpConfiguration(scenario) {
  const v3 = scenario.schema === 'be-mvp-scenario-v3'
  refuse(v3 || scenario.schema === 'be-mvp-scenario-v2', 'not an MVP scenario')
  const domains = scenario.domains.map((d) => ({
    name: d.name,
    index: d.index,
    hart: d.hart,
    base: number(d.window.hpa),
    size: number(d.window.bytes),
    rights: rights(d.window.rights),
  }))
  const named = (index) => {
    refuse(Number.isInteger(index) && domains[index], `${index} is not a domain`)
    return domains[index].name
  }
  const objects = domains.map((d) => ({
    key: `window:${d.name}`,
    name: null,
    cls: 'memory',
    base: d.base,
    size: d.size,
    owner: d.name,
  }))
  const memory = (name, row, owner) => ({
    key: `object:${name}`,
    name,
    cls: 'memory',
    base: number(row.hpa),
    size: number(row.bytes),
    owner,
  })
  objects.push(...scenario.objects.map((o) => memory(o.name, o, o.owner)))
  let pages
  let channels
  if (v3) {
    pages = scenario.pages.map((p) => ({
      name: p.name,
      channel: p.channel,
      writer: p.writer === undefined ? undefined : named(p.writer),
      reader: named(p.reader),
      rights: Object.fromEntries(
        p.rights.flatMap((value, index) =>
          value.length > 0 ? [[named(index), rights(value)]] : [],
        ),
      ),
    }))
    scenario.pages.forEach((p, index) => {
      objects.push(memory(p.name, p, p.channel ?? pages[index].reader))
    })
    channels = pages
      .filter((p) => p.channel !== undefined)
      .map((p) => ({ name: p.channel, object: p.name, writer: p.writer, reader: p.reader }))
  } else {
    channels = scenario.channels.map((c) => ({
      name: c.name,
      object: c.object,
      writer: c.writer,
      reader: c.reader,
    }))
    pages = scenario.channels.map((c) => ({
      name: c.object,
      rights: { [c.writer]: rights(c.writer_rights), [c.reader]: rights(c.reader_rights) },
    }))
  }
  for (const c of channels) {
    objects.push({ key: `channel:${c.name}`, name: c.name, cls: 'channel', object: c.object })
  }
  const ends = new Map(channels.map((c) => [c.object, c]))
  const grants = []
  const grant = (subject, object, cls, perms) => grants.push({ subject, object, cls, perms })
  for (const d of domains) {
    grant(d.name, `window:${d.name}`, 'memory', ['map', ...d.rights])
    for (const page of pages) {
      const c = ends.get(page.name)
      if (page.rights[d.name] !== undefined) {
        grant(d.name, `object:${page.name}`, 'memory', ['map', ...page.rights[d.name]])
      }
      for (const [role, perm] of [['writer', 'send'], ['reader', 'receive']]) {
        if (c && c[role] === d.name) {
          grant(d.name, `channel:${c.name}`, 'channel', [perm])
        }
      }
    }
    for (const g of v3 ? scenario.grants : []) {
      if (named(g.from) === d.name) {
        grant(d.name, `subject:${named(g.to)}`, 'domain', g.permissions)
      }
    }
  }
  const match = (entry) => {
    const found =
      entry.class === 'memory'
        ? objects.find(
            (o) =>
              o.cls === 'memory' &&
              o.base === number(entry.hpa) &&
              o.size === number(entry.bytes),
          )
        : objects.find((o) => o.cls === 'channel' && o.name === entry.name)
    return found &&
      (found.name === null || found.name === entry.name) &&
      found.object === entry.object
      ? found.key
      : null
  }
  return {
    subjects: [{ name: 'monitor' }, ...domains.map((d) => ({ name: d.name, index: d.index }))],
    objects,
    channels,
    grants,
    bindings: domains
      .filter((d) => d.hart !== undefined)
      .map((d) => ({ domain: d.name, hart: d.hart })),
    harts: [...new Set([scenario.platform.control_hart, ...domains.map((d) => d.hart)])],
    controlHart: scenario.platform.control_hart,
    match,
  }
}

// The model's instance format: objects by name, the channels, and the
// manifest's grants listed rather than derived from windows and pages.
function modelConfiguration(scenario) {
  const objects = scenario.objects.map((o) => ({
    key: `object:${o.name}`,
    name: o.name,
    cls: o.class,
    owner: o.owner,
  }))
  for (const c of scenario.channels) {
    objects.push({ key: `channel:${c.name}`, name: c.name, cls: 'channel', object: c.object })
  }
  const domains = scenario.domains.map((d) => d.name)
  const target = (g) =>
    g.class === 'domain' && domains.includes(g.object)
      ? `subject:${g.object}`
      : objects.find(
          (o) => o.name === g.object && (o.cls === 'channel') === (g.class === 'channel'),
        )?.key
  return {
    subjects: [
      { name: 'monitor' },
      ...scenario.domains.map((d) => ({ name: d.name, index: d.index })),
    ],
    objects,
    channels: scenario.channels,
    grants: scenario.grants.map((g) => ({
      subject: g.subject,
      object: target(g),
      cls: g.class,
      perms: g.permissions,
    })),
    bindings: scenario.domains
      .filter((d) => d.hart !== undefined)
      .map((d) => ({ domain: d.name, hart: d.hart })),
    harts: scenario.harts,
    controlHart: scenario.control_hart,
    match: (entry) => {
      const found = objects.find((o) => o.name === entry.name && o.cls === entry.class)
      return found && found.object === entry.object ? found.key : null
    },
  }
}

function configuration(scenario) {
  return scenario.schema === MODEL_INSTANCE
    ? modelConfiguration(scenario)
    : mvpConfiguration(scenario)
}

function extra(table, name, offset) {
  if (!table.has(name)) {
    table.set(name, offset + table.size)
  }
  return table.get(name)
}

// One instance's sources as raw identifiers and report names.
export function translate(policyText, scenario) {
  const policy = parsePolicy(policyText)
  const config = configuration(scenario)
  const declared = [...new Set(policy.classes.map((c) => c.name))]
  declared.forEach((name, position) => {
    refuse(V1_CLASSES[position] === name, `policy: class ${name} is not v1's ${position}`)
  })
  for (const c of policy.classes) {
    const v1 = V1[V1_CLASSES.indexOf(c.name)][1]
    refuse([...new Set(c.perms)].join() === v1.join(), `policy: class ${c.name} is not v1's`)
  }
  const types = new Map()
  const classExtras = new Map()
  const permExtras = new Map()
  const type = (name) => extra(types, name, 0)
  const cls = (name) =>
    V1_CLASSES.includes(name)
      ? V1_CLASSES.indexOf(name)
      : extra(classExtras, name, V1_CLASSES.length)
  const perm = (name) =>
    V1_PERMS.includes(name) ? V1_PERMS.indexOf(name) : extra(permExtras, name, V1_PERMS.length)
  const permed = (row, list) => ({ ...row, perms: list.map(perm) })
  policy.types.forEach(type)
  const raw = {
    types: policy.types.map(type),
    classes: policy.classes.map((c) => permed({ cls: cls(c.name) }, c.perms)),
    rules: policy.rules.map((r) =>
      permed({ source: type(r.source), target: type(r.target), cls: cls(r.cls) }, r.perms),
    ),
  }

  const labeling = scenario.labeling
  refuse(
    Array.isArray(labeling?.subjects) && Array.isArray(labeling?.objects),
    'labeling: not lists of subjects and objects',
  )
  const subjectIds = new Map(config.subjects.map((s, index) => [s.name, index]))
  const subjects = config.subjects.map((s) => s.name)
  const objectIds = new Map()
  const objects = []
  const identify = (key, name) => {
    if (!objectIds.has(key)) {
      objectIds.set(key, objects.length)
      objects.push(name)
    }
  }
  const keys = labeling.objects.map((entry) => config.match(entry))
  labeling.objects.forEach((entry, index) => keys[index] && identify(keys[index], entry.name))
  config.objects.forEach((o) => identify(o.key, o.name ?? o.key.replace(':', '_')))
  refuse(objects.length === config.objects.length, 'manifest: an object repeats')
  const fresh = (list, name) => list.push(name) - 1
  const labels = labeling.subjects.map((entry) => {
    const s = config.subjects.find((x) => x.name === entry.name)
    const same = s && entry.domain_index === s.index
    const id = same ? subjectIds.get(s.name) : fresh(subjects, entry.name)
    return { kind: 'subject', entity: id, type: type(entry.type) }
  })
  labeling.objects.forEach((entry, index) => {
    const id = keys[index] ? objectIds.get(keys[index]) : fresh(objects, entry.name)
    labels.push({ kind: 'object', entity: id, type: type(entry.type) })
  })
  const needs = scenario.need.map((n) => {
    refuse(
      Object.keys(n).sort().join() === 'class,permissions,source,target' &&
        Array.isArray(n.permissions),
      `need: ${JSON.stringify(n)} is not one need entry`,
    )
    const key = { source: type(n.source), target: type(n.target), cls: cls(n.class) }
    return permed(key, n.permissions)
  })

  const domainNames = subjects.slice(1, config.subjects.length)
  const subjectOf = (name) => {
    refuse(subjectIds.has(name), `manifest: ${name} is not a subject`)
    return subjectIds.get(name)
  }
  const objectOf = (key) => {
    refuse(objectIds.has(key), `manifest: ${key} is not an object`)
    return objectIds.get(key)
  }
  const byObject = (a, b) => a.object - b.object
  const view = {
    ownerships: config.objects
      .filter((o) => o.cls === 'memory' && domainNames.includes(o.owner))
      .map((o) => ({ object: objectOf(o.key), owner: subjectOf(o.owner) }))
      .sort(byObject),
    channels: config.channels.map((c) => ({
      object: objectOf(`channel:${c.name}`),
      storage: objectOf(`object:${c.object}`),
      writer: subjectOf(c.writer),
      reader: subjectOf(c.reader),
    })),
    grants: config.grants.map((g) =>
      permed(
        {
          subject: subjectOf(g.subject),
          object: g.object?.startsWith('subject:')
            ? subjectOf(g.object.slice(8))
            : objectOf(g.object),
          cls: cls(g.cls),
        },
        g.perms,
      ),
    ),
    bindings: config.bindings.map((b) => ({ domain: subjectOf(b.domain), hart: b.hart })),
    harts: config.harts.map(number),
    controlHart: number(config.controlHart),
  }
  const instance = {
    policy: raw,
    labeling: {
      subjects: config.subjects.map((s, index) => index),
      objects: config.objects
        .map((o) => ({ object: objectOf(o.key), cls: cls(o.cls) }))
        .sort(byObject),
      labels,
    },
    needs,
    view,
  }
  const names = {
    types: [...types.keys()],
    classes: [...V1_CLASSES, ...classExtras.keys()],
    perms: [...V1_PERMS, ...permExtras.keys()],
    subjects,
    objects,
  }
  return { instance, names }
}

// Model 0.2's projection: Instance 1 without the resources beyond Model
// 0.2's inventory, the rules granting execute (exactly their guest-code
// rules), those rules' need sets, and the types nothing then names. Its
// policy is rendered in Part 2's syntax and translated like any other, so
// its identifiers are the contract's, restricted to the projection.
export function project(policyText, scenario) {
  const policy = parsePolicy(policyText)
  const projected = structuredClone(scenario)
  const dropped = new Set(
    scenario.objects.filter((o) => o.resource > MODEL_0_2_RESOURCES).map((o) => o.name),
  )
  const kept = scenario.labeling.objects.filter((e) => !dropped.has(e.name))
  const droppedTypes = new Set(
    scenario.labeling.objects.filter((e) => dropped.has(e.name)).map((e) => e.type),
  )
  const rules = policy.rules.filter((r) => !r.perms.includes('execute'))
  refuse(
    policy.rules.every((r) => rules.includes(r) !== droppedTypes.has(r.target)) &&
      kept.every((e) => !droppedTypes.has(e.type)),
    "projection: the execute rules are not exactly the dropped resources' rules",
  )
  const named = new Set([
    ...rules.flatMap((r) => [r.source, r.target]),
    ...scenario.labeling.subjects.map((e) => e.type),
    ...kept.map((e) => e.type),
  ])
  const keys = new Set(rules.map((r) => `${r.source} ${r.target} ${r.cls}`))
  projected.objects = scenario.objects.filter((o) => !dropped.has(o.name))
  projected.grants = scenario.grants.filter((g) => !dropped.has(g.object))
  projected.labeling.objects = kept
  projected.need = scenario.need.filter((n) => keys.has(`${n.source} ${n.target} ${n.class}`))
  const statement = (r) => `allow ${r.source} ${r.target} : ${r.cls} { ${r.perms.join(' ')} };`
  const text = [
    '# Derived by model/tools/gen-policy-fixtures.mjs from model/fixtures/',
    "# instance-1/policy.te: Model 0.2's projection of Instance 1 (security",
    '# model v1 Revision 1, R1.5), without resources 12 and 13 and execute.',
    '',
    ...policy.types.filter((t) => named.has(t)).map((t) => `type ${t};`),
    ...policy.classes.map((c) => `class ${c.name} { ${c.perms.join(' ')} }`),
    ...rules.map(statement),
  ]
  return { policyText: `${text.join('\n')}\n`, scenario: projected }
}

// The MVP checker's edit vocabulary (policy-check.py, edit()): ['rule',
// TEXT] appends a rule; ['swap', OLD, NEW] replaces text found once; ['set'
// or 'add', PATH, VALUE] and ['drop', PATH] change the scenario.
export function applyEdits(sources, edits) {
  let text = sources.policyText
  const scenario = structuredClone(sources.scenario)
  for (const [kind, first, ...rest] of edits) {
    const arity = kind === 'rule' || kind === 'drop' ? 0 : 1
    refuse(rest.length === arity, `${JSON.stringify(kind)} is not an edit`)
    if (kind === 'rule') {
      text = `${text}${first}\n`
      continue
    }
    if (kind === 'swap') {
      refuse(text.split(first).length === 2, `${JSON.stringify(first)} is not in the policy once`)
      text = text.split(first).join(rest[0])
      continue
    }
    refuse(['set', 'add', 'drop'].includes(kind) && Array.isArray(first), `${kind} is not an edit`)
    const node = first.slice(0, -1).reduce((value, step) => value[step], scenario)
    const key = first[first.length - 1]
    if (kind === 'drop' && Array.isArray(node)) {
      node.splice(key, 1)
    } else if (kind === 'drop') {
      delete node[key]
    } else {
      node[key] = kind === 'add' ? [...node[key], rest[0]] : rest[0]
    }
  }
  return { ...sources, policyText: text, scenario }
}

// A seeded generator: FNV-1a of "seed:index", then mulberry32.
function random(seed, index) {
  let state = 2166136261
  for (const byte of Buffer.from(`${seed}:${index}`)) {
    state = Math.imul(state ^ byte, 16777619) >>> 0
  }
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let t = state
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// Q8's single defects, each as edits over one instance's sources; PICK
// draws one candidate with the seeded generator.
export const DEFECTS = {
  'drop-rule': (s, pick) => [['swap', s.line(pick(s.rules)), '']],
  'add-permission': (s, pick) => {
    const [rule, perm] = pick(
      s.rules.flatMap((r) =>
        s.permsOf(r.cls).filter((p) => !r.perms.includes(p)).map((p) => [r, p]),
      ),
    )
    return [s.rewrite(rule, { perms: [...rule.perms, perm] })]
  },
  'remove-permission': (s, pick) => {
    const [rule, perm] = pick(
      s.rules.filter((r) => r.perms.length > 1).flatMap((r) => r.perms.map((p) => [r, p])),
    )
    return [s.rewrite(rule, { perms: rule.perms.filter((p) => p !== perm) })]
  },
  'swap-labels': (s, pick) => {
    const entries = s.scenario.labeling.objects
    const [i, j] = pick(
      entries.flatMap((a, i) =>
        entries.flatMap((b, j) => (i < j && a.type !== b.type ? [[i, j]] : [])),
      ),
    )
    return [
      ['set', ['labeling', 'objects', i, 'type'], entries[j].type],
      ['set', ['labeling', 'objects', j, 'type'], entries[i].type],
    ]
  },
  'undeclared-type': (s, pick) => [s.rewrite(pick(s.rules), { target: 'undeclared_t' })],
  'unknown-permission': (s, pick) => {
    const [rule, perm] = pick(s.rules.flatMap((r) => r.perms.map((p) => [r, p])))
    const perms = rule.perms.map((p) => (p === perm ? 'unknown' : p))
    return [s.rewrite(rule, { perms })]
  },
  'narrow-need': (s, pick) => {
    const [i, k] = pick(
      s.scenario.need.flatMap((n, i) =>
        n.permissions.length > 1 ? n.permissions.map((p, k) => [i, k]) : [],
      ),
    )
    return [['drop', ['need', i, 'permissions', k]]]
  },
  'channel-without-storage': (s, pick) => {
    const storage = (c) =>
      s.rules.filter((r) => r.cls === 'memory' && r.source === c.source && r.target === c.target)
    const rule = pick(s.rules.filter((r) => r.cls === 'channel' && storage(r).length > 0))
    return storage(rule).map((r) => ['swap', s.line(r), ''])
  },
  'storage-without-channel': (s, pick) => [
    ['swap', s.line(pick(s.rules.filter((r) => r.cls === 'channel'))), ''],
  ],
  // A domain's object relabeled with a type another domain reads.
  'secret-readable': (s, pick) => {
    const [index, target] = pick(
      s.scenario.labeling.objects.flatMap((entry, index) => {
        const owner = s.owners.get(index)
        const readable = (r) =>
          r.cls === 'memory' &&
          r.perms.includes('read') &&
          r.target !== entry.type &&
          s.domainTypes.some(([name, t]) => name !== owner && t === r.source)
        return owner === undefined ? [] : s.rules.filter(readable).map((r) => [index, r.target])
      }),
    )
    return [['set', ['labeling', 'objects', index, 'type'], target]]
  },
  'grant-without-rule': (s, pick) => pick(s.ungranted),
}

// The candidates DEFECTS draws from, over one instance's sources.
function defectView(sources) {
  const policy = parsePolicy(sources.policyText)
  const { scenario, policyText: text } = sources
  const line = (rule) => {
    const start = text.lastIndexOf('\n', rule.start) + 1
    const end = text.indexOf('\n', rule.end)
    const found = text.slice(start, end < 0 ? text.length : end + 1)
    refuse(
      found.trim() === text.slice(rule.start, rule.end) && text.split(found).length === 2,
      `${found} is not one statement found once`,
    )
    return found
  }
  const rewrite = (rule, change) => {
    const r = { ...rule, ...change }
    const statement = `allow ${r.source} ${r.target} : ${r.cls} { ${r.perms.join(' ')} };`
    return ['swap', text.slice(rule.start, rule.end), statement]
  }
  const config = configuration(scenario)
  const domains = config.subjects.slice(1).map((d) => d.name)
  const owners = new Map()
  scenario.labeling.objects.forEach((entry, index) => {
    const owner = config.objects.find((o) => o.key === config.match(entry))?.owner
    if (domains.includes(owner)) {
      owners.set(index, owner)
    }
  })
  const domainTypes = scenario.labeling.subjects
    .filter((e) => domains.includes(e.name))
    .map((e) => [e.name, e.type])
  const typeOf = (name) => domainTypes.find(([d]) => d === name)?.[1]
  const allowed = (s, t, c, p) =>
    policy.rules.some(
      (r) => r.source === s && r.target === t && r.cls === c && r.perms.includes(p),
    )
  const ungranted = []
  if (scenario.schema === 'be-mvp-scenario-v3') {
    domains.forEach((from, a) =>
      domains.forEach((to, b) => {
        const present = scenario.grants.some((g) => g.from === a && g.to === b)
        if (a !== b && !present && !allowed(typeOf(from), typeOf(to), 'domain', 'pause')) {
          ungranted.push([['add', ['grants'], { from: a, to: b, permissions: ['pause'] }]])
        }
      }),
    )
  } else if (scenario.schema === 'be-mvp-scenario-v2') {
    scenario.channels.forEach((c, index) => {
      const page = scenario.labeling.objects.find((e) => e.name === c.object)?.type
      for (const role of ['writer', 'reader']) {
        const field = `${role}_rights`
        if (!c[field].includes('execute') && !allowed(typeOf(c[role]), page, 'memory', 'execute')) {
          ungranted.push([['add', ['channels', index, field], 'execute']])
        }
      }
    })
  } else {
    for (const [index, owner] of owners) {
      const entry = scenario.labeling.objects[index]
      for (const d of domains) {
        if (d !== owner && !allowed(typeOf(d), entry.type, 'memory', 'map')) {
          const permissions = ['map', 'read']
          const row = { subject: d, object: entry.name, class: 'memory', permissions }
          ungranted.push([['add', ['grants'], row]])
        }
      }
    }
  }
  return {
    rules: policy.rules,
    scenario,
    line,
    rewrite,
    permsOf: (name) => policy.classes.find((c) => c.name === name)?.perms ?? [],
    owners,
    domainTypes,
    ungranted,
  }
}

// One mutation's edits: a defect of DEFECTS, its parameters drawn from the
// seed and the mutation's index.
export function seededEdits(sources, defect, seed, index) {
  refuse(Object.hasOwn(DEFECTS, defect), `${defect} is not a defect of Q8`)
  const next = random(seed, index)
  const pick = (choices) => {
    refuse(choices.length > 0, `${defect} has no candidate`)
    return choices[Math.floor(next() * choices.length)]
  }
  return DEFECTS[defect](defectView(sources), pick)
}

function load(source) {
  const scenario = JSON.parse(read(path.join(source.directory, source.scenario)))
  const policyBytes = read(path.join(source.directory, scenario.policy))
  return { ...source, scenario, policyBytes, policyText: policyBytes.toString('ascii') }
}

// policy-check.py's verbatim rule: the lines after the comments are the
// security model's code block.
function checkVerbatim(text) {
  const model = read('planning/security-model-v1.md').toString('utf8')
  const block = /^### Instance 1.*?^```text\n(.*?)^```/ms.exec(model)
  const lines = text.endsWith('\n') ? text.slice(0, -1).split('\n') : text.split('\n')
  const body = lines
    .filter((line) => !line.startsWith('#'))
    .map((line) => `${line}\n`)
    .join('')
    .replace(/^\n+/, '')
  refuse(block && body === block[1], "instance-1: policy.te is not Part 2's Instance 1")
}

function cString(value) {
  return `"${String(value).replace(/[\\"]/g, '\\$&')}"`
}

function cIds(values) {
  return values.length === 0 ? '{ 0U }' : `{ ${values.map((v) => `${v}U`).join(', ')} }`
}

function cArray(count, field, items, render, indent) {
  const lines = [`${indent}.${count}_count = ${items.length}U,`]
  if (items.length > 0) {
    lines.push(
      `${indent}.${field} = {`,
      ...items.map((item) => `${indent}\t${render(item)},`),
      `${indent}},`,
    )
  }
  return lines
}

function cFixture(symbol, fixture) {
  const { instance: i, names } = fixture.translated
  const fields = [
    ['type', 'types'],
    ['class', 'classes'],
    ['perm', 'perms'],
    ['subject', 'subjects'],
    ['object', 'objects'],
  ]
  const permed = (x) => `${x.perms.length}U, ${cIds(x.perms)}`
  const ids = (...values) => values.map((v) => `${v}U`).join(', ')
  const cls = (c) => `{ ${ids(c.cls)}, ${permed(c)} }`
  const rule = (r) => `{ ${ids(r.source, r.target, r.cls)}, ${permed(r)} }`
  const object = (o) => `{ ${ids(o.object, o.cls)} }`
  const kind = (l) => (l.kind === 'subject' ? 'BE_RAW_SUBJECT' : 'BE_RAW_OBJECT')
  const label = (l) => `{ ${kind(l)}, ${ids(l.entity, l.type)} }`
  const owned = (o) => `{ ${ids(o.object, o.owner)} }`
  const channel = (c) => `{ ${ids(c.object, c.storage, c.writer, c.reader)} }`
  const grant = (g) => `{ ${ids(g.subject, g.object, g.cls)}, ${permed(g)} }`
  const binding = (b) => `{ ${ids(b.domain, b.hart)} }`
  return [
    ...fields.flatMap(([, field]) => [
      `static const char *const ${symbol}_${field}[] = {`,
      ...(names[field].length > 0 ? names[field] : ['']).map((v) => `\t${cString(v)},`),
      '};',
    ]),
    `static const struct be_policy_names ${symbol}_names = {`,
    ...fields.flatMap(([count, field]) => [
      `\t.${count}_count = ${names[field].length}U,`,
      `\t.${field} = ${symbol}_${field},`,
    ]),
    '};',
    `static const struct be_raw_instance ${symbol}_instance = {`,
    '\t.policy = {',
    `\t\t.type_count = ${i.policy.types.length}U,`,
    `\t\t.types = ${cIds(i.policy.types)},`,
    ...cArray('class', 'classes', i.policy.classes, cls, '\t\t'),
    ...cArray('rule', 'rules', i.policy.rules, rule, '\t\t'),
    '\t},',
    '\t.labeling = {',
    `\t\t.subject_count = ${i.labeling.subjects.length}U,`,
    `\t\t.subjects = ${cIds(i.labeling.subjects)},`,
    ...cArray('object', 'objects', i.labeling.objects, object, '\t\t'),
    ...cArray('label', 'labels', i.labeling.labels, label, '\t\t'),
    '\t},',
    ...cArray('need', 'needs', i.needs, rule, '\t'),
    '\t.view = {',
    ...cArray('ownership', 'ownerships', i.view.ownerships, owned, '\t\t'),
    ...cArray('channel', 'channels', i.view.channels, channel, '\t\t'),
    ...cArray('grant', 'grants', i.view.grants, grant, '\t\t'),
    ...cArray('binding', 'bindings', i.view.bindings, binding, '\t\t'),
    `\t\t.hart_count = ${i.view.harts.length}U,`,
    `\t\t.harts = ${cIds(i.view.harts)},`,
    `\t\t.control_hart = ${i.view.controlHart}U,`,
    '\t},',
    '};',
    '',
  ]
}

function cTable(table, symbols, fixtures) {
  return [
    `static const struct be_policy_fixture ${table}[] = {`,
    ...fixtures.flatMap((f, index) => [
      '\t{',
      `\t\t${cString(f.name)},`,
      `\t\t${cString(f.source)},`,
      `\t\t${cString(f.policySha256)},`,
      `\t\t${cString(f.description)},`,
      `\t\t${f.projection ? 1 : 0}U,`,
      `\t\t&${symbols[index]}_instance,`,
      `\t\t&${symbols[index]}_names,`,
      '\t},',
    ]),
    '};',
    '',
  ]
}

function cLookup(kind, table, count) {
  return [
    `be_size be_policy_${kind}_count(void)`,
    '{',
    `\treturn ${count === 0 ? '0U' : `BE_ARRAY_SIZE(${table})`};`,
    '}',
    '',
    `const struct be_policy_fixture *be_policy_${kind}(be_size index)`,
    '{',
    ...(count === 0
      ? ['\t(void)index;']
      : [`\tif (index < BE_ARRAY_SIZE(${table}))`, `\t\treturn &${table}[index];`]),
    '\treturn (const struct be_policy_fixture *)0;',
    '}',
  ]
}

function emitC(fixtures, mutations) {
  const symbols = fixtures.map((f) => `be_policy_${f.name}`)
  const mutationSymbols = mutations.map((m) => `be_policy_${m.name}`)
  return `${[
    '// SPDX-License-Identifier: GPL-3.0-only',
    '/*',
    ' * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>',
    ' */',
    '',
    '/*',
    ' * Generated by model/tools/gen-policy-fixtures.mjs from model/fixtures/',
    ' * and the MVP scenarios te-poc and anchor; do not edit. The instances',
    ' * are data: no model binary reads a file at run time.',
    ' */',
    '#include <be/policy_fixtures.h>',
    '',
    ...fixtures.flatMap((f, index) => cFixture(symbols[index], f)),
    ...mutations.flatMap((m, index) => cFixture(mutationSymbols[index], m)),
    ...cTable('be_policy_fixtures', symbols, fixtures),
    ...(mutations.length > 0 ? cTable('be_policy_mutations', mutationSymbols, mutations) : []),
    ...cLookup('fixture', 'be_policy_fixtures', fixtures.length),
    '',
    ...cLookup('mutation', 'be_policy_mutations', mutations.length),
  ].join('\n')}\n`
}

function rocqNats(values) {
  return `[${values.join('; ')}]`
}

function rocqList(items, indent) {
  return items.length === 0 ? '[]' : `[${items.join(`;\n${indent} `)}]`
}

function rocqInstance(i, indent) {
  const inner = `${indent}     `
  const nats = (x) => rocqNats(x.perms)
  const list = (items, render, at = inner) => rocqList(items.map(render), at)
  const entity = (l) => `(${l.kind === 'subject' ? 'RawSubject' : 'RawObject'} ${l.entity})`
  const cls = (c) => `mk_raw_class ${c.cls} ${nats(c)}`
  const rule = (r) => `mk_raw_rule ${r.source} ${r.target} ${r.cls} ${nats(r)}`
  const object = (o) => `mk_raw_object ${o.object} ${o.cls}`
  const label = (l) => `mk_raw_label ${entity(l)} ${l.type}`
  const need = (n) => `mk_raw_need ${n.source} ${n.target} ${n.cls} ${nats(n)}`
  const owned = (o) => `mk_raw_ownership ${o.object} ${o.owner}`
  const channel = (c) => `mk_raw_channel ${c.object} ${c.storage} ${c.writer} ${c.reader}`
  const grant = (g) => `mk_raw_grant ${g.subject} ${g.object} ${g.cls} ${nats(g)}`
  const binding = (b) => `mk_raw_binding ${b.domain} ${b.hart}`
  return [
    'mk_raw_instance',
    `${indent}  (mk_raw_policy`,
    `${inner}${rocqNats(i.policy.types)}`,
    `${inner}${list(i.policy.classes, cls)}`,
    `${inner}${list(i.policy.rules, rule)})`,
    `${indent}  (mk_raw_labeling`,
    `${inner}${rocqNats(i.labeling.subjects)}`,
    `${inner}${list(i.labeling.objects, object)}`,
    `${inner}${list(i.labeling.labels, label)})`,
    `${indent}  ${list(i.needs, need, `${indent}  `)}`,
    `${indent}  (mk_raw_view`,
    `${inner}${list(i.view.ownerships, owned)}`,
    `${inner}${list(i.view.channels, channel)}`,
    `${inner}${list(i.view.grants, grant)}`,
    `${inner}${list(i.view.bindings, binding)}`,
    `${inner}${rocqNats(i.view.harts)}`,
    `${inner}${i.view.controlHart})`,
  ].join('\n')
}

function emitRocq(fixtures, mutations) {
  const definitions = fixtures.map((f) =>
    [
      `Definition ${f.name} : raw_instance :=`,
      `  ${rocqInstance(f.translated.instance, '  ')}.`,
      '',
    ].join('\n'),
  )
  const listed = mutations.map(
    (m, index) => `(${index}, ${rocqInstance(m.translated.instance, '     ')})`,
  )
  return `${[
    '(* SPDX-License-Identifier: GPL-3.0-only *)',
    '(*',
    ' * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>',
    ' *)',
    '',
    '(*',
    ' * Generated by model/tools/gen-policy-fixtures.mjs from the same sources',
    ' * as build/model/policy/fixtures.c; do not edit. The terms use the raw',
    ' * vocabulary that Policy.v defines, with the identifiers that',
    ' * include/be/policy.h documents.',
    ' *)',
    '',
    'Require Import Policy.',
    'From Stdlib Require Import List.',
    'Import ListNotations.',
    '',
    ...definitions,
    `Definition mutations : list (nat * raw_instance) :=\n  ${rocqList(listed, '  ')}.`,
  ].join('\n')}\n`
}

function writeTree(output, relative, bytes) {
  const file = path.join(output, relative)
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, bytes)
}

export function generate(output) {
  const bases = Object.fromEntries(SOURCES.map((source) => [source.name, load(source)]))
  checkVerbatim(bases.instance1.policyText)
  const fixtures = SOURCES.map((source) => ({
    name: source.name,
    source: source.directory,
    policySha256: sha256(bases[source.name].policyBytes),
    description: source.description,
    projection: false,
    translated: translate(bases[source.name].policyText, bases[source.name].scenario),
  }))
  const projected = project(bases.instance1.policyText, bases.instance1.scenario)
  fixtures.push({
    name: PROJECTION.name,
    source: `${SOURCES[0].directory} (projection)`,
    policySha256: sha256(Buffer.from(projected.policyText, 'ascii')),
    description: PROJECTION.description,
    projection: true,
    translated: translate(projected.policyText, projected.scenario),
  })
  const set = JSON.parse(read('model/fixtures/mutations.json'))
  refuse(
    set.schema === 'be-model-policy-mutations-v1' && Array.isArray(set.mutations),
    'mutations: not a be-model-policy-mutations-v1 set',
  )
  const mutations = set.mutations.map((spec, index) => {
    const base = bases[spec.instance]
    refuse(base, `mutation ${index}: ${spec.instance} is not an instance`)
    const edits = spec.edits ?? seededEdits(base, spec.defect, set.seed, index)
    const mutated = applyEdits(base, edits)
    return {
      name: `mutation${index}`,
      instance: spec.instance,
      defect: spec.defect ?? 'explicit',
      edits,
      source: base.directory,
      policySha256: sha256(Buffer.from(mutated.policyText, 'ascii')),
      description: `${spec.instance}: ${spec.defect ?? 'explicit edits'}`,
      projection: false,
      translated: translate(mutated.policyText, mutated.scenario),
      mvp: base.scenario.schema === MODEL_INSTANCE ? null : mutated,
    }
  })

  for (const directory of ['instances', 'mutations', 'projection']) {
    fs.rmSync(path.join(output, directory), { recursive: true, force: true })
  }
  writeTree(output, 'fixtures.c', emitC(fixtures, mutations))
  writeTree(output, 'Instances.v', emitRocq(fixtures, mutations))
  writeTree(output, 'projection/policy.te', projected.policyText)
  for (const source of SOURCES.slice(1)) {
    const base = bases[source.name]
    writeTree(output, `instances/${source.name}/${base.scenario.policy}`, base.policyBytes)
    writeTree(
      output,
      `instances/${source.name}/scenario.json`,
      read(path.join(source.directory, source.scenario)),
    )
  }
  for (const m of mutations.filter((mutation) => mutation.mvp)) {
    writeTree(output, `mutations/${m.name}/${m.mvp.scenario.policy}`, m.mvp.policyText)
    const scenario = `${JSON.stringify(m.mvp.scenario, null, 2)}\n`
    writeTree(output, `mutations/${m.name}/scenario.json`, scenario)
  }
  const index = {
    schema: 'be-model-policy-fixtures-v1',
    seed: set.seed,
    instances: fixtures.map((f) => ({
      name: f.name,
      source: f.source,
      policy_sha256: f.policySha256,
      projection: f.projection,
      mvp: SOURCES.slice(1).some((s) => s.name === f.name) ? `instances/${f.name}` : null,
    })),
    mutations: mutations.map((m) => ({
      name: m.name,
      instance: m.instance,
      defect: m.defect,
      edits: m.edits,
      policy_sha256: m.policySha256,
      mvp: m.mvp ? `mutations/${m.name}` : null,
    })),
  }
  writeTree(output, 'index.json', `${JSON.stringify(index, null, 2)}\n`)
  return { fixtures, mutations }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.length !== 4 || process.argv[2] !== '--output') {
    console.error('usage: node gen-policy-fixtures.mjs --output DIR')
    process.exit(2)
  }
  try {
    const { fixtures, mutations } = generate(path.resolve(process.argv[3]))
    console.log(
      `Beryllium policy fixtures: PASS instances=${fixtures.length - 1} ` +
        `projection=1 mutations=${mutations.length}`,
    )
  } catch (error) {
    console.error(`Beryllium policy fixtures: FAIL ${error.message}`)
    process.exit(1)
  }
}
