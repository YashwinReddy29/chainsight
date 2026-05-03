#!/bin/bash
echo "Starting ChainSight..."
export $(cat ~/chainsight/.env | grep -v '#' | xargs)
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "http.server 3000" 2>/dev/null
sleep 1
cd ~/chainsight/sbom-engine
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080 &
cd ~/chainsight/dashboard
python3 -m http.server 3000 &
sleep 2
echo ""
echo "ChainSight running:"
echo "  SBOM Engine: http://192.168.133.238:8080"
echo "  Dashboard:   http://localhost:3000"
echo ""
echo "In Bob IDE: generate code then type /sbom"
