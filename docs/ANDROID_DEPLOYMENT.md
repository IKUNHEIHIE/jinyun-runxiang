# Android、服务端与教师工作台开发运行

本说明对应隔离开发环境；不覆盖已有生产部署。开发数据不会自动清空。正式教学内容、支付、模型服务、远程课堂视频均需要独立配置。

截至2026-10-18，最新开发包为个人中心恢复阶段 `BB4FF6A5…`，完整产物、测试和迁移范围见文末。下列按日期保留的包均为历史记录。

## 当前环境

- Windows Node 26；WSL Ubuntu Node 22、Python 3.12、Docker。
- JDK 21：`D:\Android\Jdk21\jdk-21.0.12.1+1`。Gradle 8.14.3 不支持当前 Android Studio 自带的 Java 25，本项目构建使用 JDK 21。
- Android SDK：`D:\Android\Sdk`，compile/target SDK 36，最低 Android API 24。
- 测试模拟器：`Medium_Phone_API_37.0`，serial `emulator-5554`，1080×2400、density 420。尚不能代替实体设备兼容性测试。
- 手机界面：Vue 3、Vite 7.3.7、Capacitor 8；教师工作台：现有 Vue Pure Admin。

## 启动隔离服务端

在 WSL 安装项目锁定依赖并创建 Python 环境后运行：

```bash
python3 -m venv ~/.venvs/jinyun-android
~/.venvs/jinyun-android/bin/pip install -r backend/requirements.lock.txt pytest
~/.venvs/jinyun-android/bin/python scripts/start_android_dev.py --serve
```

脚本只管理 Docker 容器 `jinyun-android-mysql`、卷 `jinyun_android_mysql_data` 和数据库 `jinyun_android_dev`。MySQL 绑定 WSL `127.0.0.1:13306`。不会操作其他容器，不会重置已存在的开发数据。

随机开发凭据保存在 `.local/android/credentials.json`，不得提交、截图或公开上传。该文件包括 `student_demo`、`teacher_demo`、`admin_demo` 的开发密码及数据库、JWT 配置。应用服务默认监听端口 8000。

初始用户、课程、班级和目录仅用于开发联调。课程正式视频尚未提供，其中皮影课程使用仓库自带 10 秒片段验证播放器，界面明确标记为联调样片。商品价格、图片来自设计稿，未生成虚假支付、销量、关注、评分和学习统计。

## 启动独立教师后台（WSL）

从仓库根目录执行：

```bash
bash scripts/run_teacher_workspace.sh
```

脚本将源码同步到 `~/.local/share/jinyun-teacher-workspace`，Linux 依赖与 Windows `node_modules` 分开，使用锁文件安装并启动端口 5173。每次修改源码后重新运行脚本或同步源码；修改源仓库不会自动同步到该目录。

访问 `http://127.0.0.1:5173`，使用 `teacher_demo` 的本地开发凭据登录。TEACHER 只显示教师工作台；ADMIN 可进入原有管理界面和教师工作台。真实权限由服务端数据库角色与班级归属检查执行。学生账号不能登录管理后台。

教师工作台提供班级创建、邀请码、真实学情、考勤、作业发布与批改、备课历史/PPTX 导出、班级通知、课堂讨论与举手。未设置 HTTPS 视频地址的课堂提供文字互动，不声称已接入远程音视频。

构建教师后台：

```bash
bash scripts/run_teacher_workspace.sh build
```

## 构建 Android Debug APK

在 Windows 仓库根目录执行：

```powershell
cd user-web
npm ci
cd ..
$env:GRADLE_USER_HOME = 'D:\Android\Gradle'
.\scripts\build_android_debug.ps1
```

脚本查找 SDK 和 JDK 21，执行类型检查、Vite Android 模式构建、Capacitor 同步、应用 clean/debug 构建，并将 APK 复制到 `.local/android/artifacts/jinyun-runxiang-debug.apk`，输出 SHA256。完整原始设计资源继续保存在源码目录，仅当前手机页面使用的素材进入 APK。

当前对 Capacitor Android 8.5.3 保留一项临时兼容修复：`user-web/scripts/patch-capacitor.mjs` 为页面根元素尚未创建时的安全区域注入增加空值检查，后续页面提交仍正常写入间距。安装依赖的 postinstall 与构建脚本均会检查并幂等应用；上游代码未知变化时构建停止，升级框架后应复核或移除修复。相关官方问题为 <https://github.com/ionic-team/capacitor/issues/8530>。JDK 版本检查直接读取标准错误流，已兼容 Windows PowerShell 5.1。

开发 API 默认为 `http://127.0.0.1:8000/api`。安装前确认目标设备，不要向未知设备批量安装：

```powershell
& 'D:\Android\Sdk\platform-tools\adb.exe' -s emulator-5554 reverse tcp:8000 tcp:8000
& 'D:\Android\Sdk\platform-tools\adb.exe' -s emulator-5554 install -r '.local\android\artifacts\jinyun-runxiang-debug.apk'
& 'D:\Android\Sdk\platform-tools\adb.exe' -s emulator-5554 shell am start -n com.jinyun.runxiang/.MainActivity
```

`adb reverse` 将设备自己的回环端口映射到开发电脑。测试模拟器原有代理配置导致 `10.0.2.2` 超时，因此本机采用上述映射；没有修改模拟器原有代理。

连接远程服务时构建新的 Debug 包：

```powershell
.\scripts\build_android_debug.ps1 -ApiUrl 'https://你的服务域名/api'
```

服务端必须可通过 HTTPS 访问；本地明文仅在 Debug 网络配置内对回环地址与模拟器主机地址开放。正式 Release 还需签名、正式服务地址、发布配置与真机验证，当前 Debug 包不能直接视为生产发布包。

## 数据库结构与验证

- 新库使用 `database/schema_all.sql`，然后单独执行 V17 初始化徽章目录；两个 Compose 配置已为全新数据库按此顺序挂载。不要在执行完整结构后重复执行含 ALTER 的旧迁移。
- 已升级至 V9 的既有库按 V10、V11、V12、V13、V14、V15、V16、V17、V18、V19、V20 顺序执行，记录已执行版本；V12、V16 的 ADD COLUMN 只能执行一次。V20 幂等增加 `assignment.contest_id` 并创建 `contest`、`contest_entry`。V14 增加作品图集、规格、鉴赏要点及评论点赞记录。V15 新增每日学习记录，并从仍保存的进度、完成时间和离线事件按上海日期回填；无法恢复旧版已覆盖的日期。隔离开发启动脚本会创建该表并幂等回填，不清空数据。
- V16 保存打卡定位精度与 ONSITE/CLOUD/UNCERTAIN 分类，将旧的用户/基地唯一索引改为普通索引，允许精度不足后再次到访；奖励仍按独立唯一流水去重。启动脚本幂等补齐列与索引。旧记录没有当时精度，继续按历史距离规则读取。
- V16 回滚脚本在同一 ALTER 中恢复旧唯一约束并移除新增列；存在重复到访时会拒绝执行。不得为强行回滚删除真实到访记录，代码回滚可保留新增结构。
- V17 初始化五项原稿课程徽章、现场徽章和探路者，并确保用户/徽章唯一约束；发现旧重复记录时拒绝加约束，不删数据。已保存的整门已发布课程完成记录可回填，重复执行不覆盖管理员字段和原解锁时间。其回滚脚本保留目录、约束和历史授予，只用于安全回滚代码。正式环境不用包含演示统计的 `seed_data.sql`。
- V18 增加反馈回复与兑换处理的六列；V19 增加备课请求标识、模式和教师/请求唯一约束，两者均按实际结构幂等补齐。V19旧行保持NULL，不推测旧生成模式；同教师重复请求返回同一记录，不同配置返回409。V18/V19回滚仅回退代码并保留新增数据，详见各迁移与回滚脚本。
- 升级前备份并检查结构。`database/migrations/rollback/` 会删除新增记录，生产回滚必须先确认；一般代码回滚可保留新增表以避免数据丢失。
- `scripts/audit_mobile_migrations.py` 只在专用测试容器内新建审计库，验证初始化、升级和空库回滚，审计库保留供检查，不触及应用库。

接口回归：

```bash
cd backend
~/.venvs/jinyun-android/bin/python -m pytest tests/test_mobile_client.py tests/test_security_regressions.py tests/test_lesson_plans.py -q --disable-warnings
```

当前通过 130 项（test_mobile_client.py 86 项 + test_security_regressions.py 24 项 + test_lesson_plans.py 20 项）；仍有既有 `datetime.utcnow()` 弃用等提示，本轮3954条，日志 `.local/android/test-lesson-plan-backend-full.log`。自动化测试使用每项独立的 SQLite 数据库；另有真实 MySQL 结构迁移验证和浏览器/Android 联调证据，不能将接口测试等同于全部页面验收。

在仓库根目录运行 `node scripts/test_progress_queue.mjs`，验证实际客户端队列在上海跨日时保留每天记录、同日合并、完成状态保留及部分确认后重试，并阻止换登录令牌后继续发送旧账号批次。该测试隔离网络与设备存储，不修改开发用户数据。

运行 `node scripts/test_mobile_session_races.mjs`，验证实际客户端请求代码中旧账号的延迟 401、资料和退出响应不会清除新账号；当前账号的 401 仍清理本地私有会话并显示登录入口。

运行 `node scripts/test_course_player_progress.mjs`，验证实际播放器组件在恢复历史位置时不保存进度，实际播放仍可保存完成，切章节、切账号和延迟加载保持隔离。浏览器与 Android 也已验证恢复到 10 秒但未播放时不增加离线事件，手动重播后保存且徽章/能量不重复。

皮影任务图片与纸样由本地模板生成，语言模型仅可辅助文字分析；当前没有三维生成服务。`POST /api/ai/tasks` 的 `MESH_3D` 请求返回 HTTP 503，不写入任务或发放奖励。任务查询会修正历史三维能力误述及本地配色色板，不修改保存记录；无需新增数据库迁移。原生导出根据当前选择返回彩色图、轮廓图或纸样，三种文件已与服务器原件逐字节核对。纸样仅作参考，实际制作与设备切割未验证。

## 皮影阶段安装包记录（2026-10-17）

该阶段 Debug APK：188,041,554 字节，SHA256 `E016C7FBF28270E62DD7906B4BCFF71F3722BD4F854CEF49ACE840DA6D135EE2`，构建日志 `.local/android/build-shadow-workshop-resumed-final.log`。该包在模拟器实际完成 360dp/约 411dp 皮影整页、指定收藏恢复、社区发布与账户刷新；纸样导出证据保留实际使用的前一包版本，详见 `.local/android/shadow-workshop-evidence.json`。此记录为历史版本，不扩大为当前包全量验收。

新增 `POST /api/ai/tasks/{task_id}/favorite`，请求 `{collected: true|false}`，只允许收藏本人成功任务的规范生成图片，重复设置幂等；查询返回 collected。个人收藏 ASSET 结果带 task_id/tool_type，客户端用它打开指定创作。复用原有收藏表，无新增结构迁移。皮影参数 face_style 支持 CLASSIC/FLORAL/BOLD，角色与主色进入本地二维模板；实体制作和外部模型仍未验证。

仓库根目录运行 `node scripts/test_workshop_session_races.mjs`，验证实际工坊/个人中心/收藏组件的指定任务、选中导出、统计刷新及切换令牌/卸载后的延迟响应隔离。皮影阶段日志在 `.local/android/test-shadow-workshop-resumed.log`（84 项通过）。

## 漆绣阶段安装包记录（2026-10-17）

漆绣阶段 Debug APK 位于 `.local/android/artifacts/jinyun-runxiang-debug.apk`，221,605,925 字节，SHA256 `7C912F8EAB9665430DFC52EF1C10E134A75BD10405649C1207814109F7FCAF19`。构建日志 `.local/android/build-lacquer-workshop-final.log` 包含类型检查、前端构建、Capacitor 同步和 Gradle 成功记录。本轮后端 101 项回归通过，日志 `.local/android/test-lacquer-workshop.log`。

`LACQUER`/`EMBROIDERY` 的 `input_payload.local_pattern` 接受 `FLORAL`、`GEOMETRIC`、`AUSPICIOUS`，`color_palette` 为有效十六进制色数组。可选 `sketch_url` 必须对应本人拥有、实际存在的本地上传图片；仅保存为参考，不自动分析或重绘。提示词长度、纹样类型、色板、文件归属/MIME/路径在创建任务及奖励前校验。结果明确返回本地模板、模型/重绘/LoRA不可用、无已补全草图和无A4纸样；读取旧记录同样修正能力说明，但不改写原数据库记录。本轮复用任务 JSON 与 ASSET 收藏，无新增结构迁移。

当前包原生验证两种屏宽、旧几何收藏恢复、从保存任务生成花鸟纹样后保持创作区位置、首页/个人中心能量 260→280、系统导出与取消；导出文件与服务器逐字节一致。55D36B2F…包验证几何收藏/导出，8B7927D8…包验证朱砂吉祥文字生成/导出/社区作品4发布，不能混称为当前包全部复测。三个实际任务、导出散列、13张当前包截图与版本范围保存在 `.local/android/lacquer-workshop-evidence.json`。模拟器已恢复 1080×2400、420dpi、Asia/Shanghai。

当前 PID 7008 的有限日志有 Chromium first_paint 统计诊断与取消分享的桥接消息，未见 FATAL EXCEPTION/Uncaught；不等于全部异常与生命周期通过。原始设计 PNG、真实设备、草图重绘/LoRA、实体制作、授权、完整竞赛及其余页面验收仍未完成。客户端专项回归还覆盖漆绣参数/参考恢复、失败任务提示、创建后清除旧 task_id 与切换会话后的延迟上传隔离。


## 当前用户服务与安装包（2026-10-17）

用户服务阶段APK为 .local/android/artifacts/jinyun-runxiang-debug.apk，221,606,689 字节，SHA256 `8315E84F6BA713C1075943308E080CFB810DF495D90C151109673B29D233CD43`。构建日志 .local/android/build-support-android-final.log；WSL后台构建日志 .local/android/build-support-admin.log。该后台源码通过npm run typecheck，WSL独立副本已同步，管理员在 /#/support/index 进入“兑换与反馈”，教师仍只能访问教师工作台。

升级到V17的库继续执行 database/migrations/V18__support_handling.sql。V18为可重复执行的加列迁移：user_feedback增加reply_text、handled_by、handled_at；energy_exchange增加handling_note、handled_by、handled_at。旧处理人和时间保持NULL，旧回复读取为空串；不回填虚构结果。V18回滚脚本只用于回退应用代码，保留六列和所有处理记录。全量schema已包含这些字段，开发启动脚本会幂等补齐；迁移审计在新建的专用审计库验证，不清空应用库。

新增 GET /api/mobile/me/feedback（仅本人记录）、GET /api/mobile/admin/feedback、PUT /api/mobile/admin/feedback/{id}。反馈PENDING可进入PROCESSING或RESOLVED，PROCESSING可完成回复；RESOLVED必须有非空回复，结束后不能覆盖或退回。完全相同的重复操作返回已有结果，不改写处理人/时间。管理反馈和兑换列表都返回items/total/page/page_size，支持status、page及1–100范围的page_size；原管理兑换列表响应由数组改为该分页结构，本仓库新工作台已适配。

PUT /api/mobile/admin/exchanges/{id}的FULFILLED现在要求非空tracking_no（发放凭据或物流单号），handling_note为用户可见说明；CANCELLED不能带发放单号，工作台要求填写取消原因。终态不能互相修改，相同终态但不同凭据/说明返回409；相同重复提交不重复退款。处理人来自真实管理员身份，客户端不提交操作者ID。

回归日志 .local/android/test-support-handling.log 为104项通过。仓库根目录运行 node scripts/test_support_session_races.mjs，验证实际管理/手机组件的延迟列表、失败草稿、重复提交和换号隔离，以及管理HTTP层的旧401处理；node scripts/test_mobile_lifecycle_recovery.mjs 验证真实根组件的联网/路由/前台恢复、同令牌合并、不同令牌并行隔离及监听器清理。既有会话与工坊专项测试保持通过。

19B62707…包执行原生提交、WSL后台处理和411dp回显；用户服务阶段8315E84F…包验证360dp同记录、断开开发API后冷启动显示未知余额、恢复连接后账户260能量。真实MySQL重复处理后能量、库存、处理人和时间不变，测试商品已下架且记录保留；没有实际支付/寄送。版本与9张截图见 .local/android/support-flow-evidence.json。全部页面视觉、长列表返回位置、目录管理、授权和完整竞赛仍待完成。

## 市集专项阶段安装包（2026-10-17）

市集阶段APK：当时产物路径 .local/android/artifacts/jinyun-runxiang-debug.apk，226,906,885字节，SHA256 02C5C1149FE2F566D6DCD6DBBE6812E7D97BE73C27F72EC6C16547290C552552。该路径现已更新为下节教师页包。构建日志 .local/android/build-market-android-final.log 包含类型检查、Vite Android构建、Capacitor同步及Gradle成功。构建方法仍为 scripts/build_android_debug.ps1，开发API为 http://127.0.0.1:8000/api，安装后配置 adb reverse tcp:8000 tcp:8000。

已执行adb install -r并在API37模拟器运行。最终包360dp验证首屏/商品/浏览更多/能量不足保留输入及系统返回，约411dp检查首屏/兑换。上一C4743331…包创建并取消开发订单2；全部截图逐一记录散列，不把历史专项混称为当前包全量复验。真实MySQL确认该单取消、SKU库存10、基金记录0、能量260，原兑换两笔及库存10/10/1保留；无实际付款/寄送，本轮不改后端/迁移或重置数据。

四份客户端专项日志 .local/android/test-market-client.log；完整本轮记录 .local/android/market-page-evidence.json。模拟器恢复1080×2400/420dpi/Asia/Shanghai。原始画布PNG、全量视觉、正式支付、授权与生产对接、完整竞赛仍未通过验收。

## 教师个人中心阶段安装包（2026-10-17）

教师中心阶段 APK（路径已由后续包更新）：`.local/android/artifacts/jinyun-runxiang-debug.apk`，241,507,079 字节，SHA256 `D9D41D023E85A4EF9F1F5B11F024C1CE5CEC29AD87F2D7FB934B6416E04DE6AC`。构建日志 `.local/android/build-teacher-profile-android-final.log` 记录类型检查、Vite、Capacitor 同步和 Gradle BUILD SUCCESSFUL；构建/安装与端口映射沿用前文方法。已安装于 emulator-5554 并验证教师登录状态、360dp/约411dp 教师页、三项教学入口/返回和未达成条件弹窗。证据中每张原生截图带对应 APK 散列，早期 BB513C5D…包的截图单独标注。

本次 `/mobile/teacher/overview` 兼容增加统计及四项当前里程碑，不更改数据库列，不写永久徽章或能量。已有 V18 数据库即可运行；升级后继续使用原有开发数据。曾停止的现有 MySQL 容器、API、手机前端与 WSL 教师工作台已恢复，未清空或重新初始化数据库，其他 Dify 资源未改动。开发 API 8000、手机预览 5174、独立教师工作台 5173；后台源代码本阶段无新增修改。

新增专项在仓库根目录运行：

```bash
node scripts/test_teacher_profile_session.mjs
node scripts/test_mobile_lifecycle_recovery.mjs
```

前者覆盖统计合并、旧账号/弹窗隔离、隐藏/联网刷新及卸载清理；后者增加角色延迟恢复和学生转离教师页断言。两项通过日志为 `.local/android/test-teacher-profile-client.log`。接口 107 项包含有效成员去重/跨班隔离、上海日期、未知统计、GET 不授奖与 BALLAD 新/历史结果修正；只使用隔离测试库，不调用外部作曲服务。BALLAD 谱面是本地模板，伴奏/演唱尚未提供，旧数据库内容保留但读取不再暴露雨声音效为生成音频。

真实开发记录核对见 `.local/android/teacher-profile-evidence.json`：2026-10-17 班级1/学生1考勤 PRESENT，由教师2保存，到课率与提交率100%，教师/学生能量100/260、教师永久徽章0。14张分版本原生图与2张浏览器图、相同返回边界、有限进程日志均单独记录；模拟器1080×2400、420dpi、Asia/Shanghai。原始画布PNG、白色时钟图标/叠层裁剪、学情/备课页重新视觉校准、完整竞赛和全生命周期仍待完成。

## 班级学情专项安装包（2026-10-17，历史版本）

APK `.local/android/artifacts/jinyun-runxiang-debug.apk`：274,507,902字节，SHA256 `AEC574CE686CD987671ED1B13A5838CAB8226650168B98BBE11327DF7DB0ACBB`。最终构建日志 `.local/android/build-teacher-analytics-android-icon-final.log` 包含类型检查/Vite/Capacitor/Gradle成功，已安装emulator-5554。构建、开发API 8000与adb reverse方法沿用前文；此包仍是Debug开发产物，原图较大，正式发布前需继续评估体积。

本轮新增班级analytics读取接口及可选考勤day字段，不改表或初始化数据。旧API字段保留，手机/WSL教师后台使用同一有效学生范围、去重进度/徽章和上海日期；后台源码同步后类型检查与WSL构建通过（`.local/android/build-teacher-analytics-admin.log`）。新建空班ID2仅供联调且保留。原班级1的开发考勤经过后台LEAVE→Android PRESENT→后台刷新/MySQL核对；能量与授奖未改变。

回归日志 `.local/android/test-teacher-analytics.log` 为110项通过、3432条既有弃用等提示。仓库根目录 `node scripts/test_teacher_analytics_session.mjs` 验证真实组件班级/账号旧响应、同班合并、未知排名、草稿跨日、重复保存与清理；连同教师页和根组件恢复专项，三项通过日志为 `.local/android/test-teacher-analytics-client.log`。过期考勤日期409拒绝、有效章节/重复记录、近七日上海边界与班级隔离均有独立数据库测试。只读实际API/MySQL与23张分版本原生图、6张浏览器图见 `.local/android/teacher-analytics-evidence.json`。

最终AEC574CE…包核对360dp/约411dp首屏和徽章区；F2DF5CE5…包的原生空班/弹窗/考勤闭环保留版本标识。模拟器恢复1080×2400、420dpi、Asia/Shanghai，有限进程日志未见崩溃模式匹配。原始画布PNG、背景透明度/裁剪、源页脚矢量、书法/策展/传承规则和完整备课/竞赛等仍待补齐。

## 备课阶段开发包（2026-10-18，历史版本）

APK `.local/android/artifacts/jinyun-runxiang-debug.apk`：274,627,373字节，SHA256 `314D630A00B122F37324942501109F418F66337BFAAC326645C93846A9783666`。`build-lesson-plan-android-source-ids.log`记录类型检查、Vite、Capacitor及Gradle成功；实际设备内APK散列与产物一致。该包只在API37模拟器验证，没有实体设备或生产发布结论。

升级到V18的既有库执行 `database/migrations/V19__lesson_plan_requests.sql`，不要重置或重新播种数据库。当前全量schema和开发启动脚本已包含V19。真实MySQL新库/V9升级/重复执行/保留记录代码回滚见 `.local/android/migration-audit.json`；开发库迁移前后旧方案内容摘要一致，见 `lesson-plan-migration-dev.json`。回滚V19保留两列及唯一索引，旧应用忽略即可。

教师手机与独立后台均默认LOCAL本地课程模板。`/api/mobile/teacher/lesson-plan-capabilities`仅返回能力开关和时长范围。AUTO需已有的服务端模型配置，不向客户端返回密钥；本轮只模拟模型成功/失败，没有付费调用。模型超时或内容不完整回退时明确标记来源。旧历史不重写，缺失部分在课件中明确提示；不再提供虚构下载链接。

`node scripts/test_lesson_plan_session.mjs`执行真实组件及文件助手的延迟账号、请求重试、重复点击、历史刷新、取消分享及缓存清理专项，两组通过。后端130项通过；后台类型检查与WSL构建见 `typecheck-lesson-plan-admin.log`、`build-lesson-plan-admin-final.log`。类型检查在最后一处仅模板的学段/时长显示调整前执行，最终源码构建在调整后执行。

主要生成/跨端/断网流程使用B2466C9D…包；314D630A…仅修正两处设计追踪属性后重建，补检360dp/约411dp配置、历史、结果和360dp分享/取消。28张分版本原生、3张浏览器、实际课件及11页渲染散列统一见 `.local/android/lesson-plan-evidence.json`，不要将旧版本流程混称为最终包全量复验。有限进程日志0条崩溃模式匹配；模拟器恢复1080×2400、420dpi、Asia/Shanghai，原代理与API端口映射保留。完整视觉、外部服务、旧Android、进程回收与全项目剩余工作仍待完成。

## 首页阶段安装包（2026-10-18，历史版本）

当前APK `.local/android/artifacts/jinyun-runxiang-debug.apk` 为274,630,887字节，SHA256 `D1101DF4C9B30A75F41AAD3B1BF450C6046E62C67E48AE4CB80DFAA6DC30C04A`。构建日志 `.local/android/build-home-android-level-final.log`，构建脚本含vue-tsc、Vite、Capacitor与Gradle；设备内APK散列与产物相同。备课阶段314D630A…另存 `.local/android/artifacts/lesson-plan-314d630a-debug.apk`，其清单已改指向存档，避免被当前产物覆盖。

无需新增依赖、后端配置或迁移，沿用V19与开发API映射。`node scripts/test_home_session.mjs`验证真实首页脚本的筛选晚响应、独立错误、重复签到、账号隔离、旧查询覆盖、可见性/卸载；`.local/android/test-home-client-final.log`一组通过。备课组件及文件助手回归两组通过，日志 `test-home-lesson-client.log`。本轮未改后端，最近130项后端回归是备课阶段记录，未重复执行。

F08B64DC…包实际签到使教师开发能量100→110；重复接口调用增加0、当天唯一流水1条。学生260、教师永久徽章0，4条备课及旧行摘要保持。D1101DF4…最终包检查360dp/约411dp首页及课程、360dp课程入口/返回与离线/恢复。全部版本范围、21张原生/3张浏览器及只读数据库核对见 `.local/android/home-page-evidence.json`。最终360dp返回卡片边界相差2个物理像素，不能描述为完全一致。模拟器恢复1080×2400、420dpi、Asia/Shanghai，原代理与API端口映射保留。完整原图、全账号/跨日/进程回收及实体设备仍待验证。

## 最新个人中心恢复包（2026-10-18）

APK `.local/android/artifacts/jinyun-runxiang-debug.apk` 为274,631,763字节，SHA256 `BB4FF6A572BEAF55B613016986B92486B69F814015E2366EF3A8E381FA0A23A6`；构建日志 `.local/android/build-profile-recovery-android.log`。类型检查、Vite、Capacitor与Gradle成功，设备中APK散列一致。构建/安装/API映射方式沿用前文，无新依赖、服务端配置或结构迁移。首页D1101DF4…另存 `artifacts/home-d1101df4-debug.apk`，对应清单已指向该存档。

在仓库根目录执行 `node scripts/test_profile_session.mjs`、`node scripts/test_profile_scroll.mjs`。两组通过，日志分别为 `test-profile-session.log`、`test-profile-scroll.log`；旧代码的账号保存用例先失败，保留在 `test-profile-before-fix.log`。当前源码已通过格式检查。后端未改变，最近130项回归仍是备课阶段记录，本轮没有重复执行或清空开发库。

当前包验证教师约411dp与学生360dp反馈返回、学生真实收藏返回、个人资料保存、普通师生登录/退出与离线重试。教师简介测试值经API/MySQL核对后恢复原五项字段（含NULL），账号更新/登录时间仍反映真实操作。模拟器恢复1080×2400、420dpi、Asia/Shanghai、原代理与8000映射，原生和浏览器均已恢复教师登录，独立教师后台也已重新登录。22张分版本原生、4张浏览器和完整范围见 `.local/android/profile-recovery-evidence.json`。没有实体设备、全账号竞态、跨日或进程回收的全量验收结论。

## 班级对抗赛、目录管理与最终安装包（2026-10-18）

本节为当前最新包，后续历史版本记录保留在文末以免混淆。

- V20 迁移 `database/migrations/V20__class_contests.sql`：幂等增加 `assignment.contest_id` 与索引，创建 `contest`、`contest_entry`。隔离开发启动脚本 `scripts/start_android_dev.py` 会在 V19 后执行 V20；`database/schema_all.sql` 已同步。
- 对抗赛复用现有作业提交/批改链路；教师端 `POST/GET/PUT /api/teacher/contests...` 与学生端 `GET /api/mobile/me/contests...` 已挂载。运营目录管理接口位于 `/api/admin/catalog/...`，仅管理员可访问。
- `GET /contests/:id` 深链自动打开详情；手机教师端与教师后台详情均支持截止/公布前编辑参赛名单，已有提交后移出名单、截止或公布后修改返回 409。

最终 Debug APK：`.local/android/artifacts/jinyun-runxiang-debug.apk`，274,763,236 字节，SHA256 `bfe844ee2b67bfe24e8885d816930bd106576b6edc2af0cdd35bf9e57c4563b8`。构建日志 `.local/android/build-final17.log` 包含 Vite Android 构建、Capacitor 同步与 Gradle `BUILD SUCCESSFUL`（日志中另有一次 `JAVA_HOME` 未设置导致的失败，改用下述 JDK 21 后成功）；前端类型检查单独执行 `vue-tsc --noEmit`，日志 `.local/android/typecheck-final17.log`（退出码 0）。Windows 本机构建需设置 `JAVA_HOME=D:\Android\Jdk21\jdk-21.0.12.1+1`；Android Studio 自带 JBR 为 Java 25，不满足 Gradle 的 Java 21 工具链要求。已安装 emulator-5554，设备内 `base.apk` 散列与产物一致；开发 API 映射仍为 `adb -s emulator-5554 reverse tcp:8000 tcp:8000`，API 使用 `http://127.0.0.1:8000/api`。

Android WebView 的本地源是 `https://localhost`，因此后端 CORS 白名单必须包含 `https://localhost`（本轮已加入 `backend/app/main.py`，同时保留 `http://localhost` 与 `capacitor://localhost`）。本机 HTTP API 调试构建还需允许混合内容：`user-web/capacitor.config.ts` 仅在 `VITE_API_BASE_URL` 以 `http://` 开头时写入 `android.allowMixedContent: true`；使用 HTTPS API 构建时该开关关闭。若修改 CORS 或 Capacitor 配置，需要重启后端并重新执行构建/安装。

设计基准渲染：`python scripts/render_design_baselines.py` 会启动本地静态服务并用无头 Edge 将 `docs/mastergo/*.html` 渲染到 `.local/design-baselines/`（373/375px 画板）；需本机安装 Edge，可用 `--only home` 或 `--force` 控制。地图底图改为 `user-web/public/design/maps/tianjin-districts.svg`，由天津行政区 GeoJSON 生成，页面标注 `DataV.GeoAtlas` 数据来源。

验收证据：后端全量 133 项通过（`.local/android/test-final17-full.log`，含名单增删、重复名单 409、公布后名单锁定与非遗收藏状态回读）；前端 `vue-tsc --noEmit` 退出码 0；学生深链详情 `.local/android/screenshots/final-student-contest-clean.png`；名单编辑 `.local/android/screenshots/final-roster-editor-final.png`（保存返回“参赛名单已更新”）；课程播放页与答题态 `.local/design-baselines/app-course-player-final9.png`、`app-course-quiz-result-final8b.png`；百科顶部检索 `.local/design-baselines/app-heritage-top-final12.png`（“泥人张”命中《穆桂英挂帅》）；非遗详情长文与设计长图 `.local/design-baselines/app-heritage-detail-final16.png`、`app-heritage-themes-final14.png`、`app-heritage-origin-final14.png`；收藏后刷新仍为 ★ 的实机画面 `.local/design-baselines/app-heritage-collected-final17.png`；全路由冒烟学生 28 条/教师 9 条均无破图与未捕获异常（`.local/android/route-audit-student.json`、`route-audit-teacher.json`；教师访问学生专属 `/contests/:id` 的 403 属权限预期）；教师后台 `npm run typecheck` 与 `npm run build` 通过。WSL 教师工作区已 rsync 本轮源码并重启 5173，HTTP 200。用于名单编辑验收的临时 OPEN 轮次（0 提交）已从隔离开发库清理。

此包仍是 Debug 开发产物，使用开发 API 与调试签名；不含正式商店签名、生产服务地址、实体设备/旧 Android/进程回收验证，也不包含作品授权协议、合作社生产、支付或外部生成服务。
