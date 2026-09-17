#!/usr/bin/env python3
"""
Rebuild chapter3.html:
  · 3.1  → three-step interactive extraction widget
  · 3.2  → English paragraph on CSV → RDF → knowledge graph
  · 3.3  → refreshed result tables (18 cases), English only
"""
import csv, json, re, os, sys, html as H

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inline_assets import inline as inline_assets

ROOT = "/Users/oliverislianym/Desktop/WishGraph-Project"
CH3 = f"{ROOT}/output/chapter3.html"
SRC_CSV = f"{ROOT}/data/wishgraph_structured_cases.csv"
RES = json.load(open("/tmp/wg_results.json", encoding="utf-8"))

KEYWORDS = {"SELECT", "WHERE", "GROUP", "BY", "ORDER", "AS", "OPTIONAL", "FILTER",
            "PREFIX", "DISTINCT", "CONCAT", "GROUP_CONCAT", "NOT", "IN", "LIMIT",
            "BIND", "VALUES", "HAVING", "ASC", "DESC", "UNION", "STR"}
TOKEN = re.compile(r'(\?[A-Za-z_]\w*|"(?:[^"\\]|\\.)*"|[A-Za-z_]\w*:[A-Za-z_]\w*|[A-Za-z_]\w*)')


def esc(t):
    return H.escape(str(t), quote=False)


def hl(sparql):
    out = []
    for line in sparql.split("\n"):
        if line.strip().startswith("#"):
            out.append(f'<span class="c-comment">{esc(line)}</span>')
            continue
        buf = []
        for piece in TOKEN.split(line):
            if not piece:
                continue
            if piece.startswith("?"):
                buf.append(f'<span class="c-uri">{esc(piece)}</span>')
            elif piece.startswith('"'):
                buf.append(f'<span class="c-lit">{esc(piece)}</span>')
            elif ":" in piece:
                pre = piece.split(":", 1)[0]
                cls = "c-prop" if pre in ("rdfs", "rdf", "owl", "xsd") else "c-class"
                buf.append(f'<span class="{cls}">{esc(piece)}</span>')
            elif piece in KEYWORDS:
                buf.append(f'<span class="c-prop">{esc(piece)}</span>')
            else:
                buf.append(esc(piece))
        out.append("".join(buf))
    return "\n".join(out)


def local(u):
    return u.rsplit("#", 1)[-1]


def table(vars_, rows, headers):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for r in rows:
        tds = []
        for i, v in enumerate(r):
            if i == 0:
                tds.append(f'<td class="mono">{esc(local(v))}</td>')
            else:
                tds.append(f'<td>{esc(v) if v.strip() else "&mdash;"}</td>')
        body.append("          <tr>" + "".join(tds) + "</tr>")
    return ("      <div class=\"ans-scroll\"><table>\n"
            f"        <thead><tr>{th}</tr></thead>\n"
            "        <tbody>\n" + "\n".join(body) + "\n"
            "        </tbody>\n"
            "      </table></div>")


# ─────────────────────────────────────────────────────────────
# 3.1 — the extraction wizard
# ─────────────────────────────────────────────────────────────

PROMPT = """Based on the headers of this CSV file and our ontology, please analyze these posts and fill them into the CSV file. There are  2 links (https://weibo.com/3054324355/5341196991072199; https://weibo.com/5974630971/5337482515973538).
Requirements:
Every post must have corresponding content for the nine core classes: CyberRitualCase, Subject, PerformativeAction, Platform, SecularPressure, RemediatedSignifier, RitualSymbol, Archetype, RemediationStrategy, and AffectiveOutcome. Specifically:
For SecularPressure and AffectiveOutcome, you need to uncover the poster's expectations that may be revealed behind the text or wishes, and then categorize them accordingly.
For RemediatedSignifier, you only need to identify whether the user posted an image or a video.
For RitualSymbol, you need to interpret which ritualistic "imageries" (symbolic elements) are used in the images or videos.
Subclasses such as Mantra, Emoji, etc., may not necessarily have corresponding content for every post; leaving them blank is normal.
You must strictly adhere to the rules defined in the ontology."""


def build_wizard(csv_header, csv_rows):
    n_rows = len(csv_rows)
    n_cols = len(csv_header)

    head = "".join(f"<th>{esc(h)}</th>" for h in csv_header)
    body = []
    for i, r in enumerate(csv_rows, 1):
        tds = [f'<td class="wz-idx">{i}</td>']
        for j, cell in enumerate(r):
            v = cell.strip()
            if j == 0:
                tds.append(f'<td class="wz-case">{esc(v)}</td>')
            elif not v:
                tds.append('<td class="wz-nil">—</td>')
            else:
                parts = [p.strip() for p in v.split(";") if p.strip()]
                tds.append("<td>" + "<span class=\"wz-cell\">" +
                           "</span><span class=\"wz-cell\">".join(esc(p) for p in parts) +
                           "</span></td>")
        body.append("            <tr>" + "".join(tds) + "</tr>")

    return f'''  <div class="wz">
    <div class="wz-rail" role="tablist" aria-label="Data extraction steps">
      <button class="wz-tab is-active" data-step="1" role="tab" aria-selected="true">
        <span class="wz-num">1</span>
        <span class="wz-txt"><span class="wz-t">Internet posts</span>
        <span class="wz-s">raw material collected from social media</span></span>
      </button>
      <button class="wz-tab" data-step="2" role="tab" aria-selected="false">
        <span class="wz-num">2</span>
        <span class="wz-txt"><span class="wz-t">AI recognition with prompt</span>
        <span class="wz-s">multimodal extraction driven by the ontology</span></span>
      </button>
      <button class="wz-tab" data-step="3" role="tab" aria-selected="false">
        <span class="wz-num">3</span>
        <span class="wz-txt"><span class="wz-t">Human check &amp; structured data into CSV</span>
        <span class="wz-s">manually verified and unified terminology</span></span>
      </button>
      <div class="wz-foot">
        <span class="wz-foot-k">Corpus</span>
        <span class="wz-foot-v">{n_rows} posts</span>
        <span class="wz-foot-k">Schema</span>
        <span class="wz-foot-v">{n_cols} columns</span>
      </div>
    </div>

    <div class="wz-stage">

      <!-- STEP 1 ───────────────────────────────────────── -->
      <div class="wz-panel is-active" data-step="1">
        <div class="wz-head">
          <span class="wz-step">Step 1 / 3</span>
          <h3>Internet posts</h3>
          <p>The raw material is not a spreadsheet yet — it is a pair of posts that a user
             actually published on Weibo: an illustrated good-luck image and a devotional
             picture of Caishen, the God of Wealth. Everything the ontology later formalises
             is already present here, as image, text, emoji and caption.</p>
        </div>
        <div class="wz-posts">
          <figure class="wz-post">
            <img src="../assets/post_wealth_cat_wish.png" alt="Illustrated good-luck post with two cartoon cats among banknotes" loading="lazy">
            <figcaption>
              <span class="wz-tag">Post 1</span>
              Weibo · illustrated wish image
              <em>Two cartoon cats on banknotes, the caption 好運來 (“may good fortune come”),
              scattered 100-yuan notes and heart emoji.</em>
            </figcaption>
          </figure>
          <figure class="wz-post">
            <img src="../assets/post_caishen_blessing.png" alt="Devotional painting of Caishen, the Chinese God of Wealth, riding a golden lion" loading="lazy">
            <figcaption>
              <span class="wz-tag">Post 2</span>
              Weibo · devotional wealth image
              <em>Caishen riding a golden lion, cranes, a halo of coins and gold ingots, with
              the watermark 九叔风水命理.</em>
            </figcaption>
          </figure>
        </div>
        <p class="wz-hint">These two images are the input of the next step. Nothing here is typed by
           hand yet — the whole point of the pipeline is that the ontology decides what to look for.</p>
      </div>

      <!-- STEP 2 ───────────────────────────────────────── -->
      <div class="wz-panel" data-step="2">
        <div class="wz-head">
          <span class="wz-step">Step 2 / 3</span>
          <h3>AI recognition with prompt</h3>
          <p>Instead of describing the images freely, the multimodal model is handed the CSV
             headers and the ontology rules, then asked to fill one row per post.</p>
        </div>
        <div class="wz-ai">
          <div class="wz-prompt">
            <div class="wz-prompt-head"><span class="wz-dot"></span>Prompt sent to the model</div>
            <pre>{esc(PROMPT)}</pre>
          </div>
          <div class="wz-bot">
            <div class="wz-think" id="wzThink">
              <span class="wz-think-t" id="wzThinkT">Reading the CSV headers…</span>
            </div>
            <div class="wz-robot" aria-hidden="true">
              <div class="wz-ranti"><span class="wz-ranti-dot"></span></div>
              <div class="wz-rhead">
                <span class="wz-reye"></span><span class="wz-reye"></span>
                <span class="wz-rmouth"></span>
              </div>
              <div class="wz-rbody"><span class="wz-rslot"></span><span class="wz-rslot"></span></div>
            </div>
            <p class="wz-bot-cap">Scanning the image, matching every element against the header row</p>
            <div class="wz-header-mem">
              <span class="wz-hm-k">In mind — the 9 core classes to fill</span>
              <div class="wz-hm-row" id="wzMem"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- STEP 3 ───────────────────────────────────────── -->
      <div class="wz-panel" data-step="3">
        <div class="wz-head">
          <span class="wz-step">Step 3 / 3</span>
          <h3>Human check &amp; structured data into CSV</h3>
          <p>The model's draft is inspected by hand and the terminology is unified against the
             ontology. What comes out is the full structured dataset — all {n_cols} columns for
             {n_rows} posts. Scroll the table in both directions.</p>
        </div>
        <div class="wz-csv">
          <div class="wz-csv-bar">
            <span class="wz-csv-file">wishgraph_structured_cases.csv</span>
            <span class="wz-csv-meta">{n_rows} rows × {n_cols} columns</span>
          </div>
          <div class="wz-csv-scroll">
            <table class="wz-table">
              <thead><tr><th class="wz-idx">#</th>{head}</tr></thead>
              <tbody>
{chr(10).join(body)}
              </tbody>
            </table>
          </div>
        </div>
        <p class="wz-hint">Vertical scrollbar on the right, horizontal scrollbar at the bottom of the
           frame — the table keeps its own size instead of stretching the page.</p>
      </div>

    </div>
  </div>'''


# ─────────────────────────────────────────────────────────────
# 3.3 — read-outs, recomputed for the 18-case corpus
# ─────────────────────────────────────────────────────────────

BLOCKS = [
    dict(key="cq1",
         h3="CQ1 — Performative Action, Subject and Platform",
         q="What performative actions are carried out in each cyber-ritual case, who performs them, and on which platform does the case circulate?",
         props="cw:hasPerformativeAction · cw:performedBy · cw:circulatesOn",
         headers=["Case", "Performative Action (performed by)", "Platform"],
         note="""<strong>Read-out.</strong> Across the eighteen cases the ritual is overwhelmingly a
         <strong>posting</strong> act: sixteen cases consist of publishing a wishing artefact, one is a pure
         <strong>commenting</strong> ritual (<code>Case_XiaohongshuCET6Comment</code>), and one —
         <code>Case_InstagramWealth</code> — carries both, a materialistic user posting a wealth-manifesting
         video and a commenter claiming that wealth in the replies. That split is why
         <code>cw:performedBy</code> is modelled on the <em>action</em> rather than on the case: one case can
         host more than one ritual role. Platform distribution follows the same logic —
         Xiaohongshu hosts seven of the eighteen cases, TikTok four, Instagram three, Weibo two, and
         Bilibili and X one each — so the practice is concentrated on image-and-note platforms even though
         the corpus also reaches the short-video and microblogging ecosystems."""),

    dict(key="cq2",
         h3="CQ2 — Trigger / Pressure",
         q="Which secular pressure triggers each cyber-ritual case, and what type of pressure is it?",
         props="cw:triggeredBy · cw:SecularPressure 的子类",
         headers=["Case", "Secular Pressure", "Pressure Type"],
         note="""<strong>Read-out.</strong> Fifteen of the eighteen cases respond to a
         <strong>mundane</strong> pressure — exam or career pressure, future uncertainty, status anxiety,
         romantic desire, wealth and prosperity wishes — while only three are triggered by an
         <strong>existential</strong> pressure: modern spiritual anxiety, illness, and illness inside the
         family. Cyber-ritual wishing in this corpus is therefore predominantly a response to
         <em>everyday</em> precarity rather than to mortality or cosmic doubt. Note that the same pressure
         class recurs across ritual formats and platforms: exam pressure triggers both a posting ritual
         (<code>Case_CatWish</code>) and a commenting ritual (<code>Case_XiaohongshuCET6Comment</code>), and
         career-and-wealth pressure spans Xiaohongshu, Weibo and Instagram. The pressure <em>type</em> is not
         stored as a literal string — it is read from the sub-class the pressure instance is typed with, so
         the answer is derived from the class hierarchy rather than duplicated in the data."""),

    dict(key="cq3",
         h3="CQ3 — Transformation and Affective Outcome",
         q="Which remediation strategy transforms each cyber-ritual case, and what outcome does the case resolve into?",
         props="cw:transformedVia · cw:resolvesIntoAffect",
         headers=["Case", "Remediation Strategy", "Strategy Type", "Affective Outcome"],
         note="""<strong>Read-out.</strong> All five remediation types are attested, and together they form a
         gradient of distance from the original sacred source. <strong>Digital Transposition</strong> (four
         cases) restores the traditional icon essentially unchanged — a Buddha photograph, a healing
         talisman, a wealth-god altar. <strong>Sacred Amplification</strong> (three cases) keeps an already
         sacred source and intensifies its aura. <strong>Sacred Hybridization</strong> (two cases) crosses the
         sacred frame with a non-sacred figure. <strong>Secular Idol Deification</strong> (three cases) and
         <strong>Symbolic Enchantment</strong> (six cases) replace the deity outright — with a celebrity meme,
         a sports car, a cheque or a stack of cash. Secular enchantment is thus the single largest strategy
         in the corpus. The outcome vocabulary tracks the same gradient: restorative strategies resolve into
         domain-specific reassurance (health, prosperity, family recovery), while the deifying and
         enchanting strategies resolve into self-persuasive states such as <em>Ironic Comfort of Wealth
         Delusion</em>, <em>Prosperity Expectation</em> or <em>Financial Empowerment</em> — seventeen distinct
         outcomes for eighteen cases."""),

    dict(key="cq4",
         h3="CQ4 — Signifier and Ritual Symbol",
         q="Which remediated signifier is employed in each cyber-ritual case, and which ritual symbols does it contain?",
         props="cw:employsSignifier · cw:containsSymbol",
         headers=["Case", "Remediated Signifier", "Signifier Type", "Ritual Symbols"],
         note="""<strong>Read-out.</strong> Signifier type tracks the platform economy: eleven cases use still
         <strong>images</strong>, which cluster on Xiaohongshu, Instagram and Weibo where they are easy to
         save, re-post and keep as a phone wallpaper, while seven use <strong>videos</strong>, which dominate
         TikTok, Bilibili and X, where motion and audio carry the ritual charge. Ritual symbols are not
         decoration — they are the load-bearing vocabulary of the practice: a knitted kasaya, a lotus
         cushion, a manifesting mantra, a talisman drawn in red ink, a praying-hands emoji, an ingot of gold.
         Only two cases (<code>Case_HealthWish</code> and <code>Case_InstagramTraditionalPrayer</code>)
         carry no ritual symbol at all, and both are Digital Transposition cases, in which sacredness is
         inherited from the source rather than produced by remediation. Note the modelling decision: symbols
         hang off the <em>signifier</em>, not off the case, because one signifier can circulate several
         symbols at once — the richest case in the corpus stacks three."""),

    dict(key="cq5",
         h3="CQ5 — Archetype and Archetype Type",
         q="For each cyber-ritual case, which archetype is remediated by its signifier, and what type of archetype is it?",
         props="cw:employsSignifier · cw:remediates · cw:Archetype 的子类",
         headers=["Case", "Archetype", "Archetype Type"],
         note="""<strong>Read-out.</strong> Four archetype types are attested across the corpus:
         <strong>Traditional</strong> (Mahayana Buddhism, Medicine Buddha, Guanyin, Caishen, the God of
         Wealth and a Taoist healing talisman — eight cases), <strong>Modern</strong> (Kris Jenner and a
         supportive celebrity momager meme — five cases), <strong>Animal</strong> (the cat, the butterfly,
         the lucky rabbit — three cases) and <strong>Secular Commodity</strong> (the luxury sports car, the
         stack of cash, wealth assets, a romantic couple ideal and a successful executive ideal — three
         cases). The last two categories are the analytical payoff of the ontology: they mark the moment when
         the sacred slot is filled not by a deity but by <em>capital</em>. <code>Case_CatWish</code> is the
         only hybrid case, remediating an animal archetype and a traditional one through a single image —
         precisely the <code>cw:SacredHybridization</code> that its strategy instance is typed with. As in
         CQ2, the archetype type is read from the class hierarchy rather than from a literal."""),
]


def build_block(spec, sparql):
    r = RES[spec["key"]]
    props = spec["props"].replace(" 的子类", " sub-classes")
    return "\n".join([
        '  <div class="cq-block">',
        f'    <h3>{spec["h3"]}</h3>',
        f'    <p>{spec["q"]}</p>',
        f'    <div class="cq-props">{props}</div>',
        f'    <div class="code-block">{hl(sparql)}</div>',
        '    <div class="answer-block">',
        f'      <div class="answer-head"><span>Query Result</span><span class="rows">{len(r["rows"])} rows</span></div>',
        table(r["vars"], r["rows"], spec["headers"]),
        '    </div>',
        f'    <p class="answer-note">{spec["note"]}</p>',
        '  </div>',
    ])


def extract_queries(rq_path):
    txt = open(rq_path, encoding="utf-8").read()
    bodies = []
    for part in txt.split("#" * 74):
        part = part.strip()
        if not part or "SELECT" not in part:
            continue
        j = part.index("\n", part.index("PREFIX rdfs"))
        bodies.append(part[part.index("\n", j):].strip())
    return bodies


def find_div(s, start):
    i = s.index('<div class="cq-block">', start)
    depth, j = 0, i
    pat = re.compile(r"<div\b|</div>")
    while True:
        m = pat.search(s, j)
        if not m:
            raise ValueError("unbalanced div")
        depth += 1 if m.group(0) == "<div" else -1
        j = m.end()
        if depth == 0:
            return i, j


def section_span(s, sec_id):
    a = s.index(f'<section id="{sec_id}"')
    b = s.index("</section>", a) + len("</section>")
    return a, b


# ─────────────────────────────────────────────────────────────
# new CSS
# ─────────────────────────────────────────────────────────────

WIZARD_CSS = r"""
/* ── 3.1 extraction wizard ── */
.wz {
  display: grid; grid-template-columns: 262px 1fr;
  border: 1px solid var(--border); border-radius: 12px; overflow: hidden;
  background: var(--card-bg); box-shadow: 0 8px 28px rgba(60,30,0,.08);
  margin-bottom: 1.6rem;
}
.wz-rail {
  background: linear-gradient(180deg,#221105,#3b1d04);
  padding: .75rem .6rem .7rem; display: flex; flex-direction: column; gap: .4rem;
}
.wz-tab {
  display: grid; grid-template-columns: 24px 1fr; gap: .55rem; align-items: start;
  text-align: left; cursor: pointer; font-family: Arial, sans-serif;
  background: rgba(255,255,255,.035); border: 1px solid transparent;
  border-left: 3px solid transparent; border-radius: 8px;
  padding: .6rem .6rem .6rem .5rem; color: #bf9f57;
  transition: background .22s ease, border-color .22s ease, color .22s ease;
}
.wz-tab:hover { background: rgba(201,148,58,.1); }
.wz-tab.is-active {
  background: rgba(201,148,58,.16); border-color: rgba(201,148,58,.3);
  border-left-color: var(--gold); color: #f6e3b4;
}
.wz-num {
  width: 22px; height: 22px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center;
  font-size: .68rem; font-weight: bold;
  background: rgba(201,148,58,.2); color: #e8cd8a; border: 1px solid rgba(201,148,58,.35);
}
.wz-tab.is-active .wz-num { background: var(--gold); color: #2a1400; border-color: var(--gold-light); }
.wz-txt { display: block; min-width: 0; }
.wz-t { display: block; font-size: .775rem; line-height: 1.3; }
.wz-s { display: block; font-size: .62rem; color: rgba(196,163,90,.62); line-height: 1.45; margin-top: .18rem; }
.wz-foot {
  margin-top: auto; padding-top: .7rem; border-top: 1px solid rgba(201,148,58,.2);
  display: grid; grid-template-columns: auto 1fr; gap: .1rem .5rem; align-items: baseline;
}
.wz-foot-k { font-family: Arial, sans-serif; font-size: .58rem; letter-spacing: .08em;
  text-transform: uppercase; color: rgba(201,148,58,.55); }
.wz-foot-v { font-family: Arial, sans-serif; font-size: .68rem; color: #e0c179; }

.wz-stage { min-width: 0; padding: 1.15rem 1.25rem 1.25rem; }
.wz-panel { display: none; animation: wzIn .32s ease both; }
.wz-panel.is-active { display: block; }
@keyframes wzIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.wz-head { margin-bottom: 1rem; }
.wz-step {
  display: inline-block; font-family: Arial, sans-serif; font-size: .6rem;
  letter-spacing: .09em; text-transform: uppercase; color: var(--gold);
  background: var(--tag-bg); border: 1px solid var(--tag-border);
  border-radius: 20px; padding: .1rem .55rem; margin-bottom: .4rem;
}
.wz-head h3 { font-size: 1.02rem; color: var(--accent); margin-bottom: .3rem; }
.wz-head p { font-size: .82rem; color: var(--muted); font-family: Arial, sans-serif; line-height: 1.65; }
.wz-hint {
  font-size: .72rem; color: var(--muted); font-family: Arial, sans-serif;
  margin-top: .8rem; padding-left: .7rem; border-left: 3px solid var(--gold-light); line-height: 1.6;
}

/* step 1 — the two posts */
.wz-posts { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.wz-post {
  margin: 0; background: #fff; border: 1px solid var(--border); border-radius: 10px;
  overflow: hidden; display: flex; flex-direction: column;
  transition: transform .3s cubic-bezier(.2,.7,.3,1), box-shadow .3s ease;
}
.wz-post:hover { transform: translateY(-3px); box-shadow: 0 10px 26px rgba(60,30,0,.13); }
.wz-post img {
  width: 100%; height: 260px; object-fit: contain;
  background: repeating-conic-gradient(#f6efe2 0% 25%, #fdf8ef 0% 50%) 50%/18px 18px;
  display: block;
}
.wz-post figcaption {
  font-family: Arial, sans-serif; font-size: .7rem; color: var(--muted);
  padding: .6rem .75rem .7rem; line-height: 1.55; border-top: 1px solid var(--border);
}
.wz-post figcaption em { display: block; font-style: italic; color: #8b7355; margin-top: .25rem; font-size: .68rem; }
.wz-tag {
  display: inline-block; font-size: .58rem; letter-spacing: .07em; text-transform: uppercase;
  background: var(--gold); color: #fff; border-radius: 20px;
  padding: .08rem .45rem; margin-right: .4rem;
}

/* step 2 — prompt + robot */
.wz-ai { display: grid; grid-template-columns: 1fr 236px; gap: 1rem; align-items: start; }
.wz-prompt { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; background: #1b0e03; }
.wz-prompt-head {
  display: flex; align-items: center; gap: .4rem;
  background: linear-gradient(90deg,#2c1a0e,#3d1a00); color: var(--gold-light);
  font-family: Arial, sans-serif; font-size: .63rem; letter-spacing: .07em;
  text-transform: uppercase; padding: .42rem .75rem;
}
.wz-dot { width: 7px; height: 7px; border-radius: 50%; background: #7ee081; box-shadow: 0 0 6px #7ee081; }
.wz-prompt pre {
  margin: 0; padding: .8rem .85rem; font-family: 'Courier New', monospace;
  font-size: .665rem; line-height: 1.68; color: #d8cbb6;
  white-space: pre-wrap; word-break: break-word; max-height: 372px; overflow-y: auto;
}
.wz-bot { display: flex; flex-direction: column; align-items: center; gap: .55rem; }
.wz-think {
  position: relative; background: #fff; border: 1px solid var(--tag-border);
  border-radius: 10px; padding: .45rem .6rem; min-height: 52px;
  display: flex; align-items: center; justify-content: center; width: 100%;
  box-shadow: 0 3px 10px rgba(201,148,58,.14);
}
.wz-think::after {
  content: ""; position: absolute; bottom: -7px; left: 50%; transform: translateX(-50%) rotate(45deg);
  width: 11px; height: 11px; background: #fff;
  border-right: 1px solid var(--tag-border); border-bottom: 1px solid var(--tag-border);
}
.wz-think-t {
  font-family: Arial, sans-serif; font-size: .685rem; color: var(--accent);
  text-align: center; line-height: 1.4;
}
.wz-robot { position: relative; padding-top: 14px; }
.wz-ranti {
  width: 2px; height: 13px; background: var(--gold);
  margin: 0 auto;
}
.wz-ranti-dot {
  display: block; width: 7px; height: 7px; border-radius: 50%; background: var(--red);
  transform: translate(-2.5px,-2px); animation: wzPulse 1.5s ease-in-out infinite;
}
@keyframes wzPulse { 0%,100% { opacity: .35; transform: translate(-2.5px,-2px) scale(.85); }
  50% { opacity: 1; transform: translate(-2.5px,-2px) scale(1.25); } }
.wz-rhead {
  position: relative; width: 88px; height: 66px; border-radius: 16px;
  background: linear-gradient(160deg,#4a2a08,#2a1404);
  border: 2px solid var(--gold);
  display: flex; align-items: center; justify-content: center; gap: 13px;
  margin: 0 auto;
}
.wz-reye {
  width: 15px; height: 15px; border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #bfe8ff, #4aa8e0 60%, #1b6fa8);
  animation: wzBlink 3.4s infinite;
}
.wz-reye:nth-child(2) { animation-delay: .12s; }
@keyframes wzBlink { 0%,92%,100% { transform: scaleY(1); } 95% { transform: scaleY(.12); } }
.wz-rmouth {
  position: absolute; bottom: 9px; left: 50%; transform: translateX(-50%);
  width: 22px; height: 3px; border-radius: 3px; background: rgba(240,208,133,.7);
  animation: wzTalk 1.15s ease-in-out infinite;
}
@keyframes wzTalk { 0%,100% { width: 12px; } 50% { width: 26px; } }
.wz-rbody {
  width: 66px; height: 40px; margin: 5px auto 0; border-radius: 9px;
  background: linear-gradient(160deg,#3d1d04,#221105); border: 2px solid rgba(201,148,58,.7);
  display: flex; align-items: center; justify-content: center; gap: 7px;
}
.wz-rslot {
  width: 16px; height: 16px; border-radius: 4px;
  background: rgba(240,208,133,.28); border: 1px solid rgba(240,208,133,.5);
  animation: wzSlot 2.1s ease-in-out infinite;
}
.wz-rslot:nth-child(2) { animation-delay: .35s; }
@keyframes wzSlot { 0%,100% { background: rgba(240,208,133,.22); } 50% { background: rgba(240,208,133,.6); } }
.wz-bot-cap {
  font-family: Arial, sans-serif; font-size: .62rem; color: var(--muted);
  text-align: center; line-height: 1.5; font-style: italic;
  border-top: 1px dashed var(--border); padding-top: .5rem; width: 100%;
}
.wz-header-mem { width: 100%; }
.wz-hm-k {
  display: block; font-family: Arial, sans-serif; font-size: .57rem;
  letter-spacing: .07em; text-transform: uppercase; color: var(--gold);
  margin-bottom: .35rem;
}
.wz-hm-row { display: flex; flex-wrap: wrap; gap: .22rem; }
.wz-hm-row span {
  font-family: Arial, sans-serif; font-size: .575rem;
  background: #fdf4e0; border: 1px solid var(--border); color: #8a6420;
  border-radius: 4px; padding: .1rem .32rem;
  transition: background .3s ease, color .3s ease, border-color .3s ease;
}
.wz-hm-row span.on { background: var(--gold); border-color: var(--gold); color: #fff; }

/* step 3 — the CSV table with its own scrollbars */
.wz-csv { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; background: #fff; }
.wz-csv-bar {
  display: flex; justify-content: space-between; align-items: center; gap: .6rem;
  background: linear-gradient(90deg,#2c1a0e,#3d1a00); color: var(--gold-light);
  font-family: Arial, sans-serif; font-size: .64rem; letter-spacing: .05em;
  padding: .42rem .75rem;
}
.wz-csv-file { font-family: 'Courier New', monospace; }
.wz-csv-meta { background: rgba(240,208,133,.18); border-radius: 10px; padding: .05rem .5rem; font-size: .6rem; }
.wz-csv-scroll { max-height: 430px; overflow: auto; }
.wz-table { border-collapse: separate; border-spacing: 0; font-family: Arial, sans-serif; font-size: .64rem; width: max-content; min-width: 100%; }
.wz-table thead th {
  position: sticky; top: 0; z-index: 3;
  background: #fdf4e0; color: var(--accent); text-align: left;
  font-size: .6rem; letter-spacing: .03em; text-transform: uppercase;
  padding: .45rem .55rem; border-bottom: 1px solid var(--border);
  border-right: 1px solid #f0e3c6; white-space: nowrap;
}
.wz-table thead th.wz-idx { left: 0; z-index: 4; }
.wz-table tbody td {
  padding: .38rem .55rem; border-bottom: 1px solid #f3ead6; border-right: 1px solid #f6efdf;
  color: var(--ink); vertical-align: top; max-width: 220px;
}
.wz-table tbody tr:nth-child(even) td { background: #fffdf7; }
.wz-table tbody tr:hover td { background: #fff7e6; }
.wz-table td.wz-idx, .wz-table th.wz-idx {
  position: sticky; left: 0; z-index: 2; width: 34px; min-width: 34px;
  background: #fdf4e0; color: var(--gold); font-weight: bold; text-align: center;
}
.wz-table tbody tr:nth-child(even) td.wz-idx { background: #faf0da; }
.wz-table tbody tr:hover td.wz-idx { background: #f7ecd2; }
.wz-table td.wz-case {
  background: #fff9ec; font-family: 'Courier New', monospace; font-size: .6rem;
  color: var(--accent); white-space: nowrap; position: sticky; left: 34px; z-index: 1;
  border-right: 1px solid var(--border);
}
.wz-table tbody tr:hover td.wz-case { background: #fdf1d9; }
.wz-table td.wz-nil { color: #cbbfa9; text-align: center; }
.wz-cell {
  display: inline-block; background: #fdf4e0; border: 1px solid #f0e0bc;
  color: #8a6420; border-radius: 10px; padding: .03rem .35rem; margin: .05rem .12rem .05rem 0;
  white-space: nowrap; font-size: .6rem;
}

/* 3.3 answer tables: show every row, scroll only if the page gets narrow */
.ans-scroll { overflow-x: auto; }
.ans-scroll thead th { position: sticky; top: 0; z-index: 2; background: #fdf4e0; }

/* keep the SPARQL line breaks inside the code viewer */
.code-block { white-space: pre; }

@media (max-width: 1080px) {
  .wz { grid-template-columns: 1fr; }
  .wz-rail { flex-direction: row; flex-wrap: wrap; }
  .wz-tab { flex: 1 1 210px; }
  .wz-foot { display: none; }
}
@media (max-width: 860px) {
  .wz-posts { grid-template-columns: 1fr; }
  .wz-ai { grid-template-columns: 1fr; }
  .wz-bot { flex-direction: row; flex-wrap: wrap; justify-content: center; }
  .wz-header-mem { flex: 1 1 100%; }
}
"""

ROBOT_JS = r"""
// ── 3.1 extraction wizard ──
(function () {
  const tabs = Array.from(document.querySelectorAll('.wz-tab'));
  const panels = Array.from(document.querySelectorAll('.wz-panel'));
  if (!tabs.length) return;

  tabs.forEach(tab => tab.addEventListener('click', () => {
    const step = tab.dataset.step;
    tabs.forEach(t => {
      const on = t === tab;
      t.classList.toggle('is-active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    panels.forEach(p => p.classList.toggle('is-active', p.dataset.step === step));
  }));

  // the robot's inner monologue
  const lines = [
    'Reading the CSV headers\u2026',
    'Nine core classes to fill\u2026',
    'Analysing the two Weibo images\u2026',
    'Image or video? That fixes the signifier\u2026',
    'Interpreting the ritual imageries\u2026',
    'Uncovering the wish behind the caption\u2026',
    'Checking the ontology rules before filling\u2026'
  ];
  const CLASSES = ['CyberRitualCase', 'Subject', 'PerformativeAction', 'Platform',
                   'SecularPressure', 'RemediatedSignifier', 'RitualSymbol',
                   'Archetype', 'RemediationStrategy', 'AffectiveOutcome'];
  const tEl = document.getElementById('wzThinkT');
  const mEl = document.getElementById('wzMem');
  if (!tEl || !mEl) return;

  mEl.innerHTML = CLASSES.map(c => `<span>${c}</span>`).join('');
  const chips = Array.from(mEl.children);
  let i = 0, k = 0;
  setInterval(() => {
    chips.forEach(c => c.classList.remove('on'));
    chips[k % chips.length].classList.add('on');
    k++;
    if (k % 2 === 0) {
      tEl.textContent = lines[i % lines.length];
      i++;
    }
  }, 900);
})();
"""


def main():
    s = open(CH3, encoding="utf-8").read()

    # ── 0. drop the duplicated chapter-3 CSS block ──
    marker = "/* ── Chapter 3 v2: dimension legend ── */"
    a = s.index(marker)
    b = s.index(marker, a + 10)
    seg_len = b - a
    # only drop if the following text really repeats the same block
    if s[a:b].strip()[:180] == s[b:b + seg_len].strip()[:180]:
        s = s[:a] + s[b:]
        print(f"removed duplicated CSS block ({seg_len} bytes)")

    # ── 1. strip the Chinese one-liners ──
    n_zh = len(re.findall(r'<p class="cq-zh">.*?</p>\s*', s, re.S))
    s = re.sub(r'\s*<p class="cq-zh">.*?</p>', "", s, flags=re.S)
    s = re.sub(r"\.cq-zh\s*\{[^}]*\}\s*", "", s)
    print(f"removed {n_zh} Chinese read-through lines + .cq-zh rule")

    # ── 2. append the new wizard CSS ──
    s = s.replace("</style>", WIZARD_CSS + "\n</style>", 1)

    # ── 3. rebuild section 3.1 ──
    with open(SRC_CSV, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    csv_header = rows[0]
    csv_rows = [r + [""] * (len(csv_header) - len(r)) for r in rows[1:] if any(c.strip() for c in r)]

    a31, b31 = section_span(s, "sec31")
    new31 = f'''<section id="sec31">
<div class="section">
  <h2 class="section-title"><span class="num pill">3.1</span> Data and Extraction
    <span class="step-label sub">Raw material &rarr; structured data</span></h2>
  <p style="font-size:0.88rem;color:var(--muted);font-family:Arial,sans-serif;margin-bottom:1.6rem;">
    The corpus does not begin as a dataset. It begins as a pair of posts that people actually
    published on Weibo, and it becomes structured data through three steps: collecting the posts,
    letting a multimodal model read them against the ontology, and checking the result by hand.
    Step through the three stages below.
  </p>

{build_wizard(csv_header, csv_rows)}
</div>
</section>'''
    s = s[:a31] + new31 + s[b31:]
    print(f"section 3.1 rebuilt ({len(new31)} bytes)")

    # ── 4. insert the English paragraph in 3.2 ──
    anchor = '  <figure class="onto-graph">'
    para = '''  <p style="font-size:0.88rem;color:var(--muted);font-family:Arial,sans-serif;margin-bottom:1.4rem;">
    Through a Python script, the structured data recorded in
    <code>wishgraph_structured_cases.csv</code> is converted into machine-readable RDF instances:
    one individual for every case and for each of its dimension values, linked by the object
    properties declared in the ontology. Loading those instances into the ontology described in this
    section yields the WishGraph knowledge graph &mdash; the <strong>T-BOX</strong> (the schema, its
    classes and properties) plus the <strong>A-BOX</strong> (the assertions about concrete cyber-ritual
    cases) together make up <strong>Wish Graph</strong>, the graph that is queried in 3.3.
  </p>

'''
    assert anchor in s, "3.2 figure anchor not found"
    s = s.replace(anchor, para + anchor, 1)
    print("section 3.2 paragraph inserted")

    # ── 5. fix the 3.3 intro and rebuild the five blocks ──
    intro_anchor = ('  <p style="font-size:0.88rem;color:var(--muted);font-family:Arial,sans-serif;'
                    'margin-bottom:1.6rem;">\n    The five competency questions were reformulated as SPARQL queries')
    new_intro = '''  <p style="font-size:0.88rem;color:var(--muted);font-family:Arial,sans-serif;margin-bottom:1.6rem;">
    The five competency questions were reformulated as SPARQL queries and executed against the
    A-Box. Every query below is followed by its actual result set, so the chapter doubles as
    evidence that the ontology is queryable rather than merely descriptive. The queries run
    against the <code>cw:</code> namespace of the T-Box
    (<code>http://www.ontologydesignpatterns.org/ont/cyberwishing/cw.owl#</code>) and read each
    dimension&rsquo;s <em>type</em> from the sub-class the instance is typed with, so every table
    below can be reproduced in Prot&eacute;g&eacute; or in any endpoint holding
    <code>ontology/wishgraph_full.ttl</code>.
  </p>'''
    a33 = s.index('id="sec33"')
    idx = s.index(intro_anchor, a33)
    end = s.index("</p>", idx) + len("</p>")
    s = s[:idx] + new_intro + s[end:]
    print("section 3.3 intro replaced")

    queries = extract_queries(f"{ROOT}/ontology/sparql_queries.rq")
    assert len(queries) == 5, f"expected 5 queries, got {len(queries)}"
    first, _ = find_div(s, a33)
    last = first
    for _ in range(5):
        _, last = find_div(s, last)
    new_blocks = "\n\n".join(build_block(spec, q) for spec, q in zip(BLOCKS, queries))
    s = s[:first] + new_blocks + s[last:]
    print("five CQ blocks rebuilt")

    # ── 6. JS: drop the dead table builders, add the wizard logic ──
    s = re.sub(r'^const FIELDS = \[.*?\];\s*$', "", s, flags=re.M | re.S)
    s = re.sub(r'^const CASES = \[.*?\];\s*$', "", s, flags=re.M | re.S)
    start = s.index("// ── Dataset table ──")
    end = s.index("</script>", start)
    s = s[:start] + s[end:]
    print("removed obsolete dataset-table JS")
    s = s.replace("</script>\n</body>", ROBOT_JS + "\n</script>\n</body>", 1)

    open(CH3, "w", encoding="utf-8").write(s)
    print(f"chapter3.html written: {len(s)} bytes")

    # the page must survive being opened on its own -- embed the figures
    inline_assets(CH3)


if __name__ == "__main__":
    main()
