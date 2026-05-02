import uuid
from datetime import datetime, timezone

def generate_sbom(session_id, dependencies, cve_results, license_results, provenance_results, freshness_results):
    cve_map = {r.get('package', r.get('name', '')): r for r in cve_results if r}
    license_map = {r.get('name', ''): r for r in license_results if r}
    prov_map = {p.get('package', ''): p for p in provenance_results if p}

    freshness_map = {}
    if isinstance(freshness_results, list):
        for item in freshness_results:
            if item and item.get('id'):
                freshness_map[item['id']] = item
    elif isinstance(freshness_results, dict) and 'results' in freshness_results:
        for item in freshness_results['results']:
            if item and item.get('id'):
                freshness_map[item['id']] = item

    components = []
    vulnerabilities = []

    for dep in dependencies:
        name = dep.get('name', '')
        version = dep.get('version', 'unknown')
        ecosystem = dep.get('ecosystem', 'unknown')
        if not name:
            continue

        cve_data = cve_map.get(name, {})
        lic_data = license_map.get(name, {})
        prov_data = prov_map.get(name, {})

        post_cutoff_count = 0
        freshness_risk = 'NONE'
        for cve in cve_data.get('cves', []):
            fresh = freshness_map.get(cve['id'], {})
            if fresh.get('is_bob_blind_spot'):
                post_cutoff_count += 1
                if fresh.get('freshness_risk') == 'CRITICAL':
                    freshness_risk = 'CRITICAL'
                elif fresh.get('freshness_risk') == 'HIGH' and freshness_risk != 'CRITICAL':
                    freshness_risk = 'HIGH'

        component = {
            'type': 'library',
            'bom-ref': f'{name}@{version}',
            'name': name,
            'version': version if version not in ('unknown', None) else None,
            'purl': build_purl(name, version, ecosystem),
            'licenses': [{'license': {'id': lic_data.get('spdx_id', 'NOASSERTION')}}],
            'properties': [
                {'name': 'chainsight:ecosystem', 'value': ecosystem},
                {'name': 'chainsight:ai-generated', 'value': 'true'},
                {'name': 'chainsight:ai-tool', 'value': 'IBM Bob'},
                {'name': 'chainsight:session-id', 'value': session_id},
                {'name': 'chainsight:cve-count', 'value': str(cve_data.get('cve_count', 0))},
                {'name': 'chainsight:severity', 'value': cve_data.get('severity', 'NONE')},
                {'name': 'chainsight:freshness-risk', 'value': freshness_risk},
                {'name': 'chainsight:post-cutoff-cves', 'value': str(post_cutoff_count)},
                {'name': 'chainsight:provenance-confidence', 'value': str(prov_data.get('overall_provenance_confidence', 0.0))},
                {'name': 'chainsight:provenance-summary', 'value': str(prov_data.get('summary', 'Not classified'))[:200]},
                {'name': 'ai:generation-method', 'value': 'AI-assisted (IBM Bob)'},
                {'name': 'ai:training-cutoff', 'value': '2024-11-01'},
            ]
        }
        component = {k: v for k, v in component.items() if v is not None}
        components.append(component)

        for cve in cve_data.get('cves', []):
            fresh = freshness_map.get(cve['id'], {})
            is_blind = fresh.get('is_bob_blind_spot', False)
            vuln = {
                'bom-ref': f'vuln-{cve["id"]}-{name}',
                'id': cve['id'],
                'source': {'name': 'OSV', 'url': f'https://osv.dev/vulnerability/{cve["id"]}'},
                'description': cve.get('summary', '')[:300],
                'published': cve.get('published', ''),
                'affects': [{'ref': f'{name}@{version}'}],
                'properties': [
                    {'name': 'chainsight:post-training-cutoff', 'value': str(is_blind).lower()},
                    {'name': 'chainsight:days-after-cutoff', 'value': str(fresh.get('days_after_cutoff', 0))},
                    {'name': 'chainsight:bob-awareness', 'value': 'UNKNOWN_AT_GENERATION' if is_blind else 'KNOWN_AT_GENERATION'},
                    {'name': 'chainsight:freshness-risk', 'value': fresh.get('freshness_risk', 'UNKNOWN')},
                    {'name': 'chainsight:message', 'value': fresh.get('message', '')[:300]},
                ]
            }
            if cve.get('fixed_in'):
                vuln['recommendation'] = f'Upgrade {name} to {cve["fixed_in"]} or later'
            vulnerabilities.append(vuln)

    return {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.6',
        'serialNumber': f'urn:uuid:{uuid.uuid4()}',
        'version': 1,
        'metadata': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tools': [
                {'vendor': 'IBM', 'name': 'Bob', 'version': '1.0'},
                {'vendor': 'ChainSight', 'name': 'ChainSight SBOM Engine', 'version': '1.0.0'}
            ],
            'properties': [
                {'name': 'chainsight:session-id', 'value': session_id},
                {'name': 'chainsight:generation-method', 'value': 'AI-assisted (IBM Bob)'},
                {'name': 'chainsight:training-cutoff', 'value': '2024-11-01'},
                {'name': 'chainsight:sbom-type', 'value': 'AI-Generated Code SBOM'},
                {'name': 'ai:tool-name', 'value': 'IBM Bob'},
                {'name': 'ai:regulation-compliance', 'value': 'EU-AI-Act-Article-11,US-EO-14028'},
            ]
        },
        'components': components,
        'vulnerabilities': vulnerabilities
    }

def build_purl(name, version, ecosystem):
    eco_map = {'PyPI':'pypi','npm':'npm','Go':'golang','Maven':'maven','Cargo':'cargo','crates.io':'cargo'}
    eco = eco_map.get(ecosystem, ecosystem.lower())
    name_enc = name.replace('/', '%2F')
    if version and version not in ('unknown', 'UNKNOWN', None):
        return f'pkg:{eco}/{name_enc}@{version}'
    return f'pkg:{eco}/{name_enc}'

def assess_posture(sbom):
    vulns = sbom.get('vulnerabilities', [])
    if not vulns:
        return 'PASS'
    for vuln in vulns:
        for prop in vuln.get('properties', []):
            if prop['name'] == 'chainsight:post-training-cutoff' and prop['value'] == 'true':
                return 'FAIL'
        for rating in vuln.get('ratings', []):
            if str(rating.get('severity', '')).lower() == 'critical':
                return 'FAIL'
    return 'WARN'
