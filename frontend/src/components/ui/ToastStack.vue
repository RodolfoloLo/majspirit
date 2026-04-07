<script setup lang="ts">
import { useUiStore } from "../../stores/ui";

const ui = useUiStore();
</script>

<template>
  <div class="toast-stack" aria-live="polite">
    <transition-group name="toast">
      <article
        v-for="notice in ui.notices"
        :key="notice.id"
        class="toast-item"
        :class="`toast-${notice.level}`"
      >
        <p>{{ notice.text }}</p>
        <button type="button" @click="ui.remove(notice.id)">关闭</button>
      </article>
    </transition-group>
  </div>
</template>
