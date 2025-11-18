#!/usr/bin/env python3
"""
TTS Security Report Generator
Generates comprehensive PDF security assessment reports
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image, Frame, PageTemplate
)
from reportlab.pdfgen import canvas

class SecurityReportGenerator:
    def __init__(self, args):
        self.input_dir = Path(args.input_dir)
        self.project_name = args.project_name
        self.component_name = args.component_name
        self.git_repo = args.git_repo
        self.git_branch = args.git_branch
        self.contact_email = args.contact_email
        self.developer = args.developer
        self.devops_engineer = args.devops_engineer
        self.sonarqube_url = args.sonarqube_url

        # Auto-detect Jenkins build number from environment
        self.jenkins_build = os.getenv('BUILD_NUMBER', 'Unknown')

        # Generate output filename with component name and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"security-report-{self.component_name.replace(' ', '-')}_{timestamp}.pdf"
        self.output_file = self.input_dir / output_filename if args.output_file is None else Path(args.output_file)

        # Load scan data
        self.summary = self._load_summary()
        self.scan_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.doc_number = f"TTS-SEC-{datetime.now().strftime('%Y%m%d')}-B{self.jenkins_build}"

        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        # Story (content) for PDF
        self.story = []

    def _load_summary(self):
        """Load summary.json from input directory"""
        summary_file = self.input_dir / "summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                return json.load(f)
        return {
            "total_findings": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a4d7c'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a4d7c'),
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='RiskCritical',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.white,
            backColor=colors.HexColor('#d32f2f'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=24
        ))

    def _calculate_risk_score(self):
        """Calculate overall risk score"""
        critical = self.summary.get("critical", 0)
        high = self.summary.get("high", 0)
        medium = self.summary.get("medium", 0)

        # Risk Score = (CRITICAL × 4 + HIGH × 2 + MEDIUM × 1) / 10
        score = (critical * 4 + high * 2 + medium * 1) / 10.0

        if score >= 10:
            level = "CRITICAL"
            color = "#d32f2f"
        elif score >= 7:
            level = "HIGH"
            color = "#f57c00"
        elif score >= 3:
            level = "MEDIUM"
            color = "#fbc02d"
        else:
            level = "LOW"
            color = "#388e3c"

        return round(score, 1), level, color

    def add_cover_page(self):
        """Add cover page"""
        # Logo (if exists)
        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            try:
                img = Image(str(logo_path), width=2*inch, height=0.8*inch)
                self.story.append(img)
                self.story.append(Spacer(1, 0.3*inch))
            except:
                pass  # Skip if logo can't be loaded

        # Watermark
        watermark = Paragraph(
            "When No One Has the Answers™",
            ParagraphStyle('watermark', fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
        )
        self.story.append(watermark)
        self.story.append(Spacer(1, 1.5*inch))

        # Title
        title = Paragraph("TTS SECURITY ASSESSMENT<br/>REPORT", self.styles['CustomTitle'])
        self.story.append(title)
        self.story.append(Spacer(1, 0.3*inch))

        subtitle = Paragraph(
            "Comprehensive Security Scan Analysis",
            ParagraphStyle('subtitle', fontSize=12, textColor=colors.grey, alignment=TA_CENTER)
        )
        self.story.append(subtitle)
        self.story.append(Spacer(1, 0.8*inch))

        # Project Information Table
        data = [
            ['Document Number:', self.doc_number],
            ['Project Name:', f"{self.project_name}"],
            ['Component:', self.component_name],
            ['Scan Date:', self.scan_date],
            ['Jenkins Build:', f"#{self.jenkins_build}"],
            ['Git Repository:', self.git_repo],
            ['Git Branch:', self.git_branch],
            ['Contact Email:', self.contact_email],
            ['Developer:', self.developer],
            ['DevOps Engineer:', self.devops_engineer],
            ['Total Findings:', str(self.summary.get('total_findings', 0))]
        ]

        table = Table(data, colWidths=[2.2*inch, 4.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 0.5*inch))

        # Risk Level Box
        risk_score, risk_level, risk_color = self._calculate_risk_score()
        risk_text = f"OVERALL RISK LEVEL: {risk_level} ({risk_score}/10)"

        risk_para = Paragraph(
            risk_text,
            ParagraphStyle(
                'risk',
                fontSize=16,
                textColor=colors.white,
                backColor=colors.HexColor(risk_color),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                leading=30,
                leftIndent=10,
                rightIndent=10,
                spaceBefore=10,
                spaceAfter=10
            )
        )
        self.story.append(risk_para)

        self.story.append(PageBreak())

    def add_executive_summary(self):
        """Add executive summary"""
        self.story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))

        risk_score, risk_level, _ = self._calculate_risk_score()

        summary_text = f"""
        This security assessment report presents the findings from a comprehensive security scan of the
        {self.component_name} component. The scan was performed on {self.scan_date} using industry-standard
        security tools including Semgrep, Trivy, and TruffleHog.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • Total Security Findings: {self.summary.get('total_findings', 0)}<br/>
        • Critical Severity: {self.summary.get('critical', 0)}<br/>
        • High Severity: {self.summary.get('high', 0)}<br/>
        • Medium Severity: {self.summary.get('medium', 0)}<br/>
        • Low Severity: {self.summary.get('low', 0)}<br/>
        <br/>
        <b>Overall Risk Score:</b> {risk_score}/10 ({risk_level})<br/>
        """

        self.story.append(Paragraph(summary_text, self.styles['Normal']))
        self.story.append(Spacer(1, 0.3*inch))

    def add_findings_breakdown(self):
        """Add detailed findings breakdown"""
        self.story.append(Paragraph("FINDINGS BREAKDOWN", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))

        # Severity Summary Table
        data = [
            ['Severity', 'Count', 'Percentage'],
            ['Critical', str(self.summary.get('critical', 0)),
             f"{(self.summary.get('critical', 0) / max(self.summary.get('total_findings', 1), 1) * 100):.1f}%"],
            ['High', str(self.summary.get('high', 0)),
             f"{(self.summary.get('high', 0) / max(self.summary.get('total_findings', 1), 1) * 100):.1f}%"],
            ['Medium', str(self.summary.get('medium', 0)),
             f"{(self.summary.get('medium', 0) / max(self.summary.get('total_findings', 1), 1) * 100):.1f}%"],
            ['Low', str(self.summary.get('low', 0)),
             f"{(self.summary.get('low', 0) / max(self.summary.get('total_findings', 1), 1) * 100):.1f}%"],
        ]

        table = Table(data, colWidths=[2*inch, 1.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))

    def add_severity_definitions(self):
        """Add severity level definitions"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("SEVERITY LEVEL DEFINITIONS", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))

        data = [
            ['Severity', 'Definition', 'Action Required'],
            ['CRITICAL', 'Exploitable vulnerabilities or exposed secrets', 'Immediate remediation'],
            ['HIGH', 'Significant security risks', 'Fix within 1 week'],
            ['MEDIUM', 'Important security issues', 'Fix within 1 month'],
            ['LOW', 'Minor security issues', 'Monitor and improve'],
            ['INFO', 'Informational findings', 'Consider for future work']
        ]

        table = Table(data, colWidths=[1.2*inch, 3*inch, 2.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('WORDWRAP', (0, 0), (-1, -1), True)
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))

        # Risk Scoring Methodology
        self.story.append(Paragraph("RISK SCORING METHODOLOGY", self.styles['Heading3']))
        self.story.append(Spacer(1, 0.1*inch))

        methodology_text = """
        The overall risk score is calculated using a weighted formula that prioritizes critical and
        high-severity findings:<br/><br/>
        <b>Risk Score = (CRITICAL × 4 + HIGH × 2 + MEDIUM × 1) / 10</b><br/><br/>
        <b>Risk Level Thresholds:</b><br/>
        • 0.0 - 3.0: LOW (Minimal security concerns)<br/>
        • 3.0 - 5.0: MEDIUM (Some security issues identified)<br/>
        • 5.0 - 7.0: HIGH (Significant security concerns)<br/>
        • 7.0 - 10.0: CRITICAL (Severe security vulnerabilities)<br/>
        • 10.0+: CRITICAL (Critical security crisis)
        """

        self.story.append(Paragraph(methodology_text, self.styles['Normal']))
        self.story.append(Spacer(1, 0.3*inch))

    def add_sonarqube_section(self):
        """Add SonarQube integration section"""
        if not self.sonarqube_url:
            return

        self.story.append(PageBreak())
        self.story.append(Paragraph("SONARQUBE CODE QUALITY ANALYSIS", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))

        sonar_text = f"""
        In addition to security scanning, this project undergoes continuous code quality analysis
        through SonarQube. SonarQube provides insights into code quality, maintainability, reliability,
        and security.<br/><br/>
        <b>SonarQube Dashboard:</b><br/>
        {self.sonarqube_url}<br/><br/>
        <b>Analysis Includes:</b><br/>
        • Code Smells and Bugs<br/>
        • Security Hotspots<br/>
        • Code Coverage<br/>
        • Code Duplication<br/>
        • Technical Debt Assessment<br/><br/>
        Please review the SonarQube dashboard for detailed code quality metrics and trends.
        """

        self.story.append(Paragraph(sonar_text, self.styles['Normal']))
        self.story.append(Spacer(1, 0.3*inch))

    def add_contact_support(self):
        """Add contact and support information"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("CONTACT & SUPPORT", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))

        contact_text = """
        For questions, concerns, or assistance regarding this security assessment report,
        please contact the TTS Security and DevOps teams.
        """
        self.story.append(Paragraph(contact_text, self.styles['Normal']))
        self.story.append(Spacer(1, 0.2*inch))

        # Contact table (without Purpose column)
        data = [
            ['Department', 'Contact'],
            ['Security Team', self.contact_email],
            ['DevOps Team', self.devops_engineer],
            ['Development Team', self.developer],
            ['TTS Support', 'support@ttsme.com']
        ]

        table = Table(data, colWidths=[2*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))

        # Reporting False Positives
        self.story.append(Paragraph("REPORTING FALSE POSITIVES OR ISSUES", self.styles['Heading3']))
        self.story.append(Spacer(1, 0.1*inch))

        false_positive_text = f"""
        If you believe any findings in this report are false positives or require clarification:<br/><br/>
        <b>1.</b> Document the specific finding (page number, issue ID, file location)<br/>
        <b>2.</b> Provide justification or evidence showing why it's a false positive<br/>
        <b>3.</b> Email the details to {self.contact_email} with subject: "Security Scan False Positive - {self.component_name}"<br/>
        <b>4.</b> The security team will review within 2 business days<br/><br/>
        For urgent security concerns or active incidents, contact the security team immediately.
        """

        self.story.append(Paragraph(false_positive_text, self.styles['Normal']))

    def generate(self):
        """Generate the PDF report"""
        print(f"Generating security report: {self.output_file}")

        # Create PDF document
        doc = SimpleDocTemplate(
            str(self.output_file),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Add content
        self.add_cover_page()
        self.add_executive_summary()
        self.add_findings_breakdown()
        self.add_severity_definitions()
        self.add_sonarqube_section()
        self.add_contact_support()

        # Build PDF
        doc.build(self.story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)

        print(f"✅ Report generated successfully: {self.output_file}")
        return str(self.output_file)

    def _add_page_number(self, canvas, doc):
        """Add page number and footer to each page"""
        canvas.saveState()

        # Footer
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.grey)
        canvas.drawString(
            0.75*inch,
            0.5*inch,
            f"INTERNAL USE ONLY | Doc: {self.doc_number}"
        )

        # Page number
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(7.5*inch, 0.5*inch, text)

        canvas.restoreState()


def main():
    parser = argparse.ArgumentParser(
        description="TTS Security Report Generator - Generate PDF security reports"
    )

    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing security scan JSON files"
    )

    parser.add_argument(
        "--output-file",
        help="Output PDF file path (auto-generated if not specified)"
    )

    parser.add_argument(
        "--project-name",
        required=True,
        help="Project name (e.g., ADXSIP)"
    )

    parser.add_argument(
        "--component-name",
        required=True,
        help="Component name (e.g., ADXSIP Backend)"
    )

    parser.add_argument(
        "--git-repo",
        required=True,
        help="Git repository URL"
    )

    parser.add_argument(
        "--git-branch",
        required=True,
        help="Git branch name"
    )

    parser.add_argument(
        "--contact-email",
        default="security@ttsme.com",
        help="Contact email for security issues"
    )

    parser.add_argument(
        "--developer",
        default="Development Team",
        help="Developer name or team"
    )

    parser.add_argument(
        "--devops-engineer",
        default="Kannan Giridharan",
        help="DevOps engineer name"
    )

    parser.add_argument(
        "--sonarqube-url",
        help="SonarQube dashboard URL (optional)"
    )

    args = parser.parse_args()

    # Validate input directory
    if not os.path.exists(args.input_dir):
        print(f"ERROR: Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    # Generate report
    generator = SecurityReportGenerator(args)
    report_path = generator.generate()

    print(f"\n📄 Security report: {report_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
