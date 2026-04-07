from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.schemas.auth import LoginReq, RegisterReq, TokenResp
from backend.schemas.user import UserResp
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResp)
async def register(payload: RegisterReq, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        return await service.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/login", response_model=TokenResp)
async def login(payload: LoginReq, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        return await service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get("/me", response_model=UserResp)
async def me(user=Depends(get_current_user)):
    return user

#payload参数是从请求体中解析出来的，FastAPI会根据请求的Content-Type自动选择合适的解析器来处理请求体数据，并将其转换为对应的Pydantic模型实例。在这个例子中，payload参数被声明为RegisterReq/LoginReq类型，因此FastAPI会尝试将请求体中的数据解析为RegisterReq/LoginReq模型实例。如果解析失败（例如缺少必需字段或字段类型不匹配），FastAPI会自动返回一个400 Bad Request响应，并包含详细的错误信息。