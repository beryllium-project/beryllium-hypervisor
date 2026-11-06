<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->
<!--
  Accessible desktop-only sidebar splitter for the planning documentation.

  VitePress remains responsible for layout and mobile drawers. This component
  changes only the documented CSS width properties, validates persisted input,
  and removes every global listener when Vue unmounts or hot-reloads it.
-->
<script setup lang="ts">
import { onContentUpdated } from 'vitepress'
import {
  computed,
  nextTick,
  onMounted,
  onUnmounted,
  ref
} from 'vue'

type SidebarKind = 'navigation' | 'outline'

interface ResizeConfiguration {
  cssProperty: string
  defaultWidth: number
  minimumWidth: number
  maximumWidth: number
  minimumViewport: number
  storageKey: string
  label: string
}

const configurations: Record<SidebarKind, ResizeConfiguration> = {
  navigation: {
    cssProperty: '--vp-sidebar-width',
    defaultWidth: 320,
    minimumWidth: 260,
    maximumWidth: 480,
    minimumViewport: 960,
    storageKey: 'beryllium.planning.navigation-sidebar-width.v1',
    label: 'Resize documentation navigation sidebar'
  },
  outline: {
    cssProperty: '--be-outline-sidebar-width',
    defaultWidth: 256,
    minimumWidth: 208,
    maximumWidth: 360,
    minimumViewport: 1280,
    storageKey: 'beryllium.planning.outline-sidebar-width.v1',
    label: 'Resize document outline sidebar'
  }
}

const props = defineProps<{
  kind: SidebarKind
}>()

const configuration = configurations[props.kind]
const handle = ref<HTMLElement | null>(null)
const visible = ref(false)
const dragging = ref(false)
const width = ref(configuration.defaultWidth)
const maximumWidth = ref(configuration.maximumWidth)
const instructionsId = `be-${props.kind}-sidebar-resize-instructions`
const keyboardStep = 16

let activePointerId: number | null = null
let mounted = false
let observedContainer: Element | null = null
let preferredWidth = configuration.defaultWidth
let resizeObserver: ResizeObserver | null = null
let startPointerX = 0
let startWidth = configuration.defaultWidth
let usingRepositoryDefault = true

const valueText = computed(
  () => `${width.value} pixels. Use Left and Right Arrow keys to resize.`
)

onMounted(async () => {
  mounted = true
  const storedWidth = readStoredWidth()
  if (storedWidth !== null) {
    preferredWidth = storedWidth
    usingRepositoryDefault = false
  }

  await nextTick()
  if (!mounted) {
    return
  }

  if (props.kind === 'outline' && 'ResizeObserver' in window) {
    resizeObserver = new ResizeObserver(refreshLayout)
    observeOutlineContainer()
  }

  window.addEventListener('resize', refreshLayout)
  refreshLayout()
})

onContentUpdated(() => {
  void nextTick().then(() => {
    if (!mounted) {
      return
    }
    observeOutlineContainer()
    refreshLayout()
  })
})

onUnmounted(() => {
  mounted = false
  stopDragging()
  window.removeEventListener('resize', refreshLayout)
  resizeObserver?.disconnect()
  resizeObserver = null
  observedContainer = null
})

function refreshLayout(): void {
  if (!mounted) {
    return
  }

  visible.value =
    window.matchMedia(
      `(min-width: ${configuration.minimumViewport}px)`
    ).matches && layoutSurfaceExists()
  maximumWidth.value = calculateMaximumWidth()
  applyPreferredWidth()
}

function layoutSurfaceExists(): boolean {
  if (props.kind === 'navigation') {
    return document.querySelector('.VPSidebar') !== null
  }
  return (
    document.querySelector(
      '.VPDoc.has-aside .aside:not(.left-aside)'
    ) !== null
  )
}

function calculateMaximumWidth(): number {
  if (props.kind === 'navigation') {
    /*
     * Below the centered 1440px layout, reserve enough room for either the
     * document alone or VitePress's 640px document, 256px outline, and 64px
     * document padding. The wider centered layout safely permits the cap.
     */
    let available = configuration.maximumWidth
    if (window.innerWidth < 1280) {
      available = window.innerWidth - 580
    } else if (window.innerWidth < 1440) {
      available = window.innerWidth - 960
    }
    return clamp(
      Math.floor(available),
      configuration.minimumWidth,
      configuration.maximumWidth
    )
  }

  const container = document.querySelector<HTMLElement>('.VPDoc .container')
  // Keep VitePress's documented 640px minimum content column intact.
  const available = (container?.getBoundingClientRect().width ?? 896) - 640
  return clamp(
    Math.floor(available),
    configuration.minimumWidth,
    configuration.maximumWidth
  )
}

function observeOutlineContainer(): void {
  if (props.kind !== 'outline' || resizeObserver === null) {
    return
  }

  const container = document.querySelector('.VPDoc .container')
  if (container === observedContainer) {
    return
  }

  resizeObserver.disconnect()
  observedContainer = container
  if (observedContainer !== null) {
    resizeObserver.observe(observedContainer)
  }
}

function applyPreferredWidth(): void {
  const nextWidth = clamp(
    preferredWidth,
    configuration.minimumWidth,
    maximumWidth.value
  )
  width.value = nextWidth

  if (
    usingRepositoryDefault &&
    nextWidth === configuration.defaultWidth
  ) {
    document.documentElement.style.removeProperty(
      configuration.cssProperty
    )
    return
  }

  document.documentElement.style.setProperty(
    configuration.cssProperty,
    `${nextWidth}px`
  )
}

function chooseWidth(nextWidth: number): void {
  usingRepositoryDefault = false
  preferredWidth = clamp(
    Math.round(nextWidth),
    configuration.minimumWidth,
    maximumWidth.value
  )
  applyPreferredWidth()
  writeStoredWidth(preferredWidth)
}

function resetWidth(): void {
  usingRepositoryDefault = true
  preferredWidth = configuration.defaultWidth
  removeStoredWidth()
  applyPreferredWidth()
}

function startDragging(event: PointerEvent): void {
  if (event.button !== 0 || !event.isPrimary) {
    return
  }

  event.preventDefault()
  activePointerId = event.pointerId
  startPointerX = event.clientX
  startWidth = width.value
  dragging.value = true
  handle.value?.focus()
  handle.value?.setPointerCapture(event.pointerId)
  document.documentElement.classList.add('be-sidebar-resizing')
  window.addEventListener('pointermove', continueDragging, {
    passive: false
  })
  window.addEventListener('pointerup', finishDragging)
  window.addEventListener('pointercancel', finishDragging)
}

function continueDragging(event: PointerEvent): void {
  if (event.pointerId !== activePointerId) {
    return
  }

  event.preventDefault()
  const direction = props.kind === 'navigation' ? 1 : -1
  preferredWidth = clamp(
    startWidth + direction * (event.clientX - startPointerX),
    configuration.minimumWidth,
    maximumWidth.value
  )
  usingRepositoryDefault = false
  applyPreferredWidth()
}

function finishDragging(event: PointerEvent): void {
  if (event.pointerId !== activePointerId) {
    return
  }

  writeStoredWidth(preferredWidth)
  stopDragging()
}

function stopDragging(): void {
  if (
    activePointerId !== null &&
    handle.value?.hasPointerCapture(activePointerId)
  ) {
    handle.value.releasePointerCapture(activePointerId)
  }

  activePointerId = null
  dragging.value = false
  document.documentElement.classList.remove('be-sidebar-resizing')
  window.removeEventListener('pointermove', continueDragging)
  window.removeEventListener('pointerup', finishDragging)
  window.removeEventListener('pointercancel', finishDragging)
}

function handleKeydown(event: KeyboardEvent): void {
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      chooseWidth(width.value - keyboardStep)
      break
    case 'ArrowRight':
      event.preventDefault()
      chooseWidth(width.value + keyboardStep)
      break
    case 'Home':
      event.preventDefault()
      resetWidth()
      break
    case 'End':
      event.preventDefault()
      chooseWidth(maximumWidth.value)
      break
  }
}

function readStoredWidth(): number | null {
  try {
    const stored = window.localStorage.getItem(configuration.storageKey)
    if (stored === null) {
      return null
    }

    const parsed = Number(stored)
    if (
      Number.isFinite(parsed) &&
      parsed >= configuration.minimumWidth &&
      parsed <= configuration.maximumWidth
    ) {
      return Math.round(parsed)
    }

    window.localStorage.removeItem(configuration.storageKey)
    return null
  } catch (error) {
    console.warn(
      `Unable to restore ${props.kind} sidebar width from localStorage.`,
      error
    )
    return null
  }
}

function writeStoredWidth(nextWidth: number): void {
  try {
    window.localStorage.setItem(
      configuration.storageKey,
      String(Math.round(nextWidth))
    )
  } catch (error) {
    console.warn(
      `Unable to persist ${props.kind} sidebar width to localStorage.`,
      error
    )
  }
}

function removeStoredWidth(): void {
  try {
    window.localStorage.removeItem(configuration.storageKey)
  } catch (error) {
    console.warn(
      `Unable to reset ${props.kind} sidebar width in localStorage.`,
      error
    )
  }
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(Math.max(value, minimum), maximum)
}
</script>

<template>
  <div
    v-if="visible"
    ref="handle"
    class="be-sidebar-resizer"
    :class="[
      `be-sidebar-resizer--${kind}`,
      { 'is-dragging': dragging }
    ]"
    role="separator"
    aria-orientation="vertical"
    :aria-label="configuration.label"
    :aria-describedby="instructionsId"
    :aria-valuemin="configuration.minimumWidth"
    :aria-valuemax="maximumWidth"
    :aria-valuenow="width"
    :aria-valuetext="valueText"
    aria-keyshortcuts="ArrowLeft ArrowRight Home End"
    tabindex="0"
    :title="`${configuration.label}; double-click to reset`"
    :data-sidebar-resizer="kind"
    :data-storage-key="configuration.storageKey"
    @dblclick="resetWidth"
    @keydown="handleKeydown"
    @pointerdown="startDragging"
  >
    <span :id="instructionsId" class="visually-hidden">
      Drag horizontally, use Left and Right Arrow keys, or press Home to
      restore the repository default width.
    </span>
  </div>
</template>
