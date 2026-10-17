import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── PORTUGAL (4 entries) ─────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "belém_tower",
    "name": "Belém Tower (Torre de Belém)",
    "city": "Lisbon",
    "country": "Portugal",
    "region": "Southern Europe",
    "type": "Fortress",
    "period": "1514-1520 CE",
    "description": "Fortified tower on the Tagus riverbank, iconic symbol of the Portuguese Age of Discovery.",
    "historical_significance": "UNESCO World Heritage Site (1983); masterpiece of Manueline architecture; departure point for explorers.",
    "architectural_features": "Moorish-inspired merlons, rope motifs in stone, ornate window frames, underground dungeon, armory room, balcony overlooking river, statue of Saint Vincent.",
    "heritage_status": "UNESCO World Heritage Site (Monument of Belém)",
    "sources": [{"title": "UNESCO World Heritage List - Belém", "url": "https://whc.unesco.org/en/list/267"}]
  },
  {
    "site_id": "jerónimos_monastery",
    "name": "Jerónimos Monastery",
    "city": "Lisbon",
    "country": "Portugal",
    "region": "Southern Europe",
    "type": "Monastery",
    "period": "1501-1520 CE",
    "description": "Former Benedictine monastery, finest example of Manueline architecture, burial place of Vasco da Gama and Luís de Camões.",
    "historical_significance": "UNESCO World Heritage Site (1983); symbol of Portuguese maritime power; masterpiece of Gothic-Manueline style.",
    "architectural_features": "Intricate stone carvings of ropes, spheres, and marine motifs, cloister with ribbed vaults, royal pantheon, twin bell towers, carved walnut doors.",
    "heritage_status": "UNESCO World Heritage Site (Monument of Belém)",
    "sources": [{"title": "UNESCO World Heritage List - Belém", "url": "https://whc.unesco.org/en/list/267"}]
  },
  {
    "site_id": "evora_cathedral",
    "name": "Évora Cathedral",
    "city": "Évora",
    "country": "Portugal",
    "region": "Southern Europe",
    "type": "Cathedral",
    "period": "1186-1250 CE",
    "description": "Massive Gothic cathedral with fortress-like appearance, one of the finest examples of Portuguese Gothic architecture.",
    "historical_significance": "UNESCO World Heritage Site (1986, as Historic Centre of Évora); important religious and military monument.",
    "architectural_features": "Bastion-like facade with round buttresses, Gothic cloister with azulejo tiles, Royal Pantheon with circular vault, chapel of bones (Capela dos Ossos), bell tower.",
    "heritage_status": "UNESCO World Heritage Site (Historic Centre of Évora)",
    "sources": [{"title": "UNESCO World Heritage List - Évora", "url": "https://whc.unesco.org/en/list/786"}]
  },
  {
    "site_id": "porto_vinho",
    "name": "Porto Historic Centre",
    "city": "Porto",
    "country": "Portugal",
    "region": "Southern Europe",
    "type": "Historic City",
    "period": "Roman-19th century CE",
    "description": "Medieval city on the Douro river, famous for Port wine cellars and the iconic Dom Luis I Bridge.",
    "historical_significance": "UNESCO World Heritage Site (1996); one of Europe's oldest cities; birthplace of Port wine trade.",
    "architectural_features": "Livraria Lello bookstore with Neo-Gothic interior, São Bento Station with tile panels, Sé Cathedral fortress, Clérigos Tower, Dom Luis I iron bridge, Ribeira waterfront.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Porto", "url": "https://whc.unesco.org/en/list/779"}]
  },
])

# ── GERMANY (5 entries) ──────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "colosseum_athens",
    "name": "Brandenburg Gate",
    "city": "Berlin",
    "country": "Germany",
    "region": "Central Europe",
    "type": "Monument",
    "period": "1788-1791 CE",
    "description": "Neoclassical monument marking the site of the former Berlin Wall, symbol of German division and reunification.",
    "historical_significance": "Most famous landmark of Germany; symbol of European unity; site of historic moments including WWII liberation and 1989 Wall fall.",
    "architectural_features": "Doric hexastyle colonnade, Quadriga bronze chariot atop, 12 columns forming 5 passageways, Elbe sandstone construction, Peace and Victory allegories.",
    "heritage_status": "National Heritage Monument",
    "sources": [{"title": "German Federal Monuments Office", "url": "https://www.denkmalpflege.de"}]
  },
  {
    "site_id": "neuschwanstein",
    "name": "Neuschwanstein Castle",
    "city": "Schwangau",
    "country": "Germany",
    "region": "Central Europe",
    "type": "Castle",
    "period": "1869-1886 CE",
    "description": "Romantic hill castle commissioned by King Ludwig II, inspiration for Disney's Sleeping Beauty Castle.",
    "historical_significance": "Most visited castle in Germany; symbol of 19th-century Romanticism; influenced castle design worldwide.",
    "architectural_features": "Romanesque Revival towers and facades, Swan Knight Hall with murals, throne room with mosaic, marble bathroom with plumbing, Alpine mountain setting.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Bavarian Palace Department", "url": "https://www.schloesser.bayern.de"}]
  },
  {
    "site_id": "aachen_cathedral",
    "name": "Aachen Cathedral",
    "city": "Aachen",
    "country": "Germany",
    "region": "Central Europe",
    "type": "Cathedral",
    "period": "792-805 CE (Charlemagne's chapel); later Gothic additions",
    "description": "Royal chapel founded by Charlemagne, coronation church of German kings for over 600 years.",
    "historical_significance": "UNESCO World Heritage Site (1978); greatest Carolingian monument; burial place of Charlemagne.",
    "architectural_features": "Octagonal dome with Carolingian mosaics, Palatine Chapel interior, Gothic choir added 1355, imperial throne, Treasury with Reliquary of the Virgin.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Aachen", "url": "https://whc.unesco.org/en/list/43"}]
  },
  {
    "site_id": "musel_island",
    "name": "Museum Island, Berlin",
    "city": "Berlin",
    "country": "Germany",
    "region": "Central Europe",
    "type": "Museum Complex",
    "period": "1830-1930 CE",
    "description": "Group of five world-renowned museums on an island in the Spree River, housing collections spanning millennia.",
    "historical_significance": "UNESCO World Heritage Site (1999); one of the most important museum complexes in the world.",
    "architectural_features": "Pergamon Museum with Ishtar Gate and Market Gate, Altes Museum with neoclassical portico, Neues Museum with Nefertiti bust, Bode Museum with baroque dome, Alte Nationalgalerie.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Berlin", "url": "https://whc.unesco.org/en/list/430"}]
  },
  {
    "site_id": "worms_cathedral",
    "name": "Worms Cathedral (Wormser Dom)",
    "city": "Worms",
    "country": "Germany",
    "region": "Central Europe",
    "type": "Cathedral",
    "period": "1181 CE (main structure); 12th-13th century",
    "description": "Imperial cathedral and burial place of Emperor Henry IV, important Romanesque monument.",
    "historical_significance": "UNESCO World Heritage Site (2021, as part of Medieval Routes of Santiago de Compostela in Germany); key stop on the pilgrimage route.",
    "architectural_features": "Twin west towers with bulbous domes, Romanesque nave with pointed arches, Gothic choir additions, tomb of Emperor Henry IV, vibrant frescoes.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Worms", "url": "https://whc.unesco.org/en/list/1581"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after Portugal + Germany: {len(catalogue)}")