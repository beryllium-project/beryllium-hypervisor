(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Public Architecture Model 0.2 theorem bundle.
 *
 * The bundle covers only the fixed abstract single-hart, two-domain model.
 * It is not a C, assembly, compiler, firmware, or hardware refinement.
 *)

From Stdlib Require Import List.
Require Export Model Initialization Isolation Transition.

(** [architecture_model_0_2_claim_set] records every public obligation. *)
Record architecture_model_0_2_claim_set : Prop := {
  claim_inventory_closure :
    forall input canonical,
      canonicalize input = Some canonical ->
      proposal_inventory_closed input = true /\
      forall stage_root address object derived_rights,
        derived_mapping (derive_enforcement canonical) stage_root address =
          Some (object, derived_rights) ->
        In object platform_inventory;

  claim_complete_ownership_binding :
    forall input canonical,
      canonicalize input = Some canonical ->
      canonical = canonical_configuration /\
      forall subject,
        In subject (canonical_domains canonical) /\
        frame_owner (private_for subject) = Some subject /\
        domain_for_root (root_for subject) = subject;

  claim_no_direct_authority :
    forall input canonical,
      canonicalize input = Some canonical ->
      proposal_direct_authority input = false;

  claim_sealing_requires_validation :
    forall state,
      state_phase (seal_state state) = Sealed ->
      state_phase state = Validated /\
      exists canonical,
        state_canonical state = Some canonical /\
        state_enforcement state = None /\
        state_sealed state = false;

  claim_derivation_requires_sealing :
    forall state,
      state_phase (derive_roots state) = RootsDerived ->
      state_phase state = Sealed /\
      state_sealed state = true /\
      exists canonical,
        state_canonical state = Some canonical /\
        state_enforcement state = None;

  claim_failed_validation_no_publication :
    forall input,
      proposal_valid input = false ->
      state_phase (validate_proposal (copied_proposal_state input)) = Failed /\
      state_canonical (validate_proposal (copied_proposal_state input)) =
        None /\
      state_enforcement (validate_proposal (copied_proposal_state input)) =
        None /\
      running_context_valid
        (validate_proposal (copied_proposal_state input)) = false;

  claim_activation_completeness :
    forall state target entered,
      activate_domain state target = Some entered ->
      state_phase state = RootsDerived /\
      state_sealed state = true /\
      exists canonical enforcement,
        state_canonical state = Some canonical /\
        state_enforcement state = Some enforcement /\
        canonical = canonical_configuration /\
        enforcement = derive_enforcement canonical;

  claim_unique_private_ownership :
    forall object first second,
      private_frame object ->
      frame_owner object = Some first ->
      frame_owner object = Some second ->
      first = second;

  claim_resource_non_overlap :
    forall left right,
      In left platform_inventory ->
      In right platform_inventory ->
      left <> right ->
      extents_disjoint left right;

  claim_monitor_exclusion :
    forall enforcement stage_root address object derived_rights,
      derived_mapping enforcement stage_root address =
        Some (object, derived_rights) ->
      monitor_private object ->
      False;

  claim_derived_root_soundness :
    forall canonical stage_root address object derived_rights,
      derived_mapping (derive_enforcement canonical) stage_root address =
        Some (object, derived_rights) ->
      canonical_mapping (domain_for_root stage_root) address =
        Some (object, derived_rights);

  claim_derived_rights_bounded :
    forall canonical stage_root address object derived_rights,
      derived_mapping (derive_enforcement canonical) stage_root address =
        Some (object, derived_rights) ->
      rights_subset derived_rights
        (canonical_authority (domain_for_root stage_root) object);

  claim_mapping_soundness :
    forall state address requested object,
      checked_access state address requested = Some object ->
      exists subject stage_root enforcement derived_rights,
        active_domain state = Some subject /\
        active_root state = Some stage_root /\
        state_enforcement state = Some enforcement /\
        stage_root = root_for subject /\
        derived_mapping enforcement stage_root address =
          Some (object, derived_rights) /\
        canonical_mapping subject address =
          Some (object, derived_rights) /\
        rights_subset derived_rights
          (canonical_authority subject object);

  claim_directional_channel :
    (forall state address requested,
      checked_access state address requested = Some SharedFrame ->
      exists subject derived_rights,
        active_domain state = Some subject /\
        address = SharedGPA /\
        canonical_mapping subject address =
          Some (SharedFrame, derived_rights) /\
        rights_subset derived_rights (channel_rights subject)) /\
    (forall first second object first_address second_address
        first_rights second_rights,
      first <> second ->
      canonical_mapping first first_address = Some (object, first_rights) ->
      canonical_mapping second second_address = Some (object, second_rights) ->
      object = SharedFrame /\
      first_address = SharedGPA /\
      second_address = SharedGPA /\
      rights_subset first_rights (channel_rights first) /\
      rights_subset second_rights (channel_rights second));

  claim_proposal_source_independence :
    forall first second first_canonical second_canonical,
      canonicalize first = Some first_canonical ->
      canonicalize second = Some second_canonical ->
      first_canonical = second_canonical /\
      derive_enforcement first_canonical =
        derive_enforcement second_canonical;

  claim_source_independent_behavior :
    forall first second first_canonical second_canonical stage_root address,
      canonicalize first = Some first_canonical ->
      canonicalize second = Some second_canonical ->
      derived_mapping (derive_enforcement first_canonical)
        stage_root address =
      derived_mapping (derive_enforcement second_canonical)
        stage_root address;

  claim_maintained_proposal_equivalence :
    canonicalize proposal_source_a = canonicalize proposal_source_b;

  claim_root_domain_binding :
    forall state target entered,
      enter_target state target = Some entered ->
      active_domain entered = Some target /\
      active_vcpu entered = Some (vcpu_for target) /\
      active_root entered = Some (root_for target) /\
      active_vmid entered = Some (vmid_for target) /\
      active_stack entered = Some (stack_for target) /\
      active_saved_state entered = Some (state_for target);

  claim_saved_state_separation :
    forall state source target outgoing,
      active_domain state = Some source ->
      source <> target ->
      switch_request_valid state target = true ->
      saved_registers (write_target_root state target outgoing) target =
      saved_registers state target;

  claim_pre_fence_denial :
    forall state target outgoing,
      switch_request_valid state target = true ->
      enter_target (write_target_root state target outgoing) target = None;

  claim_switch_freshness :
    forall state target outgoing previous entered,
      active_root state = Some previous ->
      switch_request_valid state target = true ->
      enter_target
        (complete_hfence_gvma (write_target_root state target outgoing))
        target = Some entered ->
      root_write_complete (write_target_root state target outgoing) = true /\
      fence_complete (write_target_root state target outgoing) = false /\
      translation_cache (write_target_root state target outgoing) =
        translation_cache state /\
      fence_complete
        (complete_hfence_gvma (write_target_root state target outgoing)) =
        true /\
      forall cached,
        cached_root cached = previous ->
        ~ In cached (translation_cache entered);

  claim_canonical_immutability :
    forall state request,
      state_canonical (operation_step state request) =
      state_canonical state;

  claim_terminal_fail_closed :
    ((forall state address requested,
      running_context_valid state = true ->
      checked_access state address requested = None ->
      snd (access_step state address requested) = None /\
      fst (access_step state address requested) = state) /\
     (forall state address requested,
      running_context_valid state = false ->
      state_phase (fst (access_step state address requested)) = Failed /\
      snd (access_step state address requested) = None)) /\
    (forall state target outgoing,
      switch_request_valid state target = false ->
      state_phase (write_target_root state target outgoing) = Failed) /\
    (forall state target,
      entry_ready state target = false ->
      state_phase (enter_step state target) = Failed) /\
    (forall state request,
      state_phase state = Failed ->
      state_phase (operation_step state request) = Failed)
}.

(** [architecture_model_0_2_claims] packages all public obligations. *)
Theorem architecture_model_0_2_claims : architecture_model_0_2_claim_set.
Proof.
  refine
    {| claim_inventory_closure :=
         validation_success_inventory_closure;
       claim_complete_ownership_binding :=
         validation_success_complete_ownership_binding;
       claim_no_direct_authority :=
         accepted_proposal_has_no_direct_authority;
       claim_sealing_requires_validation :=
         sealing_requires_validation;
       claim_derivation_requires_sealing :=
         root_derivation_requires_sealing;
       claim_failed_validation_no_publication :=
         failed_validation_no_publication;
       claim_activation_completeness :=
         activation_completeness;
       claim_unique_private_ownership :=
         unique_private_ownership;
       claim_resource_non_overlap :=
         canonical_resource_non_overlap;
       claim_monitor_exclusion :=
         monitor_exclusion;
       claim_derived_root_soundness :=
         derived_root_soundness;
       claim_derived_rights_bounded :=
         derived_rights_bounded;
       claim_mapping_soundness :=
         mapping_soundness;
       claim_directional_channel :=
         directional_channel_confinement;
       claim_proposal_source_independence :=
         proposal_source_independence;
       claim_source_independent_behavior :=
         source_independent_enforcement_behavior;
       claim_maintained_proposal_equivalence :=
         maintained_proposals_canonicalize_equally;
       claim_root_domain_binding :=
         root_domain_binding;
       claim_saved_state_separation :=
         saved_state_separation;
       claim_pre_fence_denial :=
         pre_fence_target_entry_denied;
       claim_switch_freshness :=
         switch_freshness;
       claim_canonical_immutability :=
         canonical_state_immutable_after_sealing;
       claim_terminal_fail_closed :=
         terminal_fail_closed_behavior |}.
Qed.
