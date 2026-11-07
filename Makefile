# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# The repository's root targets, which ./be runs: gates 6 and 7 of MVP 1.0's
# eight (model-check and model-evaluate) and the planning site's checks.
# `make` alone prints ./be's help, which lists all eight gates; the MVP's
# own gates run through ./mvp/mvp and mvp/Makefile. The documentation
# source check, and so gate 6, first installs the packages afresh from
# package-lock.json with npm ci, which removes any node_modules and checks
# each package against the lock's integrity, so that no tree already there
# is trusted (the release's security review, S-03).

.PHONY: help model-check model-evaluate docs-source-check docs-check \
	node-modules

help:
	@./be help

model-check: docs-source-check
	$(MAKE) -C model check

model-evaluate:
	$(MAKE) -C model evaluate

node-modules:
	npm ci --no-audit --no-fund

docs-source-check: node-modules
	npm run docs:source-check

docs-check:
	npm run docs:check
