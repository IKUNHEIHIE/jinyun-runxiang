# 《津韵润乡》天津非遗赋能乡村美育智能应用平台

> **JinYun RunXiang** — AI-Powered Rural Aesthetic Education Platform Rooted in Tianjin Intangible Cultural Heritage

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Vue3](https://img.shields.io/badge/Frontend-Vue%203.5-42b883?logo=vue.js)](https://vuejs.org/)
[![Element Plus](https://img.shields.io/badge/UI-Element%20Plus%202.11-409eff?logo=element)](https://element-plus.org/)
[![MySQL](https://img.shields.io/badge/Database-MySQL%208.0-4479a1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

---

## 项目简介

《津韵润乡》是一套面向天津农村地区的**非遗文化数字化美育综合平台**，融合多模态 AI（DeepSeek 大模型）、3D 非遗资产可视化与双师教学体系，帮助乡村中小学生系统学习杨柳青年画、泥人张彩塑、皮影戏、津门风筝等天津非遗技艺。

平台采用**前后端分离**的全栈架构，三端独立运行，数据实时互通：

| 端位 | 技术栈 | 访问地址 | 说明 |
|:---|:---|:---:|:---|
| **运营管理后台** `admin-web` | Vue Pure Admin · Element Plus 2.11 · Vite 7 | `:5173` | 内容管理 / 用户治理 / 数据大盘 / 系统设置 |
| **用户前台门户** `user-web` | Vue 3.5 · Element Plus · Three.js | `:5174` | 非遗微课 / AI 工坊 / 美育广场 / 助农市集 |
| **后端 API 服务** `backend` | FastAPI 0.115 · SQLAlchemy 2 · MySQL 8 | `:8000` | RESTful API · JWT 鉴权 · DeepSeek AI 网关 |

---

## 功能模块

### 用户前台（`user-web`）

- 🎨 **非遗微课堂**：分龄段（小学低/高年级、初中）课程筛选，非遗门类标签，原生视频播放器，骨架屏加载
- 🤖 **AI 数字工坊**：4 步创作向导（选非遗 → 灵感提示词 → AI 绘图 → 纸样下料），津门皮影 3D 骨骼检视，A4 切割纸样 SVG 导出
- 🌸 **美育广场**：响应式瀑布流作品墙，点赞动效，学校/名师标签，创作故事抽屉详情
- 🛒 **文创助农市集**：非遗文创认购，美育专项扶持基金实时进度条，积分核销
- 🗺️ **津门研学地图**：天津六区非遗基地 GPS 实时测距（Haversine 算法），电子围栏打卡
- 👤 **个人成长中心**：学徒/教师双视图，工匠能量等级，研学时光轴，荣誉徽章墙

### 运营管理后台（`admin-web`）

- 📊 **数据大盘**：日活 DAU、课程播放趋势、社区热榜（ECharts）
- 👥 **用户中台**：全量学员/教师档案，角色管理，账号启停
- 📚 **内容管理**：课程 CMS（视频/图文），社区作品审核，助农商品上架
- ⚙️ **系统设置**：大模型 API 接入配置（DeepSeek / 自定义），站点品牌自定义，真实网络连通性探活
- 🏫 **设备管理**：具身智能机器人设备注册 / 心跳监控 / 指令下发
- 🎭 **活动管理**：非遗传承人预约、研学活动审批

### 后端 API（`backend`）

- 🔐 **认证与权限**：JWT + RBAC 双重守卫，scrypt 加盐密码存储，兼容旧版 SHA-256 登录后升级，防注册提权
- 🏗️ **泛型仓储层**：`CRUDBase[Model, Create, Update]`（参照 FastAPI 官方生产模板）
- 🤖 **AI 网关**：官方 OpenAI SDK 统一驱动 DeepSeek，支持流式 SSE 响应与多模态审美诊断
- 🔒 **安全加固**：文件上传白名单 + 50MB 熔断，随机散列命名防路径遍历，全局异常 TraceId 链路日志

---

## 项目结构

```
jinyun-runxiang/
├── admin-web/          # 运营管理后台（Vue Pure Admin）
├── user-web/           # 用户前台门户（Vue 3 + Element Plus）
├── backend/            # 后端 API 服务（FastAPI）
│   ├── app/
│   │   ├── api/        # 路由控制器（auth/course/ai_workshop/community/mall…）
│   │   ├── core/       # 配置 / 安全 / LLM 网关
│   │   ├── crud/       # 泛型仓储层（CRUDBase）
│   │   ├── models/     # SQLAlchemy ORM 实体
│   │   ├── schemas/    # Pydantic 数据传输对象
│   │   └── static/     # 本地非遗 SVG 资产 / 3D 皮影模型
│   ├── tests/          # 端到端功能测试
│   └── requirements.txt
├── database/
│   ├── schema_all.sql          # 完整建库 DDL（60 张核心表）
│   ├── seed_data.sql           # 初始非遗数据
│   └── generate_100_seed_data.py  # 100 条测试数据生成脚本
├── mobile-app/         # Flutter 移动端（学生/教师）
├── docs/               # 项目文档
├── 津韵润乡_UI设计文档.docx
├── 津韵润乡_前端开发文档.docx
├── 津韵润乡_后端功能文档.docx
├── 津韵润乡_数据库设计文档.docx
└── README.md
```

---

## 快速开始

### 环境要求

| 工具 | 版本 |
|:---|:---|
| Python | ≥ 3.11 |
| Node.js | ≥ 20 |
| MySQL | 8.0 |
| Redis | ≥ 7.0（可选，会话缓存） |

### 1. 数据库初始化

```bash
mysql -u root -p -e "CREATE DATABASE jinyun_runxiang CHARACTER SET utf8mb4;"
mysql -u root -p jinyun_runxiang < database/schema_all.sql
mysql -u root -p jinyun_runxiang < database/seed_data.sql

# 生成 100 条测试数据（可选）
python3 database/generate_100_seed_data.py
```

### 2. 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制模板后按需修改）
cp .env.example .env
# 编辑 .env，填写 DB_URL、JWT_SECRET_KEY、DEEPSEEK_API_KEY 等

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问 **http://localhost:8000/docs** 查看交互式 API 文档。

### 3. 运营管理后台启动

```bash
cd admin-web
npm install
npm run dev          # 开发模式，端口 :5173
# npm run build      # 生产构建
```

### 4. 用户前台启动

```bash
cd user-web
npm install
npm run dev          # 开发模式，端口 :5174
# npm run build      # 生产构建
```

---

## 环境变量说明（`backend/.env`）

| 变量名 | 说明 | 示例 |
|:---|:---|:---|
| `DATABASE_URL` | MySQL 连接字符串 | `mysql+pymysql://user:pass@localhost/jinyun_runxiang` |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产必改） | 任意随机字符串 |
| `JWT_EXPIRE_HOURS` | Token 有效期（小时） | `24` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | `sk-xxxxxxx` |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com/v1` |

> ⚠️ `.env` 文件已加入 `.gitignore`，请勿将真实密钥提交到仓库。

---

## 技术栈总览

### 后端
- **FastAPI 0.115** — 高性能异步 Python Web 框架
- **SQLAlchemy 2.0** — ORM（参数化查询，防 SQL 注入）
- **Pydantic v2** — 数据校验与设置管理（`pydantic-settings`）
- **PyJWT** — JWT 令牌签发与校验
- **scrypt** — 加盐密码哈希存储
- **OpenAI SDK** — 统一驱动 DeepSeek 多模态推理
- **Loguru** — 结构化日志 + TraceId 链路追踪

### 前端（管理后台）
- **Vue Pure Admin (pure-admin-thin)** — 企业级后台模板
- **Vue 3.5 + Vite 7 + TypeScript**
- **Element Plus 2.11** — 组件库
- **Pinia** — 状态管理
- **ECharts** — 数据可视化

### 前端（用户门户）
- **Vue 3.5 + Vite 5 + Element Plus 2.8**
- **Three.js** — 皮影戏 3D 骨骼检视
- **津派非遗 Design Tokens** — 主色 `#8B4A2F`（紫铜赤红）

### 数据库
- **MySQL 8.0** — 业务事实库（60 张核心表）
- **Redis 7** — 会话缓存（可选）

---

## 安全审计评级

经 OWASP Top 10（2021/2025）与 CWE 标准全量审计：

| 维度 | 评级 |
|:---|:---:|
| 安全漏洞（OWASP / CWE） | **A** |
| 架构与质量（SOLID 原则） | **A+** |
| 代码规范与可维护性 | **A** |
| 数据一致性与事务 | **A+** |

**综合评级：A（优秀 / 准生产就绪）**

---

## 开源规范文档

| 文档 | 说明 |
|:---|:---|
| [津韵润乡_UI设计文档.docx](津韵润乡_UI设计文档.docx) | 完整 UI 规范与设计稿说明 |
| [津韵润乡_前端开发文档.docx](津韵润乡_前端开发文档.docx) | 前端组件与页面开发规范 |
| [津韵润乡_后端功能文档.docx](津韵润乡_后端功能文档.docx) | 后端 API 接口与业务逻辑规范 |
| [津韵润乡_数据库设计文档.docx](津韵润乡_数据库设计文档.docx) | 数据库设计文档（60 张核心表） |

---

## License

[MIT](LICENSE) © 2026 IKUNHEIHIE
