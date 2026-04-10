<script setup lang="ts">
import { useUiStore } from "../../stores/ui";

const ui = useUiStore();
</script>

<template>
  <div class="fixed right-4 top-4 z-50 grid w-[min(340px,calc(100vw-2rem))] gap-2" aria-live="polite">
    <transition-group name="toast">
      <article
        v-for="notice in ui.notices"
        :key="notice.id"
        class="flex items-start justify-between gap-3 rounded-2xl border px-3 py-2 text-sm shadow-lg backdrop-blur"
        :class="{
          'border-emerald-700/35 bg-emerald-50/95 text-emerald-700': notice.level === 'success',
          'border-jade-600/35 bg-rice-50/95 text-jade-600': notice.level === 'info',
          'border-amber-700/35 bg-amber-50/95 text-amber-700': notice.level === 'warning',
          'border-cinnabar-600/35 bg-rose-50/95 text-cinnabar-600': notice.level === 'error',
        }"
      >
        <p class="m-0 leading-5">{{ notice.text }}</p>
        <button type="button" class="rounded-lg px-2 py-1 text-xs hover:bg-black/5" @click="ui.remove(notice.id)">
          关闭
        </button>
      </article>
    </transition-group>
  </div>
</template>
