# ChainSight SBOM Generator Skill
## Description
Triggers the full ChainSight supply chain security pipeline after any code generatio
Produces a CycloneDX 1.6 SBOM with CVE analysis, license classification, and AI prov
## When to run
After any Bob session that generates code with external package dependencies.
## Steps
1. Parse the conversation for all DEPENDENCIES blocks and import statements
2. Deduplicate the package list
3. Call check_cve for batch CVE lookup via OSV.dev
4. Call classify_license for each package
5. Call score_freshness with all CVE IDs to find Bob blind spots
6. Call sbom_generate with all data to produce the CycloneDX JSON
7. Save to ./sbom-output/
8. Return the SBOM summary
## Output format
Always return the full summary block including posture (PASS/WARN/FAIL).
Always mention how many CVEs were unknown to Bob at generation time.
