"""
slack_notifier.py
Sends real Slack notifications when Bob blind spots are detected.
Uses Slack Incoming Webhooks — no bot token needed.
Set SLACK_WEBHOOK_URL in .env to enable.
"""

import os
import json
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')


def send_blind_spot_alert(session_id: str, blind_spots: list, posture: str, fixes: list = None) -> bool:
    """Send a Slack alert when Bob blind spots are detected."""
    if not SLACK_WEBHOOK_URL:
        return False

    blind_count = len(blind_spots)
    fix_count = len(fixes) if fixes else 0

    # Build the Slack message with Block Kit
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔴 BOB BLIND SPOT DETECTED — {blind_count} CVE(s)",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Session ID*\n`{session_id}`"},
                {"type": "mrkdwn", "text": f"*Posture*\n`{posture}`"},
                {"type": "mrkdwn", "text": f"*Blind Spots*\n`{blind_count} CVE(s) unknown to Bob`"},
                {"type": "mrkdwn", "text": f"*Auto-fixes*\n`{fix_count} available`"},
            ]
        },
        {"type": "divider"},
    ]

    # Add each blind spot
    for bs in blind_spots[:3]:  # Max 3 to avoid message truncation
        props = {p['name']: p['value'] for p in bs.get('properties', [])}
        days = props.get('chainsight:days-after-cutoff', '?')
        affects = ', '.join(a.get('ref', '') for a in bs.get('affects', []))
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"👁 *{bs['id']}*\n"
                    f"Package: `{affects}`\n"
                    f"Published *{days} days* after Bob training cutoff (2024-11-01)\n"
                    f"Bob had NO knowledge of this vulnerability at generation time\n"
                    f"{bs.get('recommendation', '') or '_No automated fix available_'}"
                )
            }
        })

    if blind_count > 3:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"_...and {blind_count - 3} more blind spot(s)_"}
        })

    # Add fix commands if available
    if fixes:
        fix_cmds = '\n'.join(f"`pip install {f['package']}=={f['fixed_version']}`" for f in fixes[:5])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🔧 Auto-Fix Commands:*\n{fix_cmds}"
            }
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": (
                    f"ChainSight | IBM Bob Dev Day 2026 | "
                    f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
                    f"EU CRA Article 13 — shipping this code may violate compliance requirements"
                )
            }
        ]
    })

    payload = {
        "text": f"BOB BLIND SPOT: {blind_count} CVE(s) unknown to IBM Bob detected in session {session_id}",
        "blocks": blocks
    }

    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        return False


def send_pass_notification(session_id: str, component_count: int) -> bool:
    """Send a brief Slack notification for clean sessions."""
    if not SLACK_WEBHOOK_URL:
        return False

    payload = {
        "text": f"✅ ChainSight: Session `{session_id}` passed — {component_count} packages scanned, no blind spots detected."
    }

    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception:
        return False
