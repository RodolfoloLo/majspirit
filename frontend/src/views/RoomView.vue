<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";
import { useRoomStore } from "../stores/rooms";
import { useUiStore } from "../stores/ui";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const roomStore = useRoomStore();
const ui = useUiStore();

const roomId = computed(() => Number(route.params.id));
const players = computed(() => roomStore.currentRoom?.players || []);
const me = computed(() => players.value.find((p) => p.user_id === auth.user?.id));

onMounted(async () => {
  try {
    await roomStore.loadRoom(roomId.value);
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "加载房间失败", "error");
  }
});

async function joinAtSeat(seat: number): Promise<void> {
  try {
    await roomStore.join(roomId.value, seat);
    ui.push(`已入座 ${seat} 号位`, "success");
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "入座失败", "error");
  }
}

async function toggleReady(): Promise<void> {
  if (!me.value) return;
  try {
    await roomStore.ready(roomId.value, !me.value.ready);
    ui.push(me.value.ready ? "已取消准备" : "已准备", "info");
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "准备状态更新失败", "error");
  }
}

async function doStart(): Promise<void> {
  try {
    const result = await roomStore.start(roomId.value);
    ui.push("开局指令已发送", "success");
    if (result?.game_id) {
      await router.push({ name: "game", params: { id: result.game_id } });
    }
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "开局失败", "error");
  }
}

async function leaveRoomNow(): Promise<void> {
  try {
    await roomStore.leave(roomId.value);
    ui.push("你已离开房间", "warning");
    await router.push({ name: "lobby" });
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "离开失败", "error");
  }
}
</script>

<template>
  <section class="room-page">
    <article class="card room-head">
      <h1>{{ roomStore.currentRoom?.name || `房间 #${roomId}` }}</h1>
      <p>状态：{{ roomStore.currentRoom?.status || "waiting" }}</p>
      <div class="room-actions">
        <button class="ghost" type="button" @click="leaveRoomNow">离开房间</button>
        <button class="primary" type="button" @click="toggleReady" :disabled="!me">
          {{ me?.ready ? "取消准备" : "我已准备" }}
        </button>
        <button class="primary" type="button" @click="doStart">开始对局</button>
      </div>
    </article>

    <div class="seat-grid">
      <article v-for="seat in [0, 1, 2, 3]" :key="seat" class="seat card">
        <h3>{{ seat }} 号位</h3>
        <template v-if="players.find((p) => p.seat === seat)">
          <p>玩家 ID：{{ players.find((p) => p.seat === seat)?.user_id }}</p>
          <p>
            状态：{{ players.find((p) => p.seat === seat)?.ready ? "已准备" : "未准备" }}
          </p>
        </template>
        <template v-else>
          <p>空位</p>
          <button class="ghost" type="button" @click="joinAtSeat(seat)">入座</button>
        </template>
      </article>
    </div>
  </section>
</template>
