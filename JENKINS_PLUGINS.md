# Jenkins Plugins Required for ADXSIP Build Pipeline

## Installation Order

### Step 1: Install Suggested Plugins (Automatic)
When you first access Jenkins, select **"Install suggested plugins"**. This will automatically install:

✅ **Core Plugins** (installed automatically):
- Git
- GitHub
- Pipeline
- Pipeline: Stage View
- Workflow Aggregator
- Credentials Binding
- SSH Credentials
- Plain Credentials
- Timestamper
- Build Timeout
- Workspace Cleanup
- Gradle
- Ant
- Maven Integration
- Pipeline Maven Integration
- Email Extension
- Mailer

### Step 2: Install Additional Required Plugins (Manual)

After suggested plugins install and Jenkins restarts, go to:
**Manage Jenkins → Plugins → Available plugins**

Search and install these plugins **ONE BY ONE** or select all and install together:

#### ✅ Required for Our Pipeline:

1. **Email Extension Plugin**
   - Plugin ID: `email-ext`
   - Why: For sending comprehensive HTML emails with attachments
   - Used in: Jenkinsfile stages for sending deployment reports

2. **HTTP Request Plugin**
   - Plugin ID: `http-request`
   - Why: For sending Teams webhook notifications
   - Used in: All notification stages

3. **SonarQube Scanner for Jenkins**
   - Plugin ID: `sonar`
   - Why: For code quality analysis and quality gates
   - Used in: SonarQube Analysis and Quality Gate stages

4. **SSH Agent Plugin**
   - Plugin ID: `ssh-agent`
   - Why: For SSH connections to host system to run builds
   - Used in: Git pull, Maven build, Angular build stages

5. **Pipeline Utility Steps**
   - Plugin ID: `pipeline-utility-steps`
   - Why: For reading JSON files (readJSON)
   - Used in: Reading security scan summary.json

6. **Config File Provider Plugin**
   - Plugin ID: `config-file-provider`
   - Why: For managing Maven settings and configuration files
   - Used in: Maven builds with SonarQube

#### ✅ Recommended (Optional but Useful):

7. **Blue Ocean**
   - Plugin ID: `blueocean`
   - Why: Modern UI for viewing pipelines
   - Optional: Makes pipeline visualization much better

8. **AnsiColor**
   - Plugin ID: `ansicolor`
   - Why: Colorized console output
   - Optional: Makes logs easier to read

9. **Build Timestamp Plugin**
   - Plugin ID: `build-timestamp`
   - Why: Adds BUILD_TIMESTAMP variable
   - Optional: Already using sh date command

10. **GitHub Branch Source Plugin**
    - Plugin ID: `github-branch-source`
    - Why: For GitHub webhooks and branch management
    - Optional: If you want automatic builds on push

### Step 3: Restart Jenkins

After installing all plugins:
- Check **"Restart Jenkins when installation is complete and no jobs are running"**
- Wait 1-2 minutes for restart

---

## Complete Plugin Installation Command

If you prefer to install plugins via CLI (advanced):

```bash
# Enter Jenkins container
docker exec -it jenkins-master bash

# Install plugins
jenkins-plugin-cli --plugins \
  email-ext \
  http-request \
  sonar \
  ssh-agent \
  pipeline-utility-steps \
  config-file-provider \
  blueocean \
  ansicolor \
  build-timestamp \
  github-branch-source

# Restart Jenkins
exit
docker restart jenkins-master
```

---

## Verification After Installation

Go to **Manage Jenkins → Plugins → Installed plugins**

You should see:
- ✅ Email Extension Plugin
- ✅ HTTP Request Plugin
- ✅ SonarQube Scanner
- ✅ SSH Agent Plugin
- ✅ Pipeline Utility Steps
- ✅ Config File Provider Plugin

If all are present → **READY TO CREATE PIPELINES!** 🚀

---

## Plugin Usage in Our Pipeline

### Jenkinsfile.backend and Jenkinsfile.frontend use:

| Stage | Plugin Used | Purpose |
|-------|------------|---------|
| Notify Start | HTTP Request | Send Teams webhook notification |
| Update Code | SSH Agent | SSH to host to run `git pull` |
| Security Scans | (none) | Direct shell commands |
| Generate Report | Pipeline Utility Steps | Read summary.json |
| Notify Security Scan | HTTP Request | Send Teams webhook with PDF link |
| SonarQube Analysis | SonarQube Scanner | Run `mvn sonar:sonar` |
| Quality Gate | SonarQube Scanner | Wait for quality gate result |
| Build | SSH Agent | SSH to host to run `mvn clean install` |
| Copy to Output | (none) | Direct shell commands |
| Deploy | (none) | Run deploy.py on Windows agent |
| Notify Success | HTTP Request | Send Teams webhook notification |
| Notify Success (email) | Email Extension | Send HTML email with PDF attachment |
| Post: Failure | HTTP Request + Email Extension | Send failure notifications |

---

## Notes

1. **Email Extension Plugin** is different from **Mailer Plugin**:
   - Mailer: Simple text emails
   - Email Extension: HTML emails with attachments (what we need)

2. **SSH Agent Plugin** vs **SSH Credentials Plugin**:
   - SSH Credentials: Stores SSH keys
   - SSH Agent: Uses SSH keys to execute commands (what we need)

3. All plugins are **free and open source**

4. Total additional plugins to install manually: **4 required + 4 optional** = 8 plugins

---

## Troubleshooting

**If plugin installation fails:**
1. Check Jenkins logs: `docker logs jenkins-master`
2. Restart Jenkins: `docker restart jenkins-master`
3. Try installing plugins one at a time instead of all together

**If plugin is not available:**
- Check if you selected "Install suggested plugins" first
- Some plugins may already be installed
- Refresh the Available plugins list

**If pipeline fails with "No such DSL method":**
- Missing plugin! Check the plugin list above
- Restart Jenkins after installing plugins
