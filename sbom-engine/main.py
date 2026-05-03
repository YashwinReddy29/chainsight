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
from slack_notifier import send_blind_spot_alert, send_pass_notification
from sbom_attestor import sign_sbom, verify_sbom

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

        # Sign the SBOM for integrity verification
        sbom = sign_sbom(sbom)

        sbom_path = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
        with open(sbom_path, 'w') as f:
            json.dump(sbom, f, indent=2)

        saved = save_sbom_audit(session_id, sbom, posture, stats)

        # Send Slack notification
        blind_vuln_list = [v for v in sbom.get('vulnerabilities', [])
                          if any(p['name'] == 'chainsight:post-training-cutoff' and p['value'] == 'true'
                                 for p in v.get('properties', []))]
        if blind_vuln_list:
            from auto_fix import generate_fixes
            fixes_for_slack = generate_fixes(sbom)
            send_blind_spot_alert(session_id, blind_vuln_list, posture, fixes_for_slack.get('fixes', []))
        elif posture == 'PASS':
            send_pass_notification(session_id, len(sbom.get('components', [])))


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


# ─── SBOM Diff endpoint ───────────────────────────────────────────────────────

from sbom_diff import diff_sboms, format_diff_report

@app.get('/diff/{session_old}/{session_new}')
async def diff_sessions(session_old: str, session_new: str, format: str = 'json'):
    """
    Compare two Bob sessions and return what changed.
    format=json returns structured diff
    format=markdown returns human-readable report
    """
    try:
        diff = diff_sboms(session_old, session_new)
        if format == 'markdown':
            return {'report': format_diff_report(diff)}
        return diff
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/diff/latest')
async def diff_latest_sessions():
    """Compare the two most recent Bob sessions automatically."""
    sessions = get_all_sessions()
    if len(sessions) < 2:
        raise HTTPException(status_code=400, detail='Need at least 2 sessions to diff')
    sorted_sessions = sorted(sessions, key=lambda s: s.get('timestamp', ''))
    old = sorted_sessions[-2]['session_id']
    new = sorted_sessions[-1]['session_id']
    diff = diff_sboms(old, new)
    return diff


# ─── Auto-Fix endpoints ───────────────────────────────────────────────────────

from auto_fix import generate_fixes, generate_fixed_requirements, generate_remediation_report

@app.get('/fix/{session_id}')
async def get_fixes(session_id: str):
    """Generate automatic fix recommendations for a session's blind spots."""
    sbom_path = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
    if not sbom_path.exists():
        raise HTTPException(status_code=404, detail=f'Session {session_id} not found')
    with open(sbom_path) as f:
        sbom = json.load(f)
    fixes = generate_fixes(sbom)
    return fixes

@app.get('/fix/{session_id}/report')
async def get_fix_report(session_id: str):
    """Get markdown remediation report for a session."""
    sbom_path = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
    if not sbom_path.exists():
        raise HTTPException(status_code=404, detail=f'Session {session_id} not found')
    with open(sbom_path) as f:
        sbom = json.load(f)
    fixes = generate_fixes(sbom)
    report = generate_remediation_report(session_id, fixes)
    return {'session_id': session_id, 'report': report, 'fixes': fixes}

@app.post('/fix/{session_id}/apply')
async def apply_fixes(session_id: str, requirements_content: str = ''):
    """Apply fixes to a requirements.txt and return the patched version."""
    sbom_path = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
    if not sbom_path.exists():
        raise HTTPException(status_code=404, detail=f'Session {session_id} not found')
    with open(sbom_path) as f:
        sbom = json.load(f)
    fixes_data = generate_fixes(sbom)
    if not requirements_content:
        return {'error': 'No requirements content provided', 'fixes': fixes_data}
    patched = generate_fixed_requirements(requirements_content, fixes_data['fixes'])
    return {
        'session_id': session_id,
        'original': requirements_content,
        'patched': patched,
        'fixes_applied': fixes_data['total_fixes'],
        'fixes': fixes_data['fixes']
    }


# ─── PDF Report endpoint ──────────────────────────────────────────────────────

from fastapi.responses import Response
from pdf_report import generate_pdf_report
from auto_fix import generate_fixes

@app.get('/report/{session_id}/pdf')
async def get_pdf_report(session_id: str):
    """Generate and download a PDF compliance report for a session."""
    sbom_path = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
    if not sbom_path.exists():
        raise HTTPException(status_code=404, detail=f'Session {session_id} not found')
    with open(sbom_path) as f:
        sbom = json.load(f)
    fixes = generate_fixes(sbom)
    pdf_bytes = generate_pdf_report(session_id, sbom, fixes)
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail='PDF generation failed — install reportlab')
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="chainsight-{session_id}.pdf"'}
    )


# ─── Attestation endpoints ─────────────────────────────────────────────────────

@app.get('/verify/{session_id}')
async def verify_session(session_id: str):
    """Verify the cryptographic attestation of a session SBOM."""
    sbom_path = SBOM_OUTPUT_DIR / f'{session_id}.cdx.json'
    if not sbom_path.exists():
        raise HTTPException(status_code=404, detail=f'Session {session_id} not found')
    with open(sbom_path) as f:
        sbom = json.load(f)
    result = verify_sbom(sbom)
    return {'session_id': session_id, **result}
