"""
sbom_attestor.py
Cryptographically signs CycloneDX SBOMs using HMAC-SHA256.
The signature proves the SBOM has not been tampered with since generation.
Satisfies the integrity requirements of US EO-14028 and EU CRA Article 13.
In production, use asymmetric signing (RSA/ECDSA) with a PKI.
For hackathon: HMAC-SHA256 demonstrates the concept correctly.
"""

import hashlib
import hmac
import json
import os
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Signing key — in production this would be an HSM-protected private key
SIGNING_KEY = os.getenv('CHAINSIGHT_SIGNING_KEY', 'chainsight-ibm-bob-hackathon-2026-signing-key')


def sign_sbom(sbom: dict) -> dict:
    """
    Add a cryptographic attestation to a CycloneDX SBOM.
    Returns the SBOM with attestation fields added.
    """
    # Create canonical form for signing (sorted keys, no whitespace)
    # We sign the components and vulnerabilities — the critical fields
    canonical = json.dumps({
        'serialNumber': sbom.get('serialNumber', ''),
        'components': sbom.get('components', []),
        'vulnerabilities': sbom.get('vulnerabilities', []),
    }, sort_keys=True, separators=(',', ':'))

    # HMAC-SHA256 signature
    signature = hmac.new(
        SIGNING_KEY.encode(),
        canonical.encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.b64encode(signature).decode()

    # SHA-256 content hash for integrity verification
    content_hash = hashlib.sha256(canonical.encode()).hexdigest()

    # Add attestation to SBOM metadata
    attestation = {
        'name': 'chainsight:attestation',
        'value': json.dumps({
            'algorithm': 'HMAC-SHA256',
            'signature': sig_b64,
            'content_hash': content_hash,
            'signed_at': datetime.now(timezone.utc).isoformat(),
            'signed_by': 'ChainSight v1.0 — IBM Bob Dev Day 2026',
            'key_id': hashlib.sha256(SIGNING_KEY.encode()).hexdigest()[:16],
            'fields_signed': ['serialNumber', 'components', 'vulnerabilities'],
            'compliance': 'US-EO-14028, EU-CRA-Article-13'
        })
    }

    signed_sbom = dict(sbom)
    if 'metadata' not in signed_sbom:
        signed_sbom['metadata'] = {}
    if 'properties' not in signed_sbom['metadata']:
        signed_sbom['metadata']['properties'] = []

    # Remove any existing attestation
    signed_sbom['metadata']['properties'] = [
        p for p in signed_sbom['metadata']['properties']
        if p.get('name') != 'chainsight:attestation'
    ]
    signed_sbom['metadata']['properties'].append(attestation)

    return signed_sbom


def verify_sbom(sbom: dict) -> dict:
    """
    Verify the cryptographic attestation of a signed SBOM.
    Returns verification result with details.
    """
    # Find attestation
    props = sbom.get('metadata', {}).get('properties', [])
    attestation_prop = next(
        (p for p in props if p.get('name') == 'chainsight:attestation'),
        None
    )

    if not attestation_prop:
        return {
            'valid': False,
            'error': 'No attestation found in SBOM',
            'tampered': 'UNKNOWN'
        }

    try:
        att = json.loads(attestation_prop['value'])
    except Exception:
        return {'valid': False, 'error': 'Malformed attestation', 'tampered': 'POSSIBLE'}

    # Recreate canonical form
    canonical = json.dumps({
        'serialNumber': sbom.get('serialNumber', ''),
        'components': sbom.get('components', []),
        'vulnerabilities': sbom.get('vulnerabilities', []),
    }, sort_keys=True, separators=(',', ':'))

    # Verify content hash
    current_hash = hashlib.sha256(canonical.encode()).hexdigest()
    stored_hash = att.get('content_hash', '')

    if current_hash != stored_hash:
        return {
            'valid': False,
            'error': 'Content hash mismatch — SBOM may have been tampered with',
            'tampered': 'YES',
            'stored_hash': stored_hash,
            'current_hash': current_hash
        }

    # Verify HMAC signature
    expected_sig = base64.b64encode(
        hmac.new(SIGNING_KEY.encode(), canonical.encode(), hashlib.sha256).digest()
    ).decode()

    if not hmac.compare_digest(expected_sig, att.get('signature', '')):
        return {
            'valid': False,
            'error': 'Signature verification failed — SBOM has been tampered with',
            'tampered': 'YES'
        }

    return {
        'valid': True,
        'tampered': 'NO',
        'signed_at': att.get('signed_at'),
        'signed_by': att.get('signed_by'),
        'algorithm': att.get('algorithm'),
        'key_id': att.get('key_id'),
        'content_hash': current_hash,
        'compliance': att.get('compliance'),
        'message': 'SBOM integrity verified — content has not been modified since signing'
    }
