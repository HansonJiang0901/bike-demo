#!/usr/bin/env python3
"""FitWheel Captive Portal Server.

Normal mode (port 8080, no root needed):
    python3 serve.py

Captive portal mode (port 80, requires root — triggers auto-popup on phones):
    sudo python3 serve.py 80
"""
import http.server, socketserver, socket, os, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
os.chdir(os.path.dirname(os.path.abspath(__file__)))

CAPTIVE_PORTAL_PROBES = {
    "/hotspot-detect.html",
    "/library/test/success.html",
    "/generate_204",
    "/gen_204",
    "/connecttest.txt",
    "/ncsi.txt",
    "/redirect",
    "/canonical.html",
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

ip = get_local_ip()
APP_URL = f"http://{ip}:{PORT}" if PORT != 80 else f"http://{ip}"

# Minimal landing page served inside the captive portal mini-browser.
PORTAL_PAGE = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FitWheel</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{
    min-height:100vh;
    background:radial-gradient(ellipse at top,#2a0000 0%,#0a0000 70%);
    color:#fff;
    font-family:-apple-system,sans-serif;
    display:flex;flex-direction:column;
    align-items:center;justify-content:center;
    padding:24px;text-align:center;
  }}
  .icon{{font-size:64px;margin-bottom:16px}}
  h1{{font-size:24px;color:#ff4444;margin-bottom:6px}}
  p{{font-size:14px;color:#a06060;margin-bottom:28px}}
  .buttons{{display:flex;gap:16px;width:100%;max-width:340px}}
  .choice{{
    flex:1;
    background:#1a0505;border:2px solid #8b1a1a;border-radius:16px;
    padding:24px 12px;text-align:center;text-decoration:none;
    color:#fff;transition:border-color .2s,box-shadow .2s;
  }}
  .choice:active{{transform:scale(.96)}}
  .choice.guest:active{{border-color:#ff6b6b;box-shadow:0 0 20px rgba(255,107,107,.3)}}
  .choice.member:active{{border-color:#ffd700;box-shadow:0 0 20px rgba(255,215,0,.3)}}
  .ch-icon{{font-size:36px;margin-bottom:10px}}
  .ch-label{{font-size:17px;font-weight:700;margin-bottom:4px}}
  .ch-desc{{font-size:12px;color:#a06060}}
</style>
</head><body>
  <div class="icon">🚴</div>
  <h1>FitWheel</h1>
  <p>選擇登入方式開始訓練</p>
  <div class="buttons">
    <a class="choice guest" href="{APP_URL}?mode=guest" target="_blank">
      <div class="ch-icon">👤</div>
      <div class="ch-label">訪客登入</div>
      <div class="ch-desc">免註冊，立即開始</div>
    </a>
    <a class="choice member" href="{APP_URL}?mode=member" target="_blank">
      <div class="ch-icon">⭐</div>
      <div class="ch-label">會員登入</div>
      <div class="ch-desc">記錄您的訓練數據</div>
    </a>
  </div>
</body></html>"""

LOCAL_FILES = {"/", "/index.html", "/favicon.ico", "/portal"}

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]

        # Captive portal probe or any unknown path → serve landing page
        if path in CAPTIVE_PORTAL_PROBES or path == "/portal":
            self._serve_portal()
            return

        # Check Host header: if the request is for a foreign domain
        # (e.g. connectivitycheck.gstatic.com), it's a captive portal probe
        host = self.headers.get("Host", "")
        if host and ip not in host and "localhost" not in host:
            self._serve_portal()
            return

        if path == "/":
            self.path = "/index.html"

        super().do_GET()

    def _serve_portal(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PORTAL_PAGE.encode())

    def log_message(self, fmt, *args):
        pass

print(f"\n  FitWheel Captive Portal Server")
print(f"  ─────────────────────────────────────")
print(f"  Local:   http://localhost:{PORT}")
print(f"  Network: {APP_URL}")

if PORT == 80:
    print(f"\n  [Captive Portal Mode]")
    print(f"  Portal mini-browser → landing page → open in Safari")
    print(f"\n  dnsmasq config:")
    print(f"     address=/captive.apple.com/{ip}")
    print(f"     address=/connectivitycheck.gstatic.com/{ip}")
    print(f"     address=/clients3.google.com/{ip}")
    print(f"     address=/www.msftconnecttest.com/{ip}")
    print(f"     address=/detectportal.firefox.com/{ip}")
    print(f"     server=8.8.8.8")
    print(f"     server=1.1.1.1")
else:
    print(f"\n  Tip: run 'sudo python3 serve.py 80' for captive portal mode")

print(f"\n  ┌──────────────────────────────────────┐")
print(f"  │  Open on phone: {APP_URL:<22} │")
print(f"  └──────────────────────────────────────┘")
print(f"\n  Press Ctrl+C to stop.\n")

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
