#!/usr/bin/env python3
"""
Rebuild WishGraph A-Box (18 cases) from wishgraph_structured_cases(1).csv,
merge with the T-Box, and re-run the five competency-question SPARQL queries.

Also dumps a CASES json payload for chapter3.html.
"""
import csv, json, re, sys
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.compare import isomorphic

ROOT = "/Users/oliverislianym/Desktop/WishGraph-Project"
CW = Namespace("http://www.ontologydesignpatterns.org/ont/cyberwishing/cw.owl#")
CREON = Namespace("http://www.ontologydesignpatterns.org/ont/creativity/creon.owl#")
DUL = Namespace("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

SRC_CSV = f"{ROOT}/data/wishgraph_structured_cases.csv"

# ── column positions in the CSV ──
COL = {
    "case": 0, "platform": 1, "subject": 2, "action": 3,
    "posting": 4, "commenting": 5,
    "pressure": 6, "mundane": 7, "existential": 8,
    "signifier": 9, "image": 10, "video": 11,
    "symbol": 12, "mantra": 13, "emoji": 14, "visual": 15,
    "archetype": 16, "traditional": 17, "modern": 18, "animal": 19, "commodity": 20,
    "strategy": 21, "digital": 22, "amplification": 23, "hybridization": 24,
    "deification": 25, "enchantment": 26,
    "outcome": 27,
}

# typed columns -> (base column, RDF class)
TYPE_COLS = [
    ("posting", "action", "PostingAction"),
    ("commenting", "action", "CommentingAction"),
    ("mundane", "pressure", "MundanePressure"),
    ("existential", "pressure", "ExistentialPressure"),
    ("image", "signifier", "ImageSignifier"),
    ("video", "signifier", "VideoSignifier"),
    ("mantra", "symbol", "Mantra"),
    ("emoji", "symbol", "Emoji"),
    ("visual", "symbol", "VisualOrAuditoryMarker"),
    ("traditional", "archetype", "TraditionalArchetype"),
    ("modern", "archetype", "ModernArchetype"),
    ("animal", "archetype", "Animal"),
    ("commodity", "archetype", "SecularCommodity"),
    ("digital", "strategy", "DigitalTransposition"),
    ("amplification", "strategy", "SacredAmplification"),
    ("hybridization", "strategy", "SacredHybridization"),
    ("deification", "strategy", "SecularIdolDeification"),
    ("enchantment", "strategy", "SymbolicEnchantment"),
]

# ── hand-written labels carried over from the previous A-Box, so the teacher
#    sees the same wording for the nine original cases ──
MANUAL_LABELS = {
    "Bilibili": "Bilibili Platform",
    "Instagram": "Instagram Platform",
    "Tiktok": "Douyin Platform",
    "XPlatform": "X Platform",
    "Xiaohongshu": "Xiaohongshu Platform",
    "Weibo": "Weibo Platform",
    "CET6Commenter": "Commenter Anhui Student",
    "DigitalEnlightenmentPoster": "Panda Chakra User",
    "ExamWishPoster": "Exam-Wishing User",
    "HealthWishPoster": "Health-Wishing User",
    "KardashianManifestingPoster": "Ambitious User",
    "ManifestPoster": "User Shally",
    "MaterialisticUser": "Materialistic User",
    "RomanceSeekingUser": "Romance Seeking User",
    "TraditionalPrayerPoster": "Devout Instagram User",
    "WealthClaimCommenter": "Commenter Rammyy",
    "AcademicSuccess": "Sincere Hope for Academic Success",
    "FinancialFreedom": "Hope for Financial Freedom",
    "HealthRecovery": "Hope for Health Recovery",
    "InnerPeace": "Sincere Hope for Inner Peace",
    "MemeTherapy": "Meme Therapy",
    "NewYearVibes": "Sincere Hope for New Year Vibes",
    "Prosperity": "Sincere Hope for Prosperity",
    "RomanticAttraction": "Sincere Hope for Romantic Attraction",
    "WealthDelusion": "Ironic Comfort of Wealth Delusion",
    "BlueBuddhaImg": "Blue Buddha Image",
    "Butterfly": "Traditional Butterfly Symbol",
    "ButterflyGod": "Butterfly Subliminal Remediation",
    "ButterflySubliminal": "Butterfly Subliminal Strategy",
    "CareerWealth": "Career and Wealth Pressure",
    "CashManifestingVideo": "Cash Manifesting Video",
    "Cat": "Cat Archetype",
    "CatBuddha": "Cat Buddha Remediation",
    "Commenting_CET6Manifestation": "Commenting CET-6 Manifestation",
    "Commenting_ClaimWealth": "Commenting Claim Wealth",
    "Emoji_PrayingHands": "Praying Hands Emoji",
    "Emoji_RedHeart": "Red Heart Emoji Symbol",
    "ExamCatImg": "Exam Cat Image",
    "ExamPressure": "Exam Pressure",
    "ExistentialPressure_ModernAnxiety": "Modern Anxiety and Existential Pressure",
    "GlitterAesthetic": "Glitter Aesthetic",
    "HealthProblem": "Health Problem",
    "KnittedKasaya": "Knitted Kasaya",
    "KrisJennerMemeImg": "Kris Jenner Meme Image",
    "KrisJennerPopIcon": "Kris Jenner Pop Icon",
    "KrisJennerReplyImage": "Kris Jenner Reply Image",
    "LoFiBeatAndSlowMo": "Lo-Fi Beat and Slow Motion",
    "LotusCushion": "Lotus Cushion",
    "LuxurySportsCar": "Luxury Sports Car",
    "Mahayana": "Mahayana Buddhist Archetype",
    "ManifestingMantraText": "Manifesting Mantra Text",
    "Mantra_CET6Success": "CET-6 Success Mantra",
    "Mantra_ClaimEnergy": "Claim Energy Mantra",
    "MedicineBuddha": "Medicine Buddha",
    "MundanePressure_FutureUncertainty": "Future Uncertainty Pressure",
    "MundanePressure_RomanticAnxiety": "Romantic Anxiety",
    "MundanePressure_StatusAnxiety": "Social Status Anxiety",
    "MundanePressure_WealthDesire": "Wealth Desire Pressure",
    "PopIdolGod": "Playful Remediation of Pop Idol",
    "Posting_BuddhaTeaching": "Posting Buddha Teaching",
    "Posting_ExamWish": "Posting Exam Wish",
    "Posting_HealthWish": "Posting Health Wish",
    "Posting_Manifest2026": "Posting Manifest 2026 Action",
    "Posting_ManifestingSpell": "Posting Manifesting Spell",
    "Posting_NewYearPrayer": "Posting New Year Prayer Action",
    "Posting_SubliminalVideo": "Posting Subliminal Video",
    "Posting_WealthManifesting": "Posting Wealth Manifesting",
    "PsychedelicAestheticRemediation": "Psychedelic Aesthetic Remediation",
    "PsychedelicAura": "Psychedelic Aura",
    "PsychedelicBuddhaVideo": "Psychedelic Buddha Video",
    "Remediation_CashFetishization": "Cash Fetishization Strategy",
    "Remediation_LuxuryCar": "Luxury Car Fetishization",
    "RestoreOriginal": "Restoring Original Sacred Form",
    "SportsCarManifestingVideo": "Sports Car Manifesting Video",
    "StackOfCash": "Stack of Cash Commodity Archetype",
    "SubliminalAudioFrequency": "Subliminal Audio Frequency",
    "SubliminalButterflyVideo": "Subliminal Butterfly Video",
    "TraditionalBuddhaPostImage": "Traditional Buddha Post Image",
}

# labels for the new dimensions that would otherwise read awkwardly
EXTRA_LABELS = {
    "Mantra_GoodLuckComes": "Good Luck Comes Mantra",
    "Mantra_GlobalTycoon": "Global Tycoon Mantra",
    "Mantra_BornToSucceed": "Born to Succeed Mantra",
    "Mantra_HundredIllnessesRetreat": "Hundred Illnesses Retreat Mantra",
    "Mantra_WishImmediatelyRealized": "Wish-Immediately-Realized Mantra",
    "Mantra_CaishenArrival": "Caishen Arrival Mantra",
    "Mantra_EverythingWillBeAlright": "Everything Will Be Alright Mantra",
    "Mantra_DoingAmazingSweetie": "Doing Amazing Sweetie Mantra",
    "Emoji_WhiteHeart": "White Heart Emoji",
    "Emoji_BlackHeart": "Black Heart Emoji",
    "LoFiBeatAndSlowMo": "Lo-Fi Beat and Slow Motion",
    "CashStacks": "Cash Stacks Marker",
    "LuxuryGoldAesthetic": "Luxury Gold Aesthetic",
    "ExecutiveLuxuryAesthetic": "Executive Luxury Aesthetic",
    "RainbowAura": "Rainbow Aura",
    "RedTalismanInk": "Red Talisman Ink",
    "GoldenAura": "Golden Aura",
    "CloudAesthetic": "Cloud Aesthetic",
    "GoldenHalo": "Golden Halo",
    "GoldCoins": "Gold Coins",
    "Yuanbao": "Yuanbao Ingot",
    "PinkCuteAesthetic": "Pink Cute Aesthetic",
    "SunsetAesthetic": "Sunset Aesthetic",
    "RomanticMusic": "Romantic Music",
    "DigitalAltarDisplay": "Digital Altar Display",
    "SubliminalAudioFrequency": "Subliminal Audio Frequency",
    "GodOfWealth": "God of Wealth",
    "Caishen": "Caishen the God of Wealth",
    "Guanyin": "Guanyin Bodhisattva",
    "TaoistHealingTalisman": "Taoist Healing Talisman",
    "WealthAssets": "Wealth Assets",
    "RomanticCoupleIdeal": "Romantic Couple Ideal",
    "SuccessfulExecutiveIdeal": "Successful Executive Ideal",
    "SupportiveCelebrityMomagerMeme": "Supportive Celebrity Momager Meme",
    "Rabbit": "Lucky Rabbit",
    "Weibo": "Weibo Platform",
    "Remediation_RabbitLuck": "Rabbit Luck Enchantment",
    "XPlatform": "X Platform",
    # ── pressures ──
    "ExistentialPressure_FamilyIllness": "Family Illness Pressure",
    "MundanePressure_CareerFinancialAspiration": "Career and Financial Aspiration Pressure",
    "MundanePressure_FinancialProsperity": "Financial Prosperity Pressure",
    "MundanePressure_GeneralUncertainty": "General Uncertainty Pressure",
    "MundanePressure_RomanticDesire": "Romantic Desire Pressure",
    "MundanePressure_RomanticFutureUncertainty": "Romantic Future Uncertainty Pressure",
    "MundanePressure_WealthStatusDesire": "Wealth and Status Desire Pressure",
    # ── strategies ──
    "DigitalTransposition_HealingTalisman": "Healing Talisman Digital Transposition",
    "DigitalTransposition_WealthGodAltar": "Wealth God Altar Digital Transposition",
    "SacredAmplification_Caishen": "Caishen Sacred Amplification",
    "SacredAmplification_Guanyin": "Guanyin Sacred Amplification",
    "SecularIdolDeification_CelebrityMeme": "Celebrity Meme Deification",
    "SymbolicEnchantment_LoveIdeal": "Love Ideal Enchantment",
    "SymbolicEnchantment_SuccessIdeal": "Success Ideal Enchantment",
    "SymbolicEnchantment_WealthAssets": "Wealth Assets Enchantment",
    # ── signifiers ──
    "BornToSucceedVideo": "Born to Succeed Video",
    # ── actions / subjects for the newer cases ──
    "Posting_LoveManifestVideo": "Posting Love Manifestation Video",
    "Posting_ReassuranceMemeVideo": "Posting Reassurance Meme Video",
    "Posting_SuccessAffirmationVideo": "Posting Success Affirmation Video",
    "Posting_HealthTalismanPrayer": "Posting Health Talisman Prayer",
    "Posting_GuanyinWish": "Posting Guanyin Wish",
    "Posting_CaishenBlessing": "Posting Caishen Blessing",
    "Posting_LikeCommentBlessing": "Posting Like-and-Comment Blessing",
    "Posting_WealthGodAltar": "Posting Wealth God Altar",
    "Posting_GlobalTycoonMantra": "Posting Global Tycoon Mantra",
    "ReassuranceManifestPoster": "Reassurance Manifesting User",
    "FinancialSuccessPoster": "Financial Success User",
    "LoveManifestPoster": "Love Manifesting User",
    "ProsperityManifestPoster": "Prosperity Manifesting User",
    "UKWealthGodPoster": "UK Wealth God Poster",
    "GuanyinWishPoster": "Guanyin Wish Poster",
    "CaishenBlessingPoster": "Caishen Blessing Poster",
    "LuckyRabbitWishPoster": "Lucky Rabbit Wish Poster",
    "GrandfatherHealthPoster": "Grandfather Health Poster",
}

# rdfs:label of each case
CASE_LABELS = {
    "Case_CatWish": "Cat Buddha Exam Wish Case",
    "Case_DigitalEnlightenment": "Digital Enlightenment Case",
    "Case_HealthWish": "Medicine Buddha Health Wish Case",
    "Case_InstagramTraditionalPrayer": "Instagram Traditional Buddha Prayer Case",
    "Case_InstagramWealth": "Instagram Wealth Manifesting Case",
    "Case_ManifestingKardashian": "Manifesting Kardashian Case",
    "Case_SubliminalRomance": "Subliminal Romance Case",
    "Case_XWealthManifesting": "X Wealth Manifesting Case",
    "Case_XiaohongshuCET6Comment": "Xiaohongshu CET-6 Comment Case",
    "Case_UKWealthGodAltar": "UK Wealth God Altar Case",
    "Case_GlobalTycoonMantra": "Global Tycoon Mantra Case",
    "Case_TikTokLoveManifestation": "TikTok Love Manifestation Case",
    "Case_CelebrityMemeReassurance": "Celebrity Meme Reassurance Case",
    "Case_FinancialSuccessAffirmation": "Financial Success Affirmation Case",
    "Case_GrandfatherHealthPrayer": "Grandfather Health Prayer Case",
    "Case_GuanyinWishFulfillment": "Guanyin Wish Fulfillment Case",
    "Case_WeiboCaishenBlessing": "Weibo Caishen Blessing Case",
    "Case_WeiboLuckyRabbitWish": "Weibo Lucky Rabbit Wish Case",
}

# the CSV leaves this strategy untyped; typed by analogy with the other
# Remediation_* symbols, which the ontology classifies as Symbolic Enchantment
STRATEGY_FALLBACK = {"Remediation_RabbitLuck": "SymbolicEnchantment"}


# ─────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────

def split_multi(v):
    if not v:
        return []
    return [x.strip() for x in v.split(";") if x.strip()]


def camel_to_words(s):
    s = s.replace("_", " ")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return re.sub(r"\s+", " ", s).strip()


SUFFIX = [("Img", " Image"), ("Image", " Image"), ("Video", " Video")]


def auto_label(name):
    if name in MANUAL_LABELS:
        return MANUAL_LABELS[name]
    if name in EXTRA_LABELS:
        return EXTRA_LABELS[name]
    if name in CASE_LABELS:
        return CASE_LABELS[name]
    base = camel_to_words(name)
    # strip a leading redundant type word
    for pre in ("Mantra ", "Emoji "):
        pass
    for suf, rep in SUFFIX:
        if base.endswith(suf) and not base.endswith(" " + rep.strip()):
            base = base[: -len(suf)] + rep
            break
    if base.startswith("Mantra ") and not base.endswith("Mantra"):
        base = base[len("Mantra "):] + " Mantra"
    if base.startswith("Emoji ") and not base.endswith("Emoji"):
        base = base[len("Emoji "):] + " Emoji"
    base = re.sub(r"\s+", " ", base).strip()
    return base


def typed_class(instance, base_col, data):
    """which RDF class should this instance carry, according to the CSV?"""
    for col, bcol, cls in TYPE_COLS:
        if bcol != base_col:
            continue
        if instance in split_multi(data[COL[col]]):
            return cls
    if base_col == "strategy" and instance in STRATEGY_FALLBACK:
        return STRATEGY_FALLBACK[instance]
    return None


# ─────────────────────────────────────────────────────────────
# load + parse the CSV
# ─────────────────────────────────────────────────────────────

def load_cases():
    with open(SRC_CSV, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]
    cases = []
    for r in body:
        r = r + [""] * (len(header) - len(r))
        cases.append(r)
    return header, cases


def build_abox(cases):
    """Return (ttl_lines, caselist) — caselist feeds the HTML table."""
    case_blocks, dim_blocks = [], {}   # local name -> list of ttl lines
    case_rows = []

    def add(local, cls, label, comment, extra=()):
        """register a dimension individual (idempotent, merges types)"""
        blk = dim_blocks.setdefault(local, {"types": set(), "label": label,
                                            "comment": comment, "extra": set()})
        if cls:
            blk["types"].add(cls)
        if label:
            blk["label"] = label
        if comment:
            blk["comment"] = comment
        for e in extra:
            blk["extra"].add(e)

    for data in cases:
        case = data[COL["case"]].strip()
        if not case:
            continue
        platform = data[COL["platform"]].strip()
        subjects = split_multi(data[COL["subject"]])
        actions = split_multi(data[COL["action"]])
        pressure = data[COL["pressure"]].strip()
        signifier = data[COL["signifier"]].strip()
        symbols = split_multi(data[COL["symbol"]])
        archetypes = split_multi(data[COL["archetype"]])
        strategy = data[COL["strategy"]].strip()
        outcome = data[COL["outcome"]].strip()

        # ── platform ──
        if platform:
            add(platform, "Platform", auto_label(platform),
                "A digital platform on which cyber-wishing cases circulate.")

        # ── subject: commenters perform commenting actions, everyone else posts ──
        poster = next((s for s in subjects if "Commenter" not in s), None)
        commenter = next((s for s in subjects if "Commenter" in s), None)
        for s in subjects:
            add(s, "Subject", auto_label(s),
                f"A subject who participates in a cyber-wishing practice on {auto_label(platform)}.")

        # ── performative actions ──
        for a in actions:
            cls = typed_class(a, "action", data)
            who = commenter if cls == "CommentingAction" else poster
            who = who or (subjects[0] if subjects else None)
            extra = [f"cw:performedBy cw:{who}"] if who else []
            verb = "commenting on" if cls == "CommentingAction" else "posting"
            add(a, cls, auto_label(a),
                f"The performative act of {verb} a cyber-wishing signifier on "
                f"{auto_label(platform)}.", extra)

        # ── pressure ──
        if pressure:
            add(pressure, typed_class(pressure, "pressure", data), auto_label(pressure),
                "A real-world secular pressure that triggers a cyber-wishing practice.")

        # ── signifier ──
        if signifier:
            extra = []
            if symbols:
                extra.append("cw:containsSymbol " + ", ".join(f"cw:{s}" for s in symbols))
            if archetypes:
                extra.append("cw:remediates " + ", ".join(f"cw:{a}" for a in archetypes))
            add(signifier, typed_class(signifier, "signifier", data),
                auto_label(signifier),
                "A digital signifier that carries the wishing practice.", extra)

        # ── ritual symbols (attached to the signifier) ──
        for s in symbols:
            add(s, typed_class(s, "symbol", data), auto_label(s),
                "A ritual symbol attested in the digital signifier of this practice.")

        # ── archetypes (remediated by the signifier) ──
        for a in archetypes:
            add(a, typed_class(a, "archetype", data), auto_label(a),
                "An archetype that is remediated into a digital wishing signifier.")

        # ── strategy ──
        if strategy:
            add(strategy, typed_class(strategy, "strategy", data), auto_label(strategy),
                "The remediation strategy through which the traditional source is "
                "adapted into a digital format.")

        # ── outcome ──
        if outcome:
            add(outcome, "AffectiveOutcome", auto_label(outcome),
                "The affective resolution produced by the cyber-wishing practice.")

        # ── the case itself ──
        stmts = [f"    rdfs:label \"{CASE_LABELS.get(case, camel_to_words(case))}\"@en"]
        stmts.append('    rdfs:comment "A cyber-ritual case circulating on '
                     f'{auto_label(platform)}'
                     f'{"" if not pressure else ", triggered by " + auto_label(pressure)}'
                     f'{"" if not outcome else " and resolving into " + auto_label(outcome)}."@en')
        if platform:
            stmts.append(f"    cw:circulatesOn cw:{platform}")
        if signifier:
            stmts.append(f"    cw:employsSignifier cw:{signifier}")
        if actions:
            stmts.append("    cw:hasPerformativeAction " +
                         ", ".join(f"cw:{a}" for a in actions))
        if outcome:
            stmts.append(f"    cw:resolvesIntoAffect cw:{outcome}")
        if strategy:
            stmts.append(f"    cw:transformedVia cw:{strategy}")
        if pressure:
            stmts.append(f"    cw:triggeredBy cw:{pressure}")
        body = " ;\n".join(stmts) + " ."
        case_blocks.append(f"cw:{case} a cw:CyberRitualCase , owl:NamedIndividual ;\n{body}")

        # ── row for the HTML table ──
        case_rows.append({
            "id": case,
            "name": CASE_LABELS.get(case, camel_to_words(case)),
            "platform": platform,
            "subject": subjects,
            "action": actions,
            "pressure": pressure,
            "pressureType": typed_class(pressure, "pressure", data) or "",
            "signifier": signifier,
            "signifierType": typed_class(signifier, "signifier", data) or "",
            "symbols": symbols,
            "archetype": archetypes,
            "archetypeType": " / ".join(sorted({
                typed_class(a, "archetype", data) for a in archetypes if typed_class(a, "archetype", data)
            })),
            "strategy": strategy,
            "strategyType": typed_class(strategy, "strategy", data) or "",
            "outcome": outcome,
        })

    # ── render the dimension instances, grouped by first type for readability ──
    grouped = {}
    for local, blk in dim_blocks.items():
        primary = sorted(blk["types"])[0] if blk["types"] else "owl:Thing"
        grouped.setdefault(primary, []).append((local, blk))

    lines = []
    for cls in sorted(grouped):
        lines.append(f"# ── {cls} ──\n")
        for local, blk in sorted(grouped[cls]):
            types = ", ".join(f"cw:{t}" for t in sorted(blk["types"])) or "owl:Thing"
            stmts = [f"    rdfs:label \"{blk['label']}\"@en",
                     f"    rdfs:comment \"{blk['comment']}\"@en"]
            stmts += [f"    {e}" for e in sorted(blk["extra"])]
            body = " ;\n".join(stmts) + " ."
            lines.append(f"cw:{local} a {types} , owl:NamedIndividual ;\n{body}\n")
    return case_blocks, lines, case_rows


HEADER = """# ─────────────────────────────────────────────────────────────────────────────
# WishGraph — A-Box (assertional level)
#
# {n} cyber-ritual cases, each linked to its dimension instances through the
# object properties declared in the T-Box. Dimension instances are typed with
# the appropriate sub-class, which is how the "type" facets are expressed.
#
# Generated from data/wishgraph_structured_cases.csv by scripts/build_ontology.py
# ─────────────────────────────────────────────────────────────────────────────

@prefix cw: <http://www.ontologydesignpatterns.org/ont/cyberwishing/cw.owl#> .
@prefix creon: <http://www.ontologydesignpatterns.org/ont/creativity/creon.owl#> .
@prefix dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

############################################################
# Cyber-ritual cases
############################################################
"""


def main():
    header, cases = load_cases()
    case_blocks, dim_lines, case_rows = build_abox(cases)
    print(f"cases parsed : {len(case_rows)}")
    print(f"individuals  : {len(dim_lines)} lines")

    ttl = HEADER.format(n=len(case_rows))
    ttl += "\n" + "\n\n".join(case_blocks) + "\n\n"
    ttl += ("############################################################\n"
            "# Dimension instances\n"
            "############################################################\n\n")
    ttl += "\n".join(dim_lines)
    open(f"{ROOT}/ontology/wishgraph_abox.ttl", "w", encoding="utf-8").write(ttl)

    # full = tbox + abox
    tbox = open(f"{ROOT}/ontology/wishgraph_tbox.ttl", encoding="utf-8").read()
    full = tbox + "\n\n" + ttl
    open(f"{ROOT}/ontology/wishgraph_full.ttl", "w", encoding="utf-8").write(full)

    g = Graph()
    g.parse(data=full, format="turtle")
    print(f"full graph   : {len(g)} triples")

    json.dump(case_rows, open("/tmp/wg_cases.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ── sanity: every case must have all six links ──
    missing = []
    for c in case_rows:
        for k in ("platform", "pressure", "signifier", "strategy", "outcome"):
            if not c[k]:
                missing.append((c["id"], k))
        if not c["archetype"]:
            missing.append((c["id"], "archetype"))
    print(f"incomplete   : {missing if missing else 'none'}")


if __name__ == "__main__":
    main()
