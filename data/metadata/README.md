# Global Monument Catalogue

This directory contains the curated metadata for the Heritage Recognition project.

## global_monument_catalogue.json

**This is the authoritative global catalogue of heritage monuments and sites.**

- **Scope:** UNESCO World Heritage Sites, national heritage monuments, and other culturally significant structures spanning multiple continents.
- **Schema:** Each entry follows a standardized format with fields for `site_id`, `name`, `alternate_names`, `country`, `country_code`, `region`, `city`, `latitude`, `longitude`, `type`, `period`, `description`, `historical_significance`, `architectural_features`, `heritage_status`, `wikidata_id`, `commons_id`, `sources`, and `images`.

### Current status

- **The first 155 records are hand-curated** and are preserved verbatim. They carry no `wikidata_id` / `commons_id` / `images` because they predate automated ingestion.
- **Further records are ingested automatically** from the Wikimedia Commons cultural-heritage category tree and Wikidata by
  `scripts/ingest_global_heritage.py`. Those records carry real `wikidata_id`, `commons_id`, coordinates where Wikidata
  has them, and licensed image candidates. Ingested records leave `city`, `region` and `historical_significance` null
  rather than guessing, because the source data does not supply them.
- **Canonical store:** `data/metadata/heritage_catalogue.db` (SQLite). This JSON file is a *generated export* of it — edit
  the database by re-running the ingestion tool, never by hand-editing this file.
- **Backups:** every export that would overwrite this file first copies it to `data/metadata/backups/`.
- **Image candidates:** `data/metadata/global_image_manifest.json`. No image files have been downloaded; `local_path` is
  null until a deliberate download pass runs.
- **The FAISS index has not been rebuilt.** Ingested records are catalogue-only.

See `docs/heritage_ingestion_design.md` for the full design, sources and storage rationale.

### What this catalogue is NOT

- This is **not** the image dataset. Images are collected separately.
- This is **not** used directly by the FAISS index. The FAISS index is built from actual images in `data/raw/`, and the
  backend reads `heritage_metadata.json` and `heritage_evidence.json` — not this file. Recognition is unaffected by
  changes here.
- This catalogue serves as a reference metadata layer for documentation and future evidence enrichment.

### Future phases

1. **Image collection phase:** Each site will receive multiple reference images covering different viewpoints, lighting
   conditions, and seasonal appearances. Licences and attribution are already recorded in the image manifest.
2. **FAISS rebuild:** The FAISS index will be rebuilt only after the image collection phase is complete, using the new
   images from `data/raw/`.
3. **Ollama fallback:** For sites outside this catalogue (or when no local match is found), the system falls back to
   Ollama vision-based identification as a global fallback.
- **Image dataset:** Separate from this catalogue; see `data/raw/` for existing images.

## Other files

- `heritage_metadata.json`: Legacy metadata format (legacy use only).
- `image_manifest.json`: Mapping of images to sites for the FAISS index.
- `.gitkeep`: Ensures the directory is tracked by git even when empty.
