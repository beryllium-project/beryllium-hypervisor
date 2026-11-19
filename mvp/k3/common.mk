# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# M11-B's names (planning/mvp-m11-board-addendum.md), for every fragment
# under mvp/k3/. mvp/tools.mk includes the fragments that its last line
# names, this one first, before mvp/Makefile's image variables: a
# prerequisite or a := value here names only what is defined above it.
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/common.mk is read through mvp/Makefile: make -C mvp TARGET)
endif

K3B_DIR := $(MVP_DIR)/k3
K3B_BUILD := $(BUILD)/k3
# Tier 1: check's deterministic outputs, which the evidence bundle's
# images.sha256 lists, and its scratch, which nothing lists.
K3B_CHECK := $(K3B_BUILD)/check
K3B_WORK := $(K3B_BUILD)/work
# Tier 2: the board gate's outputs and record, and the card images.
K3B_GATE := $(K3B_BUILD)/gate
K3B_CARD := $(K3B_BUILD)/card
K3B_RECORDS := $(RECORDS)/k3
K3B_PUBLISHED_PINS := $(K3B_DIR)/published-pins.txt
K3B_PLATFORM := $(K3B_DIR)/platform.json

# The images under test, GCC only (QB12): each one's sitting, board boot
# image, expectation, and name on the card.
K3B_IMAGES := two-guests-off anchor k3-breach-g1 k3-breach-c
K3B_SITTING_two-guests-off := first
K3B_BOARD_IMAGE_two-guests-off := $(BUILD)/variants/gcc/two-guests-off/be-mvp-boot.img
K3B_EXPECT_two-guests-off := $(GEN)/expect/two-guests-off.json
K3B_STAGED_two-guests-off := be-mvp-two-guests-off-gcc.img
K3B_SITTING_anchor := second
K3B_BOARD_IMAGE_anchor := $(BUILD)/gcc/anchor/be-mvp-boot.img
K3B_EXPECT_anchor := $(GEN)/anchor/expect/anchor.json
K3B_STAGED_anchor := be-mvp-anchor-gcc.img
K3B_SITTING_k3-breach-g1 := second
K3B_BOARD_IMAGE_k3-breach-g1 := $(K3B_CHECK)/breach/gcc/k3-breach-g1/be-mvp-boot.img
K3B_STAGED_k3-breach-g1 := be-mvp-anchor-k3-breach-g1-gcc.img
K3B_SITTING_k3-breach-c := second
K3B_BOARD_IMAGE_k3-breach-c := $(K3B_CHECK)/breach/gcc/k3-breach-c/be-mvp-boot.img
K3B_STAGED_k3-breach-c := be-mvp-anchor-k3-breach-c-gcc.img

# The board gate's steps, in order; each fragment adds its own.
K3B_GATE_STEPS :=
