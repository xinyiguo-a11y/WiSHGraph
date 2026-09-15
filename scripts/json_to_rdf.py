#!/usr/bin/env python3
"""
json_to_rdf.py
--------------
Converts wishgraph_cases.json (A-Box instances) into Turtle RDF.
Produces: ontology/wishgraph_abox.ttl

Each CyberWishingCase is an OWL individual linked to all related entities.
"""

import json
import re
import os

JSON_PATH = os.path.join(os.path.dirname(__file__), "../output/wishgraph_cases.json")
TBOX_PATH = os.path.join(os.path.dirname(__file__), "../ontology/wishgraph_tbox.ttl")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../ontology/wishgraph_abox.ttl")
MERGED_PATH = os.path.join(os.path.dirname(__file__), "../ontology/wishgraph_full.ttl")

PREFIX = "https://example.org/wishgraph#"


def safe_id(text: str) -> str:
    """Make a URL-safe identifier from arbitrary text."""
    s = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "_", text.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:60] if s else "unnamed"


def turtle_literal(text: str) -> str:
    """Escape a string for Turtle triple-quoted literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def write_individual(lines, uri, rdf_type, label, description=""):
    lines.append(f"wg:{uri}")
    lines.append(f"    a wg:{rdf_type} ;")
    lines.append(f'    rdfs:label "{turtle_literal(label)}" ;')
    if description:
        lines.append(f'    wg:hasDescription "{turtle_literal(description)}" ;')
    # Remove trailing comma from last property
    last = lines[-1]
    if last.endswith(" ;"):
        lines[-1] = last[:-2] + " ."
    else:
        lines.append("    .")
    lines.append("")


def main():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    cases = data["cases"]
    lines = []

    # Prefixes
    lines += [
        "@prefix wg: <https://example.org/wishgraph#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        "# ─────────────────────────────────────────────────────────────────────────",
        "# WishGraph A-Box  –  Cyber-Wishing Case Instances",
        f"# Generated from {len(cases)} CSV rows | 2026-05-08",
        "# ─────────────────────────────────────────────────────────────────────────",
        "",
    ]

    # Collect entity registries to avoid duplicate individuals
    persons_written = set()
    pressures_written = set()
    products_written = set()
    targets_written = set()
    practices_written = set()
    platforms_written = set()
    mechanisms_written = set()
    affective_written = set()
    meme_written = set()
    symbols_written = set()

    case_blocks = []  # Store case triples to write after entities

    for case in cases:
        case_id = safe_id(case.get("id", f"case_{case['caseIndex']}"))
        person_label = case.get("person", "").strip()
        pressure_label = case.get("pressure", "").strip()
        product_label = case.get("cyberProduct", "").strip()
        target_label = case.get("culturalTarget", "").strip()
        source_url = case.get("sourceURL", "").strip()
        source_type = case.get("sourceType", "").strip()

        # --- Entity URIs ---
        person_id = safe_id(person_label) if person_label else None
        pressure_id = safe_id(pressure_label) if pressure_label else None
        product_id = safe_id(product_label) if product_label else None
        target_id = safe_id(target_label) if target_label else None
        source_id = f"src_{case_id}" if source_url or source_type else None

        # Write Person individual
        if person_id and person_id not in persons_written:
            write_individual(lines, person_id, "Person", person_label)
            persons_written.add(person_id)

        # Write Pressure individual
        if pressure_id and pressure_id not in pressures_written:
            write_individual(lines, pressure_id, "Pressure", pressure_label)
            pressures_written.add(pressure_id)

        # Write CyberProduct individual
        if product_id and product_id not in products_written:
            write_individual(lines, product_id, "CyberProduct", product_label)
            products_written.add(product_id)

        # Write CulturalTarget individual
        if target_id and target_id not in targets_written:
            write_individual(lines, target_id, "CulturalTarget", target_label)
            targets_written.add(target_id)

        # Write DigitalPractice individuals
        practice_ids = []
        for p in case.get("digitalPractice", []):
            pid = safe_id(p)
            if pid and pid not in practices_written:
                write_individual(lines, pid, "DigitalPractice", p)
                practices_written.add(pid)
            if pid:
                practice_ids.append(pid)

        # Write Platform individuals
        platform_ids = []
        for pl in case.get("platform", []):
            plid = safe_id(pl)
            if plid and plid not in platforms_written:
                write_individual(lines, plid, "Platform", pl)
                platforms_written.add(plid)
            if plid:
                platform_ids.append(plid)

        # Write TransformationMechanism individuals
        mechanism_ids = []
        for m in case.get("transformationMechanism", []):
            mid = safe_id(m)
            if mid and mid not in mechanisms_written:
                write_individual(lines, mid, "TransformationMechanism", m)
                mechanisms_written.add(mid)
            if mid:
                mechanism_ids.append(mid)

        # Write AffectiveFunction individuals
        affective_ids = []
        for a in case.get("affectiveFunction", []):
            aid = safe_id(a)
            if aid and aid not in affective_written:
                write_individual(lines, aid, "AffectiveFunction", a)
                affective_written.add(aid)
            if aid:
                affective_ids.append(aid)

        # Write MemeFunction individuals
        meme_ids = []
        for m in case.get("memeFunction", []):
            mid2 = safe_id(m)
            if mid2 and mid2 not in meme_written:
                write_individual(lines, mid2, "MemeFunction", m)
                meme_written.add(mid2)
            if mid2:
                meme_ids.append(mid2)

        # Write RitualSymbol individuals
        symbol_ids = []
        for s in case.get("ritualSymbol", []):
            sid = safe_id(s)
            if sid and sid not in symbols_written:
                write_individual(lines, sid, "RitualSymbol", s)
                symbols_written.add(sid)
            if sid:
                symbol_ids.append(sid)

        # Write Source individual
        if source_id:
            lines.append(f"wg:{source_id}")
            lines.append(f"    a wg:Source ;")
            if source_url:
                lines.append(f'    wg:hasSourceURL <{source_url}> ;')
            if source_type:
                lines.append(f'    wg:hasSourceType "{turtle_literal(source_type)}" ;')
            lines[-1] = lines[-1].rstrip(" ;") + " ."
            lines.append("")

        # --- CyberWishingCase individual ---
        block = []
        block.append(f"wg:{case_id}")
        block.append(f"    a wg:CyberWishingCase , owl:NamedIndividual ;")
        block.append(f'    rdfs:label "CyberWishingCase_{case["caseIndex"]}: {turtle_literal(person_label)}" ;')

        if person_id:
            block.append(f"    wg:hasPerson wg:{person_id} ;")
        if pressure_id:
            block.append(f"    wg:hasPressure wg:{pressure_id} ;")
        if product_id:
            block.append(f"    wg:usesCyberProduct wg:{product_id} ;")
        if target_id:
            # Also add alignment on product
            block.append(f"    wg:alignsWithCulturalTarget wg:{target_id} ;")
        for pid in practice_ids:
            block.append(f"    wg:performsPractice wg:{pid} ;")
        for plid in platform_ids:
            block.append(f"    wg:circulatesOnPlatform wg:{plid} ;")
        for mid in mechanism_ids:
            block.append(f"    wg:hasTransformationMechanism wg:{mid} ;")
        for aid in affective_ids:
            block.append(f"    wg:servesAffectiveFunction wg:{aid} ;")
        for mid2 in meme_ids:
            block.append(f"    wg:servesMemeFunction wg:{mid2} ;")
        for sid in symbol_ids:
            block.append(f"    wg:usesRitualSymbol wg:{sid} ;")
        if source_id:
            block.append(f"    wg:hasSource wg:{source_id} ;")

        # Fix trailing semicolon → period
        if block[-1].endswith(" ;"):
            block[-1] = block[-1][:-2] + " ."
        else:
            block.append("    .")
        block.append("")
        case_blocks.extend(block)

    lines += [
        "# ─────────────────────────────────────────────────────────────────────────",
        "# CyberWishingCase individuals",
        "# ─────────────────────────────────────────────────────────────────────────",
        "",
    ]
    lines.extend(case_blocks)

    abox_content = "\n".join(lines)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(abox_content)
    print(f"✓ A-Box written → {OUTPUT_PATH}")

    # Also write merged T-Box + A-Box
    with open(TBOX_PATH, encoding="utf-8") as f:
        tbox = f.read()
    with open(MERGED_PATH, "w", encoding="utf-8") as f:
        f.write(tbox)
        f.write("\n\n# ═══════════════════════════════════════════════════════════\n")
        f.write("# A-BOX INSTANCES (appended)\n")
        f.write("# ═══════════════════════════════════════════════════════════\n\n")
        # Skip prefix lines in abox (already in tbox)
        abox_lines = abox_content.split("\n")
        skip = True
        for line in abox_lines:
            if skip and (line.startswith("@prefix") or line == ""):
                continue
            skip = False
            f.write(line + "\n")
    print(f"✓ Full ontology written → {MERGED_PATH}")


if __name__ == "__main__":
    main()
