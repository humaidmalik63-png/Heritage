#!/usr/bin/env python3
"""
Download reference images for all monuments in the catalogue from Wikimedia Commons.

Downloads 5-10 images per monument to data/raw/<site_id>/.
Uses Wikimedia Commons API to search for and download high-quality images.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from PIL import Image
import io

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PATH = ROOT / "data" / "metadata" / "global_monument_catalogue.json"
RAW_DIR = ROOT / "data" / "raw"

# Wikimedia API configuration
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "HeritageRecognition/1.0 (research project; humai@example.com)"
MAX_IMAGES_PER_SITE = 8
MIN_IMAGES_PER_SITE = 5
REQUEST_DELAY = 0.5  # seconds between requests
DOWNLOAD_TIMEOUT = 30

# Minimum image dimensions to accept
MIN_WIDTH = 800
MIN_HEIGHT = 600
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

def load_catalogue():
    """Load the monument catalogue."""
    with open(CATALOGUE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def search_wikimedia(site_name, country, limit=20):
    """Search Wikimedia Commons for images of a monument."""
    # Try multiple search strategies
    search_terms = [
        f"{site_name} {country}",
        site_name,
        f"{site_name} architecture",
        f"{site_name} exterior",
    ]
    
    all_results = []
    seen_pageids = set()
    
    for term in search_terms:
        if len(all_results) >= limit:
            break
            
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": term,
            "srnamespace": 6,  # File namespace
            "srlimit": min(limit, 10),
            "srprop": "size|timestamp",
        }
        
        try:
            url = WIKIMEDIA_API + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            for item in data.get("query", {}).get("search", []):
                pageid = item.get("pageid")
                if pageid and pageid not in seen_pageids:
                    seen_pageids.add(pageid)
                    all_results.append(item)
                    
        except Exception as e:
            print(f"  Search error for '{term}': {e}")
        
        time.sleep(REQUEST_DELAY)
    
    return all_results[:limit]

def get_image_info(pageid):
    """Get direct image URL and metadata for a page ID."""
    params = {
        "action": "query",
        "format": "json",
        "pageids": pageid,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|width|height|extmetadata",
        "iiurlwidth": 2048,
    }
    
    try:
        url = WIKIMEDIA_API + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        pages = data.get("query", {}).get("pages", {})
        page = pages.get(str(pageid))
        if page and "imageinfo" in page:
            info = page["imageinfo"][0]
            return {
                "url": info.get("url"),
                "width": info.get("width"),
                "height": info.get("height"),
                "size": info.get("size"),
                "mime": info.get("mime"),
            }
    except Exception as e:
        print(f"  Image info error for pageid {pageid}: {e}")
    
    return None

def download_image(url, dest_path):
    """Download an image from URL and save it."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
            data = response.read()
        
        if len(data) > MAX_FILE_SIZE:
            return False, f"File too large ({len(data)} bytes)"
        
        # Verify it's a valid image
        img = Image.open(io.BytesIO(data))
        img.verify()
        
        # Re-open for processing
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        
        # Check dimensions
        if img.width < MIN_WIDTH or img.height < MIN_HEIGHT:
            return False, f"Image too small ({img.width}x{img.height})"
        
        # Save as JPEG
        img.save(dest_path, "JPEG", quality=90, optimize=True)
        return True, f"{img.width}x{img.height}, {len(data)} bytes"
        
    except Exception as e:
        return False, str(e)

def download_images_for_site(site, existing_count=0):
    """Download images for a single monument."""
    site_id = site["site_id"]
    name = site["name"]
    country = site["country"]
    
    site_dir = RAW_DIR / site_id
    site_dir.mkdir(parents=True, exist_ok=True)
    
    # Count existing images
    existing = list(site_dir.glob("*.jpg")) + list(site_dir.glob("*.jpeg")) + list(site_dir.glob("*.png"))
    existing_count = len(existing)
    
    needed = max(0, MIN_IMAGES_PER_SITE - existing_count)
    target = min(MAX_IMAGES_PER_SITE - existing_count, MAX_IMAGES_PER_SITE)
    
    if needed <= 0:
        print(f"  {site_id}: Already has {existing_count} images, skipping")
        return existing_count
    
    print(f"\n{site_id} ({name}, {country}): Need {needed}, targeting {target} images")
    
    # Search for images
    results = search_wikimedia(name, country, limit=target * 3)
    print(f"  Found {len(results)} search results")
    
    downloaded = 0
    for i, item in enumerate(results):
        if downloaded >= target:
            break
            
        pageid = item.get("pageid")
        info = get_image_info(pageid)
        if not info or not info.get("url"):
            continue
        
        # Skip non-image mimes
        mime = info.get("mime", "")
        if not mime.startswith("image/"):
            continue
        
        # Determine extension
        ext = ".jpg"
        if "png" in mime:
            ext = ".png"
        elif "webp" in mime:
            ext = ".webp"
        
        filename = f"{site_id}_{existing_count + downloaded + 1:02d}{ext}"
        dest_path = site_dir / filename
        
        if dest_path.exists():
            continue
        
        success, msg = download_image(info["url"], dest_path)
        if success:
            downloaded += 1
            print(f"  ✓ {filename}: {msg}")
        else:
            print(f"  ✗ {filename}: {msg}")
        
        time.sleep(REQUEST_DELAY)
    
    total = existing_count + downloaded
    print(f"  Total for {site_id}: {total} images ({downloaded} new)")
    return total

def main():
    print("=" * 60)
    print("Wikimedia Commons Image Downloader")
    print("=" * 60)
    
    catalogue = load_catalogue()
    print(f"Loaded {len(catalogue)} monuments from catalogue")
    
    # Track results
    results = {}
    total_downloaded = 0
    
    for i, site in enumerate(catalogue):
        print(f"\n[{i+1}/{len(catalogue)}] Processing {site['site_id']}...")
        try:
            count = download_images_for_site(site)
            results[site["site_id"]] = count
            total_downloaded += count
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            break
        except Exception as e:
            print(f"  ERROR: {e}")
            results[site["site_id"]] = 0
    
    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    for site_id, count in sorted(results.items()):
        status = "✓" if count >= MIN_IMAGES_PER_SITE else "⚠"
        print(f"  {status} {site_id}: {count} images")
    print(f"\nTotal images across all sites: {total_downloaded}")
    print(f"Average per site: {total_downloaded / len(catalogue):.1f}")

if __name__ == "__main__":
    sys.exit(main())