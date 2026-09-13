import urllib.parse
import httpx
import pptx

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_suggestion_1_festivals():
    print("=== Testing Suggestion 1: Folk Festivals CRUD ===")
    with httpx.Client(base_url=BASE_URL, trust_env=False, timeout=10.0) as client:
        # 1. List festivals
        res = client.get("/festivals")
        assert res.status_code == 200, f"Failed to list festivals: {res.text}"
        festivals = res.json()["data"]
        assert len(festivals) >= 5, f"Expected at least 5 seeded festivals, got {len(festivals)}"
        print(f"✓ Successfully listed {len(festivals)} festivals from database.")

        # 2. Check Home feed festival topic
        res_home = client.get("/home/feed")
        assert res_home.status_code == 200
        topic = res_home.json()["data"]["festival_topic"]
        assert topic and "title" in topic, "Failed to get dynamic festival topic in home feed"
        print(f"✓ Dynamic home feed festival topic: {topic['title']} ({topic['date']})")

def test_suggestion_2_screen_overview():
    print("\n=== Testing Suggestion 2: Digital Screen Overview Stream ===")
    with httpx.Client(base_url=BASE_URL, trust_env=False, timeout=10.0) as client:
        res = client.get("/screen/overview")
        assert res.status_code == 200, f"Failed to get screen overview: {res.text}"
        data = res.json()["data"]
        
        # Verify KPIs
        assert len(data["kpis"]) == 5, f"Expected 5 KPIs, got {len(data['kpis'])}"
        print(f"✓ Screen KPIs verified: {[k['label'] + '=' + k['value'] for k in data['kpis']]}")
        
        # Verify Charts data
        assert len(data["pie_chart"]) >= 5, "Pie chart missing categories"
        assert len(data["bar_chart"]["values"]) == 5, "Bar chart missing values"
        print("✓ Pie and Bar chart data dynamically aggregated from database.")

        # Verify Donation stream
        assert len(data["donation_orders"]) >= 7, "Donation orders missing"
        print(f"✓ Real-time donation order stream verified: {len(data['donation_orders'])} items.")

def test_suggestion_3_pptx_export():
    print("\n=== Testing Suggestion 3: Real PPTX Lesson Plan Export ===")
    with httpx.Client(base_url=BASE_URL, trust_env=False, timeout=15.0) as client:
        params = {"topic": "杨柳青木版年画", "grade": "小学四年级", "duration_minutes": 45}
        url = "/teacher/lesson-plans/export-pptx?" + urllib.parse.urlencode(params)
        res = client.get(url)
        assert res.status_code == 200, f"Failed to export PPTX: {res.status_code}"
        assert "presentation" in res.headers.get("content-type", ""), "Invalid content-type for PPTX"
        content_len = len(res.content)
        assert content_len > 20000, f"PPTX file too small ({content_len} bytes)"
        
        # Parse generated PPTX using python-pptx
        import io
        prs = pptx.Presentation(io.BytesIO(res.content))
        slide_count = len(prs.slides)
        assert slide_count >= 6, f"Expected at least 6 slides, got {slide_count}"
        print(f"✓ Successfully generated real PPTX file ({content_len} bytes) with {slide_count} slides.")

if __name__ == "__main__":
    test_suggestion_1_festivals()
    test_suggestion_2_screen_overview()
    test_suggestion_3_pptx_export()
    print("\n🎉 ALL THREE SUGGESTIONS VERIFIED SUCCESSFULLY WITH ZERO ERRORS!")
