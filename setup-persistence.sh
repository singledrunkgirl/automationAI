#!/bin/bash
# save as setup-persistence.sh

# MSFRPC Service
cat > /tmp/msfrpcd.service << 'SERV'
[Unit]
Description=Metasploit RPC Service
After=network.target
[Service]
Type=simple
User=root
ExecStart=/usr/bin/msfrpcd -P kali -S -f -a 127.0.0.1
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SERV
sudo mv /tmp/msfrpcd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable msfrpcd
sudo systemctl start msfrpcd

# Exploit Engine Service
cat > /tmp/exploit-engine.service << 'SERV'
[Unit]
Description=HackWithAI Exploit Engine
After=network.target
[Service]
Type=simple
User=kali
WorkingDirectory=/home/kali/HackWithAI
ExecStart=/usr/bin/python3 /home/kali/HackWithAI/core/exploit_engine.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SERV
sudo mv /tmp/exploit-engine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable exploit-engine
sudo systemctl start exploit-engine

# Lock Config
sudo chattr +i /home/kali/HackWithAI/.env 2>/dev/null

# Status
echo "=== Services Status ==="
sudo systemctl is-enabled msfrpcd exploit-engine
ss -tlnp | grep -E '5556|55553'
echo "=== ALL SET: PERSISTENCE ACTIVE ==="
