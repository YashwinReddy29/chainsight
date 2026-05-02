---
description: Generate a CycloneDX 1.6 SBOM for all dependencies in this session
---
Run the ChainSight SBOM pipeline now.
Step 1: Extract all package dependencies from code generated in this conversation. L
Step 2: For each dependency found, call the check_cve MCP tool to query OSV.dev for
Step 3: For each dependency, call the classify_license MCP tool to get the SPDX lice
Step 4: Call the score_freshness MCP tool with all CVEs found to identify Bob blind
Step 5: Call the sbom_generate MCP tool with all collected data to produce the Cyclo
Step 6: Report back a summary in this format:
---SBOM SUMMARY---
Session ID: [id]
Total dependencies: X
CVEs found: X (CRITICAL: X, HIGH: X, MEDIUM: X, LOW: X)
Bob blind spots: X CVEs unknown at generation time
License issues: X
Compliance posture: PASS | WARN | FAIL
SBOM saved to: ./sbom-output/[id].cdx.json
---END---
