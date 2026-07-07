"""
Daily email outreach — sends personalized cold emails to leads.
Uses the central email service at ~/.email-service/
Usage: python3 email_outreach.py [--limit 25]
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, '/Users/macbookpro/.email-service')
from email_service import send_with_claude, already_sent

SCRIPT_DIR = Path(__file__).parent
LEADS_DIR = SCRIPT_DIR / 'leads'
LIMIT = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 25


def country_from_path(p: Path) -> str:
    name = p.parent.name.lower()
    if 'uae' in name or 'emirates' in name: return 'UAE'
    if 'saudi' in name: return 'Saudi Arabia'
    if 'greece' in name: return 'Greece'
    if 'germany' in name: return 'Germany'
    if 'switzerland' in name or 'swiss' in name: return 'Switzerland'
    return name.replace('-', ' ').title()


def language_from_country(country: str) -> str:
    c = (country or '').lower()
    if 'uae' in c or 'emirates' in c or 'saudi' in c: return 'Arabic'
    if 'greece' in c: return 'Greek'
    if 'germany' in c or 'switzerland' in c: return 'German'
    return 'English'


def read_all_leads() -> list:
    leads = []
    for csv_path in sorted(LEADS_DIR.rglob('*.csv')):
        if csv_path.name.endswith('.bak'):
            continue
        country = country_from_path(csv_path)
        try:
            with open(csv_path, encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    row['_country'] = country
                    leads.append(row)
        except Exception:
            pass
    return leads


def send_test_email():
    """--test: send ONE sample Claude-written outreach email to your own inbox to verify the pipeline."""
    from email_service import _get_account
    me = _get_account()['user']
    print(f'TEST MODE — sending one sample outreach email to {me}')
    send_with_claude(
        to=me,
        context=(
            'Lead: Taimoor Test Business, UAE. Website: https://example.com. '
            'This is a verification TEST send. Pitch website, AI chatbot, and mobile app services.'
        ),
        project='scrapper-outreach-test',
        skip_if_sent=False,  # always send, even if a previous test is logged
    )
    print(f'Test email sent to {me}. Check your inbox.')


def main():
    if '--test' in sys.argv:
        send_test_email()
        return
    all_leads = read_all_leads()
    leads_with_email = [l for l in all_leads if (l.get('Email') or '').strip() and '@' in (l.get('Email') or '')]
    pending = [l for l in leads_with_email if not already_sent(l['Email'].strip())]

    print(f'Total leads with email: {len(leads_with_email)}')
    print(f'Already sent: {len(leads_with_email) - len(pending)}')
    print(f'Pending: {len(pending)}')

    if not pending:
        if not leads_with_email:
            print('No emails found! Run: python3 extract_emails.py')
        else:
            print('All leads already emailed!')
        return

    to_send = pending[:LIMIT]
    print(f'Sending {len(to_send)} emails today\n')

    sent_count = 0
    for lead in to_send:
        email = lead['Email'].strip()
        name = (lead.get('Name') or 'Unknown')[:40]
        country = lead.get('_country', '')
        website = lead.get('Website', '')
        print(f'  [{sent_count+1}/{len(to_send)}] {name} → {email}')

        lang = language_from_country(country)
        has_site = bool(website and website.startswith('http'))
        context = (
            f'Lead: {name}, {country}. '
            + (f'They ALREADY have a website ({website}) — do NOT offer to build one. Offer a FREE quick review of their current site and pitch growth: SEO, Google Maps ranking, social media. '
               if has_site else
               'They have NO website — offer to build one, and set up their Google Business Profile (Google Maps) for FREE as a first risk-free step. ')
            + f'Write the ENTIRE email in {lang}, simple and friendly, no jargon and no English service names. '
            + 'Build trust: you have 150+ completed projects and references they can check, and it is risk-free — they pay only when happy with the result. '
            + 'Keep it short and end with a simple invitation to reply.'
        )

        try:
            send_with_claude(
                to=email,
                context=context,
                project='scrapper-outreach',
                skip_if_sent=True,
            )
            sent_count += 1
        except Exception as e:
            print(f'    Failed: {e}')

    print(f'\nDone! Sent {sent_count}/{len(to_send)} emails today.')


if __name__ == '__main__':
    main()
