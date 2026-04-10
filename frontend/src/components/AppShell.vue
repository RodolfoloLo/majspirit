<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const showNav = computed(() => route.name !== "auth");

async function logout(): Promise<void> {
  await auth.logout();
  void router.push({ name: "auth" });
}
</script>

<template>
  <div class="min-h-screen text-ink-900">
    <header
      v-if="showNav"
      class="sticky top-0 z-30 border-b border-rice-100/15 bg-gradient-to-r from-ink-900/90 to-ink-700/85 px-5 py-3 text-rice-100 backdrop-blur"
    >
      <div class="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-3">
        <div class="flex items-end gap-3">
          <span class="font-brush text-4xl leading-none tracking-[0.12em]">雀灵麻将</span>
          <span class="pb-1 text-sm font-semibold text-brass-400">MajSpirit</span>
        </div>
        <nav class="flex items-center gap-2 text-sm">
          <RouterLink
            to="/lobby"
            class="rounded-full border px-3 py-1.5 transition"
            :class="route.name === 'lobby'
              ? 'border-rice-100/35 bg-rice-100/15'
              : 'border-transparent hover:border-rice-100/30 hover:bg-rice-100/10'"
          >
            雀局大厅
          </RouterLink>
          <RouterLink
            to="/history"
            class="rounded-full border px-3 py-1.5 transition"
            :class="route.name === 'history'
              ? 'border-rice-100/35 bg-rice-100/15'
              : 'border-transparent hover:border-rice-100/30 hover:bg-rice-100/10'"
          >
            牌谱战绩
          </RouterLink>
        </nav>
        <div class="flex items-center gap-2">
          <span class="rounded-full border border-rice-100/20 bg-rice-100/10 px-3 py-1 text-xs text-rice-100">
            {{ auth.user?.nickname || auth.user?.email || "游客" }}
          </span>
          <button type="button" class="ink-btn-danger" @click="logout">退出</button>
        </div>
      </div>
    </header>

    <main class="mx-auto w-full max-w-7xl px-3 py-4 sm:px-5">
      <RouterView v-slot="{ Component }">
        <Transition name="view-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>
