<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";

import { MajSocket } from "../ws/majsocket";
import { getStoredToken } from "../lib/token";
import type { WsEvent } from "../types/api";

const route = useRoute();
const gameId = computed(() => Number(route.params.id));
const wsLogs = ref<WsEvent[]>([]);

const socket = new MajSocket({
  onMessage(event) {
    wsLogs.value.unshift(event);
    if (wsLogs.value.length > 50) wsLogs.value.length = 50;
  },
});

onMounted(() => {
  const token = getStoredToken();
  if (token) {
    socket.connect(token);
  }
});

onUnmounted(() => {
  socket.disconnect();
});
</script>

<template>
  <section class="game-page">
    <article class="card">
      <h1>对局进行中 · #{{ gameId }}</h1>
      <p>这里展示实时事件流。后续可扩展手牌渲染、摸打动画和断线重连状态恢复。</p>
    </article>

    <article class="card logs">
      <h2>WebSocket 事件</h2>
      <ul>
        <li v-for="(log, idx) in wsLogs" :key="`${log.type}-${log.ts}-${idx}`">
          <strong>{{ log.type }}</strong>
          <span>{{ log.ts }}</span>
        </li>
      </ul>
    </article>
  </section>
</template>
