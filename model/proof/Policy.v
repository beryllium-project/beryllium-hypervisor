(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Security model v1's policy layer over the bounded abstract model (MVP M3,
 * work package M3-3): the raw term vocabulary the instance generator emits,
 * the A1 validator, the total default-deny semantics, the analyses A2 to A8
 * as functions, A8 soundness, flow confinement and A6's closure equality,
 * sealing with policy around the accepted Model 0.2 seam, and the adapter
 * from the accepted canonical state to its policy view, Model 0.2's
 * projection of Instance 1. This is a bounded abstract model, not a C
 * refinement; it reads the accepted modules and changes none of them.
 *)

From Stdlib Require Import Bool NArith PeanoNat Relations.
(* Exported, so that a module requiring this one can import ListNotations. *)
From Stdlib Require Export List.
Require Import Claims.
Import ListNotations.

(*
 * M3 raw-term vocabulary, shared verbatim by this module (which defines
 * it), the generator model/tools/gen-policy-fixtures.mjs (which emits terms
 * over it into build/model/policy/Instances.v), and the C mirror
 * model/include/be/policy.h. Names are natural numbers; the string tables
 * live only in the generator's C output and the reports.
 *
 * Identifier assignment, per instance (the generator's rule, mirrored by
 * the C data): type ids in declaration order in policy.te, 0-based; class
 * ids in declaration order; permission ids in order of first appearance
 * across the class declarations; subject ids in the labeling's subject
 * order (the monitor first, then the domains); object ids in the
 * labeling's object order; hart ids are the platform's hart numbers. A
 * domain is named by its subject id in ownerships, grants, channels, and
 * bindings.
 *)

Record raw_class := mk_raw_class { rc_class : nat; rc_perms : list nat }.
Record raw_rule := mk_raw_rule
  { rr_source : nat; rr_target : nat; rr_class : nat; rr_perms : list nat }.
Record raw_policy := mk_raw_policy
  { rp_types : list nat; rp_classes : list raw_class; rp_rules : list raw_rule }.

Inductive raw_entity : Type := RawSubject (n : nat) | RawObject (n : nat).
Record raw_label := mk_raw_label { rl_entity : raw_entity; rl_type : nat }.
Record raw_object := mk_raw_object { ro_object : nat; ro_class : nat }.
Record raw_labeling := mk_raw_labeling
  { rl_subjects : list nat; rl_objects : list raw_object;
    rl_labels : list raw_label }.

Record raw_need := mk_raw_need
  { rn_source : nat; rn_target : nat; rn_class : nat; rn_perms : list nat }.

(*
 * The manifest view: what the sealed configuration grants and binds.
 * rg_perms are the permission ids the manifest grants the subject on the
 * object in that class (memory: map for presence in the root, read/write/
 * execute for the leaf rights; channel: send or receive; domain: the
 * management permissions). A channel names its channel object, its storage
 * object (class memory), its writer subject, and its reader subject.
 * Ownership names a memory object's owning domain (subject id). Bindings
 * and harts are mechanism metadata outside A8 (security model v1 Revision
 * 1, R1.3).
 *)
Record raw_grant := mk_raw_grant
  { rg_subject : nat; rg_object : nat; rg_class : nat; rg_perms : list nat }.
Record raw_channel := mk_raw_channel
  { rch_object : nat; rch_storage : nat; rch_writer : nat; rch_reader : nat }.
Record raw_ownership := mk_raw_ownership { row_object : nat; row_owner : nat }.
Record raw_binding := mk_raw_binding { rb_domain : nat; rb_hart : nat }.
Record raw_view := mk_raw_view
  { rv_ownerships : list raw_ownership; rv_channels : list raw_channel;
    rv_grants : list raw_grant; rv_bindings : list raw_binding;
    rv_harts : list nat; rv_control_hart : nat }.

Record raw_instance := mk_raw_instance
  { ri_policy : raw_policy; ri_labeling : raw_labeling;
    ri_needs : list raw_need; ri_view : raw_view }.

(*
 * Part 2's v1 classes and permissions. Raw terms carry numbers only, so the
 * analyses name the v1 vocabulary by the identifiers the contract's rule
 * assigns to a policy that declares Part 2's classes in Part 2's order with
 * Part 2's permission order, as every instance does: classes memory 0,
 * channel 1, domain 2, manifest 3; permissions read 0, write 1, execute 2,
 * map 3, send 4, receive 5, enter 6, switch_to 7, terminate 8, pause 9
 * (manifest's read is read). A1 refuses a declared class that is not one of
 * these with exactly its permissions, as the MVP checker refuses a class
 * that is not a v1 class.
 *)
Definition class_memory : nat := 0.
Definition class_channel : nat := 1.
Definition class_domain : nat := 2.
Definition class_manifest : nat := 3.

Definition perm_read : nat := 0.
Definition perm_write : nat := 1.
Definition perm_execute : nat := 2.
Definition perm_map : nat := 3.
Definition perm_send : nat := 4.
Definition perm_receive : nat := 5.
Definition perm_enter : nat := 6.
Definition perm_switch_to : nat := 7.
Definition perm_terminate : nat := 8.
Definition perm_pause : nat := 9.

(** [v1_class_perms] is each v1 class's permission set (Part 2). *)
Definition v1_class_perms (class : nat) : option (list nat) :=
  if class =? class_memory then
    Some [perm_read; perm_write; perm_execute; perm_map]
  else if class =? class_channel then Some [perm_send; perm_receive]
  else if class =? class_domain then
    Some [perm_enter; perm_switch_to; perm_terminate; perm_pause]
  else if class =? class_manifest then Some [perm_read]
  else None.

(** [mem] is executable membership in a list of identifiers. *)
Definition mem (x : nat) (values : list nat) : bool :=
  existsb (Nat.eqb x) values.

Lemma mem_in : forall x values, mem x values = true <-> In x values.
Proof.
  intros x values.
  unfold mem.
  rewrite existsb_exists.
  split.
  - intros [y [Hin Heq]].
    apply Nat.eqb_eq in Heq.
    subst y.
    exact Hin.
  - intros Hin.
    exists x.
    split; [exact Hin | apply Nat.eqb_refl].
Qed.

(** [repeats] lists each identifier that occurs again later in a list. *)
Fixpoint repeats (values : list nat) : list nat :=
  match values with
  | [] => []
  | x :: rest => if mem x rest then x :: repeats rest else repeats rest
  end.

(** [nodupb] holds when no identifier repeats. *)
Definition nodupb (values : list nat) : bool :=
  match repeats values with
  | [] => true
  | _ :: _ => false
  end.

(** [dedup] keeps one occurrence of each identifier. *)
Fixpoint dedup (values : list nat) : list nat :=
  match values with
  | [] => []
  | x :: rest => if mem x rest then dedup rest else x :: dedup rest
  end.

(** [same_set] compares two identifier lists as sets. *)
Definition same_set (left right : list nat) : bool :=
  forallb (fun x => mem x right) left && forallb (fun x => mem x left) right.

(** [is_empty] holds for the empty list. *)
Definition is_empty {A : Type} (values : list A) : bool :=
  match values with
  | [] => true
  | _ :: _ => false
  end.

(*
 * A1, well-formedness (Part 3): every type and class in the rules is
 * declared, every permission in a rule belongs to its class, every rule's
 * permission set is nonempty, and the labeling assigns exactly one declared
 * type to every subject and object of the configuration. Raw terms make
 * each failure representable: an undeclared type, an unknown permission,
 * an unlabeled object. Like the MVP checker's A1 it also refuses a type or
 * class declared twice, a permission repeated in a class or rule, a class
 * that is not Part 2's v1 class, and an object of a class other than memory
 * or channel; and, like the C mirror's, it requires every entity the view
 * names to be one of the configuration's, so that each has its label. A
 * malformed need set fails A4, and a grant no rule allows fails A8, as in
 * both checkers. The generator emits no non-v1 class and no object of
 * another class, so the C mirror, which checks only that a class's
 * permissions are nonempty and unrepeated, never meets either; its
 * representation bounds (BE_POLICY_MAX_ constants) have no counterpart in
 * raw terms, and every generated instance is within them.
 *)

(** [a1_finding] enumerates A1's refusals, each naming what it refuses. *)
Inductive a1_finding : Type :=
| A1TypeDeclaredTwice (type : nat)
| A1ClassDeclaredTwice (class : nat)
| A1ClassNotV1 (class : raw_class)
| A1RuleUndeclaredType (rule : raw_rule) (type : nat)
| A1RuleUndeclaredClass (rule : raw_rule)
| A1RuleEmptyPermissions (rule : raw_rule)
| A1RuleRepeatedPermission (rule : raw_rule)
| A1RulePermissionNotInClass (rule : raw_rule) (perm : nat)
| A1SubjectListedTwice (subject : nat)
| A1ObjectListedTwice (object : nat)
| A1ObjectClass (object : raw_object)
| A1LabelOfNothing (label : raw_label)
| A1LabelUndeclaredType (label : raw_label)
| A1Unlabeled (entity : raw_entity)
| A1LabeledTwice (entity : raw_entity)
| A1ViewNamesNothing (entity : raw_entity).

(** [class_perms] is a declared class's permissions, if it is declared. *)
Definition class_perms (policy : raw_policy) (class : nat)
    : option (list nat) :=
  match find (fun declared => rc_class declared =? class)
      (rp_classes policy) with
  | Some declared => Some (rc_perms declared)
  | None => None
  end.

(** [v1_class] holds for a declaration of a v1 class with its permissions. *)
Definition v1_class (declared : raw_class) : bool :=
  match v1_class_perms (rc_class declared) with
  | Some perms =>
      nodupb (rc_perms declared) && same_set (rc_perms declared) perms
  | None => false
  end.

(** [rule_findings] checks one rule against the declarations. *)
Definition rule_findings (policy : raw_policy) (rule : raw_rule)
    : list a1_finding :=
  map (A1RuleUndeclaredType rule)
    (filter (fun type => negb (mem type (rp_types policy)))
       [rr_source rule; rr_target rule]) ++
  match class_perms policy (rr_class rule) with
  | Some perms =>
      map (A1RulePermissionNotInClass rule)
        (filter (fun perm => negb (mem perm perms)) (rr_perms rule))
  | None => [A1RuleUndeclaredClass rule]
  end ++
  (if is_empty (rr_perms rule) then [A1RuleEmptyPermissions rule] else []) ++
  (if nodupb (rr_perms rule) then [] else [A1RuleRepeatedPermission rule]).

(** [policy_findings] checks the declarations and every rule. *)
Definition policy_findings (policy : raw_policy) : list a1_finding :=
  map A1TypeDeclaredTwice (repeats (rp_types policy)) ++
  map A1ClassDeclaredTwice (repeats (map rc_class (rp_classes policy))) ++
  map A1ClassNotV1 (filter (fun declared => negb (v1_class declared))
    (rp_classes policy)) ++
  flat_map (rule_findings policy) (rp_rules policy).

(** [entity_eqb] is executable equality of labeled entities. *)
Definition entity_eqb (left right : raw_entity) : bool :=
  match left, right with
  | RawSubject x, RawSubject y => x =? y
  | RawObject x, RawObject y => x =? y
  | _, _ => false
  end.

(** [configuration_entities] lists every subject and object to be labeled. *)
Definition configuration_entities (labeling : raw_labeling)
    : list raw_entity :=
  map RawSubject (rl_subjects labeling) ++
  map (fun object => RawObject (ro_object object)) (rl_objects labeling).

(** [entity_known] holds for an entity of the configuration. *)
Definition entity_known (labeling : raw_labeling) (entity : raw_entity)
    : bool :=
  existsb (entity_eqb entity) (configuration_entities labeling).

(** [label_count] counts the labels of one entity. *)
Definition label_count (labels : list raw_label) (entity : raw_entity)
    : nat :=
  length (filter (fun label => entity_eqb (rl_entity label) entity) labels).

(** [labeling_findings] checks that each entity has one declared type. *)
Definition labeling_findings (policy : raw_policy) (labeling : raw_labeling)
    : list a1_finding :=
  map A1SubjectListedTwice (repeats (rl_subjects labeling)) ++
  map A1ObjectListedTwice (repeats (map ro_object (rl_objects labeling))) ++
  map A1ObjectClass
    (filter (fun object => negb ((ro_class object =? class_memory) ||
                                 (ro_class object =? class_channel)))
       (rl_objects labeling)) ++
  map A1LabelOfNothing
    (filter (fun label => negb (entity_known labeling (rl_entity label)))
       (rl_labels labeling)) ++
  map A1LabelUndeclaredType
    (filter (fun label => negb (mem (rl_type label) (rp_types policy)))
       (rl_labels labeling)) ++
  flat_map (fun entity =>
      match label_count (rl_labels labeling) entity with
      | 0 => [A1Unlabeled entity]
      | 1 => []
      | _ => [A1LabeledTwice entity]
      end) (configuration_entities labeling).

(**
 * [view_entities] lists every entity the view names: a domain-class
 * grant's object is the target domain, a subject.
 *)
Definition view_entities (view : raw_view) : list raw_entity :=
  flat_map (fun owned =>
      [RawObject (row_object owned); RawSubject (row_owner owned)])
    (rv_ownerships view) ++
  flat_map (fun channel =>
      [RawObject (rch_object channel); RawObject (rch_storage channel);
       RawSubject (rch_writer channel); RawSubject (rch_reader channel)])
    (rv_channels view) ++
  flat_map (fun grant =>
      [RawSubject (rg_subject grant);
       if rg_class grant =? class_domain then RawSubject (rg_object grant)
       else RawObject (rg_object grant)])
    (rv_grants view) ++
  map (fun binding => RawSubject (rb_domain binding)) (rv_bindings view).

(** [view_findings] refuses a view naming an entity outside the labeling. *)
Definition view_findings (labeling : raw_labeling) (view : raw_view)
    : list a1_finding :=
  map A1ViewNamesNothing
    (filter (fun entity => negb (entity_known labeling entity))
       (view_entities view)).

(** [a1_findings] is A1's complete list of refusals. *)
Definition a1_findings (policy : raw_policy) (labeling : raw_labeling)
    (view : raw_view) : list a1_finding :=
  policy_findings policy ++ labeling_findings policy labeling ++
  view_findings labeling view.

(** [a1_ok] holds when A1 finds nothing. *)
Definition a1_ok (policy : raw_policy) (labeling : raw_labeling)
    (view : raw_view) : bool :=
  is_empty (a1_findings policy labeling view).

(**
 * [validated] is a policy, labeling, need sets, and view that passed A1.
 * Only [validate] constructs one from raw terms; its last field is A1's
 * success, so every value of this type is well formed.
 *)
Record validated : Type := mk_validated {
  v_policy : raw_policy;
  v_labeling : raw_labeling;
  v_needs : list raw_need;
  v_view : raw_view;
  v_well_formed : a1_ok v_policy v_labeling v_view = true
}.

(** [validate] is A1: a validated value, or [None] with [a1_findings]. *)
Definition validate (policy : raw_policy) (labeling : raw_labeling)
    (needs : list raw_need) (view : raw_view) : option validated :=
  match bool_dec (a1_ok policy labeling view) true with
  | left well_formed =>
      Some (mk_validated policy labeling needs view well_formed)
  | right _ => None
  end.

(** [validate_instance] validates an instance's four terms. *)
Definition validate_instance (instance : raw_instance) : option validated :=
  validate (ri_policy instance) (ri_labeling instance) (ri_needs instance)
    (ri_view instance).

Lemma validate_fields :
  forall policy labeling needs view checked,
    validate policy labeling needs view = Some checked ->
    v_policy checked = policy /\ v_labeling checked = labeling /\
    v_needs checked = needs /\ v_view checked = view.
Proof.
  intros policy labeling needs view checked Hvalid.
  unfold validate in Hvalid.
  destruct (bool_dec (a1_ok policy labeling view) true); try discriminate.
  inversion Hvalid; subst checked.
  repeat split; reflexivity.
Qed.

(**
 * [label_type] is the labeling's total function: the type of an entity's
 * label. A1 gives each configuration entity exactly one label of a declared
 * type, so on the configuration this is that label; elsewhere it is 0 and
 * never consulted for a well-formed view.
 *)
Definition label_type (labels : list raw_label) (entity : raw_entity) : nat :=
  match find (fun label => entity_eqb (rl_entity label) entity) labels with
  | Some label => rl_type label
  | None => 0
  end.

Definition subject_type (checked : validated) (subject : nat) : nat :=
  label_type (rl_labels (v_labeling checked)) (RawSubject subject).

Definition object_type (checked : validated) (object : nat) : nat :=
  label_type (rl_labels (v_labeling checked)) (RawObject object).

(*
 * The semantics (Part 2): [decide] answers allow (true) exactly when some
 * rule allows the permission, and deny (false) otherwise. It is a Rocq
 * function over the validated policy, so it is total by construction.
 *)

(** [rule_allows] holds when one rule allows one request. *)
Definition rule_allows (rule : raw_rule) (source target class perm : nat)
    : bool :=
  (rr_source rule =? source) && (rr_target rule =? target) &&
  (rr_class rule =? class) && mem perm (rr_perms rule).

(** [decide] is the policy's decision for one request. *)
Definition decide (checked : validated) (source target class perm : nat)
    : bool :=
  existsb (fun rule => rule_allows rule source target class perm)
    (rp_rules (v_policy checked)).

(** [policy_allows] is the decision's specification: a rule allows it. *)
Definition policy_allows (checked : validated) (source target class perm : nat)
    : Prop :=
  exists rule,
    In rule (rp_rules (v_policy checked)) /\ rr_source rule = source /\
    rr_target rule = target /\ rr_class rule = class /\
    In perm (rr_perms rule).

Lemma decide_spec :
  forall checked source target class perm,
    decide checked source target class perm = true <->
    policy_allows checked source target class perm.
Proof.
  intros checked source target class perm.
  unfold decide, policy_allows, rule_allows.
  rewrite existsb_exists.
  split.
  - intros [rule [Hin Hallows]].
    repeat rewrite andb_true_iff in Hallows.
    destruct Hallows as [[[Hsource Htarget] Hclass] Hperm].
    apply Nat.eqb_eq in Hsource, Htarget, Hclass.
    apply mem_in in Hperm.
    exists rule.
    repeat split; assumption.
  - intros [rule [Hin [Hsource [Htarget [Hclass Hperm]]]]].
    exists rule.
    split; [exact Hin |].
    subst.
    rewrite !Nat.eqb_refl.
    simpl.
    apply mem_in.
    exact Hperm.
Qed.

(**
 * [policy_decide_total] is T1 (I10): [decide] answers every request,
 * allow exactly when some rule allows it and deny otherwise, so deny is
 * the default; the answer depends only on the rules; and with no rule
 * every request is denied.
 *)
Theorem policy_decide_total :
  forall checked source target class perm,
    (decide checked source target class perm = true <->
       policy_allows checked source target class perm) /\
    (decide checked source target class perm = false <->
       ~ policy_allows checked source target class perm) /\
    (forall other,
       rp_rules (v_policy other) = rp_rules (v_policy checked) ->
       decide other source target class perm =
       decide checked source target class perm) /\
    (rp_rules (v_policy checked) = [] ->
       decide checked source target class perm = false).
Proof.
  intros checked source target class perm.
  split; [apply decide_spec |].
  split.
  - rewrite <- decide_spec.
    destruct (decide checked source target class perm); split;
      intros H; try reflexivity; try discriminate;
      exfalso; apply H; reflexivity.
  - split.
    + intros other Hrules.
      unfold decide.
      rewrite Hrules.
      reflexivity.
    + intros Hnone.
      unfold decide.
      rewrite Hnone.
      reflexivity.
Qed.

(*
 * The configuration's subjects and objects as the analyses read them, as
 * the C mirror (include/be/policy.h) and the generator number them: the
 * monitor is subject 0 and every other subject of the configuration is a
 * domain, named by its index plus one. A domain's private objects are the
 * memory objects an ownership gives it; monitor memory is every memory
 * object that no ownership names and no channel uses, so a view carries no
 * ownership for it; a channel's storage is its channel's. These are the
 * MVP checker's owners: a domain, a channel, or the monitor.
 *)

(** [monitor_subject] is the monitor, subject 0. *)
Definition monitor_subject : nat := 0.

(** [domains] is the configuration's domains, by subject id. *)
Definition domains (checked : validated) : list nat :=
  filter (fun subject => negb (subject =? monitor_subject))
    (rl_subjects (v_labeling checked)).

(** [domain_types] is the types labeling the domains. *)
Definition domain_types (checked : validated) : list nat :=
  map (subject_type checked) (domains checked).

(** [domains_of_type] is the domains one type labels. *)
Definition domains_of_type (checked : validated) (type : nat) : list nat :=
  filter (fun domain => subject_type checked domain =? type) (domains checked).

(** [owned] holds for an object an ownership names. *)
Definition owned (checked : validated) (object : nat) : bool :=
  existsb (fun ownership => row_object ownership =? object)
    (rv_ownerships (v_view checked)).

(** [channel_uses] holds for a channel's object or storage. *)
Definition channel_uses (checked : validated) (object : nat) : bool :=
  existsb (fun channel => (rch_object channel =? object) ||
                          (rch_storage channel =? object))
    (rv_channels (v_view checked)).

(** [monitor_object] holds for memory no ownership names and no channel uses. *)
Definition monitor_object (checked : validated) (object : raw_object) : bool :=
  (ro_class object =? class_memory) &&
  negb (owned checked (ro_object object)) &&
  negb (channel_uses checked (ro_object object)).

(** [monitor_types] is the types labeling monitor memory. *)
Definition monitor_types (checked : validated) : list nat :=
  map (fun object => object_type checked (ro_object object))
    (filter (monitor_object checked) (rl_objects (v_labeling checked))).

(** [private_pairs] is each domain-owned object's type with its owner. *)
Definition private_pairs (checked : validated) : list (nat * nat) :=
  map (fun ownership =>
      (object_type checked (row_object ownership), row_owner ownership))
    (filter (fun ownership => mem (row_owner ownership) (domains checked))
       (rv_ownerships (v_view checked))).

Definition rules_of (checked : validated) : list raw_rule :=
  rp_rules (v_policy checked).

(*
 * A2, unreachable authority: a rule is reachable when some subject is
 * labeled with its source and some object of its class with its target; a
 * domain is the domain-class object its own type labels.
 *)

Definition rule_reachable (checked : validated) (rule : raw_rule) : bool :=
  existsb (fun subject => subject_type checked subject =? rr_source rule)
    (rl_subjects (v_labeling checked)) &&
  (if rr_class rule =? class_domain then
     mem (rr_target rule) (domain_types checked)
   else
     existsb (fun object => (ro_class object =? rr_class rule) &&
                            (object_type checked (ro_object object) =?
                             rr_target rule))
       (rl_objects (v_labeling checked))).

Definition a2 (checked : validated) : bool :=
  forallb (rule_reachable checked) (rules_of checked).

(*
 * A3, contradictory authority, as the MVP checker checks the policy
 * against the invariants: no domain type holds any permission on a type
 * labeling monitor memory (I2), nor map on a type labeling another
 * domain's private memory (I1); every channel rule has a memory rule on
 * its target from its source, and storage that several source types hold
 * has a channel rule for each of them; and a domain rule held by a domain
 * type names another domain's type.
 *)

Definition memory_sources (checked : validated) (target : nat) : list nat :=
  dedup (map rr_source
    (filter (fun rule => (rr_class rule =? class_memory) &&
                         (rr_target rule =? target)) (rules_of checked))).

Definition channel_rule_for (checked : validated) (source target : nat)
    : bool :=
  existsb (fun rule => (rr_class rule =? class_channel) &&
                       (rr_source rule =? source) &&
                       (rr_target rule =? target)) (rules_of checked).

Definition maps_other_private (checked : validated) (rule : raw_rule) : bool :=
  (rr_class rule =? class_memory) && mem perm_map (rr_perms rule) &&
  existsb (fun pair =>
      (fst pair =? rr_target rule) &&
      existsb (fun domain => negb (snd pair =? domain))
        (domains_of_type checked (rr_source rule)))
    (private_pairs checked).

Definition a3_rule (checked : validated) (rule : raw_rule) : bool :=
  let held := mem (rr_source rule) (domain_types checked) in
  negb (held && mem (rr_target rule) (monitor_types checked)) &&
  negb (held && maps_other_private checked rule) &&
  negb ((rr_class rule =? class_channel) &&
        negb (mem (rr_source rule)
                (memory_sources checked (rr_target rule)))) &&
  negb (held && (rr_class rule =? class_domain) &&
        negb (mem (rr_target rule) (domain_types checked) &&
              negb (rr_target rule =? rr_source rule))).

Definition storage_declared (checked : validated) (target : nat) : bool :=
  (length (memory_sources checked target) <=? 1) ||
  forallb (fun source => channel_rule_for checked source target)
    (memory_sources checked target).

Definition a3 (checked : validated) : bool :=
  forallb (a3_rule checked) (rules_of checked) &&
  forallb (storage_declared checked)
    (map rr_target (filter (fun rule => rr_class rule =? class_memory)
       (rules_of checked))).

(*
 * A4, over-broad authority: each need entry is one set of declared names
 * for a new (source, target, class); every rule has an entry, and its
 * permissions are within it. A malformed entry is A4's finding, as in the
 * MVP checker.
 *)

Definition need_key (need : raw_need) (source target class : nat) : bool :=
  (rn_source need =? source) && (rn_target need =? target) &&
  (rn_class need =? class).

Definition need_entry_valid (policy : raw_policy) (accepted : list raw_need)
    (need : raw_need) : bool :=
  negb (existsb (fun earlier =>
      need_key earlier (rn_source need) (rn_target need) (rn_class need))
    accepted) &&
  mem (rn_source need) (rp_types policy) &&
  mem (rn_target need) (rp_types policy) &&
  match class_perms policy (rn_class need) with
  | Some perms =>
      negb (is_empty (rn_perms need)) && nodupb (rn_perms need) &&
      forallb (fun perm => mem perm perms) (rn_perms need)
  | None => false
  end.

(** [accept_needs] keeps each valid entry and records any invalid one. *)
Fixpoint accept_needs (policy : raw_policy) (accepted : list raw_need)
    (needs : list raw_need) : list raw_need * bool :=
  match needs with
  | [] => (accepted, true)
  | need :: rest =>
      if need_entry_valid policy accepted need then
        accept_needs policy (accepted ++ [need]) rest
      else (fst (accept_needs policy accepted rest), false)
  end.

Definition need_for (accepted : list raw_need) (rule : raw_rule)
    : option (list nat) :=
  match find (fun need => need_key need (rr_source rule) (rr_target rule)
                            (rr_class rule)) accepted with
  | Some need => Some (rn_perms need)
  | None => None
  end.

Definition a4 (checked : validated) : bool :=
  let accepted := accept_needs (v_policy checked) [] (v_needs checked) in
  snd accepted &&
  forallb (fun rule =>
      match need_for (fst accepted) rule with
      | Some perms => forallb (fun perm => mem perm perms) (rr_perms rule)
      | None => false
      end) (rules_of checked).

(*
 * A5, non-revocable authority: shared writable storage is a memory target
 * type one source type may write and another may read. A raw view carries
 * no revocation operation, so every view is static, and A5 passes with a
 * report, "static, not revocable, single writer", for each shared target
 * with one writer type, which V3's default permits for a static
 * configuration; a shared target with two writer types has no revocation
 * path and fails.
 *)

Definition writers (checked : validated) (target : nat) : list nat :=
  dedup (map rr_source (filter (fun rule =>
      (rr_class rule =? class_memory) && (rr_target rule =? target) &&
      mem perm_write (rr_perms rule)) (rules_of checked))).

Definition readers (checked : validated) (target : nat) : list nat :=
  dedup (map rr_source (filter (fun rule =>
      (rr_class rule =? class_memory) && (rr_target rule =? target) &&
      mem perm_read (rr_perms rule)) (rules_of checked))).

Definition shared_targets (checked : validated) : list nat :=
  filter (fun target =>
      existsb (fun writer =>
          existsb (fun reader => negb (reader =? writer))
            (readers checked target))
        (writers checked target))
    (dedup (map rr_target (filter (fun rule =>
        (rr_class rule =? class_memory) && mem perm_write (rr_perms rule))
      (rules_of checked)))).

Definition a5 (checked : validated) : bool :=
  forallb (fun target => length (writers checked target) <=? 1)
    (shared_targets checked).

(** [a5_report] is each shared target with its single writer type. *)
Definition a5_report (checked : validated) : list (nat * nat) :=
  flat_map (fun target =>
      match writers checked target with
      | [writer] => [(target, writer)]
      | _ => []
      end) (shared_targets checked).

(*
 * A6, information flow modulo the declared channels (Part 3): the flow
 * relation F relates distinct source types s1 and s2 when one memory rule
 * gives s1 write and another gives s2 read on one target type; the declared
 * channel relation D relates distinct s1 and s2 when one channel rule gives
 * s1 send and another gives s2 receive on one target type (D, like F,
 * relates distinct types, as the MVP checker reads it). A6 requires
 * F+ = D+. Both relations are finite lists of pairs over the declared
 * types, and their closures are computed by adding compositions until none
 * is new; A6 also checks that each computed closure is transitively closed,
 * so that its verdict never rests on the iteration's bound.
 *)

(** [pair_eqb] is executable equality of type pairs. *)
Definition pair_eqb (left right : nat * nat) : bool :=
  (fst left =? fst right) && (snd left =? snd right).

Definition pair_mem (pair : nat * nat) (pairs : list (nat * nat)) : bool :=
  existsb (pair_eqb pair) pairs.

Definition rule_pairs (class first second : nat) (rules : list raw_rule)
    : list (nat * nat) :=
  flat_map (fun one => flat_map (fun two =>
      if (rr_class one =? class) && (rr_class two =? class) &&
         (rr_target one =? rr_target two) &&
         negb (rr_source one =? rr_source two) &&
         mem first (rr_perms one) && mem second (rr_perms two)
      then [(rr_source one, rr_source two)] else []) rules) rules.

(** [flow_pairs] is F; [channel_pairs] is D. *)
Definition flow_pairs (checked : validated) : list (nat * nat) :=
  rule_pairs class_memory perm_write perm_read (rules_of checked).

Definition channel_pairs (checked : validated) : list (nat * nat) :=
  rule_pairs class_channel perm_send perm_receive (rules_of checked).

Definition compose_pairs (pairs : list (nat * nat)) : list (nat * nat) :=
  flat_map (fun one => flat_map (fun two =>
      if snd one =? fst two then [(fst one, snd two)] else []) pairs) pairs.

Definition closure_step (pairs : list (nat * nat)) : list (nat * nat) :=
  pairs ++
  filter (fun pair => negb (pair_mem pair pairs)) (compose_pairs pairs).

(** [closure_iter] adds compositions until a step adds none. *)
Fixpoint closure_iter (fuel : nat) (pairs : list (nat * nat))
    : list (nat * nat) :=
  match fuel with
  | 0 => pairs
  | S rest =>
      let next := closure_step pairs in
      if length next =? length pairs then pairs else closure_iter rest next
  end.

(** [closed] holds when every composition is already present. *)
Definition closed (pairs : list (nat * nat)) : bool :=
  forallb (fun pair => pair_mem pair pairs) (compose_pairs pairs).

Definition pairs_incl (left right : list (nat * nat)) : bool :=
  forallb (fun pair => pair_mem pair right) left.

(**
 * [closure] is the transitive closure of pairs over the declared types:
 * each step that adds a pair adds one of at most (types x types) pairs, so
 * one more step than that reaches the fixpoint.
 *)
Definition closure (checked : validated) (pairs : list (nat * nat))
    : list (nat * nat) :=
  let types := length (rp_types (v_policy checked)) in
  closure_iter (S (types * types)) pairs.

Definition a6 (checked : validated) : bool :=
  let flows := closure checked (flow_pairs checked) in
  let channels := closure checked (channel_pairs checked) in
  closed flows && closed channels && pairs_incl flows channels &&
  pairs_incl channels flows.

(*
 * A7, authority non-amplification: it constrains a delegation. A raw view
 * has no request vocabulary, and pause and terminate make no grant, so a
 * domain holding only those has delegated nothing and A7 is vacuous; a
 * domain holding any other domain permission would need the vocabulary
 * Part 6 leaves to a later plan, and A7 then fails closed, as the MVP
 * checker's does.
 *)

Definition delegating_rule (checked : validated) (rule : raw_rule) : bool :=
  (rr_class rule =? class_domain) &&
  mem (rr_source rule) (domain_types checked) &&
  existsb (fun perm =>
      negb ((perm =? perm_pause) || (perm =? perm_terminate)))
    (rr_perms rule).

Definition a7 (checked : validated) : bool :=
  negb (existsb (delegating_rule checked) (rules_of checked)).

(*
 * A8, manifest conformance, under Revision 1's reading (R1.3): every grant
 * of the view (presence as map, the leaf rights, a channel endpoint, a
 * management permission) is allowed by a rule for its subject's and
 * object's types in its class, as the MVP checker and the C mirror check
 * the grants; and, so that T2 covers each channel's endpoints directly, each
 * channel's writer has send and its reader receive on the channel's type.
 * Every generated view carries those endpoints as grants, so on every
 * generated view the verdict is the two checkers'. Structural bindings, the
 * hart binding among them, are mechanism metadata outside A8.
 *)

(** [grant_target_type] is a grant's object type, a subject's for a domain. *)
Definition grant_target_type (checked : validated) (grant : raw_grant) : nat :=
  if rg_class grant =? class_domain then subject_type checked (rg_object grant)
  else object_type checked (rg_object grant).

Definition grant_allowed (checked : validated) (grant : raw_grant) : bool :=
  forallb (fun perm =>
      decide checked (subject_type checked (rg_subject grant))
        (grant_target_type checked grant) (rg_class grant) perm)
    (rg_perms grant).

Definition endpoints_allowed (checked : validated) (channel : raw_channel)
    : bool :=
  decide checked (subject_type checked (rch_writer channel))
    (object_type checked (rch_object channel)) class_channel perm_send &&
  decide checked (subject_type checked (rch_reader channel))
    (object_type checked (rch_object channel)) class_channel perm_receive.

Definition a8 (checked : validated) : bool :=
  forallb (grant_allowed checked) (rv_grants (v_view checked)) &&
  forallb (endpoints_allowed checked) (rv_channels (v_view checked)).

(**
 * [verdicts] is the per-analysis result, indices 1 to 8, that the M3-5
 * oracle prints. An A1 failure leaves A2 to A8 not run: they are absent
 * from the list, which the C mirror and the MVP checker report as
 * not-run.
 *)
Definition verdicts (instance : raw_instance) : list (nat * bool) :=
  match validate_instance instance with
  | Some checked =>
      [(1, true); (2, a2 checked); (3, a3 checked); (4, a4 checked);
       (5, a5 checked); (6, a6 checked); (7, a7 checked); (8, a8 checked)]
  | None => [(1, false)]
  end.

(** [all_pass] is every analysis passing. *)
Definition all_pass : list (nat * bool) :=
  [(1, true); (2, true); (3, true); (4, true); (5, true); (6, true);
   (7, true); (8, true)].

(*
 * T2 (I11, A8 soundness): a validated view that passes A8 grants no
 * permission the policy denies, and each channel endpoint has its send or
 * receive rule. A8 is an upper bound: a view may grant less than the
 * policy allows and still pass.
 *)
Theorem policy_a8_sound :
  forall checked,
    a8 checked = true ->
    (forall grant perm,
       In grant (rv_grants (v_view checked)) ->
       In perm (rg_perms grant) ->
       decide checked (subject_type checked (rg_subject grant))
         (grant_target_type checked grant) (rg_class grant) perm = true) /\
    (forall channel,
       In channel (rv_channels (v_view checked)) ->
       decide checked (subject_type checked (rch_writer channel))
         (object_type checked (rch_object channel)) class_channel
         perm_send = true /\
       decide checked (subject_type checked (rch_reader channel))
         (object_type checked (rch_object channel)) class_channel
         perm_receive = true).
Proof.
  intros checked Ha8.
  unfold a8 in Ha8.
  apply andb_true_iff in Ha8 as [Hgrants Hchannels].
  rewrite forallb_forall in Hgrants, Hchannels.
  split.
  - intros grant perm Hgrant Hperm.
    specialize (Hgrants grant Hgrant).
    unfold grant_allowed in Hgrants.
    rewrite forallb_forall in Hgrants.
    exact (Hgrants perm Hperm).
  - intros channel Hchannel.
    specialize (Hchannels channel Hchannel).
    unfold endpoints_allowed in Hchannels.
    apply andb_true_iff in Hchannels.
    exact Hchannels.
Qed.

(*
 * The flow relations as propositions. [rule_relation] relates the distinct
 * source types of two rules of one class on one target, the first holding
 * [first] and the second [second]: F for memory write and read, D for
 * channel send and receive.
 *)
Definition rule_relation (class first second : nat) (rules : list raw_rule)
    (source1 source2 : nat) : Prop :=
  source1 <> source2 /\
  exists one two,
    In one rules /\ In two rules /\
    rr_class one = class /\ rr_class two = class /\
    rr_target one = rr_target two /\
    In first (rr_perms one) /\ In second (rr_perms two) /\
    rr_source one = source1 /\ rr_source two = source2.

(** [policy_flow] is Part 3's F; [declared_channel] is its D. *)
Definition policy_flow (checked : validated) : nat -> nat -> Prop :=
  rule_relation class_memory perm_write perm_read (rules_of checked).

Definition declared_channel (checked : validated) : nat -> nat -> Prop :=
  rule_relation class_channel perm_send perm_receive (rules_of checked).

(**
 * [view_flow] is the view's flow relation on subject types: a memory grant
 * with write to a subject of one type and one with read to a subject of
 * another type, on one object. It is lifted to types by the labeling, as F
 * is defined on types; two subjects of one type are one policy subject.
 *)
Definition view_flow (checked : validated) (type1 type2 : nat) : Prop :=
  type1 <> type2 /\
  exists grant1 grant2,
    In grant1 (rv_grants (v_view checked)) /\
    In grant2 (rv_grants (v_view checked)) /\
    rg_class grant1 = class_memory /\ rg_class grant2 = class_memory /\
    rg_object grant1 = rg_object grant2 /\
    In perm_write (rg_perms grant1) /\ In perm_read (rg_perms grant2) /\
    subject_type checked (rg_subject grant1) = type1 /\
    subject_type checked (rg_subject grant2) = type2.

Lemma grant_target_type_memory :
  forall checked grant,
    rg_class grant = class_memory ->
    grant_target_type checked grant = object_type checked (rg_object grant).
Proof.
  intros checked grant Hclass.
  unfold grant_target_type.
  rewrite Hclass.
  reflexivity.
Qed.

(**
 * [policy_a8_flow_confinement] is T3a: a validated view passing A8 has
 * its flow relation contained in the policy's.
 *)
Theorem policy_a8_flow_confinement :
  forall checked,
    a8 checked = true ->
    forall type1 type2,
      view_flow checked type1 type2 -> policy_flow checked type1 type2.
Proof.
  intros checked Ha8 type1 type2
    [Hdistinct [grant1 [grant2 [Hin1 [Hin2 [Hclass1 [Hclass2
      [Hobject [Hwrite [Hread [Htype1 Htype2]]]]]]]]]]].
  destruct (policy_a8_sound checked Ha8) as [Hgrants _].
  pose proof (Hgrants grant1 perm_write Hin1 Hwrite) as Hallow1.
  pose proof (Hgrants grant2 perm_read Hin2 Hread) as Hallow2.
  apply decide_spec in Hallow1, Hallow2.
  rewrite grant_target_type_memory in Hallow1, Hallow2 by assumption.
  destruct Hallow1 as [rule1 [Hrule1 [Hsource1 [Htarget1 [Hrclass1 Hperm1]]]]].
  destruct Hallow2 as [rule2 [Hrule2 [Hsource2 [Htarget2 [Hrclass2 Hperm2]]]]].
  split; [exact Hdistinct |].
  exists rule1, rule2.
  repeat split; try assumption.
  - congruence.
  - congruence.
  - congruence.
  - congruence.
  - congruence.
Qed.

Lemma pair_mem_in :
  forall pair pairs, pair_mem pair pairs = true <-> In pair pairs.
Proof.
  intros [a b] pairs.
  unfold pair_mem.
  rewrite existsb_exists.
  split.
  - intros [[c d] [Hin Heq]].
    unfold pair_eqb in Heq.
    simpl in Heq.
    apply andb_true_iff in Heq as [Hac Hbd].
    apply Nat.eqb_eq in Hac, Hbd.
    subst.
    exact Hin.
  - intros Hin.
    exists (a, b).
    split; [exact Hin |].
    unfold pair_eqb.
    simpl.
    rewrite !Nat.eqb_refl.
    reflexivity.
Qed.

Lemma rule_pairs_spec :
  forall class first second rules source1 source2,
    In (source1, source2) (rule_pairs class first second rules) <->
    rule_relation class first second rules source1 source2.
Proof.
  intros class first second rules source1 source2.
  unfold rule_pairs, rule_relation.
  rewrite in_flat_map.
  split.
  - intros [one [Hone Hinner]].
    rewrite in_flat_map in Hinner.
    destruct Hinner as [two [Htwo Hpair]].
    destruct ((rr_class one =? class) && (rr_class two =? class) &&
              (rr_target one =? rr_target two) &&
              negb (rr_source one =? rr_source two) &&
              mem first (rr_perms one) && mem second (rr_perms two))
      eqn:Hcheck; [| contradiction].
    destruct Hpair as [Hpair | []].
    inversion Hpair; subst source1 source2.
    repeat rewrite andb_true_iff in Hcheck.
    destruct Hcheck as
      [[[[[Hclass1 Hclass2] Htarget] Hsource] Hfirst] Hsecond].
    apply Nat.eqb_eq in Hclass1, Hclass2, Htarget.
    apply negb_true_iff, Nat.eqb_neq in Hsource.
    apply mem_in in Hfirst, Hsecond.
    split; [exact Hsource |].
    exists one, two.
    repeat split; assumption.
  - intros [Hdistinct [one [two [Hone [Htwo [Hclass1 [Hclass2 [Htarget
      [Hfirst [Hsecond [Hsource1 Hsource2]]]]]]]]]]].
    exists one.
    split; [exact Hone |].
    rewrite in_flat_map.
    exists two.
    split; [exact Htwo |].
    subst source1 source2.
    rewrite Hclass1, Hclass2, Htarget, !Nat.eqb_refl.
    apply Nat.eqb_neq in Hdistinct.
    rewrite Hdistinct.
    apply mem_in in Hfirst, Hsecond.
    rewrite Hfirst, Hsecond.
    simpl.
    left.
    reflexivity.
Qed.

Lemma compose_pairs_spec :
  forall pairs source target,
    In (source, target) (compose_pairs pairs) ->
    exists middle, In (source, middle) pairs /\ In (middle, target) pairs.
Proof.
  intros pairs source target Hin.
  unfold compose_pairs in Hin.
  rewrite in_flat_map in Hin.
  destruct Hin as [[a b] [Hone Hinner]].
  rewrite in_flat_map in Hinner.
  destruct Hinner as [[c d] [Htwo Hpair]].
  simpl in Hpair.
  destruct (b =? c) eqn:Hbc; [| contradiction].
  destruct Hpair as [Hpair | []].
  inversion Hpair; subst a d.
  apply Nat.eqb_eq in Hbc.
  subst c.
  exists b.
  split; assumption.
Qed.

Lemma compose_pairs_complete :
  forall pairs source middle target,
    In (source, middle) pairs -> In (middle, target) pairs ->
    In (source, target) (compose_pairs pairs).
Proof.
  intros pairs source middle target Hone Htwo.
  unfold compose_pairs.
  rewrite in_flat_map.
  exists (source, middle).
  split; [exact Hone |].
  rewrite in_flat_map.
  exists (middle, target).
  split; [exact Htwo |].
  simpl.
  rewrite Nat.eqb_refl.
  left.
  reflexivity.
Qed.

Lemma closure_iter_sound :
  forall (relation : nat -> nat -> Prop) fuel pairs,
    (forall source target, In (source, target) pairs ->
       clos_trans nat relation source target) ->
    forall source target, In (source, target) (closure_iter fuel pairs) ->
      clos_trans nat relation source target.
Proof.
  intros relation fuel.
  induction fuel as [| fuel IH]; intros pairs Hsound source target Hin.
  - exact (Hsound source target Hin).
  - simpl in Hin.
    destruct (length (closure_step pairs) =? length pairs).
    + exact (Hsound source target Hin).
    + apply (IH (closure_step pairs)); [| exact Hin].
      clear source target Hin.
      intros source target Hin.
      unfold closure_step in Hin.
      apply in_app_or in Hin as [Hold | Hnew].
      * exact (Hsound source target Hold).
      * apply filter_In in Hnew as [Hcomposed _].
        destruct (compose_pairs_spec pairs source target Hcomposed)
          as [middle [Hfirst Hsecond]].
        apply t_trans with middle.
        -- exact (Hsound source middle Hfirst).
        -- exact (Hsound middle target Hsecond).
Qed.

Lemma closure_iter_incl :
  forall fuel pairs pair, In pair pairs -> In pair (closure_iter fuel pairs).
Proof.
  intros fuel.
  induction fuel as [| fuel IH]; intros pairs pair Hin.
  - exact Hin.
  - simpl.
    destruct (length (closure_step pairs) =? length pairs).
    + exact Hin.
    + apply IH.
      unfold closure_step.
      apply in_or_app.
      left.
      exact Hin.
Qed.

Lemma closed_complete :
  forall (relation : nat -> nat -> Prop) pairs,
    closed pairs = true ->
    (forall source target, relation source target ->
       In (source, target) pairs) ->
    forall source target, clos_trans nat relation source target ->
      In (source, target) pairs.
Proof.
  intros relation pairs Hclosed Hbase source target Hclosure.
  induction Hclosure as [source target Hstep |
    source middle target _ IHfirst _ IHsecond].
  - exact (Hbase source target Hstep).
  - unfold closed in Hclosed.
    rewrite forallb_forall in Hclosed.
    apply pair_mem_in.
    apply Hclosed.
    apply compose_pairs_complete with middle; assumption.
Qed.

Lemma closure_equal_one_way :
  forall checked (relation1 relation2 : nat -> nat -> Prop) pairs1 pairs2,
    (forall source target,
       In (source, target) pairs1 <-> relation1 source target) ->
    (forall source target,
       In (source, target) pairs2 <-> relation2 source target) ->
    closed (closure checked pairs1) = true ->
    pairs_incl (closure checked pairs1) (closure checked pairs2) = true ->
    forall source target,
      clos_trans nat relation1 source target ->
      clos_trans nat relation2 source target.
Proof.
  intros checked relation1 relation2 pairs1 pairs2 Hspec1 Hspec2 Hclosed
    Hincl source target Hclosure.
  assert (Hin : In (source, target) (closure checked pairs1)).
  {
    apply (closed_complete relation1); [exact Hclosed | | exact Hclosure].
    intros a b Hrelation.
    apply closure_iter_incl.
    apply Hspec1.
    exact Hrelation.
  }
  unfold pairs_incl in Hincl.
  rewrite forallb_forall in Hincl.
  apply Hincl, pair_mem_in in Hin.
  unfold closure in Hin.
  eapply closure_iter_sound; [| exact Hin].
  intros a b Hpair.
  apply t_step.
  apply Hspec2.
  exact Hpair.
Qed.

(**
 * [policy_a6_closure_equality] is T3b: a validated policy passing A6 has
 * the transitive closure of its flow relation equal to that of its
 * declared channel relation, F+ = D+, closures taken over the finite
 * declared types.
 *)
Theorem policy_a6_closure_equality :
  forall checked,
    a6 checked = true ->
    forall source target,
      clos_trans nat (policy_flow checked) source target <->
      clos_trans nat (declared_channel checked) source target.
Proof.
  intros checked Ha6 source target.
  unfold a6 in Ha6.
  repeat rewrite andb_true_iff in Ha6.
  destruct Ha6 as [[[Hclosed_flows Hclosed_channels] Hflows] Hchannels].
  split.
  - apply (closure_equal_one_way checked (policy_flow checked)
      (declared_channel checked) (flow_pairs checked) (channel_pairs checked));
      try assumption; intros a b; apply rule_pairs_spec.
  - apply (closure_equal_one_way checked (declared_channel checked)
      (policy_flow checked) (channel_pairs checked) (flow_pairs checked));
      try assumption; intros a b; apply rule_pairs_spec.
Qed.

(** [delegation_free] holds when no domain holds a delegating permission. *)
Definition delegation_free (checked : validated) : Prop :=
  forall rule,
    In rule (rules_of checked) -> rr_class rule = class_domain ->
    In (rr_source rule) (domain_types checked) ->
    forall perm, In perm (rr_perms rule) ->
      perm = perm_pause \/ perm = perm_terminate.

(**
 * [policy_a7_vacuous] states A7's vacuity: with no request vocabulary, A7
 * passes exactly when no domain holds a domain permission beyond pause and
 * terminate, which make no grant, so it holds vacuously for a view without
 * delegation and fails closed otherwise.
 *)
Theorem policy_a7_vacuous :
  forall checked, a7 checked = true <-> delegation_free checked.
Proof.
  intros checked.
  unfold a7, delegation_free.
  rewrite negb_true_iff.
  split.
  - intros Hnone rule Hrule Hclass Hsource perm Hperm.
    assert (Hquiet : delegating_rule checked rule = false).
    {
      destruct (delegating_rule checked rule) eqn:Hdelegating;
        [| reflexivity].
      assert (Hfound : existsb (delegating_rule checked) (rules_of checked)
                       = true).
      { apply existsb_exists. exists rule. split; assumption. }
      rewrite Hfound in Hnone.
      discriminate.
    }
    unfold delegating_rule in Hquiet.
    rewrite Hclass, Nat.eqb_refl in Hquiet.
    apply mem_in in Hsource.
    rewrite Hsource in Hquiet.
    simpl in Hquiet.
    destruct (existsb (fun perm => negb ((perm =? perm_pause) ||
                                         (perm =? perm_terminate)))
                (rr_perms rule)) eqn:Hany; [discriminate |].
    destruct ((perm =? perm_pause) || (perm =? perm_terminate)) eqn:Hmanagement.
    + apply orb_true_iff in Hmanagement as [Hpause | Hterminate].
      * left. apply Nat.eqb_eq. exact Hpause.
      * right. apply Nat.eqb_eq. exact Hterminate.
    + assert (Hfound : existsb (fun perm => negb ((perm =? perm_pause) ||
                                                 (perm =? perm_terminate)))
                         (rr_perms rule) = true).
      { apply existsb_exists. exists perm. rewrite Hmanagement. auto. }
      rewrite Hfound in Hany.
      discriminate.
  - intros Hfree.
    destruct (existsb (delegating_rule checked) (rules_of checked))
      eqn:Hfound; [| reflexivity].
    apply existsb_exists in Hfound as [rule [Hrule Hdelegating]].
    unfold delegating_rule in Hdelegating.
    repeat rewrite andb_true_iff in Hdelegating.
    destruct Hdelegating as [[Hclass Hsource] Hany].
    apply Nat.eqb_eq in Hclass.
    apply mem_in in Hsource.
    apply existsb_exists in Hany as [perm [Hperm Hbeyond]].
    destruct (Hfree rule Hrule Hclass Hsource perm Hperm) as [Hp | Hp];
      subst perm; discriminate.
Qed.

(**
 * [policy_monitor_memory_ungranted] connects I2 and I15 to the view: in a
 * validated view passing A3 and A8, no domain holds any permission, so no
 * map, on monitor memory; the MVP scenarios label the hart region monitor
 * memory.
 *)
Theorem policy_monitor_memory_ungranted :
  forall checked,
    a3 checked = true -> a8 checked = true ->
    forall grant object,
      In grant (rv_grants (v_view checked)) ->
      In (rg_subject grant) (domains checked) ->
      rg_class grant <> class_domain ->
      In object (rl_objects (v_labeling checked)) ->
      ro_object object = rg_object grant ->
      monitor_object checked object = true ->
      rg_perms grant = [].
Proof.
  intros checked Ha3 Ha8 grant object Hgrant Hdomain Hclass Hobject
    Hsame Hmonitor.
  destruct (rg_perms grant) as [| perm rest] eqn:Hperms; [reflexivity |].
  exfalso.
  destruct (policy_a8_sound checked Ha8) as [Hgrants _].
  assert (Hin : In perm (rg_perms grant))
    by (rewrite Hperms; left; reflexivity).
  pose proof (Hgrants grant perm Hgrant Hin) as Hallowed.
  apply decide_spec in Hallowed.
  destruct Hallowed as [rule [Hrule [Hsource [Htarget _]]]].
  unfold a3 in Ha3.
  apply andb_true_iff in Ha3 as [Hrules _].
  rewrite forallb_forall in Hrules.
  specialize (Hrules rule Hrule).
  unfold a3_rule in Hrules.
  cbv zeta in Hrules.
  repeat rewrite andb_true_iff in Hrules.
  destruct Hrules as [[[Hmonitor_rule _] _] _].
  assert (Hheld : mem (rr_source rule) (domain_types checked) = true).
  {
    apply mem_in.
    rewrite Hsource.
    unfold domain_types.
    apply in_map.
    exact Hdomain.
  }
  assert (Hmonitor_type : mem (rr_target rule) (monitor_types checked) = true).
  {
    apply mem_in.
    rewrite Htarget.
    unfold grant_target_type.
    apply Nat.eqb_neq in Hclass.
    rewrite Hclass.
    unfold monitor_types.
    rewrite <- Hsame.
    apply (in_map (fun object => object_type checked (ro_object object))).
    apply filter_In.
    split; assumption.
  }
  rewrite Hheld, Hmonitor_type in Hmonitor_rule.
  discriminate.
Qed.

(*
 * The adapter from the accepted canonical state (Model.v) to its policy
 * view. Subject ids: the monitor 0, then the canonical domains in order;
 * object ids: the canonical resources in [platform_inventory]'s order,
 * then the channel whose storage is the shared frame. The view's presence
 * grants (map) are the canonical mappings; their leaf rights are the
 * canonical authority's; the shared frame's channel has the producer as
 * writer and the consumer as reader, by [channel_rights]. Model 0.2 runs
 * both domains on its one hart by checked switches and is not a binding
 * instance (Binding.v), so the view binds no domain to a hart; its started
 * hart, the control hart, is that one hart. This is the C mirror's
 * be_view_of_canonical, and the generator's projection (Instances.v,
 * instance1_m02).
 *)

Definition domain_subject (subject : domain) : nat :=
  match subject with
  | Management => 1
  | Protected => 2
  end.

Definition frame_object (object : frame) : nat :=
  match object with
  | MonitorCodeFrame => 0
  | MonitorDataFrame => 1
  | ManagementRootFrame => 2
  | ProtectedRootFrame => 3
  | ManagementStackFrame => 4
  | ProtectedStackFrame => 5
  | ManagementStateFrame => 6
  | ProtectedStateFrame => 7
  | ManagementPrivateFrame => 8
  | ProtectedPrivateFrame => 9
  | SharedFrame => 10
  end.

Definition shared_channel_object : nat := 11.

Definition fixed_profile_hart : nat := 0.

(** [perms_of_rights] is a rights record's leaf permissions. *)
Definition perms_of_rights (granted : rights) : list nat :=
  (if right_read granted then [perm_read] else []) ++
  (if right_write granted then [perm_write] else []) ++
  (if right_execute granted then [perm_execute] else []).

(** [perm_of_access] is the permission an accepted access kind exercises. *)
Definition perm_of_access (requested : access_kind) : nat :=
  match requested with
  | AccessRead => perm_read
  | AccessWrite => perm_write
  | AccessExecute => perm_execute
  end.

(** [modeled_gpas] is Model.v's complete guest-physical address space. *)
Definition modeled_gpas : list gpa := [PrivateGPA; SharedGPA].

Definition mapping_grants (subject : domain) : list raw_grant :=
  flat_map (fun address =>
      match canonical_mapping subject address with
      | Some (object, _) =>
          [mk_raw_grant (domain_subject subject) (frame_object object)
             class_memory
             (perm_map :: perms_of_rights (canonical_authority subject object))]
      | None => []
      end) modeled_gpas.

Definition endpoint_grants (subject : domain) : list raw_grant :=
  if right_write (channel_rights subject) then
    [mk_raw_grant (domain_subject subject) shared_channel_object class_channel
       [perm_send]]
  else if right_read (channel_rights subject) then
    [mk_raw_grant (domain_subject subject) shared_channel_object class_channel
       [perm_receive]]
  else [].

Definition channel_end (writes : bool) (subjects : list domain) : nat :=
  match find (fun subject =>
      Bool.eqb (right_write (channel_rights subject)) writes &&
      right_read (channel_rights subject)) subjects with
  | Some subject => domain_subject subject
  | None => monitor_subject
  end.

(** [view_of_canonical] is the canonical state's policy view. *)
Definition view_of_canonical (canonical : canonical_state) : raw_view :=
  {| rv_ownerships :=
       flat_map (fun object =>
           match frame_owner object with
           | Some owner =>
               [mk_raw_ownership (frame_object object) (domain_subject owner)]
           | None => []
           end) (canonical_resources canonical);
     rv_channels :=
       [mk_raw_channel shared_channel_object (frame_object SharedFrame)
          (channel_end true (canonical_domains canonical))
          (channel_end false (canonical_domains canonical))];
     rv_grants :=
       flat_map (fun subject =>
           mapping_grants subject ++ endpoint_grants subject)
         (canonical_domains canonical);
     rv_bindings := [];
     rv_harts := [fixed_profile_hart];
     rv_control_hart := fixed_profile_hart |}.

(*
 * Identities, for reporting and equivalence only, as the accepted
 * canonical identity is. They use the C mirror's method (model/src/
 * policy.c): 64-bit FNV-1a over each field as a little-endian 64-bit word,
 * a tag first (1 policy, 2 labeling, 4 combined) and each list's length
 * before its elements, so a policy's and a labeling's identities here equal
 * be_policy_identity and be_labeling_identity of the same terms. The
 * combined configuration identity folds the canonical identity, the policy
 * identity, and the labeling identity in the MVP checker's order
 * (manifest, policy, labeling), as be_combined_identity does. The canonical
 * identity is the accepted model's ([canonical_identity], Model.v), not the
 * C canonical state's, so a sealed combined identity is this model's own;
 * only determinism is claimed. Need sets are part of no identity, as the
 * MVP checker's identity omits them.
 *)

Definition fnv_offset : N := 14695981039346656037.
Definition fnv_prime : N := 1099511628211.
Definition fnv_modulus : N := 18446744073709551616.

(** [fnv_byte] folds one byte. *)
Definition fnv_byte (identity byte : N) : N :=
  N.modulo (N.lxor identity byte * fnv_prime) fnv_modulus.

(** [fnv_bytes] folds a word's low [count] bytes, least significant first. *)
Fixpoint fnv_bytes (count : nat) (identity word : N) : N :=
  match count with
  | 0 => identity
  | S rest =>
      fnv_bytes rest (fnv_byte identity (N.modulo word 256)) (N.div word 256)
  end.

(** [fnv_word] folds one identifier as a 64-bit word. *)
Definition fnv_word (identity : N) (word : nat) : N :=
  fnv_bytes 8 identity (N.of_nat word).

(** [fnv_list] folds a list's length, then its elements. *)
Definition fnv_list (identity : N) (words : list nat) : N :=
  fold_left fnv_word words (fnv_word identity (length words)).

Definition policy_identity (policy : raw_policy) : N :=
  let identity := fnv_list (fnv_word fnv_offset 1) (rp_types policy) in
  let identity :=
    fold_left (fun identity declared =>
        fnv_list (fnv_word identity (rc_class declared)) (rc_perms declared))
      (rp_classes policy)
      (fnv_word identity (length (rp_classes policy))) in
  fold_left (fun identity rule =>
      fnv_list
        (fnv_word (fnv_word (fnv_word identity (rr_source rule))
           (rr_target rule)) (rr_class rule))
        (rr_perms rule))
    (rp_rules policy) (fnv_word identity (length (rp_rules policy))).

Definition entity_kind (entity : raw_entity) : nat :=
  match entity with
  | RawSubject _ => 0
  | RawObject _ => 1
  end.

Definition entity_id (entity : raw_entity) : nat :=
  match entity with
  | RawSubject subject => subject
  | RawObject object => object
  end.

Definition labeling_identity (labeling : raw_labeling) : N :=
  let identity := fnv_list (fnv_word fnv_offset 2) (rl_subjects labeling) in
  let identity :=
    fold_left (fun identity object =>
        fnv_word (fnv_word identity (ro_object object)) (ro_class object))
      (rl_objects labeling)
      (fnv_word identity (length (rl_objects labeling))) in
  fold_left (fun identity label =>
      fnv_word
        (fnv_word (fnv_word identity (entity_kind (rl_entity label)))
           (entity_id (rl_entity label)))
        (rl_type label))
    (rl_labels labeling) (fnv_word identity (length (rl_labels labeling))).

(** [combined_identity] is one configuration identity from three. *)
Definition combined_identity (canonical policy labeling : N) : N :=
  fnv_bytes 8
    (fnv_bytes 8 (fnv_bytes 8 (fnv_word fnv_offset 4) canonical) policy)
    labeling.

(**
 * [canonical_labeling] holds when a labeling's entities are exactly the
 * canonical state's view's: the monitor and the canonical domains as
 * subjects 0 to n, and the frames then the channel as objects 0 to m, each
 * of its class (the C mirror's sealing checks the same).
 *)
Definition canonical_labeling (canonical : canonical_state)
    (labeling : raw_labeling) : bool :=
  let subjects := S (length (canonical_domains canonical)) in
  let frames := length (canonical_resources canonical) in
  (length (rl_subjects labeling) =? subjects) &&
  forallb (fun subject => mem subject (rl_subjects labeling))
    (seq 0 subjects) &&
  (length (rl_objects labeling) =? S frames) &&
  forallb (fun object =>
      existsb (fun listed =>
          (ro_object listed =? object) &&
          (ro_class listed =?
           if object <? frames then class_memory else class_channel))
        (rl_objects labeling)) (seq 0 (S frames)).

(**
 * [sealed_with_policy] is a canonical state sealed with a policy and a
 * labeling that passed A1 to A6 and A8 on its view, with one combined
 * configuration identity.
 *)
Record sealed_with_policy : Type := mk_sealed_with_policy {
  swp_canonical : canonical_state;
  swp_validated : validated;
  swp_canonical_identity : N;
  swp_policy_identity : N;
  swp_labeling_identity : N;
  swp_configuration_identity : N
}.

Definition conforms (checked : validated) : bool :=
  a2 checked && a3 checked && a4 checked && a5 checked && a6 checked &&
  a8 checked.

(**
 * [seal_with_policy] is Part 7's gate as a layer around the accepted seam:
 * the accepted [canonical_state] is untouched, and a policy-sealed record
 * exists only when the labeling is the canonical state's and A1 to A6 and
 * A8 pass on the canonical state's view. A7 is not a condition: it is
 * vacuous without a request vocabulary (the plan's gate is A1 to A6 and A8).
 *)
Definition seal_with_policy (canonical : canonical_state) (policy : raw_policy)
    (labeling : raw_labeling) (needs : list raw_need)
    : option sealed_with_policy :=
  if canonical_labeling canonical labeling then
    match validate policy labeling needs (view_of_canonical canonical) with
    | Some checked =>
        if conforms checked then
          Some {| swp_canonical := canonical;
                  swp_validated := checked;
                  swp_canonical_identity :=
                    N.of_nat (canonical_identity canonical);
                  swp_policy_identity := policy_identity policy;
                  swp_labeling_identity := labeling_identity labeling;
                  swp_configuration_identity :=
                    combined_identity (N.of_nat (canonical_identity canonical))
                      (policy_identity policy) (labeling_identity labeling) |}
        else None
    | None => None
    end
  else None.

(**
 * [policy_seal_requires_conformance] is T5: a policy-sealed state exists
 * only for inputs passing A1 to A6 and A8 on the canonical state's view,
 * with a labeling of exactly that state's entities, and it binds that
 * canonical state, policy, and labeling through one combined configuration
 * identity.
 *)
Theorem policy_seal_requires_conformance :
  forall canonical policy labeling needs sealed,
    seal_with_policy canonical policy labeling needs = Some sealed ->
    exists checked,
      canonical_labeling canonical labeling = true /\
      validate policy labeling needs (view_of_canonical canonical) =
        Some checked /\
      a2 checked = true /\ a3 checked = true /\ a4 checked = true /\
      a5 checked = true /\ a6 checked = true /\ a8 checked = true /\
      swp_canonical sealed = canonical /\ swp_validated sealed = checked /\
      swp_canonical_identity sealed =
        N.of_nat (canonical_identity canonical) /\
      swp_policy_identity sealed = policy_identity policy /\
      swp_labeling_identity sealed = labeling_identity labeling /\
      swp_configuration_identity sealed =
        combined_identity (N.of_nat (canonical_identity canonical))
          (policy_identity policy) (labeling_identity labeling).
Proof.
  intros canonical policy labeling needs sealed Hsealed.
  unfold seal_with_policy in Hsealed.
  destruct (canonical_labeling canonical labeling) eqn:Hlabeling;
    [| discriminate].
  destruct (validate policy labeling needs (view_of_canonical canonical))
    as [checked |] eqn:Hvalid; [| discriminate].
  destruct (conforms checked) eqn:Hconforms; [| discriminate].
  inversion Hsealed; subst sealed.
  unfold conforms in Hconforms.
  repeat rewrite andb_true_iff in Hconforms.
  destruct Hconforms as [[[[[Ha2 Ha3] Ha4] Ha5] Ha6] Ha8].
  exists checked.
  repeat split; assumption.
Qed.

(*
 * Model 0.2's projection of Instance 1 (security model v1, Part 2;
 * Revision 1's erratum, R1.5): Instance 1's policy restricted to the
 * objects the accepted model has, so without the guest-code types
 * mgmt_code_t and prot_code_t, their two rules, and any execute grant.
 *
 *   types:    monitor_t 0, mgmt_t 1, prot_t 2, mgmt_private_t 3,
 *             prot_private_t 4, shared_mp_t 5, monitor_mem_t 6
 *   classes:  memory 0 {read write execute map}, channel 1 {send receive}
 *   subjects: the monitor 0, Management 1, Protected 2
 *   objects:  the eleven frames 0 to 10 in platform_inventory's order
 *             (monitor code, data, two roots, two stacks, two saved
 *             states: monitor_mem_t; the two private frames; the shared
 *             frame: shared_mp_t), and the shared frame's channel 11
 *
 * Its view is [view_of_canonical canonical_configuration], by computation
 * ([policy_projection_view]): four non-executable mappings, the private
 * ones and the producer's shared one read-write, the consumer's shared one
 * read-only, each with map for its presence, the channel's endpoints, and
 * no hart binding. It is the adapter's side of the projection; the
 * generator derives the same term from Instance 1's fixture as
 * Instances.v's instance1_m02, and PolicyClaims.v shows the two equal.
 *)
Definition projection_m02 : raw_instance :=
  {| ri_policy :=
       {| rp_types := [0; 1; 2; 3; 4; 5; 6];
          rp_classes := [mk_raw_class 0 [0; 1; 2; 3]; mk_raw_class 1 [4; 5]];
          rp_rules :=
            [mk_raw_rule 1 3 0 [0; 1; 3]; mk_raw_rule 1 5 0 [0; 1; 3];
             mk_raw_rule 1 5 1 [4];
             mk_raw_rule 2 4 0 [0; 1; 3]; mk_raw_rule 2 5 0 [0; 3];
             mk_raw_rule 2 5 1 [5]] |};
     ri_labeling :=
       {| rl_subjects := [0; 1; 2];
          rl_objects :=
            [mk_raw_object 0 0; mk_raw_object 1 0; mk_raw_object 2 0;
             mk_raw_object 3 0; mk_raw_object 4 0; mk_raw_object 5 0;
             mk_raw_object 6 0; mk_raw_object 7 0; mk_raw_object 8 0;
             mk_raw_object 9 0; mk_raw_object 10 0; mk_raw_object 11 1];
          rl_labels :=
            [mk_raw_label (RawSubject 0) 0; mk_raw_label (RawSubject 1) 1;
             mk_raw_label (RawSubject 2) 2;
             mk_raw_label (RawObject 0) 6; mk_raw_label (RawObject 1) 6;
             mk_raw_label (RawObject 2) 6; mk_raw_label (RawObject 3) 6;
             mk_raw_label (RawObject 4) 6; mk_raw_label (RawObject 5) 6;
             mk_raw_label (RawObject 6) 6; mk_raw_label (RawObject 7) 6;
             mk_raw_label (RawObject 8) 3; mk_raw_label (RawObject 9) 4;
             mk_raw_label (RawObject 10) 5; mk_raw_label (RawObject 11) 5] |};
     ri_needs :=
       [mk_raw_need 1 3 0 [0; 1; 3]; mk_raw_need 1 5 0 [0; 1; 3];
        mk_raw_need 1 5 1 [4];
        mk_raw_need 2 4 0 [0; 1; 3]; mk_raw_need 2 5 0 [0; 3];
        mk_raw_need 2 5 1 [5]];
     ri_view :=
       {| rv_ownerships := [mk_raw_ownership 8 1; mk_raw_ownership 9 2];
          rv_channels := [mk_raw_channel 11 10 1 2];
          rv_grants :=
            [mk_raw_grant 1 8 0 [3; 0; 1]; mk_raw_grant 1 10 0 [3; 0; 1];
             mk_raw_grant 1 11 1 [4];
             mk_raw_grant 2 9 0 [3; 0; 1]; mk_raw_grant 2 10 0 [3; 0];
             mk_raw_grant 2 11 1 [5]];
          rv_bindings := [];
          rv_harts := [0];
          rv_control_hart := 0 |} |}.

(** [policy_projection_view] is the adapter's view of the fixed profile. *)
Theorem policy_projection_view :
  ri_view projection_m02 = view_of_canonical canonical_configuration.
Proof.
  vm_compute.
  reflexivity.
Qed.

(**
 * [policy_access_permission_bridge] is the first bridge: an accepted
 * rights record allows an access kind exactly when the permission that
 * kind exercises is among the record's leaf permissions.
 *)
Theorem policy_access_permission_bridge :
  forall granted requested,
    rights_allow granted requested = true <->
    In (perm_of_access requested) (perms_of_rights granted).
Proof.
  intros [[] [] []] []; simpl; split; intros H; try discriminate;
    try reflexivity; intuition discriminate.
Qed.

(**
 * [policy_authority_grant_bridge] is the second bridge: each canonical
 * mapping is a grant of the canonical state's view, with map for its
 * presence and the canonical authority's leaf permissions.
 *)
Theorem policy_authority_grant_bridge :
  forall subject address object derived_rights,
    canonical_mapping subject address = Some (object, derived_rights) ->
    In (mk_raw_grant (domain_subject subject) (frame_object object)
          class_memory
          (perm_map :: perms_of_rights (canonical_authority subject object)))
      (rv_grants (view_of_canonical canonical_configuration)).
Proof.
  intros subject address object derived_rights Hmapping.
  destruct subject, address; simpl in Hmapping;
    inversion Hmapping; subst; vm_compute; intuition.
Qed.

Lemma rights_subset_allow :
  forall derived authority requested,
    rights_subset derived authority ->
    rights_allow derived requested = true ->
    rights_allow authority requested = true.
Proof.
  intros derived authority requested [Hread [Hwrite Hexecute]] Hallowed.
  destruct requested; simpl in *; auto.
Qed.

(** [projection_check] evaluates one analysis on the validated projection. *)
Definition projection_check (check : validated -> bool) : bool :=
  match validate_instance projection_m02 with
  | Some checked => check checked
  | None => false
  end.

(**
 * [policy_projection_mappings_allowed] is T4: T2 composed with the
 * accepted [claim_derived_root_soundness] (presence) and
 * [claim_derived_rights_bounded] (leaf rights), used as accepted, through
 * the adapter and the two bridges. For Model 0.2's projection of Instance
 * 1, every mapping of [derive_enforcement canonical_configuration] has its
 * presence (map) and each of its leaf rights allowed by [decide]. It covers
 * the projection's four mappings; it says nothing about the two guest-code
 * resources and their execute right of the full Instance 1, which the
 * accepted model does not contain.
 *)
Theorem policy_projection_mappings_allowed :
  exists checked,
    validate_instance projection_m02 = Some checked /\
    forall stage_root address object derived_rights,
      derived_mapping (derive_enforcement canonical_configuration)
        stage_root address = Some (object, derived_rights) ->
      decide checked
        (subject_type checked (domain_subject (domain_for_root stage_root)))
        (object_type checked (frame_object object)) class_memory perm_map =
        true /\
      forall requested,
        rights_allow derived_rights requested = true ->
        decide checked
          (subject_type checked (domain_subject (domain_for_root stage_root)))
          (object_type checked (frame_object object)) class_memory
          (perm_of_access requested) = true.
Proof.
  destruct (validate_instance projection_m02) as [checked |] eqn:Hvalid;
    [| vm_compute in Hvalid; discriminate].
  exists checked.
  split; [reflexivity |].
  assert (Ha8 : a8 checked = true).
  {
    assert (Hcomputed : projection_check a8 = true)
      by (vm_compute; reflexivity).
    unfold projection_check in Hcomputed.
    rewrite Hvalid in Hcomputed.
    exact Hcomputed.
  }
  destruct (validate_fields _ _ _ _ _ Hvalid) as [_ [_ [_ Hview]]].
  destruct (policy_a8_sound checked Ha8) as [Hallowed _].
  intros stage_root address object derived_rights Hmapping.
  pose proof (claim_derived_root_soundness architecture_model_0_2_claims
    canonical_configuration stage_root address object derived_rights Hmapping)
    as Hcanonical.
  pose proof (claim_derived_rights_bounded architecture_model_0_2_claims
    canonical_configuration stage_root address object derived_rights Hmapping)
    as Hbounded.
  pose proof (policy_authority_grant_bridge _ _ _ _ Hcanonical) as Hgrant.
  rewrite <- policy_projection_view, <- Hview in Hgrant.
  split.
  - exact (Hallowed _ perm_map Hgrant (or_introl eq_refl)).
  - intros requested Hrequested.
    apply (Hallowed _ (perm_of_access requested) Hgrant).
    right.
    apply policy_access_permission_bridge.
    exact (rights_subset_allow _ _ _ Hbounded Hrequested).
Qed.

(** [view_flow_pairs] is the view's flow relation as a list. *)
Definition view_flow_pairs (checked : validated) : list (nat * nat) :=
  flat_map (fun grant1 => flat_map (fun grant2 =>
      if (rg_class grant1 =? class_memory) && (rg_class grant2 =? class_memory)
         && (rg_object grant1 =? rg_object grant2) &&
         mem perm_write (rg_perms grant1) && mem perm_read (rg_perms grant2) &&
         negb (subject_type checked (rg_subject grant1) =?
               subject_type checked (rg_subject grant2))
      then [(subject_type checked (rg_subject grant1),
             subject_type checked (rg_subject grant2))]
      else []) (rv_grants (v_view checked))) (rv_grants (v_view checked)).

Lemma view_flow_pairs_spec :
  forall checked type1 type2,
    In (type1, type2) (view_flow_pairs checked) <->
    view_flow checked type1 type2.
Proof.
  intros checked type1 type2.
  unfold view_flow_pairs, view_flow.
  rewrite in_flat_map.
  split.
  - intros [grant1 [Hin1 Hinner]].
    rewrite in_flat_map in Hinner.
    destruct Hinner as [grant2 [Hin2 Hpair]].
    match type of Hpair with
    | In _ (if ?check then _ else _) =>
        destruct check eqn:Hcheck; [| contradiction]
    end.
    destruct Hpair as [Hpair | []].
    inversion Hpair; subst type1 type2.
    repeat rewrite andb_true_iff in Hcheck.
    destruct Hcheck as
      [[[[[Hclass1 Hclass2] Hobject] Hwrite] Hread] Hdistinct].
    apply Nat.eqb_eq in Hclass1, Hclass2, Hobject.
    apply negb_true_iff, Nat.eqb_neq in Hdistinct.
    apply mem_in in Hwrite, Hread.
    split; [exact Hdistinct |].
    exists grant1, grant2.
    repeat split; assumption.
  - intros [Hdistinct [grant1 [grant2 [Hin1 [Hin2 [Hclass1 [Hclass2 [Hobject
      [Hwrite [Hread [Htype1 Htype2]]]]]]]]]]].
    exists grant1.
    split; [exact Hin1 |].
    rewrite in_flat_map.
    exists grant2.
    split; [exact Hin2 |].
    rewrite Hclass1, Hclass2, Hobject, Htype1, Htype2, !Nat.eqb_refl.
    apply Nat.eqb_neq in Hdistinct.
    rewrite Hdistinct.
    apply mem_in in Hwrite, Hread.
    rewrite Hwrite, Hread.
    simpl.
    left.
    reflexivity.
Qed.

Lemma pairs_incl_in :
  forall left right pair,
    pairs_incl left right = true -> In pair left -> In pair right.
Proof.
  intros left right pair Hincl Hin.
  unfold pairs_incl in Hincl.
  rewrite forallb_forall in Hincl.
  apply pair_mem_in.
  exact (Hincl pair Hin).
Qed.

Definition same_pairs (left right : list (nat * nat)) : bool :=
  pairs_incl left right && pairs_incl right left.

(**
 * [policy_projection_flows_equal] shows, by computation, that the view's
 * flows, the policy's flows, and the declared channels are one relation
 * for Model 0.2's projection of Instance 1, {(mgmt_t, prot_t)}. It is not
 * claimed in general: A8 does not require a view to realize every flow the
 * policy allows.
 *)
Theorem policy_projection_flows_equal :
  exists checked,
    validate_instance projection_m02 = Some checked /\
    forall type1 type2,
      (view_flow checked type1 type2 <-> policy_flow checked type1 type2) /\
      (policy_flow checked type1 type2 <->
         declared_channel checked type1 type2).
Proof.
  destruct (validate_instance projection_m02) as [checked |] eqn:Hvalid;
    [| vm_compute in Hvalid; discriminate].
  exists checked.
  split; [reflexivity |].
  assert (Hsame :
    same_pairs (view_flow_pairs checked) (flow_pairs checked) &&
    same_pairs (flow_pairs checked) (channel_pairs checked) = true).
  {
    assert (Hcomputed : projection_check (fun checked =>
        same_pairs (view_flow_pairs checked) (flow_pairs checked) &&
        same_pairs (flow_pairs checked) (channel_pairs checked)) = true)
      by (vm_compute; reflexivity).
    unfold projection_check in Hcomputed.
    rewrite Hvalid in Hcomputed.
    exact Hcomputed.
  }
  unfold same_pairs in Hsame.
  repeat rewrite andb_true_iff in Hsame.
  destruct Hsame as [[Hview_flow Hflow_view] [Hflow_channel Hchannel_flow]].
  unfold flow_pairs, channel_pairs in *.
  intros type1 type2.
  unfold policy_flow, declared_channel.
  rewrite <- view_flow_pairs_spec, <- !rule_pairs_spec.
  split; split; intros Hin.
  - exact (pairs_incl_in _ _ _ Hview_flow Hin).
  - exact (pairs_incl_in _ _ _ Hflow_view Hin).
  - exact (pairs_incl_in _ _ _ Hflow_channel Hin).
  - exact (pairs_incl_in _ _ _ Hchannel_flow Hin).
Qed.

(** [pairs_eqb] is executable equality of lists of type pairs. *)
Fixpoint pairs_eqb (left right : list (nat * nat)) : bool :=
  match left, right with
  | [], [] => true
  | pair1 :: rest1, pair2 :: rest2 =>
      pair_eqb pair1 pair2 && pairs_eqb rest1 rest2
  | _, _ => false
  end.

Lemma pairs_eqb_eq :
  forall left right, pairs_eqb left right = true -> left = right.
Proof.
  induction left as [| [a b] rest IH]; intros [| [c d] others] Hequal;
    simpl in Hequal; try discriminate; try reflexivity.
  apply andb_true_iff in Hequal as [Hpair Hrest].
  unfold pair_eqb in Hpair.
  simpl in Hpair.
  apply andb_true_iff in Hpair as [Hac Hbd].
  apply Nat.eqb_eq in Hac, Hbd.
  subst c d.
  rewrite (IH others Hrest).
  reflexivity.
Qed.

(**
 * [stated_results] is what security model v1 states for an instance:
 * every analysis passes; A5 with its report, each shared target type with
 * its single writer type ("static, not revocable, single writer"); and A7
 * vacuously, no domain holding a delegating permission.
 *)
Definition stated_results (instance : raw_instance) (shared : list (nat * nat))
    : Prop :=
  verdicts instance = all_pass /\
  exists checked,
    validate_instance instance = Some checked /\
    a5_report checked = shared /\ delegation_free checked.

Definition results_check (instance : raw_instance) (shared : list (nat * nat))
    : bool :=
  match validate_instance instance with
  | Some checked => pairs_eqb (a5_report checked) shared && a7 checked
  | None => false
  end.

Lemma stated_results_by_computation :
  forall instance shared,
    verdicts instance = all_pass ->
    results_check instance shared = true ->
    stated_results instance shared.
Proof.
  intros instance shared Hverdicts Hcheck.
  split; [exact Hverdicts |].
  unfold results_check in Hcheck.
  destruct (validate_instance instance) as [checked |]; [| discriminate].
  apply andb_true_iff in Hcheck as [Hreport Ha7].
  exists checked.
  split; [reflexivity |].
  split.
  - apply pairs_eqb_eq.
    exact Hreport.
  - apply policy_a7_vacuous.
    exact Ha7.
Qed.

(**
 * [policy_projection_results] is the projection's computed verdicts: every
 * analysis passes, A5 reporting shared_mp_t (5) with its single writer
 * mgmt_t (1), A7 vacuous; and the accepted canonical configuration seals
 * with the projection's policy and labeling.
 *)
Theorem policy_projection_results :
  stated_results projection_m02 [(5, 1)] /\
  seal_with_policy canonical_configuration (ri_policy projection_m02)
    (ri_labeling projection_m02) (ri_needs projection_m02) <> None.
Proof.
  split.
  - apply stated_results_by_computation; vm_compute; reflexivity.
  - vm_compute.
    discriminate.
Qed.
