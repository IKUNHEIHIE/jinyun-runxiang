# 津韵润乡部署说明

## 配置

复制项目根目录 `.env.example` 为 `.env`，为 JWT_SECRET_KEY、MYSQL_PASSWORD、MYSQL_ROOT_PASSWORD 分别填写独立随机值。JWT 占位符不能用于启动。

生成随机值：

```console
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 容器部署

```console
docker compose up -d --build
docker compose ps
```

统一入口 `/` 为用户端，`/admin/` 为管理端，`/api/` 为后端。MySQL、Redis 及后端仅在容器网络内访问；后端健康检查为 `/health`。静态文件持久化到 `backend/static`，数据库使用 `mysql_data` 卷。

全新数据库会导入 schema_all.sql，随后执行 V17 初始化七项徽章规则；不导入演示账号、销量或学习结果。五项课程徽章使用仓库中的原稿图形。启动后创建个人管理员：

```console
docker compose exec backend python -m app.scripts.create_admin
```

已有数据库不会因为容器重新启动而自动更新。先备份并核对已执行版本；旧结构先升级 V9，再按 V10–V17 顺序通过 MySQL 客户端执行缺失迁移，随后部署新版服务。不要在已执行完整 schema_all.sql 的新库上重复执行旧 ALTER。手动初始化新库时，在完整结构之后单独执行 V17，以建立徽章目录。详见 docs/ANDROID_DEPLOYMENT.md 的各版本说明。

V17 可重复执行，不覆盖已编辑的目录字段；从真实整门课程完成记录回填徽章，不生成进度或额外能量。用户/徽章唯一约束发现历史重复记录时会拒绝创建，需先核对数据，不自动删记录。V17 的代码回滚保留已授予徽章与目录。旧 seed_data.sql 含演示统计和历史记录，仅用于独立演示库，不属于正式初始化步骤。

历史订单、基金记录和共享账号需要核对，见 SECURITY_REMEDIATION.md。不要删除数据卷来进行版本升级。

## 本地开发

后端复制 backend/.env.example 为 backend/.env 并配置 MySQL 及随机密钥，在 backend 目录执行：

```console
python -m pip install -r requirements.lock.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

管理端在 admin-web 目录：

```console
pnpm install --frozen-lockfile
pnpm dev
pnpm build
pnpm typecheck
```

用户端在 user-web 目录：

```console
npm ci
npm run dev
npm run build
npx vue-tsc --noEmit
```

本地管理端端口 5173，用户端 5174。用户使用个人账号登录；学员可注册，教师由管理员分配。

## 移动端

在 mobile-app 目录安装 Flutter 依赖后指定真实可达服务地址：

```console
flutter pub get
flutter run --dart-define=API_BASE_URL=https://your-host.example/api
```

模拟器或真机均不能把 127.0.0.1 当成开发电脑。离线事件保存在按用户隔离的 Hive 队列中，恢复前台及定时重试会同步，只有确认的事件会被删除。

## 服务边界与验证

尚未配置真实支付、视觉服务或设备网关时，平台不会报告已支付、生成模拟测评分数或伪造设备 ACK。具体接入要求、迁移及已运行测试见 SECURITY_REMEDIATION.md。

本次验证不包含真实 MySQL、Docker 或 Flutter 环境；部署前仍需在目标环境执行迁移和联调验证。
