import importlib.util, json, os, sys

spec = importlib.util.spec_from_file_location(
    "fmi", os.path.join(os.path.dirname(__file__), "fetch_monument_images.py"))
fmi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fmi)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAT = json.load(open(os.path.join(ROOT, "data", "metadata", "global_monument_catalogue.json"), encoding="utf-8"))
byid = {r["site_id"]: r for r in CAT}

FN = os.path.join(ROOT, "frontend_new")
m = json.load(open(os.path.join(FN, "assets", "images", "monuments", "image_manifest.json"), encoding="utf-8"))
imgs = m.get("images", {})
local = {f[:-5] for f in os.listdir(os.path.join(FN, "assets", "images", "sites")) if f.endswith(".webp")}
missing = sorted({r["site_id"] for r in CAT} - set(imgs) - local)

throttle = fmi.Throttle()
for sid in missing:
    rec = byid[sid]
    print("=" * 70)
    print(sid, "|", rec.get("name"))
    print("  distinctive:", fmi.distinctive(rec.get("name", "")))
    urls = [e.get("source_url") for e in (rec.get("images") or [])][:3]
    print("  catalogue urls:", len(urls))
    for u in urls:
        t = fmi.commons_title_from_url(u or "")
        print("     ->", t)
        if t:
            try:
                infos = fmi.imageinfo(throttle, [t])
            except Exception as exc:
                print("        API error:", exc)
                continue
            if not infos:
                print("        NO imageinfo returned")
                continue
            cand = fmi.candidate_from(infos[0])
            ok, reason = fmi.judge(cand, rec)
            print(f"        judge ok={ok} reason={reason}")
            print(f"        lic={cand['licence']!r} mime={cand['mime']} {cand['width']}x{cand['height']}")
            if not ok:
                bypass = reason == "title does not name the monument (wanted one of " \
                                 + str(fmi.distinctive(rec.get("name", ""))) + ")"
                print(f"        catalogue-curation bypass would allow? {bypass}")
