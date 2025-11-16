# Jenkins Build Server - Architecture Update

## Date: 2025-11-16

## Summary of Changes

We switched from **SSH approach** to **Fat Docker approach** for simpler, faster builds!

---

## What Changed?

### ❌ OLD ARCHITECTURE (SSH Approach):
```
Jenkins (Docker - lightweight) → SSH to host → run mvn/ng on host → copy artifacts
```
**Problems:**
- Complex SSH setup (keys, permissions)
- SSH overhead (slower)
- Host dependencies

### ✅ NEW ARCHITECTURE (Fat Docker):
```
Jenkins (Docker with ALL tools) → mount /tts/ttsbuild → build inside Docker → write to /tts/outputttsbuild
```
**Benefits:**
- ✅ **No SSH needed** - simpler!
- ✅ **Faster** - direct execution
- ✅ **Self-contained** - everything in Docker
- ✅ **Portable** - works anywhere

---

## Files Updated

### 1. `docker-compose.yml`
- **SonarQube**: `sonarqube:lts-community` → `sonarqube:community` (LATEST)
- **PostgreSQL**: `postgres:15` → `postgres:16` (LATEST)
- **Jenkins agent port**: `50001:50001` ✅ (already correct)

### 2. `jenkins/Dockerfile` (MAJOR UPDATE)
**Added:**
- ✅ **SDKMAN** for Java & Maven management
  - Java 8 (8.0.432-tem)
  - Java 17 (17.0.13-tem) - default
  - Maven 3.9.9
- ✅ **NVM** for Node.js management
  - Node.js v20 (latest LTS)
- ✅ **Angular CLI** latest version
- ✅ All security tools (Semgrep, Trivy, TruffleHog)
- ✅ Python 3 + PDF libraries

**Helper script created:**
- `/var/jenkins_home/switch-java.sh` - switch between Java 8 and 17

### 3. `jenkins/Jenkinsfile.backend`
**Removed:**
- ❌ SSH agent blocks
- ❌ HOST_USER, HOST_CODE_PATH variables

**Added:**
- ✅ Direct `mvn clean install` inside Docker
- ✅ Direct `git pull` on mounted folder
- ✅ `JAVA_VERSION` environment variable (8 or 17)
- ✅ SDKMAN java switching in build stages

### 4. `jenkins/Jenkinsfile.frontend`
**Removed:**
- ❌ SSH agent blocks

**Added:**
- ✅ Direct `npm install` inside Docker
- ✅ Direct `ng build` inside Docker
- ✅ `NODE_VERSION` environment variable
- ✅ NVM node switching in build stages

### 5. `JENKINS_PLUGINS.md` (NEW)
- Complete list of required Jenkins plugins
- Installation instructions
- Plugin usage documentation

---

## Installed Tools in Docker

### Build Tools:
- **Java 8** (8.0.432-tem) via SDKMAN
- **Java 17** (17.0.13-tem) via SDKMAN - DEFAULT
- **Maven 3.9.9** via SDKMAN
- **Node.js v20** (latest LTS) via NVM
- **Angular CLI** (latest) via npm

### Security Tools:
- **Semgrep 1.52.0** (SAST)
- **Trivy v0.58.2** (vulnerability scanner)
- **TruffleHog v3.63.7** (secret scanner)

### Python:
- **Python 3.13**
- **reportlab, Pillow, requests**

---

## How to Switch Java Versions

### In Jenkinsfile:
```groovy
environment {
    JAVA_VERSION = '17'  // or '8'
}

stage('Build') {
    steps {
        sh """
            source /var/jenkins_home/.sdkman/bin/sdkman-init.sh
            sdk use java ${JAVA_VERSION}.0.13-tem
            mvn clean install
        """
    }
}
```

### Manually in container:
```bash
docker exec -it jenkins-master bash
source ~/.sdkman/bin/sdkman-init.sh
sdk use java 8.0.432-tem   # Switch to Java 8
sdk use java 17.0.13-tem   # Switch to Java 17
```

---

## New Build Flow

### Backend (Maven/Java):
1. Git pull on mounted folder
2. Security scan (Semgrep, Trivy, TruffleHog)
3. Generate PDF report
4. SonarQube analysis (with Java 17)
5. Quality gate
6. Maven build (inside Docker, Java 17)
7. Copy WAR to /tts/outputttsbuild/
8. Windows agent deploys

### Frontend (Angular/Node):
1. Git pull on mounted folder
2. npm install (Node.js v20)
3. Security scan
4. Generate PDF report
5. Angular build (ng build --prod, Node.js v20)
6. Copy dist to /tts/outputttsbuild/
7. Windows agent deploys

---

## What's Removed

### No Longer Needed:
- ❌ SSH key setup
- ❌ SSH credentials in Jenkins
- ❌ host.docker.internal configuration
- ❌ sshagent blocks in Jenkinsfile
- ❌ SSH testing commands
- ❌ Build tools on host (can remove if not used by other projects)

---

## Benefits Summary

| Aspect | OLD (SSH) | NEW (Fat Docker) |
|--------|-----------|------------------|
| **Simplicity** | Complex SSH setup | Just Docker |
| **Speed** | SSH overhead | Direct execution |
| **Portability** | Host-dependent | Self-contained |
| **Maintenance** | SSH keys, host tools | Just update Dockerfile |
| **Security** | SSH authentication | No SSH needed |
| **Debugging** | Check host + Docker | Just check Docker |

---

## Next Steps

1. Push changes to GitHub
2. On build server: `git pull && docker-compose down && docker-compose up -d --build`
3. Install Jenkins plugins (see JENKINS_PLUGINS.md)
4. Configure SonarQube integration
5. Create pipeline jobs
6. Test builds!

---

## Rollback (If Needed)

If you need to go back to SSH approach:
```bash
git revert HEAD
docker-compose down
docker-compose up -d --build
```

---

**Architecture is now SIMPLER and FASTER!** 🚀
