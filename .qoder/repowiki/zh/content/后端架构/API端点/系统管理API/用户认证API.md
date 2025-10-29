# 用户认证API

<cite>
**本文档引用的文件**
- [login.py](file://backend/apps/system/api/login.py)
- [auth.py](file://backend/apps/system/middleware/auth.py)
- [security.py](file://backend/common/core/security.py)
- [user.py](file://backend/apps/system/crud/user.py)
- [schemas.py](file://backend/common/core/schemas.py)
</cite>

## 目录
1. [简介](#简介)
2. [核心认证流程](#核心认证流程)
3. [JWT令牌生成机制](#jwt令牌生成机制)
4. [认证失败处理](#认证失败处理)
5. [客户端调用示例](#客户端调用示例)
6. [认证中间件工作原理](#认证中间件工作原理)
7. [总结](#总结)

## 简介
本文档详细描述了SQLBot系统的用户认证API，重点介绍`/login/access-token`端点的JWT认证机制。文档涵盖了从用户登录请求到令牌生成、验证的完整流程，以及相关的错误处理机制和客户端调用方式。

**Section sources**
- [login.py](file://backend/apps/system/api/login.py#L1-L34)

## 核心认证流程

用户认证流程通过`/login/access-token`端点实现，采用OAuth2PasswordRequestForm表单接收用户凭证。系统首先验证用户账户和密码，然后检查用户状态和工作区关联情况，最后生成JWT访问令牌。

```mermaid
sequenceDiagram
participant 客户端 as 客户端
participant 登录API as login.py
participant 认证函数 as authenticate()
participant 数据库 as 数据库
客户端->>登录API : POST /login/access-token
登录API->>认证函数 : 调用authenticate()
认证函数->>数据库 : 查询用户账户
数据库-->>认证函数 : 返回用户数据
认证函数->>认证函数 : 验证MD5密码
认证函数-->>登录API : 返回用户DTO或None
alt 认证成功
登录API->>登录API : 创建访问令牌
登录API-->>客户端 : 返回Token响应
else 认证失败
登录API-->>客户端 : 返回400错误
end
```

**Diagram sources**
- [login.py](file://backend/apps/system/api/login.py#L1-L34)
- [user.py](file://backend/apps/system/crud/user.py#L38-L44)

**Section sources**
- [login.py](file://backend/apps/system/api/login.py#L1-L34)
- [user.py](file://backend/apps/system/crud/user.py#L38-L44)

## JWT令牌生成机制

系统使用`create_access_token`函数生成JWT令牌，该函数接收用户数据和过期时间作为参数，创建包含过期时间声明的JWT令牌。

```mermaid
flowchart TD
Start([开始]) --> CopyData["复制用户数据"]
CopyData --> SetExpire["设置过期时间<br/>exp = 当前时间 + 过期时长"]
SetExpire --> UpdateData["更新数据字典<br/>添加exp字段"]
UpdateData --> EncodeJWT["使用SECRET_KEY和HS256算法<br/>编码JWT令牌"]
EncodeJWT --> ReturnToken["返回生成的访问令牌"]
ReturnToken --> End([结束])
```

**Diagram sources**
- [security.py](file://backend/common/core/security.py#L14-L20)

**Section sources**
- [security.py](file://backend/common/core/security.py#L14-L20)

## 认证失败处理

系统实现了全面的认证失败处理机制，针对不同情况返回相应的错误信息：

```mermaid
flowchart TD
Start([认证开始]) --> CheckAccount["检查账户是否存在"]
CheckAccount --> |账户不存在| ReturnError1["返回: 账户或密码错误"]
CheckAccount --> |账户存在| CheckPassword["验证密码"]
CheckPassword --> |密码错误| ReturnError1
CheckPassword --> |密码正确| CheckStatus["检查用户状态"]
CheckStatus --> |用户已禁用| ReturnError2["返回: 用户已被禁用"]
CheckStatus --> |用户启用| CheckWorkspace["检查工作区关联"]
CheckWorkspace --> |未关联工作区| ReturnError3["返回: 未关联工作区"]
CheckWorkspace --> |已关联工作区| ReturnSuccess["返回: 认证成功"]
style ReturnError1 fill:#f9d0c4,stroke:#333
style ReturnError2 fill:#f9d0c4,stroke:#333
style ReturnError3 fill:#f9d0c4,stroke:#333
style ReturnSuccess fill:#d4edda,stroke:#333
```

具体的错误处理逻辑包括：
- **账户密码错误**：当账户不存在或密码验证失败时，返回"账户或密码错误"信息
- **用户禁用状态**：当用户状态不为1（启用）时，返回"用户已被禁用"信息
- **未关联工作区**：当用户未关联任何工作区时，返回"未关联工作区"信息

**Diagram sources**
- [login.py](file://backend/apps/system/api/login.py#L25-L34)

**Section sources**
- [login.py](file://backend/apps/system/api/login.py#L25-L34)

## 客户端调用示例

### 请求格式
客户端需要通过POST请求调用`/login/access-token`端点，使用标准的OAuth2密码授权模式。

**请求头**
```
Content-Type: application/x-www-form-urlencoded
```

**请求体参数**
- `username`: 用户账户名
- `password`: 用户密码
- `grant_type`: 固定值"password"

### 成功响应示例
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiYWNjb3VudCI6ImFkbWluIiwiZXhwIjoxNzE3MTY4MjIxfQ.5fRZ5nVZ4QZ4QZ4QZ4QZ4QZ4QZ4QZ4QZ4QZ4QZ4QZ4",
  "token_type": "bearer"
}
```

### 失败响应示例
**账户密码错误**
```json
{
  "detail": "账户或密码错误"
}
```

**用户已被禁用**
```json
{
  "detail": "用户已被禁用"
}
```

**未关联工作区**
```json
{
  "detail": "未关联工作区"
}
```

**Section sources**
- [login.py](file://backend/apps/system/api/login.py#L1-L34)
- [schemas.py](file://backend/common/core/schemas.py#L13-L15)

## 认证中间件工作原理

认证中间件`TokenMiddleware`负责验证后续请求中的JWT令牌，确保用户权限的持续有效性。

```mermaid
sequenceDiagram
participant 客户端 as 客户端
participant 中间件 as TokenMiddleware
participant 数据库 as 数据库
客户端->>中间件 : 发送带令牌的请求
中间件->>中间件 : 检查是否为OPTIONS请求
中间件->>中间件 : 检查是否在白名单中
中间件->>中间件 : 提取Authorization头
中间件->>中间件 : 验证Bearer模式
中间件->>中间件 : 解码JWT令牌
中间件->>数据库 : 查询用户信息
数据库-->>中间件 : 返回用户数据
中间件->>中间件 : 验证用户状态
中间件->>中间件 : 验证工作区关联
alt 验证成功
中间件->>中间件 : 设置current_user
中间件-->>客户端 : 继续处理请求
else 验证失败
中间件-->>客户端 : 返回401错误
end
```

中间件的工作流程包括：
1. 排除OPTIONS预检请求
2. 检查请求路径是否在白名单中
3. 从请求头中提取JWT令牌
4. 验证令牌的Bearer模式
5. 解码并验证JWT签名和过期时间
6. 查询数据库获取用户详细信息
7. 验证用户状态和工作区关联
8. 将用户信息存储在请求状态中供后续处理使用

**Diagram sources**
- [auth.py](file://backend/apps/system/middleware/auth.py#L20-L198)

**Section sources**
- [auth.py](file://backend/apps/system/middleware/auth.py#L20-L198)

## 总结
SQLBot系统的用户认证机制基于JWT标准实现，提供了安全可靠的用户身份验证功能。系统通过`/login/access-token`端点处理用户登录，使用MD5密码验证和JWT令牌生成确保安全性。认证中间件在后续请求中验证令牌有效性，实现了无状态的会话管理。完整的错误处理机制为客户端提供了清晰的反馈信息，有助于快速定位和解决问题。