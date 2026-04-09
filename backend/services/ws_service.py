from backend.core.security import decode_access_token


def parse_user_id_from_token(token: str | None) -> int:
    if not token:
        raise ValueError("missing token")
    payload = decode_access_token(token)
    sub = payload.get("sub")#JWT payload 中的 "sub" 字段通常用来存储用户ID或其他唯一标识符。在这个函数中，我们从解码后的 JWT payload 中获取 "sub" 字段的值，并将其转换为整数类型作为用户ID返回。如果 "sub" 字段不存在或无效，我们会抛出一个 ValueError 异常，表示 token 的有效载荷不正确。
    if not sub:
        raise ValueError("invalid token payload")
    return int(sub)