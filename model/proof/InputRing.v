(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Purpose: the MVP's console input ring alone, beside Binding.v (MVP M7-5;
 * planning/mvp-m7-plan.md, D-8 and Q10; security model v1, Revision 2's
 * R2.1 and I17, with Revision 1's I16): its objects, steps, harts, and
 * writes, the drop rule, the focus parser's table, and one byte's routing;
 * I16's one-writer rule, its separation from Binding.v, the drop rule, I17.
 * Lineage: at 165d4c4d, mvp/src/mvp-input.c (focus_table, classify,
 * be_mvp_focus_step, be_mvp_input_arm, _byte, _flush, _serve), mvp-ring.h
 * (be_mvp_ring_room, _post, _publish, _acquire, _take, _release),
 * mvp-runtime.c (arm_input, poll_input), mvp-hartmain.c (console_read).
 * Trust: an abstract model, not a refinement of the C; Binding.v is
 * imported unedited. Its object and transition types are closed, so the
 * objects and steps here are sums of Binding.v's and the input path's. An
 * input step is the input path's part of steps Binding.v names, hart 0's
 * own after the barrier (Start, Wake) or a domain hart's exit (ExitRecord),
 * whose footprints name the hart's stack and data or saved frame and SBI
 * core state; it lists only the input path's writes beyond those.
 * Scope: not modeled are the ring's set-up before the barrier (hart 0's,
 * as I16 allows), the firmware read (any bytes may arrive), the bytes
 * beyond their class, the first poll's bytes (dropped before-armed ahead
 * of the parser), the batch's 256-byte bound (a poll reads at most 256),
 * the records' encoding (a room counts payload bytes), the guest window's
 * contents and its write-authority check, BE_MVP:16 to :18 and their
 * accounting, timing, concurrency, and the fences.
 *)

From Stdlib Require Import Bool List PeanoNat NArith.
Require Import Binding.
Import ListNotations.

(**
 * [input_object]: hart 0's routing state (be_mvp_console_in, its read
 * buffer and writer views); per domain, the ring's records (block offset
 * 0xd000), head and tail (the state page's input_head and input_tail), and
 * the domain hart's stage with its reader view (mvp-platform.h); and one
 * object set for them, Binding.v's objects, and domain memory.
 *)
Inductive input_object : Type :=
| InputRouting
| InputRecords (domain : nat)
| InputHead (domain : nat)
| InputTail (domain : nat)
| InputStage (domain : nat).
Inductive system_object : Type :=
| BindingObject (object : hart_object)
| InputObject (object : input_object)
| DomainMemory (domain : nat).

(**
 * [input_writer] is the one hart that writes an input object: the ring's
 * writer, hart 0, its records and head and its own routing state; the
 * ring's reader, the domain's hart, its tail and its stage.
 *)
Definition input_writer (binding : binding_instance) (object : input_object)
    : hart :=
  match object with
  | InputRouting | InputRecords _ | InputHead _ => bi_control binding
  | InputTail domain | InputStage domain => bi_hart_of binding domain
  end.

(**
 * [Poll] is hart 0's arming and polls (arm_input, poll_input,
 * be_mvp_input_byte); [Flush] hart 0's post of a domain's batch
 * (be_mvp_input_flush and the publish), reading the tail; [Serve] the
 * domain hart's served read (console_read: the acquire, be_mvp_input_serve
 * copying into the guest's window, the release), reading head and records.
 *)
Inductive input_transition : Type :=
| Poll
| Flush (domain : nat)
| Serve (domain : nat).

Definition input_hart (binding : binding_instance) (step : input_transition)
    : hart :=
  match step with
  | Serve domain => bi_hart_of binding domain
  | _ => bi_control binding
  end.

Definition input_footprint (step : input_transition) : list system_object :=
  match step with
  | Poll => [InputObject InputRouting]
  | Flush domain =>
      map InputObject [InputRouting; InputRecords domain; InputHead domain]
  | Serve domain =>
      [InputObject (InputTail domain); InputObject (InputStage domain);
       DomainMemory domain]
  end.

(** A step of Binding.v's or of the input path's, its hart and writes. *)
Inductive system_step : Type :=
| BindingStep (step : transition)
| InputStep (step : input_transition).

Definition system_hart (binding : binding_instance) (step : system_step)
    : hart :=
  match step with
  | BindingStep step => transition_hart binding step
  | InputStep step => input_hart binding step
  end.

Definition system_footprint (binding : binding_instance)
    (step : system_step) : list system_object :=
  match step with
  | BindingStep step => map BindingObject (footprint binding step)
  | InputStep step => input_footprint step
  end.

(* An input step writes input objects and only its serving domain's memory. *)
Lemma input_footprint_kinds :
  forall step object,
    In object (input_footprint step) ->
    (exists input, object = InputObject input) \/
    (exists domain, step = Serve domain /\ object = DomainMemory domain).
Proof.
  intros [| domain | domain] object Hin; simpl in Hin;
    intuition (subst; eauto).
Qed.

(**
 * [input_ring_single_writer] (I16 over the input ring), for any binding:
 * every system step that writes an input object runs on its writer,
 * Binding.v's steps, by transition_hart, writing none; and an input step
 * writes domain memory only on that domain's own hart.
 *)
Theorem input_ring_single_writer :
  forall binding,
    (forall step object,
       In (InputObject object) (system_footprint binding step) ->
       system_hart binding step = input_writer binding object) /\
    (forall step domain,
       In (DomainMemory domain) (input_footprint step) ->
       input_hart binding step = bi_hart_of binding domain).
Proof.
  intros binding; split.
  - intros [step | [| domain | domain]] object Hin; simpl in Hin |- *;
      [apply in_map_iff in Hin as [? [? _]]; discriminate | ..];
      repeat destruct Hin as [Hin | Hin]; try discriminate;
      try contradiction; injection Hin as <-; reflexivity.
  - intros step domain Hin.
    destruct (input_footprint_kinds _ _ Hin) as [[? ?] | [? [-> Hsame]]];
      [discriminate |].
    injection Hsame as <-; reflexivity.
Qed.

(**
 * A domain's input records, and what they lie apart from: every block's
 * inbound and outbound rings, every domain's memory, and every other
 * domain's records (mvp-layout.h: BE_MVP_INPUT_RING_OFFSET,
 * BE_MVP_BLOCK_INBOUND_OFFSET, BE_MVP_BLOCK_OUTBOUND_OFFSET, and sizes).
 *)
Definition input_records (binding : binding_instance) (domain : nat)
    : extent :=
  mk_extent (bi_block binding domain + 0xd000) 0x1000.

Definition input_apart (binding : binding_instance) (domain : nat)
    : list extent :=
  flat_map (fun other =>
      [mk_extent (bi_block binding other + 0x4000) 0x1000;
       mk_extent (bi_block binding other + 0x5000) 0x8000] ++
      domain_memory binding other ++
      (if domain =? other then [] else [input_records binding other]))
    (bi_domains binding).

(**
 * [input_ring_disjoint_from_control]: in the one object set no input step
 * writes an object any Binding.v step writes, so the input path writes no
 * control ring word and Binding.v's H3 stands as proved; and in the MVP
 * binding each domain's input records lie apart from every block's two
 * control rings, every domain's memory (its window, the shared pages), and
 * the other domain's records. Its indices and stage lie in the state page
 * (mvp-runtime.c's static assert holds the hart page there) and its
 * routing state in hart 0's data, extents H2 holds apart from domain memory.
 *)
Theorem input_ring_disjoint_from_control :
  (forall binding input_step binding_step object,
     In object (system_footprint binding (InputStep input_step)) ->
     ~ In object (system_footprint binding (BindingStep binding_step))) /\
  (forall domain extent,
     In domain (bi_domains mvp_binding) ->
     In extent (input_apart mvp_binding domain) ->
     extents_disjoint (input_records mvp_binding domain) extent).
Proof.
  split.
  - intros binding input_step binding_step object Hinput Hbinding.
    simpl in Hbinding.
    apply in_map_iff in Hbinding as [other [<- _]].
    destruct (input_footprint_kinds _ _ Hinput) as [[? ?] | [? [_ ?]]];
      discriminate.
  - intros domain extent Hdomain Hextent.
    apply (all_disjoint_sound [input_records mvp_binding domain]
             (input_apart mvp_binding domain));
      [| left; reflexivity | exact Hextent].
    simpl in Hdomain.
    destruct Hdomain as [<- | [<- | []]]; vm_compute; reflexivity.
Qed.

(**
 * [flush] is the drop rule (D-4; be_mvp_input_flush): of [pending] batched
 * bytes, the first [Nat.min room pending] are posted, [room] being
 * be_mvp_ring_room's answer, and the rest dropped as ring-full.
 * [input_drop_rule]: the rule is total, so a full ring fails nothing; it
 * conserves bytes; it never posts past the room, so the ring is never
 * overrun; and it drops exactly when the batch exceeds the room.
 *)
Definition flush (room pending : nat) : nat * nat :=
  (Nat.min room pending, pending - Nat.min room pending).

Theorem input_drop_rule :
  forall room pending,
    fst (flush room pending) + snd (flush room pending) = pending /\
    fst (flush room pending) <= room /\
    (snd (flush room pending) = 0 <-> pending <= room).
Proof.
  intros room pending; unfold flush; simpl.
  split; [rewrite Nat.add_comm; apply Nat.sub_add, Nat.le_min_r |].
  split; [apply Nat.le_min_l | split; intros Hle].
  - apply Nat.sub_0_le in Hle.
    exact (Nat.le_trans _ _ _ Hle (Nat.le_min_l room pending)).
  - rewrite Nat.min_r by exact Hle; apply Nat.sub_diag.
Qed.

(**
 * The focus parser (D-3): three states, five byte classes ([classify]:
 * '~', '0', '1', CR or LF, other), and four kinds; [focus_table] is
 * mvp-input.c's focus_table cell by cell, and [focus_step] is
 * be_mvp_focus_step, whose refusal of a fourth state has none to refuse.
 *)
Inductive focus_state : Type := LineStart | AfterPrefix | InLine.
Inductive byte_class : Type :=
| ClassPrefix | ClassDigit0 | ClassDigit1 | ClassEnd | ClassOther.
Inductive focus_kind : Type := Deliver | Select | Drop | Hold.

Definition classify (byte : N) : byte_class :=
  if (byte =? 0x7e)%N then ClassPrefix
  else if (byte =? 0x30)%N then ClassDigit0
  else if (byte =? 0x31)%N then ClassDigit1
  else if ((byte =? 0x0d)%N || (byte =? 0x0a)%N)%bool then ClassEnd
  else ClassOther.

Definition focus_table (state : focus_state) (class : byte_class)
    : focus_kind * focus_state :=
  match state, class with
  | LineStart, ClassPrefix => (Hold, AfterPrefix)
  | LineStart, ClassDigit0 => (Deliver, InLine)
  | LineStart, ClassDigit1 => (Deliver, InLine)
  | LineStart, ClassEnd => (Deliver, LineStart)
  | LineStart, ClassOther => (Deliver, InLine)
  | AfterPrefix, ClassPrefix => (Deliver, InLine)
  | AfterPrefix, ClassDigit0 => (Select, LineStart)
  | AfterPrefix, ClassDigit1 => (Select, LineStart)
  | AfterPrefix, ClassEnd => (Drop, LineStart)
  | AfterPrefix, ClassOther => (Drop, LineStart)
  | InLine, ClassPrefix => (Deliver, InLine)
  | InLine, ClassDigit0 => (Deliver, InLine)
  | InLine, ClassDigit1 => (Deliver, InLine)
  | InLine, ClassEnd => (Deliver, LineStart)
  | InLine, ClassOther => (Deliver, InLine)
  end.

Definition focus_step (state : focus_state) (byte : N)
    : focus_kind * focus_state :=
  focus_table state (classify byte).

(* A selecting digit's domain: out->domain in be_mvp_focus_step. *)
Definition select_domain (byte : N) : nat :=
  match classify byte with ClassDigit1 => 1 | _ => 0 end.

(** A drop's reason (enum be_mvp_input_drop), and one byte's route. *)
Inductive drop_reason : Type :=
| NoFocus | NoGrant | NotRunning | RingFull | BadSequence | BeforeArmed.

Inductive route : Type :=
| RouteDeliver (domain : nat) (byte : N)
| RouteSelect (domain : nat)
| RouteDrop (reason : drop_reason)
| RouteHold.

(**
 * [route_byte] is be_mvp_input_byte after the first poll: from the sealed
 * console grants, the focus, the domains hart 0 holds running, the
 * parser's state, and one byte, its route, the next focus, and the
 * parser's next state. [routed grants] is every focus and parser state
 * reached from arming (no focus, a line's start; be_mvp_input_arm) by any
 * bytes, each routed with any domains running.
 *)
Definition route_byte (grants running : nat -> bool) (focus : option nat)
    (state : focus_state) (byte : N) : route * option nat * focus_state :=
  let (kind, next) := focus_step state byte in
  match kind with
  | Deliver =>
      (match focus with
       | Some domain =>
           if negb (grants domain) then RouteDrop NoFocus
           else if negb (running domain) then RouteDrop NotRunning
           else RouteDeliver domain byte
       | None => RouteDrop NoFocus
       end, focus, next)
  | Select =>
      if grants (select_domain byte)
      then (RouteSelect (select_domain byte), Some (select_domain byte), next)
      else (RouteDrop NoGrant, focus, next)
  | Drop => (RouteDrop BadSequence, focus, next)
  | Hold => (RouteHold, focus, next)
  end.

Inductive routed (grants : nat -> bool) : option nat -> focus_state -> Prop :=
| routed_armed : routed grants None LineStart
| routed_byte : forall running focus state byte verdict focus' state',
    routed grants focus state ->
    route_byte grants running focus state byte = (verdict, focus', state') ->
    routed grants focus' state'.

Lemma route_byte_focus :
  forall grants running focus state byte verdict focus' state',
    route_byte grants running focus state byte = (verdict, focus', state') ->
    (forall domain delivered, verdict = RouteDeliver domain delivered ->
       focus = Some domain /\ grants domain = true /\
       running domain = true /\ delivered = byte) /\
    (focus' = focus \/
     exists domain, verdict = RouteSelect domain /\
       grants domain = true /\ focus' = Some domain).
Proof.
  intros grants running focus state byte verdict focus' state' Hroute.
  unfold route_byte in Hroute.
  destruct (focus_step state byte) as [[] next]; cbv beta iota in Hroute.
  - destruct focus as [domain |];
      [destruct (grants domain) eqn:Hgrant, (running domain) eqn:Hrunning |];
      simpl in Hroute; injection Hroute as <- <- _; split; auto;
      intros ? ? Hsame; try discriminate; injection Hsame as <- <-; auto.
  - destruct (grants (select_domain byte)) eqn:Hgrant;
      injection Hroute as <- <- _; split; try discriminate; eauto.
  - injection Hroute as <- <- _; split; [discriminate | auto].
  - injection Hroute as <- <- _; split; [discriminate | auto].
Qed.

(**
 * [input_routing_to_focus] (I17 at the model's level): from arming, the
 * focus is only ever a granted domain; a delivered byte is the typed byte
 * and goes to the current focus, granted and running; the focus changes
 * only by a selection of a granted domain, so one naming an ungranted
 * domain leaves it as it was; and a byte for a focus that is not running
 * is dropped as not-running.
 *)
Theorem input_routing_to_focus :
  forall grants focus state,
    routed grants focus state ->
    (forall domain, focus = Some domain -> grants domain = true) /\
    (forall running byte verdict focus' state',
       route_byte grants running focus state byte = (verdict, focus', state') ->
       (forall domain delivered, verdict = RouteDeliver domain delivered ->
          focus = Some domain /\ grants domain = true /\
          running domain = true /\ delivered = byte) /\
       (focus' = focus \/
        exists domain, verdict = RouteSelect domain /\
          grants domain = true /\ focus' = Some domain) /\
       (forall domain, fst (focus_step state byte) = Deliver ->
          focus = Some domain -> running domain = false ->
          verdict = RouteDrop NotRunning)).
Proof.
  intros grants focus state Hrouted.
  assert (Hgranted :
            forall domain, focus = Some domain -> grants domain = true).
  { induction Hrouted as [| running focus state byte verdict focus' state'
                            _ IH Hroute]; [discriminate |].
    intros domain Hfocus.
    destruct (route_byte_focus _ _ _ _ _ _ _ _ Hroute)
      as [_ [-> | [other [_ [Hgrant Hsome]]]]]; [exact (IH domain Hfocus) |].
    rewrite Hfocus in Hsome; injection Hsome as ->; exact Hgrant. }
  split; [exact Hgranted |].
  intros running byte verdict focus' state' Hroute.
  destruct (route_byte_focus _ _ _ _ _ _ _ _ Hroute) as [Hdeliver Hfocus'].
  split; [exact Hdeliver | split; [exact Hfocus' |]].
  intros domain Hkind Hfocus Hrunning.
  unfold route_byte in Hroute.
  destruct (focus_step state byte) as [kind next].
  simpl in Hkind; subst kind.
  rewrite Hfocus, (Hgranted domain Hfocus), Hrunning in Hroute.
  simpl in Hroute; injection Hroute as <- _ _.
  reflexivity.
Qed.
