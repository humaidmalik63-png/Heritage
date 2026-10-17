import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── FRANCE (6 entries) ───────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "eiffel_tower",
    "name": "Eiffel Tower (Tour Eiffel)",
    "city": "Paris",
    "country": "France",
    "region": "Western Europe",
    "type": "Tower",
    "period": "1887-1889 CE",
    "description": "Iron lattice tower on the Champ de Mars, built as the entrance arch for the 1889 World's Fair.",
    "historical_significance": "Most-visited paid monument in the world; symbol of France and engineering achievement of the Industrial Age.",
    "architectural_features": "330m wrought-iron lattice structure, three levels with restaurants, 18,038 metallic components, 2.5 million rivets, four arched legs at base.",
    "heritage_status": "Part of UNESCO World Heritage Site (Paris, Banks of the Seine)",
    "sources": [{"title": "UNESCO World Heritage List - Paris", "url": "https://whc.unesco.org/en/list/609"}]
  },
  {
    "site_id": "versailles_palace",
    "name": "Palace of Versailles",
    "city": "Versailles",
    "country": "France",
    "region": "Western Europe",
    "type": "Palace",
    "period": "1661-1710 CE",
    "description": "Royal château and capital of the French monarchy from Louis XIV to the French Revolution, one of the grandest palaces in the world.",
    "historical_significance": "UNESCO World Heritage Site (1979); seat of absolute monarchy; signed the Treaty of Versailles ending WWI in the Hall of Mirrors.",
    "architectural_features": "Hall of Mirrors with 357 mirrors, Royal Chapel with twin towers, Gardens by Le Notre with 150 fountains, marble courtyards, Queen's Hamlet.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Palace of Versailles", "url": "https://whc.unesco.org/en/list/884"}]
  },
  {
    "site_id": "mont_saint_michel",
    "name": "Mont Saint-Michel",
    "city": "Mont-Saint-Michel",
    "country": "France",
    "region": "Western Europe",
    "type": "Abbey",
    "period": "966-1874 CE",
    "description": "Tide-swept island commune crowned by a medieval abbey, one of the most recognizable landmarks in France.",
    "historical_significance": "UNESCO World Heritage Site (1979); masterpiece of Gothic architecture; pilgrimage site since 708 CE.",
    "architectural_features": "Gothic abbey with flying buttresses, Romanesque crypt, steep cobbled streets, fortified ramparts, tidal flats surrounding the rock, spire with archangel Michael statue.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Mont Saint-Michel", "url": "https://whc.unesco.org/en/list/785"}]
  },
  {
    "site_id": "chartres_cathedral",
    "name": "Chartres Cathedral",
    "city": "Chartres",
    "country": "France",
    "region": "Western Europe",
    "type": "Cathedral",
    "period": "1194-1250 CE",
    "description": "Highpoint of French Gothic architecture, famous for its intact medieval stained-glass windows and labyrinth.",
    "historical_significance": "UNESCO World Heritage Site (1979); contains 174 original 12th-13th century stained glass windows; major medieval pilgrimage destination.",
    "architectural_features": "Twin west towers of different styles, Rose windows with deep blue 'Chartres blue', nave vaulting at 37m, stone labyrinth on floor, pyramidal spires.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Chartres Cathedral", "url": "https://whc.unesco.org/en/list/882"}]
  },
  {
    "site_id": "loire_valley",
    "name": "Loire Valley Chateaux",
    "city": "Tours",
    "country": "France",
    "region": "Western Europe",
    "type": "Chateau Complex",
    "period": "15th-17th century CE",
    "description": "Concentration of historic chateaux along the Loire River, representing the pinnacle of French Renaissance architecture.",
    "historical_significance": "UNESCO World Heritage Site (2000); cultural landscape showcasing the Renaissance revival of classical ideals in architecture and garden design.",
    "architectural_features": "Chateau de Chambord with double-helix staircase, Chateau de Chenonceau spanning the river, Chateau de Amboise with Leonardo's tomb, formal French gardens.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Loire Valley", "url": "https://whc.unesco.org/en/list/885"}]
  },
  {
    "site_id": "le_partenon_paris",
    "name": "Pantheon, Paris",
    "city": "Paris",
    "country": "France",
    "region": "Western Europe",
    "type": "Mausoleum",
    "period": "1758-1790 CE",
    "description": "Neoclassical monument in the Latin Quarter, originally a church dedicated to St Genevieve, now a mausoleum for distinguished French citizens.",
    "historical_significance": "Final resting place of Voltaire, Rousseau, Hugo, Zola, and Curie; symbol of French secularism and republican values.",
    "architectural_features": "Greek-cross plan with massive Corinthian portico, 83m dome with coffered interior, Foucault's pendulum suspension point, oculus with bronze grating.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Centre des Monuments Nationaux", "url": "https://www.culture.fr/pantheon"}]
  },
])

# ── GREECE (6 entries) ───────────────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "parthenon",
    "name": "Parthenon",
    "city": "Athens",
    "country": "Greece",
    "region": "Southern Europe",
    "type": "Temple",
    "period": "447-432 BCE",
    "description": "Former temple to the goddess Athena, crowning the Acropolis of Athens and the defining symbol of Classical Greece and Western civilization.",
    "historical_significance": "UNESCO World Heritage Site (1987); greatest monument of Classical Greece; epitome of Doric architecture.",
    "architectural_features": "Octastyle peripteral Doric temple, 8x17 column arrangement, subtle entasis curves, pedimental sculptures, contiguous Ionic frieze, marble construction.",
    "heritage_status": "UNESCO World Heritage Site (Acropolis of Athens)",
    "sources": [{"title": "UNESCO World Heritage List - Acropolis of Athens", "url": "https://whc.unesco.org/en/list/404"}]
  },
  {
    "site_id": "acropolis_athens",
    "name": "Acropolis of Athens",
    "city": "Athens",
    "country": "Greece",
    "region": "Southern Europe",
    "type": "Fortified Citadel",
    "period": "5th century BCE",
    "description": "Ancient citadel located on a rocky outcrop above Athens, containing the remains of several historically significant buildings.",
    "historical_significance": "UNESCO World Heritage Site (1987); symbol of ancient Greek democracy and civilization.",
    "architectural_features": "Propylaea monumental entrance, Temple of Athena Nike, Erechtheion with Caryatid porch, Parthenon, ancient fortification walls, theater of Dionysus below.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Acropolis of Athens", "url": "https://whc.unesco.org/en/list/404"}]
  },
  {
    "site_id": "epidauros_theatre",
    "name": "Ancient Theatre of Epidaurus",
    "city": "Epidaurus",
    "country": "Greece",
    "region": "Southern Europe",
    "type": "Theatre",
    "period": "4th century BCE (4th-3rd century BCE)",
    "description": "Ancient theatre with exceptionally well-preserved stage building and legendary acoustics, still used for performances today.",
    "historical_significance": "UNESCO World Heritage Site (1988); considered the most perfect ancient Greek theatre; attributed to architect Polykleitos the Younger.",
    "architectural_features": "Semi-circular orchestra, 55 tiers of marble seats holding 14,000 spectators, symmetrical tier arrangement, excellent acoustics allowing whisper to carry to top row.",
    "heritage_status": "UNESCO World Heritage Site (Ancient Epidaurus)",
    "sources": [{"title": "UNESCO World Heritage List - Ancient Epidaurus", "url": "https://whc.unesco.org/en/list/451"}]
  },
  {
    "site_id": "delphi_sanctuary",
    "name": "Sanctuary of Apollo at Delphi",
    "city": "Delphi",
    "country": "Greece",
    "region": "Southern Europe",
    "type": "Sanctuary",
    "period": "8th century BCE-4th century CE",
    "description": "Ancient sanctuary dedicated to Apollo, home of the famous Oracle of Delphi, considered the navel (omphalos) of the ancient world.",
    "historical_significance": "UNESCO World Heritage Site (1987); most important sanctuary of ancient Greece; consulted by rulers and city-states for centuries.",
    "architectural_features": "Temple of Apollo with Doric columns, Tholos of circular design, stadium for athletic games, Treasury buildings of city-states, sacred spring, amphitheatre.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Delphi", "url": "https://whc.unesco.org/en/list/454"}]
  },
  {
    "site_id": "meteoras_monasteries",
    "name": "Meteora Monasteries",
    "city": "Kalambaka",
    "country": "Greece",
    "region": "Southern Europe",
    "type": "Monastery Complex",
    "period": "14th century CE",
    "description": "Eastern Orthodox monasteries built atop enormous natural rock pillars in central Greece, among the most spectacular monastic complexes in the world.",
    "historical_significance": "UNESCO World Heritage Site (1988); second most important Byzantine monastic center after Mount Athos.",
    "architectural_features": "Six large monasteries perched on sandstone columns up to 400m high, fresco-covered churches, stone staircases carved into rock, isolated walkways, defensive walls.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Meteora", "url": "https://whc.unesco.org/en/list/453"}]
  },
  {
    "site_id": "krete_malia",
    "name": "Palace of Knossos",
    "city": "Heraklion",
    "country": "Greece",
    "region": "Southern Europe",
    "type": "Palace Complex",
    "period": "2000-1350 BCE",
    "description": "Largest Bronze Age archaeological site on Crete and regarded as Europe's oldest city, legendary home of King Minos and the Labyrinth.",
    "historical_significance": "UNESCO World Heritage Site (1987, as part of Mycenae and Tiryns - extended to include Knossos); heart of Minoan civilization.",
    "architectural_features": "Multi-story palace complex with drainage systems, vibrant fresco paintings of bull-leaping, Megaron throne room, central courtyard, storage magazines with giant pithoi jars.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Knossos", "url": "https://whc.unesco.org/en/list/375"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after France + Greece: {len(catalogue)}")