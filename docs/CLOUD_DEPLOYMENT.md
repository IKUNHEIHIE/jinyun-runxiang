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

## 开发测试数据同步与演示内容（2026-10-18）

- 将本地 WSL 开发库 `jinyun_android_dev` 全量导出并导入云端 `jinyun_runxiang`；MySQL 8 的 `utf8mb4_0900_*` 排序规则转换为 MariaDB 10.11 支持的 `utf8mb4_unicode_ci` 后导入成功。
- 云端现有：4 个账号、6 门课程/6 个章节、5 条非遗、3 个地标、8 条社区作品、11 条评论、9 个 AI 任务、10 个商品、7 件收藏、2 个订单、3 条学习日记录。
- 额外补充 4 条社区作品（风筝/年画/皮影/青花）及详情、8 条评论；为 `student_demo` 补充今日学习记录和 7 件收藏，首页/社区/个人中心不再空态。
- 小课堂演示视频使用外链，不下载到服务器：
  - `https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4`（CC0）
  - `https://media.w3.org/2010/05/sintel/trailer.mp4`（Sintel，CC BY 3.0）
- 云端学生 28 条路由审计：破图 0、横向溢出 0、未捕获异常 0、失败请求 0（`.local/deploy/cloud-route-audit-student2.json`）；新增作品详情 `/community/5` 9 张图片无缺失；课程播放器读取到外链视频且 `readyState=1`。
- 当前云端库为开发/测试数据，正式运营前仍需替换账号密码、清理演示统计并配置备份。

## 已验证

- 2026-10-18：`https://core.wentian.org/health` 200；`https://admin.wentian.org/` 200；TLS 证书签发成功。
- `admin/student_demo/teacher_demo` 通过云端 `/api/auth/login` 均返回 200。
- App final31 连接云端后首页加载 5 条非遗推荐，封面来自 `https://admin.wentian.org/static/design/...`（800px），无本地 `127.0.0.1:8000` 请求。
- 教师后台用无头浏览器实际登录，运营大盘返回真实数据库统计。
