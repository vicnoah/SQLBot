import os
import debugpy

# License functionality removed
# import sqlbot_xpack
from alembic.config import Config
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from fastapi_mcp import FastApiMCP
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from alembic import command
from apps.api import api_router
from common.utils.embedding_threads import fill_empty_table_and_ds_embeddings
from apps.system.crud.aimodel_manage import async_model_info
from apps.system.crud.assistant import init_dynamic_cors
from apps.system.middleware.auth import TokenMiddleware
from common.core.config import settings
from common.core.response_middleware import ResponseMiddleware, exception_handler
from common.core.sqlbot_cache import init_sqlbot_cache
from common.utils.embedding_threads import fill_empty_terminology_embeddings, fill_empty_data_training_embeddings
from common.utils.utils import SQLBotLogUtil

# 环境变量控制调试
DEBUG_ENABLED = os.getenv("DEBUG_ENABLED", "false").lower() == "true"
DEBUG_PORT = int(os.getenv("DEBUG_PORT", "5678"))

print(f"🔧 调试模式: {DEBUG_ENABLED}")
print(f"🔧 调试端口: {DEBUG_PORT}")

# 启用调试（仅在调试模式下运行）
def setup_debugging():
    if not DEBUG_ENABLED:
        print("🔧 调试模式未启用")
        return
    
    try:
        # 检查是否在调试模式下运行
        debugpy.listen(("0.0.0.0", DEBUG_PORT))
        print(f"🎯 调试器已启动，等待连接... (端口 {DEBUG_PORT})")
        
        # 可选：设置断点自动等待连接
        DEBUG_WAIT_FOR_CLIENT = os.getenv("DEBUG_WAIT_FOR_CLIENT", "false").lower() == "true"
        if DEBUG_WAIT_FOR_CLIENT:
            debugpy.wait_for_client()
            print("🔌 调试器已连接")
    except Exception as e:
        print(f"❌ 调试器设置失败: {e}")

# 在应用启动前调用
setup_debugging()

def run_migrations():
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        SQLBotLogUtil.error(f"Migration failed: {e}")


def init_terminology_embedding_data():
    fill_empty_terminology_embeddings()


def init_data_training_embedding_data():
    fill_empty_data_training_embeddings()


def init_table_and_ds_embedding():
    fill_empty_table_and_ds_embeddings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        run_migrations()
        init_sqlbot_cache()
        init_dynamic_cors(app)
        init_terminology_embedding_data()
        init_data_training_embedding_data()
        init_table_and_ds_embedding()
        SQLBotLogUtil.info("✅ SQLBot 初始化完成")
        await async_model_info()  # 异步加密已有模型的密钥和地址
    except Exception as e:
        SQLBotLogUtil.error(f"Initialization failed: {e}")
        SQLBotLogUtil.info("✅ SQLBot 初始化完成 (部分功能受限)")
    # License functionality removed
    # await sqlbot_xpack.core.clean_xpack_cache()
    yield
    SQLBotLogUtil.info("SQLBot 应用关闭")


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags and len(route.tags) > 0 else ""
    return f"{tag}-{route.name}"


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan
)

mcp_app = FastAPI()
# mcp server, images path
images_path = settings.MCP_IMAGE_PATH
os.makedirs(images_path, exist_ok=True)
mcp_app.mount("/images", StaticFiles(directory=images_path), name="images")

mcp = FastApiMCP(
    app,
    name="SQLBot MCP Server",
    description="SQLBot MCP Server",
    describe_all_responses=True,
    describe_full_response_schema=True,
    include_operations=["get_datasource_list", "get_model_list", "mcp_question", "mcp_start", "mcp_assistant"]
)

mcp.mount(mcp_app)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(TokenMiddleware)  # 重新启用认证中间件以设置current_user
app.add_middleware(ResponseMiddleware)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, exception_handler.http_exception_handler)
app.add_exception_handler(Exception, exception_handler.global_exception_handler)

mcp.setup_server()

# License functionality removed
# sqlbot_xpack.init_fastapi_app(app)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    # uvicorn.run("main:mcp_app", host="0.0.0.0", port=8001) # mcp server
