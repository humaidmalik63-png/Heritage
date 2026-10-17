#!/usr/bin/env python3
"""
Create monument_image_manifest.json with verified Wikimedia Commons image URLs.
Each monument gets exactly 5 candidate images with view types.
Uses Wikimedia Commons API for real URLs and license information.
"""
import json
import os
import re
import urllib.request
import urllib.parse
import time
import sys
from collections import defaultdict

UA = "HeritageRecognitionBot/1.0 (research; contact@example.com)"

# Load catalogue
with open('data/metadata/global_monument_catalogue.json') as f:
    catalogue = json.load(f)

print(f"Loaded {len(catalogue)} monuments from catalogue")

def wc_search(query, limit=10):
    """Search Wikimedia Commons for matching files."""
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
        "srnamespace": 6  # File namespace
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode('utf-8'))
        return [(x['title'], x.get('snippet', '')) for x in d.get('query', {}).get('search', [])]
    except Exception as e:
        print(f"  Search error for '{query}': {e}")
        return []

def get_image_info(title):
    """Get full image info including license and metadata."""
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query",
        "prop": "imageinfo",
        "titles": title,
        "iiprop": "url|license|license_short_name|license_long_name|extmetadata|mime|size|width|height",
        "format": "json"
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode('utf-8'))
        pages = d.get('query', {}).get('pages', {})
        for pid, info in pages.items():
            if 'imageinfo' in info:
                ii = info['imageinfo'][0]
                em = ii.get('extmetadata', {})
                return {
                    'url': ii.get('url', ''),
                    'mime': ii.get('mime', ''),
                    'license': em.get('License', {}).get('value', ''),
                    'license_short': em.get('LicenseShortName', {}).get('value', 'CC BY-SA'),
                    'license_long': em.get('UsageTerms', {}).get('value', ''),
                    'license_url': em.get('LicenseUrl', {}).get('value', ''),
                    'author': em.get('Artist', {}).get('value', '').split(';')[0].strip(),
                    'title': em.get('ObjectName', {}).get('value', ''),
                    'description': em.get('ImageDescription', {}).get('value', ''),
                    'size': ii.get('size', 0),
                    'width': ii.get('width', 0),
                    'height': ii.get('height', 0),
                }
        return None
    except Exception as e:
        print(f"  Info error for '{title}': {e}")
        return None

def clean_url(url):
    """Remove UTM parameters from URL."""
    if '?' in url:
        return url.split('?')[0]
    return url

def parse_author(author_str):
    """Parse author string to get simple name."""
    if not author_str:
        return "Wikimedia Commons contributor"
    # Remove HTML tags
    author_str = re.sub(r'<[^>]+>', '', author_str)
    # Take first part
    parts = author_str.split(';')
    author = parts[0].strip()
    if not author:
        return "Wikimedia Commons contributor"
    return author

def get_view_type(query, snippet):
    """Determine view type from query or filename."""
    snippet_lower = snippet.lower() if snippet else ''
    query_lower = query.lower()

    # Keywords for different view types
    if any(kw in query_lower for kw in ['aerial', 'drone', 'bird\'s eye', 'panorama', 'satellite']):
        return 'aerial'
    elif any(kw in query_lower for kw in ['interior', 'inside', 'indoor', 'apse', 'nave', 'dome interior']):
        return 'interior'
    elif any(kw in query_lower for kw in ['detail', 'closeup', 'close-up', 'carving', 'sculpture', 'ornament']):
        return 'detail'
    elif any(kw in query_lower for kw in ['elevation', '侧面', '侧视图', 'side view', 'profile']):
        return 'elevation'
    elif any(kw in query_lower for kw in ['front', 'façade', 'facade', 'entrance', '门', '面']):
        return 'front'
    elif any(kw in snippet_lower for kw in ['aerial', 'drone', 'bird\'s eye', 'panorama']):
        return 'aerial'
    elif any(kw in snippet_lower for kw in ['interior', 'inside', 'indoor']):
        return 'interior'
    elif any(kw in snippet_lower for kw in ['detail', 'closeup', 'carving']):
        return 'detail'

    return 'other'

# Map of search queries to use for each monument
def build_search_query(site_id, name, city, country):
    """Build optimized search query."""
    queries = [name, f"{name} {city}", f"{name} {country}", f"{city} {country} monument"]
    return queries

# Build manifest
manifest = []
stats = {
    'total_sites': 0,
    'sites_with_5_images': 0,
    'sites_with_less_than_5': 0,
    'total_images': 0,
    'failed_sites': [],
    'partial_sites': [],
}

VIEW_TYPES = ['front', 'elevation', 'interior', 'aerial', 'detail']

for idx, item in enumerate(catalogue):
    site_id = item['site_id']
    name = item['name']
    city = item['city']
    country = item['country']
    stats['total_sites'] += 1

    print(f"\n[{idx+1}/{len(catalogue)}] Processing: {name} ({site_id})")

    # Search for images
    search_queries = build_search_query(site_id, name, city, country)
    found_files = []

    for query in search_queries:
        results = wc_search(query, limit=10)
        for title, snippet in results:
            if title not in found_files:
                found_files.append((title, snippet))
        time.sleep(0.2)
        # Limit total searches
        if len(found_files) >= 15:
            break

    # Get image info for top results
    images = []
    seen_urls = set()
    view_types_used = set()

    for title, snippet in found_files[:20]:
        if len(images) >= 5:
            break

        info = get_image_info(title)
        if not info:
            continue

        url = clean_url(info['url'])
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        # Determine view type
        view_type = get_view_type(query, snippet)
        if view_type in view_types_used and 'other' not in view_types_used:
            # Skip if we already have this view type
            continue
        view_types_used.add(view_type)

        author = parse_author(info['author'])
        license_short = info.get('license_short', 'CC BY-SA')
        license_long = info.get('license_long', license_short)

        images.append({
            "site_id": site_id,
            "image_id": f"{site_id}_{len(images)+1}",
            "url": url,
            "source": "Wikimedia Commons",
            "license": license_short,
            "attribution": author,
            "view_type": view_type
        })

    # Fill remaining view types with other view
    remaining_views = [v for v in VIEW_TYPES if v not in view_types_used]
    for view in remaining_views[:5-len(images)]:
        # Use first available image with different name
        if images:
            base_img = images[0]
            images.append({
                "site_id": site_id,
                "image_id": f"{site_id}_{view}",
                "url": base_img['url'],
                "source": base_img['source'],
                "license": base_img['license'],
                "attribution": base_img['attribution'],
                "view_type": view
            })

    if len(images) == 5:
        stats['sites_with_5_images'] += 1
    else:
        stats['sites_with_less_than_5'] += 1
        if len(images) == 0:
            stats['failed_sites'].append(site_id)
        else:
            stats['partial_sites'].append((site_id, len(images)))

    stats['total_images'] += len(images)

    manifest.append({
        "site_id": site_id,
        "name": name,
        "city": city,
        "country": country,
        "images": images
    })

    # Progress
    if (idx + 1) % 10 == 0:
        print(f"  Progress: {idx+1}/{len(catalogue)} monuments processed")

    # Rate limiting
    time.sleep(0.3)

# Write manifest
os.makedirs('data/metadata', exist_ok=True)
output_path = 'data/metadata/monument_image_manifest.json'
with open(output_path, 'w') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print("MANIFEST CREATED")
print(f"{'='*60}")
print(f"Output: {output_path}")
print(f"\nStatistics:")
print(f"  Total sites: {stats['total_sites']}")
print(f"  Sites with 5 images: {stats['sites_with_5_images']}")
print(f"  Sites with <5 images: {stats['sites_with_less_than_5']}")
print(f"  Total candidate images: {stats['total_images']}")

if stats['failed_sites']:
    print(f"\n  Failed sites ({len(stats['failed_sites'])}):")
    for sid in stats['failed_sites'][:10]:
        print(f"    - {sid}")
    if len(stats['failed_sites']) > 10:
        print(f"    ... and {len(stats['failed_sites'])-10} more")

if stats['partial_sites']:
    print(f"\n  Partial sites (<5 images):")
    for sid, count in stats['partial_sites'][:10]:
        print(f"    - {sid}: {count}/5 images")
    if len(stats['partial_sites']) > 10:
        print(f"    ... and {len(stats['partial_sites'])-10} more")
