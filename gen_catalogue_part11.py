import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── UNITED STATES (4 entries) ────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "statue_liberty",
    "name": "Statue of Liberty",
    "city": "New York",
    "country": "United States",
    "region": "North America",
    "type": "Monument",
    "period": "1886 CE",
    "description": "Colossal neoclassical sculpture on Liberty Island, a gift from France symbolizing freedom and democracy.",
    "historical_significance": "UNESCO World Heritage Site (1984); iconic symbol of America and welcome to millions of immigrants.",
    "architectural_features": "Copper skin (now green patina) over iron framework, tablet inscribed JULY IV MDCCLXXVI, seven-spiked crown representing seven seas/continents, broken chains at feet, torch held aloft.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Statue of Liberty", "url": "https://whc.unesco.org/en/list/376"}]
  },
  {
    "site_id": "gettysburg",
    "name": "Gettysburg National Military Park",
    "city": "Gettysburg",
    "country": "United States",
    "region": "North America",
    "type": "Battlefield",
    "period": "1863 CE (battle); memorial 1869-",
    "description": "Site of the decisive Battle of Gettysburg, the turning point of the American Civil War.",
    "historical_significance": "Most important Civil War battlefield; site of Lincoln's Gettysburg Address; 50,000+ casualties in three days.",
    "architectural_features": "Devil's Den boulders, Little Round Top with rifle trenches, Citadell Avenue with 1,400+ monuments, Soldiers' National Cemetery with Lincoln's tomb, Gettysburg Museum.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "National Park Service - Gettysburg", "url": "https://www.nps.gov/gett"}]
  },
  {
    "site_id": "grand_canyon",
    "name": "Grand Canyon National Park",
    "city": "Grand Canyon",
    "country": "United States",
    "region": "North America",
    "type": "Natural Monument",
    "period": "6 million years of erosion",
    "description": "Steep-sided canyon carved by the Colorado River, one of the largest and most spectacular canyons in the world.",
    "historical_significance": "UNESCO World Heritage Site (1979); natural wonder showcasing 2 billion years of geological history.",
    "architectural_features": "446km long canyon up to 29km wide and 1.8km deep, layered red rock strata, Colorado River at base, viewpoint terraces, ancient petroglyphs.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Grand Canyon", "url": "https://whc.unesco.org/en/list/311"}]
  },
  {
    "site_id": "alcatraz_island",
    "name": "Alcatraz Island",
    "city": "San Francisco",
    "country": "United States",
    "region": "North America",
    "type": "Penitentiary",
    "period": "1861-1963 CE",
    "description": "Island prison in San Francisco Bay, once housing infamous criminals like Al Capone.",
    "historical_significance": "National Heritage Site; symbol of untouchable security; now a popular museum of American criminal history.",
    "architectural_features": "Main penitentiary building with cellblocks, hospital wing, warden's house, execution chamber, radar and searchlight platforms, prison farm ruins.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "National Park Service - Alcatraz", "url": "https://www.nps.gov/alca"}]
  },
])

# ── BRAZIL (4 entries) ───────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "christ_redeemer",
    "name": "Christ the Redeemer (Cristo Redentor)",
    "city": "Rio de Janeiro",
    "country": "Brazil",
    "region": "South America",
    "type": "Monument",
    "period": "1922-1931 CE",
    "description": "Art Deco statue of Jesus Christ with arms outstretched atop Corcovado mountain, most iconic symbol of Brazil.",
    "historical_significance": "New Seven Wonder of the World; most recognizable symbol of Christianity and Rio de Janeiro.",
    "architectural_features": "28m tall statue (38m with pedestal), reinforced concrete and soapstone exterior, Art Deco geometric forms, panoramic views of city, tram railway to summit.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Rio de Janeiro Tourism", "url": "https://www.riodejaneiro.rj.gov.br"}]
  },
  {
    "site_id": "iguazu_falls",
    "name": "Iguazu Falls (Cataratas do Iguaçu)",
    "city": "Foz do Iguaçu",
    "country": "Brazil",
    "region": "South America",
    "type": "Natural Monument",
    "period": "Geological formation",
    "description": "Spectacular waterfall system on the Iguazu River, comprising 275 individual falls over 2.7km width.",
    "historical_significance": "UNESCO World Heritage Site (1986); one of the seven natural wonders of the world; largest waterfall system by volume.",
    "architectural_features": "Devil's Throat (Garganta del Diablo) U-shaped cascade, 150m drop, walkway platforms, subtropical rainforest setting, colorful rainbows in spray.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Iguazu", "url": "https://whc.unesco.org/en/list/776"}]
  },
  {
    "site_id": "oyapock_rio_janeiro",
    "name": "Ouro Preto Historic Town",
    "city": "Ouro Preto",
    "country": "Brazil",
    "region": "South America",
    "type": "Historic Town",
    "period": "17th-18th century CE",
    "description": "Well-preserved colonial mining town, center of the Brazilian Gold Rush, rich in Baroque art and architecture.",
    "historical_significance": "UNESCO World Heritage Site (1980); finest example of Brazilian colonial architecture; birthplace of Brazilian independence movement.",
    "architectural_features": "Church of Saint Francis of Assisi with Aleijadinho sculptures, Santo Ildefonso church with gold leaf interior, cobblestone streets, stepped terrain, baroque cathedrals.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Ouro Preto", "url": "https://whc.unesco.org/en/list/147"}]
  },
  {
    "site_id": "brasilia",
    "name": "Brasília",
    "city": "Brasília",
    "country": "Brazil",
    "region": "South America",
    "type": "Planned Capital",
    "period": "1956-1960 CE",
    "description": "Purpose-built capital city designed by Oscar Niemeyer and Lúcio Costa, masterpiece of modernist urban planning.",
    "historical_significance": "UNESCO World Heritage Site (1987); first planned capital built in the 20th century; audacious modernist experiment.",
    "architectural_features": "Airplane-shaped urban plan, National Congress with twin towers and domes, Cathedral of Brasília with hyperboloid concrete ribs, Palácio da Alvorada, Supreme Court building.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Brasília", "url": "https://whc.unesco.org/en/list/870"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after USA + Brazil: {len(catalogue)}")