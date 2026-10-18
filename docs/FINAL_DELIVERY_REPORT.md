# 津韵润乡：当前交付状态与剩余工作

更新：2026-10-18。整体任务仍在进行中。当前已有可安装、可联调的 Android Debug 开发版，但尚未完成全量设计、功能与设备验收。没有实体真机测试证据，也没有可支持“97%还原”或“全部完成”的量化依据。

## 当前可测试产物

- APK：D:/admin/desktop/codex/school/smxc/jinyun-runxiang/.local/android/artifacts/jinyun-runxiang-debug.apk
- 包名：com.jinyun.runxiang
- 大小：274,631,763 字节
- SHA-256：BB4FF6A572BEAF55B613016986B92486B69F814015E2366EF3A8E381FA0A23A6
- 已安装到 emulator-5554，设备中 APK 与交付文件的 SHA-256 相同。
- 构建记录：.local/android/build-profile-recovery-android.log，包含类型检查、Vite、Capacitor 与 Gradle 构建。首页阶段D1101DF4…及备课阶段314D630A…分别另存为 .local/android/artifacts/home-d1101df4-debug.apk、lesson-plan-314d630a-debug.apk。
- 运行方式与配置见 [Android 部署说明](ANDROID_DEPLOYMENT.md)。该包使用开发 API；正式发布还需服务地址、签名及设备兼容性验证。

## 八项交付要求的当前证据

| 要求 | 当前状态 | 证据与未完成部分 |
|---|---|---|
| Android App | 已具备阶段开发版 | APK 构建、安装和局部真实运行通过；完整生命周期、旧 Android 与实体设备验证未完成 |
| 手机前端 | 部分完成 | 已逐页推进原始属性和资源还原；全量有效画板、所有状态与多尺寸视觉验收尚未通过 |
| 后端 | 已扩展并持续完善 | 130 项独立数据库回归通过；真实 MySQL 迁移和局部端到端记录另存，不等于所有业务完成 |
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
- 该轮终验包（final7，后续已被 final18 取代）：274,131,701 字节，SHA256 `2DC227A74EBFFEA6D0390E7B403BC9C29BD9F88ADDD357EFCB1790C12C0D1CA9`，构建日志 `.local/android/build-final7.log`（类型检查、Vite、Capacitor、Gradle `BUILD SUCCESSFUL`）。
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
- 终验包：274,763,249 字节，SHA256 `5280ae68767cf1b9d7df0730ce0b18cc92f5dd643bc6775cd105d6b1aaa23e93`，构建日志 `.local/android/build-final18.log`；已安装 emulator-5554，设备内 `base.apk` 散列与产物一致。
- 前端 `vue-tsc --noEmit` 退出码 0（`.local/android/typecheck-final18.log`）；后端全量回归 **133 项通过**（`.local/android/test-final18-full.log`）。final18 全路由冒烟（学生 28 条、教师 9 条）无破图、无未捕获异常、无本地请求失败；教师访问学生专属 `/contests/:id` 的 403 为权限预期。新增实测截图 `.local/design-baselines/app-heritage-stats-final18.png`。

## 尚未完成的核心工作

1. 全部有效设计页、所有状态及多尺寸的逐页验收。当前已能从 `docs/mastergo/*.html` 渲染设计导出基准并完成首页、课程、非遗、地图、市集、AI 工坊、个人中心的重点对照；剩余页面/状态与原始画布位图仍需继续核对。备课原稿的 4px 横向装饰线也未作为已验收项。
2. 作品许可、设计者/生产者归属、真实授权协议与生产对接；现有说明或标签不代表协议已落地。
3. 正式教学视频、外部图像/音频生成、LoRA 与草图重绘、三维、支付及远程视频课堂等服务。当前本地模板和演示资源不能代表这些能力已完成。
4. 工坊历史作品的“原位更新”能力及部分页面的设计细节；顶部悬浮搜索已补齐，课程播放页教师卡片、随堂鉴赏外框与底部工具条已按设计重建，但原始画布位图与多尺寸/多状态逐页对照仍未完成。地图底图已替换为天津行政区示意图，不再使用设计稿中的美国地图。
5. 实体设备、旧 Android、进程回收、完整跨账号/离线/跨日及全生命周期回归；Debug 包体积与生产发布配置仍需评估。

设计稿教师学情页出现的“书法/策展/传承”是示例分类，现有课程数据没有对应分类；本轮没有伪造这三类徽章。徽章目录已可在运营后台维护，实际授予规则仍以真实课程与场所数据为准。

当前证据只支持上述范围。原报告中的全量完成、实体真机验证、未经测量的还原百分比及不匹配的接口/组件清单已更正。整体目标保持进行中。
