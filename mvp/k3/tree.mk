# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/tree.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the board's device tree (B-3), and D-3's checker on it.
