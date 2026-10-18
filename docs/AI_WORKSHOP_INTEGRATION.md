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
