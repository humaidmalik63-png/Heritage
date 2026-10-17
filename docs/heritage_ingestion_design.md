# Global Heritage Ingestion — Design

Scope: how a 155-record hand-curated catalogue becomes a global heritage dataset
without breaking the application, and without touching recognition.

---

## 1. Sources

Only official, public, machine-readable interfaces are used. No search-engine
scraping, no random websites, no invented values.

| Source | Endpoint | Used for |
|---|---|---|
| Wikimedia Commons | `commons.wikimedia.org/w/api.php` | heritage category enumeration, monument → Wikidata mapping, file URLs, **licence + author metadata** |
| Wikidata | `www.wikidata.org/w/api.php` (`wbgetentities`) | labels, descriptions, structured claims: country, coordinates, inception, heritage designation, architectural style, instance-of |

### Why the Commons category tree

`Category:Cultural heritage monuments by country` currently has 130 country
subcategories. Each is walked `Country → by region/province → monument`. This is
the machine-readable face of the Commons monuments database, and it is where
photographs with real licence metadata actually live — Wikidata alone cannot
supply `author`, `license`, `license_url` or `attribution`.

### Why not SPARQL

Wikidata Query Service is the natural way to enumerate heritage sites, and a
cultural-heritage query is included in the design. It was **not** used for this
run because the endpoint was returning `429 Aggressively rate-limiting to
1 req/min` during an active WDQS outage. At 1 request per minute a 100-record
test would take roughly an hour and a full import would be impractical. The
category-walk path is ~0.5 s per request and is unaffected. A SPARQL source can
be added as an additional provider later without changing the schema.

### Country coverage

The country list is **read from the Commons root category**, never hard-coded, so
the architecture imports whatever the source data contains. 130 countries were
resolved in this run.

---

## 2. Data model

`data/metadata/global_monument_catalogue.json` — one object per site:

```
site_id                  stable, generated, unique
name                     English label from Wikidata
alternate_names          other English aliases (verbatim from Wikidata)
country                  normalised country name
country_code             Wikidata country Q-id (stable across renames)
region                   preserved where the hand catalogue had it
city                     preserved where the hand catalogue had it
latitude, longitude      from P625
type                     instance-of labels (P31)
period                   derived from inception (P571)
description              Wikidata English description
historical_significance  preserved where the hand catalogue had it
architectural_features   architectural style (P149)
heritage_status          heritage designation (P1435)
wikidata_id              Q-id, the primary stable identity
commons_id               Commons category title
sources                  [{title, url}] pointing at the source records
images                   image candidate list (below)
```

Image records:

```
local_path        null until an image is actually downloaded
source            "Wikimedia Commons"
source_url        Commons file description page
commons_file_url  upload.wikimedia.org direct URL
author            extmetadata.Artist, HTML stripped
license           canonical licence name, allow-listed
license_url       extmetadata.LicenseUrl
attribution       "<author> / <license>"
view_type         derived heuristic: front|aerial|interior|detail|elevation|other
```

`view_type` is a derived label over API-returned data, not asserted fact.

### Licence policy

A file is only accepted when `LicenseShortName` **and** `LicenseUrl` are both
present and the licence matches an explicit allow-list (CC0, PD, CC BY,
CC BY-SA, GFDL and their versioned variants). Anything unclear is dropped rather
than guessed at. Every accepted image keeps its author, licence, licence URL and
attribution.

### Period derivation

`P571` inception is rendered into readable form, e.g. `+1250` → `1250 CE`,
`+0216` → `3rd century BCE`. The underlying date is not stored, only the derived
label, which is why this is described as derived rather than authoritative.

---

## 3. Storage decision (Phase 4)

**SQLite is canonical. The JSON catalogue is a generated export.**

The decision was made against this project's actual numbers rather than in the
abstract:

- The 155 hand-curated records are 140 KB. At the same per-record size,
  ~100k heritage sites would be roughly **90 MB** in one JSON file — too large to
  ship to a browser, and re-parsed on every page load. The frontend already
  carries a bundled copy of the catalogue, so this scales badly in both
  directions.
- A single JSON file has nowhere to put a **unique constraint**. Deduplicating on
  `wikidata_id` is the central correctness requirement; SQLite enforces it with a
  partial unique index. In JSON, correctness depends entirely on the script being
  run correctly.
- `--resume` becomes a query (`WHERE wikidata_id NOT IN (...)`) rather than
  hand-maintained checkpoint state.

**Why not JSON shards:** shards fix the size problem but not the dedup or resume
problem, and they make the dataset harder to inspect and diff while it is still
small enough to inspect. Sharded *export* is still available as an option, so the
large-file path does not need a redesign later.

**The application contract is unchanged.** `global_monument_catalogue.json` is
generated from the database, so the app reads exactly what it reads today and
never needs to know SQLite exists.

Schema: `sites`, `images`, `ingest_state` (resume checkpoint),
`source_files` (backup provenance).

---

## 4. Deduplication (Phase 5)

Applied in order, first match wins:

1. **Wikidata Q-id** — authoritative. Enforced by a unique index, so it holds
   even under concurrent runs.
2. **`name_key` + `country_slug`** — normalised name paired with country.
   Normalisation strips case, accents and punctuation.
3. **existing `site_id`** — hand-curated records are inserted first, so incoming
   records that duplicate them are detected against the curated set.

### "Springfield" must not collapse

Country is part of the duplicate key, so `Springfield, United States` and
`Springfield, Canada` remain separate records. `site_id` is generated as
`{slugified_name}_{slugified_country}`, which makes same-name-different-country
distinguishable in the identifier itself, not just in the metadata. This was
enforced during development because the naive key `(name)` alone would have
merged them.

---

## 5. Safety

- The existing catalogue is read and inserted **verbatim** — no field is
  rewritten, no record is dropped.
- `global_monument_catalogue.json` is copied to
  `data/metadata/backups/<timestamp>_global_monument_catalogue.json`
  **before** every export that would overwrite it.
- Backups are recorded in the database with their path, size and timestamp.
- `frontend_new/`, `frontend/`, `backend/` and `ml/` are never written to.
- FAISS is never touched; `data/processed/index/` is read-only to this pipeline.
- **No image files are downloaded.** The pipeline reads metadata only.

---

## 6. Operational flags

```
--limit N              stop after N new records (test mode)
--country NAME         restrict to one country
--resume               continue, skipping what is already stored
--categories-per-country N   how many leaf categories to sample per country
--images-per-site N     image candidates per site (default 5)
--no-images            metadata only, skip image discovery
--export-only          regenerate JSON from the database, no network
--min-interval S       API throttle, default 0.15 s
```

---

## 7. Known limitations

- The category walk samples a bounded number of leaf categories per country. A
  full global import needs this bound raised and the run made resumable; the
  design supports both but the scale has not been exercised yet.
- Some Commons categorisation is imperfect upstream — a small number of
  monuments sit in another country's heritage tree. The pipeline records what
  the source says rather than second-guessing it.
- `city` and `region` are not populated for ingested records; Commons categories
  are organised by country and administrative area, not by a normalised city
  field. Hand-curated records keep theirs.
- `historical_significance` is not available from the sources used, so ingested
  records leave it null rather than paraphrase a description into it.
- The FAISS index has **not** been rebuilt. The new records are catalogue-only
  until an image download and indexing pass is run deliberately.
