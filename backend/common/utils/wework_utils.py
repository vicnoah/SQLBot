"""
企业微信OAuth工具类
"""
import httpx
from typing import Optional, Dict, Any
from common.core.config import settings
from common.utils.utils import SQLBotLogUtil


class WeWorkOAuthClient:
    """企业微信OAuth客户端"""

    BASE_URL = "https://qyapi.weixin.qq.com"

    @classmethod
    async def get_access_token(cls) -> Optional[str]:
        """
        获取企业微信access_token
        
        Returns:
            access_token字符串,失败返回None
        """
        url = f"{cls.BASE_URL}/cgi-bin/gettoken"
        params = {
            "corpid": settings.WEWORK_CORP_ID,
            "corpsecret": settings.WEWORK_SECRET
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()
                
                if data.get("errcode") == 0:
                    return data.get("access_token")
                else:
                    SQLBotLogUtil.error(f"获取企业微信access_token失败: {data}")
                    return None
        except Exception as e:
            SQLBotLogUtil.error(f"获取企业微信access_token异常: {str(e)}")
            return None

    @classmethod
    async def get_user_info(cls, code: str) -> Optional[Dict[str, Any]]:
        """
        通过code获取企业微信用户信息
        
        Args:
            code: OAuth授权码
            
        Returns:
            用户信息字典,失败返回None
        """
        access_token = await cls.get_access_token()
        if not access_token:
            return None
        
        url = f"{cls.BASE_URL}/cgi-bin/auth/getuserinfo"
        params = {
            "access_token": access_token,
            "code": code
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()
                
                if data.get("errcode") == 0:
                    return data
                else:
                    SQLBotLogUtil.error(f"获取企业微信用户信息失败: {data}")
                    return None
        except Exception as e:
            SQLBotLogUtil.error(f"获取企业微信用户信息异常: {str(e)}")
            return None

    @classmethod
    async def get_user_detail(cls, userid: str) -> Optional[Dict[str, Any]]:
        """
        获取企业微信用户详细信息
        
        Args:
            userid: 企业微信用户ID
            
        Returns:
            用户详细信息字典,失败返回None
        """
        access_token = await cls.get_access_token()
        if not access_token:
            return None
        
        url = f"{cls.BASE_URL}/cgi-bin/user/get"
        params = {
            "access_token": access_token,
            "userid": userid
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()
                
                if data.get("errcode") == 0:
                    return data
                else:
                    SQLBotLogUtil.error(f"获取企业微信用户详细信息失败: {data}")
                    return None
        except Exception as e:
            SQLBotLogUtil.error(f"获取企业微信用户详细信息异常: {str(e)}")
            return None

    @classmethod
    def get_authorize_url(cls, redirect_uri: str, state: str = "STATE") -> str:
        """
        获取企业微信OAuth授权链接
        
        Args:
            redirect_uri: 回调地址
            state: 状态参数
            
        Returns:
            授权链接
        """
        import urllib.parse
        
        params = {
            "appid": settings.WEWORK_CORP_ID,
            "redirect_uri": urllib.parse.quote(redirect_uri),
            "response_type": "code",
            "scope": "snsapi_base",
            "state": state,
            "agentid": settings.WEWORK_AGENT_ID
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://open.weixin.qq.com/connect/oauth2/authorize?{query_string}#wechat_redirect"
