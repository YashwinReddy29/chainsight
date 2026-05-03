#!/bin/bash
# ChainSight Multi-Repo Scanner
# Scans all Python projects in a directory for Bob blind spots
# Uses Bob Shell for AI-assisted analysis of each repo

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

ENGINE_URL="${CHAINSIGHT_ENGINE:-http://192.168.133.238:8080}"
SCAN_DIR="${1:-.}"
REPORT_DIR="$HOME/chainsight/sbom-output/org-scan-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$REPORT_DIR"

echo ""
echo -e "${BOLD}ChainSight Org-Wide Scanner${NC}"
echo -e "Powered by IBM Bob + watsonx.ai"
echo "Directory: $SCAN_DIR"
echo "Report: $REPORT_DIR"
echo "─────────────────────────────────"
echo ""

TOTAL_REPOS=0
TOTAL_BLIND=0
TOTAL_CVES=0
FAIL_REPOS=()

# Find all requirements.txt files
while IFS= read -r req_file; do
    REPO_DIR=$(dirname "$req_file")
    REPO_NAME=$(basename "$REPO_DIR")
    TOTAL_REPOS=$((TOTAL_REPOS + 1))

    echo -e "  📦 Scanning: ${BOLD}$REPO_NAME${NC}"

    # Parse packages
    PACKAGES=$(python3 -c "
import re, json
packages = []
try:
    with open('$req_file') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^([\w.-]+)==([\d.]+)', line)
            if m:
                packages.append({'name': m.group(1), 'version': m.group(2), 'ecosystem': 'PyPI'})
except:
    pass
print(json.dumps(packages))
" 2>/dev/null)

    COUNT=$(echo "$PACKAGES" | python3 -c "import sys,json;print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

    if [ "$COUNT" -eq "0" ]; then
        echo -e "     ${NC}No packages found — skipping"
        continue
    fi

    # Run scan via ChainSight engine
    SESSION_ID="orgscan-${REPO_NAME}-$(date +%s)"
    RESULT=$(curl -s -X POST "$ENGINE_URL/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"session_id\": \"$SESSION_ID\",
            \"dependencies\": $PACKAGES,
            \"cve_results\": [],
            \"license_results\": [],
            \"freshness_results\": []
        }" 2>/dev/null)

    # Also check OSV directly for freshness
    BLIND_RESULT=$(echo "$PACKAGES" | python3 "$HOME/chainsight/git-hooks/blind-spot-check.py" 2>/dev/null)
    BLIND=$(echo "$BLIND_RESULT" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['blind_count'])" 2>/dev/null || echo "0")
    TOTAL_CVE=$(echo "$BLIND_RESULT" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['total'])" 2>/dev/null || echo "0")

    TOTAL_BLIND=$((TOTAL_BLIND + BLIND))
    TOTAL_CVES=$((TOTAL_CVES + TOTAL_CVE))

    if [ "$BLIND" -gt "0" ]; then
        echo -e "     ${PURPLE}${BOLD}👁 $BLIND blind spot(s) — $TOTAL_CVE CVE(s)${NC}"
        FAIL_REPOS+=("$REPO_NAME")
        # Save blind spot details
        echo "$BLIND_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for b in data['blind_spots']:
    print(f\"     → {b['id']} in {b['package']}=={b['version']} ({b['days_after']} days after cutoff)\")
" 2>/dev/null
    elif [ "$TOTAL_CVE" -gt "0" ]; then
        echo -e "     ${YELLOW}⚠  $TOTAL_CVE known CVE(s) — no blind spots${NC}"
    else
        echo -e "     ${GREEN}✓  Clean — $COUNT packages, no CVEs${NC}"
    fi

    # Save per-repo report
    echo "$BLIND_RESULT" > "$REPORT_DIR/${REPO_NAME}.json"
    echo ""

done < <(find "$SCAN_DIR" -name "requirements.txt" -not -path "*/venv/*" -not -path "*/.git/*" -not -path "*/node_modules/*" 2>/dev/null)

# Summary
echo "─────────────────────────────────"
echo -e "${BOLD}Org Scan Complete${NC}"
echo ""
echo -e "  Repos scanned:    $TOTAL_REPOS"
echo -e "  Total CVEs:       ${TOTAL_CVES}"

if [ "$TOTAL_BLIND" -gt "0" ]; then
    echo -e "  Bob blind spots:  ${RED}${BOLD}$TOTAL_BLIND${NC}"
    echo ""
    echo -e "  ${RED}${BOLD}Repos with blind spots:${NC}"
    for repo in "${FAIL_REPOS[@]}"; do
        echo -e "    ${RED}• $repo${NC}"
    done
else
    echo -e "  Bob blind spots:  ${GREEN}0${NC}"
fi

echo ""
echo -e "  Reports saved to: $REPORT_DIR"
echo ""
