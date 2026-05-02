import os
import uuid
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from provenance_classifier import classify_provenance
from cyclonedx_generator import generate_sbom, assess_posture
from cloudant_client import save_sbom_audit, get_all_sessions

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SBOM_OUTPUT_DIR = Path('../sbom-output')
SBOM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title='ChainSight SBOM Engine', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

class GenerateSBOMRequest(BaseModel):
    session_id: Optional[str] = None
    dependencies: List[Any] = []
    cve_results: List[Any] = []
    license_results: List[Any] = []
    freshness_results: Any = []
    generated_code: Optional[str] = None

@app.get('/health')
async def health():
    return {'status': 'ok', 'service': 'ChainSight SBOM Engine', 'version': '1.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat()}

@app.post('/generate')
async def generate(req: GenerateSBOMRequest):
    session_id = req.session_id or str(uuid.uuid4())[:8]
    logger.info(f"Generating SBOM: {session_id} — {len(req.dependencies)} deps")
    try:
        provenance = []
        if req.generated_code and req.dependencies:
            prov = classify_provenance(req.generated_code)
            provenance = [{'package': d.get('name',''), **prov} for d in req.dependencies]

        sbom = generate_sbom(
            session_id=session_id,
            dependencies=req.dependencies,
            cve_results=req.cve_results,
            license_results=req.license_results,
            provenance_results=provenance,
            freshness_results=req.freshness_results
        )

        posture = assess_posture(sbom)

        post_cutoff = 0
        critical = 0
        high = 0
        for vuln in sbom.get('vulnerabilities', []):
            for prop in vuln.get('properties', []):
                if prop['name'] == 'chainsight:post-training-cutoff' and prop['value'] == 'true':
                    post_cutoff += 1
            for rating in vuln.get('ratings', []):
                sev = rating.get('severity', '').lower()
                if sev == 'critical': critical += 1
                elif sev == 'high': high += 1

        stats = {'post_cutoff_cves': post_cutoff, 'critical_count': critical, 'high_count': high}

        sbom_path = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
        with open(sbom_path, 'w') as f:
            json.dump(sbom, f, indent=2)

        saved = save_sbom_audit(session_id, sbom, posture, stats)

        return {
            'success': True,
            'summary': {
                'session_id': session_id,
                'sbom_file': str(sbom_path),
                'compliance_posture': posture,
                'total_components': len(sbom.get('components', [])),
                'total_vulnerabilities': len(sbom.get('vulnerabilities', [])),
                'post_cutoff_cves': post_cutoff,
                'critical_count': critical,
                'high_count': high,
                'saved_to_cloudant': saved,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception as e:
        logger.error(f"SBOM generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/sessions')
async def sessions():
    return get_all_sessions()

@app.get('/session/{session_id}')
async def session(session_id: str):
    p = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
    if not p.exists():
        raise HTTPException(status_code=404, detail=f'Session {session_id} not found')
    with open(p) as f:
        return json.load(f)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('SBOM_ENGINE_PORT', 8080)))
