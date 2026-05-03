"""
license_policy.py
Enforces license policies for AI-generated code.
Flags packages with licenses incompatible with your project policy.
Common enterprise policies:
- No GPL in commercial products (copyleft contamination)
- No AGPL anywhere (server-side copyleft)
- No unknown licenses in production code
"""

POLICIES = {
    'commercial': {
        'name': 'Commercial Product Policy',
        'description': 'No copyleft licenses allowed in commercial products',
        'blocked': ['GPL-2.0-only', 'GPL-3.0-only', 'AGPL-3.0-only', 'LGPL-2.1-only', 'LGPL-3.0-only', 'CC-BY-SA-4.0', 'OSL-3.0'],
        'warn': ['MPL-2.0', 'EUPL-1.2', 'CDDL-1.0', 'LicenseRef-Unknown', 'NOASSERTION'],
        'allowed': ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', 'CC0-1.0', 'Unlicense', 'WTFPL']
    },
    'strict': {
        'name': 'Strict Open Source Policy',
        'description': 'Only permissive licenses, no unknown',
        'blocked': ['GPL-2.0-only', 'GPL-3.0-only', 'AGPL-3.0-only', 'LGPL-2.1-only', 'LGPL-3.0-only', 'LicenseRef-Unknown', 'NOASSERTION', 'LicenseRef-Proprietary'],
        'warn': ['MPL-2.0', 'EUPL-1.2'],
        'allowed': ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', 'CC0-1.0']
    },
    'permissive': {
        'name': 'Permissive Only Policy',
        'description': 'Only MIT, Apache, BSD licenses allowed',
        'blocked': ['GPL-2.0-only', 'GPL-3.0-only', 'AGPL-3.0-only', 'LGPL-2.1-only', 'LGPL-3.0-only', 'MPL-2.0', 'EUPL-1.2', 'LicenseRef-Unknown', 'NOASSERTION'],
        'warn': ['CC0-1.0', 'Unlicense'],
        'allowed': ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC']
    }
}


def check_license_policy(components: list, policy_name: str = 'commercial') -> dict:
    """Check components against a license policy."""
    policy = POLICIES.get(policy_name, POLICIES['commercial'])
    violations = []
    warnings = []
    compliant = []

    for comp in components:
        name = comp.get('name', '')
        license_id = 'UNKNOWN'
        if comp.get('licenses'):
            license_id = comp['licenses'][0]['license'].get('id', 'UNKNOWN')

        if license_id in policy['blocked']:
            violations.append({
                'package': name,
                'version': comp.get('version', 'unknown'),
                'license': license_id,
                'severity': 'BLOCK',
                'reason': f"License {license_id} is blocked by {policy['name']}",
                'action': f"Replace {name} with a permissively-licensed alternative"
            })
        elif license_id in policy['warn']:
            warnings.append({
                'package': name,
                'version': comp.get('version', 'unknown'),
                'license': license_id,
                'severity': 'WARN',
                'reason': f"License {license_id} requires review under {policy['name']}",
                'action': "Legal review recommended before shipping"
            })
        else:
            compliant.append({
                'package': name,
                'version': comp.get('version', 'unknown'),
                'license': license_id,
                'status': 'COMPLIANT'
            })

    return {
        'policy': policy['name'],
        'policy_key': policy_name,
        'description': policy['description'],
        'total_components': len(components),
        'violations': violations,
        'warnings': warnings,
        'compliant': compliant,
        'violation_count': len(violations),
        'warning_count': len(warnings),
        'compliant_count': len(compliant),
        'policy_status': 'FAIL' if violations else 'WARN' if warnings else 'PASS'
    }
