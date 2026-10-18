#!/usr/bin/env python3
"""Render MasterGo HTML exports into PNG design baselines.

The exports live in docs/mastergo and reference image-resource.mastergo.com
URLs. serve_design_baselines.Handler rewrites those URLs to bundled assets and
adds local fonts, so the pages render offline in headless Edge.
"""
import argparse
import os
import re
import subprocess
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from serve_design_baselines import Handler

ROOT = Path(__file__).resolve().parents[1]
DESIGN_DIR = ROOT / "docs" / "mastergo"


def find_edge() -> str:
    candidates = [
        os.environ.get("EDGE_PATH", ""),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise SystemExit("Microsoft Edge not found; set EDGE_PATH")


def page_size(html: str):
    match = re.search(r"width:([0-9.]+)px;min-height:([0-9.]+)px", html[:3000])
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / ".local" / "design-baselines"))
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    edge = find_edge()
    profile_dir = ROOT / ".local" / "edge-headless-design"
    profile_dir.mkdir(parents=True, exist_ok=True)

    server = None
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 5191), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
    except OSError:
        pass  # an existing baseline server is fine

    rendered = 0
    for html_file in sorted(DESIGN_DIR.glob("*.html")):
        if args.only and html_file.stem not in args.only:
            continue
        html = html_file.read_text(encoding="utf-8")
        size = page_size(html)
        if not size:
            continue
        width, height = size
        if width < 300:
            continue
        dest = out_dir / (html_file.stem + ".png")
        if dest.exists() and dest.stat().st_size > 10000 and not args.force:
            print("skip", html_file.stem)
            continue
        command = [
            edge,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile_dir}",
            "--virtual-time-budget=3000",
            f"--window-size={int(width)},{int(height)}",
            f"--screenshot={dest.resolve().as_posix()}",
            f"http://127.0.0.1:5191/docs/mastergo/{html_file.name}",
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        if result.returncode != 0 or not dest.exists():
            raise SystemExit(f"render failed: {html_file.name}\n{result.stderr[-500:]}")
        print(f"{html_file.stem} {int(width)}x{int(height)} -> {dest}")
        rendered += 1

    if server:
        server.shutdown()
    print(f"rendered {rendered} baseline(s) into {out_dir}")


if __name__ == "__main__":
    main()
