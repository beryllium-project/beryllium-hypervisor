(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Canonical resource, derivation, source-independence, and access proofs for
 * the fixed Model 0.2 instance.
 *)

From Stdlib Require Import Bool Lia List.
Require Import Model Initialization.

Local Lemma rights_subsetb_sound :
  forall derived authority,
    rights_subsetb derived authority = true ->
    rights_subset derived authority.
Proof.
  intros derived authority.
  unfold rights_subsetb, rights_subset.
  repeat rewrite andb_true_iff.
  repeat rewrite implb_true_iff.
  tauto.
Qed.

Local Lemma root_eqb_true :
  forall left right, root_eqb left right = true -> left = right.
Proof.
  destruct left, right; simpl; intros; try discriminate; reflexivity.
Qed.

Local Lemma running_context_bindings :
  forall state,
    running_context_valid state = true ->
    exists subject stage_root,
      active_domain state = Some subject /\
      active_root state = Some stage_root /\
      stage_root = root_for subject.
Proof.
  intros [current_phase inventory_bound proposed canonical enforcement sealed
    current_domain current_vcpu current_root current_vmid current_stack
    current_saved pending root_done fence_done cache saved] Hvalid.
  unfold running_context_valid in Hvalid.
  simpl in Hvalid.
  apply andb_true_iff in Hvalid as [_ Hbindings].
  destruct current_phase; simpl in Hbindings; try discriminate.
  destruct current_domain as [subject |]; simpl in Hbindings;
    try discriminate.
  destruct current_vcpu as [processor |]; simpl in Hbindings;
    try discriminate.
  destruct current_root as [stage_root |]; simpl in Hbindings;
    try discriminate.
  destruct current_vmid as [identifier |]; simpl in Hbindings;
    try discriminate.
  destruct current_stack as [trusted_sp |]; simpl in Hbindings;
    try discriminate.
  destruct current_saved as [saved_id |]; simpl in Hbindings;
    try discriminate.
  repeat rewrite andb_true_iff in Hbindings.
  assert (Hroot : root_eqb stage_root (root_for subject) = true) by tauto.
  apply root_eqb_true in Hroot.
  exists subject, stage_root.
  repeat split; try reflexivity; exact Hroot.
Qed.

(** [unique_private_ownership] preserves Model 0.1 private ownership. *)
Theorem unique_private_ownership :
  forall object first second,
    private_frame object ->
    frame_owner object = Some first ->
    frame_owner object = Some second ->
    first = second.
Proof.
  intros object first second _ Hfirst Hsecond.
  congruence.
Qed.

(**
 * [canonical_resource_non_overlap] proves every pair of distinct fixed
 * inventory resources has disjoint page-indexed extents.
 *)
Theorem canonical_resource_non_overlap :
  forall left right,
    In left platform_inventory ->
    In right platform_inventory ->
    left <> right ->
    extents_disjoint left right.
Proof.
  destruct left, right; simpl; intros _ _ Hdifferent;
    try contradiction; unfold extents_disjoint; simpl; lia.
Qed.

(** [monitor_exclusion] proves no derived root reaches monitor-owned state. *)
Theorem monitor_exclusion :
  forall enforcement stage_root address object derived_rights,
    derived_mapping enforcement stage_root address =
      Some (object, derived_rights) ->
    monitor_private object ->
    False.
Proof.
  intros enforcement stage_root address object derived_rights Hmapping.
  destruct enforcement, stage_root, address; simpl in Hmapping;
    inversion Hmapping; subst; simpl; contradiction.
Qed.

(**
 * [derived_root_soundness] proves every derived mapping is exactly the
 * canonical mapping for the bound domain and root.
 *)
Theorem derived_root_soundness :
  forall canonical stage_root address object derived_rights,
    derived_mapping (derive_enforcement canonical) stage_root address =
      Some (object, derived_rights) ->
    canonical_mapping (domain_for_root stage_root) address =
      Some (object, derived_rights).
Proof.
  intros canonical stage_root address object derived_rights Hmapping.
  destruct canonical, stage_root, address; exact Hmapping.
Qed.

(**
 * [derived_rights_bounded] proves every derived right is a subset of the
 * exact canonical domain/frame authority.
 *)
Theorem derived_rights_bounded :
  forall canonical stage_root address object derived_rights,
    derived_mapping (derive_enforcement canonical) stage_root address =
      Some (object, derived_rights) ->
    rights_subset derived_rights
      (canonical_authority (domain_for_root stage_root) object).
Proof.
  intros canonical stage_root address object derived_rights Hmapping.
  destruct canonical, stage_root, address; simpl in Hmapping;
    inversion Hmapping; subst; unfold rights_subset; simpl; tauto.
Qed.

(**
 * [mapping_soundness] proves every successful active access is derived from
 * the active domain's canonical authority.
 *)
Theorem mapping_soundness :
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
      rights_subset derived_rights (canonical_authority subject object).
Proof.
  intros state address requested object Haccess.
  unfold checked_access in Haccess.
  destruct (running_context_valid state) eqn:Hvalid; try discriminate.
  destruct (active_domain state) as [subject |] eqn:Hdomain;
    try discriminate.
  destruct (active_root state) as [stage_root |] eqn:Hroot;
    try discriminate.
  destruct (state_enforcement state) as [enforcement |] eqn:Henforcement;
    try discriminate.
  destruct (derived_mapping enforcement stage_root address)
    as [[mapped derived_rights] |] eqn:Hmapping; try discriminate.
  destruct
    (rights_subsetb derived_rights (canonical_authority subject mapped) &&
     rights_allow derived_rights requested) eqn:Hallowed; try discriminate.
  inversion Haccess; subst mapped.
  apply andb_true_iff in Hallowed as [Hsubset _].
  destruct (running_context_bindings state Hvalid)
    as [bound_subject [bound_root
      [Hbound_domain [Hbound_root Hbinding]]]].
  assert (Hcurrent_binding : stage_root = root_for subject) by congruence.
  destruct enforcement.
  simpl in Hmapping.
  exists subject, stage_root, DerivedEnforcement, derived_rights.
  split; [reflexivity |].
  split; [reflexivity |].
  split; [reflexivity |].
  split; [exact Hcurrent_binding |].
  split; [exact Hmapping |].
  split.
  - subst stage_root.
    destruct subject; exact Hmapping.
  - now apply rights_subsetb_sound.
Qed.

(**
 * [directional_channel_confinement] proves shared backing is the sole
 * cross-domain storage path and retains its directional rights.
 *)
Theorem directional_channel_confinement :
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
    rights_subset second_rights (channel_rights second)).
Proof.
  split.
  - intros state address requested Haccess.
    destruct (mapping_soundness state address requested SharedFrame Haccess)
      as [subject [stage_root [enforcement [derived_rights
        [Hdomain [Hroot [Henforcement [Hbinding
          [Hderived [Hcanonical Hsubset]]]]]]]]]].
    subst stage_root.
    destruct subject, address; simpl in Hcanonical;
      inversion Hcanonical; subst; try discriminate.
    + exists Management, read_write_rights.
      repeat split; try assumption; unfold rights_subset; simpl; tauto.
    + exists Protected, read_rights.
      repeat split; try assumption; unfold rights_subset; simpl; tauto.
  - intros first second object first_address second_address
      first_rights second_rights Hdifferent Hfirst Hsecond.
    destruct first, second; try contradiction;
      destruct first_address, second_address;
      simpl in Hfirst, Hsecond;
      inversion Hfirst; inversion Hsecond; subst; try discriminate;
      repeat split; try reflexivity; unfold rights_subset; simpl; tauto.
Qed.

(**
 * [proposal_source_independence] proves source vocabulary, producer identity,
 * and forward/reverse record order cannot change canonical or derived state.
 *)
Theorem proposal_source_independence :
  forall first second first_canonical second_canonical,
    canonicalize first = Some first_canonical ->
    canonicalize second = Some second_canonical ->
    first_canonical = second_canonical /\
    derive_enforcement first_canonical =
      derive_enforcement second_canonical.
Proof.
  intros first second first_canonical second_canonical
    Hfirst Hsecond.
  unfold canonicalize in *.
  destruct (proposal_valid first); try discriminate.
  destruct (proposal_valid second); try discriminate.
  inversion Hfirst; inversion Hsecond; subst.
  split; reflexivity.
Qed.

(**
 * [source_independent_enforcement_behavior] carries canonical equality into
 * every modeled root and access kind.
 *)
Theorem source_independent_enforcement_behavior :
  forall first second first_canonical second_canonical stage_root address,
    canonicalize first = Some first_canonical ->
    canonicalize second = Some second_canonical ->
    derived_mapping (derive_enforcement first_canonical) stage_root address =
    derived_mapping (derive_enforcement second_canonical) stage_root address.
Proof.
  intros first second first_canonical second_canonical stage_root address
    Hfirst Hsecond.
  destruct (proposal_source_independence
    first second first_canonical second_canonical Hfirst Hsecond)
    as [Hequal _].
  now subst second_canonical.
Qed.

(** The two maintained neutral fixtures exercise opposite proposal orders. *)
Theorem maintained_proposals_canonicalize_equally :
  canonicalize proposal_source_a = canonicalize proposal_source_b.
Proof.
  reflexivity.
Qed.
