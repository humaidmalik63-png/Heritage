import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── TURKEY (6 entries) ───────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "hagia_sophia",
    "name": "Hagia Sophia",
    "city": "Istanbul",
    "country": "Turkey",
    "region": "Western Asia",
    "type": "Mosque/Church",
    "period": "532-537 CE",
    "description": "Former Eastern Orthodox Catholic patriarchal basilica, later an imperial mosque, now a mosque, showcasing Byzantine and Ottoman architecture.",
    "historical_significance": "UNESCO World Heritage Site (2014); masterpiece of Byzantine architecture; symbol of Istanbul for 1,500 years.",
    "architectural_features": "Massive central dome 31m diameter rising 55m, pendentive support system, marble screens with Islamic calligraphy, minarets added by Ottomans, golden mosaics.",
    "heritage_status": "UNESCO World Heritage Site (Historic Areas of Istanbul)",
    "sources": [{"title": "UNESCO World Heritage List - Istanbul", "url": "https://whc.unesco.org/en/list/356"}]
  },
  {
    "site_id": "sultan Ahmet_mosque",
    "name": "Blue Mosque (Sultan Ahmed Mosque)",
    "city": "Istanbul",
    "country": "Turkey",
    "region": "Western Asia",
    "type": "Mosque",
    "period": "1609-1616 CE",
    "description": "Ottoman imperial mosque known for its blue Iznik tile interior and six minarets, directly facing the Hagia Sophia.",
    "historical_significance": "Icon of Istanbul's skyline; considered the last great mosque of the classical Ottoman period.",
    "architectural_features": "Six minarets, central dome flanked by four semi-domes, blue Iznik tile work in interior, massive courtyard with ablution fountain, marble pillars.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Turkish Ministry of Culture", "url": "https://www.kulturturizm.gov.tr"}]
  },
  {
    "site_id": "gallipoli",
    "name": "Gallipoli Peninsula Battlefields",
    "city": "Gallipoli",
    "country": "Turkey",
    "region": "Western Asia",
    "type": "Military Memorial",
    "period": "1915-1916 CE",
    "description": "Battlefield complex commemorating the WWI Gallipoli Campaign, significant to both Turkey and Australia/New Zealand.",
    "historical_significance": "Founding moment of modern Turkey; ANZAC Day originates from this campaign; strategic straits control.",
    "architectural_features": "ANZAC Cove landing site, Lone Pine memorial, Chunuk Bair cemetery, Turkish martyrs memorial with crescent finial, naval guns on headlands.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Turkish War Museums", "url": "https://www.csk.gov.tr"}]
  },
  {
    "site_id": "pamukkale",
    "name": "Pamukkale Hot Springs",
    "city": " Denizli",
    "country": "Turkey",
    "region": "Western Asia",
    "type": "Natural/Historical Site",
    "period": "2nd century BCE-19th century CE",
    "description": "White travertine terraces formed by thermal waters, site of ancient Hierapolis spa city.",
    "historical_significance": "UNESCO World Heritage Site (1988); natural wonder combined with ancient Greco-Roman spa complex.",
    "architectural_features": "Cotton-colored calcium carbonate terraces, Ancient theatre with marble seating, Gate of Apollo, necropolis extending 1km, thermal pools.",
    "heritage_status": "UNESCO World Heritage Site (Hierapolis-Pamukkale)",
    "sources": [{"title": "UNESCO World Heritage List - Hierapolis-Pamukkale", "url": "https://whc.unesco.org/en/list/859"}]
  },
  {
    "site_id": "hagia_irini",
    "name": "Hagia Eirene (Church of Peace)",
    "city": "Istanbul",
    "country": "Turkey",
    "region": "Western Asia",
    "type": "Church",
    "period": "5th century CE",
    "description": "Byzantine church in the Topkapi Palace grounds, one of the few Constantinople churches not converted to a mosque.",
    "historical_significance": "Oldest church in Istanbul still standing; used as imperial treasury after Ottoman conquest.",
    "architectural_features": "Basilica plan with three naves, massive dome on pendentives, brick construction with stone bands, original marble floor, apse with mosaic fragments.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Topkapi Palace Museums", "url": "https://www.topkapisarayi.gov.tr"}]
  },
  {
    "site_id": "troia_hisarlik",
    "name": "Troy (Hisarlik)",
    "city": "Canakkale",
    "country": "Turkey",
    "region": "Western Asia",
    "type": "Archaeological Site",
    "period": "3000-800 BCE",
    "description": "Legendary city of the Trojan War, excavated by Heinrich Schliemann, one of the most important archaeological sites in the world.",
    "historical_significance": "UNESCO World Heritage Site (1998); subject of Homer's Iliad; evidence of 9 layers of civilization.",
    "architectural_features": "Circular tower (Scheil Tower), defensive walls with gate openings, multi-layered ruins showing successive cities, wooden reconstruction of Trojan Horse gate.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Troy", "url": "https://whc.unesco.org/en/list/881"}]
  },
])

# ── JAPAN (6 entries) ────────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "fushimi_inari",
    "name": "Fushimi Inari Taisha",
    "city": "Kyoto",
    "country": "Japan",
    "region": "East Asia",
    "type": "Shinto Shrine",
    "period": "711 CE (current structures 14th-20th century)",
    "description": "Shinto shrine dedicated to Inari, the god of rice and prosperity, famous for its thousands of vermilion torii gates.",
    "historical_significance": "Head shrine of all 30,000 Inari shrines in Japan; one of Kyoto's most iconic landmarks.",
    "architectural_features": "Senbon Torii (thousands of vermilion gates), fox statues (Inari's messengers), main hall with cypress bark roof, sacred mountain trails, sub-shrines.",
    "heritage_status": "National Important Cultural Property",
    "sources": [{"title": "Fushimi Inari Taisha Official", "url": "https://inari.jp/en/"}]
  },
  {
    "site_id": "kyoto_kinkakuji",
    "name": "Kinkaku-ji (Golden Pavilion)",
    "city": "Kyoto",
    "country": "Japan",
    "region": "East Asia",
    "type": "Temple",
    "period": "1397 CE (rebuilt 1955)",
    "description": "Zen Buddhist temple covered in gold leaf, reflecting perfectly in the mirror pond below.",
    "historical_significance": "UNESCO World Heritage Site (1994); original pavilion built as retirement villa for shogun Ashikaga Yoshimitsu.",
    "architectural_features": "Three-storey pagoda-style building, gold-leaf exterior on upper two floors, pine tree on roof pinnacle, Kyo-chi-chin pond reflection, Rokuson-in garden.",
    "heritage_status": "UNESCO World Heritage Site (Historic Monuments of Ancient Kyoto)",
    "sources": [{"title": "UNESCO World Heritage List - Kyoto", "url": "https://whc.unesco.org/en/list/688"}]
  },
  {
    "site_id": "nara_todaiji",
    "name": "Todai-ji Temple",
    "city": "Nara",
    "country": "Japan",
    "region": "East Asia",
    "type": "Buddhist Temple",
    "period": "752 CE",
    "description": "Buddhist temple housing the world's largest bronze statue of Buddha (Daibutsu) in a massive wooden hall.",
    "historical_significance": "UNESCO World Heritage Site (1998); head temple of Japanese Kegon school of Buddhism; symbol of Nara period cultural zenith.",
    "architectural_features": "Great Buddha Hall (Daibutsuden) 57m x 50m, 15m bronze Buddha statue with lotus throne, Nandaimon gate with guardian kings, giant bronze lily cup.",
    "heritage_status": "UNESCO World Heritage Site (Historic Monuments of Ancient Nara)",
    "sources": [{"title": "UNESCO World Heritage List - Nara", "url": "https://whc.unesco.org/en/list/687"}]
  },
  {
    "site_id": "hiroshima_park",
    "name": "Hiroshima Peace Memorial (Genbaku Dome)",
    "city": "Hiroshima",
    "country": "Japan",
    "region": "East Asia",
    "type": "Memorial",
    "period": "1915 CE (bombing August 6, 1945)",
    "description": "Ruined industrial support building left intact by the atomic bomb, preserved as a symbol of nuclear devastation and peace.",
    "historical_significance": "UNESCO World Heritage Site (1996); most powerful symbol of nuclear destruction and the peace movement.",
    "architectural_features": "Dome-shaped skeletal frame rising from ruined concrete base, ribs visible against sky, preserved blast damage, surrounding park with atomic bomb museum.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Hiroshima", "url": "https://whc.unesco.org/en/list/775"}]
  },
  {
    "site_id": "nikko_toshogu",
    "name": "Nikko Toshogu Shrine",
    "city": "Nikko",
    "country": "Japan",
    "region": "East Asia",
    "type": "Shinto Shrine",
    "period": "1617 CE",
    "description": "Opulent Shinto shrine dedicated to Tokugawa Ieyasu, founder of the Tokugawa shogunate, the most elaborate shrine in Japan.",
    "historical_significance": "UNESCO World Heritage Site (1999); peak of Edo-period decorative art; most visited shrine in Japan.",
    "architectural_features": "Yomeimon Gate with 200 woodcarvings, seven-storied pagoda, ornate tomb with golden decorations, 'see no evil, hear no evil, speak no evil' monkeys carved in stone.",
    "heritage_status": "UNESCO World Heritage Site (Shrines and Temples of Nikko)",
    "sources": [{"title": "UNESCO World Heritage List - Nikko", "url": "https://whc.unesco.org/en/list/678"}]
  },
  {
    "site_id": "otsuki_koami",
    "name": "Itsukushima Shrine (Miyajima)",
    "city": "Hatsukaichi",
    "country": "Japan",
    "region": "East Asia",
    "type": "Shinto Shrine",
    "period": "593 CE origins; current structures 1168 CE",
    "description": "Shinto shrine famous for its 'floating' torii gate in the Seto Inland Sea, appearing to float at high tide.",
    "historical_significance": "UNESCO World Heritage Site (1996); major pilgrimage site since ancient times; symbol of Japanese aesthetic harmony with nature.",
    "architectural_features": "Vermillion torii gate standing in sea, Shinden-zukuri style shrine with connecting corridors, stage-like main hall over water, tidal variations affecting appearance.",
    "heritage_status": "UNESCO World Heritage Site (Itsukushima Shrine)",
    "sources": [{"title": "UNESCO World Heritage List - Itsukushima", "url": "https://whc.unesco.org/en/list/773"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Turkey + Japan: {len(catalogue)}")