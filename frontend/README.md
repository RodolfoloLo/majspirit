# MajSpirit Frontend

这个文档按“后端同学能快速看懂前端”的目标来写，重点解释每个目录的职责和调用关系。

## 1. 技术栈与入口

- 框架: Vue 3 + TypeScript + Vite
- 路由: Vue Router
- 状态管理: Pinia
- 样式: Tailwind + 自定义组件类（在 `src/style.css`）
- 网络层: Axios 封装在 `src/api/client.ts`
- 实时通信: WebSocket 封装在 `src/ws/majsocket.ts`

启动入口:

- `src/main.ts`: 挂载 Vue 应用、注册 Router + Pinia、加载全局样式
- `src/App.vue`: 根组件，主要承载布局壳组件
- `src/components/AppShell.vue`: 顶部导航、页面切换容器（`RouterView`）

## 2. 目录分工（按职责）

### 页面层（View）

- `src/views/AuthView.vue`: 登录/注册页面
- `src/views/LobbyView.vue`: 房间大厅（创建房间、进入房间）
- `src/views/RoomView.vue`: 房间内座位/准备/开始
- `src/views/GameView.vue`: 对局页面（只保留展示与事件绑定）
- `src/views/HistoryView.vue`: 历史战绩与对局详情
- `src/views/NotFoundView.vue`: 404 页面

### 业务模块层（Feature）

- `src/features/game/useGameView.ts`: 对局页面的业务控制器（状态、请求、动作、WebSocket 生命周期）
- `src/features/game/tileSprite.ts`: 牌编码到雪碧图坐标的映射逻辑

说明:
`GameView.vue` 现在只负责模板渲染；复杂逻辑下沉到 `features/game`，降低页面文件复杂度。

### 接口层（API）

- `src/api/client.ts`: Axios 实例 + 通用响应解包
- `src/api/auth.ts`: 登录、注册、获取用户、登出
- `src/api/rooms.ts`: 房间相关接口
- `src/api/games.ts`: 对局状态与动作接口（discard/tsumo/ron/pass）
- `src/api/history.ts`: 战绩列表与详情接口

设计原则:
页面与 Store 不直接拼 URL，统一通过 API 层调用。

### 状态层（Store）

- `src/stores/auth.ts`: 用户与 token 生命周期
- `src/stores/rooms.ts`: 房间列表与当前房间
- `src/stores/ui.ts`: 全局通知（Toast）

### 通用工具层（lib / types / ws）

- `src/lib/token.ts`: token 本地存取
- `src/lib/error.ts`: 接口错误消息提取
- `src/lib/requestId.ts`: request_id 读取辅助
- `src/types/api.ts`: 前后端契约类型
- `src/ws/majsocket.ts`: WebSocket 连接、重连、心跳

## 3. 一个请求是怎么走的（后端视角）

以“出牌”为例:

1. 用户在 `src/views/GameView.vue` 点击“出牌”按钮
2. 事件转发给 `src/features/game/useGameView.ts` 的 `doDiscard`
3. `doDiscard` 调用 `src/api/games.ts` 的 `discardTile`
4. `discardTile` 走 `src/api/client.ts` 发 HTTP 请求
5. 后端返回后，`useGameView.ts` 触发 `refreshGame` 拉最新 state/actions
6. `GameView.vue` 依赖响应式状态自动重渲染

WebSocket 事件也是类似路径:

1. `useGameView.ts` 在 `onMounted` 里连接 `MajSocket`
2. 收到 `game_*` 事件后触发 `refreshGame`
3. 页面状态同步更新

## 4. 对局页面拆分后的阅读顺序（推荐）

建议按下面顺序看，不容易迷路:

1. `src/views/GameView.vue`（先看模板上有哪些区块）
2. `src/features/game/useGameView.ts`（看每个按钮背后的动作）
3. `src/features/game/tileSprite.ts`（看牌面如何映射图片）
4. `src/api/games.ts`（看和后端的接口对应）
5. `src/types/api.ts`（看字段契约）

## 5. 当前前端结构设计规则

- 规则 1: 页面组件只放“展示 + 事件绑定”，不堆业务细节。
- 规则 2: 业务逻辑优先放在 `features/<domain>/useXxx.ts`。
- 规则 3: 所有 HTTP 请求统一走 `src/api/*`。
- 规则 4: 契约类型统一维护在 `src/types/api.ts`。
- 规则 5: 临时修补脚本不进长期代码结构，改动直接落到模块文件。

## 6. 本地开发

安装依赖:

```bash
npm install
```

开发模式:

```bash
npm run dev
```

生产构建:

```bash
npm run build
```

