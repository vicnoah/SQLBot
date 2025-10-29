import json
from typing import List, Optional

from sqlalchemy import and_
from apps.datasource.crud.row_permission import transFilterTree
from apps.datasource.models.datasource import CoreDatasource, CoreField, CoreTable
from common.core.deps import CurrentUser, SessionDep
# License functionality removed - permission system simplified
# from sqlbot_xpack.permissions.api.permission import transRecord2DTO
# from sqlbot_xpack.permissions.models.ds_permission import DsPermission, PermissionDTO
# from sqlbot_xpack.permissions.models.ds_rules import DsRules


def get_row_permission_filters(session: SessionDep, current_user: CurrentUser, ds: CoreDatasource,
                               tables: Optional[list] = None, single_table: Optional[CoreTable] = None):
    """简化的行权限过滤器 - 暂时返回空列表，不进行权限控制"""
    # License functionality removed - no row-level permissions
    return []


def get_column_permission_fields(session: SessionDep, current_user: CurrentUser, table: CoreTable,
                                 fields: list[CoreField]):
    """简化的列权限检查 - 返回所有字段，不进行权限控制"""
    # License functionality removed - no column-level permissions
    return fields


def is_normal_user(current_user: CurrentUser):
    return current_user.id != 1


def filter_list(list_a, list_b):
    id_to_invalid = {}
    for b in list_b:
        if not b['enable']:
            id_to_invalid[b['field_id']] = True

    return [a for a in list_a if not id_to_invalid.get(a.id, False)]
