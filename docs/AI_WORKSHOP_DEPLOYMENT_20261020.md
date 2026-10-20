# AI 工坊治理改造线上部署记录（2026-10-20）

按用户授权更新 `core.wentian.org` / `admin.wentian.org` 后端与 Nginx 配置。本次不创建 GitHub Release，不导入本地测试库，不覆盖既有业务数据。

## 变更内容

| 项目 | 值 |
| --- | --- |
| 服务器 | `smxc-azure`（Debian 12，uvicorn `--workers 2`，服务用户 `jinyun`） |
| 部署包 | `backend/app` 全量目录，tar SHA256 `a198d08b80f9fab4fc9b1b8187367a901c2df773f8fdee55d2d7617a9757133c` |
| 备份 | `/var/backups/jinyun/workshop-20261020T133556Z/`（`app.before`、`env.before`、`requirements.before`、`nginx.before`、`db.sql.gz` 39 KB、`NOTES.txt`），目录权限 700 |
| 依赖 | 无新增。服务端 venv（Python 3.11.2 / FastAPI 0.143.3 / Starlette 1.8.0）导入 `app.main`、`app.core.moderation|quota|file_urls`、`app.api.ai_workshop` 全部通过，`compileall` 无错 |
| 权限 | `app/` 归 `jinyun:jinyun`，目录 750、文件 640（避免上次“权限过严导致回退”的同类问题） |
| 签名密钥 | 首次请求时以 `O_CREAT\|O_EXCL` + 0600 生成 `/opt/jinyun/backend/data/file_url_secret.key`（`jinyun:jinyun 600`），两个 worker 共用同一主机同一文件 |
| Nginx | `core.wentian.org` 与 `admin.wentian.org` 各增加 `location ^~ /static/generated/`，`expires -1` + `Cache-Control: no-store always`；线上完整配置已回抄为 `deploy/nginx/jinyun.live-copy.conf` |
| 额度 | 服务器 `SysConfig` 暂无 `ai_quota` 行，使用默认值：每人每日 60 次（剪影 50、三维 50）、每分钟 30 次 |

## 线上验证（正式 HTTPS，独立验证账号）

沿用 2026-10-19 的合成账号 `ai_cloud_check_20261019`（uid 17，非演示人格账号）。验证前其状态为 `DISABLED`，验证结束已恢复 `DISABLED`。全程只用本地规则模板，未触发任何付费生图。

| 检查 | 结果 |
| --- | --- |
| 剪影生成为真实任务 | `POST /api/ai/silhouette/generate` 200，`generation_method = local_rule_template`，写入 `SILHOUETTE` 任务 |
| 同 `request_id` 重放 | 复用同一 `task_id`，未重复生成、未重复奖励 |
| 签名链接读取 | `GET <signed> = 200` |
| 无签名读取 | `GET <bare> = 403` |
| `/static//generated/…` | `403`（修复前可绕过） |
| `/static/uploads/../generated/…` | `403`（修复前可绕过） |
| 内容检查 | 屏蔽词命中返回 `422 剪影描述未通过内容检查：描述包含需调整的词语：…` |
| 三维结果诚实性 | `metrics.mode = DEMO_LIBRARY`、`triangles = 8321`、`license = CC0 1.0` |
| 删除三维作品 | `removed_assets = 1`、`removed_files = 0`，随后共享馆藏 GLB `GET = 200`（复审 blocker：修复前会误删 `static/models/heritage3d/*.glb`） |
| 删除剪影作品 | `removed_assets = 1`、`removed_files = 1`（本人生成文件被清理） |
| 作品列表 / 收藏 | `GET /api/ai/tasks` 返回该账号总数，`/api/mobile/me/collections` 正常 |
| 额度 | `GET /api/ai/quota` 返回 `total/silhouette/mesh_3d/remaining_*/limits`，默认阈值生效 |
| 未登录访问 | `GET /api/ai/quota` = `401`；`/static/generated/*` 无签名 = `403` |
| 响应头 | 两个域名的 `/static/generated/` 均返回 `Cache-Control: no-store` |
| 健康检查 | `systemctl is-active jinyun-backend = active`，`GET /health = 200` |

验证脚本：`.local/deploy/workshop-cloud-smoke.py`（只读凭据文件、不打印密钥，仅本地模式调用）。

## 回退

```bash
ssh smxc-azure
B=/var/backups/jinyun/workshop-20261020T133556Z
sudo rm -rf /opt/jinyun/backend/app && sudo cp -a $B/app.before /opt/jinyun/backend/app
sudo chown -R jinyun:jinyun /opt/jinyun/backend/app
sudo cp $B/nginx.before /etc/nginx/sites-available/jinyun && sudo nginx -t && sudo systemctl reload nginx
sudo systemctl restart jinyun-backend && curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/health
```

回退不删除任务、图片与业务历史；`data/file_url_secret.key` 可保留（保留则既有签名继续有效，删除则全部签名失效，用户需重新打开作品）。数据库备份为 `$B/db.sql.gz`，不要直接覆盖正在使用的库。

---

# 追加部署（2026-10-20 深夜）：皮影作品删除残留修复

同日第二次部署，只替换一个后端文件。真机演示发现删除皮影（`SHADOW_PUPPET`）作品时只清理了 `_colored.svg`，`_lineart.svg`、`_template.svg` 连同对应 `Asset` 行残留在库与磁盘上。无数据库迁移、无 Nginx 改动、无前端改动。

## 根因与变更

| 项目 | 值 |
| --- | --- |
| 服务器 | `smxc-azure`（Azure Debian 12），应用目录 `/opt/jinyun/backend`，虚拟环境 `/opt/jinyun/backend/.venv`（不是 `venv`），运行用户 `jinyun` |
| systemd | 单元 `jinyun-backend`：`WorkingDirectory=/opt/jinyun/backend`、`EnvironmentFile=/opt/jinyun/backend/.env`、`ExecStart=/opt/jinyun/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2` |
| 改动文件 | 仅 `backend/app/core/task_assets.py`，SHA256 `ad1f4fcbf924ffa6…`（本地与远端前缀一致） |
| 根因 | `task_result_urls()` 依赖固定字段白名单 `RESULT_URL_FIELDS`，皮影的 `line_art_url`、`print_template_url` 不在名单内，删除时只有 `_colored.svg` 进入回收集合；同类遗漏还有各工坊的 `completed_sketch_url`、`sheet_music_url`、`model_url` |
| 修复 | 新增 `_generated_urls()`，递归遍历 `result_summary_json`（含嵌套 dict / list）收集所有以 `/static/generated/` 开头的字符串；`task_result_urls()` 取「白名单 ∪ 递归结果」后再统一去签名 |
| 为什么保留并集而不是替换 | `backend/app/api/community.py` 发布作品时用 `task_result_urls(task)` 判断图集归属，`MESH_3D` 的结果 URL 是 `/static/models/…`，不在 `/static/generated/` 前缀下；若只留递归结果，这些图会被判为“不属于该任务”而报 404 |

## 备份路径

| 项 | 值 |
| --- | --- |
| 旧代码备份 | `/tmp/task_assets.py.bak-<epoch>`（`sudo cp` 落位前的线上文件） |
| 上传暂存 | `/tmp/task_assets.py.new`（`scp` 上传，远端 `sha256sum` 校验后再落位） |
| 数据库 | 无迁移、无数据写入，故不做 `db.sql.gz` |
| Nginx | 未改动，`/static/generated/` 的 `no-store` 与双域名配置是同日 13:35 那次部署做的 |

## 部署动作与证据

| 步骤 | 命令 | 结果 |
| --- | --- | --- |
| 上传 | `scp backend/app/core/task_assets.py smxc-azure:/tmp/task_assets.py.new` | 远端 `sha256sum` 前缀 `ad1f4fcbf924ffa6`，与本地一致 |
| 备份 | `sudo cp /opt/jinyun/backend/app/core/task_assets.py /tmp/task_assets.py.bak-<epoch>` | 旧文件已保存 |
| 落位 | `sudo install -o jinyun -g jinyun -m 640 /tmp/task_assets.py.new /opt/jinyun/backend/app/core/task_assets.py` | `jinyun:jinyun 640`，与首次部署的权限口径一致 |
| 重启 | `sudo systemctl restart jinyun-backend` | 正常返回 |
| 服务状态 | `systemctl is-active jinyun-backend` | `active` |
| 健康检查 | `curl http://127.0.0.1:8000/health` | `200` |
| 代码到位 | `sudo grep -c '_generated_urls' /opt/jinyun/backend/app/core/task_assets.py` | `4` |

### 踩坑记录

- `sudo -u jinyun /opt/jinyun/backend/.venv/bin/python -c 'import app.main'` 会因缺少 `JWT_SECRET_KEY` 抛 pydantic `ValidationError`：应用配置依赖 systemd 注入的 `EnvironmentFile`，直接换用户执行时环境里没有。需要在服务器上跑脚本用下面的方式：

  ```bash
  sudo systemd-run --wait --pipe --collect \
    -p User=jinyun \
    -p WorkingDirectory=/opt/jinyun/backend \
    -p EnvironmentFile=/opt/jinyun/backend/.env \
    /opt/jinyun/backend/.venv/bin/python <脚本>
  ```

- 用 `set -e` 串「备份 → 安装 → 导入自检 → 重启」时，导入自检一失败就会跳过重启，出现“文件已换、进程还跑旧代码”的状态（上面的 `ValidationError` 正是这种失败）。自检要么去掉，要么放到重启之后，用 `curl http://127.0.0.1:8000/health` 代替。

## 生产验证（正式 HTTPS，本地脚本，未付费调用模型）

`.local/deploy/verify-shadow-purge.py`：用演示学生账号登录 `https://admin.wentian.org/api`，新建一个 `generation_mode = LOCAL` 的皮影任务，取结果里的三个签名 URL，删除前后各探测一次。

| 检查 | 结果 |
| --- | --- |
| 新建任务 | `POST /api/ai/tasks`（`SHADOW_PUPPET` / `LOCAL`）成功，`task_id = b727e76826e5f18b0387e443d9c51b15` |
| 结果 URL | `colored_image_url`、`line_art_url`、`print_template_url` 三条，去签名后互不相同 |
| 删除前可达性 | `[200, 200, 200]` |
| 删除 | `DELETE /api/ai/tasks/<task_id>` 返回 `removed_assets = 3`、`removed_files = 3` |
| 删除后可达性 | `[404, 404, 404]` |
| 脚本结论 | 末行 `VERDICT PASS` |

对比：修复前同一操作只回收 1 个文件（`_colored.svg`），线稿与纸样 SVG 及其 `Asset` 行会留下。

## 只读巡检：`static/generated` 残留盘点

`.local/deploy/classify-generated-leftovers.py`（服务器副本 `/tmp/classify.py`，经 `systemd-run` 注入 `.env` 执行）遍历 `AiTask.result_summary_json`、`CommunityPost.cover_url`、`CommunityPostDetail.gallery_json`、`UserCollection(ASSET)` 四类引用来源，把 `/opt/jinyun/backend/static/generated/` 下无引用的文件与 `Asset` 行分类。首轮输出 `.local/deploy/leftovers-pretty.json`：

| 指标 | 数量 |
| --- | --- |
| `static/generated` 文件 | 149 |
| 指向 `static/generated` 的 `Asset` 行 | 36 |
| 被任务结果引用 | 26 |
| 被收藏引用 | 5 |
| 孤儿 `Asset` 行 | 10 |
| 孤儿文件 | 113 |

随后用 `--purge-prefix 5fa2be101c106bc7de4c14344ce7ffff` 分两次清掉本轮演示自己产生的 2 行 + 2 个文件（第一次删行、第二次才删文件：文件是否算孤儿取决于行是否还在）。

| 调用 | `Asset` 行 | 孤儿行 | 报告孤儿文件 | 本次删除 |
| --- | --- | --- | --- | --- |
| 第一次 | 36 | 10 | 113 | 2 行、0 文件 |
| 第二次 | 34 | 8 | 115（含本轮自产的 2 个） | 0 行、2 文件 |

`find /opt/jinyun/backend/static/generated -name '5fa2be10*'` 最终为 0。仓库另有 `scripts/prune_orphan_assets.py`，默认 dry-run 只出 JSON 报告，不显式加 `--delete` 不删行也不删文件。

## 孤儿批量清理（2026-10-20 23:18 起，经用户批准）

先备份再执行：`sudo tar czf /var/backups/jinyun/generated-before-orphan-purge-20261020T151859Z.tgz -C /opt/jinyun/backend/static generated`。

清理脚本 `.local/deploy/purge-generated-leftovers.py`（服务器 `/tmp/purge-leftovers.py`，默认只报告，`--apply` 才删）在同一轮里做两遍：先删孤儿 `Asset` 行并提交，再重新分类删文件，因为文件是否算孤儿取决于行是否还在。

| 项目 | 清理前 | 清理后 |
| --- | --- | --- |
| `static/generated` 目录项 | 147 | 26 |
| `Asset` 行（generated 前缀） | 34 | 26 |
| 孤儿 `Asset` 行 | 8（id 36–43，属主 user 1、2） | 0 |
| 孤儿文件 | 113（删行后又暴露 8 个，共删 121） | 0 |
| 仍被任务/收藏引用 | 26 个任务 URL、5 个收藏 URL | 不变 |

清理后核对：`http://127.0.0.1:8000/health` = 200；`GET /api/ai/tasks` 仍 16 件、封面字段正常；`GET /api/mobile/me/collections?kind=ASSET` 3 条、无孤儿；模拟器作品页 6 张签名 SVG 全部加载（`naturalWidth` > 0），破图 0。回滚方式为解上面的备份包：`sudo tar xzf /var/backups/jinyun/generated-before-orphan-purge-20261020T151859Z.tgz -C /opt/jinyun/backend/static`（只恢复文件，`Asset` 行需按备份清单另行导入）。

## 回滚

```bash
ssh smxc-azure
sudo install -o jinyun -g jinyun -m 640 /tmp/task_assets.py.bak-<epoch> /opt/jinyun/backend/app/core/task_assets.py
sudo systemctl restart jinyun-backend
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/health   # 期望 200
```

- 若只用 `sudo cp`，落位文件的属主与权限会沿用 `/tmp` 下的备份（`root` / 644），需再执行 `sudo chown jinyun:jinyun` 与 `sudo chmod 640`，否则可能重现上次的权限问题。
- 回滚只改变之后删除行为的范围；本轮验证已回收的 3 个 SVG 与对应 `Asset` 行不会因回滚而恢复。
- 无数据库迁移、无 Nginx 改动，回滚不涉及 `nginx -t` / `reload`，也不需要恢复 `db.sql.gz`。
