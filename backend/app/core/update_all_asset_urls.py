from app.core.database import SessionLocal
from app.models.entities import CommunityPost, Course, HeritageLandmark, Product, UserProfile

def update_asset_urls():
    db = SessionLocal()
    try:
        # 1. 更新社区帖子封面图
        posts = db.query(CommunityPost).all()
        post_img_map = {
            "皮影": "/static/images/shadow_puppet_1.svg",
            "穆桂英": "/static/images/shadow_puppet_1.svg",
            "孙悟空": "/static/images/shadow_puppet_2.svg",
            "年画": "/static/images/yangliuqing_1.svg",
            "杨柳青": "/static/images/yangliuqing_1.svg",
            "抱鱼": "/static/images/yangliuqing_2.svg",
            "泥人": "/static/images/clay_figurine_1.svg",
            "泥塑": "/static/images/clay_figurine_1.svg",
            "兔子王": "/static/images/clay_figurine_2.svg",
            "青铜": "/static/images/bronze_taotie_1.svg",
            "饕餮": "/static/images/bronze_taotie_2.svg",
            "风筝": "/static/images/weiji_kite_1.svg",
            "大漆": "/static/images/lacquer_craft_1.svg",
            "螺钿": "/static/images/lacquer_craft_1.svg",
            "版画": "/static/images/hangu_woodcut_1.svg",
            "大鼓": "/static/images/shadow_puppet_3.svg",
            "社团": "/static/images/yangliuqing_3.svg",
        }
        svg_pool = [
            "/static/images/shadow_puppet_1.svg",
            "/static/images/yangliuqing_1.svg",
            "/static/images/clay_figurine_1.svg",
            "/static/images/bronze_taotie_1.svg",
            "/static/images/weiji_kite_1.svg",
            "/static/images/lacquer_craft_1.svg",
            "/static/images/hangu_woodcut_1.svg",
            "/static/images/shadow_puppet_2.svg",
            "/static/images/yangliuqing_2.svg",
            "/static/images/clay_figurine_2.svg"
        ]
        
        post_cnt = 0
        for i, p in enumerate(posts):
            matched = False
            for k, url in post_img_map.items():
                if k in (p.title or "") or k in (p.content or ""):
                    p.cover_url = url
                    matched = True
                    break
            if not matched:
                p.cover_url = svg_pool[i % len(svg_pool)]
            post_cnt += 1
        
        # 2. 更新非遗微课封面图
        courses = db.query(Course).all()
        course_cat_map = {
            "SHADOW_PUPPET": "/static/images/shadow_puppet_1.svg",
            "PAINTING": "/static/images/yangliuqing_1.svg",
            "CLAY": "/static/images/clay_figurine_1.svg",
            "BRONZE": "/static/images/bronze_taotie_1.svg",
            "LACQUER": "/static/images/lacquer_craft_1.svg",
            "KITE": "/static/images/weiji_kite_1.svg",
            "BALLAD": "/static/images/shadow_puppet_2.svg",
            "FOLK_CUSTOM": "/static/images/yangliuqing_2.svg"
        }
        course_cnt = 0
        for c in courses:
            c.cover_url = course_cat_map.get(c.category, "/static/images/shadow_puppet_1.svg")
            course_cnt += 1

        # 3. 更新研学地标封面图
        landmarks = db.query(HeritageLandmark).all()
        lm_pool = [
            "/static/images/landmark_duleyi.svg",
            "/static/images/landmark_tianjin_museum.svg",
            "/static/images/landmark_yangliuqing.svg",
            "/static/images/landmark_guangdong_guild.svg"
        ]
        lm_cnt = 0
        for i, lm in enumerate(landmarks):
            lm.cover_url = lm_pool[i % len(lm_pool)]
            lm_cnt += 1

        # 4. 更新助农文创商品封面图
        products = db.query(Product).all()
        prod_pool = [
            "/static/images/product_diy_kit.svg",
            "/static/images/product_clay_rabbit.svg"
        ]
        prod_cnt = 0
        for i, pr in enumerate(products):
            pr.cover_url = prod_pool[i % len(prod_pool)]
            prod_cnt += 1

        db.commit()
        print(f"Updated {post_cnt} posts, {course_cnt} courses, {lm_cnt} landmarks, {prod_cnt} products to authentic local SVGs!")
    finally:
        db.close()

if __name__ == "__main__":
    update_asset_urls()
