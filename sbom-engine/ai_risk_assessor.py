"""
ai_risk_assessor.py
Uses watsonx.ai LLaMA to generate natural language risk assessments.
Explains in plain English what the blind spots mean and why they matter.
"""
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
logger = logging.getLogger(__name__)

WATSONX_URL = os.getenv('WATSONX_URL', 'https://us-south.ml.cloud.ibm.com')
WATSONX_API_KEY = os.getenv('WATSONX_API_KEY')
PROJECT_ID = os.getenv('WATSONX_PROJECT_ID')


def generate_risk_assessment(session_id: str, sbom: dict, fixes: dict) -> dict:
    """Generate a natural language risk assessment using LLaMA."""

    # Build context for the prompt
    components = sbom.get('components', [])
    vulns = sbom.get('vulnerabilities', [])
    blind_vulns = []
    known_vulns = []

    for v in vulns:
        props = {p['name']: p['value'] for p in v.get('properties', [])}
        if props.get('chainsight:post-training-cutoff') == 'true':
            blind_vulns.append({
                'id': v['id'],
                'description': v.get('description', ''),
                'days_after': props.get('chainsight:days-after-cutoff', '?'),
                'affects': [a.get('ref', '') for a in v.get('affects', [])],
                'fix': v.get('recommendation', 'No fix available')
            })
        else:
            known_vulns.append(v['id'])

    if not blind_vulns:
        return {
            'session_id': session_id,
            'risk_level': 'LOW',
            'assessment': f'Session {session_id} passed ChainSight scan. All {len(components)} packages are clean with no Bob blind spots detected. Bob was aware of all CVEs found (if any) at code generation time.',
            'headline': 'Clean session — no Bob blind spots',
            'action_required': False,
            'generated_by': 'rule-based'
        }

    # Build prompt for LLaMA
    blind_summary = '\n'.join([
        f"- {b['id']}: {b['description'][:100]} (in {', '.join(b['affects'])}, published {b['days_after']} days after Bob training cutoff)"
        for b in blind_vulns[:3]
    ])

    fix_summary = '\n'.join([
        f"- Upgrade {f['package']} from {f['current_version']} to {f['fixed_version']}"
        for f in fixes.get('fixes', [])[:3]
    ])

    prompt = f"""You are a cybersecurity expert explaining a supply chain security finding to a software engineering team.

IBM Bob AI generated code that introduced these vulnerabilities that Bob could NOT know about (published after training cutoff):

{blind_summary}

Available fixes:
{fix_summary if fix_summary else "No automated fixes available"}

Write a 2-3 sentence plain English risk assessment explaining:
1. What the risk is and why Bob could not warn about it
2. What the business impact could be
3. What to do immediately

Be specific, professional, and direct. Do not use bullet points. Write as flowing sentences.

Risk assessment:"""

    try:
        if not WATSONX_API_KEY or not PROJECT_ID:
            raise ValueError("No credentials")

        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        client = APIClient(credentials)
        model = ModelInference(
            model_id='meta-llama/llama-3-3-70b-instruct',
            api_client=client,
            project_id=PROJECT_ID,
            params={'max_new_tokens': 200, 'temperature': 0.3}
        )

        response = model.generate_text(prompt=prompt)
        assessment = response.strip()

        # Clean up common LLaMA artifacts
        for prefix in ['Risk assessment:', 'Assessment:', 'Here is']:
            if assessment.lower().startswith(prefix.lower()):
                assessment = assessment[len(prefix):].strip()

        return {
            'session_id': session_id,
            'risk_level': 'CRITICAL' if len(blind_vulns) > 2 else 'HIGH',
            'assessment': assessment,
            'headline': f'{len(blind_vulns)} Bob blind spot(s) — vulnerabilities unknown at generation time',
            'blind_spots': blind_vulns,
            'fixes_available': len(fixes.get('fixes', [])),
            'action_required': True,
            'generated_by': 'meta-llama/llama-3-3-70b-instruct'
        }

    except Exception as e:
        logger.error(f"AI risk assessment failed: {e}")
        # Fallback rule-based assessment
        pkg_names = list(set([a for b in blind_vulns for a in b['affects']]))
        max_days = max(int(b.get('days_after', 0)) for b in blind_vulns)
        assessment = (
            f"This Bob session introduced {len(blind_vulns)} critical vulnerability(ies) in "
            f"{', '.join(pkg_names[:3])} that were published up to {max_days} days after Bob's "
            f"training cutoff — Bob had no knowledge of these CVEs when generating this code. "
            f"An attacker could exploit these vulnerabilities in production. "
            f"{'Automated fixes are available — apply them immediately.' if fixes.get('fixes') else 'Manual security review required before deployment.'}"
        )
        return {
            'session_id': session_id,
            'risk_level': 'CRITICAL' if len(blind_vulns) > 2 else 'HIGH',
            'assessment': assessment,
            'headline': f'{len(blind_vulns)} Bob blind spot(s) detected',
            'blind_spots': blind_vulns,
            'fixes_available': len(fixes.get('fixes', [])),
            'action_required': True,
            'generated_by': 'rule-based-fallback'
        }
