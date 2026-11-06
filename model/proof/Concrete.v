(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Purpose: stage 1's concrete operational model of the MVP's harts 0 to 2
 * (MVP M8, work package M8-3; planning/mvp-m8-plan.md, D-1 to D-3), its
 * definitions: the shared words and the objects that type them, the three
 * harts' programs as one labelled transition system whose steps are the
 * protocol steps of the specification's section 2, each step's write set,
 * the Binding.v transition it refines, and the system's traces.
 * Specification: planning/mvp-m8-specifications.md, SHA-256
 * ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d, accepted
 * as reviewer of record at exact commit 004f31ae with that hash unchanged;
 * its errata S-1 to S-4 (P1 scoped to the block's published words, P5
 * below the exit ceiling, the parked domain's reading, and
 * mgmt_answered_once's safety reading) are recorded in
 * planning/mvp-m8-plan.md's decision record, not in the document;
 * sections 1 and 2; the properties P1 to P9 of its section 3 are proved
 * in ConcreteRings.v, ConcreteBridge.v, and ConcreteClaims.v.
 * Semantics: a trace is a finite interleaving of the three harts' steps
 * from the initial state; each step reads the memory as the trace left it
 * and writes it at once (sequentially consistent interleaving at word
 * granularity, the plan's D-3). Every stage-1 theorem is a statement
 * about these traces and nothing beyond them; the ordering premises L1 to
 * L5 that make this semantics describe the hardware are ConcreteRings.v's
 * and ConcreteClaims.v's hypotheses, discharged by M8-4's litmus tests.
 * Lineage: the readings are symbols at stage 1's target commit, each in a
 * reads comment naming a file under mvp/src and a symbol, checked by
 * model/tests/check-concrete-readings.sh; every layout constant is
 * ConcreteLayout.v's, generated from mvp/src/mvp-layout.h. The target
 * commit was M8's (6fbcc3d1); M10 re-made every reading at release
 * candidate 4's tree (planning/mvp-m10-plan.md, D-2 and Q4), where M9's
 * measurement log replaced measure(): the launch gate and the log are
 * re-read and re-abstracted (config, gate_verdict, global_rule),
 * be_mvp_runtime_main's order is unchanged (the placement, the log, the
 * fence, publish_blocks), and every other cited symbol's definition is as
 * at 6fbcc3d1; mvp-layout.h is unchanged.
 * Trust: an abstract model of the protocol, not a refinement of the C.
 * Binding.v and InputRing.v are imported unedited; their object types are
 * closed, so the objects here are a sum of theirs and stage 1's new ones,
 * each new one inside a Binding.v object (enclosing).
 * Abstractions, each a choice of this model and none a claim about the C:
 * - A word holds an N. A ring index is a 64-bit word, N modulo 2^64 (the
 *   plan's Q5), so the wraparound is modelled; a ring's capacity is the
 *   configuration's, any power of two in [512, 32768].
 * - A ring's buffer is byte cells; a record's image is the C's layout: a
 *   16-byte header (type, domain, the length's two little-endian bytes,
 *   four reserved zero bytes, the time's eight little-endian bytes), the
 *   payload, and zero padding to 8.
 * - The published block is a few words per field group: the descriptor
 *   (hart id, domain, hgatp) and its generation word, the first-entry
 *   frame as one word, the walked map and leaves as eleven words, the
 *   configuration as four; the SBI core's state, the controls, entered,
 *   the saved frame, and a hart's trusted stack are words the hart's steps
 *   write, the stack as one word per hart.
 * - A hart's control flow (its program position and its queue of ring
 *   actions) and stage 1's history log are the model's, not monitor
 *   memory; a stack local the protocol needs (hart 0's drain order) is a
 *   word of the hart's stack.
 * - CSRs, the firmware, SBI HSM's timing, IPIs, the console's text, the
 *   guest, and time are not modelled: an exit of any kind may occur at any
 *   time in guest mode, a hart in an HS wait may read its inbound ring at
 *   any time, and every value the hardware supplies (an exit record, a
 *   time, a console line, a batch of input bytes) is a step's argument.
 * - Refusal checks whose only effect is to fail the run are kept where a
 *   property depends on them and otherwise left out (hart 0's checks of
 *   record times and of SHUTDOWN's counters); leaving one out adds
 *   behaviours, never removes one.
 * - The measurement's content is M9's: each domain's launch gate is a
 *   predicate on the domain's placed bytes and the image's expected launch
 *   register for it, any predicate per domain, and the log's close is a
 *   boolean, any boolean; the log page and its registers are not words of
 *   this model, a reading stated before gate_verdict.
 * - Not modelled: the R3 prelude, probes, and the G-stage tables (the
 *   roots are one word per domain, written by prepare), the console's
 *   partial line that a PAUSED or TERMINATED flush posts first (M7 Q9),
 *   the fallback lines, and harts 3 to 7.
 *)

From Stdlib Require Import Bool List PeanoNat NArith Lia.
Require Import Binding InputRing ConcreteLayout.
Import ListNotations.
Local Open Scope N_scope.

(* --------------------------------------------------------------------- *)
(** * Words, indices, and capacities *)

(** [word_modulus] is 2^64: a ring index is an N below it (Q5). *)
Definition word_modulus : N := 2 ^ 64.

(* reads: mvp/src/mvp-ring.c:be_mvp_ring_post *)
Definition add64 (a b : N) : N := (a + b) mod word_modulus.

(** [sub64 a b] is the unsigned 64-bit difference a - b, for b below 2^64. *)
Definition sub64 (a b : N) : N := (a + word_modulus - b) mod word_modulus.

(**
 * [cap_okb] is the C's capacity rule: a power of two from 512
 * (BE_MVP_RING_MIN_BYTES) to 32768 (BE_MVP_OUTBOUND_RING_BYTES).
 *)
(* reads: mvp/src/mvp-ring.h:BE_MVP_RING_MIN_BYTES *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_init *)
Definition cap_okb (cap : N) : bool :=
  existsb (fun k => cap =? 2 ^ N.of_nat k) (seq 9 7) &&
  (cap <=? be_mvp_outbound_ring_bytes).

(* --------------------------------------------------------------------- *)
(** * Rings *)

(**
 * [cring] is one of a domain's three rings: Binding.v's two control rings
 * and InputRing.v's input ring.
 *)
Inductive cring : Type :=
| Ctl (channel : ring)
| Inp (domain : nat).

Definition ring_eqb (left right : ring) : bool :=
  match left, right with
  | InboundRing a, InboundRing b => Nat.eqb a b
  | OutboundRing a, OutboundRing b => Nat.eqb a b
  | _, _ => false
  end.

Definition cring_eqb (left right : cring) : bool :=
  match left, right with
  | Ctl a, Ctl b => ring_eqb a b
  | Inp a, Inp b => Nat.eqb a b
  | _, _ => false
  end.

Lemma ring_eqb_eq : forall a b, ring_eqb a b = true <-> a = b.
Proof.
  intros [a | a] [b | b]; simpl; split; intros H; try discriminate;
    try (apply Nat.eqb_eq in H; subst; reflexivity);
    try (injection H as <-; apply Nat.eqb_refl).
Qed.

Lemma cring_eqb_eq : forall a b, cring_eqb a b = true <-> a = b.
Proof.
  intros [a | a] [b | b]; simpl; split; intros H; try discriminate.
  - apply ring_eqb_eq in H; subst; reflexivity.
  - injection H as <-; apply ring_eqb_eq; reflexivity.
  - apply Nat.eqb_eq in H; subst; reflexivity.
  - injection H as <-; apply Nat.eqb_refl.
Qed.

Lemma cring_eqb_refl : forall a, cring_eqb a a = true.
Proof.
  intros a; apply cring_eqb_eq; reflexivity.
Qed.

(** [ring_domain] is the domain every record of the ring names. *)
Definition ring_domain (channel : cring) : nat :=
  match channel with
  | Ctl (InboundRing d) | Ctl (OutboundRing d) | Inp d => d
  end.

(** [dhart] is a domain's hart, Binding.v's binding: G0 on 1, G1 on 2. *)
Definition dhart (d : nat) : hart := bi_hart_of mvp_binding d.

(**
 * [cring_writer] posts a ring's records and publishes its head;
 * [cring_reader] acquires the head, takes, and releases the tail: the
 * control rings as Binding.v's ring_writer and ring_reader, the input
 * ring hart 0's to write (InputRing.v's input_writer).
 *)
Definition cring_writer (channel : cring) : hart :=
  match channel with
  | Ctl r => ring_writer mvp_binding r
  | Inp _ => bi_control mvp_binding
  end.

Definition cring_reader (channel : cring) : hart :=
  match channel with
  | Ctl r => ring_reader mvp_binding r
  | Inp d => dhart d
  end.

(** The record types (enum be_mvp_record_type). *)
(* reads: mvp/src/mvp.h:be_mvp_record_type *)
Definition rec_ready : N := 1.
Definition rec_entered : N := 2.
Definition rec_line : N := 3.
Definition rec_pong : N := 4.
Definition rec_shutdown : N := 5.
Definition rec_fail : N := 6.
Definition rec_ping : N := 7.
Definition rec_ack : N := 8.
Definition rec_denial : N := 9.
Definition rec_mgmt_request : N := 10.
Definition rec_paused : N := 11.
Definition rec_terminated : N := 12.
Definition rec_mgmt_result : N := 13.
Definition rec_pause : N := 14.
Definition rec_terminate : N := 15.
Definition rec_input : N := 16.

(** [ring_types] is a ring's type set (BE_MVP_RECORDS_OUTBOUND, _INBOUND, _INPUT). *)
(* reads: mvp/src/mvp.h:BE_MVP_RECORDS_OUTBOUND *)
(* reads: mvp/src/mvp.h:BE_MVP_RECORDS_INBOUND *)
(* reads: mvp/src/mvp.h:BE_MVP_RECORDS_INPUT *)
Definition ring_types (channel : cring) : list N :=
  match channel with
  | Ctl (OutboundRing _) =>
      [rec_ready; rec_entered; rec_line; rec_pong; rec_shutdown; rec_fail;
       rec_denial; rec_mgmt_request; rec_paused; rec_terminated]
  | Ctl (InboundRing _) =>
      [rec_ping; rec_ack; rec_mgmt_result; rec_pause; rec_terminate]
  | Inp _ => [rec_input]
  end.

Definition type_in (type : N) (types : list N) : bool :=
  existsb (N.eqb type) types.

(** [is_control] holds for the inbound and outbound rings. *)
Definition is_control (channel : cring) : bool :=
  match channel with Ctl _ => true | Inp _ => false end.

(* --------------------------------------------------------------------- *)
(** * Records and their images *)

(**
 * [record] is what a writer posts: a type, its time, and its payload
 * bytes; the header's domain is the ring's. A taken record is its image's
 * decoding.
 *)
(* reads: mvp/src/mvp-ring.h:be_mvp_record *)
Record record : Type := mk_record {
  rec_type : N;
  rec_time : N;
  rec_payload : list N
}.

Definition rec_length (r : record) : N := N.of_nat (length (rec_payload r)).

Fixpoint nlist_eqb (left right : list N) : bool :=
  match left, right with
  | [], [] => true
  | a :: l, b :: r => (a =? b) && nlist_eqb l r
  | _, _ => false
  end.

Definition record_eqb (left right : record) : bool :=
  (rec_type left =? rec_type right) && (rec_time left =? rec_time right) &&
  nlist_eqb (rec_payload left) (rec_payload right).

Lemma nlist_eqb_eq : forall l r, nlist_eqb l r = true <-> l = r.
Proof.
  induction l as [| a l IH]; intros [| b r]; simpl; split; intros H;
    try congruence.
  - apply andb_true_iff in H as [Hab Hlr].
    apply N.eqb_eq in Hab; apply IH in Hlr; subst; reflexivity.
  - injection H as <- <-; rewrite N.eqb_refl; simpl; apply IH; reflexivity.
Qed.

Lemma record_eqb_eq : forall l r, record_eqb l r = true <-> l = r.
Proof.
  intros [t1 m1 p1] [t2 m2 p2]; unfold record_eqb; simpl; split; intros H.
  - apply andb_true_iff in H as [H Hp]; apply andb_true_iff in H as [Ht Hm].
    apply N.eqb_eq in Ht, Hm; apply nlist_eqb_eq in Hp; subst; reflexivity.
  - injection H as <- <- <-; rewrite !N.eqb_refl; simpl.
    apply nlist_eqb_eq; reflexivity.
Qed.

(** [record_bytes]: 16 plus the length rounded up to 8, or 0 above 256. *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_record_bytes *)
Definition record_bytes (length : N) : N :=
  if length <=? 256 then 16 + (length + 7) / 8 * 8 else 0.

(** [le_bytes n v] is v's n little-endian bytes; [le_value] reads them. *)
Fixpoint le_bytes (n : nat) (v : N) : list N :=
  match n with
  | O => []
  | S k => v mod 256 :: le_bytes k (v / 256)
  end.

Fixpoint le_value (bytes : list N) : N :=
  match bytes with
  | [] => 0
  | b :: rest => b + 256 * le_value rest
  end.

(** [words_payload] is be_mvp_ring_post_words's payload: each word's bytes. *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_post_words *)
Definition words_payload (words : list N) : list N :=
  flat_map (le_bytes 8) words.

(** [record_word] is be_mvp_record_word: payload word i, or 0 past it. *)
(* reads: mvp/src/mvp-ring.c:be_mvp_record_word *)
Definition record_word (r : record) (i : nat) : N :=
  if (N.of_nat (8 * i + 8) <=? rec_length r) && (i <? 32)%nat
  then le_value (firstn 8 (skipn (8 * i) (rec_payload r)))
  else 0.

(**
 * [image] is the bytes be_mvp_ring_post writes for a record on a ring of
 * domain [dom]: the header, the payload, and zero padding.
 *)
Definition image (dom : N) (r : record) : list N :=
  let len := rec_length r in
  [rec_type r mod 256; dom mod 256; len mod 256; len / 256 mod 256;
   0; 0; 0; 0] ++
  le_bytes 8 (rec_time r) ++
  map (fun b => b mod 256) (rec_payload r) ++
  repeat 0 (N.to_nat (record_bytes len - 16 - len)).

(* --------------------------------------------------------------------- *)
(** * The words of monitor memory and the objects that type them *)

(** A block's words: published data, its state page's, its saved page and stack. *)
Inductive core_field : Type :=
| CorePhase
| CoreAwaiting
| CoreAnswer
| CoreBy
| CoreExits
| CoreDenials
| CoreRequests.

Inductive block_field : Type :=
| BGen
| BDesc (k : nat)
| BEntry
| BWalked (k : nat)
| BConfig (k : nat)
| BControls
| BEntered
| BCore (f : core_field)
| BSaved
| BStack.

(** A ring's words: the two index lines, the buffer's bytes, and the views. *)
(* reads: mvp/src/mvp-ring.h:be_mvp_ring_index *)
(* reads: mvp/src/mvp-ring.h:be_mvp_ring *)
Inductive ring_field : Type :=
| RHead
| RTail
| RBuf (position : N)
| RWCur
| RWLim
| RWFail
| RWPeak
| RRCur
| RRLim
| RRFail.

(**
 * Hart 0's own words: per domain its track (enum be_mvp_domain_phase) and
 * counters, the gate's verdicts, the management state, the run's
 * completion, the record it took, the input drops, and its drain order, a
 * local of its stack (struct be_mvp_drain).
 *)
(* reads: mvp/src/mvp-hart.h:be_mvp_control *)
(* reads: mvp/src/mvp-hart.h:be_mvp_mgmt_state *)
(* reads: mvp/src/mvp-hart.h:be_mvp_drain *)
Inductive ctl_field : Type :=
| KGate (d : nat)
| KTrack (d : nat)
| KPinged (d : nat)
| KPonged (d : nat)
| KLines (d : nat)
| KDenials (d : nat)
| KRequests (d : nat)
| KAwaiting (d : nat)
| KPending (t : nat)
| KBy (t : nat)
| KFid (t : nat)
| KSeq (t : nat)
| KDone
| KRecord
| KDrops (d : nat)
| KDrainNext
| KDrainIdle
| KDrainVisits.

(** [cword] is one word of the state stage 1 models. *)
Inductive cword : Type :=
| WBlock (d : nat) (f : block_field)
| WRing (channel : cring) (f : ring_field)
| WCtl (f : ctl_field)
| WRoot (d : nat)
| WGuest (d : nat)
| WBinding.

Definition core_eqb (a b : core_field) : bool :=
  match a, b with
  | CorePhase, CorePhase | CoreAwaiting, CoreAwaiting
  | CoreAnswer, CoreAnswer | CoreBy, CoreBy | CoreExits, CoreExits
  | CoreDenials, CoreDenials | CoreRequests, CoreRequests => true
  | _, _ => false
  end.

Definition block_eqb (a b : block_field) : bool :=
  match a, b with
  | BGen, BGen | BEntry, BEntry | BControls, BControls
  | BEntered, BEntered | BSaved, BSaved | BStack, BStack => true
  | BDesc i, BDesc j | BWalked i, BWalked j | BConfig i, BConfig j =>
      Nat.eqb i j
  | BCore f, BCore g => core_eqb f g
  | _, _ => false
  end.

Definition rfield_eqb (a b : ring_field) : bool :=
  match a, b with
  | RHead, RHead | RTail, RTail | RWCur, RWCur | RWLim, RWLim
  | RWFail, RWFail | RWPeak, RWPeak | RRCur, RRCur | RRLim, RRLim
  | RRFail, RRFail => true
  | RBuf p, RBuf q => N.eqb p q
  | _, _ => false
  end.

Definition ctl_eqb (a b : ctl_field) : bool :=
  match a, b with
  | KGate i, KGate j | KTrack i, KTrack j | KPinged i, KPinged j
  | KPonged i, KPonged j | KLines i, KLines j | KDenials i, KDenials j
  | KRequests i, KRequests j | KAwaiting i, KAwaiting j
  | KPending i, KPending j | KBy i, KBy j | KFid i, KFid j
  | KSeq i, KSeq j | KDrops i, KDrops j => Nat.eqb i j
  | KDone, KDone | KRecord, KRecord | KDrainNext, KDrainNext
  | KDrainIdle, KDrainIdle | KDrainVisits, KDrainVisits => true
  | _, _ => false
  end.

(* The field is compared first, so two words of different fields differ by
   computation whatever their domain or ring. *)
Definition cword_eqb (a b : cword) : bool :=
  match a, b with
  | WBlock d f, WBlock e g => block_eqb f g && Nat.eqb d e
  | WRing r f, WRing s g => rfield_eqb f g && cring_eqb r s
  | WCtl f, WCtl g => ctl_eqb f g
  | WRoot d, WRoot e | WGuest d, WGuest e => Nat.eqb d e
  | WBinding, WBinding => true
  | _, _ => false
  end.

Lemma core_eqb_eq : forall a b, core_eqb a b = true <-> a = b.
Proof.
  intros [] []; simpl; split; intros H; congruence.
Qed.

Lemma block_eqb_eq : forall a b, block_eqb a b = true <-> a = b.
Proof.
  intros [| i | | i | i | | | f | |] [| j | | j | j | | | g | |]; simpl;
    split; intros H; try congruence;
    try (apply Nat.eqb_eq in H; subst; reflexivity);
    try (injection H as <-; apply Nat.eqb_refl).
  - apply core_eqb_eq in H; subst; reflexivity.
  - injection H as <-; apply core_eqb_eq; reflexivity.
Qed.

Lemma rfield_eqb_eq : forall a b, rfield_eqb a b = true <-> a = b.
Proof.
  intros [| | p | | | | | | |] [| | q | | | | | | |]; simpl; split;
    intros H; try congruence.
  - apply N.eqb_eq in H; subst; reflexivity.
  - injection H as <-; apply N.eqb_refl.
Qed.

Lemma ctl_eqb_eq : forall a b, ctl_eqb a b = true <-> a = b.
Proof.
  intros [i | i | i | i | i | i | i | i | i | i | i | i | | | i | | |]
    [j | j | j | j | j | j | j | j | j | j | j | j | | | j | | |]; simpl;
    split; intros H; try congruence;
    try (apply Nat.eqb_eq in H; subst; reflexivity);
    try (injection H as <-; apply Nat.eqb_refl).
Qed.

Lemma cword_eqb_eq : forall a b, cword_eqb a b = true <-> a = b.
Proof.
  intros [d f | r f | f | d | d |] [e g | s g | g | e | e |]; simpl; split;
    intros H; try congruence.
  - apply andb_true_iff in H as [Hf Hd].
    apply block_eqb_eq in Hf; apply Nat.eqb_eq in Hd; subst; reflexivity.
  - injection H as <- <-; rewrite Nat.eqb_refl, andb_true_r.
    apply block_eqb_eq; reflexivity.
  - apply andb_true_iff in H as [Hf Hr].
    apply rfield_eqb_eq in Hf; apply cring_eqb_eq in Hr; subst; reflexivity.
  - injection H as <- <-; rewrite cring_eqb_refl, andb_true_r.
    apply rfield_eqb_eq; reflexivity.
  - apply ctl_eqb_eq in H; subst; reflexivity.
  - injection H as <-; apply ctl_eqb_eq; reflexivity.
  - apply Nat.eqb_eq in H; subst; reflexivity.
  - injection H as <-; apply Nat.eqb_refl.
  - apply Nat.eqb_eq in H; subst; reflexivity.
  - injection H as <-; apply Nat.eqb_refl.
Qed.

Lemma cword_eqb_refl : forall a, cword_eqb a a = true.
Proof.
  intros a; apply cword_eqb_eq; reflexivity.
Qed.

Lemma cword_eqb_neq : forall a b, a <> b -> cword_eqb a b = false.
Proof.
  intros a b Hne.
  destruct (cword_eqb a b) eqn:H; [apply cword_eqb_eq in H; contradiction |].
  reflexivity.
Qed.

(**
 * [new_object] is stage 1's objects that Binding.v leaves without words
 * (its ring objects and the state page have no extent there): a ring's
 * buffer bytes, and the state page's SBI core words split into the phase
 * group (the phase, the management wait, the order's requester) and the
 * counters. [enclosing] is the Binding.v object each lies inside.
 *)
Inductive new_object : Type :=
| RingBytes (channel : ring)
| StatePhase (domain : nat)
| StateCounters (domain : nat).

Definition enclosing (object : new_object) : hart_object :=
  match object with
  | RingBytes r => RingRecords r
  | StatePhase d | StateCounters d => StateCore d
  end.

(**
 * [cobject] is the object types of stage 1's words: InputRing.v's one
 * object set (Binding.v's objects, the input path's, and domain memory)
 * and the new objects.
 *)
Inductive cobject : Type :=
| CSys (object : system_object)
| CNew (object : new_object).

Definition bobj (object : hart_object) : cobject := CSys (BindingObject object).
Definition iobj (object : input_object) : cobject := CSys (InputObject object).

(**
 * [view_object] is where one side's view of a ring lies: hart 0's in its
 * own data (be_mvp_inbound, be_mvp_outbound) or its input routing
 * (be_mvp_input_rings), a domain hart's in its hart page's ring views or,
 * for the input ring, its stage (struct be_mvp_hart_page).
 *)
(* reads: mvp/src/mvp-platform.h:be_mvp_hart_page *)
Definition view_object (channel : cring) (writer_side : bool) : cobject :=
  match channel with
  | Ctl (InboundRing d) =>
      if writer_side then bobj ControlData else bobj (HartRingViews d)
  | Ctl (OutboundRing d) =>
      if writer_side then bobj (HartRingViews d) else bobj ControlData
  | Inp d =>
      if writer_side then iobj InputRouting else iobj (InputStage d)
  end.

(** [word_object] types each word. *)
Definition word_object (w : cword) : cobject :=
  match w with
  | WBlock d f =>
      match f with
      | BGen | BDesc _ => bobj (BlockDescriptor d)
      | BEntry => bobj (BlockEntryFrame d)
      | BWalked _ => bobj (BlockWalked d)
      | BConfig _ => bobj (StateConfiguration d)
      | BControls => bobj (StateControls d)
      | BEntered => bobj (StateEntered d)
      | BCore (CorePhase | CoreAwaiting | CoreAnswer | CoreBy) =>
          CNew (StatePhase d)
      | BCore (CoreExits | CoreDenials | CoreRequests) =>
          CNew (StateCounters d)
      | BSaved => bobj (BlockSaved d)
      | BStack => bobj (BlockStack d)
      end
  | WRing (Ctl r) RHead => bobj (RingHead r)
  | WRing (Ctl r) RTail => bobj (RingTail r)
  | WRing (Ctl r) (RBuf _) => CNew (RingBytes r)
  | WRing (Inp d) RHead => iobj (InputHead d)
  | WRing (Inp d) RTail => iobj (InputTail d)
  | WRing (Inp d) (RBuf _) => iobj (InputRecords d)
  | WRing channel (RWCur | RWLim | RWFail | RWPeak) => view_object channel true
  | WRing channel (RRCur | RRLim | RRFail) => view_object channel false
  | WCtl (KDrainNext | KDrainIdle | KDrainVisits) => bobj ControlStack
  | WCtl _ => bobj ControlData
  | WRoot d => bobj (DomainRoot d)
  | WGuest d => CSys (DomainMemory d)
  | WBinding => bobj BindingTable
  end.

(* --------------------------------------------------------------------- *)
(** * Memory *)

(** [mem] is monitor memory and domain memory, one N per word. *)
Definition mem : Type := cword -> N.

Definition upd (m : mem) (w : cword) (v : N) : mem :=
  fun w' => if cword_eqb w' w then v else m w'.

Lemma upd_same : forall m w v, upd m w v w = v.
Proof.
  intros m w v; unfold upd; rewrite cword_eqb_refl; reflexivity.
Qed.

Lemma upd_other : forall m w v w', w' <> w -> upd m w v w' = m w'.
Proof.
  intros m w v w' Hne; unfold upd; rewrite cword_eqb_neq by exact Hne.
  reflexivity.
Qed.

(**
 * [write_cells m channel cap base bytes] is m with [bytes] stored at the
 * ring's buffer positions base, base + 1, ..., each masked by cap - 1 (a
 * position is a count modulo the capacity): the C's store_le loop.
 *)
(* reads: mvp/src/mvp-ring.c:store_le *)
Definition write_cells (m : mem) (channel : cring) (cap base : N)
    (bytes : list N) : mem :=
  fun w =>
    match w with
    | WRing channel' (RBuf p) =>
        if cring_eqb channel' channel && (p <? cap) then
          let offset := (p + cap - base mod cap) mod cap in
          if offset <? N.of_nat (length bytes)
          then nth (N.to_nat offset) bytes 0
          else m w
        else m w
    | _ => m w
    end.

(** [cell] reads one buffer byte at count [base + i]; [cells] reads n. *)
(* reads: mvp/src/mvp-ring.c:load_le *)
Definition cell (m : mem) (channel : cring) (cap base i : N) : N :=
  m (WRing channel (RBuf ((base + i) mod cap))).

Definition cells (m : mem) (channel : cring) (cap base : N) (n : nat)
    : list N :=
  map (fun i => cell m channel cap base (N.of_nat i)) (seq 0 n).

(* --------------------------------------------------------------------- *)
(** * The ring operations (mvp-ring.c), on a ring's words *)

Definition rd (m : mem) (channel : cring) (f : ring_field) : N :=
  m (WRing channel f).

(** [refuse_writer] and [refuse_reader] fail a view: it stays failed. *)
(* reads: mvp/src/mvp-ring.c:refuse *)
(* reads: mvp/src/mvp-ring.c:usable *)
Definition refuse_writer (m : mem) (channel : cring) : mem :=
  upd m (WRing channel RWFail) 1.

Definition refuse_reader (m : mem) (channel : cring) : mem :=
  upd m (WRing channel RRFail) 1.

Definition failed_view (v : N) : bool := negb (v =? 0).

(**
 * [ring_post]: the writer's post (be_mvp_ring_post): a type outside the
 * ring's set or a payload above 256 bytes, a malformed tail (unaligned or
 * more than a capacity behind the published head), or no room fails the
 * view and writes no buffer byte; else the record's image is written past
 * the cursor, the cursor advances by its size, and the peak follows.
 *)
Definition ring_post (cap : N) (channel : cring) (m : mem) (r : record)
    : bool * mem :=
  if failed_view (rd m channel RWFail) then (false, refuse_writer m channel)
  else if negb (type_in (rec_type r) (ring_types channel)) ||
          (256 <? rec_length r)
  then (false, refuse_writer m channel)
  else
    let tail := rd m channel RTail in
    let cursor := rd m channel RWCur in
    if negb (tail mod 8 =? 0) || (cap <? sub64 (rd m channel RWLim) tail)
    then (false, refuse_writer m channel)
    else
      let used := sub64 cursor tail in
      let size := record_bytes (rec_length r) in
      if (cap <? used) || (cap - used <? size)
      then (false, refuse_writer m channel)
      else
        (true,
         upd (upd (write_cells m channel cap cursor
                     (image (N.of_nat (ring_domain channel)) r))
                (WRing channel RWCur) (add64 cursor size))
           (WRing channel RWPeak)
           (N.max (rd m channel RWPeak) (used + size))).

(** [ring_publish] (be_mvp_ring_publish): the head and the limit := cursor. *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_publish *)
Definition ring_publish (channel : cring) (m : mem) : bool * mem :=
  if failed_view (rd m channel RWFail) then (false, refuse_writer m channel)
  else
    let cursor := rd m channel RWCur in
    (true, upd (upd m (WRing channel RHead) cursor) (WRing channel RWLim)
             cursor).

(**
 * [ring_acquire] (be_mvp_ring_acquire): the head, checked aligned, at most
 * a capacity past the released tail and not behind the cursor, becomes the
 * reader's limit; the answer is the bytes available.
 *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_acquire *)
Definition ring_acquire (cap : N) (channel : cring) (m : mem) : N * mem :=
  if failed_view (rd m channel RRFail) then (0, refuse_reader m channel)
  else
    let head := rd m channel RHead in
    let released := rd m channel RTail in
    let cursor := rd m channel RRCur in
    if negb (head mod 8 =? 0) || (cap <? sub64 head released) ||
       (sub64 head released <? sub64 cursor released)
    then (0, refuse_reader m channel)
    else (sub64 head cursor, upd m (WRing channel RRLim) head).

(** [take_result] is one take's outcome (enum be_mvp_ring_status). *)
Inductive take_result : Type :=
| TakeInvalid
| TakeEmpty
| TakeRecord (r : record) (img : list N).

Definition all_zero (bytes : list N) : bool := forallb (N.eqb 0) bytes.

(**
 * [ring_take] (be_mvp_ring_take): at the cursor, below the acquired limit,
 * a header whose type is the ring's, whose domain is the ring's, whose
 * reserved bytes and padding are zero, and whose record ends at or before
 * the limit is decoded and the cursor advances past it; anything else
 * fails the view. The image is the bytes it read, in order.
 *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_take *)
Definition ring_take (cap : N) (channel : cring) (m : mem)
    : take_result * mem :=
  if failed_view (rd m channel RRFail) then (TakeInvalid, refuse_reader m channel)
  else
    let cursor := rd m channel RRCur in
    let limit := rd m channel RRLim in
    if cursor =? limit then (TakeEmpty, m)
    else
      let available := sub64 limit cursor in
      if available <? 16 then (TakeInvalid, refuse_reader m channel)
      else
        let at_ i := cell m channel cap cursor i in
        let type := at_ 0 in
        let len := at_ 2 + 256 * at_ 3 in
        let size := record_bytes len in
        if negb (type_in type (ring_types channel)) ||
           negb (at_ 1 =? N.of_nat (ring_domain channel)) ||
           negb (all_zero [at_ 4; at_ 5; at_ 6; at_ 7]) ||
           (size =? 0) || (available <? size)
        then (TakeInvalid, refuse_reader m channel)
        else
          let body := cells m channel cap (cursor + 16) (N.to_nat (size - 16)) in
          if negb (all_zero (skipn (N.to_nat len) body))
          then (TakeInvalid, refuse_reader m channel)
          else
            (TakeRecord
               (mk_record type (le_value (cells m channel cap (cursor + 8) 8))
                  (firstn (N.to_nat len) body))
               (cells m channel cap cursor (N.to_nat size)),
             upd m (WRing channel RRCur) (add64 cursor size)).

(** [ring_release] (be_mvp_ring_release): the tail := the reader's cursor. *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_release *)
Definition ring_release (channel : cring) (m : mem) : bool * mem :=
  if failed_view (rd m channel RRFail) then (false, refuse_reader m channel)
  else (true, upd m (WRing channel RTail) (rd m channel RRCur)).

(**
 * [ring_room] (be_mvp_ring_room): the payload bytes the next record can
 * carry, at most 256, a multiple of 8 below it, 0 when none fits; a
 * malformed tail fails the view; it posts nothing.
 *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_room *)
Definition ring_room (cap : N) (channel : cring) (m : mem) : N * mem :=
  if failed_view (rd m channel RWFail) then (0, refuse_writer m channel)
  else
    let tail := rd m channel RTail in
    let cursor := rd m channel RWCur in
    if negb (tail mod 8 =? 0) || (cap <? sub64 (rd m channel RWLim) tail) ||
       (cap <? sub64 cursor tail)
    then (0, refuse_writer m channel)
    else
      let free := cap - sub64 cursor tail in
      (if free <=? 16 then 0
       else if free - 16 <? 256 then free - 16 - (free - 16) mod 8 else 256,
       m).

(**
 * [ring_init] is hart 0's set-up of one ring before the barrier
 * (ring_views: be_mvp_ring_reset, then be_mvp_ring_init for both views):
 * both indices zero, both views at zero and not failed.
 *)
(* reads: mvp/src/mvp-runtime.c:ring_views *)
(* reads: mvp/src/mvp-ring.c:be_mvp_ring_reset *)
Definition ring_init (channel : cring) (m : mem) : mem :=
  fold_left (fun m' f => upd m' (WRing channel f) 0)
    [RHead; RTail; RWCur; RWLim; RWFail; RWPeak; RRCur; RRLim; RRFail] m.

(* --------------------------------------------------------------------- *)
(** * The denial decision (Leaf A, be_mvp_denial_decide) *)

(** A walked window and its root's walked page leaves (struct
    be_mvp_gstage_map, struct be_mvp_gstage_leaves). *)
(* reads: mvp/src/mvp-gstage.h:be_mvp_gstage_leaf *)
(* reads: mvp/src/mvp-gstage.h:be_mvp_gstage_leaves *)
Record leaf : Type := mk_leaf {
  leaf_gpa : N;
  leaf_bytes : N;
  leaf_pte : N
}.

(* reads: mvp/src/mvp-gstage.h:be_mvp_gstage_map *)
Record walked : Type := mk_walked {
  map_gpa : N;
  map_size : N;
  map_leaves : list leaf
}.

(**
 * [exit_rec] is what the vector saves on an exit (struct be_mvp_exit) and
 * the ecall's registers: a7 the extension, a6 the function, a0 and a1 its
 * arguments; [ex_line] is a console line the exit completes, if any.
 *)
(* reads: mvp/src/mvp.h:be_mvp_exit *)
Record exit_rec : Type := mk_exit {
  ex_scause : N;
  ex_hstatus : N;
  ex_htval : N;
  ex_htinst : N;
  ex_stval : N;
  ex_sepc : N;
  ex_vsstatus : N;
  ex_vstvec : N;
  ex_time : N;
  ex_a7 : N;
  ex_a6 : N;
  ex_a0 : N;
  ex_a1 : N;
  ex_line : list N
}.

(** The causes, the status bits, and the opcodes the entry names. *)
(* reads: mvp/src/mvp.h:BE_MVP_SCAUSE_SUPERVISOR_SOFTWARE *)
Definition scause_ssi : N := 2 ^ 63 + 1.
Definition scause_ecall : N := 10.
Definition scause_fetch_gpf : N := 20.
Definition scause_load_gpf : N := 21.
Definition scause_store_gpf : N := 23.
Definition hstatus_gva_bit : N := 6.
Definition hstatus_spv_bit : N := 7.
Definition hstatus_spvp_bit : N := 8.
Definition vsstatus_sie_bit : N := 1.
Definition vsstatus_spie_bit : N := 5.
Definition vsstatus_spp_bit : N := 8.
Definition pte_w_bit : N := 2.
(* reads: mvp/src/mvp.h:BE_MVP_HTVAL_LIMIT *)
Definition htval_limit : N := 2 ^ 39.
(* reads: mvp/src/mvp.h:BE_MVP_HTINST_LIMIT *)
Definition htinst_limit : N := 2 ^ 32.
Definition opcode_load : N := 0.
Definition opcode_store : N := 8.
Definition opcode_amo : N := 11.

Definition is_gpf (scause : N) : bool :=
  (scause =? scause_fetch_gpf) || (scause =? scause_load_gpf) ||
  (scause =? scause_store_gpf).

(** [access_fault]: the access fault a guest-page fault becomes, or 0. *)
(* reads: mvp/src/mvp-sbi.c:access_fault *)
Definition access_fault (scause : N) : N :=
  if scause =? scause_fetch_gpf then 1
  else if scause =? scause_load_gpf then 5
  else if scause =? scause_store_gpf then 7
  else 0.

(** [htinst_accepted]: zero, or a transformed load (21) or store or AMO (23). *)
(* reads: mvp/src/mvp-sbi.c:htinst_accepted *)
Definition htinst_accepted (scause htinst : N) : bool :=
  let opcode := N.land (N.shiftr htinst 2) 31 in
  if htinst =? 0 then true
  else if (htinst_limit <=? htinst) || negb (N.testbit htinst 0) then false
  else if scause =? scause_load_gpf then opcode =? opcode_load
  else if scause =? scause_store_gpf then
    (opcode =? opcode_store) || (opcode =? opcode_amo)
  else false.

(* reads: mvp/src/mvp-sbi.c:inside *)
Definition inside (address base bytes : N) : bool :=
  negb (bytes =? 0) && (base <=? address) && (address - base <? bytes).

(** [leaf_at]: the first of the three leaves that holds the GPA. *)
(* reads: mvp/src/mvp-sbi.c:leaf_at *)
(* reads: mvp/src/mvp-layout.h:BE_MVP_PAGES_MAX *)
Definition leaf_at (leaves : list leaf) (gpa : N) : option leaf :=
  find (fun l => inside gpa (leaf_gpa l) (leaf_bytes l))
    (firstn (N.to_nat be_mvp_pages_max) leaves).

Definition exit_gpa (e : exit_rec) : N :=
  N.lor (N.shiftl (ex_htval e) 2) (N.land (ex_stval e) 3).

(** [denial] is one accepted denial: what is logged and injected. *)
(* reads: mvp/src/mvp.h:be_mvp_denial *)
Record denial : Type := mk_denial {
  dn_cause : N;
  dn_kind : N;
  dn_gpa : N;
  dn_htval : N;
  dn_htinst : N;
  dn_stval : N;
  dn_sepc : N;
  dn_vsstatus : N;
  dn_vstvec : N;
  dn_time : N;
  dn_inject_vscause : N;
  dn_inject_vstval : N;
  dn_inject_vsepc : N;
  dn_inject_vsstatus : N;
  dn_resume_pc : N
}.

Definition inject_vsstatus (e : exit_rec) : N :=
  N.lor
    (N.lor
       (N.ldiff (ex_vsstatus e)
          (2 ^ vsstatus_spp_bit + 2 ^ vsstatus_spie_bit +
           2 ^ vsstatus_sie_bit))
       (if N.testbit (ex_hstatus e) hstatus_spvp_bit
        then 2 ^ vsstatus_spp_bit else 0))
    (if N.testbit (ex_vsstatus e) vsstatus_sie_bit
     then 2 ^ vsstatus_spie_bit else 0).

(**
 * [denial_decide] is be_mvp_denial_decide: an image that accepts
 * denials, a window, a guest-page fault from VU mode (SPV 1, SPVP 0, GVA
 * 1), htval below 2^39, an accepted htinst, a Direct or Vectored vstvec,
 * and a GPA outside the window that no leaf holds (unmapped), or a store
 * at a leaf without W (read-only); the result carries the fields and the
 * values to inject.
 *)
(* reads: mvp/src/mvp-sbi.c:be_mvp_denial_decide *)
Definition denial_decide (accept : bool) (w : walked) (e : exit_rec)
    : option denial :=
  let vscause := access_fault (ex_scause e) in
  let gpa := exit_gpa e in
  if negb accept || (map_size w =? 0) then None
  else if (vscause =? 0) || negb (N.testbit (ex_hstatus e) hstatus_spv_bit) ||
          N.testbit (ex_hstatus e) hstatus_spvp_bit ||
          negb (N.testbit (ex_hstatus e) hstatus_gva_bit) ||
          (htval_limit <=? ex_htval e) ||
          negb (htinst_accepted (ex_scause e) (ex_htinst e)) ||
          (1 <? N.land (ex_vstvec e) 3)
  then None
  else if inside gpa (map_gpa w) (map_size w) then None
  else
    let kind :=
      match leaf_at (map_leaves w) gpa with
      | None => Some 0
      | Some l =>
          if (ex_scause e =? scause_store_gpf) &&
             negb (N.testbit (leaf_pte l) pte_w_bit)
          then Some 1 else None
      end in
    match kind with
    | None => None
    | Some k =>
        Some (mk_denial (ex_scause e) k gpa (ex_htval e) (ex_htinst e)
                (ex_stval e) (ex_sepc e) (ex_vsstatus e) (ex_vstvec e)
                (ex_time e) vscause (ex_stval e) (ex_sepc e)
                (inject_vsstatus e) (N.ldiff (ex_vstvec e) 3))
    end.

(* --------------------------------------------------------------------- *)
(** * The management decision (be_mvp_mgmt_decide) *)

(* reads: mvp/src/mvp.h:be_mvp_mgmt_grant *)
Record mgmt_grant : Type := mk_mgmt_grant {
  mg_from : N;
  mg_to : N;
  mg_perms : N
}.

(** [target_state] is a request's target as hart 0 sees it. *)
(* reads: mvp/src/mvp.h:be_mvp_target_state *)
Inductive target_state : Type :=
| TRunning
| TPaused
| TTerminated
| TShutdown
| TPending.

(** The SBI results, as the 64-bit words the records carry. *)
(* reads: mvp/src/mvp.h:BE_MVP_SBI_ERR_DENIED *)
Definition sbi_success : N := 0.
Definition sbi_not_supported : N := word_modulus - 2.
Definition sbi_invalid_param : N := word_modulus - 3.
Definition sbi_denied : N := word_modulus - 4.
Definition sbi_invalid_state : N := word_modulus - 10.
(* reads: mvp/src/mvp.h:BE_MVP_MGMT_DELIVER *)
Definition mgmt_deliver : N := 1.
Definition fid_pause : N := 0.
Definition fid_terminate : N := 1.

Definition granted (grants : list mgmt_grant) (requester fid target : N)
    : bool :=
  let perm := if fid =? fid_pause then 1 else 2 in
  (N.of_nat (length grants) <=? 4) && (requester <? 2) &&
  existsb (fun g => (mg_from g =? requester) && (mg_to g =? target) &&
                    negb (N.land (mg_perms g) perm =? 0)) grants.

(**
 * [mgmt_decide] is be_mvp_mgmt_decide: a function other than pause and
 * terminate is not supported; an unknown target is INVALID_PARAM; a pair
 * no grant names, the requester itself included, is DENIED; a target not
 * running, but for a terminate of a paused one, is INVALID_STATE; else the
 * request is delivered.
 *)
(* reads: mvp/src/mvp-sbi.c:be_mvp_mgmt_decide *)
Definition mgmt_decide (grants : list mgmt_grant) (requester fid target : N)
    (state : target_state) : N :=
  if negb ((fid =? fid_pause) || (fid =? fid_terminate)) then sbi_not_supported
  else if 2 <=? target then sbi_invalid_param
  else if negb (granted grants requester fid target) then sbi_denied
  else
    match state with
    | TRunning => mgmt_deliver
    | TPaused => if fid =? fid_terminate then mgmt_deliver else sbi_invalid_state
    | _ => sbi_invalid_state
    end.

(* --------------------------------------------------------------------- *)
(** * The configuration a run is sealed with *)

(**
 * [config] is what an image fixes before the barrier: each ring's
 * capacity, each domain's walked window and leaves (its derived root's),
 * whether the image accepts denials and the management extension, the
 * sealed management grants, which domains the configuration grants console
 * input, the exit ceiling, and the measurement log (M9): the bytes placed
 * in each window, which the domain's launch records measure; the image's
 * expected launch register for each domain; each domain's gate, its
 * predicate on the two; and whether the log takes every record and
 * closes with the image's expected count (M9's content: any predicate per
 * domain and any boolean here). Before M9 one domain, the measured one,
 * had a gate, on one expected value; M9 gates every domain on its own
 * launch register and adds the close, so the gate and the expected value
 * are per domain here and the close is new; the record's other fields are
 * as at M8's target commit.
 *)
(* reads: mvp/src/mvp-runtime.c:be_mvp_log_constants *)
Record config : Type := mk_config {
  cfg_capacity : cring -> N;
  cfg_root : nat -> walked;
  cfg_accept_denial : bool;
  cfg_accept_mgmt : bool;
  cfg_grants : list mgmt_grant;
  cfg_input : nat -> bool;
  cfg_ceiling : N;
  cfg_placed : nat -> N;
  cfg_expected : nat -> N;
  cfg_gate : nat -> N -> N -> bool;
  cfg_log_closes : bool
}.

Definition config_ok (c : config) : Prop :=
  forall channel, cap_okb (cfg_capacity c channel) = true.

Definition bool_word (b : bool) : N := if b then 1 else 0.

(** [walked_words] lays a walked root out as eleven words. *)
Definition leaf_words (l : leaf) : list N := [leaf_gpa l; leaf_bytes l; leaf_pte l].

Definition walked_words (w : walked) : list N :=
  [map_gpa w; map_size w] ++
  flat_map leaf_words (firstn 3 (map_leaves w ++ repeat (mk_leaf 0 0 0) 3)).

(** [read_walked] reads them back from a block. *)
Definition read_walked (m : mem) (d : nat) : walked :=
  let at_ k := m (WBlock d (BWalked k)) in
  mk_walked (at_ 0%nat) (at_ 1%nat)
    [mk_leaf (at_ 2%nat) (at_ 3%nat) (at_ 4%nat);
     mk_leaf (at_ 5%nat) (at_ 6%nat) (at_ 7%nat);
     mk_leaf (at_ 8%nat) (at_ 9%nat) (at_ 10%nat)].

(** The SBI core's phases (enum be_mvp_phase). *)
(* reads: mvp/src/mvp.h:be_mvp_phase *)
Definition phase_running : N := 0.
Definition phase_stopped : N := 1.
Definition phase_failed : N := 2.
Definition phase_paused : N := 3.
Definition phase_terminated : N := 4.

(** Hart 0's view of a domain (enum be_mvp_domain_phase). *)
(* reads: mvp/src/mvp-hart.h:be_mvp_domain_phase *)
Definition track_none : N := 0.
Definition track_started : N := 1.
Definition track_ready : N := 2.
Definition track_entered : N := 3.
Definition track_shutdown : N := 4.
Definition track_failed : N := 5.
Definition track_paused : N := 6.
Definition track_terminated : N := 7.

(* --------------------------------------------------------------------- *)
(** * Records the harts post *)

(* reads: mvp/src/mvp-sbi.c:be_mvp_post_ready *)
Definition ready_record : record :=
  mk_record rec_ready 0 (words_payload (repeat 0 8)).

(* reads: mvp/src/mvp-sbi.c:be_mvp_post_entered *)
Definition entered_record (entry : N) : record :=
  mk_record rec_entered 0 (words_payload [entry; 0; 0]).

Definition line_record (bytes : list N) : record :=
  mk_record rec_line 0 bytes.

(* reads: mvp/src/mvp-sbi.c:be_mvp_post_denial *)
Definition denial_record (seq : N) (dn : denial) : record :=
  mk_record rec_denial 0
    (words_payload
       [seq; dn_cause dn; dn_kind dn; dn_gpa dn; dn_htval dn; dn_htinst dn;
        dn_stval dn; dn_sepc dn; dn_vsstatus dn; dn_vstvec dn;
        dn_inject_vscause dn; dn_time dn]).

(* reads: mvp/src/mvp-sbi.c:be_mvp_post_mgmt_request *)
Definition request_record (fid target seq : N) : record :=
  mk_record rec_mgmt_request 0 (words_payload [fid; target; seq]).

(* reads: mvp/src/mvp-sbi.c:be_mvp_post_shutdown *)
Definition shutdown_record (exits denials requests : N) : record :=
  mk_record rec_shutdown 0 (words_payload [exits; denials; requests]).

(* reads: mvp/src/mvp-sbi.c:be_mvp_post_fail *)
Definition fail_record : record :=
  mk_record rec_fail 0 (words_payload [1]).

Definition pong_record (sent : N) : record :=
  mk_record rec_pong 0 (words_payload [sent; 0; 0]).

Definition transition_record (type exits requester : N) : record :=
  mk_record type 0 (words_payload [exits; requester]).

Definition ping_record : record := mk_record rec_ping 0 [].
Definition ack_record : record := mk_record rec_ack 0 [].

(* reads: mvp/src/mvp-runtime.c:answer *)
Definition result_record (code seq : N) : record :=
  mk_record rec_mgmt_result 0 (words_payload [code; seq]).

(* reads: mvp/src/mvp-runtime.c:deliver *)
Definition order_record (fid requester : N) : record :=
  mk_record (if fid =? fid_pause then rec_pause else rec_terminate) 0
    (words_payload [requester]).

Definition input_record (bytes : list N) : record :=
  mk_record rec_input 0 bytes.

(* --------------------------------------------------------------------- *)
(** * The harts' control flow and stage 1's history *)

(** [act] is a ring action a hart has queued, in program order. *)
Inductive act : Type :=
| APost (channel : cring) (r : record)
| APublish (channel : cring).

(** Where a domain hart reads its inbound ring from. *)
Inductive serve_kind : Type :=
| FromGuest (* an IPI exit (ipi) *)
| FromWait  (* its management call's wait in HS (mgmt_call, wait_serve) *)
| FromPark  (* a paused or terminated park's wake (parked) *)
| FromFail. (* its FAIL's wait for hart 0's ACK (acknowledged) *)

(** [serve_phase]: acquire, then takes (one taken yet, an answer posted), then release. *)
Inductive serve_phase : Type :=
| SAcquire
| STake (taken posted : bool)
| SRelease (posted : bool).

Inductive input_phase : Type :=
| IAcquire
| ITake
| IRelease.

(** A domain hart's program position. *)
(* reads: mvp/src/mvp-hartmain.c:be_mvp_hart_main *)
(* reads: mvp/src/mvp-hartmain.c:be_mvp_dispatch *)
Inductive dmode : Type :=
| DOff
| DStart
| DEarlyPark
| DEntering
| DGuest
| DServe (k : serve_kind) (p : serve_phase)
| DInput (p : input_phase)
| DWaitMgmt
| DParking
| DParked
| DShut
| DFailing
| DFailWait
| DHalted.

(** Hart 0's program position. *)
(* reads: mvp/src/mvp-runtime.c:be_mvp_runtime_main *)
(* reads: mvp/src/mvp-runtime.c:control_loop *)
Inductive h0mode : Type :=
| H0Boot
| H0Publish (d : nat)
| H0Start (d : nat)
| H0Idle
| H0Visit
| H0Take (d : nat)
| H0Release (d : nat) (taken : option record)
| H0Handle (d : nat) (r : record)
| H0Input (d : nat) (bytes : list N) (posted : option N)
| H0Done
| H0Ending
| H0Ended
| H0Failed.

(** What a domain hart's exit decides (be_mvp_handle_exit and the dispatch). *)
Inductive exit_action : Type :=
| XFail
| XResume
| XLine (bytes : list N)
| XIpi
| XDeny (dn : denial)
| XMgmt (fid target : N)
| XShutdown
| XInput.

(**
 * [gev] is stage 1's history: each step's observable outcome, appended in
 * trace order. It is the model's record of the trace, not monitor memory.
 *)
Inductive gev : Type :=
| GPost (channel : cring) (img : list N)
| GRefused (channel : cring)
| GPublish (channel : cring) (head : N)
| GAcquire (channel : cring) (available : N)
| GTake (channel : cring) (img : list N)
| GRelease (channel : cring) (tail : N)
| GRoom (channel : cring) (answer : N)
| GDrop (channel : cring) (n : N)
| GGate (d : nat) (verdict : bool)
| GPublished (d : nat)
| GStart (d : nat)
| GReady (d : nat) (generation : N)
| GEnter (d : nat)
| GExit (d : nat) (e : exit_rec) (a : exit_action)
| GDecide (requester : nat) (fid target seq : N) (state : target_state)
    (outcome : N)
| GSettle (target requester : nat) (seq code : N)
| GPark (d : nat)
| GFail (d : nat)
| GEnd (done : bool).

Record cstate : Type := mk_cstate {
  cs_mem : mem;
  cs_h0 : h0mode;
  cs_h0todo : list act;
  cs_dmode : nat -> dmode;
  cs_dtodo : nat -> list act;
  cs_log : list gev
}.

(* --------------------------------------------------------------------- *)
(** * The steps *)

(**
 * [cstep] is the specification's section 2 steps, each with what the
 * hardware supplies: prepare, publish(d), start(d), ready(d), enter(d),
 * post(r, rec), publish_ring(r), acquire(r), take(r), release(r), room(r),
 * drop(r, n), drain (a round-robin pass's start; its visits are acquire,
 * take, and release, and a drained record's step [CStepRecord d]),
 * exit(d, e), decide_mgmt (CDecideMgmt d, for the requests and the
 * transitions they cause), park(d), fail(d), hart 0's input poll, and end.
 *)
Inductive cstep : Type :=
| CPrepare
| CPublishBlock (d : nat)
| CStart (d : nat)
| CReady (d : nat)
| CEnter (d : nat)
| CPost (channel : cring) (r : record)
| CPublish (channel : cring)
| CAcquire (channel : cring)
| CTake (channel : cring)
| CRelease (channel : cring)
| CRoom (channel : cring)
| CDrop (channel : cring) (n : N)
| CDrain
| CStepRecord (d : nat)
| CExit (d : nat) (e : exit_rec)
| CDecideMgmt (d : nat)
| CPark (d : nat)
| CFail (d : nat)
| CPoll (d : nat) (bytes : list N)
| CRunEnd.

(** [chart] is the hart that takes a step. *)
Definition chart (st : cstep) : hart :=
  match st with
  | CPrepare | CPublishBlock _ | CStart _ | CDrain | CStepRecord _
  | CDecideMgmt _ | CPoll _ _ | CRunEnd | CDrop _ _ => bi_control mvp_binding
  | CReady d | CEnter d | CExit d _ | CPark d | CFail d => dhart d
  | CPost channel _ | CPublish channel | CRoom channel => cring_writer channel
  | CAcquire channel | CTake channel | CRelease channel => cring_reader channel
  end.

(** [cphase]: preparation and publication come before the barrier. *)
Definition cphase (st : cstep) : barrier_phase :=
  match st with
  | CPrepare | CPublishBlock _ => BeforeBarrier
  | _ => AfterBarrier
  end.

(**
 * [refines] is the Binding.v transition each step is part of: a post the
 * one its record belongs to; a publish, acquire, take, or release on a
 * control ring one whose footprint names the index it writes (the
 * transition of the record it carries shares those writes); a step on the
 * input ring hart 0's Wake or the domain hart's ExitRecord, InputRing.v's
 * reading of the input path.
 *)
Definition refines_post (channel : cring) (r : record) : transition :=
  match channel with
  | Ctl (OutboundRing d) =>
      let t := rec_type r in
      if t =? rec_ready then Ready d
      else if t =? rec_entered then Entered d
      else if t =? rec_pong then Pong d
      else if t =? rec_mgmt_request then Request d
      else if t =? rec_paused then Pause d
      else if t =? rec_terminated then Terminate d
      else if t =? rec_shutdown then Shutdown d
      else if t =? rec_fail then FailRecord d
      else ExitRecord d
  | Ctl (InboundRing d) =>
      let t := rec_type r in
      if (t =? rec_pause) || (t =? rec_terminate) then DecideDeliver d
      else if t =? rec_mgmt_result then Answer d
      else if t =? rec_ack then Acknowledge d
      else Ping d
  | Inp _ => Wake
  end.

Definition refines (st : cstep) : transition :=
  match st with
  | CPrepare => Prepare
  | CPublishBlock _ => Publish
  | CStart d => Start d
  | CReady d => Ready d
  | CEnter d => Entered d
  | CPost channel r => refines_post channel r
  | CPublish (Ctl (OutboundRing d)) => ExitRecord d
  | CPublish (Ctl (InboundRing d)) => Ping d
  | CPublish (Inp _) | CRoom _ | CDrop _ _ | CDrain | CPoll _ _ => Wake
  | CAcquire (Ctl (OutboundRing d)) | CTake (Ctl (OutboundRing d))
  | CRelease (Ctl (OutboundRing d)) | CStepRecord d => Drain d
  | CAcquire (Ctl (InboundRing d)) | CTake (Ctl (InboundRing d))
  | CRelease (Ctl (InboundRing d)) => Pong d
  | CAcquire (Inp d) | CTake (Inp d) | CRelease (Inp d) | CExit d _ =>
      ExitRecord d
  | CDecideMgmt d => DecideDeliver d
  | CPark d => Park d
  | CFail d => FailRecord d
  | CRunEnd => RunEnd
  end.

(** [refines_input] is the InputRing.v input step a step is part of. *)
Definition refines_input (st : cstep) : option input_transition :=
  match st with
  | CPoll _ _ | CRoom (Inp _) | CDrop (Inp _) _ => Some Poll
  | CPost (Inp d) _ | CPublish (Inp d) => Some (Flush d)
  | CAcquire (Inp d) | CTake (Inp d) | CRelease (Inp d) => Some (Serve d)
  | _ => None
  end.

(**
 * [cwrites st w] is the step's write set, a superset of the words its
 * semantics changes (ConcreteBridge.v proves it): each step writes its
 * hart's stack word and the words named here.
 *)
Definition is_view_field (writer_side : bool) (f : ring_field) : bool :=
  match f with
  | RWCur | RWLim | RWFail | RWPeak => writer_side
  | RRCur | RRLim | RRFail => negb writer_side
  | _ => false
  end.

Definition stack_word (h : hart) : cword :=
  match h with
  | O => WCtl KDrainNext
  | S d => WBlock d BStack
  end.

Definition hart0_own (w : cword) : bool :=
  match w with
  | WCtl _ => true
  | _ => false
  end.

Definition block_published (f : block_field) : bool :=
  match f with
  | BGen | BDesc _ | BEntry | BWalked _ | BConfig _ => true
  | _ => false
  end.

Definition own_ring_word (d : nat) (w : cword) : bool :=
  match w with
  | WRing channel f =>
      Nat.eqb (ring_domain channel) d &&
      match channel, f with
      | _, RBuf _ => false
      | _, _ => true
      end
  | _ => false
  end.

Definition cwrites (st : cstep) (w : cword) : bool :=
  cword_eqb w (stack_word (chart st)) ||
  match st, w with
  | CPrepare, (WRoot d | WGuest d) => Nat.ltb d 2
  | CPrepare, WCtl _ => true
  | CPublishBlock d, WBlock d' f =>
      Nat.eqb d d' && negb (match f with BSaved | BStack => true | _ => false end)
  | CPublishBlock d, WRing _ _ => own_ring_word d w
  | CPublishBlock _, WCtl _ => true
  | CStart _, WCtl _ => true
  | CReady d, WBlock d' (BControls | BEntered) => Nat.eqb d d'
  | CEnter d, WBlock d' BSaved => Nat.eqb d d'
  | (CPost channel _), WRing channel' f =>
      cring_eqb channel channel' &&
      match f with RBuf _ => true | RWCur | RWFail | RWPeak => true | _ => false end
  | CPublish channel, WRing channel' f =>
      cring_eqb channel channel' &&
      match f with RHead | RWLim | RWFail => true | _ => false end
  | CRoom channel, WRing channel' RWFail => cring_eqb channel channel'
  | (CAcquire channel), WRing channel' f =>
      cring_eqb channel channel' &&
      match f with RRLim | RRFail => true | _ => false end
  | (CTake channel), WRing channel' f =>
      cring_eqb channel channel' &&
      match f with RRCur | RRFail => true | _ => false end
  | (CTake (Ctl (InboundRing d)) | CRelease (Ctl (InboundRing d)) | CTake (Inp d)
     | CRelease (Inp d)), WBlock d' (BCore _) => Nat.eqb d d'
  | CTake (Ctl (OutboundRing _)), WCtl KRecord => true
  | CTake (Inp d), WGuest d' => Nat.eqb d d'
  | CRelease channel, WRing channel' f =>
      cring_eqb channel channel' &&
      match f with RTail | RRFail => true | _ => false end
  | CDrop _ _, WCtl _ => true
  | (CDrain | CStepRecord _ | CDecideMgmt _ | CPoll _ _ | CRunEnd), WCtl _ =>
      true
  | (CAcquire (Ctl (OutboundRing _)) | CRelease (Ctl (OutboundRing _))),
    WCtl _ => true
  | (CPost (Ctl (InboundRing _)) _ | CPost (Inp _) _
     | CPublish (Ctl (InboundRing _)) | CPublish (Inp _) | CRoom (Inp _)), WCtl _ =>
      true
  | CExit d e, WBlock d' (BSaved | BCore _) => Nat.eqb d d'
  | CFail d, WBlock d' (BCore _) => Nat.eqb d d'
  | _, _ => false
  end.

(* --------------------------------------------------------------------- *)
(** * The step semantics *)

Definition upd_fun {A : Type} (f : nat -> A) (d : nat) (v : A) : nat -> A :=
  fun d' => if Nat.eqb d' d then v else f d'.

Definition set_mem (s : cstate) (m : mem) : cstate :=
  mk_cstate m (cs_h0 s) (cs_h0todo s) (cs_dmode s) (cs_dtodo s) (cs_log s).

Definition set_h0 (s : cstate) (mode : h0mode) (todo : list act) : cstate :=
  mk_cstate (cs_mem s) mode todo (cs_dmode s) (cs_dtodo s) (cs_log s).

Definition set_d (s : cstate) (d : nat) (mode : dmode) (todo : list act)
    : cstate :=
  mk_cstate (cs_mem s) (cs_h0 s) (cs_h0todo s) (upd_fun (cs_dmode s) d mode)
    (upd_fun (cs_dtodo s) d todo) (cs_log s).

Definition add_log (s : cstate) (events : list gev) : cstate :=
  mk_cstate (cs_mem s) (cs_h0 s) (cs_h0todo s) (cs_dmode s) (cs_dtodo s)
    (cs_log s ++ events).

Definition dmode_of (s : cstate) (d : nat) : dmode := cs_dmode s d.
Definition dtodo_of (s : cstate) (d : nat) : list act := cs_dtodo s d.

Definition outbound (d : nat) : cring := Ctl (OutboundRing d).
Definition inbound (d : nat) : cring := Ctl (InboundRing d).

Definition core (m : mem) (d : nat) (f : core_field) : N :=
  m (WBlock d (BCore f)).

Definition set_core (m : mem) (d : nat) (f : core_field) (v : N) : mem :=
  upd m (WBlock d (BCore f)) v.

Definition ctl (m : mem) (f : ctl_field) : N := m (WCtl f).

Definition set_ctl (m : mem) (f : ctl_field) (v : N) : mem := upd m (WCtl f) v.

(** The SBI results hart 0 answers a request with. *)
(* reads: mvp/src/mvp-sbi.c:answerable *)
Definition answerable (code : N) : bool :=
  (code =? sbi_success) || (code =? sbi_invalid_param) ||
  (code =? sbi_denied) || (code =? sbi_invalid_state).

(** [served] is one inbound record's service on a domain hart. *)
Record served : Type := mk_served {
  sv_ok : bool;
  sv_phase : N;
  sv_awaiting : N;
  sv_answer : N;
  sv_by : N;
  sv_post : option record
}.

(**
 * [serve_record] is the SBI core's service of one inbound record by the
 * hart's phase: a PING while running answered with a PONG; the
 * MGMT_RESULT the hart awaits, kept; a PAUSE while running and not
 * waiting, answered with PAUSED; a TERMINATE then or while paused,
 * answered with TERMINATED; anything else fails the hart.
 *)
(* reads: mvp/src/mvp-sbi.c:serve_record *)
Definition serve_record (accept_mgmt : bool) (phase awaiting answer requester exits : N)
    (r : record) : served :=
  let running := phase =? phase_running in
  let ordered := accept_mgmt && (rec_length r =? 8) && (record_word r 0 <? 2) in
  let fail := mk_served false phase_failed awaiting answer requester None in
  let t := rec_type r in
  if t =? rec_ping then
    if running && (rec_length r =? 0)
    then mk_served true phase awaiting answer requester
           (Some (pong_record (rec_time r)))
    else fail
  else if t =? rec_mgmt_result then
    if running && negb (awaiting =? 0) && (rec_length r =? 16) &&
       (record_word r 1 =? awaiting) && answerable (record_word r 0)
    then mk_served true phase 0 (record_word r 0) requester None
    else fail
  else if t =? rec_pause then
    if ordered && running && (awaiting =? 0)
    then mk_served true phase_paused awaiting answer (record_word r 0)
           (Some (transition_record rec_paused exits (record_word r 0)))
    else fail
  else if t =? rec_terminate then
    if ordered && ((running && (awaiting =? 0)) || (phase =? phase_paused))
    then mk_served true phase_terminated awaiting answer (record_word r 0)
           (Some (transition_record rec_terminated exits (record_word r 0)))
    else fail
  else fail.

(** The SBI extensions an exit's ecall may name. *)
(* reads: mvp/src/mvp.h:BE_MVP_SBI_EID_MGMT *)
Definition eid_mgmt : N := 0x08004245.
(* reads: mvp/src/mvp.h:BE_MVP_SBI_EID_SRST *)
Definition eid_srst : N := 0x53525354.
(* reads: mvp/src/mvp.h:BE_MVP_SBI_EID_DBCN *)
Definition eid_dbcn : N := 0x4442434e.

Definition nonempty {A : Type} (l : list A) : bool :=
  match l with [] => false | _ => true end.

(**
 * [exit_decide] is be_mvp_handle_exit with the dispatch: an exit at the
 * ceiling, from VS mode, an interrupt but the IPI, an exception but a VS
 * ecall, a guest-page fault the denial entry refuses, or a reboot or a
 * failure's SRST fails the domain; an IPI serves the inbound ring; an
 * accepted guest-page fault is denied; a management call posts its
 * request and waits; an SRST shutdown posts SHUTDOWN and parks; a granted
 * console read serves the input ring; a console write that completes
 * lines posts them; anything else returns to the guest. The window checks
 * of the console's reads and writes are not modelled.
 *)
(* reads: mvp/src/mvp-sbi.c:be_mvp_handle_exit *)
(* reads: mvp/src/mvp-sbi.c:be_mvp_classify_cause *)
(* reads: mvp/src/mvp-sbi.c:sbi_srst *)
(* reads: mvp/src/mvp-sbi.c:sbi_dbcn *)
(* reads: mvp/src/mvp-sbi.c:sbi_mgmt *)
Definition exit_decide (ceiling accept_denial accept_mgmt accept_input exits : N)
    (w : walked) (e : exit_rec) : exit_action :=
  if ceiling <=? exits then XFail
  else if negb (N.testbit (ex_hstatus e) hstatus_spv_bit) then XFail
  else if ex_scause e =? scause_ssi then XIpi
  else if is_gpf (ex_scause e) then
    match denial_decide (accept_denial =? 1) w e with
    | Some dn => XDeny dn
    | None => XFail
    end
  else if negb (ex_scause e =? scause_ecall) then XFail
  else if (ex_a7 e =? eid_mgmt) && (accept_mgmt =? 1) then
    if (ex_a6 e =? fid_pause) || (ex_a6 e =? fid_terminate)
    then XMgmt (ex_a6 e) (ex_a0 e) else XResume
  else if (ex_a7 e =? eid_srst) && (ex_a6 e =? 0) then
    if (2 <? ex_a0 e) || (1 <? ex_a1 e) then XResume
    else if negb (ex_a0 e =? 0) then XFail
    else if ex_a1 e =? 0 then XShutdown else XFail
  else if (ex_a7 e =? eid_dbcn) && (ex_a6 e =? 1) then
    if (accept_input =? 1) && negb (ex_a0 e =? 0) then XInput else XResume
  else if (ex_a7 e =? eid_dbcn) && ((ex_a6 e =? 0) || (ex_a6 e =? 2)) &&
          nonempty (ex_line e)
  then XLine (ex_line e)
  else XResume.

(** A domain hart's exit decision, from the words of its own page. *)
Definition hart_exit_action (m : mem) (d : nat) (e : exit_rec) : exit_action :=
  exit_decide (m (WBlock d (BConfig 0))) (m (WBlock d (BConfig 1)))
    (m (WBlock d (BConfig 2))) (m (WBlock d (BConfig 3)))
    (core m d CoreExits) (read_walked m d) e.

(** Hart 0's publication of one block (publish_blocks), the generation last. *)
(* reads: mvp/src/mvp-runtime.c:publish_blocks *)
(* reads: mvp/src/mvp-hart.c:be_mvp_block_fill *)
Definition block_hpa (d : nat) : N :=
  if Nat.eqb d 0 then be_mvp_g0_block_hpa else be_mvp_g1_block_hpa.

Definition hgatp_of (d : nat) : N :=
  if Nat.eqb d 0 then be_mvp_g0_hgatp else be_mvp_g1_hgatp.

Fixpoint upd_list (m : mem) (writes : list (cword * N)) : mem :=
  match writes with
  | [] => m
  | (w, v) :: rest => upd_list (upd m w v) rest
  end.

Definition core_fields : list core_field :=
  [CorePhase; CoreAwaiting; CoreAnswer; CoreBy; CoreExits; CoreDenials;
   CoreRequests].

Definition block_writes (c : config) (d : nat) : list (cword * N) :=
  [(WBlock d (BDesc 0), N.of_nat (dhart d));
   (WBlock d (BDesc 1), N.of_nat d);
   (WBlock d (BDesc 2), hgatp_of d);
   (WBlock d (BDesc 3), block_hpa d);
   (WBlock d BEntry, be_mvp_kernel_gpa);
   (WBlock d (BConfig 0), cfg_ceiling c);
   (WBlock d (BConfig 1), bool_word (cfg_accept_denial c));
   (WBlock d (BConfig 2), bool_word (cfg_accept_mgmt c));
   (WBlock d (BConfig 3), bool_word (cfg_input c d));
   (WBlock d BControls, 0);
   (WBlock d BEntered, 0)] ++
  map (fun f => (WBlock d (BCore f), 0)) core_fields ++
  map (fun k => (WBlock d (BWalked k), nth k (walked_words (cfg_root c d)) 0))
    (seq 0 11).

Definition publish_block (c : config) (m : mem) (d : nat) : mem :=
  upd (ring_init (Inp d) (ring_init (outbound d) (ring_init (inbound d)
         (upd_list m (block_writes c d)))))
    (WBlock d BGen) be_mvp_generation.

(*
 * The measurement log (M9; mvp/docs/log-profile.md), a reading and not a
 * theorem: the log page and its registers, hart 0's be_mvp_log and
 * be_mvp_log_registers in the MVP region's BSS, are not words of this
 * model. measure_log is the only code that writes them (through
 * mvp-log.c's be_mvp_log_init, be_mvp_log_append, be_mvp_log_gate, and
 * be_mvp_log_close, on its own call path), hart 0 runs it once, after the
 * placement and before publish_blocks and the barrier's fence (in
 * be_mvp_runtime_main), so every write precedes the barrier and every
 * domain hart's start; after the barrier hart 0 reads only the registers
 * (the terminated domain's launch register) and writes neither; and no
 * domain hart's code names them (the image checker's HART0_ONLY rule;
 * security model v1's I19). So no step after prepare reads or writes a
 * word of the log, and prepare stands for all of it: the gates' verdicts
 * (KGate) and the global rule below.
 *)
(* reads: mvp/src/mvp-runtime.c:be_mvp_log *)
(* reads: mvp/src/mvp-runtime.c:be_mvp_log_registers *)
(* reads: mvp/src/mvp-runtime.c:measure_log *)

(**
 * [gate_verdict]: domain d's launch gate (log_launch; since M9 every
 * domain has one, on its own launch register): d's gate predicate on d's
 * bytes as placed, which d's launch records measure into its register,
 * and the image's expected launch register for d.
 *)
(* reads: mvp/src/mvp-runtime.c:log_launch *)
(* reads: mvp/src/mvp-log.c:be_mvp_log_gate *)
Definition gate_verdict (c : config) (m : mem) (d : nat) : bool :=
  cfg_gate c d (m (WGuest d)) (cfg_expected c d).

(**
 * [global_rule]: M9's global rule (planning/mvp-m9-plan.md, D-1): every
 * domain's launch gate passed and the log, having taken every record,
 * closed with the image's expected count, before BE_MVP:07; otherwise
 * hart 0 fails the run and no domain hart starts. Hart 0 runs the gates
 * in domain order and stops at the first failure; prepare, one step, takes
 * both verdicts and the close together.
 *)
(* reads: mvp/src/mvp-log.c:be_mvp_log_append *)
(* reads: mvp/src/mvp-log.c:be_mvp_log_close *)
Definition global_rule (c : config) (m : mem) : bool :=
  gate_verdict c m 0 && gate_verdict c m 1 && cfg_log_closes c.

(** Hart 0's preparation: the windows placed, the roots built, the gate. *)
(* reads: mvp/src/mvp-runtime.c:build_gstage *)
(* reads: mvp/src/mvp-runtime.c:place_payload *)
Definition prepare_mem (c : config) (m : mem) : mem :=
  let placed := upd_list m
    [(WGuest 0, cfg_placed c 0); (WGuest 1, cfg_placed c 1);
     (WRoot 0, 1); (WRoot 1, 1)] in
  upd_list placed
    [(WCtl (KGate 0), bool_word (gate_verdict c placed 0));
     (WCtl (KGate 1), bool_word (gate_verdict c placed 1))].

(** Hart 0's round-robin drain order (be_mvp_drain_begin, _next, _visited). *)
(* reads: mvp/src/mvp-hart.c:be_mvp_drain_begin *)
(* reads: mvp/src/mvp-hart.c:be_mvp_drain_next *)
(* reads: mvp/src/mvp-hart.c:be_mvp_drain_visited *)
Definition drain_begin (cap : N) (m : mem) : mem :=
  upd_list m [(WCtl KDrainNext, 0); (WCtl KDrainIdle, 0);
              (WCtl KDrainVisits, 2 * (cap / 16 + 1))].

Definition drain_next (m : mem) : option nat :=
  let next := ctl m KDrainNext in
  if (ctl m KDrainVisits =? 0) || (2 <=? ctl m KDrainIdle) || (2 <=? next)
  then None else Some (N.to_nat next).

Definition drain_visited (m : mem) (took : bool) : mem :=
  match drain_next m with
  | None => m
  | Some _ =>
      let next := ctl m KDrainNext in
      upd_list m
        [(WCtl KDrainVisits, ctl m KDrainVisits - 1);
         (WCtl KDrainIdle, if took then 0 else ctl m KDrainIdle + 1);
         (WCtl KDrainNext, if next + 1 <? 2 then next + 1 else 0)]
  end.

Definition next_is (next : option nat) (d : nat) : bool :=
  match next with Some d' => Nat.eqb d' d | None => false end.

(** After a visit: the order advances; the pass ends when it says so. *)
Definition after_visit (s : cstate) (m : mem) (took : bool) : cstate :=
  let m' := drain_visited m took in
  set_h0 (set_mem s m')
    (match drain_next m' with Some _ => H0Visit | None => H0Idle end) [].

(** [target_of]: a request's target as hart 0 sees it (target_state). *)
(* reads: mvp/src/mvp-hart.c:target_state *)
Definition target_of (m : mem) (t : nat) : target_state :=
  let phase := ctl m (KTrack t) in
  if phase =? track_shutdown then TShutdown
  else if phase =? track_terminated then TTerminated
  else if negb (ctl m (KPending t) =? 0) || negb (ctl m (KAwaiting t) =? 0)
  then TPending
  else if phase =? track_paused then TPaused
  else TRunning.

Inductive h0outcome : Type :=
| HContinue
| HDone
| HEnding
| HInvalid.

(** [settle]: the answer to the request pending on a target, @code. *)
(* reads: mvp/src/mvp-hart.c:settle *)
Definition settle (m : mem) (target : nat) (code : N)
    : mem * list act * list gev :=
  let requester := N.to_nat (ctl m (KBy target)) in
  let seq := ctl m (KSeq target) in
  (upd_list m [(WCtl (KAwaiting requester), 0); (WCtl (KPending target), 0);
               (WCtl (KBy target), 0); (WCtl (KFid target), 0);
               (WCtl (KSeq target), 0)],
   [APost (inbound requester) (result_record code seq);
    APublish (inbound requester)],
   [GSettle target requester seq code]).

(** [complete]: every domain shut down or terminated. *)
(* reads: mvp/src/mvp-hart.c:complete *)
Definition complete (m : mem) : bool :=
  forallb (fun d => (ctl m (KTrack d) =? track_shutdown) ||
                    (ctl m (KTrack d) =? track_terminated)) [0; 1]%nat.

Definition invalid (m : mem) : mem * list act * h0outcome * list gev :=
  (m, [], HInvalid, []).

(**
 * [handle_step] is be_mvp_control_record's step of one drained record
 * other than the management ones: READY and ENTERED in turn; a LINE, and
 * the domain's one PING with its first, unless a delivered request is
 * pending on it; its PONG; a DENIAL; SHUTDOWN, answering a request pending
 * on it; FAIL, acknowledged, ending the run; anything else fails the run.
 *)
(* reads: mvp/src/mvp-hart.c:be_mvp_control_record *)
(* reads: mvp/src/mvp-hart.c:apply *)
(* reads: mvp/src/mvp-hart.c:domain_shutdown *)
(* reads: mvp/src/mvp-hart.c:domain_fail *)
(* reads: mvp/src/mvp-runtime.c:step *)
Definition handle_step (m : mem) (d : nat) (r : record)
    : mem * list act * h0outcome * list gev :=
  let t := rec_type r in
  let phase := ctl m (KTrack d) in
  if Nat.leb 2 d || (phase =? track_none) || (ctl m KDone =? 1) then invalid m
  else if t =? rec_ready then
    if phase =? track_started
    then (set_ctl m (KTrack d) track_ready, [], HContinue, [])
    else invalid m
  else if t =? rec_entered then
    if phase =? track_ready
    then (set_ctl m (KTrack d) track_entered, [], HContinue, [])
    else invalid m
  else if t =? rec_line then
    if phase =? track_entered then
      let m1 := set_ctl m (KLines d) (ctl m (KLines d) + 1) in
      if ctl m (KPinged d) =? 0 then
        let m2 := set_ctl m1 (KPinged d) 1 in
        if ctl m (KPending d) =? 0
        then (m2, [APost (inbound d) ping_record; APublish (inbound d)],
              HContinue, [])
        else (m2, [], HContinue, [])
      else (m1, [], HContinue, [])
    else invalid m
  else if t =? rec_pong then
    if (phase =? track_entered) && (ctl m (KPinged d) =? 1) &&
       (ctl m (KPonged d) =? 0)
    then (set_ctl m (KPonged d) 1, [], HContinue, [])
    else invalid m
  else if t =? rec_denial then
    if phase =? track_entered
    then (set_ctl m (KDenials d) (ctl m (KDenials d) + 1), [], HContinue, [])
    else invalid m
  else if t =? rec_shutdown then
    if (phase =? track_entered) && (ctl m (KPonged d) =? 1) &&
       (ctl m (KAwaiting d) =? 0) then
      let m1 := set_ctl m (KTrack d) track_shutdown in
      let '(m2, todo, events) :=
        if ctl m1 (KPending d) =? 0 then (m1, [], [])
        else settle m1 d sbi_invalid_state in
      if complete m2 then (set_ctl m2 KDone 1, todo, HDone, events)
      else (m2, todo, HContinue, events)
    else invalid m
  else if t =? rec_fail then
    if negb (phase =? track_shutdown)
    then (set_ctl m (KTrack d) track_failed,
          [APost (inbound d) ack_record; APublish (inbound d)], HEnding, [])
    else invalid m
  else invalid m.

Definition is_mgmt_record (r : record) : bool :=
  (rec_type r =? rec_mgmt_request) || (rec_type r =? rec_paused) ||
  (rec_type r =? rec_terminated).

(**
 * [handle_mgmt] is the management step: a MGMT_REQUEST from an entered
 * domain, its next sequence number and none of its own outstanding, is
 * decided by be_mvp_mgmt_decide against the sealed grants and answered at
 * once or delivered to its target's inbound ring; a PAUSED or TERMINATED
 * from the target of the request pending on it settles that request.
 *)
(* reads: mvp/src/mvp-hart.c:domain_request *)
(* reads: mvp/src/mvp-hart.c:domain_transition *)
Definition handle_mgmt (c : config) (m : mem) (d : nat) (r : record)
    : mem * list act * h0outcome * list gev :=
  let t := rec_type r in
  let phase := ctl m (KTrack d) in
  if Nat.leb 2 d || (phase =? track_none) || (ctl m KDone =? 1) ||
     negb (cfg_accept_mgmt c)
  then invalid m
  else if t =? rec_mgmt_request then
    let fid := record_word r 0 in
    let target := record_word r 1 in
    let seq := record_word r 2 in
    if (phase =? track_entered) && (rec_length r =? 24) &&
       ((fid =? fid_pause) || (fid =? fid_terminate)) &&
       (seq =? ctl m (KRequests d) + 1) && (ctl m (KAwaiting d) =? 0) then
      let m1 := set_ctl (set_ctl m (KRequests d) seq) (KAwaiting d) 1 in
      let state := if target <? 2 then target_of m1 (N.to_nat target)
                   else TRunning in
      let decision := mgmt_decide (cfg_grants c) (N.of_nat d) fid target state in
      let event := GDecide d fid target seq state decision in
      if decision =? mgmt_deliver then
        let tn := N.to_nat target in
        (upd_list m1 [(WCtl (KPending tn), 1); (WCtl (KBy tn), N.of_nat d);
                      (WCtl (KFid tn), fid); (WCtl (KSeq tn), seq)],
         [APost (inbound tn) (order_record fid (N.of_nat d));
          APublish (inbound tn)], HContinue, [event])
      else
        (set_ctl m1 (KAwaiting d) 0,
         [APost (inbound d) (result_record decision seq);
          APublish (inbound d)], HContinue, [event])
    else invalid m
  else if (t =? rec_paused) || (t =? rec_terminated) then
    let paused := t =? rec_paused in
    if (rec_length r =? 16) && (ctl m (KPending d) =? 1) &&
       (ctl m (KFid d) =? (if paused then fid_pause else fid_terminate)) &&
       (record_word r 1 =? ctl m (KBy d)) &&
       ((phase =? track_entered) || (negb paused && (phase =? track_paused)))
    then
      let m1 := set_ctl m (KTrack d)
                  (if paused then track_paused else track_terminated) in
      let '(m2, todo, events) := settle m1 d sbi_success in
      if negb paused && complete m2
      then (set_ctl m2 KDone 1, todo, HDone, events)
      else (m2, todo, HContinue, events)
    else invalid m
  else invalid m.

(** [h0_after]: hart 0's mode after a drained record's step. *)
Definition h0_after (s : cstate) (m : mem) (todo : list act)
    (outcome : h0outcome) (events : list gev) : cstate :=
  let s1 := add_log s events in
  match outcome with
  | HContinue =>
      let m' := drain_visited m true in
      set_h0 (set_mem s1 m')
        (match drain_next m' with Some _ => H0Visit | None => H0Idle end) todo
  | HDone => set_h0 (set_mem s1 m) H0Done todo
  | HEnding => set_h0 (set_mem s1 m) H0Ending todo
  | HInvalid => set_h0 (set_mem s1 m) H0Failed []
  end.

(** A writer's queued action, run: success pops it; a refusal halts. *)
Definition writer_halts (s : cstate) (channel : cring) (m : mem) : cstate :=
  match channel with
  | Ctl (OutboundRing d) => set_d (set_mem s m) d DHalted []
  | _ => set_h0 (set_mem s m) H0Failed []
  end.

Definition writer_todo (s : cstate) (channel : cring) : list act :=
  match channel with
  | Ctl (OutboundRing d) => dtodo_of s d
  | _ => cs_h0todo s
  end.

Definition set_writer_todo (s : cstate) (channel : cring) (todo : list act)
    : cstate :=
  match channel with
  | Ctl (OutboundRing d) => set_d s d (dmode_of s d) todo
  | _ => set_h0 s (cs_h0 s) todo
  end.

(** A domain hart's failure: its phase failed, FAIL next. *)
Definition hart_fails (s : cstate) (d : nat) (m : mem) : cstate :=
  set_d (set_mem s (set_core m d CorePhase phase_failed)) d DFailing [].

Definition writer_live (s : cstate) (channel : cring) : bool :=
  match channel with
  | Ctl (OutboundRing d) =>
      Nat.ltb d 2 &&
      match dmode_of s d with
      | DOff | DStart | DEarlyPark | DHalted => false
      | _ => true
      end
  | Ctl (InboundRing d) | Inp d =>
      Nat.ltb d 2 &&
      match cs_h0 s with
      | H0Boot | H0Publish _ | H0Start _ | H0Ended | H0Failed => false
      | _ => true
      end
  end.

(** [exec] is one step: None when the step is not enabled. *)
Definition exec (c : config) (s : cstate) (st : cstep) : option cstate :=
  let m := cs_mem s in
  match st with
  | CPrepare =>
      match cs_h0 s with
      | H0Boot =>
          let m' := prepare_mem c m in
          let ok := global_rule c m' in
          Some (add_log (set_h0 (set_mem s m') (if ok then H0Publish 0 else H0Failed) [])
                  [GGate 0 (gate_verdict c m' 0); GGate 1 (gate_verdict c m' 1)])
      | _ => None
      end
  | CPublishBlock d =>
      match cs_h0 s with
      | H0Publish d' =>
          if Nat.eqb d d' && Nat.ltb d 2 then
            Some (add_log (set_h0 (set_mem s (publish_block c m d))
                             (if Nat.eqb d 0 then H0Publish 1 else H0Start 0) [])
                    [GPublished d])
          else None
      | _ => None
      end
  | CStart d =>
      match cs_h0 s, dmode_of s d with
      | H0Start d', DOff =>
          if Nat.eqb d d' && Nat.ltb d 2 then
            Some (add_log
                    (set_d (set_h0 (set_mem s (set_ctl m (KTrack d) track_started))
                              (if Nat.eqb d 0 then H0Start 1 else H0Idle) [])
                       d DStart [])
                    [GStart d])
          else None
      | _, _ => None
      end
  | CReady d =>
      match dmode_of s d, dtodo_of s d with
      | DStart, [] =>
          if negb (Nat.ltb d 2) then None else
          let gen := m (WBlock d BGen) in
          let s1 := add_log s [GReady d gen] in
          if negb (gen =? be_mvp_generation) ||
             negb (m (WBlock d (BDesc 0)) =? N.of_nat (dhart d)) ||
             negb (m (WBlock d (BDesc 1)) =? N.of_nat d) ||
             negb (m (WBlock d (BDesc 3)) =? block_hpa d) ||
             negb (core m d CorePhase =? phase_running) ||
             failed_view (rd m (inbound d) RRFail) ||
             failed_view (rd m (outbound d) RWFail) ||
             failed_view (rd m (Inp d) RRFail)
          then Some (set_d s1 d DEarlyPark [])
          else
            Some (set_d (set_mem s1 (upd_list m [(WBlock d BControls, 1);
                                                 (WBlock d BEntered, 1)]))
                    d DEntering
                    [APost (outbound d) ready_record;
                     APost (outbound d) (entered_record (m (WBlock d BEntry)));
                     APublish (outbound d)])
      | _, _ => None
      end
  | CEnter d =>
      match dmode_of s d, dtodo_of s d with
      | DEntering, [] =>
          if Nat.ltb d 2 then
            Some (add_log (set_d (set_mem s (upd m (WBlock d BSaved) (m (WBlock d BEntry))))
                             d DGuest [])
                    [GEnter d])
          else None
      | _, _ => None
      end
  | CPost channel r =>
      match writer_todo s channel with
      | APost channel' r' :: rest =>
          if cring_eqb channel channel' && writer_live s channel then
            if negb (record_eqb r r') then None else
            let '(ok, m') :=
              ring_post (cfg_capacity c channel) channel m r in
            if ok then
              Some (add_log (set_writer_todo (set_mem s m') channel rest)
                      [GPost channel (image (N.of_nat (ring_domain channel)) r)])
            else Some (add_log (writer_halts s channel m') [GRefused channel])
          else None
      | _ => None
      end
  | CPublish channel =>
      match writer_todo s channel with
      | APublish channel' :: rest =>
          if cring_eqb channel channel' && writer_live s channel then
            let '(ok, m') := ring_publish channel m in
            if ok then
              Some (add_log (set_writer_todo (set_mem s m') channel rest)
                      [GPublish channel (rd m' channel RHead)])
            else Some (add_log (writer_halts s channel m') [GRefused channel])
          else None
      | _ => None
      end
  | CAcquire (Ctl (OutboundRing d) as channel) =>
      match cs_h0 s, cs_h0todo s with
      | H0Visit, [] =>
          if negb (next_is (drain_next m) d) then None else
          let '(n, m') := ring_acquire (cfg_capacity c channel) channel m in
          let s1 := add_log s [GAcquire channel n] in
          if n =? 0 then
            if failed_view (rd m' channel RRFail)
            then Some (set_h0 (set_mem s1 m') H0Failed [])
            else Some (after_visit s1 m' false)
          else Some (set_h0 (set_mem s1 m') (H0Take d) [])
      | _, _ => None
      end
  | CTake (Ctl (OutboundRing d) as channel) =>
      match cs_h0 s, cs_h0todo s with
      | H0Take d', [] =>
          if negb (Nat.eqb d d') then None else
          match ring_take (cfg_capacity c channel) channel m with
          | (TakeRecord r img, m') =>
              Some (add_log (set_h0 (set_mem s (set_ctl m' KRecord (rec_type r)))
                               (H0Release d (Some r)) [])
                      [GTake channel img])
          | (TakeEmpty, m') => Some (set_h0 (set_mem s m') (H0Release d None) [])
          | (TakeInvalid, m') => Some (set_h0 (set_mem s m') H0Failed [])
          end
      | _, _ => None
      end
  | CRelease (Ctl (OutboundRing d) as channel) =>
      match cs_h0 s, cs_h0todo s with
      | H0Release d' taken, [] =>
          if negb (Nat.eqb d d') then None else
          let '(ok, m') := ring_release channel m in
          if negb ok then Some (set_h0 (set_mem s m') H0Failed []) else
          let s1 := add_log s [GRelease channel (rd m' channel RTail)] in
          match taken with
          | Some r => Some (set_h0 (set_mem s1 m') (H0Handle d r) [])
          | None => Some (after_visit s1 m' false)
          end
      | _, _ => None
      end
  | CAcquire (Ctl (InboundRing d) as channel) =>
      match dmode_of s d, dtodo_of s d with
      | DServe k SAcquire, [] => 
          let '(n, m') := ring_acquire (cfg_capacity c channel) channel m in
          Some (add_log (set_d (set_mem s m') d (DServe k (STake false false)) [])
                  [GAcquire channel n])
      | DWaitMgmt, [] | DParked, [] | DFailWait, [] =>
          let k := match dmode_of s d with
                   | DWaitMgmt => FromWait | DParked => FromPark | _ => FromFail end in
          let '(n, m') := ring_acquire (cfg_capacity c channel) channel m in
          Some (add_log (set_d (set_mem s m') d (DServe k (STake false false)) [])
                  [GAcquire channel n])
      | _, _ => None
      end
  | CTake (Ctl (InboundRing d) as channel) =>
      match dmode_of s d, dtodo_of s d with
      | DServe k (STake taken posted), [] =>
          match ring_take (cfg_capacity c channel) channel m, k with
          | (TakeRecord r img, m'), FromFail =>
              Some (add_log (set_d (set_mem s m') d
                               (if rec_type r =? rec_ack then DHalted
                                else DServe FromFail (STake true false)) [])
                      [GTake channel img])
          | (TakeRecord r img, m'), _ =>
              let sv := serve_record (cfg_accept_mgmt c) (core m' d CorePhase)
                          (core m' d CoreAwaiting) (core m' d CoreAnswer)
                          (core m' d CoreBy) (core m' d CoreExits) r in
              let s1 := add_log s [GTake channel img] in
              if sv_ok sv then
                Some (set_d (set_mem s1 (upd_list m'
                                [(WBlock d (BCore CorePhase), sv_phase sv);
                                 (WBlock d (BCore CoreAwaiting), sv_awaiting sv);
                                 (WBlock d (BCore CoreAnswer), sv_answer sv);
                                 (WBlock d (BCore CoreBy), sv_by sv)]))
                        d (DServe k (STake true (posted || match sv_post sv with
                                                           | Some _ => true
                                                           | None => false end)))
                        (match sv_post sv with
                         | Some a => [APost (outbound d) a]
                         | None => []
                         end))
              else Some (hart_fails s1 d m')
          | (TakeEmpty, m'), FromFail => Some (set_d (set_mem s m') d DFailWait [])
          | (TakeEmpty, m'), FromGuest =>
              if taken then Some (set_d (set_mem s m') d (DServe k (SRelease posted)) [])
              else Some (hart_fails s d m')
          | (TakeEmpty, m'), _ =>
              Some (set_d (set_mem s m') d (DServe k (SRelease posted)) [])
          | (TakeInvalid, m'), FromFail => Some (set_d (set_mem s m') d DFailWait [])
          | (TakeInvalid, m'), _ => Some (hart_fails s d m')
          end
      | _, _ => None
      end
  | CRelease (Ctl (InboundRing d) as channel) =>
      match dmode_of s d, dtodo_of s d with
      | DServe k (SRelease posted), [] =>
          match k with
          | FromFail => None
          | _ =>
              let '(ok, m') := ring_release channel m in
              if negb ok then Some (hart_fails s d m') else
              let next :=
                match k with
                | FromGuest =>
                    if (core m' d CorePhase =? phase_paused) ||
                       (core m' d CorePhase =? phase_terminated)
                    then DParking else DGuest
                | FromWait =>
                    if core m' d CoreAwaiting =? 0 then DGuest else DWaitMgmt
                | _ => DParked
                end in
              Some (add_log (set_d (set_mem s m') d next
                               (if posted then [APublish (outbound d)] else []))
                      [GRelease channel (rd m' channel RTail)])
          end
      | _, _ => None
      end
  | CAcquire (Inp d as channel) =>
      match dmode_of s d, dtodo_of s d with
      | DInput IAcquire, [] =>
          let '(n, m') := ring_acquire (cfg_capacity c channel) channel m in
          Some (add_log (set_d (set_mem s m') d (DInput ITake) [])
                  [GAcquire channel n])
      | _, _ => None
      end
  | CTake (Inp d as channel) =>
      match dmode_of s d, dtodo_of s d with
      | DInput ITake, [] =>
          match ring_take (cfg_capacity c channel) channel m with
          | (TakeRecord r img, m') =>
              Some (add_log (set_d (set_mem s (upd m' (WGuest d) (le_value (rec_payload r))))
                               d (DInput IRelease) [])
                      [GTake channel img])
          | (TakeEmpty, m') => Some (set_d (set_mem s m') d (DInput IRelease) [])
          | (TakeInvalid, m') => Some (hart_fails s d m')
          end
      | _, _ => None
      end
  | CRelease (Inp d as channel) =>
      match dmode_of s d, dtodo_of s d with
      | DInput IRelease, [] =>
          let '(ok, m') := ring_release channel m in
          if negb ok then Some (hart_fails s d m') else
          Some (add_log (set_d (set_mem s m') d DGuest [])
                  [GRelease channel (rd m' channel RTail)])
      | _, _ => None
      end
  | CRoom (Inp d as channel) =>
      match cs_h0 s, cs_h0todo s with
      | H0Input d' bytes None, [] =>
          if negb (Nat.eqb d d') then None else
          let '(answer, m') := ring_room (cfg_capacity c channel) channel m in
          let s1 := add_log s [GRoom channel answer] in
          if failed_view (rd m' channel RWFail)
          then Some (set_h0 (set_mem s1 m') H0Failed [])
          else
            let posted := N.min answer (N.of_nat (length bytes)) in
            Some (set_h0 (set_mem s1 m')
                    (if posted <? N.of_nat (length bytes)
                     then H0Input d bytes (Some posted) else H0Idle)
                    (if posted =? 0 then []
                     else [APost channel (input_record (firstn (N.to_nat posted) bytes));
                           APublish channel]))
      | _, _ => None
      end
  | CRoom (Ctl _) => None
  | CDrop (Inp d as channel) n =>
      match cs_h0 s, cs_h0todo s with
      | H0Input d' bytes (Some posted), [] =>
          if Nat.eqb d d' && (n =? N.of_nat (length bytes) - posted) then
            Some (add_log (set_h0 (set_mem s (set_ctl m (KDrops d) (ctl m (KDrops d) + n)))
                             H0Idle [])
                    [GDrop channel n])
          else None
      | _, _ => None
      end
  | CDrop (Ctl _) _ => None
  | CDrain =>
      match cs_h0 s, cs_h0todo s with
      | H0Idle, [] =>
          Some (set_h0 (set_mem s (drain_begin (cfg_capacity c (outbound 0)) m))
                  H0Visit [])
      | _, _ => None
      end
  | CStepRecord d =>
      match cs_h0 s, cs_h0todo s with
      | H0Handle d' r, [] =>
          if Nat.eqb d d' && negb (is_mgmt_record r) then
            let '(m', todo, outcome, events) := handle_step m d r in
            Some (h0_after s m' todo outcome events)
          else None
      | _, _ => None
      end
  | CDecideMgmt d =>
      match cs_h0 s, cs_h0todo s with
      | H0Handle d' r, [] =>
          if Nat.eqb d d' && is_mgmt_record r then
            let '(m', todo, outcome, events) := handle_mgmt c m d r in
            Some (h0_after s m' todo outcome events)
          else None
      | _, _ => None
      end
  | CExit d e =>
      match dmode_of s d, dtodo_of s d with
      | DGuest, [] =>
          if negb (Nat.ltb d 2) then None else
          let a := hart_exit_action m d e in
          let exits := core m d CoreExits in
          let ceiling := m (WBlock d (BConfig 0)) in
          let m1 := set_core (upd m (WBlock d BSaved) (ex_sepc e)) d CoreExits
                      (if ceiling <=? exits then ceiling + 1 else exits + 1) in
          let s1 := add_log (set_mem s m1) [GExit d e a] in
          let out := outbound d in
          match a with
          | XFail => Some (hart_fails s1 d m1)
          | XResume => Some s1
          | XLine bytes =>
              Some (set_d s1 d DGuest [APost out (line_record bytes); APublish out])
          | XIpi => Some (set_d s1 d (DServe FromGuest SAcquire) [])
          | XDeny dn =>
              let seq := core m1 d CoreDenials + 1 in
              Some (set_d (set_mem s1 (set_core m1 d CoreDenials seq)) d DGuest
                      [APost out (denial_record seq dn); APublish out])
          | XMgmt fid target =>
              let seq := core m1 d CoreRequests + 1 in
              Some (set_d (set_mem s1 (upd_list m1
                              [(WBlock d (BCore CoreRequests), seq);
                               (WBlock d (BCore CoreAwaiting), seq);
                               (WBlock d (BCore CoreAnswer), 0)]))
                      d DWaitMgmt
                      [APost out (request_record fid target seq); APublish out])
          | XShutdown =>
              Some (set_d (set_mem s1 (set_core m1 d CorePhase phase_stopped)) d DShut
                      [APost out (shutdown_record (core m1 d CoreExits)
                                    (core m1 d CoreDenials) (core m1 d CoreRequests));
                       APublish out])
          | XInput => Some (set_d s1 d (DInput IAcquire) [])
          end
      | _, _ => None
      end
  | CPark d =>
      match dmode_of s d, dtodo_of s d with
      | DParking, [] => Some (add_log (set_d s d DParked []) [GPark d])
      | _, _ => None
      end
  | CFail d =>
      match dmode_of s d, dtodo_of s d with
      | DFailing, [] | DWaitMgmt, [] =>
          Some (add_log (set_d (set_mem s (set_core m d CorePhase phase_failed)) d
                           DFailWait [APost (outbound d) fail_record;
                                      APublish (outbound d)])
                  [GFail d])
      | DFailWait, [] => Some (set_d s d DHalted [])
      | _, _ => None
      end
  | CPoll d bytes =>
      match cs_h0 s, cs_h0todo s with
      | H0Idle, [] =>
          let phase := ctl m (KTrack d) in
          if Nat.ltb d 2 && cfg_input c d && nonempty bytes &&
             (N.of_nat (length bytes) <=? 256) &&
             ((phase =? track_started) || (phase =? track_ready) ||
              (phase =? track_entered)) &&
             (ctl m (KPending d) =? 0)
          then Some (set_h0 s (H0Input d bytes None) [])
          else None
      | _, _ => None
      end
  | CRunEnd =>
      match cs_h0 s, cs_h0todo s with
      | (H0Done | H0Ending | H0Idle | H0Visit), [] =>
          Some (add_log (set_h0 s H0Ended []) [GEnd (ctl m KDone =? 1)])
      | _, _ => None
      end
  end.

(** [init]: every word zero, hart 0 at its boot, the domain harts stopped. *)
Definition init : cstate :=
  mk_cstate (fun _ => 0) H0Boot [] (fun _ => DOff) (fun _ => []) [].

(** [reach c tr s]: the trace tr runs from init to s. *)
Inductive reach (c : config) : list cstep -> cstate -> Prop :=
| reach_init : reach c [] init
| reach_step : forall tr s st s',
    reach c tr s -> exec c s st = Some s' -> reach c (tr ++ [st]) s'.
