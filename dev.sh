SSR_PATH=./g2-ssr
APP_PATH=./backend
nohup node $SSR_PATH/app.js &

cd $APP_PATH
nohup uv run -m uvicorn main:mcp_app --host 0.0.0.0 --port 8001 &

uv run -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --proxy-headers

wait