#!/bin/bash
echo "Starting ChainSight..."
export $(cat ~/chainsight/.env | grep -v '#' | xargs)

pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "http.server" 2>/dev/null
sudo fuser -k 3000/tcp 2>/dev/null
sudo fuser -k 3001/tcp 2>/dev/null
sleep 2

# Start SBOM Engine
cd ~/chainsight/sbom-engine
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080 &

# Start Dashboard with CSP headers
cd ~/chainsight/dashboard
python3 -c "
import http.server, socketserver
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Content-Security-Policy',\"default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;\")
        super().end_headers()
    def log_message(self,f,*a):pass
socketserver.TCPServer.allow_reuse_address=True
with socketserver.TCPServer(('0.0.0.0',3001),H) as s:s.serve_forever()
" &

sleep 2
echo ""
echo "ChainSight running:"
echo "  SBOM Engine:  http://192.168.133.238:8080"
echo "  Dashboard:    http://192.168.133.238:3001"
echo ""
echo "In Bob IDE: generate code then type /sbom"
