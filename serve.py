#!/usr/bin/env python3
"""FitWheel Captive Portal Server.

Normal mode (port 8080, no root needed):
    python3 serve.py

Captive portal mode (port 80, requires root — triggers auto-popup on phones):
    sudo python3 serve.py 80

When running on port 80 and acting as the WiFi hotspot's DNS server,
phones will automatically open the fitness page after joining the network.
"""
import http.server, socketserver, socket, os, sys, threading

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# URLs that mobile OSes use to detect captive portals.
# If the server intercepts these and redirects, the OS pops up a browser.
CAPTIVE_PORTAL_PROBES = {
    # iOS / macOS
    "/hotspot-detect.html",
    "/library/test/success.html",
    # Android
    "/generate_204",
    "/gen_204",
    "/connecttest.txt",       # Windows
    "/ncsi.txt",              # Windows
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

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Strip query string for matching
        path = self.path.split("?")[0]

        # Intercept captive portal probes → redirect to app (skip WiFi screen)
        if path in CAPTIVE_PORTAL_PROBES:
            self.send_response(302)
            self.send_header("Location", APP_URL + "?portal=1")
            self.end_headers()
            return

        # Serve index.html for root
        if path == "/":
            self.path = "/index.html"

        super().do_GET()

    def log_message(self, fmt, *args):
        pass  # suppress access log noise

print(f"\n  FitWheel Captive Portal Server")
print(f"  ─────────────────────────────────────")
print(f"  Local:   http://localhost:{PORT}")
print(f"  Network: {APP_URL}")

if PORT == 80:
    print(f"\n  [Captive Portal Mode]")
    print(f"  Phones will auto-open the app after joining WiFi.")
    print(f"\n  Required network setup:")
    print(f"  1. This machine must be the WiFi hotspot (with internet sharing)")
    print(f"  2. dnsmasq config — only intercept captive portal domains:")
    print(f"     ─────────────────────────────────────")
    print(f"     # Captive portal detection domains")
    print(f"     address=/captive.apple.com/{ip}")
    print(f"     address=/connectivitycheck.gstatic.com/{ip}")
    print(f"     address=/www.msftconnecttest.com/{ip}")
    print(f"     address=/nmcheck.gnome.org/{ip}")
    print(f"     address=/detectportal.firefox.com/{ip}")
    print(f"     # Use real DNS for everything else (YouTube etc)")
    print(f"     server=8.8.8.8")
    print(f"     server=1.1.1.1")
    print(f"     ─────────────────────────────────────")
else:
    print(f"\n  Tip: run with 'sudo python3 serve.py 80' for captive portal mode")

print(f"\n  ┌──────────────────────────────────────┐")
print(f"  │  Open on phone: {APP_URL:<22} │")
print(f"  └──────────────────────────────────────┘")
print(f"\n  Press Ctrl+C to stop.\n")

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
