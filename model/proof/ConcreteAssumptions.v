(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Logical-assumption ledger for stage 1's concrete model (MVP M8, work
 * package M8-3; planning/mvp-m8-specifications.md, frozen at SHA-256
 * ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d): one
 * report per theorem of ConcreteRings.v, ConcreteBridge.v, and
 * ConcreteClaims.v.
 *)

Require Import ConcreteRings ConcreteBridge ConcreteClaims.

Print Assumptions ring_no_overrun.
Print Assumptions ring_take_published_only.
Print Assumptions ring_indices_monotone.
Print Assumptions control_ring_fails_closed.
Print Assumptions input_ring_drops_under_room.
Print Assumptions ring_fifo_integrity.
Print Assumptions ring_type_set.
Print Assumptions drain_round_robin.
Print Assumptions drain_in_order.
Print Assumptions concrete_step_within_footprint.
Print Assumptions single_writer_carried.
Print Assumptions roots_from_instance.
Print Assumptions flow_is_declared_channel.
Print Assumptions instance_page_numbering.
Print Assumptions mgmt_grants_from_instance.
Print Assumptions barrier_publication_block.
Print Assumptions denial_iff_entry_below_ceiling.
Print Assumptions denial_record_before_resume.
Print Assumptions mgmt_decided_by_control_hart.
Print Assumptions mgmt_outcome_from_grants.
Print Assumptions mgmt_one_pending_per_domain.
Print Assumptions mgmt_answered_once.
Print Assumptions parked_never_resumes.
Print Assumptions entry_after_gate.
Print Assumptions gate_false_no_start.
Print Assumptions stage1_claims.
