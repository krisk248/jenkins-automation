# ============================================================================
# JENKINS DOCKERFILE - Lightweight with Security Tools Only
# ============================================================================
# This Jenkins image is LIGHTWEIGHT and contains ONLY:
# - Security scanning tools: Semgrep, Trivy, TruffleHog
# - Python 3 with PDF generation libraries
# - SSH client for executing commands on host
#
# Build tools (Node.js, Maven, Java) are NOT included.
# They are used from the HOST system via SSH.
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
    openssh-client \
    jq \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# PYTHON 3 + LIBRARIES FOR PDF GENERATION
# ============================================================================
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && pip3 install --break-system-packages --no-cache-dir \
        reportlab==4.0.7 \
        Pillow==10.1.0 \
        requests==2.31.0 \
    && python3 --version

# ============================================================================
# SEMGREP - Static Application Security Testing (SAST)
# ============================================================================
RUN pip3 install --break-system-packages --no-cache-dir semgrep==1.52.0 \
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
RUN echo "=== Security Tools ===" \
    && semgrep --version \
    && trivy --version \
    && trufflehog --version \
    && echo "=== Python ===" \
    && python3 --version \
    && echo "=== SSH Client ===" \
    && ssh -V \
    && echo "=== All tools installed successfully ===" \
    && echo "" \
    && echo "NOTE: Build tools (Node.js, Maven, Java) are NOT installed." \
    && echo "      They will be used from the HOST system via SSH."
