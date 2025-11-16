# ============================================================================
# JENKINS DOCKERFILE - Complete Build Environment
# ============================================================================
# This Jenkins image contains EVERYTHING needed for builds:
# - Security scanning tools: Semgrep, Trivy, TruffleHog
# - Python 3 with PDF generation libraries
# - SDKMAN: Java 8, Java 17, Maven
# - NVM: Node.js v20
# - Angular CLI
#
# No SSH needed - builds run directly inside Docker!
# Code is mounted from host at /tts/ttsbuild/
# Output goes to /tts/outputttsbuild/
# ============================================================================

FROM jenkins/jenkins:lts

# Switch to root for system installations
USER root

# ============================================================================
# SYSTEM PACKAGES
# ============================================================================
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    jq \
    unzip \
    zip \
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
    python3-dev \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && pip3 install --break-system-packages --no-cache-dir \
        reportlab \
        Pillow \
        requests \
    && python3 --version \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# SEMGREP - Static Application Security Testing (SAST)
# ============================================================================
RUN pip3 install --break-system-packages --no-cache-dir semgrep \
    && semgrep --version

# ============================================================================
# TRIVY - Vulnerability Scanner (Standalone Binary)
# ============================================================================
RUN wget https://github.com/aquasecurity/trivy/releases/download/v0.58.2/trivy_0.58.2_Linux-64bit.tar.gz \
    && tar -xzf trivy_0.58.2_Linux-64bit.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/trivy \
    && rm trivy_0.58.2_Linux-64bit.tar.gz \
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
# SWITCH TO JENKINS USER FOR USER-LEVEL INSTALLATIONS
# ============================================================================
USER jenkins

# ============================================================================
# SDKMAN - Java & Maven Version Manager
# ============================================================================
# Install SDKMAN
RUN curl -s "https://get.sdkman.io" | bash

# Source SDKMAN and install Java 8, Java 17, and Maven
RUN bash -c "source /var/jenkins_home/.sdkman/bin/sdkman-init.sh && \
    sdk install java 8.0.432-tem && \
    sdk install java 17.0.13-tem && \
    sdk install maven 3.9.9 && \
    sdk default java 17.0.13-tem && \
    sdk default maven 3.9.9"

# Add SDKMAN to PATH
ENV SDKMAN_DIR="/var/jenkins_home/.sdkman"
ENV PATH="${SDKMAN_DIR}/candidates/java/current/bin:${SDKMAN_DIR}/candidates/maven/current/bin:${PATH}"
ENV JAVA_HOME="${SDKMAN_DIR}/candidates/java/current"
ENV MAVEN_HOME="${SDKMAN_DIR}/candidates/maven/current"

# ============================================================================
# NVM - Node.js Version Manager
# ============================================================================
# Install NVM
ENV NVM_DIR="/var/jenkins_home/.nvm"
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# Install Node.js v20 (LTS) and set as default
RUN bash -c "source $NVM_DIR/nvm.sh && \
    nvm install 20 && \
    nvm alias default 20 && \
    nvm use default"

# Add Node.js to PATH
ENV NODE_VERSION=20
ENV PATH="${NVM_DIR}/versions/node/v${NODE_VERSION}.18.0/bin:${PATH}"

# ============================================================================
# ANGULAR CLI - Latest Version
# ============================================================================
RUN bash -c "source $NVM_DIR/nvm.sh && \
    nvm use 20 && \
    npm install -g @angular/cli@latest"

# ============================================================================
# CLEANUP
# ============================================================================
USER root
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch back to Jenkins user
USER jenkins

# ============================================================================
# CREATE HELPER SCRIPT TO SWITCH JAVA VERSIONS
# ============================================================================
RUN echo '#!/bin/bash\n\
# Helper script to switch Java versions\n\
# Usage: switch-java 8 or switch-java 17\n\
source /var/jenkins_home/.sdkman/bin/sdkman-init.sh\n\
if [ "$1" = "8" ]; then\n\
    sdk use java 8.0.432-tem\n\
elif [ "$1" = "17" ]; then\n\
    sdk use java 17.0.13-tem\n\
else\n\
    echo "Usage: switch-java [8|17]"\n\
    exit 1\n\
fi\n\
java -version' > /var/jenkins_home/switch-java.sh && \
chmod +x /var/jenkins_home/switch-java.sh

# ============================================================================
# VERIFY INSTALLATIONS
# ============================================================================
RUN echo "=== SECURITY TOOLS ===" && \
    semgrep --version && \
    trivy --version && \
    trufflehog --version && \
    echo "" && \
    echo "=== PYTHON ===" && \
    python3 --version && \
    python3 -c "import reportlab; import PIL; import requests; print('Python libraries OK')" && \
    echo "" && \
    echo "=== BUILD TOOLS ===" && \
    bash -c "source /var/jenkins_home/.sdkman/bin/sdkman-init.sh && java -version" && \
    bash -c "source /var/jenkins_home/.sdkman/bin/sdkman-init.sh && mvn -version" && \
    bash -c "source /var/jenkins_home/.nvm/nvm.sh && node --version" && \
    bash -c "source /var/jenkins_home/.nvm/nvm.sh && npm --version" && \
    bash -c "source /var/jenkins_home/.nvm/nvm.sh && ng version" && \
    echo "" && \
    echo "=== ALL TOOLS INSTALLED SUCCESSFULLY ===" && \
    echo "" && \
    echo "JAVA VERSIONS AVAILABLE:" && \
    bash -c "source /var/jenkins_home/.sdkman/bin/sdkman-init.sh && sdk list java | grep installed" && \
    echo "" && \
    echo "SWITCH JAVA: source /var/jenkins_home/switch-java.sh [8|17]"

# ============================================================================
# WORKSPACE
# ============================================================================
WORKDIR /var/jenkins_home

# Expose ports
EXPOSE 8080 50001
