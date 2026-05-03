#!/usr/bin/env python3
"""ChainSight dashboard server with proper CSP headers."""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CSPHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Content-Security-Policy',
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "http://192.168.133.238:8080 "
            "https://cdnjs.cloudflare.com "
            "https://cdn.jsdelivr.net; "
            "connect-src *;"
        )
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        pass  # Suppress access logs

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("ChainSight dashboard: http://0.0.0.0:3000")
HTTPServer(('0.0.0.0', 3000), CSPHandler).serve_forever()
