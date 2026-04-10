import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";

import { discardTile, getGameActions, getGameState, passAction, ron, tsumo } from "../../api/games";
import { getStoredToken } from "../../lib/token";
import { useUiStore } from "../../stores/ui";
import type { GameActions, GameState } from "../../types/api";
import { MajSocket } from "../../ws/majsocket";
import { getTileSpritePosition } from "./tileSprite";

const seatOrder = [2, 3, 1, 0] as const;

type SeatDisplay = {
  seat: number;
  player: GameState["players"][number] | null;
  score: number;
};

export function useGameView() {
  const route = useRoute();
  const ui = useUiStore();

  const gameId = computed(() => Number(route.params.id));
  const state = ref<GameState | null>(null);
  const actions = ref<GameActions | null>(null);
  const selectedIndex = ref<number | null>(null);
  const loading = ref(false);

  const socket = new MajSocket({
    onMessage(event) {
      if (event.type.startsWith("game_")) {
        void refreshGame();
      }
    },
  });

  const myHand = computed(() => state.value?.my_hand || []);
  const mySeat = computed(() => state.value?.my_seat);

  const selectedTile = computed(() => {
    if (selectedIndex.value === null) {
      return "";
    }
    return myHand.value[selectedIndex.value] || "";
  });

  const playersBySeat = computed(() => {
    const map = new Map<number, GameState["players"][number]>();
    for (const player of state.value?.players || []) {
      map.set(player.seat, player);
    }
    return map;
  });

  const displaySeats = computed<SeatDisplay[]>(() =>
    seatOrder.map((seat) => ({
      seat,
      player: playersBySeat.value.get(seat) || null,
      score: state.value?.scores?.[seat] ?? 0,
    })),
  );

  const topSeat = computed(() => displaySeats.value.find((item) => item.seat === 2));
  const leftSeat = computed(() => displaySeats.value.find((item) => item.seat === 3));
  const rightSeat = computed(() => displaySeats.value.find((item) => item.seat === 1));
  const bottomSeat = computed(() => displaySeats.value.find((item) => item.seat === 0));

  function seatName(seat: number, userId: number | undefined, nickname: string | undefined): string {
    if (seat === mySeat.value) {
      return "你";
    }
    if (!userId) {
      return `座位 ${seat}`;
    }
    return userId < 0 ? nickname || `BOT-${seat}` : `玩家 ${userId}`;
  }

  function parseTile(tile: string): { bgPos: string } {
    return { bgPos: getTileSpritePosition(tile) };
  }

  async function refreshGame(): Promise<void> {
    loading.value = true;
    try {
      const [nextState, nextActions] = await Promise.all([
        getGameState(gameId.value),
        getGameActions(gameId.value),
      ]);
      state.value = nextState;
      actions.value = nextActions;

      if (myHand.value.length === 0) {
        selectedIndex.value = null;
      } else if (
        selectedIndex.value === null ||
        selectedIndex.value < 0 ||
        selectedIndex.value >= myHand.value.length
      ) {
        selectedIndex.value = 0;
      }
    } catch (error) {
      ui.push(error instanceof Error ? error.message : "加载对局失败", "error");
    } finally {
      loading.value = false;
    }
  }

  async function doDiscard(): Promise<void> {
    if (selectedIndex.value === null || !selectedTile.value) {
      ui.push("请先选择一张要打出的牌", "warning");
      return;
    }

    try {
      await discardTile(gameId.value, selectedTile.value);
      await refreshGame();
    } catch (error) {
      ui.push(error instanceof Error ? error.message : "出牌失败", "error");
    }
  }

  async function doTsumo(): Promise<void> {
    try {
      await tsumo(gameId.value);
      await refreshGame();
    } catch (error) {
      ui.push(error instanceof Error ? error.message : "自摸失败", "error");
    }
  }

  async function doRon(): Promise<void> {
    try {
      await ron(gameId.value);
      await refreshGame();
    } catch (error) {
      ui.push(error instanceof Error ? error.message : "荣和失败", "error");
    }
  }

  async function doPass(): Promise<void> {
    try {
      await passAction(gameId.value);
      await refreshGame();
    } catch (error) {
      ui.push(error instanceof Error ? error.message : "过牌失败", "error");
    }
  }

  onMounted(() => {
    const token = getStoredToken();
    if (token) {
      socket.connect(token);
    }
    void refreshGame();
  });

  onUnmounted(() => {
    socket.disconnect();
  });

  return {
    gameId,
    state,
    actions,
    loading,
    mySeat,
    myHand,
    topSeat,
    leftSeat,
    rightSeat,
    bottomSeat,
    selectedIndex,
    parseTile,
    seatName,
    refreshGame,
    doDiscard,
    doTsumo,
    doRon,
    doPass,
  };
}
