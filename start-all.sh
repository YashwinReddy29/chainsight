#!/bin/bash
echo ""
echo "  Starting ChainSight v7.0..."
echo ""

export $(cat ~/chainsight/.env | grep -v '#' | grep -v '^$' | xargs)

pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "http.server 3000" 2>/dev/null
sleep 1

cd ~/chainsight/sbom-engine
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080 &

cd ~/chainsight/dashboard
python3 -m http.server 3000 &

sleep 3

echo "  ✓ SBOM Engine:      http://192.168.133.238:8080"
echo "  ✓ Dashboard:        http://192.168.133.238:3000"
echo "  ✓ Dependency Graph: http://192.168.133.238:3000/graph.html"
echo ""
echo "  In Bob IDE:"
echo "  1. Switch to ChainSight Security Auditor mode"
echo "  2. Generate any code with external packages"
echo "  3. Type /sbom"
echo ""
echo "  ChainSight ready."
echo ""
