"""
Isolated Experiment: Site-Level FAISS Competitor Margin vs Vector-Level Margin
Evaluates the impact of grouping vectors by site_id before margin calculation.
Preserves production thresholds: Similarity >= 0.85, Competitor margin >= 0.10.
Does NOT modify any production files or the production FAISS index.
"""

import io
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageEnhance

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.heritage_service import build_service

SIMILARITY_THRESHOLD = 0.85
MARGIN_THRESHOLD = 0.10

CATALOG_MONUMENTS = [
    ("taj_mahal", "Taj Mahal"),
    ("ajanta_caves", "Ajanta Caves"),
    ("qutub_minar", "Qutub Minar"),
    ("red_fort_delhi", "Red Fort"),
    ("konark_sun_temple", "Konark Sun Temple"),
    ("jama_masjid_delhi", "Jama Masjid"),
]


def load_dataset() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Build the catalog and unknown/confusing evaluation datasets."""
    monument_sources = {
        "taj_mahal": [
            Path("data/raw/taj_mahal/taj_mahal_01.jpg"),
            Path("data/raw/taj_mahal/taj_mahal_02.jpg"),
            Path("data/raw/taj_mahal/taj_mahal_03.jpg"),
            Path("frontend/assets/images/slideshow/taj-mahal.jpg"),
        ],
        "ajanta_caves": [
            Path("data/raw/ajanta_caves/ajanta_caves_01.jpg"),
            Path("data/raw/ajanta_caves/ajanta_caves_02.jpg"),
            Path("data/raw/ajanta_caves/ajanta_caves_03.jpg"),
            Path("frontend/assets/images/sites/ajanta_caves.webp"),
        ],
        "qutub_minar": [
            Path("data/raw/qutub_minar/qutub_minar_01.jpg"),
            Path("data/raw/qutub_minar/qutub_minar_02.jpg"),
            Path("data/raw/qutub_minar/qutub_minar_03.jpg"),
            Path("frontend/assets/images/sites/qutub_minar.webp"),
        ],
        "red_fort_delhi": [
            Path("data/raw/red_fort/red_fort_01.jpg"),
            Path("data/raw/red_fort/red_fort_02.jpg"),
            Path("data/raw/red_fort/red_fort_03.jpg"),
            Path("frontend/assets/images/sites/red_fort.webp"),
        ],
        "konark_sun_temple": [
            Path("data/raw/konark_sun_temple/konark_sun_temple_01.jpg"),
            Path("data/raw/konark_sun_temple/konark_sun_temple_02.jpg"),
            Path("data/raw/konark_sun_temple/konark_sun_temple_03.jpg"),
            Path("frontend/assets/images/sites/konark_sun_temple.webp"),
        ],
        "jama_masjid_delhi": [
            Path("data/raw/jama_masjid/jama_masjid_01.jpg"),
            Path("frontend/assets/images/gallery/jama_masjid/01-lg.webp"),
            Path("frontend/assets/images/sites/jama_masjid.webp"),
        ],
    }

    catalog_tests = []
    for site_id, site_name in CATALOG_MONUMENTS:
        sources = monument_sources.get(site_id, [])
        for src_path in sources:
            if not src_path.exists():
                continue
            with Image.open(src_path) as img:
                orig = img.convert("RGB")
                catalog_tests.append({
                    "expected_id": site_id,
                    "expected_name": site_name,
                    "desc": f"{src_path.name} (orig)",
                    "image": orig.copy(),
                })

                # 70% center crop
                w, h = orig.size
                crop_box = (int(w * 0.15), int(h * 0.15), int(w * 0.85), int(h * 0.85))
                catalog_tests.append({
                    "expected_id": site_id,
                    "expected_name": site_name,
                    "desc": f"{src_path.name} (crop 70%)",
                    "image": orig.crop(crop_box),
                })

                # Brightness +20%
                enhancer = ImageEnhance.Brightness(orig)
                catalog_tests.append({
                    "expected_id": site_id,
                    "expected_name": site_name,
                    "desc": f"{src_path.name} (bright +20%)",
                    "image": enhancer.enhance(1.2),
                })

    # Unknown and confusing non-catalog candidates
    unknown_sources = [
        ("Colosseum (Uncatalogued Wonder)", Path("frontend/assets/images/slideshow/colosseum.jpg")),
        ("Machu Picchu (Uncatalogued Wonder)", Path("frontend/assets/images/slideshow/machu-picchu.jpg")),
        ("Great Wall of China (Uncatalogued Wonder)", Path("frontend/assets/images/slideshow/great-wall.jpg")),
        ("Petra (Uncatalogued Wonder)", Path("frontend/assets/images/slideshow/petra.jpg")),
        ("Chichen Itza (Uncatalogued Wonder)", Path("frontend/assets/images/slideshow/chichen-itza.jpg")),
        ("Christ the Redeemer (Uncatalogued Wonder)", Path("frontend/assets/images/slideshow/christ-redeemer.jpg")),
        ("Abu Simbel (Confusing Sacred Temple)", Path("data/raw/global/abu_simbel/Abu_Simbel_Temples.jpg")),
        ("Adziubzha Church (Confusing Historic Church)", Path("data/raw/global/adziubzha_church_georgia/File_3AAdzubja_church.jpg")),
        ("Akhutsa Fortress (Confusing Ruined Fortress)", Path("data/raw/global/akhutsa_fortress_abkhazia/Akhutsa_Fortress_01.jpg")),
        ("Ambara Church (Confusing Ancient Church)", Path("data/raw/global/ambara_church_georgia/Mussera.jpg")),
        ("Casbah of Algiers (Confusing Historic Architecture)", Path("data/raw/global/category_casbah_of_algiers_algeria/20141113-_DSC0030-3__15886832612.jpg")),
    ]

    unknown_tests = []
    for label, path in unknown_sources:
        if path.exists():
            with Image.open(path) as img:
                unknown_tests.append({
                    "label": label,
                    "image": img.convert("RGB"),
                    "is_unknown": True,
                })

    # Synthetic non-heritage graphic
    synth = Image.new("RGB", (300, 300), color=(180, 200, 220))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(synth)
    draw.rectangle([50, 50, 250, 250], fill=(70, 80, 90), outline=(255, 0, 0), width=4)
    draw.text((70, 140), "NON-HERITAGE TEST OBJECT", fill=(255, 255, 255))
    unknown_tests.append({
        "label": "Synthetic Non-Heritage Graphic",
        "image": synth,
        "is_unknown": True,
    })

    return catalog_tests, unknown_tests


def run_experiment():
    print("=" * 70)
    print("ISOLATED EXPERIMENT: SITE-LEVEL VS. VECTOR-LEVEL FAISS MARGIN")
    print("=" * 70)

    service = build_service()
    extractor = service.extractor
    confidence_layer = service.confidence_layer
    index = confidence_layer.index

    catalog_tests, unknown_tests = load_dataset()
    print(f"Catalog test instances: {len(catalog_tests)}")
    print(f"Unknown/confusing test instances: {len(unknown_tests)}")

    # We evaluate 3 methods:
    # 1. Vector-Level Baseline (K=5): Margin = Sim(v1) - Sim(v2)
    # 2. Site-Level (K=5): Group K=5 by site_id, Margin = TopSite.best - 2ndSite.best
    # 3. Site-Level Expanded (K=20): Group K=20 by site_id, Margin = TopSite.best - 2ndSite.best

    methods = ["Vector_Level_K5", "Site_Level_K5", "Site_Level_K20"]
    eval_results = {m: {"catalog": [], "unknown": []} for m in methods}

    # Temporary buffer for saving image to pass to extractor
    temp_img_path = Path("experiments/_temp_query.jpg")

    def evaluate_query(img: Image.Image, expected_id: Optional[str] = None):
        img.save(temp_img_path, format="JPEG", quality=90)
        emb = extractor.extract(temp_img_path)

        # Retrieve top 20 vectors from FAISS
        scores, indices = index.search(emb.astype(np.float32).reshape(1, -1), 20)
        retrieved = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            retrieved.append({
                "image_id": confidence_layer.image_ids[idx],
                "site_id": confidence_layer._site_ids[idx],
                "similarity": float(score),
            })

        # --- Method 1: Vector-Level Baseline (K=5) ---
        top5 = retrieved[:5]
        v1_sim = top5[0]["similarity"] if top5 else 0.0
        v1_site = top5[0]["site_id"] if top5 else "unknown"
        v2_sim = top5[1]["similarity"] if len(top5) > 1 else 0.0
        vec_margin = round(v1_sim - v2_sim, 6)
        vec_confirmed = (v1_sim >= SIMILARITY_THRESHOLD and vec_margin >= MARGIN_THRESHOLD)

        # --- Method 2: Site-Level (K=5) ---
        site_max_k5 = defaultdict(float)
        for r in top5:
            site_max_k5[r["site_id"]] = max(site_max_k5[r["site_id"]], r["similarity"])
        sorted_sites_k5 = sorted(site_max_k5.items(), key=lambda x: x[1], reverse=True)
        s1_site_k5, s1_sim_k5 = sorted_sites_k5[0] if sorted_sites_k5 else ("unknown", 0.0)
        s2_sim_k5 = sorted_sites_k5[1][1] if len(sorted_sites_k5) > 1 else 0.0
        site_margin_k5 = round(s1_sim_k5 - s2_sim_k5 if len(sorted_sites_k5) > 1 else float("inf"), 6)
        site_confirmed_k5 = (s1_sim_k5 >= SIMILARITY_THRESHOLD and (site_margin_k5 >= MARGIN_THRESHOLD or math.isinf(site_margin_k5)))

        # --- Method 3: Site-Level Expanded (K=20) ---
        site_max_k20 = defaultdict(float)
        for r in retrieved:
            site_max_k20[r["site_id"]] = max(site_max_k20[r["site_id"]], r["similarity"])
        sorted_sites_k20 = sorted(site_max_k20.items(), key=lambda x: x[1], reverse=True)
        s1_site_k20, s1_sim_k20 = sorted_sites_k20[0] if sorted_sites_k20 else ("unknown", 0.0)
        s2_site_k20, s2_sim_k20 = sorted_sites_k20[1] if len(sorted_sites_k20) > 1 else ("none", 0.0)
        site_margin_k20 = round(s1_sim_k20 - s2_sim_k20 if len(sorted_sites_k20) > 1 else float("inf"), 6)
        site_confirmed_k20 = (s1_sim_k20 >= SIMILARITY_THRESHOLD and (site_margin_k20 >= MARGIN_THRESHOLD or math.isinf(site_margin_k20)))

        return {
            "Vector_Level_K5": {
                "pred_site": v1_site,
                "top_sim": v1_sim,
                "second_sim": v2_sim,
                "margin": vec_margin,
                "confirmed": vec_confirmed,
                "correct": (v1_site == expected_id) if expected_id else False,
            },
            "Site_Level_K5": {
                "pred_site": s1_site_k5,
                "top_sim": s1_sim_k5,
                "second_sim": s2_sim_k5,
                "margin": site_margin_k5,
                "confirmed": site_confirmed_k5,
                "correct": (s1_site_k5 == expected_id) if expected_id else False,
            },
            "Site_Level_K20": {
                "pred_site": s1_site_k20,
                "second_site": s2_site_k20,
                "top_sim": s1_sim_k20,
                "second_sim": s2_sim_k20,
                "margin": site_margin_k20,
                "confirmed": site_confirmed_k20,
                "correct": (s1_site_k20 == expected_id) if expected_id else False,
            },
        }

    # Evaluate catalog tests
    print("\nEvaluating catalog tests...")
    for idx, test in enumerate(catalog_tests):
        res = evaluate_query(test["image"], test["expected_id"])
        for m in methods:
            eval_results[m]["catalog"].append({
                "expected_id": test["expected_id"],
                "expected_name": test["expected_name"],
                "desc": test["desc"],
                **res[m],
            })

    # Evaluate unknown tests
    print("Evaluating unknown & confusing non-catalog tests...")
    for idx, test in enumerate(unknown_tests):
        res = evaluate_query(test["image"], expected_id=None)
        for m in methods:
            eval_results[m]["unknown"].append({
                "label": test["label"],
                **res[m],
            })

    # Clean up temp file
    if temp_img_path.exists():
        temp_img_path.unlink()

    # ── METRIC COMPUTATIONS ──────────────────────────────────────────────────
    metrics = {}
    for m in methods:
        cat = eval_results[m]["catalog"]
        unk = eval_results[m]["unknown"]
        
        total_cat = len(cat)
        correct_and_confirmed = sum(1 for x in cat if x["correct"] and x["confirmed"])
        top1_correct = sum(1 for x in cat if x["correct"])
        confirmed_cat = sum(1 for x in cat if x["confirmed"])
        rejected_cat = sum(1 for x in cat if not x["confirmed"])
        
        # Per-monument stats
        by_mon = defaultdict(list)
        for x in cat:
            by_mon[x["expected_id"]].append(x)
        
        per_mon_stats = {}
        for sid, tests in by_mon.items():
            mon_total = len(tests)
            mon_top1 = sum(1 for t in tests if t["correct"])
            mon_confirmed = sum(1 for t in tests if t["correct"] and t["confirmed"])
            avg_margin = sum(t["margin"] if not math.isinf(t["margin"]) else 1.0 for t in tests) / mon_total
            avg_sim = sum(t["top_sim"] for t in tests) / mon_total
            per_mon_stats[sid] = {
                "total": mon_total,
                "top1_acc": round(mon_top1 / mon_total * 100, 2),
                "confirmed": mon_confirmed,
                "confirmed_pct": round(mon_confirmed / mon_total * 100, 2),
                "avg_sim": round(avg_sim, 4),
                "avg_margin": round(avg_margin, 4),
            }

        # Unknown and confusing stats
        total_unk = len(unk)
        false_accepts = sum(1 for u in unk if u["confirmed"])
        unknown_rejected = sum(1 for u in unk if not u["confirmed"])
        far = round(false_accepts / total_unk * 100, 2)
        urr = round(unknown_rejected / total_unk * 100, 2)

        # Confusion rejection (specifically architectural confusing sites vs non-heritage)
        confusing_tests = [u for u in unk if "Confusing" in u["label"]]
        confusing_rejected = sum(1 for u in confusing_tests if not u["confirmed"])
        crr = round(confusing_rejected / len(confusing_tests) * 100, 2) if confusing_tests else 100.0

        metrics[m] = {
            "total_catalog": total_cat,
            "overall_accuracy_pct": round(correct_and_confirmed / total_cat * 100, 2),
            "top1_match_pct": round(top1_correct / total_cat * 100, 2),
            "confirmed_matches": confirmed_cat,
            "rejected_matches": rejected_cat,
            "false_acceptance_rate_pct": far,
            "unknown_rejection_rate_pct": urr,
            "confusion_rejection_rate_pct": crr,
            "per_monument": per_mon_stats,
        }

    # Print Comparison Table
    print("\n" + "=" * 80)
    print(f"{'METRIC':<32} | {'VECTOR-LEVEL (K=5)':<18} | {'SITE-LEVEL (K=5)':<18} | {'SITE-LEVEL (K=20)':<18}")
    print("-" * 80)
    print(f"{'Overall Confirmed Acc':<32} | {metrics['Vector_Level_K5']['overall_accuracy_pct']:>16.1f}% | {metrics['Site_Level_K5']['overall_accuracy_pct']:>16.1f}% | {metrics['Site_Level_K20']['overall_accuracy_pct']:>16.1f}%")
    print(f"{'Confirmed Matches':<32} | {metrics['Vector_Level_K5']['confirmed_matches']:>14}/{metrics['Vector_Level_K5']['total_catalog']} | {metrics['Site_Level_K5']['confirmed_matches']:>14}/{metrics['Site_Level_K5']['total_catalog']} | {metrics['Site_Level_K20']['confirmed_matches']:>14}/{metrics['Site_Level_K20']['total_catalog']}")
    print(f"{'Safe Rejections':<32} | {metrics['Vector_Level_K5']['rejected_matches']:>16} | {metrics['Site_Level_K5']['rejected_matches']:>16} | {metrics['Site_Level_K20']['rejected_matches']:>16}")
    print(f"{'False Acceptance Rate (FAR)':<32} | {metrics['Vector_Level_K5']['false_acceptance_rate_pct']:>16.1f}% | {metrics['Site_Level_K5']['false_acceptance_rate_pct']:>16.1f}% | {metrics['Site_Level_K20']['false_acceptance_rate_pct']:>16.1f}%")
    print(f"{'Unknown Rejection Rate (URR)':<32} | {metrics['Vector_Level_K5']['unknown_rejection_rate_pct']:>16.1f}% | {metrics['Site_Level_K5']['unknown_rejection_rate_pct']:>16.1f}% | {metrics['Site_Level_K20']['unknown_rejection_rate_pct']:>16.1f}%")
    print(f"{'Confusion Rejection Rate (CRR)':<32} | {metrics['Vector_Level_K5']['confusion_rejection_rate_pct']:>16.1f}% | {metrics['Site_Level_K5']['confusion_rejection_rate_pct']:>16.1f}% | {metrics['Site_Level_K20']['confusion_rejection_rate_pct']:>16.1f}%")
    print("-" * 80)
    print("PER-MONUMENT CONFIRMED MATCH RATE:")
    for sid, name in CATALOG_MONUMENTS:
        vm = metrics['Vector_Level_K5']['per_monument'][sid]['confirmed_pct']
        sm5 = metrics['Site_Level_K5']['per_monument'][sid]['confirmed_pct']
        sm20 = metrics['Site_Level_K20']['per_monument'][sid]['confirmed_pct']
        print(f"  {name:<28} | {vm:>16.1f}% | {sm5:>16.1f}% | {sm20:>16.1f}%")
    print("=" * 80)

    # Detailed inspection of Taj Mahal and Red Fort changes
    print("\nTAJ MAHAL DETAILED COMPARISON:")
    taj_v = [x for x in eval_results["Vector_Level_K5"]["catalog"] if x["expected_id"] == "taj_mahal"]
    taj_s20 = [x for x in eval_results["Site_Level_K20"]["catalog"] if x["expected_id"] == "taj_mahal"]
    for tv, ts in zip(taj_v, taj_s20):
        v_status = "CONFIRMED" if tv["confirmed"] else "REJECTED"
        s_status = "CONFIRMED" if ts["confirmed"] else "REJECTED"
        print(f"  {tv['desc']:<30} | Vec: sim={tv['top_sim']:.4f}, margin={tv['margin']:.4f} ({v_status}) -> Site: margin={ts['margin']:.4f} ({s_status})")

    print("\nRED FORT DETAILED COMPARISON:")
    rf_v = [x for x in eval_results["Vector_Level_K5"]["catalog"] if x["expected_id"] == "red_fort_delhi"]
    rf_s20 = [x for x in eval_results["Site_Level_K20"]["catalog"] if x["expected_id"] == "red_fort_delhi"]
    for rv, rs in zip(rf_v, rf_s20):
        v_status = "CONFIRMED" if rv["confirmed"] else "REJECTED"
        s_status = "CONFIRMED" if rs["confirmed"] else "REJECTED"
        print(f"  {rv['desc']:<30} | Vec: sim={rv['top_sim']:.4f}, margin={rv['margin']:.4f} ({v_status}) -> Site: margin={rs['margin']:.4f} ({s_status})")

    # Check regressions (cases where Vector was Confirmed Correct, but Site became Rejected)
    regressions = []
    cat_v = eval_results["Vector_Level_K5"]["catalog"]
    cat_s = eval_results["Site_Level_K20"]["catalog"]
    for cv, cs in zip(cat_v, cat_s):
        if cv["confirmed"] and not cs["confirmed"]:
            regressions.append({"desc": cv["desc"], "vec": cv, "site": cs})

    print(f"\nRegressions (previously confirmed became rejected): {len(regressions)}")
    for r in regressions:
        print(f"  REGRESSION: {r['desc']}")

    # Save raw results
    out_file = Path("experiments/experiment_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metrics": metrics,
            "regressions": regressions,
            "results": eval_results,
        }, f, indent=2)
    print(f"\nRaw experiment results persisted to {out_file}")


if __name__ == "__main__":
    run_experiment()

