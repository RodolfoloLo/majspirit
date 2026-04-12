import pytest
from starlette.websockets import WebSocketDisconnect

from backend.main import app


REQUIRED_PATHS = {
    "/api/v1/health",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/me",
    "/api/v1/auth/logout",
    "/api/v1/rooms",
    "/api/v1/rooms/{room_id}",
    "/api/v1/rooms/{room_id}/join",
    "/api/v1/rooms/{room_id}/ready",
    "/api/v1/rooms/{room_id}/start",
    "/api/v1/rooms/{room_id}/leave",
    "/api/v1/games/{game_id}/state",
    "/api/v1/games/{game_id}/actions/available",
    "/api/v1/games/{game_id}/actions/discard",
    "/api/v1/games/{game_id}/actions/tsumo",
    "/api/v1/games/{game_id}/actions/ron",
    "/api/v1/games/{game_id}/actions/peng",
    "/api/v1/games/{game_id}/actions/pass",
    "/api/v1/history/me",
    "/api/v1/history/matches/{match_id}",
    "/api/v1/ws",
}


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/api/v1/auth/me", None),
        ("POST", "/api/v1/auth/logout", {}),
        ("GET", "/api/v1/rooms", None),
        ("GET", "/api/v1/rooms/1", None),
        ("POST", "/api/v1/rooms", {"name": "test", "max_players": 4}),
        ("POST", "/api/v1/rooms/1/join", {"seat": 1}),
        ("POST", "/api/v1/rooms/1/ready", {"ready": True}),
        ("POST", "/api/v1/rooms/1/start", {}),
        ("POST", "/api/v1/rooms/1/leave", {}),
        ("GET", "/api/v1/history/me", None),
        ("GET", "/api/v1/history/matches/1", None),
        ("GET", "/api/v1/games/1/state", None),
        ("GET", "/api/v1/games/1/actions/available", None),
        ("POST", "/api/v1/games/1/actions/discard", {"tile": "m1"}),
        ("POST", "/api/v1/games/1/actions/tsumo", {}),
        ("POST", "/api/v1/games/1/actions/ron", {}),
        ("POST", "/api/v1/games/1/actions/peng", {}),
        ("POST", "/api/v1/games/1/actions/pass", {}),
    ],
)
def test_protected_endpoints_require_auth(client, method: str, path: str, payload: dict | None):
    kwargs = {"json": payload} if payload is not None else {}
    resp = client.request(method, path, **kwargs)
    assert resp.status_code == 401
    assert resp.json()["code"] == 40101


def test_register_login_route_validation(client):
    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "bad", "nickname": "n", "password": "123456"},
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "bad", "password": "123456"},
    )

    assert register_resp.status_code == 422
    assert login_resp.status_code == 422


def test_required_api_paths_registered():
    existing = {getattr(route, "path", "") for route in app.routes}
    assert REQUIRED_PATHS.issubset(existing)


def test_ws_endpoint_requires_token(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/v1/ws"):
            pass
    assert exc.value.code == 4401
