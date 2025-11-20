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
    from apps.datasource.models.datasource import CoreDatasource, CoreTable

    rules = get_all_rules(session)

    formatted_rules = []
    for rule in rules:
        # 解析 permission_list
        try:
            permission_ids = json.loads(
                rule.permission_list) if rule.permission_list else []
        except (json.JSONDecodeError, TypeError):
            permission_ids = []

        # 解析 user_list
        try:
            users = json.loads(
                rule.user_list) if rule.user_list else []
        except (json.JSONDecodeError, TypeError, ValueError):
            users = []

        # 查询权限详情并补充名称信息
        permissions = []
        for perm_id in permission_ids:
            db_perm = session.get(DsPermission, perm_id)
            if db_perm:
                # 查询数据源名称
                ds_name = ""
                if db_perm.ds_id:
                    ds = session.get(CoreDatasource, db_perm.ds_id)
                    if ds:
                        ds_name = ds.name

                # 查询表名称
                table_name = ""
                if db_perm.table_id:
                    table = session.get(CoreTable, db_perm.table_id)
                    if table:
                        table_name = table.table_name

                # 构建权限对象
                perm_dict = {
                    "id": db_perm.id,
                    "name": db_perm.name,
                    "type": db_perm.type,
                    "ds_id": db_perm.ds_id,
                    "table_id": db_perm.table_id,
                    "ds_name": ds_name,  # 添加数据源名称
                    "table_name": table_name,  # 添加表名称
                    "expression_tree": json.loads(db_perm.expression_tree) if db_perm.expression_tree else {},
                    "tree": json.loads(db_perm.expression_tree) if db_perm.expression_tree else {},
                    "permissions": json.loads(db_perm.permissions) if db_perm.permissions else [],
                    "permission_list": json.loads(db_perm.permissions) if db_perm.permissions else []
                }
                permissions.append(perm_dict)

        formatted_rule = {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "enable": rule.enable,
            "create_time": rule.create_time,
            "permissions": permissions,
            "users": users
        }

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
#     import json
#     from datetime import datetime

#     permissions_data = rule.get('permissions', [])
#     users_data = rule.get('users', [])

#     # 第一步: 保存或更新权限规则到 ds_permission 表
#     permission_ids = []
#     for perm in permissions_data:
#         perm_id = perm.get('id')

#         # 判断是否为真实的数据库 ID
#         is_real_db_id = perm_id and isinstance(
#             perm_id, int) and perm_id < 2147483647

#         # 准备权限数据
#         permission_obj = DsPermission(
#             enable=True,
#             auth_target_type='USER',
#             type=perm.get('type'),
#             ds_id=perm.get('ds_id'),
#             table_id=perm.get('table_id'),
#             name=perm.get('name'),  # 添加这一行
#             expression_tree=perm.get('expression_tree') if isinstance(perm.get(
#                 'expression_tree'), str) else json.dumps(perm.get('expression_tree', {})),
#             permissions=perm.get('permissions') if isinstance(
#                 perm.get('permissions'), str) else json.dumps(perm.get('permissions', [])),
#             create_time=datetime.now()
#         )

#         if is_real_db_id:
#             # 更新现有权限
#             db_permission = session.get(DsPermission, perm_id)
#             if db_permission:
#                 db_permission.type = permission_obj.type
#                 db_permission.ds_id = permission_obj.ds_id
#                 db_permission.table_id = permission_obj.table_id
#                 db_permission.name = permission_obj.name  # 添加这一行
#                 db_permission.expression_tree = permission_obj.expression_tree
#                 db_permission.permissions = permission_obj.permissions
#                 session.commit()
#                 session.refresh(db_permission)
#                 permission_ids.append(db_permission.id)
#             else:
#                 raise HTTPException(
#                     status_code=404, detail="Permission not found")
#         else:
#             # 创建新权限
#             session.add(permission_obj)
#             session.commit()
#             session.refresh(permission_obj)
#             permission_ids.append(permission_obj.id)

#     # 第二步: 保存或更新规则组到 ds_rules 表
#     if rule.get('id'):
#         # 更新现有规则组
#         db_rule = session.get(DsRules, rule['id'])
#         if not db_rule:
#             raise HTTPException(status_code=404, detail="Rule not found")

#         db_rule.name = rule.get('name', db_rule.name)
#         db_rule.permission_list = json.dumps(permission_ids)
#         db_rule.user_list = json.dumps(users_data)

#         session.commit()
#         session.refresh(db_rule)
#         return db_rule
#     else:
#         # 创建新规则组
#         new_rule = DsRules(
#             enable=True,
#             name=rule['name'],
#             permission_list=json.dumps(permission_ids),
#             user_list=json.dumps(users_data),
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

    permissions_data = rule.get('permissions', [])
    users_data = rule.get('users', [])

    # 如果是更新操作,先获取旧的权限 ID 列表
    old_permission_ids = []
    if rule.get('id'):
        db_rule = session.get(DsRules, rule['id'])
        if db_rule and db_rule.permission_list:
            try:
                old_permission_ids = json.loads(db_rule.permission_list)
            except:
                old_permission_ids = []

    # 第一步: 保存或更新权限规则到 ds_permission 表
    permission_ids = []
    for perm in permissions_data:
        perm_id = perm.get('id')
        is_real_db_id = perm_id and isinstance(
            perm_id, int) and perm_id < 2147483647

        permission_obj = DsPermission(
            enable=True,
            auth_target_type='USER',
            type=perm.get('type'),
            ds_id=perm.get('ds_id'),
            table_id=perm.get('table_id'),
            name=perm.get('name'),
            expression_tree=perm.get('expression_tree') if isinstance(perm.get(
                'expression_tree'), str) else json.dumps(perm.get('expression_tree', {})),
            permissions=perm.get('permissions') if isinstance(
                perm.get('permissions'), str) else json.dumps(perm.get('permissions', [])),
            create_time=datetime.now()
        )

        if is_real_db_id:
            db_permission = session.get(DsPermission, perm_id)
            if db_permission:
                db_permission.type = permission_obj.type
                db_permission.ds_id = permission_obj.ds_id
                db_permission.table_id = permission_obj.table_id
                db_permission.name = permission_obj.name
                db_permission.expression_tree = permission_obj.expression_tree
                db_permission.permissions = permission_obj.permissions
                session.commit()
                session.refresh(db_permission)
                permission_ids.append(db_permission.id)
            else:
                raise HTTPException(
                    status_code=404, detail="Permission not found")
        else:
            session.add(permission_obj)
            session.commit()
            session.refresh(permission_obj)
            permission_ids.append(permission_obj.id)

    # 第二步: 删除不再被引用的权限记录
    if old_permission_ids:
        # 找出被删除的权限 ID
        deleted_permission_ids = set(old_permission_ids) - set(permission_ids)

        for perm_id in deleted_permission_ids:
            # 检查该权限是否被其他规则组引用
            other_rules = session.query(DsRules).filter(
                DsRules.id != rule.get('id')
            ).all()

            is_referenced = False
            for other_rule in other_rules:
                if other_rule.permission_list:
                    try:
                        other_perm_list = json.loads(
                            other_rule.permission_list)
                        if perm_id in other_perm_list:
                            is_referenced = True
                            break
                    except:
                        continue

            # 如果没有被其他规则组引用,则删除
            if not is_referenced:
                db_permission = session.get(DsPermission, perm_id)
                if db_permission:
                    session.delete(db_permission)
                    session.commit()

    # 第三步: 保存或更新规则组到 ds_rules 表
    if rule.get('id'):
        db_rule = session.get(DsRules, rule['id'])
        if not db_rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        db_rule.name = rule.get('name', db_rule.name)
        db_rule.permission_list = json.dumps(permission_ids)
        db_rule.user_list = json.dumps(users_data)

        session.commit()
        session.refresh(db_rule)
        return db_rule
    else:
        new_rule = DsRules(
            enable=True,
            name=rule['name'],
            permission_list=json.dumps(permission_ids),
            user_list=json.dumps(users_data),
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
