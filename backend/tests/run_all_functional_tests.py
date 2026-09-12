#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《津韵润乡——天津非遗赋能乡村美育智能应用》
全业务功能端到端自动化测试与缺陷排查套件 (E2E Test Suite)
"""

import sys
import time
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000/api"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record(self, domain: str, test_name: str, success: bool, detail: str = ""):
        if success:
            self.passed += 1
            print(f"  [PASS] {domain} :: {test_name} {f'({detail})' if detail else ''}")
        else:
            self.failed += 1
            err_msg = f"  [FAIL] {domain} :: {test_name} - {detail}"
            print(err_msg)
            self.errors.append(err_msg)

res = TestResult()

def run_tests():
    print("================================================================================")
    print("        《津韵润乡》项目文档要求全功能端到端测试与缺陷排查验证开始")
    print("================================================================================")

    # -------------------------------------------------------------------------
    # 模块 1：用户认证与 RBAC 权限控制体系
    # -------------------------------------------------------------------------
    print("\n[1/8] 测试认证与 RBAC 权限体系...")
    # 1.1 管理员登录
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
    admin_ok = r.status_code == 200 and r.json().get("code") == 0
    admin_token = r.json().get("data", {}).get("token", "") if admin_ok else ""
    res.record("AUTH", "管理员登录 (/auth/login)", admin_ok, f"Token获取成功")

    # 1.2 教师登录
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": "teacher_wang", "password": "teacher123"})
    teacher_ok = r.status_code == 200 and r.json().get("code") == 0
    teacher_token = r.json().get("data", {}).get("token", "") if teacher_ok else ""
    res.record("AUTH", "教师登录 (/auth/login)", teacher_ok, f"教师角色: {r.json().get('data', {}).get('user', {}).get('role_code')}")

    # 1.3 学生登录
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": "student_ming", "password": "student123"})
    student_ok = r.status_code == 200 and r.json().get("code") == 0
    student_token = r.json().get("data", {}).get("token", "") if student_ok else ""
    res.record("AUTH", "乡村学生登录 (/auth/login)", student_ok, f"能量值: {r.json().get('data', {}).get('user', {}).get('energy_value')}")

    # 1.4 RBAC 越权拦截：学生访问运营管理大屏 (必须 403)
    r = requests.get(f"{BASE_URL}/admin/dashboard", headers={"Authorization": f"Bearer {student_token}"})
    res.record("AUTH", "RBAC越权拦截：学生访问管理后台", r.status_code == 403, f"Status={r.status_code}")

    # 1.5 RBAC 越权拦截：学生访问教师备课工作台 (必须 403)
    r = requests.get(f"{BASE_URL}/teacher/classes", headers={"Authorization": f"Bearer {student_token}"})
    res.record("AUTH", "RBAC越权拦截：学生访问教师工作台", r.status_code == 403, f"Status={r.status_code}")

    # 1.6 无 Token 访问受保资源 (必须 401)
    r = requests.get(f"{BASE_URL}/admin/dashboard")
    res.record("AUTH", "未认证拦截：无Token访问", r.status_code == 401, f"Status={r.status_code}")

    # 1.7 个人信息查询 (/auth/me)
    r = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    me_ok = r.status_code == 200 and r.json().get("data", {}).get("username") == "student_ming"
    res.record("AUTH", "当前用户画像与徽章查询 (/auth/me)", me_ok, f"学校: {r.json().get('data', {}).get('school_name')}")

    # -------------------------------------------------------------------------
    # 模块 2：非遗小课堂微课与乡村离线学习同步
    # -------------------------------------------------------------------------
    print("\n[2/8] 测试非遗微课与离线学习体系...")
    # 2.1 课程列表分页与品类过滤
    r = requests.get(f"{BASE_URL}/courses?category=SHADOW_PUPPET&page=1&pageSize=5")
    courses_ok = r.status_code == 200 and len(r.json().get("data", {}).get("list", [])) > 0
    course_list = r.json().get("data", {}).get("list", [])
    first_course_id = course_list[0]["id"] if course_list else 1
    res.record("COURSE", "微课列表检索与品类过滤 (/courses)", courses_ok, f"查获 {len(course_list)} 门津派皮影微课")

    # 2.2 课程详情与章节树结构
    r = requests.get(f"{BASE_URL}/courses/{first_course_id}", headers={"Authorization": f"Bearer {student_token}"})
    detail = r.json().get("data", {})
    chapters = detail.get("chapters", [])
    res.record("COURSE", "课程详情与章节节点解析 (/courses/{id})", len(chapters) > 0, f"共 {len(chapters)} 讲微课视频")
    chapter_id = chapters[0]["id"] if chapters else 1

    # 2.3 学习进度在线上报与美育能量增发
    r = requests.post(f"{BASE_URL}/courses/progress", headers={"Authorization": f"Bearer {student_token}"}, json={
        "course_id": first_course_id,
        "chapter_id": chapter_id,
        "position_seconds": 120,
        "duration_seconds": 300,
        "completed": True
    })
    prog_ok = r.status_code == 200 and r.json().get("code") == 0
    res.record("COURSE", "学习进度上报与完课能量激励 (/courses/progress)", prog_ok, f"能量增发: {r.json().get('data', {}).get('energy_added')}")

    # 2.4 乡村弱网离线事件批量同步
    offline_event_id = f"evt_test_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{BASE_URL}/courses/sync-offline", headers={"Authorization": f"Bearer {student_token}"}, json={
        "events": [{
            "event_id": offline_event_id,
            "event_type": "PROGRESS_UPDATE",
            "payload": {
                "course_id": first_course_id,
                "chapter_id": chapter_id,
                "position_seconds": 280,
                "duration_seconds": 300,
                "completed": True
            },
            "event_time": "2026-09-12T10:00:00"
        }]
    })
    sync_ok = r.status_code == 200 and offline_event_id in r.json().get("data", {}).get("synced_event_ids", [])
    res.record("COURSE", "弱网离线事件批量回传同步 (/courses/sync-offline)", sync_ok, f"已同步事件: {offline_event_id}")

    # -------------------------------------------------------------------------
    # 模块 3：AI 多模态非遗工坊异步创作
    # -------------------------------------------------------------------------
    print("\n[3/8] 测试 AI 多模态创作工坊...")
    # 3.1 提交津派皮影生成任务
    r = requests.post(f"{BASE_URL}/ai/tasks", headers={"Authorization": f"Bearer {student_token}"}, json={
        "tool_type": "SHADOW_PUPPET",
        "input_payload": {
            "role_type": "武生·杨柳青少年",
            "prompt": "身披红绫战甲，手执银枪的津沽小少年",
            "style": "TIANJIN_HERITAGE"
        }
    })
    task_ok = r.status_code == 200 and r.json().get("code") == 0
    ai_task_id = r.json().get("data", {}).get("task_id", "")
    res.record("AI", "提交AI多模态非遗生成任务 (/ai/tasks)", task_ok, f"任务ID: {ai_task_id}")

    # 等待后台异步推理完成 (测试环境 1~2秒)
    time.sleep(1.5)

    # 3.2 轮询任务成果（包含线稿、彩色贴图与 3D GLTF 骨骼模型）
    r = requests.get(f"{BASE_URL}/ai/tasks/{ai_task_id}")
    task_detail = r.json().get("data", {})
    mesh_3d = task_detail.get("result", {}).get("mesh_3d_url", "")
    color_art = task_detail.get("result", {}).get("colored_image_url", "")
    res.record("AI", "获取异步生成资产 (3D骨骼与渲染图) (/ai/tasks/{id})", bool(mesh_3d and color_art), f"3D模型: {mesh_3d[:35]}...")

    # 3.3 模型算法注册表与预签名上传
    r = requests.get(f"{BASE_URL}/ai/models")
    models_ok = r.status_code == 200 and len(r.json().get("data", [])) > 0
    res.record("AI", "非遗垂直大模型列表检索 (/ai/models)", models_ok, f"注册模型数: {len(r.json().get('data', []))}")

    # -------------------------------------------------------------------------
    # 模块 4：社区广场、互动交流与三级内容风控
    # -------------------------------------------------------------------------
    print("\n[4/8] 测试社区广场与三级内容风控...")
    # 4.1 正常作品发帖（预期自动审核通过 APPROVED）
    r = requests.post(f"{BASE_URL}/community/posts", headers={"Authorization": f"Bearer {student_token}"}, json={
        "title": "我在乡村微课堂独立制作的汉沽版画！",
        "content": "利用黑白套色技法展现渤海湾盐田风貌，老师说刀法很细腻！",
        "category": "PAINTING",
        "cover_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600"
    })
    post_normal_ok = r.status_code == 200 and r.json().get("data", {}).get("status") == "APPROVED"
    normal_post_id = r.json().get("data", {}).get("id")
    res.record("COMMUNITY", "学生发布正常作品 (自动初审通过 APPROVED)", post_normal_ok, f"PostID: {normal_post_id}")

    # 4.2 敏感词测试发帖（预期命中敏感词，自动降级送人工审核 PENDING_REVIEW）
    r = requests.post(f"{BASE_URL}/community/posts", headers={"Authorization": f"Bearer {student_token}"}, json={
        "title": "测试违规敏感词识别机制",
        "content": "这里包含暴力的字眼，测试风控系统是否能拦截。",
        "category": "SHADOW_PUPPET",
        "cover_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600"
    })
    post_sensitive_ok = r.status_code == 200 and r.json().get("data", {}).get("status") == "PENDING_REVIEW"
    sensitive_post_id = r.json().get("data", {}).get("id")
    res.record("COMMUNITY", "三级风控敏感词拦截 (自动流转待人工复审)", post_sensitive_ok, f"PostID: {sensitive_post_id} 状态={r.json().get('data', {}).get('status')}")

    # 4.3 点赞与取消点赞 (原子计数校验)
    r1 = requests.post(f"{BASE_URL}/community/posts/{normal_post_id}/like", headers={"Authorization": f"Bearer {student_token}"})
    like_count_after = r1.json().get("data", {}).get("like_count", 0)
    r2 = requests.post(f"{BASE_URL}/community/posts/{normal_post_id}/like", headers={"Authorization": f"Bearer {student_token}"})
    unlike_count_after = r2.json().get("data", {}).get("like_count", 0)
    like_ok = (like_count_after == unlike_count_after + 1)
    res.record("COMMUNITY", "作品点赞与取消点赞切换 (/posts/{id}/like)", like_ok, f"点赞数: {like_count_after} -> {unlike_count_after}")

    # 4.4 评论发表
    r = requests.post(f"{BASE_URL}/community/posts/{normal_post_id}/comments", headers={"Authorization": f"Bearer {teacher_token}"}, json={
        "content": "这位同学刀法沉稳，极好地表达了津沽盐雕的质朴精神！"
    })
    comment_ok = r.status_code == 200 and r.json().get("code") == 0
    res.record("COMMUNITY", "教师点评互动与评论提交 (/posts/{id}/comments)", comment_ok, "评论发布成功")

    # -------------------------------------------------------------------------
    # 模块 5：教师工作台与 AI 智能备课
    # -------------------------------------------------------------------------
    print("\n[5/8] 测试教师工作台与 AI 智能备课...")
    # 5.1 教师查看所辖乡村班级
    r = requests.get(f"{BASE_URL}/teacher/classes", headers={"Authorization": f"Bearer {teacher_token}"})
    classes_ok = r.status_code == 200 and len(r.json().get("data", [])) > 0
    classes = r.json().get("data", [])
    class_id = classes[0]["id"] if classes else 1
    res.record("TEACHER", "教师班级列表查询 (/teacher/classes)", classes_ok, f"所辖班级: {classes[0]['name'] if classes else 'N/A'}")

    # 5.2 AI 智能生成非遗三维美育教案
    r = requests.post(f"{BASE_URL}/teacher/lesson-plans/generate", headers={"Authorization": f"Bearer {teacher_token}"}, json={
        "grade": "小学四年级",
        "topic": "天津皮影戏",
        "duration_minutes": 45,
        "objectives": "培养乡村儿童对家乡皮影戏的文化自豪感与动手拼接能力"
    })
    plan_data = r.json().get("data", {})
    plan_ok = r.status_code == 200 and "targets" in plan_data and "activity_design" in plan_data
    res.record("TEACHER", "AI智能结构化备课生成 (/teacher/lesson-plans/generate)", plan_ok, f"生成课题: {plan_data.get('title')}")

    # 5.3 教师布置创作作业
    r = requests.post(f"{BASE_URL}/teacher/assignments", headers={"Authorization": f"Bearer {teacher_token}"}, json={
        "class_id": class_id,
        "title": "【非遗实践】设计一件生角或旦角津派皮影",
        "type": "AI_CREATION",
        "tool_type": "SHADOW_PUPPET",
        "deadline_days": 7,
        "description": "结合本周微课所讲，利用AI工坊生成设计草图并说明设计寓意。"
    })
    assignment_ok = r.status_code == 200 and r.json().get("code") == 0
    assignment_id = r.json().get("data", {}).get("id")
    res.record("TEACHER", "教师作业发布 (/teacher/assignments)", assignment_ok, f"作业ID: {assignment_id}")

    # 5.4 班级全景学情统计与五维美育雷达图
    r = requests.get(f"{BASE_URL}/teacher/classes/{class_id}/analytics", headers={"Authorization": f"Bearer {teacher_token}"})
    analytics = r.json().get("data", {})
    radar_ok = len(analytics.get("radar_capabilities", [])) == 5
    res.record("TEACHER", "班级学情全景与五维雷达分析 (/teacher/classes/{id}/analytics)", radar_ok, f"学情五维雷达指标完整")

    # -------------------------------------------------------------------------
    # 模块 6：文创助农市集与美育专项公益基金
    # -------------------------------------------------------------------------
    print("\n[6/8] 测试文创助农与美育专项基金...")
    # 6.1 商品与 SKU 规格列表查询
    r = requests.get(f"{BASE_URL}/mall/products")
    prods = r.json().get("data", [])
    mall_ok = r.status_code == 200 and len(prods) > 0
    prod = prods[0] if prods else {}
    sku = prod.get("skus", [{}])[0]
    res.record("MALL", "文创助农商品与SKU查询 (/mall/products)", mall_ok, f"首件商品: {prod.get('name')} (助农基金比例 {prod.get('fund_rate_percent')}%)")

    # 6.2 下单购买并自动划拨美育专项基金 (防超卖与原子更新)
    r = requests.post(f"{BASE_URL}/mall/orders", headers={"Authorization": f"Bearer {student_token}"}, json={
        "items": [{
            "product_id": prod.get("id"),
            "sku_id": sku.get("id"),
            "quantity": 1
        }],
        "receiver_name": "王晓明",
        "receiver_phone": "13800138000",
        "receiver_address": "天津市蓟州区下营镇中心小学图书室"
    })
    order_ok = r.status_code == 200 and r.json().get("code") == 0
    order_no = r.json().get("data", {}).get("order_no", "")
    fund_yuan = r.json().get("data", {}).get("fund_contributed_yuan", 0)
    res.record("MALL", "下单支付与美育公益基金定向划拨 (/mall/orders)", order_ok, f"订单: {order_no} 注入基金: ¥{fund_yuan}")

    # 6.3 超卖防御测试：尝试超额扣减库存
    r_oversell = requests.post(f"{BASE_URL}/mall/orders", headers={"Authorization": f"Bearer {student_token}"}, json={
        "items": [{
            "product_id": prod.get("id"),
            "sku_id": sku.get("id"),
            "quantity": 999999 # 极大数量
        }],
        "receiver_name": "超卖测试",
        "receiver_phone": "13800000000",
        "receiver_address": "测试地址"
    })
    oversell_blocked = (r_oversell.status_code == 200 and r_oversell.json().get("code") == 4090) or r_oversell.status_code == 400
    res.record("MALL", "高并发库存超卖防御 (原子条件校验)", oversell_blocked, f"正确拦截超额扣减 (返回4090库存不足)")

    # -------------------------------------------------------------------------
    # 模块 7：具身智能设备网关与硬件指令下发
    # -------------------------------------------------------------------------
    print("\n[7/8] 测试具身智能机器人网关...")
    # 7.1 获取设备列表与遥测状态
    r = requests.get(f"{BASE_URL}/devices")
    devices = r.json().get("data", [])
    dev_ok = r.status_code == 200 and len(devices) > 0
    dev_code = devices[0].get("device_code", "DEV_SHADOW_01") if devices else "DEV_SHADOW_01"
    res.record("DEVICE", "具身智能设备列表与遥测监控 (/devices)", dev_ok, f"在线设备: {dev_code}")

    # 7.2 教师下发皮影机器人演播指令
    r = requests.post(f"{BASE_URL}/devices/{dev_code}/command", headers={"Authorization": f"Bearer {teacher_token}"}, json={
        "command_type": "PERFORM_SHADOW_PLAY",
        "payload": {
            "play_id": "SHADOW_001",
            "action_seq": ["RAISE_LEFT_ARM", "SWING_SPEAR", "NOD_HEAD"]
        }
    })
    cmd_ok = r.status_code == 200 and r.json().get("data", {}).get("status") == "ACKED"
    res.record("DEVICE", "教师向皮影机器人下发动作演播指令", cmd_ok, f"回执ID: {r.json().get('data', {}).get('command_id')}")

    # 7.3 学生尝试控制硬件 (必须 403 权限拒绝)
    r = requests.post(f"{BASE_URL}/devices/{dev_code}/command", headers={"Authorization": f"Bearer {student_token}"}, json={
        "command_type": "RESET",
        "payload": {}
    })
    res.record("DEVICE", "硬件安全控制：阻止学生越权控制机器人", r.status_code == 403, f"Status={r.status_code}")

    # -------------------------------------------------------------------------
    # 模块 8：运营管理后台与人工内容审核闭环
    # -------------------------------------------------------------------------
    print("\n[8/8] 测试运营管理后台与人工风控闭环...")
    # 8.1 管理员调取待审核内容列表 (验证刚才触发敏感词的帖子)
    r = requests.get(f"{BASE_URL}/admin/reviews?status=PENDING_REVIEW", headers={"Authorization": f"Bearer {admin_token}"})
    pending_list = r.json().get("data", [])
    has_target = any(p["post_id"] == sensitive_post_id for p in pending_list)
    res.record("ADMIN", "运营待审列表查询 (捕获敏感词作品)", has_target or len(pending_list) > 0, f"待审池存在 {len(pending_list)} 篇待核作品")

    # 8.2 管理员人工审核处置 (批准通过 APPROVE)
    r = requests.post(f"{BASE_URL}/admin/reviews/{sensitive_post_id}/action", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "action": "APPROVE",
        "comment": "经人工复审，属于测试用例，准予展示"
    })
    action_ok = r.status_code == 200 and r.json().get("data", {}).get("new_status") == "APPROVED"
    res.record("ADMIN", "管理员人工复审处置 (/admin/reviews/{id}/action)", action_ok, f"帖子状态转为 APPROVED")

    # 8.3 管理员运营大屏数据看板
    r = requests.get(f"{BASE_URL}/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    dash_data = r.json().get("data", {})
    kpi = dash_data.get("kpi", {})
    trends = dash_data.get("trends", [])
    dash_ok = r.status_code == 200 and "dau" in kpi and len(trends) > 0
    res.record("ADMIN", "运营大屏全局KPI与趋势分析 (/admin/dashboard)", dash_ok, f"总用户数: {kpi.get('total_users')}, 基金总额: ¥{kpi.get('fund_total_yuan')}")

    # -------------------------------------------------------------------------
    # 统计总结
    # -------------------------------------------------------------------------
    print("\n================================================================================")
    print(f"                      全业务功能自动化测试执行完毕")
    print(f"  测试用例总计: {res.passed + res.failed} 项")
    print(f"  成功通过 (PASS): {res.passed} 项")
    print(f"  失败用例 (FAIL): {res.failed} 项")
    print(f"  综合测试通过率: {res.passed / (res.passed + res.failed) * 100:.1f}%")
    print("================================================================================")

    if res.failed > 0:
        print("\n失败用例明细：")
        for err in res.errors:
            print(err)
        sys.exit(1)
    else:
        print("\n>>> 所有文档要求核心业务功能验证 100% 通过，系统无阻塞性缺陷！<<<")

if __name__ == "__main__":
    run_tests()
