"""Explicit development fixtures from the supplied design and existing seed file.

No orders, payments, ratings, followers or learning results are fabricated.
Only missing catalog rows are inserted; user-edited records are preserved.
"""
from app.models.entities import Product, ProductSku, HeritageLandmark, Badge, SysConfig, SysUser, Course, CourseChapter
from app.models.mobile import ExchangeItem, HeritageEntry
from app.core.course_badges import COURSE_BADGES, award_course_badges


def seed_catalog(db, image):
    # Use the course-frame originals instead of small home-page thumbnails.
    # Update only unchanged development fixtures, never teacher-edited covers.
    for title, category, thumbnail, original in [
        ("皮影艺术入门", "SHADOW_PUPPET", "5:02306", "5:05475"),
        ("剪纸技艺传承", "PAPER_CUTTING", "5:02116", "5:05573"),
        ("青花瓷韵", "CERAMICS", "5:02185", "5:05414"),
    ]:
        fixture = db.query(Course).filter_by(title=title, category=category).first()
        if (fixture and (fixture.description or "").startswith("开发环境课程") and
                fixture.cover_url == image("home", thumbnail)):
            fixture.cover_url = image("layer-40-32392", original)
    course = db.query(Course).filter_by(title="皮影艺术入门").first()
    if course:
        chapter = db.query(CourseChapter).filter_by(course_id=course.id, seq=1).first()
        if chapter and not chapter.video_url:
            chapter.video_url = "/static/videos/tianjin_shadow_puppet_lesson.mp4"
            chapter.title = "播放器联调样片（非正式教学资源）"
            course.description = "开发环境课程：使用仓库自带短片验证播放、进度保存与离线同步。正式教学视频待教师上传。"
    products = [
        ("祥云纹刺绣帆布包", "5:8080", 12800, 30),
        ("饕餮纹青铜鼎摆件", "5:8046", 36800, 25),
        ("皮影戏文创礼盒", "5:7965", 19800, 35),
        ("牡丹缠枝纹香囊", "5:7936", 6800, 40),
    ]
    for index, (name, node, cents, rate) in enumerate(products, 1):
        if not db.query(Product).filter_by(name=name).first():
            product = Product(name=name, category="CULTURAL_CREATIVE", cover_url=image("layer-5-7245", node),
                              origin_place="天津", fund_rate_percent=rate,
                              story="开发联调商品，名称、价格与图片来自MasterGo设计稿。尚未配置正式支付与发货服务。")
            db.add(product); db.flush()
            db.add(ProductSku(product_id=product.id, sku_code=f"DEV-DESIGN-{index}", name="标准款（联调）", price_cents=cents, stock=10))
    # Map-frame regional catalog. These are explicitly labelled development
    # products, not real merchant availability, purchases or paid fund records.
    for index, (name, node, district, cents) in enumerate([
        ("蓟州薄皮核桃", "5:03123", "蓟州区", 3800),
        ("燕山板栗", "5:03148", "蓟州区", 2800),
        ("宝坻红高粱酒", "5:03018", "宝坻区", 12800),
        ("有机红高粱米", "5:02992", "宝坻区", 1800),
        ("武清农家蔬菜礼盒", "5:03413", "武清区", 6800),
        ("散养土鸡蛋30枚", "5:03448", "武清区", 4500),
    ], 1):
        if not db.query(Product).filter_by(name=name).first():
            product = Product(name=name, category="AGRI_PRODUCT", cover_url=image("layer-40-11915", node),
                              origin_place="天津市" + district, fund_rate_percent=0,
                              story="开发联调商品，名称、价格与图片来自MasterGo研学地图。非正式在售农产，尚未配置正式支付与发货服务。")
            db.add(product); db.flush()
            db.add(ProductSku(product_id=product.id, sku_code=f"DEV-MAP-{index}", name="标准份（联调）", price_cents=cents, stock=10))
    for name, node, cost in [("水彩画材套装", "5:7339", 500), ("书法文房套装", "5:7288", 800)]:
        if not db.query(ExchangeItem).filter_by(name=name).first():
            db.add(ExchangeItem(name=name, cover_url=image("layer-5-7245", node), energy_cost=cost, stock=10))
    # Coordinates and addresses were already supplied in database/seed_data.sql.
    landmarks = [
        ("杨柳青古镇民俗文化馆", "年画", "天津市西青区杨柳青镇柳口路", "西青区", 39.1412, 117.0053, 800, "5:01977"),
        ("古文化街泥人张美术馆", "泥人张", "天津市南开区古文化街宫北街84号", "南开区", 39.1438, 117.1882, 500, "5:01951"),
        ("蓟州独乐寺与盘山非遗工坊", "非遗研学", "天津市蓟州区武定街41号", "蓟州区", 40.0465, 117.4089, 1000, "5:01989"),
    ]
    for name, category, address, district, lat, lng, radius, node in landmarks:
        if not db.query(HeritageLandmark).filter_by(name=name).first():
            db.add(HeritageLandmark(name=name, category=category, address=address, district=district,
                                   latitude=lat, longitude=lng, geofence_radius_meters=radius, cover_url=image("home", node),
                                   description="开发环境研学地标；配图为设计稿中的非遗作品示意。开放信息请以场馆公告为准。"))
    if not db.query(Badge).filter_by(code="BADGE_HERITAGE_PIONEER").first():
        db.add(Badge(code="BADGE_HERITAGE_PIONEER", name="乡村美育使者", description="在线下非遗地标成功签到打卡",
                     icon_url="/static/images/default_avatar.svg", condition_json={"type":"CHECKIN_COUNT","target":1}))
    if not db.query(Badge).filter_by(code="BADGE_WALK_PATHFINDER").first():
        db.add(Badge(code="BADGE_WALK_PATHFINDER", name="探路者", description="在同一上海自然日累计研学60分钟。只计算前台研学时间。",
                     icon_url="/static/images/default_avatar.svg", condition_json={"type":"DAILY_WALK_SECONDS","target":3600}))
    category_names = {"SHADOW_PUPPET": "皮影", "BRONZE": "青铜", "PAPER_CUTTING": "剪纸", "EMBROIDERY": "刺绣", "CERAMICS": "瓷器"}
    badge_images = {"SHADOW_PUPPET": ("layer-40-07198", "40:08347"), "BRONZE": ("layer-40-07198", "40:08400"),
                    "PAPER_CUTTING": ("layer-40-07198", "40:08446"), "EMBROIDERY": ("layer-40-07198", "40:08492"),
                    "CERAMICS": ("layer-5-00420", "5:00934")}
    for code, category, name, _ in COURSE_BADGES:
        if not db.query(Badge).filter_by(code=code).first():
            db.add(Badge(code=code, name=name, description=f"完成一门已发布{category_names[category]}课程的全部章节。",
                         icon_url=image(*badge_images[category]),
                         condition_json={"type": "COURSE_CATEGORY_COMPLETE", "category": category, "target": 1}))
    # Grant only from existing persisted progress; no fabricated learning records.
    for user in db.query(SysUser).order_by(SysUser.id).with_for_update().all():
        award_course_badges(db, user.id)
    if not db.query(SysConfig).filter_by(config_key="fund_goal_cents").first():
        db.add(SysConfig(config_key="fund_goal_cents", config_value="100000000", description="设计稿中的年度目标；实际累计仅统计真实入账记录"))
    entry = db.query(HeritageEntry).filter_by(title="杨柳青年画").first()
    if entry and entry.content_json.get("source") == "MasterGo 设计稿内容，开发环境初始条目":
        entry.content_json = {"source":"MasterGo 201619411459855 / 40:32809 设计稿正文", "sections":[
            {"title":"源起", "eyebrow":"ORIGIN & HISTORY", "body":"四百年传承的民间艺术。杨柳青年画发源于明代崇祯年间，盛于清代乾隆嘉庆时期，因产于天津杨柳青镇而得名。与苏州桃花坞年画并称‘南桃北柳’，是中国木版年画的重要代表。京杭大运河沿岸的交通便利、南北文化交融，为年画艺术的发展提供了沃土。明清时期，杨柳青镇‘家家会点染，户户善丹青’，形成了完整的年画产业链。"},
            {"title":"半印半画", "eyebrow":"CRAFTSMANSHIP", "body":"木版套印与手工彩绘的完美结合。", "steps":[
                {"title":"勾描刻版", "body":"画师将画稿反贴在梨木板上，以工笔勾描，再由刻工运用‘发、衬、挑、复、剔’等刀法精雕细刻，形成墨线版。"},
                {"title":"木版套印", "body":"采用‘饾版’水印技术，将墨线版与色版分次套印。一版一色，层层叠加，要求‘版版精准、色色分明’。"},
                {"title":"手工彩绘", "body":"套印完成后，画师以‘开脸’‘勾金’‘晕染’等技法手工彩绘。人物面部‘三白九染’，服饰纹样精细勾勒，赋予作品独特生命力。"},
                {"title":"装裱成品", "body":"经过托裱、裁切、装框等工序，一幅完整的杨柳青年画方才诞生。‘半印半画’的独特工艺，使其兼具版画的力度与手绘的灵动。"}]},
            {"title":"艺术特色 · 妙笔生花", "eyebrow":"ARTISTIC FEATURES", "body":"色彩鲜艳明快：朱红、石青、藤黄、花青等传统矿物颜料，色彩对比强烈而和谐。\n线条流畅细腻：继承工笔重彩传统，线条刚柔并济、疏密有致。人物衣纹飘逸灵动，面部刻画精细入微。\n构图饱满匀称：画面布局主次分明、繁而不乱，讲究‘满’与‘空’的辩证统一，在丰满的构图中留出呼吸空间。"},
            {"title":"经典题材", "eyebrow":"CLASSIC THEMES", "body":"娃娃类题材：胖娃娃或怀抱鲤鱼寓意‘连年有余’，或手捧谷穗象征‘五谷丰登’，寄托着人们对美好生活的向往。\n戏曲故事：取材于京剧、评剧等经典剧目，如《白蛇传》《西游记》《三国演义》，人物形象生动。\n风景花卉：四时花卉与山水风景，梅、兰、竹、菊寓意高洁品格，配以诗词题跋，兼具文人画意趣。"},
            {"title":"传承", "eyebrow":"CULTURAL HERITAGE", "body":"杨柳青年画是中国北方民俗文化的百科全书，记录了数百年的社会生活、民间信仰与审美趣味。2006年列入首批国家级非物质文化遗产名录。在数字化时代，杨柳青年画正以新的形式走进现代生活。当代艺术家将年画元素融入文创产品、数字艺术、时尚设计等领域，让古老艺术在新时代绽放异彩。"}
        ]}
