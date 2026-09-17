#!/usr/bin/env python3
"""Write ontology/sparql_queries.rq (cw: vocabulary) and run the 5 CQ queries."""
import json
from rdflib import Graph, Namespace, RDF, RDFS

ROOT = "/Users/oliverislianym/Desktop/WishGraph-Project"
CW = Namespace("http://www.ontologydesignpatterns.org/ont/cyberwishing/cw.owl#")

PREFIXES = """PREFIX cw:   <http://www.ontologydesignpatterns.org/ont/cyberwishing/cw.owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"""

Q1 = """# CQ1 -- which performative actions are carried out, by whom, and on which platform?
SELECT ?case
       (GROUP_CONCAT(DISTINCT CONCAT(?actionLabel, " by ", ?agentLabel); separator="; ") AS ?actions)
       ?platformLabel
WHERE {
    ?case a cw:CyberRitualCase ;
          cw:hasPerformativeAction ?action ;
          cw:circulatesOn          ?platform .
    ?action   cw:performedBy ?agent ;
              rdfs:label     ?actionLabel .
    ?agent    rdfs:label     ?agentLabel .
    ?platform rdfs:label     ?platformLabel .
}
GROUP BY ?case ?platformLabel
ORDER BY ?case"""

Q2 = """# CQ2 -- which secular pressure triggers each case, and what type of pressure is it?
SELECT ?case ?pressureLabel ?pressureTypeLabel
WHERE {
    ?case a cw:CyberRitualCase ;
          cw:triggeredBy ?pressure .
    ?pressure rdfs:label ?pressureLabel ;
              a ?pressureType .
    ?pressureType rdfs:subClassOf* cw:SecularPressure ;
                  rdfs:label       ?pressureTypeLabel .
    FILTER (?pressureType != cw:SecularPressure)
}
ORDER BY ?case"""

Q3 = """# CQ3 -- which remediation strategy transforms the case, and what does it resolve into?
SELECT ?case ?strategyLabel ?strategyTypeLabel ?outcomeLabel
WHERE {
    ?case a cw:CyberRitualCase ;
          cw:transformedVia     ?strategy ;
          cw:resolvesIntoAffect ?outcome .
    ?strategy rdfs:label ?strategyLabel ;
              a ?strategyType .
    ?strategyType rdfs:subClassOf* cw:RemediationStrategy ;
                  rdfs:label       ?strategyTypeLabel .
    FILTER (?strategyType != cw:RemediationStrategy)
    ?outcome rdfs:label ?outcomeLabel .
}
ORDER BY ?case"""

Q4 = """# CQ4 -- which remediated signifier is employed, and which ritual symbols does it contain?
SELECT ?case ?signifierLabel ?signifierTypeLabel
       (GROUP_CONCAT(?symbolLabel; separator=" | ") AS ?ritualSymbols)
WHERE {
    ?case a cw:CyberRitualCase ;
          cw:employsSignifier ?signifier .
    ?signifier rdfs:label ?signifierLabel ;
               a ?signifierType .
    ?signifierType rdfs:subClassOf* cw:RemediatedSignifier ;
                   rdfs:label       ?signifierTypeLabel .
    FILTER (?signifierType != cw:RemediatedSignifier)
    OPTIONAL {
        ?signifier cw:containsSymbol ?symbol .
        ?symbol    rdfs:label        ?symbolLabel .
    }
}
GROUP BY ?case ?signifierLabel ?signifierTypeLabel
ORDER BY ?case"""

Q5 = """# CQ5 -- which archetype is remediated by the signifier, and what type is it?
SELECT ?case
       (GROUP_CONCAT(DISTINCT ?archetypeLabel;     separator=", ") AS ?archetypes)
       (GROUP_CONCAT(DISTINCT ?archetypeTypeLabel; separator=", ") AS ?archetypeTypes)
WHERE {
    ?case a cw:CyberRitualCase ;
          cw:employsSignifier ?signifier .
    ?signifier cw:remediates ?archetype .
    ?archetype rdfs:label ?archetypeLabel ;
               a ?archetypeType .
    ?archetypeType rdfs:subClassOf* cw:Archetype ;
                   rdfs:label       ?archetypeTypeLabel .
    FILTER (?archetypeType != cw:Archetype)
}
GROUP BY ?case
ORDER BY ?case"""

QUERIES = [
    ("cq1", "CQ1 — Performative Action, Subject and Platform", Q1),
    ("cq2", "CQ2 — Trigger / Pressure", Q2),
    ("cq3", "CQ3 — Transformation and Affective Outcome", Q3),
    ("cq4", "CQ4 — Signifier and Ritual Symbol", Q4),
    ("cq5", "CQ5 — Archetype and Archetype Type", Q5),
]

FILE_HEADER = """# ─────────────────────────────────────────────────────────────────────────────
# WishGraph — SPARQL competency-question queries
# Run against ../ontology/wishgraph_full.ttl (T-Box + A-Box)
#
# Namespace cw: <http://www.ontologydesignpatterns.org/ont/cyberwishing/cw.owl#>
# All five queries travel through the case-centred graph: each case reaches its
# actors, pressures, signifiers and outcomes through the object properties
# declared in the T-Box, and reads each dimension's "type" from the sub-class
# the instance is typed with.
# ─────────────────────────────────────────────────────────────────────────────
"""


def main():
    g = Graph()
    g.parse(f"{ROOT}/ontology/wishgraph_full.ttl", format="turtle")

    # ── write the .rq file ──
    chunks = [FILE_HEADER]
    for _, title, q in QUERIES:
        bar = "#" * 74
        chunks.append(f"{bar}\n# {title}\n{bar}\n{PREFIXES}\n\n{q}\n")
    open(f"{ROOT}/ontology/sparql_queries.rq", "w", encoding="utf-8").write("\n".join(chunks))

    # ── execute ──
    out = {}
    for key, title, q in QUERIES:
        rows = []
        res = g.query(PREFIXES + "\n" + q)
        vars_ = [str(v) for v in res.vars]
        for r in res:
            rows.append(["" if r[v] is None else str(r[v]) for v in res.vars])
        out[key] = {"title": title, "vars": vars_, "rows": rows}
        print(f"{key}: {len(rows)} rows | vars={vars_}")
        for r in rows[:2]:
            print("      ", r)
    json.dump(out, open("/tmp/wg_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwrote ontology/sparql_queries.rq and /tmp/wg_results.json")


if __name__ == "__main__":
    main()
