# optional dummy server for Render
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
from bot import bot

def dummy_server():
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running.")
    server = HTTPServer(('0.0.0.0', 10000), Handler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=dummy_server).start()
    bot.run()
