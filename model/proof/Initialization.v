(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Model 0.2 inventory binding, proposal copying, canonical validation,
 * sealing, root derivation, and initial activation.
 *)

From Stdlib Require Import Bool List PeanoNat.
Require Import Model.
Import ListNotations.

(** [inventory_input] abstracts the two structural inventory checks. *)
Record inventory_input : Type := {
  inventory_complete : bool;
  inventory_nonoverlap : bool
}.

Definition inventory_valid (input : inventory_input) : bool :=
  inventory_complete input && inventory_nonoverlap input.

Definition fixed_inventory : inventory_input :=
  {| inventory_complete := true; inventory_nonoverlap := true |}.

(** [bind_inventory] accepts inventory only from the empty phase. *)
Definition bind_inventory (state : machine_state) (input : inventory_input)
    : machine_state :=
  match state_phase state with
  | Empty =>
      if inventory_valid input then
        {| state_phase := InventoryBound;
           state_inventory_bound := true;
           state_proposal := None;
           state_canonical := None;
           state_enforcement := None;
           state_sealed := false;
           active_domain := None;
           active_vcpu := None;
           active_root := None;
           active_vmid := None;
           active_stack := None;
           active_saved_state := None;
           pending_domain := None;
           root_write_complete := false;
           fence_complete := false;
           translation_cache := [];
           saved_registers := saved_registers state |}
      else failed_state state
  | _ => failed_state state
  end.

(** [copy_proposal] copies untrusted input but publishes no authority. *)
Definition copy_proposal (state : machine_state) (input : proposal)
    : machine_state :=
  match state_phase state, state_inventory_bound state with
  | InventoryBound, true =>
      {| state_phase := ProposalCopied;
         state_inventory_bound := true;
         state_proposal := Some input;
         state_canonical := None;
         state_enforcement := None;
         state_sealed := false;
         active_domain := None;
         active_vcpu := None;
         active_root := None;
         active_vmid := None;
         active_stack := None;
         active_saved_state := None;
         pending_domain := None;
         root_write_complete := false;
         fence_complete := false;
         translation_cache := [];
         saved_registers := saved_registers state |}
  | _, _ => failed_state state
  end.

(** [validate_proposal] publishes canonical state only after full validation. *)
Definition validate_proposal (state : machine_state) : machine_state :=
  match state_phase state, state_proposal state with
  | ProposalCopied, Some input =>
      match canonicalize input with
      | Some canonical =>
          {| state_phase := Validated;
             state_inventory_bound := state_inventory_bound state;
             state_proposal := Some input;
             state_canonical := Some canonical;
             state_enforcement := None;
             state_sealed := false;
             active_domain := None;
             active_vcpu := None;
             active_root := None;
             active_vmid := None;
             active_stack := None;
             active_saved_state := None;
             pending_domain := None;
             root_write_complete := false;
             fence_complete := false;
             translation_cache := [];
             saved_registers := saved_registers state |}
      | None => failed_state state
      end
  | _, _ => failed_state state
  end.

(** [seal_state] is the only transition making canonical state authoritative. *)
Definition seal_state (state : machine_state) : machine_state :=
  match state_phase state, state_canonical state,
        state_enforcement state, state_sealed state with
  | Validated, Some canonical, None, false =>
      {| state_phase := Sealed;
         state_inventory_bound := state_inventory_bound state;
         state_proposal := state_proposal state;
         state_canonical := Some canonical;
         state_enforcement := None;
         state_sealed := true;
         active_domain := None;
         active_vcpu := None;
         active_root := None;
         active_vmid := None;
         active_stack := None;
         active_saved_state := None;
         pending_domain := None;
         root_write_complete := false;
         fence_complete := false;
         translation_cache := [];
         saved_registers := saved_registers state |}
  | _, _, _, _ => failed_state state
  end.

(** [derive_roots] constructs enforcement only from sealed canonical state. *)
Definition derive_roots (state : machine_state) : machine_state :=
  match state_phase state, state_canonical state,
        state_enforcement state, state_sealed state with
  | Sealed, Some canonical, None, true =>
      {| state_phase := RootsDerived;
         state_inventory_bound := state_inventory_bound state;
         state_proposal := state_proposal state;
         state_canonical := Some canonical;
         state_enforcement := Some (derive_enforcement canonical);
         state_sealed := true;
         active_domain := None;
         active_vcpu := None;
         active_root := None;
         active_vmid := None;
         active_stack := None;
         active_saved_state := None;
         pending_domain := None;
         root_write_complete := false;
         fence_complete := false;
         translation_cache := [];
         saved_registers := saved_registers state |}
  | _, _, _, _ => failed_state state
  end.

(** [activation_ready] checks sealed derivation and the roots-derived phase. *)
Definition activation_ready (state : machine_state) : bool :=
  state_sealed state &&
  canonical_enforcement_bound state &&
  match state_phase state, translation_cache state with
  | RootsDerived, [] => true
  | _, _ => false
  end.

(** [activated_state] atomically selects every target binding. *)
Definition activated_state (state : machine_state) (target : domain)
    : machine_state :=
  {| state_phase := Active;
     state_inventory_bound := state_inventory_bound state;
     state_proposal := state_proposal state;
     state_canonical := state_canonical state;
     state_enforcement := state_enforcement state;
     state_sealed := state_sealed state;
     active_domain := Some target;
     active_vcpu := Some (vcpu_for target);
     active_root := Some (root_for target);
     active_vmid := Some (vmid_for target);
     active_stack := Some (stack_for target);
     active_saved_state := Some (state_for target);
     pending_domain := None;
     root_write_complete := true;
     fence_complete := true;
     translation_cache := [];
     saved_registers := saved_registers state |}.

(** [activate_domain] permits entry only after sealed root derivation. *)
Definition activate_domain (state : machine_state) (target : domain)
    : option machine_state :=
  if activation_ready state
  then Some (activated_state state target)
  else None.

(** A concrete copied state supports precise no-publication proofs. *)
Definition copied_proposal_state (input : proposal) : machine_state :=
  copy_proposal (bind_inventory cold_state fixed_inventory) input.

(**
 * [validation_success_inventory_closure] proves both the accepted proposal's
 * closure bit and that every derived mapping names an inventory resource.
 *)
Theorem validation_success_inventory_closure :
  forall input canonical,
    canonicalize input = Some canonical ->
    proposal_inventory_closed input = true /\
    forall stage_root address object derived_rights,
      derived_mapping (derive_enforcement canonical) stage_root address =
        Some (object, derived_rights) ->
      In object platform_inventory.
Proof.
  intros [identity vocabulary order closed bindings valid_rights direct]
    canonical Hcanonical.
  unfold canonicalize in Hcanonical.
  destruct (proposal_valid
    {| proposal_identity := identity;
       proposal_vocabulary := vocabulary;
       proposal_record_order := order;
       proposal_inventory_closed := closed;
       proposal_bindings_complete := bindings;
       proposal_rights_valid := valid_rights;
       proposal_direct_authority := direct |}) eqn:Hvalid;
    try discriminate.
  inversion Hcanonical; subst canonical.
  split.
  - unfold proposal_valid in Hvalid.
    simpl in Hvalid.
    repeat rewrite andb_true_iff in Hvalid.
    tauto.
  -
  intros stage_root address object derived_rights Hmapping.
  destruct stage_root, address; simpl in Hmapping;
    inversion Hmapping; subst; simpl; tauto.
Qed.

(**
 * [validation_success_complete_ownership_binding] carries complete canonical
 * domain, root, and private-owner bindings out of successful validation.
 *)
Theorem validation_success_complete_ownership_binding :
  forall input canonical,
    canonicalize input = Some canonical ->
    canonical = canonical_configuration /\
    forall subject,
      In subject (canonical_domains canonical) /\
      frame_owner (private_for subject) = Some subject /\
      domain_for_root (root_for subject) = subject.
Proof.
  intros input canonical Hcanonical.
  unfold canonicalize in Hcanonical.
  destruct (proposal_valid input); try discriminate.
  inversion Hcanonical; subst.
  split; [reflexivity |].
  destruct subject; simpl; auto.
Qed.

(**
 * [accepted_proposal_has_no_direct_authority] proves that successful
 * canonicalization excludes producer-published enforcement.
 *)
Theorem accepted_proposal_has_no_direct_authority :
  forall input canonical,
    canonicalize input = Some canonical ->
    proposal_direct_authority input = false.
Proof.
  intros [identity vocabulary order closed bindings valid_rights direct]
    canonical Hcanonical.
  unfold canonicalize in Hcanonical.
  destruct (proposal_valid
    {| proposal_identity := identity;
       proposal_vocabulary := vocabulary;
       proposal_record_order := order;
       proposal_inventory_closed := closed;
       proposal_bindings_complete := bindings;
       proposal_rights_valid := valid_rights;
       proposal_direct_authority := direct |}) eqn:Hvalid;
    try discriminate.
  unfold proposal_valid in Hvalid.
  simpl in Hvalid.
  repeat rewrite andb_true_iff in Hvalid.
  rewrite negb_true_iff in Hvalid.
  tauto.
Qed.

(** [sealing_requires_validation] makes the one-way seal precondition exact. *)
Theorem sealing_requires_validation :
  forall state,
    state_phase (seal_state state) = Sealed ->
    state_phase state = Validated /\
    exists canonical,
      state_canonical state = Some canonical /\
      state_enforcement state = None /\
      state_sealed state = false.
Proof.
  intros [current_phase inventory_bound proposed canonical enforcement sealed
    current_domain current_vcpu current_root current_vmid current_stack
    current_saved pending root_done fence_done cache saved] Hsealed.
  simpl in *.
  destruct current_phase; try discriminate.
  destruct canonical as [canonical |]; try discriminate.
  destruct enforcement; try discriminate.
  destruct sealed; try discriminate.
  split; [reflexivity |].
  exists canonical.
  repeat split; reflexivity.
Qed.

(** [root_derivation_requires_sealing] prevents pre-seal root publication. *)
Theorem root_derivation_requires_sealing :
  forall state,
    state_phase (derive_roots state) = RootsDerived ->
    state_phase state = Sealed /\
    state_sealed state = true /\
    exists canonical,
      state_canonical state = Some canonical /\
      state_enforcement state = None.
Proof.
  intros [current_phase inventory_bound proposed canonical enforcement sealed
    current_domain current_vcpu current_root current_vmid current_stack
    current_saved pending root_done fence_done cache saved] Hderived.
  simpl in *.
  destruct current_phase; try discriminate.
  destruct canonical as [canonical |]; try discriminate.
  destruct enforcement; try discriminate.
  destruct sealed; try discriminate.
  repeat split; try reflexivity.
  exists canonical.
  repeat split; reflexivity.
Qed.

(**
 * [failed_validation_no_publication] proves invalid copied input reaches
 * failure with no canonical state, roots, or runnable binding.
 *)
Theorem failed_validation_no_publication :
  forall input,
    proposal_valid input = false ->
    state_phase (validate_proposal (copied_proposal_state input)) = Failed /\
    state_canonical (validate_proposal (copied_proposal_state input)) = None /\
    state_enforcement (validate_proposal (copied_proposal_state input)) =
      None /\
    running_context_valid
      (validate_proposal (copied_proposal_state input)) = false.
Proof.
  intros input Hinvalid.
  unfold copied_proposal_state, bind_inventory, fixed_inventory,
    inventory_valid, copy_proposal, validate_proposal, canonicalize.
  simpl.
  rewrite Hinvalid.
  repeat split; reflexivity.
Qed.

Local Lemma canonical_bound_witness :
  forall state,
    canonical_enforcement_bound state = true ->
    state_canonical state = Some CanonicalConfiguration /\
    state_enforcement state = Some DerivedEnforcement.
Proof.
  intros state Hbound.
  unfold canonical_enforcement_bound in Hbound.
  destruct (state_canonical state) as [[] |] eqn:Hcanonical;
    destruct (state_enforcement state) as [[] |] eqn:Henforcement;
    simpl in Hbound; try discriminate.
  split; reflexivity.
Qed.

(**
 * [activation_completeness] proves successful initial entry requires sealed
 * canonical state and derived enforcement.
 *)
Theorem activation_completeness :
  forall state target entered,
    activate_domain state target = Some entered ->
    state_phase state = RootsDerived /\
    state_sealed state = true /\
    exists canonical enforcement,
      state_canonical state = Some canonical /\
      state_enforcement state = Some enforcement /\
      canonical = canonical_configuration /\
      enforcement = derive_enforcement canonical.
Proof.
  intros state target entered Hentry.
  unfold activate_domain in Hentry.
  destruct (activation_ready state) eqn:Hready; try discriminate.
  unfold activation_ready in Hready.
  apply andb_true_iff in Hready as [Hsealed_bound Hphase].
  apply andb_true_iff in Hsealed_bound as [Hsealed Hbound].
  destruct (canonical_bound_witness state Hbound)
    as [Hcanonical Henforcement].
  destruct (state_phase state) eqn:Hstatephase;
    simpl in Hphase; try discriminate.
  destruct (translation_cache state) eqn:Hcache;
    simpl in Hphase; try discriminate.
  split; [reflexivity |].
  split; [exact Hsealed |].
  exists CanonicalConfiguration, DerivedEnforcement.
  split; [exact Hcanonical |].
  split; [exact Henforcement |].
  split; reflexivity.
Qed.
