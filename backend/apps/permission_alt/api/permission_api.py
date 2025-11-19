import json
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from common.core.deps import SessionDep, CurrentUser, Trans
from common.core.decorators import require_space_admin
from common.core.pagination import Paginator
from common.core.schemas import PaginatedResponse, PaginationParams
from ..models.permission_models import DsPermission, DsRules, PermissionDTO
from ..crud.permission_crud import (
    create_permission,
    update_permission,
    delete_permission,
    get_permissions_by_table,
    create_rule,
    update_rule,
    delete_rule,
    get_all_rules,
    get_rules_paginated
)

router = APIRouter(prefix="/ds_permission", tags=["permission"])

# ============ 权限规则组管理 ============


# @router.post("/list")
# async def list_rules_paginated(
#     session: SessionDep,
#     current_user: CurrentUser,
#     pageNum: int = Query(1, description="页码"),
#     pageSize: int = Query(10, description="每页数量"),
#     keyword: Optional[str] = Query(None, description="搜索关键字")
# ):
#     """分页获取权限规则组列表"""
#     pagination = PaginationParams(page=pageNum, size=pageSize)
#     paginator = Paginator(session)
#     return await paginator.get_paginated_response(
#         stmt=DsRules,
#         pagination=pagination,
#         keyword=keyword
#     )
@router.post("/list")
async def list_rules_paginated(
    session: SessionDep,
    current_user: CurrentUser,
    pageNum: int = Query(1, description="页码"),
    pageSize: int = Query(10, description="每页数量")
):
    """分页获取权限规则组列表"""
    rules = get_all_rules(session)

    # 转换数据格式以匹配前端期望
    formatted_rules = []
    for rule in rules:
        formatted_rule = {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "enable": rule.enable,
            "create_time": rule.create_time,
            # 将 JSON 字符串解析为数组
            "permissions": json.loads(rule.permission_list) if rule.permission_list else [],
            "users": json.loads(rule.user_list) if rule.user_list else [],
        }

        # 进一步处理 permissions 数组中的嵌套 JSON 字符串
        for perm in formatted_rule["permissions"]:
            if isinstance(perm.get("expression_tree"), str):
                perm["expression_tree"] = json.loads(perm["expression_tree"])
                perm["tree"] = perm["expression_tree"]  # 前端需要 tree 字段
            if isinstance(perm.get("permissions"), str):
                perm["permission_list"] = json.loads(perm["permissions"])

        formatted_rules.append(formatted_rule)

    return {
        "items": formatted_rules,
        "total": len(formatted_rules),
        "page": pageNum,
        "size": pageSize,
        "total_pages": (len(formatted_rules) + pageSize - 1) // pageSize
    }


# @router.post("/save")
# @require_space_admin
# async def save_rule(session: SessionDep, trans: Trans, current_user: CurrentUser, rule: dict):
#     """保存权限规则组(创建或更新)"""
#     # 如果有 id 则更新,否则创建
#     if rule.get('id'):
#         # 更新现有规则
#         db_rule = session.get(DsRules, rule['id'])
#         if not db_rule:
#             raise HTTPException(status_code=404, detail="Rule not found")

#         # 更新字段
#         db_rule.name = rule.get('name', db_rule.name)
#         db_rule.permission_list = rule.get(
#             'permissions', db_rule.permission_list)
#         db_rule.user_list = rule.get('users', db_rule.user_list)

#         session.commit()
#         session.refresh(db_rule)
#         return db_rule
#     else:
#         # 创建新规则
#         import json
#         from datetime import datetime

#         new_rule = DsRules(
#             enable=True,
#             name=rule['name'],
#             permission_list=json.dumps(rule.get('permissions', [])),
#             user_list=json.dumps(rule.get('users', [])),
#             create_time=datetime.now()
#         )
#         session.add(new_rule)
#         session.commit()
#         session.refresh(new_rule)
#         return new_rule

@router.post("/save")
@require_space_admin
async def save_rule(session: SessionDep, trans: Trans, current_user: CurrentUser, rule: dict):
    """保存权限规则组(创建或更新)"""
    import json
    from datetime import datetime

    # 如果有 id 则更新,否则创建
    if rule.get('id'):
        # 更新现有规则
        db_rule = session.get(DsRules, rule['id'])
        if not db_rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        # 更新字段 - 关键:将数组转换为 JSON 字符串
        db_rule.name = rule.get('name', db_rule.name)
        db_rule.permission_list = json.dumps(
            rule.get('permissions', []))  # 序列化为 JSON 字符串
        db_rule.user_list = json.dumps(rule.get('users', []))  # 序列化为 JSON 字符串

        session.commit()
        session.refresh(db_rule)
        return db_rule
    else:
        # 创建新规则
        new_rule = DsRules(
            enable=True,
            name=rule['name'],
            permission_list=json.dumps(
                rule.get('permissions', [])),  # 序列化为 JSON 字符串
            user_list=json.dumps(rule.get('users', [])),  # 序列化为 JSON 字符串
            create_time=datetime.now()
        )
        session.add(new_rule)
        session.commit()
        session.refresh(new_rule)
        return new_rule


@router.post("/delete/{rule_id}")
@require_space_admin
async def delete_rule_api(session: SessionDep, trans: Trans, current_user: CurrentUser, rule_id: int):
    """删除权限规则组"""
    rule = session.get(DsRules, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    session.delete(rule)
    session.commit()
    return {"success": True}


@router.get("/rules")
async def list_all_rules(session: SessionDep, current_user: CurrentUser):
    """获取所有权限规则组(不分页)"""
    return get_all_rules(session)


@router.get("/rule/{rule_id}")
async def get_rule(session: SessionDep, current_user: CurrentUser, rule_id: int):
    """获取单个权限规则组详情"""
    rule = session.get(DsRules, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/rule")
@require_space_admin
async def add_rule(session: SessionDep, trans: Trans, current_user: CurrentUser, rule: DsRules):
    """创建权限规则组"""
    return create_rule(session, rule)


@router.put("/rule")
@require_space_admin
async def update_rule_api(session: SessionDep, trans: Trans, current_user: CurrentUser, rule: DsRules):
    """更新权限规则组"""
    return update_rule(session, rule)


@router.delete("/rule/{rule_id}")
@require_space_admin
async def delete_rule_api(session: SessionDep, trans: Trans, current_user: CurrentUser, rule_id: int):
    """删除权限规则组"""
    return delete_rule(session, rule_id)

# ============ 权限规则管理 ============


@router.get("/permissions/table/{table_id}")
async def get_table_permissions(
    session: SessionDep,
    current_user: CurrentUser,
    table_id: int
):
    """获取指定表的所有权限规则"""
    return get_permissions_by_table(session, table_id)


@router.post("/permission")
@require_space_admin
async def add_permission(
    session: SessionDep,
    trans: Trans,
    current_user: CurrentUser,
    permission: DsPermission
):
    """创建权限规则"""
    return create_permission(session, permission)


@router.put("/permission")
@require_space_admin
async def update_permission_api(
    session: SessionDep,
    trans: Trans,
    current_user: CurrentUser,
    permission: DsPermission
):
    """更新权限规则"""
    return update_permission(session, permission)


@router.delete("/permission/{permission_id}")
@require_space_admin
async def delete_permission_api(
    session: SessionDep,
    trans: Trans,
    current_user: CurrentUser,
    permission_id: int
):
    """删除权限规则"""
    return delete_permission(session, permission_id)
