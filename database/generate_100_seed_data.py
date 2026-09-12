import random
import uuid
import pymysql
import hashlib
from datetime import datetime, timedelta

def get_connection():
    return pymysql.connect(
        unix_socket='/tmp/mysql.sock',
        user='root',
        password='root123456',
        database='jinyun_runxiang',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def sha256_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def main():
    conn = get_connection()
    cur = conn.cursor()
    print("=== 开始向 MySQL 导入 100+ 条真实业务测试数据 ===")

    total_inserted = 0

    # 1. 插入 20 名乡村美育学生与教师账号 (各区县乡村小学)
    districts = ['蓟州区', '宝坻区', '武清区', '宁河区', '静海区', '西青区', '北辰区']
    schools = [
        '蓟州区下营镇中心小学', '蓟州区穿芳峪镇中心小学', '宝坻区大口屯镇初级中学',
        '宝坻区霍各庄镇中心校', '武清区大王古庄镇小学', '武清区汊沽港镇中心小学',
        '宁河区七里海学校', '静海区独流镇中心小学', '西青区辛口镇中心小学'
    ]
    student_names = [
        ('赵子轩', 'zhao_zx'), ('陈雨涵', 'chen_yh'), ('刘浩宇', 'liu_hy'),
        ('孙诗涵', 'sun_sh'), ('杨子墨', 'yang_zm'), ('黄梦瑶', 'huang_my'),
        ('周楚淇', 'zhou_cq'), ('吴佳怡', 'wu_jy'), ('徐文博', 'xu_wb'),
        ('朱晓彤', 'zhu_xt'), ('林思宇', 'lin_sy'), ('何晨曦', 'he_cx'),
        ('郭梓涵', 'guo_zh'), ('马天翊', 'ma_ty'), ('高艺萌', 'gao_ym'),
        ('罗家宝', 'luo_jb'), ('梁欣怡', 'liang_xy'), ('宋俊豪', 'song_jh'),
        ('谢婉婷', 'xie_wt'), ('韩子恒', 'han_zh')
    ]
    grades = ['小学三年级', '小学四年级', '小学五年级', '初中一年级']
    pwd_hash = sha256_hash("student123")

    user_ids = []
    for name, uname in student_names:
        cur.execute("""
            INSERT INTO sys_user (username, password_hash, nickname, avatar_url, role_code, grade, status, phone)
            VALUES (%s, %s, %s, %s, 'STUDENT', %s, 'ACTIVE', %s)
            ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)
        """, (
            uname, pwd_hash, name,
            f"https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
            random.choice(grades),
            f"1380000{random.randint(1000, 9999)}"
        ))
        uid = cur.lastrowid
        user_ids.append(uid)
        total_inserted += 1

        # Profile & Growth
        district = random.choice(districts)
        school = random.choice(schools)
        cur.execute("""
            INSERT INTO user_profile (user_id, school_name, district, bio, avatar_config_json)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE school_name=VALUES(school_name)
        """, (
            uid, school, district, f"来自{school}的非遗美育学徒",
            '{"outfit":"FOLK_VEST","badge":"NEWBIE"}'
        ))
        cur.execute("""
            INSERT INTO user_growth (user_id, energy_value, level_code)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE energy_value=VALUES(energy_value)
        """, (
            uid, random.randint(200, 1500),
            random.choice(['LV1_APPRENTICE', 'LV2_JOURNEYMAN', 'LV3_CRAFTSMAN'])
        ))
    conn.commit()
    print(f"✓ 成功导入 20 名乡村学生账号与档案数据")

    # 2. 插入 10 门特色非遗微课与章节
    courses_data = [
        ('魏记风筝制作技艺：骨架榫卯与凌空放飞', '非遗大师讲解“风筝魏”的折叠榫卯秘籍', 'BRONZE', 'PRIMARY_HIGH', 40, 50),
        ('汉沽版画：泥土与黑白的滨海叙事', '领略津沽盐滩版画的质朴与张力', 'PAINTING', 'JUNIOR', 45, 60),
        ('曾氏剪纸：剪刀尖上的津沽四时景', '巧剪十二生肖与民俗窗花技艺', 'SHADOW_PUPPET', 'PRIMARY_LOW', 30, 40),
        ('独乐寺鲁班锁与古建榫卯智慧', '千年辽代木构不用一钉一铆的奥秘', 'BRONZE', 'JUNIOR', 50, 70),
        ('津派面塑：指尖捏出的万千生灵', '面团里的津味童趣与生动神态', 'CLAY', 'PRIMARY_LOW', 35, 45),
        ('益德成闻药制作技艺：古法研磨百草香', '感受津门中药香氛非遗的本草智慧', 'LACQUER', 'JUNIOR', 40, 50),
        ('老美华手工制鞋：千层底纳出百年舒展', '一针一线中的传统手作精髓', 'EMBROIDERY', 'PRIMARY_HIGH', 45, 60),
        ('宝坻评剧入门：刘派唱腔清亮婉转', '从《刘巧儿》品读天津评剧之美', 'BALLAD', 'PRIMARY_HIGH', 35, 45),
        ('葛沽宝辇会：妈祖祭典里的花会盛景', '运河商埠重镇的民间祭乐巡游', 'BALLAD', 'PRIMARY_LOW', 40, 50),
        ('天津回族重刀武术：刚毅豪迈的津门气魄', '非遗武术的力与美展示', 'SHADOW_PUPPET', 'PRIMARY_HIGH', 45, 50)
    ]
    course_ids = []
    for title, sub, cat, age, dur, reward in courses_data:
        cur.execute("""
            INSERT INTO course (title, subtitle, category, age_group, cover_url, description, duration_minutes, energy_reward, view_count, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'PUBLISHED')
        """, (
            title, sub, cat, age,
            'https://images.unsplash.com/photo-1582560475093-ba66accbc424?w=600',
            f"{sub}。课程带同学们走入津沽乡土，深度领悟非遗技艺背后的文化内涵。",
            dur, reward, random.randint(300, 2000)
        ))
        cid = cur.lastrowid
        course_ids.append(cid)
        total_inserted += 1

        # 为每门课创建1个章节
        cur.execute("""
            INSERT INTO course_chapter (course_id, seq, title, video_url, duration_seconds, key_points_json)
            VALUES (%s, 1, '第一讲：传承探秘与技艺入门', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4', %s, %s)
        """, (
            cid, dur * 60, '["非遗源起与历史故事","核心原材料选取","关键操作手法图解"]'
        ))
    conn.commit()
    print(f"✓ 成功导入 10 门天津非遗微课与配套章节")

    # 3. 插入 25 条 AI 工坊异步创作任务与生成资产
    ai_tools = ['SHADOW_PUPPET', 'BRONZE', 'BALLAD', 'LACQUER', 'EMBROIDERY']
    prompts = [
        '身披铠甲的穆桂英皮影女将，手执红缨长枪',
        '商周饕餮纹样青铜守护神兽，带铜绿氧化质感',
        '天津海河晚渡时调大鼓曲牌，三弦伴奏清脆',
        '古法大漆黑漆螺钿花鸟圆盘，配中国传统泥金色号',
        '杨柳青年画风格吉祥金鱼娃娃，线条圆润生动',
        '齐天大圣大闹天宫皮影，头戴雉尾金冠',
        '夔龙纹青铜编钟浮雕纹饰，金石拓片风',
        '津门老茶馆风趣说唱单弦曲调，鼓板节奏紧凑',
        '天然矿物颜料漆艺茶具，螺钿光彩变幻',
        '手工刺绣天津市花月季图案，丝线质感细腻'
    ]
    for i in range(25):
        uid = random.choice(user_ids)
        tool = random.choice(ai_tools)
        task_uuid = uuid.uuid4().hex
        p_text = random.choice(prompts)
        
        cur.execute("""
            INSERT INTO ai_task (task_id, user_id, tool_type, status, progress, model_id, model_version, input_json, result_summary_json, trace_id)
            VALUES (%s, %s, %s, 'SUCCESS', 100, 1, '1.0.0', %s, %s, %s)
        """, (
            task_uuid, uid, tool,
            f'{{"prompt":"{p_text}","style":"TIANJIN_HERITAGE"}}',
            f'{{"colored_image_url":"/static/generated/shadow_colored_sample.svg","mesh_3d_url":"/static/models/tianjin_shadow_puppet.glb","description":"AI成功提取津门皮影艺术语言，完成刀法拓印与传统矿物色渲染。"}}',
            f"trace_{task_uuid[:8]}"
        ))
        total_inserted += 1
    conn.commit()
    print(f"✓ 成功导入 25 条 AI工坊异步生成任务与作品资产")

    # 4. 插入 25 条 社区广场学生作品与心得帖子
    post_titles = [
        '我在美育课上做的皮影“小哪吒闹海”！',
        '王老师指导的杨柳青抱鱼娃娃套印心得',
        '用AI重现天津博物馆里的青铜饕餮神兽',
        '为爷爷创作的骆派京韵大鼓小段',
        '大漆螺钿杯垫设计：天然大漆太神奇了',
        '第一次操纵三签皮影演孙悟空翻跟头',
        '给乡村学校图书角画的年画书签',
        '我的青铜纹样小神兽：它叫“津沽宝卫”',
        '传统评剧唱腔和AI五声音阶的奇妙碰撞',
        '下营中心小学非遗创客社团第一件手工作品'
    ]
    for i in range(25):
        uid = random.choice(user_ids)
        title = random.choice(post_titles)
        cur.execute("""
            INSERT INTO community_post (user_id, title, content, category, cover_url, topic_id, status, is_featured, heritage_master_like, like_count, comment_count, favorite_count, view_count)
            VALUES (%s, %s, %s, %s, %s, 1, 'APPROVED', %s, %s, %s, %s, %s, %s)
        """, (
            uid, f"{title} (#{i+1})",
            "在非遗微课堂学到了老手艺人的耐心与专注，借用AI工坊完成了灵感设计，并亲自动手雕镂打磨，感受家乡非遗的美！",
            random.choice(['SHADOW_PUPPET', 'PAINTING', 'CLAY', 'BRONZE']),
            'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600',
            1 if i % 3 == 0 else 0,
            1 if i % 5 == 0 else 0,
            random.randint(20, 260),
            random.randint(3, 40),
            random.randint(5, 50),
            random.randint(100, 800)
        ))
        pid = cur.lastrowid
        total_inserted += 1

        # 增加一条点赞与评论
        cur.execute("""
            INSERT INTO community_comment (post_id, user_id, content, status)
            VALUES (%s, 2, '造型很有传统津味！线条镂空疏密得当，继续加油！', 'APPROVED')
        """, (pid,))
        total_inserted += 1
    conn.commit()
    print(f"✓ 成功导入 25 篇社区非遗作品分享与互动评论")

    # 5. 插入 10 个天津文旅非遗地标与线下活动打卡
    landmarks_data = [
        ('黄崖关长城非遗传习基地', '古建筑与民间手艺', '天津市蓟州区黄崖关村', '蓟州区', 40.2435, 117.4321),
        ('西青杨柳青石家大院民俗馆', '民俗建筑与戏楼文化', '天津市西青区杨柳青镇御河桥西', '西青区', 39.1389, 117.0023),
        ('宝坻潮白河湿地非遗工坊', '水乡手作与苇席编织', '天津市宝坻区潮阳街道', '宝坻区', 39.7123, 117.3102),
        ('武清南湖非遗文创生态园', '民间印染与手工陶艺', '天津市武清区下朱庄街', '武清区', 39.3245, 117.0987),
        ('静海独流老醋古法酿造工坊', '传统酿造酿造技艺', '天津市静海区独流镇友好街', '静海区', 38.9321, 116.9876)
    ]
    for name, cat, addr, dist, lat, lon in landmarks_data:
        cur.execute("""
            INSERT INTO heritage_landmark (name, category, address, district, latitude, longitude, geofence_radius_meters, description, cover_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, 600, %s, %s, 'ACTIVE')
        """, (
            name, cat, addr, dist, lat, lon,
            f"津沽大地重要的文化传承地标，配套有乡村美育研学课程和非遗实地打卡点。",
            'https://images.unsplash.com/photo-1569783727725-b88d3e230756?w=600'
        ))
        lmid = cur.lastrowid
        total_inserted += 1

        # 插入1条学生打卡
        cur.execute("""
            INSERT INTO activity_checkin (activity_id, landmark_id, user_id, latitude, longitude, distance_meters)
            VALUES (1, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE distance_meters=VALUES(distance_meters)
        """, (lmid, random.choice(user_ids), lat + 0.0001, lon + 0.0001, random.randint(10, 80)))
        total_inserted += 1
    conn.commit()
    print(f"✓ 成功导入 10 条非遗文旅地标与GPS打卡记录")

    # 6. 插入 10 条文创与特色农产品助农订单及美育基金流水
    for i in range(10):
        ord_no = f"ORD20260912{uuid.uuid4().hex[:8].upper()}"
        uid = random.choice(user_ids)
        amount = random.randint(3900, 19800)
        fund = int(amount * 0.10)
        cur.execute("""
            INSERT INTO order_main (order_no, user_id, total_amount_cents, fund_amount_cents, status, receiver_name, receiver_phone, receiver_address, pay_time)
            VALUES (%s, %s, %s, %s, 'COMPLETED', '爱心助农采购人', '13812345678', '天津市南开区卫津路92号', NOW())
        """, (ord_no, uid, amount, fund))
        ord_id = cur.lastrowid
        total_inserted += 1

        # 沉淀美育基金流水
        cur.execute("""
            INSERT INTO fund_record (source_order_id, amount_cents, purpose, status)
            VALUES (%s, %s, '蓟州/宝坻乡村小学非遗美育耗材定向采购', 'ALLOCATED')
        """, (ord_id, fund))
        total_inserted += 1
    conn.commit()
    print(f"✓ 成功导入 10 笔文创助农订单与美育基金流水")

    cur.close()
    conn.close()

    print(f"\n=======================================================")
    print(f"🎉 100 条全业务测试数据生成完毕！累计新增入库记录：{total_inserted} 条")
    print(f"=======================================================")

if __name__ == '__main__':
    main()
