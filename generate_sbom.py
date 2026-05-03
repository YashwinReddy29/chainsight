#!/usr/bin/env python3
"""
Standalone SBOM Generator for ChainSight
Generates CycloneDX SBOM and checks for CVEs using OSV.dev API
"""

import json
import sys
from datetime import datetime
from typing import List, Dict, Any
import urllib.request
import urllib.error

# Bob's training cutoff date
BOB_TRAINING_CUTOFF = "2024-11-01"

def check_cve_osv(package_name: str, version: str, ecosystem: str) -> List[Dict[str, Any]]:
    """Query OSV.dev for CVEs"""
    url = "https://api.osv.dev/v1/query"
    
    payload = {
        "package": {
            "name": package_name,
            "ecosystem": ecosystem
        }
    }
    
    if version:
        payload["version"] = version
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('vulns', [])
    
    except urllib.error.URLError as e:
        print(f"Warning: Could not check CVEs for {package_name}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Error checking CVEs for {package_name}: {e}", file=sys.stderr)
        return []

def get_license_pypi(package_name: str) -> str:
    """Get license from PyPI"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            license_info = data.get('info', {}).get('license', 'UNKNOWN')
            return license_info if license_info else 'UNKNOWN'
    except Exception as e:
        print(f"Warning: Could not get license for {package_name}: {e}", file=sys.stderr)
        return 'UNKNOWN'

def analyze_dependencies(packages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Analyze dependencies for CVEs and licenses"""
    
    results = {
        'total_packages': len(packages),
        'cves_found': 0,
        'cve_severity': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'UNKNOWN': 0},
        'bob_blind_spots': 0,
        'license_issues': 0,
        'packages': []
    }
    
    for pkg in packages:
        name = pkg['name']
        version = pkg.get('version', '')
        ecosystem = pkg.get('ecosystem', 'PyPI')
        
        print(f"\nAnalyzing {name}=={version} ({ecosystem})...")
        
        # Check CVEs
        vulns = check_cve_osv(name, version, ecosystem)
        
        # Get license
        license_id = 'UNKNOWN'
        if ecosystem == 'PyPI':
            license_id = get_license_pypi(name)
        
        pkg_result = {
            'name': name,
            'version': version,
            'ecosystem': ecosystem,
            'license': license_id,
            'vulnerabilities': []
        }
        
        for vuln in vulns:
            vuln_id = vuln.get('id', 'UNKNOWN')
            published = vuln.get('published', '')
            severity = 'UNKNOWN'
            
            # Extract severity
            if 'severity' in vuln:
                if isinstance(vuln['severity'], list) and len(vuln['severity']) > 0:
                    severity = vuln['severity'][0].get('type', 'UNKNOWN')
            elif 'database_specific' in vuln:
                severity = vuln['database_specific'].get('severity', 'UNKNOWN')
            
            # Check if Bob blind spot
            is_blind_spot = published > BOB_TRAINING_CUTOFF if published else False
            
            pkg_result['vulnerabilities'].append({
                'id': vuln_id,
                'severity': severity,
                'published': published,
                'bob_blind_spot': is_blind_spot
            })
            
            results['cves_found'] += 1
            results['cve_severity'][severity] = results['cve_severity'].get(severity, 0) + 1
            
            if is_blind_spot:
                results['bob_blind_spots'] += 1
        
        # Check for license issues (GPL, AGPL, proprietary)
        if any(x in license_id.upper() for x in ['GPL', 'AGPL', 'PROPRIETARY']):
            results['license_issues'] += 1
        
        results['packages'].append(pkg_result)
    
    return results

def generate_cyclonedx_sbom(packages: List[Dict[str, str]], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate CycloneDX SBOM"""
    
    components = []
    for pkg_data in analysis['packages']:
        component = {
            'type': 'library',
            'name': pkg_data['name'],
            'version': pkg_data['version'],
            'purl': f"pkg:{pkg_data['ecosystem'].lower()}/{pkg_data['name']}@{pkg_data['version']}",
        }
        
        if pkg_data['license'] != 'UNKNOWN':
            component['licenses'] = [{'license': {'id': pkg_data['license']}}]
        
        components.append(component)
    
    sbom = {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.4',
        'version': 1,
        'metadata': {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'tools': [{
                'name': 'ChainSight SBOM Generator',
                'version': '1.0.0'
            }],
            'component': {
                'type': 'application',
                'name': 'health-check-service',
                'version': '1.0.0'
            }
        },
        'components': components
    }
    
    return sbom

def main():
    # Dependencies from this session
    packages = [
        {'name': 'httpx', 'version': '0.27.0', 'ecosystem': 'PyPI'},
        {'name': 'pydantic', 'version': '2.7.1', 'ecosystem': 'PyPI'}
    ]
    
    print("="*70)
    print("ChainSight SBOM Pipeline")
    print("="*70)
    
    # Analyze dependencies
    analysis = analyze_dependencies(packages)
    
    # Generate SBOM
    sbom = generate_cyclonedx_sbom(packages, analysis)
    
    # Save SBOM
    session_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    sbom_file = f'sbom_{session_id}.json'
    
    with open(sbom_file, 'w') as f:
        json.dump(sbom, f, indent=2)
    
    # Determine compliance posture
    compliance = 'PASS'
    if analysis['cves_found'] > 0:
        if analysis['cve_severity']['CRITICAL'] > 0:
            compliance = 'FAIL'
        elif analysis['cve_severity']['HIGH'] > 0:
            compliance = 'WARN'
    
    # Print summary
    print("\n" + "="*70)
    print("---SBOM SUMMARY---")
    print(f"Session ID: {session_id}")
    print(f"Total dependencies: {analysis['total_packages']}")
    print(f"CVEs found: {analysis['cves_found']} (CRITICAL: {analysis['cve_severity']['CRITICAL']}, HIGH: {analysis['cve_severity']['HIGH']}, MEDIUM: {analysis['cve_severity']['MEDIUM']}, LOW: {analysis['cve_severity']['LOW']})")
    print(f"Bob blind spots: {analysis['bob_blind_spots']} CVEs unknown at generation time")
    print(f"License issues: {analysis['license_issues']}")
    print(f"Compliance posture: {compliance}")
    print(f"SBOM saved to: ./{sbom_file}")
    print("---END---")
    print("="*70)
    
    # Print detailed findings
    print("\nDetailed Findings:")
    for pkg in analysis['packages']:
        print(f"\n{pkg['name']}=={pkg['version']} ({pkg['ecosystem']})")
        print(f"  License: {pkg['license']}")
        if pkg['vulnerabilities']:
            print(f"  Vulnerabilities: {len(pkg['vulnerabilities'])}")
            for vuln in pkg['vulnerabilities']:
                blind_spot_marker = " [BOB BLIND SPOT]" if vuln['bob_blind_spot'] else ""
                print(f"    - {vuln['id']} ({vuln['severity']}) published: {vuln['published']}{blind_spot_marker}")
        else:
            print("  Vulnerabilities: None found")

if __name__ == '__main__':
    main()

# Made with Bob
