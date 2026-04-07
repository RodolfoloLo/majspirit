<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getMyHistory } from "../api/history";
import type { HistoryItem } from "../types/api";
import { useUiStore } from "../stores/ui";

const ui = useUiStore();
const items = ref<HistoryItem[]>([]);
const page = ref(1);
const size = ref(20);
const loading = ref(false);

async function loadHistory(): Promise<void> {
  loading.value = true;
  try {
    const result = await getMyHistory(page.value, size.value);
    items.value = result.items;
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "加载战绩失败", "error");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadHistory();
});
</script>

<template>
  <section class="history-page card">
    <header class="history-head">
      <h1>牌谱与战绩</h1>
      <button class="ghost" type="button" @click="loadHistory" :disabled="loading">
        {{ loading ? "刷新中..." : "刷新" }}
      </button>
    </header>

    <table class="history-table" v-if="items.length">
      <thead>
        <tr>
          <th>对局</th>
          <th>名次</th>
          <th>终局分</th>
          <th>分差</th>
          <th>完成时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.match_id">
          <td>#{{ item.match_id }}</td>
          <td>{{ item.rank }}</td>
          <td>{{ item.final_score }}</td>
          <td>{{ item.score_delta > 0 ? `+${item.score_delta}` : item.score_delta }}</td>
          <td>{{ item.finished_at || "--" }}</td>
        </tr>
      </tbody>
    </table>

    <div v-else class="empty-state">
      <p>还没有历史牌局。先去大厅打一把吧。</p>
    </div>
  </section>
</template>
