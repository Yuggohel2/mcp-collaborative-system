import http.server
import socketserver
import json
import os
import time
from pathlib import Path

PORT = 9999
USER_DIR = Path.home()
OPENHANDS_DIR = USER_DIR / ".openhands"
REQUEST_FILE = OPENHANDS_DIR / "llm_request.json"
RESPONSE_FILE = OPENHANDS_DIR / "llm_response.json"

class LLMProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging to keep terminal clean
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        if self.path in ("/v1/chat/completions", "/chat/completions"):
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                print(f"\n[Proxy] Received LLM request for model: {payload.get('model')}")
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"Invalid JSON: {e}".encode())
                return

            # Ensure directory exists
            OPENHANDS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Clean up old files if they exist
            if REQUEST_FILE.exists():
                REQUEST_FILE.unlink()
            if RESPONSE_FILE.exists():
                RESPONSE_FILE.unlink()

            # Save request to file
            with open(REQUEST_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            
            print(f"[Proxy] Saved request to {REQUEST_FILE}. Waiting for orchestrator response...")

            # Wait for response file
            timeout = 180  # 3 minutes timeout
            start_time = time.time()
            response_data = None
            
            while time.time() - start_time < timeout:
                if RESPONSE_FILE.exists():
                    try:
                        # Add a tiny delay to ensure file write is completed by orchestrator
                        time.sleep(0.1)
                        with open(RESPONSE_FILE, "r", encoding="utf-8") as f:
                            response_data = json.load(f)
                        RESPONSE_FILE.unlink()
                        break
                    except Exception as e:
                        time.sleep(0.2)
                time.sleep(0.5)

            if response_data:
                print("[Proxy] Received response from orchestrator. Sending to OpenHands.")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            else:
                print("[Proxy] Timeout waiting for orchestrator response.")
                self.send_response(504)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                error_resp = {
                    "error": {
                        "message": "Gateway Timeout: Orchestrator agent did not respond in time.",
                        "type": "gateway_timeout",
                        "code": 504
                    }
                }
                self.wfile.write(json.dumps(error_resp).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    # Allow address reuse to prevent "Address already in use" errors on restarts
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), LLMProxyHandler) as httpd:
        print(f"[Proxy] LLM Local Proxy Server running on port {PORT}...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[Proxy] Server stopping...")

if __name__ == "__main__":
    run_server()
