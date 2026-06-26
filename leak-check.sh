#!/bin/bash
# leak-check.sh — Full Anonymity & Leak Audit

echo "========================================"
echo "    COMPLETE LEAK CHECK - ANONYMITY"
echo "========================================"
echo ""

# ─── [1] IP & DNS Leak ───
echo "--- [1] PUBLIC IP & DNS LEAK CHECK ---"
echo -n "  Public IP: "
curl -s ifconfig.me
echo ""

echo -n "  DNS Leak Test: "
curl -s https://dnsleaktest.com/results.html 2>/dev/null | grep -oP 'IP Address: \K[^<]+' || echo "Check manually"

echo -n "  WebRTC Leak: "
curl -s https://ipleak.net 2>/dev/null | grep -oP 'Your IP: \K[^<]+' || echo "Check browser manually"

echo ""

# ─── [2] MAC Address ───
echo "--- [2] MAC ADDRESS CHECK ---"
ip link show | grep -E 'link/ether' | awk '{print "  Interface: "$2, "MAC:", $2}'

# Check if MAC is randomized
CURRENT_MAC=$(ip link show | grep -E 'link/ether' | head -1 | awk '{print $2}')
if [[ $CURRENT_MAC == *"02:00:00"* || $CURRENT_MAC == *"00:00:00"* ]]; then
    echo "  ⚠️  MAC may not be randomized"
else
    echo "  ✅ MAC appears randomized"
fi
echo ""

# ─── [3] Browser/User-Agent Leak ───
echo "--- [3] USER-AGENT & BROWSER FINGERPRINT ---"
echo -n "  Current User-Agent: "
curl -s https://httpbin.org/user-agent | python3 -c "import sys,json; print(json.load(sys.stdin).get('user-agent','Unknown'))"
echo ""

# ─── [4] Environment Variable Leaks ───
echo "--- [4] ENVIRONMENT VARIABLE LEAKS ---"
# Check if any API keys are exposed in env
for key in API KEY SECRET TOKEN PASSWORD; do
    count=$(env | grep -ci "$key" 2>/dev/null)
    if [ "$count" -gt 0 ]; then
        echo "  ⚠️  $key variables found in environment: $count"
    fi
done
echo "  ✅ Environment scan complete"
echo ""

# ─── [5] Git/Config Leaks ───
echo "--- [5] GIT & CONFIG LEAKS ---"
if [ -d /home/kali/HackWithAI/.git ]; then
    echo "  ⚠️  Git repository detected! Possible credential leak:"
    cd /home/kali/HackWithAI && git log --oneline -5 2>/dev/null
    # Check for committed secrets
    cd /home/kali/HackWithAI && git diff --cached 2>/dev/null | grep -qi "key\|secret\|token\|password" && echo "  ❌ Secrets may be in git history!" || echo "  ✅ No secrets in git staging"
else
    echo "  ✅ No git repo found"
fi
echo ""

# ─── [6] Browser History/Data Leaks ───
echo "--- [6] BROWSER DATA LEAKS ---"
# Check Firefox profiles
if [ -d ~/.mozilla/firefox/*.default*/ ]; then
    echo "  ⚠️  Firefox profiles found - could contain cookies/history"
fi
# Check Chromium
if [ -d ~/.config/chromium ]; then
    echo "  ⚠️  Chromium data found - could contain saved passwords"
fi
echo ""

# ─── [7] Log Files Leak ───
echo "--- [7] LOG FILE LEAKS ---"
find /tmp -name "*.log" -user kali 2>/dev/null | head -5
find /home/kali -name "*.log" -mtime -7 2>/dev/null | head -10
echo "  ✅ Log scan complete"
echo ""

# ─── [8] SSH Key Leaks ───
echo "--- [8] SSH KEY LEAKS ---"
if [ -f ~/.ssh/id_rsa ]; then
    echo "  ❌ SSH PRIVATE KEY FOUND: ~/.ssh/id_rsa"
fi
if [ -f ~/.ssh/id_ed25519 ]; then
    echo "  ❌ SSH PRIVATE KEY FOUND: ~/.ssh/id_ed25519"
fi
ls ~/.ssh/*.pub 2>/dev/null && echo "  ⚠️  Public SSH keys exposed"
echo ""

# ─── [9] API Key Leak in Config Files ───
echo "--- [9] API KEY LEAK IN CONFIG FILES ---"
grep -rni "sk-" /home/kali/HackWithAI/ 2>/dev/null | grep -v ".git/" | head -5
grep -rni "AIza" /home/kali/HackWithAI/ 2>/dev/null | grep -v ".git/" | head -5
grep -rni "key=" /home/kali/HackWithAI/.env 2>/dev/null
echo ""

# ─── [10] Tor/Proxy Status ───
echo "--- [10] TOR/PROXY STATUS ---"
if command -v tor &>/dev/null; then
    systemctl is-active tor --quiet 2>/dev/null && echo "  ✅ Tor is ACTIVE" || echo "  ⚠️  Tor installed but NOT running"
else
    echo "  ℹ️  Tor not installed"
fi
if command -v proxychains &>/dev/null; then
    echo "  ✅ ProxyChains available"
fi
echo ""

# ─── [11] Whoami Check ───
echo "--- [11] WHOAMI & SYSTEM INFO ---"
echo "  User: $(whoami)"
echo "  Hostname: $(hostname)"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')"
echo "  Kernel: $(uname -r)"
echo "  Uptime: $(uptime -p | sed 's/up //')"
echo ""

echo "========================================"
echo "         LEAK CHECK COMPLETE"
echo "========================================"
