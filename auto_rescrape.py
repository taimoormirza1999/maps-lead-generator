"""
Auto-rescrape — runs when leads run low.
Checks pending lead counts; if below threshold, scrapes more from Google Maps.
Called automatically by daily_auto.sh.
"""
import asyncio
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LEADS_DIR = SCRIPT_DIR / 'leads'
WA_SENT = SCRIPT_DIR / 'whatsapp-support-bot' / 'sent-history.json'
EMAIL_SENT = SCRIPT_DIR / 'email-sent-history.json'

PHONE_THRESHOLD = 30   # rescrape if pending leads with phone < this
EMAIL_THRESHOLD = 60   # rescrape if pending leads with email < this

# Queries to cycle through when rescraping
RESCRAPE_QUERIES = [
    ('uae',          'car service Dubai UAE'),
    ('uae',          'restaurant Dubai UAE'),
    ('uae',          'real estate agency Dubai UAE'),
    ('uae',          'hotel Abu Dhabi UAE'),
    ('saudi-arabia', 'real estate agency Riyadh Saudi Arabia'),
    ('saudi-arabia', 'restaurant Riyadh Saudi Arabia'),
    ('saudi-arabia', 'car service Jeddah Saudi Arabia'),
    ('saudi-arabia', 'hotel Riyadh Saudi Arabia'),
    ('greece',       'car service Athens Greece'),
    ('greece',       'restaurant Athens Greece'),
    ('greece',       'hotel Thessaloniki Greece'),
    ('switzerland',  'car service Zurich Switzerland'),
    ('switzerland',  'restaurant Zurich Switzerland'),
    ('switzerland',  'real estate agency Zurich Switzerland'),
    ('switzerland',  'hotel Geneva Switzerland'),
    ('switzerland',  'beauty salon Basel Switzerland'),
]

# Track which query to run next (round-robin)
QUERY_STATE_FILE = SCRIPT_DIR / '.rescrape_state.json'


def load_wa_sent() -> set:
    try:
        return set(json.loads(WA_SENT.read_text()).keys())
    except Exception:
        return set()


def load_email_sent() -> set:
    try:
        return set(json.loads(EMAIL_SENT.read_text()).keys())
    except Exception:
        return set()


def count_pending() -> tuple[int, int]:
    wa_sent = load_wa_sent()
    email_sent = load_email_sent()

    phone_pending = 0
    email_pending = 0

    for csv_path in LEADS_DIR.rglob('*.csv'):
        if csv_path.name.endswith('.bak'):
            continue
        try:
            with open(csv_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    phone = row.get('Phone', '').strip().replace("'", '').replace(' ', '')
                    email = row.get('Email', '').strip()
                    if phone and len(phone) > 6 and phone not in wa_sent:
                        phone_pending += 1
                    if email and '@' in email and email not in email_sent:
                        email_pending += 1
        except Exception:
            pass

    return phone_pending, email_pending


def load_query_state() -> int:
    try:
        return json.loads(QUERY_STATE_FILE.read_text()).get('next_idx', 0)
    except Exception:
        return 0


def save_query_state(idx: int):
    QUERY_STATE_FILE.write_text(json.dumps({'next_idx': idx}))


async def rescrape_one():
    from google_maps_scraper import scrape_google_maps

    idx = load_query_state()
    country, query = RESCRAPE_QUERIES[idx % len(RESCRAPE_QUERIES)]
    next_idx = (idx + 1) % len(RESCRAPE_QUERIES)
    save_query_state(next_idx)

    today = datetime.now().strftime('%Y-%m-%d')
    safe = query.lower().replace(' ', '-').replace(',', '')
    safe = ''.join(c for c in safe if c.isalnum() or c == '-').strip('-')[:60]
    out_dir = LEADS_DIR / country
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = str(out_dir / f'leads_{country}_{safe}_{today}.csv')

    print(f'Rescraping: {query}')
    print(f'Output: {out_file}')

    businesses, fname = await scrape_google_maps(
        query, output_file=out_file, extract_emails=True, headless=True
    )
    print(f'Got {len(businesses)} businesses')
    return len(businesses)


async def main():
    phone_pending, email_pending = count_pending()
    print(f'Pending leads — phone: {phone_pending}, email: {email_pending}')

    needs_phone = phone_pending < PHONE_THRESHOLD
    needs_email = email_pending < EMAIL_THRESHOLD

    if not needs_phone and not needs_email:
        print('Enough leads, no rescrape needed.')
        return

    if needs_phone:
        print(f'Phone leads low ({phone_pending} < {PHONE_THRESHOLD}), scraping more...')
    if needs_email:
        print(f'Email leads low ({email_pending} < {EMAIL_THRESHOLD}), scraping more...')

    count = await rescrape_one()
    print(f'Rescrape done. Got {count} new leads.')


if __name__ == '__main__':
    asyncio.run(main())
