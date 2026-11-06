// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Planning VitePress theme entry point. The default theme retains ownership
 * of navigation and document structure; repository additions occupy only
 * supported layout slots and presentation hooks.
 */

import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import SidebarResizeHandle from './SidebarResizeHandle.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-bottom': () =>
        h(SidebarResizeHandle, { kind: 'navigation' }),
      'aside-top': () =>
        h(SidebarResizeHandle, { kind: 'outline' }),
      'doc-before': () =>
        h('div', { class: 'source-notice' }, [
          h('strong', 'Generated view. '),
          'Edit the Markdown files under ',
          h('code', 'planning/'),
          '; do not edit generated HTML.'
        ])
    })
  }
}
