import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
logger = logging.getLogger(__name__)

CLOUDANT_URL = os.getenv('CLOUDANT_URL')
CLOUDANT_API_KEY = os.getenv('CLOUDANT_API_KEY')
DB_NAME = 'chainsight-audit'

def get_client():
    if not CLOUDANT_URL or not CLOUDANT_API_KEY:
        raise ValueError("Cloudant credentials not in .env")
    from ibmcloudant.cloudant_v1 import CloudantV1
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
    authenticator = IAMAuthenticator(CLOUDANT_API_KEY)
    client = CloudantV1(authenticator=authenticator)
    client.set_service_url(CLOUDANT_URL)
    return client

def ensure_db(client):
    try:
        client.get_database_information(db=DB_NAME)
    except Exception:
        try:
            client.put_database(db=DB_NAME)
            logger.info(f"Created database: {DB_NAME}")
        except Exception as e:
            logger.error(f"Could not create database: {e}")

def save_sbom_audit(session_id: str, sbom: dict, posture: str, stats: dict) -> bool:
    try:
        client = get_client()
        ensure_db(client)
        from ibmcloudant.cloudant_v1 import Document
        doc = Document.from_dict({
            '_id': session_id,
            'session_id': session_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sbom_format': 'CycloneDX',
            'spec_version': '1.6',
            'compliance_posture': posture,
            'component_count': len(sbom.get('components', [])),
            'vulnerability_count': len(sbom.get('vulnerabilities', [])),
            'post_cutoff_cves': stats.get('post_cutoff_cves', 0),
            'critical_count': stats.get('critical_count', 0),
            'high_count': stats.get('high_count', 0),
            'ai_tool': 'IBM Bob',
            'sbom': sbom
        })
        client.post_document(db=DB_NAME, document=doc)
        logger.info(f"Saved to Cloudant: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Cloudant save failed: {e}")
        return False

def get_all_sessions() -> list:
    try:
        client = get_client()
        result = client.post_all_docs(db=DB_NAME, include_docs=True).get_result()
        return [
            {k: v for k, v in row['doc'].items() if k != 'sbom'}
            for row in result.get('rows', [])
            if not row['id'].startswith('_')
        ]
    except Exception as e:
        logger.error(f"Cloudant fetch failed: {e}")
        return []
