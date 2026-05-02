---
description: Generate a CycloneDX SBOM for all dependencies in this session
---

Run the ChainSight SBOM pipeline now.

Step 1: Look through this entire conversation and extract every package dependency mentioned. Check all DEPENDENCIES blocks and all import statements in code.

Step 2: For each dependency found, call the check_cve MCP tool to query OSV.dev for CVEs.

Step 3: For each dependency, call the classify_license MCP tool to get the SPDX license identifier.

Step 4: Call the score_freshness MCP tool with all CVE IDs found to identify Bob blind spots — CVEs published after your training cutoff.

Step 5: Call the sbom_generate MCP tool with all collected data.

Step 6: Report back exactly in this format:

---SBOM SUMMARY---
Session ID: [id]
Total dependencies: X
CVEs found: X (CRITICAL: X, HIGH: X, MEDIUM: X, LOW: X)
Bob blind spots: X CVEs unknown at generation time
License issues: X
Compliance posture: PASS | WARN | FAIL
SBOM saved to: ./sbom-output/[id].cdx.json
---END---
