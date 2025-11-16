# Jenkins Build Server - Hybrid Architecture

Complete Jenkins automation for ADXSIP with security scanning, quality gates, and automated deployment.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ BUILD SERVER (192.168.1.136)                                    │
│                                                                  │
│ ┌─────────────────────────┐  ┌──────────────────────────────┐  │
│ │ DOCKER                  │  │ HOST SYSTEM                  │  │
│ │                         │  │                              │  │
│ │ • Jenkins Master        │  │ • Code: /tts/ttsbuild/       │  │
│ │   - Security tools      │  │ • Output: /tts/outputtts...  │  │
│ │   - Python + PDF        │  │                              │  │
│ │   - Scans mounted code  │  │ • Node.js + NVM              │  │
│ │                         │  │ • Maven + Java SDK           │  │
│ │ • SonarQube             │  │                              │  │
│ │                         │  │ Jenkins executes:            │  │
│ │ • PostgreSQL            │  │ - git pull (via SSH)         │  │
│ │                         │  │ - mvn build (via SSH)        │  │
│ └─────────────────────────┘  │ - ng build (via SSH)         │  │
│           ▲                   └──────────────────────────────┘  │
│           │                                 ▲                   │
│           │  Mounted Volumes                │                   │
│           │  - /tts/ttsbuild (read/scan)   │                   │
│           │  - /tts/outputttsbuild (write) │                   │
│           └──────────────────────────────────┘                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

✅ **Jenkins sandboxed** in Docker (portable, easy backup)
✅ **Build tools on host** (use existing setup, no Docker conflicts)
✅ **Security scans in Docker** (Semgrep, Trivy, TruffleHog)
✅ **Fast builds** (native host speed, not containerized)
✅ **Minimal Docker image** (no Node.js, Maven - faster builds)

---

## Pipeline Flow

```
1. GitHub push → Webhook triggers Jenkins
   ↓
2. Teams Notification #1: "Deployment started"
   ↓
3. Jenkins → SSH to host → git pull
   ↓
4. Jenkins scans mounted /tts/ttsbuild folder (Semgrep, Trivy, TruffleHog)
   ↓
5. Jenkins generates PDF security report
   ↓
6. Teams Notification #2: "Security scan complete" + PDF link
   ↓
7. SonarQube analyzes code quality
   ↓
8. Quality Gate check
   ├─ FAIL → Teams + Email notification → STOP
   └─ PASS → Continue
   ↓
9. Jenkins → SSH to host → mvn clean install (or ng build)
   ↓
10. Jenkins copies artifacts to /tts/outputttsbuild/
   ↓
11. Windows agent deploys using deploy.py
   ↓
12. Teams Notification #3: "Deployment complete" + health check
   ↓
13. Email: Comprehensive report (security + deployment + PDF)
   ↓
DONE ✅
```

---

## Quick Start

### Prerequisites

1. **On build server (192.168.1.136):**
   - Docker & Docker Compose installed
   - SSH server running
   - User: `ttsbuild` with sudo access
   - `/tts/ttsbuild/` - code folders
   - `/tts/outputttsbuild/` - output folder

2. **Build tools already on host:**
   - Node.js + NVM
   - Maven
   - Java SDK

### Step 1: Clone Repository

```bash
# On build server
cd ~
git clone YOUR_GITHUB_REPO_URL jenkins-automation
cd jenkins-automation
```

### Step 2: Setup SSH for Jenkins

Jenkins needs to SSH to localhost to execute build commands on host.

```bash
# Create SSH key for Jenkins (no passphrase)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/jenkins_localhost -N ""

# Add public key to authorized_keys
cat ~/.ssh/jenkins_localhost.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test SSH works
ssh -i ~/.ssh/jenkins_localhost ttsbuild@localhost "echo 'SSH works!'"
```

### Step 3: Enable SSH Access from Docker to Host

Add host.docker.internal to /etc/hosts (if not already exists):

```bash
# Check if exists
grep "host.docker.internal" /etc/hosts

# If not exists, add it
echo "192.168.1.136 host.docker.internal" | sudo tee -a /etc/hosts
```

### Step 4: Stop Existing Jenkins (if running)

```bash
docker stop jenkins-master 2>/dev/null || true
docker rm jenkins-master 2>/dev/null || true
```

### Step 5: Build and Start Services

```bash
# Build and start (takes 3-5 minutes)
docker-compose down
docker-compose up -d --build

# Watch logs
docker-compose logs -f jenkins
# Wait for "Jenkins is fully up and running"
# Press Ctrl+C when ready
```

### Step 6: Copy SSH Key into Jenkins Container

```bash
# Copy SSH private key into Jenkins container
docker cp ~/.ssh/jenkins_localhost jenkins-master:/var/jenkins_home/.ssh/id_rsa

# Set permissions
docker exec -u root jenkins-master chown jenkins:jenkins /var/jenkins_home/.ssh/id_rsa
docker exec -u root jenkins-master chmod 600 /var/jenkins_home/.ssh/id_rsa

# Test SSH from inside Jenkins container
docker exec jenkins-master ssh -o StrictHostKeyChecking=no -i /var/jenkins_home/.ssh/id_rsa ttsbuild@host.docker.internal "echo 'SSH from container works!'"
```

### Step 7: Access Services

- **Jenkins**: http://192.168.1.136:7080
- **SonarQube**: http://192.168.1.136:9000

### Step 8: Get Jenkins Initial Password

```bash
docker exec jenkins-master cat /var/jenkins_home/secrets/initialAdminPassword
```

---

## Jenkins Configuration

### 1. Initial Setup

1. Access Jenkins: http://192.168.1.136:7080
2. Paste initial admin password
3. Install **suggested plugins**

### 2. Install Additional Plugins

📋 **See [JENKINS_PLUGINS.md](JENKINS_PLUGINS.md) for complete plugin list**

Go to **Manage Jenkins → Plugins → Available plugins**

**Required Plugins** (install these):
- Email Extension Plugin
- HTTP Request Plugin
- SonarQube Scanner for Jenkins
- SSH Agent Plugin
- Pipeline Utility Steps
- Config File Provider Plugin

**Optional but Recommended**:
- Blue Ocean (modern UI)
- AnsiColor (colorized logs)

After installing, check **"Restart Jenkins when installation is complete"**.

### 3. Configure SSH Credentials

**Manage Jenkins → Credentials → System → Global credentials → Add Credentials**

- **Kind**: SSH Username with private key
- **ID**: `localhost-ssh`
- **Username**: `ttsbuild`
- **Private Key**: Enter directly
  - Paste contents of `/home/ttsbuild/.ssh/jenkins_localhost`
  - ```bash
    cat ~/.ssh/jenkins_localhost
    ```
- **Passphrase**: (leave empty)
- **Description**: `SSH to localhost for build execution`

Click **Create**.

### 4. Configure SonarQube

**A. Setup SonarQube First**

1. Access: http://192.168.1.136:9000
2. Default login: `admin` / `admin`
3. Change password when prompted
4. My Account → Security → Generate Token
   - Name: `Jenkins`
   - Type: Global Analysis Token
   - Copy the token

**B. Add SonarQube Server in Jenkins**

**Manage Jenkins → System → SonarQube servers**

- **Name**: `SonarQube`
- **Server URL**: `http://sonarqube:9000`
- **Server authentication token**:
  - Add → Jenkins → Secret text
  - Secret: (paste SonarQube token)
  - ID: `sonarqube-token`
  - Description: `SonarQube Token`
  - Add

Click **Save**.

**C. Create Quality Gate in SonarQube**

1. SonarQube → Quality Gates → Create
2. Name: `TTS Quality Gate`
3. Add conditions:
   - **Code Coverage < 70%** → FAILED
   - **Bugs > 20** → FAILED
   - **Vulnerabilities > 10** → FAILED
4. Set as default

### 5. Configure Email Notifications

**Manage Jenkins → System → Extended E-mail Notification**

- **SMTP server**: `smtp.office365.com` (or your SMTP server)
- **SMTP Port**: `587`
- **Credentials**: Add → Username with password
  - Username: `jenkins@ttsme.com`
  - Password: (your email password or app password)
- **Use SSL**: Unchecked
- **Use TLS**: Checked
- **Default Recipients**: `kannan.giridharan@ttsme.com`

Click **Save**.

---

## Creating Jenkins Pipelines

### Backend Pipeline (ADXSIP)

**1. Create Pipeline Job**

- **New Item** → Name: `ADXSIP-Backend` → Pipeline → OK

**2. Configure**

- **Description**: `ADXSIP Backend Build and Deploy`
- **Build Triggers**:
  - Check **GitHub hook trigger for GITScm polling** (if using webhooks)

**3. Pipeline Definition**

- **Definition**: Pipeline script from SCM
- **SCM**: Git
- **Repository URL**: `https://github.com/TTS-FZLLC/adxsip-backend`
- **Credentials**: `github-pat` (add if not exists)
- **Branch**: `*/main`
- **Script Path**: `Jenkinsfile`

**4. Copy Jenkinsfile to your repo**

```bash
# Copy from jenkins-automation repo
cp ~/jenkins-automation/jenkins/Jenkinsfile.backend ~/path/to/adxsip-backend/Jenkinsfile

# Edit and update:
# - Line 37: HOST_CODE_PATH (path to your code on host)
# - Line 45: TEAMS_WEBHOOK (your Teams webhook URL)
# - Line 48: EMAIL_RECIPIENTS

# Commit and push
cd ~/path/to/adxsip-backend
git add Jenkinsfile
git commit -m "Add Jenkins pipeline"
git push
```

**5. Test Pipeline**

- Click **Build Now**
- Check console output for errors

### Frontend Pipeline (ADX-SIP)

Same steps as backend, but:
- Job name: `ADX-SIP-Frontend`
- Use `Jenkinsfile.frontend`
- Different repository URL

---

## Configuration Required

### In Jenkinsfile (each project repo)

**Backend (Jenkinsfile.backend):**
```groovy
// Line 37: Update code path on host
HOST_CODE_PATH = '/tts/ttsbuild/ADXSIP/ADX-SIP'

// Line 45: Add Teams webhook
TEAMS_WEBHOOK = 'https://ttsmedxb.webhook.office.com/webhookb2/...'

// Line 48: Update email recipients
EMAIL_RECIPIENTS = 'kannan.giridharan@ttsme.com,team@ttsme.com'
```

**Frontend (Jenkinsfile.frontend):**
```groovy
// Same updates as backend
```

### In deploy.py (Windows server)

We'll update deploy.py to add:
- `--action deploy-backend` (stop BG, stop Tomcat, backup, deploy, start Tomcat)
- `--action deploy-frontend` (backup, replace files, no Tomcat restart)
- Selective backup: `--component ADXSIP`
- Health check and JSON status output

---

## Troubleshooting

### Docker Build Fails

**Error**: Node.js version conflicts

**Solution**: This is expected! We removed Node.js from Docker. Build uses host's Node.js via SSH.

### SSH Connection Fails

```bash
# Test from inside Jenkins container
docker exec jenkins-master ssh -o StrictHostKeyChecking=no ttsbuild@host.docker.internal "echo test"

# If fails, check:
1. SSH key exists in container: docker exec jenkins-master ls -la /var/jenkins_home/.ssh/
2. Permissions: should be 600 for id_rsa
3. host.docker.internal resolves: docker exec jenkins-master ping -c 1 host.docker.internal
4. SSH server running on host: systemctl status ssh
```

### Security Scans Fail

```bash
# Enter Jenkins container
docker exec -it jenkins-master bash

# Verify tools installed
semgrep --version
trivy --version
trufflehog --version

# Test scan manually
cd /tts/ttsbuild/ADXSIP/ADX-SIP
/usr/local/bin/security-scripts/security_scan.sh
```

### SonarQube Not Starting

```bash
# Check logs
docker-compose logs sonarqube

# SonarQube needs 2GB RAM minimum
# Check available memory
free -h

# Increase if needed (edit docker-compose.yml)
```

### Git Pull Fails

```bash
# Check git is configured on host
ssh ttsbuild@localhost "cd /tts/ttsbuild/ADXSIP/ADX-SIP && git status"

# Configure git if needed
git config --global user.name "Jenkins"
git config --global user.email "jenkins@ttsme.com"
```

---

## Maintenance

### Update Jenkins Scripts

```bash
# On local machine
cd jenkins-automation
git pull

# On build server
cd ~/jenkins-automation
git pull
docker-compose down
docker-compose up -d --build
```

### View Logs

```bash
# Jenkins logs
docker-compose logs -f jenkins

# SonarQube logs
docker-compose logs -f sonarqube

# All services
docker-compose logs -f
```

### Backup Jenkins Data

```bash
# Backup Jenkins home
docker run --rm \
  -v jenkins_home:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/jenkins-backup-$(date +%Y%m%d).tar.gz /data

# Restore
docker run --rm \
  -v jenkins_home:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/jenkins-backup-YYYYMMDD.tar.gz -C /data --strip 1
```

---

## What's Installed

### In Jenkins Docker Container
- Jenkins LTS
- Semgrep 1.52.0 (code security)
- Trivy (vulnerability scanner)
- TruffleHog 3.63.7 (secret detector)
- Python 3 + PDF libraries (reportlab, Pillow)
- SSH client
- JQ (JSON processor)

### On Host System (used via SSH)
- Node.js + NVM
- Angular CLI
- Maven
- Java SDK
- Git

### In SonarQube
- Code quality analysis
- Security hotspots
- Code coverage tracking
- Quality gates

---

## Security Features

✅ **3 Security Tools**: Semgrep + Trivy + TruffleHog
✅ **Quality Gate**: Blocks bad code from deploying
✅ **PDF Reports**: Comprehensive security findings
✅ **Email Alerts**: Security + deployment status
✅ **Teams Notifications**: Real-time updates
✅ **Backup**: Automatic before every deployment
✅ **Health Checks**: Verify deployment success

---

## Next Steps

After Jenkins is running:

1. ✅ Configure SSH credentials
2. ✅ Configure SonarQube integration
3. ✅ Create pipeline jobs
4. ✅ Update deploy.py on Windows server
5. ✅ Test security scanning
6. ✅ Test full deployment pipeline

---

## Support

**Created by**: TTS DevOps Team
**Date**: 2025-11-16
**Contact**: kannan.giridharan@ttsme.com

---

## Quick Reference

```bash
# Start everything
cd ~/jenkins-automation
docker-compose up -d --build

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart Jenkins
docker-compose restart jenkins

# SSH test from Jenkins
docker exec jenkins-master ssh -o StrictHostKeyChecking=no ttsbuild@host.docker.internal "echo test"

# Access URLs
Jenkins:   http://192.168.1.136:7080
SonarQube: http://192.168.1.136:9000
```

---

**Ready to deploy! 🚀**
