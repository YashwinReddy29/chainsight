# ChainSight — AI-Generated Code Supply Chain Security

> **The first SBOM tool designed specifically for IBM Bob and AI-generated code.**

[![IBM Bob](https://img.shields.io/badge/IBM-Bob%201.0-purple)](https://bob.ibm.com)
[![watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-green)](https://dataplatform.cloud.ibm.com)
[![CycloneDX](https://img.shields.io/badge/SBOM-CycloneDX%201.6-blue)](https://cyclonedx.org)
[![EU CRA](https://img.shields.io/badge/EU%20CRA-August%202%2C%202026-red)](https://eur-lex.europa.eu)

---

## The Problem

When IBM Bob generates code, it draws from training data with a **cutoff of November 1, 2024**. CVEs published after that date are completely invisible to Bob — it will suggest vulnerable packages it has no way of knowing are compromised. These are **Bob blind spots**.

Meanwhile:
- **US Executive Order 14028** requires SBOMs for federal software
- **EU Cyber Resilience Act** mandates SBOM compliance — **deadline August 2, 2026**
- Zero tooling exists for AI-generated code specifically

---

## The Solution

ChainSight intercepts every Bob IDE session and automatically:

1. Forces exact version pins via custom Bob mode
2. Extracts all dependencies via MCP tools
3. Scans for CVEs in real time via OSV.dev
4. Detects Bob blind spots (CVEs unknown at generation time)
5. Classifies AI code provenance via IBM Granite (watsonx.ai)
6. Generates a signed CycloneDX 1.6 SBOM
7. Saves to Cloudant audit trail
8. Routes findings via watsonx Orchestrate Risk Router
9. Blocks git commits with blind spots automatically

---

## ArchitectureDeveloper
│
▼
┌─────────────────────────────────────────────┐
│           IBM Bob IDE (VS Code)             │
│  ChainSight Security Auditor Mode           │
│  → Forces exact version pins               │
│  → Outputs DEPENDENCIES block              │
│  → /sbom slash command                     │
└──────────────────────┬──────────────────────┘
│
▼
┌─────────────────────────────────────────────┐
│           MCP Server (Node.js)              │
│  extract_dependencies → parse code         │
│  check_cve          → OSV.dev API          │
│  classify_license   → PyPI/npm registry    │
│  score_freshness    → Bob blind detector   │
└──────────────────────┬──────────────────────┘
│
▼
┌─────────────────────────────────────────────┐
│         SBOM Engine (Python/FastAPI)        │
│  provenance_classifier → watsonx.ai LLaMA  │
│  cyclonedx_generator  → CycloneDX 1.6      │
│  sbom_attestor        → HMAC-SHA256 sign   │
│  auto_fix             → OSV fix versions   │
│  pdf_report           → EU CRA PDF         │
│  sbom_diff            → session comparison │
└──────┬──────────────────────┬───────────────┘
│                      │
▼                      ▼
┌─────────────┐    ┌─────────────────────────┐
│  Cloudant   │    │   watsonx Orchestrate   │
│  Audit Trail│    │   Risk Router Agent     │
│  (IBM Cloud)│    │   PASS → log            │
└─────────────┘    │   WARN → PR comment     │
│   FAIL → BLOCK PR       │
│   BLIND → Alert team    │
└─────────────────────────┘
│
▼
┌───────────────────────────────┐
│   ChainSight Dashboard        │
│   Posture timeline            │
│   Blind spot charts           │
│   SBOM diff panel             │
│   Dependency graph            │
│   Auto-fix recommendations    │
└───────────────────────────────┘

---

## 15 Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | Bob custom mode | Forces DEPENDENCIES block + exact version pins |
| 2 | /sbom slash command | One command triggers full pipeline |
| 3 | MCP server | 4 live tools: CVE, license, freshness, SBOM |
| 4 | Bob blind spot detector | CVEs unknown at Bob generation time |
| 5 | CycloneDX 1.6 SBOM | EU CRA + US EO-14028 compliant |
| 6 | watsonx.ai provenance | LLaMA 3.3 70B live AI code classification |
| 7 | Cloudant audit trail | Immutable session history |
| 8 | watsonx Orchestrate | Risk Router — BOB BLIND SPOT DETECTED |
| 9 | Dashboard + charts | Posture timeline, severity breakdown |
| 10 | SBOM diff engine | What Bob introduced between sessions |
| 11 | Git pre-commit hook | Blocks commits with blind spots + EU CRA cite |
| 12 | Auto-fix generator | Exact upgrade path from OSV.dev |
| 13 | PDF compliance report | 2-page EU CRA audit document |
| 14 | Multi-repo org scanner | Scans entire org for blind spots |
| 15 | SBOM attestation | HMAC-SHA256 cryptographic signing |

---

## IBM Products Used

| Product | Role |
|---------|------|
| **IBM Bob IDE** | Core AI development partner — generates all code |
| **watsonx.ai (LLaMA 3.3 70B)** | AI provenance classification engine |
| **watsonx Orchestrate** | Risk Router agent — routes PASS/WARN/FAIL |
| **IBM Cloudant** | Immutable SBOM audit trail |

---

## Quick Start

```bash
# Start all services
bash start-all.sh

# Dashboard: http://localhost:3000
# SBOM Engine: http://localhost:8080
# Dependency Graph: http://localhost:3000/graph.html

# In Bob IDE:
# 1. Switch to ChainSight Security Auditor mode
# 2. Generate any code with external packages
# 3. Type /sbom
# 4. Watch the pipeline run
```

---

## API Reference
GET  /health                    Health check
POST /generate                  Generate CycloneDX SBOM
GET  /sessions                  All audit sessions
GET  /session/{id}              Session SBOM
GET  /diff/{old}/{new}          SBOM diff between sessions
GET  /diff/latest               Smart diff (most interesting pair)
GET  /fix/{id}                  Auto-fix recommendations
GET  /fix/{id}/report           Markdown remediation report
GET  /report/{id}/pdf           PDF compliance report download
GET  /verify/{id}               Verify SBOM cryptographic attestation
GET  /policy/{id}?policy=commercial  License policy check
GET  /policies                  List available license policies

---

## The Bob Blind Spot
Training cutoff: 2024-11-01
Today:           2026-05-03
Gap:             548 days
CVEs published in those 548 days:

Bob has never seen them
Bob cannot warn about them
Bob will suggest vulnerable packages confidently

ChainSight catches them. All of them.

---

## Regulatory Compliance

- **US EO-14028** — SBOM requirement for federal software ✓
- **EU Cyber Resilience Act Article 13** — SBOM + vulnerability handling ✓
- **EU AI Act Article 11** — Technical documentation for AI systems ✓
- **SPDX 3.0 AI Profile** — AI-extended SBOM fields aligned ✓

---

*Built at IBM Bob Dev Day Hackathon 2026 | Team: Yashwin Reddy*
*GitHub: https://github.com/YashwinReddy29/chainsight*
