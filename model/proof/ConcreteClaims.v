(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Purpose: stage 1's claims (MVP M8, work package M8-3;
 * planning/mvp-m8-plan.md, D-1 and Q15): the properties P1, P5, P6, and P7
 * of the specification's section 3 over Concrete.v's traces, the lineage
 * of Model 0.2's and M3's theorems, and the record bundling every stage-1
 * theorem.
 * Specification: planning/mvp-m8-specifications.md, SHA-256
 * ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d, accepted
 * as reviewer of record at exact commit 004f31ae with that hash unchanged;
 * its errata S-1 to S-4 (P1 scoped to the block's published words, P5
 * below the exit ceiling, the parked domain's reading, and
 * mgmt_answered_once's safety reading) are recorded in
 * planning/mvp-m8-plan.md's decision record, not in the document;
 * section 3, with the theorem names it fixes.
 * Semantics: every theorem is about Concrete.v's traces, sequentially
 * consistent interleavings, and nothing beyond them (the plan's D-3).
 * Trust: an abstract model of the protocol, not a refinement of the C.
 *
 * Lineage index (Q15), final: each of Model 0.2's 24 theorems (Assumptions.v)
 * and M3's 22 (PolicyAssumptions.v), as inherited (holds by import on the
 * shared vocabulary), re-proved (restated and proved over the concrete
 * model), strengthened (a stronger concrete statement proved), or
 * inapplicable (about the fixed single-hart profile's objects, Model.v's
 * closed inductives, which the MVP does not run; M6-4 deferred their
 * MVP instance, ledger U-13; Q35).
 *
 * Model 0.2:
 * validation_success_inventory_closure: inapplicable - the fixed profile's
 *   inventory; the MVP validates its own configuration in M6's ported R1
 *   mechanism, which stage 1 abstracts as prepare.
 * validation_success_complete_ownership_binding: inapplicable - as above.
 * accepted_proposal_has_no_direct_authority: inapplicable - Model 0.2's
 *   proposal pipeline over closed inductives.
 * sealing_requires_validation: inapplicable - abstracted as prepare.
 * root_derivation_requires_sealing: inapplicable - abstracted as prepare.
 * failed_validation_no_publication: re-proved - gate_false_no_start: a
 *   failed launch gate publishes nothing and starts no hart.
 * activation_completeness: inapplicable - the fixed profile's activation.
 * unique_private_ownership: inapplicable - closed inductives; the MVP's
 *   ownership is Binding.v's H2 (inherited below).
 * canonical_resource_non_overlap: inapplicable - closed inductives.
 * monitor_exclusion: re-proved - roots_from_instance: each root maps its
 *   window and its granted pages, no monitor memory.
 * derived_root_soundness: re-proved - roots_from_instance.
 * derived_rights_bounded: re-proved - roots_from_instance (A8 admits each
 *   right).
 * mapping_soundness: re-proved - roots_from_instance.
 * directional_channel_confinement: re-proved - flow_is_declared_channel.
 * proposal_source_independence: inapplicable - Model 0.2's proposals.
 * source_independent_enforcement_behavior: inapplicable - as above.
 * maintained_proposals_canonicalize_equally: inapplicable - as above.
 * root_domain_binding: inapplicable - the fixed profile's switch; the
 *   MVP's static binding is Binding.v's H1 (inherited below).
 * saved_state_separation: re-proved - single_writer_carried: a domain
 *   hart's saved frame is written by that hart alone.
 * pre_fence_target_entry_denied: inapplicable - the single-hart switch,
 *   which the MVP does not have.
 * switch_freshness: inapplicable - as above.
 * canonical_state_immutable_after_sealing: re-proved -
 *   single_writer_carried: no published object is written after the
 *   barrier.
 * terminal_fail_closed_behavior: re-proved - control_ring_fails_closed
 *   and denial_iff_entry_below_ceiling: a refused post fails its view for
 *   good; a fault not denied fails the domain.
 * architecture_model_0_2_claims: inapplicable - the bundle of the above.
 *
 * M3:
 * policy_decide_total: inherited - by import.
 * policy_a8_sound: inherited - used by roots_from_instance and
 *   mgmt_grants_from_instance.
 * policy_a8_flow_confinement: inherited - used by
 *   flow_is_declared_channel.
 * policy_a6_closure_equality: inherited - used by
 *   flow_is_declared_channel.
 * policy_a7_vacuous: inherited - by import.
 * policy_monitor_memory_ungranted: inherited - by import.
 * policy_seal_requires_conformance: inherited - by import.
 * policy_projection_view: inapplicable - Instance 1's projection of Model
 *   0.2's fixed profile, which the MVP does not run.
 * policy_access_permission_bridge: inapplicable - as above.
 * policy_authority_grant_bridge: inapplicable - as above.
 * policy_projection_mappings_allowed: inapplicable - as above.
 * policy_projection_flows_equal: inapplicable - as above.
 * policy_projection_results: inapplicable - as above.
 * binding_h0_control_excluded: inherited - mvp_binding is the concrete
 *   model's binding.
 * binding_h1_injective_total: inherited - as above.
 * binding_h2_private_state: inherited - as above.
 * binding_h3_single_writer: strengthened - single_writer_carried carries
 *   it to every word every concrete step changes, the input path's too.
 * policy_instance1_results: inapplicable - Instance 1, the fixed profile.
 * policy_instance2_results: inherited - te-poc's verdicts, recomputed in
 *   ConcreteBridge.v's instance_facts.
 * policy_instance3_results: inherited - anchor's, as above.
 * policy_instance1_m02_results: inapplicable - Instance 1's projection.
 * security_model_v1_claims: inherited - the bundle, by import.
 *
 * P9 (input routing) is InputRing.v's T1 to T4, inherited by import:
 * stage 1's input steps refine InputRing.v's (Concrete.v's
 * refines_input), and single_writer_carried applies T1 to them.
 *)

From Stdlib Require Import Bool List PeanoNat NArith Lia.
Require Import Binding InputRing ConcreteLayout Concrete ConcreteRings
  ConcreteBridge.
Import ListNotations.
Local Open Scope N_scope.

(* --------------------------------------------------------------------- *)
(** * P1: barrier publication *)

(*
 * Erratum S-1, barrier_publication: the literal property is false on
 * this model, faithful to the M0 and M2 plans: in anchor (domain 0 granted
 * pause on domain 1), hart 2's ready(1) can read the published generation
 * word after hart 0 has delivered a PAUSE into domain 1's inbound ring.
 * The trace: prepare; publish(0); publish(1); start(0); start(1); hart 1's
 * ready(0), its two posts, publish, and enter(0); hart 1's exit(0) with
 * the management call pause(1); its post and publish of the request;
 * hart 0's drain visits and decide_mgmt(0), delivered; hart 0's post of
 * PAUSE into inbound(1) and publish; then hart 2's ready(1). At that read
 * inbound(1)'s head is 24, not the 0 publish(1) wrote. The ring words are
 * shared after the barrier (I16); the block's published words are not,
 * and barrier_publication_block below proves the property for them, the
 * scoped P1 of erratum S-1.
 *)

(**
 * [published_writes c d]: the block's immutable published words and the
 * values publish(d) writes them (block_writes' descriptor with its hgatp,
 * first-entry frame, configuration, and walked window and leaves); the
 * zeroed controls, entered, and core words, which domain d's hart writes
 * from its ready on, and the ring index words, which have writers after
 * the barrier, are not among them.
 *)
Definition head_writes (c : config) (d : nat) : list (cword * N) :=
  [(WBlock d (BDesc 0), N.of_nat (dhart d));
   (WBlock d (BDesc 1), N.of_nat d);
   (WBlock d (BDesc 2), hgatp_of d);
   (WBlock d (BDesc 3), block_hpa d);
   (WBlock d BEntry, be_mvp_kernel_gpa);
   (WBlock d (BConfig 0), cfg_ceiling c);
   (WBlock d (BConfig 1), bool_word (cfg_accept_denial c));
   (WBlock d (BConfig 2), bool_word (cfg_accept_mgmt c));
   (WBlock d (BConfig 3), bool_word (cfg_input c d))].

Definition walked_writes (c : config) (d : nat) : list (cword * N) :=
  map (fun k => (WBlock d (BWalked k), nth k (walked_words (cfg_root c d)) 0))
    (seq 0 11).

Definition published_writes (c : config) (d : nat) : list (cword * N) :=
  head_writes c d ++ walked_writes c d.

Lemma block_writes_split :
  forall c d,
    block_writes c d =
    head_writes c d ++ [(WBlock d BControls, 0); (WBlock d BEntered, 0)] ++
    map (fun f => (WBlock d (BCore f), 0)) core_fields ++ walked_writes c d.
Proof. reflexivity. Qed.

Lemma upd_list_other :
  forall l m w, ~ In w (map fst l) -> upd_list m l w = m w.
Proof.
  induction l as [| [w' v'] rest IH]; intros m w Hn; [reflexivity |].
  simpl in Hn |- *; rewrite IH by tauto.
  apply upd_other; intros Heq; apply Hn; left; symmetry; exact Heq.
Qed.

Lemma upd_list_read :
  forall l m w v, NoDup (map fst l) -> In (w, v) l -> upd_list m l w = v.
Proof.
  induction l as [| [w' v'] rest IH]; intros m w v Hnd Hin; [destruct Hin |].
  simpl in Hnd, Hin |- *.
  inversion Hnd as [| ? ? Hn Hnd']; subst.
  destruct Hin as [Heq | Hin].
  - injection Heq as -> ->; rewrite upd_list_other by exact Hn; apply upd_same.
  - apply IH; assumption.
Qed.

Lemma block_writes_nodup : forall c d, NoDup (map fst (block_writes c d)).
Proof.
  intros c d; cbn [block_writes head_writes walked_writes map fst app seq
                   core_fields].
  repeat constructor; simpl; intros H;
    repeat (destruct H as [H | H]; [discriminate H |]); exact H.
Qed.

Lemma published_shape :
  forall c d w v, In (w, v) (published_writes c d) ->
    In (w, v) (block_writes c d) /\
    exists f, w = WBlock d f /\ block_published f = true /\ f <> BGen.
Proof.
  intros c d w v Hin; split.
  - rewrite block_writes_split; unfold published_writes in Hin.
    apply in_app_or in Hin as [Hin | Hin]; apply in_or_app; [left; exact Hin |].
    right; apply in_or_app; right; apply in_or_app; right; exact Hin.
  - unfold published_writes in Hin; apply in_app_or in Hin as [Hin | Hin].
    + simpl in Hin; repeat (destruct Hin as [Hin | Hin];
        [injection Hin as <- <-; eexists; repeat split;
         intros Heq; discriminate Heq |]); destruct Hin.
    + unfold walked_writes in Hin; apply in_map_iff in Hin as [k [Hk _]].
      injection Hk as <- <-; eexists; repeat split; intros Heq; discriminate Heq.
Qed.

(** Only hart 0's publication of block d writes its published words. *)
Lemma cwrites_published :
  forall st d f, cwrites st (WBlock d f) = true -> block_published f = true ->
    st = CPublishBlock d.
Proof.
  intros st d f Hw Hf.
  destruct st as [| x | x | x | x | channel r | channel | channel | channel
                 | channel | channel | channel n | | x | x e | x | x | x
                 | x bytes |];
    try (destruct channel as [[x | x] | x]);
    unfold cwrites in Hw; destruct f; try discriminate Hf;
    cbn -[stack_word] in Hw;
    try (rewrite orb_false_r in Hw);
    repeat match goal with
           | H : context [stack_word ?h] |- _ =>
               destruct h as [| [| ?]]; cbn in H
           end;
    try discriminate Hw;
    repeat match goal with
           | H : (_ && _) = true |- _ => apply andb_true_iff in H as [? ?]
           | H : (_ || _) = true |- _ => apply orb_true_iff in H as [? | ?]
           end;
    try (match goal with H : false = true |- _ => discriminate H end);
    try (match goal with H : Nat.eqb ?a ?b = true |- _ =>
           apply Nat.eqb_eq in H; subst; reflexivity end).
Qed.

Lemma publish_block_reads :
  forall c m d w v, In (w, v) (published_writes c d) ->
    publish_block c m d w = v.
Proof.
  intros c m d w v Hin.
  destruct (published_shape c d w v Hin) as [Hb [f [-> [_ Hf]]]].
  unfold publish_block.
  rewrite upd_other by (intros Heq; injection Heq as Heq; exact (Hf Heq)).
  rewrite !ring_init_other by (intros g _ Heq; discriminate Heq).
  apply upd_list_read; [apply block_writes_nodup | exact Hb].
Qed.

(**
 * [block_ok c m d]: block d's generation word is zero, or it is the
 * published value and every published word holds its published value.
 *)
Definition block_ok (c : config) (m : mem) (d : nat) : Prop :=
  m (WBlock d BGen) = 0 \/
  (m (WBlock d BGen) = be_mvp_generation /\
   forall w v, In (w, v) (published_writes c d) -> m w = v).

Lemma block_ok_reach :
  forall c tr s, reach c tr s -> forall d, block_ok c (cs_mem s) d.
Proof.
  intros c tr s Hr; induction Hr as [| tr s st s' Hr IH Hexec]; intros d;
    [left; reflexivity |].
  destruct (match st with CPublishBlock x => Nat.eqb x d | _ => false end)
    eqn:Hst.
  - destruct st; try discriminate Hst; apply Nat.eqb_eq in Hst; subst.
    destruct (exec_publish_block_effect c s d s' Hexec) as [Hm _].
    right; rewrite Hm; split.
    + unfold publish_block; apply upd_same.
    + intros w v Hin; apply publish_block_reads; exact Hin.
  - assert (Hsame : forall f, block_published f = true ->
                     cs_mem s' (WBlock d f) = cs_mem s (WBlock d f)).
    { intros f Hf; apply (exec_frame c s st s' Hexec).
      destruct (cwrites st (WBlock d f)) eqn:Hw; [| reflexivity].
      rewrite (cwrites_published st d f Hw Hf) in Hst.
      rewrite Nat.eqb_refl in Hst; discriminate Hst. }
    unfold block_ok; rewrite (Hsame BGen eq_refl).
    destruct (IH d) as [H0 | [Hg Hall]]; [left; exact H0 | right].
    split; [exact Hg |].
    intros w v Hin.
    destruct (published_shape c d w v Hin) as [_ [f [-> [Hf _]]]].
    rewrite (Hsame f Hf); exact (Hall _ _ Hin).
Qed.

(**
 * P1 scoped (erratum S-1): a domain hart that reads its block's generation
 * word equal to the published value in ready(d) reads each of the block's
 * immutable published words as publish(d) wrote it.
 *)
Theorem barrier_publication_block :
  forall c tr s d s', reach c tr s -> respects L1 c (tr ++ [CReady d]) ->
    exec c s (CReady d) = Some s' ->
    cs_mem s (WBlock d BGen) = be_mvp_generation ->
    forall w v, In (w, v) (published_writes c d) -> cs_mem s w = v.
Proof.
  intros c tr s d s' Hr _ _ Hgen w v Hin.
  destruct (block_ok_reach c tr s Hr d) as [H0 | [_ Hall]].
  - rewrite Hgen in H0; discriminate H0.
  - exact (Hall w v Hin).
Qed.

(* --------------------------------------------------------------------- *)
(** * P5: denial *)

(*
 * Erratum S-2, denial_iff_entry: the literal property is false on this
 * model, faithful to M1's denial path: an exit whose fault satisfies
 * Entry(e, d), taken when the domain's exit count has reached its
 * ceiling, fails the domain (exit_decide checks the ceiling first) and is
 * not denied. denial_iff_entry_below_ceiling proves the property below
 * the ceiling.
 *)

Lemma gpf_not_ssi : forall e, is_gpf (ex_scause e) = true ->
  (ex_scause e =? scause_ssi) = false.
Proof.
  intros e H; unfold is_gpf in H.
  repeat (apply orb_true_iff in H as [H | H]); apply N.eqb_eq in H;
    rewrite H; reflexivity.
Qed.

Lemma denial_spv :
  forall a w e, N.testbit (ex_hstatus e) hstatus_spv_bit = false ->
    denial_decide a w e = None.
Proof.
  intros a w e H; unfold denial_decide; rewrite H; cbn [negb].
  destruct (negb a || (map_size w =? 0)); [reflexivity |].
  rewrite orb_true_r; reflexivity.
Qed.

(**
 * P5 below the exit ceiling: on a hart whose image accepts denials, an
 * exit with a guest-page fault (scause 20, 21, or 23), taken before the
 * domain's exit count reaches its ceiling, is denied exactly when Leaf A's
 * entry holds on the hart's own walked window and leaves; a fault not
 * denied fails the domain, which does not resume.
 *)
Theorem denial_iff_entry_below_ceiling :
  forall c tr s d e s', reach c tr s -> exec c s (CExit d e) = Some s' ->
    is_gpf (ex_scause e) = true ->
    cs_mem s (WBlock d (BConfig 1)) = 1 ->
    core (cs_mem s) d CoreExits < cs_mem s (WBlock d (BConfig 0)) ->
    cs_log s' = cs_log s ++ [GExit d e (hart_exit_action (cs_mem s) d e)] /\
    (forall dn, hart_exit_action (cs_mem s) d e = XDeny dn <->
                denial_decide true (read_walked (cs_mem s) d) e = Some dn) /\
    (denial_decide true (read_walked (cs_mem s) d) e = None ->
       hart_exit_action (cs_mem s) d e = XFail /\ cs_dmode s' d = DFailing).
Proof.
  intros c tr s d e s' _ Hexec Hg Hacc Hceil.
  assert (Hact : hart_exit_action (cs_mem s) d e =
                 match denial_decide true (read_walked (cs_mem s) d) e with
                 | Some dn => XDeny dn
                 | None => XFail
                 end).
  { unfold hart_exit_action, exit_decide; rewrite Hacc.
    replace (cs_mem s (WBlock d (BConfig 0)) <=? core (cs_mem s) d CoreExits)
      with false by (symmetry; apply N.leb_gt; exact Hceil).
    destruct (N.testbit (ex_hstatus e) hstatus_spv_bit) eqn:Hspv.
    - cbn [negb]; rewrite (gpf_not_ssi e Hg), Hg; reflexivity.
    - cbn [negb]; rewrite (denial_spv true _ e Hspv); reflexivity. }
  simpl in Hexec; exec_destruct Hexec; state_simpl.
  all: split; [reflexivity |].
  all: rewrite Hact in *;
    destruct (denial_decide true (read_walked (cs_mem s) d) e) as [dz |] eqn:Hdn;
    try discriminate.
  all: split; [intros dn'; split; intros H; congruence |].
  all: intros Hn; try discriminate Hn.
  all: split; [reflexivity |]; cbn [cs_dmode]; rewrite Nat.eqb_refl; reflexivity.
Qed.

Lemma denial_vscause :
  forall a w e dn, denial_decide a w e = Some dn ->
    dn_inject_vscause dn = 1 \/ dn_inject_vscause dn = 5 \/
    dn_inject_vscause dn = 7.
Proof.
  intros a w e dn H; unfold denial_decide in H; cbv zeta in H.
  repeat match type of H with
         | context [if ?b then _ else _] => destruct b eqn:?
         | context [match ?x with _ => _ end] => destruct x eqn:?
         end; try discriminate H.
  all: injection H as <-; cbn [dn_inject_vscause].
  all: match goal with
       | Hz : context [access_fault ?s =? 0] |- _ =>
           repeat (apply orb_false_iff in Hz as [Hz _]);
           unfold access_fault in *;
           destruct (s =? scause_fetch_gpf); [left; reflexivity |];
           destruct (s =? scause_load_gpf); [right; left; reflexivity |];
           destruct (s =? scause_store_gpf); [right; right; reflexivity |];
           discriminate Hz
       end.
Qed.

(**
 * P5: a denied exit queues exactly one DENIAL record carrying the denial's
 * fields, with the injected vscause 1, 5, or 7, and its publish; the
 * domain takes no further exit, so does not resume, before both are done.
 *)
Theorem denial_record_before_resume :
  forall c tr s d e s' dn, reach c tr s -> exec c s (CExit d e) = Some s' ->
    hart_exit_action (cs_mem s) d e = XDeny dn ->
    (dn_inject_vscause dn = 1 \/ dn_inject_vscause dn = 5 \/
     dn_inject_vscause dn = 7) /\
    cs_dmode s' d = DGuest /\
    (exists seq, cs_dtodo s' d =
       [APost (outbound d) (denial_record seq dn); APublish (outbound d)]) /\
    (forall e', exec c s' (CExit d e') = None).
Proof.
  intros c tr s d e s' dn _ Hexec Hact.
  assert (Hv : dn_inject_vscause dn = 1 \/ dn_inject_vscause dn = 5 \/
               dn_inject_vscause dn = 7).
  { unfold hart_exit_action, exit_decide in Hact.
    repeat match type of Hact with
           | context [if ?b then _ else _] => destruct b eqn:?
           | context [match ?x with _ => _ end] => destruct x eqn:?
           end; try discriminate Hact.
    all: injection Hact as <-; eapply denial_vscause; eassumption. }
  simpl in Hexec; exec_destruct Hexec;
    try (match goal with H : _ = _ |- _ => discriminate H end).
  all: match goal with H : XDeny ?x = XDeny ?y |- _ => injection H as -> end.
  all: split; [exact Hv |]; state_simpl; cbn [cs_dmode cs_dtodo];
    rewrite Nat.eqb_refl.
  all: split; [reflexivity | split; [eexists; reflexivity |]].
  all: intros e'; unfold exec; cbv zeta;
    cbn [dmode_of dtodo_of cs_dmode cs_dtodo]; rewrite Nat.eqb_refl;
    reflexivity.
Qed.

(* --------------------------------------------------------------------- *)
(** * P6: management *)

Definition no_mgmt_event (ev : gev) : Prop :=
  match ev with GDecide _ _ _ _ _ _ | GSettle _ _ _ _ => False | _ => True end.

(** Only hart 0's handling of a drained record logs a decision or an answer. *)
Lemma exec_no_mgmt :
  forall c s st s', exec c s st = Some s' ->
    (forall d, st <> CDecideMgmt d) -> (forall d, st <> CStepRecord d) ->
    exists evs, cs_log s' = cs_log s ++ evs /\ Forall no_mgmt_event evs.
Proof.
  intros c s st s' Hexec H1 H2.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (exfalso; eapply H1; reflexivity); try (exfalso; eapply H2; reflexivity);
    simpl in Hexec; try (destruct channel as [[d | d] | d]);
    exec_destruct Hexec; log_simpl;
    try (eexists; split; [reflexivity |]; repeat (constructor || exact I); fail);
    try (exists []; rewrite app_nil_r; split; [reflexivity | constructor]; fail).
Qed.

Ltac handle_split H :=
  repeat (match type of H with
          | context [if ?b then _ else _] => destruct b eqn:?
          end; cbv beta iota zeta in H);
  try discriminate H.

Lemma handle_step_no_decide :
  forall m d r m' todo o evs req fid t seq st out,
    handle_step m d r = (m', todo, o, evs) ->
    ~ In (GDecide req fid t seq st out) evs.
Proof.
  intros m d r m' todo o evs req fid t seq st out H Hin.
  unfold handle_step, invalid, settle in H; cbv beta iota zeta in H.
  handle_split H; injection H as _ _ _ <-;
    repeat (destruct Hin as [Hin | Hin]; [discriminate Hin |]); exact Hin.
Qed.

Lemma sbi_codes :
  sbi_not_supported <> mgmt_deliver /\ sbi_invalid_param <> mgmt_deliver /\
  sbi_denied <> mgmt_deliver /\ sbi_invalid_state <> mgmt_deliver.
Proof. vm_compute; repeat split; intros H; discriminate H. Qed.

Lemma mgmt_deliver_state :
  forall g r f t st, mgmt_decide g r f t st = mgmt_deliver ->
    t < 2 /\ (st = TRunning \/ (st = TPaused /\ f = fid_terminate)).
Proof.
  intros g r f t st H; unfold mgmt_decide in H.
  destruct sbi_codes as [C1 [C2 [C3 C4]]].
  destruct (negb ((f =? fid_pause) || (f =? fid_terminate))); [contradiction |].
  destruct (2 <=? t) eqn:Ht; [contradiction |].
  destruct (negb (granted g r f t)); [contradiction |].
  apply N.leb_gt in Ht; split; [exact Ht |].
  destruct st; try contradiction; [left; reflexivity |].
  destruct (f =? fid_terminate) eqn:Hf; [| contradiction].
  apply N.eqb_eq in Hf; right; split; [reflexivity | exact Hf].
Qed.

Lemma mgmt_decide_cases :
  forall g r f t st, (f = fid_pause \/ f = fid_terminate) ->
    (2 <= t -> mgmt_decide g r f t st = sbi_invalid_param) /\
    (t < 2 -> granted g r f t = false -> mgmt_decide g r f t st = sbi_denied) /\
    (t < 2 -> granted g r f t = true ->
       ((st = TRunning \/ (st = TPaused /\ f = fid_terminate)) ->
          mgmt_decide g r f t st = mgmt_deliver) /\
       (~ (st = TRunning \/ (st = TPaused /\ f = fid_terminate)) ->
          mgmt_decide g r f t st = sbi_invalid_state)).
Proof.
  intros g r f t st Hf.
  assert (Hok : negb ((f =? fid_pause) || (f =? fid_terminate)) = false)
    by (destruct Hf as [-> | ->]; reflexivity).
  unfold mgmt_decide; rewrite Hok.
  split; [intros Ht; apply N.leb_le in Ht; rewrite Ht; reflexivity |].
  split; [intros Ht Hg; apply N.leb_gt in Ht; rewrite Ht, Hg; reflexivity |].
  intros Ht Hg; apply N.leb_gt in Ht; rewrite Ht, Hg; cbn [negb].
  split.
  - intros [-> | [-> ->]]; reflexivity.
  - intros Hn; destruct st; try reflexivity.
    + exfalso; apply Hn; left; reflexivity.
    + destruct (f =? fid_terminate) eqn:E; [| reflexivity].
      exfalso; apply Hn; right; split; [reflexivity | apply N.eqb_eq; exact E].
Qed.

Lemma target_of_free :
  forall m t, target_of m t = TRunning \/ target_of m t = TPaused ->
    ctl m (KPending t) = 0 /\ ctl m (KAwaiting t) = 0.
Proof.
  intros m t H; unfold target_of in H.
  destruct (ctl m (KTrack t) =? track_shutdown);
    [destruct H as [H | H]; discriminate H |].
  destruct (ctl m (KTrack t) =? track_terminated);
    [destruct H as [H | H]; discriminate H |].
  destruct (negb (ctl m (KPending t) =? 0) || negb (ctl m (KAwaiting t) =? 0))
    eqn:Hp; [destruct H as [H | H]; discriminate H |].
  apply orb_false_iff in Hp as [H1 H2]; apply negb_false_iff, N.eqb_eq in H1, H2.
  split; assumption.
Qed.

(** Hart 0's handling of a MGMT_REQUEST: the one decision and its queue. *)
Lemma handle_mgmt_decide :
  forall c m d r m' todo o evs req fid t seq st out,
    handle_mgmt c m d r = (m', todo, o, evs) ->
    In (GDecide req fid t seq st out) evs ->
    req = d /\ o = HContinue /\ (fid = fid_pause \/ fid = fid_terminate) /\
    out = mgmt_decide (cfg_grants c) (N.of_nat d) fid t st /\
    ctl m (KAwaiting d) = 0 /\
    (t < 2 -> st = target_of (set_ctl (set_ctl m (KRequests d) seq)
                                (KAwaiting d) 1) (N.to_nat t)) /\
    (out = mgmt_deliver ->
       todo = [APost (inbound (N.to_nat t)) (order_record fid (N.of_nat d));
               APublish (inbound (N.to_nat t))] /\
       ctl m' (KPending (N.to_nat t)) = 1) /\
    (out <> mgmt_deliver ->
       todo = [APost (inbound d) (result_record out seq); APublish (inbound d)]).
Proof.
  intros c m d r m' todo o evs req fid t seq st out H Hin.
  unfold handle_mgmt, invalid, settle in H; cbv beta iota zeta in H.
  handle_split H; injection H as Hm Htd Ho He; subst m' todo o evs;
    simpl in Hin; try contradiction Hin;
    destruct Hin as [Hin | []]; try discriminate Hin.
  all: injection Hin as <- <- <- <- <- <-.
  all: repeat match goal with
              | H : (_ && _) = true |- _ => apply andb_true_iff in H as [? ?]
              | H : (_ || _) = false |- _ => apply orb_false_iff in H as [? ?]
              end.
  all: split; [reflexivity | split; [reflexivity |]].
  all: split; [match goal with
               | H : ((?f =? fid_pause) || (?f =? fid_terminate)) = true |- _ =>
                   apply orb_true_iff in H as [H | H]; apply N.eqb_eq in H;
                   [left | right]; exact H
               end |].
  all: split; [reflexivity |].
  all: split; [match goal with
               | H : (ctl _ (KAwaiting _) =? 0) = true |- _ =>
                   apply N.eqb_eq in H; exact H
               end |].
  all: split; [intros Ht; first [reflexivity |
                 match goal with
                 | H : (_ <? 2) = false |- _ => apply N.ltb_ge in H; lia
                 end] |].
  all: split; [intros Hd | intros Hd].
  all: first
    [ split; [reflexivity |]; unfold ctl, set_ctl; cbn [upd_list];
      repeat (rewrite upd_same || rewrite upd_other by (intros Heq; discriminate Heq));
      reflexivity
    | reflexivity
    | exfalso; match goal with
               | H : (_ =? mgmt_deliver) = false |- _ =>
                   apply N.eqb_neq in H; exact (H Hd)
               | H : (_ =? mgmt_deliver) = true |- _ =>
                   apply N.eqb_eq in H; exact (Hd H)
               end ].
Qed.

(** The decision a CDecideMgmt step logs, and its queue. *)
Lemma exec_decide_event :
  forall c s d s' req fid t seq st out,
    exec c s (CDecideMgmt d) = Some s' ->
    In (GDecide req fid t seq st out) (cs_log s') ->
    ~ In (GDecide req fid t seq st out) (cs_log s) ->
    exists r m' todo evs,
      handle_mgmt c (cs_mem s) d r = (m', todo, HContinue, evs) /\
      In (GDecide req fid t seq st out) evs /\
      cs_mem s' = drain_visited m' true /\ cs_h0todo s' = todo.
Proof.
  intros c s d s' req fid t seq st out Hexec Hin Hnin.
  simpl in Hexec; exec_destruct Hexec.
  match goal with
  | H : handle_mgmt _ _ _ ?r = (?m', ?todo, ?o, ?evs) |- _ =>
      assert (Hev : In (GDecide req fid t seq st out) evs)
        by (rewrite cs_log_h0_after in Hin; apply in_app_or in Hin as [Hin | Hin];
            [contradiction | exact Hin]);
      destruct (handle_mgmt_decide _ _ _ _ _ _ _ _ _ _ _ _ _ _ H Hev)
        as [_ [Ho _]]; subst o;
      exists r, m', todo, evs; split; [exact H | split; [exact Hev |]];
      split; reflexivity
  end.
Qed.

(**
 * P6: a management request is decided by hart 0 alone: the one step that
 * logs a decision is hart 0's decide_mgmt of the requester's record.
 *)
Theorem mgmt_decided_by_control_hart :
  forall c tr s st s', reach c tr s -> exec c s st = Some s' ->
    forall req fid t seq state out,
      In (GDecide req fid t seq state out) (cs_log s') ->
      ~ In (GDecide req fid t seq state out) (cs_log s) ->
      st = CDecideMgmt req /\ chart st = bi_control mvp_binding.
Proof.
  intros c tr s st s' _ Hexec req fid t seq state out Hin Hnin.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (destruct (exec_no_mgmt c s _ s' Hexec
                     (fun x H => ltac:(discriminate H))
                     (fun x H => ltac:(discriminate H))) as [evs [Hl Hq]];
         rewrite Hl in Hin; apply in_app_or in Hin as [Hin | Hin];
         [contradiction | rewrite Forall_forall in Hq; exact (False_ind _ (Hq _ Hin))]).
  - simpl in Hexec; exec_destruct Hexec.
    match goal with
    | H : handle_step _ _ _ = (_, _, _, ?evs) |- _ =>
        rewrite cs_log_h0_after in Hin; apply in_app_or in Hin as [Hin | Hin];
        [contradiction | exact (False_ind _ (handle_step_no_decide _ _ _ _ _ _ _ _ _ _ _ _ _ H Hin))]
    end.
  - destruct (exec_decide_event c s d s' req fid t seq state out Hexec Hin Hnin)
      as [r [m' [todo [evs [H [Hev _]]]]]].
    destruct (handle_mgmt_decide _ _ _ _ _ _ _ _ _ _ _ _ _ _ H Hev) as [-> _].
    split; reflexivity.
Qed.

(**
 * P6: hart 0's decision of a request from domain d is INVALID_PARAM for
 * an unknown target, DENIED when no sealed grant from d names that
 * function on the target (the requester itself included), INVALID_STATE
 * for a target terminated, shut down, paused for a pause, or with a
 * request pending, and delivered otherwise; a delivery queues PAUSE or
 * TERMINATE on the target's inbound ring, any other answer the result on
 * the requester's. The grants consulted are the configuration's sealed
 * grants (cfg_grants).
 *)
Theorem mgmt_outcome_from_grants :
  forall c tr s d s', reach c tr s -> exec c s (CDecideMgmt d) = Some s' ->
    forall req fid t seq st out,
      In (GDecide req fid t seq st out) (cs_log s') ->
      ~ In (GDecide req fid t seq st out) (cs_log s) ->
      out = mgmt_decide (cfg_grants c) (N.of_nat d) fid t st /\
      (2 <= t -> out = sbi_invalid_param) /\
      (t < 2 -> granted (cfg_grants c) (N.of_nat d) fid t = false ->
         out = sbi_denied) /\
      (t < 2 -> granted (cfg_grants c) (N.of_nat d) fid t = true ->
         ((st = TRunning \/ (st = TPaused /\ fid = fid_terminate)) ->
            out = mgmt_deliver) /\
         (~ (st = TRunning \/ (st = TPaused /\ fid = fid_terminate)) ->
            out = sbi_invalid_state)) /\
      (out = mgmt_deliver ->
         cs_h0todo s' =
           [APost (inbound (N.to_nat t)) (order_record fid (N.of_nat d));
            APublish (inbound (N.to_nat t))]) /\
      (out <> mgmt_deliver ->
         cs_h0todo s' =
           [APost (inbound d) (result_record out seq); APublish (inbound d)]).
Proof.
  intros c tr s d s' _ Hexec req fid t seq st out Hin Hnin.
  destruct (exec_decide_event c s d s' req fid t seq st out Hexec Hin Hnin)
    as [r [m' [todo [evs [H [Hev [_ Htodo]]]]]]].
  destruct (handle_mgmt_decide _ _ _ _ _ _ _ _ _ _ _ _ _ _ H Hev)
    as [_ [_ [Hf [Hout [_ [_ [Hdel Hans]]]]]]].
  destruct (mgmt_decide_cases (cfg_grants c) (N.of_nat d) fid t st Hf)
    as [C1 [C2 C3]].
  rewrite Htodo; split; [exact Hout |].
  split; [intros Ht; rewrite Hout; exact (C1 Ht) |].
  split; [intros Ht Hg; rewrite Hout; exact (C2 Ht Hg) |].
  split; [intros Ht Hg; rewrite Hout; exact (C3 Ht Hg) |].
  split; [intros Hd; exact (proj1 (Hdel Hd)) | exact Hans].
Qed.

(**
 * P6: at most one request is pending per domain: hart 0 decides a
 * domain's request only when that requester has none outstanding, and
 * delivers to a target only when no request is pending on it, after which
 * one is.
 *)
Theorem mgmt_one_pending_per_domain :
  forall c tr s d s', reach c tr s -> exec c s (CDecideMgmt d) = Some s' ->
    forall req fid t seq st out,
      In (GDecide req fid t seq st out) (cs_log s') ->
      ~ In (GDecide req fid t seq st out) (cs_log s) ->
      ctl (cs_mem s) (KAwaiting d) = 0 /\
      (out = mgmt_deliver ->
         ctl (cs_mem s) (KPending (N.to_nat t)) = 0 /\
         ctl (cs_mem s') (KPending (N.to_nat t)) = 1).
Proof.
  intros c tr s d s' _ Hexec req fid t seq st out Hin Hnin.
  destruct (exec_decide_event c s d s' req fid t seq st out Hexec Hin Hnin)
    as [r [m' [todo [evs [H [Hev [Hmem _]]]]]]].
  destruct (handle_mgmt_decide _ _ _ _ _ _ _ _ _ _ _ _ _ _ H Hev)
    as [_ [_ [_ [Hout [Haw [Hst [Hdel _]]]]]]].
  split; [exact Haw |].
  intros Hd.
  rewrite Hout in Hd.
  destruct (mgmt_deliver_state _ _ _ _ _ Hd) as [Ht Hs].
  rewrite <- Hout in Hd.
  destruct (Hdel Hd) as [_ Hp].
  split.
  - rewrite (Hst Ht) in Hs.
    assert (Hfree : target_of (set_ctl (set_ctl (cs_mem s) (KRequests d) seq)
                      (KAwaiting d) 1) (N.to_nat t) = TRunning \/
                    target_of (set_ctl (set_ctl (cs_mem s) (KRequests d) seq)
                      (KAwaiting d) 1) (N.to_nat t) = TPaused)
      by (destruct Hs as [Hs | [Hs _]]; [left | right]; exact Hs).
    destruct (target_of_free _ _ Hfree) as [Hpend _].
    unfold ctl, set_ctl in Hpend |- *.
    rewrite !upd_other in Hpend by (intros Heq; discriminate Heq).
    exact Hpend.
  - rewrite Hmem; unfold drain_visited, ctl in *.
    destruct (drain_next m'); [| exact Hp].
    cbn [upd_list]; rewrite !upd_other by (intros Heq; discriminate Heq).
    exact Hp.
Qed.

(* --------------------------------------------------------------------- *)
(** * P7: measure before entry *)

(** [gates_seen]: both launch gates were logged as passed. *)
Definition gates_seen (log : list gev) : Prop :=
  In (GGate 0 true) log /\ In (GGate 1 true) log.

(** The global rule holds only where both launch gates passed. *)
Lemma global_rule_gates :
  forall c m, global_rule c m = true ->
    gate_verdict c m 0 = true /\ gate_verdict c m 1 = true.
Proof.
  intros c m H; unfold global_rule in H.
  apply andb_true_iff in H as [H _]; apply andb_true_iff in H; exact H.
Qed.

(** Once hart 0 publishes, both gates passed at its preparation. *)
Lemma gates_reach :
  forall c tr s, reach c tr s ->
    (published1 (cs_log s) = true \/ exists d, cs_h0 s = H0Publish d) ->
    gates_seen (cs_log s).
Proof.
  intros c tr s Hr; induction Hr as [| tr s st s' Hr IH Hexec]; intros Hp.
  - destruct Hp as [Hp | [d Hp]]; discriminate Hp.
  - destruct (exec_events c s st s' Hexec) as [evs [Hl _]].
    destruct (published1 (cs_log s)) eqn:Hpub.
    + destruct (IH (or_introl eq_refl)) as [G0 G1]; rewrite Hl.
      split; apply in_or_app; left; assumption.
    + destruct (boot_steps c tr s st s' Hr Hpub Hexec) as [-> | [d ->]].
      * simpl in Hexec; exec_destruct Hexec; state_simpl.
        -- destruct (global_rule_gates _ _ Heqb) as [G0 G1]; unfold gates_seen;
             cbn [cs_log]; rewrite G0, G1.
           split; apply in_or_app; right; simpl; tauto.
        -- exfalso; destruct Hp as [Hp | [d Hp]]; [| discriminate Hp].
           cbn [cs_log] in Hp; rewrite published1_app, Hpub in Hp;
             discriminate Hp.
      * destruct (exec_publish_block_effect c s d s' Hexec) as [_ [Hl' [Hh _]]].
        destruct (IH (or_intror (ex_intro _ d Hh))) as [G0 G1]; rewrite Hl'.
        split; apply in_or_app; left; assumption.
Qed.

(**
 * P7: enter(d) occurs only after the launch gate held for d: hart 0's
 * preparation logged d's gate verdict, its predicate on d's placed bytes
 * and the image's expected launch register for d (M9: every domain's
 * gate, under the global rule), as passed.
 *)
Theorem entry_after_gate :
  forall c tr s d s', reach c tr s -> exec c s (CEnter d) = Some s' ->
    (d < 2)%nat /\ In (GGate d true) (cs_log s).
Proof.
  intros c tr s d s' Hr Hexec.
  assert (Hd : (d < 2)%nat /\ cs_dmode s d = DEntering).
  { simpl in Hexec; exec_destruct Hexec.
    split; [apply Nat.ltb_lt; assumption | assumption]. }
  destruct Hd as [Hlt Hm]; split; [exact Hlt |].
  destruct (published1 (cs_log s)) eqn:Hpub.
  - destruct (gates_reach c tr s Hr (or_introl Hpub)) as [G0 G1].
    destruct d as [| [| d]]; [exact G0 | exact G1 | lia].
  - destruct (boot_ok_reach c tr s Hr) as [_ Hb].
    destruct (Hb Hpub) as [Hoff _]; destruct (Hoff d) as [Hoff' _].
    rewrite Hoff' in Hm; discriminate Hm.
Qed.

(**
 * M9's global rule (planning/mvp-m9-plan.md, D-1), its failure at either
 * half, a launch gate or the log's close: hart 0's preparation fails the
 * run, so hart 0 is failed, no domain hart is started, and the trace takes
 * no further step.
 *)
Lemma global_rule_false_no_start :
  forall c tr s s', reach c tr s -> exec c s CPrepare = Some s' ->
    global_rule c (prepare_mem c (cs_mem s)) = false ->
    cs_h0 s' = H0Failed /\ (forall d', cs_dmode s' d' = DOff) /\
    (forall tr2 s2, reach c ((tr ++ [CPrepare]) ++ tr2) s2 -> tr2 = []).
Proof.
  intros c tr s s' Hr Hexec Hg.
  pose proof (reach_step c tr s CPrepare s' Hr Hexec) as Hr'.
  destruct (boot_ok_reach c tr s Hr) as [Hb1 Hb2].
  simpl in Hexec; exec_destruct Hexec; [congruence |].
  match goal with H : cs_h0 s = H0Boot |- _ => rename H into Hboot end.
  assert (Hpub : published1 (cs_log s) = false)
    by (apply Hb1; first [reflexivity | rewrite Hboot; reflexivity]).
  destruct (Hb2 Hpub) as [Hoff _].
  state_simpl; split; [reflexivity | split].
  - intros d'; exact (proj1 (Hoff d')).
  - intros tr2 s2 H2; destruct tr2 as [| x rest]; [reflexivity | exfalso].
    change ((tr ++ [CPrepare]) ++ x :: rest)
      with ((tr ++ [CPrepare]) ++ [x] ++ rest) in H2.
    rewrite app_assoc in H2.
    destruct (reach_app c _ _ _ H2) as [s1 H1].
    destruct (reach_snoc_inv c _ _ _ H1) as [s0 [H0 Hx]].
    rewrite (reach_det c _ _ _ H0 Hr') in Hx.
    assert (Hpub' : published1 (cs_log s ++
                      [GGate 0 (gate_verdict c (prepare_mem c (cs_mem s)) 0);
                       GGate 1 (gate_verdict c (prepare_mem c (cs_mem s)) 1)]) = false)
      by (rewrite published1_app, Hpub; reflexivity).
    destruct (boot_steps c _ _ x s1 Hr' Hpub' Hx) as [-> | [d' ->]];
      simpl in Hx; discriminate Hx.
Qed.

(**
 * P7: when the launch gate fails for one of the two domains, hart 0's
 * preparation fails the run (M9's global rule: every gate passes and the
 * log closes, or no domain hart starts): hart 0 is failed, no domain hart
 * is started, and the trace takes no further step, so no start(d') and no
 * enter(d') follow.
 *)
Theorem gate_false_no_start :
  forall c tr s s' d, reach c tr s -> exec c s CPrepare = Some s' ->
    (d < 2)%nat -> gate_verdict c (prepare_mem c (cs_mem s)) d = false ->
    cs_h0 s' = H0Failed /\ (forall d', cs_dmode s' d' = DOff) /\
    (forall tr2 s2, reach c ((tr ++ [CPrepare]) ++ tr2) s2 -> tr2 = []).
Proof.
  intros c tr s s' d Hr Hexec Hd Hg.
  apply (global_rule_false_no_start c tr s s' Hr Hexec).
  unfold global_rule; destruct d as [| [| d]];
    [rewrite Hg | rewrite Hg, andb_false_r | lia]; reflexivity.
Qed.

(* --------------------------------------------------------------------- *)
(** * P6: a parked domain never resumes *)

(** The events hart 0's handling of a record logs: decisions and answers. *)
Definition handle_event (ev : gev) : Prop :=
  match ev with GSettle _ _ _ _ | GDecide _ _ _ _ _ _ => True | _ => False end.

Lemma handle_events :
  forall c m d r m' todo o evs,
    (handle_step m d r = (m', todo, o, evs) \/
     handle_mgmt c m d r = (m', todo, o, evs)) ->
    Forall handle_event evs.
Proof.
  intros c m d r m' todo o evs [H | H];
    [unfold handle_step, invalid, settle in H | unfold handle_mgmt, invalid, settle in H];
    cbv beta iota zeta in H; handle_split H; injection H as _ _ _ <-;
    repeat (constructor || exact I).
Qed.

(** [park_seen d log]: the log records d's park. *)
Definition park_seen (d : nat) (log : list gev) : bool :=
  existsb (fun ev => match ev with GPark x => Nat.eqb x d | _ => false end) log.

Lemma park_seen_iff :
  forall d log, park_seen d log = true <-> In (GPark d) log.
Proof.
  intros d log; unfold park_seen; rewrite existsb_exists; split.
  - intros [ev [Hin He]]; destruct ev; try discriminate He.
    apply Nat.eqb_eq in He; subst; exact Hin.
  - intros Hin; exists (GPark d); split; [exact Hin | apply Nat.eqb_refl].
Qed.

(** Only a domain's park logs its GPark. *)
Lemma exec_park_origin :
  forall c s st s' d, exec c s st = Some s' ->
    In (GPark d) (cs_log s') -> ~ In (GPark d) (cs_log s) -> st = CPark d.
Proof.
  intros c s st s' d Hexec Hin Hnin.
  destruct st as [| x | x | x | x | channel r | channel | channel | channel
                 | channel | channel | channel n | | x | x e | x | x | x
                 | x bytes |];
    simpl in Hexec; try (destruct channel as [[x | x] | x]);
    exec_destruct Hexec; log_simpl;
    try (apply in_app_or in Hin as [Hin | Hin]; [contradiction |]);
    try (simpl in Hin; repeat (destruct Hin as [Hin | Hin]; [discriminate Hin |]);
         contradiction Hin).
  all: try (rewrite cs_log_h0_after in Hin; apply in_app_or in Hin as [Hin | Hin];
            [contradiction |];
            match goal with
            | H : handle_step _ _ _ = _ |- _ =>
                pose proof (handle_events c _ _ _ _ _ _ _ (or_introl H)) as Hf
            | H : handle_mgmt _ _ _ _ = _ |- _ =>
                pose proof (handle_events c _ _ _ _ _ _ _ (or_intror H)) as Hf
            end;
            rewrite Forall_forall in Hf; exact (False_ind _ (Hf _ Hin))).
  all: simpl in Hin; destruct Hin as [Hin | []]; injection Hin as ->; reflexivity.
Qed.

(** [after_park]: the modes a parked domain's hart can be in. *)
Definition after_park (mode : dmode) : bool :=
  match mode with
  | DParked | DServe FromPark _ | DServe FromFail _ | DFailing | DFailWait
  | DHalted => true
  | _ => false
  end.

Lemma parked_reach :
  forall c tr s, reach c tr s ->
    forall d, park_seen d (cs_log s) = true -> after_park (cs_dmode s d) = true.
Proof.
  intros c tr s Hr; induction Hr as [| tr s st s' Hr IH Hexec];
    intros d Hp; [discriminate Hp |].
  destruct (park_seen d (cs_log s)) eqn:Hold.
  - specialize (IH d Hold).
    exec_split st Hexec; state_simpl.
    all: try match goal with
             | H : handle_step _ _ _ = (_, _, ?o, _) |- _ => destruct o
             end;
      try match goal with
          | H : handle_mgmt _ _ _ _ = (_, _, ?o, _) |- _ => destruct o
          end;
      cbn [cs_dmode]; cbv beta; try exact IH.
    all: try (destruct (Nat.eqb d _) eqn:E;
              [apply Nat.eqb_eq in E; subst |]).
    all: first
      [ reflexivity
      | exact IH
      | match goal with
        | H : cs_dmode _ ?y = DServe ?k _ |- _ =>
            rewrite H in IH; destruct k; try discriminate IH; reflexivity
        end
      | match goal with
        | H : cs_dmode _ ?y = _ |- _ => rewrite H in IH; discriminate IH
        end ].
  - apply park_seen_iff in Hp.
    assert (Hn : ~ In (GPark d) (cs_log s))
      by (intros Hx; apply park_seen_iff in Hx; congruence).
    rewrite (exec_park_origin c s st s' d Hexec Hp Hn) in Hexec.
    simpl in Hexec; exec_destruct Hexec; state_simpl; cbn [cs_dmode];
      rewrite Nat.eqb_refl; reflexivity.
Qed.

(**
 * P6: a domain's hart that has parked never resumes its guest: it takes
 * no exit and no entry again; it only serves its inbound ring, where a
 * paused target still takes TERMINATE and answers TERMINATED (the M2
 * plan's design), or fails.
 *)
Theorem parked_never_resumes :
  forall c tr s d, reach c tr s -> In (GPark d) (cs_log s) ->
    after_park (cs_dmode s d) = true /\
    (forall e, exec c s (CExit d e) = None) /\
    exec c s (CEnter d) = None.
Proof.
  intros c tr s d Hr Hin.
  pose proof (parked_reach c tr s Hr d (proj2 (park_seen_iff d _) Hin)) as Hap.
  split; [exact Hap |].
  split; [intros e |]; simpl; unfold dmode_of;
    destruct (cs_dmode s d); try discriminate Hap; reflexivity.
Qed.

(* --------------------------------------------------------------------- *)
(** * P6: each request decided once *)

Lemma ring_ops_wctl :
  forall cap ch m k,
    (forall r, snd (ring_post cap ch m r) (WCtl k) = m (WCtl k)) /\
    snd (ring_publish ch m) (WCtl k) = m (WCtl k) /\
    snd (ring_acquire cap ch m) (WCtl k) = m (WCtl k) /\
    snd (ring_take cap ch m) (WCtl k) = m (WCtl k) /\
    snd (ring_release ch m) (WCtl k) = m (WCtl k) /\
    snd (ring_room cap ch m) (WCtl k) = m (WCtl k).
Proof. intros cap ch m k; repeat split; try intros r; ring_op_words. Qed.

Lemma publish_block_wctl :
  forall c m d k, publish_block c m d (WCtl k) = m (WCtl k).
Proof.
  intros c m d k; unfold publish_block.
  rewrite upd_other by (intros Heq; discriminate Heq).
  rewrite !ring_init_other by (intros g _ Heq; discriminate Heq).
  apply upd_list_other; cbn [block_writes map fst app seq core_fields].
  simpl; intros H; repeat (destruct H as [H | H]; [discriminate H |]); exact H.
Qed.

Ltac kreq_close :=
  unfold ctl, set_ctl, set_core, refuse_writer, refuse_reader, drain_begin,
    prepare_mem in *;
  cbn [upd_list] in *;
  repeat (first
    [ reflexivity
    | rewrite publish_block_wctl
    | rewrite upd_other by (intros Heq; discriminate Heq)
    | rewrite upd_other by (intros Heq; injection Heq as Heq;
                            first [discriminate Heq | subst; contradiction])
    | match goal with
      | |- drain_visited ?m ?b _ = _ =>
          unfold drain_visited; destruct (drain_next m); cbn [upd_list]
      | H : ring_post ?cap ?ch ?m0 ?r = (_, ?m) |- ?m ?w = _ =>
          replace m with (snd (ring_post cap ch m0 r)) by (rewrite H; reflexivity);
          rewrite (proj1 (ring_ops_wctl cap ch m0 _) r)
      | H : ring_publish ?ch ?m0 = (_, ?m) |- ?m ?w = _ =>
          replace m with (snd (ring_publish ch m0)) by (rewrite H; reflexivity);
          rewrite (proj1 (proj2 (ring_ops_wctl 0 ch m0 _)))
      | H : ring_acquire ?cap ?ch ?m0 = (_, ?m) |- ?m ?w = _ =>
          replace m with (snd (ring_acquire cap ch m0)) by (rewrite H; reflexivity);
          rewrite (proj1 (proj2 (proj2 (ring_ops_wctl cap ch m0 _))))
      | H : ring_take ?cap ?ch ?m0 = (_, ?m) |- ?m ?w = _ =>
          replace m with (snd (ring_take cap ch m0)) by (rewrite H; reflexivity);
          rewrite (proj1 (proj2 (proj2 (proj2 (ring_ops_wctl cap ch m0 _)))))
      | H : ring_release ?ch ?m0 = (_, ?m) |- ?m ?w = _ =>
          replace m with (snd (ring_release ch m0)) by (rewrite H; reflexivity);
          rewrite (proj1 (proj2 (proj2 (proj2 (proj2 (ring_ops_wctl 0 ch m0 _))))))
      | H : ring_room ?cap ?ch ?m0 = (_, ?m) |- ?m ?w = _ =>
          replace m with (snd (ring_room cap ch m0)) by (rewrite H; reflexivity);
          rewrite (proj2 (proj2 (proj2 (proj2 (proj2 (ring_ops_wctl cap ch m0 _))))))
      end ]).

Lemma handle_step_kreq :
  forall m d r m' todo o evs, handle_step m d r = (m', todo, o, evs) ->
    forall x, m' (WCtl (KRequests x)) = m (WCtl (KRequests x)).
Proof.
  intros m d r m' todo o evs H x.
  unfold handle_step, invalid, settle in H; cbv beta iota zeta in H.
  handle_split H; injection H as <- _ _ _; kreq_close.
Qed.

(** A step other than a management decision leaves every request counter. *)
Lemma exec_kreq_frame :
  forall c s st s', exec c s st = Some s' -> (forall d, st <> CDecideMgmt d) ->
    forall x, ctl (cs_mem s') (KRequests x) = ctl (cs_mem s) (KRequests x).
Proof.
  intros c s st s' Hexec Hst x.
  destruct (h0_step st) eqn:Hh.
  2: { destruct (domain_step_frame c s st s' Hh Hexec) as [_ [_ Hk]].
       unfold ctl; apply Hk. }
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (exfalso; eapply Hst; reflexivity);
    try (destruct channel as [[d0 | d0] | d0]); simpl in Hh; try discriminate Hh;
    simpl in Hexec; exec_destruct Hexec; state_simpl.
  all: try match goal with
           | H : handle_step _ _ _ = (_, _, ?o, _) |- _ => destruct o
           end;
    cbn [cs_mem]; kreq_close.
  all: match goal with
       | H : handle_step _ _ _ = (?m', _, _, _) |- ?m' ?w = _ =>
           exact (handle_step_kreq _ _ _ _ _ _ _ H x)
       end.
Qed.

Definition no_decide_event (ev : gev) : Prop :=
  match ev with GDecide _ _ _ _ _ _ => False | _ => True end.

Lemma handle_mgmt_kreq :
  forall c m d r m' todo o evs,
    handle_mgmt c m d r = (m', todo, o, evs) ->
    (Forall no_decide_event evs /\
     forall x, m' (WCtl (KRequests x)) = m (WCtl (KRequests x))) \/
    (exists fid t seq st out,
       evs = [GDecide d fid t seq st out] /\
       seq = ctl m (KRequests d) + 1 /\ m' (WCtl (KRequests d)) = seq /\
       forall x, x <> d -> m' (WCtl (KRequests x)) = m (WCtl (KRequests x))).
Proof.
  intros c m d r m' todo o evs H.
  unfold handle_mgmt, invalid, settle in H; cbv beta iota zeta in H.
  handle_split H; injection H as <- _ _ <-.
  all: try (left; split; [repeat (constructor || exact I) | intros x; kreq_close]; fail).
  all: right; do 5 eexists; split; [reflexivity |].
  all: repeat match goal with
              | H : (_ && _) = true |- _ => apply andb_true_iff in H as [? ?]
              end.
  all: split; [match goal with
               | H : (_ =? ctl _ (KRequests _) + 1) = true |- _ =>
                   apply N.eqb_eq in H; exact H
               end |].
  all: split; [kreq_close; apply upd_same |].
  all: intros x Hx; kreq_close.
Qed.

(** [decisions d seq log]: how many decisions of domain d's request seq. *)
Definition decisions (d : nat) (seq : N) (log : list gev) : nat :=
  length (filter (fun ev => match ev with
                            | GDecide d' _ _ q _ _ => Nat.eqb d' d && (q =? seq)
                            | _ => false
                            end) log).

Lemma decisions_app :
  forall d seq l1 l2,
    decisions d seq (l1 ++ l2) = (decisions d seq l1 + decisions d seq l2)%nat.
Proof. intros; unfold decisions; rewrite filter_app, length_app; reflexivity. Qed.

Lemma decisions_quiet :
  forall d seq evs, Forall no_decide_event evs -> decisions d seq evs = 0%nat.
Proof.
  intros d seq evs H; induction H as [| ev evs Hev _ IH]; [reflexivity |].
  unfold decisions in *; destruct ev; simpl; try exact IH; contradiction Hev.
Qed.
Lemma decisions_pos :
  forall d seq log fid t st out, In (GDecide d fid t seq st out) log ->
    (1 <= decisions d seq log)%nat.
Proof.
  intros d seq log fid t st out; induction log as [| ev log IH]; intros Hin;
    [destruct Hin |].
  unfold decisions in *; simpl in Hin |- *.
  destruct Hin as [-> | Hin].
  - rewrite Nat.eqb_refl, N.eqb_refl; simpl; lia.
  - specialize (IH Hin); destruct ev; try exact IH.
    match goal with |- context [if ?b then _ else _] => destruct b end;
      simpl; lia.
Qed.

Lemma decisions_single :
  forall d seq x fid t q st out,
    decisions d seq [GDecide x fid t q st out] =
    if Nat.eqb x d && (q =? seq) then 1%nat else 0%nat.
Proof.
  intros; unfold decisions; simpl.
  destruct (Nat.eqb x d && (q =? seq)); reflexivity.
Qed.

Lemma handle_step_nodec :
  forall m d r m' todo o evs, handle_step m d r = (m', todo, o, evs) ->
    Forall no_decide_event evs.
Proof.
  intros m d r m' todo o evs H.
  unfold handle_step, invalid, settle in H; cbv beta iota zeta in H.
  handle_split H; injection H as _ _ _ <-; repeat (constructor || exact I).
Qed.

Lemma h0_after_kreq :
  forall s m todo o evs x,
    ctl (cs_mem (h0_after s m todo o evs)) (KRequests x) = ctl m (KRequests x).
Proof.
  intros s m todo o evs x; rewrite cs_mem_h0_after; destruct o; try reflexivity.
  kreq_close.
Qed.

(**
 * [decisions_reach]: no request is decided twice, and a request numbered
 * past its requester's counter is not decided yet (hart 0 decides domain
 * d's request seq only when seq is the counter plus one, and raises it).
 *)
Lemma decisions_reach :
  forall c tr s, reach c tr s -> forall d seq,
    (decisions d seq (cs_log s) <= 1)%nat /\
    (ctl (cs_mem s) (KRequests d) < seq -> decisions d seq (cs_log s) = 0%nat).
Proof.
  intros c tr s Hr; induction Hr as [| tr s st s' Hr IH Hexec]; intros d seq.
  { split; [cbn; lia | intros _; reflexivity]. }
  destruct (match st with CDecideMgmt _ => true | _ => false end) eqn:Hst.
  - destruct st as [| x | x | x | x | ch r | ch | ch | ch | ch | ch | ch n | | x
                   | x e | x | x | x | x bytes |]; try discriminate Hst.
    simpl in Hexec; exec_destruct Hexec.
    match goal with
    | H : handle_mgmt _ _ _ _ = (?m', ?todo, ?o, ?evs) |- _ =>
        rewrite cs_log_h0_after, decisions_app, h0_after_kreq;
        destruct (handle_mgmt_kreq _ _ _ _ _ _ _ _ H)
          as [[Hq Hk] | [fid [t [q [st0 [out [Hevs [Hq [Hk Hk']]]]]]]]]
    end.
    + rewrite (decisions_quiet _ _ _ Hq); unfold ctl in *; rewrite Hk.
      destruct (IH d seq) as [I1 I2]; split; [lia |].
      intros Hlt; rewrite I2 by exact Hlt; reflexivity.
    + subst; unfold ctl in *; rewrite decisions_single.
      destruct (Nat.eq_dec x d) as [-> | Hxd].
      * rewrite Hk, Nat.eqb_refl; cbn [andb].
        destruct (IH d seq) as [I1 I2].
        destruct (cs_mem s (WCtl (KRequests d)) + 1 =? seq) eqn:Eq.
        -- apply N.eqb_eq in Eq; subst seq.
           rewrite I2 by lia; split; [lia | intros Hlt; lia].
        -- apply N.eqb_neq in Eq; rewrite Nat.add_0_r; split; [exact I1 |].
           intros Hlt; apply I2; lia.
      * rewrite (Hk' d (fun H => Hxd (eq_sym H))).
        replace (Nat.eqb x d) with false
          by (symmetry; apply Nat.eqb_neq; exact Hxd).
        cbn [andb]; rewrite Nat.add_0_r; exact (IH d seq).
  - assert (Hnd : forall y, st <> CDecideMgmt y)
      by (intros y ->; discriminate Hst).
    assert (Hev : exists evs, cs_log s' = cs_log s ++ evs /\
                              Forall no_decide_event evs).
    { destruct st as [| x | x | x | x | ch r | ch | ch | ch | ch | ch | ch n | | x
                     | x e | x | x | x | x bytes |];
        try (exfalso; eapply Hnd; reflexivity);
        try (destruct (exec_no_mgmt c s _ s' Hexec
                         (fun y H => ltac:(discriminate H))
                         (fun y H => ltac:(discriminate H))) as [evs [Hl Hq]];
             exists evs; split; [exact Hl |];
             eapply Forall_impl; [| exact Hq]; intros [] Hx; simpl in *; tauto).
      simpl in Hexec; exec_destruct Hexec.
      match goal with
      | H : handle_step _ _ _ = (_, _, _, ?evs) |- _ =>
          exists evs; split; [apply cs_log_h0_after |];
          exact (handle_step_nodec _ _ _ _ _ _ _ H)
      end. }
    destruct Hev as [evs [Hl Hq]].
    rewrite Hl, decisions_app, (decisions_quiet d seq evs Hq), Nat.add_0_r.
    rewrite (exec_kreq_frame c s st s' Hexec Hnd d); exact (IH d seq).
Qed.

(**
 * P6, mgmt_answered_once, as a safety property (erratum S-4's reading):
 * domain d's management request seq has at most one decision in every
 * trace, and exactly one once the trace contains its decide_mgmt step. The
 * decision is the request's answer or refusal: a refusal is answered to the
 * requester at once; a delivery is answered when its target parks or shuts
 * down, which is the target hart's progress, a liveness fact the SC
 * traces do not give and this theorem does not claim.
 *)
Theorem mgmt_answered_once :
  forall c tr s, reach c tr s -> forall d seq,
    (decisions d seq (cs_log s) <= 1)%nat /\
    ((exists fid t st out, In (GDecide d fid t seq st out) (cs_log s)) ->
       decisions d seq (cs_log s) = 1%nat).
Proof.
  intros c tr s Hr d seq.
  destruct (decisions_reach c tr s Hr d seq) as [H1 _].
  split; [exact H1 |].
  intros [fid [t [st [out Hin]]]].
  pose proof (decisions_pos d seq (cs_log s) fid t st out Hin); lia.
Qed.

(* --------------------------------------------------------------------- *)
(** * The stage-1 claim set *)

Record stage1_claim_set : Prop := {
  c_ring_no_overrun :
    ltac:(let t := type of ring_no_overrun in exact t);
  c_ring_take_published_only :
    ltac:(let t := type of ring_take_published_only in exact t);
  c_ring_indices_monotone :
    ltac:(let t := type of ring_indices_monotone in exact t);
  c_control_ring_fails_closed :
    ltac:(let t := type of control_ring_fails_closed in exact t);
  c_input_ring_drops_under_room :
    ltac:(let t := type of input_ring_drops_under_room in exact t);
  c_ring_fifo_integrity :
    ltac:(let t := type of ring_fifo_integrity in exact t);
  c_ring_type_set :
    ltac:(let t := type of ring_type_set in exact t);
  c_drain_round_robin :
    ltac:(let t := type of drain_round_robin in exact t);
  c_drain_in_order :
    ltac:(let t := type of drain_in_order in exact t);
  c_concrete_step_within_footprint :
    ltac:(let t := type of concrete_step_within_footprint in exact t);
  c_single_writer_carried :
    ltac:(let t := type of single_writer_carried in exact t);
  c_roots_from_instance :
    ltac:(let t := type of roots_from_instance in exact t);
  c_instance_page_numbering :
    ltac:(let t := type of instance_page_numbering in exact t);
  c_mgmt_grants_from_instance :
    ltac:(let t := type of mgmt_grants_from_instance in exact t);
  c_barrier_publication_block :
    ltac:(let t := type of barrier_publication_block in exact t);
  c_flow_is_declared_channel :
    ltac:(let t := type of flow_is_declared_channel in exact t);
  c_denial_iff_entry_below_ceiling :
    ltac:(let t := type of denial_iff_entry_below_ceiling in exact t);
  c_denial_record_before_resume :
    ltac:(let t := type of denial_record_before_resume in exact t);
  c_mgmt_decided_by_control_hart :
    ltac:(let t := type of mgmt_decided_by_control_hart in exact t);
  c_mgmt_outcome_from_grants :
    ltac:(let t := type of mgmt_outcome_from_grants in exact t);
  c_mgmt_one_pending_per_domain :
    ltac:(let t := type of mgmt_one_pending_per_domain in exact t);
  c_mgmt_answered_once :
    ltac:(let t := type of mgmt_answered_once in exact t);
  c_parked_never_resumes :
    ltac:(let t := type of parked_never_resumes in exact t);
  c_entry_after_gate :
    ltac:(let t := type of entry_after_gate in exact t);
  c_gate_false_no_start :
    ltac:(let t := type of gate_false_no_start in exact t)
}.

(** Every stage-1 theorem, bundled. *)
Theorem stage1_claims : stage1_claim_set.
Proof.
  exact (Build_stage1_claim_set ring_no_overrun ring_take_published_only
           ring_indices_monotone control_ring_fails_closed
           input_ring_drops_under_room ring_fifo_integrity ring_type_set
           drain_round_robin drain_in_order concrete_step_within_footprint
           single_writer_carried roots_from_instance instance_page_numbering
           mgmt_grants_from_instance barrier_publication_block
           flow_is_declared_channel
           denial_iff_entry_below_ceiling denial_record_before_resume
           mgmt_decided_by_control_hart mgmt_outcome_from_grants
           mgmt_one_pending_per_domain mgmt_answered_once parked_never_resumes
           entry_after_gate
           gate_false_no_start).
Qed.
