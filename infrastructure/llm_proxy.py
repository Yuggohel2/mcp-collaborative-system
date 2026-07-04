import http.server
import socketserver
import json
import os
import time
from pathlib import Path
from typing import Any

PORT = 9999
USER_DIR = Path.home()
OPENHANDS_DIR = USER_DIR / ".openhands"
REQUEST_FILE = OPENHANDS_DIR / "llm_request.json"
RESPONSE_FILE = OPENHANDS_DIR / "llm_response.json"

def safe_write_json(file_path: Path, data: Any):
    """Write JSON file with safety retries to prevent Windows locking/access errors."""
    for i in range(5):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return
        except (PermissionError, IOError):
            time.sleep(0.1)
    raise IOError(f"Failed to write file {file_path} after multiple retries.")

def safe_read_json(file_path: Path) -> Any:
    """Read JSON file with safety retries to prevent Windows locking/access errors."""
    for i in range(5):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (PermissionError, IOError, json.JSONDecodeError):
            time.sleep(0.1)
    raise IOError(f"Failed to read file {file_path} after multiple retries.")

def safe_unlink(file_path: Path):
    """Delete a file with safety retries to prevent Windows locking/access errors."""
    if not file_path.exists():
        return
    for i in range(5):
        try:
            file_path.unlink()
            return
        except (PermissionError, IOError):
            time.sleep(0.1)

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
            
            # Clean up old files if they exist to prevent reading stale requests
            safe_unlink(REQUEST_FILE)
            safe_unlink(RESPONSE_FILE)

            # Save request to file safely
            try:
                safe_write_json(REQUEST_FILE, payload)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Failed to write request file: {e}".encode())
                return
            
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
                        response_data = safe_read_json(RESPONSE_FILE)
                        safe_unlink(RESPONSE_FILE)
                        break
                    except Exception:
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
    port = int(os.getenv("LLM_PROXY_PORT", PORT))
    
    # Clean up any leftover files on startup
    safe_unlink(REQUEST_FILE)
    safe_unlink(RESPONSE_FILE)
    
    while True:
        try:
            with socketserver.TCPServer(("0.0.0.0", port), LLMProxyHandler) as httpd:
                print(f"[Proxy] LLM Local Proxy Server running on port {port}...")
                httpd.serve_forever()
            break
        except OSError as e:
            # Check for "Address already in use" errors (98 on Unix, 10048 on Windows)
            if e.errno in (98, 10048):
                print(f"[Proxy] Port {port} is busy. Trying {port - 1}...")
                port -= 1
                if port < 1024:
                    print("[Proxy] Error: No available ports found above 1024.")
                    break
            else:
                print(f"[Proxy] Server error binding to port {port}: {e}")
                break

if __name__ == "__main__":
    run_server()
