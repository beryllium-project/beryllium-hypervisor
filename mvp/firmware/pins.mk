# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# Purpose: pin the unmodified upstream OpenSBI source that is the M11
#          firmware base (planning/mvp-m11-plan.md, D-2 and M11-2).
# Trust:   firmware/fetch.sh checks both the commit and tree before a build,
#          and firmware/build.sh checks them again. The built binary's
#          SHA-256 is MVP_PIN_FIRMWARE_BIN_SHA256 in tools/lock/tool-lock.conf.
# Scope:   source identity only. OpenSBI is an external input under build/,
#          never committed here.

MVP_FIRMWARE_URL := https://github.com/riscv-software-src/opensbi
MVP_FIRMWARE_COMMIT := ed70256dd22c09962d146e433834239825ef0616
MVP_FIRMWARE_TREE := f36850991d64f41366e89cd40f1c494f06b8561b
