(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Public logical-assumption ledger for the security model v1 policy layer
 * and hart binding (MVP M3, work package M3-3): one report per theorem of
 * Policy.v, Binding.v, and PolicyClaims.v, and the bundle's.
 *)

Require Import PolicyClaims.

Print Assumptions policy_decide_total.
Print Assumptions policy_a8_sound.
Print Assumptions policy_a8_flow_confinement.
Print Assumptions policy_a6_closure_equality.
Print Assumptions policy_a7_vacuous.
Print Assumptions policy_monitor_memory_ungranted.
Print Assumptions policy_seal_requires_conformance.
Print Assumptions policy_projection_view.
Print Assumptions policy_access_permission_bridge.
Print Assumptions policy_authority_grant_bridge.
Print Assumptions policy_projection_mappings_allowed.
Print Assumptions policy_projection_flows_equal.
Print Assumptions policy_projection_results.
Print Assumptions binding_h0_control_excluded.
Print Assumptions binding_h1_injective_total.
Print Assumptions binding_h2_private_state.
Print Assumptions binding_h3_single_writer.
Print Assumptions policy_instance1_results.
Print Assumptions policy_instance2_results.
Print Assumptions policy_instance3_results.
Print Assumptions policy_instance1_m02_results.
Print Assumptions security_model_v1_claims.
