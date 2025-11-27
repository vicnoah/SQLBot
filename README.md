<p align="center"><img src="https://resource-fit2cloud-com.oss-cn-hangzhou.aliyuncs.com/sqlbot/sqlbot.png" alt="SQLBot" width="300" /></p>
<h3 align="center">基于大模型和 RAG 的智能问数系统</h3>
<h2 align="center">SQLBot 重制版部署文档</h2>

# SQLBot 部署文档

## 概述

本文档提供了 SQLBot 应用程序的 Docker 部署指南。SQLBot 是一个基于 PostgreSQL 数据库的应用程序，包含主应用服务和数据库服务。

## 系统要求

- Docker 20.10.0 或更高版本
- Docker Compose 1.29.0 或更高版本
- 至少 2GB 可用内存
- 至少 10GB 可用磁盘空间

## 部署步骤

### 1. 准备工作

确保已安装 Docker 和 Docker Compose

### 2. 创建项目目录

```bash
mkdir -p sqlbot-deployment/data/{sqlbot/excel,sqlbot/images,sqlbot/logs,postgresql}
cd sqlbot-deployment
```

### 3. 创建 Docker Compose 文件

在项目目录中创建 `docker-compose.yml` 文件，内容如下：

```yaml
version: '3.8'

services:
  sqlbot:
    image: ghcr.io/vicnoah/sqlbot:latest
    container_name: sqlbot
    restart: always
    networks:
      - sqlbot-network
    ports:
      - 8000:8000
      - 8001:8001
    environment:
      # Database configuration
      POSTGRES_SERVER: sqlbot-db
      POSTGRES_PORT: 5432
      POSTGRES_DB: sqlbot
      POSTGRES_USER: sqlbot
      POSTGRES_PASSWORD: sqlbot
      # Project basic settings
      PROJECT_NAME: "SQLBot"
      DEFAULT_PWD: "SQLBot@123456"
      # MCP settings
      SERVER_IMAGE_HOST: https://YOUR_SERVE_IP:MCP_PORT/images/
      # Auth & Security
      SECRET_KEY: y5txe1mRmS_JpOrUzFzHEu-kIQn3lf7ll0AOv9DQh0s
      # CORS settings
      BACKEND_CORS_ORIGINS: "http://localhost,http://localhost:5173,https://localhost,https://localhost:5173"
      # Logging
      LOG_LEVEL: "INFO"
      SQL_DEBUG: False
    volumes:
      - ./data/sqlbot/excel:/opt/sqlbot/data/excel
      - ./data/sqlbot/images:/opt/sqlbot/images
      - ./data/sqlbot/logs:/opt/sqlbot/logs
    depends_on:
      sqlbot-db:
        condition: service_healthy

  sqlbot-db:
    image: pgvector/pgvector:pg17-trixie
    container_name: sqlbot-db
    restart: always
    networks:
      - sqlbot-network
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgresql:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: sqlbot
      POSTGRES_USER: sqlbot
      POSTGRES_PASSWORD: sqlbot
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 3s
      timeout: 5s
      retries: 5

networks:
  sqlbot-network:
```
国内环境可采用此yaml
```yaml
version: '3.8'

services:
  sqlbot:
    image: ghcr.1ms.run/vicnoah/sqlbot:latest
    container_name: sqlbot
    restart: always
    networks:
      - sqlbot-network
    ports:
      - 8000:8000
      - 8001:8001
    environment:
      # Database configuration
      POSTGRES_SERVER: sqlbot-db
      POSTGRES_PORT: 5432
      POSTGRES_DB: sqlbot
      POSTGRES_USER: sqlbot
      POSTGRES_PASSWORD: sqlbot
      # Project basic settings
      PROJECT_NAME: "SQLBot"
      DEFAULT_PWD: "SQLBot@123456"
      # MCP settings
      SERVER_IMAGE_HOST: https://YOUR_SERVE_IP:MCP_PORT/images/
      # Auth & Security
      SECRET_KEY: y5txe1mRmS_JpOrUzFzHEu-kIQn3lf7ll0AOv9DQh0s
      # CORS settings
      BACKEND_CORS_ORIGINS: "http://localhost,http://localhost:5173,https://localhost,https://localhost:5173"
      # Logging
      LOG_LEVEL: "INFO"
      SQL_DEBUG: False
    volumes:
      - ./data/sqlbot/excel:/opt/sqlbot/data/excel
      - ./data/sqlbot/images:/opt/sqlbot/images
      - ./data/sqlbot/logs:/opt/sqlbot/logs
    depends_on:
      sqlbot-db:
        condition: service_healthy

  sqlbot-db:
    image: docker.1ms.run/pgvector/pgvector:pg17-trixie
    container_name: sqlbot-db
    restart: always
    networks:
      - sqlbot-network
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgresql:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: sqlbot
      POSTGRES_USER: sqlbot
      POSTGRES_PASSWORD: sqlbot
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 3s
      timeout: 5s
      retries: 5

networks:
  sqlbot-network:
```

### 4. 配置环境变量

根据您的实际环境修改以下配置：

1. `SERVER_IMAGE_HOST`: 替换 `YOUR_SERVE_IP` 和 `MCP_PORT` 为实际的服务器 IP 和端口
2. `BACKEND_CORS_ORIGINS`: 添加您的前端应用地址
3. `SECRET_KEY`: 建议生成新的密钥替换默认值

### 5. 启动服务

```bash
docker-compose up -d
```

### 6. 验证部署

1. 检查容器状态：
   ```bash
   docker-compose ps
   ```
   应该看到两个服务都处于运行状态。

2. 检查应用日志：
   ```bash
   docker-compose logs sqlbot
   ```

3. 访问应用：
   - API 服务: `http://localhost:8000`
   - 其他服务端口: `8001`

## 访问应用

部署完成后，请按以下步骤访问 SQLBot 管理界面：

1. 打开浏览器，访问：`http://您的服务器IP:8000`

2. 使用以下默认凭据登录：
   - **用户名**: `admin`
   - **密码**: `SQLBot@123456`

3. 登录成功后，您将看到 SQLBot 的主管理界面

主页面，包含多租户等功能
<img width="2183" height="1170" alt="image" src="https://github.com/user-attachments/assets/4c2814d9-dead-4527-8e11-95a3bf906d4b" />
租户空间管理
<img width="2164" height="1165" alt="image" src="https://github.com/user-attachments/assets/52ba2ec3-5434-4f0f-ac04-2db613d39111" />
AI模型设置
<img width="2173" height="1165" alt="image" src="https://github.com/user-attachments/assets/48780908-cdc1-4f5e-a601-a102bdb1618f" />
行列权限管理
<img width="2173" height="1165" alt="image" src="https://github.com/user-attachments/assets/d0f9a1ef-c63a-4a68-b745-f071ab23a2de" />
SQL示例库
<img width="2173" height="1165" alt="image" src="https://github.com/user-attachments/assets/2cecea9d-0d17-4496-aa42-f19801532ffc" />
授权信息
<img width="2173" height="1165" alt="image" src="https://github.com/user-attachments/assets/45ce2dbb-56ba-466b-8247-d8edbed6cb4f" />


数据持久化

• 数据库数据存储在 ./data/postgresql 目录

• 应用数据存储在 ./data/sqlbot 下的各个子目录中

维护命令

• 停止服务: docker-compose down

• 重启服务: docker-compose restart

• 更新镜像: 
  docker-compose pull
  docker-compose up -d

<p align="center">
  <a href="https://github.com/dataease/SQLBot/releases/latest"><img src="https://img.shields.io/github/v/release/dataease/SQLBot" alt="Latest release"></a>
  <a href="https://github.com/dataease/SQLBot"><img src="https://img.shields.io/github/stars/dataease/SQLBot?color=%231890FF&style=flat-square" alt="Stars"></a>    
  <a href="https://hub.docker.com/r/dataease/SQLbot"><img src="https://img.shields.io/docker/pulls/dataease/sqlbot?label=downloads" alt="Download"></a><br/>

</p>
<hr/>

SQLBot 是一款基于大模型和 RAG 的智能问数系统。SQLBot 的优势包括：

- **开箱即用**: 只需配置大模型和数据源即可开启问数之旅，通过大模型和 RAG 的结合来实现高质量的 text2sql；
- **易于集成**: 支持快速嵌入到第三方业务系统，也支持被 n8n、MaxKB、Dify、Coze 等 AI 应用开发平台集成调用，让各类应用快速拥有智能问数能力；
- **安全可控**: 提供基于工作空间的资源隔离机制，能够实现细粒度的数据权限控制。

## 工作原理

<img width="1105" height="577" alt="system-arch" src="https://github.com/user-attachments/assets/462603fc-980b-4b8b-a6d4-a821c070a048" />

## 快速开始

### 安装部署

准备一台 Linux 服务器，安装好 [Docker](https://docs.docker.com/get-docker/)，执行以下一键安装脚本：

```bash
docker run -d \
  --name sqlbot \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 8001:8001 \
  -v ./data/sqlbot/excel:/opt/sqlbot/data/excel \
  -v ./data/sqlbot/file:/opt/sqlbot/data/file \
  -v ./data/sqlbot/images:/opt/sqlbot/images \
  -v ./data/sqlbot/logs:/opt/sqlbot/app/logs \
  -v ./data/postgresql:/var/lib/postgresql/data \
  --privileged=true \
  dataease/sqlbot
```

你也可以通过 [1Panel 应用商店](https://apps.fit2cloud.com/1panel) 快速部署 SQLBot。

如果是内网环境，你可以通过 [离线安装包方式](https://community.fit2cloud.com/#/products/sqlbot/downloads) 部署 SQLBot。

### 访问方式

- 在浏览器中打开: http://<你的服务器IP>:8000/
- 用户名: admin
- 密码: SQLBot@123456

### 联系我们

如你有更多问题，可以加入我们的技术交流群与我们交流。

<img width="180" height="180" alt="contact_me_qr" src="https://github.com/user-attachments/assets/2594ff29-5426-4457-b051-279855610030" />

## UI 展示

  <tr>
    <img alt="q&a" src="https://github.com/user-attachments/assets/55526514-52f3-4cfe-98ec-08a986259280"   />
  </tr>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dataease/sqlbot&type=Date)](https://www.star-history.com/#dataease/sqlbot&Date)

## 飞致云旗下的其他明星项目

- [DataEase](https://github.com/dataease/dataease/) - 人人可用的开源 BI 工具
- [1Panel](https://github.com/1panel-dev/1panel/) - 现代化、开源的 Linux 服务器运维管理面板
- [MaxKB](https://github.com/1panel-dev/MaxKB/) - 强大易用的企业级智能体平台
- [JumpServer](https://github.com/jumpserver/jumpserver/) - 广受欢迎的开源堡垒机
- [Cordys CRM](https://github.com/1Panel-dev/CordysCRM) - 新一代的开源 AI CRM 系统
- [Halo](https://github.com/halo-dev/halo/) - 强大易用的开源建站工具
- [MeterSphere](https://github.com/metersphere/metersphere/) - 新一代的开源持续测试工具

## License

本仓库遵循 [FIT2CLOUD Open Source License](LICENSE) 开源协议，该许可证本质上是 GPLv3，但有一些额外的限制。

你可以基于 SQLBot 的源代码进行二次开发，但是需要遵守以下规定：

- 不能替换和修改 SQLBot 的 Logo 和版权信息；
- 二次开发后的衍生作品必须遵守 GPL V3 的开源义务。

如需商业授权，请联系 support@fit2cloud.com 。
