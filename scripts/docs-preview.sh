#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Serve one generated documentation site and optionally open it from WSL.
# Direct file browsing remains a static fallback; HTTP provides the full UI.
set -eu

repository=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
site=${1:-}

if [ "$#" -gt 0 ]; then
	shift
fi

case "$site" in
planning)
	label='Beryllium'
	build_command='docs:build:http'
	server_site='planning-preview'
	host=${BE_DOCS_HOST:-127.0.0.1}
	port=${BE_DOCS_PORT:-4174}
	no_browser=${BE_NO_BROWSER:-0}
	;;
*)
	printf 'usage: scripts/docs-preview.sh planning [options]\n' >&2
	exit 2
	;;
esac

usage()
{
	cat <<'EOF'
Usage: docs-preview.sh planning [--host HOST] [--port PORT]

Environment:
  BE_DOCS_HOST     Preview bind address (default: 127.0.0.1)
  BE_DOCS_PORT     Preview TCP port (default: 4174)
  BE_NO_BROWSER=1  Do not open the Windows browser under WSL
EOF
}

while [ "$#" -gt 0 ]; do
	case "$1" in
	--host)
		[ "$#" -ge 2 ] || {
			printf '%s\n' '--host requires a value' >&2
			exit 2
		}
		host=$2
		shift 2
		;;
	--host=*)
		host=${1#*=}
		shift
		;;
	--port)
		[ "$#" -ge 2 ] || {
			printf '%s\n' '--port requires a value' >&2
			exit 2
		}
		port=$2
		shift 2
		;;
	--port=*)
		port=${1#*=}
		shift
		;;
	-h | --help)
		usage
		exit 0
		;;
	*)
		printf 'unknown preview argument: %s\n' "$1" >&2
		usage >&2
		exit 2
		;;
	esac
done

[ -n "$host" ] || {
	printf 'preview host must not be empty\n' >&2
	exit 2
}
case "$port" in
'' | *[!0-9]*)
	printf 'preview port must be numeric\n' >&2
	exit 2
	;;
esac
if [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
	printf 'preview port is out of range: %s\n' "$port" >&2
	exit 2
fi

npm --prefix "$repository" run "$build_command"

if ! grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null &&
	! grep -qi microsoft /proc/version 2>/dev/null; then
	exec node "$repository/scripts/serve-docs.mjs" "$server_site" \
		--host "$host" --port "$port"
fi

command -v curl >/dev/null 2>&1 || {
	printf 'missing required WSL preview tool: curl\n' >&2
	exit 1
}

url=http://localhost:$port/
node "$repository/scripts/serve-docs.mjs" "$server_site" \
	--host "$host" --port "$port" &
server_pid=$!

cleanup()
{
	if kill -0 "$server_pid" 2>/dev/null; then
		kill "$server_pid" 2>/dev/null || true
	fi
	wait "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM

attempt=0
while ! curl --fail --silent --output /dev/null "$url"; do
	attempt=$((attempt + 1))
	if [ "$attempt" -ge 100 ]; then
		printf '%s preview did not start at %s\n' "$label" "$url" >&2
		exit 1
	fi
	sleep 0.1
done

printf 'Open %s documentation: %s\n' "$label" "$url"

if [ "$no_browser" != 1 ]; then
	if command -v wslview >/dev/null 2>&1; then
		wslview "$url" >/dev/null 2>&1 ||
			printf 'Could not launch wslview; open %s manually.\n' "$url" \
				>&2
	elif command -v powershell.exe >/dev/null 2>&1; then
		powershell.exe -NoProfile -NonInteractive \
			-Command "Start-Process '$url'" >/dev/null 2>&1 ||
			printf 'Could not launch Windows browser; open %s manually.\n' \
				"$url" >&2
	elif command -v cmd.exe >/dev/null 2>&1; then
		cmd.exe /c start "" "$url" >/dev/null 2>&1 ||
			printf 'Could not launch Windows browser; open %s manually.\n' \
				"$url" >&2
	else
		printf 'No Windows browser launcher found; open %s manually.\n' \
			"$url" >&2
	fi
fi

wait "$server_pid"
