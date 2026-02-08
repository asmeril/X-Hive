#!/usr/bin/env python
"""Test cookie loader for all sites"""

from intel.cookie_loader import get_cookie_loader

cl = get_cookie_loader()

sites = ['reddit', 'twitter', 'medium', 'perplexity', 'substack', 'linkedin', 'github', 'producthunt', 'youtube', 'arxiv', 'google_trends', 'discord']

print("=" * 60)
print("CEREZ YUKLEME RAPORU")
print("=" * 60)

total_cookies = 0
for site in sites:
    cookies = cl.load_cookies(site)
    status = "[OK]" if cookies else "[EMPTY]"
    total_cookies += len(cookies)
    print(f"{site:20} {status:8} ({len(cookies):2} cerez)")

print("=" * 60)
print(f"TOPLAM: {total_cookies} cerez")
print("=" * 60)
