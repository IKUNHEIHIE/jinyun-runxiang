# 津韵润乡：当前交付状态与剩余工作

更新：2026-10-18。整体任务仍在进行中。当前已有可安装、可联调的 Android Debug 开发版，但尚未完成全量设计、功能与设备验收。没有实体真机测试证据，也没有可支持“97%还原”或“全部完成”的量化依据。

## 当前可测试产物

- APK：D:/admin/desktop/codex/school/smxc/jinyun-runxiang/.local/android/artifacts/jinyun-runxiang-debug.apk
- 包名：com.jinyun.runxiang
- 大小：278,116,613 字节
- SHA-256：2beec6f21ffbfcd70ff41457dbf49abf146b17c9b42027f94294e408e3cdc55d
- 已安装到 emulator-5554，连接云端 API `https://admin.wentian.org/api` 验证。
- 构建记录：.local/deploy/build-apk-final31.log，包含 vue-tsc、Vite、Capacitor 与 Gradle 构建。final31 在 final30 基础上把 API 地址切到云端 admin 域名，并保留首页入口、页面动效与高清封面。final31 取代 final30/final29/final28/final27/final26/final25/final24/final23/final21。
- GitHub Release：`v1.0.0-beta.4`，标签提交 `3f4516d`，https://github.com/IKUNHEIHIE/jinyun-runxiang/releases/tag/v1.0.0-beta.4
- 运行方式与配置见 [Android 部署说明](ANDROID_DEPLOYMENT.md)。该包使用开发 API；正式发布还需服务地址、签名及设备兼容性验证。

## 八项交付要求的当前证据

| 要求 | 当前状态 | 证据与未完成部分 |
|---|---|---|
| Android App | 已具备阶段开发版 | APK 构建、安装和局部真实运行通过；API 30（Android 11）已补测，完整生命周期、API 24-28 与实体设备验证未完成 |
| 手机前端 | 部分完成 | 已逐页推进原始属性和资源还原；全量有效画板、所有状态与多尺寸视觉验收尚未通过 |
| 后端 | 已扩展并持续完善 | 135 项独立数据库回归通过；真实 MySQL 迁移和局部端到端记录另存，不等于所有业务完成 |
| 独立教师后台 | 已部署并联调 | WSL 后台类型检查和构建通过；班级、作业、备课等已接入，仍有管理界面和业务需要完善 |
| 功能清单 | 持续维护 | [功能与验收矩阵](MOBILE_FEATURE_MATRIX.md)区分已接入、部分实现与外部服务缺口 |
| 测试结果 | 已有阶段证据 | 当前接口回归、客户端专项、浏览器和 Android 证据按范围与版本分别记录 |
| 视觉对照 | 部分完成 | [视觉记录](VISUAL_REVIEW.md)区分结构属性、辅助渲染与运行截图；原始画布 PNG 与全量对照仍缺失 |
| 部署文档 | 已具备开发环境说明 | [部署说明](ANDROID_DEPLOYMENT.md)和[实施记录](ANDROID_IMPLEMENTATION.md)持续更新；尚未按生产发布验收 |

## 2026-10-18 智能备课专项

设计层 5:02348 的全部 10 个分区已读取，实际 DSL 237 节点，概览元数据为 254 节点。14 个原始 SVG 已通过云端替换取得。设计档案位于 docs/mastergo/reviews/lesson-plan-20261018/，辅助 HTML 位于 .local/android/references/lesson-plan-structure.html；后者不是 MasterGo 原始截图。

手机端重建了课程配置、教学目标、重难点、可展开讲稿、真实历史记录与横向模板入口。完整教学过程、互动问题和作业保留在展开内容中。历史只显示实际保存记录，不使用设计中的示例记录或假课件链接。

保存接口增加教师范围内的请求标识，网络重试可返回同一条记录；同一标识用于不同配置时拒绝。新增能力查询与游标历史接口。LOCAL 模式不会调用外部模型；AUTO 的结构化结果与失败回退经过模拟测试，未执行付费模型调用。

导出从当前保存方案生成可编辑 PPTX，保留完整长讲稿，并修复中文标点落在行首的问题。历史缺失内容明确显示未提供，不以新模板替换历史 NULL。实际 11 页课件通过完整渲染检查，文本框与源内容校验通过；未声称在 PowerPoint 中打开测试。

V19 新增 nullable request_id、request_mode 及教师/请求唯一约束。新库、V9 升级、重复执行与保留数据的代码回滚在独立 MySQL 审计库验证。开发库旧备课记录的内容摘要在迁移前后相同。

## 本轮实际联调记录

- 浏览器创建记录 2：高中、景泰蓝工艺、60 分钟、本地课程模板。
- Android 创建记录 3：大学、古琴鉴赏、45 分钟；独立教师后台可读取同一记录并成功下载 PPTX。
- 教师后台创建记录 4：高中、陶瓷文化、30 分钟；Android 刷新历史后读取同一方案。
- Android 实测系统分享课件及取消、设置/历史弹窗返回关闭、历史断网提示与恢复重试、模板横向滚动和选取。没有向分享目标发送文件。
- 约 411dp 和 360dp 的截图按 APK 版本记录。B2466C9D…包记录上述主要流程；314D630A…包修正了两处设计节点追踪标记并重新构建、安装和补检。各版本范围以 .local/android/lesson-plan-evidence.json 为准。
- 测试只使用开发数据。教师/学生能量 100/260、教师永久徽章 0；旧记录 1 保留。未将这些记录当作正式学生学情。
- 接口日志：.local/android/test-lesson-plan-backend-full.log，130 项通过。客户端真实组件与文件导出助手的延迟/账号/重试专项：scripts/test_lesson_plan_session.mjs。
- 教师后台构建、类型检查：.local/android/build-lesson-plan-admin-final.log、.local/android/typecheck-lesson-plan-admin.log。

## 2026-10-18 首页专项

重新读取5:01925全部29分区、243节点，原样提取26个SVG。修正标题纵距、推荐文字位置、课程标题/角饰/元信息及原始评分图标；没有评分的课程显示淡色星形与“暂无评分”。原始画布PNG、背景透明度/裁剪和373/375px尺寸差异仍未完成像素验收。

分类与年级保存在路由，旧请求不能覆盖新筛选。课程、百科和账户请求各自显示失败；旧账号签到响应不写入新账号，较早的账户查询不覆盖已接受签到。断网冷启动显示姓名/等级/余额/签到未知，恢复后可重试读取。最终包360dp课程详情返回的卡片边界相差2个物理像素；没有回到页首。

F08B64DC…包实际完成教师开发账号当天签到100→110；重复接口请求不增加奖励，数据库只保存一条当天签到流水。学生仍260能量，教师永久徽章0，旧备课记录未改且仍4条。FBEC39A1…保留分类/详情/返回/年级空状态证据，E3997901…保留离线与恢复记录；最终D1101DF4…补正未知等级后复查两种屏宽、课程返回及离线恢复。完整版本范围见 .local/android/home-page-evidence.json。

新增 scripts/test_home_session.mjs 专项通过，备课客户端回归两组通过，最终APK类型检查/构建与安装通过。本轮没有修改后端或迁移；最近一次后端回归仍为备课阶段130项，未为首页重复执行。整项目仍在进行中，个人中心长列表返回和全量账号/生命周期等未完成。

## 2026-10-18 个人中心返回与账号隔离

修复前D1101DF4…包从反馈页返回时，原入口由可见的[49,1774][1029,1932]变为[0,0][0,0]；旧账号保存结果还会触发新账号资料刷新，实际脚本回归先失败。现改为等待个人中心数据进入DOM后恢复滚动；后续导航、换号及超时取消旧恢复。刷新保留已读取内容，切换身份时立即清理旧记录、徽章弹窗和表单。

资料保存增加重复提交、账号/页面/编辑窗口校验。保存已被服务端接受而资料刷新失败时，明确提示已保存且暂未刷新；旧响应不关闭新编辑窗口，旧退出响应不清除新账号数据。两组实际组件/滚动助手专项通过。

当前BB4FF6A5…包在浏览器和教师约411dp、学生360dp从反馈返回时位置一致；学生从真实漆绣收藏返回相差2物理像素。Android实际保存个人简介，API/MySQL确认后恢复五项原值（含NULL）。教师→退出→学生→退出→教师的普通登录流程、学生离线重试通过；延迟响应由实际脚本专项隔离测试覆盖，未扩大为全量原生账号竞态通过。

学生仍为4件作品、3件收藏、2枚/7项目录、2学习日、260能量；教师0作品/0收藏、110能量、永久徽章0。旧备课内容保留。22张分版本原生、4张浏览器、数据与恢复证据见 .local/android/profile-recovery-evidence.json。模拟器原尺寸/密度/代理/API映射及教师登录已恢复，独立教师后台也已重新登录；本轮未改后端、数据库结构或后台源码，130项后端回归仍沿用备课阶段。全项目继续进行中。

## 2026-10-18 班级对抗赛与目录管理补全

新增 V20 迁移：`contest`、`contest_entry` 两张表，`assignment.contest_id` 回链。对抗赛复用现有作业提交与批改链路：每轮生成两个班级侧作业，学生提交仍走 `/mobile/assignments/{id}/submit`，教师评分仍走 `/teacher/submissions/{id}/review`。

已实现并实测：

- 教师创建两班对抗赛，选择两个班级的在册学生名单、轮次、创作工具、总分/平均分排名方式与截止时间；`OPEN → SCORING → PUBLISHED` 状态机，公布后提交、评分和名单全部锁定。
- 教师列表/详情、Student 端列表/详情接口；学生只看本人作品和班级汇总，看不到其他学生姓名与作品；成绩公布前作业列表也不返回分数与评语。
- 未提交、已提交未评分分别显示；班级总分/平均分、班级名次、学生班内名次与胜者按公布时的成绩快照保存。
- 教师后台新增“班级对抗赛”页签；Android 教师页新增对抗赛入口与详情页；Android 学生作业页新增“进入对抗赛”和成绩页。
- 运营后台新增“目录管理”：徽章目录（含条件 JSON、持有人数、删除保护）、市集商品（价格/库存/公益比例/上下架）、能量兑换商品（能量/库存/启停）的新增与编辑。

实测证据：

- 后端全量回归 **132 项通过**（`.local/android/test-catalog-full.log`），其中新增对抗赛全流程、公布前成绩隐藏、公布后锁定、权限隔离，以及目录管理 CRUD/删除保护测试。
- 真实开发库端到端：创建“纹样对抗赛·实测”，一班 88 分、二班 92 分，二班胜；学生端公布前无分数，公布后显示 88 分/班内第 1 名；公布后再改分或重新提交均返回 409。证据 `.local/android/contest-e2e-evidence.json`、`.local/android/contest-e2e.log`。
- Android 实测截图：`.local/android/screenshots/teacher-contests.png`、`teacher-contest-detail.png`、`student-contest.png`、`student-contest-detail.png`。
- 目录管理接口在真实开发库读取成功：7 枚徽章、10 件在售商品、3 件兑换商品；学生/无效凭据无权访问。证据 `.local/android/catalog-live.log`。
- 管理后台类型检查与生产构建通过；Android 最终包重新构建。

开发测试数据说明：为完成双班联调，在隔离开发库新增学生 `contest_e2e`（id 4，二班），仅用于本轮对抗赛验证；不影响正式学生数据。

## 2026-10-18 对抗赛深链、名单编辑与视觉基准补全（最终包）

- 修复 `/contests/:id` 深链：从作业卡“进入对抗赛”跳转后会直接打开对应详情弹层，不再停留在列表页。学生端实测显示状态、两班汇总、胜者、本人作品、得分/班内名次与教师评语。
- 手机教师端与教师后台均新增“编辑参赛名单”：打开时回填当前名单，保存调用 `PUT /teacher/contests/{id}/entries`；已有学生提交后移出名单、截止或公布后修改均由后端 409 拒绝。手机端复选框布局已按全局表单样式修正。
- 设计基准不再受“无法导出 PNG”阻塞：`docs/mastergo/*.html` 已可在本地离线渲染。新增 `scripts/render_design_baselines.py`，用无头 Edge 将 18 个有效画板输出到 `.local/design-baselines/`，并在同一 373px 宽度下用实际 APK WebView 截长图对照。
- 对照后修复的实质视觉问题：非遗百科首页原使用近白装饰图，画作主视觉缺失，现改为设计中的天津非遗画作背景；课程页顶部横幅改为设计稿的全宽无缝版式；首页百科入口改为直角 56px 横幅并收紧分类胶囊；行走地图原设计底图实为美国地图（Newington/Laurel Hill），现替换为本地生成的天津行政区 SVG（DataV.GeoAtlas 数据），打卡点按真实经纬度投影；后母戊鼎封面原指向 341×1 分隔线导致全黑，现改用设计中的 934×1200 器物图，并按设计稿重做深色沉浸式详情；教师实时数据页补上设计中的粉色蒙层，不再直接显示地毯纹理。
- 该轮终验包（final7，后续已被 final20 取代）：274,131,701 字节，SHA256 `2DC227A74EBFFEA6D0390E7B403BC9C29BD9F88ADDD357EFCB1790C12C0D1CA9`，构建日志 `.local/android/build-final7.log`（类型检查、Vite、Capacitor、Gradle `BUILD SUCCESSFUL`）。
- 已在 emulator-5554 安装最终包，设备内 `base.apk` SHA256 与产物一致。截图证据：`.local/android/screenshots/final-student-contest-clean.png`、`final-roster-editor-final.png`，以及 `.local/design-baselines/app-home-top.png`、`app-courses-top.png`、`app-heritage-top.png`、`app-map-view.png`、`app-bronze-editor.png`。
- 后端全量回归 **132 项通过**（`.local/android/test-final2.log`，含名单增删、重复名单 409 与公布后名单锁定）；教师后台 `npm run typecheck` 与 `npm run build` 通过，WSL 工作区已同步并重启 5173。

## 2026-10-18 课程播放页、教师中心、备课页与百科顶部检索最后一轮设计对照（final14）

- `5:01018` 课程播放页按设计重建：顶部课程进度/真实评分胶囊、视频卡（高清/时长/播放/进度条）、讲师信息卡（头像、传承人头衔、章节数）、章节列表、单题翻页的随堂鉴赏（选项正确/错误标记、解析、分数与下一件瑰宝/继续研习）、收藏与评价、固定底栏（能量、收藏、继续研习、前往AI工坊）。课程详情接口新增真实平均评分字段；实测答题提交后显示“鉴赏通过 · 10分”并出现解析与后续按钮；提交 5 星评价后刷新，顶部胶囊显示对应星级（截图 `.local/design-baselines/app-course-player-final12-rated.png`）。
- 教师个人中心修正底栏遮挡：最后一张“快捷操作”卡片及其文字完整露出，不再被 74px 底部导航压住。
- 智能备课页恢复设计中配置卡右上角的红色印记装饰（原先透明度 0.05 近似不可见），并对齐位置。
- 非遗百科页补上设计中的顶部悬浮搜索（返回按钮 + 搜索胶囊），与页内“资源检索”共用关键词；后端检索新增年代字段与类别别名映射，热门词“泥人张”“风筝魏”等可正确命中，实测“泥人张”返回《穆桂英挂帅》，“风筝魏”返回《沙燕风筝》。
- `40:32809` 非遗详情长文页补齐设计中的结构化内容：经典题材三张图文卡、半印半画四步工序、源起时间轴、艺术特色三卡与评论引语、传承图文卡。`HeritageDetailPage` 新增通用 `items`/`timeline`/`features`/`quote` 渲染；杨柳青年画内容写入开发库（种子脚本同步），设计图片加入 Android 资源白名单后实机加载成功（`.local/design-baselines/app-heritage-themes-final14.png`、`app-heritage-origin-final14.png`）。
- Android WebView 使用 `https://localhost` 作为源；本轮补齐后端 CORS 白名单（`https://localhost`、`http://localhost`、`capacitor://localhost`）与仅在本机 HTTP API 构建中启用的 `android.allowMixedContent`，否则调试包所有 API 请求都会被 CORS/混合内容拦截。该开关由 `VITE_API_BASE_URL` 是否为 `http://` 决定，正式 HTTPS 构建不会开启。
- final14 构建：274,718,202 字节，SHA256 `6195d0f74dcde0299d77bb4bbf8f7d6048a593d5e82edbe4c2060bf9b4fca9aa`，构建日志 `.local/android/build-final14.log`；已安装 emulator-5554，设备内 `base.apk` 散列一致（已被 final16 取代）。
- final14 后端全量回归 **132 项通过**（`.local/android/test-final14-full.log`）。新增对照截图：`.local/design-baselines/app-course-player-final9.png`、`app-course-quiz-result-final8b.png`、`app-teacher-final9.png`、`app-lesson-plan-final9.png`、`app-community-detail-final8b.png`、`app-heritage-top-final12.png`、`app-heritage-themes-final14.png`、`app-heritage-origin-final14.png`。

## 2026-10-18 非遗详情主视觉与收藏入口最终对照（final16）

- 非遗详情页主视觉改为优先读取 `content.hero_url`，杨柳青年画使用设计长图 `/design/images/1d096953210d426fc2ef3300764b80a3.webp`，不再用首页封面裁切图充当详情头图；页头右侧补上收藏星标，长图保留缩放/复位。种子脚本与隔离开发库 entry 4 均已写入该字段。
- final16 构建：274,718,402 字节，SHA256 `c76dc83ef379ddc3800af9cc5b35256c016a55a3ef619e323cb26cd7c07580ad`，构建日志 `.local/android/build-final16.log`；已安装 emulator-5554，设备内 `base.apk` 散列与产物一致（已被 final17 取代）。
- 前端 `vue-tsc --noEmit` 通过（`.local/android/typecheck-final16.log`，退出码 0）；后端全量回归 **132 项通过**（`.local/android/test-final16-full.log`）。新增对照截图 `.local/design-baselines/app-heritage-detail-final16.png`。
- final16 包内 CDP 全路由冒烟：学生 28 条路由、教师 9 条路由逐一渲染，均为 0 张破图、0 个未捕获异常、0 个本地请求失败；`/classroom` 与 `/classroom/1` 另在学生/教师两端验证通过。教师账号直接打开学生专属 `/contests/:id` 时，后端按权限返回 403（预期行为），同一路由在学生账号下正常。原始结果 `.local/android/route-audit-student.json`、`.local/android/route-audit-teacher.json`。

## 2026-10-18 非遗收藏状态回读修正（final17）

- 非遗详情接口在登录态返回当前用户的 `collected`；详情页加载时回填星标与底部收藏按钮状态，切换条目或重新加载不再把已收藏显示为未收藏。实机验证：点击收藏后星标为 ★，刷新后仍为 ★；再次点击取消后为 ☆，刷新后仍为 ☆。
- final17 构建：274,763,236 字节，SHA256 `bfe844ee2b67bfe24e8885d816930bd106576b6edc2af0cdd35bf9e57c4563b8`，构建日志 `.local/android/build-final17.log`；已安装 emulator-5554，设备内 `base.apk` 散列与产物一致（已被 final18 取代）。
- 前端 `vue-tsc --noEmit` 通过（`.local/android/typecheck-final17.log`，退出码 0）；后端全量回归 **133 项通过**（`.local/android/test-final17-full.log`，新增收藏状态回读测试）。final17 全路由冒烟（学生 28 条、教师 9 条）仍为 0 张破图、0 个未捕获异常、0 个本地请求失败；教师访问学生专属 `/contests/:id` 的 403 为权限预期。新增实测截图 `.local/design-baselines/app-heritage-collected-final17.png`。

## 2026-10-18 非遗首页资源统计条（final18）

- 按 `40:32437` 设计补上 hero 内“非遗项目 / 教学资源”统计条（30px 数字、金色加号、细分隔线、14px 标签）。数字来自已发布内容的真实计数：已发布非遗条目与已发布课程；开发库当前为 5 / 6，不使用设计示例的 128 / 56，也没有写死。
- `GET /api/mobile/heritage` 新增 `stats` 字段；后端测试在隔离库中断言已发布条目 2 / 已发布课程 1，草稿与下线内容不计入。
- final18 构建：274,763,249 字节，SHA256 `5280ae68767cf1b9d7df0730ce0b18cc92f5dd643bc6775cd105d6b1aaa23e93`，构建日志 `.local/android/build-final18.log`；已安装 emulator-5554，设备内 `base.apk` 散列与产物一致（已被 final19 取代）。
- 前端 `vue-tsc --noEmit` 退出码 0（`.local/android/typecheck-final18.log`）；后端全量回归 **133 项通过**（`.local/android/test-final18-full.log`）。final18 全路由冒烟（学生 28 条、教师 9 条）无破图、无未捕获异常、无本地请求失败；教师访问学生专属 `/contests/:id` 的 403 为权限预期。新增实测截图 `.local/design-baselines/app-heritage-stats-final18.png`。

## 2026-10-18 工坊历史作品原位更新（final19）

- 新增 `PUT /api/mobile/workshop/designs/{task_id}`：仅本人、`BRONZE`、且结果为 `user_canvas` 的设计可更新；替换构图/标题/封面/渲染风格后仍使用原 `task_id`，不新建任务。他人任务、AI 生成任务均按 404 处理。
- `BronzeCanvas` 首次保存仍走 POST，之后（包括从历史画布设计恢复后）保存走 PUT；实测打开 `task_id=d00e...` 恢复 2 个纹样，点击“完成设计”提示“设计已更新”，随后 `/ai/tasks/latest` 仍返回同一 `task_id`，未产生重复记录；测试后原始构图与封面已恢复，临时上传资产已删除。证据 `.local/android/canvas-update-e2e.txt`。
- final19 交付重建（post-sync，已被 final20 取代）：274,718,826 字节，SHA256 `5a111864c42a3b2b1c590c00cf5b1296336693fa1d7ff880d1e25bb0373d7e0e`，构建日志 `.local/android/build-post-sync.log`。
- 前端 `vue-tsc --noEmit` 退出码 0（`.local/android/typecheck-final19.log`）；后端全量回归 **133 项通过**（`.local/android/test-final19-full.log`，画布更新测试覆盖同任务更新、任务数不增、跨用户与 AI 任务拒绝）。
- 多尺寸冒烟：学生 28 条、教师 9 条路由分别在 360dp 与 411dp 下渲染，文档横向溢出 0、破图 0、请求失败 0（教师访问学生专属 `/contests/:id` 的 403 仍为权限预期）；非遗首页统计条在两种宽度均完整显示（`.local/design-baselines/app-heritage-stats-final19-360.png`、`-411.png`；原始结果 `.local/android/route-audit-student-360.json`、`-411.json`、`route-audit-teacher-360.json`、`-411.json`）。

## 2026-10-18 账号切换、保存目标与检索竞态修正（final20）

- 独立评审发现并修复三处问题：`BronzeCanvas` 在账号切换或任务状态变为非成功时未清空 `editableTaskId`，可能把新账号的保存指向旧账号任务；现在会话变化与非成功任务都会清空，并在开始上传前快照保存目标，避免上传期间目标变化导致 PUT→POST 或写错任务。`HeritagePage` 检索加入版本号，较早返回的响应不会覆盖较新的搜索结果。
- 终验包：274,763,671 字节，SHA256 `8f84c8c27bc417df3de9cffedc596de2d80e6ccb4a0656c3530bf47772cc9662`，构建日志 `.local/android/build-final20.log`；已安装 emulator-5554，设备内 `base.apk` 散列与产物一致。
- 前端 `vue-tsc --noEmit` 退出码 0（`.local/android/typecheck-final20.log`）；后端全量回归 **133 项通过**（`.local/android/test-final20-full.log`）。final20 重新实测历史画布保存仍提示“设计已更新”，latest 保持同一 `task_id`；原始数据已恢复，临时资产已删除（`.local/android/canvas-update-e2e.txt`）。
- final20 全路由冒烟（学生 28 条、教师 9 条，373dp）无破图、无未捕获异常、无本地请求失败；教师打开学生专属 `/contests/:id` 的 403 为权限预期（`.local/android/route-audit-student.json`、`route-audit-teacher.json`）。
- final20 生命周期补测：撤除 8000 端口映射后首页显示真实离线态（“暂时无法连接服务”、能量“— / 2,000”、“签到状态未知”）并可重试；恢复映射后回到 270 能量，无伪造零值。教师账号进入 `/teacher/analytics` 显示真实班级数据；切回学生后同一路由被守卫重定向到 `/profile`，首页恢复林锦/270 能量。进程回收补测：`am force-stop` 后联网冷启动保留登录并恢复 270 能量/林锦；离线冷启动显示真实错误与未知值，恢复网络后重试回到 270，资料头由 30 秒账户重试自动补齐（final21 起改为重试时并行加载）。证据 `.local/android/lifecycle-final20.txt`、离线截图 `.local/design-baselines/app-home-offline-final20.png`、`.local/design-baselines/app-home-offline-coldstart-final20.png`。

## 2026-10-18 首页账户重试恢复修正（final21）

- 离线冷启动时首页的“重试账户状态”原先只重试 `/mobile/me/summary`，能量/签到恢复后姓名与等级仍显示“账户资料暂未加载 / 等级未知”，需等待 `MobileApp` 的 30 秒账户重试。现改为在有令牌但无资料时并行调用 `/auth/me` 与 summary，按钮显示“重试中…”，重复点击只发起一次资料请求。
- 模拟器实测：断网冷启动显示未知值；恢复 8000 映射后点一次重试，3.2 秒内恢复“林锦 / LV.1 / 270 能量 / 今日已签到”，无需等待 30 秒。证据 `.local/android/account-retry-final21.txt`。
- final21 包 274,718,958 字节，SHA256 `6361ac69ca9ac76d42f9f0b36e1c8caf426edee71b84789a6672bbd1918ec61e`，构建日志 `.local/android/build-final21.log`；类型检查退出码 0（`.local/android/typecheck-final21.log`）；`node scripts/test_home_session.mjs` 通过，新增重试/重复点击断言。
- 同一轮后端补齐本地教案的学段差异：`grade_guidance` 按小学/初中/高中/大学调整实践说明、追加提问与作业证据要求（小学用两三句话，高中标注资料依据，大学区分事实/推断/价值判断）；未知学段保持原中性模板。真实接口实测小学三年级与高中返回不同 skill/homework/问题；Android 教师端选择高中/杨柳青年画生成后，展开讲稿可看到新增追问与“补充两条可查证资料”的作业，截图 `.local/design-baselines/app-lesson-plan-grade-final21.png`。全量后端回归 **135 项通过**（`.local/android/test-final21-backend.log`），WSL 开发 API 已重启并返回 200；UI 测试记录已删除并恢复学生会话。教师后台 HTML 导出改为复用同一学段模板，包含实际目标/重难点/过程/互动问题/作业/讲稿，并移除了未接入的“3D 可动模型/激光纸样/AI 三维评分”等表述；30 分钟导出实测显示 5/10/8/7 分钟环节，截图 `.local/design-baselines/app-lesson-export-high-final21.png`。此改为服务端内容，不改变 final21 APK 散列。
- 学生 28 条、教师 10 条（9 个唯一路由）在 360/373/411dp 冒烟：横向溢出 0、破图 0、异常 0、失败请求 0、控制台错误 0；教师访问学生专属 `/contests/:id` 的两个 403 为权限预期（`.local/android/route-audit-student-final21.json`、`route-audit-teacher-final21.json` 及 `-360.json`、`-411.json` 四组）。
- 新增 `scripts/prune_orphan_assets.py` 处理历史画布保存留下的未引用上传：默认 dry-run、24 小时阈值，删除前检查 URL/资产 ID/JSON 引用并限制文件目录；合成资产自测只删除未引用项。开发库 dry-run 曾把资产 2/3 列为未引用；完整库检查确认社区作品 1 的 `gallery_json` 引用它们，已保留并给脚本补上 `gallery_json` 检查。

## 2026-10-18 后台示范班级真实数据修正（final22）

- 运营后台“乡村美育示范班级”页签原先把两条示例班级写死在 `UsersView.vue`（王秀兰/张建军、42/38 人、84.5%/78.0%），页头还静态宣称“首批国家级非遗美育重点试点示范班，直连乡村智慧终端与具身设备”，表格写死“秋季进阶阶段”。这些都不是数据库事实，已全部移除。
- `GET /api/teacher/classes` 保留原有 `id/name/grade/invite_code/student_count`，新增 `teacher_name`（带班教师昵称）、`school`（教师资料中的学校；未登记返回空字符串，不回退内部 ID）、`completion`（在班学生的均值学完率：已完成章节 / 该生已开始课程的已发布章节；无学习记录返回 `null`）。学生人数改为一次聚合查询，避免逐班 N+1。
- 后台改为 `onMounted` 并行加载用户与班级；摘要按真实数据生成“共 N 个在班班级 · M 名在班学生”；学校为空显示“未登记”，学完率为 `null` 显示“暂无学习记录”而不是伪造 0%。
- 测试：在既有教师学情用例中增加教师/学校/学完率与 ADMIN 全量可见断言；`test_mobile_client.py` 89 项通过，全量后端回归 **135 项通过**（复核后最新：`.local/android/test-all-review-final22.log`），测试数未增加。
- 后台 `npx pnpm@11.25.0 typecheck` 退出码 0（`.local/android/typecheck-admin-classes-final22.exit`），生产构建 `✓ built in 13.34s`、退出码 0（`.local/android/build-admin-final22.log`）；已 rsync 到 WSL 教师工作区，Vite 5173 返回包含 `classStudentTotal` 的最新组件。
- 真实接口与页面实测：2 个班级（传统工艺研习社、学情联调空班（开发验证）），带班教师均为张新，学生数各 1，学完率分别 100% / 暂无学习记录，学校未登记；页面已无上述静态宣称。截图工具因 0×0 视口不可用，改用 DOM 结构读取核对，未伪造截图。证据 `.local/android/admin-classes-final22.txt`。
- 同轮清理其他“把写死/未接入数据当真实”的页面，并逐页用运行中的 DOM 核对：
  - 运营大屏删除“48 所实时联网 / 3 台机器人 / 16ms / 420·360·290·310·240 人 / 91.8% / 94.1 / 94.2% / 10% 收益”等静态数字；学校、设备、AI 生成、公益金、区县学生数改取 `/screen/overview` 真实聚合，无设备时显示空态，雷达显示“暂无诊断聚合数据”。
  - 社区风控删除虚构的 OCR 结论、色情/暴力概率与 98% 关联度，改为展示真实初筛方式（关键词规则）、是否命中敏感词及“图像/OCR 未接入需人工核验”。
  - 设备台删除“MQTT 总线正常/皮影走位执行中”，明确网关未接入，空遥测显示“—”，远程按钮禁用；模型页删除“GPU 集群在线就绪”；系统设置删除“5% 且 100% 实体化”承诺。
  - `user-web/src/views` 的遗留桌面页面（当前入口未挂载，不在 APK/构建中）也同步清理：首页假统计/假个人资料、AI 工坊 3D/激光/名师认证/虚构学生与展签、个人中心假徽章与演示模式、研学固定坐标。它们不代表当前 Android 入口，只为避免后续误用。
  - 后台 `typecheck` 与生产构建退出码 0（10.80s）；user-web `vue-tsc` 与 Vite 构建退出码 0（2.37s）。证据 `.local/android/honesty-fixes-final22.txt`、`typecheck-admin-honesty-final22.log`、`build-admin-honesty-final22.log`、`typecheck-user-honesty-final22.log`、`build-user-honesty-final22.log`。
- 独立复核后又补：无 `ContentReview` 记录的帖子不再冒充“关键词未命中”；大屏订单尾号/空流水；设置页延迟只在接口返回时显示；`school` 不回退内部 ID；班级学生数改为“人次”；遗留页订单状态按真实状态显示。复核后 `test_mobile_client.py` 89 项、后台与 user-web 的类型检查和构建再次通过（`*-review-final22.*`），API 重启后 `/screen/overview` 与 `/teacher/classes` 实测正常（`.local/android/live-review-final22.txt`）。
- final22 当轮不重建/不更换 APK；final21 随后被 final24 取代。`user-web/src/views` 遗留页面的文案修正不进入当前 Android 入口。

## 2026-10-18 移动端真实性清理与 final24 APK

- 移动端逐页审计发现，商城、地图、AI 工坊和课堂页仍把设计示例当成能力承诺。MallPage 删除“每一次购买点亮希望”“学生共创/学生原创”“收益注入基金”“创作变现·助学闭环”，统计改为社区创作者/已过审作品，基金改为“公益基金·入账公示”，商品标注“公益计提 X%·以确认入账为准”，共创流程明确“授权与生产暂未开放”。
- MapPage 删除“草莓樱桃正当季/避暑农家乐/当季新鲜直达/带走大山馈赠/每一次购买支持非遗”等时令、配送与购买承诺，改为主题推荐与“查看农产商品”；“参与学生”改为“在册学生”。WorkshopPage 删除“AI绘画生成/AI重现/AI重塑/AI赋能”，改为纹样参考与辅助设计；漆绣简介删除“国家级非遗”与“AI技术赋能”；课堂页与路由标题由“双师课堂”改为“在线课堂”。
- 首页能量进度按真实等级阈值显示（LV1/500、LV2/1000、LV3 满级），不再固定 2,000；课程播放页教师信息改为“平台课程/课程简介待补充”；课程横幅、百科“沉浸式”、文物“国宝级”、工坊统计重复项同步修正。
- 独立复核确认基金/作品/学生/计提比例均与后端字段一致；随后统一三处命名：市集路由标题改为“文创共创市集”、地图路由标题改为“行走的美育地图”、漆绣卡片恢复与内部页一致的设计品牌“漆绣智绘”，地图个人统计“积分”改为“能量”。
- final24 APK：274,718,830 字节，SHA256 `5078f5500705e67f7967490fd256b0982fa49100b41d21b7889d427696e3d3ea`；构建日志 `.local/android/build-apk-final24.log`，`vue-tsc --noEmit` 退出码 0，`scripts/test_home_session.mjs` 通过。安装到 emulator-5554 后拉取设备内 `base.apk`，散列与产物一致；`lastUpdateTime=2026-10-18 06:38:34`。`adb force-stop` 后冷启动仍保持林锦登录与 270 能量。另做离线冷启动：撤除 8000 映射后显示“暂时无法连接服务/签到状态未知/当前能量值 —”，没有伪造零值；恢复映射后单次重试在 5 秒内回填林锦、270、今日已签到（截图 `.local/android/final24-home-offline.png`）。按 HOME 后 `am kill` 使进程消失，重新启动仍恢复首页/林锦/270/今日已签到；另执行模拟器 `adb reboot`，启动后 WebView 短暂为 about:blank，约 5 秒后恢复首页/林锦/270/签到。上述为进程回收与整机重启模拟，不等同于真实内存压力或跨日。后端代码本轮未改，全量回归复跑仍为 **135 项通过**（`.local/android/test-all-final24.log`，26.50s）。
- 安装包内 13 条核心路由用 WebView CDP 实测：破图 0、横向溢出 0、未捕获异常/控制台 error 0，覆盖首页、课程/详情、百科/详情、AI 工坊/青铜画布、社区/详情、商城、研学地图、在线课堂、我的。另在 373dp 跑完整师生路由：学生 28 条无溢出/破图/异常/失败请求；教师 10 条同样通过，`/contests/1` 的 2 个 403 为教师访问学生专属接口的预期权限行为；学生 28 条在 360dp 复跑同样全部通过，学生 28 条与教师 10 条在 411dp 复跑也全部通过。商城结算冒烟只打开弹层、未提交订单，确认显示“创建待支付订单/尚未接入在线付款渠道”。证据 `.local/android/final24-route-audit.json`、`final24-apk-verify.txt`、`route-audit-student-final24.json`、`route-audit-teacher-final24.json`、`route-audit-student-final24-360.json`、`route-audit-student-final24-411.json`、`route-audit-teacher-final24-411.json`；运行截图 `.local/android/final24-*.png`（由 WebView `Page.captureScreenshot` 获取，不是 MasterGo 原图）。
- final21 的账户重试与教师端学段差异仍包含在 final24 中；final24 随后被 final25 取代。final24 当轮复查 WSL 开发 API `/health` 与教师工作区 `http://127.0.0.1:5173/` 均返回 200。原图通道、实体真机、旧 Android、自然进程回收、正式支付/外部模型/远程视频课堂、授权生产与全量视觉状态验收仍未完成。

## 2026-10-18 地图主题推荐死入口修复（final25）

- `/landmarks` 的“主题推荐”两张卡原先调用 `chooseCategory('采摘'/'农家乐')`，而开发库地标分类只有年画/泥人张/非遗研学，点击后必然进入“当前分类暂无开放基地”的空列表。现改为 `openAgriMarket()` 跳转 `/mall?category=agri`，卡片文案改为“田园风物/农家风味”，不再声称存在采摘园或农家乐点位。
- 实测：两张卡渲染正常；点击第一张后 hash 为 `#/mall?category=agri`，页面标题“文创共创市集”，显示农产特产筛选与真实农产商品。
- final25 APK 274,718,758 字节，SHA256 `b1b92b66ea544a6dcdc4bd56387326843dc7fb2e16676b7b02f66a378e405574`，构建日志 `.local/android/build-apk-final25.log`，类型检查与首页专项通过；安装 emulator-5554 后设备内 base.apk 散列与产物一致。13 条核心路由与学生 28 条路由（373dp）实测无破图/横向溢出/JS 异常/失败请求（`.local/android/final25-route-audit.json`、`route-audit-student-final25.json`、`.local/android/final25-*.png`）。
- final25 只改地图卡片动作与文案；final24 已完成的 360/411dp、教师 10 条、离线冷启动/重试、`am kill`、`adb reboot` 证据仍适用，相关日志保留。final25 随后被 final26 取代。

## 2026-10-18 行走页断网徽章假零修复（final26）

- 离线检查发现 `/profile/walking` 的徽章标题在断网时显示“0 / 0”，徽章区显示“暂无开放徽章”，把未知状态伪装成零。现改为加载中或无缓存且出错时标题显示“—”，徽章区展示真实错误与“重新加载”；已有缓存徽章时不被后续全局错误清空。
- final26 安装包实测：撤除 8000 映射进入行走页，标题为“— ›”、页面显示“暂时无法连接服务”，无“0 / 0”与“暂无开放徽章”；恢复映射后单击重新加载，标题恢复“2 / 7 ›”并显示真实徽章。
- final26 APK 274,718,814 字节，SHA256 `53d8f10ab931db5d0833ce6a3c3c2b01299d77611dbb8d60787a068513186091`；构建日志 `.local/android/build-apk-final26.log`，类型检查与首页专项通过；设备内 base.apk 散列一致。13 条核心路由、学生 28 条（373dp，含行走页）无破图/横向溢出/JS 异常/失败请求（`.local/android/final26-route-audit.json`、`route-audit-student-final26.json`、`.local/android/final26-*.png`）。final25 的地图入口修复保留在包内；final26 取代 final25 成为当前开发包。

## 2026-10-18 个人中心头图/收藏横滑与教师数据断网空态（final28）

- 个人中心按设计 `5:00420` 接入红色缠枝纹头图（设计资源节点 `5:00495`），替代原纯色 `#C5AAA1`；收藏区由双列网格改为设计中的横滑卡片，卡片宽 158px、间距 15px，第三张按设计在右缘露出，空态占满滚动区。头像、统计、修习、徽章和收藏数量仍取真实账号数据。
- 教师实时数据页断网时，班级选择显示“班级加载失败，请重试”；学习进度、正确率、能量、徽章和考勤空态统一为“暂不可用”，不再在请求失败时声称班级无学生或无学习记录。联网实测两个真实班级可选，统计为 1 名学生、100% 平均完成度、2 枚徽章，无错误提示。
- final28 APK 274,799,157 字节，SHA256 `f9651f31df11b9ad26fe0b495fc7b42da7306552671d419bbb31a14860e6a5d6`，构建日志 `.local/android/build-apk-final28.log`，类型检查 `.local/android/typecheck-user-final28.log` 退出码 0；设备内 `base.apk` 散列一致（`.local/android/final28-device-base.apk`），lastUpdateTime=2026-10-18 07:18:46。
- 学生 28 条路由在 373dp 与 360dp 实测均无破图、横向溢出、未捕获异常或失败请求（`.local/android/route-audit-student-final28.json`、`route-audit-student-final28-360.json`）；360dp 下个人中心文档宽 360、视口 360、17 张图片无破图。个人中心头图资源 500×867 加载成功；收藏区 3 张卡片 scrollWidth 524、clientWidth 391，确认可横滑，截图 `.local/android/final28-profile-top.png`、`final28-profile-collections.png`、`final28-profile-360.png`。教师断网态截图 `.local/android/final28-teacher-analytics-offline.png`。final26 的行走页断网修复与 final25 的地图入口修复保留。
- 旧系统补测：新建 Android 11（API 30，1080×2280，WebView 83.0.4103.120）的 AVD `jinyun_api30`，安装同一 final28 APK 成功。首页 55 张图片无破图、视口/文档宽 393 无横向溢出；学生 28 条与教师 10 条路由在 373dp 均无破图/溢出/未捕获异常/控制台 error/失败请求（教师 `/contests/1` 的 2 个 403 属权限预期）。证据 `.local/android/final28-android11-verify.txt`、`route-audit-student-api30.json`、`route-audit-teacher-api30.json`、截图 `.local/android/final28-api30-home.png`、`final28-api30-profile.png`、`final28-api30-native.png`。API 24-28 与实体设备仍未测。
- 未改后端，135 项后端回归仍为最新通过记录。原始 MasterGo 位图通道、实体真机/API 24-28/自然内存压力/跨日、外部支付/模型/音视频/远程课堂及授权生产仍未完成，全量视觉状态验收仍未通过。

## 2026-10-18 Android 9/WebView 66 兼容修复（final29）

- 实测 final28 在 Android 9（API 28，AOSP WebView 66.0.3359.158）上页面为空：`bodyText=0`、无 `h1`、无图片，原因为构建产物使用 ES2020 语法，旧 WebView 解析失败。
- 将 `user-web/vite.config.ts` 的 `build.target` 设为 `es2017` 后重建。final29 在 API 28 上首页正常渲染（55 张图片、破图 0、393 视口无横向溢出）；非遗详情与个人中心单独打开也正常，个人中心头图 500×867 加载、收藏横滑可用。
- 边界：在无窗口 API 28 模拟器上快速连跑 28 条路由时，旧 WebView 渲染进程崩溃（`FATAL:aw_browser_terminator.cc`），应用进程随之中止；改用 3GB 内存重试仍复现渲染进程 code 4，说明是 WebView 66 的稳定边界而非模拟器内存不足。单页可运行不等于全量路由兼容，API 28 全量兼容性仍未建立。
- final29 APK 274,804,557 字节，SHA256 `abcdcc5ef475f0504b2198a4309cdb90360b578816381633b1325a58e3584d7c`，构建日志 `.local/android/build-apk-final29.log`；设备内 base.apk 散列一致，lastUpdateTime=2026-10-18 07:48:04。Android 36（emulator-5554）学生 28 条路由 0 破图/溢出/异常/失败（`route-audit-student-final29.json`），首页截图 `.local/android/final29-home.png`。API 28 证据 `.local/android/final29-apk-verify.txt`、`.local/android/final29-api28-profile.png`。final29 已在 API 30 复跑：学生 28 条、教师 10 条路由 0 破图/溢出/未捕获异常/失败请求（教师 `/contests/1` 的 2 个 403 为权限预期），证据 `.local/android/route-audit-student-final29-api30.json`、`route-audit-teacher-final29-api30.json`、`.local/android/final29-api30-home.png`、`final29-api30-native.png`。
- 未改后端，135 项后端回归仍为最新通过记录。原始 MasterGo 位图通道、实体真机/API 24-27/自然内存压力/跨日、外部支付/模型/音视频/远程课堂及授权生产仍未完成。

## 2026-10-18 GitHub Release beta.2 与上传清理

- 已发布 prerelease `v1.0.0-beta.2`（tag 提交 `002a5f3`）：https://github.com/IKUNHEIHIE/jinyun-runxiang/releases/tag/v1.0.0-beta.2。资产包括 final29 APK（274,804,557 字节，SHA256 `abcdcc5e…`）、教师后台 dist zip（1,249,388 字节）、后端源码包（73,443,717 字节）和 `SHA256SUMS-beta.2.txt`；`gh release view` 确认 4 个资产均为 `uploaded`。
- 清理上传：删除 3 个 79 字节、数据库中完全无引用的 SVG；备份与记录在 `.local/release/deleted-uploads-20261018/`。此前被列为“未引用”的资产 2/3 实际被 `community_post_detail` 作品 1 的 `gallery_json` 引用，已保留；`scripts/prune_orphan_assets.py` 已补上该 JSON 检查，避免后续误删。
- 按用户决定，API 24-27、实体真机、自然内存压力/跨日等其余兼容性测试暂缓，列为已知限制；不因此宣称这些环境已通过。

## 2026-10-18 云服务器部署（Azure / Debian 12）

- 后端：https://core.wentian.org ，FastAPI systemd + MariaDB（仅 127.0.0.1）+ Redis（仅 127.0.0.1），Nginx 反代到 `127.0.0.1:8000`。
- 教师/运营后台：https://admin.wentian.org ，根路径静态 SPA；`/api/` 与 `/static/design|uploads|generated|images` 反代后端。
- TLS：Let’s Encrypt 覆盖两个域名，certbot.timer 自动续期；HTTP 已跳转 HTTPS。
- App：`user-web/.env.android` 的 `VITE_API_BASE_URL=https://admin.wentian.org/api`；构建脚本自动读取，换域名只改这一行。final31 已安装并实测首页 5 条非遗推荐、封面来自 admin 域名的 800px 资源，无本地 API 请求。
- 账号：admin/student_demo/teacher_demo 已用随机密码创建，凭据仅保存在 `.local/deploy/credentials.txt`；云端登录均返回 200。教师后台用无头浏览器登录进入运营大盘。
- 数据库：schema + seed + V17 + 本地 `heritage_entry` 5 条内容已导入；当前为隔离演示数据，正式运营前需替换。
- 详细步骤与配置副本见 [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)、[deploy/nginx/jinyun.conf](../deploy/nginx/jinyun.conf)、[deploy/systemd/jinyun-backend.service](../deploy/systemd/jinyun-backend.service)。

## 2026-10-18 开发测试数据上云与演示内容

- 本地 WSL 开发库全量同步到云端 MariaDB；排序规则从 MySQL 8 `utf8mb4_0900_*` 转为 MariaDB `utf8mb4_unicode_ci` 后导入成功。
- 云端五板块内容：首页 5 条非遗推荐、6 门课程；AI 工坊 9 个任务；社区 8 条作品/11 条评论；我的 7 件收藏、今日修习、徽章与订单。
- 小课堂章节视频改为外链（MDN CC0 花视频、Sintel CC BY 3.0 预告片），未新增本地演示视频文件。
- 云端学生 28 条路由审计：破图/溢出/异常/失败均为 0；`/community/5` 详情 9 张图片无缺失；课程播放器读取外链视频，`readyState=1`。
- 证据：`.local/deploy/cloud-data-sync.txt`、`cloud-route-audit-student2.json`、`cloud-community2.png`、`cloud-profile2.png`、`cloud-app-home.png`、`cloud-community-detail5.png`。当前为测试数据，正式运营前需替换演示账号/统计并配置备份。

## 2026-10-18 首页入口、动效与高清封面（final30）

- 首页在分类标签下新增两个入口卡：“行走的美育地图”（`/landmarks`）与“非遗文创共创市集”（`/mall`），使用 1280×720 地图图与 1779×1920 文创图，带渐变遮罩和按压反馈。
- 页面切换加入 `page-fade`/`page-push`/`page-pop` 过渡（160–200ms，transform+opacity），并支持 `prefers-reduced-motion`；全局启用平滑滚动、横向滚动的惯性滚动与 `overscroll-behavior` 限制，横向卡片增加 `scroll-snap` 与按压缩放。
- 替换 8 张低清封面：泥人、风筝、年画、皮影、剪纸、青花瓷、戏曲服饰 7 张来自 Wikimedia Commons，刺绣课使用仓库已有高清图；均输出 800px 宽并保留 `?v=hd1` 缓存失效参数。许可与署名见 [IMAGE_CREDITS.md](IMAGE_CREDITS.md)。
- final30 APK 278,116,613 字节，SHA256 `721763b6683424b10bb7ce437ad234a3fd2856cb7f06fb7f352fc98c275e5ab0`，构建日志 `.local/release/build-apk-final30.log`；安装后首页入口与封面实测：两张入口图 naturalWidth 1280/1779，推荐封面 800px，过渡类 `page-fade-*` 实测触发。学生 28 条路由 373dp 无破图/溢出/异常/失败（`.local/android/route-audit-student-final30.json`），截图 `.local/android/final30-home.png`、`final30-home-recommend.png`、`final30-map.png`、`final30-mall.png`。

## 尚未完成的核心工作

1. 全部有效设计页、所有状态及多尺寸的逐页验收。当前已能从 `docs/mastergo/*.html` 渲染设计导出基准并完成首页、课程、非遗、地图、市集、AI 工坊、个人中心的重点对照；剩余页面/状态与原始画布位图仍需继续核对。final26 再次核查原图通道：MasterGo Web 画布未登录时文件接口返回 401/403；Magic MCP 0.2.8 工具列表没有位图导出；文档 API 仅返回元数据/封面路径；Vibe MCP 的 `get_selection_image` 需要桌面客户端和当前选中图层。因此原始 PNG 仍不能在本地生成，需登录桌面端/提供分享链接后再导出。备课原稿的 4px 横向装饰线也未作为已验收项。
2. 作品许可、设计者/生产者归属、真实授权协议与生产对接；现有说明或标签不代表协议已落地。
3. 正式教学视频、音频生成、LoRA、支付及远程视频课堂等服务。真实图像生成与参考图重绘已在 2026-10-19 完成本地接入，后台与接口已部署线上并完成真实生图与编辑验证，详见 `AI_WORKSHOP_INTEGRATION.md`。三维部分为馆藏 GLB 模型库演示，不生成真实几何。
4. 部分页面的设计细节；顶部悬浮搜索已补齐，课程播放页教师卡片、随堂鉴赏外框与底部工具条已按设计重建，但原始画布位图与多尺寸/多状态逐页对照仍未完成。地图底图已替换为天津行政区示意图，不再使用设计稿中的美国地图。
5. 实体设备、API 24-28 旧系统、系统内存压力下的自然进程回收及跨日回归；本轮已在 API 30 AVD 补测师生全路由，并补显式 force-stop 冷启动、离线冷启动/重试与师生双向切号，但这些环境仍未验证。Debug 包体积与生产发布配置仍需评估。

设计稿教师学情页出现的“书法/策展/传承”是示例分类，现有课程数据没有对应分类；本轮没有伪造这三类徽章。徽章目录已可在运营后台维护，实际授予规则仍以真实课程与场所数据为准。

当前证据只支持上述范围。原报告中的全量完成、实体真机验证、未经测量的还原百分比及不匹配的接口/组件清单已更正。整体目标保持进行中。

## 2026-10-19 AI 工坊真实图像生成（已部署线上）

统一使用后台“AI 大模型与多模态接入”中的 `image_generation` 配置。新增真实生图/本地模板选择、SenseNova JSON 图片编辑和标准 OpenAI 文件上传适配、图片校验转存、任务幂等、超时/失败/取消处理与密钥掩码；保留原文本配置及历史作品，无结构迁移。

已使用 `sensenova-u1.5-lite` 实际完成青铜文生图及参考图红金刺绣重绘，两项成功任务、两次奖励，无重复提交奖励。API 37 模拟器中恢复真实作品、收藏和系统导出通过；两张导出 PNG 均与服务端原件逐字节一致。第一阶段青铜证据对应 342861AD…包，最终漆绣证据对应 A0328D40…包，未扩大为实体手机或全设备验收。

156 项后端回归、工坊客户端专项、后台构建/类型检查及 Android 构建通过。安装运行的本地包：`.local/android/artifacts/jinyun-ai-workshop-local-debug.apk`（55,997,133 字节，SHA256 `A0328D40BDB5DF9CFA01853EC241335683F90E9FC3379DA2F750CC45AA4819D3`）。连接正式服务的包：`jinyun-ai-workshop-cloud-debug.apk`（SHA256 `89463C3A57B4C5903B15587AC56BF145A4E3806EDD236B54D83677A3374BB775`），已在 API 37 模拟器中登录线上独立账号、恢复青铜 AI 图片及收藏状态，未在实体手机实测。

线上 `admin.wentian.org` 后台和 `core.wentian.org` 后端已更新。独立线上账号完成文生图、参考图编辑、重复提交复用、收藏及历史读取，两个任务对应两次奖励。密钥只配置在服务端，不在前端源码或 APK 中；未创建 Release 或版本标签。服务器备份和线上证据见 `docs/AI_WORKSHOP_DEPLOYMENT_20261019.md`。具体配置、测试、限制与回退见 `docs/AI_WORKSHOP_INTEGRATION.md`，证据见 `.local/android/ai-workshop-delivery-evidence.json`。

## 2026-10-19 导航、创作与设置体验打磨

完善登录后的目标页继续打开、取消与旧响应隔离、弹窗焦点/滚动管理、过渡方向和列表返回位置；社区筛选保留在路由中，发布/通知/课堂操作增加进度、忙态与账号/班级切换保护。百科“开始探索”改为页内滚动；漆绣新增直达创作入口及可用纹样预设。后台设置增加同步/未保存状态、加载失败重试、默认值覆盖保护、过时探测结果失效和窄屏布局。

18 个客户端专项、手机端类型检查与 Android 构建、后台类型检查与生产构建通过。浏览器 28 条主要路由在实际 360/411px 下共 56 次检查无文档溢出、意外裁切控件、已完成加载图片破损或可见错误提示。三个工坊实际完成 LOCAL 生成与 SVG 导出，导出内容与服务端一致，皮影/漆绣收藏通过；本轮没有付费生图调用。最终线上包在 Android 模拟器验证创作入口、纹样弹窗和返回关闭，安装包散列一致。未扩大为实体手机、旧系统或全量设计验收。

现有线上后台静态资源已更新，95 个文件散列验证通过，后端未重启，数据库与模型配置保留；备份 `/var/backups/jinyun/polish-20261019T000014Z`。最终连接正式服务的包：`.local/android/artifacts/jinyun-polish-cloud-debug.apk`，56,001,223 字节，SHA256 `A7F4FDED2A1476FFF8D6255F367158A9453D9D1C669D56D952BA843BA00C20A2`。本轮不创建 Release 或标签。完整范围与证据见 [体验打磨记录](POLISH_20261019.md)。


## 2026-10-19 AI 工坊 3D 数字沙盘（演示增强）

AI 工坊首页新增黑漆描金风格 3D 入口，`/ai-workshop/3d` 页面接入 Three.js 实时 GLB 渲染、自动旋转/线框/视角重置、五阶段复原管线动画、结果指标面板与 7 件馆藏模型库。页面与入口统一使用宣纸底、墨蓝标题、朱砂印章与描金线条，展台为黑漆描金视觉，避免与 App 古典风格割裂。

- 模型全部为 CC0 成品，存放于 `backend/static/models/heritage3d/`；来源与许可见 [IMAGE_CREDITS.md](IMAGE_CREDITS.md)。
- 新增 `GET /api/ai/3d/catalog` 与 `POST /api/ai/3d/generate`；后者按描述关键词在模型库内随机匹配（灯→宫灯、青花→瓷瓶、圈椅→圈椅等），并避开该用户上一次结果，写入 `MESH_3D` 成功任务。
- Nginx 新增 `/static/models/` 反代并已重载；线上接口实测：宫灯→六方宫灯、青花梅瓶→青花瓷韵、圈椅→津作圈椅、琉璃蟠龙→琉璃蟠龙。连续生成会返回不同模型。
- API 37 模拟器实测：黑漆描金入口卡、蟠龙预览、六方宫灯/木构灯彩生成、管线段与结果面板均正常；截图 `.local/deploy/3d-entry-classical.png`、`3d-page-classical.png`、`3d-pipeline-classical.png`、`3d-result-classical.png`。
- 最新安装包：`jinyun-runxiang-final32-slim.apk`（仓库根目录与桌面各一份），56,210,147 字节，SHA256 `2e74ab89543f08d61b4c6a7de430f2686bb7fe6235ccfb92e939d6a3af2ed888`。桌面启动脚本仍使用原文件名，无需改动。


## 2026-10-19 三大非遗工坊视觉提升

- AI 工坊首页三张工坊卡统一升级：朱砂序号“壹/贰/叁”、大号水印编号、朱砂印章“纹/影/漆”、描金内框、馆藏高清标签与更清晰的标签/按钮层级，保留各工坊原有主色。
- 皮影角色设计页重做头图：取消原先多图层绝对定位造成的文字重叠和白块，改为左侧宣纸文案、右侧皮影人物照片、朱砂“影”印，内容区恢复为纸面卡片并留出统一间距。
- 青铜纹样工坊页头部改为墨蓝标题 + 描金卡框 + 朱砂“纹”印，返回键统一为纸面方钮；纹样库与设计画布加描金边框。
- 漆绣智绘页保持原有大图叙事版式，未破坏已验收布局。
- 模拟器截图：`.local/deploy/workshop-cards-after.png`、`shadow-page-after.png`、`bronze-page-final.png`。


## 2026-10-19 皮影三维营造与剪影画像

- AI 工坊首页新增“一张驴皮，三千刀 / 皮影营造 · 三维工序”入口，进入 `/ai-workshop/shadow-3d`。
- 页面第一部分为六道工序三维展台：选皮、描样、镂刻、敷彩、缀结、亮影。使用馆藏皮影实物图做分层三维材质，头、身、双袖独立图层，配合皮料纹理、线稿、纸雕剪影、彩色透光四种着色状态，并加入铜铆钉、三根竹签、灯光与轻微旋转；支持单步点选与自动播放。
- 页面第二部分为“按意生成剪影画像”：用户选择生/旦/净/丑、凤冠/云髻/花冠/翎羽/方巾、团扇/折扇/长剑/纸伞/花枝，并输入描述，后端按关键词与显式选择生成 600×800 剪影 SVG，带标题、诗句、朱砂印章和参数标签，支持保存。
- 新增接口 `POST /api/ai/silhouette/generate`，生成文件写入 `/static/generated/` 并登记 Asset；后端新增 `app/core/silhouette.py`。
- 云端已部署并通过接口实测，返回 `凤冠团扇 · 旦角剪影`；模拟器截图：`.local/deploy/shadow3d-step1.png`、`shadow3d-step2.png`、`shadow3d-step3-final.png`、`shadow3d-final-step6.png`、`shadow3d-generator-result2.png`、`workshop-shadow3d-entry.png`。

## 2026-10-19 AI 工坊功能卡视觉统一

- AI 工坊首页五张入口卡（三维数字沙盘、皮影三维营造、青铜纹样工坊、皮影角色设计、漆绣智绘）合并为同一套 `feature-card` 组件：固定 206px 高、左侧文案 + 右侧 118px 媒体栏的两列网格、统一纸面/描金边框，序号“壹—伍”、朱砂印章、馆藏高清标签、三枚标签与底部对齐的进入按钮位置全部一致。
- 移除此前的黑漆大卡、独立皮影入口卡与高窄工坊卡三种异构版式；标题字号改为 `clamp(17px, 4.9vw, 19px)`，最长标题“一张驴皮，三千刀”在模拟器上无截断。
- 前两张卡不再使用线框立方体与简化剪影：三维沙盘改用应用内 Three.js 实拍的琉璃蟠龙展台（新增 `public/design/images/3d-stage-card.webp`，标签“实时演算”），皮影三维营造改用馆藏皮影实物图（标签“馆藏皮影”），与下方三张馆藏照片卡的质感一致。
- 模拟器截图：`.local/deploy/workshop-cards-media-top.png`、`workshop-cards-media-bottom.png`（旧版对照为 `workshop-cards-unified-top.png`、`workshop-cards-unified-bottom.png`）；五张卡片同高、同结构、同留白节奏，5 张媒体图均加载成功（naturalWidth>0）。
- 新安装包：`jinyun-runxiang-final32-slim.apk`（仓库根目录与 `D:\admin\desktop` 各一份），55,320,782 字节，SHA256 `906c813a9e4c976b68fb28e984d9855aac7bb2e2f52d11001c9b4df8cca8ae7f`；设备内 `base.apk` 散列与产物一致，`lastUpdateTime=2026-10-19 11:12:49`（模拟器时钟为 UTC）。该包取代上一节的 56,210,147 字节包。


## 2026-10-20 AI 工坊成品化（接线 / 作品闭环 / 上线加固）

按三轮完成代码改造，细节见 [AI_WORKSHOP_INTEGRATION.md](AI_WORKSHOP_INTEGRATION.md#2026-10-20-工坊成品化三轮改造)。

- 第一轮接线：剪影与三维结果可真正保存/分享并收藏回流；删除置信度、体素分辨率、伪造阶段耗时等虚假指标，管线阶段标注“演示”，帧率改为查看器实测；三个工坊与两个新页面统一加入“请导师点评”；三维查看器支持键盘轨道与无障碍标签。
- 第二轮作品闭环：新增 `GET /api/ai/tasks`、`DELETE /api/ai/tasks/{id}` 与 `/ai-workshop/works` 作品页（筛选、分页、收藏、两步删除，删除会连带清理 Asset、收藏与生成文件）；剪影生成改为真正的 `SILHOUETTE` 任务并纳入额度/幂等/奖励；全部生成入口加 `request_id` 幂等与响应令牌隔离、失败重发起、离线拦截与状态徽标；皮影角色设计补“参考图 · 选填”上传（后端把草图校验收紧为“本人 Asset + 文件存在 + 剥离签名”，本地模板明确不识别图片）；修掉青铜工坊写死的空“窃曲纹”分类（改为按纹样分组生成 tab，补齐 8 个真实分组）与 AI 结果覆盖手绘画布无提示的问题。
- 第三轮上线加固：`/static/generated/*` 改为 12 小时 HMAC 能力 URL（中间件统一签名、无签名读取 403，历史数据不重写）；新增每日/每分钟额度（`SysConfig(ai_quota)` 可覆写，默认每人每日 60、每分钟 30）与 `GET /api/ai/quota`；复用后台敏感词做内容检查 + 提示注入清洗与定界，点评文本以不可信数据送模；`prune_orphan_assets.py` 覆盖 `generated/` 且把收藏视为有效引用；新增管理员 `GET /api/ai/stats` 真实漏斗并在后台“AI模型与LoRA”页顶部展示。
- 独立复审修正（每条已补回归）：删除作品不再误删 `static/models/heritage3d/*.glb` 共享馆藏模型（原本一个学生删作品会让所有人的三维结果与模型库一起失效）；能力 URL 守卫改为按与 `StaticFiles` 一致的归一化路径判定，`/static//generated/x`、`/static/uploads/../generated/x` 不再绕过 403；修复 `sign_json` 正则回溯导致的“已签名链接被截断重签”；内容检查补齐换行分隔（`忽略\n指令`）、NFKC 同形字、软连字符；导师点评的标题/手记/门类三个字段先清洗再送模并 `as_untrusted_data` 定界、门类加长度上限；社区发布改用同一套 `find_blocked_text`（原本裸子串匹配，插一个零宽字符即自动过审）；`require_signature` 不再放过无查询串的裸生成链接；作品页补账号切换清空 + 删除/收藏令牌隔离 + 确认状态复位；`saveAsset` 用去掉签名的真实路径判定文件容器（此前本地 SVG 会被存成 `.png` 文件名）；`deploy/nginx/jinyun.conf` 对 `/static/generated/` 关闭缓存（`no-store`），`.gitignore` 补 `backend/data/*.key`，密钥以 `O_CREAT|O_EXCL` + 0600 创建。
- 已知未做（非本轮范围）：`/ai/evaluate` 只受每分钟节流、不计每日额度也不写 `AiTask`；分钟节流按进程计算；`OperationStatDaily` 用 UTC 日而额度用上海日，且作品删除后不再计入漏斗；上传的参考图不会被删除流程回收。
- 验收：后端全量 `166 passed`（含 10 项治理回归）；`user-web` 与 `admin-web` 类型检查 0 错误；`vite preview` 产物在 360×780 CDP 巡检 7 条工坊路由，五张卡等高 206px、媒体图全部加载、作品页与皮影“参考图 · 选填”控件正常、青铜分类为八个真实分组、无横向溢出、无未捕获异常（证据 `.local/android/workshop-ui-audit-20261020.json`）。
- 安装包 `.local/android/artifacts/jinyun-runxiang-debug.apk`（55,332,663 字节，SHA256 `680757273d207292c8935b0e1ef01432aee40b1e935093e2d8b8dbe71138b764`，2026-10-20 21:25 构建）指向 `https://admin.wentian.org/api`。线上后端仍是 2026-10-19 版本，缺少本轮新增接口，因此该包**不做设备演示、也不替换仓库根目录/桌面的 final32-slim 包**；待授权部署新后端后再重出包并在模拟器与实体机验收。
- 待办（需授权）：部署后端到 `core.wentian.org`（含 `backend/data/file_url_secret.key` 的共享与备份、多 worker 同主机、`/static/generated/` 关缓存、按需配置 `ai_quota`），随后重跑签名作品/收藏/额度端到端与 APK 实测。本轮未改动云端任何服务、配置或数据，也没有向已连接的实体手机 `HGR3TH52` 安装应用。

## 2026-10-20 深夜：生产后端上的模拟器实机演示（设备端结论）

时点说明：以下几节记录同一自然日深夜的一轮，前一节“未改动云端”为其当时状态；本轮已取得后端部署授权并完成部署与设备演示。

- 演示环境：Android 模拟器 `Medium_Phone_API_37.0`（emulator-5554）上已安装的 debug 包 `com.jinyun.runxiang`（pid 3601），WebView CDP 通过 `adb forward tcp:9333 localabstract:webview_devtools_remote_3601` 驱动；后端 API 与静态资源均为生产域名 `https://admin.wentian.org`。演示账号为开发演示用的学生「林锦」（`student_demo`），登录态来自设备 localStorage。驱动脚本 `.local/deploy/workshop-cloud-demo.mjs`，一次性求值脚本 `.local/deploy/cdp-eval.mjs`（配套表达式 `.local/deploy/expr-*.js`）。
- 设备端截图（均在 `.local/deploy/`）：
  - `demo-shadow-ref.png`：皮影角色编辑器新增的「参考图 · 选填」卡片已渲染，本地模板模式下文案为「本地模板按角色与配色生成，不读取图片内容」。
  - `demo-shadow-result.png`：文字描述填入「提灯旦角，海棠花冠，云髻步摇」后生成本地皮影，预览卡显示「丑角 · 皮影创作 / 镂空轮廓图」。
  - `demo-works3.png`：我的作品页 16 件，新建皮影作品封面是真实 SVG（`naturalWidth` 540 加载成功），三维沙盘条目改为金字「三」占位而非破图，整页 `broken images = 0`。
  - `demo-silhouette.png`：剪影画像「凤冠团扇 · 旦角剪影」在生产后端生成，签名 SVG 600×800 正常显示，配额行显示「今日剩余 58 次」，并标注「本地规则模板 · 不调用外部生成模型」。
  - `demo-3d.png`：三维数字沙盘 WebGL 画布 756×672 渲染成功，8,321 三角面 / 5 网格 / 3.6 MB，0.7s 完成馆藏匹配；页面文案为「演示模式 · 后端从馆藏级 CC0 模型库匹配返回」和「模型为 CC0 成品，本功能不生成新的几何体，也不声称按描述重建了器物」。
  - `demo-delete-arm.png`：删除二次确认提示「再点一次「删除」确认删除这件作品」出现在界面上时的截图。
- 闭环验证（均为生产环境实测）：皮影作品 `5fa2be101c106bc7de4c14344ce7ffff` 创建成功 → 收藏按钮 `aria-pressed` false→true 并提示「已收藏到我的收藏」→ 作品列表 15→16 → 两次点击删除（第一次仅武装确认，第二次真正删除）→ 列表回到 15、提示「作品已删除」，`GET /api/mobile/me/collections?kind=ASSET` 由 4 条降为 3 条且被删作品的收藏行一并消失（无孤儿收藏）；10/19 生成的三维沙盘作品仍在，说明共享 CC0 库模型文件未被误删。
- 范围限定：以上证据只覆盖该台 API 37 模拟器、该生产后端与该演示账号下的工坊创作/作品/收藏/删除路径，不构成实体设备、其他账号或权限矩阵的验收结论。

## 2026-10-20 深夜：演示中发现并修复的删除残留缺陷

- 现象：删除皮影作品时，后端只清理了 `_colored.svg`，`_lineart.svg` 与 `_template.svg` 连同它们的 `Asset` 行残留在服务器上。该缺陷由真机演示发现，此前测试未覆盖。
- 根因：`backend/app/core/task_assets.py` 的 `task_result_urls()` 依赖固定字段白名单 `RESULT_URL_FIELDS`，遗漏了皮影结果里的 `line_art_url`、`print_template_url`（以及青铜/时调/漆绣路径里的 `completed_sketch_url`、`sheet_music_url`、`model_url`）。
- 修法：新增 `_generated_urls()` 递归遍历 `result_summary_json`，收集所有以 `/static/generated/` 开头的字符串（含嵌套 dict/list）；`task_result_urls()` 改为「原白名单 ∪ 递归遍历结果」。这样既补齐删除清理，又保留 MESH_3D 的 `/static/models/...` 结果 URL 集合语义（社区发布时 `community.py` 的图集归属校验依赖它，不能缩小）。
- 回归测试：`backend/tests/test_workshop_governance.py` 新增 `test_deleting_a_shadow_work_removes_every_generated_file`，断言删除返回 `removed_assets == 3 and removed_files == 3`、三个文件均从磁盘消失、该用户 `Asset` 行清零。
- 后端全量：WSL 下 `/home/ubuntu/.venvs/jinyun-android/bin/python -m pytest tests/ -q` 结果 **168 passed**（修复前为 167 passed）。

## 2026-10-20 深夜：云端二次部署与生产删除链路复测

- 本轮云端只改一个文件：`backend/app/core/task_assets.py` 以 sha256 前缀 `ad1f4fcbf924ffa6` 上传，远端 `sha256sum` 一致；旧文件先备份到 `/tmp/task_assets.py.bak-<epoch>`，再用 `sudo install -o jinyun -g jinyun -m 640` 落位；`sudo systemctl restart jinyun-backend` 后 `is-active=active`、`http://127.0.0.1:8000/health=200`。首次部署（当日 13:35Z 的 `backend/app` 全量包）记录见 [AI 工坊治理改造线上部署记录](AI_WORKSHOP_DEPLOYMENT_20261020.md)，本次是在其之上只替换该文件。
- 生产端删除链路复测：脚本 `.local/deploy/verify-shadow-purge.py` 用演示学生账号新建一个 LOCAL 皮影作品 `b727e76826e5f18b0387e443d9c51b15`，三个产物 URL 删除前均为 200，DELETE 返回 `removed_assets 3 / removed_files 3`，删除后三个 URL 均 404，脚本输出 `VERDICT PASS`（日志 `.local/deploy/purge-mine*.json`、`.local/deploy/leftovers-pretty.json`）。
- 除上述单文件替换、后端服务重启与演示产生的数据外，本轮未改动云端 Nginx/systemd 配置、数据库结构或其他后端源码。

## 2026-10-20 深夜：生成目录孤儿文件与孤儿 Asset 行（已批量清理）

- 先用只读分类脚本 `.local/deploy/classify-generated-leftovers.py` 统计（结果 `.local/deploy/leftovers-pretty.json`）：`static/generated` 共 149 个文件、36 条 `Asset` 行、26 个仍被任务引用、5 个被收藏引用。本轮先清掉自己演示产生的 2 条孤儿 `Asset` 行与 2 个文件。
- 经用户批准后执行批量清理：先备份 `/var/backups/jinyun/generated-before-orphan-purge-20261020T151859Z.tgz`，再用 `.local/deploy/purge-generated-leftovers.py --apply` 删掉 8 条孤儿 `Asset` 行（id 36–43，属主为 user 1、2）与 121 个无引用文件；目录项 147→26，`Asset` 行 34→26，孤儿行/孤儿文件均归零。删行与删文件在同一轮里分两遍做，因为文件是否算孤儿取决于行是否还在。
- 清理后核对：`health=200`，`GET /api/ai/tasks` 仍 16 件且封面字段正常，`GET /api/mobile/me/collections?kind=ASSET` 3 条无孤儿，模拟器作品页 6 张签名 SVG 全部加载、破图 0。完整表格见 [AI 工坊治理改造线上部署记录](AI_WORKSHOP_DEPLOYMENT_20261020.md)。

## 2026-10-20 深夜：教师后台生成漏斗面板上线

- 经用户批准后把 `admin-web` 生产构建部署到 `admin.wentian.org`（根目录 `/var/www/jinyun-admin`，属主 `www-data:www-data`，目录 755 / 文件 644）。部署前备份 `/var/backups/jinyun/admin-web-before-20261020T152258Z.tgz`（2.5 MB）；产物 tar `c0210c3206119b60…` 本地与远端散列一致，`rsync -a --delete` 替换后 95 个文件，`platform-config.json` 与线上原文件 md5 相同（`cda09d6d…`），确认不是运行时配置回退。
- 上线前本地核对：`pnpm typecheck` 退出码 0、0 错误；`pnpm build` 退出码 0；`VITE_PUBLIC_PATH=/` 生效（`index.html` 内 `src`/`href` 均以 `/` 开头）；漏斗卡片确实进包（`dist/static/js/ModelsView-*.js` 命中「生成漏斗」「/ai/stats?days=14」）。前端读取字段与后端 `workshop_stats()` 返回逐字段一致（`window_days`、`totals`、`tools` 的 `total/success/success_rate/avg_seconds/failed/cancelled/running`、`quota_limits`）。
- 生产页面实测（Edge CDP 隔离上下文登录 admin 后打开 `#/models/index`）：提交任务 39 / 成功产出 39 / 失败 0 / 用户取消 0；分工坊行含青铜 6、刺绣 6、三维 12、皮影 7 等；限流脚注显示每人每日 60 次（剪影 50 / 三维 50）、每分钟 30 次。
- 上线后按实机观感修了三处并二次构建部署：卡片标题里的 emoji 在该控制台渲染成方框，已去掉；`CERAMICS`、`PAPER_CUTTING`、`SHADOW` 这些历史 `tool_type` 码不再裸显，统一显示为「历史任务 · 原码」；「平均耗时」原样输出秒数（青铜 39478 秒），改为秒/分钟/小时/天自适应显示（青铜现为 11.0 小时），并在脚注补明该值是提交到成功的墙钟时间、含排队等待。
- 提示：`index.html` 不带 `Cache-Control`，只带 ETag，控制台更新后需强刷一次才会取到新入口 chunk。

## 2026-10-21 凌晨：跑得更快——封面 WebP 化 + 静态缓存 + 骨架占位

- 封面体积：后端 `/static/design` 下 30 张课程/作品封面原本是 78 MB 的原始 PNG（单张最大 6.5 MB）。用 ffmpeg 统一转 WebP（最长边 800、quality 80）后共 **2.4 MB**，回传到服务器同目录（保留原 PNG 不动），并用 `.local/deploy/switch-covers-to-webp.py`（默认 dry-run，`--apply` 写入）把数据库里 438 条单值引用 + 211 条图集引用改为 `.webp`，仅当对应 WebP 文件存在时才替换。抽样：`b81867c8….png` 478 KB → `.webp` 32 KB。
- HTTP 缓存：两个 `/static/` 位置块新增 `Cache-Control` ——`design` 为 `public, max-age=2592000, immutable`（文件名是内容哈希），`uploads` 为 `public, max-age=604800`；`generated` 仍保持 `no-store`（签名 URL 是短期凭据）。改动前备份 `/var/backups/jinyun/nginx-before-cache-<epoch>.conf`，`nginx -t` 通过后 reload；仓库里的 `deploy/nginx/jinyun.live-copy.conf` 已同步。
- 首屏观感：新增 `components/SkeletonImage.vue` —— 羊皮纸底 + 白色高光扫过的 shimmer 动画，图片加载完成后 0.3s 淡入，失败显示线框图标，默认 `loading="lazy"`、`decoding="async"`、`fetchpriority` 按首屏/非首屏区分；`prefers-reduced-motion` 下动画停用。
- 列表渲染：重复卡片加 `content-visibility: auto` 与 `contain-intrinsic-size`，屏幕外卡片跳过渲染。
- 落地范围：`CourseCard`、首页入口/推荐、社区列表、我的收藏、市集商品与兑换、非遗百科、工坊作品、社区详情头图与相关推荐共 8 个文件、13 处封面换成骨架占位；`content-visibility` 加在课程卡（260/104px）、社区卡（320px）、收藏卡（190px）、商品卡（280px）、非遗卡（300px）、作品行（98px）。
- 验证：`vue-tsc` 0 错误、构建通过；截住 `/static/*` 图片请求后社区页 20 张卡片全部显示 shimmer 占位（`.skeleton-shimmer` × 20，无破图）；放行后恢复；首页/小课堂/社区/市集/百科逐页 `broken images = 0`，设备上封面为 `webp`（`naturalWidth=800`）。debug APK 重构建并安装（55,332,582 B，SHA256 `6C24BA6ED0D5F5E9A94DAA8EF4ED5A925F189DDBED6C62EC659A6B631B8A01C3`）。

## 2026-10-21 凌晨：AI 工坊五个模块的演示表演层

- 新增 `components/GenerationTheater.vue`：生成期间的全屏"生成现场"覆盖层——四步工序逐条点亮、右上计时、扫描光、完成盖章与三项真实统计，约 3 秒后自动收起；`prefers-reduced-motion` 下停用动画，失败路径强制关闭避免遮罩卡死。
- 三维数字沙盘：接入生成剧场；画布默认自动巡游（指针按下暂停、松开 3 秒后恢复），新增线框模式与重置视角按钮；右上 HUD 展示三角面/网格/体积/馆藏匹配耗时（真实值，缺失显示「—」）。
- 青铜纹样：生成剧场 + 结果"拓印显现"（SVG 描边或位图自下而上揭示，只播一次），结果区增加纹样组数/对称轴/主色读数。
- 皮影角色：生成剧场 + "灯下显影"（暗帘 0.6s 提亮 + 暖光斑），读数行列出行当/脸谱/取色。
- 漆绣智绘：生成剧场 + "逐层描金"（多图层 120ms 依次淡入；单图从左到右揭示并扫过一次金色高光），读数行列主色/纹样/取色。
- 剪影三维：剪影生成接入生成剧场，失败立即关闭。
- 验证：`vue-tsc` 0 错误、生产构建通过；浏览器实测剧场在 0.9s 时推进到第 2 步（"匹配行当与头冠"），约 4.5s 后收起并出现结果面板；五个模块页面均正常渲染。debug APK 重构建并安装（56,062,217 B，SHA256 `F4EE3AF30835EE1C902945866A4E92949191A56EE92A3803394D0FEC5466EF94`），设备端剪影生成后剧场自动收起、结果出现。
- 已推送 GitHub：commit `e2decbe`。

## 2026-10-21 凌晨：小课堂/社区改为分页 + 下拉刷新

- 数据扩容后原先"一次追加 50 条"的加载更多仍会让列表越滚越长，改为真正的分页：`components/PagerBar.vue`（上一页 / 第 X / Y 页 / 共 N 条 / 下一页，首末页自动禁用），小课堂与社区统一每页 20 条，切换筛选条件回到第 1 页，翻页后平滑回到页顶；`AsyncState` 重试改为按当前页重载。
- 新增 `components/PullToRefresh.vue`：页面在顶部时下拉，56px 阈值触发刷新，过程中显示"下拉刷新 / 松开刷新 / 正在刷新…"，`prefers-reduced-motion` 下关闭过渡；监听 window 的 touch 事件，仅在顶部且向下拉动时阻止原生滚动。
- 浏览器验证（411×915）：小课堂第 1 页 20 张（1/4 页、共 69 门），翻到第 4 页 9 张、"下一页"禁用；社区第 1 页 20 张（1/11 页、共 217 件）。下拉手势实测：下拉 96px 显示"松开刷新"，松手后显示"正在刷新…"并新增一次 `/community/posts` 请求（1→2），随后指示条复位。
- 说明：列表数据仍是服务端分页（`page`/`pageSize`），前端不再把多页数据堆在同一个 DOM 里。
- 翻页条排版修正：`.pager-state` 用 flex 列布局时，"第 / 数字 / / 11 页"被当成三个独立子项竖向堆叠，实机上显示成竖排文字；改为把整段包进 `.pager-count` 并加 `white-space: nowrap`，中间恢复为「第 1 / 11 页」+「共 217 件」两行居中，实测宽度 250px、高度 31px。
- 设备验证：debug APK 重构建并安装（55,330,813 B，SHA256 `7282B693DAB07043560218AFCA7F5CF314D742D92359EB5DF261DC31F52FB06F`）。模拟器上小课堂第 1 页 20 张、页码 1/4、共 69 门，翻页回顶；社区翻页条为「第 1 / 11 页」「共 217 件」两行居中（实测 183×31）；静止时下拉指示条完全收在屏幕外；合成下拉手势依次显示"松开刷新""正在刷新…"，并新增一次 `/mobile/courses` 请求（2→3）。

## 2026-10-21 凌晨：头像上传 + 批量演示数据

- 头像上传：`ProfileInput` 新增可选 `avatar_url`，`PUT /me/profile` 用 `owned_avatar_path()` 校验——去签名后必须以 `/static/uploads/` 开头、存在属于本人的 `Asset`、且 `mime_type` 为 `image/*`，否则 404「头像资源无效」；上传复用既有 `POST /ai/assets/upload`。资料编辑弹层新增头像行（5MB 上限、仅 PNG/JPEG/WebP、本地预览、上传中禁用、保存后刷新）。新增 `backend/tests/test_avatar_upload.py` 7 例，后端全量 **176 passed**；`vue-tsc` 0 错误。后端 `backend/app/api/mobile.py` 已部署（sha 前缀 `828961c33fbb993a`，备份 `/tmp/mobile.py.bak-<epoch>`，服务 active、health 200）。生产复测：上传 200 → 设置 200 → `/auth/me` 回读一致；`/static/generated/...`、他人资源、路径穿越三种输入均 404。演示账号「林锦」已上传并设置一张 SVG 头像（`/static/uploads/509a0f94...svg`），设备端已验证显示。
- 批量演示数据（经用户批准写入生产）：`.local/deploy/seed-bulk-demo.py`，`--apply` 写入、`--rollback` 按 `sys_config.demo_bulk_seed_20261021` 里记录的 id 精确回滚，脚本默认 dry-run。本次生成 200 门课程（4 章/门，共 800 章，视频沿用 MDN flower 与 Sintel 两条 CC0 示例）、200 条已过审社区作品（复用 30 张 `/static/design` 封面轮换）、299 条评论；落库后总量：课程 206、章节 806、作品 222（已过审 217）、详情 222、评论 326。分类覆盖 8 个非遗门类，学段 PRIMARY_HIGH 137 / PRIMARY_LOW 69。
- 列表分页：小课堂与社区原本各只取前 50 条且没有继续加载入口，数据扩容后新增「加载更多（还有 N 门/件）」，按页追加并按 total 判断收敛；实测小课堂 50 → 69 后按钮消失，社区显示「还有 167 件」。
- 交付包：debug APK 重构建并安装（55,328,680 B，SHA256 `5F32FE97CDB9F63EB58AABA0369CEB30A7E63F37C6D0DF7F370F5A168C05B48D`，`lastUpdateTime=2026-10-20 17:12:35Z`）。设备实测：头像 `naturalWidth=256` 正常显示；小课堂 50 张卡片带「加载更多（还有 19 门）」，点击后 69 张、按钮消失。
- 已知取舍：社区演示作品的 `comment_count` 与评论行一致（每条 1–2 条评论），点赞/浏览为随机演示值；课程按 id 升序，原有 6 门课排在新增课程之前。

## 2026-10-21 凌晨：全站 UI 重构（第一批：设计系统 + 9 个页面）

用户要求把整站前端按「我的」页的新风格重构。第一批交付：

- 设计系统：`components/PageHeader.vue` 重写为吸顶应用栏（`title`/`subtitle`/`back`/`backTo` + 右侧插槽），凡已使用它的页面自动换新；新增 `components/SectionCard.vue`（标题红竖条 + 金色分隔线 + `meta` 槽）、`components/CellGroup.vue`、`components/CellRow.vue`（48px 行高、危险行居中变红、`#value` 槽）。「我的」页同步改为使用这三个组件，视觉不变。
- 已重构页面：首页、通知、在线课堂大厅、小课堂、课堂房间、课程播放页、社区、AI 工坊首页、我的工坊作品。约束是只改模板与样式，不动请求/路由/事件/文案，不引入 Vant/NutUI 依赖。
- 路由 `meta.surface` 统一：`/`、`/courses`、`/community`、`/ai-workshop`、`/ai-workshop/works` 改为 `#f5ede4`，避免状态栏下方出现旧配色的色带。
- 验证：`vue-tsc --noEmit` 0 错误；`vite build --mode android` 成功；8 条路由在 411×915 下横向溢出均为 411/411、破图 0；debug APK 重新构建并安装（`adb install -r` 成功），设备上首页、AI 工坊、社区显示新布局。证据 `.local/deploy/ui-*.png`、`device-home-batch1.png`、`device-workshop-batch1.png`。
- 待办：非遗百科/详情、社区详情、市集、地图、行走档案、个人服务、对抗赛、发布页、工坊编辑器、3D 页、教师端各页仍为旧样式，按第二批推进。

## 2026-10-21 凌晨：「我的」页布局重做（已进 APK，模拟器实测）

用户明确要求按成熟组件库（Vant/NutUI 个人中心）的结构重做本页，本轮据此改动 `user-web/src/mobile/views/ProfilePage.vue`：

- 结构：顶部吸顶应用栏（返回、标题「我的」、右侧「编辑资料 / 登录」）→ 头图条 + 悬浮身份卡（64px 头像、昵称、等级、研学记录说明、作品/关注/粉丝/能量四格统计）→ 三个分区卡（今日修习、所获徽章、我的收藏，统一 `corner-card` 圆角与投影）→ 分成两组的 cell 列表（学习与班级 3 项、服务与设置 3 项 + 红色居中「退出登录」）。
- 移除：原 353px 绝对定位头图、头像装饰点、悬浮年份胶囊、`profile-services` 竖列链接；徽章横滑条隐藏原生滚动条。
- 保留：全部数据绑定与交互（登录/编辑表单、徽章弹层、收藏跳转、教师入口 `v-if`、退出登录），脚本只新增应用栏滚动高度判断与一个等级文案 computed。
- 验证：`vue-tsc --noEmit` 0 错误；以生产 API 构建后，在 Chromium 411×915 移动视口下核对登录态（林锦 / 12 作品 / 0 关注 / 0 粉丝 / 370 能量 / 6 个 cell）与未登录态（点击登录、四格归零、空态文案），横向溢出 411/411，点击 cell 能跳到 `#/me/orders`。证据 `.local/deploy/profile-redesign-top.png`、`profile-redesign-bottom.png`。
- 设备验证：`scripts/build_android_debug.ps1` 重新构建 debug APK（55,333,231 B，SHA256 `3B47617556A55E5F90B46D276ED8313E9A8B5ECE89BC770C1DF7B93CD5103159`，API 仍为 `https://admin.wentian.org/api`），`adb install -r` 成功，设备内 `base.apk` 拉回后散列与产物一致（`3b476175…`），`lastUpdateTime=2026-10-20 16:33:46Z`。模拟器上「我的」页四项统计为 12/0/0/370、6 个 cell、横向溢出 411/411，滚动后应用栏保持吸顶并出现细分隔线；证据 `.local/deploy/profile-device-final-top.png`、`profile-device-final-scrolled.png`、`profile-device-loaded.png`。
- 顺带修掉一处旧残留：`user-web/src/mobile/router.ts` 里 `/profile` 的 `meta.surface` 仍按旧 305px 头图配 `#c5aaa1` 渐变，导致状态栏下方出现一条赭色带；改为 `#f5ede4` 后与新页底色一致。
- 限制：样式仍沿用项目自有字体与配色变量，未引入 Vant/NutUI 依赖，也未替换其它页面；浅色/深色主题与 360dp 窄屏未在本轮复验。

## 2026-10-20 深夜：本轮已知未覆盖范围

- 设备侧：本轮全部实机证据来自 Android 15/API 37 模拟器 + 生产后端；实体设备、Android 11/API 30 与 API 28 旧 WebView 未在本轮复跑。
- 教师后台：生成漏斗面板已上线并核对，但其余后台页面本轮未做全量回归；`/ai/stats` 的历史耗时统计口径含旧数据（0.0 秒多为导入种子行 `created_at == updated_at`）。
- 测试脚手架：`#/ai-workshop/shadow` 这类动态路由在设备 WebView 里用 `location.hash` 直接赋值会被弹回 `#/`，需通过界面点击；router-link 的 touch→click 在该 WebView 下不总触发，故驱动脚本对 `<a>` 额外补发 click。这属于测试脚手架适配，未改动产品代码。
- 本地壳行为：签名 URL 在设备里由 `mediaUrl()` 前缀成绝对地址后加载正常，但直接用相对路径 fetch 会被 Capacitor 的 `shouldInterceptRequest` 以 404/空响应拦下，这是本地壳行为不是服务端故障。

## 2026-10-21 凌晨（续）：生成剧场等待真实结果 + 成品自动定位

- 生成剧场新增 `waiting`：三步/四步动画播完后不再直接揭幕，而是停在「正在合成成品」，等 `working` 转 false（任务成功）后才显示「已交付」，并有 15 秒保底；失败/取消仍立即关闭遮罩。青铜、皮影、漆绣、剪影、数字沙盘五个模块全部传入 `waiting`。
- 皮影默认预览改为「彩色皮影」（原为镂空轮廓）；青铜/皮影/漆器预置可编辑的演示描述，分别对应饕餮宫灯、提灯旦角、缠枝莲团盒。
- 剧场预览修复：长图（如皮影 540×760）此前被按宽度撑到 326×459、再被 190px 舞台裁掉大半，只露头顶；改为绝对定位 + `object-fit: contain`，并加同图模糊底衬，成品在舞台上完整可读。
- 交付后自动定位成品：皮影/漆绣滚到预览卡片，青铜滚到画布，数字沙盘滚到展台，剪影滚到剪影结果，避免"生成完还停在表单底部"。
- 验证：`vue-tsc --noEmit` 0 错误；`vite build --mode android` 通过。新 APK 56,109,796 B，SHA256 `627576DC7CFB7009E90F2F1271060D466F901078288A2C3EE4784CFFF6C80ABB`（2026-10-21 04:13 构建，API 仍为 `https://admin.wentian.org/api`），`adb install -r` 后逐模块实测：数字沙盘渲染琉璃蟠龙（HUD 9.1 万面/6.1 MB、自动巡游/线框/重置视角可用）；皮影剧场 3.3 秒（0.04s 开场 → 2.39s「已交付」→ 3.3s 收起）并滚到预览（scrollY 326）；漆绣 2.0 秒交付并滚到成品（scrollY 1527）；青铜 2.4 秒交付，统计「1 组 / 3 层 / 600×600」正常；剪影交付后滚到剪影卡（scrollY 1207）。证据 `.local/deploy/device-theater-mid2.png`、`device-shadow-result2.png`、`device-lacquer-theater.png`、`device-bronze-theater2.png`、`device-model3d-after.png`、`device-shadow3d-after.png`。
- 代码提交：`bcb7af0`（等待结果 + 默认值）、`9e351eb`（预览不裁切 + 自动定位）、`64fcada`（本条记录）已推送到 `IKUNHEIHIE/jinyun-runxiang` master（推送中途 GCM 凭据失效，重新登录后成功）。交付包同时复制为 `jinyun-runxiang-final33-demo.apk`（仓库根目录、`D:\admin\desktop`、`.local/android/artifacts/` 各一份，56,109,796 B）。
- 观感修正（用户截图反馈）：皮影页「皮影工艺 / 设计流程 / 历史传承 / 功能特色」直接铺在驴皮花纹照片上，实机小字几乎读不出。给 `.craft-region`、`.history-region` 各加一层 `::before` 米纸渐变（0.82→0.90 / 0.90→0.94，`isolation: isolate` 保证压在图上、字在下），花纹退为底纹。设备复验 `.local/deploy/device-shadow-history-veil.png`、`device-shadow-craft-veil.png`；漆绣页脚是深底亮字，未改。commit `186084a` 已推送。
- 交付包更新：`jinyun-runxiang-final34-demo.apk`，56,109,801 B，SHA256 `2ea33fb63cfacd62ce3b247323949c9b43312c8711f750f91391250a831a747f`（仓库根、`D:\admin\desktop`、`.local/android/artifacts/` 各一份），已 `adb install -r` 到 emulator-5554。

## 2026-10-21 上午：教师端（角色决定 App 外壳）

- 测试教师账号：`teacher_li / teacher_zhao / teacher_su` 已写入生产库（`.local/deploy/create-teacher-accounts.py --apply`，可用 `--rollback --apply` 整体撤回），并各自带班级、成员、通知、作业、提交、今日考勤与一场跨班对抗赛。账号与口令只存在 `.local/deploy/teacher-credentials.txt`（gitignored，不入库、不打印）。
- 角色分流：学生账号登录仍是「首页/小课堂/AI工坊/社区/我的」，教师与管理员登录后落地 `#/teacher`，标签栏换成「教学/班级/作业/对抗赛/我的」（内联线稿图标，避免借用学生图标串义）。commit `83f73f1`。
- 冷启动不再闪学生首页：`router.beforeEach` 在目标为 `/` 或教师路由且本地还没有 profile 时先 `await loadProfile()`，拿到角色再决定落点。
- 教师从「我的」页登录也会被送到教学工坊：`AuthSheet` 里 `authRedirect=/profile` 不再压过角色判定（教师 + 空/`/`/`/profile` → `replace('/teacher')`）。
- 待批改闭环：`/mobile/teacher/overview` 与 `/teacher/assignments` 新增 `review_pending`（本班学生已提交且 `assignment_review` 无记录），教学工坊页据此显示「今日待办」（待批改 / 待记录考勤 / 进行中对抗赛 / 待提交催交，每条直达对应 tab），作业卡显示「待批改 N · 去批改」。
- 去掉已升为 tab 后遗留的详情页外壳：教学工坊返回箭头、班级页返回箭头与伪「学生模式」开关（改为指向 `/courses` 的「学生端」入口），作业/对抗赛 tab 的 `PageHeader :back="false"`，只有 `#/teacher/assignments/:id` 这类详情页保留返回箭头。
- 快捷操作换成真实入口：原「成绩录入」只是跳到作业列表、「设置」跳个人资料编辑，现改为「学生成绩」→ `/teacher/analytics`、「在线课堂」→ `/teacher/classroom`；课堂活跃度为 `—` 时补一句「还没有课堂记录 · 开启在线课堂后自动统计举手与互动」。
- 验证（emulator-5554 + 生产 API，`vue-tsc --noEmit` 0 错误）：
  - 教师登录落地与外壳：`#/teacher`、tabs `教学/班级/作业/对抗赛/我的`、无返回箭头、待办 3 条、`作业 3 份 · 待批改 5`。证据 `.local/deploy/device-teacher-hub-v2.png`、`device-teacher-hub-v5.png`、`device-review-hub-after.png`。
  - 四个 tab 与详情页：班级页无返回箭头且「学生端 ›」指向 `#/courses`；作业 tab 汇总条「本班还有 5 份作业待批改」+ 三张卡 0/3/2 份待批改；对抗赛 tab 无返回箭头；`#/teacher/assignments/6` 保留返回箭头并列出 3 份提交。证据 `device-teacher-class-v2.png`、`device-teacher-work-v2.png`、`device-teacher-contest-v2.png`、`device-teacher-review-detail-v2.png`。
  - 批改端到端：给「完成一张旦角线稿」的一份提交打 92 分 + 评语 → 详情页变「已批改」→ 作业 tab 汇总 5→4、卡片 3→2、教学工坊 `待批改 5`→`待批改 4`、待办首条同步。证据 `device-review-before-list.png`、`device-review-detail.png`、`device-review-sheet-filled.png`、`device-review-after-save.png`。
  - 冷启动：教师 `#/teacher`（token 331 位）稳定；学生 `student_demo01` 冷启动仍是 `#/` + 学生五个 tab，未被误跳。证据 `device-teacher-cold-final.png`、`device-student-cold-final.png`。
  - 破图/溢出：教师端各页 `broken: []`、`overflow: false`。
- 交付物：本轮 APK `user-web/android/app/build/outputs/apk/debug/app-debug.apk`，55,997,524 B，SHA256 `1d426febadd2588848a15eb6136e0da1a205f7e064f71201910553e13e4c3943`。注意：该包同时包含另一会话未提交的「我的/工坊」改版，未复制为 `finalNN-demo.apk` 交付包，等那次改版提交后再出包。
- 已知缺口：教师端「我的」tab 仍是学生档案页（0 作品 / 0 能量 / 学生徽章墙），要改成教师档案需动 `ProfilePage.vue`，该文件正被另一会话编辑，本轮避开。
- 教师端全路由设备审计（9 条，`route-audit-teacher-shell.json`）：`#/teacher`、`/teacher/analytics`、`/teacher/assignments`、`/teacher/assignments/6`、`/teacher/contests`、`/teacher/lesson-plan`、`/teacher/notices`、`/teacher/classroom`、教师视角 `#/profile` —— 61 张图 0 破图、0 横向溢出（文档宽=视口=411）、0 JS 异常。空态文案逐条核对（活跃度无记录、测验无记录、备课无记录）。审计中发现并修掉一处口误：在线课堂房间空态在学生端写「等待老师开启吧」，教师自己看到会变成第三人称，改为按角色分支（教师 → 「还没有课堂 · 点上方「开启课堂」就能开始文字直播」），复验 `device-teacher-classroom-copy.png`。
- 含上述审计与文案修正的安装包：`user-web/android/app/build/outputs/apk/debug/app-debug.apk`，55,997,528 B，SHA256 `cc684acaa5b1cf6672b9a79be938bf91384a7cf88a22fd4c8d2ea88166ac76b2`（取代上一条 `1d426feb…`，同样含另一会话未提交的改版，未出交付包）。
- 修掉一处对抗赛权限缺陷（`backend/app/api/contest.py`，已部署 sha 见下）：`_owned_contest()` 要求教师**同时**带两班，于是跨班对抗赛对**创建它的教师自己**也是 404 —— 教师端点「查看名单与评分」只会弹「班级不存在或无权访问」。改为读权限 = 主办教师（`contest.teacher_id`）∪ 任一方班级教师 ∪ 管理员；改名单只校验**被改动的那一方**；截止/公布仍要求主办教师、带两班或管理员。鉴权挪到状态判断之前，避免无权者从 409 里读出赛事阶段。生产权限矩阵（`.local/deploy/contest-permission-check.py`，含阴性对照）：li 读 200、zhao（客队教师）读 200、su（无关教师）读 404、su 改主队名单 404、li 改客队名单 404、li 改自己主队名单 409（已过状态门禁，说明授权路径正常）。
- 补齐对抗赛演示数据（`.local/deploy/seed-contest-round.py`，dry-run 默认、`--apply`、`--rollback`）：第 2 回合 6 名学生全部提交（主队 assignment 11、客队 12），两位教师各自批改（li 94/90/86，zhao 92/88/85），li 走 SCORING → PUBLISHED。教师端详情弹层实测「本轮胜者：蓟州皮影创客班 · 主队 第 1 名 总分 270 平均 90 · 客队 第 2 名 总分 265 平均 88.3」，列表卡在冷启动后显示「已提交 6 份 · 胜者：蓟州皮影创客班」（此前一次读到 0 是脚本复用了播种前已加载的页面实例，不是接口问题）。证据 `device-teacher-contest-sheet.png`。
- 打通跨班对抗赛的创建与发现（`contest.py` + `TeacherContestsPage.vue`，已部署）：
  - 旧规则要求发起教师**同时带两个班**，而 `/teacher/classes` 只返回自己的班，所以单班教师点「新建对抗赛」只会得到「至少需要两个班级才能创建对抗赛」——这个按钮对普通教师是死的。现在新增 `GET /teacher/contest-partners`（只给班级与带队教师，不含学生名单），客队下拉可选他班；被挑战班级的名单**不允许发起方点名**（`away_student_ids` 省略即客队全班自动参赛，显式传值且不是本班教师 → 403），对方教师随后可在自己端内调整本班名单。
  - `GET /teacher/contests` 的可见范围与读权限对齐：主办教师 ∪ 任一方班级教师（原来只给主办者，被挑战方在列表里根本发现不了这场）。
  - 设备实测（teacher_li）：新建弹层客队选项含「武清青铜纹样班 · 赵振宇 · 美术组」，选中后名单区改显示「客队由其他教师带班 · 创建后该班全体学生自动参赛」，创建成功并自动打开详情。生产权限矩阵：zhao 列表能看到新开的第 1 轮、读详情 200、改**自己**客队名单 200、改**主队**名单 404、li 仍能读、无关教师 su 列表为空（阴性对照）。新对抗赛 id=4 保持 OPEN（主队 2 人 / 客队 5 人自动参赛），可直接用于现场演示提交与打分。证据 `device-contest-create-sheet.png`、`device-contest-crossclass-result.png`。
- 考勤补上「迟到」这一档（`mobile_teacher.py` + `TeacherAnalyticsPage.vue` + `TeacherPage.vue`，已部署）：`class_attendance` 里本来就有 `LATE`（种子数据给刘子墨记的就是迟到），但教师端下拉只有 未记录/到课/请假/缺勤，`AttendanceItem.status` 也只收这三种 —— 结果该生在界面上显示为**空白下拉**，迟到人数在工坊页的考勤摘要里彻底消失。现补 `LATE` 选项与 `Literal`、`/mobile/teacher/overview` 增加 `attendance_late`，摘要文案改为「应到 N 人次 · 到课 a · 迟到 b · 请假 c · 缺勤 d」（原「实到」易与迟到混淆，已改名）。设备实测：刘子墨下拉正确显示「迟到」，把赵清和改记迟到后工坊页从「到课 5 · 迟到 1 / 83.3%」变为「到课 4 · 迟到 2 / 66.7%」，再改回缺勤后为「到课 4 · 迟到 1 · 缺勤 1」。证据 `device-teacher-attendance-after.png`、`device-teacher-late-check.png`（截图名见 `.local/deploy/`）。
- 考勤记录闭环（同轮）：教师端「班级」页逐生改状态 → 保存考勤 → 工坊页「今日到课率」与摘要同步（把缺勤的赵清和记为到课：66.7% → 83.3%，实到 4 → 5）。
- 教师端剩余两个核心动作端到端复验：
  - 班级通知：以 teacher_li 在 `#/teacher/notices` 填写标题与内容 → 点「发布通知」→ 列表顶部即时出现「第三回合对抗赛：明天带刻刀与灯箱 2026-10-21 12:12」；再用 student_demo01 令牌请求 `GET /api/mobile/classes/3/notices` 返回 3 条且新通知在最前，学生端入口为「我的 → 我的班级与作业 → `/notices?class_id=3`」（`PersonalServicePage.vue` → `NoticesPage.vue`），闭环成立。证据 `device-teacher-notice-published.png`。
  - 智能备课：`#/teacher/lesson-plan` 各区块齐全（课程配置、生成教案与课件、历史备课记录含空态「还没有备课记录，生成第一份教案后会保存在这里」、推荐模板 3 张），0 破图。本轮未点「生成」以免消耗真实 AI 额度；教学成就「匠心独运」因此仍为未达成（需要至少一份教案），演示前可先生成一份点亮。证据 `device-teacher-lesson-plan.png`。
