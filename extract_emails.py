"""
Enrich lead CSVs with emails extracted from their websites.
Visits homepage + /contact page, looks for mailto links or email addresses.
Usage: python3 extract_emails.py [--dir leads/uae]
"""
import asyncio
import csv
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LEADS_DIR = SCRIPT_DIR / 'leads'

EMAIL_RE = re.compile(r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b')
JUNK_DOMAINS = {
    'example.com', 'test.com', 'sentry.io', 'wix.com', 'squarespace.com',
    'schema.org', 'w3.org', 'apple.com', 'google.com', 'facebook.com',
    'whatsapp.com', 'instagram.com', 'twitter.com', 'youtube.com',
}
JUNK_PATTERNS = [
    'noreply', 'no-reply', 'example', 'yourname', 'yoursite',
    'sentry', 'jquery', '@2x', 'domain.com', 'email.com',
]


def is_junk(email: str) -> bool:
    domain = email.split('@')[-1].lower()
    if domain in JUNK_DOMAINS:
        return True
    return any(p in email.lower() for p in JUNK_PATTERNS)


async def extract_email(context, url: str) -> str:
    page = None
    try:
        page = await context.new_page()
        await page.goto(url, wait_until='domcontentloaded', timeout=9000)

        # mailto links are the most reliable
        mailtos = await page.locator('a[href^="mailto:"]').all()
        for m in mailtos:
            href = await m.get_attribute('href') or ''
            email = href.replace('mailto:', '').split('?')[0].strip()
            if '@' in email and not is_junk(email):
                return email.lower()

        # Scan visible text
        try:
            text = await page.inner_text('body')
            candidates = EMAIL_RE.findall(text)
            valid = [e.lower() for e in candidates if not is_junk(e)]
            if valid:
                return valid[0]
        except Exception:
            pass

        # Try /contact page
        contact = url.rstrip('/') + '/contact'
        try:
            await page.goto(contact, wait_until='domcontentloaded', timeout=6000)
            mailtos = await page.locator('a[href^="mailto:"]').all()
            for m in mailtos:
                href = await m.get_attribute('href') or ''
                email = href.replace('mailto:', '').split('?')[0].strip()
                if '@' in email and not is_junk(email):
                    return email.lower()
            text = await page.inner_text('body')
            candidates = EMAIL_RE.findall(text)
            valid = [e.lower() for e in candidates if not is_junk(e)]
            if valid:
                return valid[0]
        except Exception:
            pass

        return ''
    except Exception:
        return ''
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass


async def enrich_csv(csv_path: Path) -> int:
    with open(csv_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if 'Email' not in fieldnames:
        fieldnames.append('Email')

    to_enrich = [
        r for r in rows
        if (r.get('Website') or '').startswith('http') and not (r.get('Email') or '').strip()
    ]

    if not to_enrich:
        return 0

    print(f'  {csv_path.name}: {len(to_enrich)} leads to enrich', flush=True)

    from playwright.async_api import async_playwright
    found = 0
    done = 0
    total = len(to_enrich)
    CONCURRENCY = 10  # crawl this many sites at once (was sequential = 1)
    sem = asyncio.Semaphore(CONCURRENCY)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        )

        async def worker(row):
            nonlocal found, done
            name = (row.get('Name') or '?')[:40]
            async with sem:
                email = await extract_email(ctx, row['Website'])
            done += 1
            if email:
                row['Email'] = email
                found += 1
                print(f'    [{done}/{total}] {name} ✓ {email}', flush=True)
            else:
                print(f'    [{done}/{total}] {name} no email', flush=True)

        await asyncio.gather(*(worker(r) for r in to_enrich))
        await browser.close()

    # Write back in place
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    return found


async def enrich_csv_limited(csv_path: Path, max_per_run: int = 30) -> int:
    with open(csv_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if 'Email' not in fieldnames:
        fieldnames.append('Email')

    to_enrich = [
        r for r in rows
        if (r.get('Website') or '').startswith('http') and not (r.get('Email') or '').strip()
    ][:max_per_run]

    if not to_enrich:
        return 0

    print(f'  {csv_path.name}: {len(to_enrich)} leads to enrich', flush=True)

    from playwright.async_api import async_playwright
    found = 0
    done = 0
    total = len(to_enrich)
    CONCURRENCY = 10
    sem = asyncio.Semaphore(CONCURRENCY)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        )

        async def worker(row):
            nonlocal found, done
            name = (row.get('Name') or '?')[:40]
            async with sem:
                email = await extract_email(ctx, row['Website'])
            done += 1
            if email:
                row['Email'] = email
                found += 1
                print(f'    [{done}/{total}] {name} ✓ {email}', flush=True)
            else:
                print(f'    [{done}/{total}] {name} no email', flush=True)

        await asyncio.gather(*(worker(r) for r in to_enrich))
        await browser.close()

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    return found


async def main():
    target_dir = LEADS_DIR
    max_per_run = 30
    if '--dir' in sys.argv:
        idx = sys.argv.index('--dir')
        target_dir = Path(sys.argv[idx + 1])
    if '--max' in sys.argv:
        idx = sys.argv.index('--max')
        max_per_run = int(sys.argv[idx + 1])

    all_csvs = sorted(target_dir.rglob('*.csv'))
    all_csvs = [p for p in all_csvs if not p.name.endswith('.bak')]

    if not all_csvs:
        print(f'No CSVs found in {target_dir}')
        return

    print(f'Found {len(all_csvs)} CSV files\n')

    total = 0
    for csv_path in all_csvs:
        found = await enrich_csv_limited(csv_path, max_per_run)
        total += found

    print(f'\nDone! Found {total} new emails total.')


if __name__ == '__main__':
    asyncio.run(main())
