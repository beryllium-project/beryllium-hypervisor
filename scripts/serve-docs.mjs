#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Serve one generated documentation tree at an HTTP root.
 *
 * VitePress 1.6.4 can generate portable relative URLs, but its preview command
 * mounts a relative-base build below an unusable "/./" path.  This bounded
 * server exposes only committed generated files and performs no generation.
 */
import { readFile, realpath, stat } from 'node:fs/promises'
import { createServer } from 'node:http'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const repositoryRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..'
)
const sites = {
  planning: path.join(repositoryRoot, 'docs', 'html'),
  helium: path.join(repositoryRoot, 'pathfinder', 'docs', 'html'),
  'planning-preview': path.join(
    repositoryRoot,
    'build',
    'docs',
    'preview',
    'planning'
  ),
  'helium-preview': path.join(
    repositoryRoot,
    'build',
    'docs',
    'preview',
    'helium'
  )
}
const siteName = process.argv[2]
const outputDirectory = sites[siteName]

if (!outputDirectory) {
  fail(
    'usage: serve-docs.mjs ' +
      'planning|helium|planning-preview|helium-preview ' +
      '[--host HOST] [--port PORT]'
  )
}

let outputRealDirectory
try {
  outputRealDirectory = await realpath(outputDirectory)
} catch (error) {
  console.error(`cannot resolve documentation root: ${outputDirectory}`)
  console.error(error)
  process.exit(1)
}

let host = '127.0.0.1'
let port = siteName.startsWith('planning') ? 4174 : 4173

for (let index = 3; index < process.argv.length; index += 1) {
  const argument = process.argv[index]
  if (argument === '--host' || argument === '--port') {
    if (index + 1 >= process.argv.length) {
      fail(`${argument} requires a value`)
    }
    const value = process.argv[index + 1]
    index += 1
    if (argument === '--host') {
      host = value
    } else {
      port = parsePort(value)
    }
    continue
  }
  if (argument.startsWith('--host=')) {
    host = argument.slice('--host='.length)
    continue
  }
  if (argument.startsWith('--port=')) {
    port = parsePort(argument.slice('--port='.length))
    continue
  }
  fail(`unknown documentation server argument: ${argument}`)
}

if (!host) {
  fail('documentation server host must not be empty')
}

const server = createServer((request, response) => {
  void handleRequest(request, response).catch((error) => {
    console.error(error)
    if (!response.headersSent) {
      response.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' })
    }
    response.end('Internal documentation server error\n')
  })
})

server.on('clientError', (error, socket) => {
  console.error(error)
  socket.end('HTTP/1.1 400 Bad Request\r\n\r\n')
})

server.listen(port, host, () => {
  const displayHost = host === '0.0.0.0' ? 'localhost' : host
  console.log(
    `${siteName} documentation served at http://${displayHost}:${port}/`
  )
})

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    server.close((error) => {
      if (error) {
        console.error(error)
        process.exitCode = 1
      }
    })
  })
}

async function handleRequest(request, response) {
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    response.writeHead(405, {
      Allow: 'GET, HEAD',
      'Content-Type': 'text/plain; charset=utf-8'
    })
    response.end('Method not allowed\n')
    return
  }

  let pathname
  try {
    pathname = decodeURIComponent(
      new URL(request.url ?? '/', 'http://localhost').pathname
    )
  } catch {
    response.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' })
    response.end('Malformed URL\n')
    return
  }

  const candidate = await resolveRequestPath(pathname)
  if (!candidate) {
    response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' })
    response.end('Not found\n')
    return
  }

  const body = await readFile(candidate)
  response.writeHead(200, {
    'Cache-Control': 'no-store',
    'Content-Length': body.length,
    'Content-Type': contentType(candidate)
  })
  response.end(request.method === 'HEAD' ? undefined : body)
}

async function resolveRequestPath(pathname) {
  const relative = pathname.replace(/^\/+/, '')
  const candidate = path.resolve(outputDirectory, relative)
  const prefix = `${outputDirectory}${path.sep}`

  if (candidate !== outputDirectory && !candidate.startsWith(prefix)) {
    return null
  }

  if (pathname.endsWith('/')) {
    return regularFile(path.join(candidate, 'index.html'))
  }
  return (
    (await regularFile(candidate)) ??
    (await regularFile(`${candidate}.html`)) ??
    regularFile(path.join(candidate, 'index.html'))
  )
}

async function regularFile(candidate) {
  try {
    const resolved = await realpath(candidate)
    const prefix = `${outputRealDirectory}${path.sep}`
    if (
      resolved !== outputRealDirectory &&
      !resolved.startsWith(prefix)
    ) {
      return null
    }
    const metadata = await stat(resolved)
    return metadata.isFile() ? resolved : null
  } catch (error) {
    if (
      error.code === 'ENOENT' ||
      error.code === 'ENOTDIR' ||
      error.code === 'ELOOP'
    ) {
      return null
    }
    throw error
  }
}

function contentType(candidate) {
  const types = {
    '.css': 'text/css; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.woff2': 'font/woff2'
  }
  return types[path.extname(candidate)] ?? 'application/octet-stream'
}

function parsePort(value) {
  if (!/^[0-9]+$/.test(value)) {
    fail(`documentation server port must be numeric: ${value}`)
  }
  const parsed = Number(value)
  if (parsed < 1 || parsed > 65535) {
    fail(`documentation server port is out of range: ${value}`)
  }
  return parsed
}

function fail(message) {
  console.error(message)
  process.exit(2)
}
