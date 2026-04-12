# 关于backend的一些说明:

## 目录结构
- `alembic/`: 包含数据库迁移文件.
- `api/`: 包含所有的API路由(专注于接口定义和请求处理,处理逻辑交给services层).
- `core/`: 包含核心功能，如认证、配置等.
- `db/`: 数据库相关的代码，如模型定义和数据库会话.
- `exceptions/`: 自定义异常类,简化报错逻辑.
- `models/`: 包含数据库模型定义.
- `repositories/`: 数据访问层,封装数据库操作.
- `schemas/`: 包含Pydantic模型,用于请求和响应的数据验证.
- `services/`: 专注业务逻辑!
- `utils/`: 包含一些工具函数，如错误处理、WebSocket管理等.
- `main.py`: FastAPI应用的入口文件.

> 关于Alembic(第一次使用)
> 核心定位:Alembic是SQLAlchemy的Python数据库迁移工具,本质是数据库的"Git版本控制系统",专门管理数据库表结构的变更,和项目中的SQLAlchemy ORM深度绑定.
> 底层逻辑:读取项目中SQLAlchemy的所有ORM模型的元信息,获取当前数据库的表结构,对比两者的差异,自动生成迁移脚本(也可以手动编写),通过执行迁移脚本来更新数据库表结构.
> 核心作用:解决了很多痛点:手写SQL容易出错,多人协作数据库不一致,变更无法回滚...
> 基本用法:
> 1. 初始化Alembic: `alembic init alembic`
> 2. 配置数据库连接: 修改`alembic.ini`中的`sqlalchemy.url`为你的数据库连接字符串.
> 3. 绑定模型: 修改`alembic/env.py`,导入你的SQLAlchemy模型,并将`target_metadata`设置为你的Base.metadata.
> 4. 生成迁移脚本: `alembic revision --autogenerate -m "描述信息"`
> 5. 执行迁移: `alembic upgrade head`
> 6. 回滚迁移: `alembic downgrade -1

## 用户模块

### 四个接口
1. POST /api/v1/auth/register
> 前端向http://localhost:8000/api/v1/auth/register 发送POST请求,请求体为RegisterReq,接口调用了数据库,然后交给AuthService.register处理注册逻辑,register继续调用数据库,交给UserRepo,先用get_user_by_email检查邮箱是否已注册,如果没有就用create创建新用户,最后用security.create_access_token生成JWT token,给接口返回TokenResp,最后用封装好的ok函数把标准返回格式返回给前端.
2. POST /api/v1/auth/login
3. GET /api/v1/auth/me
4. POST /api/v1/logout

> 关于项目中JWT的使用
> 项目中当然只有注册和登录两个功能会生成JWT token,其他接口发送的请求都需要携带JWT token来鉴权,后端会验证token的有效性和过期时间,如果token无效或过期,接口会返回401错误,前端收到401错误后会清除本地存储的token并重定向到登录页.
> 实现JWT的两个核心文件:security.py和deps.py. security.py负责生成和验证JWT token,deps.py负责从请求中提取token并验证用户身份(利用好HTTPBearer和HTTPAuthorizationCredentials).

> 大概JWT认证流程:
> 1. 用户注册：用户输入账号密码，后端调用hash_password加密密码，把用户信息存入数据库。
> 2. 用户登录：用户输入账号密码，后端从数据库查到用户，调用verify_password验证密码。验证通过后，调用create_access_token生成 Token，返回给客户端。
> 3. 客户端存储 Token：客户端拿到 Token 后，存在localStorage/sessionStorage/HttpOnly Cookie 中。
> 4. 访问需要登录的接口：客户端在请求头中带上 Token，发送请求。
> 5. 后端自动鉴权：FastAPI 自动调用get_current_user，提取 Token、验证 Token、查询用户，最终把用户对象传给接口。如果验证失败，直接返回对应的错误。

## 房间模块

### 七个接口
1. GET /api/v1/rooms(查看房间列表)
2. GET /api/v1/rooms/{room_id}(查看房间详情)
3. POST /api/v1/rooms(创建房间)
4. POST /api/v1/rooms/{room_id}/join(加入房间)
5. POST /api/v1/rooms/{room_id}/ready(准备/取消准备)
6. POST /api/v1/rooms/{room_id}/start(开始游戏)
7. POST /api/v1/rooms/{room_id}/leave(离开房间)

> 一些写services层的心得:
> 1. 首先的首先,services层专注于业务逻辑,不处理HTTP请求和响应,也不直接操作数据库.它应该调用repositories层来获取和修改数据,并且可能会调用其他服务来完成复杂的业务流程.
> 2. 怎么思考要写哪些检查?:
> -  第一步：我要操作的「资源」，它存在吗？
> - 当前用户，有没有「资格」做这个操作？
> - 这个资源的「当前状态」，允许我做这个操作吗？
> - 我要操作的「目标数据」，合法吗？
> - 做这个操作，有没有必须满足的「前置条件」？
> - 并发场景下，我的检查会不会失效？要不要兜底？
> - 最后：这些操作，要不要用事务包起来？
> 
> for instance:
> 我要做“加入房间”这个操作：
> 1. 资源存在吗？→ 房间存在吗？不存在抛错。
> 2. 用户有资格吗？→ 加入房间只要登录就行，不用额外权限，过。
> 3. 房间状态允许吗？→ 房间是不是waiting？是才能进，不然抛错。
> 4. 目标数据合法吗？→ 房间满没满？我是不是已经在房间里了？我选的座位有没有被占？都没问题，过。
> 5. 前置条件满足吗？→ 加入房间没什么前置，过。
> 6. 并发兜底？→ 加数据库唯一索引，捕获并发错误，转成业务异常。
> 7. 事务？→ 加玩家的操作包在事务里，保证原子性。

## 游戏模块

### 六个接口
GET /api/v1/games/{game_id}/state(查看游戏状态)
>先加载缓存(支持断线重连),再调用game_service.get_state获取游戏状态(根据用户ID,过滤出这个用户能看到的信息)
GET /api/v1/games/{game_id}/actions/available(查看可用操作)
>先加载缓存(支持断线重连),再调用game_service.get_available_actions获取这个用户当前能做的操作列表(根据游戏状态和用户角色过滤)
POST /api/v1/games/{game_id}/actions/discard(打牌)
POST /api/v1/games/{game_id}/actions/tsumo(自摸)
POST /api/v1/games/{game_id}/actions/ron(荣和)
POST /api/v1/games/{game_id}/actions/peng(碰牌)
>这四个实现游戏操作接口的实现思路基本一致:
>1. 限流:调用check_rate_limit,限制用户在30秒内只能对同一局游戏的同一操作进行有限次请求,防止用户疯狂点击导致服务器压力过大.
>2. 加锁:调用game_operation_lock,对同一局游戏的操作进行加锁,保证同一时间只有一个请求在操作这局游戏,防止并发操作导致游戏状态混乱.
>3. 加载缓存:调用load_game_from_cache,内存没有->从Redis读回->反序列化到内存,支持断线重连和服务器重启恢复.
>4. 游戏操作:调用game_service的对应方法,执行游戏逻辑,返回事件数据(比如谁打了什么牌,触发了什么事件).
>5. 保存缓存:调用save_game_to_cache,把内存中的游戏状态序列化后写回Redis,保证下一次操作能加载到最新状态.
>6. 解锁:自动解锁,让其他请求能继续操作这局游戏.
>7. 持久化和广播:如果游戏结束了,就把游戏状态持久化到数据库,并广播游戏事件给所有玩家.

### 超级大工具箱(game_service)
这个services层的函数实在是过于多了,现在按功能梳理清楚(一个不漏):

1. 初始化&基础设施
- [__init__()] -> 初始化计数器(game_id/match_id),内存游戏池`_games`,每局锁`_locks`.
- [lock_for(game_id)] -> asyncio.Lock 给某一局返回独立锁,保证同一局串行执行.

2. 开局/发牌链路
- [create_game(room_id,players)] + [deal_round(state)] -> {game_id,match_id}
> 负责排序玩家、补BOT座位、初始化RuntimeGameState、首轮发牌、写入内存.
- [deal_round(state)] -> None
> 洗牌/发牌/设置庄家回合/重置pending状态和round上下文.
- [next_seat(seat)] -> int
> 计算下家座位(循环0~3).

3. 状态存取(内存+缓存配合用)
- [has_game(game_id)] -> bool
> 这局是否已在内存.
- [require_game(game_id)] -> RuntimeGameState
> 获取游戏状态,不存在直接抛GameNotFound(几乎所有核心逻辑入口第一步都用它).
- [export_game_state(game_id)] -> dict[str, Any]
> 内存状态导出成可序列化字典(给Redis缓存).
- [import_game_state(payload)] -> RuntimeGameState
> 从字典恢复RuntimeGameState并放回内存(断线重连/服务重启恢复).

4. 座位/规则判断工具
- [ordered_seats(state,origin_seat)] -> list[int]
> 返回出牌者之后的优先顺序座位列表(上家/对家/下家顺位).
- [seat_of_user(state,user_id)] -> int | None
> 用户ID映射到座位.
- [is_bot_seat(state,seat)] -> bool
> 判断座位是否BOT.
- [can_win(player,extra_tile)] -> bool
> 判断能否和牌(考虑明刻open_meld_count后,手牌长度校验+胡牌算法).
- [pick_bot_tile(hand)] -> str
> BOT打牌策略(当前是简单策略:排序后取一张).

5. 日志/事件封装
- [record_turn(state,action,seat,tile,from_seat)] -> None
> 把每一步操作(摸/打/碰/和/跳过)写进当前小局turn日志.
- [build_event_base(state,event_type)] -> dict[str, Any]
> 统一事件基础字段(event_type/game_id/match_id).
- [compose_action_result(state,events)] -> dict[str, Any]
> API最终返回包装器:取最后事件+附带events数组+当前status/turn.

6. 出牌后推进核心(状态机中枢)
- [discard_by_seat(state,seat,tile)] -> dict[str, Any]
> 打牌核心:校验牌在手里->落弃牌->记录日志->先判荣和->再开碰牌窗口->否则推进到下一家摸牌.
- [advance_after_discard(state,discarded_seat)] -> dict[str, Any]
> 无人抢操作时推进:摸牌/更新回合/牌山耗尽则流局结算.
- [auto_progress(game_id)] -> dict[str, Any] | None
> 自动推进器:驱动BOT回合;若在waiting_for_peng且是真人候选,返回None等待玩家显式选择(不再超时自动跳过).

7. 玩家具体动作(按座位执行)
- [peng_by_seat(state,seat)] -> dict[str, Any]
> 执行碰牌(必须是pending_peng当前优先位),扣2张手牌,加明刻,回合切到碰牌者.
- [pass_peng_by_seat(state,seat)] -> dict[str, Any]
> 执行"不碰":从pending_peng弹出当前候选,还有人可碰则继续等待下一个,否则推进到下一家.
- [tsumo_by_seat(state,seat)] -> dict[str, Any]
> 自摸结算并产出事件(非终局是game_win,终局是game_match_end).
- [ron_by_seat(state,seat)] -> dict[str, Any]
> 荣和结算(放铳者扣分,和牌者加分),并产出事件.

8. 对局收尾/排行榜
- [build_round_result_payload(state,result)] -> dict[str, Any]
> 单局结果入档(round_logs),判断是否终局;终局生成match_end,否则开下一局.
- [build_ranking(state)] -> list[dict[str, Any]]
> 按最终分数生成排名(含delta/rank).
- [is_match_finished(game_id)] -> bool
> 比赛是否结束.
- [is_persisted(game_id)] -> bool
> 这局是否已落库.
- [mark_persisted(game_id)] -> None
> 标记已落库,避免重复持久化.
- [build_match_result(game_id)] -> dict[str, Any]
> 产出整场比赛摘要(排名+每局过程日志),给history持久化层使用.

9. API层直接调用入口(按user_id做权限+状态检查)
- [get_state(game_id,user_id)] -> dict[str, Any]
> 返回视角化后的游戏状态(我的座位/我的手牌+公共信息).
- [get_available_actions(game_id,user_id)] -> dict[str, Any]
> 返回当前用户可执行动作列表(包含碰牌阶段的[peng, pass]).
- [discard(game_id,user_id,tile)] -> dict[str, Any]
> 只允许当前回合真人打牌.
- [tsumo(game_id,user_id)] -> dict[str, Any]
> 只允许当前回合真人且满足和牌条件.
- [peng(game_id,user_id)] -> dict[str, Any]
> 只允许pending_peng当前优先位真人执行碰牌.
- [pass_peng(game_id,user_id)] -> dict[str, Any]
> 只允许pending_peng当前优先位真人执行不碰.
- [ron(game_id,user_id)] -> dict[str, Any]
> 只允许waiting_for_ron阶段且在pending_ron中的真人执行.
- [action_not_available()] -> None
> 统一抛ActionNotAvailable的出口.

10. 文件尾入口对象
- [game_service = GameService()]
> 单例服务对象,供API层直接import使用.

>关于游戏中的缓存/内存:
>内存快,但服务器已重启就没,Redis持久缓存,重启还在,断线重连能恢复.
>用Redis缓存完整游戏状态(完整RunTimeGameState),每次操作前后自动加载/保存,支持断线重连,服务器重启恢复对局.