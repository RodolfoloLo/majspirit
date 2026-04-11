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
from backend.ws.events import GAME_DISCARDED, GAME_MATCH_END, GAME_ROUND_END, GAME_WIN

SEAT_COUNT = 4
INITIAL_SCORE = 25000
BOT_ACTION_GUARD = 80


class GameService:
    def __init__(self):
        self.game_id_counter = count(9001)
        self.match_id_counter = count(5001)
        self._games: dict[int, RuntimeGameState] = {}

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
            initial_hands[seat] = hand[:]

        state.players[dealer_seat].hand.append(wall.pop(0))
        state.turn_seat = dealer_seat
        state.wall = wall
        state.status = "waiting_for_discard"
        state.pending_ron = []
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
        state.last_discard = None

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

        ron_candidates: list[int] = []
        for other_seat, other_player in state.players.items():
            if other_seat == seat:
                continue
            if is_standard_win(other_player.hand + [tile]):
                ron_candidates.append(other_seat)

        next_seat = self.next_seat(seat)
        if ron_candidates:
            state.status = "waiting_for_ron"
            state.pending_ron = ron_candidates
            state.last_discard = RuntimeLastDiscard(seat=seat, tile=tile, next_turn_seat=next_seat)

            payload = self.build_event_base(state, GAME_DISCARDED)
            payload.update(
                {
                    "seat": seat,
                    "tile": tile,
                    "status": state.status,
                    "pending_ron": ron_candidates,
                    "next_turn_seat": next_seat,
                }
            )
            return payload

        payload = self.advance_after_discard(state, seat)
        payload.update({"seat": seat, "tile": tile})
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

        if not is_standard_win(player.hand + [tile]):
            raise ActionNotAvailable()

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

    def pass_by_seat(self, state: RuntimeGameState, seat: int) -> dict[str, Any]:
        state.pending_ron = [pending for pending in state.pending_ron if pending != seat]
        self.record_turn(state, action="pass", seat=seat)

        if state.pending_ron:
            payload = self.build_event_base(state, GAME_DISCARDED)
            payload.update(
                {
                    "status": state.status,
                    "pending_ron": state.pending_ron,
                    "last_discard": state.last_discard.model_dump() if state.last_discard else None,
                }
            )
            return payload

        if not state.last_discard:
            raise ActionNotAvailable()

        discarded_seat = state.last_discard.seat
        return self.advance_after_discard(state, discarded_seat)

    def run_auto_bots(self, state: RuntimeGameState) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        guard = BOT_ACTION_GUARD

        while guard > 0:
            guard -= 1

            if state.status == "waiting_for_ron":
                pending = state.pending_ron
                human_pending = [seat for seat in pending if not self.is_bot_seat(state, seat)]
                bot_pending = [seat for seat in pending if self.is_bot_seat(state, seat)]

                if human_pending:
                    for bot_seat in bot_pending:
                        self.record_turn(state, action="pass", seat=bot_seat)

                    state.pending_ron = human_pending
                    payload = self.build_event_base(state, GAME_DISCARDED)
                    payload.update(
                        {
                            "status": state.status,
                            "pending_ron": state.pending_ron,
                            "last_discard": state.last_discard.model_dump() if state.last_discard else None,
                        }
                    )
                    events.append(payload)
                    break

                if not state.pending_ron:
                    if not state.last_discard:
                        break
                    events.append(self.advance_after_discard(state, state.last_discard.seat))
                    continue

                winner_seat = state.pending_ron[0]
                events.append(self.ron_by_seat(state, winner_seat))
                continue

            if state.status != "waiting_for_discard":
                break

            turn_seat = state.turn_seat
            player = state.players[turn_seat]
            if not player.is_bot:
                break

            if is_standard_win(player.hand):
                events.append(self.tsumo_by_seat(state, turn_seat))
                continue

            tile = self.pick_bot_tile(player.hand)
            events.append(self.discard_by_seat(state, turn_seat, tile))

        return events

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

        if state.status == "waiting_for_ron":
            actions = ["pass"]
            if seat in state.pending_ron:
                actions.insert(0, "ron")
            return GameActionsResp(seat=seat, actions=actions, deadline_ms=10000).model_dump()

        turn_player = state.players[state.turn_seat]
        if turn_player.user_id != user_id:
            return GameActionsResp(seat=seat, actions=[], deadline_ms=0).model_dump()

        actions = ["discard"]
        if is_standard_win(turn_player.hand):
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
        events.extend(self.run_auto_bots(state))
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
        if not is_standard_win(player.hand):
            raise ActionNotAvailable()

        events = [self.tsumo_by_seat(state, seat)]
        events.extend(self.run_auto_bots(state))
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
        events.extend(self.run_auto_bots(state))
        return self.compose_action_result(state, events)

    def pass_action(self, game_id: int, user_id: int) -> dict[str, Any]:
        state = self.require_game(game_id)
        if state.status != "waiting_for_ron" or not state.last_discard:
            raise ActionNotAvailable()

        seat = self.seat_of_user(state, user_id)
        if seat is None or seat not in state.pending_ron:
            raise ActionNotAvailable()
        if self.is_bot_seat(state, seat):
            raise ActionNotAvailable()

        events = [self.pass_by_seat(state, seat)]
        events.extend(self.run_auto_bots(state))
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
