<script setup lang="ts">
import { useGameView } from "../features/game/useGameView";

const {
  actions,
  bottomSeat,
  doDiscard,
  doPass,
  doRon,
  doTsumo,
  effect,
  gameId,
  leftSeat,
  loading,
  myHand,
  mySeat,
  parseTile,
  refreshGame,
  rightSeat,
  seatName,
  selectedIndex,
  state,
  topSeat,
} = useGameView();
</script>

<template>
  <section class="grid gap-4">
    <article class="paper-card">
      <div class="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 class="m-0 font-brush text-5xl text-cinnabar-600">MajSpirit</h1>
          <p class="mb-0 mt-1 text-sm text-ink-700/85">
            对局 #{{ gameId }} · 第 {{ state?.round_index || "-" }} 小局
          </p>
        </div>
        <button
          class="ink-btn-ghost"
          type="button"
          @click="refreshGame"
          :disabled="loading"
        >
          {{ loading ? "刷新中..." : "刷新状态" }}
        </button>
      </div>

      <div class="mahjong-table p-3 sm:p-5" v-if="state">
        <div
          class="absolute left-1/2 top-4 z-20 -translate-x-1/2 rounded-full border border-rice-100/30 bg-ink-900/60 px-4 py-1 text-xs text-rice-100 backdrop-blur"
        >
          当前出牌位 {{ state.turn_seat }} · 状态 {{ state.status }}
        </div>

        <Transition name="result-burst">
          <div
            v-if="effect"
            :key="effect.seed"
            class="round-effect-overlay"
            :class="effect.kind === 'match_end' ? 'match-end' : 'win'"
          >
            <div class="round-effect-text">{{ effect.text }}</div>
          </div>
        </Transition>

        <div class="grid h-full w-full grid-cols-3 grid-rows-3 gap-2 sm:gap-4">
          <div
            class="col-start-2 row-start-1 flex flex-col items-center justify-start gap-2 pt-6"
          >
            <div class="seat-panel w-full max-w-[430px] text-center text-xs">
              <div class="font-semibold">
                {{
                  seatName(
                    2,
                    topSeat?.player?.user_id,
                    topSeat?.player?.nickname,
                  )
                }}（2）
              </div>
              <div class="mt-1 text-rice-100/85">
                分数 {{ topSeat?.score || 0 }}
              </div>
            </div>
            <div class="flex flex-wrap justify-center gap-1">
              <div
                v-for="index in topSeat?.player?.hand_count || 0"
                :key="`top-hand-${index}`"
                class="tile-back h-10 w-7"
              ></div>
            </div>
            <TransitionGroup
              name="discard"
              tag="div"
              class="flex max-w-[420px] flex-wrap justify-center gap-1"
            >
              <div
                v-for="(tile, idx) in topSeat?.player?.discards || []"
                :key="`top-discard-${idx}-${tile}`"
                class="tile-face h-9 w-7 text-xs"
              >
                <div class="mahjong-sprite" :style="{ backgroundPosition: parseTile(tile).bgPos }"></div>
              </div>
            </TransitionGroup>
          </div>

          <div
            class="col-start-1 row-start-2 flex flex-col items-start justify-center gap-2 pl-1 sm:pl-4"
          >
            <div class="seat-panel text-xs">
              <div class="font-semibold">
                {{
                  seatName(
                    3,
                    leftSeat?.player?.user_id,
                    leftSeat?.player?.nickname,
                  )
                }}（3）
              </div>
              <div class="mt-1 text-rice-100/85">
                分数 {{ leftSeat?.score || 0 }}
              </div>
            </div>
            <div class="flex flex-col gap-1">
              <div
                v-for="index in leftSeat?.player?.hand_count || 0"
                :key="`left-hand-${index}`"
                class="tile-back h-7 w-10"
              ></div>
            </div>
            <TransitionGroup
              name="discard"
              tag="div"
              class="grid grid-cols-2 gap-1"
            >
              <div
                v-for="(tile, idx) in leftSeat?.player?.discards || []"
                :key="`left-discard-${idx}-${tile}`"
                class="tile-face h-9 w-7 text-xs"
              >
                <div class="mahjong-sprite" :style="{ backgroundPosition: parseTile(tile).bgPos }"></div>
              </div>
            </TransitionGroup>
          </div>

          <div
            class="col-start-3 row-start-2 flex flex-col items-end justify-center gap-2 pr-1 sm:pr-4"
          >
            <div class="seat-panel text-xs">
              <div class="font-semibold">
                {{
                  seatName(
                    1,
                    rightSeat?.player?.user_id,
                    rightSeat?.player?.nickname,
                  )
                }}（1）
              </div>
              <div class="mt-1 text-rice-100/85">
                分数 {{ rightSeat?.score || 0 }}
              </div>
            </div>
            <div class="flex flex-col gap-1">
              <div
                v-for="index in rightSeat?.player?.hand_count || 0"
                :key="`right-hand-${index}`"
                class="tile-back h-7 w-10"
              ></div>
            </div>
            <TransitionGroup
              name="discard"
              tag="div"
              class="grid grid-cols-2 gap-1"
            >
              <div
                v-for="(tile, idx) in rightSeat?.player?.discards || []"
                :key="`right-discard-${idx}-${tile}`"
                class="tile-face h-9 w-7 text-xs"
              >
                <div class="mahjong-sprite" :style="{ backgroundPosition: parseTile(tile).bgPos }"></div>
              </div>
            </TransitionGroup>
          </div>

          <div
            class="col-start-2 row-start-2 flex flex-col items-center justify-center gap-2"
          >
            <div
              class="rounded-2xl border border-rice-100/30 bg-ink-900/40 px-5 py-3 text-center text-rice-100 backdrop-blur"
            >
              <div class="text-xs text-rice-100/80">牌山</div>
              <div class="mt-1 text-3xl font-semibold">
                {{ state.wall_remaining }}
              </div>
            </div>
          </div>

          <div
            class="col-start-1 col-span-3 row-start-3 flex flex-col items-center justify-end gap-2 pb-2"
          >
            <div class="seat-panel w-full max-w-[620px] text-xs">
              <div class="font-semibold">
                {{
                  seatName(
                    0,
                    bottomSeat?.player?.user_id,
                    bottomSeat?.player?.nickname,
                  )
                }}（0）
              </div>
              <div class="mt-1 text-rice-100/85">
                分数 {{ bottomSeat?.score || 0 }}
              </div>
            </div>

            <TransitionGroup
              name="discard"
              tag="div"
              class="flex max-w-[620px] flex-wrap justify-center gap-1"
            >
              <div
                v-for="(tile, idx) in bottomSeat?.player?.discards || []"
                :key="`bottom-discard-${idx}-${tile}`"
                class="tile-face h-9 w-7 text-xs"
              >
                <div class="mahjong-sprite" :style="{ backgroundPosition: parseTile(tile).bgPos }"></div>
              </div>
            </TransitionGroup>

            <TransitionGroup
              name="tile"
              tag="div"
              class="flex w-full max-w-[980px] flex-wrap items-end justify-center gap-1.5 pb-1"
            >
              <button
                v-for="(tile, idx) in myHand"
                :key="`${tile}-${idx}`"
                type="button"
                class="tile-face"
                :class="{ selected: selectedIndex === idx }"
                @click="selectedIndex = idx"
              >
                <div class="mahjong-sprite" :style="{ backgroundPosition: parseTile(tile).bgPos }"></div>
              </button>
            </TransitionGroup>
          </div>
        </div>
      </div>

      <div v-if="actions" class="mt-3 flex flex-wrap items-center justify-center gap-2">
        <button
          class="ink-btn-primary"
          type="button"
          @click="doDiscard"
          :disabled="!actions.actions.includes('discard')"
        >
          出牌
        </button>
        <button
          class="ink-btn-primary"
          type="button"
          @click="doTsumo"
          :disabled="!actions.actions.includes('tsumo')"
        >
          自摸
        </button>
        <button
          class="ink-btn-ghost"
          type="button"
          @click="doRon"
          :disabled="!actions.actions.includes('ron')"
        >
          荣和
        </button>
        <button
          class="ink-btn-ghost"
          type="button"
          @click="doPass"
          :disabled="!actions.actions.includes('pass')"
        >
          过
        </button>
      </div>

      <p v-if="actions" class="mb-0 mt-1 text-center text-xs text-ink-700/85">
        你的座位：{{ mySeat ?? "-" }}，可用动作：{{ actions.actions.join(" / ") || "无" }}
      </p>
    </article>
  </section>
</template>
