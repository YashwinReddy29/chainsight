"""
auto_fix.py
When blind spots are detected, automatically generates:
1. Fixed requirements.txt with safe package versions
2. A git patch file with the upgrades
3. A remediation report explaining each fix
Uses OSV.dev to find the fixed version, then generates the fix.
"""

import json
import urllib.request
from datetime import datetime, timezone


def get_fixed_version(package_name: str, ecosystem: str, vuln_id: str) -> str:
    """Query OSV for the fixed version of a vulnerable package."""
    try:
        body = json.dumps({
            'package': {'name': package_name, 'ecosystem': ecosystem}
        }).encode()
        req = urllib.request.Request(
            'https://api.osv.dev/v1/query',
            data=body,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        for vuln in data.get('vulns', []):
            if vuln.get('id') == vuln_id or vuln_id in vuln.get('aliases', []):
                for affected in vuln.get('affected', []):
                    for rng in affected.get('ranges', []):
                        for event in rng.get('events', []):
                            if event.get('fixed'):
                                return event['fixed']
    except Exception:
        pass
    return None


def get_latest_safe_version(package_name: str, ecosystem: str) -> str:
    """Get the latest version of a package from PyPI or npm."""
    try:
        if ecosystem == 'PyPI':
            url = f'https://pypi.org/pypi/{package_name}/json'
            with urllib.request.urlopen(url, timeout=8) as r:
                data = json.loads(r.read())
            return data['info']['version']
        if ecosystem == 'npm':
            enc = package_name.replace('/', '%2F')
            url = f'https://registry.npmjs.org/{enc}/latest'
            with urllib.request.urlopen(url, timeout=8) as r:
                data = json.loads(r.read())
            return data.get('version', '')
    except Exception:
        pass
    return None


def generate_fixes(session_data: dict) -> dict:
    """
    Given SBOM session data, generate fix recommendations
    and a patched requirements.txt content.
    """
    fixes = []
    unfixable = []

    components = session_data.get('components', [])
    vulnerabilities = session_data.get('vulnerabilities', [])

    # Build map of package -> blind spot vulns
    blind_map = {}
    for vuln in vulnerabilities:
        props = {p['name']: p['value'] for p in vuln.get('properties', [])}
        if props.get('chainsight:post-training-cutoff') == 'true':
            for affected in vuln.get('affects', []):
                ref = affected.get('ref', '')
                pkg_name = ref.split('@')[0] if '@' in ref else ref
                if pkg_name not in blind_map:
                    blind_map[pkg_name] = []
                blind_map[pkg_name].append({
                    'id': vuln['id'],
                    'description': vuln.get('description', ''),
                    'recommendation': vuln.get('recommendation', ''),
                    'days_after_cutoff': int(props.get('chainsight:days-after-cutoff', 0))
                })

    # Generate fixes for each affected package
    for pkg_name, vulns in blind_map.items():
        # Find current version
        current_version = 'unknown'
        ecosystem = 'PyPI'
        for comp in components:
            if comp.get('name') == pkg_name:
                current_version = comp.get('version', 'unknown')
                props = {p['name']: p['value'] for p in comp.get('properties', [])}
                ecosystem = props.get('chainsight:ecosystem', 'PyPI')
                break

        # Try to find fix version from recommendation first
        fix_version = None
        for vuln in vulns:
            if vuln['recommendation']:
                import re
                m = re.search(r'(\d+\.\d+[\.\d]*)', vuln['recommendation'])
                if m:
                    fix_version = m.group(1)
                    break

        # Fall back to getting fixed version from OSV
        if not fix_version and vulns:
            fix_version = get_fixed_version(pkg_name, ecosystem, vulns[0]['id'])

        # Fall back to latest version
        if not fix_version:
            fix_version = get_latest_safe_version(pkg_name, ecosystem)

        if fix_version:
            fixes.append({
                'package': pkg_name,
                'current_version': current_version,
                'fixed_version': fix_version,
                'ecosystem': ecosystem,
                'vulns_fixed': [v['id'] for v in vulns],
                'days_after_cutoff': max(v['days_after_cutoff'] for v in vulns),
                'action': f'Upgrade {pkg_name} from {current_version} to {fix_version}'
            })
        else:
            unfixable.append({
                'package': pkg_name,
                'current_version': current_version,
                'ecosystem': ecosystem,
                'vulns': [v['id'] for v in vulns],
                'action': f'No automated fix available for {pkg_name} — manual review required'
            })

    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'fixes': fixes,
        'unfixable': unfixable,
        'total_fixes': len(fixes),
        'total_unfixable': len(unfixable),
        'auto_fixable': len(fixes) > 0
    }


def generate_fixed_requirements(original_req_content: str, fixes: list) -> str:
    """
    Apply fixes to a requirements.txt content string.
    Returns the patched requirements.txt content.
    """
    lines = original_req_content.split('\n')
    fix_map = {f['package'].lower(): f['fixed_version'] for f in fixes}
    output_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            output_lines.append(line)
            continue

        import re
        m = re.match(r'^([\w.-]+)==([\d.]+)(.*)', stripped)
        if m:
            pkg = m.group(1)
            old_ver = m.group(2)
            rest = m.group(3)
            if pkg.lower() in fix_map:
                new_ver = fix_map[pkg.lower()]
                output_lines.append(f'{pkg}=={new_ver}{rest}  # ChainSight: upgraded from {old_ver} — Bob blind spot fix')
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)

    return '\n'.join(output_lines)


def generate_remediation_report(session_id: str, fixes_data: dict) -> str:
    """Generate a markdown remediation report."""
    lines = [
        f"# ChainSight Auto-Fix Remediation Report",
        f"",
        f"**Session:** `{session_id}`",
        f"**Generated:** {fixes_data['timestamp']}",
        f"**Auto-fixable:** {fixes_data['total_fixes']} packages",
        f"**Manual review needed:** {fixes_data['total_unfixable']} packages",
        f"",
        f"## Automated Fixes",
        f"",
        f"These packages had Bob blind spots and have been automatically upgraded:",
        f"",
    ]

    for fix in fixes_data['fixes']:
        lines += [
            f"### `{fix['package']}`",
            f"- **Current version:** `{fix['current_version']}`",
            f"- **Fixed version:** `{fix['fixed_version']}`",
            f"- **CVEs resolved:** {', '.join(fix['vulns_fixed'])}",
            f"- **Urgency:** {fix['days_after_cutoff']} days after Bob training cutoff",
            f"- **Action:** `pip install {fix['package']}=={fix['fixed_version']}`",
            f"",
        ]

    if fixes_data['unfixable']:
        lines += [f"## Manual Review Required", f""]
        for u in fixes_data['unfixable']:
            lines += [
                f"### `{u['package']}`",
                f"- **Current version:** `{u['current_version']}`",
                f"- **CVEs:** {', '.join(u['vulns'])}",
                f"- **Action:** Manual security review required",
                f"",
            ]

    lines += [
        f"## How to Apply",
        f"",
        f"```bash",
        f"# Apply all fixes at once",
    ]
    for fix in fixes_data['fixes']:
        lines.append(f"pip install {fix['package']}=={fix['fixed_version']}")
    lines += [
        f"```",
        f"",
        f"---",
        f"*Generated by ChainSight — IBM Bob Supply Chain Security Scanner*",
    ]

    return '\n'.join(lines)
