import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── ITALY (10 entries) ───────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "colosseum",
    "name": "Colosseum (Flavian Amphitheatre)",
    "city": "Rome",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Amphitheatre",
    "period": "70-80 CE",
    "description": "Largest ancient amphitheatre ever built, capable of holding 50,000-80,000 spectators for gladiatorial contests and public spectacles.",
    "historical_significance": "UNESCO World Heritage Site (1980); symbol of Imperial Rome and one of the New Seven Wonders of the World.",
    "architectural_features": "Four-storey arcade with Doric, Ionic, and Corinthian orders, elliptical plan 189x156m, hypogeum underground network, velarium sail canopy system.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Rome", "url": "https://whc.unesco.org/en/list/91/"}]
  },
  {
    "site_id": "pantheon_rome",
    "name": "Pantheon",
    "city": "Rome",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Temple",
    "period": "126 CE (reconstructed by Hadrian)",
    "description": "Former Roman temple now a Catholic church, renowned for its massive unreinforced concrete dome with central oculus.",
    "historical_significance": "Best-preserved ancient Roman building; influenced Renaissance and Neoclassical architecture worldwide.",
    "architectural_features": "43.3m diameter unreinforced concrete dome, 8m oculus opening, coffered ceiling panels, portico with 8 Corinthian columns, granite interior columns.",
    "heritage_status": "Part of UNESCO World Heritage Site (Historic Centre of Rome)",
    "sources": [{"title": "UNESCO World Heritage List - Rome", "url": "https://whc.unesco.org/en/list/91/"}]
  },
  {
    "site_id": "leaning_tower_pisa",
    "name": "Leaning Tower of Pisa",
    "city": "Pisa",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Bell Tower",
    "period": "1173-1372 CE",
    "description": "Freestanding bell tower known for its unintended lean caused by soft foundation soil during construction.",
    "historical_significance": "UNESCO World Heritage Site (1987, as part of Piazza dei Miracoli); engineering marvel demonstrating medieval structural ingenuity.",
    "architectural_features": "Romanesque marble cylinders, 296 steps, eight storeys of arcades, 54.86m height, 3.97-degree tilt, white Carrara marble exterior.",
    "heritage_status": "UNESCO World Heritage Site (Piazza del Duomo, Pisa)",
    "sources": [{"title": "UNESCO World Heritage List - Pisa", "url": "https://whc.unesco.org/en/list/876"}]
  },
  {
    "site_id": "venice_historic",
    "name": "Venice and its Lagoon",
    "city": "Venice",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Historic City",
    "period": "5th century CE-1797 CE",
    "description": "City built on 118 small islands connected by 400+ bridges, famous for its canals, Gothic-Renaissance architecture, and maritime history.",
    "historical_significance": "UNESCO World Heritage Site (1987); unique urban ecosystem and masterpiece of human creative genius.",
    "architectural_features": "St Mark's Basilica with Byzantine domes and golden mosaics, Doge's Palace with Gothic tracery, Rialto Bridge, Grand Canal waterfront palazzi.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Venice", "url": "https://whc.unesco.org/en/list/394"}]
  },
  {
    "site_id": "florence_duomo",
    "name": "Florence Cathedral (Santa Maria del Fiore)",
    "city": "Florence",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Cathedral",
    "period": "1296-1436 CE",
    "description": "Gothic cathedral famous for Brunelleschi's revolutionary dome, the largest masonry dome ever built.",
    "historical_significance": "UNESCO World Heritage Site (1982); masterpiece of Renaissance engineering and architecture.",
    "architectural_features": "Red terracotta dome by Brunelleschi, green-white-pink marble facade, Giotto's Campanile, Baptistery with Gates of Paradise, vast interior.",
    "heritage_status": "UNESCO World Heritage Site (Historic Centre of Florence)",
    "sources": [{"title": "UNESCO World Heritage List - Florence", "url": "https://whc.unesco.org/en/list/174"}]
  },
  {
    "site_id": "pompeii",
    "name": "Archaeological Areas of Pompeii",
    "city": "Naples",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Archaeological Site",
    "period": "79 CE (buried); 1748 CE (excavation begins)",
    "description": "Ancient Roman city preserved by volcanic ash from Mount Vesuvius eruption, offering unmatched insight into daily Roman life.",
    "historical_significance": "UNESCO World Heritage Site (1997); most complete archaeological record of a Roman city.",
    "architectural_features": "Forum with Temple of Jupiter, amphitheatre, thermae (baths), villas with mosaic floors, plaster casts of victims, frescoes and street graffiti.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Pompeii", "url": "https://whc.unesco.org/en/list/829"}]
  },
  {
    "site_id": "milan_duomo",
    "name": "Milan Cathedral (Duomo di Milano)",
    "city": "Milan",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Cathedral",
    "period": "1386-1965 CE",
    "description": "Greatest Italian example of Gothic architecture, taking six centuries to complete, with an impressive rooftop terrace.",
    "historical_significance": "Largest church in Italy; symbol of Milan and Italian Gothic craftsmanship.",
    "architectural_features": "135 spires and 3,400 statues, pointed arches and flying buttresses, golden Madonnina statue on apex, rose windows, marble facade in pink Verona stone.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Opera di Milano Duomo", "url": "https://www.duomomilano.it"}]
  },
  {
    "site_id": "palatine_hill",
    "name": "Palatine Hill (Palatino)",
    "city": "Rome",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Archaeological Site",
    "period": "1000 BCE onwards",
    "description": "Central hill of the Seven Hills of Rome, site of early Roman settlements and imperial palaces.",
    "historical_significance": "UNESCO World Heritage Site (1980); legendary birthplace of Rome where Romulus founded the city; residence of emperors.",
    "architectural_features": "Domus Augustana and Domus Flavia ruins, Gardens of Farnesina, Vitellian stairs, remains of Nero's golden house, ancient road Via Sacra at base.",
    "heritage_status": "UNESCO World Heritage Site (Historic Centre of Rome)",
    "sources": [{"title": "UNESCO World Heritage List - Rome", "url": "https://whc.unesco.org/en/list/91/"}]
  },
  {
    "site_id": "trastevere_church",
    "name": "Basilica di Santa Maria in Trastevere",
    "city": "Rome",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Basilica",
    "period": "4th century CE origins; 12th century renovation",
    "description": "Ancient basilica in the Trastevere district, one of the most beautiful early Christian churches in Rome.",
    "historical_significance": "One of Rome's oldest churches; traditionally dated to the 4th century when Pope Urban I built the first chapel.",
    "architectural_features": "12 ancient granite columns supporting a Romanesque nave, golden Byzantine mosaics in the apse depicting the Virgin and Child, campanile, cosmatesque floor.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Diocese of Rome - Santa Maria in Trastevere", "url": "https://www.diocesi.roma.it"}]
  },
  {
    "site_id": "duomo_milan",
    "name": "Sforza Castle (Castello Sforzesco)",
    "city": "Milan",
    "country": "Italy",
    "region": "Southern Europe",
    "type": "Castle",
    "period": "1360-1450 CE",
    "description": "Large fortified castle in the heart of Milan, originally built by the Visconti family and later expanded by the Sforzas.",
    "historical_significance": "One of the largest citadels in Europe; symbol of Milanese power during the Renaissance.",
    "architectural_features": "Five massive corner towers, 400m perimeter walls, Courtyard of Honor, unfinished fresco by Bramante, Michelangelo's final Pietà fragment, medieval armory.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Milan Castle Museums", "url": "https://www.castellomilanese.it"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Italy: {len(catalogue)}")