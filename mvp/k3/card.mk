# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/card.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the firmware's FIT, the environment, and the card image (B-4).
