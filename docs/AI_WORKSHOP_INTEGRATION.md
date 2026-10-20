# AI 工坊生图与参考图编辑

更新：2026-10-19。此说明覆盖本次 AI 工坊开发、本地联调与线上部署，不代表项目全量验收。

## 配置入口

管理后台 → 系统设置 → **AI 大模型与多模态接入** → **AI 工坊 · 生图与参考图编辑**。

沿用既有权限：配置读取与修改仅允许 ADMIN。普通教师与学生不能读取密钥。手机端只读取不含密钥的能力开关，不保存或传递模型密钥。

配置仍保存在原有 `sys_config` 的 `llm_settings` 中，新增 `image_generation` 子对象，无结构迁移。保存旧客户端未提交的生图字段时保留原值；密钥回读为 `********`，保留掩码表示保持原密钥，清空表示移除。没有把密钥写入前端源码、APK 或交付包。

## 本次 SenseNova 配置

| 字段 | 配置 |
| --- | --- |
| 启用真实生图 | 开启 |
| 复用文本连接 | 关闭，避免覆盖原有文字模型 |
| 生图 API Base | `https://token.sensenova.cn/v1` |
| 生图模型 ID | `sensenova-u1.5-lite` |
| 支持参考图编辑 | 开启 |
| 编辑请求格式 | SenseNova 图片数组（JSON images） |
| 图片尺寸 | `1024x1024` |
| 图片返回方式 | `b64_json` |
| 超时 | 120 秒 |
| API Key | 在后台填写；文档不包含真实密钥 |

文生图调用 `/images/generations`。SenseNova 编辑调用 `/images/edits`，使用 JSON `images: [{image_url: "data:image/png;base64,..."}]`；标准 OpenAI 文件上传模式则使用 multipart `image`。完整生成地址被粘贴到 Base 字段时，服务端会去除重复的接口后缀。

SenseNova 官方请求说明：[商汤 U1.5 Lite 接入说明](https://www.sensetime.com/cn/news/sensenova-u1-5-lite-token-plan-20260911-1741)。本次实现没有依赖“公测免费”的长期承诺；后续计费及额度以服务商项目为准。

“检查配置与模型访问”只查询模型，不请求图片，不将检查通过冒充真实生图通过。部分兼容网关不提供模型查询，此时明确显示未验证，需要用工坊的实际生成验证。

## 工坊行为

- 青铜、皮影与漆绣均支持选择 **AI 图像生成 / 本地模板**。没有配置生图服务时，AI 选项不可选。
- 显式选择本地模板时不调用文字模型或生图服务；旧客户端未声明模式的请求保持原兼容行为。
- 上传参考图后，AI 模式在开启图片编辑能力的模型上进行重绘。本地模板仅保存该图片作为参考，不自动重绘。
- 生成图片在服务端校验并转存为本地资产，避免临时链接到期。当前接受 PNG / JPEG / WebP，最大 20MB、约 1600 万像素，校验文件实际内容。参考图必须属于当前账号。
- 返回 `generation_method: ai_image`，保留实际模型名。AI 图片不会被历史模板兼容逻辑重新标为本地模板。
- AI 图片可以查看、恢复、收藏、导出及提交社区审核。青铜历史记录恢复原文字描述；上传参考和漆绣参数也随原任务恢复。
- AI 结果为二维图片，不自动提供可编辑矢量、验证过的切割纸样、三维或 LoRA。皮影 AI 结果不显示不存在的线稿/纸样选项。

## 任务与失败处理

`POST /api/ai/tasks` 新增可选 `generation_mode: AI | LOCAL` 和 `request_id`。未传模式的旧请求仍使用原本地模板流程。

同一账号、同一 `request_id` 与内容返回原任务，不重复调用或奖励；同一请求 ID 改变内容返回 409。客户端在请求结果未知的网络失败后保留该 ID，成功收到任务后才结束本次请求身份。同一账号已有活动创作时拒绝并行发起新的 AI 任务。

SDK 自动重试关闭。超时、鉴权、额度、格式错误会显示可理解的错误，不回退成伪造的 AI 成果。成功保存后才登记资产并发放原有一次创作奖励；查询与收藏不重复奖励。

取消只取消应用中的任务结果，不能保证服务商已接受的请求停止执行或停止计费。迟到的返回不会覆盖 CANCELLED 或已超时的任务，不保存该结果、不发奖励。

当前复用进程内 BackgroundTasks；服务进程终止后不盲目重放远程请求。活动任务超过十分钟未更新，会在后续读取/提交时标为中断失败，用户可手动重新创作。这不是跨进程持久队列。

## 验证与产物

本次使用独立本地测试账号，保留原有示范学生、教师与作品。真实调用两次：青铜文生图成功；把该图作为参考，生成红金刺绣效果成功。编辑请求的重复提交复用了同一任务。两项成功任务对应两次奖励，没有重复奖励。

实际图片及调用、资产与奖励核对见 `.local/android/ai-images-real-api-proof.json`。两张图片均为 1024×1024 PNG：

| 内容 | 大小 | SHA256 |
| --- | --- | --- |
| 青铜纹样 | 2,387,996 字节 | `6ed42a785f6d653b0e139a211bee2e4f9db12574a48a243e61e561eaef2ac1f7` |
| 参考图重绘 | 2,514,134 字节 | `200f0ab921f71c64cda414deb4fcde2427e147e9380a70a16118cdcdbf999703` |

后端验证包括真实 OpenAI SDK 请求序列化、标准 multipart / SenseNova JSON 编辑、四个工坊类型、账号与资产隔离、收藏/发布、幂等、失败与取消、任务中断、密钥掩码和旧配置保存兼容。使用独立 SQLite 和模拟上游，不在自动测试中调用付费服务。

```powershell
wsl.exe -e bash -lc 'cd /mnt/d/admin/desktop/codex/school/smxc/jinyun-runxiang/backend && /home/ubuntu/.venvs/jinyun-android/bin/python -m pytest tests/test_workshop_images.py tests/test_mobile_client.py tests/test_security_regressions.py tests/test_lesson_plans.py -q'
node scripts/test_workshop_session_races.mjs
```

后端需安装 `backend/requirements.txt` 中的 Pillow。后台构建与类型检查使用现有 `scripts/run_teacher_workspace.sh` 工作区。Android 沿用现有构建脚本：

```powershell
.\scripts\build_android_debug.ps1 -ApiUrl 'http://127.0.0.1:8000/api'
```

本地联调安装包为 `.local/android/artifacts/jinyun-ai-workshop-local-debug.apk`，需要本机服务与 `adb reverse tcp:8000 tcp:8000`，不能把它当成已部署线上服务的发布包。本次未向已连接的实体手机安装应用。

## 上线与回退

2026-10-19 经用户授权，已更新线上 `admin.wentian.org` 后台与 `core.wentian.org` 后端，配置 SenseNova 生图与 JSON 参考图编辑。通过 HTTPS 实际完成青铜文生图和参考图红金刺绣重绘；重复提交复用原任务，两个成功任务各奖励一次，收藏及最新任务读取通过。

已在服务器 `/var/backups/jinyun/ai-20261018T165039Z` 备份代码、后台、环境配置及完整数据库，安装并验证 Pillow 12.3.0。没有重建数据库、导入本地数据或覆盖既有业务资产；线上验证使用新建的独立测试账号。原有文本设置未被覆盖，新增密钥只保存在服务器配置中。部署清单及验证见 [线上部署记录](AI_WORKSHOP_DEPLOYMENT_20261019.md)。

回退可关闭 `image_generation.enabled` 并恢复备份代码与后台产物；保留任务、图片与资产历史。原文本模型不需要修改，生图密钥不应写入部署脚本或源码包。

## 3D 数字孪生实验室（演示增强，2026-10-19）

AI 工坊首页新增“黑漆描金”风格入口（宣纸底、墨蓝字、朱砂印、描金线），进入 `/ai-workshop/3d`。页面包含 Three.js 实时 GLB 查看器、旋转/线框/视角控制、复原管线动画和馆藏模型库，展台采用黑漆描金视觉而非赛博科技风。

另新增皮影专题页 `/ai-workshop/shadow-3d`：六道工序三维展台（选皮、描样、镂刻、敷彩、缀结、亮影）与“按意生成剪影画像”。剪影生成调用 `POST /api/ai/silhouette/generate`，参数为 `prompt`、`role`、`headwear`、`prop`，返回 600×800 SVG 与标题、诗句。

- 模型库：7 个 CC0 成品 GLB，位于 `backend/static/models/heritage3d/`，来源与许可见 `docs/IMAGE_CREDITS.md`。
- `GET /api/ai/3d/catalog`：返回模型元数据、文件大小、面数与授权信息，公开可读。
- `POST /api/ai/3d/generate`（登录用户）：接收 `prompt`/`style`，从模型库随机选一件，尽量避开该用户上一次结果，写入一条 `MESH_3D` 成功任务并返回模型与演示管线指标。
- 这是**演示型重建**：不生成真实几何，也不声称模型由用户描述生成。响应中 `metrics.mode = DEMO_LIBRARY`，前端明确标注“演示模式”。
- Nginx 需放行 `/static/models/` 到 FastAPI；配置见 `deploy/nginx/jinyun.conf`。

## 工坊首页入口卡（2026-10-19 统一）

`WorkshopPage.vue` 的五张入口卡共用一套固定结构：206px 高、左侧文案 + 右侧 118px 媒体栏、统一序号/印章/标签/底部 CTA。此前 3D 黑漆大卡、皮影独立入口卡与三张高窄工坊卡并存，已全部合并；后续新增工坊只需向 `features` 数组追加一项并复用 `feature-card` 样式，避免再次出现尺寸不一致。

媒体栏统一使用实物或实机渲染图，不再使用线框图标：3D 数字沙盘为 Three.js 展台实拍裁切（`public/design/images/3d-stage-card.webp`，标签“实时演算”），皮影三维营造为馆藏皮影实物图（标签“馆藏皮影”），其余三张沿用馆藏照片。`image` 字段既可填设计节点号，也可直接填 `/design/images/...` 路径；构建脚本会把代码中出现的直接路径一并打进 APK。

## 2026-10-20 工坊成品化三轮改造

按“接线 → 作品闭环 → 上线加固”三轮实施，三轮代码均已完成。

### 一、结果接线与真实标注

- 剪影画像、三维模型结果接入 `files.ts` 的 `saveAsset`，可真正保存/分享；`MESH_3D`、`SILHOUETTE` 加入可收藏类型，收藏回流“我的作品/收藏”，`ProfilePage`、`PersonalServicePage` 的收藏→编辑器映射同步补两类。
- 三维与剪影页新增收藏、导出、返回上一件作品入口；删除“置信度、体素分辨率、伪造阶段耗时”等无法兑现的指标，`DEMO_STAGES` 只保留工序名与 `demo: true`，前端标注“演示馆藏库匹配”“实时渲染 N 帧”（帧率由查看器 `setAnimationLoop` 实测）。
- 三个工坊与剪影/三维页统一加入“请导师点评”入口（`useEvaluation.ts` + `WorkshopReview.vue`）：本地把 SVG 结果栅格化为 PNG 上传，再调用 `/ai/evaluate`，展示评分、维度、点评与奖励。`Model3DViewer.vue` 增加键盘方向键轨道操作、焦点可见样式与 `aria-label`，供无鼠标与无障碍场景使用。

### 二、作品闭环

- 新增 `GET /api/ai/tasks`（`page`/`page_size`/`tool_type`/`status`）与 `DELETE /api/ai/tasks/{task_id}`；删除同时清理 Asset、收藏与 `static/generated` 文件，进行中任务返回 409。
- 新增作品页 `/ai-workshop/works`（`WorkshopWorksPage.vue`）：类型筛选、分页加载、收藏切换、两步删除；`WorkshopPage.vue` 顶部加入“我的收藏 · 历史 · 删除”入口。
- 剪影生成改为真实任务：写入 `AiTask(tool_type="SILHOUETTE")`、生成 `{task_id}_silhouette.svg`、登记 Asset（含大小与 SHA256）、发放一次 +20 能量，支持 `request_id` 幂等。
- 三维、剪影、工坊创作统一加 `request_id` 幂等与响应令牌隔离：账号/路由/恢复版本变化后丢弃旧响应；失败任务提供“重新发起创作”，进行中改为“重新查询任务状态”；离线时禁止发起并显示“当前离线”，`online/offline` 事件实时更新徽标。
- 皮影角色设计补参考图上传：`ShadowWorkshop.vue` 新增“参考图 · 选填”卡片（上传/移除/文案区分 AI 与本地模式），`WorkshopEditorPage.vue` 绑定 `sketch`、`uploading`、`@upload` 并在恢复任务时回读 `sketch_url`。`create_ai_task` 的草图校验从漆绣分支提到全局：必须是 `/static/` 路径、必须是本人 Asset、文件必须存在；入参先剥离签名查询串再落库。本地模板仍不识别图片，结果描述明确“上传参考图仅作为创作参考保留，未进行轮廓识别或草图重绘”。
- 修正青铜工坊两处遗留：纹样分类 tab 改为按 `patterns` 分组自动生成（此前写死的“窃曲纹”是空 tab，而回纹、蟠螭纹、凤鸟纹、蝉纹、夔龙纹、蕉叶纹没有入口）；AI 结果覆盖未保存画布时提示“可点撤销找回之前的手绘排版”（原本只写入 checkpoint 却无提示）。

### 三、上线加固

- 隐私：`app/core/file_urls.py` 用 HMAC-SHA256 给 `/static/generated/*` 生成 12 小时能力 URL，`main.py` 中间件统一签名 JSON 响应并拒绝无签名读取（403）。历史数据不重写，文件仍留在磁盘；`resolve_static_file(..., require_signature=True)` 用于导师点评等读取路径。密钥位于 `backend/data/file_url_secret.key`（首次启动以 0600 创建，Linux 生效；Windows 文件系统不保留 POSIX 权限，只作本机开发用），并发 worker 不会各自生成不同密钥。**部署注意**：多 worker 必须共享同一主机与同一密钥文件（或把该路径显式挂到共享位置），否则签名互不认；不要给签名 URL 加 CDN 长缓存；密钥不应进源码包，轮换后旧链接全部失效，需在低峰执行。
- 限流与额度：`app/core/quota.py` 支持 `SysConfig(ai_quota)` 覆写，默认每人每日 60 次（剪影 50、三维 50）与每分钟 30 次，超出返回 429；`GET /api/ai/quota` 供前端展示剩余次数，生成响应内嵌 `quota` 字段。
- 内容安全：`app/core/moderation.py` 复用后台敏感词配置，控制字符/零宽字符清洗 + `INJECTION_PATTERNS` 提示注入识别 + `as_untrusted_data` 定界，命中返回 422“未通过内容检查”。工坊创建、剪影生成、导师点评、社区发布全部走同一套检查；点评的用户文本以不可信数据块送入模型。
- 清理与可观测：`scripts/prune_orphan_assets.py` 覆盖 `generated/` 与 `uploads/`，并把 `UserCollection` 视为有效引用；每次成功生成写 `OperationStatDaily.ai_generate_count`（数据看板趋势同源）；`GET /api/ai/stats`（仅管理员）按工具聚合近 1–90 天真实漏斗（总数/成功/失败/取消/成功率/平均耗时/每日任务数/当前额度配置），后台 `ModelsView.vue` 顶部新增“AI工坊生成漏斗”面板，非管理员请求失败时面板自动隐藏；工坊日志改 `logger.warning`，不再 `print`。

### 四、独立复审后的修正

派独立 reviewer 复审后，按证据修正以下问题（每条都补了回归）：

- 删除作品不再动共享文件：`DELETE /api/ai/tasks/{id}` 之前会沿 `mesh_3d_url` 删到 `static/models/heritage3d/*.glb`（馆藏 CC0 模型不在版本库内，一个学生删除作品就会让所有人的三维结果和模型库同时坏掉）。现在只对 `generated/` 前缀的文件执行 unlink，Asset/收藏行照常清理。
- 能力 URL 守卫不再被未规范化路径绕过：`StaticFiles` 会折叠重复斜杠和 `..`，而中间件原本只看原始路径，`/static//generated/x`、`/static/uploads/../generated/x` 能绕过 403。改为按同一规则 `file_urls.normalize_path()` 归一化后再判定（含百分号解码）。
- `sign_json` 不再截断重签：原 `(?!\?exp=)` 前瞻在回溯失败时会少匹配一个字符，把已签名的 URL 变成 `...sv?exp=<新签名>...?exp=<旧签名>` 这种坏链接。改为要求名字边界干净且已带查询串的链接一律原样跳过；`signed_url` 也不再给已有查询串的 URL 追加参数。
- 内容检查补三口子：`忽略\n指令`、全角/西里尔同形字（`ｉｇｎｏｒｅ instructions`）、软连字符 `U+00AD` 之前能绕过；现在匹配前会同时看原文、NFKC 折叠与空白折叠三种形态，`^\s*system\s*:` 加 `MULTILINE`。导师点评的 `title/notes/heritage_type` 三个字段全部先清洗再送模，并以 `as_untrusted_data` 定界（此前只清洗不采用，模型收到的是原始文本，且 `heritage_type` 完全未校验）；`heritage_type` 等字段加了长度上限。社区发布改用同一套 `find_blocked_text`（此前是原始子串匹配，插一个零宽字符就能自动过审）。
- `resolve_static_file(..., require_signature=True)` 之前只在“带查询串”时校验签名，裸的生成文件链接服务端可读；现在只要落在 `generated/` 前缀就必须有有效签名，`uploads/` 不受影响。
- 作品页账号隔离：`WorkshopWorksPage.vue` 原来只在进入页面时加载一次，同一台平板上切换账号会继续显示上一位学生的作品（缩略图还是 12 小时有效的能力 URL），收藏/删除也会打到错误账号。现在监听 token/uid 变化即清空并重载，删除与收藏的回调按会话令牌隔离，翻页/切筛选会清掉“再点一次确认”的预备状态。
- 导出文件容器不再被签名骗过：`saveAsset` 之前用整串 URL 正则取扩展名，签名后的链接永远匹配不上，本地 SVG 会被存成 `.png` 名字。现在按去掉查询串的路径判定，并以真实容器纠正传入的文件名。
- 运营侧配置：`deploy/nginx/jinyun.conf` 的 `/static/generated/` 段加 `expires -1` + `Cache-Control: no-store`（签名链接等价于短时凭据，缓存下来等于绕过隔离）；`.gitignore` 补 `backend/data/*.key`，避免把签名密钥提交进仓库。密钥改为 `O_CREAT|O_EXCL` + 0600 创建，两个 worker 同时首启不会各造一把。

已知未做（保留为后续项，非本轮范围）：`/ai/evaluate` 只受每分钟节流、不计入每日额度，也不写 `AiTask`，因此 `/ai/quota`、`/ai/stats` 看不到它；每日额度在跨 worker 时仍按进程内节流（默认 2 worker，等效 60/分钟）；`OperationStatDaily` 计数与上海日口径、`generated/` 文件裁剪仍不覆盖已删除任务；上传的参考图不会被删除流程回收（它们在 `uploads/`，可能被别处引用）。

### 五、真机演示暴露的删除残留

当天深夜在模拟器接生产后端演示时发现“删除作品”对皮影没做到完全回收，按证据修正并补回归：

- 现象：删除一件皮影（`SHADOW_PUPPET`）作品后，服务器上只回收了 `<task_id>_colored.svg`，`<task_id>_lineart.svg` 与 `<task_id>_template.svg` 连同它们的 `Asset` 行仍留在 `backend/static/generated/` 下。皮影 LOCAL 分支一次会写三个 SVG，`backend/app/api/ai_workshop.py` 会为结果里每个 `/static/generated/` URL 建一条 `Asset` 行，因此这是用户可感知的隐私与存储泄漏。
- 根因：`backend/app/core/task_assets.py` 的 `task_result_urls()` 只扫描常量 `RESULT_URL_FIELDS = ("colored_image_url", "rendered_image_url", "image_url", "mesh_3d_url", "vector_svg_url")` 加一个 `result["model"]["url"]`，而皮影结果用的是 `line_art_url` 和 `print_template_url` 这两个字段名，青铜/时调/漆绣结果里还存在 `completed_sketch_url`、`sheet_music_url`、`model_url` 等同类字段，全部不在白名单内；删除流程 `delete_ai_task()` 依赖 `task_result_urls(task)` 得到要回收的 URL 集合，因此漏删。
- 修法：新增 `_generated_urls(node)` 递归遍历 `result_summary_json`（dict / list / tuple / str），凡以 `/static/generated/` 开头的字符串都收进集合；`task_result_urls()` 返回“原白名单字段 ∪ 递归遍历结果”再做 `split_signature` 归一。这里刻意用并集而不是替换：`backend/app/api/community.py` 的发布接口用 `task_result_urls(task)` 判断图集 URL 是否属于本人作品，而 MESH_3D 的模型地址是 `/static/models/heritage3d/*.glb`（不在 `/static/generated/` 前缀下），只保留递归遍历结果就会把这些地址从集合里剔除，导致学生把三维作品发布到社区时被判定为“图片不存在或不属于当前用户”。同时把共享库模型排除在删除目标之外也更安全：`delete_ai_task()` 只有对 `generated/` 前缀的文件才 `unlink`。
- 回归：`backend/tests/test_workshop_governance.py` 新增 `test_deleting_a_shadow_work_removes_every_generated_file`，用 `assets` fixture 把静态目录重定向到 tmp_path，创建一件 LOCAL 皮影作品，断言三个产物文件名互不相同且落盘，删除时返回 `removed_assets == 3 and removed_files == 3`，三个文件从磁盘消失，该用户 `Asset` 行清零。后端全量在 WSL 下 `pytest tests/ -q` 为 `168 passed`（此前 167）。
- 生产复测：部署该修复后，用演示账号新建并删除一件 LOCAL 皮影作品 `b727e76826e5f18b0387e443d9c51b15`，三个签名 URL 删除前 200、删除后 404，接口返回 `removed_files=3`（修复前为 1）。
- 独立复审发现并已修复的回归：第一版递归收的是「任何 `/static/generated/` 字符串」，而创建接口允许把自己另一件作品的生成 SVG 当参考图（`sketch_url` 只校验 `Asset.created_by` 与图片类型），于是删作品 B 会连带删掉作品 A 的文件。现改为只收本任务前缀 `/static/generated/{task_id}_`，并新增 `test_deleting_a_work_never_removes_another_works_files`（建 A → 用 A 的成品当 B 的参考图 → 删 B → A 的文件仍在、列表仍有封面）。顺带补了 `backend/tests/conftest.py`，让单个测试文件可以独立运行（此前只有整目录跑才会注入 `JWT_SECRET_KEY`）。
- 顺带记录一条真机演示观察（不是缺陷）：作品列表接口返回的封面是相对路径 `/static/generated/...?exp=...&sig=...`，前端 `user-web/src/mobile/api.ts` 的 `mediaUrl()` 只在 `/static/design/` 分支追加 `?v=hd1`，对 `/static/generated/` 原样拼接 API 域名，签名查询串得以保留，因此设备端 `<img>` 能正常加载（实测封面 `naturalWidth` 540/600，破图 0）。

### 验证

后端全量回归 `166 passed`（`tests/test_workshop_governance.py` 十项：签名收藏作品全生命周期与删除、过期签名拒绝、未规范化路径与遍历形式绕过、共享三维模型不被删除、屏蔽词+额度+注入、清洗规则覆盖换行/同形字/零宽、真实三维指标与收藏、管理员漏斗与权限、作品列表分页/筛选/归属/409、皮影参考图归属与诚实标注）。`user-web` `vue-tsc --noEmit` 与 `admin-web` `vue-tsc --noEmit --skipLibCheck` 均 0 错误。生产构建产物用 360×780 CDP 巡检七条工坊路由（`.local/android/workshop-ui-audit-20261020.json`）：五张卡等高 206px 且媒体图全部加载、`#/ai-workshop/works` 正常渲染筛选与登录引导、皮影表单出现“参考图 · 选填”上传控件、青铜分类为八个真实分组、无横向溢出、无未捕获异常（仅该浏览器环境访问线上 API 的 CORS 报错）。安装包 `.local/android/artifacts/jinyun-runxiang-debug.apk` 内置 `https://admin.wentian.org/api`；由于线上后端尚未部署本轮改动，收藏/作品列表/额度等新接口在云端会 404，因此本轮未做设备安装验收，也不要用该包做线上演示。
