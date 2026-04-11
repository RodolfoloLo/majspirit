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

type EffectKind = "win" | "match_end";

type ActionPayload = {
  event_type?: string;
  events?: Array<{ event_type?: string }>;
};

const HONOR_ORDER: Record<string, number> = {
  east: 1,
  south: 2,
  west: 3,
  north: 4,
  red: 5,
  green: 6,
  white: 7,
};

const SUIT_ORDER: Record<string, number> = {
  m: 1,
  s: 2,
  p: 3,
};

function tileSortKey(tile: string): [number, number] {
  const basic = /^([msp])(\d)$/.exec(tile);
  if (basic) {
    return [SUIT_ORDER[basic[1]], Number.parseInt(basic[2], 10)];
  }
  return [4, HONOR_ORDER[tile] ?? 99];
}

export function useGameView() {
  const route = useRoute();
  const ui = useUiStore();

  const gameId = computed(() => Number(route.params.id));
  const state = ref<GameState | null>(null);
  const actions = ref<GameActions | null>(null);
  const selectedIndex = ref<number | null>(null);
  const loading = ref(false);
  const effect = ref<{ kind: EffectKind; text: string; seed: number } | null>(null);

  let effectTimer: ReturnType<typeof setTimeout> | null = null;

  function triggerEffect(kind: EffectKind): void {
    if (effectTimer) {
      clearTimeout(effectTimer);
    }

    effect.value = {
      kind,
      text: kind === "match_end" ? "对局结束" : "和牌!",
      seed: Date.now(),
    };

    effectTimer = setTimeout(() => {
      effect.value = null;
      effectTimer = null;
    }, 1700);
  }

  function applyEffectFromPayload(payload: unknown): void {
    const data = payload as ActionPayload;
    const eventTypes = new Set<string>();

    if (data?.event_type) {
      eventTypes.add(data.event_type);
    }

    for (const item of data?.events || []) {
      if (item?.event_type) {
        eventTypes.add(item.event_type);
      }
    }

    if (eventTypes.has("game_match_end")) {
      triggerEffect("match_end");
      return;
    }

    if (eventTypes.has("game_win")) {
      triggerEffect("win");
    }
  }

  const socket = new MajSocket({
    onMessage(event) {
      if (event.type === "game_match_end") {
        triggerEffect("match_end");
      } else if (event.type === "game_win") {
        triggerEffect("win");
      }

      if (event.type.startsWith("game_")) {
        void refreshGame();
      }
    },
  });

  const myHand = computed(() => {
    const hand = state.value?.my_hand || [];
    return [...hand].sort((a, b) => {
      const [aGroup, aRank] = tileSortKey(a);
      const [bGroup, bRank] = tileSortKey(b);

      if (aGroup !== bGroup) {
        return aGroup - bGroup;
      }

      return aRank - bRank;
    });
  });
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
      const result = await discardTile(gameId.value, selectedTile.value);
      applyEffectFromPayload(result);
      await refreshGame();
    } catch (error) {
      ui.push(error instanceof Error ? error.message : "出牌失败", "error");
    }
  }

  async function doTsumo(): Promise<void> {
    try {
      const result = await tsumo(gameId.value);
      applyEffectFromPayload(result);
      await refreshGame();
    } catch (error) {
      ui.push(error instanceof Error ? error.message : "自摸失败", "error");
    }
  }

  async function doRon(): Promise<void> {
    try {
      const result = await ron(gameId.value);
      applyEffectFromPayload(result);
      await refreshGame();
    } catch (error) {
      ui.push(error instanceof Error ? error.message : "荣和失败", "error");
    }
  }

  async function doPass(): Promise<void> {
    try {
      const result = await passAction(gameId.value);
      applyEffectFromPayload(result);
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
    if (effectTimer) {
      clearTimeout(effectTimer);
      effectTimer = null;
    }
    socket.disconnect();
  });

  return {
    gameId,
    state,
    actions,
    effect,
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
