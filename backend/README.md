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