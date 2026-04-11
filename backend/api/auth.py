from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.core.response import ok
from backend.schemas.auth import LoginReq, RegisterReq, LogoutResp
from backend.schemas.user import UserResp
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(payload: RegisterReq, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token = await service.register(payload)
    return ok(token.model_dump())


@router.post("/login")
async def login(payload: LoginReq, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token = await service.login(payload)
    return ok(token.model_dump())


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return ok(UserResp.model_validate(user).model_dump())

#为什么ok函数参数需要model_dump()呢?
#如果是在路由函数中直接返回一个 Pydantic 模型实例，FastAPI 会自动调用该模型的 .dict() 方法来将其转换为一个字典，然后再将其转换为 JSON 格式返回给客户端。
#但是这里我们使用了一个自定义的 ok() 函数来包装响应数据，这个函数可能期望接收一个普通的字典而不是一个 Pydantic 模型实例。因此，我们需要显式地调用 .model_dump() 方法来将 Pydantic 模型转换为一个字典，以确保 ok() 函数能够正确处理并返回响应数据。
#总结就是FastAPI路由函数在返回时返回类型必须是Pydantic模型实例或者字典,如果是前者会自动调用.dict()方法转换成字典,如果是后者则直接返回.但是如果我们使用了一个自定义的响应包装函数(比如ok()),这个函数可能期望接收一个普通的字典而不是一个 Pydantic 模型实例。因此，我们需要显式地调用 .model_dump() 方法来将 Pydantic 模型转换为一个字典，以确保 ok() 函数能够正确处理并返回响应数据。

@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    return ok(LogoutResp(logged_out=True).model_dump())