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
3. 正式教学视频、音频生成、LoRA、三维、支付及远程视频课堂等服务。真实图像生成与参考图重绘已在 2026-10-19 完成本地接入，后台与接口已部署线上并完成真实生图与编辑验证，详见 `AI_WORKSHOP_INTEGRATION.md`。
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
