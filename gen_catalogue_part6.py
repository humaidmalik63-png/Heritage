import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── UNITED KINGDOM (6 entries) ───────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "tower_of_london",
    "name": "Tower of London",
    "city": "London",
    "country": "United Kingdom",
    "region": "Northern Europe",
    "type": "Castle",
    "period": "1066-1078 CE",
    "description": "Historic castle on the north bank of the Thames, founded by William the Conqueror, used as palace, prison, armory, and zoo.",
    "historical_significance": "UNESCO World Heritage Site (1988); 900-year history of power, imprisonment, and execution; houses the Crown Jewels.",
    "architectural_features": "White Tower with corner towers, inner and outer wards, Bloody Tower, Traitor's Gate water entrance, medieval armory displays, ravens keeping tradition.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Tower of London", "url": "https://whc.unesco.org/en/list/422"}]
  },
  {
    "site_id": "westminster_abbey",
    "name": "Westminster Abbey",
    "city": "London",
    "country": "United Kingdom",
    "region": "Northern Europe",
    "type": "Abbey",
    "period": "960 CE origins; 1245-1517 CE current Gothic structure",
    "description": "Gothic abbey church where coronations, weddings, and burials of British monarchs have taken place for nearly 1,000 years.",
    "historical_significance": "UNESCO World Heritage Site (1987); site of every coronation since 1066; Poets' Corner honors literary giants.",
    "architectural_features": "Rayonnant Gothic facade with twin towers, Henry VII Chapel with fan vaulting, Norman crypt, rose windows, stone screen choir stalls, tombs of kings and queens.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Westminster Abbey", "url": "https://whc.unesco.org/en/list/388"}]
  },
  {
    "site_id": "stonehenge",
    "name": "Stonehenge",
    "city": "Amesbury",
    "country": "United Kingdom",
    "region": "Northern Europe",
    "type": "Stone Circle",
    "period": "3000-2000 BCE",
    "description": "Prehistoric stone circle monument consisting of massive standing stones arranged in a circular setting.",
    "historical_significance": "UNESCO World Heritage Site (1986); most famous prehistoric monument in the world; aligns with summer solstice sunrise.",
    "architectural_features": "Sarsen stones up to 7m tall weighing 25-50 tonnes, bluestones from Wales, trilithon horseshoes, heel stone, ancient earthwork enclosure.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Stonehenge", "url": "https://whc.unesco.org/en/list/373"}]
  },
  {
    "site_id": "edinburgh_castle",
    "name": "Edinburgh Castle",
    "city": "Edinburgh",
    "country": "United Kingdom",
    "region": "Northern Europe",
    "type": "Castle",
    "period": "12th century CE (on volcanic rock since 850 CE)",
    "description": "Historic fortress dominating Edinburgh's skyline from Castle Rock, seat of Scottish royalty for centuries.",
    "historical_significance": "One of most important historic sites in Scotland; contains the Scottish Crown Jewels and Stone of Destiny.",
    "architectural_features": "Volcanic crag and tail formation, Great Hall, St Margaret's Chapel (oldest building), Castle guns firing daily, Royal Palace interiors, National War Museum.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Historic Environment Scotland", "url": "https://www.historicenvironment.scot"}]
  },
  {
    "site_id": "canterbury_cathedral",
    "name": "Canterbury Cathedral",
    "city": "Canterbury",
    "country": "United Kingdom",
    "region": "Northern Europe",
    "type": "Cathedral",
    "period": "597 CE origins; 1174-1250 CE Gothic reconstruction",
    "description": "One of the oldest and most famous Christian structures in England, seat of the Archbishop of Canterbury.",
    "historical_significance": "UNESCO World Heritage Site (1988); center of Christianity in England for 1,400+ years; martyrdom of Thomas Becket in 1170.",
    "architectural_features": "Tudor bell tower, Gothic nave with flying buttresses, Trinity Chapel with Becket's tomb, chapter house, cloister gardens, stained glass from 12th century.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Canterbury", "url": "https://whc.unesco.org/en/list/465"}]
  },
  {
    "site_id": "buckingham_palace",
    "name": "Buckingham Palace",
    "city": "London",
    "country": "United Kingdom",
    "region": "Northern Europe",
    "type": "Palace",
    "period": "1703 CE; rebuilt 1820-1837",
    "description": "London residence and administrative headquarters of the British monarch, symbol of the British monarchy worldwide.",
    "historical_significance": "Official royal residence since 1837; site of state occasions and diplomatic receptions; iconic symbol of British sovereignty.",
    "architectural_features": "White Portland stone facade, central balustraded terrace, 775 rooms including Ballroom and Long Gallery, garden lake, iron railings and gates.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Royal Collection Trust", "url": "https://www.royal.uk"}]
  },
])

# ── SPAIN (6 entries) ────────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "alhambra_granada",
    "name": "Alhambra Palace",
    "city": "Granada",
    "country": "Spain",
    "region": "Southern Europe",
    "type": "Palace-Fortress",
    "period": "1238-1358 CE",
    "description": "Stunning palace and fortress complex showcasing the finest Islamic architecture in Western Europe.",
    "historical_significance": "UNESCO World Heritage Site (1984); last great monument of Islamic Spain; masterpiece of Nasrid architecture.",
    "architectural_features": "Court of the Lions with marble fountain, Hall of the Abencerrajes geometric dome, Generalife gardens with water channels, stucco arabesques, muqarnas honeycomb vaulting.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Alhambra", "url": "https://whc.unesco.org/en/list/298"}]
  },
  {
    "site_id": "sagrada_familia",
    "name": "Sagrada Familia",
    "city": "Barcelona",
    "country": "Spain",
    "region": "Southern Europe",
    "type": "Basilica",
    "period": "1882-present (ongoing)",
    "description": "Antoni Gaudi's unfinished masterpiece, the largest unfinished Catholic church in the world, iconic symbol of Barcelona.",
    "historical_significance": "UNESCO World Heritage Site (2005); Gaudi's life work spanning 43 years; unique synthesis of Gothic and Art Nouveau forms.",
    "architectural_features": "Three elaborate facades (Nativity, Passion, Glory), 18 spires representing biblical figures, forest-like interior columns, stained glass creating rainbow light, intricate stone carvings.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Works of Gaudi", "url": "https://whc.unesco.org/en/list/320"}]
  },
  {
    "site_id": "alhambra_madrid",
    "name": "Royal Palace of Madrid (Palacio Real)",
    "city": "Madrid",
    "country": "Spain",
    "region": "Southern Europe",
    "type": "Palace",
    "period": "1738-1764 CE",
    "description": "Largest royal palace in Western Europe, official residence of the Spanish royal family (used for state ceremonies only).",
    "historical_significance": "Largest operating royal palace in Europe by floor area; symbol of Spanish Bourbon monarchy.",
    "architectural_features": "Baroque-Classicist facade with 3,000 rooms, Royal Armory with historic weapons, Throne Room with Murillo painting, Sabatini Gardens, celestial dome ceiling.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Spanish Royal Household", "url": "https://www.casareal.es"}]
  },
  {
    "site_id": "mezquita_cordoba",
    "name": "Mezquita-Catedral of Cordoba",
    "city": "Cordoba",
    "country": "Spain",
    "region": "Southern Europe",
    "type": "Mosque-Cathedral",
    "period": "784-987 CE (mosque); 1236 CE (cathedral conversion)",
    "description": "Monumental mosque-cathedral blending Islamic and Christian architecture, once the largest in the world.",
    "historical_significance": "UNESCO World Heritage Site (1984); symbol of convivencia between Muslim and Christian cultures; masterpiece of Moorish architecture.",
    "architectural_features": "Forest of double-deck red-and-white arches,Mihrab prayer niche with golden mosaics, Renaissance cathedral nave inserted inside, bell tower from minaret, Courtyard of Orange Trees.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Cordoba", "url": "https://whc.unesco.org/en/list/293"}]
  },
  {
    "site_id": "santiago_cathedral",
    "name": "Santiago de Compostela Cathedral",
    "city": "Santiago de Compostela",
    "country": "Spain",
    "region": "Southern Europe",
    "type": "Cathedral",
    "period": "1075-1211 CE",
    "description": "Roman Catholic cathedral and endpoint of the Camino de Santiago pilgrimage route, reputed burial site of Saint James.",
    "historical_significance": "UNESCO World Heritage Site (1985); one of Christianity's three great pilgrimage sites alongside Rome and Jerusalem.",
    "architectural_features": "Baroque Facade of Glory, Pantleon (rose window), Plateresque cloister, silver censer Botafumeiro swinging at 68 km/h, Romanesque porticoes with sculpted figures.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Santiago de Compostela", "url": "https://whc.unesco.org/en/list/347"}]
  },
  {
    "site_id": "guggenheim_bilbao",
    "name": "Guggenheim Museum Bilbao",
    "city": "Bilbao",
    "country": "Spain",
    "region": "Southern Europe",
    "type": "Museum",
    "period": "1997 CE",
    "description": "Iconic contemporary museum building by Frank Gehry, transformed Bilbao from industrial decline to cultural tourism destination.",
    "historical_significance": "Pioneered the 'Bilbao Effect' - using architecture to revitalize cities; titanium-clad curves rival any historic monument.",
    "architectural_features": "Titanium and limestone curves, glass atrium spiraling 50m, undulating forms reflecting river light, spiral galleries, urban plaza with 'Puppy' sculpture.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Guggenheim Bilbao", "url": "https://www.guggenheim-bilbao.eus"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after UK + Spain: {len(catalogue)}")