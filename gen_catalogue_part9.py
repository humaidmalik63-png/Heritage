import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── INDONESIA (4 entries) ────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "borobudur",
    "name": "Borobudur Temple",
    "city": "Magelang",
    "country": "Indonesia",
    "region": "Southeast Asia",
    "type": "Buddhist Temple",
    "period": "800-825 CE",
    "description": "Largest Buddhist temple in the world, a massive stepped pyramid covered in 2,672 relief panels and 504 Buddha statues.",
    "historical_significance": "UNESCO World Heritage Site (1991); greatest Buddhist monument in Southeast Asia; represents the cosmos in stone.",
    "architectural_features": "Nine stacked platforms (6 square, 3 circular), 72 bell-shaped stupas perforated with Buddha statues, 2,672 narrative relief panels, 504 Buddha statues, mandala ground plan.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Borobudur", "url": "https://whc.unesco.org/en/list/617"}]
  },
  {
    "site_id": "prambanan",
    "name": "Prambanan Temple Compound",
    "city": "Yogyakarta",
    "country": "Indonesia",
    "region": "Southeast Asia",
    "type": "Hindu Temple",
    "period": "850 CE",
    "description": "Largest Hindu temple complex in Indonesia, dedicated to the Trimurti (Brahma, Vishnu, Shiva).",
    "historical_significance": "UNESCO World Heritage Site (1991); masterpiece of Hindu architecture in Southeast Asia; contemporary of Borobudur.",
    "architectural_features": "Main temple 47m tall surrounded by 224 smaller temples, bas-relief panels depicting Ramayana, Nandi and Garuda statues, ornate candi (temple) towers, intricately carved lintels.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Prambanan", "url": "https://whc.unesco.org/en/list/616"}]
  },
  {
    "site_id": "ubud_palem",
    "name": "Sangiran Early Human Site",
    "city": "Sragen",
    "country": "Indonesia",
    "region": "Southeast Asia",
    "type": "Archaeological Site",
    "period": "1.6 million-100,000 years BP",
    "description": "One of the most important early human fossil sites in the world, yielding remains of Java Man.",
    "historical_significance": "UNESCO World Heritage Site (1996); key evidence for human evolution in Southeast Asia.",
    "architectural_features": "Erosion valleys exposing sedimentary layers, fossil-bearing strata, museum with 140+ hominin specimens, excavation sites across 65 sq km.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Sangiran", "url": "https://whc.unesco.org/en/list/653"}]
  },
  {
    "site_id": "bali_subak",
    "name": "Cultural Landscape of Bali: Subak System",
    "city": "Bali",
    "country": "Indonesia",
    "region": "Southeast Asia",
    "type": "Cultural Landscape",
    "period": "9th century CE-ongoing",
    "description": "Rice terraces managed by the subak water-sharing system, embodying the Hindu philosophy of Tri Hita Karana.",
    "historical_significance": "UNESCO World Heritage Site (2012); living cultural landscape demonstrating sustainable agricultural practice.",
    "architectural_features": "Step-cut rice terraces, temple complexes (Pura) at water sources, irrigation channels and weirs, volcanic mountain backdrop, traditional Balinese village layout.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Bali", "url": "https://whc.unesco.org/en/list/1153"}]
  },
])

# ── JORDAN (4 entries) ───────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "petra",
    "name": "Petra",
    "city": "Wadi Musa",
    "country": "Jordan",
    "region": "Western Asia",
    "type": "Rock-Cut City",
    "period": "4th century BCE-2nd century CE",
    "description": "Ancient Nabataean city carved into rose-red sandstone cliffs, famous for its facade known as Al-Khazneh.",
    "historical_significance": "UNESCO World Heritage Site (1985); New Seven Wonder of the World; lost to the Western world until 1812.",
    "architectural_features": "Al-Khazneh (Treasury) 40m facade, Al-Deir (Monastery) larger facade, Siq canyon entrance, Royal Tombs with colonnaded facades, Roman-style theater, hypogeum tombs.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Petra", "url": "https://whc.unesco.org/en/list/78"}]
  },
  {
    "site_id": "um_rashrash",
    "name": "Umm ar-Rasas (Kastrom Mefa'a)",
    "city": "Mafraq",
    "country": "Jordan",
    "region": "Western Asia",
    "type": "Archaeological Site",
    "period": "Roman-Byzantine periods",
    "description": "Ancient city with well-preserved Byzantine mosaics depicting towns and landscapes of the Holy Land.",
    "historical_significance": "UNESCO World Heritage Site (2011); important Christian pilgrimage site with exceptional mosaic floor.",
    "architectural_features": "Mosaic floor with Greek inscriptions and topographical maps, St. Stephen's Church ruins, tower foundations, early Christian basilicas, Roman road remnants.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Umm ar-Rasas", "url": "https://whc.unesco.org/en/list/1364"}]
  },
  {
    "site_id": "qumran_caves",
    "name": "Qumran Caves (Dead Sea Scrolls)",
    "city": "Qumran",
    "country": "Jordan",
    "region": "Western Asia",
    "type": "Cave Complex",
    "period": "2nd century BCE-1st century CE",
    "description": "Caves where the Dead Sea Scrolls were discovered in 1947, profoundly impacting biblical scholarship.",
    "historical_significance": "One of the most important archaeological discoveries of the 20th century; Essene settlement where scrolls were hidden.",
    "architectural_features": "Eleven cave systems, plastered micro-writes, pottery jars, ancient water cisterns, ritual baths (mikva'ot), community buildings.",
    "heritage_status": "UNESCO World Heritage Site (tentative)",
    "sources": [{"title": "Israel Antiquities Authority", "url": "https://www.antiquities.org.il"}]
  },
  {
    "site_id": "wadi_rum",
    "name": "Wadi Rum Protected Area",
    "city": "Aqaba",
    "country": "Jordan",
    "region": "Western Asia",
    "type": "Natural/Cultural Site",
    "period": "Ancient petroglyphs-ongoing",
    "description": "Vast sandstone desert valley with towering red dunes and ancient Nabataean petroglyphs.",
    "historical_significance": "UNESCO World Heritage Site (2011); 'Valley of the Moon'; filming location for Lawrence of Arabia and The Martian.",
    "architectural_features": "Jabal Umm al-Biyara rock arch, Kandara valley petroglyphs, Nabataean inscriptions and altars, ancient water channels, Bedouin tent camps.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Wadi Rum", "url": "https://whc.unesco.org/en/list/1363"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Indonesia + Jordan: {len(catalogue)}")