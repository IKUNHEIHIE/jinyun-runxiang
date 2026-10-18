"""Preview immutable MasterGo exports with bundled fonts and image resources."""
import re
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/docs/mastergo/") and path.endswith(".html"):
            file = (ROOT / path.lstrip("/")).resolve()
            if ROOT / "docs" / "mastergo" not in file.parents or not file.exists():
                self.send_error(404)
                return
            html = file.read_text(encoding="utf-8")
            html = re.sub(r"https://image-resource\.mastergo\.com/[^\s\"')<>]+",
                          lambda m: "/user-web/public/design/images/" + m.group().split("/")[-1], html)
            fonts = '<style>@font-face{font-family:"Noto Sans SC";src:url("/user-web/public/design/fonts/NotoSansSC.ttf");font-weight:100 900}@font-face{font-family:"Noto Serif SC";src:url("/user-web/public/design/fonts/NotoSerifSC.ttf");font-weight:100 900}</style>'
            fonts += '<style>@font-face{font-family:"Ma Shan Zheng";src:url("/user-web/public/design/fonts/MaShanZheng.ttf")}</style>'
            body = html.replace("</head>", fonts + "</head>").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html;charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 5191), Handler).serve_forever()
