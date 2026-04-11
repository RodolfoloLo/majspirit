<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getMatchDetail, getMyHistory } from "../api/history";
import type { HistoryItem, MatchDetailResponse } from "../types/api";
import { useUiStore } from "../stores/ui";

const ui = useUiStore();
const items = ref<HistoryItem[]>([]);
const page = ref(1);
const size = ref(20);
const loading = ref(false);
const detail = ref<MatchDetailResponse | null>(null);
const detailLoading = ref(false);

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

async function openDetail(matchId: number): Promise<void> {
  detailLoading.value = true;
  try {
    detail.value = await getMatchDetail(matchId);
  } catch (error) {
    ui.push(error instanceof Error ? error.message : "加载牌局详情失败", "error");
  } finally {
    detailLoading.value = false;
  }
}

function seatLabel(seat: number): string {
  const rankItem = detail.value?.detail.ranking.find((item) => item.seat === seat);
  if (!rankItem) {
    return `座位${seat}`;
  }
  if (rankItem.is_bot) {
    return rankItem.nickname || `BOT-${seat}`;
  }
  return `玩家${rankItem.user_id}`;
}

function roundOutcomeText(round: MatchDetailResponse["detail"]["rounds"][number]): string {
  const result = round.result;
  if (!result || typeof result.type !== "string") {
    return "本局结果缺失";
  }

  if (result.type === "draw") {
    return "平局（流局）";
  }

  if (result.type === "tsumo") {
    const winnerSeat = Number(result.winner_seat);
    return `${seatLabel(winnerSeat)} 自摸`;
  }

  if (result.type === "ron") {
    const winnerSeat = Number(result.winner_seat);
    const loserSeat = Number(result.loser_seat);
    return `${seatLabel(winnerSeat)} 荣和（放铳：${seatLabel(loserSeat)}）`;
  }

  return "本局结束";
}
</script>

<template>
  <section class="paper-card">
    <header class="mb-4 flex items-center justify-between gap-3">
      <h1 class="m-0 text-2xl font-semibold text-ink-900">牌谱与战绩</h1>
      <button class="ink-btn-ghost" type="button" @click="loadHistory" :disabled="loading">
        {{ loading ? "刷新中..." : "刷新" }}
      </button>
    </header>

    <div class="overflow-x-auto" v-if="items.length">
      <table class="w-full min-w-[700px] border-collapse text-sm">
      <thead>
        <tr>
          <th class="border-b border-jade-600/20 px-3 py-2 text-left">对局</th>
          <th class="border-b border-jade-600/20 px-3 py-2 text-left">名次</th>
          <th class="border-b border-jade-600/20 px-3 py-2 text-left">终局分</th>
          <th class="border-b border-jade-600/20 px-3 py-2 text-left">分差</th>
          <th class="border-b border-jade-600/20 px-3 py-2 text-left">完成时间</th>
          <th class="border-b border-jade-600/20 px-3 py-2 text-left">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.match_id">
          <td class="border-b border-jade-600/10 px-3 py-2">#{{ item.match_id }}</td>
          <td class="border-b border-jade-600/10 px-3 py-2">{{ item.rank }}</td>
          <td class="border-b border-jade-600/10 px-3 py-2">{{ item.final_score }}</td>
          <td class="border-b border-jade-600/10 px-3 py-2">{{ item.score_delta > 0 ? `+${item.score_delta}` : item.score_delta }}</td>
          <td class="border-b border-jade-600/10 px-3 py-2">{{ item.finished_at || "--" }}</td>
          <td class="border-b border-jade-600/10 px-3 py-2">
            <button class="ink-btn-ghost" type="button" @click="openDetail(item.match_id)">查看详情</button>
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <div v-else class="rounded-2xl border border-dashed border-jade-600/25 bg-rice-50/70 px-4 py-5 text-sm text-ink-700">
      还没有历史牌局。先去大厅打一把吧。
    </div>

    <article v-if="detail" class="paper-card mt-4">
      <header class="flex items-center justify-between gap-3">
        <h2 class="m-0 text-lg font-semibold text-ink-900">对局 #{{ detail.match_id }} 详情</h2>
        <span class="text-xs text-ink-700/80">房间 {{ detail.room_id }}</span>
      </header>
      <p class="mb-0 mt-3 text-sm text-ink-800">终局排名：
        <span v-for="r in detail.detail.ranking" :key="`${detail.match_id}-${r.seat}`">
          [{{ r.rank }}位:{{ r.is_bot ? (r.nickname || "BOT") : `玩家${r.user_id}` }}({{ r.final_score }})]
        </span>
      </p>
      <div v-if="detailLoading" class="mt-3 text-sm text-ink-700">加载中...</div>
      <div class="mt-3 grid gap-3">
        <article
          v-for="round in detail.detail.rounds"
          :key="round.round_index"
          class="rounded-2xl border border-jade-600/20 bg-rice-50/80 p-3"
        >
          <h3 class="m-0 text-base text-ink-900">第 {{ round.round_index }} 小局 · 庄家 {{ round.dealer_seat }}</h3>
          <p class="mb-0 mt-2 text-sm text-ink-700">结果：{{ roundOutcomeText(round) }}</p>
        </article>
      </div>
    </article>
  </section>
</template>
