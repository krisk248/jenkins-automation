#!/usr/bin/env python3
"""
TTS Security Scanner
Comprehensive security scanning for multiple application types
Saves all outputs to dedicated security report directory (NOT code folder)
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

class SecurityScanner:
    def __init__(self, args):
        self.project_name = args.project_name
        self.component_name = args.component_name
        self.app_type = args.app_type
        self.code_path = Path(args.code_path)
        self.output_dir = Path(args.output_dir)
        self.scan_path = args.scan_path

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Results storage
        self.results = {
            "project": self.project_name,
            "component": self.component_name,
            "app_type": self.app_type,
            "scan_date": datetime.now().isoformat(),
            "scans": {}
        }

        # Define exclude patterns based on app type
        self.exclude_patterns = self._get_exclude_patterns()

    def _get_exclude_patterns(self):
        """Get exclude patterns based on app type"""
        common_excludes = [
            "**/.git/**",
            "**/node_modules/**",
            "**/target/**",
            "**/build/**",
            "**/dist/**",
            "**/.idea/**",
            "**/.vscode/**",
            "**/security-reports/**",
            "**/security-report.pdf",
            "**/summary.json",
            "**/C:/**",
            "**/otherFiles/**",
            "**/*.class",
            "**/*.war",
            "**/*.jar",
            "**/*.log",
            "**/.angular/**",
            "**/.m2/**",
            "**/bin/**",
            "**/obj/**"
        ]

        app_specific = {
            "java8": ["**/target/**", "**/.m2/**"],
            "java17": ["**/target/**", "**/.m2/**"],
            "angular": ["**/node_modules/**", "**/dist/**", "**/.angular/**"],
            "gulp": ["**/node_modules/**", "**/dist/**", "**/build/**"]
        }

        return common_excludes + app_specific.get(self.app_type, [])

    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_command(self, cmd, description):
        """Run shell command and return output"""
        self.log(f"Running: {description}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.code_path
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            self.log(f"Error running {description}: {e}", "ERROR")
            return 1, "", str(e)

    def create_exclude_file(self):
        """Create temporary exclude patterns file for TruffleHog"""
        exclude_file = self.output_dir / "trufflehog-exclude.txt"
        with open(exclude_file, 'w') as f:
            for pattern in self.exclude_patterns:
                # Convert glob patterns to regex for TruffleHog
                pattern = pattern.replace("**/", "").replace("/**", "")
                f.write(f"{pattern}\n")
        return str(exclude_file)

    def run_semgrep(self):
        """Run Semgrep security scan"""
        self.log("=== Running Semgrep ===")
        output_file = self.output_dir / "semgrep.json"

        # Determine Semgrep config based on app type
        configs = {
            "java8": "p/java",
            "java17": "p/java",
            "angular": "p/typescript p/javascript",
            "gulp": "p/javascript p/html"
        }
        config = configs.get(self.app_type, "p/security-audit")

        # Build scan target (only scan specified path)
        scan_target = self.code_path / self.scan_path

        cmd = f"""
        semgrep --config {config} \
                --json \
                --output {output_file} \
                {scan_target}
        """

        code, stdout, stderr = self.run_command(cmd, "Semgrep scan")

        if code == 0 or os.path.exists(output_file):
            self.log(f"Semgrep completed: {output_file}", "SUCCESS")
            self.results["scans"]["semgrep"] = str(output_file)
            return True
        else:
            self.log(f"Semgrep failed: {stderr}", "ERROR")
            return False

    def run_trivy_fs(self):
        """Run Trivy filesystem scan"""
        self.log("=== Running Trivy Filesystem Scan ===")
        output_file = self.output_dir / "trivy-fs.json"

        scan_target = self.code_path / self.scan_path

        cmd = f"""
        trivy fs \
              --format json \
              --output {output_file} \
              --scanners vuln,secret,misconfig \
              {scan_target}
        """

        code, stdout, stderr = self.run_command(cmd, "Trivy filesystem scan")

        if code == 0 or os.path.exists(output_file):
            self.log(f"Trivy FS completed: {output_file}", "SUCCESS")
            self.results["scans"]["trivy_fs"] = str(output_file)
            return True
        else:
            self.log(f"Trivy FS failed: {stderr}", "ERROR")
            return False

    def run_trivy_pkg(self):
        """Run Trivy package scan (for dependencies)"""
        self.log("=== Running Trivy Package Scan ===")
        output_file = self.output_dir / "trivy-pkg.json"

        # Scan different package files based on app type
        scan_targets = {
            "java8": "pom.xml",
            "java17": "pom.xml",
            "angular": "package.json",
            "gulp": "package.json"
        }

        target_file = self.code_path / scan_targets.get(self.app_type, "pom.xml")

        if not target_file.exists():
            self.log(f"Package file not found: {target_file}", "WARNING")
            return False

        cmd = f"""
        trivy fs \
              --format json \
              --output {output_file} \
              --scanners vuln \
              {target_file}
        """

        code, stdout, stderr = self.run_command(cmd, "Trivy package scan")

        if code == 0 or os.path.exists(output_file):
            self.log(f"Trivy package scan completed: {output_file}", "SUCCESS")
            self.results["scans"]["trivy_pkg"] = str(output_file)
            return True
        else:
            self.log(f"Trivy package scan failed: {stderr}", "ERROR")
            return False

    def run_trufflehog(self):
        """Run TruffleHog secret scan"""
        self.log("=== Running TruffleHog ===")
        output_file = self.output_dir / "trufflehog.json"
        output_raw = self.output_dir / "trufflehog-raw.json"

        # Create exclude file
        exclude_file = self.create_exclude_file()

        # Scan only specified path
        scan_target = self.code_path / self.scan_path

        cmd = f"""
        trufflehog filesystem {scan_target} \
                   --json \
                   --exclude-paths={exclude_file} \
                   > {output_raw} 2>&1
        """

        code, stdout, stderr = self.run_command(cmd, "TruffleHog secret scan")

        # TruffleHog may return non-zero even on success
        if os.path.exists(output_raw):
            # Process and clean up TruffleHog output
            try:
                with open(output_raw, 'r') as f:
                    lines = f.readlines()

                findings = []
                for line in lines:
                    try:
                        finding = json.loads(line)
                        findings.append(finding)
                    except:
                        continue

                with open(output_file, 'w') as f:
                    json.dump(findings, f, indent=2)

                self.log(f"TruffleHog completed: {output_file} ({len(findings)} findings)", "SUCCESS")
                self.results["scans"]["trufflehog"] = str(output_file)
                return True
            except Exception as e:
                self.log(f"Error processing TruffleHog output: {e}", "ERROR")
                return False
        else:
            self.log("TruffleHog failed: No output generated", "ERROR")
            return False

    def run_npm_audit(self):
        """Run npm audit (for Node.js projects)"""
        if self.app_type not in ["angular", "gulp"]:
            self.log("Skipping npm audit (not a Node.js project)")
            return True

        self.log("=== Running npm audit ===")
        output_file = self.output_dir / "npm-audit.json"

        package_json = self.code_path / "package.json"
        if not package_json.exists():
            self.log("No package.json found, skipping npm audit", "WARNING")
            return True

        cmd = f"npm audit --json > {output_file} 2>&1 || true"

        code, stdout, stderr = self.run_command(cmd, "npm audit")

        if os.path.exists(output_file):
            self.log(f"npm audit completed: {output_file}", "SUCCESS")
            self.results["scans"]["npm_audit"] = str(output_file)
            return True
        else:
            self.log("npm audit failed", "ERROR")
            return False

    def calculate_summary(self):
        """Calculate summary statistics from scan results"""
        self.log("=== Calculating Summary ===")

        summary = {
            "total_findings": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
            "by_tool": {}
        }

        # Parse Semgrep results
        semgrep_file = self.output_dir / "semgrep.json"
        if semgrep_file.exists():
            try:
                with open(semgrep_file) as f:
                    data = json.load(f)
                    findings = data.get("results", [])
                    summary["by_tool"]["semgrep"] = len(findings)

                    for finding in findings:
                        severity = finding.get("extra", {}).get("severity", "INFO").upper()
                        if severity == "ERROR":
                            summary["critical"] += 1
                        elif severity == "WARNING":
                            summary["high"] += 1
                        else:
                            summary["medium"] += 1
                        summary["total_findings"] += 1
            except Exception as e:
                self.log(f"Error parsing Semgrep results: {e}", "WARNING")

        # Parse Trivy results
        trivy_files = ["trivy-fs.json", "trivy-pkg.json"]
        for trivy_file in trivy_files:
            file_path = self.output_dir / trivy_file
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        data = json.load(f)
                        results = data.get("Results", [])

                        trivy_count = 0
                        for result in results:
                            vulns = result.get("Vulnerabilities", []) or []
                            trivy_count += len(vulns)

                            for vuln in vulns:
                                severity = vuln.get("Severity", "UNKNOWN").upper()
                                if severity == "CRITICAL":
                                    summary["critical"] += 1
                                elif severity == "HIGH":
                                    summary["high"] += 1
                                elif severity == "MEDIUM":
                                    summary["medium"] += 1
                                elif severity == "LOW":
                                    summary["low"] += 1
                                else:
                                    summary["info"] += 1
                                summary["total_findings"] += 1

                        summary["by_tool"][trivy_file.replace(".json", "")] = trivy_count
                except Exception as e:
                    self.log(f"Error parsing {trivy_file}: {e}", "WARNING")

        # Parse TruffleHog results
        trufflehog_file = self.output_dir / "trufflehog.json"
        if trufflehog_file.exists():
            try:
                with open(trufflehog_file) as f:
                    findings = json.load(f)
                    summary["by_tool"]["trufflehog"] = len(findings)
                    # All TruffleHog findings are critical (exposed secrets)
                    summary["critical"] += len(findings)
                    summary["total_findings"] += len(findings)
            except Exception as e:
                self.log(f"Error parsing TruffleHog results: {e}", "WARNING")

        # Save summary
        summary_file = self.output_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        self.log(f"Summary: {summary['total_findings']} total findings", "SUCCESS")
        self.log(f"  Critical: {summary['critical']}", "INFO")
        self.log(f"  High: {summary['high']}", "INFO")
        self.log(f"  Medium: {summary['medium']}", "INFO")
        self.log(f"  Low: {summary['low']}", "INFO")

        return summary

    def run_all_scans(self):
        """Run all security scans"""
        self.log(f"Starting security scans for {self.project_name} - {self.component_name}")
        self.log(f"App Type: {self.app_type}")
        self.log(f"Code Path: {self.code_path}")
        self.log(f"Output Dir: {self.output_dir}")
        self.log(f"Scan Path: {self.scan_path}")

        # Run scans
        scans = [
            self.run_semgrep,
            self.run_trivy_fs,
            self.run_trivy_pkg,
            self.run_trufflehog,
        ]

        # Add npm audit for Node.js projects
        if self.app_type in ["angular", "gulp"]:
            scans.append(self.run_npm_audit)

        success_count = 0
        for scan in scans:
            if scan():
                success_count += 1

        # Calculate summary
        summary = self.calculate_summary()

        self.log(f"Security scans completed: {success_count}/{len(scans)} successful")
        self.log(f"All reports saved to: {self.output_dir}")

        return success_count == len(scans)


def main():
    parser = argparse.ArgumentParser(
        description="TTS Security Scanner - Comprehensive security scanning"
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
        "--app-type",
        required=True,
        choices=["java8", "java17", "angular", "gulp"],
        help="Application type (determines which scans to run)"
    )

    parser.add_argument(
        "--code-path",
        required=True,
        help="Path to source code directory"
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for security reports (NOT in code folder)"
    )

    parser.add_argument(
        "--scan-path",
        default="src/",
        help="Relative path within code to scan (default: src/)"
    )

    args = parser.parse_args()

    # Validate paths
    if not os.path.exists(args.code_path):
        print(f"ERROR: Code path does not exist: {args.code_path}")
        sys.exit(1)

    # Run scanner
    scanner = SecurityScanner(args)
    success = scanner.run_all_scans()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
