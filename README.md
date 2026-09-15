# WishGraph — Knowledge Representation Project

An ontology of **cyber-wishing, digital folklore and platformed rituals** in contemporary Chinese internet culture.

## Project Overview

WishGraph models how everyday pressures are transformed into meme-based digital rituals across Chinese-language platforms (RedNote, Weibo, Bilibili, WeChat, Douyin, TikTok and others).

The ontology captures relations among:
- **Social actors** (students, jobseekers, gamers, couples, travellers…)
- **Pressures** (exam anxiety, job insecurity, gacha randomness, relationship uncertainty…)
- **Cyber products** (deity memes, lucky wallpapers, online divination tools…)
- **Cultural targets** (Caishen, Wenchang Dijun, Mazu, Guanyin, Yuelao…)
- **Digital practices** (reposting, commenting "99", avatar-changing, online divination…)
- **Platforms** (RedNote, Weibo, Bilibili, Douyin, WeChat…)
- **Affective functions** (anxiety relief, hope generation, confidence building…)
- **Meme functions** (virality, community bonding, humour, participatory blessing…)

## Repository Structure

```
WishGraph-Project/
├── data/
│   └── metadata.csv              # Raw dataset — 14 cyber-wishing cases
├── docs/
│   ├── WishGraph.docx            # Project framework document (Group A)
│   └── 知识提取PJ_beyoo.pdf      # Project brief (PDF)
├── ontology/
│   ├── wishgraph_tbox.ttl        # OWL T-Box (classes & properties)
│   ├── wishgraph_abox.ttl        # OWL A-Box (case instances)
│   ├── wishgraph_full.ttl        # Merged T-Box + A-Box
│   └── sparql_queries.rq         # SPARQL queries for all 5 Competency Questions
├── output/
│   ├── wishgraph_cases.json      # Structured JSON (intermediate)
│   └── knowledgerepresentation.html  # ★ Main deliverable — interactive web page
└── scripts/
    ├── csv_to_json.py            # Step 1: CSV → JSON
    └── json_to_rdf.py            # Step 2: JSON → Turtle RDF (T-Box + A-Box)
```

## Deliverables

| File | Description |
|------|-------------|
| `output/knowledgerepresentation.html` | **Main output** — interactive knowledge representation page |
| `ontology/wishgraph_tbox.ttl` | OWL ontology T-Box (12 classes, 11 object properties) |
| `ontology/wishgraph_abox.ttl` | OWL A-Box with 14 CyberWishingCase individuals |
| `ontology/wishgraph_full.ttl` | Merged ontology ready for Protégé / GraphDB |
| `ontology/sparql_queries.rq` | SPARQL queries corresponding to CQ1–CQ5 |
| `output/wishgraph_cases.json` | Intermediate JSON bridging CSV and RDF |

## Methodology

1. **Domain Analysis & Meme Collection** — collect representative cyber-wishing examples from Chinese-language platforms
2. **AI-assisted Extraction** — extract structured fields from each meme/post using the CSV schema
3. **CSV → JSON** (`scripts/csv_to_json.py`) — parse and normalise the metadata CSV
4. **JSON → RDF** (`scripts/json_to_rdf.py`) — instantiate OWL individuals in Turtle format
5. **Ontology Modelling** — define T-Box in `wishgraph_tbox.ttl` (classes, object properties, datatype properties)
6. **SPARQL Testing** — test competency questions against the populated ontology
7. **Knowledge Representation Page** — render all findings as `knowledgerepresentation.html`

## Ontology Namespace

```
Prefix: wg:
URI:    https://example.org/wishgraph#
```

## Competency Questions

| # | Question |
|---|----------|
| CQ1 | Which types of users engage in cyber-wishing, and what pressures motivate them? |
| CQ2 | How are traditional deities transformed into cyber products and meme devices? |
| CQ3 | What digital practices mediate cyber-wishing across different platforms? |
| CQ4 | What affective functions do cyber-wishing practices serve for different user groups? |
| CQ5 | How do meme functions and ritual symbols support the circulation of cyber-wishing? |

## Running the Scripts

```bash
# Requires Python 3.x (no external dependencies beyond standard library)
cd WishGraph-Project

# Step 1: Convert CSV to JSON
python3 scripts/csv_to_json.py

# Step 2: Convert JSON to RDF Turtle
python3 scripts/json_to_rdf.py
```

## Loading in Protégé

1. Open Protégé (desktop or WebProtégé)
2. File → Open → select `ontology/wishgraph_full.ttl`
3. Run SPARQL queries from `ontology/sparql_queries.rq`

## Theoretical Background

- **Adapted 4P Framework** (Rhodes 1961): Person, Process, Product, Press + Platform
- **Digital Folklore** (Howard 2008; Blank 2009)
- **Ritual Theory** (Bell 1992; Turner 1969)
- **Meme Theory** (Shifman 2014; Milner 2016)
- **Affective Practice** (Ahmed 2004)
- **Platform Affordances** (Bucher & Helmond 2018)
- **Ontology Engineering** — eXtreme Design (Presutti et al. 2009; Gruber 1993)
