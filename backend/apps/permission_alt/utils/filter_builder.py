import json  
from typing import List  
from sqlmodel import Session  
from apps.datasource.models.datasource import CoreDatasource  
from ..models.permission_models import DsPermission  
  
def build_sql_filter(session: Session, permissions: List[DsPermission], ds: CoreDatasource) -> str:  
    """  
    将权限表达式树转换为SQL WHERE条件  
      
    Args:  
        session: 数据库会话  
        permissions: 权限列表  
        ds: 数据源对象  
          
    Returns:  
        SQL WHERE条件字符串  
    """  
    if not permissions:  
        return ""  
      
    # 合并多个权限的过滤条件(使用OR连接)  
    filter_parts = []  
    for permission in permissions:  
        if permission.expression_tree:  
            tree = json.loads(permission.expression_tree) if isinstance(permission.expression_tree, str) else permission.expression_tree  
            filter_sql = convert_tree_to_sql(tree, ds.type)  
            if filter_sql:  
                filter_parts.append(f"({filter_sql})")  
      
    return " OR ".join(filter_parts) if filter_parts else ""  
  
def convert_tree_to_sql(tree: dict, db_type: str) -> str:  
    """  
    将表达式树转换为SQL条件  
      
    表达式树格式:  
    {  
        "logic": "and" | "or",  
        "children": [  
            {  
                "field": "字段名",  
                "operator": "eq" | "ne" | "gt" | "lt" | ...,  
                "value": "值"  
            },  
            ...  
        ]  
    }  
    """  
    if not tree or not tree.get('children'):  
        return ""  
      
    logic = tree.get('logic', 'and').upper()  
    conditions = []  
      
    for child in tree['children']:  
        if 'children' in child:  
            # 递归处理嵌套条件  
            sub_condition = convert_tree_to_sql(child, db_type)  
            if sub_condition:  
                conditions.append(f"({sub_condition})")  
        else:  
            # 处理单个条件  
            condition = build_condition(child, db_type)  
            if condition:  
                conditions.append(condition)  
      
    return f" {logic} ".join(conditions) if conditions else ""  
  
def build_condition(item: dict, db_type: str) -> str:  
    """  
    构建单个过滤条件  
      
    Args:  
        item: 条件项,包含 field, operator, value  
        db_type: 数据库类型  
          
    Returns:  
        SQL条件字符串  
    """  
    field_name = item.get('field')  
    operator = item.get('operator')  
    value = item.get('value')  
      
    if not field_name or not operator:  
        return ""  
      
    # 根据数据库类型添加字段引号  
    if db_type in ['mysql', 'doris']:  
        quoted_field = f"`{field_name}`"  
    elif db_type in ['pg', 'oracle', 'ck', 'dm', 'excel', 'redshift']:  
        quoted_field = f'"{field_name}"'  
    elif db_type == 'sqlServer':  
        quoted_field = f"[{field_name}]"  
    else:  
        quoted_field = field_name  
      
    # 处理不同的操作符  
    if operator == 'eq':  
        return f"{quoted_field} = '{value}'"  
    elif operator == 'ne':  
        return f"{quoted_field} <> '{value}'"  
    elif operator == 'gt':  
        return f"{quoted_field} > '{value}'"  
    elif operator == 'lt':  
        return f"{quoted_field} < '{value}'"  
    elif operator == 'gte':  
        return f"{quoted_field} >= '{value}'"  
    elif operator == 'lte':  
        return f"{quoted_field} <= '{value}'"  
    elif operator == 'in':  
        values = value.split(',') if isinstance(value, str) else value  
        quoted_values = "', '".join(values)  
        return f"{quoted_field} IN ('{quoted_values}')"  
    elif operator == 'not_in':  
        values = value.split(',') if isinstance(value, str) else value  
        quoted_values = "', '".join(values)  
        return f"{quoted_field} NOT IN ('{quoted_values}')"  
    elif operator == 'like':  
        return f"{quoted_field} LIKE '%{value}%'"  
    elif operator == 'not_like':  
        return f"{quoted_field} NOT LIKE '%{value}%'"  
    elif operator == 'is_null':  
        return f"{quoted_field} IS NULL"  
    elif operator == 'is_not_null':  
        return f"{quoted_field} IS NOT NULL"  
      
    return ""