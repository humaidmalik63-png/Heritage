import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── UZBEKISTAN (4 entries) ───────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "samarkand_registan",
    "name": "Registan Square, Samarkand",
    "city": "Samarkand",
    "country": "Uzbekistan",
    "region": "Central Asia",
    "type": "Madrasa Complex",
    "period": "1417-1660 CE",
    "description": "Iconic square flanked by three magnificent Islamic madrasas, jewel of the Silk Road.",
    "historical_significance": "UNESCO World Heritage Site (2001, as part of Samarkand); heart of Timurid Renaissance; described by Marco Polo.",
    "architectural_features": "Ulugh Beg Madrasa with blue tilework, Tilla-Kori Madrasa with gold facade, Sher-Dor Madrasa with tiger motifs, massive pishtaq arches, muqarnas decoration, central pool.",
    "heritage_status": "UNESCO World Heritage Site (Samarkand - Crossroads of Cultures)",
    "sources": [{"title": "UNESCO World Heritage List - Samarkand", "url": "https://whc.unesco.org/en/list/603"}]
  },
  {
    "site_id": "shah_i_zinda",
    "name": "Shah-i-Zinda Necropolis",
    "city": "Samarkand",
    "country": "Uzbekistan",
    "region": "Central Asia",
    "type": "Necropolis",
    "period": "11th-15th century CE",
    "description": "Sacred necropolis with a row of ornate mausoleums adorned with brilliant turquoise tilework.",
    "historical_significance": "UNESCO World Heritage Site (2001); pilgrimage site dedicated to Kusam ibn Abbas; finest example of Timurid funerary architecture.",
    "architectural_features": "Ornate mausoleums with carved stone screens, turquoise and cobalt tile mosaics, arched iwans, geometric patterns, portal decorations, reflecting pools.",
    "heritage_status": "UNESCO World Heritage Site (Samarkand - Crossroads of Cultures)",
    "sources": [{"title": "UNESCO World Heritage List - Samarkand", "url": "https://whc.unesco.org/en/list/603"}]
  },
  {
    "site_id": "bukhara_minarets",
    "name": "Historic Centre of Bukhara",
    "city": "Bukhara",
    "country": "Uzbekistan",
    "region": "Central Asia",
    "type": "Historic City",
    "period": "8th-19th century CE",
    "description": "Well-preserved medieval Central Asian city with over 140 architectural monuments spanning 1,000+ years.",
    "historical_significance": "UNESCO World Heritage Site (1993); major center of Islamic culture and trade on the Silk Road; 'the museum of Central Asia'.",
    "architectural_features": "Poi-Kalyan complex with Kalyan Minaret (46.5m), Kalyan Mosque, Mir-i-Arab Madrasa, trading domes (coups), Ark Fortress, Ismail Samani Mausoleum (9th century).",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Bukhara", "url": "https://whc.unesco.org/en/list/602"}]
  },
  {
    "site_id": "khiva_itchan",
    "name": "Itchan Kala, Khiva",
    "city": "Khiva",
    "country": "Uzbekistan",
    "region": "Central Asia",
    "type": "Fortified Inner City",
    "period": "8th-19th century CE",
    "description": "Walled inner city of Khiva, a remarkably preserved example of Central Asian Islamic architecture.",
    "historical_significance": "UNESCO World Heritage Site (1990); one of the best-preserved medieval cities on the Silk Road.",
    "architectural_features": "4km of mud-brick walls, Islam Khoja Minaret (slenderest in Uzbekistan), Khan Mosque with painted ceiling, Muhammad Amin Khan Madrasa, ornate wooden columns.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Itchan Kala", "url": "https://whc.unesco.org/en/list/473"}]
  },
])

# ── SOUTH KOREA (4 entries) ──────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "changdeokgung_palace",
    "name": "Changdeokgung Palace",
    "city": "Seoul",
    "country": "South Korea",
    "region": "East Asia",
    "type": "Palace",
    "period": "1405 CE",
    "description": "Joseon dynasty royal palace harmoniously integrated with the natural landscape of Seoul's secret garden.",
    "historical_significance": "UNESCO World Heritage Site (1997); finest example of Korean palace architecture; secret garden (Huwon) is a masterpiece of landscape design.",
    "architectural_features": "Injeongjeon throne hall with dragon pillar, Donggung pavilion over pond, Biwon (Secret Garden) with ponds and pavilions, traditional Korean roof curves, ondol heating systems.",
    "heritage_status": "UNESCO World Heritage Site (Royal Palaces of Joseon)",
    "sources": [{"title": "UNESCO World Heritage List - Seoul Palaces", "url": "https://whc.unesco.org/en/list/851"}]
  },
  {
    "site_id": "bucheon_temple",
    "name": "Bulguksa Temple",
    "city": "Gyeongju",
    "country": "South Korea",
    "region": "East Asia",
    "type": "Buddhist Temple",
    "period": "751 CE",
    "description": "Historic Buddhist temple representing the best of Buddhist art of the early Zen period.",
    "historical_significance": "UNESCO World Heritage Site (1995, with Seokguram); most important Buddhist temple in Korea; symbol of Korean Buddhist art.",
    "architectural_features": "Dabotap multi-tiered pagoda with intricate stonework, Tongd Mokchang staircase, Geungnakjeon main hall, bronze Buddha statues, stone lanterns, temple grounds on mountainside.",
    "heritage_status": "UNESCO World Heritage Site (Historic Monuments of Gyeongju)",
    "sources": [{"title": "UNESCO World Heritage List - Gyeongju", "url": "https://whc.unesco.org/en/list/707"}]
  },
  {
    "site_id": "seokguram_cave",
    "name": "Seokguram Grotto",
    "city": "Gyeongju",
    "country": "South Korea",
    "region": "East Asia",
    "type": "Buddhist Cave Temple",
    "period": "774 CE",
    "description": "Artificial granite cave temple housing a magnificent seated Buddha statue, considered a masterpiece of Buddhist art.",
    "historical_significance": "UNESCO World Heritage Site (1995); 'the most perfect Buddhist sculpture in the world'; architectural and sculptural masterpiece.",
    "architectural_features": "Granite dome ceiling with lotus motif, 3.3m seated Buddha with ushnisha, 29 bodhisattvas and guardians in niches, corbel-vaulted construction, atmospheric lighting.",
    "heritage_status": "UNESCO World Heritage Site (Historic Monuments of Gyeongju)",
    "sources": [{"title": "UNESCO World Heritage List - Gyeongju", "url": "https://whc.unesco.org/en/list/707"}]
  },
  {
    "site_id": "jongmyo_shrine",
    "name": "Jongmyo Shrine",
    "city": "Seoul",
    "country": "South Korea",
    "region": "East Asia",
    "type": "Confucian Shrine",
    "period": "1394 CE",
    "description": "Royal ancestral shrine of the Joseon dynasty, site of Jongmyo Jeryeak ancestral ritual since 1394.",
    "historical_significance": "UNESCO World Heritage Site (1995); oldest royal ancestral shrine in Korea; ritual performed continuously for over 600 years.",
    "architectural_features": "Jongmyo Shrine hall with 19 ancestral tablets, hyeonpu stone elephants, vermilion lacquered pillars, traditional music performance pavilion, ceremonial grounds.",
    "heritage_status": "UNESCO World Heritage Site (Royal Ancestral Rituals and Songs)",
    "sources": [{"title": "UNESCO World Heritage List - Jongmyo", "url": "https://whc.unesco.org/en/list/850"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Uzbekistan + South Korea: {len(catalogue)}")