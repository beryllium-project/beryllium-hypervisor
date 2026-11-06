(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Beryllium single-hart runtime R7 bounded exact-byte proof.
 *
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Claims: the single exported theorem bundle for the R7 package.
 *
 * This module adds no new obligation. It exports exactly one proposition,
 * `be_r7_claims`, and one theorem, `be_r7_claims_hold`, assembled from the
 * per-module bundles already proved in ISA.v, Exact.v, Entry.v, Trap.v,
 * Switch.v, and Configuration.v. Nothing else is exported, and no claim is
 * strengthened here.
 *
 * What the bundle establishes, and only this:
 *
 *   1. ISA: the bounded RV64I/Zicsr/RV64C subset used by the scoped symbols
 *      is decoded by a guard-first decoder that re-encodes every accepted
 *      unit to the original bytes, and refuses every word outside the
 *      subset.
 *   2. Exact: the two pinned linked ELF images contain exactly the
 *      enumerated scoped symbols, words, and control-flow targets; every
 *      scoped unit decodes and re-encodes exactly; the cross-toolchain
 *      identical and differing sets are exactly as classified.
 *   3. Entry: the frozen reset, install, readback, and first-entry
 *      sequences have the stated shape, ordering, and terminal SRET.
 *   4. Trap: the trap wrapper exchanges the trusted stack first, masks the
 *      named controls before the C cut point, and writes the accepted
 *      320-byte frame at unique, aligned, bounded offsets.
 *   5. Switch: the root transaction writes, fences, reads back, and
 *      publishes in the accepted order; reset and restore never rewrite a
 *      G-stage root; the published tails are call-free; and the shared
 *      entry tail holds the sole R5 guest-return SRET.
 *   6. Configuration: the generated fixed configuration trace equals the
 *      frozen R1/R2 constants and implies exactly the stated finite access
 *      matrix.
 *
 * Complete cut-point and assumption ledger for the bundle. Each item below
 * is outside every theorem in this package and is restated in the module
 * that borders it:
 *
 *   - C cut points: the R3/R4/R5 restricted C mechanism bodies, the trap
 *     dispatch body, the C-formed pending switch binding, and the
 *     R1/R2 validator and Sv39x4 builder implementations are not proved.
 *   - Tool and parser boundaries: the direct ELF parser, the independent
 *     objdump cross-check, the direct configuration extractor, the exact
 *     input generator, and Rocq's own kernel and host platform are trusted.
 *   - Compiler and linker: GCC, Clang, GNU ld, and lld are trusted to have
 *     produced the pinned images; R7 proves properties of the bytes they
 *     emitted, not of the translation that emitted them.
 *   - Firmware and emulation: the pinned OpenSBI handoff and QEMU are
 *     trusted; no theorem here consumes a QEMU trace.
 *   - Architecture: the ratified RISC-V specification is assumed to be
 *     represented faithfully by the bounded local semantics; H-extension
 *     behaviour beyond the modelled encodings is not formalised.
 *   - Profile: single hart, no DMA, no devices, no guest SBI, and the fixed
 *     synthetic two-domain profile are assumed throughout.
 *
 * Explicit non-claims. This bundle is not a proof of the R5 runtime, of any
 * C body, of the whole ELF image, of the whole hypervisor, of information
 * flow, availability, timing, or side channels, and not a hardware or
 * formal-verification result for Beryllium. Hardware validation remains
 * NOT RUN. Nothing here transfers a Model 0.2 or Helium theorem, selects
 * CHERI, software capabilities, or Type Enforcement, or authorises an
 * R8 or any successor package.
 *)

From Stdlib Require Import ZArith String List Bool.
Require Import ISA ExactInput Exact Entry Trap Switch
               ConfigurationTrace Configuration.

(* The single exported bundle. Each conjunct is the already-proved bundle of
   one maintained module; this module introduces no further obligation. *)
Definition be_r7_claims : Prop :=
  isa_claims
  /\ exact_claims
  /\ entry_claims
  /\ trap_claims
  /\ switch_claims
  /\ configuration_claims.

Theorem be_r7_claims_hold : be_r7_claims.
Proof.
  exact (conj isa_claims_hold
         (conj exact_claims_hold
         (conj entry_claims_hold
         (conj trap_claims_hold
         (conj switch_claims_hold
               configuration_claims_hold))))).
Qed.

(* Reported by the proof stage: the bundle must be closed under the global
   context, with no axiom, admitted proof, or project parameter. *)
Print Assumptions be_r7_claims_hold.
