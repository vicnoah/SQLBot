# API参考

<cite>
**本文档中引用的文件**  
- [chat.py](file://backend/apps/chat/api/chat.py)
- [datasource.py](file://backend/apps/datasource/api/datasource.py)
- [dashboard_api.py](file://backend/apps/dashboard/api/dashboard_api.py)
- [user.py](file://backend/apps/system/api/user.py)
- [workspace.py](file://backend/apps/system/api/workspace.py)
- [config.py](file://backend/common/core/config.py)
- [security.py](file://backend/common/core/security.py)
- [auth.py](file://backend/apps/system/middleware/auth.py)
- [schemas.py](file://backend/common/core/schemas.py)
</cite>

## 目录
1. [简介](#简介)
2. [API版本控制](#api版本控制)
3. [认证与安全](#认证与安全)
4. [核心API端点](#核心api端点)
   1. [/chat - 对话服务](#chat---对话服务)
   2. [/datasource - 数据源管理](#datasource---数据源管理)
   3. [/dashboard - 仪表板管理](#dashboard---仪表板管理)
   4. [/user - 用户管理](#user---用户管理)
   5. [/workspace - 工作空间管理](#workspace---工作空间管理)
5. [错误处理](#错误处理)
6. [使用模式](#使用模式)

## 简介
SQLBot公共API为系统的核心功能提供了程序化访问接口。本参考文档详细说明了主要API端点，包括/chat、/datasource、/dashboard、/user和/workspace等核心功能组。API遵循RESTful设计原则，支持JSON请求/响应格式，并通过JWT进行安全认证。

**API基础URL**: `http://your-sqlbot-instance.com/api/v1`

**Section sources**
- [config.py](file://backend/common/core/config.py#L29)

## API版本控制
SQLBot API通过URL路径实现版本控制，当前版本为v1。所有API端点均以`/api/v1`为前缀。

版本信息在`backend/common/core/config.py`中定义：
```python
API_V1_STR: str = "/api/v1"
```

此设计允许未来版本的API共存，确保向后兼容性。客户端应在所有请求中包含此版本前缀。

**Section sources**
- [config.py](file://backend/common/core/config.py#L29)

## 认证与安全
SQLBot API采用基于JWT（JSON Web Token）的认证机制，所有受保护的端点都需要有效的认证令牌。

### 认证头
- **标准认证**: `X-SQLBOT-TOKEN: Bearer <JWT_TOKEN>`
- **助手认证**: `X-SQLBOT-ASSISTANT-TOKEN: Assistant <JWT_TOKEN>`
- **嵌入式认证**: `X-SQLBOT-ASSISTANT-TOKEN: Embedded <JWT_TOKEN>`

令牌通过`backend/apps/system/middleware/auth.py`中的`TokenMiddleware`类进行验证。该中间件处理所有传入请求，验证JWT签名和有效期，并将用户信息注入请求上下文。

### JWT结构
认证令牌包含以下声明：
- `id`: 用户ID
- `exp`: 过期时间戳
- `assistant_id`: （可选）助手ID

令牌使用HS256算法和服务器端`SECRET_KEY`进行签名。

### 敏感数据过滤
系统自动过滤敏感信息，如密码字段。响应中不会包含完整的用户凭证信息。

**Section sources**
- [auth.py](file://backend/apps/system/middleware/auth.py#L20-L198)
- [security.py](file://backend/common/core/security.py#L1-L44)
- [config.py](file://backend/common/core/config.py#L27)

## 核心API端点

### /chat - 对话服务
对话API支持自然语言查询、SQL生成、数据分析和预测功能。

#### 获取对话列表
- **HTTP方法**: `GET`
- **URL路径**: `/api/v1/chat/list`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体**: 无
- **响应格式**: 
```json
{
  "items": [
    {
      "id": 1,
      "name": "对话1",
      "create_time": 1700000000,
      "update_time": 1700000000
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "total_pages": 1
}
```

#### 开始新对话
- **HTTP方法**: `POST`
- **URL路径**: `/api/v1/chat/start`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体schema**:
```json
{
  "question": "查询销售额",
  "datasource": 1,
  "origin": 0
}
```
- **响应格式**: 同获取对话列表

#### 流式查询
- **HTTP方法**: `POST`
- **URL路径**: `/api/v1/chat/question`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体schema**:
```json
{
  "question": "上季度销售额是多少？",
  "chat_id": 1
}
```
- **响应格式**: `text/event-stream` (SSE)

**curl示例**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/question \
  -H "X-SQLBOT-TOKEN: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"question": "上季度销售额", "chat_id": 1}'
```

**Section sources**
- [chat.py](file://backend/apps/chat/api/chat.py#L0-L228)

### /datasource - 数据源管理
数据源API提供对数据库连接的CRUD操作和数据预览功能。

#### 获取数据源列表
- **HTTP方法**: `GET`
- **URL路径**: `/api/v1/datasource/list`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体**: 无
- **响应格式**:
```json
[
  {
    "id": 1,
    "name": "生产数据库",
    "type": "mysql",
    "host": "prod-db.example.com",
    "port": 3306,
    "database": "sales"
  }
]
```

#### 添加数据源
- **HTTP方法**: `POST`
- **URL路径**: `/api/v1/datasource/add`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体schema**:
```json
{
  "name": "新数据源",
  "type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "username": "user",
  "password": "pass",
  "database": "mydb"
}
```
- **响应格式**: 同获取数据源列表中的单个项

#### 上传Excel文件
- **HTTP方法**: `POST`
- **URL路径**: `/api/v1/datasource/uploadExcel`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体**: `multipart/form-data` 包含文件
- **响应格式**:
```json
{
  "filename": "data_abc123.xlsx",
  "sheets": [
    {"tableName": "sheet1_abc123", "tableComment": ""}
  ]
}
```

**curl示例**:
```bash
curl -X POST http://localhost:8000/api/v1/datasource/uploadExcel \
  -H "X-SQLBOT-TOKEN: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@data.xlsx"
```

**Section sources**
- [datasource.py](file://backend/apps/datasource/api/datasource.py#L0-L328)

### /dashboard - 仪表板管理
仪表板API支持仪表板的创建、更新、删除和加载操作。

#### 创建仪表板
- **HTTP方法**: `POST`
- **URL路径**: `/api/v1/dashboard/create_resource`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体schema**:
```json
{
  "name": "销售仪表板",
  "config": {
    "layout": "grid",
    "theme": "dark"
  }
}
```
- **响应格式**:
```json
{
  "id": "dash_123",
  "name": "销售仪表板",
  "config": {...},
  "create_time": 1700000000
}
```

#### 加载仪表板
- **HTTP方法**: `POST`
- **URL路径**: `/api/v1/dashboard/load_resource`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体schema**:
```json
{
  "id": "dash_123"
}
```
- **响应格式**: 同创建仪表板响应

#### 删除仪表板
- **HTTP方法**: `DELETE`
- **URL路径**: `/api/v1/dashboard/delete_resource/{resource_id}`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **路径参数**: `resource_id` - 仪表板ID
- **响应格式**: `200 OK` 或错误响应

**Section sources**
- [dashboard_api.py](file://backend/apps/dashboard/api/dashboard_api.py#L0-L48)

### /user - 用户管理
用户API提供用户信息查询、创建、更新和密码管理功能。

#### 获取当前用户信息
- **HTTP方法**: `GET`
- **URL路径**: `/api/v1/user/info`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体**: 无
- **响应格式**:
```json
{
  "id": 1,
  "account": "admin",
  "name": "Administrator",
  "email": "admin@sqlbot.local",
  "oid": 1,
  "status": 1
}
```

#### 分页查询用户
- **HTTP方法**: `GET`
- **URL路径**: `/api/v1/user/pager/{pageNum}/{pageSize}`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **路径参数**:
  - `pageNum`: 页码
  - `pageSize`: 每页大小
- **查询参数**:
  - `keyword`: 搜索关键字
  - `status`: 用户状态
  - `oidlist`: 工作空间ID列表
- **响应格式**:
```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "size": 20,
  "total_pages": 1
}
```

#### 修改密码
- **HTTP方法**: `PUT`
- **URL路径**: `/api/v1/user/pwd`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体schema**:
```json
{
  "pwd": "旧密码",
  "new_pwd": "新密码"
}
```
- **响应格式**: `200 OK` 或错误响应

**Section sources**
- [user.py](file://backend/apps/system/api/user.py#L0-L236)

### /workspace - 工作空间管理
工作空间API管理多租户环境下的工作空间和用户分配。

#### 获取工作空间列表
- **HTTP方法**: `GET`
- **URL路径**: `/api/v1/system/workspace`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体**: 无
- **响应格式**:
```json
[
  {
    "id": 1,
    "name": "主工作空间",
    "create_time": 1700000000
  }
]
```

#### 为用户分配工作空间
- **HTTP方法**: `POST`
- **URL路径**: `/api/v1/system/workspace/uws`
- **认证要求**: 是（管理员）
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **请求体schema**:
```json
{
  "oid": 1,
  "uid_list": [1, 2, 3],
  "weight": 1
}
```
- **响应格式**: `200 OK` 或错误响应

#### 分页查询工作空间用户
- **HTTP方法**: `GET`
- **URL路径**: `/api/v1/system/workspace/uws/pager/{pageNum}/{pageSize}`
- **认证要求**: 是
- **请求头**: `X-SQLBOT-TOKEN: Bearer <token>`
- **路径参数**:
  - `pageNum`: 页码
  - `pageSize`: 每页大小
- **查询参数**:
  - `keyword`: 搜索关键字
  - `oid`: 工作空间ID
- **响应格式**: 分页响应格式

**Section sources**
- [workspace.py](file://backend/apps/system/api/workspace.py#L0-L225)

## 错误处理
API使用标准HTTP状态码表示请求结果，并提供详细的错误信息。

### 常见错误码
- `400 Bad Request`: 请求参数无效或缺失
- `401 Unauthorized`: 认证失败或令牌过期
- `403 Forbidden`: 无权访问资源
- `404 Not Found`: 请求的资源不存在
- `500 Internal Server Error`: 服务器内部错误

### 异常响应格式
```json
{
  "message": "详细的错误描述"
}
```

对于流式响应（如/chat/question），错误通过SSE事件发送：
```
event: error
data: {"message": "错误详情"}
```

**Section sources**
- [auth.py](file://backend/apps/system/middleware/auth.py#L20-L198)
- [schemas.py](file://backend/common/core/schemas.py#L46-L51)

## 使用模式
### 分页参数
大多数列表端点支持分页，使用以下参数：
- `pageNum`: 页码（从1开始）
- `pageSize`: 每页项目数
- 返回的`PaginatedResponse`包含分页元数据

### 流式响应处理
/chat端点使用SSE（Server-Sent Events）提供流式响应。客户端应：
1. 设置`Accept: text/event-stream`头
2. 处理`data:`事件流
3. 监听`error`事件以处理异常
4. 实现连接重试逻辑

### 认证令牌管理
- 令牌有效期由`ACCESS_TOKEN_EXPIRE_MINUTES`配置（默认8天）
- 客户端应在`401 Unauthorized`响应后重新认证
- 令牌应安全存储，避免泄露