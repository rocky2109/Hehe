import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import asyncio
from bot import run_bot

# Start a dummy HTTP server to satisfy Render's port check
def start_dummy_server():
    port = 10000
    print(f"🌐 Starting dummy server on port {port}")
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Run both bot and dummy server
if __name__ == "__main__":
    threading.Thread(target=start_dummy_server).start()
    asyncio.run(run_bot())
