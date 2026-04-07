# MajSpirit Frontend

Vue 3 + TypeScript + Vite 前端，已对接 MajSpirit API 文档约定。

## 本地开发

1. 安装依赖

	npm install

2. 启动开发服务器

	npm run dev

3. 打开页面

	http://127.0.0.1:5173

## 环境变量

复制 `.env.example` 到 `.env`，按需覆盖：

- `VITE_API_BASE_URL`：HTTP API 根路径。默认 `/api/v1`，依赖 Vite 代理到后端 8000。
- `VITE_WS_BASE_URL`：WebSocket 根地址。默认跟随当前站点地址。

## 已实现模块

- 用户认证：登录/注册、会话恢复、登出
- 大厅房间：创建房间、查看房间、进入房间
- 房间操作：入座、准备、开局、离开
- 牌谱记录：历史战绩列表
- 实时能力：WebSocket 连接、自动重连、心跳
- 统一错误提示：Toast

## 安全说明

- Token 存储在 `sessionStorage`，减少长期驻留风险。
- 所有请求自动附带 `X-Request-Id`，便于后端追踪。
- 生产环境请使用 `wss://`，并对 URL query 中 token 做日志脱敏。
- 生产部署建议由网关统一处理 CORS 与 HTTPS 证书。
