from collections import defaultdict

from fastapi import WebSocket


class WSManager:
    def __init__(self):
        #self.user_sockets 是一个字典，键是用户ID，值是一个集合，包含该用户的所有 WebSocket 连接。这种设计允许一个用户在多个设备或浏览器标签页同时在线，每个连接都会被记录下来。当需要向某个用户发送消息时，我们可以通过这个字典找到该用户的所有连接，并逐一发送消息。
        self.user_sockets: dict[int, set[WebSocket]] = defaultdict(set) 

    #connect() 方法在用户建立 WebSocket 连接时被调用。它接受用户ID和 WebSocket 对象作为参数，首先调用 ws.accept() 来接受连接请求，然后将该 WebSocket 对象添加到 user_sockets 字典中对应用户ID的集合里。
    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self.user_sockets[user_id].add(ws)

    def disconnect(self, user_id: int, ws: WebSocket):
        sockets = self.user_sockets.get(user_id)
        if not sockets:
            return
        if ws in sockets:
            sockets.remove(ws)
        if not sockets:
            self.user_sockets.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: dict):
        sockets = self.user_sockets.get(user_id, set())
        dead = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, payload: dict):
        for user_id in list(self.user_sockets.keys()):
            await self.send_to_user(user_id, payload)


ws_manager = WSManager()
