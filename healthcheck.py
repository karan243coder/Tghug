"""
Optional: Simple HTTP server for health checks
Not required for worker mode, but useful for monitoring
"""

import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "telegram-image-editor",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logs


def start_health_server(port=8080):
    """Start health check server (optional)"""
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    start_health_server()