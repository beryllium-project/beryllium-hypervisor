(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Public logical-assumption ledger for Architecture Model 0.2.
 *)

Require Import Claims.

Print Assumptions validation_success_inventory_closure.
Print Assumptions validation_success_complete_ownership_binding.
Print Assumptions accepted_proposal_has_no_direct_authority.
Print Assumptions sealing_requires_validation.
Print Assumptions root_derivation_requires_sealing.
Print Assumptions failed_validation_no_publication.
Print Assumptions activation_completeness.
Print Assumptions unique_private_ownership.
Print Assumptions canonical_resource_non_overlap.
Print Assumptions monitor_exclusion.
Print Assumptions derived_root_soundness.
Print Assumptions derived_rights_bounded.
Print Assumptions mapping_soundness.
Print Assumptions directional_channel_confinement.
Print Assumptions proposal_source_independence.
Print Assumptions source_independent_enforcement_behavior.
Print Assumptions maintained_proposals_canonicalize_equally.
Print Assumptions root_domain_binding.
Print Assumptions saved_state_separation.
Print Assumptions pre_fence_target_entry_denied.
Print Assumptions switch_freshness.
Print Assumptions canonical_state_immutable_after_sealing.
Print Assumptions terminal_fail_closed_behavior.
Print Assumptions architecture_model_0_2_claims.
