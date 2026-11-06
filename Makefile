# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# The repository's root targets, which ./be runs: gates 6 and 7 of MVP 1.0's
# eight (model-check and model-evaluate) and the planning site's checks.
# `make` alone prints ./be's help, which lists all eight gates; the MVP's
# own gates run through ./mvp/mvp and mvp/Makefile.

.PHONY: help model-check model-evaluate docs-source-check docs-check

help:
	@./be help

model-check: docs-source-check
	$(MAKE) -C model check

model-evaluate:
	$(MAKE) -C model evaluate

docs-source-check:
	npm run docs:source-check

docs-check:
	npm run docs:check
