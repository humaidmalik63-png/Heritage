import json

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "r", encoding="utf-8") as f:
    catalogue = json.load(f)

# ── TURKEY (additional 2 entries to complete) ───────────────────────────
catalogue.extend([
  {
    "site_id": "hagia_irini_istanbul",
    "name": "Hagia Eirene (Church of Peace)",
    "city": "Istanbul",
    "country": "Turkey",
    "region": "Western Asia",
    "type": "Church",
    "period": "5th century CE",
    "description": "Byzantine church in the Topkapi Palace grounds, one of the few Constantinople churches not converted to a mosque.",
    "historical_significance": "Oldest church in Istanbul still standing; used as imperial treasury after Ottoman conquest.",
    "architectural_features": "Basilica plan with three naves, massive dome on pendentives, brick construction with stone bands, original marble floor, apse with mosaic fragments.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Topkapi Palace Museums", "url": "https://www.topkapisarayi.gov.tr"}]
  },
  {
    "site_id": "troia_hisarlik_turkey",
    "name": "Troy (Hisarlik)",
    "city": "Canakkale",
    "country": "Turkey",
    "region": "Western Asia",
    "type": "Archaeological Site",
    "period": "3000-800 BCE",
    "description": "Legendary city of the Trojan War, excavated by Heinrich Schliemann, one of the most important archaeological sites in the world.",
    "historical_significance": "UNESCO World Heritage Site (1998); subject of Homer's Iliad; evidence of 9 layers of civilization.",
    "architectural_features": "Circular tower (Scheil Tower), defensive walls with gate openings, multi-layered ruins showing successive cities, wooden reconstruction of Trojan Horse gate.",
    "heritage_status": "UNESCO World Heritage Site",
    "sources": [{"title": "UNESCO World Heritage List - Troy", "url": "https://whc.unesco.org/en/list/881"}]
  },
])

# ── INDIA (additional 3 entries) ─────────────────────────────────────────
catalogue.extend([
  {
    "site_id": "gorakhpur_temple_hawa",
    "name": "Sun Temple, Modhera",
    "city": "Modhera",
    "country": "India",
    "region": "South Asia",
    "type": "Temple",
    "period": "1026-1027 CE",
    "description": "A Hindu temple dedicated to the sun god Surya, aligned so that first rays illuminate the inner sanctum on spring and summer equinoxes.",
    "historical_significance": "Exquisite example of Solanki architecture; known for its elaborate sculptural decoration and innovative orientation.",
    "architectural_features": "Surya Kund stepped reservoir, matha (temple hall) with carved pillars, exquisitely carved walls depicting daily life and mythology, ornate doorway with decorative arch.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Archaeological Survey of India - Modhera Sun Temple", "url": "https://asi.nic.in/monuments/modhera.asp"}]
  },
  {
    "site_id": "tughlaqabad_fort",
    "name": "Tughlaqabad Fort",
    "city": "New Delhi",
    "country": "India",
    "region": "South Asia",
    "type": "Fort",
    "period": "1321 CE",
    "description": "Ruined fort built by Ghiyas-ud-din Tughlaq, the first ruler of the Tughlaq dynasty, known for its massive walls and strategic location.",
    "historical_significance": "Demonstrates military architecture of the early Delhi Sultanate; notable for its massive ramparts and commanding position.",
    "architectural_features": "Rubble masonry walls, irregular bastions, narrow winding passages, ruined gateways, watchtowers, austere defensive design.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Archaeological Survey of India - Tughlaqabad", "url": "https://asi.nic.in/monuments/tughlaqabad.asp"}]
  },
  {
    "site_id": "ferozshah_fort",
    "name": "Feroz Shah Kotla",
    "city": "Delhi",
    "country": "India",
    "region": "South Asia",
    "type": "Fort",
    "period": "1354 CE",
    "description": "Fortress built by Feroz Shah Tughlaq, featuring the imposing Ashoka Pillar brought from Meerut.",
    "historical_significance": "Important monument of the Tughlaq period; showcases the reuse of ancient pillars in Islamic architecture.",
    "architectural_features": "Ashoka Pillar with Brahmi inscriptions, octagonal tomb of Feroz Shah, mosque with arched entrances, reservoir ( Hauz Khas), massive stone walls.",
    "heritage_status": "National Heritage Site",
    "sources": [{"title": "Archaeological Survey of India - Feroz Shah Kotla", "url": "https://asi.nic.in/monuments/ferozshah-kotla.asp"}]
  },
])

with open(r"C:\Users\humai\AI\data\metadata\global_monument_catalogue.json", "w", encoding="utf-8") as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)
print(f"Total entries after additions: {len(catalogue)}")