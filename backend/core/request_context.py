from contextvars import ContextVar


_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    request_id = _request_id_ctx.get()
    return request_id or None

#contextvars的ContextVar类提供了一种在异步环境中存储和访问上下文变量的机制。通过使用ContextVar，可以在不同的协程之间共享数据，而不会发生冲突或数据泄漏。在这个代码中，我们定义了一个名为_request_id_ctx的ContextVar，用于存储请求ID。set_request_id函数用于设置请求ID，而get_request_id函数用于获取当前请求ID。这种设计使得我们可以在整个请求处理过程中访问和使用请求ID，无论是在同步还是异步代码中。
#具体是怎么发ID的?
#其实就是 给每个HTTP请求分配了唯一的ID(request_id)