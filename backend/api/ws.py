import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.ws_service import parse_user_id_from_token
from backend.ws.events import HEARTBEAT, USER_OFFLINE, USER_ONLINE
from backend.ws.manager import ws_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    #ws参数是WebSocket对象，代表当前连接的客户端。我们从查询参数中获取 token，并解析出 user_id 来识别用户身份。如果 token 无效，就拒绝连接。
    #WebSocket类的属性/方法有很多，常用的有：
    # - query_params: 获取连接时的查询参数，比如 token
    # - accept(): 接受连接，必须调用这个方法才能正式建立 WebSocket 连接
    # - send_text()/send_json(): 发送文本或 JSON 消息给客户端
    # - receive_text()/receive_json(): 接收客户端发送的文本或 JSON 消息
    # - close(): 关闭连接
    token = ws.query_params.get("token")
    try:
        user_id = parse_user_id_from_token(token)
    except Exception:
        await ws.close(code=4401)
        return

    await ws_manager.connect(user_id, ws)#认证通过,建立连接
    #只是 向所有在线用户广播一条用户上线的消息.
    await ws_manager.broadcast(
        {
            "type": USER_ONLINE,
            "ts": datetime.now(timezone.utc).isoformat(),
            "data": {"user_id": user_id},
        }
    )

    #连接建立后，服务端进入循环，持续监听客户端发来的消息：
    try:
        while True:
            #消息解析逻辑:先尝试把收到的raw用json.loads解析成字典,如果解析成功,就从字典里拿拿"type"字段作为msg_type
            raw = await ws.receive_text()
            msg_type = raw
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    msg_type = parsed.get("type", raw)
            #如果解析失败:(比如客户端发的是纯文本ping),就直接用原始内容作为msg_type
            except json.JSONDecodeError:
                pass

            if msg_type in {"ping", "heartbeat.ping"}:
                await ws.send_json(
                    {
                        "type": HEARTBEAT,
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "data": "pong",
                    }
                )
    #连接断开的处理
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, ws)
        await ws_manager.broadcast(
            {
                "type": USER_OFFLINE,
                "ts": datetime.now(timezone.utc).isoformat(),
                "data": {"user_id": user_id},
            }
        )

#这个文件的作用就是建立WebSocket连接,至于建立连接之后的消息处理逻辑,在其他文件实现.

#WebSocket连接时使用的URL是ws://127.0.0.1:8000/api/v1/ws?token=<JWT>
#通用消息结构为:
#{
#    "type": "event_type",
#    "ts": "2007-01-15T00:00:00Z",
#    "request_id": "optional-client-message-id",
#    "data": {...}
#}