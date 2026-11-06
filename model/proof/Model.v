(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Fixed Architecture Model 0.2 proposal, canonical, enforcement, and machine
 * state. This is a bounded abstract model, not a C or runtime refinement.
 *)

From Stdlib Require Import Bool List ZArith.
Import ListNotations.

(** [domain] identifies the two untrusted VS execution contexts. *)
Inductive domain : Type :=
| Management
| Protected.

(** [root] identifies the immutable G-stage roots. *)
Inductive root : Type :=
| ManagementRoot
| ProtectedRoot.

(** [vmid] deliberately projects both roots onto VMID zero. *)
Inductive vmid : Type :=
| VMIDZero.

(** [vcpu] identifies the sole vCPU bound to each domain. *)
Inductive vcpu : Type :=
| ManagementVCPU
| ProtectedVCPU.

(** [trusted_stack] identifies monitor-private transition stacks. *)
Inductive trusted_stack : Type :=
| ManagementStack
| ProtectedStack.

(** [saved_state_id] identifies monitor-private saved-register records. *)
Inductive saved_state_id : Type :=
| ManagementState
| ProtectedState.

(** [frame] enumerates the complete bounded physical-resource inventory. *)
Inductive frame : Type :=
| MonitorCodeFrame
| MonitorDataFrame
| ManagementRootFrame
| ProtectedRootFrame
| ManagementStackFrame
| ProtectedStackFrame
| ManagementStateFrame
| ProtectedStateFrame
| ManagementPrivateFrame
| ProtectedPrivateFrame
| SharedFrame.

(** [gpa] is the complete modeled guest-physical address space. *)
Inductive gpa : Type :=
| PrivateGPA
| SharedGPA.

(** [access_kind] is the complete modeled VS memory operation set. *)
Inductive access_kind : Type :=
| AccessRead
| AccessWrite
| AccessExecute.

(** [rights] records G-stage read, write, and execute authority. *)
Record rights : Type := {
  right_read : bool;
  right_write : bool;
  right_execute : bool
}.

(** [no_rights] grants no modeled operation. *)
Definition no_rights : rights :=
  {| right_read := false; right_write := false; right_execute := false |}.

(** [read_rights] grants read-only channel authority. *)
Definition read_rights : rights :=
  {| right_read := true; right_write := false; right_execute := false |}.

(** [read_write_rights] grants non-executable private or producer authority. *)
Definition read_write_rights : rights :=
  {| right_read := true; right_write := true; right_execute := false |}.

(** [rights_allow] checks one operation against a rights record. *)
Definition rights_allow (granted : rights) (requested : access_kind) : bool :=
  match requested with
  | AccessRead => right_read granted
  | AccessWrite => right_write granted
  | AccessExecute => right_execute granted
  end.

(** [rights_subset] states that derived rights do not exceed authority. *)
Definition rights_subset (derived authority : rights) : Prop :=
  (right_read derived = true -> right_read authority = true) /\
  (right_write derived = true -> right_write authority = true) /\
  (right_execute derived = true -> right_execute authority = true).

(** [rights_subsetb] is the executable rights-subset check. *)
Definition rights_subsetb (derived authority : rights) : bool :=
  implb (right_read derived) (right_read authority) &&
  implb (right_write derived) (right_write authority) &&
  implb (right_execute derived) (right_execute authority).

(** Fixed identifier equality functions used by executable checks. *)
Definition domain_eqb (left right : domain) : bool :=
  match left, right with
  | Management, Management | Protected, Protected => true
  | _, _ => false
  end.

Definition root_eqb (left right : root) : bool :=
  match left, right with
  | ManagementRoot, ManagementRoot | ProtectedRoot, ProtectedRoot => true
  | _, _ => false
  end.

Definition vmid_eqb (left right : vmid) : bool :=
  match left, right with
  | VMIDZero, VMIDZero => true
  end.

Definition vcpu_eqb (left right : vcpu) : bool :=
  match left, right with
  | ManagementVCPU, ManagementVCPU | ProtectedVCPU, ProtectedVCPU => true
  | _, _ => false
  end.

Definition stack_eqb (left right : trusted_stack) : bool :=
  match left, right with
  | ManagementStack, ManagementStack | ProtectedStack, ProtectedStack => true
  | _, _ => false
  end.

Definition state_id_eqb (left right : saved_state_id) : bool :=
  match left, right with
  | ManagementState, ManagementState | ProtectedState, ProtectedState => true
  | _, _ => false
  end.

(** Immutable canonical binding functions. *)
Definition root_for (subject : domain) : root :=
  match subject with
  | Management => ManagementRoot
  | Protected => ProtectedRoot
  end.

Definition domain_for_root (stage_root : root) : domain :=
  match stage_root with
  | ManagementRoot => Management
  | ProtectedRoot => Protected
  end.

Definition vmid_for (_ : domain) : vmid := VMIDZero.

Definition vcpu_for (subject : domain) : vcpu :=
  match subject with
  | Management => ManagementVCPU
  | Protected => ProtectedVCPU
  end.

Definition stack_for (subject : domain) : trusted_stack :=
  match subject with
  | Management => ManagementStack
  | Protected => ProtectedStack
  end.

Definition state_for (subject : domain) : saved_state_id :=
  match subject with
  | Management => ManagementState
  | Protected => ProtectedState
  end.

(** [platform_inventory] is the complete bounded resource inventory. *)
Definition platform_inventory : list frame :=
  [MonitorCodeFrame; MonitorDataFrame;
   ManagementRootFrame; ProtectedRootFrame;
   ManagementStackFrame; ProtectedStackFrame;
   ManagementStateFrame; ProtectedStateFrame;
   ManagementPrivateFrame; ProtectedPrivateFrame; SharedFrame].

(** Page-indexed extents make non-overlap explicit in the fixed model. *)
Definition frame_base (object : frame) : nat :=
  match object with
  | MonitorCodeFrame => 0
  | MonitorDataFrame => 2
  | ManagementRootFrame => 4
  | ProtectedRootFrame => 8
  | ManagementStackFrame => 12
  | ProtectedStackFrame => 14
  | ManagementStateFrame => 16
  | ProtectedStateFrame => 17
  | ManagementPrivateFrame => 512
  | ProtectedPrivateFrame => 513
  | SharedFrame => 514
  end.

Definition frame_pages (object : frame) : nat :=
  match object with
  | MonitorCodeFrame | MonitorDataFrame
  | ManagementStackFrame | ProtectedStackFrame => 2
  | ManagementRootFrame | ProtectedRootFrame => 4
  | _ => 1
  end.

Definition extents_disjoint (left right : frame) : Prop :=
  frame_base left + frame_pages left <= frame_base right \/
  frame_base right + frame_pages right <= frame_base left.

(** Canonical ownership and exclusion functions. *)
Definition private_frame (object : frame) : Prop :=
  object = ManagementPrivateFrame \/ object = ProtectedPrivateFrame.

Definition frame_owner (object : frame) : option domain :=
  match object with
  | ManagementPrivateFrame => Some Management
  | ProtectedPrivateFrame => Some Protected
  | _ => None
  end.

Definition monitor_private (object : frame) : Prop :=
  match object with
  | ManagementPrivateFrame | ProtectedPrivateFrame | SharedFrame => False
  | _ => True
  end.

Definition private_for (subject : domain) : frame :=
  match subject with
  | Management => ManagementPrivateFrame
  | Protected => ProtectedPrivateFrame
  end.

Definition channel_rights (subject : domain) : rights :=
  match subject with
  | Management => read_write_rights
  | Protected => read_rights
  end.

Definition canonical_authority (subject : domain) (object : frame) : rights :=
  if match subject, object with
     | Management, ManagementPrivateFrame
     | Protected, ProtectedPrivateFrame => true
     | _, _ => false
     end
  then read_write_rights
  else
    match object with
    | SharedFrame => channel_rights subject
    | _ => no_rights
    end.

Definition canonical_mapping (subject : domain) (address : gpa)
    : option (frame * rights) :=
  match address with
  | PrivateGPA => Some (private_for subject, read_write_rights)
  | SharedGPA => Some (SharedFrame, channel_rights subject)
  end.

(** Proposal provenance is untrusted and absent from canonical state. *)
Inductive source_vocabulary : Type :=
| RelationsA
| RelationsB.

Inductive proposal_order : Type :=
| ForwardOrder
| ReverseOrder
| IncompleteOrder.

Record proposal : Type := {
  proposal_identity : nat;
  proposal_vocabulary : source_vocabulary;
  proposal_record_order : proposal_order;
  proposal_inventory_closed : bool;
  proposal_bindings_complete : bool;
  proposal_rights_valid : bool;
  proposal_direct_authority : bool
}.

Definition proposed_domains (order : proposal_order) : list domain :=
  match order with
  | ForwardOrder => [Management; Protected]
  | ReverseOrder => [Protected; Management]
  | IncompleteOrder => [Management]
  end.

Definition domain_order_complete (order : proposal_order) : bool :=
  match order with
  | ForwardOrder | ReverseOrder => true
  | IncompleteOrder => false
  end.

Definition proposal_valid (input : proposal) : bool :=
  Nat.ltb 0 (proposal_identity input) &&
  domain_order_complete (proposal_record_order input) &&
  proposal_inventory_closed input &&
  proposal_bindings_complete input &&
  proposal_rights_valid input &&
  negb (proposal_direct_authority input).

Definition proposal_source_a : proposal :=
  {| proposal_identity := 1;
     proposal_vocabulary := RelationsA;
     proposal_record_order := ForwardOrder;
     proposal_inventory_closed := true;
     proposal_bindings_complete := true;
     proposal_rights_valid := true;
     proposal_direct_authority := false |}.

Definition proposal_source_b : proposal :=
  {| proposal_identity := 2;
     proposal_vocabulary := RelationsB;
     proposal_record_order := ReverseOrder;
     proposal_inventory_closed := true;
     proposal_bindings_complete := true;
     proposal_rights_valid := true;
     proposal_direct_authority := false |}.

(**
 * [canonical_state] is a structurally valid canonical configuration.
 *
 * The fixed Model 0.2 proof instance has one constructor. Invalid, partial,
 * provenance-bearing, or unsealed proposal state cannot inhabit this type.
 *)
Inductive canonical_state : Type :=
| CanonicalConfiguration.

Definition canonical_domains (_ : canonical_state) : list domain :=
  [Management; Protected].

Definition canonical_resources (_ : canonical_state) : list frame :=
  platform_inventory.

Definition fixed_configuration_identity : nat := 2.

Definition canonical_identity (_ : canonical_state) : nat :=
  fixed_configuration_identity.

Definition canonical_configuration : canonical_state :=
  CanonicalConfiguration.

(** [canonicalize] validates and normalizes source order and vocabulary. *)
Definition canonicalize (input : proposal) : option canonical_state :=
  if proposal_valid input then Some canonical_configuration else None.

(**
 * [enforcement_state] structurally represents the sole complete derived root
 * set. No identity-only or partially populated enforcement value exists.
 *)
Inductive enforcement_state : Type :=
| DerivedEnforcement.

Definition enforcement_identity (_ : enforcement_state) : nat :=
  fixed_configuration_identity.

Definition enforcement_roots (_ : enforcement_state) : list root :=
  [ManagementRoot; ProtectedRoot].

Definition derive_enforcement (_ : canonical_state)
    : enforcement_state :=
  DerivedEnforcement.

Definition derived_mapping (enforcement : enforcement_state) (stage_root : root)
    (address : gpa) : option (frame * rights) :=
  match enforcement with
  | DerivedEnforcement =>
      canonical_mapping (domain_for_root stage_root) address
  end.

(** Register and translation-cache projections retained from Model 0.1. *)
Definition register_file : Type := nat -> Z.
Definition empty_registers : register_file := fun _ => 0%Z.
Definition initial_saved_registers : domain -> register_file :=
  fun _ => empty_registers.

Record cache_entry : Type := {
  cached_root : root;
  cached_gpa : gpa;
  cached_frame : frame;
  cached_rights : rights
}.

(** [phase] is the complete Model 0.2 control-phase vocabulary. *)
Inductive phase : Type :=
| Empty
| InventoryBound
| ProposalCopied
| Validated
| Sealed
| RootsDerived
| Active
| Switching
| Failed.

(** [machine_state] contains all security-relevant fixed-hart state. *)
Record machine_state : Type := {
  state_phase : phase;
  state_inventory_bound : bool;
  state_proposal : option proposal;
  state_canonical : option canonical_state;
  state_enforcement : option enforcement_state;
  state_sealed : bool;
  active_domain : option domain;
  active_vcpu : option vcpu;
  active_root : option root;
  active_vmid : option vmid;
  active_stack : option trusted_stack;
  active_saved_state : option saved_state_id;
  pending_domain : option domain;
  root_write_complete : bool;
  fence_complete : bool;
  translation_cache : list cache_entry;
  saved_registers : domain -> register_file
}.

(** [cold_state] has no bound input or published authority. *)
Definition cold_state : machine_state :=
  {| state_phase := Empty;
     state_inventory_bound := false;
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
     saved_registers := initial_saved_registers |}.

(** [failed_state] removes runnable bindings and preserves audit evidence. *)
Definition failed_state (state : machine_state) : machine_state :=
  {| state_phase := Failed;
     state_inventory_bound := state_inventory_bound state;
     state_proposal := state_proposal state;
     state_canonical := state_canonical state;
     state_enforcement := state_enforcement state;
     state_sealed := state_sealed state;
     active_domain := None;
     active_vcpu := None;
     active_root := None;
     active_vmid := None;
     active_stack := None;
     active_saved_state := None;
     pending_domain := None;
     root_write_complete := false;
     fence_complete := false;
     translation_cache := translation_cache state;
     saved_registers := saved_registers state |}.

(** [canonical_enforcement_bound] admits only the complete structural pair. *)
Definition canonical_enforcement_bound (state : machine_state) : bool :=
  match state_canonical state, state_enforcement state with
  | Some CanonicalConfiguration, Some DerivedEnforcement => true
  | _, _ => false
  end.

(** [running_context_valid] checks every active atomic binding. *)
Definition running_context_valid (state : machine_state) : bool :=
  state_sealed state &&
  canonical_enforcement_bound state &&
  match state_phase state, active_domain state, active_vcpu state,
        active_root state, active_vmid state, active_stack state,
        active_saved_state state with
  | Active, Some subject, Some processor, Some stage_root,
      Some identifier, Some trusted_sp, Some saved_id =>
      vcpu_eqb processor (vcpu_for subject) &&
      root_eqb stage_root (root_for subject) &&
      vmid_eqb identifier (vmid_for subject) &&
      stack_eqb trusted_sp (stack_for subject) &&
      state_id_eqb saved_id (state_for subject)
  | _, _, _, _, _, _, _ => false
  end.

(** [checked_access] uses only derived enforcement bound to canonical state. *)
Definition checked_access (state : machine_state) (address : gpa)
    (requested : access_kind) : option frame :=
  if running_context_valid state then
    match active_domain state, active_root state, state_enforcement state with
    | Some subject, Some stage_root, Some enforcement =>
        match derived_mapping enforcement stage_root address with
        | Some (object, derived_rights) =>
            if rights_subsetb derived_rights
                 (canonical_authority subject object) &&
               rights_allow derived_rights requested
            then Some object
            else None
        | None => None
        end
    | _, _, _ => None
    end
  else None.

(** [cache_translation] records a successful active-root translation. *)
Definition cache_translation (state : machine_state) (address : gpa)
    : machine_state :=
  match active_root state, state_enforcement state with
  | Some stage_root, Some enforcement =>
      match derived_mapping enforcement stage_root address with
      | Some (object, derived_rights) =>
          {| state_phase := state_phase state;
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
             root_write_complete := root_write_complete state;
             fence_complete := fence_complete state;
             translation_cache :=
               {| cached_root := stage_root;
                  cached_gpa := address;
                  cached_frame := object;
                  cached_rights := derived_rights |} ::
               translation_cache state;
             saved_registers := saved_registers state |}
      | None => failed_state state
      end
  | _, _ => failed_state state
  end.

(** [access_step] distinguishes ordinary denial from invalid-phase failure. *)
Definition access_step (state : machine_state) (address : gpa)
    (requested : access_kind) : machine_state * option frame :=
  if running_context_valid state then
    match checked_access state address requested with
    | Some object => (cache_translation state address, Some object)
    | None => (state, None)
    end
  else (failed_state state, None).
