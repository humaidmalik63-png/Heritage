#!/usr/bin/env python3
"""
Phase 2 - download verified Wikimedia Commons images for the global heritage catalogue.

Consumes data/metadata/global_image_manifest.json (candidates already collected)
and writes verified images to data/raw/global/<site_id>/.

Safety gates applied BEFORE any network call:
  - required attribution present (author, license, license_url, source_url)
  - license in approved Creative Commons set
  - license name consistent with license_url (CC BY vs CC BY-SA contradictions rejected)
  - URL is https on upload.wikimedia.org
  - filename is not a map / diagram / plan / logo / banner / screenshot

Safety gates applied AFTER download:
  - HTTP 200
  - content actually an image (magic bytes, not just Content-Type)
  - decoded pixel dimensions meet minimum
  - sha256 not already present (content-level duplicate detection)
  - file size within bounds

The manifest is updated with downloaded / local_path / file_size / mime_type /
download_error while preserving all original attribution fields.

Read-only with respect to: data/metadata/global_monument_catalogue.json,
data/processed/** (FAISS), frontend*/**, backend/, ml/.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "metadata" / "global_image_manifest.json"
CATALOGUE_PATH = ROOT / "data" / "metadata" / "global_monument_catalogue.json"
RAW_ROOT = ROOT / "data" / "raw" / "global"

USER_AGENT = (
    "HeritageRecognitionDatasetBuild/2.0 "
    "(offline heritage image dataset construction; contact: local-research)"
)

# Only permissive Creative Commons licences are accepted.
ALLOWED_LICENCE_RE = re.compile(
    r"^(CC0|CC BY(?:-SA)?\s*\d(?:\.\d)?)$", re.IGNORECASE
)

# Filename tokens that indicate the file is not a photograph of the monument.
EXCLUDE_TOKENS = {
    "map", "maps", "mapa", "mapas", "mappen", "karte", "karten", "carte", "cartes",
    "diagram", "diagrama", "diagramme", "plan", "plans", "plano", "planos",
    "logo", "logos", "flag", "flagge", "banner", "banners", "icon", "icons",
    "chart", "charts", "graph", "graphs", "svg", "locator", "kositka",
    "leyenda", "legenda", "stavba", "screenshot", "screenie",
}

MIN_WIDTH = 640
MIN_HEIGHT = 480
MIN_BYTES = 4 * 1024
MAX_BYTES = 25 * 1024 * 1024
TIMEOUT = 30
DELAY = 3.0                # polite spacing between downloads
RETRIES = 2
MAX_BACKOFF = 20           # never sleep longer than this on Retry-After
THROTTLE_STOP_AFTER = 6    # consecutive 429s before we pause
THROTTLE_COOLDOWN = 75     # seconds to wait once we are being throttled
MAX_SWEEPS = 40            # max retry sweeps over throttled items
MAX_COOLDOWNS = 6          # give up after this many cooldowns with no progress


# --------------------------------------------------------------------------
# image sniffing (stdlib only - Pillow is not installed in this environment)
# --------------------------------------------------------------------------

MAGIC = (
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"GIF87a", "image/gif", ".gif"),
    (b"GIF89a", "image/gif", ".gif"),
    (b"BM", "image/bmp", ".bmp"),
)


def sniff_image(data: bytes):
    """Return (mime, ext, width, height) from magic bytes, or (None, None, 0, 0)."""
    if data[:3] == b"\xff\xd8\xff":
        return ("image/jpeg", ".jpg") + jpeg_size(data)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ("image/png", ".png") + png_size(data)
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ("image/gif", ".gif") + gif_size(data)
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return ("image/tiff", ".tiff") + tiff_size(data)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ("image/webp", ".webp") + webp_size(data)
    return (None, None, 0, 0)


def png_size(d):
    if len(d) < 24:
        return (0, 0)
    return (int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big"))


def gif_size(d):
    if len(d) < 10:
        return (0, 0)
    return (int.from_bytes(d[6:8], "little"), int.from_bytes(d[8:10], "little"))


def tiff_size(d):
    try:
        e = "little" if d[:2] == b"II" else "big"
        off = int.from_bytes(d[4:8], e)
        n = int.from_bytes(d[off:off + 2], e)
        w = h = 0
        for i in range(n):
            eo = off + 2 + i * 12
            tag = int.from_bytes(d[eo:eo + 2], e)
            if tag == 256:
                w = int.from_bytes(d[eo + 8:eo + 12], e)
            elif tag == 257:
                h = int.from_bytes(d[eo + 8:eo + 12], e)
        return (w, h)
    except Exception:
        return (0, 0)


def jpeg_size(d):
    i, n = 2, len(d)
    while i < n - 9:
        if d[i] != 0xFF:
            i += 1
            continue
        marker = d[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg = int.from_bytes(d[i + 2:i + 4], "big")
        # SOF0..SOF15 except DHT(C4)/JPG(C8)/DAC(CC)
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h = int.from_bytes(d[i + 5:i + 7], "big")
            w = int.from_bytes(d[i + 7:i + 9], "big")
            return (w, h)
        i += 2 + seg
    return (0, 0)


def webp_size(d):
    try:
        c = d[12:16]
        if c == b"VP8 ":
            return (int.from_bytes(d[26:28], "little") & 0x3FFF,
                    int.from_bytes(d[28:30], "little") & 0x3FFF)
        if c == b"VP8X":
            w = int.from_bytes(d[24:27], "little") + 1
            h = int.from_bytes(d[27:30], "little") + 1
            return (w, h)
        if c == b"VP8L":
            b = int.from_bytes(d[21:25], "little")
            return ((b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1)
    except Exception:
        pass
    return (0, 0)


# --------------------------------------------------------------------------
# pre-flight validation
# --------------------------------------------------------------------------

def filename_tokens(url: str):
    name = url.rsplit("/", 1)[-1].split("?", 1)[0]
    stem = name.rsplit(".", 1)[0].lower()
    return set(re.split(r"[^a-z0-9]+", stem)), name


def preflight(rec: dict):
    """Return None if the record passes, else a rejection reason string."""
    lic = (rec.get("license") or "").strip()
    lic_url = (rec.get("license_url") or "").strip().lower()

    for f in ("source_url", "commons_file_url", "author", "license", "license_url"):
        if not (rec.get(f) or "").strip():
            return f"missing_{f}"

    if not ALLOWED_LICENCE_RE.match(lic):
        return f"unapproved_license:{lic}"

    # The licence name and the licence URL must agree on ShareAlike.
    if ("by-sa" in lic.lower()) != ("by-sa" in lic_url):
        return f"license_url_contradiction:{lic}"

    url = rec["commons_file_url"]
    if not url.startswith("https://upload.wikimedia.org/"):
        return "non_commons_upload_host"

    toks, name = filename_tokens(url)
    bad = toks & EXCLUDE_TOKENS
    if bad:
        return f"excluded_asset:{sorted(bad)[0]}"

    if name.lower().endswith(".svg"):
        return "excluded_asset:svg"
    return None


# --------------------------------------------------------------------------
# download
# --------------------------------------------------------------------------

_last_request = 0.0


def fetch(url: str):
    """Return (data, error).

    Honours Retry-After on 429/503 but caps the wait so a throttled or hot
    file cannot stall the whole run.

    Throttling is returned as a distinct "throttled" error so the caller can
    DEFER the item and keep going, instead of burning the attempt budget on
    infrastructure errors that will clear on their own.
    """
    global _last_request
    # Pace BEFORE the request so the first burst is also rate-limited.
    elapsed = time.time() - _last_request
    if elapsed < DELAY:
        time.sleep(DELAY - elapsed)
    _last_request = time.time()

    last = None
    for attempt in range(RETRIES + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read(), None
        except urllib.error.HTTPError as e:
            code = e.code
            if code in (404, 400, 403):
                return None, f"http_{code}"
            if code in (429, 503):
                try:
                    wait = float(e.headers.get("Retry-After", 0) or 0)
                except (TypeError, ValueError):
                    wait = 0.0
                return None, f"http_{code}_throttled(retry_after={int(wait or 0)}s)"
            last = f"http_{code}"
        except urllib.error.URLError as e:
            last = f"urlerror:{getattr(e, 'reason', e)}"
        except Exception as e:
            last = f"{type(e).__name__}:{e}"
        if attempt < RETRIES:
            time.sleep(1.2 * (attempt + 1))
    return None, last or "unknown_error"


def slugify(rec: dict) -> str:
    # Prefer the clean Commons filename: decode it and drop the "File:" namespace
    # prefix so we do not persist percent-escapes like "%3A" into the tree.
    src = rec.get("source_url", "")
    name = src.rsplit("/", 1)[-1].split("?", 1)[0]
    name = unquote(name)
    if name.lower().startswith("file:"):
        name = name[5:]
    name = name.lstrip(":")
    name = re.sub(r"\.(jpe?g|png|tiff?|webp|gif|bmp)$", "", name, flags=re.I)
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")

    # Non-Latin titles (Arabic/Romanian) can reduce to nothing useful, and an
    # 80-char cut can leave a meaningless stub like "3". Fall back to the stable
    # image_id in those cases so files stay identifiable and collision-free.
    if len(s) < 6:
        return rec["image_id"][:80]
    if len(s) >= 80 and s.endswith("_"):
        s = s.rstrip("_")
    return s[:80]


def run(limit, per_site, dry_run, manifest):
    # ---- build the attempt plan: round-robin across monuments so a small
    # ---- test still spans many monuments instead of exhausting the first few.
    per_site_cap = Counter()

    eligible, rejected = 0, Counter()
    for site in manifest:
        for rec in site["images"]:
            why = preflight(rec)
            if why:
                rejected[why.split(":")[0]] += 1
                rec["_reject"] = why
            else:
                eligible += 1

    print(f"candidates      : {sum(len(s['images']) for s in manifest)}")
    print(f"eligible        : {eligible}")
    print(f"pre-flight reject: {sum(rejected.values())}")
    for k, v in rejected.most_common():
        print(f"    - {k}: {v}")

    # round-robin ordering
    order = []
    depth = 0
    while True:
        added = False
        for site in manifest:
            imgs = [i for i in site["images"] if "_reject" not in i]
            if depth < len(imgs):
                order.append(imgs[depth])
                added = True
        if not added:
            break
        depth += 1

    seen_hash = set()
    stats = Counter()
    licences = Counter()
    sites_hit = set()
    attempted = 0
    deferred = []      # items skipped due to throttling, retried on a later pass
    max_consecutive_throttle = 0

    if dry_run:
        print(f"\n[DRY RUN] would attempt {min(limit, len(order))} of {len(order)} eligible")
        return

    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    # ---- resume: seed the duplicate-detection set from what is already on disk
    for site in manifest:
        for rec in site["images"]:
            if rec.get("downloaded") and rec.get("local_path"):
                fp = ROOT / rec["local_path"]
                if fp.exists() and rec.get("sha256"):
                    seen_hash.add(rec["sha256"])
                    stats["already_done"] += 1

    if stats["already_done"]:
        print(f"resuming: {stats['already_done']} images already on disk\n")

    def attempt(rec):
        """Download one record. Returns one of: ok / failed / throttled."""
        nonlocal attempted
        sid = rec["_site_id"]
        attempted += 1
        data, err = fetch(rec["commons_file_url"])

        if err or not data:
            if err and "throttled" in err:
                rec.update(downloaded=False, local_path=None, file_size=None,
                           mime_type=None, download_error=err)
                return "throttled"
            rec.update(downloaded=False, local_path=None, file_size=None,
                       mime_type=None, download_error=err or "empty_response")
            stats["failed"] += 1
            print(f"  [{attempted}] FAIL {rec['image_id']}: {err}")
            return "failed"

        if len(data) < MIN_BYTES:
            rec.update(downloaded=False, local_path=None, file_size=len(data),
                       mime_type=None, download_error=f"too_small:{len(data)}b")
            stats["invalid"] += 1
            stats["failed"] += 1
            print(f"  [{attempted}] INVALID {rec['image_id']}: {len(data)} bytes")
            return "failed"

        if len(data) > MAX_BYTES:
            rec.update(downloaded=False, local_path=None, file_size=len(data),
                       mime_type=None, download_error=f"too_large:{len(data)}b")
            stats["invalid"] += 1
            stats["failed"] += 1
            print(f"  [{attempted}] INVALID {rec['image_id']}: too large")
            return "failed"

        mime, ext, w, h = sniff_image(data)
        if not mime:
            rec.update(downloaded=False, local_path=None, file_size=len(data),
                       mime_type=None, download_error="not_an_image")
            stats["invalid"] += 1
            stats["failed"] += 1
            print(f"  [{attempted}] NON-IMAGE {rec['image_id']}")
            return "failed"

        if w < MIN_WIDTH or h < MIN_HEIGHT:
            rec.update(downloaded=False, local_path=None, file_size=len(data),
                       mime_type=mime, download_error=f"below_min:{w}x{h}")
            stats["invalid"] += 1
            stats["failed"] += 1
            print(f"  [{attempted}] TOO SMALL {rec['image_id']}: {w}x{h}")
            return "failed"

        digest = hashlib.sha256(data).hexdigest()
        if digest in seen_hash:
            rec.update(downloaded=False, local_path=None, file_size=len(data),
                       mime_type=mime, download_error=f"duplicate_content:{digest[:12]}")
            stats["duplicate"] += 1
            stats["failed"] += 1
            print(f"  [{attempted}] DUPLICATE {rec['image_id']}")
            return "failed"

        site_dir = RAW_ROOT / sid
        site_dir.mkdir(parents=True, exist_ok=True)
        dest = site_dir / f"{slugify(rec)}{ext}"
        n = 2
        while dest.exists():
            dest = site_dir / f"{slugify(rec)}_{n}{ext}"
            n += 1
        dest.write_bytes(data)

        seen_hash.add(digest)
        rel = dest.relative_to(ROOT).as_posix()
        rec.update(downloaded=True, local_path=rel, file_size=len(data),
                   mime_type=mime, download_error=None,
                   sha256=digest, width_local=w, height_local=h)
        stats["downloaded"] += 1
        stats["bytes"] += len(data)
        licences[rec["license"]] += 1
        sites_hit.add(sid)
        per_site_cap[sid] += 1
        print(f"  [{attempted}] OK {rec['image_id']} -> {rel} ({w}x{h}, {len(data)//1024} KB)")
        # Checkpoint after every success. The run can be long and the upstream
        # host throttles hard, so a kill must never orphan a downloaded file.
        write_manifest(manifest)
        return "ok"

    # The upstream throttle is INTERMITTENT: within one sweep some URLs return
    # 200 and others 429. So a single 429 must not end the run - we defer the
    # item and keep going, then sweep the deferred set again on later passes.
    queue = list(order)
    deferred = []
    sweep = 0
    for sweep in range(MAX_SWEEPS):
        deferred = []
        consecutive = 0
        made_progress = False
        while queue:
            rec = queue.pop(0)
            if stats["downloaded"] >= limit:
                break
            sid = rec["_site_id"]
            if per_site_cap[sid] >= per_site:
                continue
            if rec.get("downloaded") and rec.get("local_path") and (ROOT / rec["local_path"]).exists():
                continue

            result = attempt(rec)

            if result == "throttled":
                deferred.append(rec)
                consecutive += 1
                max_consecutive_throttle = max(max_consecutive_throttle, consecutive)
                if consecutive >= THROTTLE_STOP_AFTER:
                    # long hard block: pause, then resume rather than abort
                    consecutive = 0
                    time.sleep(THROTTLE_COOLDOWN)
                    stats["cooldowns"] += 1
            else:
                consecutive = 0
                if result == "ok":
                    made_progress = True
                    time.sleep(DELAY)

        if stats["downloaded"] >= limit or not deferred:
            break
        if not made_progress and stats["cooldowns"] >= MAX_COOLDOWNS:
            print(f"\n  !! no progress after {stats['cooldowns']} cooldowns; "
                  f"stopping and deferring {len(deferred)} items")
            break
        print(f"  -- sweep {sweep+1} done: {stats['downloaded']} downloaded, "
              f"retrying {len(deferred)} throttled items")
        queue = deferred
        # re-open a per-site slot for each deferred item so it can be retried
        for r in queue:
            per_site_cap[r["_site_id"]] = max(0, per_site_cap[r["_site_id"]] - 1)

    stats["deferred"] = len(deferred)
    stats["sweeps"] = sweep + 1
    write_manifest(manifest)
    return manifest, stats, licences, sites_hit, attempted, order, deferred


def write_manifest(manifest):
    """Write a clean copy to disk without stripping internal keys in memory."""
    clean = []
    for site in manifest:
        clean_site = {"site_id": site["site_id"], "name": site.get("name"),
                      "city": site.get("city"), "country": site.get("country"),
                      "image_count": site.get("image_count")}
        clean_images = []
        for rec in site["images"]:
            r = {k: v for k, v in rec.items() if not k.startswith("_")}
            r.setdefault("downloaded", False)
            r.setdefault("local_path", None)
            r.setdefault("file_size", None)
            r.setdefault("mime_type", None)
            r.setdefault("download_error", None)
            clean_images.append(r)
        clean_site["images"] = clean_images
        clean.append(clean_site)
    tmp = MANIFEST_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(MANIFEST_PATH)


def tag_sites(manifest):
    for site in manifest:
        for rec in site["images"]:
            rec["_site_id"] = site["site_id"]


def reconcile(manifest):
    """Re-adopt image files on disk that the manifest does not know about.

    A killed run (or any crash between writing a file and checkpointing the
    manifest) leaves real images that must not be silently re-downloaded or
    lost. We match each orphan back to its source record via the site folder
    plus the decoded Commons filename.
    """
    if not RAW_ROOT.exists():
        return 0, 0

    known = {r["local_path"] for s in manifest for r in s["images"] if r.get("local_path")}
    orphans = []
    for dp, _dn, fn in os.walk(RAW_ROOT):
        for f in fn:
            fp = Path(dp) / f
            rel = fp.relative_to(ROOT).as_posix()
            if rel not in known:
                orphans.append((fp, rel))
    if not orphans:
        return 0, 0

    # index records by (site_id, slug) so orphans can be matched back
    index = {}
    for s in manifest:
        for r in s["images"]:
            index.setdefault((s["site_id"], slugify(r)), r)

    adopted = unknown = 0
    for fp, rel in orphans:
        site_id = Path(rel).parent.name
        stem = fp.stem
        rec = index.get((site_id, stem))
        if rec is None:
            # fall back to a suffix match (slug truncated -> "name_2")
            for (sid, slug), r in index.items():
                if sid == site_id and (stem == slug or stem.rsplit("_", 1)[0] == slug):
                    rec = r
                    break
        data = fp.read_bytes()
        mime, _ext, w, h = sniff_image(data)
        if rec is None:
            unknown += 1
            print(f"  orphan (no manifest match): {rel}")
            continue
        rec.update(downloaded=True, local_path=rel, file_size=len(data),
                   mime_type=mime, download_error=None,
                   sha256=hashlib.sha256(data).hexdigest(),
                   width_local=w, height_local=h)
        adopted += 1
        print(f"  re-adopted: {rel} -> {rec['image_id']} ({w}x{h}, {len(data)//1024} KB)")

    return adopted, unknown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--per-site", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reconcile-only", action="store_true")
    a = ap.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tag_sites(manifest)

    adopted, unknown = reconcile(manifest)
    if adopted or unknown:
        write_manifest(manifest)
        print(f"reconcile: adopted={adopted} unmatched={unknown}\n")

    if a.reconcile_only:
        return 0

    result = run(a.limit, a.per_site, a.dry_run, manifest)
    if result is None:
        return 0
    _, stats, licences, sites_hit, attempted, order, deferred = result

    print("\n" + "=" * 62)
    print("PHASE 2 TEST SUMMARY")
    print("=" * 62)
    print(f"attempted          : {attempted}")
    print(f"downloaded         : {stats['downloaded']}")
    print(f"failed (content)   : {stats['failed']}")
    print(f"  invalid/non-image: {stats['invalid']}")
    print(f"  duplicates       : {stats['duplicate']}")
    print(f"deferred (throttle): {stats['deferred']}  <- NOT content failures, retry later")
    print(f"already on disk    : {stats['already_done']}")
    print(f"monuments covered  : {len(sites_hit)}")
    print(f"disk bytes         : {stats['bytes']:,} ({stats['bytes']/1024/1024:.2f} MB)")
    print("licences           :")
    for k, v in licences.most_common():
        print(f"    {v:4d}  {k}")
    if deferred:
        print("\nthrottled sample (will be retried once the limit clears):")
        for r in deferred[:8]:
            print(f"    {r['image_id']}  {r['download_error']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())