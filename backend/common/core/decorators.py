from functools import wraps
from typing import Callable
import inspect
from fastapi import HTTPException
from common.core.deps import CurrentUser, Trans
from common.utils.utils import SQLBotLogUtil


def require_space_admin(func: Callable):
    """
    装饰器:要求用户必须是空间管理员或系统管理员
    适用于需要空间管理权限的接口
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 从 kwargs 中提取依赖注入的参数
        current_user = kwargs.get('current_user') or kwargs.get('user')
        trans = kwargs.get('trans')

        if not current_user:
            raise HTTPException(
                status_code=500, detail="Missing current_user dependency")
        if not trans:
            raise HTTPException(
                status_code=500, detail="Missing trans dependency")

        # 权限检查
        SQLBotLogUtil.debug(f'current_user: {current_user}')
        if not current_user.isAdmin and current_user.weight != 1:
            raise HTTPException(
                status_code=403,
                detail=trans('i18n_permission.no_permission', url='', msg='')
            )

        # 调用原函数
        return await func(*args, **kwargs)

    # 保留原函数的签名,这对 FastAPI 的依赖注入至关重要
    wrapper.__signature__ = inspect.signature(func)
    return wrapper


def require_admin(func: Callable):
    """
    装饰器:要求用户必须是系统管理员
    适用于系统级管理接口
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user') or kwargs.get('user')
        trans = kwargs.get('trans')

        if not current_user:
            raise HTTPException(
                status_code=500, detail="Missing current_user dependency")
        if not trans:
            raise HTTPException(
                status_code=500, detail="Missing trans dependency")

        if not current_user.isAdmin:
            raise HTTPException(
                status_code=403,
                detail=trans('i18n_permission.no_permission', url='',
                             msg=trans('i18n_permission.only_admin'))
            )

        return await func(*args, **kwargs)

    wrapper.__signature__ = inspect.signature(func)
    return wrapper


def require_not_normal_user(func: Callable):
    """
    装饰器:要求用户不能是普通成员
    适用于需要管理权限的接口
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user') or kwargs.get('user')
        trans = kwargs.get('trans')

        if not current_user:
            raise HTTPException(
                status_code=500, detail="Missing current_user dependency")
        if not trans:
            raise HTTPException(
                status_code=500, detail="Missing trans dependency")

        # weight=0 表示普通成员
        if not current_user.isAdmin and current_user.weight == 0:
            raise HTTPException(
                status_code=403,
                detail=trans('i18n_permission.no_permission', url='', msg='')
            )

        return await func(*args, **kwargs)

    wrapper.__signature__ = inspect.signature(func)
    return wrapper
