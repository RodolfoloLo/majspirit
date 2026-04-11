from backend.models.room_player import RoomPlayer
from backend.services.game_service import GameService


def test_create_game_and_state():
    service = GameService()
    players = [RoomPlayer(room_id=1, user_id=i + 1, seat=i, ready=True) for i in range(4)]

    meta = service.create_game(room_id=1, players=players)
    state = service.get_state(meta["game_id"])

    assert state["game_id"] == meta["game_id"]
    assert state["match_id"] == meta["match_id"]
    assert state["turn_seat"] == 0
    assert state["wall_remaining"] > 0
    assert len(state["players"]) == 4


def test_match_ends_after_four_round_tsumo(monkeypatch):
    monkeypatch.setattr("backend.services.game_service.is_standard_win", lambda tiles: True)

    service = GameService()
    players = [RoomPlayer(room_id=1, user_id=i + 1, seat=i, ready=True) for i in range(4)]
    meta = service.create_game(room_id=1, players=players)

    for _ in range(4):
        current = service.get_state(meta["game_id"])
        turn_user_id = current["players"][current["turn_seat"]]["user_id"]
        service.tsumo(meta["game_id"], turn_user_id)

    final_state = service.get_state(meta["game_id"])
    assert final_state["status"] == "match_end"

    summary = service.build_match_result(meta["game_id"])
    assert summary["match_id"] == meta["match_id"]
    assert len(summary["ranking"]) == 4
    assert len(summary["rounds"]) == 4


def test_discard_ron_has_priority_over_peng(monkeypatch):
    monkeypatch.setattr("backend.services.game_service.is_standard_win", lambda tiles: False)

    service = GameService()
    players = [RoomPlayer(room_id=1, user_id=i + 1, seat=i, ready=True) for i in range(4)]
    meta = service.create_game(room_id=1, players=players)

    game_id = meta["game_id"]
    state = service._games[game_id]
    state.players[0].hand = ["m1"] + state.players[0].hand[1:]
    state.players[2].hand = ["m1", "m1"] + state.players[2].hand[2:]

    monkeypatch.setattr(
        GameService,
        "can_win",
        lambda self, player, extra_tile=None: player.seat == 1 and extra_tile == "m1",
    )

    result = service.discard(game_id, state.players[0].user_id, "m1")

    assert result["event_type"] == "game_win"
    assert result["round_result"]["type"] == "ron"
    assert result["round_result"]["winner_seat"] == 1


def test_discard_opens_peng_window(monkeypatch):
    monkeypatch.setattr("backend.services.game_service.is_standard_win", lambda tiles: False)

    service = GameService()
    players = [RoomPlayer(room_id=1, user_id=i + 1, seat=i, ready=True) for i in range(4)]
    meta = service.create_game(room_id=1, players=players)

    game_id = meta["game_id"]
    state = service._games[game_id]
    state.players[0].hand = ["m1"] + state.players[0].hand[1:]
    state.players[1].hand = ["m1", "m1"] + state.players[1].hand[2:]

    result = service.discard(game_id, state.players[0].user_id, "m1")
    assert result["status"] == "waiting_for_peng"
    assert 1 in result["pending_peng"]

    actions = service.get_available_actions(game_id=game_id, user_id=state.players[1].user_id)
    assert actions["actions"] == ["peng"]

    peng_result = service.peng(game_id=game_id, user_id=state.players[1].user_id)
    assert peng_result["event_type"] == "game_peng"
    assert peng_result["turn_seat"] == 1
    assert state.players[1].open_meld_count == 1
    assert state.players[1].open_melds == [["m1", "m1", "m1"]]


def test_deal_round_resets_open_melds():
    service = GameService()
    players = [RoomPlayer(room_id=1, user_id=i + 1, seat=i, ready=True) for i in range(4)]
    meta = service.create_game(room_id=1, players=players)

    game_id = meta["game_id"]
    state = service._games[game_id]
    state.players[0].open_meld_count = 1
    state.players[0].open_melds = [["m2", "m2", "m2"]]

    service.deal_round(state)

    assert state.players[0].open_meld_count == 0
    assert state.players[0].open_melds == []


def test_create_game_with_missing_players_fills_bots():
    service = GameService()
    players = [
        RoomPlayer(room_id=1, user_id=11, seat=0, ready=True),
        RoomPlayer(room_id=1, user_id=12, seat=2, ready=True),
    ]

    meta = service.create_game(room_id=1, players=players)
    state = service.get_state(meta["game_id"], user_id=11)

    assert len(state["players"]) == 4
    assert sum(1 for p in state["players"] if p["is_bot"]) == 2
    assert state["my_seat"] == 0


def test_bot_auto_progress_step(monkeypatch):
    monkeypatch.setattr("backend.services.game_service.is_standard_win", lambda tiles: False)

    service = GameService()
    players = [RoomPlayer(room_id=1, user_id=21, seat=0, ready=True)]
    meta = service.create_game(room_id=1, players=players)

    state = service.get_state(meta["game_id"], user_id=21)
    first_tile = state["my_hand"][0]

    event = service.discard(meta["game_id"], user_id=21, tile=first_tile)
    step_event = service.auto_progress(meta["game_id"])
    final_state = service.get_state(meta["game_id"], user_id=21)

    assert len(event["events"]) == 1
    assert step_event is not None
    assert final_state["status"] in {"waiting_for_discard", "waiting_for_peng"}


def test_available_actions_includes_tsumo_for_seven_pairs():
    service = GameService()
    players = [RoomPlayer(room_id=1, user_id=i + 1, seat=i, ready=True) for i in range(4)]
    meta = service.create_game(room_id=1, players=players)

    game_id = meta["game_id"]
    state = service._games[game_id]
    seat = state.turn_seat
    user_id = state.players[seat].user_id

    # Manually craft a 14-tile seven pairs hand for current turn player.
    state.players[seat].hand = [
        "m1",
        "m1",
        "m2",
        "m2",
        "s3",
        "s3",
        "s4",
        "s4",
        "p5",
        "p5",
        "p6",
        "p6",
        "east",
        "east",
    ]

    actions = service.get_available_actions(game_id=game_id, user_id=user_id)
    assert "tsumo" in actions["actions"]
