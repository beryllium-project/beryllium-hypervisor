(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Purpose: stage 1's two obligations (MVP M8, work package M8-3;
 * planning/mvp-m8-plan.md, D-1): obligation 1, every step of every trace
 * writes only within the footprint of the Binding.v transition it refines,
 * and Binding.v's H3 carried to the concrete steps (P2); obligation 2, the
 * concrete roots and their leaf rights are derived from the generated
 * instance, are rights Policy.v's A8 admits, and the only cross-domain
 * flow they allow is the declared channel, by A6 (P5's rights).
 * Specification: planning/mvp-m8-specifications.md, SHA-256
 * ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d, accepted
 * as reviewer of record at exact commit 004f31ae with that hash unchanged;
 * its errata S-1 to S-4 (P1 scoped to the block's published words, P5
 * below the exit ceiling, the parked domain's reading, and
 * mgmt_answered_once's safety reading) are recorded in
 * planning/mvp-m8-plan.md's decision record, not in the document;
 * section 3, P2 and P5, with the theorem names it fixes.
 * Semantics: Concrete.v's traces, sequentially consistent interleavings.
 * Method: a step's declared write set (Concrete.v's cwrites) bounds what it
 * changes (ConcreteRings.v's exec_frame); each word it names is typed by
 * Concrete.v's word_object and lies in its transition's footprint, a new
 * object through the Binding.v object enclosing it, an input object
 * through InputRing.v's input step, and before the barrier any object
 * hart 0 writes (I16 gives every object to hart 0 there). Every step of a
 * trace names one of the two domains (step_ok_reach), so its transition is
 * one of mvp_binding's and H3 applies.
 * Trust: an abstract model of the protocol, not a refinement of the C. The
 * derivation of a domain's root from an instance's view is this module's
 * reading of be_mvp_core_gstage: the window is the domain's own memory
 * object at the guest window's address; each other memory object granted
 * to the domain's subject is a page leaf, 4 KiB at be_mvp_channel_gpa plus
 * 4 KiB per object after the two windows, with the grant's read, write,
 * and execute as the leaf's R, W, and X. The numbering is the generator's
 * and is checked on the generated instances (instance_page_numbering);
 * the one fact assumed is that the scenarios list their pages in
 * guest-physical order from be_mvp_channel_gpa, as both scenario.json do.
 *)

From Stdlib Require Import Bool List PeanoNat NArith Lia Relations.
Require Import Policy Instances Binding InputRing ConcreteLayout Concrete
  ConcreteRings.
Import ListNotations.
Local Open Scope N_scope.

(* --------------------------------------------------------------------- *)
(** * Every step of a trace names one of the two domains *)

(** [step_ok]: a step's domain, or its ring's, is one of the two; a room or
    a drop is on an input ring. *)
Definition step_ok (st : cstep) : Prop :=
  match st with
  | CPrepare | CDrain | CRunEnd => True
  | CPublishBlock d | CStart d | CReady d | CEnter d | CStepRecord d
  | CExit d _ | CDecideMgmt d | CPark d | CFail d | CPoll d _ => (d < 2)%nat
  | CPost ch _ | CPublish ch | CAcquire ch | CTake ch | CRelease ch =>
      (ring_domain ch < 2)%nat
  | CRoom ch | CDrop ch _ =>
      match ch with Inp d => (d < 2)%nat | Ctl _ => False end
  end.

(** [dom_inv]: a domain outside the two never starts, and hart 0 takes
    input only for one of the two. *)
Definition dom_inv (s : cstate) : Prop :=
  (forall d, (2 <= d)%nat -> cs_dmode s d = DOff /\ cs_dtodo s d = []) /\
  (forall d bytes o, cs_h0 s = H0Input d bytes o -> (d < 2)%nat).

Ltac ltb_facts :=
  repeat match goal with
  | H : (_ && _) = true |- _ => apply andb_true_iff in H as [? ?]
  | H : negb _ = false |- _ => apply negb_false_iff in H
  | H : Nat.ltb _ _ = true |- _ => apply Nat.ltb_lt in H
  | H : Nat.eqb _ _ = true |- _ => apply Nat.eqb_eq in H
  end.

Lemma dom_inv_reach : forall c tr s, reach c tr s -> dom_inv s.
Proof.
  intros c tr s Hr; induction Hr as [| tr s st s' Hr IH Hexec].
  - split; [intros d _; split; reflexivity | intros d bytes o H; discriminate H].
  - destruct IH as [I1 I2].
    exec_split st Hexec; state_simpl; unfold dom_inv;
      cbn [cs_h0 cs_h0todo cs_dmode cs_dtodo cs_log cs_mem].
    all: try match goal with
             | H : handle_step _ _ _ = (_, _, ?o, _) |- _ => destruct o
             end;
      try match goal with
          | H : handle_mgmt _ _ _ _ = (_, _, ?o, _) |- _ => destruct o
          end;
      repeat match goal with
             | |- context [match drain_next ?m with _ => _ end] =>
                 destruct (drain_next m)
             end;
      cbn [cs_h0 cs_h0todo cs_dmode cs_dtodo cs_log cs_mem]; split.
    all: try (intros dx Hdx; cbv beta;
              repeat match goal with
                     | |- context [Nat.eqb dx ?y] =>
                         let E := fresh "E" in
                         destruct (Nat.eqb dx y) eqn:E;
                         [apply Nat.eqb_eq in E; subst dx |]
                     end;
              first [ apply I1; exact Hdx
                    | ltb_facts; lia
                    | exfalso; destruct (I1 _ Hdx) as [Hm Ht]; ltb_facts;
                      first [congruence | lia] ]).
    all: try (intros dx bx ox Hmx;
              first [ discriminate Hmx
                    | exact (I2 _ _ _ Hmx)
                    | injection Hmx as <- <- <-; ltb_facts; first
                        [ lia
                        | match goal with
                          | H : cs_h0 _ = H0Input ?y _ _ |- _ =>
                              pose proof (I2 _ _ _ H); subst; lia
                          end
                        | pose proof (I2 _ _ _ eq_refl); subst; lia ] ]).
Qed.

Lemma drain_next_lt : forall m d, drain_next m = Some d -> (d < 2)%nat.
Proof.
  intros m d H; unfold drain_next in H.
  destruct ((ctl m KDrainVisits =? 0) || (2 <=? ctl m KDrainIdle) ||
            (2 <=? ctl m KDrainNext)) eqn:Hc; [discriminate H |].
  injection H as <-.
  apply orb_false_iff in Hc as [_ Hc]; apply N.leb_gt in Hc.
  assert (Hn : ctl m KDrainNext = 0 \/ ctl m KDrainNext = 1) by lia.
  destruct Hn as [-> | ->]; cbn; lia.
Qed.

(** [step_ok_reach]: every step a trace takes names one of the two domains. *)
Lemma step_ok_reach :
  forall c tr s st s', reach c tr s -> exec c s st = Some s' -> step_ok st.
Proof.
  intros c tr s st s' Hr Hexec.
  destruct (dom_inv_reach c tr s Hr) as [Hd Hi].
  destruct (h0_inv_reach c tr s Hr) as [_ [_ Hv]].
  assert (Hvis : forall y, (cs_h0 s = H0Take y \/ (exists x, cs_h0 s = H0Release y x) \/
                            (exists r, cs_h0 s = H0Handle y r)) -> (y < 2)%nat).
  { intros y [Hm | [[x Hm] | [r Hm]]]; rewrite Hm in Hv; exact (drain_next_lt _ _ Hv). }
  exec_split st Hexec; cbn [step_ok ring_domain]; ltb_facts; subst;
    try exact I; try lia.
  all: unfold dmode_of, dtodo_of in *;
    repeat match goal with
           | H : writer_live _ _ = true |- _ => cbn [writer_live] in H
           end;
    ltb_facts; subst; try lia.
  all: match goal with
       | H : cs_dmode _ ?y = _ |- (?y < 2)%nat =>
           destruct (Nat.lt_ge_cases y 2) as [? | Hge]; [assumption |];
           destruct (Hd _ Hge) as [Hm _]; congruence
       | H : cs_dtodo _ ?y = _ :: _ |- (?y < 2)%nat =>
           destruct (Nat.lt_ge_cases y 2) as [? | Hge]; [assumption |];
           destruct (Hd _ Hge) as [_ Hm]; congruence
       | H : cs_h0 _ = H0Take ?y |- _ =>
           first [exact (Hvis _ (or_introl H)) | exact (Hvis _ (or_introl eq_refl))]
       | H : cs_h0 _ = H0Release ?y ?x |- _ =>
           first [exact (Hvis _ (or_intror (or_introl (ex_intro _ x H))))
                 | exact (Hvis _ (or_intror (or_introl (ex_intro _ x eq_refl))))]
       | H : cs_h0 _ = H0Handle ?y ?r |- _ =>
           first [exact (Hvis _ (or_intror (or_intror (ex_intro _ r H))))
                 | exact (Hvis _ (or_intror (or_intror (ex_intro _ r eq_refl))))]
       | H : cs_h0 _ = H0Input ?y ?b ?o |- _ =>
           first [exact (Hi _ _ _ H) | exact (Hi _ _ _ eq_refl)]
       | H : next_is (drain_next _) ?y = true |- _ =>
           apply next_is_some, drain_next_lt in H; exact H
       end.
Qed.

(* --------------------------------------------------------------------- *)
(** * Obligation 1: each step's writes within its transition's footprint *)

(**
 * [within st o]: a word of object o may be written by st: a Binding.v
 * object in the footprint of the transition st refines, a new object
 * through the Binding.v object enclosing it, an input object or domain
 * memory in the footprint of the input step st refines, or any object
 * before the barrier, which only hart 0 writes.
 *)
Definition within (st : cstep) (o : cobject) : Prop :=
  match o with
  | CSys (BindingObject b) => In b (footprint mvp_binding (refines st))
  | CNew n => In (enclosing n) (footprint mvp_binding (refines st))
  | CSys other =>
      (exists t, refines_input st = Some t /\ In other (input_footprint t)) \/
      (cphase st = BeforeBarrier /\ chart st = bi_control mvp_binding)
  end.

Lemma two_cases : forall d, (d < 2)%nat -> d = 0%nat \/ d = 1%nat.
Proof. intros d H; lia. Qed.

Ltac in_tac := solve [simpl; repeat (first [left; reflexivity | right])].

Ltac within_tac :=
  cbn [within word_object view_object bobj iobj enclosing refines refines_post
       refines_input chart cphase cring_writer cring_reader stack_word dhart
       ring_writer ring_reader bi_control bi_hart_of mvp_binding];
  repeat match goal with |- context [if ?b then _ else _] => destruct b end;
  first [ in_tac
        | left; eexists; split; [reflexivity | in_tac]
        | right; split; reflexivity ].

Ltac concrete_domain :=
  match goal with
  | H : (?d < 2)%nat |- _ => destruct (two_cases d H) as [-> | ->]
  end.

(** A step's own stack word lies in its transition's footprint. *)
Lemma stack_within :
  forall st, step_ok st -> within st (word_object (stack_word (chart st))).
Proof.
  intros st Hok.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (destruct channel as [[d | d] | d]); cbn [step_ok ring_domain] in Hok;
    try contradiction Hok;
    first [within_tac | concrete_domain; within_tac].
Qed.

(** Each word a step names lies in its transition's footprint. *)
Lemma cwrites_within :
  forall st w, step_ok st -> cwrites st w = true -> within st (word_object w).
Proof.
  intros st w Hok Hw.
  unfold cwrites in Hw; apply orb_true_iff in Hw as [Hs | Hw].
  { apply cword_eqb_eq in Hs; subst w; apply stack_within; exact Hok. }
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (destruct channel as [[d | d] | d]); cbn [step_ok ring_domain] in Hok;
    try contradiction Hok;
    destruct w as [d' f | ch f | k | d' | d' |];
    try (destruct ch as [[d'' | d''] | d'']);
    try (destruct f; try (match goal with cf : core_field |- _ => destruct cf end));
    try destruct k;
    simpl in Hw; try discriminate Hw; ltb_facts;
    try (match goal with H : false = true |- _ => discriminate H end); subst;
    first [within_tac | concrete_domain; within_tac].
Qed.

(**
 * P2, obligation 1: every step of every trace names one of the two domains,
 * every word in its declared write set lies within the footprint of the
 * Binding.v transition it refines (new objects through the object
 * enclosing them, input objects through InputRing.v's step), and every
 * word it changes is one of them.
 *)
Theorem concrete_step_within_footprint :
  forall c tr s st s', reach c tr s -> exec c s st = Some s' ->
    step_ok st /\
    (forall w, cwrites st w = true -> within st (word_object w)) /\
    (forall w, cs_mem s' w <> cs_mem s w -> within st (word_object w)).
Proof.
  intros c tr s st s' Hr Hexec.
  pose proof (step_ok_reach c tr s st s' Hr Hexec) as Hok.
  split; [exact Hok | split].
  - intros w; apply cwrites_within; exact Hok.
  - intros w Hne; apply cwrites_within; [exact Hok |].
    destruct (cwrites st w) eqn:Hw; [reflexivity |].
    exfalso; apply Hne; exact (exec_frame c s st s' Hexec w Hw).
Qed.

(* --------------------------------------------------------------------- *)
(** * H3 carried to the concrete steps *)

(** [binding_object]: the Binding.v object a word's object is or lies in. *)
Definition binding_object (o : cobject) : option hart_object :=
  match o with
  | CSys (BindingObject b) => Some b
  | CNew n => Some (enclosing n)
  | CSys _ => None
  end.

Lemma within_footprint :
  forall st o b, within st o -> binding_object o = Some b ->
    In b (footprint mvp_binding (refines st)).
Proof.
  intros st [[b' | i | d] | n] b Hw Hb; simpl in Hb; try discriminate Hb;
    injection Hb as <-; exact Hw.
Qed.

Lemma chart_refines :
  forall st, step_ok st -> chart st = transition_hart mvp_binding (refines st).
Proof.
  intros st Hok.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (destruct channel as [[d | d] | d]); cbn [step_ok ring_domain] in Hok;
    try contradiction Hok;
    cbn [chart refines refines_post cring_writer cring_reader dhart];
    repeat match goal with |- context [if ?b then _ else _] => destruct b end;
    reflexivity.
Qed.

Lemma cphase_refines :
  forall st, cphase st = transition_phase (refines st).
Proof.
  intros st.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (destruct channel as [[d | d] | d]); cbn [cphase refines refines_post];
    repeat match goal with |- context [if ?b then _ else _] => destruct b end;
    reflexivity.
Qed.

Lemma refines_in :
  forall st, step_ok st -> In (refines st) (transitions mvp_binding).
Proof.
  intros st Hok.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (destruct channel as [[d | d] | d]); cbn [step_ok ring_domain] in Hok;
    try contradiction Hok; try concrete_domain;
    cbn [refines refines_post];
    repeat match goal with |- context [if ?b then _ else _] => destruct b end;
    in_tac.
Qed.

Lemma chart_refines_input :
  forall st t, refines_input st = Some t -> chart st = input_hart mvp_binding t.
Proof.
  intros st t H.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    try (destruct channel as [[d | d] | d]); simpl in H; try discriminate H;
    injection H as <-; reflexivity.
Qed.

(**
 * P2, H3 carried: for every step of every trace and every word it changes,
 * before the barrier the step is hart 0's; after it, the word's Binding.v
 * object is not published data, a ring's records and head are written only
 * by its writer and its tail only by its reader, a private object only by
 * its owner; an input object only by its InputRing.v writer, and a
 * domain's memory only by that domain's hart.
 *)
Theorem single_writer_carried :
  forall c tr s st s', reach c tr s -> exec c s st = Some s' ->
    forall w, cs_mem s' w <> cs_mem s w ->
      (cphase st = BeforeBarrier -> chart st = bi_control mvp_binding) /\
      (forall b, binding_object (word_object w) = Some b ->
         cphase st = AfterBarrier ->
         published b = false /\
         (forall r, b = RingRecords r \/ b = RingHead r ->
            chart st = ring_writer mvp_binding r) /\
         (forall r, b = RingTail r -> chart st = ring_reader mvp_binding r) /\
         (forall owner, private_owner mvp_binding b = Some owner ->
            owner = chart st)) /\
      (forall i, word_object w = CSys (InputObject i) ->
         cphase st = AfterBarrier -> chart st = input_writer mvp_binding i) /\
      (forall d, word_object w = CSys (DomainMemory d) ->
         cphase st = AfterBarrier -> chart st = bi_hart_of mvp_binding d).
Proof.
  intros c tr s st s' Hr Hexec w Hne.
  destruct (concrete_step_within_footprint c tr s st s' Hr Hexec)
    as [Hok [_ Hwithin]].
  specialize (Hwithin w Hne).
  destruct binding_h3_single_writer as [_ [H3b [H3c [H3d H3e]]]].
  destruct (input_ring_single_writer mvp_binding) as [T1a T1b].
  pose proof (refines_in st Hok) as Hin.
  pose proof (chart_refines st Hok) as Hchart.
  pose proof (cphase_refines st) as Hphase.
  split; [| split; [| split]].
  - intros Hb; destruct st; simpl in Hb; try discriminate Hb; reflexivity.
  - intros b Hb Hph; rewrite Hphase in Hph.
    pose proof (within_footprint _ _ _ Hwithin Hb) as Hfoot.
    split; [exact (H3b _ _ Hin Hph Hfoot) |].
    split; [| split].
    + intros r Hr'; rewrite Hchart; apply (H3c _ r Hin Hph).
      destruct Hr' as [-> | ->]; [left | right]; exact Hfoot.
    + intros r ->; rewrite Hchart; exact (H3d _ r Hin Hph Hfoot).
    + intros owner Hown; rewrite Hchart; exact (H3e _ _ _ Hin Hph Hfoot Hown).
  - intros i Hi Hph; rewrite Hi in Hwithin; simpl in Hwithin.
    destruct Hwithin as [[t [Ht Hin_t]] | [Hb _]];
      [| rewrite Hb in Hph; discriminate Hph].
    rewrite (chart_refines_input st t Ht).
    exact (T1a (InputStep t) i Hin_t).
  - intros d Hdm Hph; rewrite Hdm in Hwithin; simpl in Hwithin.
    destruct Hwithin as [[t [Ht Hin_t]] | [Hb _]];
      [| rewrite Hb in Hph; discriminate Hph].
    rewrite (chart_refines_input st t Ht).
    exact (T1b t d Hin_t).
Qed.

(* --------------------------------------------------------------------- *)
(** * Obligation 2: the roots derived from the instance, their rights A8's *)

Definition pte_r_bit : N := 1.

Definition has_perm (perm : nat) (perms : list nat) : bool :=
  existsb (Nat.eqb perm) perms.

(** A leaf's bits: valid, and read, write, and execute as granted. *)
Definition pte_of (perms : list nat) : N :=
  1 + (if has_perm perm_read perms then 2 else 0) +
  (if has_perm perm_write perms then 4 else 0) +
  (if has_perm perm_execute perms then 8 else 0).

(**
 * [root_of_instance inst d]: domain d's walked window and page leaves as
 * be_mvp_core_gstage derives them from the sealed configuration whose
 * policy view is inst's: the guest window, and a 4 KiB leaf for each other
 * memory object granted to the domain's subject (subject d + 1), objects 0
 * and 1 being the two windows.
 *)
(* reads: mvp/src/mvp-core.c:be_mvp_core_gstage *)
(* reads: mvp/src/mvp-core.c:add_page *)
Definition page_leaf (grant : raw_grant) : leaf :=
  mk_leaf (be_mvp_channel_gpa + 4096 * N.of_nat (rg_object grant - 2)) 4096
    (pte_of (rg_perms grant)).

Definition domain_page (d : nat) (grant : raw_grant) : bool :=
  Nat.eqb (rg_subject grant) (S d) && Nat.eqb (rg_class grant) class_memory &&
  Nat.leb 2 (rg_object grant).

Definition root_of_instance (inst : raw_instance) (d : nat) : walked :=
  mk_walked be_mvp_guest_gpa be_mvp_guest_bytes
    (map page_leaf (filter (domain_page d) (rv_grants (ri_view inst)))).

(** The window's grant: the domain's own memory object, read, written, run. *)
Definition window_grant (d : nat) (grant : raw_grant) : bool :=
  Nat.eqb (rg_subject grant) (S d) && Nat.eqb (rg_object grant) d &&
  Nat.eqb (rg_class grant) class_memory && has_perm perm_read (rg_perms grant) &&
  has_perm perm_write (rg_perms grant) && has_perm perm_execute (rg_perms grant).

Definition window_ok (view : raw_view) (d : nat) : bool :=
  existsb (window_grant d) (rv_grants view).

Lemma has_perm_in : forall p perms, has_perm p perms = true <-> In p perms.
Proof.
  intros p perms; unfold has_perm; rewrite existsb_exists; split.
  - intros [x [Hx He]]; apply Nat.eqb_eq in He; subst; exact Hx.
  - intros H; exists p; split; [exact H | apply Nat.eqb_refl].
Qed.

Lemma pte_bits :
  forall perms,
    N.testbit (pte_of perms) pte_w_bit = has_perm perm_write perms /\
    N.testbit (pte_of perms) pte_r_bit = has_perm perm_read perms.
Proof.
  intros perms; unfold pte_of.
  destruct (has_perm perm_read perms), (has_perm perm_write perms),
    (has_perm perm_execute perms); split; reflexivity.
Qed.

Lemma view_of_checked :
  forall inst checked, validate_instance inst = Some checked ->
    v_view checked = ri_view inst.
Proof.
  intros inst checked H; unfold validate_instance in H.
  destruct (validate_fields _ _ _ _ _ H) as [_ [_ [_ Hv]]]; exact Hv.
Qed.

Lemma root_leaf_grant :
  forall inst d l, In l (map_leaves (root_of_instance inst d)) ->
    exists g, In g (rv_grants (ri_view inst)) /\ rg_subject g = S d /\
      rg_class g = class_memory /\ (2 <= rg_object g)%nat /\ l = page_leaf g.
Proof.
  intros inst d l Hl; simpl in Hl.
  apply in_map_iff in Hl as [g [<- Hg]].
  apply filter_In in Hg as [Hg Hp]; unfold domain_page in Hp.
  apply andb_true_iff in Hp as [Hp Hle]; apply andb_true_iff in Hp as [Hs Hc].
  apply Nat.eqb_eq in Hs, Hc; apply Nat.leb_le in Hle.
  exists g; repeat split; assumption.
Qed.

(** te-poc and anchor pass every analysis, and grant each domain its window. *)
Lemma instance_facts :
  forall inst, inst = instance2 \/ inst = instance3 ->
    exists checked, validate_instance inst = Some checked /\
      a8 checked = true /\ a6 checked = true /\
      window_ok (ri_view inst) 0 = true /\ window_ok (ri_view inst) 1 = true.
Proof.
  intros inst Hinst.
  assert (Hver : verdicts inst = all_pass)
    by (destruct Hinst as [-> | ->]; vm_compute; reflexivity).
  assert (Hwin : window_ok (ri_view inst) 0 = true /\
                 window_ok (ri_view inst) 1 = true)
    by (destruct Hinst as [-> | ->]; split; vm_compute; reflexivity).
  unfold verdicts in Hver.
  destruct (validate_instance inst) as [checked |] eqn:Hv;
    [| discriminate Hver].
  injection Hver as Ha2 Ha3 Ha4 Ha5 Ha6 Ha7 Ha8.
  exists checked; repeat split; try assumption; apply Hwin.
Qed.

(**
 * P5, obligation 2: for te-poc and anchor, when the configuration's roots
 * are those the instance derives, each domain's window is its own memory
 * object, granted read, write, and execute under rules the policy has, and
 * each page leaf is a memory grant to the domain whose every right A8
 * admits, the leaf's W bit its write right: every mapping and right of the
 * root is one the generated instance's A8 admits.
 *)
Theorem roots_from_instance :
  forall inst c, inst = instance2 \/ inst = instance3 ->
    (forall d, (d < 2)%nat -> cfg_root c d = root_of_instance inst d) ->
    exists checked,
      validate_instance inst = Some checked /\ a8 checked = true /\
      forall d, (d < 2)%nat ->
        map_gpa (cfg_root c d) = be_mvp_guest_gpa /\
        map_size (cfg_root c d) = be_mvp_guest_bytes /\
        (exists g, In g (rv_grants (v_view checked)) /\ rg_subject g = S d /\
           rg_object g = d /\ rg_class g = class_memory /\
           In perm_read (rg_perms g) /\ In perm_write (rg_perms g) /\
           In perm_execute (rg_perms g) /\
           forall perm, In perm (rg_perms g) ->
             decide checked (subject_type checked (S d))
               (grant_target_type checked g) class_memory perm = true) /\
        (forall l, In l (map_leaves (cfg_root c d)) ->
           exists g, In g (rv_grants (v_view checked)) /\ rg_subject g = S d /\
             rg_class g = class_memory /\ l = page_leaf g /\
             (N.testbit (leaf_pte l) pte_w_bit = true <->
              In perm_write (rg_perms g)) /\
             (forall perm, In perm (rg_perms g) ->
                decide checked (subject_type checked (S d))
                  (grant_target_type checked g) class_memory perm = true)).
Proof.
  intros inst c Hinst Hroot.
  destruct (instance_facts inst Hinst) as [checked [Hv [H8 [_ [W0 W1]]]]].
  destruct (policy_a8_sound checked H8) as [Hgr _].
  pose proof (view_of_checked _ _ Hv) as Hview.
  exists checked; split; [exact Hv | split; [exact H8 |]].
  intros d Hd; rewrite (Hroot d Hd).
  split; [reflexivity | split; [reflexivity | split]].
  - assert (Hw : window_ok (ri_view inst) d = true)
      by (destruct (two_cases d Hd) as [-> | ->]; assumption).
    unfold window_ok in Hw; apply existsb_exists in Hw as [g [Hg Hwg]].
    unfold window_grant in Hwg.
    repeat match goal with
           | H : (_ && _) = true |- _ => apply andb_true_iff in H as [? ?]
           end.
    rewrite <- Hview in Hg.
    exists g; split; [exact Hg |].
    repeat match goal with
           | H : Nat.eqb _ _ = true |- _ => apply Nat.eqb_eq in H
           | H : has_perm _ _ = true |- _ => apply has_perm_in in H
           end.
    repeat split; try assumption.
    intros perm Hp; rewrite <- (Hgr g perm Hg Hp).
    f_equal; [congruence | congruence].
  - intros l Hl.
    destruct (root_leaf_grant inst d l Hl) as [g [Hg [Hs [Hc [_ ->]]]]].
    rewrite <- Hview in Hg.
    exists g; split; [exact Hg | split; [exact Hs | split; [exact Hc |]]].
    split; [reflexivity | split].
    + cbn [leaf_pte page_leaf]; rewrite (proj1 (pte_bits (rg_perms g))).
      apply has_perm_in.
    + intros perm Hp; rewrite <- (Hgr g perm Hg Hp), Hs, Hc; reflexivity.
Qed.

(**
 * P5, A6 applied: for te-poc and anchor with the roots the instance
 * derives, a page one domain's root maps writable and another's maps
 * readable, the two subjects of different types, is a flow from the first
 * type to the second that the declared channels' transitive closure
 * contains: the only cross-domain flow is the declared channel.
 *)
Theorem flow_is_declared_channel :
  forall inst c, inst = instance2 \/ inst = instance3 ->
    (forall d, (d < 2)%nat -> cfg_root c d = root_of_instance inst d) ->
    exists checked, validate_instance inst = Some checked /\
      forall d1 d2 l1 l2, (d1 < 2)%nat -> (d2 < 2)%nat ->
        In l1 (map_leaves (cfg_root c d1)) ->
        In l2 (map_leaves (cfg_root c d2)) ->
        leaf_gpa l1 = leaf_gpa l2 ->
        N.testbit (leaf_pte l1) pte_w_bit = true ->
        N.testbit (leaf_pte l2) pte_r_bit = true ->
        subject_type checked (S d1) <> subject_type checked (S d2) ->
        clos_trans nat (declared_channel checked)
          (subject_type checked (S d1)) (subject_type checked (S d2)).
Proof.
  intros inst c Hinst Hroot.
  destruct (instance_facts inst Hinst) as [checked [Hv [H8 [H6 _]]]].
  pose proof (view_of_checked _ _ Hv) as Hview.
  exists checked; split; [exact Hv |].
  intros d1 d2 l1 l2 Hd1 Hd2 Hl1 Hl2 Hgpa Hw Hrd Hne.
  rewrite (Hroot d1 Hd1) in Hl1; rewrite (Hroot d2 Hd2) in Hl2.
  destruct (root_leaf_grant inst d1 l1 Hl1) as [g1 [Hg1 [Hs1 [Hc1 [Ho1 ->]]]]].
  destruct (root_leaf_grant inst d2 l2 Hl2) as [g2 [Hg2 [Hs2 [Hc2 [Ho2 ->]]]]].
  rewrite <- Hview in Hg1, Hg2.
  cbn [leaf_gpa leaf_pte page_leaf] in Hgpa, Hw, Hrd.
  rewrite (proj1 (pte_bits _)), has_perm_in in Hw.
  rewrite (proj2 (pte_bits _)), has_perm_in in Hrd.
  assert (Hobj : rg_object g1 = rg_object g2) by lia.
  apply (proj1 (policy_a6_closure_equality checked H6 _ _)).
  apply t_step, (policy_a8_flow_confinement checked H8).
  split; [exact Hne |].
  exists g1, g2; repeat split; try assumption; congruence.
Qed.

(* --------------------------------------------------------------------- *)
(** * The generated instances' object numbering, checked *)

(*
 * The generator numbers a scenario's objects in its labeling's order and
 * then the configuration's others (model/tools/gen-policy-fixtures.mjs,
 * translate's identify; mvpConfiguration lists the two windows first).
 * page_leaf places object o at be_mvp_channel_gpa + 4 KiB (o - 2). Checked
 * below by computation on the generated te-poc and anchor: objects 0 and 1
 * are the two windows, each owned by its domain's subject and granted as
 * memory only to it, and the pages granted are the objects from 2 on,
 * consecutively (te-poc's one shared page, anchor's request, response, and
 * secret pages), at most be_mvp_pages_max. Instances.v records no extents,
 * so what stays assumed is the pages' order: that the scenarios list
 * their pages in the order of their guest-physical addresses from
 * be_mvp_channel_gpa (both scenarios' scenario.json do, 4 KiB apart).
 *)
Definition window_owned (view : raw_view) (d : nat) : bool :=
  existsb (fun o => Nat.eqb (row_object o) d && Nat.eqb (row_owner o) (S d))
    (rv_ownerships view).

Definition windows_own (view : raw_view) : bool :=
  forallb (fun g => implb (Nat.eqb (rg_class g) class_memory &&
                           Nat.ltb (rg_object g) 2)
                          (Nat.eqb (rg_subject g) (S (rg_object g))))
    (rv_grants view).

Definition page_objects (view : raw_view) : list nat :=
  dedup (map rg_object
           (filter (fun g => Nat.eqb (rg_class g) class_memory &&
                             Nat.leb 2 (rg_object g)) (rv_grants view))).

Theorem instance_page_numbering :
  window_owned (ri_view instance2) 0 = true /\
  window_owned (ri_view instance2) 1 = true /\
  windows_own (ri_view instance2) = true /\
  page_objects (ri_view instance2) = [2%nat] /\
  window_owned (ri_view instance3) 0 = true /\
  window_owned (ri_view instance3) 1 = true /\
  windows_own (ri_view instance3) = true /\
  page_objects (ri_view instance3) = [2%nat; 3%nat; 4%nat] /\
  (3 <= N.to_nat be_mvp_pages_max)%nat.
Proof. repeat split; vm_compute; reflexivity. Qed.

(* --------------------------------------------------------------------- *)
(** * The sealed management grants from the instance *)

(**
 * [grant_of]: a management grant of the view (class domain) as the sealed
 * configuration's be_mvp_mgmt_grant: requester and target by domain index
 * (subject id less one), pause as bit 1 and terminate as bit 2 (granted).
 *)
(* reads: mvp/src/mvp.h:be_mvp_mgmt_grant *)
Definition mgmt_bits (perms : list nat) : N :=
  (if has_perm perm_pause perms then 1 else 0) +
  (if has_perm perm_terminate perms then 2 else 0).

Definition grant_of (g : raw_grant) : mgmt_grant :=
  mk_mgmt_grant (N.of_nat (rg_subject g - 1)) (N.of_nat (rg_object g - 1))
    (mgmt_bits (rg_perms g)).

Definition mgmt_grants_of (view : raw_view) : list mgmt_grant :=
  map grant_of (filter (fun g => Nat.eqb (rg_class g) class_domain)
                  (rv_grants view)).

Lemma mgmt_grants_general :
  forall inst checked, validate_instance inst = Some checked ->
    a8 checked = true ->
    (forall g, In g (mgmt_grants_of (ri_view inst)) ->
       exists rg, In rg (rv_grants (v_view checked)) /\
         rg_class rg = class_domain /\ g = grant_of rg /\
         forall perm, In perm (rg_perms rg) ->
           decide checked (subject_type checked (rg_subject rg))
             (grant_target_type checked rg) class_domain perm = true) /\
    (forall rg, In rg (rv_grants (v_view checked)) ->
       rg_class rg = class_domain -> In (grant_of rg) (mgmt_grants_of (ri_view inst))).
Proof.
  intros inst checked Hv H8.
  pose proof (view_of_checked _ _ Hv) as Hview.
  destruct (policy_a8_sound checked H8) as [Hgr _].
  split.
  - intros g Hg; unfold mgmt_grants_of in Hg.
    apply in_map_iff in Hg as [rg [<- Hrg]].
    apply filter_In in Hrg as [Hrg Hc]; apply Nat.eqb_eq in Hc.
    rewrite <- Hview in Hrg.
    exists rg; split; [exact Hrg | split; [exact Hc | split; [reflexivity |]]].
    intros perm Hp; rewrite <- Hc; exact (Hgr rg perm Hrg Hp).
  - intros rg Hrg Hc; unfold mgmt_grants_of; apply in_map.
    rewrite <- Hview; apply filter_In; split; [exact Hrg |].
    apply Nat.eqb_eq; exact Hc.
Qed.

(**
 * P6 with obligation 2: for te-poc and anchor, a configuration sealed with
 * the instance's management grants holds exactly the management grants
 * of the generated instance's view, each with every right A8 admits: none
 * for te-poc, and for anchor domain 0's pause and terminate on domain 1.
 *)
Theorem mgmt_grants_from_instance :
  forall inst c, inst = instance2 \/ inst = instance3 ->
    cfg_grants c = mgmt_grants_of (ri_view inst) ->
    exists checked,
      validate_instance inst = Some checked /\ a8 checked = true /\
      (forall g, In g (cfg_grants c) ->
         exists rg, In rg (rv_grants (v_view checked)) /\
           rg_class rg = class_domain /\ g = grant_of rg /\
           forall perm, In perm (rg_perms rg) ->
             decide checked (subject_type checked (rg_subject rg))
               (grant_target_type checked rg) class_domain perm = true) /\
      (forall rg, In rg (rv_grants (v_view checked)) ->
         rg_class rg = class_domain -> In (grant_of rg) (cfg_grants c)) /\
      (inst = instance2 -> cfg_grants c = []) /\
      (inst = instance3 -> cfg_grants c = [mk_mgmt_grant 0 1 3]).
Proof.
  intros inst c Hinst Hg.
  destruct (instance_facts inst Hinst) as [checked [Hv [H8 _]]].
  destruct (mgmt_grants_general inst checked Hv H8) as [G1 G2].
  exists checked; split; [exact Hv | split; [exact H8 |]].
  rewrite Hg; split; [exact G1 | split; [exact G2 |]].
  split; intros ->; vm_compute; reflexivity.
Qed.
