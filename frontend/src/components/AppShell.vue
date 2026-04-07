<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const showNav = computed(() => route.name !== "auth");

function logout(): void {
  auth.logout();
  void router.push({ name: "auth" });
}
</script>

<template>
  <div class="app-shell">
    <header v-if="showNav" class="topbar">
      <div class="brand">
        <span class="brand-zh">麻将灵境</span>
        <span class="brand-en">MajSpirit</span>
      </div>
      <nav class="nav-links">
        <RouterLink to="/lobby">雀局大厅</RouterLink>
        <RouterLink to="/history">牌谱战绩</RouterLink>
      </nav>
      <div class="user-pane">
        <span class="chip">{{ auth.user?.nickname || auth.user?.email || "游客" }}</span>
        <button type="button" class="danger" @click="logout">退出</button>
      </div>
    </header>

    <main class="page-wrap">
      <RouterView />
    </main>
  </div>
</template>
