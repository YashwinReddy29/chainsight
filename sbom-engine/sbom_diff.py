"""
sbom_diff.py
Compares two CycloneDX SBOMs and shows exactly what changed between Bob sessions.
- New dependencies introduced
- New CVEs introduced
- New Bob blind spots introduced
- Packages upgraded or downgraded
- License changes
This is the "what did Bob change" report — critical for code review.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

SBOM_OUTPUT_DIR = Path('../sbom-output')


def load_sbom(session_id: str) -> dict:
    path = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
    if not path.exists():
        raise FileNotFoundError(f'SBOM not found: {session_id}')
    with open(path) as f:
        return json.load(f)


def extract_components(sbom: dict) -> dict:
    """Extract components as a dict keyed by package name."""
    components = {}
    for c in sbom.get('components', []):
        name = c.get('name', '')
        if not name:
            continue
        props = {p['name']: p['value'] for p in c.get('properties', [])}
        components[name] = {
            'name': name,
            'version': c.get('version', 'unknown'),
            'purl': c.get('purl', ''),
            'license': c['licenses'][0]['license']['id'] if c.get('licenses') else 'UNKNOWN',
            'cve_count': int(props.get('chainsight:cve-count', 0)),
            'severity': props.get('chainsight:severity', 'NONE'),
            'freshness_risk': props.get('chainsight:freshness-risk', 'NONE'),
            'post_cutoff_cves': int(props.get('chainsight:post-cutoff-cves', 0)),
            'ai_generated': props.get('chainsight:ai-generated', 'true'),
        }
    return components


def extract_vulnerabilities(sbom: dict) -> dict:
    """Extract vulnerabilities as a dict keyed by vuln ID."""
    vulns = {}
    for v in sbom.get('vulnerabilities', []):
        vid = v.get('id', '')
        if not vid:
            continue
        props = {p['name']: p['value'] for p in v.get('properties', [])}
        affects = [a.get('ref', '') for a in v.get('affects', [])]
        vulns[vid] = {
            'id': vid,
            'description': v.get('description', ''),
            'published': v.get('published', ''),
            'affects': affects,
            'recommendation': v.get('recommendation', ''),
            'post_cutoff': props.get('chainsight:post-training-cutoff', 'false') == 'true',
            'bob_awareness': props.get('chainsight:bob-awareness', 'UNKNOWN'),
            'days_after_cutoff': int(props.get('chainsight:days-after-cutoff', 0)),
            'message': props.get('chainsight:message', ''),
        }
    return vulns


def diff_sboms(session_id_old: str, session_id_new: str) -> dict:
    """
    Compare two Bob sessions and return a structured diff.
    """
    sbom_old = load_sbom(session_id_old)
    sbom_new = load_sbom(session_id_new)

    comps_old = extract_components(sbom_old)
    comps_new = extract_components(sbom_new)
    vulns_old = extract_vulnerabilities(sbom_old)
    vulns_new = extract_vulnerabilities(sbom_new)

    # Component changes
    added_packages = []
    removed_packages = []
    upgraded_packages = []
    downgraded_packages = []
    unchanged_packages = []

    all_packages = set(comps_old.keys()) | set(comps_new.keys())

    for name in all_packages:
        old = comps_old.get(name)
        new = comps_new.get(name)

        if old and not new:
            removed_packages.append(old)
        elif new and not old:
            added_packages.append(new)
        elif old and new:
            if old['version'] != new['version']:
                change = {**new, 'old_version': old['version'], 'new_version': new['version']}
                # Simple version comparison
                try:
                    from packaging.version import Version
                    if Version(new['version']) > Version(old['version']):
                        upgraded_packages.append(change)
                    else:
                        downgraded_packages.append(change)
                except Exception:
                    upgraded_packages.append(change)
            else:
                unchanged_packages.append(new)

    # Vulnerability changes
    new_vulns = []
    fixed_vulns = []
    new_blind_spots = []

    for vid, vuln in vulns_new.items():
        if vid not in vulns_old:
            new_vulns.append(vuln)
            if vuln['post_cutoff']:
                new_blind_spots.append(vuln)

    for vid, vuln in vulns_old.items():
        if vid not in vulns_new:
            fixed_vulns.append(vuln)

    # Posture change
    def get_posture(sbom):
        vulns = sbom.get('vulnerabilities', [])
        if not vulns:
            return 'PASS'
        for v in vulns:
            for p in v.get('properties', []):
                if p['name'] == 'chainsight:post-training-cutoff' and p['value'] == 'true':
                    return 'FAIL'
        return 'WARN'

    posture_old = get_posture(sbom_old)
    posture_new = get_posture(sbom_new)

    posture_change = 'unchanged'
    if posture_old != posture_new:
        risk_order = {'PASS': 1, 'WARN': 2, 'FAIL': 3}
        if risk_order.get(posture_new, 0) > risk_order.get(posture_old, 0):
            posture_change = 'degraded'
        else:
            posture_change = 'improved'

    # Risk score delta
    blind_old = sum(1 for v in vulns_old.values() if v['post_cutoff'])
    blind_new = sum(1 for v in vulns_new.values() if v['post_cutoff'])

    return {
        'session_old': session_id_old,
        'session_new': session_id_new,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'packages_added': len(added_packages),
            'packages_removed': len(removed_packages),
            'packages_upgraded': len(upgraded_packages),
            'packages_downgraded': len(downgraded_packages),
            'new_cves': len(new_vulns),
            'fixed_cves': len(fixed_vulns),
            'new_blind_spots': len(new_blind_spots),
            'blind_spots_old': blind_old,
            'blind_spots_new': blind_new,
            'blind_spot_delta': blind_new - blind_old,
            'posture_old': posture_old,
            'posture_new': posture_new,
            'posture_change': posture_change,
            'risk_direction': '↑ WORSE' if posture_change == 'degraded' else '↓ BETTER' if posture_change == 'improved' else '→ SAME'
        },
        'added_packages': added_packages,
        'removed_packages': removed_packages,
        'upgraded_packages': upgraded_packages,
        'downgraded_packages': downgraded_packages,
        'new_vulnerabilities': new_vulns,
        'fixed_vulnerabilities': fixed_vulns,
        'new_blind_spots': new_blind_spots,
    }


def format_diff_report(diff: dict) -> str:
    """Format diff as human-readable markdown report."""
    s = diff['summary']
    lines = [
        f"# ChainSight SBOM Diff Report",
        f"",
        f"**Session A:** `{diff['session_old']}`",
        f"**Session B:** `{diff['session_new']}`",
        f"**Generated:** {diff['timestamp']}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Posture change | {s['posture_old']} → {s['posture_new']} ({s['risk_direction']}) |",
        f"| New packages | +{s['packages_added']} |",
        f"| Removed packages | -{s['packages_removed']} |",
        f"| Upgraded packages | {s['packages_upgraded']} |",
        f"| New CVEs introduced | {s['new_cves']} |",
        f"| CVEs fixed | {s['fixed_cves']} |",
        f"| New Bob blind spots | **{s['new_blind_spots']}** |",
        f"| Blind spot delta | {'+' if s['blind_spot_delta'] >= 0 else ''}{s['blind_spot_delta']} |",
        f"",
    ]

    if diff['new_blind_spots']:
        lines += [
            f"## ⚠ New Bob Blind Spots",
            f"*These CVEs were introduced by Bob and were unknown at generation time*",
            f"",
        ]
        for v in diff['new_blind_spots']:
            lines += [
                f"- **{v['id']}** — {v['description'][:100]}",
                f"  - Published: {v['published'][:10]} ({v['days_after_cutoff']} days after Bob cutoff)",
                f"  - {v['message'][:150]}",
                f"  - Fix: {v['recommendation'] or 'No fix available'}",
                f"",
            ]

    if diff['added_packages']:
        lines += [f"## New Packages Introduced by Bob", f""]
        for p in diff['added_packages']:
            risk = f"⚠ {p['cve_count']} CVE(s)" if p['cve_count'] > 0 else "✓ Clean"
            blind = f" | 👁 {p['post_cutoff_cves']} blind spot(s)" if p['post_cutoff_cves'] > 0 else ""
            lines.append(f"- `{p['name']}=={p['version']}` — {risk}{blind}")
        lines.append("")

    if diff['new_vulnerabilities']:
        lines += [f"## New CVEs Introduced", f""]
        for v in diff['new_vulnerabilities']:
            blind_marker = " 👁 **BOB BLIND SPOT**" if v['post_cutoff'] else ""
            lines.append(f"- **{v['id']}**{blind_marker} in {', '.join(v['affects'])}")
            if v['recommendation']:
                lines.append(f"  - Fix: {v['recommendation']}")
        lines.append("")

    if diff['fixed_vulnerabilities']:
        lines += [f"## CVEs Resolved", f""]
        for v in diff['fixed_vulnerabilities']:
            lines.append(f"- ~~{v['id']}~~ — resolved in new session")
        lines.append("")

    return '\n'.join(lines)
