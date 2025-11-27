import json
from typing import List, Optional

from fastapi import HTTPException
from common.utils.utils import SQLBotLogUtil
from sqlalchemy import select, and_
from sqlmodel import Session

from apps.datasource.models.datasource import CoreDatasource, CoreField, CoreTable
from common.core.deps import CurrentUser
from ..models.permission_models import DsPermission, DsRules, PermissionDTO
from ..utils.filter_builder import build_sql_filter


def is_normal_user(current_user: CurrentUser) -> bool:
    """判断是否为普通用户(非系统管理员)"""
    return current_user.id != 1


def get_row_permission_filters(
    session: Session,
    current_user: CurrentUser,
    ds: CoreDatasource,
    tables: Optional[list] = None,
    single_table: Optional[CoreTable] = None
) -> List[dict]:
    """  
    获取行权限过滤条件  

    Args:  
        session: 数据库会话  
        current_user: 当前用户  
        ds: 数据源对象  
        tables: 表名列表  
        single_table: 单个表对象  

    Returns:  
        [{"table": "表名", "filter": "WHERE条件"}, ...]  
    """
    # 获取表列表
    if single_table:
        table_list = [session.get(CoreTable, single_table.id)]
    else:
        table_list = session.query(CoreTable).filter(
            and_(CoreTable.ds_id == ds.id, CoreTable.table_name.in_(tables))
        ).all()

    filters = []

    # 只对普通用户应用权限
    if not is_normal_user(current_user):
        return filters

    # 获取所有规则组
    contain_rules = session.query(DsRules).filter(DsRules.enable == True).all()

    for table in table_list:
        # 查询该表的行权限
        row_permissions = session.query(DsPermission).filter(
            and_(
                DsPermission.table_id == table.id,
                DsPermission.type == 'row',
                DsPermission.enable == True
            )
        ).all()

        # 过滤出用户关联的权限
        user_permissions = []
        for permission in row_permissions:
            # 检查权限和用户是否在同一规则组中
            for rule in contain_rules:
                p_list = json.loads(
                    rule.permission_list) if rule.permission_list else []
                u_list = json.loads(rule.user_list) if rule.user_list else []

                if (permission.id in p_list and
                        (current_user.id in u_list or str(current_user.id) in u_list)):
                    user_permissions.append(permission)
                    break

        # 构建WHERE条件
        where_str = build_sql_filter(session, user_permissions, ds)
        filters.append({"table": table.table_name, "filter": where_str})

    return filters


def get_column_permission_fields(
    session: Session,
    current_user: CurrentUser,
    table: CoreTable,
    fields: List[CoreField],
    contain_rules: List[DsRules]
) -> List[CoreField]:
    """  
    获取列权限过滤后的字段列表  

    Args:  
        session: 数据库会话  
        current_user: 当前用户  
        table: 数据表对象  
        fields: 原始字段列表  
        contain_rules: 规则组列表  

    Returns:  
        过滤后的字段列表  
    """
    # 非普通用户不过滤
    if not is_normal_user(current_user):
        return fields

    # 查询该表的列权限
    column_permissions = session.query(DsPermission).filter(
        and_(
            DsPermission.table_id == table.id,
            DsPermission.type == 'column',
            DsPermission.enable == True
        )
    ).all()

    SQLBotLogUtil.info(f"column_permissions: {column_permissions}")
    SQLBotLogUtil.info(f"contain_rules: {contain_rules}")

    if not column_permissions:
        return fields

    # 过滤出用户关联的权限
    for permission in column_permissions:
        # 检查权限和用户是否在同一规则组中
        for rule in contain_rules:
            p_list = json.loads(
                rule.permission_list) if rule.permission_list else []
            u_list = json.loads(rule.user_list) if rule.user_list else []

            if (permission.id in p_list and
                    (current_user.id in u_list or str(current_user.id) in u_list)):
                # 应用列权限过滤
                permission_list = json.loads(
                    permission.permissions) if permission.permissions else []
                fields = filter_fields_by_permission(fields, permission_list)
                break

    return fields


def create_permission(session: Session, permission: DsPermission) -> DsPermission:
    """创建权限规则"""
    session.add(permission)
    session.commit()
    session.refresh(permission)
    return permission


def update_permission(session: Session, permission: DsPermission) -> DsPermission:
    """更新权限规则"""
    db_permission = session.get(DsPermission, permission.id)
    if not db_permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    for key, value in permission.dict(exclude_unset=True).items():
        setattr(db_permission, key, value)

    session.commit()
    session.refresh(db_permission)
    return db_permission


def delete_permission(session: Session, permission_id: int) -> bool:
    """删除权限规则"""
    permission = session.get(DsPermission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    session.delete(permission)
    session.commit()
    return True


def get_permissions_by_table(session: Session, table_id: int) -> List[DsPermission]:
    """获取指定表的所有权限规则"""
    return session.query(DsPermission).filter(DsPermission.table_id == table_id).all()


def create_rule(session: Session, rule: DsRules) -> DsRules:
    """创建权限规则组"""
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def update_rule(session: Session, rule: DsRules) -> DsRules:
    """更新权限规则组"""
    db_rule = session.get(DsRules, rule.id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for key, value in rule.dict(exclude_unset=True).items():
        setattr(db_rule, key, value)

    session.commit()
    session.refresh(db_rule)
    return db_rule


def delete_rule(session: Session, rule_id: int) -> bool:
    """删除权限规则组"""
    rule = session.get(DsRules, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    session.delete(rule)
    session.commit()
    return True


def get_all_rules(session: Session) -> List[DsRules]:
    """获取所有权限规则组"""
    return session.query(DsRules).filter(DsRules.enable == True).all()


def get_rules_paginated(
    session: Session,
    page: int,
    size: int,
    keyword: Optional[str] = None
):
    """分页获取规则组"""
    stmt = select(DsRules).where(DsRules.enable == True)

    if keyword:
        stmt = stmt.where(DsRules.name.ilike(f"%{keyword}%"))

    stmt = stmt.order_by(DsRules.create_time.desc())

    # 这里返回 statement,让 Paginator 处理分页
    return stmt

def filter_fields_by_permission(fields: List[CoreField], permission_list: list) -> List[CoreField]:
    """根据权限列表过滤字段"""
    # 如果没有权限配置,返回所有字段
    if not permission_list:
        return fields

    # 构建允许访问的字段映射(使用 field_id 作为键)
    allowed_fields = {}
    for perm in permission_list:
        if perm.get('enable', False):  # 只记录 enable=true 的字段
            # 使用 field_id 作为键,这是权限配置中的字段标识
            allowed_fields[perm['field_id']] = True

    # 只保留允许访问的字段
    # 注意:这里需要用 CoreField.id 与 permission 中的 field_id 匹配
    return [f for f in fields if allowed_fields.get(f.id, False)]
