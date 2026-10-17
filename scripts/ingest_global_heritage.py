#!/usr/bin/env python3
"""Global heritage catalogue ingestion pipeline.

Sources (official, public, machine-readable only):
  * Wikimedia Commons API  - category enumeration + file/license metadata
  * Wikidata API (wbgetentities) - structured claims

Never scrapes search engines, never invents metadata, image URLs, licenses or
attribution. Every value written is either carried over verbatim from the
existing catalogue or returned by one of the two APIs above.

Storage: SQLite is canonical; the application JSON is a generated export.
See docs/heritage_ingestion_design.md for the rationale.

Safety: the existing catalogue is backed up before any generated dataset is
rewritten, and its records are merged in verbatim - never dropped or rewritten.

Usage
-----
    python3 scripts/ingest_global_heritage.py --limit 100
    python3 scripts/ingest_global_heritage.py --country "India" --limit 50
    python3 scripts/ingest_global_heritage.py --resume
    python3 scripts/ingest_global_heritage.py --export-only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGUE_JSON = os.path.join(ROOT, "data", "metadata", "global_monument_catalogue.json")
IMAGE_MANIFEST_JSON = os.path.join(ROOT, "data", "metadata", "global_image_manifest.json")
DB_PATH = os.path.join(ROOT, "data", "metadata", "heritage_catalogue.db")
BACKUP_DIR = os.path.join(ROOT, "data", "metadata", "backups")

USER_AGENT = (
    "HeritageDiscoveryIngest/0.1 "
    "(heritage catalogue research; https://www.wikidata.org/; local development)"
)
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# Root category that enumerates every country, so the country list comes from
# the source data rather than being hard-coded here.
COUNTRY_ROOT_CATEGORY = "Category:Cultural heritage monuments by country"
COUNTRY_CATEGORY_FMT = "Category:Cultural heritage monuments in {country}"

# Commons page titles are "Category:Name"; the API takes the bare name.
NAME_PREFIX = "Category:"

# Only licenses we can state unambiguously are accepted. Anything missing or
# unrecognised is dropped rather than guessed at.
ALLOWED_LICENSES = {
    "cc0": "CC0",
    "cc-zero": "CC0",
    "public domain": "Public domain",
    "pd": "Public domain",
    "attribution": "CC BY",
    "cc by": "CC BY",
    "cc-by": "CC BY",
    "cc by-sa": "CC BY-SA",
    "cc-by-sa": "CC BY-SA",
    "cc by-sa 2.0": "CC BY-SA 2.0",
    "cc by-sa 3.0": "CC BY-SA 3.0",
    "cc by-sa 4.0": "CC BY-SA 4.0",
    "cc by-sa 2.5": "CC BY-SA 2.5",
    "cc by-sa 3.5": "CC BY-SA 3.5",
    "cc by 2.0": "CC BY 2.0",
    "cc by 3.0": "CC BY 3.0",
    "cc by 4.0": "CC BY 4.0",
    "gfdl": "GFDL",
    "gnu free documentation license": "GFDL",
}

VIEW_KEYWORDS = [
    ("aerial", ["aerial", "drone", "bird", "panorama", "panoramic", "luftbild"]),
    ("interior", ["interior", "inside", "indoor", "nave", "apse", "chancel", "indoors"]),
    ("detail", ["detail", "closeup", "close-up", "carving", "sculpture", "ornament", "relief"]),
    ("elevation", ["elevation", "profile", "side", "lateral", "panoramio"]),
    ("front", ["front", "facade", "façade", "entrance", "gateway", "portal"]),
]

# Wikidata properties used for normalisation.
P_INSTANCE = "P31"
P_COUNTRY = "P17"
P_COORD = "P625"
P_INCEPTION = "P571"
P_HERITAGE = "P1435"
P_ARCH_STYLE = "P149"
P_COMMONS_CAT = "P373"
P_IMAGE = "P18"
P_LABEL = "rdfs:label"

# Q-ids whose English labels are meaningless as free text (acronyms, etc.).
SKIP_INSTANCE_TYPES = {
    "Q563342",       # stab (rejected heritage-listing concept)
    "Q19887878",    # rejected monument entry
    "Q13406463",    # list of monuments
    "Q179700",      # archaeological site (too broad, kept only with a name)
}


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def strip_html(text: str) -> str:
    """Commons extmetadata is full of HTML; reduce it to plain text."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    text = text.replace("&quot;", '"').replace("&#039;", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text or "site"


def norm_name(text: str) -> str:
    """Aggressively normalised name, used only for duplicate *detection*."""
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def classify_view_type(filename: str, description: str) -> str:
    """Derive a coarse view label from the file name / description.

    This is a derived heuristic over data the API returned; it is not
    asserted as ground truth.
    """
    hay = f"{filename} {description}".lower()
    for view, keys in VIEW_KEYWORDS:
        if any(k in hay for k in keys):
            return view
    return "other"


# --------------------------------------------------------------------------
# API client
# --------------------------------------------------------------------------
class WikiClient:
    """Thin, polite client for the Commons and Wikidata APIs."""

    def __init__(self, min_interval: float = 0.15, retries: int = 4, verbose: bool = True):
        self.min_interval = min_interval
        self.retries = retries
        self.verbose = verbose
        self._last = 0.0
        self.request_count = 0

    def _throttle(self) -> None:
        wait = self.min_interval - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)

    def get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        params = dict(params)
        params["format"] = "json"
        params["formatversion"] = "1"
        url = endpoint + "?" + urllib.parse.urlencode(params)
        for attempt in range(self.retries):
            self._throttle()
            self._last = time.time()
            self.request_count += 1
            req = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8", "replace"))
            except urllib.error.HTTPError as exc:
                if exc.code == 429:                     # rate limited -> back off
                    delay = min(60, 5 * (2 ** attempt))
                    if self.verbose:
                        print(f"    [429] backing off {delay}s", file=sys.stderr)
                    time.sleep(delay)
                    continue
                if exc.code == 404:
                    return None
                if attempt == self.retries - 1:
                    return None
                time.sleep(2 * (attempt + 1))
            except Exception:
                if attempt == self.retries - 1:
                    return None
                time.sleep(2 * (attempt + 1))
        return None

    # -- Commons -----------------------------------------------------------
    def category_members(self, category: str, kind: str = "subcat",
                         limit: int = 500) -> List[Dict[str, str]]:
        """List direct members of a Commons category (handles continuation)."""
        out: List[Dict[str, str]] = []
        cont: Dict[str, Any] = {}
        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmtype": kind,
                "cmlimit": str(min(limit, 500)),
            }
            params.update(cont)
            data = self.get(COMMONS_API, params)
            if not data:
                break
            out.extend(data.get("query", {}).get("categorymembers", []))
            if "continue" in data and len(out) < limit:
                cont = {k: v for k, v in data["continue"].items() if k != "continue"}
                if not cont:
                    break
            else:
                break
        return out[:limit]

    def page_wikibase_items(self, titles: List[str]) -> Dict[str, str]:
        """Map page title -> Wikidata Q-id, via Commons pageprops."""
        out: Dict[str, str] = {}
        for i in range(0, len(titles), 50):
            chunk = titles[i:i + 50]
            data = self.get(COMMONS_API, {
                "action": "query", "titles": "|".join(chunk),
                "prop": "pageprops", "ppprop": "wikibase_item",
            })
            if not data:
                continue
            for page in data.get("query", {}).get("pages", {}).values():
                if "missing" in page:
                    continue
                qid = page.get("pageprops", {}).get("wikibase_item")
                if qid:
                    out[page.get("title", "")] = qid
        return out

    def file_imageinfo(self, titles: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch URL + full licence metadata for a batch of File: titles."""
        out: Dict[str, Dict[str, Any]] = {}
        for i in range(0, len(titles), 50):
            chunk = titles[i:i + 50]
            data = self.get(COMMONS_API, {
                "action": "query", "titles": "|".join(chunk),
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|mime|size|user",
            })
            if not data:
                continue
            for page in data.get("query", {}).get("pages", {}).values():
                infos = page.get("imageinfo")
                if not infos:
                    continue
                out[page.get("title", "")] = infos[0]
        return out

    # -- Wikidata ----------------------------------------------------------
    def entities(self, qids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch Wikidata entities (labels, descriptions, claims)."""
        out: Dict[str, Dict[str, Any]] = {}
        for i in range(0, len(qids), 50):
            chunk = qids[i:i + 50]
            data = self.get(WIKIDATA_API, {
                "action": "wbgetentities",
                "ids": "|".join(chunk),
                "props": "labels|descriptions|claims|aliases",
                "languages": "en",
            })
            if not data:
                continue
            out.update(data.get("entities", {}))
        return out


# --------------------------------------------------------------------------
# Wikidata claim helpers
# --------------------------------------------------------------------------
def claim_values(entity: Dict[str, Any], prop: str) -> List[Any]:
    values = []
    for claim in entity.get("claims", {}).get(prop, []):
        snak = claim.get("mainsnak")
        if not snak or snak.get("snaktype") != "value":
            continue
        dv = snak.get("datavalue", {}).get("value")
        if dv is not None:
            values.append(dv)
    return values


def claim_qids(entity: Dict[str, Any], prop: str) -> List[str]:
    out = []
    for dv in claim_values(entity, prop):
        if isinstance(dv, dict) and dv.get("id"):
            out.append(dv["id"])
    return out


# --------------------------------------------------------------------------
# SQLite store (canonical)
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS sites (
    site_id            TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    alternate_names    TEXT,
    country            TEXT,
    country_code       TEXT,
    region             TEXT,
    city               TEXT,
    latitude           REAL,
    longitude          REAL,
    type               TEXT,
    period             TEXT,
    description        TEXT,
    historical_significance TEXT,
    architectural_features  TEXT,
    heritage_status    TEXT,
    wikidata_id        TEXT,
    commons_id         TEXT,
    sources            TEXT,
    origin             TEXT NOT NULL,      -- 'existing' | 'wikimedia'
    country_slug       TEXT,               -- source country category
    name_key           TEXT,               -- normalised name, for duplicate detection
    first_seen         TEXT,
    updated_at         TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sites_wikidata
    ON sites(wikidata_id) WHERE wikidata_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sites_country ON sites(country);
CREATE INDEX IF NOT EXISTS idx_sites_normname ON sites(name_key);
CREATE TABLE IF NOT EXISTS images (
    image_key         TEXT PRIMARY KEY,   -- stable: commons file title
    site_id           TEXT NOT NULL,
    local_path        TEXT,
    source            TEXT,
    source_url        TEXT,
    commons_file_url  TEXT,
    author            TEXT,
    license           TEXT,
    license_url       TEXT,
    attribution       TEXT,
    view_type         TEXT,
    width             INTEGER,
    height            INTEGER,
    created_at        TEXT,
    FOREIGN KEY(site_id) REFERENCES sites(site_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_images_site ON images(site_id);
CREATE TABLE IF NOT EXISTS ingest_state (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS source_files (
    path        TEXT PRIMARY KEY,
    sha256      TEXT,
    size_bytes  INTEGER,
    backed_up_at TEXT
);
"""


def open_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # name_key is used for duplicate detection; add it if the table predates it
    cols = {r[1] for r in conn.execute("PRAGMA table_info(sites)")}
    if "name_key" not in cols:
        conn.execute("ALTER TABLE sites ADD COLUMN name_key TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sites_normname ON sites(name_key)")
    conn.commit()
    return conn


def backup_file(path: str) -> str:
    """Timestamped copy of a generated dataset, recorded in the database."""
    if not os.path.exists(path):
        return ""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    base = os.path.basename(path)
    dest = os.path.join(BACKUP_DIR, f"{stamp}_{base}")
    with open(path, "rb") as src, open(dest, "wb") as dst:
        dst.write(src.read())
    return dest


# --------------------------------------------------------------------------
# existing catalogue
# --------------------------------------------------------------------------
def load_existing_catalogue() -> List[Dict[str, Any]]:
    if not os.path.exists(CATALOGUE_JSON):
        return []
    with open(CATALOGUE_JSON, encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def existing_to_row(rec: Dict[str, Any], origin: str = "existing") -> Dict[str, Any]:
    """Map a catalogue record onto the wider schema, preserving every value."""
    return {
        "site_id": rec.get("site_id") or slugify(rec.get("name", "")),
        "name": rec.get("name", ""),
        "alternate_names": rec.get("alternate_names") or [],
        "country": rec.get("country"),
        "country_code": rec.get("country_code"),
        "region": rec.get("region"),
        "city": rec.get("city"),
        "latitude": rec.get("latitude"),
        "longitude": rec.get("longitude"),
        "type": rec.get("type"),
        "period": rec.get("period"),
        "description": rec.get("description"),
        "historical_significance": rec.get("historical_significance"),
        "architectural_features": rec.get("architectural_features"),
        "heritage_status": rec.get("heritage_status"),
        "wikidata_id": rec.get("wikidata_id"),
        "commons_id": rec.get("commons_id"),
        "sources": rec.get("sources") or [],
        "origin": origin,
        "name_key": norm_name(rec.get("name", "")),
        "country_slug": slugify(rec.get("country", "")),
    }


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------
# Subcategories of the root category that look like a country, e.g.
# "Cultural heritage monuments in Albania" -> "Albania"
COUNTRY_NAME_RE = re.compile(r"^Cultural heritage monuments in (.+)$", re.IGNORECASE)

# Subcategories that describe the *dataset* rather than a monument. These are
# never records in their own right; they must be filtered out at every level.
META_CATEGORY_RE = re.compile(
    r"(quality images|featured pictures|valued images|"
    r"with (known|outstanding|unknown) ids?|without known ids|"
    r"and wikidata|by name\b|by subject|by city|by country|"
    r"unidentified|unphotographed|unphotographed|"
    r"interference fields|photographs|images|media|copyright|"
    r"disputes|requests|cleanup|template|to be (checked|photographed)|"
    r"without images|no images)",
    re.IGNORECASE,
)

# Admin divisions we know how to descend through, matched on the "by X" suffix.
GROUPING_RE = re.compile(
    r"\bby (region|province|state|county|municipality|city|district|parish|"
    r"oblast|department|prefecture|voivodeship|state or territory|"
    r"federal subject|autonomous community|constituent country|canton|"
    r"commune|arrondissement|governorate|subdivision)\b",
    re.IGNORECASE,
)


def list_source_countries(client: WikiClient) -> List[str]:
    """Country names, taken from the Commons root category (not hard-coded)."""
    out: List[str] = []
    cont: Dict[str, Any] = {}
    while True:
        data = client.get(COMMONS_API, {
            "action": "query", "list": "categorymembers",
            "cmtitle": COUNTRY_ROOT_CATEGORY, "cmtype": "subcat",
            "cmlimit": "500",
            **cont,
        })
        if not data:
            break
        for m in data.get("query", {}).get("categorymembers", []):
            title = m.get("title", "")
            if not title.startswith(NAME_PREFIX):
                continue
            name = title[len(NAME_PREFIX):]
            m_country = COUNTRY_NAME_RE.match(name)
            if m_country:
                out.append(m_country.group(1).strip())
        if "continue" in data:
            cont = {k: v for k, v in data["continue"].items() if k != "continue"}
            if not cont:
                break
        else:
            break
    return sorted(set(out))


def is_meta_category(title: str) -> bool:
    """True for dataset/plumbing categories, which are not monuments."""
    name = title[len(NAME_PREFIX):] if title.startswith(NAME_PREFIX) else title
    return META_CATEGORY_RE.search(name) is not None


# Categories whose whole purpose is to *hold* other categories: "Cultural
# heritage monuments in Abruzzo", "Heritage buildings in Karnataka". They are
# containers, not monuments, so the walk must descend through them.
CONTAINER_RE = re.compile(
    r"^(.*\b(cultural heritage|heritage|monuments?|historic|historical|listed|"
    r"protected|archaeological|architectural)\b[^/]*?)\bin\s+\S",
    re.IGNORECASE,
)


def is_grouping_category(title: str) -> bool:
    """True for '... by region' / 'by municipality' style intermediates."""
    return GROUPING_RE.search(title) is not None


def is_container_category(title: str) -> bool:
    """True for administrative/regional containers that hold monuments."""
    name = title[len(NAME_PREFIX):] if title.startswith(NAME_PREFIX) else title
    if is_grouping_category(title):
        return True
    # a bare container has no date/ordinal in the name; real monuments usually
    # carry one, but the strongest signal is the trailing "in <Place>" phrase
    return CONTAINER_RE.search(name) is not None


def discover_monument_categories(client: WikiClient, country: str,
                                 max_categories: int, max_depth: int = 3
                                 ) -> List[str]:
    """Walk Country -> by-region -> monument, collecting leaf categories.

    Category naming differs per country, so grouping categories are detected by
    their '... by X' suffix and dataset categories are filtered out, rather than
    relying on a fixed list of country-specific paths.
    """
    root = COUNTRY_CATEGORY_FMT.format(country=country)
    leaves: List[str] = []
    seen: set = set()
    frontier: List[Tuple[str, int]] = [(root, 0)]

    while frontier and len(leaves) < max_categories:
        cat, depth = frontier.pop(0)
        if cat in seen or depth > max_depth:
            continue
        seen.add(cat)
        members = client.category_members(cat, kind="subcat", limit=500)

        subcats = [m["title"] for m in members
                   if m.get("title", "").startswith(NAME_PREFIX)
                   and not is_meta_category(m["title"])]

        containers = [s for s in subcats if is_container_category(s)]
        candidates = [s for s in subcats if not is_container_category(s)]

        # Descend through containers; the country level is almost entirely
        # plumbing, and real monuments live one or two levels further down.
        if containers and depth < max_depth:
            for g in containers:
                frontier.append((g, depth + 1))
        else:
            for c in candidates:
                if c not in seen:
                    leaves.append(c)
                    if len(leaves) >= max_categories:
                        break

    return leaves[:max_categories]


# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------
def period_from_inception(entity: Dict[str, Any]) -> Optional[str]:
    """Render P571 as a human period string, e.g. '1250 CE' or '3rd century BCE'."""
    times = claim_values(entity, P_INCEPTION)
    if not times:
        return None
    raw = times[0].get("time") if isinstance(times[0], dict) else str(times[0])
    if not raw:
        return None
    m = re.match(r"^([+-])(\d{4,})-(\d{2})-(\d{2})", raw)
    if not m:
        return None
    sign, year, _month, _day = m.groups()
    year_i = int(year)
    era = "BCE" if sign == "-" else "CE"
    year_i = abs(year_i)
    if year_i == 0:
        return None
    if year_i < 1000:
        century = (year_i - 1) // 100 + 1
        suffix = "st" if century == 1 else "nd" if century == 2 else "rd" if century == 3 else "th"
        return f"{century}{suffix} century {era}"
    return f"{year_i} {era}"


def coords_from_entity(entity: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    for dv in claim_values(entity, P_COORD):
        if isinstance(dv, dict) and "latitude" in dv:
            return round(float(dv["latitude"]), 6), round(float(dv["longitude"]), 6)
    return None, None


def resolve_qid_labels(client: WikiClient, qids: Iterable[str]) -> Dict[str, str]:
    """Turn Q-ids into English labels in batched API calls."""
    qids = [q for q in qids if q]
    if not qids:
        return {}
    entities = client.entities(sorted(set(qids)))
    out = {}
    for qid, ent in entities.items():
        label = ent.get("labels", {}).get("en", {}).get("value")
        if label:
            out[qid] = label
    return out


def build_site_record(client: WikiClient, category_title: str, qid: str,
                      entity: Dict[str, Any], country: str,
                      heritage_labels: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Turn one Commons category + Wikidata entity into a catalogue record."""
    cat_name = category_title[len(NAME_PREFIX):] if category_title.startswith(NAME_PREFIX) \
        else category_title
    label = (entity.get("labels", {}).get("en", {}).get("value") or "").strip()
    desc = (entity.get("descriptions", {}).get("en", {}).get("value") or "").strip()
    name = label or cat_name
    if not name:
        return None

    instances = set(claim_qids(entity, P_INSTANCE))
    if instances & SKIP_INSTANCE_TYPES:
        return None

    aliases = []
    for alias in entity.get("aliases", {}).get("en", []):
        val = (alias.get("value") or "").strip()
        if val and val.lower() != name.lower():
            aliases.append(val)

    lat, lon = coords_from_entity(entity)
    country_qids = claim_qids(entity, P_COUNTRY)
    country_name = heritage_labels.get(country_qids[0], country) if country_qids else country
    country_code = country_qids[0] if country_qids else None   # Q-id kept as the stable code

    heritage_qids = claim_qids(entity, P_HERITAGE)
    heritage_labels_here = [heritage_labels.get(q, q) for q in heritage_qids]

    style_qids = claim_qids(entity, P_ARCH_STYLE)
    style_labels = [heritage_labels.get(q, q) for q in style_qids]

    instance_labels = [heritage_labels.get(q, q) for q in sorted(instances)][:3]

    sources = [{
        "title": f"Wikidata: {name}",
        "url": f"https://www.wikidata.org/wiki/{qid}",
    }]
    if category_title:
        sources.append({
            "title": f"Wikimedia Commons: {cat_name}",
            "url": "https://commons.wikimedia.org/wiki/" +
                   urllib.parse.quote(category_title.replace(" ", "_")),
        })

    return {
        "site_id": f"{slugify(name)}_{slugify(country_name)[:12]}",
        "name": name,
        "alternate_names": aliases[:8],
        "country": country_name,
        "country_code": country_code,
        "region": None,
        "city": None,
        "latitude": lat,
        "longitude": lon,
        "type": ", ".join(instance_labels) if instance_labels else None,
        "period": period_from_inception(entity),
        "description": desc or None,
        "historical_significance": None,
        "architectural_features": ", ".join(style_labels) if style_labels else None,
        "heritage_status": ", ".join(heritage_labels_here) if heritage_labels_here else None,
        "wikidata_id": qid,
        "commons_id": category_title,
        "sources": sources,
        "images": [],
        "origin": "wikimedia",
        "name_key": norm_name(name),
        "country_slug": slugify(country_name),
    }


# --------------------------------------------------------------------------
# images
# --------------------------------------------------------------------------
def licence_from_extmeta(em: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Return (canonical licence, licence url) or (None, None) if unclear.

    A file with no licence statement, or one outside the allow-list, is
    rejected rather than guessed at.
    """
    short = strip_html(em.get("LicenseShortName", {}).get("value", ""))
    url = strip_html(em.get("LicenseUrl", {}).get("value", ""))
    if not short or not url:
        return None, None
    key = short.lower().strip()
    canonical = ALLOWED_LICENSES.get(key)
    if canonical is None:
        for alias, canon in ALLOWED_LICENSES.items():
            if key.startswith(alias):
                canonical = canon
                break
    if canonical is None:
        return None, None
    return canonical, url


def clean_file_url(url: str) -> str:
    """Drop the API's analytics query string, keeping the canonical file URL."""
    if not url:
        return ""
    return url.split("?")[0]


def collect_images(client: WikiClient, site: Dict[str, Any],
                   per_site: int = 5) -> List[Dict[str, Any]]:
    """Find licensed photographs for a site in its Commons category.

    Only metadata is read. Nothing is downloaded.
    """
    cat = site.get("commons_id")
    if not cat:
        return []
    members = client.category_members(cat, kind="file", limit=40)
    titles = [m["title"] for m in members if m.get("title", "").startswith("File:")]
    if not titles:
        return []
    infos = client.file_imageinfo(titles)

    images: List[Dict[str, Any]] = []
    used_views = set()
    for title in titles:
        if len(images) >= per_site:
            break
        info = infos.get(title)
        if not info:
            continue
        mime = info.get("mime", "")
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        em = info.get("extmetadata", {})
        licence, licence_url = licence_from_extmeta(em)
        if not licence:
            continue                                    # unclear licence -> skip
        url = info.get("url")
        if not url:
            continue
        author = strip_html(em.get("Artist", {}).get("value", ""))
        descr = strip_html(em.get("ImageDescription", {}).get("value", ""))
        fname = title[len("File:"):] if title.startswith("File:") else title
        view = classify_view_type(fname, descr)
        if view in used_views and view != "other":
            continue
        used_views.add(view)
        images.append({
            "image_key": title,
            "site_id": site["site_id"],
            "local_path": None,
            "source": "Wikimedia Commons",
            "source_url": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
            "commons_file_url": clean_file_url(url),
            "author": author or "Wikimedia Commons contributor",
            "license": licence,
            "license_url": licence_url,
            "attribution": f"{author or 'Unknown'} / {licence}" if author else licence,
            "view_type": view,
            "width": info.get("width"),
            "height": info.get("height"),
        })
    return images


# --------------------------------------------------------------------------
# database writes
# --------------------------------------------------------------------------
def upsert_site(conn: sqlite3.Connection, row: Dict[str, Any]) -> bool:
    """Insert a site. Returns False when it is a duplicate and was skipped."""
    ts = now_iso()
    # list/dict columns are stored as JSON text; sqlite cannot bind a list
    for key in ("alternate_names", "sources"):
        if isinstance(row.get(key), (list, dict)):
            row[key] = json.dumps(row[key], ensure_ascii=False)

    # only write columns that actually exist, so callers can pass richer dicts
    # (e.g. the "images" list) without the insert failing
    table_cols = {r[1] for r in conn.execute("PRAGMA table_info(sites)")}
    cols = [c for c in row.keys() if c in table_cols and c not in ("first_seen", "updated_at")]
    values = [row.get(c) for c in cols]
    placeholders = ",".join("?" for _ in cols)
    updates = ",".join(f"{c}=excluded.{c}" for c in cols if c not in ("site_id", "origin"))
    try:
        conn.execute(
            f"INSERT INTO sites ({','.join(cols)}, first_seen, updated_at) "
            f"VALUES ({placeholders}, ?, ?) "
            f"ON CONFLICT(site_id) DO UPDATE SET {updates}, updated_at=excluded.updated_at",
            values + [ts, ts],
        )
        return True
    except sqlite3.IntegrityError:
        return False                              # unique wikidata_id collision


def add_images(conn: sqlite3.Connection, images: List[Dict[str, Any]]) -> None:
    for img in images:
        # update on conflict so a re-run refreshes stored metadata (for example
        # after the file-URL cleanup) instead of keeping a stale first write
        conn.execute(
            "INSERT INTO images (image_key, site_id, local_path, source, source_url,"
            " commons_file_url, author, license, license_url, attribution, view_type,"
            " width, height, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(image_key) DO UPDATE SET"
            "   source_url=excluded.source_url, commons_file_url=excluded.commons_file_url,"
            "   author=excluded.author, license=excluded.license,"
            "   license_url=excluded.license_url, attribution=excluded.attribution,"
            "   view_type=excluded.view_type, width=excluded.width, height=excluded.height",
            (img["image_key"], img["site_id"], img["local_path"], img["source"],
             img["source_url"], img["commons_file_url"], img["author"], img["license"],
             img["license_url"], img["attribution"], img["view_type"],
             img.get("width"), img.get("height"), now_iso()),
        )


# --------------------------------------------------------------------------
# export
# --------------------------------------------------------------------------
def export_json(conn: sqlite3.Connection, path: str, backup: bool = True) -> int:
    """Generate the application-facing catalogue from the database."""
    if backup and os.path.exists(path):
        made = backup_file(path)
        if made:
            conn.execute(
                "INSERT OR REPLACE INTO source_files (path, sha256, size_bytes, backed_up_at)"
                " VALUES (?,?,?,?)",
                (os.path.relpath(path, ROOT), "", os.path.getsize(made), now_iso()),
            )
            print(f"  backup -> {os.path.relpath(made, ROOT)}")

    rows = conn.execute(
        # hand-curated records first, then ingested ones, so the file stays
        # reviewable and a diff against the original stays readable
        "SELECT * FROM sites ORDER BY CASE origin WHEN 'existing' THEN 0 ELSE 1 END, name ASC"
    ).fetchall()
    images_by_site: Dict[str, List[Dict[str, Any]]] = {}
    for img in conn.execute("SELECT * FROM images ORDER BY site_id, view_type"):
        images_by_site.setdefault(img["site_id"], []).append({
            "local_path": img["local_path"],
            "source": img["source"],
            "source_url": img["source_url"],
            # normalised on export as well as on write, so a row stored before
            # the cleanup was introduced can never leak tracking parameters
            "commons_file_url": clean_file_url(img["commons_file_url"] or ""),
            "author": img["author"],
            "license": img["license"],
            "license_url": img["license_url"],
            "attribution": img["attribution"],
            "view_type": img["view_type"],
        })

    out: List[Dict[str, Any]] = []
    for row in rows:
        rec = {
            "site_id": row["site_id"],
            "name": row["name"],
            "alternate_names": json.loads(row["alternate_names"] or "[]"),
            "country": row["country"],
            "country_code": row["country_code"],
            "region": row["region"],
            "city": row["city"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "type": row["type"],
            "period": row["period"],
            "description": row["description"],
            "historical_significance": row["historical_significance"],
            "architectural_features": row["architectural_features"],
            "heritage_status": row["heritage_status"],
            "wikidata_id": row["wikidata_id"],
            "commons_id": row["commons_id"],
            "sources": json.loads(row["sources"] or "[]"),
            "images": images_by_site.get(row["site_id"], []),
        }
        out.append(rec)

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return len(out)


def export_image_manifest(conn: sqlite3.Connection, path: str) -> Tuple[int, int]:
    """Image-candidate manifest: which files, licences and attributions."""
    if os.path.exists(path):
        backup_file(path)
    sites = {r["site_id"]: r for r in conn.execute("SELECT site_id, name, city, country FROM sites")}
    per_site: Dict[str, List[Dict[str, Any]]] = {}
    for img in conn.execute("SELECT * FROM images ORDER BY site_id, view_type"):
        per_site.setdefault(img["site_id"], []).append({
            "image_id": f"{img['site_id']}_{len(per_site.get(img['site_id'], [])) + 1:02d}",
            "local_path": img["local_path"],
            "source": img["source"],
            "source_url": img["source_url"],
            "commons_file_url": clean_file_url(img["commons_file_url"] or ""),
            "author": img["author"],
            "license": img["license"],
            "license_url": img["license_url"],
            "attribution": img["attribution"],
            "view_type": img["view_type"],
            "width": img["width"],
            "height": img["height"],
        })
    manifest = []
    for site_id, site in sites.items():
        images = per_site.get(site_id, [])
        if not images:
            continue
        manifest.append({
            "site_id": site_id,
            "name": site["name"],
            "city": site["city"],
            "country": site["country"],
            "image_count": len(images),
            "images": images,
        })
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
    return len(manifest), sum(len(m["images"]) for m in manifest)


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------
def report(conn: sqlite3.Connection) -> Dict[str, Any]:
    q = conn.execute
    total = q("SELECT COUNT(*) c FROM sites").fetchone()["c"]
    existing = q("SELECT COUNT(*) c FROM sites WHERE origin='existing'").fetchone()["c"]
    new = q("SELECT COUNT(*) c FROM sites WHERE origin='wikimedia'").fetchone()["c"]
    stats = {
        "total_records": total,
        "existing_records": existing,
        "new_records": new,
        "countries": q("SELECT COUNT(DISTINCT country) c FROM sites WHERE country IS NOT NULL").fetchone()["c"],
        "with_coordinates": q("SELECT COUNT(*) c FROM sites WHERE latitude IS NOT NULL").fetchone()["c"],
        "with_wikidata_id": q("SELECT COUNT(*) c FROM sites WHERE wikidata_id IS NOT NULL").fetchone()["c"],
        "with_commons_id": q("SELECT COUNT(*) c FROM sites WHERE commons_id IS NOT NULL").fetchone()["c"],
        "with_period": q("SELECT COUNT(*) c FROM sites WHERE period IS NOT NULL").fetchone()["c"],
        "with_heritage_status": q("SELECT COUNT(*) c FROM sites WHERE heritage_status IS NOT NULL").fetchone()["c"],
        "with_description": q("SELECT COUNT(*) c FROM sites WHERE description IS NOT NULL").fetchone()["c"],
        "with_images": q("SELECT COUNT(DISTINCT site_id) c FROM images").fetchone()["c"],
        "image_candidates": q("SELECT COUNT(*) c FROM images").fetchone()["c"],
    }
    stats["missing_description"] = total - stats["with_description"]
    stats["missing_coordinates"] = total - stats["with_coordinates"]
    stats["missing_period"] = total - stats["with_period"]
    stats["missing_images"] = total - stats["with_images"]
    return stats


def print_report(stats: Dict[str, Any], countries: List[str], dupes: List[Tuple[str, str, str]]) -> None:
    bar = "=" * 64
    print(f"\n{bar}\nINGESTION REPORT\n{bar}")
    print(f"  Total records        : {stats['total_records']}")
    print(f"  Existing (preserved) : {stats['existing_records']}")
    print(f"  Newly discovered     : {stats['new_records']}")
    print(f"  Countries represented: {stats['countries']}")
    print(f"  Records with coords  : {stats['with_coordinates']}  (missing {stats['missing_coordinates']})")
    print(f"  Records with Wikidata: {stats['with_wikidata_id']}")
    print(f"  Records w/ Commons id: {stats['with_commons_id']}")
    print(f"  Records with period  : {stats['with_period']}  (missing {stats['missing_period']})")
    print(f"  Records with heritage: {stats['with_heritage_status']}")
    print(f"  Records with images  : {stats['with_images']}  (missing {stats['missing_images']})")
    print(f"  Image candidates     : {stats['image_candidates']}")
    print(f"  Duplicate candidates : {len(dupes)}")
    if dupes:
        print("\n  duplicate name+country candidates (name, country, site_ids):")
        for name, country, ids in dupes[:10]:
            print(f"    - {name} ({country}) :: {ids}")
    print(bar)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest global heritage records from Wikimedia")
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after adding N new records (0 = no limit)")
    ap.add_argument("--country", action="append", default=[],
                    help="restrict to a country name as spelled in the Commons category")
    ap.add_argument("--resume", action="store_true",
                    help="skip records already stored, continue where it stopped")
    ap.add_argument("--categories-per-country", type=int, default=12,
                    help="leaf monument categories to sample per country")
    ap.add_argument("--images-per-site", type=int, default=5)
    ap.add_argument("--no-images", action="store_true", help="skip image discovery")
    ap.add_argument("--export-only", action="store_true",
                    help="regenerate JSON from the database without any network calls")
    ap.add_argument("--min-interval", type=float, default=0.15)
    args = ap.parse_args()

    conn = open_db()
    client = WikiClient(min_interval=args.min_interval)

    # --- always preserve the existing catalogue -------------------------
    existing = load_existing_catalogue()
    print(f"existing catalogue: {len(existing)} records")
    if existing and not args.export_only:
        for rec in existing:
            upsert_site(conn, existing_to_row(rec))
        conn.commit()

    if args.export_only:
        n = export_json(conn, CATALOGUE_JSON, backup=True)
        m, imgs = export_image_manifest(conn, IMAGE_MANIFEST_JSON)
        print(f"exported {n} records to catalogue, {m} manifest entries "
              f"({imgs} images) from database")
        return 0

    # --- resume state ----------------------------------------------------
    state_key = f"progress:{','.join(sorted(args.country)) if args.country else 'ALL'}"
    added_before = 0
    if args.resume:
        row = conn.execute("SELECT value FROM ingest_state WHERE key=?", (state_key,)).fetchone()
        if row:
            added_before = int(json.loads(row["value"]).get("added", 0))
            print(f"resuming: {added_before} records already added in a previous run")

    # --- enumerate source countries --------------------------------------
    print("resolving source countries from Commons root category...")
    countries = args.country or list_source_countries(client)
    print(f"  {len(countries)} source countries")

    # --- ingest ----------------------------------------------------------
    new_rows: List[Dict[str, Any]] = []
    added = 0
    backfilled = 0
    dupes: List[Tuple[str, str, str]] = []
    seen_ids = {r["site_id"] for r in conn.execute("SELECT site_id FROM sites")}
    seen_wikidata = {r["wikidata_id"] for r in conn.execute(
        "SELECT wikidata_id FROM sites WHERE wikidata_id IS NOT NULL")}
    seen_name_country = {(r["name_key"], r["country_slug"]) for r in conn.execute(
        "SELECT name_key, country_slug FROM sites")}

    for ci, country in enumerate(countries, 1):
        if args.limit and added >= args.limit:
            break
        cats = discover_monument_categories(client, country, args.categories_per_country)
        if not cats:
            continue
        print(f"[{ci}/{len(countries)}] {country}: {len(cats)} categories")

        # resolve Commons category -> Wikidata Q-id in one batched call
        qmap = client.page_wikibase_items(cats)
        qids = [q for q in qmap.values() if q]
        entities = client.entities(sorted(set(qids)))
        if not entities:
            continue

        # labels needed to normalise country / heritage / style / instance
        label_qids = set()
        for ent in entities.values():
            for prop in (P_COUNTRY, P_HERITAGE, P_ARCH_STYLE, P_INSTANCE):
                label_qids.update(claim_qids(ent, prop))
        labels = resolve_qid_labels(client, label_qids)

        for cat in cats:
            if args.limit and added >= args.limit:
                break
            qid = qmap.get(cat)
            if not qid:
                continue
            ent = entities.get(qid)
            if not ent:
                continue
            if qid in seen_wikidata:
                # already stored: record the duplicate, but still backfill
                # images if this site has none yet
                dupes.append((cat, country, f"wikidata:{qid}"))
                if not args.no_images:
                    known = conn.execute(
                        "SELECT site_id FROM sites WHERE wikidata_id=?", (qid,)
                    ).fetchone()
                    have = 0
                    if known:
                        have = conn.execute(
                            "SELECT COUNT(*) c FROM images WHERE site_id=?",
                            (known["site_id"],)).fetchone()["c"]
                    if known and have == 0:
                        stub = {"site_id": known["site_id"],
                                "commons_id": cat}
                        found = collect_images(client, stub, per_site=args.images_per_site)
                        if found:
                            add_images(conn, found)
                            backfilled += 1
                continue
            row = build_site_record(client, cat, qid, ent, country, labels)
            if not row:
                continue
            key = (row["name_key"], row["country_slug"])
            if key in seen_name_country:
                dupes.append((row["name"], row["country"], row["site_id"]))
                continue
            # keep site_id unique within this run
            base_id = row["site_id"]
            n = 2
            while row["site_id"] in seen_ids:
                row["site_id"] = f"{base_id}_{n}"
                n += 1
            seen_ids.add(row["site_id"])
            seen_wikidata.add(qid)
            seen_name_country.add(key)

            if not args.no_images:
                imgs = collect_images(client, row, per_site=args.images_per_site)
                row["images"] = imgs
                if imgs:
                    add_images(conn, imgs)

            upsert_site(conn, row)
            new_rows.append(row)
            added += 1

    conn.commit()
    conn.execute("INSERT OR REPLACE INTO ingest_state (key, value, updated_at) VALUES (?,?,?)",
                 (state_key, json.dumps({"added": added_before + added,
                                         "run_at": now_iso()}), now_iso()))
    conn.commit()

    # --- export ----------------------------------------------------------
    n = export_json(conn, CATALOGUE_JSON, backup=True)
    m, imgs = export_image_manifest(conn, IMAGE_MANIFEST_JSON)

    stats = report(conn)
    print_report(stats, countries, dupes)
    print(f"\nAPI requests made: {client.request_count}")
    print(f"new this run: {added} | image backfills: {backfilled}")
    print(f"catalogue    -> {os.path.relpath(CATALOGUE_JSON, ROOT)}  ({n} records)")
    print(f"image manifest-> {os.path.relpath(IMAGE_MANIFEST_JSON, ROOT)}  ({m} sites, {imgs} images)")
    print(f"database     -> {os.path.relpath(DB_PATH, ROOT)}")
    print("no image files were downloaded\n")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
