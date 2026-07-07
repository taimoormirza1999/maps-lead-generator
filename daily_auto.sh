#!/bin/bash
# Daily outreach — runs at 9am (now driven by OpenClaw cron, not launchd)
# Full pipeline: rescrape if needed → extract emails → send 25 emails → send 5 WhatsApp

# Ensure claude CLI (~/.local/bin) and node (homebrew) resolve regardless of caller env.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

SCRAPPER_DIR="/Users/macbookpro/Desktop/personal/scrapper"
PYTHON="$SCRAPPER_DIR/venv/bin/python3"
NODE=$(which node 2>/dev/null || echo "node")
LOG_DIR="$SCRAPPER_DIR/logs"
DATE=$(date +%Y-%m-%d)
LOG="$LOG_DIR/daily-outreach-$DATE.log"

mkdir -p "$LOG_DIR"

send_alert() {
    local subject="$1"
    local body="$2"
    "$PYTHON" -c "
import smtplib, sys
from email.mime.text import MIMEText
from pathlib import Path

env = {}
for line in Path('$SCRAPPER_DIR/.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

user = env.get('GMAIL_USER','')
pwd  = env.get('GMAIL_APP_PASSWORD','')
if not user or not pwd:
    sys.exit(0)

msg = MIMEText('''$body''', 'plain')
msg['Subject'] = '''$subject'''
msg['From'] = user
msg['To']   = user

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as s:
        s.ehlo(); s.starttls(); s.ehlo()
        s.login(user, pwd)
        s.sendmail(user, user, msg.as_string())
except Exception as e:
    print(f'Alert email failed: {e}')
"
}

{
echo ""
echo "============================================"
echo "Daily outreach: $(date)"
echo "============================================"

cd "$SCRAPPER_DIR" || { echo "ERROR: scrapper dir not found"; exit 1; }

# Step 1: Rescrape if leads are running low
echo ""
echo "--- Step 1: Check leads / auto-rescrape ---"
"$PYTHON" auto_rescrape.py

# Step 2: Extract emails from leads that have websites but no email yet
echo ""
echo "--- Step 2: Extract missing emails ---"
"$PYTHON" extract_emails.py --max 30

# Step 3: Send 25 emails
echo ""
echo "--- Step 3: Email outreach (25) ---"
"$PYTHON" email_outreach.py --limit 25

# Step 4: Send 5 WhatsApp messages
echo ""
echo "--- Step 4: WhatsApp outreach (5) ---"
cd "$SCRAPPER_DIR/whatsapp-support-bot" || { echo "ERROR: whatsapp dir not found"; exit 1; }
"$NODE" auto-outreach.js --limit 5
WA_EXIT=$?

echo ""
echo "Done: $(date)"
} >> "$LOG" 2>&1

# Check if WhatsApp session expired — notify via email
if grep -q "QR code required\|session expired\|Auth failed\|ProtocolError\|Execution context was destroyed\|WHATSAPP_NEEDS_REAUTH" "$LOG" 2>/dev/null; then
    send_alert \
        "Action needed: WhatsApp session expired" \
        "Your WhatsApp session expired — the daily outreach skipped WhatsApp today.

To fix it, run this once on your Mac:
  cd /Users/macbookpro/Desktop/personal/scrapper/whatsapp-support-bot
  node outreach-services.js

Scan the QR code, wait for 'Connected', then Ctrl+C.
Tomorrow's run will work automatically again.

Log: $LOG" >> "$LOG" 2>&1
fi
