FROM kalilinux/kali-rolling

LABEL org.opencontainers.image.title="HackWithAI v2 Agent Sandbox"
LABEL org.opencontainers.image.description="AI Agent Penetration Testing Environment"
LABEL org.opencontainers.image.source="https://github.com/HackWithAI"
LABEL org.opencontainers.image.vendor="HackWithAI"

# ============================================================================
# Environment Variables
# ============================================================================
ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user
ENV GOPATH=/home/user/go
ENV GOCACHE=/home/user/go/.cache
ENV PATH=/home/user/.local/bin:/usr/local/go/bin:/home/user/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# ============================================================================
# Base System Setup (use default Kali CDN mirror - auto-routes to healthy mirrors)
# ============================================================================
RUN apt-get update && \
    apt-get install -y kali-archive-keyring sudo && \
    apt-get update && \
    apt-get upgrade -y

# ============================================================================
# Core System Packages
# ============================================================================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Essential utilities
    curl \
    wget \
    git \
    ca-certificates \
    gnupg2 \
    unzip \
    jq \
    tree \
    perl \
    sudo \
    # Build tools
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    binutils \
    # Python stack
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    python-is-python3 \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libglib2.0-dev \
    # Ruby stack
    ruby-full \
    ruby-dev \
    libnet-ssleay-perl \
    libio-socket-ssl-perl \
    libcrypt-ssleay-perl \
    libssl-dev \
    # Network utilities
    iputils-ping \
    dnsutils \
    iproute2 \
    net-tools \
    whois \
    traceroute \
    netcat-traditional \
    tcpdump \
    # Search tools
    ripgrep \
    # Text editors
    vim \
    nano \
    less \
    # Network scanning & enumeration (from Kali repos - pre-compiled!)
    nmap \
    naabu \
    nikto \
    whatweb \
    wafw00f \
    # Web vulnerability scanners
    sqlmap \
    wapiti \
    wpscan \
    # DNS/subdomain enumeration
    subfinder \
    dnsrecon \
    dnsenum \
    # Web fuzzing & discovery
    ffuf \
    arjun \
    gobuster \
    dirsearch \
    # SMB/NetBIOS tools
    smbclient \
    smbmap \
    nbtscan \
    python3-impacket \
    enum4linux \
    # Network discovery
    hping3 \
    arp-scan \
    # Utilities
    socat \
    proxychains4 \
    seclists \
    hashid \
    libimage-exiftool-perl \
    cewl \
    # SSL/TLS testing
    testssl.sh \
    # Web crawling & recon
    gospider \
    nuclei \
    # Authentication/bruteforce
    hydra \
    # Programming languages
    golang \
    nodejs \
    npm \
    tmux \
    chromium \
    fonts-liberation \
    # Forensics
    binwalk \
    foremost \
    # Document conversion
    pandoc \
    poppler-utils \
    # Web application security scanner
    zaproxy \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# ============================================================================
# Extended Pentest Toolset
# ============================================================================
# Kali package availability changes over time. Install these one-by-one so one
# renamed or unavailable package does not block the full sandbox image build.
RUN set -eux; \
    apt-get update; \
    for pkg in \
      masscan rustscan amass theharvester recon-ng sublist3r dnsx \
      feroxbuster wfuzz commix responder bettercap medusa crunch \
      john hashcat aircrack-ng reaver wifite kismet tshark wireguard-tools \
      exploitdb metasploit-framework beef-xss burpsuite \
      joomscan droopescan xsstrike \
      set spiderfoot sherlock testdisk cherrytree dradis faraday \
      gvm openvas; do \
        apt-get install -y --no-install-recommends "$pkg" || echo "Skipping optional package: $pkg"; \
    done; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# ============================================================================
# WhatWeb Ruby Library Symlink Fix
# ============================================================================
RUN set -eux; \
    if command -v whatweb >/dev/null 2>&1; then \
      mkdir -p /usr/bin/lib; \
      if ls /usr/lib/ruby/vendor_ruby/*.rb >/dev/null 2>&1; then \
        ln -sf /usr/lib/ruby/vendor_ruby/*.rb /usr/bin/lib/; \
      fi; \
    fi

# ============================================================================
# User Setup
# ============================================================================
RUN set -eux; \
    if ! id -u user >/dev/null 2>&1; then \
      useradd --create-home --shell /bin/bash user; \
    fi; \
    usermod -aG sudo user; \
    install -d -m 0755 /etc/sudoers.d /home/user/upload /home/user/go; \
    printf 'user ALL=(ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/hwai-user; \
    chmod 0440 /etc/sudoers.d/hwai-user; \
    user_group="$(id -gn user)"; \
    chown -R "user:${user_group}" /home/user

WORKDIR /home/user

# Ensure login shells, including E2B's Dockerfile builder shell, keep system
# binary directories after adding user-local and Go bin paths.
RUN printf 'export PATH=/home/user/.local/bin:/usr/local/go/bin:/home/user/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n' \
    > /etc/profile.d/00-hwai-path.sh && chmod 644 /etc/profile.d/00-hwai-path.sh

# ============================================================================
# Python Packages for Document Generation & Security Tools
# ============================================================================
RUN pip3 install --break-system-packages \
    reportlab \
    python-docx \
    openpyxl \
    python-pptx \
    pandas \
    pypandoc \
    odfpy

# Additional security-focused Python packages
# Kali's python3-rich package may be newer than httpx[cli]'s rich<14
# requirement, and pip cannot uninstall dpkg-owned packages without RECORD
# metadata. Install a pip-managed compatible rich first so httpx[cli] resolves
# against /usr/local without touching the distro package.
RUN pip3 install --break-system-packages --ignore-installed 'rich<14,>=10' && \
    pip3 install --break-system-packages requests aiohttp jinja2 'httpx[cli]' ratelimit pycryptodomex && \
    pip3 install --break-system-packages shodan censys holehe || true

# ============================================================================
# Git-based Security Tools
# ============================================================================
RUN set -eux; \
    # JWT analysis tool
    git clone https://github.com/ticarpi/jwt_tool.git /opt/jwt_tool || true && \
    if [ -f /opt/jwt_tool/jwt_tool.py ]; then chmod +x /opt/jwt_tool/jwt_tool.py; fi && \
    # Git repository dumper
    git clone https://github.com/internetwache/GitTools.git /opt/gittools && \
    chmod +x /opt/gittools/Dumper/gitdumper.sh /opt/gittools/Extractor/extractor.sh && \
    ln -sf /opt/gittools/Dumper/gitdumper.sh /usr/local/bin/gitdumper && \
    ln -sf /opt/gittools/Extractor/extractor.sh /usr/local/bin/gitextractor && \
    git clone https://github.com/s0md3v/XSStrike.git /opt/XSStrike || true && \
    ([ -f /opt/XSStrike/xsstrike.py ] && ln -sf /opt/XSStrike/xsstrike.py /usr/local/bin/xsstrike) || true && \
    git clone https://github.com/devanshbatham/ParamSpider.git /opt/ParamSpider || true && \
    ([ -f /opt/ParamSpider/paramspider.py ] && ln -sf /opt/ParamSpider/paramspider.py /usr/local/bin/paramspider) || true && \
    git clone https://github.com/devanshbatham/OpenRedireX.git /opt/OpenRedireX || true && \
    ([ -f /opt/OpenRedireX/openredirex.py ] && ln -sf /opt/OpenRedireX/openredirex.py /usr/local/bin/openredirex) || true

# ============================================================================
# Binary Downloads (Platform-aware)
# ============================================================================
RUN set -eux; \
    # Secret scanning tool
    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin && \
    # Vulnerability scanner for containers and filesystems
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin && \
    # httpx with proper architecture detection
    arch=$(uname -m); \
    if [ "$arch" = "x86_64" ]; then platform="linux_amd64"; \
    elif [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then platform="linux_arm64"; \
    else platform="linux_amd64"; fi; \
    HTTPX_URL=$(curl -s https://api.github.com/repos/projectdiscovery/httpx/releases/latest \
      | grep "browser_download_url" | cut -d '"' -f4 \
      | grep "${platform}.zip$" | head -n1); \
    test -n "$HTTPX_URL"; \
    echo "Fetching httpx: $HTTPX_URL"; \
    wget -qO /tmp/httpx.zip "$HTTPX_URL"; \
    mkdir -p /tmp/httpx_extracted; \
    unzip -q /tmp/httpx.zip -d /tmp/httpx_extracted; \
    httpx_bin=$(find /tmp/httpx_extracted -type f -name httpx | head -n1); \
    test -n "$httpx_bin"; \
    mv "$httpx_bin" /usr/local/bin/httpx; \
    chmod +x /usr/local/bin/httpx; \
    rm -rf /tmp/httpx_extracted /tmp/httpx.zip

# ============================================================================
# Create Wrapper Scripts for Python Tools
# ============================================================================
RUN set -eux; \
    # JWT Tool wrapper
    ([ -f /opt/jwt_tool/jwt_tool.py ] && echo '#!/bin/bash\npython3 /opt/jwt_tool/jwt_tool.py "$@"' > /usr/local/bin/jwt-tool && chmod +x /usr/local/bin/jwt-tool) || true

# ============================================================================
# Browser Automation
# ============================================================================
ENV AGENT_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium
ENV AGENT_BROWSER_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
ENV AGENT_BROWSER_ARGS="--disable-blink-features=AutomationControlled,--no-first-run,--no-default-browser-check,--disable-dev-shm-usage,--no-sandbox,--lang=en-US"
ENV AGENT_BROWSER_SCREENSHOT_DIR=/home/user/agent-browser-screenshots

RUN npm install -g agent-browser@0.26.0 && \
    mkdir -p /home/user/agent-browser-screenshots && \
    chown -R user:user /home/user/agent-browser-screenshots && \
    agent-browser doctor --offline --quick

# ============================================================================
# Go-based Security Tools
# ============================================================================
RUN set -eux; \
    go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest && \
    go install github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install github.com/projectdiscovery/cvemap/cmd/cvemap@latest && \
    go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest && \
    go install github.com/projectdiscovery/chaos-client/cmd/chaos@latest && \
    go install github.com/lc/gau/v2/cmd/gau@latest && \
    go install github.com/tomnomnom/waybackurls@latest && \
    go install github.com/hakluke/hakrawler@latest && \
    go install github.com/hahwul/dalfox/v2@latest

# ============================================================================
# TestSSL Symlink - Allow access via both 'testssl' and 'testssl.sh'
# ============================================================================
RUN set -eux; \
    if command -v testssl >/dev/null 2>&1; then \
      ln -sf $(which testssl) /usr/local/bin/testssl.sh; \
    fi

# ============================================================================
# Update Nuclei Templates
# ============================================================================
RUN nuclei -update-templates

# ============================================================================
# Tool Validation
# ============================================================================
RUN set -eux; \
    echo "=== Starting tool validation ===" && \
    test -d /usr/share/seclists && \
    echo "✓ SecLists installed" && \
    which nmap && echo "✓ nmap" && \
    which naabu && echo "✓ naabu" && \
    which nikto && echo "✓ nikto" && \
    which whatweb && echo "✓ whatweb" && \
    which wafw00f && echo "✓ wafw00f" && \
    which sqlmap && echo "✓ sqlmap" && \
    which wapiti && echo "✓ wapiti" && \
    which wpscan && echo "✓ wpscan" && \
    which subfinder && echo "✓ subfinder" && \
    which dnsrecon && echo "✓ dnsrecon" && \
    which dnsenum && echo "✓ dnsenum" && \
    which whois && echo "✓ whois" && \
    which ffuf && echo "✓ ffuf" && \
    which arjun && echo "✓ arjun" && \
    which gobuster && echo "✓ gobuster" && \
    which dirsearch && echo "✓ dirsearch" && \
    which testssl && echo "✓ testssl" && \
    which testssl.sh && echo "✓ testssl.sh" && \
    which nuclei && echo "✓ nuclei" && \
    which hydra && echo "✓ hydra" && \
    which smbclient && echo "✓ smbclient" && \
    which smbmap && echo "✓ smbmap" && \
    which nbtscan && echo "✓ nbtscan" && \
    which enum4linux && echo "✓ enum4linux" && \
    which arp-scan && echo "✓ arp-scan" && \
    which gospider && echo "✓ gospider" && \
    which interactsh-client && echo "✓ interactsh-client" && \
    which katana && echo "✓ katana" && \
    which cvemap && echo "✓ cvemap" && \
    (which masscan && echo "✓ masscan" || true) && \
    (which rustscan && echo "✓ rustscan" || true) && \
    (which amass && echo "✓ amass" || true) && \
    (which theHarvester && echo "✓ theHarvester" || true) && \
    (which recon-ng && echo "✓ recon-ng" || true) && \
    (which gau && echo "✓ gau" || true) && \
    (which waybackurls && echo "✓ waybackurls" || true) && \
    (which hakrawler && echo "✓ hakrawler" || true) && \
    (which feroxbuster && echo "✓ feroxbuster" || true) && \
    (which wfuzz && echo "✓ wfuzz" || true) && \
    (which dalfox && echo "✓ dalfox" || true) && \
    (which searchsploit && echo "✓ searchsploit" || true) && \
    (which msfconsole && echo "✓ metasploit" || true) && \
    (which commix && echo "✓ commix" || true) && \
    (which responder && echo "✓ responder" || true) && \
    (which bettercap && echo "✓ bettercap" || true) && \
    (which john && echo "✓ john" || true) && \
    (which hashcat && echo "✓ hashcat" || true) && \
    (which aircrack-ng && echo "✓ aircrack-ng" || true) && \
    (which tshark && echo "✓ tshark" || true) && \
    (which medusa && echo "✓ medusa" || true) && \
    (which crunch && echo "✓ crunch" || true) && \
    (which shodan && echo "✓ shodan" || true) && \
    (which holehe && echo "✓ holehe" || true) && \
    (which spiderfoot && echo "✓ spiderfoot" || true) && \
    (which sherlock && echo "✓ sherlock" || true) && \
    (which photorec && echo "✓ photorec" || true) && \
    which jwt-tool && echo "✓ jwt_tool" && \
    which gitdumper && echo "✓ gitdumper" && \
    which trufflehog && echo "✓ trufflehog" && \
    which trivy && echo "✓ trivy" && \
    which zaproxy && echo "✓ zaproxy" && \
    which httpx && echo "✓ httpx" && \
    which chromium && echo "✓ chromium" && \
    which agent-browser && echo "✓ agent-browser" && \
    which rg && echo "✓ ripgrep" && \
    which go && echo "✓ go" && \
    which python3 && echo "✓ python3" && \
    which node && echo "✓ node" && \
    which ruby && echo "✓ ruby" && \
    which tmux && echo "✓ tmux" && \
    python3 -c "import reportlab; print('✓ reportlab')" && \
    python3 -c "import docx; print('✓ python-docx')" && \
    python3 -c "import openpyxl; print('✓ openpyxl')" && \
    python3 -c "import pptx; print('✓ python-pptx')" && \
    python3 -c "import pandas; print('✓ pandas')" && \
    python3 -c "import odf; print('✓ odfpy')" && \
    python3 -c "import requests; print('✓ requests')" && \
    echo "=== Version Information ===" && \
    nmap --version | head -n1 && \
    python3 --version && \
    go version && \
    node --version && \
    ruby --version && \
    echo "=== All critical tools validated successfully ==="

# ============================================================================
# Final Cleanup & Permissions
# ============================================================================
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/archives/* && \
    chown -R user:user /home/user

# Default shell
SHELL ["/bin/bash", "-c"]
