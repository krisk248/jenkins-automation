#!/usr/bin/env python3
"""
TTS Security Report Generator with Command-Line Interface
Generates comprehensive PDF security assessment reports with detailed findings

This version wraps the full report generator with command-line argument parsing
while maintaining ALL detailed findings sections from Semgrep, Trivy, and TruffleHog.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="TTS Security Report Generator - Generate comprehensive PDF security reports with detailed findings"
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

    # Set environment variables for the full report generator
    os.environ['PROJECT_NAME'] = args.project_name
    os.environ['GIT_URL'] = args.git_repo
    os.environ['GIT_BRANCH'] = args.git_branch
    os.environ['CONTACT_EMAIL'] = args.contact_email
    os.environ['DEVELOPER_NAME'] = args.developer
    os.environ['DEVOPS_ENGINEER'] = args.devops_engineer

    if not os.getenv('BUILD_NUMBER'):
        os.environ['BUILD_NUMBER'] = 'Unknown'

    if not os.getenv('SCAN_DATE'):
        from datetime import datetime
        os.environ['SCAN_DATE'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Change to input directory so the full generator can find security-reports/
    original_dir = os.getcwd()
    input_path = Path(args.input_dir).absolute()

    # The full generator expects files in "security-reports/" subdirectory
    # Our scans output directly to input_dir, so we need to create the structure
    security_reports_subdir = input_path / 'security-reports'
    security_reports_subdir.mkdir(exist_ok=True)

    # Copy or symlink JSON files to security-reports/ subdirectory
    import shutil
    for json_file in ['semgrep.json', 'trivy.json', 'trufflehog.json', 'trufflehog-raw.json', 'summary.json']:
        src = input_path / json_file
        dst = security_reports_subdir / json_file

        if src.exists():
            if dst.exists():
                dst.unlink()  # Remove old symlink/file

            try:
                # Try symlink first (faster)
                dst.symlink_to(src)
            except (OSError, NotImplementedError):
                # Fall back to copy if symlinks not supported
                shutil.copy(str(src), str(dst))

    os.chdir(input_path)

    # Call the full report generator script
    script_dir = Path(__file__).parent
    full_generator = script_dir / 'generate_report_FULL.py'

    if not full_generator.exists():
        print(f"ERROR: Full report generator not found: {full_generator}")
        print("Please ensure generate_report_FULL.py is in the same directory")
        sys.exit(1)

    print(f"Generating comprehensive security report with detailed findings...")
    print(f"Project: {args.project_name}")
    print(f"Component: {args.component_name}")
    print(f"")

    try:
        # Run the full generator
        result = subprocess.run(
            [sys.executable, str(full_generator)],
            check=True,
            capture_output=False
        )

        # Find generated PDF
        pdf_files = list(Path('.').glob('security-reports/security-report*.pdf'))
        if not pdf_files:
            pdf_files = list(Path('.').glob('security-report*.pdf'))

        if pdf_files:
            generated_pdf = pdf_files[0]
            print(f"\n✅ Report generated successfully: {generated_pdf}")

            # If output file specified, copy to that location
            if args.output_file:
                import shutil
                shutil.copy(str(generated_pdf), args.output_file)
                print(f"   Copied to: {args.output_file}")

                # Also handle SonarQube section if URL provided
                if args.sonarqube_url:
                    print(f"   SonarQube Dashboard: {args.sonarqube_url}")
        else:
            print("\n⚠️ PDF file not found, but generation may have completed")
            print(f"   Check directory: {Path('.').absolute()}")

    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Report generation failed with exit code {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        os.chdir(original_dir)

    sys.exit(0)


if __name__ == "__main__":
    main()
