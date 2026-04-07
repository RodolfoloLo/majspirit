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
  <section class="lobby-page">
    <div class="hero-panel card">
      <h1>雀局大厅</h1>
      <p>创建新房间，或加入正在等待开局的牌桌。推荐四人满员后统一点击准备。</p>
      <div class="hero-actions">
        <label>
          房间名
          <input v-model.trim="roomName" type="text" maxlength="100" />
        </label>
        <label>
          人数
          <select v-model.number="maxPlayers">
            <option :value="2">2 人</option>
            <option :value="3">3 人</option>
            <option :value="4">4 人</option>
          </select>
        </label>
        <button class="primary" type="button" @click="createRoomAndEnter">创建并进入</button>
      </div>
    </div>

    <div class="room-grid">
      <article v-for="room in roomStore.rooms" :key="room.room_id ?? room.id" class="room-card card">
        <header>
          <h3>{{ room.name || `房间 #${room.room_id ?? room.id}` }}</h3>
          <span class="status">{{ room.status || "waiting" }}</span>
        </header>
        <p>房主：{{ room.owner_id || "未知" }}</p>
        <p>人数：{{ room.max_players || 4 }} / 4</p>
        <button class="ghost" type="button" @click="enterRoom(Number(room.room_id ?? room.id))">
          查看并加入
        </button>
      </article>

      <article v-if="roomStore.rooms.length === 0" class="room-card card empty">
        <h3>当前没有房间</h3>
        <p>先创建一个“春风雅局”试试。</p>
      </article>
    </div>
  </section>
</template>
