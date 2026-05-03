#!/bin/bash
echo ""
echo "  Starting ChainSight v8.0..."
echo ""

export $(cat ~/chainsight/.env | grep -v '#' | grep -v '^$' | xargs)

# Kill everything cleanly
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "dashboard/server.py" 2>/dev/null
pkill -f "http.server 3000" 2>/dev/null
fuser -k 3000/tcp 2>/dev/null
fuser -k 8080/tcp 2>/dev/null
sleep 2

# Start SBOM engine
cd ~/chainsight/sbom-engine
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080 &

# Start dashboard
cd ~/chainsight/dashboard
python3 server.py &

sleep 3

echo "  ✓ SBOM Engine:      http://192.168.133.238:8080"
echo "  ✓ Dashboard:        http://192.168.133.238:3000"
echo "  ✓ Dependency Graph: http://192.168.133.238:3000/graph.html"
echo "  ✓ Attack Sim:       http://192.168.133.238:3000/simulation.html"
echo "  ✓ CVE Timeline:     http://192.168.133.238:3000/timeline.html"
echo ""
echo "  ChainSight ready."
echo ""
