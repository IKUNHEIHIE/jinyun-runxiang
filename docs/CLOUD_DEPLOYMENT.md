# 云服务器部署（2026-10-18）

## 服务器与域名

- 服务器：`20.214.140.142`（SSH 别名 `smxc-azure`，Debian 12，2 vCPU / 3.8 GiB / 60 GB）
- 后端 canonical 域名：https://core.wentian.org （`/health`、`/api/*`、`/static/*` 反代到 FastAPI `127.0.0.1:8000`）
- 教师/运营后台：https://admin.wentian.org （静态 SPA 根路径；`/api/`、`/static/design|uploads|generated|images` 反代到同一后端）
- App 当前 API：`https://admin.wentian.org/api`（按业务要求走 admin 域名；admin 的 Nginx 同时反代 API）
- TLS：Let’s Encrypt，覆盖两个域名，certbot.timer 已启用自动续期

## 运行组件

| 组件 | 方式 | 端口/路径 |
|---|---|---|
| Nginx | apt，`/etc/nginx/sites-available/jinyun` | 公网 80/443 |
| FastAPI | systemd `jinyun-backend.service`，uvicorn 2 workers | `127.0.0.1:8000` |
| MariaDB | apt，数据库 `jinyun_runxiang` | 仅 `127.0.0.1:3306` |
| Redis | apt | 仅 `127.0.0.1:6379` |
| 后端目录 | `/opt/jinyun/backend`，venv `.venv` | 环境文件 `.env`（600） |
| 后台静态 | `/var/www/jinyun-admin` | Nginx root |

## App 域名配置

后端地址只由 [user-web/.env.android](../user-web/.env.android) 控制：

```dotenv
VITE_API_BASE_URL=https://admin.wentian.org/api
```

`scripts/build_android_debug.ps1` 在未传 `-ApiUrl` 时自动读取该文件；换域名只需修改这一行并重新打包。开发联调仍可显式传 `-ApiUrl http://127.0.0.1:8000/api`。

## 后台构建与部署

```bash
cd admin-web
npm run build          # .env.production 中 VITE_PUBLIC_PATH=/
# 将 dist/ 同步到服务器 /var/www/jinyun-admin
```

教师/运营后台入口即 `https://admin.wentian.org/`；管理员账号由服务器初始化脚本随机生成，凭据只保存在本机 `.local/deploy/credentials.txt`（不进入仓库/Release）。学生 `student_demo` 与教师 `teacher_demo` 也是随机密码，首次联调后请按实际需要替换或禁用。

## 数据库

- 新库导入 `database/schema_all.sql`、`database/seed_data.sql`、`database/migrations/V17__course_design_badges.sql`，随后补齐非遗内容（本地开发库的 `heritage_entry` 5 条已导入）。
- 当前为隔离演示数据；正式运营前应清理演示统计、替换账号密码并接入真实业务数据。
- 备份建议：`mariadb-dump jinyun_runxiang | gzip > backup.sql.gz`，并设置离线保存。

## 部署配置副本

- Nginx：[deploy/nginx/jinyun.conf](../deploy/nginx/jinyun.conf)
- systemd：[deploy/systemd/jinyun-backend.service](../deploy/systemd/jinyun-backend.service)

## 已验证

- 2026-10-18：`https://core.wentian.org/health` 200；`https://admin.wentian.org/` 200；TLS 证书签发成功。
- `admin/student_demo/teacher_demo` 通过云端 `/api/auth/login` 均返回 200。
- App final31 连接云端后首页加载 5 条非遗推荐，封面来自 `https://admin.wentian.org/static/design/...`（800px），无本地 `127.0.0.1:8000` 请求。
- 教师后台用无头浏览器实际登录，运营大盘返回真实数据库统计。
