# ChainSight — AI-Generated Code Supply Chain Security

> **The first SBOM tool designed specifically for IBM Bob and AI-generated code.**

[![IBM Bob](https://img.shields.io/badge/IBM-Bob%201.0-purple)](https://bob.ibm.com)
[![watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-green)](https://dataplatform.cloud.ibm.com)
[![Orchestrate](https://img.shields.io/badge/IBM-watsonx%20Orchestrate-orange)](https://www.ibm.com/products/watsonx-orchestrate)
[![Cloudant](https://img.shields.io/badge/IBM-Cloudant-red)](https://www.ibm.com/products/cloudant)
[![CycloneDX](https://img.shields.io/badge/SBOM-CycloneDX%201.6-blue)](https://cyclonedx.org)
[![EU CRA](https://img.shields.io/badge/EU%20CRA-August%202%2C%202026-red)](https://eur-lex.europa.eu)

---

## The Problem

When IBM Bob generates code, it draws from training data with a cutoff of **November 1, 2024**. CVEs published after that date are completely invisible to Bob — it will suggest vulnerable packages it has no way of knowing are compromised. These are **Bob blind spots**.

**Real example from this project:**
- Bob suggested `python-multipart==0.0.9`
- GHSA-wp53-j4wj-2cfg was published **451 days after Bob's training cutoff**
- Bob confidently suggested this package with no warning
- Without ChainSight, this vulnerability ships to production

Meanwhile:
- **US Executive Order 14028** requires SBOMs for federal software
- **EU Cyber Resilience Act** mandates SBOM compliance — **deadline August 2, 2026**
- Zero tooling exists for AI-generated code specifically

---

## The Solution

ChainSight intercepts every IBM Bob session and automatically:

1. Forces exact version pins via **ChainSight Security Auditor** custom Bob mode
2. Extracts all dependencies via **4 MCP tools**
3. Scans for CVEs in real time via **OSV.dev** (free, no API key)
4. Detects **Bob blind spots** — CVEs unknown at generation time
5. Classifies AI code provenance via **LLaMA 3.3 70B on watsonx.ai**
6. Generates signed **CycloneDX 1.6 SBOM** with AI extension fields
7. Saves to **IBM Cloudant** immutable audit trail
8. Routes findings via **watsonx Orchestrate** Risk Router agent
9. Blocks **git commits** with blind spots automatically
10. Generates **AI risk assessments** in plain English

---

## Demo
Bob suggests: python-multipart==0.0.9
ChainSight:   GHSA-wp53-j4wj-2cfg — published 451 days after Bob training cutoff
Bob had NO knowledge of this CVE at generation time
COMMIT BLOCKED — EU CRA Article 13
Fix: pip install python-multipart==0.0.18

---

## Architecture
IBM Bob IDE (VS Code)
│ ChainSight Security Auditor mode
│ Forces DEPENDENCIES block on every response
│ /sbom slash command
▼
MCP Server (Node.js) — 4 live tools
├── extract_dependencies  → parse code for packages
├── check_cve             → OSV.dev real-time scan
├── classify_license      → PyPI/npm registry lookup
└── score_freshness       → Bob blind spot detector
▼
SBOM Engine (Python/FastAPI) — 20 endpoints
├── provenance_classifier  → watsonx.ai LLaMA 3.3 70B
├── cyclonedx_generator    → CycloneDX 1.6 + AI fields
├── sbom_attestor          → HMAC-SHA256 signing
├── auto_fix               → OSV.dev fix versions
├── ai_risk_assessor       → watsonx.ai risk in plain English
├── pdf_report             → EU CRA compliance PDF
├── sbom_diff              → session comparison engine
├── license_policy         → blocks GPL in commercial code
├── bundle_generator       → ZIP compliance package
└── slack_notifier         → Slack webhook alerts
│
├──→ IBM Cloudant           immutable audit trail
└──→ watsonx Orchestrate    Risk Router agent
├── PASS  → log only
├── WARN  → PR comment
└── FAIL  → block PR + BOB BLIND SPOT DETECTED
Git Pre-Commit Hook
└── blocks commits with blind spots
└── cites EU CRA Article 13
Dashboard (4 pages)
├── index.html       main dashboard + compliance scoring
├── graph.html       interactive D3.js dependency graph
├── timeline.html    CVE discovery timeline
└── simulation.html  attack simulation (with vs without)

---

## IBM Products Used

| Product | How Used |
|---------|----------|
| **IBM Bob IDE** | Core AI partner — custom Security Auditor mode, /sbom slash command, 4 MCP tools, session exports |
| **watsonx.ai (LLaMA 3.3 70B)** | AI provenance classification + natural language risk assessment |
| **watsonx Orchestrate** | ChainSight Risk Router agent — routes PASS/WARN/FAIL, blocks PRs, sends BOB BLIND SPOT DETECTED alerts |
| **IBM Cloudant** | Immutable SBOM audit trail — every Bob session saved with full CycloneDX document |

---

## 20 Features Built

| # | Feature | Status |
|---|---------|--------|
| 1 | Bob custom mode (ChainSight Security Auditor) | ✅ |
| 2 | /sbom slash command | ✅ |
| 3 | MCP server — 4 live tools | ✅ |
| 4 | Bob blind spot detector | ✅ |
| 5 | CycloneDX 1.6 SBOM generation | ✅ |
| 6 | watsonx.ai LLaMA provenance classification | ✅ |
| 7 | IBM Cloudant audit trail | ✅ |
| 8 | watsonx Orchestrate Risk Router | ✅ |
| 9 | Compliance dashboard with charts | ✅ |
| 10 | SBOM diff engine | ✅ |
| 11 | Git pre-commit hook (blocks blind spots) | ✅ |
| 12 | Auto-fix generator | ✅ |
| 13 | PDF compliance report | ✅ |
| 14 | Multi-repo org scanner | ✅ |
| 15 | SBOM attestation (HMAC-SHA256) | ✅ |
| 16 | Interactive dependency graph (D3.js) | ✅ |
| 17 | License policy engine | ✅ |
| 18 | AI risk assessment (watsonx.ai) | ✅ |
| 19 | Attack simulation page | ✅ |
| 20 | Session replay + trending alerts | ✅ |

---

## Quick Start

```bash
# Clone
git clone https://github.com/YashwinReddy29/chainsight.git
cd chainsight

# Add your IBM Cloud credentials to .env
cp .env.example .env
# Fill in: WATSONX_API_KEY, WATSONX_PROJECT_ID, CLOUDANT_URL, CLOUDANT_API_KEY

# Start everything
bash start-all.sh

# Open dashboard
# http://localhost:3000
```

---

## API Reference — 20 Endpoints
GET  /health                          Health check
POST /generate                        Generate CycloneDX SBOM
GET  /sessions                        All audit sessions (Cloudant)
GET  /session/{id}                    Session SBOM
GET  /scores                          Compliance scores 0-100
GET  /heatmap                         Package risk heatmap
GET  /trends                          Trending risk alerts
POST /replay/{id}                     Re-scan vs current CVE database
GET  /diff/{old}/{new}                SBOM diff between sessions
GET  /diff/latest                     Smart diff — most interesting pair
GET  /fix/{id}                        Auto-fix recommendations
GET  /fix/{id}/report                 Markdown remediation report
GET  /report/{id}/pdf                 PDF compliance report download
GET  /bundle/{id}                     ZIP compliance bundle
GET  /verify/{id}                     Verify SBOM cryptographic attestation
GET  /assess/{id}                     AI risk assessment via watsonx.ai
GET  /policy/{id}?policy=commercial   License policy check
GET  /policies                        Available license policies
WS   /ws                              WebSocket live feed
GET  /ws/clients                      Connected dashboard clients

---

## Bob Blind Spot — The Core Innovation
Bob training cutoff:  2024-11-01
Hackathon date:       2026-05-03
Gap:                  548 days
In 548 days:

Hundreds of CVEs published
Bob suggested vulnerable packages confidently
Bob could not warn you — it never saw these CVEs

ChainSight catches them before they ship.
Every time. Automatically.

---

## Regulatory Compliance

| Regulation | Requirement | ChainSight |
|-----------|-------------|------------|
| US EO-14028 | SBOM for federal software | CycloneDX 1.6 ✅ |
| EU CRA Article 13 | SBOM + vulnerability handling | Full compliance ✅ |
| EU AI Act Article 11 | Technical documentation for AI | AI extension fields ✅ |
| SPDX 3.0 AI Profile | AI-extended SBOM fields | Aligned ✅ |

**EU CRA Deadline: August 2, 2026 — 91 days away**

---

## Repository Structure
chainsight/
├── .bob/                    Bob IDE configuration
│   ├── modes/               ChainSight Security Auditor mode
│   ├── commands/            /sbom slash command
│   └── skills/              SBOM generator skill
├── mcp-server/              Node.js MCP server (4 tools)
│   └── tools/               extract, cve, license, freshness
├── sbom-engine/             Python FastAPI (20 endpoints)
│   ├── main.py              All API endpoints
│   ├── provenance_classifier.py   watsonx.ai LLaMA
│   ├── cyclonedx_generator.py     CycloneDX 1.6
│   ├── sbom_attestor.py           HMAC-SHA256 signing
│   ├── auto_fix.py                Fix recommendations
│   ├── ai_risk_assessor.py        watsonx.ai risk assessment
│   ├── pdf_report.py              PDF generation
│   ├── sbom_diff.py               Session comparison
│   ├── license_policy.py          License enforcement
│   ├── bundle_generator.py        ZIP compliance package
│   ├── slack_notifier.py          Slack alerts
│   └── live_feed.py               WebSocket live feed
├── dashboard/               Web dashboard (4 pages)
│   ├── index.html           Main dashboard
│   ├── graph.html           Dependency graph
│   ├── timeline.html        CVE timeline
│   └── simulation.html      Attack simulation
├── git-hooks/               Pre-commit blind spot scanner
├── bob_sessions/            Bob task exports (12 sessions)
├── sbom-output/             Generated CycloneDX SBOMs
├── .github/workflows/       GitHub Actions CI/CD
├── start-all.sh             One-command startup
└── README.md                This file

---

## Built At

**IBM Bob Dev Day Hackathon 2026**
Team: Yashwin Reddy | Syracuse University
GitHub: https://github.com/YashwinReddy29/chainsight

*Powered by IBM Bob + watsonx.ai + watsonx Orchestrate + IBM Cloudant*
