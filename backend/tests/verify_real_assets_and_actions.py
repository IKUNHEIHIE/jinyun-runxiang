import sys
import httpx

BASE_URL = "http://localhost:8000"

def test_real_assets_and_actions():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. 验证静态 3D 模型
    res = client.get("/static/models/tianjin_shadow_puppet.glb")
    assert res.status_code == 200, f"3D model failed: {res.status_code}"
    assert len(res.content) > 500, "3D model content is empty"
    print("✓ [PASS] 真实 3D GLB 皮影模型托管正常 (Content-Length:", len(res.content), "bytes)")

    # 2. 验证微课 MP4 视频
    res = client.get("/static/videos/tianjin_shadow_puppet_lesson.mp4")
    assert res.status_code == 200, f"MP4 video failed: {res.status_code}"
    assert res.headers.get("content-type") == "video/mp4"
    print("✓ [PASS] 真实 MP4 微课导学视频托管正常 (Content-Length:", len(res.content), "bytes)")

    # 3. 登录管理员
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. 真实文件上传接口
    files = {"file": ("test_puppet_craft.svg", b"<svg width='100' height='100'><rect width='100' height='100' fill='red'/></svg>", "image/svg+xml")}
    up_res = client.post("/api/ai/assets/upload", files=files, headers=headers)
    assert up_res.status_code == 200, f"Upload failed: {up_res.text}"
    up_data = up_res.json()["data"]
    file_url = up_data["file_url"]
    assert file_url.startswith("/static/uploads/"), f"Unexpected url: {file_url}"
    # 验证上传后的静态文件可访问
    get_up = client.get(file_url)
    assert get_up.status_code == 200
    print("✓ [PASS] 真实多模态文件上传与静态落盘验证成功 (URL:", file_url, ")")

    # 5. 课程发布与状态下架/上架切换
    course_data = {
        "title": "津派皮影神兽数字化重构实操",
        "subtitle": "非遗传统与AI技术交融",
        "category": "SHADOW_PUPPET",
        "age_group": "小学高段",
        "duration_minutes": 40,
        "energy_reward": 45,
        "description": "亲手制作皮影关节并使用AI生成专属津门皮影神兽。"
    }
    c_res = client.post("/api/courses", json=course_data, headers=headers)
    assert c_res.status_code == 200, f"Create course failed: {c_res.text}"
    course_id = c_res.json()["data"]["id"]
    print("✓ [PASS] 课程新建发布接口成功 (Course ID:", course_id, ")")

    toggle_res = client.put(f"/api/courses/{course_id}/status", headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["data"]["status"] == "OFFLINE"
    print("✓ [PASS] 课程状态流转切换成功 (OFFLINE)")

    toggle_res2 = client.put(f"/api/courses/{course_id}/status", headers=headers)
    assert toggle_res2.status_code == 200
    assert toggle_res2.json()["data"]["status"] == "PUBLISHED"
    print("✓ [PASS] 课程重新上架发布成功 (PUBLISHED)")

    # 6. AI 模型配置持久化与状态切换
    models_res = client.get("/api/ai/models?all_status=true", headers=headers)
    assert models_res.status_code == 200
    models = models_res.json()["data"]
    assert len(models) > 0
    first_model = models[0]
    update_res = client.put(f"/api/ai/models/{first_model['id']}", json={
        "name": first_model["name"],
        "prompt_template": "津门杨柳青年画特色Prompt，融合天津传统套印木版画风：{prompt}",
        "status": "ACTIVE"
    }, headers=headers)
    assert update_res.status_code == 200
    print("✓ [PASS] AI 模型参数与 Prompt 模版持久化修改成功")

    print("\n=======================================================")
    print(">>> 真实资产与业务动作端到端专项验证全部 PASS！<<<")
    print("=======================================================")

if __name__ == "__main__":
    test_real_assets_and_actions()
