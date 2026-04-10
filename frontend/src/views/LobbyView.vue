<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { useRoomStore } from "../stores/rooms";
import { useUiStore } from "../stores/ui";

const roomStore = useRoomStore();
const ui = useUiStore();
const router = useRouter();

const roomName = ref("春风雅局");
const maxPlayers = ref(4);

onMounted(async () => {
  try {
    await roomStore.loadRooms();
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "加载房间失败", "error");
  }
});

async function createRoomAndEnter(): Promise<void> {
  try {
    const room = await roomStore.createAndEnter(roomName.value, maxPlayers.value);
    const id = Number(room.room_id ?? room.id);
    if (!id) {
      ui.push("后端未返回房间 ID", "error");
      return;
    }
    ui.push("房间创建成功", "success");
    await router.push({ name: "room", params: { id } });
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "创建房间失败", "error");
  }
}

async function enterRoom(roomId?: number): Promise<void> {
  if (!roomId) {
    ui.push("无效房间 ID", "error");
    return;
  }
  await router.push({ name: "room", params: { id: roomId } });
}
</script>

<template>
  <section class="grid gap-4">
    <div class="paper-card">
      <div class="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 class="m-0 text-3xl font-semibold text-ink-900">雀局大厅</h1>
          <p class="mt-2 text-sm text-ink-700/80">创建新房间，或加入正在等待开局的牌桌。</p>
        </div>
        <span class="status-chip">经典四人场 · BOT可补位</span>
      </div>

      <div class="grid grid-cols-1 items-end gap-3 md:grid-cols-[1.2fr_0.6fr_auto]">
        <label class="grid gap-1 text-sm text-ink-700">
          <span>房间名</span>
          <input v-model.trim="roomName" class="ink-input" type="text" maxlength="100" />
        </label>
        <label class="grid gap-1 text-sm text-ink-700">
          <span>人数</span>
          <select v-model.number="maxPlayers" class="ink-input">
            <option :value="4">4 人</option>
          </select>
        </label>
        <button class="ink-btn-primary" type="button" @click="createRoomAndEnter">创建并进入</button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
      <article
        v-for="room in roomStore.rooms"
        :key="room.room_id ?? room.id"
        class="paper-card group transition duration-300 hover:-translate-y-1"
      >
        <header class="mb-3 flex items-center justify-between gap-2">
          <h3 class="m-0 text-lg text-ink-900">{{ room.name || `房间 #${room.room_id ?? room.id}` }}</h3>
          <span class="rounded-full border border-jade-600/30 bg-jade-500/10 px-2 py-0.5 text-xs text-jade-600">
            {{ room.status || "waiting" }}
          </span>
        </header>
        <p class="m-0 text-sm text-ink-700">房主：{{ room.owner_id || "未知" }}</p>
        <p class="mb-4 mt-2 text-sm text-ink-700">人数：{{ room.max_players || 4 }} / 4</p>
        <button class="ink-btn-ghost" type="button" @click="enterRoom(Number(room.room_id ?? room.id))">
          查看并加入
        </button>
      </article>

      <article v-if="roomStore.rooms.length === 0" class="paper-card">
        <h3 class="m-0 text-xl text-ink-900">当前没有房间</h3>
        <p class="mb-0 mt-2 text-sm text-ink-700">先创建一个“春风雅局”试试。</p>
      </article>
    </div>
  </section>
</template>
