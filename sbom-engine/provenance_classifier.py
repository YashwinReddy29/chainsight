import os
import json
import logging
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
logger = logging.getLogger(__name__)

WATSONX_URL = os.getenv('WATSONX_URL', 'https://us-south.ml.cloud.ibm.com')
WATSONX_API_KEY = os.getenv('WATSONX_API_KEY')
PROJECT_ID = os.getenv('WATSONX_PROJECT_ID')

PROMPT = """You are a software supply chain security analyst performing AI code provenance analysis.

Analyze the provided code and identify which well-known open-source libraries or patterns it resembles.

Respond ONLY with valid JSON, no markdown, no explanation:
{
  "resemblances": [
    {
      "library": "string",
      "version_range": "string",
      "confidence": 0.0,
      "license": "string",
      "security_notes": "string"
    }
  ],
  "overall_provenance_confidence": 0.0,
  "dominant_pattern": "string",
  "summary": "string"
}

Code to analyze:
"""

def classify_provenance(code: str) -> dict:
    if not WATSONX_API_KEY or not PROJECT_ID:
        logger.warning("watsonx.ai credentials not set — using fallback")
        return _fallback(code)
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        client = APIClient(credentials)
        model = ModelInference(
            model_id='ibm/granite-13b-instruct-v2',
            api_client=client,
            project_id=PROJECT_ID,
            params={'max_new_tokens': 600, 'temperature': 0.1, 'stop_sequences': ['\n\n\n']}
        )
        code_sample = code[:3000] if len(code) > 3000 else code
        response = model.generate_text(prompt=PROMPT + code_sample)
        text = response.strip()
        if text.startswith('```'):
            lines = text.split('\n')[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)
        result = json.loads(text)
        result['classified_by'] = 'ibm-granite-13b-instruct-v2'
        return result
    except Exception as e:
        logger.error(f"watsonx.ai failed: {e}")
        return _fallback(code, error=str(e))

def _fallback(code: str, error: str = None) -> dict:
    resemblances = []
    patterns = [
        ('fastapi', 'FastAPI', '0.x', 'MIT', 'Keep updated — active CVE history'),
        ('flask', 'Flask', '2.x-3.x', 'BSD-3-Clause', 'SSTI vulnerabilities in older versions'),
        ('django', 'Django', '4.x-5.x', 'BSD-3-Clause', 'Well maintained — keep updated'),
        ('jwt', 'PyJWT', '2.x', 'MIT', 'Use 2.4.0+ to avoid algorithm confusion CVEs'),
        ('jose', 'python-jose', '3.x', 'MIT', 'KNOWN CVEs — consider PyJWT instead'),
        ('bcrypt', 'passlib/bcrypt', 'any', 'Apache-2.0', 'Standard password hashing'),
        ('requests', 'requests', '2.28+', 'Apache-2.0', 'Use 2.28.2+ for CVE-2023-32681 fix'),
        ('sqlalchemy', 'SQLAlchemy', '2.x', 'MIT', 'Use 2.x for security improvements'),
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
        'summary': f"Rule-based fallback. Detected {len(resemblances)} patterns.",
        'classified_by': 'rule-based-fallback',
        'error': error
    }
