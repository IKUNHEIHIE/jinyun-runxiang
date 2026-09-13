import xml.etree.ElementTree as ET

def test_xml(svg_str, name="test"):
    try:
        ET.fromstring(svg_str)
        print(f"[{name}] XML is valid!")
        return True
    except Exception as e:
        print(f"[{name}] XML error: {e}")
        return False

print("Helper ready")
