import json
from collections import Counter

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Validation
site_ids = [e["site_id"] for e in data]
unique_ids = set(site_ids)
duplicates = [sid for sid in site_ids if site_ids.count(sid) > 1]
countries = sorted(set(e["country"] for e in data))
regions = sorted(set(e["region"] for e in data))

# Country breakdown
country_counts = Counter(e["country"] for e in data)

print("=" * 60)
print("CATALOGUE VALIDATION")
print("-" * 60)
print("Total sites: " + str(len(data)))
print("Unique site_ids: " + str(len(unique_ids)))
if duplicates:
    print("Duplicate site_ids: " + str(duplicates))
else:
    print("Duplicate site_ids: None")
print("Countries: " + str(len(countries)))
print("Continents/regions: " + str(len(regions)))
print()
print("COUNTRY BREAKDOWN:")
for country, count in sorted(country_counts.items(), key=lambda x: -x[1]):
    print("  " + country + ": " + str(count))
print()
print("REGIONS:")
for region in regions:
    print("  " + region)
print()
print("ALL SITE_IDS:")
for sid in site_ids:
    print("  " + sid)
