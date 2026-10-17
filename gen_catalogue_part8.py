import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── PERU (4 entries) ─────────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "machu_picchu",
    "name": "Machu Picchu",
    "city": "Cusco",
    "country": "Peru",
    "region": "South America",
    "type": "Inca Citadel",
    "period": "1450 CE",
    "description": "15th-century Inca citadel set high in the Andes, one of the most iconic archaeological sites in the world.",
    "historical_significance": "UNESCO World Heritage Site (1983); New Seven Wonder of the World; lost to Europeans until 1911; masterpiece of Inca engineering.",
    "architectural_features": "Terraced slopes following mountain contours, Temple of the Sun with circular walls, Intihuatana stone, Room of the Three Windows, precise ashlar masonry without mortar, urban and agricultural sectors.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Machu Picchu", "url": "https://whc.unesco.org/en/list/1331"}]
  },
  {
    "site_id": "nazca_lines",
    "name": "Nazca Lines",
    "city": "Nazca",
    "country": "Peru",
    "region": "South America",
    "type": "Geoglyphs",
    "period": "500 BCE-500 CE",
    "description": "Massive ancient geoglyphs etched into the desert plateau, depicting animals, plants, and geometric shapes visible only from the air.",
    "historical_significance": "UNESCO World Heritage Site (1994); one of archaeology's greatest mysteries; demonstrates extraordinary precision and planning.",
    "architectural_features": "Over 800 straight lines up to 30km long, 300+ geometric figures, animal representations including hummingbird, spider, monkey, 90m condor, 300m lizard, trapezoid shapes.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Nazca Lines", "url": "https://whc.unesco.org/en/list/299"}]
  },
  {
    "site_id": "cuzco_center",
    "name": "Historic Centre of Cusco",
    "city": "Cusco",
    "country": "Peru",
    "region": "South America",
    "type": "Historic City",
    "period": "12th-18th century CE",
    "description": "Former capital of the Inca Empire with colonial Spanish architecture built atop Inca foundations.",
    "historical_significance": "UNESCO World Heritage Site (1983); capital of the Inca Empire (Tawantinsuyu); living testimony of Andean and Spanish colonial fusion.",
    "architectural_features": "Temple of Coricancha with gold-plated walls, San Juan Church built over Inca walls, 12-angled stone in Calle Santa Teresa, Plaza de Armas, baroque facades on Inca foundations.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Cusco", "url": "https://whc.unesco.org/en/list/273"}]
  },
  {
    "site_id": "sacsayhuaman",
    "name": "Sacsayhuaman Fortress",
    "city": "Cusco",
    "country": "Peru",
    "region": "South America",
    "type": "Fortress",
    "period": "1438-1472 CE",
    "description": "Massive Inca fortress overlooking Cusco with some of the largest stones ever used in construction.",
    "historical_significance": "Part of UNESCO World Heritage Site (1983); demonstrates Inca military engineering and monumental stonework.",
    "architectural_features": "Zigzag walls with stones up to 120 tonnes, perfectly fitted polygonal masonry without mortar, three terraced walls, ceremonial platforms, underground tunnels.",
    "heritage_status": "UNESCO World Heritage Site (Historic Sanctuary of Machu Picchu)",
    "sources": [{"title": "UNESCO World Heritage List - Machu Picchu", "url": "https://whc.unesco.org/en/list/1331"}]
  },
])

# ── IRAN (5 entries) ─────────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "persepolis",
    "name": "Persepolis (Takht-e Jamshid)",
    "city": "Marvdasht",
    "country": "Iran",
    "region": "Western Asia",
    "type": "Palace Complex",
    "period": "518-330 BCE",
    "description": "Ceremonial capital of the Achaemenid Empire, founded by Darius the Great, destroyed by Alexander the Great.",
    "historical_significance": "UNESCO World Heritage Site (1979); greatest achievement of ancient Persian architecture; symbol of Iranian imperial glory.",
    "architectural_features": "Apadana palace with 72 columns, Gate of All Nations, Throne Hall with 100 columns, relief sculptures of 23 subject nations, twin bull-headed columns, massive stairway reliefs.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Persepolis", "url": "https://whc.unesco.org/en/list/137"}]
  },
  {
    "site_id": "isfahan_maidan",
    "name": "Naqsh-e Jahan Square",
    "city": "Isfahan",
    "country": "Iran",
    "region": "Western Asia",
    "type": "Royal Square",
    "period": "1598-1629 CE",
    "description": "One of the largest city squares in the world, surrounded by mosques, palaces, and bazaars from the Safavid era.",
    "historical_significance": "UNESCO World Heritage Site (1979); masterpiece of Islamic urban design; heart of Safavid Isfahan.",
    "architectural_features": "546m x 160m rectangle, Shah Mosque with seven-color mosaic tiles, Sheikh Lotfollah Mosque with pearlescent dome, Ali Qapu Palace with music room, vast bazaar arcade.",
    "heritage_status": "UNESCO World Heritage Site (Naqsh-e Jahan Square)",
    "sources": [{"title": "UNESCO World Heritage List - Isfahan", "url": "https://whc.unesco.org/en/list/897"}]
  },
  {
    "site_id": "pasargadae",
    "name": "Pasargadae",
    "city": "Pasargadae",
    "country": "Iran",
    "region": "Western Asia",
    "type": "Ancient Capital",
    "period": "546-330 BCE",
    "description": "First capital of the Achaemenid Empire, containing the tomb of Cyrus the Great.",
    "historical_significance": "UNESCO World Heritage Site (2004); birthplace of Persian imperial civilization; Cyrus Cylinder is considered first charter of human rights.",
    "architectural_features": "Tomb of Cyrus with simple rectangular form and gabled roof, Garden of Cyrus with four-fold water channels, Audience Hall ruins, fortification walls, inscribed stone blocks.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Pasargadae", "url": "https://whc.unesco.org/en/list/1161"}]
  },
  {
    "site_id": "yazd_old",
    "name": "Yazd Historic City",
    "city": "Yazd",
    "country": "Iran",
    "region": "Western Asia",
    "type": "Historic City",
    "period": "7th century BCE-20th century CE",
    "description": "Desert city with mud-brick architecture adapted to extreme climate, continuous human settlement for 3,000 years.",
    "historical_significance": "UNESCO World Heritage Site (2010); finest example of desert city architecture; Zoroastrian community still preserves ancient traditions.",
    "architectural_features": "Windcatcher towers (badgirs) for passive cooling, mud-brick alleyways, Jameh Mosque with tallest brick minaret, Fatemi House, Zoroastrian Fire Temple with eternal flame.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Yazd", "url": "https://whc.unesco.org/en/list/1325"}]
  },
  {
    "site_id": "shushtar_hydraulic",
    "name": "Shushtar Historical Hydraulic System",
    "city": "Shushtar",
    "country": "Iran",
    "region": "Western Asia",
    "type": "Hydraulic Complex",
    "period": "5th century BCE-7th century CE",
    "description": "Ancient system of dams, canals, and water mills demonstrating sophisticated hydraulic engineering.",
    "historical_significance": "UNESCO World Heritage Site (2009); most impressive hydraulic system of ancient Iran; influenced Roman engineering.",
    "architectural_features": "Band-e Kaisar Roman-era dam, 17 water mills, tunnels cutting through rock, diversion weirs, channels and reservoirs, Qanats (underground aqueducts).",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Shushtar", "url": "https://whc.unesco.org/en/list/1299"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Peru + Iran: {len(catalogue)}")