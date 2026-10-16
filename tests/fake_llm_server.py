"""A stand-in OpenAI-compatible chat server (like Groq/OpenRouter) for offline tests."""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

LOG = []


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        LOG.append(body)
        if self.headers.get("Authorization") != "Bearer good-key":
            self.send_response(401); self.end_headers(); self.wfile.write(b'{"error":"bad key"}'); return
        if body["model"] == "slow-model":
            import time
            time.sleep(3)
        if body["model"] == "gone-model":
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"error":"model not found"}'); return
        if body["model"] == "busy-model":
            self.send_response(429); self.end_headers(); self.wfile.write(b'{"error":"rate limit"}'); return
        last = body["messages"][-1]["content"]
        if body.get("response_format"):
            content = json.dumps({"questions": [{"question": "Which pollutant mainly causes acid rain?",
                                                  "options": ["Sulphur dioxide", "Ozone", "Argon", "Helium"],
                                                  "answer": 1, "explanation": "SO2 forms sulphuric acid in rain.",
                                                  "hint": "Think of coal power plants."}]})
        else:
            content = f"🙂 Tutor reply to: {last[:60]} | system msgs: {sum(m['role']=='system' for m in body['messages'])}"
        out = json.dumps({"choices": [{"message": {"role": "assistant", "content": content}}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(out)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
