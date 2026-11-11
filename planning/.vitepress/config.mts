// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>

import path from 'node:path'
import { defineConfig } from 'vitepress'
import type { SiteConfig } from 'vitepress'

const base = process.env.DOCS_BASE ?? './'
const outDir = process.env.DOCS_OUT_DIR ?? '../docs/html'
// A relative link to a Markdown page: its path, then any ?query or #fragment.
const relativeMarkdownLink =
  /^(?![a-z][a-z0-9+.-]*:)([^/?#][^?#]*\.md)([?#].*)?$/i

export default defineConfig({
  lang: 'en-US',
  title: 'Beryllium documentation',
  titleTemplate: ':title | Beryllium',
  description:
    'Planning, architecture, research, and assurance documentation for Beryllium.',
  base,
  rewrites: {
    'README.md': 'index.md'
  },
  outDir,
  cacheDir: '../node_modules/.vitepress-cache',
  cleanUrls: false,
  vite: {
    build: {
      // Local search is already lazy-loaded as one 754 KB generated corpus.
      chunkSizeWarningLimit: 800
    }
  },
  transformHtml(html) {
    const portableHtml =
      base === './'
        ? html.replaceAll('href="./"', 'href="./index.html"')
        : html

    return portableHtml.replaceAll(
      'src="/diagrams/',
      `src="${base}diagrams/`
    )
  },
  markdown: {
    lineNumbers: true,
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    },
    // VitePress generates a rewritten page at its new path (README.md as
    // index.md) but leaves the relative links that name it: a page's
    // [...](README.md) would render as ./README.html, which the site never
    // has. Each relative link whose target page is rewritten points instead
    // at the page generated for it, as an explicit .html file. The map is
    // the one VitePress resolved from `rewrites` above, in the site config
    // it sets before rendering any page (VITEPRESS_CONFIG, which its own
    // content loader reads). The Markdown keeps README.md, which works
    // where the Markdown is read as it is.
    config(md) {
      md.core.ruler.push('rewritten_link_targets', (state) => {
        const site = (globalThis as { VITEPRESS_CONFIG?: SiteConfig })
          .VITEPRESS_CONFIG
        const page = state.env?.realPath ?? state.env?.path
        if (!site || typeof page !== 'string') {
          return
        }
        const source = path
          .relative(site.srcDir, page)
          .split(path.sep)
          .join('/')
        const generated = site.rewrites.map[source] ?? source
        const tokens = state.tokens.flatMap((block) => block.children ?? [])
        for (const token of tokens) {
          const link =
            token.type === 'link_open'
              ? relativeMarkdownLink.exec(token.attrGet('href') ?? '')
              : null
          const target =
            link &&
            site.rewrites.map[
              path.posix.join(path.posix.dirname(source), decodeURI(link[1]))
            ]
          if (target) {
            const href = path.posix
              .relative(path.posix.dirname(generated), target)
              .replace(/\.md$/, '.html')
            token.attrSet(
              'href',
              `${href.startsWith('../') ? '' : './'}${href}${link[2] ?? ''}`
            )
          }
        }
      })
    }
  },
  themeConfig: {
    siteTitle: 'Beryllium wiki',
    nav: [
      { text: 'Overview', link: '/' },
      { text: 'Beryllium roadmap', link: '/roadmap' },
      { text: 'Orientation', link: '/project-orientation' },
      { text: 'Glossary', link: '/glossary' },
      { text: 'Handoff', link: '/HANDOFF' },
      {
        text: 'Source-first review',
        link: '/source-first-documentation-policy-review-summary'
      },
      {
        text: 'Current',
        items: [
          { text: 'Post-pathfinder decision', link: '/pathfinder-comparison' },
          { text: 'Architecture Model 0.1', link: '/architecture-model-0.1' },
          {
            text: 'Model 0.1 evidence',
            link: '/architecture-model-0.1-evidence'
          },
          {
            text: 'Architecture Model 0.2',
            link: '/architecture-model-0.2'
          },
          {
            text: 'Model 0.2 evidence',
            link: '/architecture-model-0.2-evidence'
          },
          {
            text: 'Bounded single-hart runtime plan',
            link: '/single-hart-runtime-plan'
          },
          {
            text: 'Single-hart runtime R0 freeze',
            link: '/single-hart-runtime-r0-freeze'
          },
          {
            text: 'Single-hart runtime R1 evidence',
            link: '/single-hart-runtime-r1-evidence'
          },
          {
            text: 'R1 human review summary',
            link: '/single-hart-runtime-r1-review-summary'
          },
          {
            text: 'R2 bounded plan (accepted)',
            link: '/single-hart-runtime-r2-plan'
          },
          {
            text: 'R2 plan review summary',
            link: '/single-hart-runtime-r2-plan-review-summary'
          },
          {
            text: 'R2 Sv39x4 backend evidence (accepted)',
            link: '/single-hart-runtime-r2-evidence'
          },
          {
            text: 'R2 implementation review (accepted)',
            link: '/single-hart-runtime-r2-review-summary'
          },
          {
            text: 'R3 evidence (accepted)',
            link: '/single-hart-runtime-r3-evidence'
          },
          {
            text: 'R3 review and acceptance record',
            link: '/single-hart-runtime-r3-review-summary'
          },
          {
            text: 'R4 review and acceptance packet',
            link: '/single-hart-runtime-r4-review-summary'
          },
          {
            text: 'R5 bounded plan (accepted)',
            link: '/single-hart-runtime-r5-plan'
          },
          {
            text: 'R5 plan review and acceptance record',
            link: '/single-hart-runtime-r5-plan-review-summary'
          },
          {
            text: 'R5 checked-switch evidence (accepted target)',
            link: '/single-hart-runtime-r5-evidence'
          },
          {
            text: 'R5 review and acceptance record',
            link: '/single-hart-runtime-r5-review-summary'
          },
          {
            text: 'R6 bounded plan (accepted, incl. revisions R6-A and R6-B)',
            link: '/single-hart-runtime-r6-plan'
          },
          {
            text: 'R6 plan review and acceptance record',
            link: '/single-hart-runtime-r6-plan-review-summary'
          },
          {
            text: 'R6 plan revision review and acceptance record',
            link: '/single-hart-runtime-r6-plan-revision-review-summary'
          },
          {
            text: 'R6-B plan revision review and acceptance record',
            link: '/single-hart-runtime-r6-plan-r6b-review-summary'
          },
          {
            text: 'R6 adversarial-image evidence (accepted target)',
            link: '/single-hart-runtime-r6-evidence'
          },
          {
            text: 'R6 review and acceptance record',
            link: '/single-hart-runtime-r6-review-summary'
          },
          {
            text: 'R7 proof and evidence plan (accepted, incl. revision R7-A)',
            link: '/single-hart-runtime-r7-plan'
          },
          {
            text: 'R7 plan review and acceptance record',
            link: '/single-hart-runtime-r7-plan-review-summary'
          },
          {
            text: 'R7-A plan revision review and acceptance record',
            link: '/single-hart-runtime-r7-plan-r7a-review-summary'
          },
          {
            text: 'R7 bounded exact-proof and evidence record',
            link: '/single-hart-runtime-r7-evidence'
          },
          {
            text: 'R7 review and acceptance record',
            link: '/single-hart-runtime-r7-review-summary'
          },
          {
            text: 'R8 K3 core-validation plan (accepted; dropped 2026-10-08)',
            link: '/single-hart-runtime-r8-plan'
          },
          {
            text: 'R8 plan review and acceptance record',
            link: '/single-hart-runtime-r8-plan-review-summary'
          },
          {
            text: 'R8-A plan revision review and acceptance record',
            link: '/single-hart-runtime-r8-plan-r8a-review-summary'
          },
          {
            text: 'R8-C plan revision review and acceptance record',
            link: '/single-hart-runtime-r8-plan-r8c-review-summary'
          },
          {
            text: 'R8-H0 local profile freeze (not reviewed)',
            link: '/single-hart-runtime-r8-h0-freeze'
          },
          {
            text: 'R8-H0/R8-C review and acceptance record',
            link: '/single-hart-runtime-r8-h0-review-summary'
          },
          {
            text: 'R8 active-line maintenance plan (R8-ALM1-A accepted)',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan'
          },
          {
            text: 'R8 active-line maintenance plan review (original target)',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan-review-summary'
          },
          {
            text: 'R8-ALM1-A review and acceptance record',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary'
          },
          {
            text: 'K3 Linux/KVM qualification plan (K0-A accepted; KVM0 dropped 2026-10-08)',
            link: '/k3-kvm0-plan'
          },
          {
            text: 'KVM0 original plan review summary (superseded)',
            link: '/k3-kvm0-plan-review-summary'
          },
          {
            text: 'KVM0 K0-A plan review and acceptance record',
            link: '/k3-kvm0-plan-k0a-review-summary'
          },
          {
            text: 'KVM0 K0-I implementation review and acceptance record',
            link: '/k3-kvm0-k0i-review-summary'
          },
          {
            text: 'KVM0 K0-S source-owner preparation authorization record',
            link: '/k3-kvm0-k0s-authorization-record'
          },
          {
            text: 'KVM0 K0-S source-owner preparation review and acceptance record',
            link: '/k3-kvm0-k0s-review-summary'
          },
          {
            text: 'K3 B0 result review and acceptance record',
            link: '/k3-b0-result-review-summary'
          },
          {
            text: 'K3 B1 result review and acceptance record',
            link: '/k3-b1-result-review-summary'
          },
          {
            text: 'K3 B2 result review and acceptance record',
            link: '/k3-b2-result-review-summary'
          },
          {
            text: 'K3 B3 result review and acceptance record',
            link: '/k3-b3-result-review-summary'
          },
          {
            text: 'K3 B4 result review and acceptance record',
            link: '/k3-b4-result-review-summary'
          },
          {
            text: 'Accepted-tool fixes review and acceptance record',
            link: '/accepted-tool-fixes-review-summary'
          },
          {
            text: 'K3 B5 plan (accepted)',
            link: '/k3-b5-plan'
          },
          {
            text: 'K3 B5 result review and acceptance record',
            link: '/k3-b5-result-review-summary'
          },
          {
            text: 'K3 B6 plan (accepted)',
            link: '/k3-b6-plan'
          },
          {
            text: 'K3 B6 result review and acceptance record',
            link: '/k3-b6-result-review-summary'
          },
          { text: 'K3 B7 plan (accepted)', link: '/k3-b7-plan' },
          {
            text: 'K3 B7 result review and acceptance record',
            link: '/k3-b7-result-review-summary'
          },
          {
            text: 'S1 He-to-Be synthesis (accepted 2026-10-18)',
            link: '/he-to-be-synthesis'
          },
          {
            text: 'S1 synthesis review summary',
            link: '/he-to-be-synthesis-review-summary'
          },
          {
            text: 'Project review 2026-10-17 (accepted 2026-10-18)',
            link: '/project-review-2026-10-17'
          },
          {
            text: 'S1 and TE-trigger revision plan (accepted 2026-10-18)',
            link: '/s1-te-trigger-revision-plan'
          },
          {
            text: 'Project review and revision plan review summary',
            link: '/project-review-2026-10-17-review-summary'
          },
          {
            text: 'S1 and TE-trigger revision RP-1 to RP-3 review and acceptance record',
            link: '/s1-te-trigger-revision-review-summary'
          },
          {
            text: 'S2 security model v1 plan (accepted 2026-10-19)',
            link: '/s2-security-model-plan'
          },
          {
            text: 'S2 plan review summary',
            link: '/s2-security-model-plan-review-summary'
          },
          {
            text: 'Security model v1 (accepted 2026-10-22)',
            link: '/security-model-v1'
          },
          {
            text: 'Security model v1 review and acceptance record',
            link: '/security-model-v1-review-summary'
          },
          {
            text: 'S3 MVP plan (accepted 2026-10-23)',
            link: '/mvp-plan'
          },
          {
            text: 'S3 MVP plan review and acceptance record',
            link: '/mvp-plan-review-summary'
          },
          {
            text: 'MVP M0 plan (accepted 2026-10-23)',
            link: '/mvp-m0-plan'
          },
          {
            text: 'MVP M0 plan review and acceptance record',
            link: '/mvp-m0-plan-review-summary'
          },
          {
            text: 'MVP M0 result review and acceptance record',
            link: '/mvp-m0-result-review-summary'
          },
          {
            text: 'MVP M1 plan (accepted 2026-10-26)',
            link: '/mvp-m1-plan'
          },
          {
            text: 'MVP M1 plan review and acceptance record',
            link: '/mvp-m1-plan-review-summary'
          },
          {
            text: 'MVP M1 result review and acceptance record',
            link: '/mvp-m1-result-review-summary'
          },
          {
            text: 'MVP M2 plan (accepted 2026-10-27)',
            link: '/mvp-m2-plan'
          },
          {
            text: 'MVP M2 plan review and acceptance record',
            link: '/mvp-m2-plan-review-summary'
          },
          {
            text: 'MVP M2 result review and acceptance record',
            link: '/mvp-m2-result-review-summary'
          },
          {
            text: 'MVP M3 plan (accepted 2026-10-28)',
            link: '/mvp-m3-plan'
          },
          {
            text: 'MVP M3 plan review and acceptance record',
            link: '/mvp-m3-plan-review-summary'
          },
          {
            text: 'Security model v1 Revision 1 review and acceptance record',
            link: '/security-model-v1-revision-1-review-summary'
          },
          {
            text: 'MVP M3 evidence record',
            link: '/mvp-m3-evidence'
          },
          {
            text: 'MVP M3 result review and acceptance record',
            link: '/mvp-m3-result-review-summary'
          },
          {
            text: 'MVP M4 plan (accepted 2026-10-28)',
            link: '/mvp-m4-plan'
          },
          {
            text: 'MVP M4 plan review and acceptance record',
            link: '/mvp-m4-plan-review-summary'
          },
          {
            text: 'MVP M4 evidence record',
            link: '/mvp-m4-evidence'
          },
          {
            text: 'MVP M4 result review and acceptance record',
            link: '/mvp-m4-result-review-summary'
          },
          {
            text: 'MVP 1.0 release candidate walkthrough',
            link: '/mvp-rc-walkthrough'
          },
          {
            text: 'MVP M5 plan (accepted 2026-10-29)',
            link: '/mvp-m5-plan'
          },
          {
            text: 'MVP M5 plan review and acceptance record',
            link: '/mvp-m5-plan-review-summary'
          },
          {
            text: 'MVP M5 evidence record',
            link: '/mvp-m5-evidence'
          },
          {
            text: 'MVP M5 result review and acceptance record',
            link: '/mvp-m5-result-review-summary'
          },
          {
            text: 'Project snapshot as of MVP 1.0 release candidate 2',
            link: '/project-snapshot-mvp-1.0-rc2'
          },
          {
            text: 'After release candidate 3: the candidates on one page (2026-10-31)',
            link: '/post-rc3-candidates-2026-10-31'
          },
          {
            text: 'MVP plan revision S3-C review and acceptance record (accepted 2026-11-01)',
            link: '/mvp-plan-s3c-review-summary'
          },
          {
            text: 'MVP M6 plan (accepted 2026-10-30)',
            link: '/mvp-m6-plan'
          },
          {
            text: 'MVP M6 plan review and acceptance record',
            link: '/mvp-m6-plan-review-summary'
          },
          {
            text: 'MVP M7 plan: interactive guests (accepted 2026-11-01)',
            link: '/mvp-m7-plan'
          },
          {
            text: 'MVP M7 plan review and acceptance record',
            link: '/mvp-m7-plan-review-summary'
          },
          {
            text: 'MVP M7 evidence record',
            link: '/mvp-m7-evidence'
          },
          {
            text: 'MVP M7 result review and acceptance record',
            link: '/mvp-m7-result-review-summary'
          },
          {
            text: 'MVP M8 plan: the first verification plan (accepted 2026-11-02)',
            link: '/mvp-m8-plan'
          },
          {
            text: 'MVP M8 plan review and acceptance record',
            link: '/mvp-m8-plan-review-summary'
          },
          {
            text: 'MVP M8 specifications (stage 1 properties, the pilot contracts; Revision 1 accepted 2026-11-03)',
            link: '/mvp-m8-specifications'
          },
          {
            text: 'MVP M8 specifications Revision 1 review packet',
            link: '/mvp-m8-specifications-revision-1-review-summary'
          },
          {
            text: 'MVP M8 evidence record',
            link: '/mvp-m8-evidence'
          },
          {
            text: 'MVP M8 result review and acceptance record (accepted 2026-11-04)',
            link: '/mvp-m8-result-review-summary'
          },
          {
            text: 'MVP M9 plan: measurement (accepted 2026-11-03)',
            link: '/mvp-m9-plan'
          },
          {
            text: 'MVP M9 plan review and acceptance record',
            link: '/mvp-m9-plan-review-summary'
          },
          {
            text: 'MVP M9 plan: the gpt-6-astra steering review (first candidate)',
            link: '/mvp-m9-plan-review-gpt-6-astra'
          },
          {
            text: 'MVP M9 platform-probe template (read-only, filled by the human)',
            link: '/mvp-m9-platform-probe'
          },
          {
            text: 'MVP M9 crosswalk: the log against the TCG and systemd model (D-7)',
            link: '/mvp-m9-crosswalk'
          },
          {
            text: 'MVP M9 evidence record',
            link: '/mvp-m9-evidence'
          },
          {
            text: 'MVP M9 result review and acceptance record (accepted 2026-11-03)',
            link: '/mvp-m9-result-review-summary'
          },
          {
            text: 'MVP M10 plan: release candidate 4 (accepted 2026-11-04)',
            link: '/mvp-m10-plan'
          },
          {
            text: 'MVP M10 plan review and acceptance record',
            link: '/mvp-m10-plan-review-summary'
          },
          {
            text: 'MVP M10 evidence record',
            link: '/mvp-m10-evidence'
          },
          {
            text: 'MVP M10 result review and acceptance record (accepted 2026-11-05)',
            link: '/mvp-m10-result-review-summary'
          },
          {
            text: 'MVP M11 plan: the physical boundary under the monitor (proposed 2026-11-11)',
            link: '/mvp-m11-plan'
          },
          {
            text: 'Security model v1 Revision 2 review packet (the console path)',
            link: '/security-model-v1-revision-2-review-summary'
          },
          {
            text: 'Security model v1 Revision 3 review packet (the measurement log)',
            link: '/security-model-v1-revision-3-review-summary'
          },
          {
            text: 'MVP M6 evidence record (release candidate 3)',
            link: '/mvp-m6-evidence'
          },
          {
            text: 'MVP M6 result review and acceptance record (release candidate 3)',
            link: '/mvp-m6-result-review-summary'
          },
          {
            text: 'Debt sweep 3 review packet (the RC3 snapshot reviews)',
            link: '/rc3-review-remediation-review-summary'
          },
          {
            text: 'Debt sweep 4 review packet (items 99, 100, 102, 105; SECURITY.md)',
            link: '/mvp-debt-4-review-summary'
          },
          {
            text: 'Debt sweep 5 review packet (item 95, the closure from public sources)',
            link: '/mvp-debt-5-review-summary'
          },
          {
            text: 'S3-C: the three independent reviews reconciled',
            link: '/mvp-plan-s3c-review-reconciliation'
          },
          {
            text: 'S3-C review input: Copilot CLI',
            link: '/mvp-plan-s3c-review-copilot-cli'
          },
          {
            text: 'S3-C review input: Codex CLI',
            link: '/mvp-plan-s3c-independent-design-review'
          },
          {
            text: 'S3-C review input: Claude Code',
            link: '/mvp-plan-s3c-review-claude-code'
          }
        ]
      },
      {
        text: 'Helium',
        items: [
          { text: 'Original plan', link: '/pathfinder-plan' },
          { text: 'Original and dual evidence', link: '/pathfinder-evidence' },
          { text: 'Minimal RISC-V plan', link: '/minimal-pathfinder-plan' },
          {
            text: 'Minimal RISC-V evidence',
            link: '/minimal-pathfinder-evidence'
          },
          {
            text: 'Fixed TE experiment',
            link: '/type-enforcement-pathfinder-plan'
          },
          {
            text: 'Fixed TE evidence',
            link: '/type-enforcement-pathfinder-evidence'
          },
          {
            text: 'Isolation and policy research',
            link: '/isolation-engine-policy-research'
          }
        ]
      },
      {
        text: 'Sidebars',
        items: [
          {
            text: 'High-assurance standards',
            link: '/sidebar-high-assurance-standards'
          },
          {
            text: 'Rust VS components',
            link: '/sidebar-rust-vs-components'
          },
          {
            text: 'Linux VBS-equivalence',
            link: '/sidebar-lvbs-equivalence'
          },
          {
            text: 'Dynamic authority caches',
            link: '/sidebar-dynamic-authority-caches'
          },
          {
            text: 'Minimal VS runtimes',
            link: '/sidebar-minimal-vs-runtimes'
          },
          {
            text: 'CHERI-RISC-V and the MVP',
            link: '/sidebar-cheri-mvp'
          },
          {
            text: 'The CHERI platform',
            link: '/cheri-platform'
          },
          {
            text: 'CHERI enforcement plan (accepted)',
            link: '/cheri-enforcement-plan'
          },
          {
            text: 'CHERI enforcement plan review and acceptance record',
            link: '/cheri-enforcement-plan-review-summary'
          },
          {
            text: 'CHERI enforcement result review and acceptance record',
            link: '/cheri-enforcement-result-review-summary'
          }
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'Implementation plan', link: '/implementation-plan' },
          { text: 'Arm64 pathfinder plan', link: '/arm64-pathfinder-plan' },
          { text: 'RISC-V security hardware', link: '/riscv-security-hardware' },
          { text: 'CHERI alignment', link: '/cheri-alignment' },
          {
            text: 'Capability and holistic policy',
            link: '/capability-policy-architecture'
          },
          {
            text: 'Supervisory security policy',
            link: '/supervisory-security-policy'
          },
          {
            text: 'M-mode, SBI, and VS decomposition',
            link: '/beryllium-hypervisor-notes'
          },
          {
            text: 'Session transcripts',
            link: '/session-analysis-transcripts-2026-07-20'
          },
          { text: 'Open tooling', link: '/open-tooling' }
        ]
      }
    ],
    sidebar: [
      {
        text: 'Start here',
        items: [
          { text: 'Planning overview', link: '/' },
          { text: 'Beryllium roadmap', link: '/roadmap' },
          { text: 'Project orientation', link: '/project-orientation' },
          { text: 'Glossary', link: '/glossary' },
          { text: 'Session handoff', link: '/HANDOFF' },
          {
            text: 'Source-first documentation review',
            link: '/source-first-documentation-policy-review-summary'
          },
          {
            text: 'Post-pathfinder decision',
            link: '/pathfinder-comparison'
          },
          {
            text: 'Architecture Model 0.1',
            link: '/architecture-model-0.1'
          },
          {
            text: 'Model 0.1 implementation and evidence',
            link: '/architecture-model-0.1-evidence'
          },
          {
            text: 'Architecture Model 0.2',
            link: '/architecture-model-0.2'
          },
          {
            text: 'Model 0.2 implementation and evidence',
            link: '/architecture-model-0.2-evidence'
          },
          {
            text: 'Bounded single-hart runtime plan',
            link: '/single-hart-runtime-plan'
          },
          {
            text: 'Single-hart runtime R1 evidence',
            link: '/single-hart-runtime-r1-evidence'
          },
          {
            text: 'R1 review and acceptance record',
            link: '/single-hart-runtime-r1-review-summary'
          },
          {
            text: 'R2 bounded plan (accepted)',
            link: '/single-hart-runtime-r2-plan'
          },
          {
            text: 'R2 plan review summary',
            link: '/single-hart-runtime-r2-plan-review-summary'
          },
          {
            text: 'R2 Sv39x4 backend evidence (accepted)',
            link: '/single-hart-runtime-r2-evidence'
          },
          {
            text: 'R2 implementation review (accepted)',
            link: '/single-hart-runtime-r2-review-summary'
          },
          {
            text: 'R3 boot and first-entry evidence',
            link: '/single-hart-runtime-r3-evidence'
          },
          {
            text: 'R3 implementation review packet',
            link: '/single-hart-runtime-r3-review-summary'
          },
          {
            text: 'R4 review and acceptance packet',
            link: '/single-hart-runtime-r4-review-summary'
          },
          {
            text: 'R5 bounded plan (accepted)',
            link: '/single-hart-runtime-r5-plan'
          },
          {
            text: 'R5 plan review and acceptance record',
            link: '/single-hart-runtime-r5-plan-review-summary'
          },
          {
            text: 'R5 checked-switch evidence (accepted target)',
            link: '/single-hart-runtime-r5-evidence'
          },
          {
            text: 'R5 review and acceptance record',
            link: '/single-hart-runtime-r5-review-summary'
          },
          {
            text: 'R6 bounded plan (accepted, incl. revisions R6-A and R6-B)',
            link: '/single-hart-runtime-r6-plan'
          },
          {
            text: 'R6 plan review and acceptance record',
            link: '/single-hart-runtime-r6-plan-review-summary'
          },
          {
            text: 'R6 plan revision review and acceptance record',
            link: '/single-hart-runtime-r6-plan-revision-review-summary'
          },
          {
            text: 'R6-B plan revision review and acceptance record',
            link: '/single-hart-runtime-r6-plan-r6b-review-summary'
          },
          {
            text: 'R6 adversarial-image evidence (accepted target)',
            link: '/single-hart-runtime-r6-evidence'
          },
          {
            text: 'R6 review and acceptance record',
            link: '/single-hart-runtime-r6-review-summary'
          },
          {
            text: 'R7 proof and evidence plan (accepted, incl. revision R7-A)',
            link: '/single-hart-runtime-r7-plan'
          },
          {
            text: 'R7 plan review and acceptance record',
            link: '/single-hart-runtime-r7-plan-review-summary'
          },
          {
            text: 'R7-A plan revision review and acceptance record',
            link: '/single-hart-runtime-r7-plan-r7a-review-summary'
          },
          {
            text: 'R7 bounded exact-proof and evidence record',
            link: '/single-hart-runtime-r7-evidence'
          },
          {
            text: 'R7 review and acceptance record',
            link: '/single-hart-runtime-r7-review-summary'
          },
          {
            text: 'R8 K3 core-validation plan (accepted; dropped 2026-10-08)',
            link: '/single-hart-runtime-r8-plan'
          },
          {
            text: 'R8 plan review and acceptance record',
            link: '/single-hart-runtime-r8-plan-review-summary'
          },
          {
            text: 'R8-A plan revision review and acceptance record',
            link: '/single-hart-runtime-r8-plan-r8a-review-summary'
          },
          {
            text: 'R8-C plan revision review and acceptance record',
            link: '/single-hart-runtime-r8-plan-r8c-review-summary'
          },
          {
            text: 'R8-H0 local profile freeze (not reviewed)',
            link: '/single-hart-runtime-r8-h0-freeze'
          },
          {
            text: 'R8-H0/R8-C review and acceptance record',
            link: '/single-hart-runtime-r8-h0-review-summary'
          },
          {
            text: 'R8 active-line maintenance plan (R8-ALM1-A accepted)',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan'
          },
          {
            text: 'R8 active-line maintenance plan review (original target)',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan-review-summary'
          },
          {
            text: 'R8-ALM1-A review and acceptance record',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary'
          },
          {
            text: 'K3 Linux/KVM qualification plan (K0-A accepted; KVM0 dropped 2026-10-08)',
            link: '/k3-kvm0-plan'
          },
          {
            text: 'KVM0 original plan review summary (superseded)',
            link: '/k3-kvm0-plan-review-summary'
          },
          {
            text: 'KVM0 K0-A plan review and acceptance record',
            link: '/k3-kvm0-plan-k0a-review-summary'
          },
          {
            text: 'KVM0 K0-I implementation review and acceptance record',
            link: '/k3-kvm0-k0i-review-summary'
          },
          {
            text: 'KVM0 K0-S source-owner preparation authorization record',
            link: '/k3-kvm0-k0s-authorization-record'
          },
          {
            text: 'KVM0 K0-S source-owner preparation review and acceptance record',
            link: '/k3-kvm0-k0s-review-summary'
          },
          {
            text: 'K3 B0 result review and acceptance record',
            link: '/k3-b0-result-review-summary'
          },
          {
            text: 'K3 B1 result review and acceptance record',
            link: '/k3-b1-result-review-summary'
          },
          {
            text: 'K3 B2 result review and acceptance record',
            link: '/k3-b2-result-review-summary'
          },
          {
            text: 'K3 B3 result review and acceptance record',
            link: '/k3-b3-result-review-summary'
          },
          {
            text: 'K3 B4 result review and acceptance record',
            link: '/k3-b4-result-review-summary'
          },
          {
            text: 'Accepted-tool fixes review and acceptance record',
            link: '/accepted-tool-fixes-review-summary'
          },
          {
            text: 'K3 B5 plan (accepted)',
            link: '/k3-b5-plan'
          },
          {
            text: 'K3 B5 result review and acceptance record',
            link: '/k3-b5-result-review-summary'
          },
          {
            text: 'K3 B6 plan (accepted)',
            link: '/k3-b6-plan'
          },
          {
            text: 'K3 B6 result review and acceptance record',
            link: '/k3-b6-result-review-summary'
          },
          { text: 'K3 B7 plan (accepted)', link: '/k3-b7-plan' },
          {
            text: 'K3 B7 result review and acceptance record',
            link: '/k3-b7-result-review-summary'
          },
          {
            text: 'S1 He-to-Be synthesis (accepted 2026-10-18)',
            link: '/he-to-be-synthesis'
          },
          {
            text: 'S1 synthesis review summary',
            link: '/he-to-be-synthesis-review-summary'
          },
          {
            text: 'Project review 2026-10-17 (accepted 2026-10-18)',
            link: '/project-review-2026-10-17'
          },
          {
            text: 'S1 and TE-trigger revision plan (accepted 2026-10-18)',
            link: '/s1-te-trigger-revision-plan'
          },
          {
            text: 'Project review and revision plan review summary',
            link: '/project-review-2026-10-17-review-summary'
          },
          {
            text: 'S1 and TE-trigger revision RP-1 to RP-3 review and acceptance record',
            link: '/s1-te-trigger-revision-review-summary'
          },
          {
            text: 'S2 security model v1 plan (accepted 2026-10-19)',
            link: '/s2-security-model-plan'
          },
          {
            text: 'S2 plan review summary',
            link: '/s2-security-model-plan-review-summary'
          },
          {
            text: 'Security model v1 (accepted 2026-10-22)',
            link: '/security-model-v1'
          },
          {
            text: 'Security model v1 review and acceptance record',
            link: '/security-model-v1-review-summary'
          },
          {
            text: 'S3 MVP plan (accepted 2026-10-23)',
            link: '/mvp-plan'
          },
          {
            text: 'S3 MVP plan review and acceptance record',
            link: '/mvp-plan-review-summary'
          },
          {
            text: 'MVP M0 plan (accepted 2026-10-23)',
            link: '/mvp-m0-plan'
          },
          {
            text: 'MVP M0 plan review and acceptance record',
            link: '/mvp-m0-plan-review-summary'
          },
          {
            text: 'MVP M0 result review and acceptance record',
            link: '/mvp-m0-result-review-summary'
          },
          {
            text: 'MVP M1 plan (accepted 2026-10-26)',
            link: '/mvp-m1-plan'
          },
          {
            text: 'MVP M1 plan review and acceptance record',
            link: '/mvp-m1-plan-review-summary'
          },
          {
            text: 'MVP M1 result review and acceptance record',
            link: '/mvp-m1-result-review-summary'
          },
          {
            text: 'MVP M2 plan (accepted 2026-10-27)',
            link: '/mvp-m2-plan'
          },
          {
            text: 'MVP M2 plan review and acceptance record',
            link: '/mvp-m2-plan-review-summary'
          },
          {
            text: 'MVP M2 result review and acceptance record',
            link: '/mvp-m2-result-review-summary'
          },
          {
            text: 'MVP M3 plan (accepted 2026-10-28)',
            link: '/mvp-m3-plan'
          },
          {
            text: 'MVP M3 plan review and acceptance record',
            link: '/mvp-m3-plan-review-summary'
          },
          {
            text: 'Security model v1 Revision 1 review and acceptance record',
            link: '/security-model-v1-revision-1-review-summary'
          },
          {
            text: 'MVP M3 evidence record',
            link: '/mvp-m3-evidence'
          },
          {
            text: 'MVP M3 result review and acceptance record',
            link: '/mvp-m3-result-review-summary'
          },
          {
            text: 'MVP M4 plan (accepted 2026-10-28)',
            link: '/mvp-m4-plan'
          },
          {
            text: 'MVP M4 plan review and acceptance record',
            link: '/mvp-m4-plan-review-summary'
          },
          {
            text: 'MVP M4 evidence record',
            link: '/mvp-m4-evidence'
          },
          {
            text: 'MVP M4 result review and acceptance record',
            link: '/mvp-m4-result-review-summary'
          },
          {
            text: 'MVP 1.0 release candidate walkthrough',
            link: '/mvp-rc-walkthrough'
          },
          {
            text: 'MVP M5 plan (accepted 2026-10-29)',
            link: '/mvp-m5-plan'
          },
          {
            text: 'MVP M5 plan review and acceptance record',
            link: '/mvp-m5-plan-review-summary'
          },
          {
            text: 'MVP M5 evidence record',
            link: '/mvp-m5-evidence'
          },
          {
            text: 'MVP M5 result review and acceptance record',
            link: '/mvp-m5-result-review-summary'
          },
          {
            text: 'Project snapshot as of MVP 1.0 release candidate 2',
            link: '/project-snapshot-mvp-1.0-rc2'
          },
          {
            text: 'After release candidate 3: the candidates on one page (2026-10-31)',
            link: '/post-rc3-candidates-2026-10-31'
          },
          {
            text: 'MVP plan revision S3-C review and acceptance record (accepted 2026-11-01)',
            link: '/mvp-plan-s3c-review-summary'
          },
          {
            text: 'MVP M6 plan (accepted 2026-10-30)',
            link: '/mvp-m6-plan'
          },
          {
            text: 'MVP M6 plan review and acceptance record',
            link: '/mvp-m6-plan-review-summary'
          },
          {
            text: 'MVP M7 plan: interactive guests (accepted 2026-11-01)',
            link: '/mvp-m7-plan'
          },
          {
            text: 'MVP M7 plan review and acceptance record',
            link: '/mvp-m7-plan-review-summary'
          },
          {
            text: 'MVP M7 evidence record',
            link: '/mvp-m7-evidence'
          },
          {
            text: 'MVP M7 result review and acceptance record',
            link: '/mvp-m7-result-review-summary'
          },
          {
            text: 'MVP M8 plan: the first verification plan (accepted 2026-11-02)',
            link: '/mvp-m8-plan'
          },
          {
            text: 'MVP M8 plan review and acceptance record',
            link: '/mvp-m8-plan-review-summary'
          },
          {
            text: 'MVP M8 specifications (stage 1 properties, the pilot contracts; Revision 1 accepted 2026-11-03)',
            link: '/mvp-m8-specifications'
          },
          {
            text: 'MVP M8 specifications Revision 1 review packet',
            link: '/mvp-m8-specifications-revision-1-review-summary'
          },
          {
            text: 'MVP M8 evidence record',
            link: '/mvp-m8-evidence'
          },
          {
            text: 'MVP M8 result review and acceptance record (accepted 2026-11-04)',
            link: '/mvp-m8-result-review-summary'
          },
          {
            text: 'MVP M9 plan: measurement (accepted 2026-11-03)',
            link: '/mvp-m9-plan'
          },
          {
            text: 'MVP M9 plan review and acceptance record',
            link: '/mvp-m9-plan-review-summary'
          },
          {
            text: 'MVP M9 plan: the gpt-6-astra steering review (first candidate)',
            link: '/mvp-m9-plan-review-gpt-6-astra'
          },
          {
            text: 'MVP M9 platform-probe template (read-only, filled by the human)',
            link: '/mvp-m9-platform-probe'
          },
          {
            text: 'MVP M9 crosswalk: the log against the TCG and systemd model (D-7)',
            link: '/mvp-m9-crosswalk'
          },
          {
            text: 'MVP M9 evidence record',
            link: '/mvp-m9-evidence'
          },
          {
            text: 'MVP M9 result review and acceptance record (accepted 2026-11-03)',
            link: '/mvp-m9-result-review-summary'
          },
          {
            text: 'MVP M10 plan: release candidate 4 (accepted 2026-11-04)',
            link: '/mvp-m10-plan'
          },
          {
            text: 'MVP M10 plan review and acceptance record',
            link: '/mvp-m10-plan-review-summary'
          },
          {
            text: 'MVP M10 evidence record',
            link: '/mvp-m10-evidence'
          },
          {
            text: 'MVP M10 result review and acceptance record (accepted 2026-11-05)',
            link: '/mvp-m10-result-review-summary'
          },
          {
            text: 'MVP M11 plan: the physical boundary under the monitor (proposed 2026-11-11)',
            link: '/mvp-m11-plan'
          },
          {
            text: 'Security model v1 Revision 2 review packet (the console path)',
            link: '/security-model-v1-revision-2-review-summary'
          },
          {
            text: 'Security model v1 Revision 3 review packet (the measurement log)',
            link: '/security-model-v1-revision-3-review-summary'
          },
          {
            text: 'MVP M6 evidence record (release candidate 3)',
            link: '/mvp-m6-evidence'
          },
          {
            text: 'MVP M6 result review and acceptance record (release candidate 3)',
            link: '/mvp-m6-result-review-summary'
          },
          { text: 'Helium PoC', link: '/pathfinder-plan' },
          { text: 'Helium evidence', link: '/pathfinder-evidence' },
          { text: 'Minimal RISC-V PoC', link: '/minimal-pathfinder-plan' },
          {
            text: 'Minimal RISC-V evidence',
            link: '/minimal-pathfinder-evidence'
          },
          {
            text: 'Fixed TE experiment',
            link: '/type-enforcement-pathfinder-plan'
          },
          {
            text: 'Fixed TE evidence',
            link: '/type-enforcement-pathfinder-evidence'
          },
          {
            text: 'Isolation engine and CAP+TE research',
            link: '/isolation-engine-policy-research'
          }
        ]
      },
      {
        text: 'Architecture and roadmap',
        items: [
          {
            text: 'Post-pathfinder decision',
            link: '/pathfinder-comparison'
          },
          {
            text: 'Architecture Model 0.1',
            link: '/architecture-model-0.1'
          },
          {
            text: 'Model 0.1 implementation and evidence',
            link: '/architecture-model-0.1-evidence'
          },
          {
            text: 'Architecture Model 0.2',
            link: '/architecture-model-0.2'
          },
          {
            text: 'Model 0.2 implementation and evidence',
            link: '/architecture-model-0.2-evidence'
          },
          {
            text: 'Bounded single-hart runtime plan',
            link: '/single-hart-runtime-plan'
          },
          {
            text: 'Single-hart runtime R1 evidence',
            link: '/single-hart-runtime-r1-evidence'
          },
          {
            text: 'R1 review and acceptance record',
            link: '/single-hart-runtime-r1-review-summary'
          },
          {
            text: 'R2 bounded plan (accepted)',
            link: '/single-hart-runtime-r2-plan'
          },
          {
            text: 'R2 plan review summary',
            link: '/single-hart-runtime-r2-plan-review-summary'
          },
          {
            text: 'R2 Sv39x4 backend evidence (accepted)',
            link: '/single-hart-runtime-r2-evidence'
          },
          {
            text: 'R2 implementation review (accepted)',
            link: '/single-hart-runtime-r2-review-summary'
          },
          {
            text: 'R3 boot and first-entry evidence',
            link: '/single-hart-runtime-r3-evidence'
          },
          {
            text: 'R3 implementation review packet',
            link: '/single-hart-runtime-r3-review-summary'
          },
          {
            text: 'R4 review and acceptance packet',
            link: '/single-hart-runtime-r4-review-summary'
          },
          {
            text: 'R5 bounded plan (accepted)',
            link: '/single-hart-runtime-r5-plan'
          },
          {
            text: 'R5 plan review and acceptance record',
            link: '/single-hart-runtime-r5-plan-review-summary'
          },
          {
            text: 'R5 checked-switch evidence (accepted target)',
            link: '/single-hart-runtime-r5-evidence'
          },
          {
            text: 'R5 review and acceptance record',
            link: '/single-hart-runtime-r5-review-summary'
          },
          {
            text: 'R6 bounded plan (accepted, incl. revisions R6-A and R6-B)',
            link: '/single-hart-runtime-r6-plan'
          },
          {
            text: 'R6 plan review and acceptance record',
            link: '/single-hart-runtime-r6-plan-review-summary'
          },
          {
            text: 'R6 plan revision review and acceptance record',
            link: '/single-hart-runtime-r6-plan-revision-review-summary'
          },
          {
            text: 'R6-B plan revision review and acceptance record',
            link: '/single-hart-runtime-r6-plan-r6b-review-summary'
          },
          {
            text: 'R6 adversarial-image evidence (accepted target)',
            link: '/single-hart-runtime-r6-evidence'
          },
          {
            text: 'R6 review and acceptance record',
            link: '/single-hart-runtime-r6-review-summary'
          },
          {
            text: 'R7 proof and evidence plan (accepted, incl. revision R7-A)',
            link: '/single-hart-runtime-r7-plan'
          },
          {
            text: 'R7 plan review and acceptance record',
            link: '/single-hart-runtime-r7-plan-review-summary'
          },
          {
            text: 'R7-A plan revision review and acceptance record',
            link: '/single-hart-runtime-r7-plan-r7a-review-summary'
          },
          {
            text: 'R7 bounded exact-proof and evidence record',
            link: '/single-hart-runtime-r7-evidence'
          },
          {
            text: 'R7 review and acceptance record',
            link: '/single-hart-runtime-r7-review-summary'
          },
          {
            text: 'R8 K3 core-validation plan (accepted; dropped 2026-10-08)',
            link: '/single-hart-runtime-r8-plan'
          },
          {
            text: 'R8 plan review and acceptance record',
            link: '/single-hart-runtime-r8-plan-review-summary'
          },
          {
            text: 'R8-A plan revision review and acceptance record',
            link: '/single-hart-runtime-r8-plan-r8a-review-summary'
          },
          {
            text: 'R8-C plan revision review and acceptance record',
            link: '/single-hart-runtime-r8-plan-r8c-review-summary'
          },
          {
            text: 'R8-H0 local profile freeze (not reviewed)',
            link: '/single-hart-runtime-r8-h0-freeze'
          },
          {
            text: 'R8-H0/R8-C review and acceptance record',
            link: '/single-hart-runtime-r8-h0-review-summary'
          },
          {
            text: 'R8 active-line maintenance plan (R8-ALM1-A accepted)',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan'
          },
          {
            text: 'R8 active-line maintenance plan review (original target)',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan-review-summary'
          },
          {
            text: 'R8-ALM1-A review and acceptance record',
            link: '/single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary'
          },
          {
            text: 'K3 Linux/KVM qualification plan (K0-A accepted; KVM0 dropped 2026-10-08)',
            link: '/k3-kvm0-plan'
          },
          {
            text: 'KVM0 original plan review summary (superseded)',
            link: '/k3-kvm0-plan-review-summary'
          },
          {
            text: 'KVM0 K0-A plan review and acceptance record',
            link: '/k3-kvm0-plan-k0a-review-summary'
          },
          {
            text: 'KVM0 K0-I implementation review and acceptance record',
            link: '/k3-kvm0-k0i-review-summary'
          },
          {
            text: 'KVM0 K0-S source-owner preparation authorization record',
            link: '/k3-kvm0-k0s-authorization-record'
          },
          {
            text: 'KVM0 K0-S source-owner preparation review and acceptance record',
            link: '/k3-kvm0-k0s-review-summary'
          },
          {
            text: 'K3 B0 result review and acceptance record',
            link: '/k3-b0-result-review-summary'
          },
          {
            text: 'K3 B1 result review and acceptance record',
            link: '/k3-b1-result-review-summary'
          },
          {
            text: 'K3 B2 result review and acceptance record',
            link: '/k3-b2-result-review-summary'
          },
          {
            text: 'K3 B3 result review and acceptance record',
            link: '/k3-b3-result-review-summary'
          },
          {
            text: 'K3 B4 result review and acceptance record',
            link: '/k3-b4-result-review-summary'
          },
          {
            text: 'Accepted-tool fixes review and acceptance record',
            link: '/accepted-tool-fixes-review-summary'
          },
          {
            text: 'K3 B5 plan (accepted)',
            link: '/k3-b5-plan'
          },
          {
            text: 'K3 B5 result review and acceptance record',
            link: '/k3-b5-result-review-summary'
          },
          {
            text: 'K3 B6 plan (accepted)',
            link: '/k3-b6-plan'
          },
          {
            text: 'K3 B6 result review and acceptance record',
            link: '/k3-b6-result-review-summary'
          },
          { text: 'K3 B7 plan (accepted)', link: '/k3-b7-plan' },
          {
            text: 'K3 B7 result review and acceptance record',
            link: '/k3-b7-result-review-summary'
          },
          {
            text: 'S1 He-to-Be synthesis (accepted 2026-10-18)',
            link: '/he-to-be-synthesis'
          },
          {
            text: 'S1 synthesis review summary',
            link: '/he-to-be-synthesis-review-summary'
          },
          {
            text: 'Project review 2026-10-17 (accepted 2026-10-18)',
            link: '/project-review-2026-10-17'
          },
          {
            text: 'S1 and TE-trigger revision plan (accepted 2026-10-18)',
            link: '/s1-te-trigger-revision-plan'
          },
          {
            text: 'Project review and revision plan review summary',
            link: '/project-review-2026-10-17-review-summary'
          },
          {
            text: 'S1 and TE-trigger revision RP-1 to RP-3 review and acceptance record',
            link: '/s1-te-trigger-revision-review-summary'
          },
          {
            text: 'S2 security model v1 plan (accepted 2026-10-19)',
            link: '/s2-security-model-plan'
          },
          {
            text: 'S2 plan review summary',
            link: '/s2-security-model-plan-review-summary'
          },
          {
            text: 'Security model v1 (accepted 2026-10-22)',
            link: '/security-model-v1'
          },
          {
            text: 'Security model v1 review and acceptance record',
            link: '/security-model-v1-review-summary'
          },
          {
            text: 'S3 MVP plan (accepted 2026-10-23)',
            link: '/mvp-plan'
          },
          {
            text: 'S3 MVP plan review and acceptance record',
            link: '/mvp-plan-review-summary'
          },
          {
            text: 'MVP M0 plan (accepted 2026-10-23)',
            link: '/mvp-m0-plan'
          },
          {
            text: 'MVP M0 plan review and acceptance record',
            link: '/mvp-m0-plan-review-summary'
          },
          {
            text: 'MVP M0 result review and acceptance record',
            link: '/mvp-m0-result-review-summary'
          },
          {
            text: 'MVP M1 plan (accepted 2026-10-26)',
            link: '/mvp-m1-plan'
          },
          {
            text: 'MVP M1 plan review and acceptance record',
            link: '/mvp-m1-plan-review-summary'
          },
          {
            text: 'MVP M1 result review and acceptance record',
            link: '/mvp-m1-result-review-summary'
          },
          {
            text: 'MVP M2 plan (accepted 2026-10-27)',
            link: '/mvp-m2-plan'
          },
          {
            text: 'MVP M2 plan review and acceptance record',
            link: '/mvp-m2-plan-review-summary'
          },
          {
            text: 'MVP M2 result review and acceptance record',
            link: '/mvp-m2-result-review-summary'
          },
          {
            text: 'MVP M3 plan (accepted 2026-10-28)',
            link: '/mvp-m3-plan'
          },
          {
            text: 'MVP M3 plan review and acceptance record',
            link: '/mvp-m3-plan-review-summary'
          },
          {
            text: 'Security model v1 Revision 1 review and acceptance record',
            link: '/security-model-v1-revision-1-review-summary'
          },
          {
            text: 'MVP M3 evidence record',
            link: '/mvp-m3-evidence'
          },
          {
            text: 'MVP M3 result review and acceptance record',
            link: '/mvp-m3-result-review-summary'
          },
          {
            text: 'MVP M4 plan (accepted 2026-10-28)',
            link: '/mvp-m4-plan'
          },
          {
            text: 'MVP M4 plan review and acceptance record',
            link: '/mvp-m4-plan-review-summary'
          },
          {
            text: 'MVP M4 evidence record',
            link: '/mvp-m4-evidence'
          },
          {
            text: 'MVP M4 result review and acceptance record',
            link: '/mvp-m4-result-review-summary'
          },
          {
            text: 'MVP 1.0 release candidate walkthrough',
            link: '/mvp-rc-walkthrough'
          },
          {
            text: 'MVP M5 plan (accepted 2026-10-29)',
            link: '/mvp-m5-plan'
          },
          {
            text: 'MVP M5 plan review and acceptance record',
            link: '/mvp-m5-plan-review-summary'
          },
          {
            text: 'MVP M5 evidence record',
            link: '/mvp-m5-evidence'
          },
          {
            text: 'MVP M5 result review and acceptance record',
            link: '/mvp-m5-result-review-summary'
          },
          {
            text: 'Project snapshot as of MVP 1.0 release candidate 2',
            link: '/project-snapshot-mvp-1.0-rc2'
          },
          {
            text: 'After release candidate 3: the candidates on one page (2026-10-31)',
            link: '/post-rc3-candidates-2026-10-31'
          },
          {
            text: 'MVP plan revision S3-C review and acceptance record (accepted 2026-11-01)',
            link: '/mvp-plan-s3c-review-summary'
          },
          {
            text: 'MVP M6 plan (accepted 2026-10-30)',
            link: '/mvp-m6-plan'
          },
          {
            text: 'MVP M6 plan review and acceptance record',
            link: '/mvp-m6-plan-review-summary'
          },
          {
            text: 'MVP M7 plan: interactive guests (accepted 2026-11-01)',
            link: '/mvp-m7-plan'
          },
          {
            text: 'MVP M7 plan review and acceptance record',
            link: '/mvp-m7-plan-review-summary'
          },
          {
            text: 'MVP M7 evidence record',
            link: '/mvp-m7-evidence'
          },
          {
            text: 'MVP M7 result review and acceptance record',
            link: '/mvp-m7-result-review-summary'
          },
          {
            text: 'MVP M8 plan: the first verification plan (accepted 2026-11-02)',
            link: '/mvp-m8-plan'
          },
          {
            text: 'MVP M8 plan review and acceptance record',
            link: '/mvp-m8-plan-review-summary'
          },
          {
            text: 'MVP M8 specifications (stage 1 properties, the pilot contracts; Revision 1 accepted 2026-11-03)',
            link: '/mvp-m8-specifications'
          },
          {
            text: 'MVP M8 specifications Revision 1 review packet',
            link: '/mvp-m8-specifications-revision-1-review-summary'
          },
          {
            text: 'MVP M8 evidence record',
            link: '/mvp-m8-evidence'
          },
          {
            text: 'MVP M8 result review and acceptance record (accepted 2026-11-04)',
            link: '/mvp-m8-result-review-summary'
          },
          {
            text: 'MVP M9 plan: measurement (accepted 2026-11-03)',
            link: '/mvp-m9-plan'
          },
          {
            text: 'MVP M9 plan review and acceptance record',
            link: '/mvp-m9-plan-review-summary'
          },
          {
            text: 'MVP M9 plan: the gpt-6-astra steering review (first candidate)',
            link: '/mvp-m9-plan-review-gpt-6-astra'
          },
          {
            text: 'MVP M9 platform-probe template (read-only, filled by the human)',
            link: '/mvp-m9-platform-probe'
          },
          {
            text: 'MVP M9 crosswalk: the log against the TCG and systemd model (D-7)',
            link: '/mvp-m9-crosswalk'
          },
          {
            text: 'MVP M9 evidence record',
            link: '/mvp-m9-evidence'
          },
          {
            text: 'MVP M9 result review and acceptance record (accepted 2026-11-03)',
            link: '/mvp-m9-result-review-summary'
          },
          {
            text: 'MVP M10 plan: release candidate 4 (accepted 2026-11-04)',
            link: '/mvp-m10-plan'
          },
          {
            text: 'MVP M10 plan review and acceptance record',
            link: '/mvp-m10-plan-review-summary'
          },
          {
            text: 'MVP M10 evidence record',
            link: '/mvp-m10-evidence'
          },
          {
            text: 'MVP M10 result review and acceptance record (accepted 2026-11-05)',
            link: '/mvp-m10-result-review-summary'
          },
          {
            text: 'MVP M11 plan: the physical boundary under the monitor (proposed 2026-11-11)',
            link: '/mvp-m11-plan'
          },
          {
            text: 'Security model v1 Revision 2 review packet (the console path)',
            link: '/security-model-v1-revision-2-review-summary'
          },
          {
            text: 'Security model v1 Revision 3 review packet (the measurement log)',
            link: '/security-model-v1-revision-3-review-summary'
          },
          {
            text: 'MVP M6 evidence record (release candidate 3)',
            link: '/mvp-m6-evidence'
          },
          {
            text: 'MVP M6 result review and acceptance record (release candidate 3)',
            link: '/mvp-m6-result-review-summary'
          },
          { text: 'Implementation plan', link: '/implementation-plan' },
          {
            text: 'Isolation engine and CAP+TE',
            link: '/isolation-engine-policy-research'
          },
          {
            text: 'Capability and holistic policy',
            link: '/capability-policy-architecture'
          },
          {
            text: 'Supervisory security policy',
            link: '/supervisory-security-policy'
          },
          {
            text: 'M-mode, SBI, and VS decomposition',
            link: '/beryllium-hypervisor-notes'
          },
          { text: 'Arm64 pathfinder plan', link: '/arm64-pathfinder-plan' },
          { text: 'RISC-V and K3 hardware', link: '/riscv-security-hardware' },
          { text: 'CHERI alignment', link: '/cheri-alignment' }
        ]
      },
      {
        text: 'Assurance and research',
        items: [
          { text: 'Open tooling', link: '/open-tooling' },
          { text: 'Research synthesis', link: '/research-synthesis' },
          { text: 'Research provenance', link: '/research-provenance' },
          {
            text: 'Hypervisor architecture notes',
            link: '/beryllium-hypervisor-notes'
          },
          {
            text: 'Session transcript index',
            link: '/session-analysis-transcripts-2026-07-20'
          },
          {
            text: 'TE and VBS assessment transcript',
            link: '/session-analysis-te-vbs-2026-07-20'
          },
          {
            text: 'HS isolation-engine transcript',
            link: '/session-analysis-isolation-engine-2026-07-20'
          },
          {
            text: 'CAP+TE and CHERI transcript',
            link: '/session-analysis-cap-te-cheri-2026-07-20'
          }
        ]
      },
      {
        text: 'Future research sidebars',
        items: [
          {
            text: 'High-assurance standards and open tooling',
            link: '/sidebar-high-assurance-standards'
          },
          {
            text: 'Rust for future VS components',
            link: '/sidebar-rust-vs-components'
          },
          {
            text: 'Optional Linux VBS-equivalence',
            link: '/sidebar-lvbs-equivalence'
          },
          {
            text: 'Dynamic authority caches',
            link: '/sidebar-dynamic-authority-caches'
          },
          {
            text: 'LiteBox and minimal VS runtimes',
            link: '/sidebar-minimal-vs-runtimes'
          },
          {
            text: 'CHERI-RISC-V and the MVP\'s mechanisms',
            link: '/sidebar-cheri-mvp'
          },
          {
            text: 'The CHERI platform',
            link: '/cheri-platform'
          },
          {
            text: 'CHERI enforcement plan (accepted)',
            link: '/cheri-enforcement-plan'
          },
          {
            text: 'CHERI enforcement plan review and acceptance record',
            link: '/cheri-enforcement-plan-review-summary'
          },
          {
            text: 'CHERI enforcement result review and acceptance record',
            link: '/cheri-enforcement-result-review-summary'
          }
        ]
      }
    ],
    outline: {
      level: [2, 4],
      label: 'On this page'
    },
    search: {
      provider: 'local'
    },
    docFooter: {
      prev: 'Previous',
      next: 'Next'
    },
    externalLinkIcon: true,
    sidebarMenuLabel: 'Documentation',
    returnToTopLabel: 'Return to top'
  }
})
