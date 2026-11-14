exec(open("/tmp/final/helpers.py").read())
import pandas as pd, re
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR

T = "/mnt/user-data/uploads/Project/WildfireDamageCP/results/tables/"
FIRES = ["Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton"]
CATS = ["Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton 2025"]
ev = lambda s: "Eaton" if s.startswith("Eaton") else s.split(": ")[1]
num = lambda s: float(str(s).split(" ")[0])
mod = lambda s: s.split(" ")[0]
def load(f):
    d = pd.read_csv(T + f); d["fire"] = d.evaluation.map(ev); d["m"] = d.model.map(mod); return d
A, K, C, R = load("table2_accuracy.csv"), load("table3_calibration.csv"), load("table4_conformal.csv"), load("table5b_routing_A1.csv")
E1 = pd.read_csv(T + "e1_summary.csv")
def getv(d, col, **f):
    for k_, v in f.items(): d = d[d[k_] == v]
    return [num(x) for x in d.set_index("fire").reindex(FIRES)[col]]
def e1v(model, meth, arm, n, col):
    q = E1[(E1.model == model) & (E1.scheme == "B") & (E1.method == meth) & (E1.arm == arm) & (E1.n == n)].set_index("tgt")
    return [float(q.loc[t, col]) for t in ["fold1", "fold2", "fold3", "fold4", "eaton"]]
TIER = {"T1": GREEN, "T2": GREY, "T3": GOLD}

PL = (0.08, 0.14, 0.8, 0.68)  # manual inner plot layout (x, y, w, h) as fractions


def bar_chart(s, x, y, w, h, series, vmin, vmax, fmt='0.00', ref=None, reflab=None, cats=CATS, lsize=12):
    cd = CategoryChartData(); cd.categories = cats
    for nm, v, col in series: cd.add_series(nm, v)
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd); ch = gf.chart
    ch.font.name = FONT; ch.font.size = Pt(13); ch.font.color.rgb = BODY
    va = ch.value_axis; va.minimum_scale = vmin; va.maximum_scale = vmax; va.has_major_gridlines = False
    va.tick_labels.font.size = Pt(12); va.format.line.fill.background(); va.tick_labels.number_format = fmt; va.tick_labels.number_format_is_linked = False
    ch.category_axis.tick_labels.font.size = Pt(14); ch.category_axis.format.line.color.rgb = GREY
    pl = ch.plots[0]; pl.gap_width = 60; pl.overlap = -5
    for i, (nm, v, col) in enumerate(series):
        se = pl.series[i]; se.format.fill.solid(); se.format.fill.fore_color.rgb = col
        se.data_labels.show_value = True; se.data_labels.number_format = fmt; se.data_labels.number_format_is_linked = False
        se.data_labels.font.size = Pt(lsize); se.data_labels.font.bold = True; se.data_labels.font.color.rgb = BODY
        se.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    ch.has_legend = len(series) > 1
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(14); ch.legend.font.name = FONT
    pa = ch._chartSpace.chart.plotArea
    lay = pa.find(qn("c:layout"))
    if lay is None:
        lay = etree.SubElement(pa, qn("c:layout")); pa.remove(lay); pa.insert(0, lay)
    lay.append(etree.fromstring('<c:manualLayout xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:layoutTarget val="inner"/>'
                                '<c:xMode val="edge"/><c:yMode val="edge"/><c:x val="%g"/><c:y val="%g"/><c:w val="%g"/><c:h val="%g"/></c:manualLayout>' % PL))
    out = [gf]
    if ref is not None:
        yy = y + h * (PL[1] + PL[3] * (1 - (ref - vmin) / (vmax - vmin)))
        ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x + w * PL[0]), Inches(yy), Inches(x + w * (PL[0] + PL[2])), Inches(yy))
        ln.line.color.rgb = RED; ln.line.width = Pt(2); ln.line.dash_style = MSO_LINE.DASH
        lb = txt(s.shapes, x + w * (PL[0] + PL[2]) + 0.05, yy - 0.3, w * (1 - PL[0] - PL[2]) - 0.05, 0.6, reflab.split(" ", 1), 12, True, RED, PP_ALIGN.LEFT)
        out += [ln, lb]
    return out


# ---------- keep template title (0) and thank-you (15) ----------
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst); keep_last = ids[15]
for sid in ids[1:15]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
from pptx.opc.packuri import PackURI
prs.slides[1].part.partname = PackURI("/ppt/slides/slide99.xml")
t = prs.slides[0]
for sh in t.shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("Presentation Title"):
        tf = sh.text_frame; p0 = tf.paragraphs[0]; r0 = p0.runs[0]; r0.text = "Knowing When to Ask an Inspector"
        sh.top = Inches(1.15); sh.height = Inches(2.0); tf.word_wrap = True; r0.font.size = Pt(40)
        for r in p0.runs[1:]: r.text = ""
    elif sh.has_text_frame and "October" in sh.text_frame.text:
        sh.top = Inches(3.35); ps = sh.text_frame.paragraphs
        ps[0].runs[0].text = "Calibrated wildfire damage assessment with inspector routing · CIV E 779 final presentation · November 2026"
        for r in ps[0].runs[1:]: r.text = ""
        rs = ps[-1].runs; rs[0].text = "By: "; rs[1].text = "Ziyad ElFayoumy, Ayman Saeed, Yeganeh"
        for r in rs[2:]: r.text = ""
t.notes_slide.notes_text_frame.text = ("No animation.\nKEY MESSAGE: We built and tested a way for damage-assessment AI to say when it is sure enough to skip a field visit, and when to send an inspector.\n"
    "Course: CIV E 779 (Machine Learning for Engineers), Fall 2026, Dr. Qipei (Gavin) Mei. All analysis finished 11 Nov 2026.")

# ---------- S2 problem ----------
s = new_slide("After a Fire, Who Checks Every House?",
 "CLICK ORDER: (1) before→after pair, (2) KPI tiles, (3) card.\n"
 "KEY MESSAGE: Damage checks after a wildfire are slow and manual; AI is fast but does not say when it is unsure.\n"
 "Numbers: CAL FIRE inspected 18,428 structures after the January 2025 Eaton Fire (DINS 2025 Eaton Public View, Data.gov). "
 "Jasper wildfire, July 2024: over $880 million insured damage (Insurance Bureau of Canada, 2024).\n"
 "Images: Eaton building DINS #14910 (destroyed), Maxar WorldView-3, 1 Jan vs 14 Jan 2025, 64 m x 64 m crops.\n"
 "Card source: Kshirsagar et al. (2026, Remote Sensing): xView2 top models generalise poorly to new regions.")
a = pic(s.shapes, "dins14910_pre.jpg", 0.6, 1.95, 3.0, 3.0); ar = arrow(s.shapes, 3.75, 3.25); b = pic(s.shapes, "dins14910_post.jpg", 4.35, 1.95, 3.0, 3.0)
c1 = txt(s.shapes, 0.6, 5.0, 3.0, 0.4, "Before · 1 Jan 2025", 14, True, GREEN, PP_ALIGN.CENTER)
c2 = txt(s.shapes, 4.35, 5.0, 3.0, 0.4, "After · 14 Jan 2025 · destroyed", 14, True, RED, PP_ALIGN.CENTER)
c3 = txt(s.shapes, 0.6, 5.45, 6.75, 0.4, "Eaton Fire, Altadena (California) · satellite view of one house", 13, False, DGREY, PP_ALIGN.CENTER)
g1 = group(s, [a, ar, b, c1, c2, c3])
g2 = group(s, [kpi(s.shapes, 7.9, 1.95, 2.35, 1.45, "18,428", "structures inspected on foot · Eaton 2025"),
               kpi(s.shapes, 10.45, 1.95, 2.35, 1.45, "$880M", "insured loss · Jasper 2024", key=True)])
g3 = group(s, card(s.shapes, 7.9, 3.75, 4.9, 1.6, "AI is fast, but…", "models trained on past fires lose accuracy on new fires, and do not say when they are unsure", accent=RED))
animate(s, [("fade", [g1]), ("fade", [g2]), ("fade", [g3])])

# ---------- S3 idea ----------
s = new_slide("Our Idea: Auto-Label When Sure, Ask When Not",
 "CLICK ORDER: pipeline builds left to right (4 clicks), then the two outcomes.\n"
 "KEY MESSAGE: Each house gets a SET of possible damage levels with a target error rate; one-label sets are auto-labelled, larger sets go to an inspector.\n"
 "Steps: (1) model gives 3 class probabilities (no damage / damaged / destroyed); (2) temperature scaling makes the probabilities honest (one parameter T fitted on calibration fires); "
 "(3) split conformal prediction turns probabilities into a set that should contain the true class 90% of the time (α = 0.10); "
 "(4) routing: a one-class set is auto-labelled, otherwise the house is sent to an inspector. The routing threshold is chosen on calibration fires so that ≤ 5% of destroyed homes are auto-labelled as something else.\n"
 "The example sets on this slide are illustrative (schematic).")
P = []
P.append(group(s, [pic(s.shapes, "dins14910_pre.jpg", 0.5, 2.05, 1.45, 1.45), pic(s.shapes, "dins14910_post.jpg", 0.5, 3.6, 1.45, 1.45),
                   txt(s.shapes, 0.3, 5.15, 1.85, 0.6, "pre + post image", 13, True, GREEN, PP_ALIGN.CENTER)]))
steps = [("Model", "T1 / T2 / T3", GREEN), ("Calibrate", "temperature scaling", GREEN), ("Prediction set", "conformal, 90% target", GREEN)]
for i, (tt, cap, col) in enumerate(steps):
    x = 2.55 + i * 2.55
    ar_ = arrow(s.shapes, x - 0.5, 3.35, 0.38, 0.4)
    bx = box(s.shapes, x, 2.75, 2.05, 1.6, fill=col); label(bx, [[(tt, True, GOLD, 19)], [(cap, False, WHITE, 13)]])
    P.append(group(s, [ar_, bx]))
o1 = [arrow(s.shapes, 10.2, 2.45, 0.4, 0.38), chip(s.shapes, 10.7, 2.3, 2.2, 0.7, "{destroyed}", fill=MINT, color=GREEN, size=16),
      txt(s.shapes, 10.7, 3.0, 2.2, 0.4, "1 label → auto-label", 14, True, LGREEN, PP_ALIGN.CENTER)]
o2 = [arrow(s.shapes, 10.2, 4.15, 0.4, 0.38), chip(s.shapes, 10.7, 4.0, 2.2, 0.7, "{damaged, destroyed}", fill=MINT, color=GREEN, size=14),
      txt(s.shapes, 10.7, 4.7, 2.2, 0.4, "2+ labels → inspector", 14, True, RED, PP_ALIGN.CENTER)]
bl = chip(s.shapes, 0.5, 6.05, 12.35, 0.6, "Rule: auto-label only if ≤ 5% of destroyed homes would be missed (checked on past fires)", fill=GOLD, color=GREEN, size=16)
animate(s, [("fade", [p]) for p in P] + [("fade", [group(s, o1 + o2)]), ("fade", [bl])])

# ---------- S4 different ----------
exec(open("/tmp/deck/new_diff_slide.py").read())

# ---------- S5 data ----------
s = new_slide("Data: Five Wildfires, 83,079 Buildings",
 "CLICK ORDER: (1) four xBD training/test fires, (2) Eaton external test, (3) label strip.\n"
 "KEY MESSAGE: Four xBD wildfires for leave-one-fire-out testing plus one field-inspected fire (Eaton 2025) the models never saw.\n"
 "Counts after harmonisation and exclusions (Table 1): Santa Rosa 21,869 (5,810 destroyed, 216 damaged); Woolsey 24,976 (4,180; 558); Pinery 5,428 (229; 180); Portugal 22,349 (1,090; 472); Eaton 8,457 (3,907; 543). "
 "xBD total 74,622 after excluding 138 buildings whose centre falls outside the crop.\n"
 "Sources: xBD/xView2 full GeoTIFF release (Gupta et al. 2019, CC BY-NC-SA); CAL FIRE DINS 2025 Eaton (field-inspection labels); Maxar Open Data WorldView-3 pair, 1 Jan and 14 Jan 2025 (CC BY-NC 4.0).\n"
 "Labels: no damage / damaged (xBD minor+major; DINS Affected 1–9%, Minor, Major) / destroyed. 'Damaged' is only 1–3% of xBD buildings and 6.4% of Eaton.\n"
 "socal-fire and woolsey-fire in xBD are the same area 4 days apart → merged into one 'Woolsey' fold.")
fires = [("xbd_santa-rosa-wildfire.jpg", "Santa Rosa", "California 2017", 21869, 5810), ("xbd_woolsey-fire.jpg", "Woolsey", "California 2018", 24976, 4180),
         ("xbd_pinery-bushfire.jpg", "Pinery", "Australia 2015", 5428, 229), ("xbd_portugal-wildfire.jpg", "Portugal", "Portugal 2017", 22349, 1090),
         ("dins14910_post.jpg", "Eaton", "California 2025", 8457, 3907)]
G = []
for i, (im, nm, wh, n, d) in enumerate(fires):
    x = 0.45 + i * 2.5 + (0.25 if i == 4 else 0)
    sh = [pic(s.shapes, im, x, 1.9, 2.25, 2.25), txt(s.shapes, x, 4.2, 2.25, 0.4, nm, 20, True, GREEN if i < 4 else RED, PP_ALIGN.CENTER),
          txt(s.shapes, x, 4.6, 2.25, 0.35, wh, 13, False, DGREY, PP_ALIGN.CENTER),
          chip(s.shapes, x + 0.1, 5.0, 2.05, 0.45, f"{n:,} houses", fill=MINT, color=GREEN, size=14),
          chip(s.shapes, x + 0.1, 5.5, 2.05, 0.45, f"{100 * d / n:.0f}% destroyed", fill=GOLD, color=GREEN, size=14)]
    G.append(sh)
tagx = txt(s.shapes, 0.45, 6.05, 9.8, 0.4, "xBD satellite images · leave-one-fire-out", 14, True, GREEN, PP_ALIGN.CENTER)
tage = txt(s.shapes, 10.2, 6.05, 2.5, 0.4, "external test · field-inspected", 14, True, RED, PP_ALIGN.CENTER)
sep = box(s.shapes, 10.07, 1.9, 0.04, 4.5, fill=GREY, shape=MSO_SHAPE.RECTANGLE)
lab = chip(s.shapes, 0.45, 6.5, 12.4, 0.42, "3 classes: no damage · damaged · destroyed   ('damaged' = only 1–6% of houses)", fill=MINT, color=BODY, size=13)
animate(s, [("fade", [group(s, sum(G[:4], []) + [tagx])]), ("fade", [group(s, G[4] + [tage, sep])]), ("fade", [lab])])

# ---------- S6 data prep ----------
s = new_slide("Building a Clean Dataset",
 "CLICK ORDER: (1) crop fix before→after, (2)–(4) one card per fix.\n"
 "KEY MESSAGE: Each data problem was fixed once and checked automatically before any model was trained.\n"
 "Crops: 64 m × 64 m ground square around each building, 224 × 224 px, pre and post. v1 padded buildings near tile edges with black (~20% of crops > 25% black). "
 "v2 shifts the window inside the tile and stores the building position: 0.25% of sampled crops > 25% black.\n"
 "Archive: xBD is 6 parts (~55 GB) with 54 GB free on the laptop; scripts read the parts as one stream (counting 532 s, cropping 767 s). SHA1 of all 6 parts matched xview2.org.\n"
 "Eaton: Maxar WorldView-3 before (1 Jan 2025) and after (14 Jan 2025), 0% cloud. Overlay check on 30 houses: DINS points on or within a few metres of the house; pre/post image shift median 2.33 m, max 5.20 m.\n"
 "Dropped: BRIGHT (post-event images are radar, not colour).")
g1 = group(s, [pic(s.shapes, "v1_padded.png", 0.55, 2.0, 2.6, 2.36), arrow(s.shapes, 3.3, 2.95), pic(s.shapes, "v2_fixed.png", 3.9, 2.0, 2.6, 2.4),
               txt(s.shapes, 0.55, 4.45, 2.6, 0.4, "v1: black padding", 14, True, RED, PP_ALIGN.CENTER),
               txt(s.shapes, 3.9, 4.45, 2.6, 0.4, "v2: window shifted", 14, True, LGREEN, PP_ALIGN.CENTER),
               kpi(s.shapes, 1.6, 5.0, 3.85, 1.3, "20% → 0.25%", "crops with > 25% black", key=True)])
cards = [("55 GB archive, 54 GB free", "read as one stream; all 6 checksums match", GREEN),
         ("Two xBD 'fires' were one fire", "socal + woolsey merged: no test house in training", GOLD),
         ("Eaton imagery", "same-satellite Maxar pair; houses aligned within 2.3 m (median)", LGREEN)]
CG = [group(s, card(s.shapes, 7.0, 2.0 + i * 1.45, 5.85, 1.25, tt, ll, accent=ac)) for i, (tt, ll, ac) in enumerate(cards)]
animate(s, [("fade", [g1])] + [("fade", [c]) for c in CG])

# ---------- S7 design ----------
s = new_slide("Testing on Fires the Model Never Saw",
 "CLICK ORDER: (1) fold grid, (2) Eaton column, (3) rules chips.\n"
 "KEY MESSAGE: Every result is on a fire the model never trained on; Eaton is a fully external, field-inspected test.\n"
 "Leave-one-fire-out: fold k tests on one xBD fire; the other three are split by 0.005° grid cell (~500 m) into train 70% / val 10% / calib 20% (building shares). "
 "Grid cells keep neighbouring houses together, so near-duplicates never cross roles. Every fold model also scores all 8,457 Eaton buildings.\n"
 "Rules (models, metrics, α = 0.10, ≤ 5% routing rule, bootstrap) were written and committed before training (commit 47a8a44). "
 "Uncertainty: 95% cluster-bootstrap CIs over grid cells (1,000 resamples); 3 seeds for T1 and T3; Eaton = mean ± SD over the 4 fold models.")
cols = ["Santa Rosa", "Woolsey", "Pinery", "Portugal"]
GR = []
for j, cn in enumerate(cols): GR.append(txt(s.shapes, 2.0 + j * 2.05, 1.85, 1.95, 0.4, cn, 15, True, GREEN, PP_ALIGN.CENTER))
for i in range(4):
    GR.append(txt(s.shapes, 0.5, 2.38 + i * 0.72, 1.4, 0.5, f"Fold {i + 1}", 16, True, BODY, anchor=MSO_ANCHOR.MIDDLE))
    for j in range(4):
        test = i == j
        b_ = box(s.shapes, 2.0 + j * 2.05, 2.35 + i * 0.72, 1.95, 0.58, fill=RED if test else MINT, adj=0.15)
        label(b_, "test" if test else "train / val / calib", size=14 if test else 12, color=WHITE if test else GREEN); GR.append(b_)
EC = [txt(s.shapes, 10.4, 1.85, 2.4, 0.4, "Eaton 2025", 15, True, RED, PP_ALIGN.CENTER)]
for i in range(4):
    b_ = box(s.shapes, 10.4, 2.35 + i * 0.72, 2.4, 0.58, fill=GOLD, adj=0.15); label(b_, "external test", size=13, color=GREEN); EC.append(b_)
rules = [chip(s.shapes, 0.5, 5.45, 3.9, 0.55, "Splits by ~500 m grid cell", fill=GREEN, color=WHITE, size=14),
         chip(s.shapes, 4.6, 5.45, 4.1, 0.55, "Rules frozen before training", fill=GREEN, color=WHITE, size=14),
         chip(s.shapes, 8.9, 5.45, 3.9, 0.55, "3 seeds · bootstrap CIs", fill=GREEN, color=WHITE, size=14)]
animate(s, [("wipe", [group(s, GR)]), ("fade", [group(s, EC)]), ("fade", [group(s, rules)])])

# ---------- S8 models ----------
s = new_slide("Three Models, One Uncertainty Layer",
 "CLICK ORDER: one click per model (3), then the shared layer.\n"
 "KEY MESSAGE: The same calibration, prediction-set and routing steps run on top of a CNN, a zero-shot VLM and a fine-tuned VLM.\n"
 "T1: Siamese ConvNeXt-Tiny (ImageNet weights), pre/post crops with a red marker on the building, class-weighted cross-entropy, early stopping on val; 4 folds × 3 seeds.\n"
 "T2: Qwen3-VL-8B-Instruct zero-shot with one frozen prompt; class probabilities = softmax over the A/B/C answer-token logits; 1 run over all 83,079 buildings.\n"
 "T3: same VLM + LoRA (rank 16), 3-way cross-entropy on the A/B/C logits, ≤ 3 epochs, early stopping on val; 4 folds × 3 seeds. Pilot: 50 LoRA steps, 44 GB peak, no out-of-memory.\n"
 "Compute: H200 GPUs.\n"
 "Shared layer: temperature scaling on calib → conformal sets (LAC, APS, Ordinal, Mondrian) at α = 0.10 → routing rule.")
tiers = [("T1 · CNN", ["Siamese ConvNeXt-Tiny", "trained on our crops", "12 runs"], GREEN),
         ("T2 · VLM zero-shot", ["Qwen3-VL-8B, as-is", "asked A / B / C", "no training"], GREY),
         ("T3 · VLM + LoRA", ["same VLM", "LoRA fine-tuned", "12 runs"], GOLD)]
TG = []
for i, (tt, ll, col) in enumerate(tiers):
    x = 0.5 + i * 4.17
    hd = box(s.shapes, x, 1.9, 3.95, 0.75, fill=col, adj=0.2); label(hd, tt, size=20, color=GOLD if col == GREEN else GREEN if col == GOLD else WHITE)
    bd = box(s.shapes, x, 2.7, 3.95, 1.95, fill=MINT, adj=0.06)
    tt_ = txt(s.shapes, x + 0.2, 2.8, 3.55, 1.8, [[("• " + l, False, BODY, 17)] for l in ll], anchor=MSO_ANCHOR.MIDDLE)
    TG.append(group(s, [hd, bd, tt_]))
lay_ = [box(s.shapes, 0.5, 4.95, 12.3, 1.2, fill=GREEN, adj=0.1)]
label(lay_[0], [[("Same layer for all three", True, GOLD, 18)], [("probabilities → temperature scaling → prediction sets (90%) → auto-label or inspector", False, WHITE, 16)]])
animate(s, [("fade", [g]) for g in TG] + [("wipe", [group(s, lay_)])])

# ---------- S9 accuracy ----------
s = new_slide("Result 1: Fine-Tuning Makes the VLM Match the CNN",
 "CLICK ORDER: (1) chart, (2) card on the damaged class.\n"
 "KEY MESSAGE: LoRA fine-tuning lifts the VLM from 0.31–0.43 to the CNN's level (0.52–0.69 macro-F1); all models drop on fires unlike the training fires.\n"
 "Macro-F1 (seed mean), test fires with 95% cluster-bootstrap CIs: T1 0.669 [0.656, 0.682] / 0.638 / 0.578 / 0.534; T3 0.667 / 0.637 / 0.571 / 0.519; T2 0.399 / 0.375 / 0.373 / 0.311. "
 "Eaton: T1 0.683 ± 0.026, T3 0.693 ± 0.026, T2 0.426.\n"
 "Damaged-class F1 is 0.09–0.22 on every test fire for T1 and T3 (seed means); 'damaged' is 1–3% of training houses and many Eaton 'Affected 1–9%' houses look intact from above.\n"
 "T1 vs T3 differences are descriptive only (no paired test). Full table: report Table 2.")
ch = bar_chart(s, 0.4, 1.75, 8.6, 4.95, [(n, getv(A, "macro_F1", m=m), TIER[m]) for n, m in [("T1 CNN", "T1"), ("T2 VLM zero-shot", "T2"), ("T3 VLM + LoRA", "T3")]], 0, 0.85)
cc = card(s.shapes, 9.3, 2.1, 3.6, 1.9, "Fine-tuning pays", "T3 reaches the CNN: 0.52–0.69 vs 0.31–0.43 zero-shot", accent=LGREEN)
cd_ = card(s.shapes, 9.3, 4.2, 3.6, 1.9, "'Damaged' is hard", "F1 ≤ 0.22 on every test fire: rare and often invisible from above", accent=RED)
animate(s, [("wipe", ch), ("fade", [group(s, cc)]), ("fade", [group(s, cd_)])])

# ---------- S10 calibration ----------
s = new_slide("Result 2: T1 and T3 Know How Sure They Are",
 "CLICK ORDER: (1) chart, (2) card.\n"
 "KEY MESSAGE: After temperature scaling, the CNN and the fine-tuned VLM are well calibrated (ECE ≤ 0.036); the zero-shot VLM stays overconfident.\n"
 "ECE = expected calibration error, 15 equal-width bins on the top-class probability; lower is better. Values: seed means after scaling (Table 3).\n"
 "T2's fitted temperature is 6.8–11.9 (it puts almost all probability on one answer); scaling reduces its ECE from 0.30–0.56 to 0.07–0.23, still far from T1/T3.\n"
 "Reliability diagrams: report Figure (fig1_reliability).")
ch = bar_chart(s, 0.4, 1.75, 8.6, 4.95, [(n, getv(K, "ECE after", m=m), TIER[m]) for n, m in [("T1 CNN", "T1"), ("T2 VLM zero-shot", "T2"), ("T3 VLM + LoRA", "T3")]], 0, 0.27, fmt="0.00")
k1 = kpi(s.shapes, 9.3, 2.1, 3.6, 1.6, "≤ 0.036", "ECE · T1 and T3, all fires", key=True)
k2 = card(s.shapes, 9.3, 3.95, 3.6, 2.1, "Zero-shot VLM", "overconfident (T = 6.8–11.9); still 0.07–0.23 ECE after scaling", accent=RED)
animate(s, [("wipe", ch), ("fade", [group(s, [k1] + k2)])])

# ---------- S11 coverage ----------
s = new_slide("Result 3: The 90% Guarantee Breaks on New Fires",
 "CLICK ORDER: (1) chart, (2) target line note, (3) card.\n"
 "KEY MESSAGE: Coverage of destroyed homes meets the 90% target when the test fire looks like the training fires (Santa Rosa, Eaton) and fails badly when it does not (Woolsey, Pinery, Portugal).\n"
 "Mondrian (class-conditional) conformal sets at α = 0.10, thresholds from calib of the training fires. Destroyed-class coverage (seed mean): "
 "T1 0.97 / 0.69 / 0.46 / 0.24 (0.235), Eaton 0.93; T3 0.975 / 0.75 / 0.60 / 0.30, Eaton 0.97; T2 0.99 / 0.83 / 0.71 / 0.40, Eaton 0.99.\n"
 "Why: conformal guarantees assume the new data are exchangeable with the calibration data. A new fire (other country, sensor, building style) violates this.\n"
 "Also: non-randomised APS/Ordinal sets collapse to one class for T1/T3 (calib accuracy > 0.90), reported in Table 4.")
ch = bar_chart(s, 0.4, 1.75, 8.6, 4.95, [(n, getv(C[C.method == "Mondrian"], "cov destroyed", m=m), TIER[m]) for n, m in [("T1 CNN", "T1"), ("T2 VLM zero-shot", "T2"), ("T3 VLM + LoRA", "T3")]],
               0, 1.1, ref=0.9, reflab="90% target")
c1 = card(s.shapes, 9.3, 2.1, 3.6, 1.9, "Holds", "Santa Rosa and Eaton: 0.93–0.99 of destroyed homes covered", accent=LGREEN)
c2 = card(s.shapes, 9.3, 4.2, 3.6, 1.9, "Breaks", "Portugal: only 0.24–0.40 covered, the new fire looks different", accent=RED)
animate(s, [("wipe", ch[:1]), ("fade", ch[1:]), ("fade", [group(s, c1 + c2)])])

# ---------- S12 Eaton workload ----------
ra = R[R.method == "APS"]
t3a, t3m = num(ra[(ra.m == "T3") & (ra.fire == "Eaton")]["auto-labelled share"].iloc[0]), num(ra[(ra.m == "T3") & (ra.fire == "Eaton")]["missed destroyed"].iloc[0])
s = new_slide("Result 4: On Eaton, 93% of Houses Need No Visit",
 "CLICK ORDER: (1) map, (2) KPI tiles.\n"
 f"KEY MESSAGE: On the 2025 Eaton Fire, T3 with APS sets auto-labels {t3a:.0%} of houses and misses only {t3m:.1%} of destroyed homes.\n"
 "Numbers: T3, APS sets, routing α chosen on calib (≤ 5% missed destroyed): auto-labelled 0.934 ± 0.044, missed destroyed 0.010 ± 0.006 (mean ± SD over 12 fold × seed models). "
 "T1: 0.910 auto, 0.028 missed. 0.934 × 8,457 ≈ 7,900 houses.\n"
 "Map: ONE run (T3 fold 1 seed 0, α = 0.055): routed 594 (7.0%), auto-labelled correct 7,377 (87.2%), auto-labelled wrong 477 (5.6%), missed destroyed 9 of 3,907. "
 "Blue = auto-labelled correct, green = routed to inspector, orange = auto-labelled wrong, × = missed destroyed. Axes in km from the centroid.\n"
 "Caveat: auto-labelled houses still have 6% errors overall, mostly 'damaged' houses labelled as another class; the rule protects only 'destroyed'.")
m_ = pic(s.shapes, "eaton_map_aps.png", 0.6, 1.75, 8.0, None)
leg = []
for i, (lab_, col_) in enumerate([("auto-labelled, correct", RGBColor.from_string("2A78D6")), ("routed to inspector", RGBColor.from_string("1BAF7A")), ("auto-labelled, wrong", RGBColor.from_string("EB6834"))]):
    leg += [box(s.shapes, 0.6 + i * 2.85, 6.42, 0.18, 0.18, fill=col_, shape=MSO_SHAPE.OVAL), txt(s.shapes, 0.82 + i * 2.85, 6.32, 2.6, 0.35, lab_, 13, False, BODY)]
leg.append(txt(s.shapes, 0.6, 6.66, 8.4, 0.3, "one run: T3 fold 1 seed 0 · × = missed destroyed (9 of 3,907)", 11, False, DGREY))
m_ = group(s, [m_] + leg)
k1 = kpi(s.shapes, 9.35, 1.9, 3.5, 1.45, f"{t3a:.0%}", "auto-labelled, no visit", key=True)
k2 = kpi(s.shapes, 9.35, 3.5, 3.5, 1.45, f"{t3m:.1%}", "destroyed homes missed")
k3 = kpi(s.shapes, 9.35, 5.1, 3.5, 1.45, "≈ 7,900", "of 8,457 houses")
animate(s, [("fade", [m_]), ("fade", [group(s, [k1, k2, k3])])])

# ---------- S13 routing on new fires ----------
s = new_slide("Result 5: The 5% Rule Does Not Transfer",
 "CLICK ORDER: (1) chart, (2) target line, (3) card.\n"
 "KEY MESSAGE: The routing threshold that keeps missed destroyed ≤ 5% on past fires lets 9–43% of destroyed homes slip through on fires that look different.\n"
 "APS sets, α chosen on calib (rule 8; A1 gives the same choice for APS). Missed destroyed, seed mean, with 95% CI: "
 "T1 0.9% / 14.0% [12.2, 15.7] / 31.7% [25.9, 38.9] / 42.7% [39.2, 46.3]; T3 1.1% / 9.4% / 20.4% / 38.3%; Eaton T1 2.8%, T3 1.0%. "
 "Auto-labelled share stays 90–95% on those three fires, so the model is confidently wrong rather than unsure.\n"
 "Recorded failure: T3 fold 4 seed 1 chose α = 0.5, auto-labelled all of Portugal and missed 54% of its destroyed homes.\n"
 "Post-hoc randomised APS (P1, not preregistered) lowers T3 misses to 0.9 / 3.7 / 9.2 / 15.1% at 72–83% auto-labelled.")
ch = bar_chart(s, 0.4, 1.75, 8.6, 4.95, [(n, getv(ra, "missed destroyed", m=m), TIER[m]) for n, m in [("T1 CNN", "T1"), ("T3 VLM + LoRA", "T3")]],
               0, 0.5, fmt="0%", ref=0.05, reflab="5% target")
c1 = card(s.shapes, 9.3, 2.1, 3.6, 2.0, "Confidently wrong", "90–95% still auto-labelled while 9–43% of destroyed homes are missed", accent=RED)
c2 = card(s.shapes, 9.3, 4.3, 3.6, 1.8, "Lesson", "a guarantee from past fires is not a guarantee on a new one", accent=GOLD)
animate(s, [("wipe", ch[:1]), ("fade", ch[1:]), ("fade", [group(s, c1 + c2)])])

# ---------- S14 examples ----------
s = new_slide("What the Model Sees: Three Eaton Houses",
 "CLICK ORDER: one click per example (3).\n"
 "KEY MESSAGE: Clear destruction is auto-labelled, ambiguous houses go to an inspector, and the rare misses are houses that look intact from above.\n"
 "All three are destroyed homes (DINS) from T3 fold 1 seed 0, Mondrian sets at α = 0.090, one random building per category (fig4_examples). "
 "p = calibrated probabilities of no damage / damaged / destroyed. Red circle = building of interest; each crop is 64 m wide.\n"
 "(1) Auto-labelled correct: set {destroyed}, p = 0.00 / 0.00 / 0.99 (3,119 such houses in this run). "
 "(2) Routed: set {damaged, destroyed}, p = 0.03 / 0.05 / 0.92 (778 destroyed houses routed). "
 "(3) Missed: set {damaged}, p = 0.41 / 0.18 / 0.42; roof looks intact from above (10 such houses).")
ex = [("ex_des_auto", "Auto-labelled ✓", "{destroyed}", LGREEN), ("ex_des_route", "Sent to inspector", "{damaged, destroyed}", GOLD), ("ex_des_miss", "Missed ✗", "{damaged}", RED)]
EX = []
for i, (f, tt, st, col) in enumerate(ex):
    x = 0.45 + i * 4.2
    EX.append(group(s, [pic(s.shapes, f + "_pre.png", x, 1.95, 1.95, 1.95), pic(s.shapes, f + "_post.png", x + 2.05, 1.95, 1.95, 1.95),
                        txt(s.shapes, x, 3.95, 1.95, 0.35, "before", 13, False, DGREY, PP_ALIGN.CENTER), txt(s.shapes, x + 2.05, 3.95, 1.95, 0.35, "after", 13, False, DGREY, PP_ALIGN.CENTER),
                        chip(s.shapes, x, 4.45, 4.0, 0.6, tt, fill=col, color=WHITE if col != GOLD else GREEN, size=17),
                        txt(s.shapes, x, 5.15, 4.0, 0.45, "set " + st, 16, True, GREEN, PP_ALIGN.CENTER)]))
ft = txt(s.shapes, 0.45, 5.85, 12.4, 0.4, "All three houses were destroyed (CAL FIRE field inspection) · T3 model · Eaton 2025", 14, False, DGREY, PP_ALIGN.CENTER)
animate(s, [("fade", [e_]) for e_ in EX[:-1]] + [("fade", [EX[-1], ft])])

# ---------- S15 E1 ----------
b_cov, r_cov = e1v("t3", "Mondrian", "baseline", 200, "cov_c2"), e1v("t3", "Mondrian", "recal", 200, "cov_c2")
b_mis, r_mis = e1v("t3", "APS", "baseline", 200, "missed_A1"), e1v("t3", "APS", "recal", 200, "missed_A1")
s = new_slide("Fix? Calibrate on ~200 Houses from the New Fire",
 "CLICK ORDER: (1) coverage chart, (2) missed chart, (3) bottom line.\n"
 "KEY MESSAGE: Labelling ~200 houses on the new fire restores coverage of destroyed homes, but not the 5% miss target on fires with few destroyed homes.\n"
 "ADDED ANALYSIS (E1), not preregistered: designed after the main results were seen; rules committed before computing (commit 64faa7f). "
 "Recalibrate T, conformal thresholds and routing α on a sample drawn by whole grid cells (≈ 235–252 houses for n = 200), 20 repeats, evaluated on the rest of the fire. T3 shown; T1 gives the same picture; random-house samples too.\n"
 f"Coverage of destroyed (Mondrian): {', '.join(f'{a_:.2f}→{b_:.2f}' for a_, b_ in zip(b_cov, r_cov))} (SR, Woolsey, Pinery, Portugal, Eaton).\n"
 f"Missed destroyed (APS): {', '.join(f'{a_:.1%}→{b_:.1%}' for a_, b_ in zip(b_mis, r_mis))}. ≤ 5% met in only 35–50% of repeats on Woolsey/Pinery/Portugal; samples there hold only 12–46 destroyed homes. "
 "Auto-labelled share falls (Portugal 95% → 67%). On Santa Rosa and Eaton, recalibration only adds noise.\n"
 "Assumes inspector labels equal the dataset labels.")
L = [("other fires (current)", GREY), ("local sample ≈200", GREEN)]
c1 = bar_chart(s, 0.3, 1.75, 6.4, 4.4, [(L[0][0], b_cov, GREY), (L[1][0], r_cov, LGREEN)], 0, 1.15, ref=0.9, reflab="90% target", lsize=11)
t1_ = txt(s.shapes, 0.3, 6.1, 6.4, 0.35, "Destroyed homes covered (Mondrian)", 15, True, GREEN, PP_ALIGN.CENTER)
c2 = bar_chart(s, 6.75, 1.75, 6.3, 4.4, [(L[0][0], b_mis, GREY), (L[1][0], r_mis, LGREEN)], 0, 0.45, fmt="0%", ref=0.05, reflab="5% target", lsize=11)
t2_ = txt(s.shapes, 6.75, 6.1, 6.3, 0.35, "Destroyed homes missed (APS routing)", 15, True, GREEN, PP_ALIGN.CENTER)
bl = chip(s.shapes, 0.45, 6.5, 12.4, 0.45, "Added analysis (not preregistered) · coverage restored · 5% target still missed on 3 of 5 fires", fill=GOLD, color=GREEN, size=14)
animate(s, [("wipe", c1 + [t1_]), ("wipe", c2 + [t2_]), ("fade", [bl])])

# ---------- S16 limitations ----------
s = new_slide("What We Must Be Honest About",
 "CLICK ORDER: one card per click (4).\n"
 "KEY MESSAGE: The main limits are fire shift, the 'damaged' class, and three analysis choices made after seeing the results; all are disclosed.\n"
 "A1 (amendment to the routing rule): 'largest α' hit the grid edge for LAC; replaced by 'maximise calib auto-share subject to ≤ 5% missed'. Proposed after seeing test results; original-rule results kept. Changes only LAC rows.\n"
 "P1 (post-hoc): randomised APS/Ordinal, because non-randomised sets collapsed to one class. Never a headline.\n"
 "E1 (added analysis): few-shot recalibration on the new fire.\n"
 "Data: only 4 distinct xBD wildfires; DINS 'Affected 1–9%' houses are labelled damaged but often look intact from above; 64 m crops at ~0.3–0.5 m resolution.\n"
 "Licences: xBD and Maxar Open Data are non-commercial; a product would need other imagery.")
lims = [("Fire shift", "guarantees hold only when the new fire resembles past fires", RED),
        ("'Damaged' class", "rare (1–6%) and often invisible from above: F1 ≤ 0.22", RED),
        ("Decided after results", "A1 routing rule, P1 randomised sets, E1 recalibration: all disclosed", GOLD),
        ("Scope", "4 xBD fires + 1 external fire; non-commercial imagery", GREY)]
LG_ = []
for i, (tt, ll, ac) in enumerate(lims):
    x, y = 0.5 + (i % 2) * 6.25, 2.0 + (i // 2) * 2.2
    LG_.append(group(s, card(s.shapes, x, y, 6.0, 1.9, tt, ll, accent=ac, tsize=20, lsize=16)))
animate(s, [("fade", [g]) for g in LG_])

# ---------- S17 takeaways ----------
s = new_slide("Takeaways and Next Steps",
 "CLICK ORDER: (1)–(3) takeaways, (4) next steps.\n"
 "KEY MESSAGE: Calibrated sets make damage AI usable for triage when the new fire resembles past fires; detecting and fixing fire shift is the next problem.\n"
 "Next steps for a paper: weighted conformal prediction under covariate shift (Tibshirani et al. 2019); a shift detector that tells when to recalibrate; more fires (e.g., BRIGHT optical events, DisasterM3); "
 "better 'damaged' labels or a destroyed-vs-not task; check full texts of related work. Venue ideas: IEEE JSTARS, IJDRR (fit to confirm).")
tk = [("1", "Fine-tuned VLM = CNN", "LoRA lifts the VLM to 0.52–0.69 macro-F1; both are well calibrated"),
      ("2", "Triage works on Eaton", "93% of houses auto-labelled, 1.0% of destroyed homes missed"),
      ("3", "Fire shift breaks guarantees", "9–43% missed on new fires; ~200 local labels fix coverage, not misses")]
TK = []
for i, (n_, tt, ll) in enumerate(tk):
    y = 1.9 + i * 1.12
    nb = box(s.shapes, 0.5, y + 0.12, 0.7, 0.7, fill=GREEN, shape=MSO_SHAPE.OVAL); label(nb, n_, size=22, color=GOLD)
    TK.append(group(s, [nb, txt(s.shapes, 1.4, y, 7.2, 0.95, [[(tt, True, GREEN, 20)], [(ll, False, BODY, 15)]], anchor=MSO_ANCHOR.MIDDLE)]))
nx = [box(s.shapes, 8.9, 1.9, 3.95, 4.6, fill=MINT, adj=0.06), txt(s.shapes, 9.1, 2.0, 3.6, 0.5, "Next (paper)", 20, True, GREEN)]
for i, l in enumerate(["Weighted conformal under shift", "Detect when a fire is 'new'", "More fires and sensors", "Better 'damaged' labels"]):
    nx.append(chip(s.shapes, 9.1, 2.7 + i * 0.9, 3.55, 0.65, l, fill=None, color=GREEN, size=14, line=GREEN, dash=True))
TK.append(group(s, nx))
animate(s, [("fade", [g]) for g in TK])

# ---------- move Thank-you to the end ----------
sldIdLst.remove(keep_last); sldIdLst.append(keep_last)
prs.slides[-1].notes_slide.notes_text_frame.text = "No animation. Questions."
prs.save(OUT)
print("saved", OUT, len(prs.slides), "slides")
