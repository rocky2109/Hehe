import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import asyncio
from bot import run_bot  # ✅ This will work now

def start_dummy_server():
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            # ✅ FIX: Encode emoji text to bytes
            self.wfile.write("🤖 Telegram Bot is running on Render!".encode("utf-8"))

    port = 10000
    print(f"🌐 Dummy HTTP server running on port {port}")
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=start_dummy_server).start()
    asyncio.run(run_bot())
