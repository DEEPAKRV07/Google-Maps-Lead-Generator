"""
Regression Test: Single-Threaded vs. Multi-Threaded Website Enrichment (4 Workers)
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import website_crawler

TEST_SITES = [
    {"Business Name": "Store 1", "Website": "https://google.com", "Google Maps Link": "https://maps.google.com/test1"},
    {"Business Name": "Store 2", "Website": "https://microsoft.com", "Google Maps Link": "https://maps.google.com/test2"},
    {"Business Name": "Store 3", "Website": "https://github.com", "Google Maps Link": "https://maps.google.com/test3"},
    {"Business Name": "Store 4", "Website": "https://wikipedia.org", "Google Maps Link": "https://maps.google.com/test4"},
    {"Business Name": "Store 5", "Website": "https://python.org", "Google Maps Link": "https://maps.google.com/test5"},
    {"Business Name": "Store 6", "Website": "https://pypi.org", "Google Maps Link": "https://maps.google.com/test6"},
    {"Business Name": "Store 7", "Website": "https://mozilla.org", "Google Maps Link": "https://maps.google.com/test7"},
    {"Business Name": "Store 8", "Website": "https://stackoverflow.com", "Google Maps Link": "https://maps.google.com/test8"},
]

print("========================================")
print("RUNNING BENCHMARK: SINGLE-THREADED")
print("========================================")
t0 = time.time()
single_results = [website_crawler.crawl_single_website(lead["Website"]) for lead in TEST_SITES]
single_time = round(time.time() - t0, 2)
single_rate = round(len(TEST_SITES) / max(single_time, 0.1) * 60, 1)
print(f"Single-Threaded Duration: {single_time} seconds ({single_rate} sites/min)")

print("\n========================================")
print("RUNNING BENCHMARK: MULTI-THREADED (4 WORKERS)")
print("========================================")
t1 = time.time()
multi_results = website_crawler.enrich_leads_multithreaded(TEST_SITES, max_workers=4)
multi_time = round(time.time() - t1, 2)
multi_rate = round(len(TEST_SITES) / max(multi_time, 0.1) * 60, 1)
speedup = round(single_time / max(multi_time, 0.1), 2)
print(f"Multi-Threaded Duration : {multi_time} seconds ({multi_rate} sites/min)")
print(f"Speedup Factor          : {speedup}x Faster!")
print("========================================")
