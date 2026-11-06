// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 partition handler registry.
//
// FRAMEWORK-OWNED.  Partition agents must not edit this file; they implement
// the exported handler objects in their own catalogue module.
//
// A handler is the only place partition-specific behaviour is allowed to
// exist.  The framework never substitutes a default, never guesses, and never
// reports a success-shaped placeholder: an unimplemented handler fails loudly
// with `not implemented`, which is a distinct condition from a fixture result
// and from a scratch fault.

import { staticHandlers } from './catalogue-static.mjs'
import { hostHandlers } from './catalogue-host.mjs'
import { dynamicHandlers, controlHandlers } from './catalogue-dynamic.mjs'
import { partitions } from './catalogue-schema.mjs'

// Every operation a partition may be asked to perform, and the partitions that
// must supply it.  A handler that declares an operation outside this table, or
// omits one inside it, is a framework violation rather than a fixture result.
export const handlerOperations = {
  static: ['materialiseDefect', 'classifyRejection'],
  host: ['describeScenario', 'classifyResult'],
  dynamic: ['materialiseDefect', 'classifyRun'],
  control: ['materialiseDefect', 'classifyRun']
}
export const handlerStates = ['not-implemented', 'implemented']

const registry = {
  static: staticHandlers,
  host: hostHandlers,
  dynamic: dynamicHandlers,
  control: controlHandlers
}

const fail = (condition, text) => {
  if (!condition) throw new Error(`R6 handlers: ${text}`)
}

for (const partition of partitions) {
  const handler = registry[partition]

  fail(handler !== undefined && handler !== null,
    `${partition} partition exports no handler object`)
  fail(handler.partition === partition,
    `${partition} handler declares partition ${handler.partition}`)
  fail(handlerStates.includes(handler.state),
    `${partition} handler declares unknown state ${handler.state}`)

  const declared = Object.keys(handler)
    .filter((key) => !['partition', 'state'].includes(key)).sort()

  fail(JSON.stringify(declared) === JSON.stringify([...handlerOperations[partition]].sort()),
    `${partition} handler operations are ${declared.join(',') || 'none'}, ` +
    `expected ${handlerOperations[partition].join(',')}`)

  for (const operation of handlerOperations[partition]) {
    const implementation = handler[operation]

    if (handler.state === 'not-implemented') {
      fail(implementation === null,
        `${partition}.${operation} is supplied while the handler declares not-implemented`)
      continue
    }
    fail(typeof implementation === 'function',
      `${partition}.${operation} is not implemented while the handler declares implemented`)
  }
}

export const handlerState = (partition) => {
  fail(partitions.includes(partition), `unknown partition ${partition}`)
  return registry[partition].state
}

export const notImplemented = (partition, operation) =>
  new Error(`BE_R6:FAIL ${partition}.${operation} not implemented`)

// The single entry point the framework uses to reach partition behaviour.
// There is deliberately no fallback branch: an unimplemented operation throws,
// and the caller must let it propagate.
export const invoke = (partition, operation, ...args) => {
  fail(partitions.includes(partition), `unknown partition ${partition}`)
  fail(handlerOperations[partition].includes(operation),
    `${partition} declares no operation ${operation}`)

  const handler = registry[partition]

  if (handler.state !== 'implemented') throw notImplemented(partition, operation)
  return handler[operation](...args)
}

export const summary = () =>
  partitions.map((partition) => `${partition}=${registry[partition].state}`).join(' ')
