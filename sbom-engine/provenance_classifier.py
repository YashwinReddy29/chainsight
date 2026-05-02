import os
import json
import re
import logging
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
logger = logging.getLogger(__name__)

WATSONX_URL = os.getenv('WATSONX_URL', 'https://us-south.ml.cloud.ibm.com')
WATSONX_API_KEY = os.getenv('WATSONX_API_KEY')
PROJECT_ID = os.getenv('WATSONX_PROJECT_ID')

PROMPT = """Analyze this Python code and identify which open-source libraries it uses.

Return ONLY one JSON object. Do not repeat it. Do not add comments.

Format:
{"resemblances":[{"library":"python-jose","version_range":"3.x","confidence":0.9,"license":"MIT","security_notes":"Has known CVEs, consider PyJWT"}],"overall_provenance_confidence":0.85,"dominant_pattern":"python-jose","summary":"JWT authentication using python-jose"}

Code to analyze:
{CODE}

JSON:"""


def extract_first_json(text: str) -> str:
    """Find first valid JSON object in LLaMA response."""
    # LLaMA returns: ' \n{json}\n# comments\n{json again}\n...'
    # We want the first { ... } block
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            return line
    # If no single-line JSON, find first { and match to closing }
    match = re.search(r'\{[^{}]*"resemblances"[^{}]*\[.*?\][^{}]*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return ''


def classify_provenance(code: str) -> dict:
    if not WATSONX_API_KEY or not PROJECT_ID:
        return _fallback(code)
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        client = APIClient(credentials)
        model = ModelInference(
            model_id='meta-llama/llama-3-3-70b-instruct',
            api_client=client,
            project_id=PROJECT_ID,
            params={'max_new_tokens': 400, 'temperature': 0.05}
        )

        code_sample = code[:1500] if len(code) > 1500 else code
        prompt = PROMPT.replace('{CODE}', code_sample)
        response = model.generate_text(prompt=prompt)

        if not response or not response.strip():
            return _fallback(code)

        json_str = extract_first_json(response)
        if not json_str:
            logger.warning(f"No JSON found in response: {repr(response[:100])}")
            return _fallback(code)

        result = json.loads(json_str)
        result['classified_by'] = 'meta-llama/llama-3-3-70b-instruct'
        result['watsonx_url'] = WATSONX_URL
        logger.info(f"LLaMA provenance: {result.get('dominant_pattern')} confidence={result.get('overall_provenance_confidence')}")
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}")
        return _fallback(code)
    except Exception as e:
        logger.error(f"watsonx.ai failed: {e}")
        return _fallback(code, error=str(e))


def _fallback(code: str, error: str = None) -> dict:
    resemblances = []
    patterns = [
        ('fastapi', 'FastAPI', '0.x', 'MIT', 'Keep updated — active CVE history'),
        ('flask', 'Flask', '2.x-3.x', 'BSD-3-Clause', 'SSTI vulnerabilities in older versions'),
        ('django', 'Django', '4.x-5.x', 'BSD-3-Clause', 'Well maintained'),
        ('jwt', 'PyJWT', '2.x', 'MIT', 'Use 2.4.0+ to avoid algorithm confusion CVEs'),
        ('jose', 'python-jose', '3.x', 'MIT', 'KNOWN CVEs — consider PyJWT instead'),
        ('bcrypt', 'passlib/bcrypt', 'any', 'Apache-2.0', 'Standard password hashing'),
        ('requests', 'requests', '2.28+', 'Apache-2.0', 'Use 2.28.2+ for CVE-2023-32681 fix'),
        ('sqlalchemy', 'SQLAlchemy', '2.x', 'MIT', 'Use 2.x for security improvements'),
        ('cryptography', 'cryptography', '42.x+', 'Apache-2.0', 'Multiple 2025/2026 CVEs'),
        ('psycopg2', 'psycopg2', '2.9+', 'LGPL-3.0', 'Stable — keep updated'),
        ('express', 'Express.js', '4.x', 'MIT', 'Check prototype pollution CVEs'),
        ('axios', 'axios', '1.x', 'MIT', 'Use 1.6.0+ for SSRF fix'),
    ]
    code_lower = code.lower()
    for keyword, library, version_range, license_, notes in patterns:
        if keyword in code_lower:
            resemblances.append({
                'library': library,
                'version_range': version_range,
                'confidence': 0.7,
                'license': license_,
                'security_notes': notes
            })
    return {
        'resemblances': resemblances,
        'overall_provenance_confidence': 0.6 if resemblances else 0.2,
        'dominant_pattern': resemblances[0]['library'] if resemblances else 'unknown',
        'summary': f"Detected {len(resemblances)} known patterns.",
        'classified_by': 'rule-based-fallback',
        'error': error
    }
