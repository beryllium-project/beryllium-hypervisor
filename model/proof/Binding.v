(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * The MVP's static hart binding over the abstract model (MVP M3, work
 * package M3-3; security model v1, Revision 1, I13 to I16): harts,
 * domains, the binding, the monitor-owned objects Revision 1 classifies,
 * the two phases around the boot barrier, and a transition vocabulary read
 * from the MVP's control loop and fast path with a total write footprint
 * per transition. The obligations H0 to H3 are stated over any binding and
 * proved for the MVP's three-hart instance. They concern the static binding
 * and which hart takes which transition; they say nothing about concurrent
 * execution, memory ordering, the IPI protocol, or the barrier's
 * implementation, which the MVP plan names as unmodeled. Model 0.2 is not a
 * binding instance: its two domains share one hart by checked switches,
 * outside I13 to I16's scope (Revision 1, R1.2).
 *)

From Stdlib Require Import Bool List PeanoNat NArith.
Import ListNotations.

(** [hart] is a hart number: configuration data, not authority (S1 H03). *)
Definition hart := nat.

(**
 * [extent] is the physical byte range from [extent_base] up to, and not
 * including, [extent_base + extent_size].
 *)
Record extent : Type := mk_extent {
  extent_base : N;
  extent_size : N
}.

Definition extents_disjoint (left right : extent) : Prop :=
  (extent_base left + extent_size left <= extent_base right)%N \/
  (extent_base right + extent_size right <= extent_base left)%N.

Definition extents_disjointb (left right : extent) : bool :=
  N.leb (extent_base left + extent_size left) (extent_base right) ||
  N.leb (extent_base right + extent_size right) (extent_base left).

Lemma extents_disjointb_sound :
  forall left right,
    extents_disjointb left right = true -> extents_disjoint left right.
Proof.
  intros left right Hcheck.
  unfold extents_disjointb in Hcheck.
  apply orb_true_iff in Hcheck as [Hbelow | Habove].
  - left.
    apply N.leb_le.
    exact Hbelow.
  - right.
    apply N.leb_le.
    exact Habove.
Qed.

(*
 * The MVP layout (mvp/src/mvp-layout.h, M0 to M2): the accepted image at
 * the monitor's base, the hart region with one 64 KiB block per domain
 * hart, the MVP region, the two domain windows, and the shared pages that
 * hold every channel page and the secret page. Each value is the macro
 * named by its definition: BE_MVP_MONITOR_HPA, BE_MVP_ACCEPTED_IMAGE_BYTES,
 * BE_MVP_G0_BLOCK_HPA, BE_MVP_G1_BLOCK_HPA, BE_MVP_REGION_HPA,
 * BE_MVP_REGION_BYTES, BE_MVP_G0_HPA, BE_MVP_G1_HPA, BE_MVP_GUEST_BYTES,
 * BE_MVP_SHARED_PAGES_HPA, and BE_MVP_SHARED_PAGES_BYTES.
 *)
Definition mvp_monitor_hpa : N := 0x102000000.
Definition mvp_accepted_image_bytes : N := 0x34000.
Definition mvp_g0_block_hpa : N := 0x102044000.
Definition mvp_g1_block_hpa : N := 0x102054000.
Definition mvp_region_hpa : N := 0x102064000.
Definition mvp_region_bytes : N := 0x40000.
Definition mvp_g0_hpa : N := 0x110000000.
Definition mvp_g1_hpa : N := 0x114000000.
Definition mvp_guest_bytes : N := 0x4000000.
Definition mvp_shared_pages_hpa : N := 0x118000000.
Definition mvp_shared_pages_bytes : N := 0x3000.

(* A block's private pages, by the BE_MVP_BLOCK_ offsets and sizes. *)
Definition block_stack_offset : N := 0x0.
Definition block_stack_bytes : N := 0x2000.
Definition block_saved_offset : N := 0x2000.
Definition block_saved_bytes : N := 0x1000.
Definition block_state_offset : N := 0x3000.
Definition block_state_bytes : N := 0x1000.

(**
 * [ring] names one of a domain's two rings in its hart's block: the
 * inbound ring, which the control hart writes and the domain hart reads,
 * and the outbound ring, which the domain hart writes and the control hart
 * reads (mvp-layout.h, "The NOLOAD hart region"; mvp-hart.h).
 *)
Inductive ring : Type :=
| InboundRing (domain : nat)
| OutboundRing (domain : nat).

(**
 * [hart_object] enumerates the monitor-owned objects of Revision 1's I15
 * and I16 (R1.2), each domain's indexed by the domain whose hart runs its
 * block:
 *
 * - private to the domain's hart after the barrier (I15): the trusted stack
 *   (block 0x0, 0x2000), the saved frame (0x2000, 0x1000), and the state
 *   page's words the hart alone writes, [StateControls] (controls),
 *   [StateCore] (state, the SBI core's mutable words), [StateEntered]
 *   (entered), and [HartRingViews], the hart's own views of its two rings
 *   (mvp-platform.h, struct be_mvp_hart_page), which mvp-hartmain.c:547-548
 *   names the hart's from the barrier on, as it does the SBI core's state;
 *   R1.2's parenthesis lists the state page's words and not the views;
 * - immutable published data (I16): the block descriptor with its
 *   generation word, the first-entry frame, the walked map and leaves, the
 *   state's configuration (its exit ceiling and its denial and management
 *   flags), hart 0's binding table (const, mvp-runtime.c:244), and each
 *   domain's G-stage root and tables in the pool, which hart 0 builds before
 *   the barrier and no hart writes after it (M0 plan, boot step 5; R1.2's
 *   list does not name the pool);
 * - ring state (I16): each ring's records and head, its writer's, and its
 *   tail, its reader's;
 * - the control hart's own state, private to it and not shared (I16,
 *   review erratum 6): its data, the management state among it
 *   (mvp-hart.h, struct be_mvp_mgmt_state), and its trusted stack.
 *)
Inductive hart_object : Type :=
| BlockStack (domain : nat)
| BlockSaved (domain : nat)
| StateControls (domain : nat)
| StateCore (domain : nat)
| StateEntered (domain : nat)
| HartRingViews (domain : nat)
| BlockDescriptor (domain : nat)
| BlockEntryFrame (domain : nat)
| BlockWalked (domain : nat)
| StateConfiguration (domain : nat)
| DomainRoot (domain : nat)
| BindingTable
| RingRecords (channel : ring)
| RingHead (channel : ring)
| RingTail (channel : ring)
| ControlData
| ControlStack.

(**
 * [binding_instance] is a static binding: the control hart, the started
 * harts (the never-started harts are outside the model), the domains by
 * domain index, [bi_hart_of], each domain hart's block, each domain's
 * window, the shared pages, and the two extents that hold the control
 * hart's own stack and data. Domain indices are the MVP sources'; the
 * policy view names the same domains by subject id (index plus one).
 *)
Record binding_instance : Type := mk_binding_instance {
  bi_control : hart;
  bi_harts : list hart;
  bi_domains : list nat;
  bi_hart_of : nat -> hart;
  bi_block : nat -> N;
  bi_window : nat -> extent;
  bi_pages : extent;
  bi_accepted_image : extent;
  bi_mvp_region : extent
}.

(** [private_owner] is the hart an object is private to, after the barrier. *)
Definition private_owner (binding : binding_instance) (object : hart_object)
    : option hart :=
  match object with
  | BlockStack domain | BlockSaved domain | StateControls domain
  | StateCore domain | StateEntered domain | HartRingViews domain =>
      Some (bi_hart_of binding domain)
  | ControlData | ControlStack => Some (bi_control binding)
  | _ => None
  end.

(** [published] holds for immutable published data. *)
Definition published (object : hart_object) : bool :=
  match object with
  | BlockDescriptor _ | BlockEntryFrame _ | BlockWalked _
  | StateConfiguration _ | DomainRoot _ | BindingTable => true
  | _ => false
  end.

(** [ring_writer] writes a ring's records and head; [ring_reader] its tail. *)
Definition ring_writer (binding : binding_instance) (channel : ring) : hart :=
  match channel with
  | InboundRing _ => bi_control binding
  | OutboundRing domain => bi_hart_of binding domain
  end.

Definition ring_reader (binding : binding_instance) (channel : ring) : hart :=
  match channel with
  | InboundRing domain => bi_hart_of binding domain
  | OutboundRing _ => bi_control binding
  end.

(** [domain_objects] is one domain's objects; [objects] all of them. *)
Definition domain_objects (domain : nat) : list hart_object :=
  [BlockStack domain; BlockSaved domain; StateControls domain;
   StateCore domain; StateEntered domain; HartRingViews domain;
   BlockDescriptor domain; BlockEntryFrame domain; BlockWalked domain;
   StateConfiguration domain; DomainRoot domain;
   RingRecords (InboundRing domain); RingHead (InboundRing domain);
   RingTail (InboundRing domain);
   RingRecords (OutboundRing domain); RingHead (OutboundRing domain);
   RingTail (OutboundRing domain)].

Definition objects (binding : binding_instance) : list hart_object :=
  BindingTable :: ControlData :: ControlStack ::
  flat_map domain_objects (bi_domains binding).

(**
 * [object_extents] is where each private object lies (H2): a domain
 * hart's stack and saved page exactly, its state-page words within the
 * state page, the control hart's stack within the accepted image (the R3
 * trusted stack, top 0x102027000, mvp-runtime.c:151), and its data within
 * the accepted image and the MVP region; mvp-layout.h gives no finer
 * bound for the last two, so they are containing extents. Other objects
 * need no extent here.
 *)
Definition object_extents (binding : binding_instance) (object : hart_object)
    : list extent :=
  match object with
  | BlockStack domain =>
      [mk_extent (bi_block binding domain + block_stack_offset)
         block_stack_bytes]
  | BlockSaved domain =>
      [mk_extent (bi_block binding domain + block_saved_offset)
         block_saved_bytes]
  | StateControls domain | StateCore domain | StateEntered domain
  | HartRingViews domain =>
      [mk_extent (bi_block binding domain + block_state_offset)
         block_state_bytes]
  | ControlData => [bi_accepted_image binding; bi_mvp_region binding]
  | ControlStack => [bi_accepted_image binding]
  | _ => []
  end.

(**
 * [domain_memory] is a domain's memory: its window and the shared pages
 * that hold every channel page and the secret page. [root_extents] is all
 * a domain's root can map: its window and, of the shared pages, only the
 * pages its scenario declares (mvp-layout.h, "The shared pages").
 *)
Definition domain_memory (binding : binding_instance) (domain : nat)
    : list extent :=
  [bi_window binding domain; bi_pages binding].

Definition root_extents (binding : binding_instance) (domain : nat)
    : list extent :=
  [bi_window binding domain; bi_pages binding].

(** [barrier_phase] is a transition's side of the boot barrier. *)
Inductive barrier_phase : Type :=
| BeforeBarrier
| AfterBarrier.

(**
 * [transition] is the vocabulary of the MVP monitor's steps, enumerated
 * from hart 0's boot sequence, publication, and control loop
 * (mvp/src/mvp-runtime.c) and from a domain hart's entry and fast path
 * (mvp/src/mvp-hartmain.c), as the M0 to M2 plans describe them. A domain
 * argument names the domain whose hart takes the step, or, for hart 0's
 * steps, the domain whose ring it touches: the target of a delivery and
 * the requester of an answer.
 *)
Inductive transition : Type :=
| Prepare
| Publish
| Start (domain : nat)
| Ready (domain : nat)
| Entered (domain : nat)
| ExitRecord (domain : nat)
| Drain (domain : nat)
| Ping (domain : nat)
| Pong (domain : nat)
| Request (domain : nat)
| DecideDeliver (domain : nat)
| Answer (domain : nat)
| Pause (domain : nat)
| Terminate (domain : nat)
| Park (domain : nat)
| Shutdown (domain : nat)
| FailRecord (domain : nat)
| Acknowledge (domain : nat)
| Wake
| RunEnd.

(** [transition_hart] is the hart that takes a transition. *)
Definition transition_hart (binding : binding_instance) (step : transition)
    : hart :=
  match step with
  | Prepare | Publish | Start _ | Drain _ | Ping _ | DecideDeliver _
  | Answer _ | Acknowledge _ | Wake | RunEnd => bi_control binding
  | Ready domain | Entered domain | ExitRecord domain | Pong domain
  | Request domain | Pause domain | Terminate domain | Park domain
  | Shutdown domain | FailRecord domain => bi_hart_of binding domain
  end.

(**
 * [transition_phase]: hart 0's preparation and publication come before
 * the barrier, whose last write, the generation words, is the
 * publication's (mvp-runtime.c:1506-1509); every other step comes after
 * it. The domain harts are started after it (mvp-runtime.c:2201-2202, 2108;
 * M0 plan, boot steps 4 and 5).
 *)
Definition transition_phase (step : transition) : barrier_phase :=
  match step with
  | Prepare | Publish => BeforeBarrier
  | _ => AfterBarrier
  end.

(* Hart 0's own state, written by each of its steps. *)
Definition control_own : list hart_object := [ControlData; ControlStack].

(*
 * The publication's writes into one domain hart's block
 * (mvp-runtime.c:1471-1505): the whole hart page zeroed (1475), the
 * descriptor (1476), the first-entry frame (1481), the walked map and
 * leaves (1485-1488), the state's configuration (1489-1491), zero ring
 * indices (be_mvp_ring_reset, 1447) and both ring views, the domain hart's
 * among them (1492-1503), and the generation word last (1507-1509). It
 * writes neither the block's stack and saved page nor any ring's records.
 *)
Definition block_publication (domain : nat) : list hart_object :=
  [StateControls domain; StateCore domain; StateEntered domain;
   HartRingViews domain; BlockDescriptor domain; BlockEntryFrame domain;
   BlockWalked domain; StateConfiguration domain;
   RingHead (InboundRing domain); RingTail (InboundRing domain);
   RingHead (OutboundRing domain); RingTail (OutboundRing domain)].

(*
 * A domain hart's writes on any exit it serves: its trusted stack, the
 * saved frame (the vector, mvp-trap.S:424-545, and the dispatch's return,
 * mvp-hartmain.c:502), and the SBI core's state (be_mvp_handle_exit,
 * mvp-hartmain.c:467).
 *)
Definition exit_own (domain : nat) : list hart_object :=
  [BlockStack domain; BlockSaved domain; StateCore domain].

(*
 * A domain hart's post to its outbound ring: its view, the records, and,
 * by the publish, the head (mvp-hartmain.c:69-73; mvp-ring.c
 * be_mvp_ring_post and be_mvp_ring_publish).
 *)
Definition outbound_post (domain : nat) : list hart_object :=
  [HartRingViews domain; RingRecords (OutboundRing domain);
   RingHead (OutboundRing domain)].

(*
 * Hart 0's post to a domain's inbound ring (mvp-runtime.c:1568-1582,
 * post_inbound): its own view, the records, and, by the publish, the head.
 *)
Definition inbound_post (domain : nat) : list hart_object :=
  control_own ++
  [RingRecords (InboundRing domain); RingHead (InboundRing domain)].

(**
 * [footprint] is each transition's total write footprint over the objects
 * above, read from the MVP sources at the M2 result (18d552bc); CSR writes,
 * firmware calls, and the console are not monitor-owned memory.
 *)
Definition footprint (binding : binding_instance) (step : transition)
    : list hart_object :=
  match step with
  (* mvp-runtime.c:2133-2200: hart 0's BSS cleared, the R3 prelude, the
     probes, both roots built and re-walked into the pool (build_gstage),
     the windows and pages cleared and placed, the measurement into its
     own data; it also writes the windows and shared pages, domain memory
     outside this classification, and no hart-region word. *)
  | Prepare =>
      map DomainRoot (bi_domains binding) ++ control_own
  (* mvp-runtime.c:1465-1511, publish_blocks. *)
  | Publish =>
      flat_map block_publication (bi_domains binding) ++ control_own
  (* mvp-runtime.c:2076-2108 and 1517-1561: the budget's CSRs, the control
     loop's and the management state's initialization, hart_start and
     hart_get_status, BE_MVP:08, be_mvp_control_started. *)
  | Start _ => control_own
  (* mvp-hartmain.c:525-579: the generation word and the descriptor read,
     the CSRs armed with their readbacks into controls (567), the one
     install, entered (578), and READY posted (579). *)
  | Ready domain =>
      [BlockStack domain; StateControls domain; StateEntered domain;
       HartRingViews domain; RingRecords (OutboundRing domain)]
  (* mvp-hartmain.c:580-585: ENTERED posted and published, one IPI, the
     first-entry frame copied into the saved page, the resume tail. *)
  | Entered domain =>
      [BlockStack domain; BlockSaved domain] ++ outbound_post domain
  (* mvp-hartmain.c:459-505, the dispatch: SBI calls, a console's LINE
     records (239-271), a timer, and an accepted denial's injection,
     DENIAL record, and frame (432-456). *)
  | ExitRecord domain => exit_own domain ++ outbound_post domain
  (* mvp-runtime.c:1921-1948, one visit: acquire, take into hart 0's copy,
     release the outbound tail, then step the record (1810-1876). *)
  | Drain domain => control_own ++ [RingTail (OutboundRing domain)]
  (* mvp-runtime.c:1585-1589, ping. *)
  | Ping domain => inbound_post domain
  (* mvp-hartmain.c:330-344, the IPI exit: the inbound tail released and a
     PONG posted (mvp-sbi.c:610-728). *)
  | Pong domain =>
      exit_own domain ++ outbound_post domain ++ [RingTail (InboundRing domain)]
  (* mvp-hartmain.c:389-417 and 279-300: MGMT_REQUEST posted, then the wait
     in HS, taking the MGMT_RESULT and answering any PING. *)
  | Request domain =>
      exit_own domain ++ outbound_post domain ++ [RingTail (InboundRing domain)]
  (* mvp-runtime.c:1844-1846 and 1633-1641: the decision against the sealed
     grants in hart 0's management state, then PAUSE or TERMINATE posted
     to the target's inbound ring. *)
  | DecideDeliver domain => inbound_post domain
  (* mvp-runtime.c:1599-1626, answer: MGMT_RESULT to the requester. *)
  | Answer domain => inbound_post domain
  (* mvp-hartmain.c:330-349 and mvp-sbi.c:642-664: PAUSE taken, the phase
     and requester recorded, PAUSED posted, then the paused park. *)
  | Pause domain =>
      exit_own domain ++ outbound_post domain ++ [RingTail (InboundRing domain)]
  (* mvp-sbi.c:647-664, from the IPI exit (mvp-hartmain.c:330-349) or the
     paused park (310-320): TERMINATE taken, TERMINATED posted. *)
  | Terminate domain =>
      exit_own domain ++ outbound_post domain ++ [RingTail (InboundRing domain)]
  (* mvp-trap.S's park writes nothing; a paused or terminated hart's wake
     (mvp-hartmain.c:310-320, 279-300) acquires and releases its empty
     inbound ring. *)
  | Park domain =>
      [BlockStack domain; HartRingViews domain; RingTail (InboundRing domain)]
  (* mvp-hartmain.c:353-370, the SRST exit: the partial line flushed,
     SHUTDOWN posted and published, one IPI, the park. *)
  | Shutdown domain => exit_own domain ++ outbound_post domain
  (* mvp-hartmain.c:145-182: FAIL posted and published, one IPI, then the
     wait for hart 0's ACK, which takes from the inbound ring and releases
     nothing (85-103), or the hart's own lines through DBCN and SRST. *)
  | FailRecord domain => exit_own domain ++ outbound_post domain
  (* mvp-runtime.c:1693-1711: the domain's FAIL lines and the ACK posted
     and published into its inbound ring, then hart 0's terminal path. *)
  | Acknowledge domain => inbound_post domain
  (* mvp-runtime.c:2029-2043 and 1994-2020: the wait, the wake's counters,
     the SSIP clear, and the READY wait. *)
  | Wake => control_own
  (* mvp-runtime.c:1672-1684 and 730-776: BE_MVP:13 and :14 or a FAIL and
     DETAIL line, then SRST. *)
  | RunEnd => control_own
  end.

(** [domain_transitions] is one domain's steps; [transitions] all of them. *)
Definition domain_transitions (domain : nat) : list transition :=
  [Start domain; Ready domain; Entered domain; ExitRecord domain;
   Drain domain; Ping domain; Pong domain; Request domain;
   DecideDeliver domain; Answer domain; Pause domain; Terminate domain;
   Park domain; Shutdown domain; FailRecord domain; Acknowledge domain].

Definition transitions (binding : binding_instance) : list transition :=
  Prepare :: Publish :: Wake :: RunEnd ::
  flat_map domain_transitions (bi_domains binding).

(*
 * The obligations over a binding.
 *)

(** [H0]: every domain's hart is not the control hart. *)
Definition H0 (binding : binding_instance) : Prop :=
  forall domain,
    In domain (bi_domains binding) ->
    bi_hart_of binding domain <> bi_control binding.

(**
 * [H1] (I13, I14): the binding is injective, each hart running at most one
 * domain, and total into the started harts other than the control hart,
 * each domain running on exactly one; it says nothing about started harts
 * that run no domain.
 *)
Definition H1 (binding : binding_instance) : Prop :=
  (forall domain1 domain2,
     In domain1 (bi_domains binding) -> In domain2 (bi_domains binding) ->
     bi_hart_of binding domain1 = bi_hart_of binding domain2 ->
     domain1 = domain2) /\
  (forall domain,
     In domain (bi_domains binding) ->
     In (bi_hart_of binding domain) (bi_harts binding) /\
     bi_hart_of binding domain <> bi_control binding).

(**
 * [H2] (I15): each hart's private objects lie in extents disjoint from
 * every other hart's private objects, from every domain's memory, and from
 * all every domain's root can map; and each has an extent.
 *)
Definition H2 (binding : binding_instance) : Prop :=
  (forall object owner,
     In object (objects binding) -> private_owner binding object = Some owner ->
     object_extents binding object <> []) /\
  (forall object1 object2 owner1 owner2,
     In object1 (objects binding) -> In object2 (objects binding) ->
     private_owner binding object1 = Some owner1 ->
     private_owner binding object2 = Some owner2 ->
     owner1 <> owner2 ->
     forall extent1 extent2,
       In extent1 (object_extents binding object1) ->
       In extent2 (object_extents binding object2) ->
       extents_disjoint extent1 extent2) /\
  (forall object owner domain,
     In object (objects binding) -> private_owner binding object = Some owner ->
     In domain (bi_domains binding) ->
     forall extent1 extent2,
       In extent1 (object_extents binding object) ->
       In extent2 (domain_memory binding domain) ->
       extents_disjoint extent1 extent2) /\
  (forall object owner domain,
     In object (objects binding) -> private_owner binding object = Some owner ->
     In domain (bi_domains binding) ->
     forall extent1 extent2,
       In extent1 (object_extents binding object) ->
       In extent2 (root_extents binding domain) ->
       extents_disjoint extent1 extent2).

(**
 * [H3] (I16): before the barrier only the control hart writes; after it no
 * transition writes immutable published data, a ring's records and head
 * are written only by its writer and its tail only by its reader, and every
 * private object a transition writes is its own hart's, so no domain hart
 * writes another hart's private state and the control hart writes none of
 * a domain hart's (I15).
 *)
Definition H3 (binding : binding_instance) : Prop :=
  (forall step object,
     In step (transitions binding) -> transition_phase step = BeforeBarrier ->
     In object (footprint binding step) ->
     transition_hart binding step = bi_control binding) /\
  (forall step object,
     In step (transitions binding) -> transition_phase step = AfterBarrier ->
     In object (footprint binding step) -> published object = false) /\
  (forall step channel,
     In step (transitions binding) -> transition_phase step = AfterBarrier ->
     (In (RingRecords channel) (footprint binding step) \/
      In (RingHead channel) (footprint binding step)) ->
     transition_hart binding step = ring_writer binding channel) /\
  (forall step channel,
     In step (transitions binding) -> transition_phase step = AfterBarrier ->
     In (RingTail channel) (footprint binding step) ->
     transition_hart binding step = ring_reader binding channel) /\
  (forall step object owner,
     In step (transitions binding) -> transition_phase step = AfterBarrier ->
     In object (footprint binding step) ->
     private_owner binding object = Some owner ->
     owner = transition_hart binding step).

(* Executable forms of H2 and H3, for a finite binding. *)

Definition all_disjoint (extents1 extents2 : list extent) : bool :=
  forallb (fun extent1 => forallb (extents_disjointb extent1) extents2)
    extents1.

Definition private_ok (binding : binding_instance) (object : hart_object)
    : bool :=
  match private_owner binding object with
  | Some owner =>
      negb (match object_extents binding object with
            | [] => true
            | _ :: _ => false
            end) &&
      forallb (fun other =>
          match private_owner binding other with
          | Some other_owner =>
              (owner =? other_owner) ||
              all_disjoint (object_extents binding object)
                (object_extents binding other)
          | None => true
          end) (objects binding) &&
      forallb (fun domain =>
          all_disjoint (object_extents binding object)
            (domain_memory binding domain) &&
          all_disjoint (object_extents binding object)
            (root_extents binding domain)) (bi_domains binding)
  | None => true
  end.

Definition h2_check (binding : binding_instance) : bool :=
  forallb (private_ok binding) (objects binding).

Definition write_ok (binding : binding_instance) (step : transition)
    (object : hart_object) : bool :=
  match transition_phase step with
  | BeforeBarrier => transition_hart binding step =? bi_control binding
  | AfterBarrier =>
      negb (published object) &&
      match object with
      | RingRecords channel | RingHead channel =>
          transition_hart binding step =? ring_writer binding channel
      | RingTail channel =>
          transition_hart binding step =? ring_reader binding channel
      | _ => true
      end &&
      match private_owner binding object with
      | Some owner => owner =? transition_hart binding step
      | None => true
      end
  end.

Definition h3_check (binding : binding_instance) : bool :=
  forallb (fun step => forallb (write_ok binding step) (footprint binding step))
    (transitions binding).

Lemma all_disjoint_sound :
  forall extents1 extents2 extent1 extent2,
    all_disjoint extents1 extents2 = true ->
    In extent1 extents1 -> In extent2 extents2 ->
    extents_disjoint extent1 extent2.
Proof.
  intros extents1 extents2 extent1 extent2 Hcheck Hin1 Hin2.
  unfold all_disjoint in Hcheck.
  rewrite forallb_forall in Hcheck.
  specialize (Hcheck extent1 Hin1).
  rewrite forallb_forall in Hcheck.
  apply extents_disjointb_sound.
  exact (Hcheck extent2 Hin2).
Qed.

Lemma h2_check_sound :
  forall binding, h2_check binding = true -> H2 binding.
Proof.
  intros binding Hcheck.
  unfold h2_check in Hcheck.
  rewrite forallb_forall in Hcheck.
  split; [| split; [| split]].
  - intros object owner Hobject Howner Hempty.
    specialize (Hcheck object Hobject).
    unfold private_ok in Hcheck.
    rewrite Howner, Hempty in Hcheck.
    discriminate.
  - intros object1 object2 owner1 owner2 Hobject1 Hobject2 Howner1 Howner2
      Hdistinct extent1 extent2 Hin1 Hin2.
    specialize (Hcheck object1 Hobject1).
    unfold private_ok in Hcheck.
    rewrite Howner1 in Hcheck.
    apply andb_true_iff in Hcheck as [[_ Hothers]%andb_true_iff _].
    rewrite forallb_forall in Hothers.
    specialize (Hothers object2 Hobject2).
    rewrite Howner2 in Hothers.
    apply orb_true_iff in Hothers as [Hsame | Hdisjoint].
    + apply Nat.eqb_eq in Hsame.
      contradiction.
    + exact (all_disjoint_sound _ _ _ _ Hdisjoint Hin1 Hin2).
  - intros object owner domain Hobject Howner Hdomain extent1 extent2 Hin1 Hin2.
    specialize (Hcheck object Hobject).
    unfold private_ok in Hcheck.
    rewrite Howner in Hcheck.
    apply andb_true_iff in Hcheck as [_ Hdomains].
    rewrite forallb_forall in Hdomains.
    specialize (Hdomains domain Hdomain).
    apply andb_true_iff in Hdomains as [Hmemory _].
    exact (all_disjoint_sound _ _ _ _ Hmemory Hin1 Hin2).
  - intros object owner domain Hobject Howner Hdomain extent1 extent2 Hin1 Hin2.
    specialize (Hcheck object Hobject).
    unfold private_ok in Hcheck.
    rewrite Howner in Hcheck.
    apply andb_true_iff in Hcheck as [_ Hdomains].
    rewrite forallb_forall in Hdomains.
    specialize (Hdomains domain Hdomain).
    apply andb_true_iff in Hdomains as [_ Hroots].
    exact (all_disjoint_sound _ _ _ _ Hroots Hin1 Hin2).
Qed.

Lemma write_ok_of :
  forall binding step object,
    h3_check binding = true -> In step (transitions binding) ->
    In object (footprint binding step) -> write_ok binding step object = true.
Proof.
  intros binding step object Hcheck Hstep Hobject.
  unfold h3_check in Hcheck.
  rewrite forallb_forall in Hcheck.
  specialize (Hcheck step Hstep).
  rewrite forallb_forall in Hcheck.
  exact (Hcheck object Hobject).
Qed.

Lemma h3_check_sound :
  forall binding, h3_check binding = true -> H3 binding.
Proof.
  intros binding Hcheck.
  split; [| split; [| split; [| split]]].
  - intros step object Hstep Hphase Hobject.
    pose proof (write_ok_of binding step object Hcheck Hstep Hobject) as Hok.
    unfold write_ok in Hok.
    rewrite Hphase in Hok.
    apply Nat.eqb_eq.
    exact Hok.
  - intros step object Hstep Hphase Hobject.
    pose proof (write_ok_of binding step object Hcheck Hstep Hobject) as Hok.
    unfold write_ok in Hok.
    rewrite Hphase in Hok.
    repeat rewrite andb_true_iff in Hok.
    destruct Hok as [[Hpublished _] _].
    apply negb_true_iff.
    exact Hpublished.
  - intros step channel Hstep Hphase Hring.
    destruct Hring as [Hring | Hring];
      pose proof (write_ok_of binding step _ Hcheck Hstep Hring) as Hok;
      unfold write_ok in Hok; rewrite Hphase in Hok;
      repeat rewrite andb_true_iff in Hok;
      destruct Hok as [[_ Hwriter] _];
      apply Nat.eqb_eq; exact Hwriter.
  - intros step channel Hstep Hphase Hring.
    pose proof (write_ok_of binding step _ Hcheck Hstep Hring) as Hok.
    unfold write_ok in Hok.
    rewrite Hphase in Hok.
    repeat rewrite andb_true_iff in Hok.
    destruct Hok as [[_ Hreader] _].
    apply Nat.eqb_eq.
    exact Hreader.
  - intros step object owner Hstep Hphase Hobject Howner.
    pose proof (write_ok_of binding step object Hcheck Hstep Hobject) as Hok.
    unfold write_ok in Hok.
    rewrite Hphase, Howner in Hok.
    repeat rewrite andb_true_iff in Hok.
    destruct Hok as [_ Hown].
    apply Nat.eqb_eq.
    exact Hown.
Qed.

(**
 * [mvp_binding] is the MVP's three-hart layout (MVP 1.0 under static
 * ownership; mvp-layout.h and the te-poc and anchor scenarios): the
 * control hart 0, G0 (domain 0) on hart 1 and G1 (domain 1) on hart 2,
 * harts 3 to 7 never started; each domain hart's block in the hart region;
 * each domain's window; the shared pages; and the two extents holding hart
 * 0's own stack and data. Each domain has two rings: the outbound ring its
 * hart writes and hart 0 reads, the inbound ring hart 0 writes and its hart
 * reads. The hart numbers are configuration data in the term, not
 * authority.
 *)
Definition mvp_binding : binding_instance :=
  {| bi_control := 0;
     bi_harts := [0; 1; 2];
     bi_domains := [0; 1];
     bi_hart_of := fun domain =>
       match domain with
       | 0 => 1
       | _ => 2
       end;
     bi_block := fun domain =>
       match domain with
       | 0 => mvp_g0_block_hpa
       | _ => mvp_g1_block_hpa
       end;
     bi_window := fun domain =>
       match domain with
       | 0 => mk_extent mvp_g0_hpa mvp_guest_bytes
       | _ => mk_extent mvp_g1_hpa mvp_guest_bytes
       end;
     bi_pages := mk_extent mvp_shared_pages_hpa mvp_shared_pages_bytes;
     bi_accepted_image := mk_extent mvp_monitor_hpa mvp_accepted_image_bytes;
     bi_mvp_region := mk_extent mvp_region_hpa mvp_region_bytes |}.

(** [binding_h0_control_excluded] is H0 for the MVP binding. *)
Theorem binding_h0_control_excluded : H0 mvp_binding.
Proof.
  intros domain Hdomain.
  simpl in Hdomain.
  destruct Hdomain as [<- | [<- | []]]; discriminate.
Qed.

(** [binding_h1_injective_total] is H1 for the MVP binding. *)
Theorem binding_h1_injective_total : H1 mvp_binding.
Proof.
  split.
  - intros domain1 domain2 Hdomain1 Hdomain2 Hsame.
    simpl in Hdomain1, Hdomain2.
    destruct Hdomain1 as [<- | [<- | []]], Hdomain2 as [<- | [<- | []]];
      simpl in Hsame; congruence.
  - intros domain Hdomain.
    simpl in Hdomain.
    destruct Hdomain as [<- | [<- | []]]; simpl; split;
      try discriminate; tauto.
Qed.

(** [binding_h2_private_state] is H2 for the MVP binding, by computation. *)
Theorem binding_h2_private_state : H2 mvp_binding.
Proof.
  apply h2_check_sound.
  vm_compute.
  reflexivity.
Qed.

(** [binding_h3_single_writer] is H3 for the MVP binding, by computation. *)
Theorem binding_h3_single_writer : H3 mvp_binding.
Proof.
  apply h3_check_sound.
  vm_compute.
  reflexivity.
Qed.
