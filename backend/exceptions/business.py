class BusinessError(Exception):
    def __init__(self, code: int, message: str, http_status: int = 400):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)

#super()是什么?super()是一个内置函数，用于调用父类（超类）的方法。在这个上下文中，super().__init__(message)调用了父类Exception的构造函数，并将message参数传递给它。这确保了BusinessError类正确地继承了Exception类的行为，同时还允许我们在BusinessError中添加额外的属性（如code和http_status）。
#抛出错误给FastAPI的具体格式:
# raise BusinessError(code=40001, message="player not in room", http_status=400)
#当这个错误被抛出时，FastAPI会捕获它并返回一个HTTP响应，响应的状态码将是400（由http_status指定），响应体将包含一个JSON对象，其中包含code和message字段。例如：
# HTTP/1.1 400 Bad Request
# Content-Type: application/json
# {
#     "code": 40001,
#     "message": "player not in room"
# }

class EmailAlreadyExists(BusinessError):
    def __init__(self):
        super().__init__(code=40904, message="email already exists", http_status=409)


class InvalidCredentials(BusinessError):
    def __init__(self):
        super().__init__(code=40102, message="invalid credentials", http_status=401)


class InvalidToken(BusinessError):
    def __init__(self):
        super().__init__(code=40103, message="invalid token", http_status=401)


class UserNotFound(BusinessError):
    def __init__(self):
        super().__init__(code=40104, message="user not found", http_status=401)


class NotAuthenticated(BusinessError):
    def __init__(self):
        super().__init__(code=40101, message="not authenticated", http_status=401)


class RoomNotFound(BusinessError):
    def __init__(self):
        super().__init__(code=40401, message="room not found", http_status=404)


class RoomIsFull(BusinessError):
    def __init__(self):
        super().__init__(code=40901, message="room is full", http_status=409)


class AlreadyInRoom(BusinessError):
    def __init__(self):
        super().__init__(code=40902, message="already in room", http_status=409)


class SeatOccupied(BusinessError):
    def __init__(self):
        super().__init__(code=40903, message="seat occupied", http_status=409)


class PlayerNotInRoom(BusinessError):
    def __init__(self):
        super().__init__(code=40001, message="player not in room", http_status=400)


class OnlyOwnerCanStart(BusinessError):
    def __init__(self):
        super().__init__(code=40301, message="only owner can start", http_status=403)


class RoomCannotStart(BusinessError):
    def __init__(self):
        super().__init__(code=40002, message="room cannot start", http_status=400)


class GameNotFound(BusinessError):
    def __init__(self):
        super().__init__(code=40402, message="game not found", http_status=404)


class NotYourTurn(BusinessError):
    def __init__(self):
        super().__init__(code=40905, message="not your turn", http_status=409)


class InvalidTile(BusinessError):
    def __init__(self):
        super().__init__(code=40003, message="invalid tile", http_status=400)


class ActionNotAvailable(BusinessError):
    def __init__(self):
        super().__init__(code=40906, message="action not available", http_status=409)


class HistoryNotReady(BusinessError):
    def __init__(self):
        super().__init__(code=50002, message="history storage not ready", http_status=500)


class MatchHistoryNotFound(BusinessError):
    def __init__(self):
        super().__init__(code=40403, message="match history not found", http_status=404)


class TooManyRequests(BusinessError):
    def __init__(self):
        super().__init__(code=42901, message="too many requests", http_status=429)