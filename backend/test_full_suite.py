import xml.etree.ElementTree as ET

def test_xml(svg_str, name):
    try:
        ET.fromstring(svg_str)
        print(f"✓ [{name}] Valid SVG")
        return True
    except Exception as e:
        print(f"✗ [{name}] Error: {e}")
        return False
