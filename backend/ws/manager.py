from collections import defaultdict

from fastapi import WebSocket #WebSocket是一个类，代表一个 WebSocket 连接.


class WSManager:
    def __init__(self):
        #self.user_sockets 是一个字典，键是用户ID，值是一个集合，包含该用户的所有 WebSocket 连接。这种设计允许一个用户在多个设备或浏览器标签页同时在线，每个连接都会被记录下来。当需要向某个用户发送消息时，我们可以通过这个字典找到该用户的所有连接，并逐一发送消息。
        self.user_sockets: dict[int, set[WebSocket]] = defaultdict(set) 

    #connect() 方法在用户建立 WebSocket 连接时被调用。它接受用户ID和 WebSocket 对象作为参数，首先调用 ws.accept() 来接受连接请求，然后将该 WebSocket 对象添加到 user_sockets 字典中对应用户ID的集合里。
    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self.user_sockets[user_id].add(ws)

    #为什么disconnect() 方法是同步函数???:因为它只是修改了内存中的数据结构(从集合中移除一个 WebSocket 对象)，并不涉及任何异步操作，所以不需要使用 async 定义为异步函数。
    def disconnect(self, user_id: int, ws: WebSocket):
        sockets = self.user_sockets.get(user_id)
        if not sockets:
            return
        if ws in sockets:
            sockets.remove(ws)
        if not sockets:
            self.user_sockets.pop(user_id, None)


    async def send_to_user(self, user_id: int, payload: dict):
        sockets = self.user_sockets.get(user_id)
        if not sockets:
            return
        #异常处理
        dead = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)
#说明:#
# WebSocket协议本身是二进制/文本的通用传输层,不要求也不限制数据格式,所以我们可以在应用层定义自己的消息格式.
# WebSocket消息发送本身是异步的,无确认的,协议本身不保证一定送达(类似UDP,而不是TCP的请求-响应),所以这个函数需要做的是 执行发送动作+请求失败处理 ,而不是返回发送结果.

    async def broadcast(self, payload: dict):#dict即json对象.
        for user_id in list(self.user_sockets.keys()):
            await self.send_to_user(user_id, payload)


ws_manager = WSManager() #在这里创建全局唯一的 WSManager 实例,供整个应用使用,以免每次导入时都创建一个新的实例.
