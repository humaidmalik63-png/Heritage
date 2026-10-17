import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── MEXICO (5 entries) ───────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "chichen_itza",
    "name": "Chichen Itza",
    "city": "Chichen Itza",
    "country": "Mexico",
    "region": "Central America",
    "type": "Archaeological Site",
    "period": "600-1200 CE",
    "description": "Major pre-Columbian Maya city featuring El Castillo pyramid, Great Ball Court, and Temple of Warriors.",
    "historical_significance": "UNESCO World Heritage Site (1988); one of the New Seven Wonders of the World; demonstrates advanced Maya astronomy and engineering.",
    "architectural_features": "El Castillo pyramid with 365 steps (solar calendar), serpent shadow phenomenon at equinox, Great Ball Court with acoustics, Temple of Warriors with colonnades, observatory El Caracol.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Chichen Itza", "url": "https://whc.unesco.org/en/list/886"}]
  },
  {
    "site_id": "teotihuacan",
    "name": "Teotihuacan",
    "city": "Teotihuacan",
    "country": "Mexico",
    "region": "Central America",
    "type": "Archaeological Site",
    "period": "100 BCE-750 CE",
    "description": "Ancient Mesoamerican city with the largest pyramids in the pre-Columbian Americas, once home to 200,000 people.",
    "historical_significance": "UNESCO World Heritage Site (1987); one of the largest ancient cities in the world; influences Aztec cosmology.",
    "architectural_features": "Pyramid of the Sun (65m high), Pyramid of the Moon, Avenue of the Dead 4km long, Temple of Quetzalcoatl with carved serpents, Palace of Quetzalpapalotl, extensive mural paintings.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Teotihuacan", "url": "https://whc.unesco.org/en/list/427"}]
  },
  {
    "site_id": "centra_valle_mexico",
    "name": "Centro Historico de Mexico City",
    "city": "Mexico City",
    "country": "Mexico",
    "region": "Central America",
    "type": "Historic Center",
    "period": "1521-1821 CE",
    "description": "Historic center built over the Aztec capital Tenochtitlan, containing some of the most important colonial architecture in the Americas.",
    "historical_significance": "UNESCO World Heritage Site (1987); largest collection of colonial architecture in the Americas; built atop the destroyed Aztec capital.",
    "architectural_features": "Metropolitan Cathedral onAztec temple foundations, National Palace with Rivera murals, Templo Mayor ruins, Palacio de Bellas Artes, Zocalo plaza, Casa de los Azulejos.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Mexico City", "url": "https://whc.unesco.org/en/list/412"}]
  },
  {
    "site_id": "xochimilco",
    "name": "Xochimilco Canals",
    "city": "Mexico City",
    "country": "Mexico",
    "region": "Central America",
    "type": "Cultural Landscape",
    "period": "14th century CE-ongoing",
    "description": "Remnants of the ancient Aztec chinampa agricultural system, now a network of canals and floating gardens.",
    "historical_significance": "UNESCO World Heritage Site (1987); last remaining vestige of the ancient lake and canal system of Tenochtitlan.",
    "architectural_features": "Artificial chinampa islands, trajineras (colorful boats), ceramic tile pavilions, floating markets, aqueduct ruins, traditional farming techniques still practiced.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Xochimilco", "url": "https://whc.unesco.org/en/list/866"}]
  },
  {
    "site_id": "palenque_ruins",
    "name": "Palenque",
    "city": "Palenque",
    "country": "Mexico",
    "region": "Central America",
    "type": "Archaeological Site",
    "period": "615-799 CE",
    "description": "Maya city renowned for its sophisticated architecture and intricate stucco reliefs, set in tropical jungle.",
    "historical_significance": "UNESCO World Heritage Site (1987); peak of Classic Maya art and architecture; birthplace of King Pakal the Great.",
    "architectural_features": "Temple of Inscriptions with Pakal's tomb, Palace complex with distinctive tower, Group of the Crosses temples, refined stucco facades, natural spring integration.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Palenque", "url": "https://whc.unesco.org/en/list/428"}]
  },
])

# ── CAMBODIA (3 entries) ─────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "angkor_wat",
    "name": "Angkor Wat",
    "city": "Siem Reap",
    "country": "Cambodia",
    "region": "Southeast Asia",
    "type": "Temple Complex",
    "period": "1113-1150 CE",
    "description": "Largest religious monument in the world, originally Hindu then Buddhist, masterpiece of Khmer architecture.",
    "historical_significance": "UNESCO World Heritage Site (1992); symbol of Cambodia appearing on its national flag; represents Mount Meru, home of the gods.",
    "architectural_features": "Five lotus-bud towers rising 65m, 3km longGallery bas-reliefs depicting Ramayana and Mahabharata, moat 190m wide, galleries with devata carvings, cruciform terraces.",
    "heritage_status": "UNESCO World Heritage Site (Angkor)",
    "sources": [{"title": "UNESCO World Heritage List - Angkor", "url": "https://whc.unesco.org/en/list/668"}]
  },
  {
    "site_id": "angkor_thom",
    "name": "Angkor Thom and Bayon",
    "city": "Siem Reap",
    "country": "Cambodia",
    "region": "Southeast Asia",
    "type": "Temple Complex",
    "period": "1219-1247 CE",
    "description": "Last capital of the Khmer Empire featuring the famous Bayon temple with its smiling stone faces.",
    "historical_significance": "UNESCO World Heritage Site (1992); monumental expression of Mahayana Buddhist cosmology.",
    "architectural_features": "Bayon temple with 54 towers bearing 216 giant serene faces, four elaborately carved triumphal gates, Terrace of the Elephants, banyan trees growing over ruins.",
    "heritage_status": "UNESCO World Heritage Site (Angkor)",
    "sources": [{"title": "UNESCO World Heritage List - Angkor", "url": "https://whc.unesco.org/en/list/668"}]
  },
  {
    "site_id": "preah_khan",
    "name": "Preah Khan Temple",
    "city": "Siem Reap",
    "country": "Cambodia",
    "region": "Southeast Asia",
    "type": "Temple",
    "period": "1191 CE",
    "description": "Large temple-complex built by King Jayavarman VII as a memorial to his father, combining Buddhist and Hindu elements.",
    "historical_significance": "UNESCO World Heritage Site (1992); represents the height of Khmer temple construction under the Bayon style.",
    "architectural_features": "Long gallery with elephant capitals, jade terrace, central sanctuary with Buddha image, jungle-entangled ruins, elaborate devata carvings, moat with naga balustrades.",
    "heritage_status": "UNESCO World Heritage Site (Angkor)",
    "sources": [{"title": "UNESCO World Heritage List - Angkor", "url": "https://whc.unesco.org/en/list/668"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Mexico + Cambodia: {len(catalogue)}")