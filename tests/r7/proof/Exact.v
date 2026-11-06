(* SPDX-License-Identifier: GPL-3.0-only *)
(* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> *)
(*
 * Exact linked-byte obligations for the R7 proof
 * (planning/single-hart-runtime-r7-plan.md, "Exact decoding").
 *
 * Maintained proof source. It consumes the generated, data-only ExactInput
 * module (produced twice and byte-compared, and independently cross-checked
 * against locked GNU objdump before Rocq ever sees it) and checks, for both
 * pinned toolchains:
 *
 *   - the two image records, their pinned build-path-independent allocated
 *     image identity, and the exact allocated-section table behind it;
 *   - the exact scoped symbol set, address, size, and unit count, and that
 *     every scoped symbol lies wholly inside the pinned .monitor.text row;
 *   - gapless unit framing that consumes each declared symbol size exactly;
 *   - complete, lossless decode of every scoped unit in the bounded model;
 *   - the expected cross-toolchain equalities and the expected differences,
 *     each classified and justified rather than merely counted;
 *   - control-flow targets recomputed here from the decoded words and
 *     compared with the extractor's own list; and
 *   - that no control-flow edge leaves the scoped symbol set except to a
 *     named C cut point.
 *
 * Explicit cut points, assumed and not proved here: the C mechanism bodies
 * (`be_r5_trap_dispatch`, `be_r5_runtime_terminal`), the direct ELF parser,
 * GNU objdump, the compiler and linker outside the extracted symbols,
 * OpenSBI, QEMU, and RISC-V hardware.
 *)

From Stdlib Require Import ZArith String List Bool.
Require Import ISA ExactInput.
Import ListNotations.
Open Scope Z_scope.

(* ------------------------------------------------------- scoped symbols *)

Definition scoped_names : list string :=
  ["be_r3_arch_reset_state";
   "be_r3_arch_install_management";
   "be_r3_arch_enter_management";
   "be_r5_arch_reset_state";
   "be_r5_trap_vector";
   "be_r5_arch_read_controls";
   "be_r5_arch_install_root";
   "be_r5_arch_reset_target";
   "be_r5_arch_restore_active";
   "be_r5_switch_tail";
   "be_r5_enter_guest_tail"]%string.

(* The three symbols assembled without `.option norvc`; they are the only
   scoped symbols permitted to contain 16-bit compressed units. *)
Definition privileged_names : list string :=
  ["be_r3_arch_reset_state";
   "be_r3_arch_install_management";
   "be_r3_arch_enter_management"]%string.

Definition empty_symbol : be_r7_symbol :=
  {| be_r7_symbol_name := "";
     be_r7_symbol_address := -1;
     be_r7_symbol_size := -1;
     be_r7_symbol_units := [];
     be_r7_symbol_targets := [] |}.

Definition sym (img : be_r7_image) (name : string) : be_r7_symbol :=
  match find (fun s => String.eqb (be_r7_symbol_name s) name) (be_r7_image_symbols img) with
  | Some s => s
  | None => empty_symbol
  end.

Definition unit_triple (u : be_r7_unit) : Z * Z * Z :=
  (be_r7_unit_offset u, be_r7_unit_length u, be_r7_unit_value u).

Definition symbol_triples (s : be_r7_symbol) : list (Z * Z * Z) :=
  map unit_triple (be_r7_symbol_units s).

Definition symbol_steps (s : be_r7_symbol) : list step := stream_of (symbol_triples s).

Definition steps (img : be_r7_image) (name : string) : list step :=
  symbol_steps (sym img name).

Definition base_of (img : be_r7_image) (name : string) : Z :=
  be_r7_symbol_address (sym img name).

Definition size_of (img : be_r7_image) (name : string) : Z :=
  be_r7_symbol_size (sym img name).

(* ------------------------------------------------------- image identity *)

(* Two identities are recorded per image and they are not interchangeable.

   The whole-ELF-file digest (be_r7_image_elf_sha256) is an observed *run*
   identity. The accepted R5 recipes compile with `-g3 -gdwarf-4` and no
   `-fdebug-prefix-map`, so DW_AT_comp_dir embeds the absolute path of the
   building worktree: two correct builds of identical sources at different
   paths agree on every loadable byte and differ only in non-allocated
   `.debug_*` bytes (and, for Clang, the `$d` mapping-symbol strings).
   Pinning that digest here would assert something false outside a single
   directory, so it is recorded and deliberately not pinned.

   The pinned identity is be_r7_image_alloc_sha256: the schema-tagged
   be-r7-alloc-image-v1 digest over the entry point and, in section-header
   order, every SHF_ALLOC section's name, type, flags, address, size, and
   contents -- exactly the bytes the loader maps and the hart executes, and
   nothing else. It was measured equal across two independent worktrees at
   different absolute paths, and it is pinned together with the full
   allocated-section table below, so this is strictly more exact about the
   executed image than the file digest it replaces. *)

Definition alloc_schema : string := "be-r7-alloc-image-v1".

Definition gcc_alloc_sha256 : string :=
  "46fdf832d26e3e8f3212a0fa78adc56bf45afcad11225656ab5b5d1dcab73d27".
Definition clang_alloc_sha256 : string :=
  "162a96462e722a622f6b362e10fa27517a08b16d7ae2f765070cfee580211994".

Definition image_identity_ok (img : be_r7_image) (toolchain digest : string)
  (sections file_bytes memory_bytes entry symbols : Z) : bool :=
  String.eqb (be_r7_image_toolchain img) toolchain
  && String.eqb (be_r7_image_alloc_schema img) alloc_schema
  && String.eqb (be_r7_image_alloc_sha256 img) digest
  && (be_r7_image_alloc_section_count img =? sections)
  && (Z.of_nat (length (be_r7_image_alloc_sections img)) =? sections)
  && (be_r7_image_alloc_file_bytes img =? file_bytes)
  && (be_r7_image_alloc_memory_bytes img =? memory_bytes)
  && (be_r7_image_elf_entry img =? entry)
  && (be_r7_image_symbol_count img =? symbols).

Definition entry_address : Z := 0x80200000.

Theorem gcc_image_identity_is_exact :
  image_identity_ok be_r7_gcc_image "gcc" gcc_alloc_sha256 16 46856 153352
                    entry_address 386 = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_image_identity_is_exact :
  image_identity_ok be_r7_clang_image "clang" clang_alloc_sha256 16 46096 152592
                    entry_address 521 = true.
Proof. vm_compute. reflexivity. Qed.

(* Difference claims. Both hold for any build path: the toolchains disagree
   on the loadable image itself, not merely on debug bytes. *)
Theorem the_two_images_are_distinct_files :
  String.eqb (be_r7_image_elf_sha256 be_r7_gcc_image)
             (be_r7_image_elf_sha256 be_r7_clang_image) = false.
Proof. vm_compute. reflexivity. Qed.

Theorem the_two_loadable_images_are_distinct :
  String.eqb (be_r7_image_alloc_sha256 be_r7_gcc_image)
             (be_r7_image_alloc_sha256 be_r7_clang_image) = false.
Proof. vm_compute. reflexivity. Qed.

Theorem both_images_share_the_frozen_entry_point :
  (be_r7_image_elf_entry be_r7_gcc_image =? entry_address)
  && (be_r7_image_elf_entry be_r7_clang_image =? entry_address) = true.
Proof. vm_compute. reflexivity. Qed.

(* --------------------------------------------------- allocated sections *)

Definition section_eqb (a b : be_r7_section) : bool :=
  String.eqb (be_r7_section_name a) (be_r7_section_name b)
  && (be_r7_section_type a =? be_r7_section_type b)
  && (be_r7_section_flags a =? be_r7_section_flags b)
  && (be_r7_section_addr a =? be_r7_section_addr b)
  && (be_r7_section_size a =? be_r7_section_size b)
  && String.eqb (be_r7_section_sha256 a) (be_r7_section_sha256 b).

Definition sections_eqb (a b : list be_r7_section) : bool :=
  (Nat.eqb (length a) (length b))
  && forallb (fun p => section_eqb (fst p) (snd p)) (combine a b).

Definition sht_nobits : Z := 8.
Definition shf_alloc : Z := 0x2.
Definition shf_exec : Z := 0x4.

Definition empty_section : be_r7_section :=
  {| be_r7_section_name := "";
     be_r7_section_type := -1;
     be_r7_section_flags := -1;
     be_r7_section_addr := -1;
     be_r7_section_size := -1;
     be_r7_section_sha256 := "" |}.

Definition section_of (img : be_r7_image) (name : string) : be_r7_section :=
  match find (fun s => String.eqb (be_r7_section_name s) name)
             (be_r7_image_alloc_sections img) with
  | Some s => s
  | None => empty_section
  end.

Definition gcc_alloc_sections : list be_r7_section :=
  [{| be_r7_section_name := ".monitor.text"; be_r7_section_type := 1; be_r7_section_flags := 0x6;
      be_r7_section_addr := 0x80200000; be_r7_section_size := 30224;
      be_r7_section_sha256 := "4f5d43803d58246ceefde126b091a84ee01b3dc9ed5da5a4a461441ff4d1564e" |};
   {| be_r7_section_name := ".monitor.input"; be_r7_section_type := 1; be_r7_section_flags := 0x2;
      be_r7_section_addr := 0x80208000; be_r7_section_size := 1160;
      be_r7_section_sha256 := "fbe427d9541e75e55cee6e4e67164fd0ad95d5eebc7da5cc0f3acb2e55071219" |};
   {| be_r7_section_name := ".monitor.rodata"; be_r7_section_type := 1; be_r7_section_flags := 0x2;
      be_r7_section_addr := 0x80208490; be_r7_section_size := 3208;
      be_r7_section_sha256 := "ad209889856cfc0a8253365dfaf917951c26371986ffbc034a55d733e3510c32" |};
   {| be_r7_section_name := ".monitor.data"; be_r7_section_type := 1; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80209120; be_r7_section_size := 4072;
      be_r7_section_sha256 := "a2ed99909fa8f0e83e41e0d4fa6a5cb6636931c8fa6790aee025794d38642a1f" |};
   {| be_r7_section_name := ".diagnostic"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8020f000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".gstage.root.management"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80214000; be_r7_section_size := 32768;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".gstage.root.protected"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8021c000; be_r7_section_size := 32768;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".stack.management"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80225000; be_r7_section_size := 8192;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".stack.protected"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80228000; be_r7_section_size := 8192;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".saved.management"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8022b000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".saved.protected"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8022c000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".private.management"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8022e000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".private.protected"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8022f000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".shared"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80230000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".guest.code.management"; be_r7_section_type := 1; be_r7_section_flags := 0x6;
      be_r7_section_addr := 0x80232000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "c61ea0146498624a8d66b0e2c8009dc92ef79f581949c3cfd8e1f3f4dde60f9d" |};
   {| be_r7_section_name := ".guest.code.protected"; be_r7_section_type := 1; be_r7_section_flags := 0x6;
      be_r7_section_addr := 0x80233000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "1bec687dabe929d676d5ed0d3cecb601c8932a034520fbe7f05ec8c47d67edd5" |}].

Definition clang_alloc_sections : list be_r7_section :=
  [{| be_r7_section_name := ".monitor.text"; be_r7_section_type := 1; be_r7_section_flags := 0x6;
      be_r7_section_addr := 0x80200000; be_r7_section_size := 30272;
      be_r7_section_sha256 := "0b3a5e06a7cd0ce145f9d054a7d94eb9b6e87dc6095186c71a82a27e903bb578" |};
   {| be_r7_section_name := ".monitor.input"; be_r7_section_type := 1; be_r7_section_flags := 0x2;
      be_r7_section_addr := 0x80208000; be_r7_section_size := 1160;
      be_r7_section_sha256 := "e24da06e5ad1da2d5a23aae8c46a212b868674628e20f2a1a4cba7876884403d" |};
   {| be_r7_section_name := ".monitor.rodata"; be_r7_section_type := 1; be_r7_section_flags := 0x32;
      be_r7_section_addr := 0x80208490; be_r7_section_size := 2400;
      be_r7_section_sha256 := "8d0abfe264f00bcb95ec4021920cb5bd5d45af0c877e05b76709d0aa8d6e0d55" |};
   {| be_r7_section_name := ".monitor.data"; be_r7_section_type := 1; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80208df0; be_r7_section_size := 4072;
      be_r7_section_sha256 := "a2ed99909fa8f0e83e41e0d4fa6a5cb6636931c8fa6790aee025794d38642a1f" |};
   {| be_r7_section_name := ".diagnostic"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8020f000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".gstage.root.management"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80214000; be_r7_section_size := 32768;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".gstage.root.protected"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8021c000; be_r7_section_size := 32768;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".stack.management"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80225000; be_r7_section_size := 8192;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".stack.protected"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80228000; be_r7_section_size := 8192;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".saved.management"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8022b000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".saved.protected"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8022c000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".private.management"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8022e000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".private.protected"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x8022f000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".shared"; be_r7_section_type := 8; be_r7_section_flags := 0x3;
      be_r7_section_addr := 0x80230000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "nobits" |};
   {| be_r7_section_name := ".guest.code.management"; be_r7_section_type := 1; be_r7_section_flags := 0x6;
      be_r7_section_addr := 0x80232000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "c61ea0146498624a8d66b0e2c8009dc92ef79f581949c3cfd8e1f3f4dde60f9d" |};
   {| be_r7_section_name := ".guest.code.protected"; be_r7_section_type := 1; be_r7_section_flags := 0x6;
      be_r7_section_addr := 0x80233000; be_r7_section_size := 4096;
      be_r7_section_sha256 := "788d045042a98214b781c98884b139356f450a0ec4eaba0961144bc94876b3b0" |}].

Theorem gcc_allocated_image_layout_is_exact :
  sections_eqb (be_r7_image_alloc_sections be_r7_gcc_image) gcc_alloc_sections = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_allocated_image_layout_is_exact :
  sections_eqb (be_r7_image_alloc_sections be_r7_clang_image) clang_alloc_sections = true.
Proof. vm_compute. reflexivity. Qed.

(* Every pinned row really carries SHF_ALLOC: the digest above covers the
   loaded image and cannot have been diluted with a non-allocated section. *)
Definition all_allocated (l : list be_r7_section) : bool :=
  forallb (fun s => Z.land (be_r7_section_flags s) shf_alloc =? shf_alloc) l.

Theorem both_pinned_tables_contain_only_allocated_sections :
  all_allocated gcc_alloc_sections && all_allocated clang_alloc_sections = true.
Proof. vm_compute. reflexivity. Qed.

(* The recorded file/memory totals are exactly the sums of the pinned rows,
   with SHT_NOBITS rows occupying memory but no file bytes. *)
Definition alloc_file_total (l : list be_r7_section) : Z :=
  fold_left (fun acc s =>
               if be_r7_section_type s =? sht_nobits then acc
               else acc + be_r7_section_size s) l 0.

Definition alloc_memory_total (l : list be_r7_section) : Z :=
  fold_left (fun acc s => acc + be_r7_section_size s) l 0.

Theorem gcc_allocated_totals_follow_the_pinned_rows :
  (alloc_file_total gcc_alloc_sections =? be_r7_image_alloc_file_bytes be_r7_gcc_image)
  && (alloc_memory_total gcc_alloc_sections =? be_r7_image_alloc_memory_bytes be_r7_gcc_image)
  = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_allocated_totals_follow_the_pinned_rows :
  (alloc_file_total clang_alloc_sections =? be_r7_image_alloc_file_bytes be_r7_clang_image)
  && (alloc_memory_total clang_alloc_sections =? be_r7_image_alloc_memory_bytes be_r7_clang_image)
  = true.
Proof. vm_compute. reflexivity. Qed.

(* Containment: every scoped symbol decoded below lies wholly inside the one
   pinned, read-only, executable .monitor.text row of its own image. *)
Definition monitor_text_ok (s : be_r7_section) : bool :=
  String.eqb (be_r7_section_name s) ".monitor.text"
  && (be_r7_section_type s =? 1)
  && (be_r7_section_flags s =? shf_alloc + shf_exec).

Definition within (s : be_r7_section) (addr size : Z) : bool :=
  (0 <? size) && (be_r7_section_addr s <=? addr)
  && (addr + size <=? be_r7_section_addr s + be_r7_section_size s).

Definition scoped_symbols_inside_monitor_text (img : be_r7_image) : bool :=
  let t := section_of img ".monitor.text" in
  monitor_text_ok t
  && forallb (fun s => within t (be_r7_symbol_address s) (be_r7_symbol_size s))
             (be_r7_image_symbols img).

Theorem gcc_scoped_symbols_live_inside_the_pinned_monitor_text :
  scoped_symbols_inside_monitor_text be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_scoped_symbols_live_inside_the_pinned_monitor_text :
  scoped_symbols_inside_monitor_text be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* ---------------------------------------------------------- symbol set *)

Definition eqb_string_list (a b : list string) : bool :=
  (Nat.eqb (length a) (length b))
  && forallb (fun p => String.eqb (fst p) (snd p)) (combine a b).

Definition image_names (img : be_r7_image) : list string :=
  map be_r7_symbol_name (be_r7_image_symbols img).

Theorem gcc_carries_exactly_the_scoped_symbols :
  eqb_string_list (image_names be_r7_gcc_image) scoped_names = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_carries_exactly_the_scoped_symbols :
  eqb_string_list (image_names be_r7_clang_image) scoped_names = true.
Proof. vm_compute. reflexivity. Qed.

(* --------------------------------------------------------- exact layout *)

Record layout_row : Set := mk_row {
  row_name : string;
  row_address : Z;
  row_size : Z;
  row_units : Z
}.

Definition row_eqb (a b : layout_row) : bool :=
  String.eqb (row_name a) (row_name b)
  && (row_address a =? row_address b)
  && (row_size a =? row_size b)
  && (row_units a =? row_units b).

Definition rows_eqb (a b : list layout_row) : bool :=
  (Nat.eqb (length a) (length b)) && forallb (fun p => row_eqb (fst p) (snd p)) (combine a b).

Definition layout_of (img : be_r7_image) : list layout_row :=
  map (fun s => mk_row (be_r7_symbol_name s) (be_r7_symbol_address s)
                       (be_r7_symbol_size s) (Z.of_nat (length (be_r7_symbol_units s))))
      (be_r7_image_symbols img).

Definition gcc_layout : list layout_row :=
  [mk_row "be_r3_arch_reset_state" 0x80206a90 426 107;
   mk_row "be_r3_arch_install_management" 0x80206c40 14 4;
   mk_row "be_r3_arch_enter_management" 0x80206c50 86 38;
   mk_row "be_r5_arch_reset_state" 0x80206cf0 428 107;
   mk_row "be_r5_trap_vector" 0x80206ea0 360 90;
   mk_row "be_r5_arch_read_controls" 0x80207010 36 9;
   mk_row "be_r5_arch_install_root" 0x80207040 44 11;
   mk_row "be_r5_arch_reset_target" 0x80207070 516 129;
   mk_row "be_r5_arch_restore_active" 0x80207280 512 128;
   mk_row "be_r5_switch_tail" 0x80207480 212 53;
   mk_row "be_r5_enter_guest_tail" 0x80207560 136 34].

Definition clang_layout : list layout_row :=
  [mk_row "be_r3_arch_reset_state" 0x80206ac0 426 107;
   mk_row "be_r3_arch_install_management" 0x80206c70 14 4;
   mk_row "be_r3_arch_enter_management" 0x80206c80 86 38;
   mk_row "be_r5_arch_reset_state" 0x80206d20 428 107;
   mk_row "be_r5_trap_vector" 0x80206ed0 360 90;
   mk_row "be_r5_arch_read_controls" 0x80207040 36 9;
   mk_row "be_r5_arch_install_root" 0x80207070 44 11;
   mk_row "be_r5_arch_reset_target" 0x802070a0 516 129;
   mk_row "be_r5_arch_restore_active" 0x802072b0 512 128;
   mk_row "be_r5_switch_tail" 0x802074b0 212 53;
   mk_row "be_r5_enter_guest_tail" 0x80207590 136 34].

Theorem gcc_layout_is_exact : rows_eqb (layout_of be_r7_gcc_image) gcc_layout = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_layout_is_exact : rows_eqb (layout_of be_r7_clang_image) clang_layout = true.
Proof. vm_compute. reflexivity. Qed.

(* Both images place the eleven scoped symbols with identical sizes and unit
   counts; only their absolute addresses differ. *)
Definition sizes_and_counts (l : list layout_row) : list (Z * Z) :=
  map (fun r => (row_size r, row_units r)) l.

Definition eqb_pair_list (a b : list (Z * Z)) : bool :=
  (Nat.eqb (length a) (length b))
  && forallb (fun p => (fst (fst p) =? fst (snd p)) && (snd (fst p) =? snd (snd p)))
             (combine a b).

Theorem both_images_agree_on_sizes_and_unit_counts :
  eqb_pair_list (sizes_and_counts (layout_of be_r7_gcc_image))
                (sizes_and_counts (layout_of be_r7_clang_image)) = true.
Proof. vm_compute. reflexivity. Qed.

(* -------------------------------------------------------- unit framing *)

(* Units must tile the declared symbol size exactly: first offset zero, each
   following offset the previous offset plus its own length, only 2- or
   4-byte widths, and the final offset plus length equal to the size. *)
Fixpoint framing_walk (next : Z) (units : list be_r7_unit) : Z :=
  match units with
  | [] => next
  | u :: rest =>
      if (be_r7_unit_offset u =? next)
         && ((be_r7_unit_length u =? 2) || (be_r7_unit_length u =? 4))
      then framing_walk (next + be_r7_unit_length u) rest
      else -1
  end.

Definition symbol_framing_ok (s : be_r7_symbol) : bool :=
  framing_walk 0 (be_r7_symbol_units s) =? be_r7_symbol_size s.

Definition image_framing_ok (img : be_r7_image) : bool :=
  forallb symbol_framing_ok (be_r7_image_symbols img).

Theorem gcc_units_tile_every_symbol_exactly : image_framing_ok be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_units_tile_every_symbol_exactly : image_framing_ok be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------------- complete decode *)

Definition symbol_decodes (s : be_r7_symbol) : bool :=
  match decode_stream (symbol_triples s) with Some _ => true | None => false end.

Definition symbol_units_exact (s : be_r7_symbol) : bool :=
  forallb triple_exact (symbol_triples s).

Definition image_decodes (img : be_r7_image) : bool :=
  forallb symbol_decodes (be_r7_image_symbols img).

Definition image_units_exact (img : be_r7_image) : bool :=
  forallb symbol_units_exact (be_r7_image_symbols img).

Theorem gcc_every_scoped_unit_decodes : image_decodes be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_every_scoped_unit_decodes : image_decodes be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem gcc_every_scoped_unit_re_encodes_exactly : image_units_exact be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_every_scoped_unit_re_encodes_exactly : image_units_exact be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------------------- cardinality *)

Definition image_unit_count (img : be_r7_image) : nat :=
  fold_right (fun s acc => (length (be_r7_symbol_units s) + acc)%nat) 0%nat
             (be_r7_image_symbols img).

Definition image_width_count (w : Z) (img : be_r7_image) : nat :=
  fold_right (fun s acc =>
                (length (filter (fun u => Z.eqb (be_r7_unit_length u) w) (be_r7_symbol_units s)) + acc)%nat)
             0%nat (be_r7_image_symbols img).

Definition image_target_count (img : be_r7_image) : nat :=
  fold_right (fun s acc => (length (be_r7_symbol_targets s) + acc)%nat) 0%nat
             (be_r7_image_symbols img).

Theorem gcc_unit_cardinality : image_unit_count be_r7_gcc_image = 710%nat.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_unit_cardinality : image_unit_count be_r7_clang_image = 710%nat.
Proof. vm_compute. reflexivity. Qed.

Theorem total_scoped_unit_cardinality :
  (image_unit_count be_r7_gcc_image + image_unit_count be_r7_clang_image)%nat = 1420%nat.
Proof. vm_compute. reflexivity. Qed.

Theorem scoped_width_split :
  image_width_count 4 be_r7_gcc_image = 675%nat /\
  image_width_count 2 be_r7_gcc_image = 35%nat /\
  image_width_count 4 be_r7_clang_image = 675%nat /\
  image_width_count 2 be_r7_clang_image = 35%nat.
Proof.
  refine (conj _ (conj _ (conj _ _))); vm_compute; reflexivity.
Qed.

Theorem total_scoped_target_cardinality :
  (image_target_count be_r7_gcc_image + image_target_count be_r7_clang_image)%nat = 144%nat.
Proof. vm_compute. reflexivity. Qed.

(* Compressed units exist only in the three symbols assembled without
   `.option norvc`; the eight R5 trap/switch symbols are pure 32-bit. *)
Definition compressed_confined (img : be_r7_image) : bool :=
  forallb (fun s =>
             if existsb (fun n => String.eqb n (be_r7_symbol_name s)) privileged_names
             then true
             else forallb (fun u => be_r7_unit_length u =? 4) (be_r7_symbol_units s))
          (be_r7_image_symbols img).

Theorem gcc_compressed_units_are_confined : compressed_confined be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_compressed_units_are_confined : compressed_confined be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------- cross-toolchain shape *)

Definition units_eqb (a b : list be_r7_unit) : bool :=
  (Nat.eqb (length a) (length b))
  && forallb (fun p => (be_r7_unit_offset (fst p) =? be_r7_unit_offset (snd p))
                       && (be_r7_unit_length (fst p) =? be_r7_unit_length (snd p))
                       && (be_r7_unit_value (fst p) =? be_r7_unit_value (snd p)))
             (combine a b).

Definition identical_names : list string :=
  ["be_r3_arch_install_management";
   "be_r3_arch_enter_management";
   "be_r5_arch_read_controls";
   "be_r5_arch_install_root";
   "be_r5_enter_guest_tail"]%string.

Definition differing_names : list string :=
  ["be_r3_arch_reset_state";
   "be_r5_arch_reset_state";
   "be_r5_trap_vector";
   "be_r5_arch_reset_target";
   "be_r5_arch_restore_active";
   "be_r5_switch_tail"]%string.

Theorem the_two_partitions_cover_the_scoped_set :
  eqb_string_list (identical_names ++ differing_names)
                  ["be_r3_arch_install_management"; "be_r3_arch_enter_management";
                   "be_r5_arch_read_controls"; "be_r5_arch_install_root";
                   "be_r5_enter_guest_tail"; "be_r3_arch_reset_state";
                   "be_r5_arch_reset_state"; "be_r5_trap_vector";
                   "be_r5_arch_reset_target"; "be_r5_arch_restore_active";
                   "be_r5_switch_tail"]%string = true
  /\ Nat.eqb (length (identical_names ++ differing_names)) (length scoped_names) = true.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

Definition symbol_bytes_equal (name : string) : bool :=
  units_eqb (be_r7_symbol_units (sym be_r7_gcc_image name))
            (be_r7_symbol_units (sym be_r7_clang_image name)).

Theorem toolchain_identical_symbols_are_byte_identical :
  forallb symbol_bytes_equal identical_names = true.
Proof. vm_compute. reflexivity. Qed.

Theorem toolchain_differing_symbols_really_differ :
  forallb (fun n => negb (symbol_bytes_equal n)) differing_names = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------ classified expected differences *)

Definition prev_is_auipc_for (p : option step) (rs : Z) : bool :=
  match p with
  | Some s => match st_instr s with Iauipc rd _ => rd =? rs | _ => false end
  | None => false
  end.

(* An ADDIW/ADDI selection difference is architecturally immaterial only when
   the pair completes a LUI-based constant whose 32-bit sum does not overflow,
   so both forms leave the same sign-extended 64-bit value. *)
Definition lui_pair_in_range (p : option step) (rd imm : Z) : bool :=
  match p with
  | Some s =>
      match st_instr s with
      | Ilui d u =>
          let v := sext (Z.shiftl u 12) 32 + imm in
          (d =? rd) && (-2147483648 <=? v) && (v <? 2147483648)
      | _ => false
      end
  | None => false
  end.

Inductive diff_class : Set := DiffAddiwSelection | DiffRelocImm | DiffRelocHigh | DiffCallImm.

Definition classify (pa pb : option step) (x y : step) : option diff_class :=
  match st_instr x, st_instr y with
  | Iopimm OpAddiw rd1 rs1 i1, Iopimm OpAddi rd2 rs2 i2 =>
      if (rd1 =? rd2) && (rs1 =? rs2) && (i1 =? i2) && (rd1 =? rs1)
         && lui_pair_in_range pa rd1 i1 && lui_pair_in_range pb rd2 i2
      then Some DiffAddiwSelection else None
  | Iopimm OpAddi rd1 rs1 _, Iopimm OpAddi rd2 rs2 _ =>
      if (rd1 =? rd2) && (rs1 =? rs2) && (rd1 =? rs1)
         && prev_is_auipc_for pa rs1 && prev_is_auipc_for pb rs2
      then Some DiffRelocImm else None
  | Iauipc rd1 _, Iauipc rd2 _ => if rd1 =? rd2 then Some DiffRelocHigh else None
  | Ijalr rd1 rs1 _, Ijalr rd2 rs2 _ =>
      if (rd1 =? rd2) && (rs1 =? rs2) && prev_is_auipc_for pa rs1 && prev_is_auipc_for pb rs2
      then Some DiffCallImm else None
  | _, _ => None
  end.

Fixpoint diff_walk (pa pb : option step) (a b : list step) : list (Z * option diff_class) :=
  match a, b with
  | x :: xs, y :: ys =>
      let rest := diff_walk (Some x) (Some y) xs ys in
      if (st_value x =? st_value y) && (st_len x =? st_len y)
      then rest
      else (st_offset x, classify pa pb x y) :: rest
  | _, _ => []
  end.

Definition symbol_diffs (name : string) : list (Z * option diff_class) :=
  diff_walk None None (steps be_r7_gcc_image name) (steps be_r7_clang_image name).

Definition diff_count (name : string) : nat := length (symbol_diffs name).

Definition diffs_all_classified (name : string) : bool :=
  forallb (fun d => match snd d with Some _ => true | None => false end) (symbol_diffs name).

Theorem every_cross_toolchain_difference_is_classified :
  forallb diffs_all_classified scoped_names = true.
Proof. vm_compute. reflexivity. Qed.

Definition diff_counts : list nat := map diff_count scoped_names.

Theorem cross_toolchain_difference_counts_are_exact :
  diff_counts = [2; 0; 0; 2; 9; 0; 0; 10; 12; 3; 0]%nat.
Proof. vm_compute. reflexivity. Qed.

Definition class_count (c : diff_class) : nat :=
  length (filter (fun d => match snd d with
                           | Some k => match k, c with
                                       | DiffAddiwSelection, DiffAddiwSelection => true
                                       | DiffRelocImm, DiffRelocImm => true
                                       | DiffRelocHigh, DiffRelocHigh => true
                                       | DiffCallImm, DiffCallImm => true
                                       | _, _ => false
                                       end
                           | None => false
                           end)
                 (concat (map symbol_diffs scoped_names))).

Theorem cross_toolchain_difference_classes_are_exact :
  class_count DiffAddiwSelection = 17%nat /\
  class_count DiffRelocImm = 9%nat /\
  class_count DiffRelocHigh = 3%nat /\
  class_count DiffCallImm = 9%nat.
Proof. refine (conj _ (conj _ (conj _ _))); vm_compute; reflexivity. Qed.

(* ------------------------------------------- address materialization pairs *)

Definition addr_stack_management_end : Z := 0x80227000.
Definition addr_stack_protected_end : Z := 0x8022a000.
Definition addr_saved_management_start : Z := 0x8022b000.
Definition addr_saved_protected_start : Z := 0x8022c000.

Fixpoint la_walk (base : Z) (prev : option step) (l : list step) : list (Z * Z) :=
  match l with
  | [] => []
  | s :: rest =>
      let here :=
        match st_instr s, prev with
        | Iopimm OpAddi rd rs1 imm, Some p =>
            match st_instr p with
            | Iauipc prd u =>
                if (prd =? rs1) && (rd =? rs1)
                then [(st_offset s, step_pc base p + sext (Z.shiftl u 12) 32 + imm)]
                else []
            | _ => []
            end
        | _, _ => []
        end in
      here ++ la_walk base (Some s) rest
  end.

Definition symbol_la (img : be_r7_image) (name : string) : list (Z * Z) :=
  la_walk (base_of img name) None (steps img name).

Definition image_la (img : be_r7_image) : list Z :=
  map snd (concat (map (symbol_la img) scoped_names)).

(* Materialized addresses are either the frozen monitor-owned data extents or
   this image's own trap vector; nothing else is formed from an immediate. *)
Definition la_expected (img : be_r7_image) (a : Z) : bool :=
  (a =? addr_stack_management_end) || (a =? addr_stack_protected_end)
  || (a =? addr_saved_management_start) || (a =? addr_saved_protected_start)
  || (a =? base_of img "be_r5_trap_vector").

Theorem gcc_materialized_addresses_are_bound :
  forallb (la_expected be_r7_gcc_image) (image_la be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_materialized_addresses_are_bound :
  forallb (la_expected be_r7_clang_image) (image_la be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* Once each image's own trap-vector address is normalized away, the two
   toolchains materialize exactly the same addresses in the same order: the
   differing immediates are compensating relocations, not different behavior. *)
Definition normalize_la (img : be_r7_image) (a : Z) : Z :=
  if a =? base_of img "be_r5_trap_vector" then 0 else a.

Theorem materialized_addresses_agree_across_toolchains :
  eqb_list_Z (map (normalize_la be_r7_gcc_image) (image_la be_r7_gcc_image))
             (map (normalize_la be_r7_clang_image) (image_la be_r7_clang_image)) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem materialized_address_cardinality :
  length (image_la be_r7_gcc_image) = 14%nat /\
  length (image_la be_r7_clang_image) = 14%nat.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

(* -------------------------------------------------- control-flow targets *)

Definition kind_name (k : target_kind) : string :=
  match k with TkJ => "J-type" | TkB => "B-type" | TkAuipc => "auipc-pair" end.

Definition computed_targets (img : be_r7_image) (name : string) : list (Z * target_kind * Z) :=
  targets_of (base_of img name) (steps img name).

Definition generated_targets (img : be_r7_image) (name : string) : list be_r7_target :=
  be_r7_symbol_targets (sym img name).

Definition target_agrees (p : (Z * target_kind * Z) * be_r7_target) : bool :=
  let c := fst p in let e := snd p in
  (target_offset c =? be_r7_target_offset e)
  && String.eqb (kind_name (target_kind_of c)) (be_r7_target_format e)
  && (target_address c =? be_r7_target_address e).

Definition targets_agree (img : be_r7_image) (name : string) : bool :=
  let c := computed_targets img name in
  let e := generated_targets img name in
  (Nat.eqb (length c) (length e)) && forallb target_agrees (combine c e).

(* The extractor is not trusted for meaning: every target it reported is
   recomputed here from the decoded words and must agree exactly. *)
Theorem gcc_targets_are_independently_recomputed :
  forallb (targets_agree be_r7_gcc_image) scoped_names = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_targets_are_independently_recomputed :
  forallb (targets_agree be_r7_clang_image) scoped_names = true.
Proof. vm_compute. reflexivity. Qed.

Definition target_counts (img : be_r7_image) : list nat :=
  map (fun n => length (computed_targets img n)) scoped_names.

Theorem target_counts_are_exact :
  target_counts be_r7_gcc_image = [0; 0; 0; 0; 8; 0; 0; 25; 27; 12; 0]%nat /\
  target_counts be_r7_clang_image = [0; 0; 0; 0; 8; 0; 0; 25; 27; 12; 0]%nat.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

(* The two named C cut points. Their identity comes from the independent
   objdump cross-check, a trusted boundary; their bodies are not proved. *)
Definition gcc_cut_dispatch : Z := 0x80205d2a.
Definition gcc_cut_terminal : Z := 0x80205b1a.
Definition clang_cut_dispatch : Z := 0x80205f38.
Definition clang_cut_terminal : Z := 0x80205e98.

Definition cut_points (img : be_r7_image) : list Z :=
  if String.eqb (be_r7_image_toolchain img) "gcc"
  then [gcc_cut_dispatch; gcc_cut_terminal]
  else [clang_cut_dispatch; clang_cut_terminal].

Definition inside_scope (img : be_r7_image) (a : Z) : bool :=
  existsb (fun n => in_range (base_of img n) (size_of img n) a) scoped_names.

Definition target_is_bound (img : be_r7_image) (t : Z * target_kind * Z) : bool :=
  inside_scope img (target_address t) || mem_Z (target_address t) (cut_points img).

Definition image_targets (img : be_r7_image) : list (Z * target_kind * Z) :=
  concat (map (computed_targets img) scoped_names).

Theorem gcc_no_control_edge_leaves_the_scope :
  forallb (target_is_bound be_r7_gcc_image) (image_targets be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_no_control_edge_leaves_the_scope :
  forallb (target_is_bound be_r7_clang_image) (image_targets be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

Definition external_targets (img : be_r7_image) : list Z :=
  map target_address (filter (fun t => negb (inside_scope img (target_address t)))
                             (image_targets img)).

Theorem gcc_external_edges_are_only_the_named_cut_points :
  forallb (fun a => mem_Z a (cut_points be_r7_gcc_image)) (external_targets be_r7_gcc_image) = true
  /\ length (external_targets be_r7_gcc_image) = 9%nat.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

Theorem clang_external_edges_are_only_the_named_cut_points :
  forallb (fun a => mem_Z a (cut_points be_r7_clang_image)) (external_targets be_r7_clang_image) = true
  /\ length (external_targets be_r7_clang_image) = 9%nat.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

(* Every control transfer is accounted for: a resolved branch, a resolved
   direct jump, a resolved AUIPC pair, an architectural return, or the entry
   `SRET`. No unresolved register-indirect transfer exists in the scope. *)
Fixpoint transfers_accounted (prev : option step) (l : list step) : bool :=
  match l with
  | [] => true
  | s :: rest =>
      let ok :=
        match st_instr s with
        | Ijalr rd rs1 imm =>
            ((rd =? 0) && (rs1 =? reg_ra) && (imm =? 0)) || prev_is_auipc_for prev rs1
        | Icjr rs1 => rs1 =? reg_ra
        | _ => true
        end in
      ok && transfers_accounted (Some s) rest
  end.

Definition image_transfers_accounted (img : be_r7_image) : bool :=
  forallb (fun n => transfers_accounted None (steps img n)) scoped_names.

Theorem gcc_every_indirect_transfer_is_a_return_or_resolved_pair :
  image_transfers_accounted be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_every_indirect_transfer_is_a_return_or_resolved_pair :
  image_transfers_accounted be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* --------------------------------------------------------- claim bundle *)

Definition exact_claims : Prop :=
  image_identity_ok be_r7_gcc_image "gcc" gcc_alloc_sha256 16 46856 153352
                    entry_address 386 = true /\
  image_identity_ok be_r7_clang_image "clang" clang_alloc_sha256 16 46096 152592
                    entry_address 521 = true /\
  sections_eqb (be_r7_image_alloc_sections be_r7_gcc_image) gcc_alloc_sections = true /\
  sections_eqb (be_r7_image_alloc_sections be_r7_clang_image) clang_alloc_sections = true /\
  String.eqb (be_r7_image_alloc_sha256 be_r7_gcc_image)
             (be_r7_image_alloc_sha256 be_r7_clang_image) = false /\
  scoped_symbols_inside_monitor_text be_r7_gcc_image = true /\
  scoped_symbols_inside_monitor_text be_r7_clang_image = true /\
  eqb_string_list (image_names be_r7_gcc_image) scoped_names = true /\
  eqb_string_list (image_names be_r7_clang_image) scoped_names = true /\
  rows_eqb (layout_of be_r7_gcc_image) gcc_layout = true /\
  rows_eqb (layout_of be_r7_clang_image) clang_layout = true /\
  image_framing_ok be_r7_gcc_image = true /\
  image_framing_ok be_r7_clang_image = true /\
  image_decodes be_r7_gcc_image = true /\
  image_decodes be_r7_clang_image = true /\
  image_units_exact be_r7_gcc_image = true /\
  image_units_exact be_r7_clang_image = true /\
  (image_unit_count be_r7_gcc_image + image_unit_count be_r7_clang_image)%nat = 1420%nat /\
  compressed_confined be_r7_gcc_image = true /\
  compressed_confined be_r7_clang_image = true /\
  forallb symbol_bytes_equal identical_names = true /\
  forallb diffs_all_classified scoped_names = true /\
  diff_counts = [2; 0; 0; 2; 9; 0; 0; 10; 12; 3; 0]%nat /\
  forallb (la_expected be_r7_gcc_image) (image_la be_r7_gcc_image) = true /\
  forallb (la_expected be_r7_clang_image) (image_la be_r7_clang_image) = true /\
  eqb_list_Z (map (normalize_la be_r7_gcc_image) (image_la be_r7_gcc_image))
             (map (normalize_la be_r7_clang_image) (image_la be_r7_clang_image)) = true /\
  forallb (targets_agree be_r7_gcc_image) scoped_names = true /\
  forallb (targets_agree be_r7_clang_image) scoped_names = true /\
  forallb (target_is_bound be_r7_gcc_image) (image_targets be_r7_gcc_image) = true /\
  forallb (target_is_bound be_r7_clang_image) (image_targets be_r7_clang_image) = true /\
  image_transfers_accounted be_r7_gcc_image = true /\
  image_transfers_accounted be_r7_clang_image = true.

Theorem exact_claims_hold : exact_claims.
Proof.
  unfold exact_claims.
  refine (conj gcc_image_identity_is_exact
          (conj clang_image_identity_is_exact
           (conj gcc_allocated_image_layout_is_exact
           (conj clang_allocated_image_layout_is_exact
           (conj the_two_loadable_images_are_distinct
           (conj gcc_scoped_symbols_live_inside_the_pinned_monitor_text
           (conj clang_scoped_symbols_live_inside_the_pinned_monitor_text
           (conj gcc_carries_exactly_the_scoped_symbols
            (conj clang_carries_exactly_the_scoped_symbols
             (conj gcc_layout_is_exact
              (conj clang_layout_is_exact
               (conj gcc_units_tile_every_symbol_exactly
                (conj clang_units_tile_every_symbol_exactly
                 (conj gcc_every_scoped_unit_decodes
                  (conj clang_every_scoped_unit_decodes
                   (conj gcc_every_scoped_unit_re_encodes_exactly
                    (conj clang_every_scoped_unit_re_encodes_exactly
                     (conj total_scoped_unit_cardinality
                      (conj gcc_compressed_units_are_confined
                       (conj clang_compressed_units_are_confined
                        (conj toolchain_identical_symbols_are_byte_identical
                         (conj every_cross_toolchain_difference_is_classified
                          (conj cross_toolchain_difference_counts_are_exact
                           (conj gcc_materialized_addresses_are_bound
                            (conj clang_materialized_addresses_are_bound
                             (conj materialized_addresses_agree_across_toolchains
                              (conj gcc_targets_are_independently_recomputed
                               (conj clang_targets_are_independently_recomputed
                                (conj gcc_no_control_edge_leaves_the_scope
                                 (conj clang_no_control_edge_leaves_the_scope
                                  (conj gcc_every_indirect_transfer_is_a_return_or_resolved_pair
                                        clang_every_indirect_transfer_is_a_return_or_resolved_pair))))))))))))))))))))))))))))))).
Qed.
