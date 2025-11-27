"""
企业微信OAuth工具类
"""
import httpx
import sys
import os
from typing import Optional, Dict, Any
from common.core.config import settings
from common.utils.utils import SQLBotLogUtil
from common.utils.weworkapi.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt


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
    def get_qrcode_login_url(cls, redirect_uri: str, state: str = "STATE") -> str:
        """
        获取企业微信扫码登录链接(新版)
        
        Args:
            redirect_uri: 回调地址
            state: 状态参数
            
        Returns:
            扫码登录链接
        """
        import urllib.parse
        
        # 使用新版扫码登录链接
        params = {
            "login_type": "CorpApp",  # 企业自建应用登录
            "appid": settings.WEWORK_CORP_ID,
            "agentid": settings.WEWORK_AGENT_ID,
            "redirect_uri": urllib.parse.quote(redirect_uri, safe=''),
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://login.work.weixin.qq.com/wwlogin/sso/login?{query_string}"

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


class WeWorkCallbackHandler:
    """企业微信回调处理器"""

    @classmethod
    def _get_crypt_instance(cls) -> Optional[WXBizJsonMsgCrypt]:
        """
        获取加解密实例
        
        Returns:
            WXBizJsonMsgCrypt实例
        """
        if WXBizJsonMsgCrypt is None:
            SQLBotLogUtil.error("企业微信加解密库未加载")
            return None
        
        try:
            # 从配置中获取Token和EncodingAESKey
            token = settings.WEWORK_TOKEN if hasattr(settings, 'WEWORK_TOKEN') else ''
            encoding_aes_key = settings.WEWORK_ENCODING_AES_KEY if hasattr(settings, 'WEWORK_ENCODING_AES_KEY') else ''
            corp_id = settings.WEWORK_CORP_ID
            
            if not token or not encoding_aes_key:
                SQLBotLogUtil.error("企业微信回调配置不完整,请设置 WEWORK_TOKEN 和 WEWORK_ENCODING_AES_KEY")
                return None
            
            SQLBotLogUtil.info(f"初始化加解密实例 - CorpID: {corp_id}, Token: {token[:5]}..., AESKey: {encoding_aes_key[:10]}...")
            return WXBizJsonMsgCrypt(token, encoding_aes_key, corp_id)
        except Exception as e:
            SQLBotLogUtil.error(f"创建加解密实例失败: {str(e)}")
            return None

    @classmethod
    def verify_url(
        cls,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        echostr: str
    ) -> Optional[str]:
        """
        验证回调URL(GET请求)
        
        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 加密的随机字符串
            
        Returns:
            解密后的明文字符串,失败返回None
        """
        wxcpt = cls._get_crypt_instance()
        if not wxcpt:
            return None
        
        try:
            SQLBotLogUtil.info(f"VerifyURL - msg_signature: {msg_signature}, timestamp: {timestamp}, nonce: {nonce}, echostr: {echostr[:20]}...")
            
            # 调用VerifyURL方法验证并解密
            ret, echo_str = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
            
            if ret != 0:
                # 根据错误码给出具体的错误信息
                error_messages = {
                    -40001: "签名验证错误",
                    -40002: "JSON解析错误",
                    -40003: "计算签名错误",
                    -40004: "AES密钥非法",
                    -40005: "CorpID验证失败(请检查WEWORK_CORP_ID配置是否与企业微信后台一致)",
                    -40006: "AES加密错误",
                    -40007: "AES解密错误",
                    -40008: "非法的buffer",
                    -40009: "Base64编码错误",
                    -40010: "Base64解码错误",
                    -40011: "生成JSON错误"
                }
                error_msg = error_messages.get(ret, f"未知错误({ret})")
                SQLBotLogUtil.error(f"VerifyURL失败, 错误码: {ret}, 错误信息: {error_msg}")
                SQLBotLogUtil.error(f"请检查配置: WEWORK_TOKEN, WEWORK_ENCODING_AES_KEY, WEWORK_CORP_ID")
                return None
            
            SQLBotLogUtil.info(f"回调URL验证成功, 解密结果: {echo_str}")
            return echo_str
        
        except Exception as e:
            SQLBotLogUtil.error(f"回调URL验证异常: {str(e)}")
            import traceback
            SQLBotLogUtil.error(traceback.format_exc())
            return None

    @classmethod
    def decrypt_msg(
        cls,
        post_data: str,
        msg_signature: str,
        timestamp: str,
        nonce: str
    ) -> Optional[str]:
        """
        解密回调消息(POST请求)
        
        Args:
            post_data: POST请求体(加密的JSON字符串)
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            
        Returns:
            解密后的JSON字符串,失败返回None
        """
        wxcpt = cls._get_crypt_instance()
        if not wxcpt:
            return None
        
        try:
            # 调用DecryptMsg方法解密
            ret, decrypted_msg = wxcpt.DecryptMsg(post_data, msg_signature, timestamp, nonce)
            
            if ret != 0:
                SQLBotLogUtil.error(f"DecryptMsg失败, 错误码: {ret}")
                return None
            
            SQLBotLogUtil.info("消息解密成功")
            return decrypted_msg
        
        except Exception as e:
            SQLBotLogUtil.error(f"消息解密异常: {str(e)}")
            return None

    @classmethod
    def encrypt_msg(
        cls,
        reply_msg: str,
        nonce: str,
        timestamp: Optional[str] = None
    ) -> Optional[str]:
        """
        加密响应消息
        
        Args:
            reply_msg: 待加密的JSON字符串
            nonce: 随机数
            timestamp: 时间戳(可选)
            
        Returns:
            加密后的JSON字符串,失败返回None
        """
        wxcpt = cls._get_crypt_instance()
        if not wxcpt:
            return None
        
        try:
            # 调用EncryptMsg方法加密
            ret, encrypted_msg = wxcpt.EncryptMsg(reply_msg, nonce, timestamp)
            
            if ret != 0:
                SQLBotLogUtil.error(f"EncryptMsg失败, 错误码: {ret}")
                return None
            
            SQLBotLogUtil.info("消息加密成功")
            return encrypted_msg
        
        except Exception as e:
            SQLBotLogUtil.error(f"消息加密异常: {str(e)}")
            return None
