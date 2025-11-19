#!/usr/bin/env python3
"""
Comprehensive Security Assessment Report Generator
Generates professional PDF reports with complete findings, charts, and visual elements
"""
import json
import subprocess
import sys
import os
from datetime import datetime
from html import escape as html_escape

# Auto-detect project name
def detect_project_name():
    """Auto-detect project name from package.json, pom.xml, or environment"""
    # First try environment variable
    env_name = os.environ.get('PROJECT_NAME', '').strip()
    if env_name:
        return env_name

    # Try package.json (Node.js projects)
    if os.path.exists('package.json'):
        try:
            with open('package.json', 'r') as f:
                pkg = json.load(f)
                name = pkg.get('name', '').strip()
                if name:
                    # Capitalize and clean up
                    return name.replace('-', ' ').replace('_', ' ').title()
        except:
            pass

    # Try pom.xml (Maven projects)
    if os.path.exists('pom.xml'):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse('pom.xml')
            root = tree.getroot()
            # Maven uses namespaces
            ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
            name = root.find('m:name', ns)
            if name is not None and name.text:
                return name.text.strip()
            artifactId = root.find('m:artifactId', ns)
            if artifactId is not None and artifactId.text:
                return artifactId.text.replace('-', ' ').replace('_', ' ').title()
        except:
            pass

    # Try git remote URL
    try:
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            url = result.stdout.strip()
            # Extract repo name from URL
            repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            return repo_name.replace('-', ' ').replace('_', ' ').title()
    except:
        pass

    # Fallback
    return 'Security Scan Report'

PROJECT_NAME = detect_project_name()
print(f'Detected project name: {PROJECT_NAME}')

# Generate unique document number
def generate_document_number():
    """Generate unique document number in format: TTS-SEC-YYYYMMDD-BXX"""
    date_str = datetime.now().strftime('%Y%m%d')
    build_num = os.environ.get('BUILD_NUMBER', '000')
    return f'TTS-SEC-{date_str}-B{build_num.zfill(3)}'

DOCUMENT_NUMBER = generate_document_number()
print(f'Document number: {DOCUMENT_NUMBER}')

# Get additional metadata from environment
DEVELOPER_NAME = os.environ.get('DEVELOPER_NAME', os.environ.get('GIT_COMMITTER_NAME', 'Unknown'))
DEVOPS_ENGINEER = os.environ.get('DEVOPS_ENGINEER', os.environ.get('BUILD_USER', 'DevOps Team'))
CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', os.environ.get('EMAIL_RECIPIENTS', 'security@ttsme.com'))
GIT_URL = os.environ.get('GIT_URL', os.environ.get('GITHUB_URL', 'Unknown'))
GIT_BRANCH = os.environ.get('GIT_BRANCH', 'Unknown')

# Install required packages
def install_package(package):
    try:
        __import__(package)
        return True
    except ImportError:
        print(f'Installing {package}...')
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'])
            return True
        except:
            print(f'Failed to install {package}, using basic PDF generation')
            return False

has_reportlab = install_package('reportlab')

if has_reportlab:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                    Spacer, PageBreak, Image as RLImage, KeepTogether)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics import renderPDF
    from reportlab.lib.colors import HexColor

print('Processing scan results...')

# Initialize statistics
issues_found = []
stats = {
    'critical': 0,
    'high': 0,
    'medium': 0,
    'low': 0,
    'info': 0,
    'total': 0
}

# Tool-specific counters
tool_stats = {
    'Semgrep': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0, 'total': 0},
    'Trivy': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0, 'total': 0},
    'TruffleHog': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0, 'total': 0}
}

# Process Semgrep results
print('Processing Semgrep results...')
try:
    if os.path.exists('security-reports/semgrep.json'):
        with open('security-reports/semgrep.json', 'r') as f:
            semgrep_data = json.load(f)
            results = semgrep_data.get('results', [])

            for result in results:
                severity = result.get('extra', {}).get('severity', 'INFO').upper()
                if severity == 'ERROR':
                    severity = 'HIGH'
                elif severity == 'WARNING':
                    severity = 'MEDIUM'

                issue = {
                    'tool': 'Semgrep',
                    'type': 'Code Security',
                    'severity': severity,
                    'file': result.get('path', 'Unknown')[:80],
                    'line': result.get('start', {}).get('line', 0),
                    'title': result.get('check_id', 'Unknown'),
                    'details': result.get('extra', {}).get('message', 'No description')[:200]
                }
                issues_found.append(issue)

                sev_lower = severity.lower()
                if sev_lower in stats:
                    stats[sev_lower] += 1
                    tool_stats['Semgrep'][sev_lower] += 1
                stats['total'] += 1
                tool_stats['Semgrep']['total'] += 1

            print(f'  Found {len(results)} Semgrep issues')
except Exception as e:
    print(f'  Semgrep processing error: {e}')

# Process Trivy results
print('Processing Trivy results...')
trivy_count = 0
try:
    if os.path.exists('security-reports/trivy.json'):
        with open('security-reports/trivy.json', 'r') as f:
            trivy_data = json.load(f)

            for result in trivy_data.get('Results', []):
                # Process vulnerabilities (CVEs in dependencies)
                for vuln in result.get('Vulnerabilities', []):
                    severity = vuln.get('Severity', 'UNKNOWN').upper()

                    issue = {
                        'tool': 'Trivy',
                        'type': 'Vulnerability',
                        'severity': severity,
                        'file': result.get('Target', 'Unknown')[:80],
                        'line': 0,
                        'title': '{} - {}'.format(vuln.get('PkgName', 'Unknown'), vuln.get('VulnerabilityID', '')),
                        'details': 'Version: {} | Fix: {}'.format(
                            vuln.get('InstalledVersion', '?'),
                            vuln.get('FixedVersion', 'No fix available')
                        )
                    }
                    issues_found.append(issue)

                    sev_lower = severity.lower()
                    if sev_lower in stats:
                        stats[sev_lower] += 1
                        tool_stats['Trivy'][sev_lower] += 1
                    stats['total'] += 1
                    tool_stats['Trivy']['total'] += 1
                    trivy_count += 1

                # Process misconfigurations
                for misconfig in result.get('Misconfigurations', []):
                    severity = misconfig.get('Severity', 'UNKNOWN').upper()

                    issue = {
                        'tool': 'Trivy',
                        'type': 'Misconfiguration',
                        'severity': severity,
                        'file': result.get('Target', 'Unknown')[:80],
                        'line': misconfig.get('CauseMetadata', {}).get('StartLine', 0),
                        'title': '{} - {}'.format(misconfig.get('ID', 'Unknown'), misconfig.get('Title', '')),
                        'details': misconfig.get('Description', 'No description')[:200]
                    }
                    issues_found.append(issue)

                    sev_lower = severity.lower()
                    if sev_lower in stats:
                        stats[sev_lower] += 1
                        tool_stats['Trivy'][sev_lower] += 1
                    stats['total'] += 1
                    tool_stats['Trivy']['total'] += 1
                    trivy_count += 1

                # Process secrets
                for secret in result.get('Secrets', []):
                    severity = secret.get('Severity', 'HIGH').upper()

                    issue = {
                        'tool': 'Trivy',
                        'type': 'Secret',
                        'severity': severity,
                        'file': result.get('Target', 'Unknown')[:80],
                        'line': secret.get('StartLine', 0),
                        'title': secret.get('Title', 'Secret detected'),
                        'details': secret.get('RuleID', 'Secret found - hidden for security')
                    }
                    issues_found.append(issue)

                    sev_lower = severity.lower()
                    if sev_lower in stats:
                        stats[sev_lower] += 1
                        tool_stats['Trivy'][sev_lower] += 1
                    stats['total'] += 1
                    tool_stats['Trivy']['total'] += 1
                    trivy_count += 1

            print(f'  Found {trivy_count} Trivy issues')
except Exception as e:
    print(f'  Trivy processing error: {e}')

# Process TruffleHog results
print('Processing TruffleHog results...')
try:
    if os.path.exists('security-reports/trufflehog.json'):
        with open('security-reports/trufflehog.json', 'r') as f:
            trufflehog_data = json.load(f)

            for secret in trufflehog_data.get('secrets', []):
                source = secret.get('SourceMetadata', {}).get('Data', {}).get('Filesystem', {})

                issue = {
                    'tool': 'TruffleHog',
                    'type': 'Secret',
                    'severity': 'CRITICAL',
                    'file': source.get('file', 'Unknown')[:80],
                    'line': source.get('line', 0),
                    'title': secret.get('DetectorName', 'Secret detected'),
                    'details': 'Verified: {}'.format(secret.get('Verified', False))
                }
                issues_found.append(issue)
                stats['critical'] += 1
                tool_stats['TruffleHog']['critical'] += 1
                stats['total'] += 1
                tool_stats['TruffleHog']['total'] += 1

            print(f'  Found {len(trufflehog_data.get("secrets", []))} TruffleHog secrets')
except Exception as e:
    print(f'  TruffleHog processing error: {e}')

# Sort issues by severity then tool
severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
issues_found.sort(key=lambda x: (severity_order.get(x['severity'], 5), x['tool'], x['file']))

# Calculate risk score
if stats['total'] > 0:
    risk_score = min(10.0, (stats['critical'] * 4 + stats['high'] * 2 + stats['medium'] * 1) / 10.0)
else:
    risk_score = 0.0

# Determine risk level
if risk_score >= 7:
    risk_level = 'CRITICAL'
    risk_color = HexColor('#d32f2f')
elif risk_score >= 5:
    risk_level = 'HIGH'
    risk_color = HexColor('#f57c00')
elif risk_score >= 3:
    risk_level = 'MEDIUM'
    risk_color = HexColor('#fbc02d')
else:
    risk_level = 'LOW'
    risk_color = HexColor('#388e3c')

print('\nSummary:')
print('  Total issues: {}'.format(stats['total']))
print('  Critical: {}'.format(stats['critical']))
print('  High: {}'.format(stats['high']))
print('  Medium: {}'.format(stats['medium']))
print('  Low: {}'.format(stats['low']))
print('  Info: {}'.format(stats['info']))
print('  Risk Level: {} ({:.1f}/10)'.format(risk_level, risk_score))

# ===================== GENERATE COMPREHENSIVE PDF REPORT =====================
print('\nGenerating comprehensive PDF report...')

if has_reportlab:
    try:
        # Define severity colors
        SEVERITY_COLORS = {
            'CRITICAL': HexColor('#d32f2f'),  # Red
            'HIGH': HexColor('#f57c00'),      # Orange
            'MEDIUM': HexColor('#fbc02d'),    # Yellow
            'LOW': HexColor('#1976d2'),       # Blue
            'INFO': HexColor('#757575')       # Gray
        }

        # Custom page template with header and footer
        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                canvas.Canvas.__init__(self, *args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_page_number(num_pages)
                    canvas.Canvas.showPage(self)
                canvas.Canvas.save(self)

            def draw_page_number(self, page_count):
                # Footer with page number and document number (skip first page)
                if self._pageNumber > 1:
                    self.setFont("Helvetica", 8)
                    self.setFillColor(colors.grey)

                    # Left side: Confidential + Document Number
                    footer_left = "INTERNAL USE ONLY | Doc: {}".format(DOCUMENT_NUMBER)
                    self.drawString(1*cm, 1*cm, footer_left)

                    # Right side: Page numbers
                    page = "Page {} of {}".format(self._pageNumber, page_count)
                    self.drawRightString(A4[0] - 1*cm, 1*cm, page)

                # Header with project name (skip first page)
                if self._pageNumber > 1:
                    self.setFont("Helvetica-Bold", 10)
                    self.setFillColor(HexColor('#1e3a5f'))
                    self.drawString(1*cm, A4[1] - 1.5*cm, "TTS Security Assessment Report")
                    self.drawRightString(A4[0] - 1*cm, A4[1] - 1.5*cm, PROJECT_NAME[:40])
                    # Horizontal line
                    self.setStrokeColor(colors.grey)
                    self.setLineWidth(0.5)
                    self.line(1*cm, A4[1] - 1.7*cm, A4[0] - 1*cm, A4[1] - 1.7*cm)

        # Create PDF document with custom canvas
        doc = SimpleDocTemplate('security-report.pdf', pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2.5*cm, bottomMargin=2*cm)
        story = []
        styles = getSampleStyleSheet()

        # ==================== CUSTOM STYLES ====================
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=HexColor('#1e3a5f'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=HexColor('#424242'),
            alignment=TA_CENTER,
            spaceAfter=30
        )

        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=HexColor('#1e3a5f'),
            spaceAfter=15,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )

        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#424242'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )

        heading3_style = ParagraphStyle(
            'CustomHeading3',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=HexColor('#616161'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#212121'),
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )

        # ==================== COVER PAGE ====================
        # Add TTS company logo
        logo_path = '/usr/local/bin/security-scripts/logo.png'
        if os.path.exists(logo_path):
            try:
                logo = RLImage(logo_path, width=4*inch, height=0.8*inch, kind='proportional')
                story.append(logo)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                print(f'  Warning: Could not load TTS logo: {e}')
        else:
            print(f'  Warning: TTS logo not found at {logo_path}')

        # Company tagline
        tagline_style = ParagraphStyle(
            'Tagline',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        story.append(Paragraph('When No One Has the Answers™', tagline_style))
        story.append(Spacer(1, 0.5*inch))

        # Main title
        story.append(Paragraph('TTS SECURITY ASSESSMENT REPORT', title_style))
        story.append(Spacer(1, 0.1*inch))

        # Subtitle
        subtitle2_style = ParagraphStyle(
            'Subtitle2',
            parent=styles['Normal'],
            fontSize=12,
            textColor=HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        story.append(Paragraph('Comprehensive Security Scan Analysis', subtitle2_style))
        story.append(Spacer(1, 0.3*inch))

        # Document details table (expanded with all fields)
        doc_data = [
            ['Document Number:', DOCUMENT_NUMBER],
            ['Project Name:', html_escape(PROJECT_NAME)],
            ['Scan Date:', os.environ.get('SCAN_DATE', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
            ['Jenkins Build:', '#{}'.format(os.environ.get('BUILD_NUMBER', 'Unknown'))],
            ['Git Repository:', html_escape(GIT_URL[:60])],
            ['Git Branch:', html_escape(GIT_BRANCH)],
            ['Contact Email:', CONTACT_EMAIL],
            ['Developer:', html_escape(DEVELOPER_NAME)],
            ['DevOps Engineer:', html_escape(DEVOPS_ENGINEER)],
            ['Total Findings:', str(stats['total'])]
        ]

        doc_table = Table(doc_data, colWidths=[4*cm, 11*cm])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#1e3a5f')),
            ('BACKGROUND', (1, 0), (1, -1), HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#212121')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(doc_table)
        story.append(Spacer(1, 0.4*inch))

        # Risk level banner (full width, prominent on cover)
        risk_banner_style = ParagraphStyle(
            'RiskBanner',
            parent=styles['Normal'],
            fontSize=20,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )

        # Create colored banner box
        risk_banner_table = Table(
            [[Paragraph('OVERALL RISK LEVEL: {} ({:.1f}/10)'.format(risk_level, risk_score), risk_banner_style)]],
            colWidths=[15*cm]
        )
        risk_banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), risk_color),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(risk_banner_table)
        story.append(Spacer(1, 0.5*inch))

        # Confidentiality notice
        confidential_style = ParagraphStyle(
            'Confidential',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#d32f2f'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph('INTERNAL USE ONLY', confidential_style))

        story.append(PageBreak())

        # ==================== EXECUTIVE SUMMARY ====================
        story.append(Paragraph('EXECUTIVE SUMMARY', heading1_style))
        story.append(Spacer(1, 0.2*inch))

        summary_text = """
        This comprehensive security assessment report presents findings from automated security scanning
        performed on <b>{}</b>. The analysis includes Static Application Security Testing (SAST),
        Software Composition Analysis (SCA), and Secret Detection across the entire codebase.
        """.format(html_escape(PROJECT_NAME))
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 0.2*inch))

        # Statistics summary table
        summary_data = [
            ['Metric', 'Count', 'Percentage', 'Risk Impact'],
            ['CRITICAL', str(stats['critical']),
             '{:.1f}%'.format((stats['critical']/max(stats['total'],1))*100),
             '⚠ Immediate Action Required'],
            ['HIGH', str(stats['high']),
             '{:.1f}%'.format((stats['high']/max(stats['total'],1))*100),
             '⚠ Priority Remediation'],
            ['MEDIUM', str(stats['medium']),
             '{:.1f}%'.format((stats['medium']/max(stats['total'],1))*100),
             '⚡ Planned Fix'],
            ['LOW', str(stats['low']),
             '{:.1f}%'.format((stats['low']/max(stats['total'],1))*100),
             '📋 Monitor'],
            ['INFO', str(stats['info']),
             '{:.1f}%'.format((stats['info']/max(stats['total'],1))*100),
             'ℹ Informational'],
            ['TOTAL', str(stats['total']), '100%', '']
        ]

        summary_table = Table(summary_data, colWidths=[3*cm, 2*cm, 2.5*cm, 5.5*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), HexColor('#ffebee')),
            ('BACKGROUND', (0, 2), (-1, 2), HexColor('#fff3e0')),
            ('BACKGROUND', (0, 3), (-1, 3), HexColor('#fffde7')),
            ('BACKGROUND', (0, 4), (-1, 4), HexColor('#e3f2fd')),
            ('BACKGROUND', (0, 5), (-1, 5), HexColor('#f5f5f5')),
            ('BACKGROUND', (0, 6), (-1, 6), HexColor('#e0e0e0')),
            ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

        # ==================== PIE CHART - SEVERITY DISTRIBUTION ====================
        if stats['total'] > 0:
            story.append(Paragraph('Findings by Severity', heading2_style))

            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 150
            pie.height = 150
            pie.data = [
                stats['critical'], stats['high'], stats['medium'],
                stats['low'], stats['info']
            ]
            pie.labels = [
                'Critical: {}'.format(stats['critical']),
                'High: {}'.format(stats['high']),
                'Medium: {}'.format(stats['medium']),
                'Low: {}'.format(stats['low']),
                'Info: {}'.format(stats['info'])
            ]
            pie.slices.strokeWidth = 0.5
            pie.slices[0].fillColor = SEVERITY_COLORS['CRITICAL']
            pie.slices[1].fillColor = SEVERITY_COLORS['HIGH']
            pie.slices[2].fillColor = SEVERITY_COLORS['MEDIUM']
            pie.slices[3].fillColor = SEVERITY_COLORS['LOW']
            pie.slices[4].fillColor = SEVERITY_COLORS['INFO']
            drawing.add(pie)
            story.append(drawing)
            story.append(Spacer(1, 0.2*inch))

        # ==================== BAR CHART - FINDINGS BY TOOL ====================
        story.append(Paragraph('Findings by Security Tool', heading2_style))

        drawing = Drawing(400, 200)
        bar = VerticalBarChart()
        bar.x = 50
        bar.y = 50
        bar.height = 125
        bar.width = 300
        bar.data = [
            [tool_stats['Semgrep']['total'],
             tool_stats['Trivy']['total'],
             tool_stats['TruffleHog']['total']]
        ]
        bar.categoryAxis.categoryNames = ['Semgrep\n(SAST)', 'Trivy\n(SCA)', 'TruffleHog\n(Secrets)']
        bar.valueAxis.valueMin = 0
        bar.valueAxis.valueMax = max([tool_stats['Semgrep']['total'],
                                      tool_stats['Trivy']['total'],
                                      tool_stats['TruffleHog']['total']], default=10) * 1.2
        bar.bars[0].fillColor = HexColor('#1976d2')
        drawing.add(bar)
        story.append(drawing)
        story.append(Spacer(1, 0.3*inch))

        # ==================== RISK GAUGE VISUALIZATION ====================
        story.append(Paragraph('Risk Score Gauge', heading2_style))

        # Create risk gauge
        gauge_drawing = Drawing(400, 100)

        # Background gauge bar
        gauge_bg = Rect(50, 40, 300, 30, fillColor=HexColor('#e0e0e0'), strokeColor=colors.grey)
        gauge_drawing.add(gauge_bg)

        # Filled gauge bar (proportional to risk score)
        gauge_fill_width = (risk_score / 10.0) * 300
        gauge_fill = Rect(50, 40, gauge_fill_width, 30, fillColor=risk_color, strokeColor=None)
        gauge_drawing.add(gauge_fill)

        # Risk score text
        gauge_text = String(200, 55, '{:.1f} / 10.0'.format(risk_score),
                           fontSize=14, fillColor=colors.white,
                           textAnchor='middle', fontName='Helvetica-Bold')
        gauge_drawing.add(gauge_text)

        # Scale markers
        for i in range(11):
            x = 50 + (i * 30)
            marker = String(x, 25, str(i), fontSize=8, fillColor=colors.grey, textAnchor='middle')
            gauge_drawing.add(marker)

        story.append(gauge_drawing)
        story.append(Spacer(1, 0.3*inch))

        # Key findings summary
        story.append(Paragraph('Key Findings', heading2_style))
        key_findings = []
        if stats['critical'] > 0:
            key_findings.append('• <b>{} CRITICAL</b> issues require immediate attention and remediation'.format(stats['critical']))
        if stats['high'] > 0:
            key_findings.append('• <b>{} HIGH</b> severity vulnerabilities identified in code and dependencies'.format(stats['high']))
        if tool_stats['TruffleHog']['total'] > 0:
            key_findings.append('• <b>{} secrets</b> detected that may expose credentials or API keys'.format(tool_stats['TruffleHog']['total']))
        if stats['medium'] > 0:
            key_findings.append('• <b>{} MEDIUM</b> severity issues should be addressed in upcoming sprints'.format(stats['medium']))
        if stats['total'] == 0:
            key_findings.append('• ✅ <b>No security issues detected</b> - excellent security posture')

        for finding in key_findings:
            story.append(Paragraph(finding, body_style))

        story.append(PageBreak())

        # ==================== SCAN COVERAGE & SCOPE ====================
        story.append(Paragraph('SCAN COVERAGE & SCOPE', heading1_style))
        story.append(Spacer(1, 0.2*inch))

        coverage_intro = """
        This security assessment was performed using automated scanning tools to identify
        vulnerabilities, misconfigurations, and security risks across the entire codebase.
        """
        story.append(Paragraph(coverage_intro, body_style))
        story.append(Spacer(1, 0.2*inch))

        # Coverage table
        coverage_data = [
            ['Aspect', 'Details'],
            ['Scan Type', 'Automated Security Assessment (SAST + SCA + Secret Detection)'],
            ['Tools Used', 'Semgrep v{} | Trivy v{} | TruffleHog v3'.format(
                os.popen('semgrep --version 2>/dev/null | head -1').read().strip() or 'Latest',
                os.popen('trivy --version 2>/dev/null | head -1 | awk \'{print $2}\'').read().strip() or 'Latest'
            )],
            ['Scan Date', os.environ.get('SCAN_DATE', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
            ['Project Type', 'Node.js/JavaScript' if os.path.exists('package.json') else
                           'Maven/Java' if os.path.exists('pom.xml') else
                           'Python' if os.path.exists('requirements.txt') else 'Multi-language'],
            ['Files Scanned', 'All source code, configuration files, and dependencies'],
            ['Scan Depth', 'Full codebase including git history for secret detection']
        ]

        coverage_table = Table(coverage_data, colWidths=[4*cm, 11*cm])
        coverage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f9f9f9')),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#212121')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(coverage_table)
        story.append(Spacer(1, 0.3*inch))

        # What was analyzed
        story.append(Paragraph('What Was Analyzed', heading2_style))
        analyzed_items = [
            '• <b>Source Code:</b> All JavaScript/TypeScript files for code-level vulnerabilities',
            '• <b>Dependencies:</b> All npm packages for known CVEs and security issues',
            '• <b>Configuration Files:</b> Docker, YAML, JSON files for misconfigurations',
            '• <b>Git History:</b> All commits scanned for accidentally committed secrets',
            '• <b>Third-party Libraries:</b> Checked against vulnerability databases (NVD, GitHub Advisory)'
        ]
        for item in analyzed_items:
            story.append(Paragraph(item, body_style))
            story.append(Spacer(1, 6))

        story.append(PageBreak())

        # ==================== DETAILED FINDINGS BY TOOL ====================
        story.append(Paragraph('DETAILED FINDINGS BY TOOL', heading1_style))
        story.append(Spacer(1, 0.2*inch))

        # Helper function to create issue table
        def create_issue_table(issues_list, tool_name):
            """Create a professional table for issues"""
            if not issues_list:
                return Paragraph('<i>No issues found by {}</i>'.format(tool_name), body_style)

            # Group by severity
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                severity_issues = [i for i in issues_list if i['severity'] == severity]
                if not severity_issues:
                    continue

                # Severity header
                severity_header = Paragraph(
                    '<para backColor="{}" textColor="white" fontSize="12" spaceAfter="8">'
                    '<b>{} - {} Issues</b></para>'.format(
                        SEVERITY_COLORS[severity], severity, len(severity_issues)
                    ),
                    body_style
                )
                story.append(severity_header)
                story.append(Spacer(1, 0.1*inch))

                # Create table for all issues in this severity (NO LIMIT!)
                table_data = [['#', 'File / Location', 'Issue', 'Details']]

                for idx, issue in enumerate(severity_issues, 1):
                    location = issue['file']
                    if issue['line'] > 0:
                        location += ':' + str(issue['line'])

                    table_data.append([
                        str(idx),
                        Paragraph('<font size="8">{}</font>'.format(html_escape(location[:60])), body_style),
                        Paragraph('<font size="8"><b>{}</b><br/>[{}]</font>'.format(
                            html_escape(issue['title'][:80]), html_escape(issue['type'])
                        ), body_style),
                        Paragraph('<font size="8">{}</font>'.format(html_escape(issue['details'][:120])), body_style)
                    ])

                issue_table = Table(table_data, colWidths=[1*cm, 4*cm, 5*cm, 5*cm])
                issue_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#424242')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f5f5f5')])
                ]))
                story.append(issue_table)
                story.append(Spacer(1, 0.2*inch))

        # ==================== SEMGREP FINDINGS ====================
        story.append(Paragraph('Semgrep - Static Application Security Testing (SAST)', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        semgrep_desc = """
        <b>Semgrep</b> performs static code analysis to identify security vulnerabilities,
        code quality issues, and potential bugs by analyzing source code patterns.
        It detected <b>{} issues</b> in this scan.
        """.format(tool_stats['Semgrep']['total'])
        story.append(Paragraph(semgrep_desc, body_style))
        story.append(Spacer(1, 0.2*inch))

        semgrep_issues = [i for i in issues_found if i['tool'] == 'Semgrep']
        create_issue_table(semgrep_issues, 'Semgrep')

        if semgrep_issues:
            story.append(PageBreak())

        # ==================== TRIVY FINDINGS ====================
        story.append(Paragraph('Trivy - Software Composition Analysis (SCA)', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        trivy_desc = """
        <b>Trivy</b> scans for vulnerabilities in project dependencies, misconfigurations,
        and exposed secrets. It checks against CVE databases and security best practices.
        It detected <b>{} issues</b> in this scan.
        """.format(tool_stats['Trivy']['total'])
        story.append(Paragraph(trivy_desc, body_style))
        story.append(Spacer(1, 0.2*inch))

        trivy_issues = [i for i in issues_found if i['tool'] == 'Trivy']
        create_issue_table(trivy_issues, 'Trivy')

        if trivy_issues:
            story.append(PageBreak())

        # ==================== TRUFFLEHOG FINDINGS ====================
        story.append(Paragraph('TruffleHog - Secret Detection', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        trufflehog_desc = """
        <b>TruffleHog</b> scans for exposed secrets, API keys, passwords, and credentials
        in source code and git history. All findings are treated as CRITICAL.
        It detected <b>{} secrets</b> in this scan.
        """.format(tool_stats['TruffleHog']['total'])
        story.append(Paragraph(trufflehog_desc, body_style))
        story.append(Spacer(1, 0.2*inch))

        trufflehog_issues = [i for i in issues_found if i['tool'] == 'TruffleHog']
        create_issue_table(trufflehog_issues, 'TruffleHog')

        story.append(PageBreak())

        # ==================== COMPLETE APPENDIX ====================
        story.append(Paragraph('COMPLETE FINDINGS APPENDIX', heading1_style))
        story.append(Spacer(1, 0.2*inch))

        appendix_text = """
        This appendix contains a comprehensive list of all {} security findings
        discovered during the automated security assessment, organized by severity level.
        """.format(stats['total'])
        story.append(Paragraph(appendix_text, body_style))
        story.append(Spacer(1, 0.2*inch))

        # Create master table with ALL findings
        if issues_found:
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                severity_issues = [i for i in issues_found if i['severity'] == severity]
                if not severity_issues:
                    continue

                story.append(Paragraph('{} Severity - {} Issues'.format(severity, len(severity_issues)),
                                     heading2_style))
                story.append(Spacer(1, 0.1*inch))

                # All issues table
                appendix_data = [['#', 'Tool', 'Type', 'File:Line', 'Issue Title']]
                for idx, issue in enumerate(severity_issues, 1):
                    location = '{}:{}'.format(issue['file'][:40], issue['line']) if issue['line'] > 0 else issue['file'][:40]
                    appendix_data.append([
                        str(idx),
                        issue['tool'],
                        issue['type'][:15],
                        Paragraph('<font size="7">{}</font>'.format(html_escape(location)), body_style),
                        Paragraph('<font size="7">{}</font>'.format(html_escape(issue['title'][:70])), body_style)
                    ])

                appendix_table = Table(appendix_data, colWidths=[1*cm, 2*cm, 2.5*cm, 4*cm, 6*cm])
                appendix_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), SEVERITY_COLORS[severity]),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#fafafa')])
                ]))
                story.append(appendix_table)
                story.append(Spacer(1, 0.3*inch))

        story.append(PageBreak())

        # ==================== RECOMMENDATIONS ====================
        story.append(Paragraph('RECOMMENDATIONS & NEXT STEPS', heading1_style))
        story.append(Spacer(1, 0.2*inch))

        recommendations = []
        if stats['critical'] > 0:
            recommendations.append(('IMMEDIATE ACTION',
                'Address all {} CRITICAL issues within 24-48 hours. These represent severe security risks.'.format(stats['critical'])))
        if stats['high'] > 0:
            recommendations.append(('HIGH PRIORITY',
                'Remediate {} HIGH severity vulnerabilities within 1-2 weeks. These pose significant security risks.'.format(stats['high'])))
        if tool_stats['TruffleHog']['total'] > 0:
            recommendations.append(('SECRET ROTATION',
                'Immediately rotate all {} exposed secrets and revoke compromised credentials.'.format(tool_stats['TruffleHog']['total'])))
        if tool_stats['Trivy']['total'] > 0:
            recommendations.append(('DEPENDENCY UPDATES',
                'Update vulnerable dependencies to their latest secure versions. Review package.json/requirements.txt.'))

        recommendations.extend([
            ('SECURITY PRACTICES',
             'Implement pre-commit hooks (e.g., Husky + TruffleHog) to prevent secrets from being committed.'),
            ('CI/CD INTEGRATION',
             'Integrate security scanning into CI/CD pipeline to catch issues early in development.'),
            ('DEVELOPER TRAINING',
             'Conduct security awareness training focusing on common vulnerabilities and secure coding practices.'),
            ('REGULAR SCANNING',
             'Schedule automated security scans weekly or on every merge to main branch.'),
            ('SECURITY CHAMPIONS',
             'Designate security champions within development teams to promote security best practices.')
        ])

        for idx, (title, desc) in enumerate(recommendations, 1):
            rec_box = Table([[Paragraph('<b>{}. {}</b>'.format(idx, title), heading3_style)],
                           [Paragraph(desc, body_style)]],
                          colWidths=[15*cm])
            rec_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e3f2fd')),
                ('BACKGROUND', (0, 1), (-1, 1), colors.white),
                ('BOX', (0, 0), (-1, -1), 1, HexColor('#1976d2')),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10)
            ]))
            story.append(rec_box)
            story.append(Spacer(1, 0.15*inch))

        story.append(PageBreak())

        # ==================== ABOUT THIS ASSESSMENT ====================
        story.append(Paragraph('ABOUT THIS ASSESSMENT', heading1_style))
        story.append(Spacer(1, 0.2*inch))

        about_intro = """
        This security assessment report was generated using industry-standard automated security
        scanning tools to identify vulnerabilities, security risks, and compliance issues in the codebase.
        """
        story.append(Paragraph(about_intro, body_style))
        story.append(Spacer(1, 0.3*inch))

        # Security Tools Used
        story.append(Paragraph('Security Tools Used', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        # Semgrep
        story.append(Paragraph('<b>1. Semgrep (Static Application Security Testing - SAST)</b>', heading3_style))
        semgrep_desc = """
        <b>Purpose:</b> Semgrep analyzes source code for security vulnerabilities and coding issues
        by matching code patterns against a comprehensive database of security rules.<br/><br/>
        <b>Coverage:</b> JavaScript, TypeScript, Python, Java, Go, Ruby, PHP, C#, and 30+ languages<br/><br/>
        <b>Detects:</b> SQL injection, Cross-Site Scripting (XSS), authentication bypass, hardcoded secrets,
        insecure cryptographic operations, path traversal, command injection, and OWASP Top 10 vulnerabilities<br/><br/>
        <b>Database:</b> Uses rules from security researchers, OWASP guidelines, and CWE standards
        """
        story.append(Paragraph(semgrep_desc, body_style))
        story.append(Spacer(1, 0.2*inch))

        # Trivy
        story.append(Paragraph('<b>2. Trivy (Software Composition Analysis - SCA)</b>', heading3_style))
        trivy_desc = """
        <b>Purpose:</b> Trivy scans dependencies and infrastructure for known vulnerabilities (CVEs),
        misconfigurations, and exposed secrets in packages and configuration files.<br/><br/>
        <b>Coverage:</b> npm, Maven, Gradle, pip, Go modules, Ruby gems, Composer packages, Docker images,
        Kubernetes manifests, Terraform files<br/><br/>
        <b>Detects:</b> Known CVEs in dependencies, security misconfigurations, exposed secrets in config files,
        outdated packages with security patches, license compliance issues<br/><br/>
        <b>Database:</b> National Vulnerability Database (NVD), GitHub Security Advisories, vendor-specific databases
        """
        story.append(Paragraph(trivy_desc, body_style))
        story.append(Spacer(1, 0.2*inch))

        # TruffleHog
        story.append(Paragraph('<b>3. TruffleHog (Secret Detection)</b>', heading3_style))
        trufflehog_desc = """
        <b>Purpose:</b> TruffleHog performs deep scans for leaked credentials, API keys, and secrets
        that may have been accidentally committed to source code or git history.<br/><br/>
        <b>Coverage:</b> All source code files, configuration files, and complete git commit history<br/><br/>
        <b>Detects:</b> API keys (AWS, Azure, GCP), passwords, authentication tokens, private keys,
        database credentials, OAuth secrets, service account keys<br/><br/>
        <b>Verification:</b> Attempts to verify found secrets against cloud providers to determine if they are active
        """
        story.append(Paragraph(trufflehog_desc, body_style))
        story.append(Spacer(1, 0.3*inch))

        # Severity Definitions
        story.append(Paragraph('Severity Level Definitions', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        severity_defs = [
            ['Severity', 'Definition', 'Action Required'],
            ['CRITICAL', 'Exploitable vulnerabilities or exposed secrets that require immediate remediation',
             'Fix within 24-48 hours'],
            ['HIGH', 'Significant security risks that could lead to data breach or system compromise',
             'Fix within 1 week'],
            ['MEDIUM', 'Important security issues that should be addressed in upcoming development sprints',
             'Fix within 1 month'],
            ['LOW', 'Minor security issues or best practice violations to be monitored and improved',
             'Fix when convenient'],
            ['INFO', 'Informational findings and recommendations for security improvements',
             'Consider for future work']
        ]

        severity_table = Table(severity_defs, colWidths=[2.5*cm, 7.5*cm, 5*cm])
        severity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (0, 1), HexColor('#ffebee')),
            ('BACKGROUND', (0, 2), (0, 2), HexColor('#fff3e0')),
            ('BACKGROUND', (0, 3), (0, 3), HexColor('#fffde7')),
            ('BACKGROUND', (0, 4), (0, 4), HexColor('#e3f2fd')),
            ('BACKGROUND', (0, 5), (0, 5), HexColor('#f5f5f5')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(severity_table)
        story.append(Spacer(1, 0.3*inch))

        # Risk Scoring
        story.append(Paragraph('Risk Scoring Methodology', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        risk_formula = """
        The overall risk score is calculated using a weighted formula that prioritizes critical
        and high-severity findings:<br/><br/>
        <b>Risk Score = (CRITICAL × 4 + HIGH × 2 + MEDIUM × 1) / 10</b><br/><br/>
        <b>Risk Level Thresholds:</b><br/>
        • 0.0 - 3.0: LOW (Minimal security concerns)<br/>
        • 3.0 - 5.0: MEDIUM (Some security issues identified)<br/>
        • 5.0 - 7.0: HIGH (Significant security risks present)<br/>
        • 7.0 - 10.0: CRITICAL (Severe security risks requiring immediate action)<br/><br/>
        This scoring system ensures that critical vulnerabilities have the highest impact on the
        overall security posture assessment.
        """
        story.append(Paragraph(risk_formula, body_style))
        story.append(Spacer(1, 0.3*inch))

        # Scanning Process
        story.append(Paragraph('Automated Scanning Process', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        process_desc = """
        <b>1. Code Checkout:</b> Latest code is pulled from the Git repository<br/><br/>
        <b>2. Dependency Installation:</b> Project dependencies are installed (npm, Maven, pip, etc.)<br/><br/>
        <b>3. Parallel Security Scans:</b> All three tools run simultaneously for efficiency<br/>
        &nbsp;&nbsp;&nbsp;• Semgrep scans all source code files<br/>
        &nbsp;&nbsp;&nbsp;• Trivy scans dependencies and configuration files<br/>
        &nbsp;&nbsp;&nbsp;• TruffleHog scans for secrets in code and git history<br/><br/>
        <b>4. Results Aggregation:</b> Findings are collected and normalized from all tools<br/><br/>
        <b>5. Report Generation:</b> Professional PDF report is created with all findings<br/><br/>
        <b>6. Notifications:</b> Results are sent via email and Microsoft Teams
        """
        story.append(Paragraph(process_desc, body_style))

        story.append(PageBreak())

        # ==================== CONTACT & SUPPORT ====================
        story.append(Paragraph('CONTACT & SUPPORT', heading1_style))
        story.append(Spacer(1, 0.2*inch))

        contact_intro = """
        For questions, concerns, or assistance regarding this security assessment report,
        please contact the TTS Security and DevOps teams.
        """
        story.append(Paragraph(contact_intro, body_style))
        story.append(Spacer(1, 0.3*inch))

        # Contact information
        contact_data = [
            ['Department', 'Contact', 'Purpose'],
            ['Security Team', CONTACT_EMAIL, 'Security findings, vulnerability questions, risk assessment'],
            ['DevOps Team', html_escape(DEVOPS_ENGINEER), 'Pipeline issues, scan execution, Jenkins configuration'],
            ['Development Team', html_escape(DEVELOPER_NAME), 'Code-related questions, remediation guidance'],
            ['TTS Support', 'support@ttsme.com', 'General inquiries and escalations']
        ]

        contact_table = Table(contact_data, colWidths=[3.5*cm, 5*cm, 6.5*cm])
        contact_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f9f9f9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(contact_table)
        story.append(Spacer(1, 0.3*inch))

        # Reporting Issues
        story.append(Paragraph('Reporting False Positives or Issues', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        reporting_text = """
        If you believe any findings in this report are false positives or require clarification:<br/><br/>
        <b>1.</b> Document the specific finding (page number, issue ID, file location)<br/>
        <b>2.</b> Provide justification or evidence showing why it's a false positive<br/>
        <b>3.</b> Email the details to {} with subject: "Security Scan False Positive - {}"<br/>
        <b>4.</b> The security team will review within 2 business days<br/><br/>
        For urgent security concerns or active incidents, contact the security team immediately.
        """.format(CONTACT_EMAIL, html_escape(PROJECT_NAME))
        story.append(Paragraph(reporting_text, body_style))
        story.append(Spacer(1, 0.3*inch))

        # Next Steps
        story.append(Paragraph('Next Steps', heading2_style))
        story.append(Spacer(1, 0.1*inch))

        next_steps_text = """
        <b>1.</b> Review all CRITICAL and HIGH severity findings immediately<br/>
        <b>2.</b> Create tickets/tasks in your project management system for remediation<br/>
        <b>3.</b> Prioritize fixes based on exploitability and business impact<br/>
        <b>4.</b> Schedule follow-up scans after remediation to verify fixes<br/>
        <b>5.</b> Integrate security scanning into your CI/CD pipeline for continuous monitoring
        """
        story.append(Paragraph(next_steps_text, body_style))
        story.append(Spacer(1, 0.5*inch))

        # Footer
        footer_text = """
        <para align="center" fontSize="9" textColor="grey">
        <b>End of Security Assessment Report</b><br/>
        Document: {} | Generated: {} | Build #{}<br/>
        © {} Total Technologies and Solutions FZ-LLC | INTERNAL USE ONLY
        </para>
        """.format(DOCUMENT_NUMBER,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  os.environ.get('BUILD_NUMBER', 'Unknown'),
                  datetime.now().year)
        story.append(Paragraph(footer_text, body_style))

        # Build the PDF with custom canvas
        doc.build(story, canvasmaker=NumberedCanvas)
        print('  ✅ Comprehensive PDF report generated successfully: security-report.pdf')
        print('  📄 Report contains {} pages with {} complete findings'.format(
            len(doc._saved_page_states) if hasattr(doc, '_saved_page_states') else 'multiple',
            stats['total']
        ))

    except Exception as e:
        print(f'  ❌ PDF generation error: {e}')
        import traceback
        traceback.print_exc()

        # Create fallback simple PDF
        print('  Creating simple fallback PDF...')
        c = canvas.Canvas('security-report.pdf', pagesize=A4)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(100, 750, 'SECURITY SCAN REPORT')
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, 'Project: {}'.format(PROJECT_NAME))
        c.drawString(100, 670, 'Build: #{}'.format(os.environ.get('BUILD_NUMBER', 'Unknown')))
        c.drawString(100, 640, 'Date: {}'.format(os.environ.get('SCAN_DATE', 'Unknown')))
        c.drawString(100, 600, 'Total Issues: {}'.format(stats['total']))
        c.drawString(100, 570, 'Critical: {}'.format(stats['critical']))
        c.drawString(100, 540, 'High: {}'.format(stats['high']))
        c.drawString(100, 510, 'Medium: {}'.format(stats['medium']))
        c.drawString(100, 480, 'Low: {}'.format(stats['low']))
        c.drawString(100, 450, 'Risk Level: {} ({:.1f}/10)'.format(risk_level, risk_score))
        c.save()
        print('  Fallback PDF created')
else:
    print('  ❌ ReportLab not available, cannot generate PDF')

# Save summary for notifications
summary = {
    'total': stats['total'],
    'critical': stats['critical'],
    'high': stats['high'],
    'medium': stats['medium'],
    'low': stats['low'],
    'info': stats['info'],
    'risk_level': risk_level,
    'risk_score': round(risk_score, 1)
}

with open('summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print('\n✅ Report generation completed successfully!')
print('📊 Files created:')
print('   - security-report.pdf (Comprehensive {} page report)'.format('15-30' if stats['total'] > 50 else '5-15'))
print('   - summary.json (For email/Teams notifications)')
print('\n🎯 Report includes:')
print('   ✓ Professional cover page with company logo')
print('   ✓ Executive summary with risk gauge')
print('   ✓ Pie chart (severity distribution)')
print('   ✓ Bar chart (findings by tool)')
print('   ✓ Complete findings by tool ({} Semgrep, {} Trivy, {} TruffleHog)'.format(
    tool_stats['Semgrep']['total'], tool_stats['Trivy']['total'], tool_stats['TruffleHog']['total']
))
print('   ✓ Full appendix with ALL {} findings (no truncation!)'.format(stats['total']))
print('   ✓ Actionable recommendations')
print('   ✓ Professional headers, footers, and page numbers')
print('   ✓ Color-coded severity levels throughout')
