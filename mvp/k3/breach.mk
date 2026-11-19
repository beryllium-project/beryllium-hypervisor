# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/breach.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the board's hostile-monitor images (B-10).
