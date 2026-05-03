"""
pdf_report.py
Generates a professional PDF compliance report for a ChainSight SBOM session.
Suitable for EU CRA Article 11 technical documentation and US EO-14028 compliance.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

SBOM_OUTPUT_DIR = Path('../sbom-output')


def generate_pdf_report(session_id: str, sbom: dict, fixes_data: dict = None) -> bytes:
    """Generate a PDF compliance report and return as bytes."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor, black, white
        from reportlab.lib.units import mm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                         Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        # Colors
        IBM_BLUE = HexColor('#0043CE')
        DARK_BG = HexColor('#111116')
        PURPLE = HexColor('#a78bfa')
        RED = HexColor('#ef4444')
        GREEN = HexColor('#22c55e')
        YELLOW = HexColor('#eab308')
        GRAY = HexColor('#71717a')
        LIGHT_GRAY = HexColor('#d4d4d8')

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle('Title', parent=styles['Title'],
            fontSize=20, textColor=IBM_BLUE, spaceAfter=4)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
            fontSize=11, textColor=GRAY, spaceAfter=16)
        h2_style = ParagraphStyle('H2', parent=styles['Heading2'],
            fontSize=13, textColor=IBM_BLUE, spaceBefore=12, spaceAfter=6)
        h3_style = ParagraphStyle('H3', parent=styles['Heading3'],
            fontSize=11, textColor=DARK_BG, spaceBefore=8, spaceAfter=4)
        body_style = ParagraphStyle('Body', parent=styles['Normal'],
            fontSize=9, textColor=DARK_BG, spaceAfter=4, leading=14)
        code_style = ParagraphStyle('Code', parent=styles['Code'],
            fontSize=8, textColor=HexColor('#1e1040'),
            backColor=HexColor('#f0edff'), borderPadding=4)
        blind_style = ParagraphStyle('Blind', parent=styles['Normal'],
            fontSize=9, textColor=HexColor('#4c1d95'),
            backColor=HexColor('#f5f0ff'), borderPadding=4)

        story = []

        # Header
        story.append(Paragraph("ChainSight Compliance Report", title_style))
        story.append(Paragraph(
            f"AI-Generated Code Supply Chain Audit — Powered by IBM Bob",
            subtitle_style
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=IBM_BLUE))
        story.append(Spacer(1, 8*mm))

        # Session metadata table
        meta = sbom.get('metadata', {})
        props = {p['name']: p['value'] for p in meta.get('properties', [])}
        posture = _get_posture(sbom)
        posture_color = RED if posture == 'FAIL' else YELLOW if posture == 'WARN' else GREEN

        meta_data = [
            ['Session ID', session_id],
            ['Generated', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['AI Tool', 'IBM Bob (Version 1.0)'],
            ['Training Cutoff', '2024-11-01'],
            ['SBOM Format', 'CycloneDX 1.6'],
            ['Serial Number', sbom.get('serialNumber', 'N/A')],
            ['Components', str(len(sbom.get('components', [])))],
            ['Vulnerabilities', str(len(sbom.get('vulnerabilities', [])))],
            ['Compliance Posture', posture],
            ['Regulation', 'EU CRA Article 11, US EO-14028'],
        ]

        meta_table = Table(meta_data, colWidths=[60*mm, 110*mm])
        meta_table.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0), (0,-1), IBM_BLUE),
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#f8f8ff')),
            ('BACKGROUND', (0,0), (-1,0), HexColor('#e8e8f8')),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [HexColor('#ffffff'), HexColor('#f8f8ff')]),
            ('GRID', (0,0), (-1,-1), 0.5, HexColor('#ddddee')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('TEXTCOLOR', (1,8), (1,8), posture_color),
            ('FONTNAME', (1,8), (1,8), 'Helvetica-Bold'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 6*mm))

        # Executive summary
        story.append(Paragraph("Executive Summary", h2_style))
        vulns = sbom.get('vulnerabilities', [])
        blind_vulns = [v for v in vulns if any(
            p['name'] == 'chainsight:post-training-cutoff' and p['value'] == 'true'
            for p in v.get('properties', [])
        )]

        summary_text = (
            f"This report documents the supply chain security audit of AI-generated code "
            f"produced by IBM Bob. The session included <b>{len(sbom.get('components', []))} packages</b> "
            f"with <b>{len(vulns)} vulnerabilities</b> detected. "
            f"<b>{len(blind_vulns)} Bob blind spot(s)</b> were identified — "
            f"vulnerabilities published after IBM Bob's training cutoff date of November 1, 2024, "
            f"which Bob could not have warned about at code generation time. "
            f"Overall compliance posture: <b>{posture}</b>."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 4*mm))

        # Bob blind spots section
        if blind_vulns:
            story.append(Paragraph("Bob Blind Spots — Critical Findings", h2_style))
            story.append(Paragraph(
                "The following vulnerabilities were UNKNOWN to IBM Bob when it generated this code. "
                "They were published after Bob's training cutoff and represent the highest priority remediation items.",
                body_style
            ))
            story.append(Spacer(1, 3*mm))

            blind_data = [['CVE ID', 'Package', 'Published', 'Days After Cutoff', 'Fix Available']]
            for v in blind_vulns:
                props_v = {p['name']: p['value'] for p in v.get('properties', [])}
                affects = ', '.join(a.get('ref', '') for a in v.get('affects', []))
                blind_data.append([
                    v.get('id', ''),
                    affects,
                    v.get('published', '')[:10],
                    f"{props_v.get('chainsight:days-after-cutoff', '?')} days",
                    'Yes' if v.get('recommendation') else 'Manual review'
                ])

            blind_table = Table(blind_data, colWidths=[40*mm, 45*mm, 25*mm, 30*mm, 30*mm])
            blind_table.setStyle(TableStyle([
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,0), (-1,0), HexColor('#4c1d95')),
                ('TEXTCOLOR', (0,0), (-1,0), white),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#faf5ff'), HexColor('#f5f0ff')]),
                ('GRID', (0,0), (-1,-1), 0.5, HexColor('#c4b5fd')),
                ('PADDING', (0,0), (-1,-1), 5),
                ('TEXTCOLOR', (0,1), (0,-1), HexColor('#4c1d95')),
                ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
            ]))
            story.append(blind_table)
            story.append(Spacer(1, 6*mm))

        # Component inventory
        story.append(Paragraph("Component Inventory (CycloneDX 1.6)", h2_style))
        comp_data = [['Package', 'Version', 'License', 'CVEs', 'Blind Spots', 'Risk']]
        for comp in sbom.get('components', []):
            props_c = {p['name']: p['value'] for p in comp.get('properties', [])}
            cve_count = props_c.get('chainsight:cve-count', '0')
            blind_count = props_c.get('chainsight:post-cutoff-cves', '0')
            severity = props_c.get('chainsight:severity', 'NONE')
            license_id = comp['licenses'][0]['license']['id'] if comp.get('licenses') else 'UNKNOWN'
            comp_data.append([
                comp.get('name', ''),
                comp.get('version', ''),
                license_id,
                cve_count,
                blind_count,
                severity
            ])

        comp_table = Table(comp_data, colWidths=[45*mm, 25*mm, 35*mm, 15*mm, 20*mm, 30*mm])
        comp_table.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), IBM_BLUE),
            ('TEXTCOLOR', (0,0), (-1,0), white),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, HexColor('#f5f5ff')]),
            ('GRID', (0,0), (-1,-1), 0.3, HexColor('#ddddee')),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(comp_table)
        story.append(Spacer(1, 6*mm))

        # Auto-fix recommendations
        if fixes_data and fixes_data.get('fixes'):
            story.append(Paragraph("Automated Remediation Plan", h2_style))
            story.append(Paragraph(
                f"ChainSight has automatically generated fix recommendations for "
                f"{fixes_data['total_fixes']} package(s). Apply these upgrades to resolve all Bob blind spots.",
                body_style
            ))
            fix_data = [['Package', 'Current', 'Fixed Version', 'CVEs Resolved', 'Command']]
            for fix in fixes_data['fixes']:
                fix_data.append([
                    fix['package'],
                    fix['current_version'],
                    fix['fixed_version'],
                    ', '.join(fix['vulns_fixed']),
                    f"pip install {fix['package']}=={fix['fixed_version']}"
                ])
            fix_table = Table(fix_data, colWidths=[35*mm, 20*mm, 20*mm, 45*mm, 50*mm])
            fix_table.setStyle(TableStyle([
                ('FONTSIZE', (0,0), (-1,-1), 7.5),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,0), (-1,0), HexColor('#166534')),
                ('TEXTCOLOR', (0,0), (-1,0), white),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, HexColor('#f0fff4')]),
                ('GRID', (0,0), (-1,-1), 0.3, HexColor('#bbf7d0')),
                ('PADDING', (0,0), (-1,-1), 4),
                ('TEXTCOLOR', (4,1), (4,-1), HexColor('#166534')),
                ('FONTNAME', (4,1), (4,-1), 'Courier'),
            ]))
            story.append(fix_table)
            story.append(Spacer(1, 6*mm))

        # Regulatory compliance section
        story.append(Paragraph("Regulatory Compliance Statement", h2_style))
        reg_text = (
            "<b>US Executive Order 14028</b> (Improving the Nation's Cybersecurity) requires "
            "Software Bill of Materials for software sold to the US federal government. "
            "This report satisfies the SBOM requirement with a CycloneDX 1.6 format document "
            "including component inventory, license information, and vulnerability disclosure.<br/><br/>"
            "<b>EU Cyber Resilience Act (CRA)</b> — Article 11 requires technical documentation "
            "including a detailed description of cybersecurity measures. The AI-extended fields "
            "in this SBOM (chainsight:ai-generated, chainsight:post-training-cutoff, "
            "chainsight:bob-awareness) satisfy the AI Act Article 11 documentation requirements "
            "for AI-generated software components. <b>EU CRA deadline: August 2, 2026.</b>"
        )
        story.append(Paragraph(reg_text, body_style))
        story.append(Spacer(1, 6*mm))

        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=GRAY))
        story.append(Spacer(1, 3*mm))
        footer_text = (
            f"Generated by ChainSight v1.0 | IBM Bob Dev Day Hackathon 2026 | "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
            f"CycloneDX 1.6 | Powered by IBM Bob + watsonx.ai + Cloudant"
        )
        story.append(Paragraph(footer_text, ParagraphStyle('Footer',
            parent=styles['Normal'], fontSize=7, textColor=GRAY, alignment=TA_CENTER)))

        doc.build(story)
        return buffer.getvalue()

    except ImportError:
        return None


def _get_posture(sbom: dict) -> str:
    vulns = sbom.get('vulnerabilities', [])
    if not vulns:
        return 'PASS'
    for v in vulns:
        for p in v.get('properties', []):
            if p['name'] == 'chainsight:post-training-cutoff' and p['value'] == 'true':
                return 'FAIL'
    return 'WARN'
