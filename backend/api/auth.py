from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_db
from backend.core.response import ok
from backend.schemas.auth import LoginReq, RegisterReq
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