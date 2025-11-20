import json
from typing import List
from sqlmodel import Session
from apps.datasource.models.datasource import CoreDatasource, CoreField
from apps.db.constant import DB
from ..models.permission_models import DsPermission


def build_sql_filter(session: Session, permissions: List[DsPermission], ds: CoreDatasource) -> str:
    """  
    将权限表达式树转换为SQL WHERE条件  
    """
    if not permissions:
        return ""

    filter_parts = []
    for permission in permissions:
        if permission.expression_tree:
            tree = json.loads(permission.expression_tree) if isinstance(
                permission.expression_tree, str) else permission.expression_tree
            filter_sql = convert_tree_to_sql(session, tree, ds)
            if filter_sql:
                filter_parts.append(f"({filter_sql})")

    return " OR ".join(filter_parts) if filter_parts else ""


def convert_tree_to_sql(session: Session, tree: dict, ds: CoreDatasource) -> str:
    """  
    将表达式树转换为SQL条件  

    实际格式:  
    {  
        "logic": "and" | "or",  
        "items": [...]  # 注意是 items 不是 children  
    }  
    """
    if not tree or not tree.get('items'):
        return ""

    logic = tree.get('logic', 'and').upper()
    conditions = []

    for item in tree['items']:
        if item.get('type') == 'tree' and item.get('sub_tree'):
            # 递归处理嵌套条件
            sub_condition = convert_tree_to_sql(session, item['sub_tree'], ds)
            if sub_condition:
                conditions.append(f"({sub_condition})")
        elif item.get('type') == 'item':
            # 处理单个条件
            condition = build_condition(session, item, ds)
            if condition:
                conditions.append(condition)

    return f" {logic} ".join(conditions) if conditions else ""


def build_condition(session: Session, item: dict, ds: CoreDatasource) -> str:
    """  
    构建单个过滤条件  

    item 格式:  
    {  
        "field_id": 777,  
        "term": "eq",  
        "value": "2",  
        "filter_type": "logic" | "enum",  
        "enum_value": []  
    }  
    """
    field_id = item.get('field_id')
    if not field_id:
        return ""

    # 通过 field_id 查询字段信息
    field = session.get(CoreField, field_id)
    if not field:
        return ""

    # 获取数据库特定的字段引号
    db = DB.get_db(ds.type)
    quoted_field = db.prefix + field.field_name + db.suffix

    # 处理枚举类型过滤
    if item.get('filter_type') == 'enum':
        enum_values = item.get('enum_value', [])
        if not enum_values:
            return ""

        # 处理 SQL Server 的 NCHAR/NVARCHAR 类型
        if ds.type == 'sqlServer' and field.field_type.upper() in ['NCHAR', 'NVARCHAR']:
            return f"({quoted_field} IN (N'" + "',N'".join(enum_values) + "'))"
        else:
            return f"({quoted_field} IN ('" + "','".join(enum_values) + "'))"

    # 处理逻辑类型过滤
    term = item.get('term')
    value = item.get('value', '')

    if not term:
        return ""

    # 转换操作符
    operator = convert_term_to_operator(term)

    # 处理不同的操作符
    if term == 'null':
        return f"{quoted_field} IS NULL"
    elif term == 'not_null':
        return f"{quoted_field} IS NOT NULL"
    elif term == 'empty':
        return f"{quoted_field} = ''"
    elif term == 'not_empty':
        return f"{quoted_field} <> ''"
    elif term in ['in', 'not in']:
        values = value.split(',') if isinstance(value, str) else value
        if ds.type == 'sqlServer' and field.field_type.upper() in ['NCHAR', 'NVARCHAR']:
            return f"{quoted_field}{operator}(N'" + "', N'".join(values) + "')"
        else:
            return f"{quoted_field}{operator}('" + "', '".join(values) + "')"
    elif term in ['like', 'not like']:
        if ds.type == 'sqlServer' and field.field_type.upper() in ['NCHAR', 'NVARCHAR']:
            return f"{quoted_field}{operator}N'%{value}%'"
        else:
            return f"{quoted_field}{operator}'%{value}%'"
    else:
        # 标准比较操作符
        if ds.type == 'sqlServer' and field.field_type.upper() in ['NCHAR', 'NVARCHAR']:
            return f"{quoted_field}{operator}N'{value}'"
        else:
            return f"{quoted_field}{operator}'{value}'"


def convert_term_to_operator(term: str) -> str:
    """将 term 转换为 SQL 操作符"""
    term_map = {
        "eq": " = ",
        "not_eq": " <> ",
        "lt": " < ",
        "le": " <= ",
        "gt": " > ",
        "ge": " >= ",
        "in": " IN ",
        "not in": " NOT IN ",
        "like": " LIKE ",
        "not like": " NOT LIKE ",
        "between": " BETWEEN "
    }
    return term_map.get(term, " = ")
