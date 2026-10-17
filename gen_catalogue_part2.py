import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── CHINA (8 entries) ────────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "forbidden_city",
    "name": "Forbidden City",
    "city": "Beijing",
    "country": "China",
    "region": "East Asia",
    "type": "Palace",
    "period": "1406-1420 CE",
    "description": "Imperial palace complex in central Beijing, residence of Chinese emperors for nearly 500 years during the Ming and Qing dynasties.",
    "historical_significance": "UNESCO World Heritage Site (1987); largest collection of preserved ancient wooden structures in China; symbol of Chinese imperial power.",
    "architectural_features": "Nine gates, golden glazed tile roofs, massive courtyards, vermilion walls, dragon-carved marble terraces, double-eave hip roofs, 9999.5 rooms.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Forbidden City", "url": "https://whc.unesco.org/en/list/438"}]
  },
  {
    "site_id": "great_wall_badaling",
    "name": "Great Wall (Badaling Section)",
    "city": "Beijing",
    "country": "China",
    "region": "East Asia",
    "type": "Fortification",
    "period": "7th century BCE-1644 CE",
    "description": "Massive stone and brick fortification stretching over 21,000 km, built to protect Chinese states from invasions.",
    "historical_significance": "UNESCO World Heritage Site (1987); longest man-made structure in the world; symbol of Chinese resilience and engineering.",
    "architectural_features": "Watchtower towers every 100-200 metres, crenellated parapets, beacon towers on ridgelines, stone and brick construction, earthen ramparts.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Great Wall", "url": "https://whc.unesco.org/en/list/410"}]
  },
  {
    "site_id": "terracotta_army",
    "name": "Terracotta Army of Qin Shi Huang",
    "city": "Xi'an",
    "country": "China",
    "region": "East Asia",
    "type": "Archaeological Site",
    "period": "210-209 BCE",
    "description": "Thousands of life-sized terracotta sculptures depicting the armies of Qin Shi Huang, China's first emperor, buried with him.",
    "historical_significance": "UNESCO World Heritage Site (1987); one of the greatest archaeological discoveries of the 20th century.",
    "architectural_features": "Over 8,000 unique soldier figures, bronze chariots, real-size weapons, pits arranged in military formation, individually carved facial features.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Mausoleum of the First Qin Emperor", "url": "https://whc.unesco.org/en/list/389"}]
  },
  {
    "site_id": "potala_palace",
    "name": "Potala Palace",
    "city": "Lhasa",
    "country": "China",
    "region": "East Asia",
    "type": "Palace",
    "period": "7th century CE origins; 17th century reconstruction",
    "description": "Massive palace fortress on Red Hill in Lhasa, former residence of the Dalai Lamas and spiritual center of Tibetan Buddhism.",
    "historical_significance": "UNESCO World Heritage Site (1994); highest and largest ancient fortress in the world at 3,700m altitude.",
    "architectural_features": "White and Red Palaces, 13-storey main tower, golden roofs, mural paintings covering 250,000 sq metres, stupas of past Dalai Lamas.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Potala Palace", "url": "https://whc.unesco.org/en/list/705"}]
  },
  {
    "site_id": "summer_palace",
    "name": "Summer Palace",
    "city": "Beijing",
    "country": "China",
    "region": "East Asia",
    "type": "Palace",
    "period": "1750 CE; rebuilt 1886-1895",
    "description": "Vast ensemble of lakes, gardens and palaces in Beijing, serving as an imperial retreat since the Jin dynasty.",
    "historical_significance": "UNESCO World Heritage Site (1998); masterpiece of Chinese landscape garden design.",
    "architectural_features": "Kunming Lake, Longevity Hill, Marble Bridge, Tower of Buddhist Incense, 7-km Long Corridor with painted beams, 17-arch bridge.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Summer Palace", "url": "https://whc.unesco.org/en/list/865"}]
  },
  {
    "site_id": "temple_of_heaven",
    "name": "Temple of Heaven",
    "city": "Beijing",
    "country": "China",
    "region": "East Asia",
    "type": "Temple",
    "period": "1420 CE",
    "description": "Complex of religious buildings where emperors of the Ming and Qing dynasties made annual sacrifices to heaven.",
    "historical_significance": "UNESCO World Heritage Site (1998); finest surviving example of Chinese sacrificial architecture.",
    "architectural_features": "Hall of Prayer for Good Harvests with three-tiered circular roof, Imperial Vault of Heaven, Echo Wall, Circular Mound Altar with blue marble tiles.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Temple of Heaven", "url": "https://whc.unesco.org/en/list/879"}]
  },
  {
    "site_id": "yellow_crane_tower",
    "name": "Yellow Crane Tower",
    "city": "Wuhan",
    "country": "China",
    "region": "East Asia",
    "type": "Tower",
    "period": "223 CE origins; reconstructed 1985",
    "description": "Iconic five-storey pavilion on Snake Hill overlooking the Yangtze River, celebrated in classical Chinese poetry for 1,700 years.",
    "historical_significance": "Most reproduced subject in Chinese poetry; symbol of Wuhan and southern China.",
    "architectural_features": "Five-storey hexagonal pavilion with yellow glazed tiles, upturned eaves, intricate bracket sets, panoramic river views, adjacent pavilions and gardens.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Hubei Provincial Cultural Heritage", "url": "https://wh.gouv.gov.cn"}]
  },
  {
    "site_id": "stone_forest",
    "name": "Stone Forest (Shilin)",
    "city": "Kunming",
    "country": "China",
    "region": "East Asia",
    "type": "Natural Monument",
    "period": "270 million years old",
    "description": "Dramatic limestone karst formations rising up to 40 metres, created by millions of years of erosion.",
    "historical_significance": "UNESCO World Heritage Site (2007); one of the most spectacular karst formations in the world.",
    "architectural_features": "Towering limestone pillars, forest-like formations, natural bridges, underground cave systems, Sword Peak Ridge walkway.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - South China Karst", "url": "https://whc.unesco.org/en/list/1330"}]
  },
])

# ── EGYPT (6 entries) ────────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "great_pyramid_giza",
    "name": "Great Pyramid of Giza (Pyramid of Khufu)",
    "city": "Giza",
    "country": "Egypt",
    "region": "North Africa",
    "type": "Pyramid",
    "period": "2580-2560 BCE",
    "description": "The oldest and largest of the three pyramids in the Giza pyramid complex, built as a tomb for Pharaoh Khufu.",
    "historical_significance": "UNESCO World Heritage Site (1979); only surviving wonder of the Ancient World; original height 146.6m.",
    "architectural_features": "Limestone blocks weighing 2.5-15 tonnes each, ascending corridor, King's Chamber with granite sarcophagus, Grand Gallery, external casing stones visible at base.",
    "heritage_status": "UNESCO World Heritage Site (Ancient Memphis and its Necropolis)",
    "sources": [{"title": "UNESCO World Heritage List - Memphis and its Necropolis", "url": "https://whc.unesco.org/en/list/88"}]
  },
  {
    "site_id": "great_sphinx",
    "name": "Great Sphinx of Giza",
    "city": "Giza",
    "country": "Egypt",
    "region": "North Africa",
    "type": "Monument",
    "period": "2500 BCE approx.",
    "description": "Limestone statue with a lion's body and human head, facing east towards the rising sun, guarding the Giza plateau.",
    "historical_significance": "UNESCO World Heritage Site (1979); largest monolithic statue in the world at 73m long and 20m high.",
    "architectural_features": "Carved from bedrock limestone, missing royal beard, ceremonial nose restored, weathering patterns on enclosure walls.",
    "heritage_status": "UNESCO World Heritage Site (Ancient Memphis and its Necropolis)",
    "sources": [{"title": "UNESCO World Heritage List - Memphis and its Necropolis", "url": "https://whc.unesco.org/en/list/88"}]
  },
  {
    "site_id": "karnak_temple",
    "name": "Karnak Temple Complex",
    "city": "Luxor",
    "country": "Egypt",
    "region": "North Africa",
    "type": "Temple",
    "period": "2055-100 BCE",
    "description": "Vast open-air museum and ancient religious complex dedicated to the Theban triad of Amun, Mut, and Khonsu.",
    "historical_significance": "UNESCO World Heritage Site (1979); largest ancient religious site ever built; worshipped for over 2,000 years.",
    "architectural_features": "Hypostyle Hall with 134 massive papyrus-column capitals, Great Aten Temple, sacred lake, obelisk of Hatshepsut, processional sphinx avenue.",
    "heritage_status": "UNESCO World Heritage Site (Thebes: Ancient Capital with its Necropolis)",
    "sources": [{"title": "UNESCO World Heritage List - Thebes", "url": "https://whc.unesco.org/en/list/89"}]
  },
  {
    "site_id": "abu_simbel",
    "name": "Abu Simbel Temples",
    "city": "Abu Simbel",
    "country": "Egypt",
    "region": "North Africa",
    "type": "Temple",
    "period": "1264-1224 BCE",
    "description": "Two massive rock-cut temples built by Ramesses II, moved in 1968 during the Aswan High Dam rescue operation.",
    "historical_significance": "UNESCO World Heritage Site (1979); greatest feat of archaeological relocation in history; aligned so sun illuminates inner sanctuary twice yearly.",
    "architectural_features": "Four 20-metre colossi of Ramesses II at facade, 36m-high entrance, four sanctuary statues, smaller Temple of Hathor with six columned statues of Nefertari.",
    "heritage_status": "UNESCO World Heritage Site (Nubian Monuments)",
    "sources": [{"title": "UNESCO World Heritage List - Nubian Monuments", "url": "https://whc.unesco.org/en/list/90"}]
  },
  {
    "site_id": "valley_of_kings",
    "name": "Valley of the Kings",
    "city": "Luxor",
    "country": "Egypt",
    "region": "North Africa",
    "type": "Tombs",
    "period": "1550-1070 BCE",
    "description": "Burial place of ancient Egyptian pharaohs, containing over 60 tombs including that of Tutankhamun.",
    "historical_significance": "UNESCO World Heritage Site (1979); richest archaeological find in modern history with Tutankhamun's tomb.",
    "architectural_features": "Decorated burial chambers with vivid wall paintings, descending corridors carved through limestone, anthropoid sarcophagi, papyrus-shaped columns.",
    "heritage_status": "UNESCO World Heritage Site (Thebes: Ancient Capital with its Necropolis)",
    "sources": [{"title": "UNESCO World Heritage List - Thebes", "url": "https://whc.unesco.org/en/list/89"}]
  },
  {
    "site_id": "luxor_temple",
    "name": "Luxor Temple",
    "city": "Luxor",
    "country": "Egypt",
    "region": "North Africa",
    "type": "Temple",
    "period": "1400-1100 BCE",
    "description": "Ancient Theban temple on the east bank of the Nile, devoted to the rejuvenation of kingship and the god Amun.",
    "historical_significance": "UNESCO World Heritage Site (1979); connected to Karnak by a 2.7km Sphinx Avenue used in the Opet Festival.",
    "architectural_features": "Colonnaded courts, Great Hypostyle Hall, massive pylon entrance, sacred lake, towering obelisk of Ramses II, colossal statue fragments.",
    "heritage_status": "UNESCO World Heritage Site (Thebes: Ancient Capital with its Necropolis)",
    "sources": [{"title": "UNESCO World Heritage List - Thebes", "url": "https://whc.unesco.org/en/list/89"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after China + Egypt: {len(catalogue)}")