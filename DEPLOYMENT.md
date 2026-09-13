# 津脉智韵·天津非遗乡村美育科技系统 — 生产部署与运维手册

## 一、 系统架构概览

津脉智韵（ShuMei）采用现代化云原生微服务全栈架构，集“非遗数字化教学 + AI审美诊断 + 助农公益商城 + 具身助教协同 + 科技数据大屏”于一体：

```
                             [ 外部用户 / 浏览器 / 电子班牌 / 大屏 ]
                                                │
                                                ▼ (Port 80 / 443)
                         ┌─────────────────────────────────────────┐
                         │           Nginx 统一反向代理网关         │
                         └───────┬──────────────┬───────────┬──────┘
                                 │              │           │
                / (根路径)       │       /admin/│    /api/  │      /static/
                ▼               ▼              ▼           ▼
        ┌───────────────┐ ┌───────────────┐ ┌───────────────────────────┐
        │   user-web    │ │   admin-web   │ │       backend (FastAPI)   │
        │ 用户前台门户   │ │ PureAdmin中台 │ │ - RESTful API / WebSocket │
        │ (Vue3 + Vite) │ │ (含科技大屏)  │ │ - AI 审美诊断引擎        │
        └───────────────┘ └───────────────┘ │ - SQLAlchemy ORM 数据层   │
                                            └─────────────┬─────────────┘
                                                          │
                                             ┌────────────┴───────────┐
                                             │  SQLite / MySQL 数据库  │
                                             └────────────────────────┘
```

---

## 二、 核心端口与服务映射

| 服务组件 | 容器内服务 | 映射端口 | 访问路径 | 职责说明 |
| :--- | :--- | :--- | :--- | :--- |
| **Nginx** | 统一入口网关 | `80` (HTTP) | `http://localhost/` | 全局路由、静态缓存、反向代理、Gzip压缩 |
| **user-web** | 用户端前端 | `80` (内部) | `http://localhost/` | 非遗微课学习、AI工坊、爱心商城、美育地标 |
| **admin-web**| 管理后台 | `80` (内部) | `http://localhost/admin/` | 课程审核、风控中台、教案导出、设备遥测 |
| **Screen** | 科技数据大屏 | `80` (内部) | `http://localhost/screen` | 1920x1080 数字孪生全屏大屏、机器人遥测 |
| **backend** | 后端 API | `8000` | `http://localhost/api/` | 业务引擎、AI多模态诊断、答题闯关、公益存证 |

---

## 三、 生产环境容器化一键部署 (Docker Compose)

### 1. 前置依赖检查
确保宿主机已安装 Docker 24.0+ 与 Docker Compose v2：
```bash
docker --version
docker compose version
```

### 2. 构建并启动全部容器集群
在项目根目录下执行：
```bash
cd /www/opencode-workspace/shumei

# 一键拉取镜像、编译多阶段前端并启动服务
docker compose up -d --build
```

### 3. 查看容器运行状态
```bash
docker compose ps
```
预期输出所有服务状态均为 `Up` (healthy)。

### 4. 容器日志排查
```bash
# 查看统一反向代理日志
docker compose logs -f nginx

# 查看后端接口与 AI 诊断调用日志
docker compose logs -f backend
```

### 5. 停止与重启集群
```bash
# 优雅停止集群
docker compose down

# 重启集群
docker compose restart
```

---

## 四、 本地开发与调试模式 (Dev Mode)

若需要分别进行本地热重载调试，可按照以下方式独立运行各端：

### 1. 后端 (FastAPI)
```bash
cd /www/opencode-workspace/shumei/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API 文档 Swagger 地址：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/v1/health`

### 2. 用户端前台 (user-web)
```bash
cd /www/opencode-workspace/shumei/user-web
npm install
npm run dev -- --host 0.0.0.0 --port 5174
```
- 访问：`http://localhost:5174/`

### 3. 管理端后台及大屏 (admin-web)
```bash
cd /www/opencode-workspace/shumei/admin-web
pnpm install
pnpm dev -- --host 0.0.0.0 --port 5173
```
- 访问管理后台：`http://localhost:5173/` (默认账号：`admin` / `admin123`)
- 直接进入科技大屏：`http://localhost:5173/#/screen`

---

## 五、 数据持久化与备份策略

1. **业务数据库 (`shumei.db`)**：
   - 映射路径：`./backend/shumei.db` 挂载至容器内部 `/app/shumei.db`。
   - 备份命令：
     ```bash
     cp ./backend/shumei.db ./backup/shumei_$(date +%Y%m%d_%H%M%S).db
     ```
2. **AI生成作品与静态素材 (`static/`)**：
   - 挂载路径：`./backend/app/static` -> `/app/app/static`。
   - 涵盖非遗微课封面、AI工坊学生画作、捐赠存证证书印章图谱。

---

## 六、 核心功能特色模块指引

1. **AI 多模态非遗审美诊断**：
   - 路径：用户前台 -> 「AI非遗工坊」 -> 点击「✦ 发起 AI 名师审美诊断 (+30 能量)」。
   - 输出三维审美雷达、名师寄语及五星勋章。
2. **爱心助农公益证书生成与查验**：
   - 路径：用户前台 -> 「文创助农商城」 -> 认购商品或点击「❖ 查验/生成爱心助农证书」。
   - 自动生成带防伪哈希、天津非遗红印与受益乡村学校属性的黄金边框防伪证书。
3. **微课真学时互动答题闯关**：
   - 路径：用户前台 -> 「非遗微课」 -> 点击播放器下方「❖ 课中非遗知识挑战」。
   - 交互式答题闯关，满分即时发放 +25 能量积分并解锁名师深度解析。
4. **名师智能备课标准化教案导出**：
   - 路径：管理后台 -> 「课程内容管理」 -> 操作列点击「导出教案 ↗」。
   - 动态生成符合国家教育部美育标准的纯净排版教案，支持直接调用浏览器打印或输出 PDF。
5. **数字孪生·乡村美育科技大屏**：
   - 路径：管理后台 -> 运营大盘顶部点击「开启全屏大盘 ↗」，或直接访问 `/#/screen`。
   - 包含天津16区基地拓扑、具身助教机器人遥测、实时助农资金动态流水与ECharts高科技动效。
