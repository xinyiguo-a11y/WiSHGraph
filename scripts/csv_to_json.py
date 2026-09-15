#!/usr/bin/env python3
"""
csv_to_json.py
--------------
Converts WishGraph metadata CSV into structured JSON for ontology population.
Produces: output/wishgraph_cases.json

Each row in the CSV becomes a CyberWishingCase with all linked entities.
"""

import csv
import json
import re
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/metadata.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../output/wishgraph_cases.json")

# Field names as in CSV header (normalized)
FIELD_MAP = {
    "person": "person",
    "创造主体 (person)": "person",
    "压力 / 需求 (press)": "pressure",
    "赛博法器 / 神祇 (product)": "cyberProduct",
    "对齐目标 ( cultural/ritual target)": "culturalTarget",
    "数字实践 / 行为 (digital practice)": "digitalPractice",
    "传播平台 (platform)": "platform",
    "g: 数字转化机制 (digital transformation)": "transformationMechanism",
    "情绪功能 (affective function)": "affectiveFunction",
    "梗功能 (meme function)": "memeFunction",
    "仪式 / 视觉符号 (ritual or visual symbol)": "ritualSymbol",
    "证据链接 (source url)": "sourceURL",
    "来源类型 (source type)": "sourceType",
}


def normalize_key(key: str) -> str:
    return key.strip().lower()


def make_id(text: str, index: int) -> str:
    """Generate a URL-safe ID from text."""
    base = re.sub(r"[^a-zA-Z0-9]+", "_", text[:30]).strip("_").lower()
    return f"case_{index:02d}_{base}" if base else f"case_{index:02d}"


def parse_list_field(value: str) -> list:
    """Split comma/semicolon separated values into a list."""
    if not value or not value.strip():
        return []
    parts = re.split(r"[;,\n]+", value)
    return [p.strip() for p in parts if p.strip()]


def main():
    cases = []
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        # Build a mapping from actual CSV column -> our field name
        col_map = {}
        for h in headers:
            nk = normalize_key(h)
            if nk in FIELD_MAP:
                col_map[h] = FIELD_MAP[nk]

        for idx, row in enumerate(reader, start=1):
            # Skip completely empty rows
            if not any(v and v.strip() for v in row.values()):
                continue

            case = {}
            for col, field in col_map.items():
                raw = row.get(col, "").strip()
                if field in ("platform", "digitalPractice", "affectiveFunction",
                             "memeFunction", "ritualSymbol", "transformationMechanism"):
                    case[field] = parse_list_field(raw)
                else:
                    case[field] = raw

            # Generate stable ID
            person_val = case.get("person", "")
            case["id"] = make_id(person_val, idx)
            case["caseIndex"] = idx

            # Ensure all expected fields exist
            for field in FIELD_MAP.values():
                if field not in case:
                    case[field] = "" if field not in (
                        "platform", "digitalPractice", "affectiveFunction",
                        "memeFunction", "ritualSymbol", "transformationMechanism"
                    ) else []

            cases.append(case)

    output = {
        "ontologyPrefix": "https://example.org/wishgraph#",
        "generated": "2026-05-08",
        "totalCases": len(cases),
        "cases": cases
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✓ Converted {len(cases)} cases → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
