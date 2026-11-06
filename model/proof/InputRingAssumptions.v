(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(* Logical-assumption ledger for InputRing.v (MVP M7-5): one per theorem. *)

Require Import InputRing.

Print Assumptions input_ring_single_writer.
Print Assumptions input_ring_disjoint_from_control.
Print Assumptions input_drop_rule.
Print Assumptions input_routing_to_focus.
