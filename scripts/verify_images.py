import urllib.request, urllib.parse, hashlib, json, os, re

# Search for actual file pages on Wikimedia Commons
search_queries = [
    ('abu_simbel', 'Abu Simbel'),
    ('aksum_stelae', 'Aksum stelae')
]

for site_id, query in search_queries:
    print(f'=== {site_id} ===')
    print(f'Search query: {query}')
    
    # Try the MediaWiki API with proper encoding
    encoded_query = urllib.parse.quote(query)
    api_url = f'https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json&formatversion=2'
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        search_results = data.get('query', {}).get('search', [])
        print(f'Search results: {len(search_results)}')
        
        for result in search_results[:5]:
            title = result.get('title', '')
            print(f'  Result: {title}')
            
            # Try to get image info for this title
            # Replace spaces with underscores for file title
            file_title = title.replace(' ', '_')
            
            # Get file info
            file_api = f'https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url&titles={urllib.parse.quote(file_title)}&format=json'
            req2 = urllib.request.Request(file_api, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2, timeout=15) as response2:
                data2 = json.loads(response2.read().decode('utf-8'))
            
            pages = data2.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if 'missing' not in page_data:
                    image_info = page_data.get('imageinfo', [])
                    if image_info:
                        url = image_info[0].get('url', '')
                        if url:
                                                    print(f'  Direct URL: {url[:100]}...')
                                                else:
                                                    print(f'  Direct URL: None...')
                    else:
                        print(f'  No image info available')
                else:
                    print(f'  Page is missing (might be a redirect)')
                    
    except Exception as e:
        print(f'Error: {e}')
    print()