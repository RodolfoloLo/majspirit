from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.ws_service import parse_user_id_from_token
from backend.ws.events import HEARTBEAT, USER_OFFLINE, USER_ONLINE
from backend.ws.manager import WSManager

router = APIRouter()

manager = WSManager()


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

    await manager.connect(user_id, ws)#认证通过,建立连接
    await manager.broadcast(
        {
            "type": USER_ONLINE,
            "ts": datetime.now(timezone.utc).isoformat(),
            "data": {"user_id": user_id},
        }
    )#连接建立后，向所有在线用户广播该用户上线的消息

    #连接建立后，服务端进入循环，持续监听客户端发来的消息：
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_json(
                    {
                        "type": HEARTBEAT,
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "data": "pong",
                    }
                )
    except WebSocketDisconnect:
        manager.disconnect(user_id, ws)
        await manager.broadcast(
            {
                "type": USER_OFFLINE,
                "ts": datetime.now(timezone.utc).isoformat(),
                "data": {"user_id": user_id},
            }
        )