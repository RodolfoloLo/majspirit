from datetime import datetime, timezone
from itertools import count

from backend.exceptions.business import ActionNotAvailable, GameNotFound, InvalidTile, NotYourTurn
from backend.models.room_player import RoomPlayer
from backend.utils.hu import is_standard_win
from backend.utils.tile_utils import build_tiles, shuffle_tiles
from backend.ws.events import GAME_DISCARDED, GAME_MATCH_END, GAME_ROUND_END, GAME_WIN


class GameService:
    def __init__(self):
        self._game_id_counter = count(9001) #游戏ID生成器，从9001开始递增
        self._match_id_counter = count(5001) #比赛ID生成器，从5001开始递增
        self._games: dict[int, dict] = {} #游戏状态存储，键为game_id，值为游戏状态的字典(包含玩家信息、牌墙、当前回合等)

    #创建游戏
    def create_game(self, room_id: int, players: list[RoomPlayer]) -> dict:
        sorted_players = sorted(players, key=lambda p: p.seat)
        if not sorted_players:
            raise ActionNotAvailable()

        used_seats = {p.seat for p in sorted_players}
        if any(seat < 0 or seat > 3 for seat in used_seats):
            raise ActionNotAvailable()

        player_state: dict[int, dict] = {}
        for p in sorted_players:
            player_state[p.seat] = {
                "user_id": p.user_id,
                "seat": p.seat,
                "hand": [],
                "discards": [],
                "is_bot": False,
                "nickname": f"P{p.user_id}",
            }

        bot_index = 1
        for seat in range(4):
            if seat in player_state:
                continue
            player_state[seat] = {
                "user_id": -(room_id * 10 + seat + 1),
                "seat": seat,
                "hand": [],
                "discards": [],
                "is_bot": True,
                "nickname": f"BOT-{bot_index}",
            }
            bot_index += 1

        game_id = next(self._game_id_counter)
        match_id = next(self._match_id_counter)
        state = {
            "game_id": game_id,
            "match_id": match_id,
            "room_id": room_id,
            "round_index": 1,
            "dealer_seat": 0,
            "turn_seat": 0,
            "wall": [],
            "status": "waiting_for_discard",
            "scores": [25000, 25000, 25000, 25000],
            "initial_scores": [25000, 25000, 25000, 25000],
            "players": player_state,
            "pending_ron": [],
            "last_discard": None,
            "current_round": None,
            "round_logs": [],
            "persisted": False,
            "final_ranking": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._deal_round(state)
        self._games[game_id] = state
        return {"game_id": game_id, "match_id": match_id}

    def get_state(self, game_id: int, user_id: int | None = None) -> dict:
        state = self.require_game(game_id)
        players = []
        for seat in sorted(state["players"].keys()):
            p = state["players"][seat]
            players.append(
                {
                    "seat": seat,
                    "user_id": p["user_id"],
                    "is_bot": p["is_bot"],
                    "nickname": p["nickname"],
                    "hand_count": len(p["hand"]),
                    "discards": p["discards"],
                }
            )

        my_hand = None
        my_seat = None
        if user_id is not None:
            my_seat = self._seat_of_user(state, user_id)
            if my_seat is not None:
                my_hand = state["players"][my_seat]["hand"]

        return {
            "game_id": state["game_id"],
            "match_id": state["match_id"],
            "round_index": state["round_index"],
            "dealer_seat": state["dealer_seat"],
            "turn_seat": state["turn_seat"],
            "wall_remaining": len(state["wall"]),
            "status": state["status"],
            "scores": state["scores"],
            "players": players,
            "my_seat": my_seat,
            "my_hand": my_hand,
            "pending_ron": state["pending_ron"],
            "last_discard": state["last_discard"],
        }

    #获取游戏状态
    def require_game(self, game_id: int) -> dict:
        state = self._games.get(game_id)
        if not state:
            raise GameNotFound()
        return state

    def _next_seat(self, seat: int) -> int:
        return (seat + 1) % 4

    def _seat_of_user(self, state: dict, user_id: int) -> int | None:
        for seat, payload in state["players"].items():
            if payload["user_id"] == user_id:
                return seat
        return None

    def _is_bot_seat(self, state: dict, seat: int) -> bool:
        return bool(state["players"][seat]["is_bot"])

    def _bot_pick_tile(self, hand: list[str]) -> str:
        # Deterministic pick keeps tests stable and avoids random flaky behavior.
        return sorted(hand)[-1]

    def _deal_round(self, state: dict) -> None:
        wall = shuffle_tiles(build_tiles())
        dealer_seat = state["dealer_seat"]

        initial_hands: dict[int, list[str]] = {}
        for seat in sorted(state["players"].keys()):
            hand = wall[:13]
            del wall[:13]
            state["players"][seat]["hand"] = hand
            state["players"][seat]["discards"] = []
            initial_hands[seat] = hand[:]

        state["players"][dealer_seat]["hand"].append(wall.pop(0))
        state["turn_seat"] = dealer_seat
        state["wall"] = wall
        state["status"] = "waiting_for_discard"
        state["pending_ron"] = []
        state["last_discard"] = None
        state["current_round"] = {
            "round_index": state["round_index"],
            "dealer_seat": dealer_seat,
            "initial_hands": initial_hands,
            "initial_wall": wall[:],
            "turns": [],
        }

    def _record_turn(self, state: dict, payload: dict) -> None:
        if state.get("current_round"):
            state["current_round"]["turns"].append(
                {
                    **payload,
                    "at": datetime.now(timezone.utc).isoformat(),
                }
            )

    def _round_result_payload(self, state: dict, result: dict) -> dict:
        state["current_round"]["result"] = result
        state["round_logs"].append(state["current_round"])
        state["current_round"] = None

        if state["round_index"] >= 4:
            ranking = self._build_ranking(state)
            state["status"] = "match_end"
            state["final_ranking"] = ranking
            return {
                "event_type": GAME_MATCH_END,
                "game_id": state["game_id"],
                "match_id": state["match_id"],
                "round_result": result,
                "ranking": ranking,
            }

        state["round_index"] += 1
        state["dealer_seat"] = self._next_seat(state["dealer_seat"])
        self._deal_round(state)
        return {
            "event_type": GAME_ROUND_END,
            "game_id": state["game_id"],
            "match_id": state["match_id"],
            "round_result": result,
            "next_round": {
                "round_index": state["round_index"],
                "dealer_seat": state["dealer_seat"],
                "turn_seat": state["turn_seat"],
            },
        }

    def _build_ranking(self, state: dict) -> list[dict]:
        entries = []
        for seat in sorted(state["players"].keys()):
            player = state["players"][seat]
            user_id = player["user_id"]
            final_score = state["scores"][seat]
            entries.append(
                {
                    "seat": seat,
                    "user_id": user_id,
                    "is_bot": player["is_bot"],
                    "nickname": player["nickname"],
                    "final_score": final_score,
                    "score_delta": final_score - state["initial_scores"][seat],
                }
            )
        entries.sort(key=lambda item: (-item["final_score"], item["seat"]))
        for idx, entry in enumerate(entries, start=1):
            entry["rank"] = idx
        return entries

    def _advance_after_discard(self, state: dict, discarded_seat: int) -> dict:
        next_seat = self._next_seat(discarded_seat)
        state["pending_ron"] = []
        state["last_discard"] = None

        if not state["wall"]:
            result = {
                "type": "draw",
                "reason": "wall_exhausted",
                "scores": state["scores"],
            }
            return self._round_result_payload(state, result)

        drawn = state["wall"].pop(0)
        state["players"][next_seat]["hand"].append(drawn)
        state["turn_seat"] = next_seat
        state["status"] = "waiting_for_discard"
        self._record_turn(state, {"action": "draw", "seat": next_seat, "tile": drawn})
        return {
            "event_type": GAME_DISCARDED,
            "game_id": state["game_id"],
            "match_id": state["match_id"],
            "next_turn_seat": next_seat,
            "status": state["status"],
        }

    def _discard_by_seat(self, state: dict, seat: int, tile: str) -> dict:
        player = state["players"][seat]
        if tile not in player["hand"]:
            raise InvalidTile()

        player["hand"].remove(tile)
        player["discards"].append(tile)
        self._record_turn(state, {"action": "discard", "seat": seat, "tile": tile})

        ron_candidates: list[int] = []
        for other_seat, other_player in state["players"].items():
            if other_seat == seat:
                continue
            if is_standard_win(other_player["hand"] + [tile]):
                ron_candidates.append(other_seat)

        next_seat = self._next_seat(seat)
        if ron_candidates:
            state["status"] = "waiting_for_ron"
            state["pending_ron"] = ron_candidates
            state["last_discard"] = {"seat": seat, "tile": tile, "next_turn_seat": next_seat}
            return {
                "event_type": GAME_DISCARDED,
                "game_id": state["game_id"],
                "match_id": state["match_id"],
                "seat": seat,
                "tile": tile,
                "status": state["status"],
                "pending_ron": ron_candidates,
                "next_turn_seat": next_seat,
            }

        payload = self._advance_after_discard(state, seat)
        payload.update(
            {
                "seat": seat,
                "tile": tile,
            }
        )
        return payload

    def _tsumo_by_seat(self, state: dict, seat: int) -> dict:
        for target_seat in range(4):
            if target_seat == seat:
                continue
            state["scores"][target_seat] -= 1000
            state["scores"][seat] += 1000

        result = {
            "type": "tsumo",
            "winner_seat": seat,
            "scores": state["scores"],
        }
        self._record_turn(state, {"action": "tsumo", "seat": seat})
        payload = self._round_result_payload(state, result)
        if payload["event_type"] != GAME_MATCH_END:
            payload["event_type"] = GAME_WIN
        return payload

    def _ron_by_seat(self, state: dict, seat: int) -> dict:
        tile = state["last_discard"]["tile"]
        loser_seat = state["last_discard"]["seat"]
        player = state["players"][seat]
        if not is_standard_win(player["hand"] + [tile]):
            raise ActionNotAvailable()

        state["scores"][seat] += 2000
        state["scores"][loser_seat] -= 2000
        self._record_turn(state, {"action": "ron", "seat": seat, "tile": tile, "from_seat": loser_seat})

        result = {
            "type": "ron",
            "winner_seat": seat,
            "loser_seat": loser_seat,
            "tile": tile,
            "scores": state["scores"],
        }
        payload = self._round_result_payload(state, result)
        if payload["event_type"] != GAME_MATCH_END:
            payload["event_type"] = GAME_WIN
        return payload

    def _pass_by_seat(self, state: dict, seat: int) -> dict:
        state["pending_ron"] = [s for s in state["pending_ron"] if s != seat]
        self._record_turn(state, {"action": "pass", "seat": seat})

        if state["pending_ron"]:
            return {
                "event_type": GAME_DISCARDED,
                "game_id": state["game_id"],
                "match_id": state["match_id"],
                "status": state["status"],
                "pending_ron": state["pending_ron"],
                "last_discard": state["last_discard"],
            }

        discarded_seat = state["last_discard"]["seat"]
        return self._advance_after_discard(state, discarded_seat)

    def _run_auto_bots(self, state: dict) -> list[dict]:
        events: list[dict] = []
        guard = 80

        while guard > 0:
            guard -= 1

            if state["status"] == "waiting_for_ron":
                pending = state["pending_ron"]
                human_pending = [seat for seat in pending if not self._is_bot_seat(state, seat)]
                bot_pending = [seat for seat in pending if self._is_bot_seat(state, seat)]

                if human_pending:
                    for bot_seat in bot_pending:
                        self._record_turn(state, {"action": "pass", "seat": bot_seat})
                    state["pending_ron"] = human_pending
                    if human_pending:
                        events.append(
                            {
                                "event_type": GAME_DISCARDED,
                                "game_id": state["game_id"],
                                "match_id": state["match_id"],
                                "status": state["status"],
                                "pending_ron": state["pending_ron"],
                                "last_discard": state["last_discard"],
                            }
                        )
                        break

                if not state["pending_ron"]:
                    discarded_seat = state["last_discard"]["seat"]
                    events.append(self._advance_after_discard(state, discarded_seat))
                    continue

                winner_seat = state["pending_ron"][0]
                events.append(self._ron_by_seat(state, winner_seat))
                continue

            if state["status"] != "waiting_for_discard":
                break

            turn_seat = state["turn_seat"]
            player = state["players"][turn_seat]
            if not player["is_bot"]:
                break

            if is_standard_win(player["hand"]):
                events.append(self._tsumo_by_seat(state, turn_seat))
                continue

            tile = self._bot_pick_tile(player["hand"])
            events.append(self._discard_by_seat(state, turn_seat, tile))

        return events

    def _compose_action_result(self, state: dict, events: list[dict]) -> dict:
        if not events:
            raise ActionNotAvailable()
        result = dict(events[-1])
        result["events"] = events
        result["status"] = state["status"]
        result["turn_seat"] = state["turn_seat"]
        return result


    def get_available_actions(self, game_id: int, user_id: int) -> dict:
        state = self._require_game(game_id)
        if state["status"] == "match_end":
            return {"seat": None, "actions": [], "deadline_ms": 0}

        seat = self._seat_of_user(state, user_id)
        if seat is None:
            return {"seat": None, "actions": [], "deadline_ms": 0}

        if state["status"] == "waiting_for_ron":
            actions = ["pass"]
            if seat in state["pending_ron"]:
                actions.insert(0, "ron")
            return {"seat": seat, "actions": actions, "deadline_ms": 10000}

        turn_seat = state["turn_seat"]
        turn_player = state["players"][turn_seat]
        if turn_player["user_id"] != user_id:
            return {"seat": seat, "actions": [], "deadline_ms": 0}

        actions = ["discard"]
        if is_standard_win(turn_player["hand"]):
            actions.append("tsumo")
        return {"seat": seat, "actions": actions, "deadline_ms": 10000}

    def discard(self, game_id: int, user_id: int, tile: str) -> dict:
        state = self._require_game(game_id)
        if state["status"] != "waiting_for_discard":
            raise ActionNotAvailable()

        seat = state["turn_seat"]
        player = state["players"][seat]
        if player["user_id"] != user_id:
            raise NotYourTurn()
        if player["is_bot"]:
            raise ActionNotAvailable()

        events = [self._discard_by_seat(state, seat, tile)]
        events.extend(self._run_auto_bots(state))
        return self._compose_action_result(state, events)

    def tsumo(self, game_id: int, user_id: int) -> dict:
        state = self._require_game(game_id)
        if state["status"] != "waiting_for_discard":
            raise ActionNotAvailable()

        seat = state["turn_seat"]
        player = state["players"][seat]
        if player["user_id"] != user_id:
            raise NotYourTurn()
        if player["is_bot"]:
            raise ActionNotAvailable()
        if not is_standard_win(player["hand"]):
            raise ActionNotAvailable()

        events = [self._tsumo_by_seat(state, seat)]
        events.extend(self._run_auto_bots(state))
        return self._compose_action_result(state, events)

    def ron(self, game_id: int, user_id: int) -> dict:
        state = self._require_game(game_id)
        if state["status"] != "waiting_for_ron" or not state["last_discard"]:
            raise ActionNotAvailable()

        seat = self._seat_of_user(state, user_id)
        if seat is None or seat not in state["pending_ron"]:
            raise ActionNotAvailable()
        if self._is_bot_seat(state, seat):
            raise ActionNotAvailable()

        events = [self._ron_by_seat(state, seat)]
        events.extend(self._run_auto_bots(state))
        return self._compose_action_result(state, events)

    def pass_action(self, game_id: int, user_id: int) -> dict:
        state = self._require_game(game_id)
        if state["status"] != "waiting_for_ron" or not state["last_discard"]:
            raise ActionNotAvailable()

        seat = self._seat_of_user(state, user_id)
        if seat is None or seat not in state["pending_ron"]:
            raise ActionNotAvailable()
        if self._is_bot_seat(state, seat):
            raise ActionNotAvailable()

        events = [self._pass_by_seat(state, seat)]
        events.extend(self._run_auto_bots(state))
        return self._compose_action_result(state, events)

    def is_match_finished(self, game_id: int) -> bool:
        state = self._require_game(game_id)
        return state["status"] == "match_end"

    def is_persisted(self, game_id: int) -> bool:
        state = self._require_game(game_id)
        return bool(state["persisted"])

    def mark_persisted(self, game_id: int) -> None:
        state = self._require_game(game_id)
        state["persisted"] = True

    def build_match_result(self, game_id: int) -> dict:
        state = self._require_game(game_id)
        if state["status"] != "match_end":
            raise ActionNotAvailable()
        ranking = state["final_ranking"] or self._build_ranking(state)

        players = [
            {
                "seat": seat,
                "user_id": payload["user_id"],
                "is_bot": payload["is_bot"],
                "nickname": payload["nickname"],
            }
            for seat, payload in sorted(state["players"].items())
        ]

        return {
            "game_id": state["game_id"],
            "match_id": state["match_id"],
            "room_id": state["room_id"],
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "players": players,
            "initial_scores": state["initial_scores"],
            "final_scores": state["scores"],
            "ranking": ranking,
            "rounds": state["round_logs"],
        }

    def action_not_available(self) -> None:
        raise ActionNotAvailable()


game_service = GameService()
