from datetime import datetime
from typing import Optional
from sqlalchemy import Column, BigInteger, DateTime, Identity, Boolean, Text
from sqlmodel import SQLModel, Field


class DsPermission(SQLModel, table=True):
    """数据源权限表"""
    __tablename__ = "ds_permission"

    id: int = Field(sa_column=Column(BigInteger, Identity(
        always=True), nullable=False, primary_key=True))
    enable: bool = Field(default=True)
    auth_target_type: str = Field(max_length=128)  # 授权目标类型
    auth_target_id: Optional[int] = None
    type: str = Field(max_length=64)  # 'row' 或 'column'
    ds_id: Optional[int] = None
    table_id: Optional[int] = None
    expression_tree: Optional[str] = None  # JSON字符串
    permissions: Optional[str] = None  # JSON字符串
    white_list_user: Optional[str] = None
    create_time: Optional[datetime] = None
    name: str = Field(max_length=128)


class DsRules(SQLModel, table=True):
    """权限规则组表"""
    __tablename__ = "ds_rules"

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={
                              "autoincrement": True})
    enable: bool = Field(default=True)
    name: str = Field(max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    permission_list: Optional[str] = None  # JSON数组
    user_list: Optional[str] = None  # JSON数组
    white_list_user: Optional[str] = None
    create_time: Optional[datetime] = None


class PermissionDTO(SQLModel):
    """权限数据传输对象"""
    id: int
    type: str
    table_id: int
    expression_tree: Optional[dict] = None
    permissions: Optional[list] = None
