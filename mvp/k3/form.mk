# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/form.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the capture checker's form for a boot from a card (B-8).
