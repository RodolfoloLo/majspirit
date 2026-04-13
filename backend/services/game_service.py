import asyncio
from datetime import datetime, timezone
from itertools import count
from typing import Any

from backend.exceptions.business import ActionNotAvailable, GameNotFound, InvalidTile, NotYourTurn
from backend.models.room_player import RoomPlayer
from backend.schemas.game import (
    GameActionsResp,
    GameStatePlayerResp,
    GameStateResp,
    LastDiscardResp,
    RuntimeGameState,
    RuntimeLastDiscard,
    RuntimePlayerState,
    RuntimeRoundState,
    RuntimeRoundTurn,
)
from backend.utils.hu import is_standard_win
from backend.utils.tile_utils import build_tiles, shuffle_tiles
from backend.ws.events import GAME_DISCARDED, GAME_MATCH_END, GAME_PENG, GAME_ROUND_END, GAME_WIN

SEAT_COUNT = 4
INITIAL_SCORE = 25000


class GameService:
    def __init__(self):
        self.game_id_counter = count(9001)
        self.match_id_counter = count(5001)
        #geme是 游戏ID,match是 比赛ID,
        self._games: dict[int, RuntimeGameState] = {} #内存中的游戏状态字典,key是game_id,value是游戏的运行时状态,所有的游戏状态都存在内存里.
        self._locks: dict[int, asyncio.Lock] = {} #每个游戏对应的异步锁,这是为了并发安全!因为异步服务可能同时收到同一个游戏的多个请求,如果不加锁,会导致状态被并发修改,出现数据不一致的问题,所以每一个游戏有一个独立的锁,保证同一个游戏是串行的.

    def lock_for(self, game_id: int) -> asyncio.Lock:
        if game_id not in self._locks:
            self._locks[game_id] = asyncio.Lock()
        return self._locks[game_id]

    def ordered_seats(self, state: RuntimeGameState, origin_seat: int) -> list[int]:
        return [
            (origin_seat + step) % SEAT_COUNT
            for step in range(1, SEAT_COUNT)
            if (origin_seat + step) % SEAT_COUNT in state.players
        ]

    def can_win(self, player: RuntimePlayerState, extra_tile: str | None = None) -> bool:
        tiles = player.hand[:]
        if extra_tile is not None:
            tiles.append(extra_tile)
        required_len = 14 - (player.open_meld_count * 3)
        if len(tiles) != required_len:
            return False
        return is_standard_win(tiles)

    def create_game(self, room_id: int, players: list[RoomPlayer]) -> dict[str, int]:
        sorted_players = sorted(players, key=lambda player: player.seat)
        if not sorted_players:
            raise ActionNotAvailable()

        used_seats = {player.seat for player in sorted_players}
        if any(seat < 0 or seat >= SEAT_COUNT for seat in used_seats):
            raise ActionNotAvailable()

        player_state: dict[int, RuntimePlayerState] = {}
        for player in sorted_players:
            player_state[player.seat] = RuntimePlayerState(
                user_id=player.user_id,
                seat=player.seat,
                nickname=f"P{player.user_id}",
            )

        bot_index = 1
        for seat in range(SEAT_COUNT):
            if seat in player_state:
                continue

            player_state[seat] = RuntimePlayerState(
                user_id=-(room_id * 10 + seat + 1),
                seat=seat,
                nickname=f"BOT-{bot_index}",
                is_bot=True,
            )
            bot_index += 1

        game_id = next(self.game_id_counter)
        match_id = next(self.match_id_counter)
        state = RuntimeGameState(
            game_id=game_id,
            match_id=match_id,
            room_id=room_id,
            round_index=1,
            dealer_seat=0,
            turn_seat=0,
            status="waiting_for_discard",
            scores=[INITIAL_SCORE] * SEAT_COUNT,
            initial_scores=[INITIAL_SCORE] * SEAT_COUNT,
            players=player_state,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self.deal_round(state)
        self._games[game_id] = state
        return {"game_id": game_id, "match_id": match_id}

    def require_game(self, game_id: int) -> RuntimeGameState:
        state = self._games.get(game_id)
        if not state:
            raise GameNotFound()
        return state

    #检查游戏是否存在
    def has_game(self, game_id: int) -> bool:
        return game_id in self._games

    #导出游戏状态为字典
    def export_game_state(self, game_id: int) -> dict[str, Any]:
        state = self.require_game(game_id)
        return state.model_dump()

    #从字典导入游戏状态,并存储在内存中
    def import_game_state(self, payload: dict[str, Any]) -> RuntimeGameState:
        state = RuntimeGameState.model_validate(payload)
        self._games[state.game_id] = state
        return state

    def next_seat(self, seat: int) -> int:
        return (seat + 1) % SEAT_COUNT

    def seat_of_user(self, state: RuntimeGameState, user_id: int) -> int | None:
        for seat, payload in state.players.items():
            if payload.user_id == user_id:
                return seat
        return None

    def is_bot_seat(self, state: RuntimeGameState, seat: int) -> bool:
        return state.players[seat].is_bot

    def pick_bot_tile(self, hand: list[str]) -> str:
        return sorted(hand)[-1]

    def deal_round(self, state: RuntimeGameState) -> None:
        wall = shuffle_tiles(build_tiles())
        dealer_seat = state.dealer_seat

        initial_hands: dict[int, list[str]] = {}
        for seat in sorted(state.players.keys()):
            hand = wall[:13]
            del wall[:13]
            player = state.players[seat]
            player.hand = hand
            player.discards = []
            player.open_meld_count = 0
            player.open_melds = []
            initial_hands[seat] = hand[:]

        state.players[dealer_seat].hand.append(wall.pop(0))
        state.turn_seat = dealer_seat
        state.wall = wall
        state.status = "waiting_for_discard"
        state.pending_ron = []
        state.pending_peng = []
        state.last_discard = None
        state.current_round = RuntimeRoundState(
            round_index=state.round_index,
            dealer_seat=dealer_seat,
            initial_hands=initial_hands,
            initial_wall=wall[:],
        )

    def record_turn(
        self,
        state: RuntimeGameState,
        action: str,
        seat: int,
        tile: str | None = None,
        from_seat: int | None = None,
    ) -> None:
        if not state.current_round:
            return

        state.current_round.turns.append(
            RuntimeRoundTurn(
                action=action,
                seat=seat,
                tile=tile,
                from_seat=from_seat,
                at=datetime.now(timezone.utc).isoformat(),
            )
        )

    def build_event_base(self, state: RuntimeGameState, event_type: str) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "game_id": state.game_id,
            "match_id": state.match_id,
        }

    def build_round_result_payload(self, state: RuntimeGameState, result: dict[str, Any]) -> dict[str, Any]:
        if not state.current_round:
            raise ActionNotAvailable()

        state.current_round.result = result
        state.round_logs.append(state.current_round)
        state.current_round = None

        if state.round_index >= 4:
            ranking = self.build_ranking(state)
            state.status = "match_end"
            state.final_ranking = ranking
            payload = self.build_event_base(state, GAME_MATCH_END)
            payload.update(
                {
                    "round_result": result,
                    "ranking": ranking,
                }
            )
            return payload

        state.round_index += 1
        state.dealer_seat = self.next_seat(state.dealer_seat)
        self.deal_round(state)
        payload = self.build_event_base(state, GAME_ROUND_END)
        payload.update(
            {
                "round_result": result,
                "next_round": {
                    "round_index": state.round_index,
                    "dealer_seat": state.dealer_seat,
                    "turn_seat": state.turn_seat,
                },
            }
        )
        return payload

    def build_ranking(self, state: RuntimeGameState) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for seat in sorted(state.players.keys()):
            player = state.players[seat]
            final_score = state.scores[seat]
            entries.append(
                {
                    "seat": seat,
                    "user_id": player.user_id,
                    "is_bot": player.is_bot,
                    "nickname": player.nickname,
                    "final_score": final_score,
                    "score_delta": final_score - state.initial_scores[seat],
                }
            )

        entries.sort(key=lambda item: (-item["final_score"], item["seat"]))
        for rank, entry in enumerate(entries, start=1):
            entry["rank"] = rank
        return entries

    def advance_after_discard(self, state: RuntimeGameState, discarded_seat: int) -> dict[str, Any]:
        next_seat = self.next_seat(discarded_seat)
        state.pending_ron = []
        state.pending_peng = []

        if not state.wall:
            result = {
                "type": "draw",
                "reason": "wall_exhausted",
                "scores": state.scores,
            }
            return self.build_round_result_payload(state, result)

        drawn = state.wall.pop(0)
        state.players[next_seat].hand.append(drawn)
        state.turn_seat = next_seat
        state.status = "waiting_for_discard"
        self.record_turn(state, action="draw", seat=next_seat, tile=drawn)

        payload = self.build_event_base(state, GAME_DISCARDED)
        payload.update(
            {
                "next_turn_seat": next_seat,
                "status": state.status,
            }
        )
        return payload

    def discard_by_seat(self, state: RuntimeGameState, seat: int, tile: str) -> dict[str, Any]:
        player = state.players[seat]
        if tile not in player.hand:
            raise InvalidTile()

        player.hand.remove(tile)
        player.discards.append(tile)
        self.record_turn(state, action="discard", seat=seat, tile=tile)

        next_seat = self.next_seat(seat)
        state.last_discard = RuntimeLastDiscard(seat=seat, tile=tile, next_turn_seat=next_seat)

        ron_candidates = [
            candidate
            for candidate in self.ordered_seats(state, seat)
            if self.can_win(state.players[candidate], tile)
        ]
        if ron_candidates:
            # Ron always has top priority and is auto-resolved.
            winner_seat = ron_candidates[0]
            payload = self.ron_by_seat(state, winner_seat)
            payload.update({"trigger_discard_seat": seat, "trigger_discard_tile": tile})
            return payload

        peng_candidates = [
            candidate
            for candidate in self.ordered_seats(state, seat)
            if state.players[candidate].hand.count(tile) >= 2
        ]
        if peng_candidates:
            state.status = "waiting_for_peng"
            state.pending_ron = []
            state.pending_peng = peng_candidates

            payload = self.build_event_base(state, GAME_DISCARDED)
            payload.update(
                {
                    "seat": seat,
                    "tile": tile,
                    "status": state.status,
                    "pending_ron": [],
                    "pending_peng": peng_candidates,
                    "next_turn_seat": next_seat,
                }
            )
            return payload

        payload = self.advance_after_discard(state, seat)
        payload.update({"seat": seat, "tile": tile})
        return payload

    def peng_by_seat(self, state: RuntimeGameState, seat: int) -> dict[str, Any]:
        if state.status != "waiting_for_peng" or not state.last_discard:
            raise ActionNotAvailable()
        if seat not in state.pending_peng:
            raise ActionNotAvailable()

        tile = state.last_discard.tile
        from_seat = state.last_discard.seat
        player = state.players[seat]
        if player.hand.count(tile) < 2:
            raise ActionNotAvailable()

        player.hand.remove(tile)
        player.hand.remove(tile)
        player.open_meld_count += 1
        player.open_melds.append([tile, tile, tile])

        state.pending_peng = []
        state.pending_ron = []
        state.turn_seat = seat
        state.status = "waiting_for_discard"

        self.record_turn(state, action="peng", seat=seat, tile=tile, from_seat=from_seat)
        payload = self.build_event_base(state, GAME_PENG)
        payload.update(
            {
                "seat": seat,
                "from_seat": from_seat,
                "tile": tile,
                "status": state.status,
                "next_turn_seat": seat,
            }
        )
        return payload

    def tsumo_by_seat(self, state: RuntimeGameState, seat: int) -> dict[str, Any]:
        for target_seat in range(SEAT_COUNT):
            if target_seat == seat:
                continue
            state.scores[target_seat] -= 1000
            state.scores[seat] += 1000

        result = {
            "type": "tsumo",
            "winner_seat": seat,
            "scores": state.scores,
        }
        self.record_turn(state, action="tsumo", seat=seat)
        payload = self.build_round_result_payload(state, result)
        if payload["event_type"] != GAME_MATCH_END:
            payload["event_type"] = GAME_WIN
        return payload

    def ron_by_seat(self, state: RuntimeGameState, seat: int) -> dict[str, Any]:
        if not state.last_discard:
            raise ActionNotAvailable()

        tile = state.last_discard.tile
        loser_seat = state.last_discard.seat
        player = state.players[seat]

        if not self.can_win(player, tile):
            raise ActionNotAvailable()

        state.pending_ron = []
        state.pending_peng = []

        state.scores[seat] += 2000
        state.scores[loser_seat] -= 2000
        self.record_turn(state, action="ron", seat=seat, tile=tile, from_seat=loser_seat)

        result = {
            "type": "ron",
            "winner_seat": seat,
            "loser_seat": loser_seat,
            "tile": tile,
            "scores": state.scores,
        }
        payload = self.build_round_result_payload(state, result)
        if payload["event_type"] != GAME_MATCH_END:
            payload["event_type"] = GAME_WIN
        return payload

    def auto_progress(self, game_id: int) -> dict[str, Any] | None:
        state = self.require_game(game_id)
        if state.status == "match_end":
            return None

        if state.status == "waiting_for_peng":
            if not state.last_discard:
                return None
            if not state.pending_peng:
                return self.advance_after_discard(state, state.last_discard.seat)

            candidate = state.pending_peng[0]
            if self.is_bot_seat(state, candidate):
                return self.peng_by_seat(state, candidate)

            # No explicit pass action: human peng window expires automatically.
            self.record_turn(state, action="auto_skip_peng", seat=candidate, tile=state.last_discard.tile)
            return self.advance_after_discard(state, state.last_discard.seat)

        if state.status != "waiting_for_discard":
            return None

        turn_seat = state.turn_seat
        player = state.players[turn_seat]
        if not player.is_bot:
            return None

        if self.can_win(player):
            return self.tsumo_by_seat(state, turn_seat)

        tile = self.pick_bot_tile(player.hand)
        return self.discard_by_seat(state, turn_seat, tile)

    def compose_action_result(self, state: RuntimeGameState, events: list[dict[str, Any]]) -> dict[str, Any]:
        if not events:
            raise ActionNotAvailable()

        result = dict(events[-1])
        result["events"] = events
        result["status"] = state.status
        result["turn_seat"] = state.turn_seat
        return result

    def get_state(self, game_id: int, user_id: int | None = None) -> dict[str, Any]:
        state = self.require_game(game_id)

        players = [
            GameStatePlayerResp(
                seat=seat,
                user_id=player.user_id,
                is_bot=player.is_bot,
                nickname=player.nickname,
                hand_count=len(player.hand),
                discards=player.discards,
                open_meld_count=player.open_meld_count,
                open_melds=player.open_melds,
            )
            for seat, player in sorted(state.players.items())
        ]

        my_seat = self.seat_of_user(state, user_id) if user_id is not None else None
        my_hand = state.players[my_seat].hand if my_seat is not None else None

        payload = GameStateResp(
            game_id=state.game_id,
            match_id=state.match_id,
            round_index=state.round_index,
            dealer_seat=state.dealer_seat,
            turn_seat=state.turn_seat,
            wall_remaining=len(state.wall),
            status=state.status,
            scores=state.scores,
            players=players,
            my_seat=my_seat,
            my_hand=my_hand,
            pending_ron=state.pending_ron,
            pending_peng=state.pending_peng,
            last_discard=LastDiscardResp.model_validate(state.last_discard.model_dump()) if state.last_discard else None,
        )
        return payload.model_dump()

    def get_available_actions(self, game_id: int, user_id: int) -> dict[str, Any]:
        state = self.require_game(game_id)
        if state.status == "match_end":
            return GameActionsResp(seat=None, actions=[], deadline_ms=0).model_dump()

        seat = self.seat_of_user(state, user_id)
        if seat is None:
            return GameActionsResp(seat=None, actions=[], deadline_ms=0).model_dump()

        if state.status == "waiting_for_peng":
            if seat in state.pending_peng and not self.is_bot_seat(state, seat):
                return GameActionsResp(seat=seat, actions=["peng"], deadline_ms=2500).model_dump()
            return GameActionsResp(seat=seat, actions=[], deadline_ms=0).model_dump()

        turn_player = state.players[state.turn_seat]
        if turn_player.user_id != user_id:
            return GameActionsResp(seat=seat, actions=[], deadline_ms=0).model_dump()

        actions = ["discard"]
        if self.can_win(turn_player):
            actions.append("tsumo")
        return GameActionsResp(seat=seat, actions=actions, deadline_ms=10000).model_dump()

    def discard(self, game_id: int, user_id: int, tile: str) -> dict[str, Any]:
        state = self.require_game(game_id)
        if state.status != "waiting_for_discard":
            raise ActionNotAvailable()

        seat = state.turn_seat
        player = state.players[seat]
        if player.user_id != user_id:
            raise NotYourTurn()
        if player.is_bot:
            raise ActionNotAvailable()

        events = [self.discard_by_seat(state, seat, tile)]
        return self.compose_action_result(state, events)

    def tsumo(self, game_id: int, user_id: int) -> dict[str, Any]:
        state = self.require_game(game_id)
        if state.status != "waiting_for_discard":
            raise ActionNotAvailable()

        seat = state.turn_seat
        player = state.players[seat]
        if player.user_id != user_id:
            raise NotYourTurn()
        if player.is_bot:
            raise ActionNotAvailable()
        if not self.can_win(player):
            raise ActionNotAvailable()

        events = [self.tsumo_by_seat(state, seat)]
        return self.compose_action_result(state, events)

    def peng(self, game_id: int, user_id: int) -> dict[str, Any]:
        state = self.require_game(game_id)
        if state.status != "waiting_for_peng":
            raise ActionNotAvailable()

        seat = self.seat_of_user(state, user_id)
        if seat is None or seat not in state.pending_peng:
            raise ActionNotAvailable()
        if self.is_bot_seat(state, seat):
            raise ActionNotAvailable()

        events = [self.peng_by_seat(state, seat)]
        return self.compose_action_result(state, events)

    def ron(self, game_id: int, user_id: int) -> dict[str, Any]:
        state = self.require_game(game_id)
        if state.status != "waiting_for_ron" or not state.last_discard:
            raise ActionNotAvailable()

        seat = self.seat_of_user(state, user_id)
        if seat is None or seat not in state.pending_ron:
            raise ActionNotAvailable()
        if self.is_bot_seat(state, seat):
            raise ActionNotAvailable()

        events = [self.ron_by_seat(state, seat)]
        return self.compose_action_result(state, events)

    def is_match_finished(self, game_id: int) -> bool:
        return self.require_game(game_id).status == "match_end"

    def is_persisted(self, game_id: int) -> bool:
        return self.require_game(game_id).persisted

    def mark_persisted(self, game_id: int) -> None:
        self.require_game(game_id).persisted = True

    def build_match_result(self, game_id: int) -> dict[str, Any]:
        state = self.require_game(game_id)
        if state.status != "match_end":
            raise ActionNotAvailable()

        ranking = state.final_ranking or self.build_ranking(state)
        players = [
            {
                "seat": seat,
                "user_id": player.user_id,
                "is_bot": player.is_bot,
                "nickname": player.nickname,
            }
            for seat, player in sorted(state.players.items())
        ]

        return {
            "game_id": state.game_id,
            "match_id": state.match_id,
            "room_id": state.room_id,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "players": players,
            "initial_scores": state.initial_scores,
            "final_scores": state.scores,
            "ranking": ranking,
            "rounds": [round_state.model_dump() for round_state in state.round_logs],
        }

    def action_not_available(self) -> None:
        raise ActionNotAvailable()


game_service = GameService()
