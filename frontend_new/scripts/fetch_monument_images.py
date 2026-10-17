"""Fetch ONE verified Wikimedia Commons image per monument card.

    C:/Users/humai/AppData/Local/Python/bin/python frontend_new/scripts/fetch_monument_images.py --dry-run
    C:/Users/humai/AppData/Local/Python/bin/python frontend_new/scripts/fetch_monument_images.py

Pipeline per monument (the order the brief requires):

    LOCAL IMAGE EXISTS          -> use it, never re-download
    LOCAL IMAGE MISSING         -> check the catalogue's verified image source
    CATALOGUE HAS A VERIFIED SRC -> resolve it through the Commons API
    NO VERIFIED SOURCE          -> search Commons, then download

Scope is the whole catalogue by default (455 records, one image each).  Pass
--limit N to cover only the first N.

Safety
------
* concurrency = 1 (strictly sequential)
* descriptive User-Agent, per the Wikimedia UA policy
* honours Retry-After, exponential backoff on 429/5xx
* checkpoint/resume: image_manifest.json is rewritten after every file, and an
  existing valid file is skipped, so a re-run never re-downloads
* no URL is ever constructed by hand.  Every file URL comes back from the
  Commons API in imageinfo; this script only reads those returned values.

It reads the catalogue and writes ONLY inside frontend_new/assets/.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from PIL import Image

# ── configuration ───────────────────────────────────────────────────────────

FRONTEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.abspath(os.path.join(FRONTEND, ".."))
CATALOGUE = os.path.join(ROOT, "data", "metadata", "global_monument_catalogue.json")
MONUMENTS_DIR = os.path.join(FRONTEND, "assets", "images", "monuments")
MANIFEST = os.path.join(MONUMENTS_DIR, "image_manifest.json")
SITES_DIR = os.path.join(FRONTEND, "assets", "images", "sites")

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "HeritageDiscoveryImageFetcher/1.0 "
    "(https://github.com/heritage-discovery; educational prototype) "
    "python-urllib/3"
)

# Must match PAGE_SIZE in app.js: the first page of the explorer grid is the
# visible card experience.  Kept here as a literal so the two cannot drift
# silently; verify_frontend_page_size() re-checks it against app.js.
VISIBLE_CARDS = 24

# Licences we accept.  Anything not matched here is rejected: the image is not
# downloaded, and the monument falls through to the architectural placeholder.
ALLOWED_LICENCE = re.compile(
    r"^(cc0|cc[\s-]?by(?:[\s-]?sa)?\b|public domain|pd[\s-]?(?:old|us|art|self|selfie)|no restrictions)",
    re.I,
)
FREE_LICENCE_URL = re.compile(
    r"^(https?://)?(creativecommons\.org|www\.commons\.wikimedia\.org/wiki/Commons:Licensing)",
    re.I,
)

# Subjects that are not "a photograph of the monument" even when the filename
# matches.  Learned from live probe runs: Commons returns these readily, and a
# filename-only match will happily hand you a statue of Minerva for the
# Brandenburg Gate, or a garden statue for Borobudur.
REJECT_TITLE = re.compile(
    r"\b("
    r"map|plan|diagram|sketch|drawing|painting|engraving|lithograph|etching|"
    r"stamp|coin|banknote|postcard|poster|logo|crest|badge|coat of arms|"
    r"flag|locator|location|reliefs?|inscription|graffiti|maquette|model of|"
    r"blueprint|portrait of|manuscript|letter|newspaper|magazine|"
    r"grave|tombstone|gravestone|cemetery|"
    r"statues?|sculptures?|bust|bronze|equestrian|"
    r"interior of|inside|ceiling|mosaic|corridors?|escalera|staircase|"
    r"flowerpots?|pots in|gardener|hotel|hostel|"
    r"people|person|crowd|protest|"
    r"museum|gift shop|ticket|book cover|album|"
    # Detail shots.  A file title that names the monument AND one of its parts
    # is a close-up of that part, not a photograph of the monument: the card
    # then advertises a rose window as "Chartres Cathedral".  Learned from a
    # dry run over catalogue records 25-30, which resolved Canterbury Cathedral
    # to a stained-glass panel, Chartres to its south rose window, Chichen Itza
    # to an Atlante statue and Mexico City to a Rivera mural.
    #
    # Deliberately absent: tower, gate, dome, palace, stupa, chapel, courtyard.
    # Those name whole monuments and are two of the 23 hand-verified picks
    # (Belém Tower, Brandenburg Gate) - rejecting them was a real bug found
    # while building this list.  Only unambiguous *parts* belong here.
    r"windows?|stained glass|rose window|"
    r"murals?|frescoe?s?|atlantes|atlante|tympanum|"
    r"doors?|doorway|doorways|portal|portals|naves|apse|apsis|crypts?|crypt|"
    r"belfry|mihrab|frieze|friezes|gargoyle|gargoyles|"
    r"panels?|carvings?|carved|"
    r"close-?ups?|details? of|detail\b|"
    r"stairway|stairways|plaque|plaques|cross-section|"
    r"crop of|from above|aerial"
    # NOTE: no trailing "|" on the last line.  "aerial|)" is an empty
    # alternative that matches at position 0 of every title and rejects
    # everything; that bug shipped once while this list was being written.
    r")\b",
    re.I,
)

# Geometric / display sanity for a card image.
MIN_EDGE = 800
MAX_ASPECT = 2.8
MAX_BYTES = 6 * 1024 * 1024
THUMB_WIDTH = 1600           # ask the API for this rendition; we store smaller

# The card is 16:10 and the detail hero is wide. A tall photo gets centre-cropped
# into mush, so prefer landscape and reward it in scoring.
CARD_ASPECT = 16 / 10

# (suffix, longest edge, quality) - mirrors prepare_gallery.py
HERO = ("lg", 1400, 80)
CARD = ("sm", 640, 78)

# Words too generic to identify a specific monument.
GENERIC = {
    "ancient", "city", "area", "areas", "archaeological", "site", "sites",
    "group", "ruins", "temple", "temples", "palace", "island", "islands",
    "stupa", "caves", "cave", "tomb", "monument", "monuments", "national",
    "the", "and", "of", "old", "great", "grand", "upper", "lower",
}

# Monuments on the first page that already ship a real local photograph in
# assets/images/sites/.  These are never downloaded and never overwritten.
LOCAL_SITES = {
    "ajanta_caves", "jama_masjid", "konark_sun_temple",
    "qutub_minar", "red_fort", "taj_mahal",
}

# Explicit, human-checked overrides for cases where the generic heuristic picks
# the wrong subject.  site_id -> Commons File: title.  Empty = trust the search.
# This is a decision table, not a fallback: every entry was fetched, inspected
# by eye on the contact sheet, and kept or replaced because of what it showed.
#
#   brasilia          the record is a CITY, not a building, so title-matching on
#                     "Brasilia" surfaces street scenes, a purple ipê tree and a
#                     football crest. Pinned to the Palácio da Alvorada, the
#                     presidential palace that IS the city's landmark.
#   bucheon_temple    record name is "Bulguksa Temple" but site_id says bucheon;
#                     the search returned a flower bed. Pinned to the main hall.
#   colosseum_athens  NOT an error: the catalogue record's own name field is
#                     "Brandenburg Gate" (a pre-existing site_id/name mismatch we
#                     must not edit). The card renders that name, so the Gate is
#                     the correct image.
PINNED = {
    "brasilia": "File:Brasília Palacio da Alvorada from Paranoá Lake.jpg",
    "bucheon_temple": "File:Bulguksa temple main building.jpg",
    # "Blue Mosque" is ambiguous: Commons' top hit for it is the one in TABRIZ,
    # Iran. This record is the Sultan Ahmed Mosque in Istanbul, so the pick has
    # to name the city explicitly.
    "sultan_ahmet_mosque":
        "File:Exterior view of the Blue Mosque (Sultan Ahmed Mosque), Istanbul.jpg",
    # The search offered "Lichtgrenze Brandenburg Gate" - photographs of the 1990
    # border closure, with crowds and the Wall. A plain daylight exterior is what
    # a monument card wants.
    "colosseum_athens": "File:Brandenburg Gate - Brandenburger Tor - Berlin - Germany - 03.jpg",
}


# ── small helpers ───────────────────────────────────────────────────────────

def strip_html(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", "", value)
    return html.unescape(text).strip()


def singular(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def clean_name(name: str) -> str:
    """'Aksum (Axum)' -> 'Aksum'; 'Belém Tower (Torre de Belém)' -> 'Belém Tower'."""
    without_paren = re.sub(r"\([^)]*\)", " ", name or "")
    return re.sub(r"\s+", " ", without_paren).strip(" ,.-")


def distinctive(name: str) -> list[str]:
    words = re.findall(r"[^\W_]+", clean_name(name), flags=re.UNICODE)
    return [w.lower() for w in words if len(w) >= 3 and w.lower() not in GENERIC]


def query_chain(name: str, alternate_names: list[str] | None = None):
    """Commons intitle queries, most specific first.

    Built from the DISTINCTIVE words, never from a plain prefix cut: the
    record "Archaeological Areas of Pompeii" must become intitle:"Pompeii",
    not intitle:"Archaeological".
    """
    base = clean_name(name)
    if not base:
        return []

    queries: list[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        if text and text not in seen:
            seen.add(text)
            queries.append(text)

    add(f'intitle:"{base}"')
    words = re.findall(r"[^\W_]+", base, flags=re.UNICODE)
    dist = [w for w in words if len(w) >= 3 and w.lower() not in GENERIC]
    for keep in range(min(3, len(dist)), 0, -1):
        add('intitle:"%s"' % " ".join(dist[:keep]))
    for alt in alternate_names or []:
        cleaned = clean_name(alt)
        if cleaned:
            add(f'intitle:"{cleaned}"')
    return queries


def verify_frontend_page_size() -> None:
    """Fail loudly if app.js no longer renders VISIBLE_CARDS on the first page."""
    app = os.path.join(FRONTEND, "app.js")
    try:
        with open(app, encoding="utf-8") as fh:
            body = fh.read()
    except OSError:
        return
    found = re.search(r"var\s+PAGE_SIZE\s*=\s*(\d+)", body)
    if found and int(found.group(1)) != VISIBLE_CARDS:
        print(
            f"  ! app.js PAGE_SIZE={found.group(1)} but this script targets "
            f"{VISIBLE_CARDS}. Update VISIBLE_CARDS before running for real.",
            file=sys.stderr,
        )


# ── HTTP ────────────────────────────────────────────────────────────────────

class Throttle:
    """Sequential requests, polite spacing, Retry-After + exponential backoff."""

    def __init__(self, delay: float = 0.35, max_tries: int = 4):
        self.delay = delay
        self.max_tries = max_tries
        self._last = 0.0

    def _wait(self) -> None:
        gap = time.monotonic() - self._last
        if gap < self.delay:
            time.sleep(self.delay - gap)

    def get(self, url: str, tries: int | None = None) -> bytes:
        tries = tries or self.max_tries
        last_error: Exception | None = None
        for attempt in range(tries):
            self._wait()
            self._last = time.monotonic()
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "application/json" if "api.php" in url else "image/*,*/*",
                        "Accept-Encoding": "identity",
                    },
                )
                with urllib.request.urlopen(req, timeout=60) as res:
                    return res.read(MAX_BYTES + 1)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 429 or exc.code >= 500:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    try:
                        pause = float(retry_after)  # type: ignore[arg-type]
                    except (TypeError, ValueError):
                        pause = min(60.0, 2.0 * (2 ** attempt))
                    print(f"      HTTP {exc.code}; sleeping {pause:.0f}s (Retry-After honoured)")
                    time.sleep(pause)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                pause = min(60.0, 2.0 * (2 ** attempt))
                print(f"      {exc}; retrying in {pause:.0f}s")
                time.sleep(pause)
        raise RuntimeError(f"giving up after {tries} attempts: {last_error}")


def api_json(throttle: Throttle, params: dict) -> dict:
    query = dict(params)
    query.update({"action": "query", "format": "json", "formatversion": "2"})
    url = API + "?" + urllib.parse.urlencode(query)
    raw = throttle.get(url)
    return json.loads(raw.decode("utf-8"))


# ── Commons lookup ──────────────────────────────────────────────────────────

def imageinfo(throttle: Throttle, titles: list[str]) -> list[dict]:
    """imageinfo straight from the API for the given File: titles."""
    data = api_json(throttle, {
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime",
        "iiurlwidth": str(THUMB_WIDTH),
    })
    out = []
    for page in (data.get("query") or {}).get("pages") or []:
        info = (page.get("imageinfo") or [{}])[0]
        if info:
            # The File: title is on the page, not inside imageinfo. Carry it
            # explicitly: candidate_from() needs it for both the relevance
            # check and the attribution record.
            info["page_title"] = page.get("title") or ""
            out.append(info)
    return out


def meta_value(meta: dict, key: str) -> str:
    return strip_html((meta.get(key) or {}).get("value", ""))


def candidate_from(info: dict) -> dict:
    """Normalise one imageinfo record into the fields we judge and store."""
    meta = info.get("extmetadata") or {}
    title = info.get("page_title") or info.get("title") or ""
    width = int(info.get("thumbwidth") or info.get("width") or 0)
    height = int(info.get("thumbheight") or info.get("height") or 0)
    licence = meta_value(meta, "LicenseShortName") or meta_value(meta, "License")
    licence_url = meta_value(meta, "LicenseUrl")
    return {
        "title": title,
        # thumburl is the API-generated rendition we actually fetch; url is the
        # full-size original.  Both come from the API - neither is built here.
        "url": info.get("thumburl") or info.get("url"),
        "original_file_url": info.get("url"),
        "description_url": info.get("descriptionurl"),
        "width": width,
        "height": height,
        "mime": info.get("mime") or "",
        "licence": licence,
        "licence_url": licence_url,
        "author": meta_value(meta, "Artist") or meta_value(meta, "Credit"),
        "date_original": meta_value(meta, "DateTimeOriginal"),
    }


def judge(cand: dict, record: dict) -> tuple[bool, str]:
    """Accept or reject a candidate.  Returns (ok, reason)."""
    title = cand["title"] or ""

    if not cand["url"]:
        return False, "no file URL returned by the API"
    if cand["mime"] not in ("image/jpeg", "image/png", "image/webp"):
        return False, f"unsupported mime {cand['mime']}"

    if not ALLOWED_LICENCE.match(cand["licence"] or ""):
        return False, f"licence not on the allow-list ({cand['licence'] or 'unknown'})"
    if cand["licence_url"] and not FREE_LICENCE_URL.match(cand["licence_url"]):
        return False, f"licence URL is not a known free licence ({cand['licence_url']})"
    if not cand["licence"] or not cand["author"]:
        return False, "incomplete attribution metadata"

    if REJECT_TITLE.search(title):
        bad = REJECT_TITLE.search(title).group(1)  # type: ignore[union-attr]
        return False, f"subject is not a monument photograph ('{bad}')"

    long_edge = max(cand["width"], cand["height"])
    short_edge = min(cand["width"], cand["height"])
    if long_edge < MIN_EDGE:
        return False, f"too small ({cand['width']}x{cand['height']})"
    if short_edge and long_edge / short_edge > MAX_ASPECT:
        return False, f"aspect ratio {long_edge / short_edge:.1f}:1 is not displayable"

    # relevance: the file title must echo at least one distinctive word of the
    # monument's name, otherwise it is some other place entirely.
    wanted = distinctive(record.get("name", ""))
    if wanted:
        low = title.lower()
        # Word-boundary match on the singular form, so "Wat" still matches
        # "Wat" and "temples" still matches "temple" in the file title.
        token_hits = [w for w in wanted
                      if re.search(rf"\b{re.escape(singular(w))}", low)]
        if not token_hits:
            return False, f"title does not name the monument (wanted one of {wanted})"
    return True, "ok"


def score(cand: dict, record: dict) -> tuple:
    """Rank accepted candidates.

    Highest priority: a title that IS the monument's name (so the photo is of
    the whole building, not a detail of it).  Then landscape framing, because
    the card crops to 16:10 and a tall photo loses its subject.  Resolution
    last - it is the weakest signal and the easiest to over-weight.
    """
    title = (cand["title"] or "").lower()
    base = clean_name(record.get("name", "")).lower()
    wanted = distinctive(record.get("name", ""))

    # 3 when the title basically IS the monument name, 2 when it leads with it,
    # 1 when the distinctive word appears somewhere.
    if base and title.startswith(base):
        name_score = 3
    elif base and base in title:
        name_score = 2
    else:
        name_score = 1 if any(
            re.search(rf"\b{re.escape(singular(w))}", title) for w in wanted
        ) else 0

    matched = sum(
        1 for w in wanted if re.search(rf"\b{re.escape(singular(w))}", title)
    )

    width = max(cand["width"], cand["height"])
    height = min(cand["width"], cand["height"])
    if width and height:
        aspect = width / height
        # 1.0 at the card's 16:10, decaying either side of it.
        framing = max(0.0, 1.0 - abs(aspect - CARD_ASPECT) / CARD_ASPECT)
    else:
        framing = 0.0

    return (name_score, matched, round(framing, 2), width)


def search_commons(throttle: Throttle, record: dict) -> tuple[dict | None, list[str]]:
    """Search, judge, and return the best candidate plus a reason trail."""
    name = record.get("name", "")
    seen: set[str] = set()
    accepted: list[dict] = []
    trail: list[str] = []

    for query in query_chain(name, record.get("alternate_names")):
        if query.endswith('""'):
            continue
        try:
            data = api_json(throttle, {
                "generator": "search",
                "gsrsearch": f"{query} filetype:bitmap",
                "gsrnamespace": "6",
                "gsrlimit": "20",
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size|mime",
                "iiurlwidth": str(THUMB_WIDTH),
            })
        except Exception as exc:  # noqa: BLE001
            trail.append(f"{query}: search failed ({exc})")
            continue

        pages = (data.get("query") or {}).get("pages") or []
        fresh = 0
        for page in pages:
            info = (page.get("imageinfo") or [{}])[0]
            if not info:
                continue
            cand = candidate_from(info)
            cand["title"] = page.get("title") or cand["title"]
            if cand["title"] in seen:
                continue
            seen.add(cand["title"])
            fresh += 1
            ok, reason = judge(cand, record)
            if ok:
                accepted.append(cand)
            else:
                trail.append(f"  reject {cand['title'][:58]}: {reason}")

        trail.append(f"{query}: {len(pages)} hits, {fresh} new")
        if len(accepted) >= 8:
            break

    if not accepted:
        return None, trail
    accepted.sort(key=lambda c: score(c, record), reverse=True)
    return accepted[0], trail


def from_catalogue(throttle: Throttle, record: dict) -> dict | None:
    """Resolve the catalogue's own verified image source through the API."""
    for entry in (record.get("images") or [])[:3]:
        url = entry.get("source_url") or ""
        m = re.search(r"/wiki/(File:[^?#]+)", url)
        if not m:
            continue
        title = urllib.parse.unquote(m.group(1)).replace("_", " ")
        try:
            infos = imageinfo(throttle, [title])
        except Exception:  # noqa: BLE001
            continue
        if not infos:
            continue
        cand = candidate_from(infos[0])
        # Trust the catalogue's curation here, but still refuse a non-free or
        # unusable file, and still re-read the licence from Commons.
        ok, reason = judge(cand, record)
        if not ok:
            ok = reason == "title does not name the monument (wanted one of " \
                           + str(distinctive(record.get("name", ""))) + ")"
        if ok:
            cand["via"] = "catalogue images[]"
            return cand
    return None


# ── local files ─────────────────────────────────────────────────────────────

def has_local(site_id: str) -> str | None:
    """Return a local path if this monument already has a real photograph."""
    thumb = os.path.join(SITES_DIR, f"{site_id}.webp")
    if os.path.isfile(thumb) and os.path.getsize(thumb) > 0:
        return os.path.relpath(thumb, FRONTEND).replace("\\", "/")
    return None


def write_webp(raw: bytes, out_dir: str, stem: str) -> list[tuple[str, int, int]]:
    """Validate the downloaded bytes, then write the display derivatives."""
    import io
    with Image.open(io.BytesIO(raw)) as opened:
        opened.load()                      # raises if the file is not a real image
        image = opened.convert("RGB")

    results = []
    for suffix, max_edge, quality in (HERO, CARD):
        variant = image.copy()
        variant.thumbnail((max_edge, max_edge), Image.LANCZOS)
        path = os.path.join(out_dir, f"{stem}-{suffix}.webp")
        variant.save(path, "WEBP", quality=quality, method=6)
        results.append((os.path.relpath(path, FRONTEND).replace("\\", "/"),
                        variant.size[0], variant.size[1]))
    return results


# ── main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve and judge candidates; download nothing")
    parser.add_argument("--limit", type=int, default=0,
                        help="how many catalogue records to cover, from the "
                             "start; 0 (the default) means the whole catalogue")
    parser.add_argument("--redo", default="",
                        help="comma-separated site_ids to re-resolve and overwrite, "
                             "ignoring the resume cache for those entries")
    args = parser.parse_args()

    verify_frontend_page_size()

    with open(CATALOGUE, encoding="utf-8") as fh:
        catalogue = json.load(fh)
    # --limit 0 means "the whole catalogue".  Slicing by args.limit would make
    # that an empty list and report a clean run having downloaded nothing, so
    # the zero is handled explicitly rather than passed to the slice.
    page = catalogue if args.limit <= 0 else catalogue[: args.limit]
    scope = "the whole catalogue" if args.limit <= 0 else f"the first {len(page)} records"

    os.makedirs(MONUMENTS_DIR, exist_ok=True)
    manifest: dict = {}
    if os.path.isfile(MANIFEST):
        try:
            with open(MANIFEST, encoding="utf-8") as fh:
                manifest = json.load(fh)
        except (OSError, json.JSONDecodeError):
            manifest = {}
    entries = manifest.setdefault("images", {})

    # --redo drops those entries first, so they are re-resolved and overwritten.
    redo = {s.strip() for s in args.redo.split(",") if s.strip()}
    for site_id in redo:
        entries.pop(site_id, None)

    throttle = Throttle()
    used_titles = {
        e.get("commons_title") for e in entries.values() if isinstance(e, dict)
    }

    print(f"Scope: {scope} ({len(page)} records)\n")
    downloaded = 0
    reused = 0
    skipped_local = 0
    failures = []

    for record in page:
        site_id = record["site_id"]
        name = record.get("name") or site_id

        local = has_local(site_id)
        if local:
            skipped_local += 1
            print(f"  LOCAL  {site_id:26s} {local}")
            continue

        if site_id in entries:
            files = entries[site_id].get("files") or []
            if files and all(
                os.path.isfile(os.path.join(FRONTEND, f)) for f in files
            ):
                reused += 1
                print(f"  CACHED {site_id:26s} already downloaded, skipping")
                continue

        print(f"  FETCH  {site_id:26s} {name[:44]}")

        cand = None
        source = None
        if site_id in PINNED:
            try:
                infos = imageinfo(throttle, [PINNED[site_id]])
                if infos:
                    cand = candidate_from(infos[0])
                    source = "pinned (human-verified)"
            except Exception as exc:  # noqa: BLE001
                print(f"      pinned lookup failed: {exc}")
        if cand is None:
            cand = from_catalogue(throttle, record)
            if cand:
                source = cand.get("via", "catalogue images[]")
        if cand is None:
            cand, trail = search_commons(throttle, record)
            source = "Commons search"
            if cand is None:
                failures.append((site_id, "no acceptable image found"))
                print(f"      none. {'; '.join(trail[-4:])}")
                continue

        if cand["title"] in used_titles:
            failures.append((site_id, "duplicate image already used by another card"))
            print(f"      skip (duplicate of another monument): {cand['title'][:52]}")
            continue

        ok, reason = judge(cand, record)
        if not ok:
            failures.append((site_id, reason))
            print(f"      rejected: {reason}")
            continue

        print(f"      pick  {cand['title'][:64]}")
        print(f"            {cand['width']}x{cand['height']}  {cand['licence']}  via {source}")

        if args.dry_run:
            used_titles.add(cand["title"])
            continue

        out_dir = os.path.join(MONUMENTS_DIR, site_id)
        os.makedirs(out_dir, exist_ok=True)
        try:
            raw = throttle.get(cand["url"])
        except Exception as exc:  # noqa: BLE001
            failures.append((site_id, f"download failed: {exc}"))
            print(f"      download failed: {exc}")
            continue

        if len(raw) > MAX_BYTES:
            failures.append((site_id, f"file too large ({len(raw)} bytes)"))
            continue

        try:
            written = write_webp(raw, out_dir, "01")
        except Exception as exc:  # noqa: BLE001
            failures.append((site_id, f"invalid image: {exc}"))
            print(f"      invalid image, discarded: {exc}")
            for f in os.listdir(out_dir):
                os.remove(os.path.join(out_dir, f))
            continue

        entries[site_id] = {
            "site_id": site_id,
            "name": name,
            "city": record.get("city"),
            "country": record.get("country"),
            "files": [w[0] for w in written],
            "width": written[0][1],
            "height": written[0][2],
            "card": written[1][0],
            "source": "Wikimedia Commons",
            "retrieved_via": source,
            "commons_title": cand["title"],
            "source_url": cand["url"],
            "original_file_url": cand.get("original_file_url"),
            "commons_page_url": cand.get("description_url"),
            "author": cand["author"],
            "license": cand["licence"],
            "license_url": cand["licence_url"],
            "date_original": cand["date_original"],
            "download_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        used_titles.add(cand["title"])
        downloaded += 1

        # checkpoint after every file
        manifest["_comment"] = (
            "Attribution for images downloaded by "
            "frontend_new/scripts/fetch_monument_images.py. One entry per "
            "monument; every URL comes from the Wikimedia Commons API."
        )
        manifest["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with open(MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"            wrote {len(written)} files")

    if not args.dry_run:
        with open(MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1, ensure_ascii=False)
            fh.write("\n")

    print(f"\nlocal images reused : {skipped_local}")
    print(f"already downloaded  : {reused}")
    print(f"downloaded          : {downloaded}")
    print(f"no image            : {len(failures)}")
    for site_id, why in failures:
        print(f"    {site_id:28s} {why}")
    if args.dry_run:
        print("\n(dry run - nothing was downloaded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())