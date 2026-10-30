#!/usr/bin/env python3
"""
Build worldwide evidence layer from global_monument_catalogue.json.

Reads the catalogue and writes:
  data/evidence/heritage_evidence.json   — claims + sources per site_id
  data/evidence/heritage_metadata.json  — structured metadata per site_id

Run with:
    C:/Users/humai/AppData/Local/Python/bin/python3.14.exe backend/build_worldwide_evidence.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PATH = ROOT / "data" / "metadata" / "global_monument_catalogue.json"
EVIDENCE_PATH = ROOT / "data" / "evidence" / "heritage_evidence.json"
METADATA_PATH = ROOT / "data" / "evidence" / "heritage_metadata.json"


def build() -> None:
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        catalogue = json.load(f)

    metadata: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []

    for record in catalogue:
        site_id = record.get("site_id")
        if not site_id:
            continue

        # ── metadata ──────────────────────────────────────────────────────
        meta = {
            "id": site_id,
            "name": record.get("name", ""),
            "alternate_name": record.get("alternate_names", [None])[0] if record.get("alternate_names") else "",
            "location": record.get("city", ""),
            "state": record.get("region", ""),
            "country": record.get("country", ""),
            "category": record.get("type", ""),
            "preservation_context": record.get("heritage_status", ""),
            "description": record.get("description", ""),
            "historical_period": record.get("period", ""),
        }
        metadata.append(meta)

        # ── evidence: extract factual claims from record fields ─────────────
        claims: List[Dict[str, str]] = []

        # Use description if available, otherwise use historical significance
        desc_text = record.get("description") or record.get("historical_significance") or ""

        if desc_text:
            claims.append({
                "site_id": site_id,
                "claim": f"The {record.get('name', site_id)}: {desc_text}",
                "source_name": record.get("sources", [{}])[0].get("title", "Catalogue record") if record.get("sources") else "Catalogue record",
                "source_url": record.get("sources", [{}])[0].get("url", "") if record.get("sources") else "",
            })

        if record.get("historical_significance"):
            src = record.get("sources", [{}])[0] if record.get("sources") else {}
            claims.append({
                "site_id": site_id,
                "claim": f"Historical significance of {record.get('name', site_id)}: {record['historical_significance']}",
                "source_name": src.get("title", "Historical record"),
                "source_url": src.get("url", ""),
            })

        if record.get("architectural_features"):
            src = record.get("sources", [{}])[0] if record.get("sources") else {}
            claims.append({
                "site_id": site_id,
                "claim": f"Architectural features of {record.get('name', site_id)}: {record['architectural_features']}",
                "source_name": src.get("title", "Architectural record"),
                "source_url": src.get("url", ""),
            })

        # Fallback if no rich fields populated
        if not claims:
            # At minimum create a claim from the name and sources
            sources = record.get("sources", [])
            claim_text = f"Record for {record.get('name', site_id)}"
            if sources:
                src = sources[0]
                claims.append({
                    "site_id": site_id,
                    "claim": claim_text,
                    "source_name": src.get("title", "Catalogue record"),
                    "source_url": src.get("url", ""),
                })
            else:
                claims.append({
                    "site_id": site_id,
                    "claim": claim_text,
                    "source_name": "Catalogue record",
                    "source_url": "",
                })

        evidence.extend(claims)

    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=1)
        f.write("\n")
    print(f"Wrote {len(evidence)} evidence entries to {EVIDENCE_PATH}")

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=1)
        f.write("\n")
    print(f"Wrote {len(metadata)} metadata entries to {METADATA_PATH}")


if __name__ == "__main__":
    build()