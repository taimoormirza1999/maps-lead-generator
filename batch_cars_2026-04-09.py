"""
Batch run for car-related leads — 2026-04-09
Targets: UAE (Dubai, Abu Dhabi), Saudi (Riyadh, Jeddah, Dammam), Greece (Athens, Thessaloniki)
"""
import asyncio
import sys
from datetime import datetime
from google_maps_scraper import scrape_google_maps

QUERIES = [
    # UAE
    ("uae", "car showroom Dubai UAE"),
    ("uae", "car wash Dubai UAE"),
    ("uae", "car service Dubai UAE"),
    ("uae", "car showroom Abu Dhabi UAE"),
    ("uae", "car wash Abu Dhabi UAE"),
    # Saudi Arabia
    ("saudi-arabia", "car showroom Riyadh Saudi Arabia"),
    ("saudi-arabia", "car wash Riyadh Saudi Arabia"),
    ("saudi-arabia", "car showroom Jeddah Saudi Arabia"),
    ("saudi-arabia", "car wash Jeddah Saudi Arabia"),
    ("saudi-arabia", "car service Dammam Saudi Arabia"),
    # Greece
    ("greece", "car wash Athens Greece"),
    ("greece", "car service Athens Greece"),
    ("greece", "car wash Thessaloniki Greece"),
]

async def main():
    summary = []
    today = datetime.now().strftime('%Y-%m-%d')
    for country, query in QUERIES:
        safe = query.lower().replace(' ', '-')
        safe = ''.join(c for c in safe if c.isalnum() or c == '-').strip('-')[:60]
        out_file = f"leads_{country}_{safe}_{today}.csv"
        print(f"\n{'#'*60}\n# {country.upper()}: {query}\n{'#'*60}")
        try:
            businesses, fname = await scrape_google_maps(query, output_file=out_file)
            summary.append((country, query, len(businesses), fname))
        except Exception as e:
            print(f"FAILED: {e}")
            summary.append((country, query, 0, f"ERROR: {e}"))

    # Write summary
    with open(f"batch_summary_{today}.txt", "w") as f:
        f.write(f"Batch run {today}\n")
        f.write("="*60 + "\n")
        total = 0
        by_country = {}
        for country, query, count, fname in summary:
            line = f"[{country}] {query} -> {count} results -> {fname}\n"
            f.write(line)
            print(line.strip())
            total += count
            by_country[country] = by_country.get(country, 0) + count
        f.write("\n" + "="*60 + "\n")
        f.write(f"TOTAL: {total}\n")
        for c, n in by_country.items():
            f.write(f"  {c}: {n}\n")
    print(f"\nTOTAL: {total}")

if __name__ == "__main__":
    asyncio.run(main())
