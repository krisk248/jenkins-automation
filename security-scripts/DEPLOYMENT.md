# Security Scripts Deployment Guide

## 📋 Overview

This guide explains how to deploy the new Python-based security scanning scripts to your Jenkins Docker container.

---

## 🎯 What Changed

### ✅ New Files Created:
1. **security_scan.py** - Smart security scanner with app type presets
2. **generate_report.py** - Enhanced PDF report generator with command-line arguments

### ✅ Benefits:
- ✅ **Code folder stays clean** - No security files pollute your Git code
- ✅ **Flexible scanning** - Supports Java 8/17, Angular, Gulp projects
- ✅ **Better PDF reports** - Filled fields, proper formatting, SonarQube integration
- ✅ **Command-line control** - Easy to customize per project

---

## 📦 Files to Deploy

```
jenkins-automation/security-scripts/
├── security_scan.py          ← NEW (replaces security_scan.sh)
├── generate_report.py         ← UPDATED
└── DEPLOYMENT.md              ← This file
```

---

## 🚀 Deployment Steps

### Step 1: Pull Latest Code from GitHub

On your server:
```bash
cd /home/kannan/Projects/Office/builddev/jenkins-automation
git pull origin main
```

### Step 2: Copy Files to Jenkins Docker Container

```bash
# Copy security_scan.py
docker cp security-scripts/security_scan.py jenkins:/usr/local/bin/security-scripts/

# Copy generate_report.py
docker cp security-scripts/generate_report.py jenkins:/usr/local/bin/security-scripts/
```

### Step 3: Make Scripts Executable

```bash
docker exec jenkins chmod +x /usr/local/bin/security-scripts/security_scan.py
docker exec jenkins chmod +x /usr/local/bin/security-scripts/generate_report.py
```

### Step 4: Verify Deployment

```bash
# Check files exist
docker exec jenkins ls -la /usr/local/bin/security-scripts/

# Expected output:
# security_scan.py
# generate_report.py
```

### Step 5: Test Scripts

```bash
# Test security_scan.py help
docker exec jenkins python3 /usr/local/bin/security-scripts/security_scan.py --help

# Test generate_report.py help
docker exec jenkins python3 /usr/local/bin/security-scripts/generate_report.py --help
```

---

## 📝 Update Your Jenkinsfile

The `Jenkinsfile-ADXSIP` has already been updated in `/home/kannan/Projects/Office/builddev/adxsip/adxsipjenkins/`

### Changes Made:

**Stage 2: Security Scan** (UPDATED)
```groovy
stage('Security Scan') {
    steps {
        sh """
            python3 /usr/local/bin/security-scripts/security_scan.py \
                --project-name "ADXSIP" \
                --component-name "ADXSIP Backend" \
                --app-type java17 \
                --code-path ${CODE_PATH} \
                --output-dir ${SECURITY_REPORT_DIR} \
                --scan-path src/
        """
    }
}
```

**Stage 3: Generate Report** (UPDATED)
```groovy
stage('Generate Security Report') {
    steps {
        sh """
            python3 /usr/local/bin/security-scripts/generate_report.py \
                --input-dir ${SECURITY_REPORT_DIR} \
                --project-name "ADXSIP" \
                --component-name "ADXSIP Backend" \
                --git-repo "${GIT_URL}" \
                --git-branch "${GIT_BRANCH}" \
                --contact-email "security@ttsme.com" \
                --developer "Development Team" \
                --devops-engineer "Kannan Giridharan" \
                --sonarqube-url "http://192.168.1.136:9000/dashboard?id=ADXSIP-Backend"
        """
    }
}
```

---

## 🧪 Testing

### Test 1: Manual Security Scan

```bash
docker exec -it jenkins bash

python3 /usr/local/bin/security-scripts/security_scan.py \
    --project-name "ADXSIP" \
    --component-name "ADXSIP Backend" \
    --app-type java17 \
    --code-path /tts/ttsbuild/ADXSIP/tts-uae-adx-sip-serverside \
    --output-dir /tmp/test-security-report \
    --scan-path src/

ls -la /tmp/test-security-report/
```

**Expected output:**
```
/tmp/test-security-report/
├── semgrep.json
├── trivy-fs.json
├── trivy-pkg.json
├── trufflehog.json
├── trufflehog-raw.json
└── summary.json
```

### Test 2: Manual Report Generation

```bash
python3 /usr/local/bin/security-scripts/generate_report.py \
    --input-dir /tmp/test-security-report \
    --project-name "ADXSIP" \
    --component-name "ADXSIP Backend" \
    --git-repo "https://github.com/your-org/adxsip-backend" \
    --git-branch "main" \
    --contact-email "security@ttsme.com" \
    --developer "Development Team" \
    --devops-engineer "Kannan Giridharan" \
    --sonarqube-url "http://192.168.1.136:9000/dashboard?id=ADXSIP-Backend"

ls -la /tmp/test-security-report/security-report-*.pdf
```

**Expected output:**
```
security-report-ADXSIP-Backend_20250118_123045.pdf
```

### Test 3: Full Jenkins Pipeline

1. Go to Jenkins UI
2. Navigate to ADXSIP job
3. Click "Build Now"
4. Monitor console output
5. Check artifacts for `security-report.pdf`
6. Verify reports in `/tts/ttsbuild/securityreport/ADXSIP/ADXSIP_*/`

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Scripts copied to `/usr/local/bin/security-scripts/`
- [ ] Scripts are executable (`chmod +x`)
- [ ] `security_scan.py --help` works
- [ ] `generate_report.py --help` works
- [ ] Code folder remains clean (no `security-report.pdf` in code directory)
- [ ] Security reports saved to `/tts/ttsbuild/securityreport/ADXSIP/`
- [ ] PDF filename includes component name and timestamp
- [ ] Jenkins pipeline runs successfully
- [ ] PDF report has all fields filled (Git repo, branch, developer, etc.)
- [ ] PDF report has SonarQube section

---

## 🔧 App Type Configuration

For other projects, change the `--app-type` parameter:

| Project Type | --app-type | Scans Run |
|-------------|-----------|----------|
| Java 8 Maven | `java8` | Semgrep (Java), Trivy, TruffleHog |
| Java 17 Maven | `java17` | Semgrep (Java), Trivy, TruffleHog |
| Angular | `angular` | Semgrep (TS/JS), Trivy, npm audit |
| Gulp HTML/JS | `gulp` | Semgrep (JS/HTML), Trivy |

### Example for Angular Project:

```groovy
sh """
    python3 /usr/local/bin/security-scripts/security_scan.py \
        --project-name "ADXSIP" \
        --component-name "ADX-SIP Frontend" \
        --app-type angular \
        --code-path ${CODE_PATH} \
        --output-dir ${SECURITY_REPORT_DIR} \
        --scan-path src/
"""
```

---

## 📊 What Gets Excluded from Scans

The scanner automatically excludes:

### Common Exclusions:
- `.git/`, `.idea/`, `.vscode/`
- `target/`, `build/`, `dist/`, `bin/`, `obj/`
- `node_modules/`, `.angular/`, `.m2/`
- `security-reports/`, `security-report.pdf`
- `C:/`, `otherFiles/` (junk folders)
- `*.class`, `*.jar`, `*.war`, `*.log`

### Result:
✅ Only `src/` and relevant files are scanned
✅ No scanning of build outputs, dependencies, or junk folders
✅ Faster scans, fewer false positives

---

## 🐛 Troubleshooting

### Issue 1: "Command not found: python3"
**Solution:**
```bash
docker exec jenkins which python3
# Should output: /usr/bin/python3 or similar
```

### Issue 2: "ModuleNotFoundError: No module named 'reportlab'"
**Solution:**
```bash
docker exec jenkins pip3 install reportlab
```

### Issue 3: "Permission denied" when running scripts
**Solution:**
```bash
docker exec jenkins chmod +x /usr/local/bin/security-scripts/*.py
```

### Issue 4: PDF generation fails
**Check:**
```bash
# Verify summary.json exists
docker exec jenkins ls -la ${SECURITY_REPORT_DIR}/summary.json

# Check Python can import reportlab
docker exec jenkins python3 -c "import reportlab; print(reportlab.Version)"
```

### Issue 5: Code folder still has security files
**Reason:** Old shell script might still be running

**Solution:**
```bash
# Remove old shell script
docker exec jenkins rm -f /usr/local/bin/security-scripts/security_scan.sh

# Verify only Python files exist
docker exec jenkins ls -la /usr/local/bin/security-scripts/
```

---

## 📞 Support

For issues:
1. Check Jenkins console output
2. Check security report directory: `/tts/ttsbuild/securityreport/ADXSIP/`
3. Check Docker container logs: `docker logs jenkins`
4. Contact: Kannan Giridharan

---

## ✨ Summary

**Before:**
```
/tts/ttsbuild/ADXSIP/tts-uae-adx-sip-serverside/
├── security-report.pdf         ❌ Pollutes code
├── summary.json                ❌ Pollutes code
├── security-reports/           ❌ Pollutes code
```

**After:**
```
/tts/ttsbuild/ADXSIP/tts-uae-adx-sip-serverside/
├── src/                        ✅ CLEAN!
└── pom.xml                     ✅ CLEAN!

/tts/ttsbuild/securityreport/ADXSIP/ADXSIP_20250118_123045/
├── semgrep.json
├── trivy-fs.json
├── trivy-pkg.json
├── trufflehog.json
└── security-report-ADXSIP-Backend_20250118_123045.pdf  ✅ All here!
```

---

**Deployment Date:** 2025-01-18
**Author:** Kannan Giridharan
**Version:** 2.0
