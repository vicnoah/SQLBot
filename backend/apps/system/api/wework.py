"""
企业微信登录API
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from pydantic import BaseModel

from common.core.deps import SessionDep, Trans
from common.core.config import settings
from common.core.security import create_access_token
from common.core.schemas import Token
from common.utils.wework_utils import WeWorkOAuthClient
from apps.system.models.user import UserModel
from apps.system.schemas.system_schema import BaseUserDTO
from apps.system.crud.user import get_user_by_account
from datetime import timedelta

router = APIRouter(tags=["wework"], prefix="/wework")


class WeWorkAuthUrlResponse(BaseModel):
    """企业微信授权URL响应"""
    auth_url: str
    enabled: bool


@router.get("/auth-url", response_model=WeWorkAuthUrlResponse)
async def get_wework_auth_url() -> WeWorkAuthUrlResponse:
    """
    获取企业微信授权链接
    
    Returns:
        包含授权URL和是否启用的响应
    """
    if not settings.WEWORK_ENABLED:
        return WeWorkAuthUrlResponse(
            auth_url="",
            enabled=False
        )
    
    redirect_uri = settings.WEWORK_REDIRECT_URI
    auth_url = WeWorkOAuthClient.get_authorize_url(redirect_uri)
    
    return WeWorkAuthUrlResponse(
        auth_url=auth_url,
        enabled=True
    )


@router.get("/callback")
async def wework_callback(
    session: SessionDep,
    trans: Trans,
    code: str = Query(..., description="企业微信授权码"),
    state: Optional[str] = Query(None, description="状态参数")
) -> Token:
    """
    企业微信OAuth回调处理
    
    Args:
        code: 企业微信授权码
        state: 状态参数
        
    Returns:
        访问令牌
    """
    if not settings.WEWORK_ENABLED:
        raise HTTPException(status_code=400, detail="企业微信登录未启用")
    
    # 通过code获取用户信息
    user_info = await WeWorkOAuthClient.get_user_info(code)
    if not user_info:
        raise HTTPException(status_code=400, detail="获取企业微信用户信息失败")
    
    userid = user_info.get("userid")
    if not userid:
        raise HTTPException(status_code=400, detail="未获取到企业微信用户ID")
    
    # 查询数据库中是否存在该企业微信用户
    statement = select(UserModel).where(UserModel.wework_userid == userid)
    db_user = session.exec(statement).first()
    
    if not db_user:
        # 获取用户详细信息
        user_detail = await WeWorkOAuthClient.get_user_detail(userid)
        if not user_detail:
            raise HTTPException(status_code=400, detail="获取企业微信用户详细信息失败")
        
        # 创建新用户
        new_user = UserModel(
            account=userid,  # 使用企业微信userid作为账号
            name=user_detail.get("name", userid),
            email=user_detail.get("email", f"{userid}@wework.local"),
            wework_userid=userid,
            status=1,  # 默认启用
            oid=0  # 需要后续分配工作空间
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        db_user = new_user
    
    # 验证用户状态
    user = BaseUserDTO.model_validate(db_user.model_dump())
    
    if user.status != 1:
        raise HTTPException(status_code=400, detail=trans('i18n_login.user_disable', msg=trans('i18n_concat_admin')))
    
    if not user.oid or user.oid == 0:
        raise HTTPException(status_code=400, detail=trans('i18n_login.no_associated_ws', msg=trans('i18n_concat_admin')))
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user_dict = user.to_dict()
    
    return Token(
        access_token=create_access_token(user_dict, expires_delta=access_token_expires)
    )


@router.get("/config")
async def get_wework_config() -> dict:
    """
    获取企业微信登录配置(公开接口,无需认证)
    
    Returns:
        包含启用状态的字典
    """
    return {
        "enabled": settings.WEWORK_ENABLED,
        "corpId": settings.WEWORK_CORP_ID if settings.WEWORK_ENABLED else "",
        "agentId": settings.WEWORK_AGENT_ID if settings.WEWORK_ENABLED else ""
    }
