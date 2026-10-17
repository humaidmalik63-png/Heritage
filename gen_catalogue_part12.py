import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── ETHIOPIA (4 entries) ─────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "lalibela_churches",
    "name": "Rock-Hewn Churches, Lalibela",
    "city": "Lalibela",
    "country": "Ethiopia",
    "region": "East Africa",
    "type": "Rock-Hewn Church",
    "period": "12th-13th century CE",
    "description": "Eleven medieval monolithic rock-cut churches carved downward from single blocks of granite, known as 'New Jerusalem'.",
    "historical_significance": "UNESCO World Heritage Site (1978); living religious site still used for worship; extraordinary achievement in sacred architecture.",
    "architectural_features": "Church of St. George (cross-shaped), Ta Giyorgis with surrounding trench, Bet Golgotha with Solomon's tomb, deep trenches separating churches, narrow passageways, Ethiopian Orthodox crosses.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Lalibela", "url": "https://whc.unesco.org/en/list/94"}]
  },
  {
    "site_id": "aksum_stelae",
    "name": "Aksum (Axum)",
    "city": "Aksum",
    "country": "Ethiopia",
    "region": "East Africa",
    "type": "Archaeological Site",
    "period": "1st-13th century CE",
    "description": "Ancient city and capital of the Kingdom of Aksum, one of the great civilizations of the ancient world.",
    "historical_significance": "UNESCO World Heritage Site (1980); legendary resting place of the Ark of the Covenant; birthplace of Ethiopian civilization.",
    "architectural_features": "24m obelisk (stelae) with false doors and windows, King Ezana's inscription, ruins of royal palaces, underground tombs, Church of St. Mary of Zion.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Aksum", "url": "https://whc.unesco.org/en/list/95"}]
  },
  {
    "site_id": "simien_mountains",
    "name": "Simien Mountains National Park",
    "city": "Gondar",
    "country": "Ethiopia",
    "region": "East Africa",
    "type": "Mountain Complex",
    "period": "Geological formation",
    "description": "Dramatic mountain landscape with jagged peaks, deep valleys, and endemic wildlife including Gelada baboons.",
    "historical_significance": "UNESCO World Heritage Site (1978); most spectacular mountain range in Africa; contains Ras Dashen at 4,550m.",
    "architectural_features": "Sheika Gena escarpment dropping 1,500m, sharp peaks and seracs, ancient lava flows, endemic species habitat, rock-hewn churches in surrounding area.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Simien Mountains", "url": "https://whc.unesco.org/en/list/57"}]
  },
  {
    "site_id": "gondar_castles",
    "name": "Fasil Ghebbi, Gondar",
    "city": "Gondar",
    "country": "Ethiopia",
    "region": "East Africa",
    "type": "Royal Enclosure",
    "period": "1636-1755 CE",
    "description": "Royal enclosure of castles and palaces built by Ethiopian emperors, called the 'Camelot of Africa'.",
    "historical_significance": "UNESCO World Heritage Site (1979); last major royal compound of the Ethiopian Empire; unique African fortress architecture.",
    "architectural_features": "Fasilides' Castle with thick walls and battlements, Debre Birhan Selassie church with ceiling paintings, library with ancient manuscripts, bathhouse of Fasilides, towered gateways.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Gondar", "url": "https://whc.unesco.org/en/list/96"}]
  },
])

# ── MOROCCO (4 entries) ──────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "meknes_medina",
    "name": "Medina of Fez",
    "city": "Fez",
    "country": "Morocco",
    "region": "North Africa",
    "type": "Historic Medina",
    "period": "9th-15th century CE",
    "description": "One of the world's largest car-free urban areas, a labyrinth of medieval alleys, madrasas, and souks.",
    "historical_significance": "UNESCO World Heritage Site (1981); secondholiest city in Islam; home to the world's oldest university (al-Qarawiyyin, founded 859).",
    "architectural_features": "Bou Inania Madrasa with zellij tilework, Al-Attarine Madrasa, Tanneries of Chouara (ancient dye pits), 9th-century city walls, 9,000+ alleyways, ornate wooden doors.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Fez", "url": "https://whc.unesco.org/en/list/248"}]
  },
  {
    "site_id": "marrakech_medina",
    "name": "Medina of Marrakech",
    "city": "Marrakech",
    "country": "Morocco",
    "region": "North Africa",
    "type": "Historic Medina",
    "period": "11th-19th century CE",
    "description": "Historic walled city famous for its vibrant souks, palaces, and the iconic Djemaa el-Fna square.",
    "historical_significance": "UNESCO World Heritage Site (1985); imperial city showcasing Berber, Arab, and Andalusian architectural traditions.",
    "architectural_features": "Koutoubia Mosque with 77m minaret, Bahia Palace with mosaic courtyards, Saadian Tombs with marble screens, Djemaa el-Fna square, intricate riad gardens.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Marrakech", "url": "https://whc.unesco.org/en/list/247"}]
  },
  {
    "site_id": "kairouan_mosque",
    "name": "Kairouan Great Mosque",
    "city": "Kairouan",
    "country": "Morocco",
    "region": "North Africa",
    "type": "Mosque",
    "period": "670 CE (original); 836-863 CE (current)",
    "description": "One of the most important mosques in the Islamic world, founded by the Arab general Uqba ibn Nafi.",
    "historical_significance": "UNESCO World Heritage Site (1988, as City of Kairouan); fourth holiest city of Islam; model for later mosques including Al-Azhar and Cordoba.",
    "architectural_features": "Square plan with courtyard, 124 columns from Roman ruins, massive wooden doors, tiered minaret, hypostyle prayer hall, sacred pool for ablutions.",
    "heritage_status": "UNESCO World Heritage Site (City of Kairouan)",
    "sources": [{"title": "UNESCO World Heritage List - Kairouan", "url": "https://whc.unesco.org/en/list/177"}]
  },
  {
    "site_id": "essaouira_port",
    "name": "Essaouira (Mogador)",
    "city": "Essaouira",
    "country": "Morocco",
    "region": "North Africa",
    "type": "Fortified Port City",
    "period": "18th century CE",
    "description": "Coastal fortress city with distinctive Portuguese and Moroccan architecture, historic port on the Atlantic.",
    "historical_significance": "UNESCO World Heritage Site (2001); well-preserved example of 18th-century North African fortified town.",
    "architectural_features": "Skala de la Ville sea fortress with cannon emplacements, medina with fortified ramparts, Portuguese-style grid streets, cedar wood doors, harbor with fishing boats.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Essaouira", "url": "https://whc.unesco.org/en/list/486"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Ethiopia + Morocco: {len(catalogue)}")