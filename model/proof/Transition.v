(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Checked save, root-write, fence, and entry transitions for Model 0.2.
 * Canonical state is immutable across every post-seal operation.
 *)

From Stdlib Require Import Bool List.
Require Import Model Initialization.
Import ListNotations.

Local Lemma domain_eqb_true :
  forall left right, domain_eqb left right = true -> left = right.
Proof.
  destruct left, right; simpl; intros; try discriminate; reflexivity.
Qed.

(** [save_register_file] updates only the outgoing domain's record. *)
Definition save_register_file (subject : domain) (registers : register_file)
    (saved : domain -> register_file) : domain -> register_file :=
  fun queried =>
    if domain_eqb queried subject then registers else saved queried.

(** [switch_request_valid] permits only a sealed active cross-domain switch. *)
Definition switch_request_valid (state : machine_state) (target : domain)
    : bool :=
  match active_domain state with
  | Some source =>
      running_context_valid state && negb (domain_eqb source target)
  | None => false
  end.

(**
 * [write_target_root] saves only source state, selects every target binding,
 * retains stale translations, and blocks target execution.
 *)
Definition write_target_root (state : machine_state) (target : domain)
    (outgoing : register_file) : machine_state :=
  if switch_request_valid state target then
    match active_domain state with
    | Some source =>
        {| state_phase := Switching;
           state_inventory_bound := state_inventory_bound state;
           state_proposal := state_proposal state;
           state_canonical := state_canonical state;
           state_enforcement := state_enforcement state;
           state_sealed := state_sealed state;
           active_domain := None;
           active_vcpu := Some (vcpu_for target);
           active_root := Some (root_for target);
           active_vmid := Some (vmid_for target);
           active_stack := Some (stack_for target);
           active_saved_state := Some (state_for target);
           pending_domain := Some target;
           root_write_complete := true;
           fence_complete := false;
           translation_cache := translation_cache state;
           saved_registers :=
             save_register_file source outgoing (saved_registers state) |}
    | None => failed_state state
    end
  else failed_state state.

(** [complete_hfence_gvma] clears all retained translations. *)
Definition complete_hfence_gvma (state : machine_state) : machine_state :=
  match state_phase state, root_write_complete state with
  | Switching, true =>
      {| state_phase := Switching;
         state_inventory_bound := state_inventory_bound state;
         state_proposal := state_proposal state;
         state_canonical := state_canonical state;
         state_enforcement := state_enforcement state;
         state_sealed := state_sealed state;
         active_domain := active_domain state;
         active_vcpu := active_vcpu state;
         active_root := active_root state;
         active_vmid := active_vmid state;
         active_stack := active_stack state;
         active_saved_state := active_saved_state state;
         pending_domain := pending_domain state;
         root_write_complete := true;
         fence_complete := true;
         translation_cache := [];
         saved_registers := saved_registers state |}
  | _, _ => failed_state state
  end.

(** [entry_ready] checks all sealed target bindings and fence completion. *)
Definition entry_ready (state : machine_state) (target : domain) : bool :=
  state_sealed state &&
  canonical_enforcement_bound state &&
  match state_phase state, pending_domain state, active_vcpu state,
        active_root state, active_vmid state, active_stack state,
        active_saved_state state, translation_cache state with
  | Switching, Some pending, Some processor, Some stage_root,
      Some identifier, Some trusted_sp, Some saved_id, [] =>
      domain_eqb pending target &&
      vcpu_eqb processor (vcpu_for target) &&
      root_eqb stage_root (root_for target) &&
      vmid_eqb identifier (vmid_for target) &&
      stack_eqb trusted_sp (stack_for target) &&
      state_id_eqb saved_id (state_for target) &&
      root_write_complete state &&
      fence_complete state
  | _, _, _, _, _, _, _, _ => false
  end.

(** [entered_state] commits a checked target entry without changing authority. *)
Definition entered_state (state : machine_state) (target : domain)
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
     root_write_complete := root_write_complete state;
     fence_complete := fence_complete state;
     translation_cache := translation_cache state;
     saved_registers := saved_registers state |}.

(** [enter_target] permits execution only after the checked fence boundary. *)
Definition enter_target (state : machine_state) (target : domain)
    : option machine_state :=
  if entry_ready state target then Some (entered_state state target) else None.

(** [enter_step] turns invalid target entry into terminal failure. *)
Definition enter_step (state : machine_state) (target : domain)
    : machine_state :=
  match enter_target state target with
  | Some entered => entered
  | None => failed_state state
  end.

(** [operation] is the complete post-seal operation vocabulary. *)
Inductive operation : Type :=
| OperationAccess (address : gpa) (requested : access_kind)
| OperationSwitch (target : domain) (outgoing : register_file)
| OperationFence
| OperationEnter (target : domain).

(** [operation_step] is the fail-closed post-seal dispatcher. *)
Definition operation_step (state : machine_state) (request : operation)
    : machine_state :=
  match request with
  | OperationAccess address requested =>
      fst (access_step state address requested)
  | OperationSwitch target outgoing =>
      write_target_root state target outgoing
  | OperationFence => complete_hfence_gvma state
  | OperationEnter target => enter_step state target
  end.

(** [root_domain_binding] proves successful entry selects one atomic binding. *)
Theorem root_domain_binding :
  forall state target entered,
    enter_target state target = Some entered ->
    active_domain entered = Some target /\
    active_vcpu entered = Some (vcpu_for target) /\
    active_root entered = Some (root_for target) /\
    active_vmid entered = Some (vmid_for target) /\
    active_stack entered = Some (stack_for target) /\
    active_saved_state entered = Some (state_for target).
Proof.
  intros state target entered Hentry.
  unfold enter_target in Hentry.
  destruct (entry_ready state target); try discriminate.
  inversion Hentry; subst.
  now repeat split.
Qed.

(**
 * [saved_state_separation] proves source save cannot modify target state.
 *)
Theorem saved_state_separation :
  forall state source target outgoing,
    active_domain state = Some source ->
    source <> target ->
    switch_request_valid state target = true ->
    saved_registers (write_target_root state target outgoing) target =
    saved_registers state target.
Proof.
  intros state source target outgoing Hsource Hdifferent Hvalid.
  unfold write_target_root.
  rewrite Hvalid, Hsource.
  simpl.
  unfold save_register_file.
  destruct (domain_eqb target source) eqn:Hequal; try reflexivity.
  apply domain_eqb_true in Hequal.
  symmetry in Hequal.
  contradiction.
Qed.

Local Lemma valid_root_write_properties :
  forall state target outgoing,
    switch_request_valid state target = true ->
    state_phase (write_target_root state target outgoing) = Switching /\
    root_write_complete (write_target_root state target outgoing) = true /\
    fence_complete (write_target_root state target outgoing) = false /\
    translation_cache (write_target_root state target outgoing) =
      translation_cache state.
Proof.
  intros state target outgoing Hvalid.
  unfold write_target_root.
  rewrite Hvalid.
  destruct (active_domain state) as [source |] eqn:Hsource.
  - now repeat split.
  - unfold switch_request_valid in Hvalid.
    rewrite Hsource in Hvalid.
    discriminate.
Qed.

Local Lemma ready_entry_has_completed_fence :
  forall state target,
    entry_ready state target = true ->
    fence_complete state = true.
Proof.
  intros state target Hready.
  unfold entry_ready in Hready.
  apply andb_true_iff in Hready as [_ Hready].
  destruct (state_phase state); simpl in Hready; try discriminate.
  destruct (pending_domain state); simpl in Hready; try discriminate.
  destruct (active_vcpu state); simpl in Hready; try discriminate.
  destruct (active_root state); simpl in Hready; try discriminate.
  destruct (active_vmid state); simpl in Hready; try discriminate.
  destruct (active_stack state); simpl in Hready; try discriminate.
  destruct (active_saved_state state); simpl in Hready; try discriminate.
  destruct (translation_cache state); simpl in Hready; try discriminate.
  repeat rewrite andb_true_iff in Hready.
  tauto.
Qed.

(**
 * [pre_fence_target_entry_denied] proves root selection alone cannot enter
 * the target, including the shared-VMID-zero projection.
 *)
Theorem pre_fence_target_entry_denied :
  forall state target outgoing,
    switch_request_valid state target = true ->
    enter_target (write_target_root state target outgoing) target = None.
Proof.
  intros state target outgoing Hvalid.
  destruct (valid_root_write_properties state target outgoing Hvalid)
    as [_ [_ [Hfence_pending _]]].
  unfold enter_target.
  destruct
    (entry_ready (write_target_root state target outgoing) target)
    eqn:Hready; try reflexivity.
  apply ready_entry_has_completed_fence in Hready.
  rewrite Hfence_pending in Hready.
  discriminate.
Qed.

Local Lemma successful_entry_has_empty_cache :
  forall state target entered,
    enter_target state target = Some entered ->
    translation_cache entered = [].
Proof.
  intros state target entered Hentry.
  unfold enter_target in Hentry.
  destruct (entry_ready state target) eqn:Hready; try discriminate.
  inversion Hentry; subst.
  unfold entry_ready in Hready.
  apply andb_true_iff in Hready as [_ Hready].
  destruct (state_phase state); simpl in Hready; try discriminate.
  destruct (pending_domain state); simpl in Hready; try discriminate.
  destruct (active_vcpu state); simpl in Hready; try discriminate.
  destruct (active_root state); simpl in Hready; try discriminate.
  destruct (active_vmid state); simpl in Hready; try discriminate.
  destruct (active_stack state); simpl in Hready; try discriminate.
  destruct (active_saved_state state); simpl in Hready; try discriminate.
  destruct (translation_cache state) eqn:Hcache;
    simpl in Hready; try discriminate.
  unfold entered_state.
  simpl.
  exact Hcache.
Qed.

(**
 * [switch_freshness] proves root write retains the old cache, fence clears
 * it, and no prior-root translation survives successful target entry.
 *)
Theorem switch_freshness :
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
      (complete_hfence_gvma (write_target_root state target outgoing)) = true /\
    forall cached,
      cached_root cached = previous ->
      ~ In cached (translation_cache entered).
Proof.
  intros state target outgoing previous entered _ Hvalid Hentry.
  destruct (valid_root_write_properties state target outgoing Hvalid)
    as [Hphase [Hroot_done [Hfence_pending Hcache]]].
  split; [exact Hroot_done |].
  split; [exact Hfence_pending |].
  split; [exact Hcache |].
  split.
  - unfold complete_hfence_gvma.
    rewrite Hphase, Hroot_done.
    reflexivity.
  - apply successful_entry_has_empty_cache in Hentry.
    rewrite Hentry.
    intros cached _ Hin.
    inversion Hin.
Qed.

(**
 * [canonical_state_immutable_after_sealing] proves no post-seal operation can
 * replace, remove, or augment canonical authority.
 *)
Theorem canonical_state_immutable_after_sealing :
  forall state request,
    state_canonical (operation_step state request) =
    state_canonical state.
Proof.
  intros state request.
  destruct request as [address requested | target outgoing | | target].
  - unfold operation_step, access_step.
    destruct (running_context_valid state); try reflexivity.
    destruct (checked_access state address requested) as [object |].
    + unfold cache_translation.
      destruct (active_root state) as [stage_root |]; try reflexivity.
      destruct (state_enforcement state) as [enforcement |];
        try reflexivity.
      destruct (derived_mapping enforcement stage_root address)
        as [[mapped derived_rights] |]; reflexivity.
    + reflexivity.
  - unfold operation_step, write_target_root.
    destruct (switch_request_valid state target); try reflexivity.
    destruct (active_domain state); reflexivity.
  - unfold operation_step, complete_hfence_gvma.
    destruct (state_phase state); try reflexivity;
      destruct (root_write_complete state); reflexivity.
  - unfold operation_step, enter_step, enter_target.
    destruct (entry_ready state target); reflexivity.
Qed.

Local Lemma failed_step_is_terminal :
  forall state request,
    state_phase state = Failed ->
    state_phase (operation_step state request) = Failed.
Proof.
  intros state request Hfailed.
  destruct request as [address requested | target outgoing | | target].
  - assert (Hcontext : running_context_valid state = false).
    {
      unfold running_context_valid.
      rewrite Hfailed.
      destruct (state_sealed state),
        (canonical_enforcement_bound state); reflexivity.
    }
    unfold operation_step, access_step.
    rewrite Hcontext.
    reflexivity.
  - assert (Hcontext : running_context_valid state = false).
    {
      unfold running_context_valid.
      rewrite Hfailed.
      destruct (state_sealed state),
        (canonical_enforcement_bound state); reflexivity.
    }
    unfold operation_step, write_target_root, switch_request_valid.
    destruct (active_domain state); simpl; try rewrite Hcontext; reflexivity.
  - unfold operation_step, complete_hfence_gvma.
    rewrite Hfailed.
    reflexivity.
  - assert (Hready : entry_ready state target = false).
    {
      unfold entry_ready.
      rewrite Hfailed.
      destruct (state_sealed state),
        (canonical_enforcement_bound state); reflexivity.
    }
    unfold operation_step, enter_step, enter_target.
    rewrite Hready.
    reflexivity.
Qed.

(**
 * [terminal_fail_closed_behavior] proves denied access grants nothing,
 * invalid transitions fail, and terminal failure cannot become runnable.
 *)
Theorem terminal_fail_closed_behavior :
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
    state_phase (operation_step state request) = Failed).
Proof.
  split.
  - split.
    + intros state address requested Hvalid Hdenied.
      unfold access_step.
      rewrite Hvalid, Hdenied.
      split; reflexivity.
    + intros state address requested Hinvalid.
      unfold access_step.
      rewrite Hinvalid.
      split; reflexivity.
  - split.
    + intros state target outgoing Hinvalid.
      unfold write_target_root.
      rewrite Hinvalid.
      reflexivity.
    + split.
      * intros state target Hinvalid.
        unfold enter_step, enter_target.
        rewrite Hinvalid.
        reflexivity.
      * apply failed_step_is_terminal.
Qed.
