# ============================================================================
# JENKINS DOCKERFILE - Build Server with Security Tools
# ============================================================================
# This custom Jenkins image includes:
# - Node.js 18 + Angular CLI (for frontend builds)
# - Maven 3.9 (for backend Java builds)
# - Python 3 with PDF generation libraries
# - Security scanning tools: Semgrep, Trivy, TruffleHog
# - Git, Docker CLI, and other build tools
# ============================================================================

FROM jenkins/jenkins:lts

# Switch to root for installations
USER root

# ============================================================================
# SYSTEM PACKAGES
# ============================================================================
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    unzip \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# NODE.JS 18 + NPM + ANGULAR CLI
# ============================================================================
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @angular/cli@latest \
    && npm --version \
    && node --version \
    && ng version

# ============================================================================
# MAVEN 3.9
# ============================================================================
RUN wget https://dlcdn.apache.org/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.tar.gz \
    && tar -xzf apache-maven-3.9.6-bin.tar.gz -C /opt \
    && ln -s /opt/apache-maven-3.9.6 /opt/maven \
    && rm apache-maven-3.9.6-bin.tar.gz

ENV MAVEN_HOME=/opt/maven
ENV PATH="${MAVEN_HOME}/bin:${PATH}"

# ============================================================================
# PYTHON 3 + LIBRARIES FOR PDF GENERATION
# ============================================================================
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && pip3 install --no-cache-dir \
        reportlab==4.0.7 \
        Pillow==10.1.0 \
        matplotlib==3.8.2 \
        pandas==2.1.4 \
        requests==2.31.0 \
    && python3 --version

# ============================================================================
# SEMGREP - Static Application Security Testing (SAST)
# ============================================================================
RUN pip3 install --no-cache-dir semgrep==1.52.0 \
    && semgrep --version

# ============================================================================
# TRIVY - Vulnerability Scanner
# ============================================================================
RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add - \
    && echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | tee -a /etc/apt/sources.list.d/trivy.list \
    && apt-get update \
    && apt-get install -y trivy \
    && trivy --version

# ============================================================================
# TRUFFLEHOG v3 - Secret Scanner
# ============================================================================
RUN wget https://github.com/trufflesecurity/trufflehog/releases/download/v3.63.7/trufflehog_3.63.7_linux_amd64.tar.gz \
    && tar -xzf trufflehog_3.63.7_linux_amd64.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/trufflehog \
    && rm trufflehog_3.63.7_linux_amd64.tar.gz \
    && trufflehog --version

# ============================================================================
# JQ - JSON Processor (for parsing scan results)
# ============================================================================
RUN apt-get update && apt-get install -y jq \
    && jq --version

# ============================================================================
# COPY CUSTOM SCRIPTS AND TEMPLATES
# ============================================================================
# Copy security scanning script
COPY scripts/security_scan.sh /usr/local/bin/security-scripts/security_scan.sh
RUN chmod +x /usr/local/bin/security-scripts/security_scan.sh

# Copy PDF report generator
COPY scripts/generate_report.py /usr/local/bin/security-scripts/generate_report.py
RUN chmod +x /usr/local/bin/security-scripts/generate_report.py

# Copy email template
COPY templates/email_template.html /usr/local/bin/security-templates/email_template.html

# ============================================================================
# CLEANUP
# ============================================================================
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch back to Jenkins user
USER jenkins

# ============================================================================
# VERIFY INSTALLATIONS
# ============================================================================
RUN echo "=== Build Tools ===" \
    && node --version \
    && npm --version \
    && ng version \
    && mvn --version \
    && echo "=== Security Tools ===" \
    && semgrep --version \
    && trivy --version \
    && trufflehog --version \
    && echo "=== Python ===" \
    && python3 --version \
    && echo "=== All tools installed successfully ==="
