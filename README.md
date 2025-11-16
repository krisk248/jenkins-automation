# Jenkins Build Server Automation

Complete Jenkins setup with SonarQube and security scanning tools for ADXSIP project.

## Components

- **Jenkins Master** - CI/CD orchestration
- **SonarQube** - Code quality and security analysis
- **PostgreSQL** - SonarQube database
- **Security Tools** - Semgrep, Trivy, TruffleHog

---

## Quick Start

### 1. Clone Repository on Build Server

```bash
cd ~
git clone YOUR_GITHUB_REPO_URL jenkins-automation
cd jenkins-automation
```

### 2. Stop Existing Jenkins (if running)

```bash
docker stop jenkins-master
docker rm jenkins-master
```

### 3. Build and Start Services

```bash
# Build custom Jenkins image with security tools
docker-compose down
docker-compose up -d --build
```

This will take 5-10 minutes to:
- Build custom Jenkins image with all tools
- Start Jenkins, SonarQube, and PostgreSQL
- Download and install all security scanners

### 4. Wait for Services to Start

```bash
# Watch Jenkins logs
docker-compose logs -f jenkins

# Wait for: "Jenkins is fully up and running"
# Press Ctrl+C when ready
```

### 5. Access Services

- **Jenkins**: http://192.168.1.136:7080
- **SonarQube**: http://192.168.1.136:9000

---

## Initial Setup

### Jenkins Configuration

1. **Get initial admin password:**
   ```bash
   docker exec jenkins-master cat /var/jenkins_home/secrets/initialAdminPassword
   ```

2. **Install suggested plugins**

3. **Install additional plugins:**
   - Email Extension Plugin
   - HTTP Request Plugin
   - SonarQube Scanner Plugin

4. **Configure GitHub credentials:**
   - Go to: Manage Jenkins → Credentials
   - Add: Username with password
   - ID: `github-pat`
   - Username: (any)
   - Password: Your GitHub Personal Access Token

5. **Configure SonarQube:**
   - Go to: Manage Jenkins → Configure System
   - Add SonarQube server:
     - Name: `SonarQube`
     - Server URL: `http://sonarqube:9000`
     - Token: (generate from SonarQube UI)

### SonarQube Configuration

1. **Access SonarQube:** http://192.168.1.136:9000

2. **Default credentials:**
   - Username: `admin`
   - Password: `admin`
   - (Change password on first login)

3. **Generate token for Jenkins:**
   - My Account → Security → Generate Token
   - Name: `Jenkins`
   - Copy token and add to Jenkins SonarQube configuration

4. **Create quality gate:**
   - Quality Gates → Create
   - Name: `TTS Quality Gate`
   - Conditions:
     - Code Coverage < 70% → FAILED
     - Bugs > 20 → FAILED
     - Vulnerabilities > 10 → FAILED
   - Set as default

---

## Creating Jenkins Pipelines

### Backend Pipeline (ADXSIP)

1. **Create new pipeline job:**
   - New Item → Pipeline
   - Name: `ADXSIP-Backend`

2. **Configure:**
   - Pipeline definition: Pipeline script from SCM
   - SCM: Git
   - Repository URL: `https://github.com/TTS-FZLLC/adxsip-backend`
   - Credentials: `github-pat`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`

3. **Copy Jenkinsfile to your backend repo:**
   ```bash
   cp jenkins/Jenkinsfile.backend YOUR_BACKEND_REPO/Jenkinsfile
   ```

4. **Update configuration in Jenkinsfile:**
   - Line 18: Update `TEAMS_WEBHOOK` URL
   - Line 21: Update `EMAIL_RECIPIENTS`

### Frontend Pipeline (ADX-SIP)

1. **Create new pipeline job:**
   - New Item → Pipeline
   - Name: `ADX-SIP-Frontend`

2. **Configure:**
   - Pipeline definition: Pipeline script from SCM
   - SCM: Git
   - Repository URL: `https://github.com/TTS-FZLLC/adx-sip-frontend`
   - Credentials: `github-pat`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`

3. **Copy Jenkinsfile to your frontend repo:**
   ```bash
   cp jenkins/Jenkinsfile.frontend YOUR_FRONTEND_REPO/Jenkinsfile
   ```

4. **Update configuration in Jenkinsfile:**
   - Line 18: Update `TEAMS_WEBHOOK` URL
   - Line 21: Update `EMAIL_RECIPIENTS`

---

## Pipeline Flow

### Backend Deployment

```
GitHub Push → Webhook Trigger
   ↓
1. Teams: "Deployment started"
   ↓
2. Checkout code from GitHub
   ↓
3. Security scans (Semgrep, Trivy, TruffleHog)
   ↓
4. Generate PDF report
   ↓
5. Teams: "Security scan complete" + PDF
   ↓
6. SonarQube analysis
   ↓
7. Quality gate check (PASS/FAIL)
   ├─ FAIL → Teams + Email notification → STOP
   └─ PASS → Continue
   ↓
8. Maven build (mvn clean install)
   ↓
9. Copy WAR to output folder
   ↓
10. Deploy to Windows server:
    - Stop BG processes (running only)
    - Stop Tomcat
    - Backup component
    - Delete old WAR
    - Copy new WAR
    - Start Tomcat
    - Health check
   ↓
11. Teams: "Deployment complete" + health status
   ↓
12. Email: Comprehensive report (security + deployment)
   ↓
DONE ✅
```

### Frontend Deployment

```
Same flow as backend, but:
- Angular build (ng build)
- Copy dist folder
- NO Tomcat stop/start
- Faster deployment
```

---

## Notifications

### Teams Notifications (3 total)

**Notification 1: Deployment Started**
- Sent immediately after GitHub webhook triggers
- Shows developer, branch, status

**Notification 2: Security Scan Complete**
- Sent after Semgrep, Trivy, TruffleHog complete
- Shows risk score, findings count
- Link to PDF report

**Notification 3: Deployment Complete/Failed**
- Sent after deployment finishes
- Shows health check status
- Deployment duration

### Email Notification (1 total)

**Comprehensive Deployment Report**
- Sent at the end (success or failure)
- Includes:
  - Deployment info (developer, time, duration)
  - Security scan summary
  - Quality gate status
  - Deployment details
  - Health check results
  - Next steps
- PDF security report attached

---

## Updating Configuration

### Change Teams Webhook

Edit Jenkinsfile in your repo:
```groovy
TEAMS_WEBHOOK = 'https://your-new-webhook-url'
```

### Change Email Recipients

Edit Jenkinsfile in your repo:
```groovy
EMAIL_RECIPIENTS = 'person1@ttsme.com,person2@ttsme.com'
```

### Update Security Scan Rules

Edit `jenkins/scripts/security_scan.sh`:
```bash
# Line 62: Semgrep configuration
semgrep scan --config=auto ...

# Line 104: Trivy severity levels
trivy fs --severity HIGH,CRITICAL,MEDIUM,LOW ...
```

Rebuild Jenkins:
```bash
docker-compose down
docker-compose up -d --build
```

---

## Maintenance

### View Logs

```bash
# Jenkins logs
docker-compose logs -f jenkins

# SonarQube logs
docker-compose logs -f sonarqube

# All services
docker-compose logs -f
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart Jenkins only
docker-compose restart jenkins

# Restart SonarQube only
docker-compose restart sonarqube
```

### Update After Code Changes

When you update files in `jenkins/` folder:

```bash
# On your local machine
git add .
git commit -m "Update Jenkins configuration"
git push

# On build server
cd ~/jenkins-automation
git pull
docker-compose down
docker-compose up -d --build
```

### Backup Jenkins Data

```bash
# Backup Jenkins home
docker run --rm -v jenkins_home:/data -v $(pwd):/backup ubuntu tar czf /backup/jenkins-backup.tar.gz /data

# Restore Jenkins home
docker run --rm -v jenkins_home:/data -v $(pwd):/backup ubuntu tar xzf /backup/jenkins-backup.tar.gz -C /data --strip 1
```

---

## Troubleshooting

### Jenkins not accessible

```bash
# Check if running
docker ps

# Check logs
docker-compose logs jenkins

# Restart
docker-compose restart jenkins
```

### SonarQube not starting

```bash
# Check logs
docker-compose logs sonarqube

# May need more memory
# Edit docker-compose.yml, add:
# environment:
#   - sonar.web.javaOpts=-Xmx1G
```

### Security scans failing

```bash
# Enter Jenkins container
docker exec -it jenkins-master bash

# Verify tools installed
semgrep --version
trivy --version
trufflehog --version

# Manually run scan
cd /var/jenkins_home/workspace/YOUR-JOB
/usr/local/bin/security-scripts/security_scan.sh
```

### Build failing on Windows agent

```bash
# Check agent connection in Jenkins UI
# Manage Jenkins → Manage Nodes and Clouds

# Verify deploy.py exists on Windows server
# C:\TTS\REManagement\UAE\SIP-NEW\jenkins\deploy.py
```

---

## Security Tools Installed

- **Semgrep 1.52.0** - SAST code security scanner
- **Trivy Latest** - Dependency vulnerability scanner
- **TruffleHog 3.63.7** - Secret detector
- **SonarQube LTS** - Code quality platform

---

## Build Tools Installed

- **Node.js 18** + Angular CLI
- **Maven 3.9.6**
- **Python 3** + PDF libraries
- **JQ** - JSON processor
- **Git**

---

## Support

For issues or questions, contact: kannan.giridharan@ttsme.com

---

## Quick Reference

```bash
# Start everything
docker-compose up -d --build

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart Jenkins
docker-compose restart jenkins

# Update after code changes
git pull && docker-compose down && docker-compose up -d --build

# Access Jenkins
http://192.168.1.136:7080

# Access SonarQube
http://192.168.1.136:9000
```
