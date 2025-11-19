import pytest  
from apps.permission_alt.crud.permission_crud import get_row_permission_filters, is_normal_user  
from apps.permission_alt.utils.filter_builder import convert_tree_to_sql  
  
def test_is_normal_user():  
    """测试普通用户判断"""  
    # 创建测试用户对象  
    admin_user = type('User', (), {'id': 1})()  
    normal_user = type('User', (), {'id': 2})()  
      
    assert not is_normal_user(admin_user)  
    assert is_normal_user(normal_user)  
  
def test_convert_tree_to_sql():  
    """测试表达式树转SQL"""  
    tree = {  
        "logic": "and",  
        "children": [  
            {"field": "age", "operator": "gt", "value": "18"},  
            {"field": "status", "operator": "eq", "value": "active"}  
        ]  
    }  
      
    sql = convert_tree_to_sql(tree, "mysql")  
    assert "`age` > '18'" in sql  
    assert "`status` = 'active'" in sql  
    assert "AND" in sql