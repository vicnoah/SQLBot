"""
企业微信登录API
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlmodel import select
from pydantic import BaseModel

from common.core.deps import SessionDep, Trans
from common.core.config import settings
from common.core.security import create_access_token
from common.core.schemas import Token
from common.utils.wework_utils import WeWorkOAuthClient, WeWorkCallbackHandler
from apps.system.models.user import UserModel
from apps.system.models.system_model import WorkspaceModel, UserWsModel
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
    获取企业微信授权链接(扫码登录)
    
    Returns:
        包含授权URL和是否启用的响应
    """
    if not settings.WEWORK_ENABLED:
        return WeWorkAuthUrlResponse(
            auth_url="",
            enabled=False
        )
    
    redirect_uri = settings.WEWORK_REDIRECT_URI
    # 使用扫码登录方式
    auth_url = WeWorkOAuthClient.get_qrcode_login_url(redirect_uri)
    
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
        
        # 获取默认工作空间(选择第一个工作空间)
        workspace_statement = select(WorkspaceModel).order_by(WorkspaceModel.create_time.asc())
        default_workspace = session.exec(workspace_statement).first()
        
        if not default_workspace:
            raise HTTPException(status_code=400, detail="系统中没有可用的工作空间,请联系管理员创建工作空间")
        
        # 创建新用户
        new_user = UserModel(
            account=userid,  # 使用企业微信userid作为账号
            name=user_detail.get("name", userid),
            email=user_detail.get("email", f"{userid}@wework.local"),
            wework_userid=userid,
            status=1,  # 默认启用
            oid=default_workspace.id  # 分配默认工作空间
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        # 创建用户-工作空间关联
        user_ws = UserWsModel(
            uid=new_user.id,
            oid=default_workspace.id,
            weight=0
        )
        session.add(user_ws)
        session.commit()
        
        db_user = new_user
        print(f"创建企业微信新用户成功: {userid}, 分配工作空间: {default_workspace.name}")
    
    # 验证用户状态
    if db_user.status != 1:
        raise HTTPException(status_code=400, detail=trans('i18n_login.user_disable', msg=trans('i18n_concat_admin')))
    
    if not db_user.oid or db_user.oid == 0:
        raise HTTPException(status_code=400, detail=trans('i18n_login.no_associated_ws', msg=trans('i18n_concat_admin')))
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 构造用户信息字典
    user_dict = {
        "id": db_user.id,
        "account": db_user.account,
        "name": db_user.name,
        "email": db_user.email,
        "oid": db_user.oid,
        "status": db_user.status,
        "wework_userid": db_user.wework_userid
    }
    
    return Token(
        access_token=create_access_token(user_dict, expires_delta=access_token_expires)
    )


@router.get("/config")
async def get_wework_config() -> dict:
    """
    获取企业微信登录配置(公开接口,无需认证)
    用于前端初始化企业微信登录组件
    
    Returns:
        包含启用状态、企业ID、应用ID的字典
    """
    return {
        "enabled": settings.WEWORK_ENABLED,
        "corpId": settings.WEWORK_CORP_ID if settings.WEWORK_ENABLED else "",
        "agentId": settings.WEWORK_AGENT_ID if settings.WEWORK_ENABLED else ""
    }


@router.api_route("/callback/data", methods=["GET", "POST"], response_class=PlainTextResponse)
async def handle_data_callback(
    request: Request,
    msg_signature: str = Query(..., description="签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    echostr: Optional[str] = Query(None, description="加密的随机字符串(仅GET请求)")
) -> PlainTextResponse:
    """
    企业微信数据回调URL(同时支持GET验证和POST业务)
    GET请求: 用于验证回调URL的有效性
    POST请求: 用于接收用户消息、事件通知等
    
    Args:
        request: FastAPI请求对象
        msg_signature: 消息签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 加密的随机字符串(仅GET请求时有此参数)
        
    Returns:
        GET: 解密后的明文字符串
        POST: 'success' 或加密后的响应消息
    """
    try:
        # GET请求 - URL验证
        if request.method == "GET":
            if not echostr:
                raise HTTPException(status_code=400, detail="GET请求缺少echostr参数")
            
            # 验证URL并解密
            echo_str = WeWorkCallbackHandler.verify_url(
                msg_signature=msg_signature,
                timestamp=timestamp,
                nonce=nonce,
                echostr=echostr
            )
            
            if not echo_str:
                raise HTTPException(status_code=400, detail="回调验证失败")
            
            print(f"数据回调URL验证成功: {echo_str}")
            return PlainTextResponse(content=echo_str)
        
        # POST请求 - 业务处理
        else:
            # 读取请求体(加密的JSON数据)
            body = await request.body()
            post_data = body.decode('utf-8')
            
            # 解密消息
            decrypted_msg = WeWorkCallbackHandler.decrypt_msg(
                post_data=post_data,
                msg_signature=msg_signature,
                timestamp=timestamp,
                nonce=nonce
            )
            
            if not decrypted_msg:
                raise HTTPException(status_code=400, detail="消息解密失败")
            
            # 处理业务逻辑
            import json
            msg_data = json.loads(decrypted_msg)
            print(f"收到企业微信数据回调: {msg_data}")
            
            # 返回 success 表示处理成功
            return PlainTextResponse(content="success")
    
    except Exception as e:
        print(f"数据回调处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据回调处理异常: {str(e)}")


@router.api_route("/callback/command", methods=["GET", "POST"], response_class=PlainTextResponse)
async def handle_command_callback(
    request: Request,
    msg_signature: str = Query(..., description="签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    echostr: Optional[str] = Query(None, description="加密的随机字符串(仅GET请求)")
) -> PlainTextResponse:
    """
    企业微信指令回调URL(同时支持GET验证和POST业务)
    GET请求: 用于验证回调URL的有效性
    POST请求: 用于接收应用授权变更事件、suite_ticket等
    
    Args:
        request: FastAPI请求对象
        msg_signature: 消息签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 加密的随机字符串(仅GET请求时有此参数)
        
    Returns:
        GET: 解密后的明文字符串
        POST: 'success' 或加密后的响应消息
    """
    try:
        # GET请求 - URL验证
        if request.method == "GET":
            if not echostr:
                raise HTTPException(status_code=400, detail="GET请求缺少echostr参数")
            
            # 验证URL并解密
            echo_str = WeWorkCallbackHandler.verify_url(
                msg_signature=msg_signature,
                timestamp=timestamp,
                nonce=nonce,
                echostr=echostr
            )
            
            if not echo_str:
                raise HTTPException(status_code=400, detail="回调验证失败")
            
            print(f"指令回调URL验证成功: {echo_str}")
            return PlainTextResponse(content=echo_str)
        
        # POST请求 - 业务处理
        else:
            # 读取请求体(加密的JSON数据)
            body = await request.body()
            post_data = body.decode('utf-8')
            
            # 解密消息
            decrypted_msg = WeWorkCallbackHandler.decrypt_msg(
                post_data=post_data,
                msg_signature=msg_signature,
                timestamp=timestamp,
                nonce=nonce
            )
            
            if not decrypted_msg:
                raise HTTPException(status_code=400, detail="消息解密失败")
            
            # 处理业务逻辑(如存储suite_ticket)
            import json
            msg_data = json.loads(decrypted_msg)
            print(f"收到企业微信指令回调: {msg_data}")
            
            # 返回 success 表示处理成功
            return PlainTextResponse(content="success")
    
    except Exception as e:
        print(f"指令回调处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"指令回调处理异常: {str(e)}")
