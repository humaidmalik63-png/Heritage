import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── SRI LANKA (3 entries) ────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "anuradhapura_ruins",
    "name": "Ancient City of Anuradhapura",
    "city": "Anuradhapura",
    "country": "Sri Lanka",
    "region": "South Asia",
    "type": "Archaeological Site",
    "period": "4th century BCE-11th century CE",
    "description": "Ancient capital of Sri Lanka, one of the longest continuously inhabited cities in the world, sacred to Buddhists.",
    "historical_significance": "UNESCO World Heritage Site (1982); birthplace of Sri Lankan civilization; over 2,500 years of Buddhist history.",
    "architectural_features": "Sri Maha Bodhi tree (sacred fig), Ruwanwelisaya stupa 55m high, Jetavanarama stupa once tallest in the world, Abhayagiri monastery complex, sacred precincts with monastic cells.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Anuradhapura", "url": "https://whc.unesco.org/en/list/183"}]
  },
  {
    "site_id": "polonnaruwa_ruins",
    "name": "Ancient City of Polonnaruwa",
    "city": "Polonnaruwa",
    "country": "Sri Lanka",
    "region": "South Asia",
    "type": "Archaeological Site",
    "period": "11th-13th century CE",
    "description": "Medieval capital with well-preserved ruins of palaces, temples, and statues from the Sinhalese kingdom.",
    "historical_significance": "UNESCO World Heritage Site (1982); finest example of medieval Sri Lankan urban planning and Buddhist art.",
    "architectural_features": "Gal Vihara rock-cut Buddha statues (13m seated, 7m standing), Tooth Relic Temple, Lotus Pond, Alahana Parivena monastery, bronze Buddha statues, ornate stupas.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Polonnaruwa", "url": "https://whc.unesco.org/en/list/184"}]
  },
  {
    "site_id": "sigiriya_rock",
    "name": "Sigiriya (Lion Rock)",
    "city": "Dambulla",
    "country": "Sri Lanka",
    "region": "South Asia",
    "type": "Fortress Palace",
    "period": "477-495 CE",
    "description": "Ancient rock fortress crowned by a palace complex, rising 200m above the surrounding plain.",
    "historical_significance": "UNESCO World Heritage Site (1982); one of the most impressive ancient fortifications in the world; famous for its frescoes and mirror wall.",
    "architectural_features": "Colossal lion paws (now ruined) at entrance, ancient gardens with water features, frescoes of celestial maidens, mirror wall with ancient graffiti, panoramic views from summit, hydraulic systems.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Sigiriya", "url": "https://whc.unesco.org/en/list/185"}]
  },
])

# ── NEPAL (3 entries) ────────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "pashupatinath_temple",
    "name": "Pashupatinath Temple",
    "city": "Kathmandu",
    "country": "Nepal",
    "region": "South Asia",
    "type": "Hindu Temple",
    "period": "5th century CE (current structure 19th century)",
    "description": "Sacred Hindu temple complex dedicated to Lord Pashupati (Shiva) on the banks of the Bagmati River.",
    "historical_significance": "UNESCO World Heritage Site (1979); most sacred Shiva temple in Nepal; important pilgrimage site for Hindus worldwide.",
    "architectural_features": "Golden roof and silver doors, four-faced Pashupati statue, ritual cremation ghats, numerous smaller shrines, bell tower, sacred bulls (Nandi), priests in traditional dress.",
    "heritage_status": "UNESCO World Heritage Site (Kathmandu Valley)",
    "sources": [{"title": "UNESCO World Heritage List - Kathmandu Valley", "url": "https://whc.unesco.org/en/list/162"}]
  },
  {
    "site_id": "sagarmatha_national_park",
    "name": "Sagarmatha National Park (Everest)",
    "city": "Solukhumbu",
    "country": "Nepal",
    "region": "South Asia",
    "type": "Mountain Park",
    "period": "Geological formation",
    "description": "Mountain park encompassing Mount Everest (Sagarmatha) and surrounding peaks, the highest point on Earth.",
    "historical_significance": "UNESCO World Heritage Site (1979); home to the world's highest peak at 8,848.86m; sacred to Sherpa people.",
    "architectural_features": "Khumbu Glacier, Tengboche Monastery, Namche Bazaar, Hillary Step, South Col route, prayer flags and chortens along trails.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Sagarmatha", "url": "https://whc.unesco.org/en/list/163"}]
  },
  {
    "site_id": "boudhanath_stupa",
    "name": "Boudhanath Stupa",
    "city": "Kathmandu",
    "country": "Nepal",
    "region": "South Asia",
    "type": "Buddhist Stupa",
    "period": "14th century CE (rebuilt after 2015 earthquake)",
    "description": "One of the largest spherical stupas in Nepal and the world, central pilgrimage site for Tibetan Buddhism.",
    "historical_significance": "UNESCO World Heritage Site (1979, as part of Kathmandu Valley); one of the largest Buddhist monuments in Nepal.",
    "architectural_features": "36m diameter base, white dome with golden spire, all-seeing eyes of Buddha painted on all four sides, conical harmika umbrella, circumambulation path with prayer wheels.",
    "heritage_status": "UNESCO World Heritage Site (Kathmandu Valley)",
    "sources": [{"title": "UNESCO World Heritage List - Kathmandu Valley", "url": "https://whc.unesco.org/en/list/162"}]
  },
])

# ── PHILIPPINES (2 entries) ──────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "vigan_hERRERA",
    "name": "Vigan Historic Town",
    "city": "Vigan",
    "country": "Philippines",
    "region": "Southeast Asia",
    "type": "Historic Town",
    "period": "16th-19th century CE",
    "description": "Best-preserved Spanish colonial town in Asia, showcasing the blend of Southeast Asian and European architecture.",
    "historical_significance": "UNESCO World Heritage Site (1999); finest example of planned Spanish colonial town in Asia.",
    "architectural_features": "Calle Crisologo cobblestone street, ancestral houses with capiz shell windows, bell towers, Bantay Church, Chinese-Inca-Iberian fusion architecture, firewalls.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Vigan", "url": "https://whc.unesco.org/en/list/651"}]
  },
  {
    "site_id": "riasa_ruins",
    "name": "Rice Terraces of the Philippine Cordilleras",
    "city": "Benguet",
    "country": "Philippines",
    "region": "Southeast Asia",
    "type": "Agricultural Landscape",
    "period": "2,000+ years",
    "description": "Ancient irrigation system carving terraces into mountain slopes, still actively farmed by indigenous communities.",
    "historical_significance": "UNESCO World Heritage Site (1995); living cultural landscape demonstrating sustainable mountain agriculture for millennia.",
    "architectural_features": "Step-cut terraces following mountain contours, ancient渠水 (irrigation) channels, stone walls, Batad and Banaue terraces, indigenous Ifugao villages.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Rice Terraces", "url": "https://whc.unesco.org/en/list/738"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Sri Lanka + Nepal + Philippines: {len(catalogue)}")